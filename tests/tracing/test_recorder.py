import pytest

from mini_agent.tracing.models import TerminationReason, TraceEventType
from mini_agent.tracing.recorder import TraceRecorder
from mini_agent.tracing.sanitize import _TRUNCATE_MARKER


def test_start_finish_produces_trace_with_completed_event() -> None:
    recorder = TraceRecorder()
    run_id = recorder.start(input_text="hello")

    trace = recorder.finish(
        success=True,
        reason=TerminationReason.FINAL_ANSWER,
        final_output="done",
        total_steps=1,
    )

    assert trace.run_id == run_id
    assert trace.input_text == "hello"
    assert trace.success is True
    assert trace.termination_reason == TerminationReason.FINAL_ANSWER
    assert trace.final_output == "done"
    assert trace.total_steps == 1
    assert trace.duration_ms >= 0
    assert trace.model_call_count == 0
    assert trace.tool_call_count == 0

    last_event = trace.events[-1]
    assert last_event.event_type == TraceEventType.AGENT_COMPLETED
    assert last_event.success is True
    assert last_event.sequence == len(trace.events) - 1


def test_finish_failure_appends_agent_failed_event() -> None:
    recorder = TraceRecorder()
    recorder.start(input_text="hello")

    trace = recorder.finish(
        success=False,
        reason=TerminationReason.MAX_STEPS,
        final_output="",
        total_steps=3,
    )

    assert trace.success is False
    assert trace.termination_reason == TerminationReason.MAX_STEPS

    last_event = trace.events[-1]
    assert last_event.event_type == TraceEventType.AGENT_FAILED
    assert last_event.success is False


def test_event_sequence_starts_at_zero_and_increments() -> None:
    recorder = TraceRecorder()
    recorder.start(input_text="x")

    recorder.record_model_request(step=1)
    recorder.record_model_response(
        step=1,
        success=True,
        has_tool_calls=True,
        content_preview="",
    )
    recorder.record_tool_call(
        step=1,
        tool_name="echo",
        tool_call_id="call_1",
        arguments_preview='{"text": "pong"}',
    )
    recorder.record_tool_result(
        step=1,
        tool_call_id="call_1",
        success=True,
        output="pong",
    )

    trace = recorder.finish(
        success=True,
        reason=TerminationReason.FINAL_ANSWER,
        final_output="done",
        total_steps=2,
    )

    sequences = [event.sequence for event in trace.events]
    assert sequences == list(range(len(trace.events)))
    assert trace.events[0].sequence == 0
    assert trace.model_call_count == 1
    assert trace.tool_call_count == 1


def test_tool_result_failure_does_not_fail_entire_trace() -> None:
    recorder = TraceRecorder()
    recorder.start(input_text="use tool")

    recorder.record_tool_call(
        step=1,
        tool_name="nope",
        tool_call_id="call_1",
        arguments_preview="{}",
    )
    recorder.record_tool_result(
        step=1,
        tool_call_id="call_1",
        success=False,
        output="Error: tool not found",
    )

    trace = recorder.finish(
        success=True,
        reason=TerminationReason.FINAL_ANSWER,
        final_output="recovered",
        total_steps=2,
    )

    tool_result_events = [
        event
        for event in trace.events
        if event.event_type == TraceEventType.TOOL_RESULT
    ]
    assert len(tool_result_events) == 1
    assert tool_result_events[0].success is False
    assert trace.success is True


def test_long_output_is_truncated_in_metadata() -> None:
    recorder = TraceRecorder(max_output_chars=20)
    recorder.start(input_text="x")

    long_output = "x" * 200
    recorder.record_tool_result(
        step=1,
        tool_call_id="call_1",
        success=True,
        output=long_output,
    )

    trace = recorder.finish(
        success=True,
        reason=TerminationReason.FINAL_ANSWER,
        final_output="done",
        total_steps=1,
    )

    tool_result = next(
        event
        for event in trace.events
        if event.event_type == TraceEventType.TOOL_RESULT
    )
    output_preview = tool_result.metadata["output_preview"]
    assert isinstance(output_preview, str)
    assert len(output_preview) <= 20
    assert _TRUNCATE_MARKER in output_preview
    assert tool_result.metadata["original_length"] == 200


def test_run_id_unique_across_runs() -> None:
    recorder = TraceRecorder()

    run_id_1 = recorder.start(input_text="first")
    trace_1 = recorder.finish(
        success=True,
        reason=TerminationReason.FINAL_ANSWER,
        final_output="a",
        total_steps=1,
    )

    run_id_2 = recorder.start(input_text="second")
    trace_2 = recorder.finish(
        success=True,
        reason=TerminationReason.FINAL_ANSWER,
        final_output="b",
        total_steps=1,
    )

    assert run_id_1 == trace_1.run_id
    assert run_id_2 == trace_2.run_id
    assert run_id_1 != run_id_2


def test_record_before_start_raises() -> None:
    recorder = TraceRecorder()

    with pytest.raises(RuntimeError):
        recorder.record_model_request(step=1)


def test_finish_before_start_raises() -> None:
    recorder = TraceRecorder()

    with pytest.raises(RuntimeError):
        recorder.finish(
            success=True,
            reason=TerminationReason.FINAL_ANSWER,
            final_output="done",
            total_steps=1,
        )
