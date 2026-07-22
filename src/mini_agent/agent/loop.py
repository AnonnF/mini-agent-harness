from pydantic import ValidationError

from mini_agent.agent.models import AgentResult, AgentStopReason
from mini_agent.exceptions import (
    InvalidModelResponseError,
    MaxAgentStepsExceededError,
    ToolExecutionError,
    ToolRegistryError,
)
from mini_agent.llm.base import LLMClient
from mini_agent.llm.models import Message, MessageRole
from mini_agent.tools.models import ToolCall
from mini_agent.tools.registry import ToolRegistry
from mini_agent.tracing.models import TerminationReason
from mini_agent.tracing.recorder import TraceRecorder


class Agent:
    def __init__(
        self,
        *,
        llm: LLMClient,
        registry: ToolRegistry,
        max_steps: int,
    ) -> None:
        self._llm = llm
        self._registry = registry
        self._max_steps = max_steps

        if max_steps < 1:
            raise ValueError("Max steps should be >= 1")

    def _run_one_tool(self, call: ToolCall) -> Message:
        try:
            tool = self._registry.get(call.name)
            args = tool.parameters_model.model_validate(call.arguments)
            output = tool.execute(args)
            return Message(
                role=MessageRole.TOOL,
                content=output,
                tool_call_id=call.id,
            )
        except (ToolRegistryError, ValidationError, ToolExecutionError) as exc:
            return Message(
                role=MessageRole.TOOL, content=f"Error: {exc}", tool_call_id=call.id
            )

    def run(
        self,
        user_input: str,
        *,
        system_prompt: str | None = None,
        recorder: TraceRecorder | None = None,
    ) -> AgentResult:
        if recorder is not None:
            recorder.start(input_text=user_input)

        messages: list[Message] = []

        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))

        messages.append(Message(role=MessageRole.USER, content=user_input))

        for step in range(1, self._max_steps + 1):
            if recorder is not None:
                recorder.record_model_request(step=step)

            response = self._llm.complete(
                messages=messages, tools=self._registry.list_tools()
            )

            if recorder is not None:
                recorder.record_model_response(
                    step=step,
                    success=True,
                    has_tool_calls=bool(response.tool_calls),
                    content_preview=response.content or "",
                    usage=response.usage,
                )

            # 分支1:模型要调用工具
            if response.tool_calls:
                messages.append(
                    Message(
                        role=MessageRole.ASSISTANT,
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                )
                for call in response.tool_calls:
                    if recorder is not None:
                        recorder.record_tool_call(
                            step=step,
                            tool_name=call.name,
                            tool_call_id=call.id,
                            arguments_preview=str(call.arguments),
                        )
                    tool_msg = self._run_one_tool(call=call)
                    if recorder is not None:
                        recorder.record_tool_result(
                            step=step,
                            tool_call_id=call.id,
                            success=not tool_msg.content.startswith("Error:"),
                            output=tool_msg.content,
                        )
                    messages.append(tool_msg)
                continue

            # 分支2: 无工具无文本 -> 非法
            if not response.content:
                if recorder is not None:
                    recorder.finish(
                        success=False,
                        reason=TerminationReason.INVALID_MODEL_RESPONSE,
                        final_output="",
                        total_steps=step,
                    )
                raise InvalidModelResponseError(
                    "Model returned neither content nor tool_calls"
                )

            # 分支3：最终回答
            messages.append(
                Message(role=MessageRole.ASSISTANT, content=response.content)
            )
            if recorder is not None:
                recorder.finish(
                    success=True,
                    reason=TerminationReason.FINAL_ANSWER,
                    final_output=response.content,
                    total_steps=step,
                )
            return AgentResult(
                success=True,
                final_text=response.content,
                steps_used=step,
                stop_reason=AgentStopReason.FINAL_ANSWER,
                messages=messages,
            )

        if recorder is not None:
            recorder.finish(
                success=False,
                reason=TerminationReason.MAX_STEPS,
                final_output="",
                total_steps=self._max_steps,
            )

        raise MaxAgentStepsExceededError(
            f"Reached max_step={self._max_steps} without a final answer"
        )
