from datetime import UTC, datetime
from uuid import uuid4

from mini_agent.llm.models import Usage
from mini_agent.tracing.models import (
    AgentTrace,
    TerminationReason,
    TraceEvent,
    TraceEventType,
)
from mini_agent.tracing.sanitize import DEFAULT_TRACE_OUTPUT_MAX_CHARS, truncate_text


class TraceRecorder:
    def __init__(
        self, *, max_output_chars: int = DEFAULT_TRACE_OUTPUT_MAX_CHARS
    ) -> None:
        if max_output_chars < 1:
            raise ValueError("max_output_chars must be >= 1")

        self._max_output_chars = max_output_chars
        self._reset()

    def _reset(self) -> None:
        self._run_id: str | None = None
        self._task_id: str | None = None
        self._input_text = ""
        self._started_at: datetime | None = None
        self._events: list[TraceEvent] = []
        self._next_sequence = 0
        self._model_call_count = 0
        self._tool_call_count = 0
        self._usage: Usage | None = None
        self._active = False

    def _require_active(self) -> None:
        if not self._active:
            raise RuntimeError("TraceRecorder has not been started")

    def _append(
        self,
        *,
        step: int,
        event_type: TraceEventType,
        success: bool,
        metadata: dict[str, object] | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        self._require_active()
        event_finished_at = finished_at or self._now()
        event_started_at = started_at or event_finished_at
        event = TraceEvent(
            sequence=self._next_sequence,
            step=step,
            event_type=event_type,
            started_at=event_started_at,
            finished_at=event_finished_at,
            success=success,
            metadata=metadata or {},
        )
        self._events.append(event)
        self._next_sequence += 1

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _preview(self, text: str) -> str:
        return truncate_text(text, max_chars=self._max_output_chars)

    def start(self, *, input_text: str, task_id: str | None = None) -> str:
        if self._active:
            raise RuntimeError("TraceRecorder is already active")

        self._reset()
        self._run_id = str(uuid4())
        self._task_id = task_id
        self._input_text = input_text
        self._started_at = self._now()
        self._active = True
        return self._run_id

    def record_model_request(self, *, step: int) -> None:
        self._append(step=step, event_type=TraceEventType.MODEL_REQUEST, success=True)

    def record_model_response(
        self,
        *,
        step: int,
        success: bool,
        has_tool_calls: bool,
        content_preview: str,
        usage: Usage | None = None,
    ) -> None:
        self._model_call_count += 1
        self._usage = usage

        self._append(
            step=step,
            event_type=TraceEventType.MODEL_RESPONSE,
            success=success,
            metadata={
                "has_tool_calls": has_tool_calls,
                "content_preview": self._preview(content_preview),
            },
        )

    def finish(
        self,
        *,
        success: bool,
        reason: TerminationReason,
        final_output: str = "",
        total_steps: int,
    ) -> AgentTrace:
        self._require_active()

        assert self._run_id is not None
        assert self._started_at is not None

        finished_at = self._now()
        duration_ms = max(
            0,
            int((finished_at - self._started_at).total_seconds() * 1000),
        )

        final_output_preview = self._preview(final_output)
        final_event_type = (
            TraceEventType.AGENT_COMPLETED if success else TraceEventType.AGENT_FAILED
        )

        self._append(
            step=total_steps,
            event_type=final_event_type,
            success=success,
            metadata={"final_output_preview": final_output_preview},
            finished_at=finished_at,
        )

        trace = AgentTrace(
            run_id=self._run_id,
            task_id=self._task_id,
            input_text=self._input_text,
            started_at=self._started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            events=list(self._events),
            final_output=final_output_preview,
            success=success,
            termination_reason=reason,
            total_steps=total_steps,
            model_call_count=self._model_call_count,
            tool_call_count=self._tool_call_count,
            usage=self._usage,
        )

        self._active = False
        return trace

    def record_tool_call(
        self,
        *,
        step: int,
        tool_name: str,
        tool_call_id: str,
        arguments_preview: str,
    ) -> None:
        self._tool_call_count += 1
        self._append(
            step=step,
            event_type=TraceEventType.TOOL_CALL,
            success=True,
            metadata={
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "arguments_preview": self._preview(arguments_preview),
            },
        )

    def record_tool_result(
        self,
        *,
        step: int,
        tool_call_id: str,
        success: bool,
        output: str,
    ) -> None:
        self._append(
            step=step,
            event_type=TraceEventType.TOOL_RESULT,
            success=success,
            metadata={
                "tool_call_id": tool_call_id,
                "output_preview": self._preview(output),
                "original_length": len(output),
            },
        )
