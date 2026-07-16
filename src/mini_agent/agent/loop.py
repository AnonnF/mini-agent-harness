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

    def run(self, user_input: str, *, system_prompt: str | None = None) -> AgentResult:
        messages: list[Message] = []

        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))

        messages.append(Message(role=MessageRole.USER, content=user_input))

        for step in range(1, self._max_steps + 1):
            response = self._llm.complete(
                messages=messages, tools=self._registry.list_tools()
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
                    messages.append(self._run_one_tool(call))
                continue

            # 分支2: 无工具无文本 -> 非法
            if not response.content:
                raise InvalidModelResponseError(
                    "Model returned neither content nor tool_calls"
                )

            # 分支3：最终回答
            messages.append(
                Message(role=MessageRole.ASSISTANT, content=response.content)
            )
            return AgentResult(
                success=True,
                final_text=response.content,
                steps_used=step,
                stop_reason=AgentStopReason.FINAL_ANSWER,
                messages=messages,
            )

        raise MaxAgentStepsExceededError(
            f"Reached max_step={self._max_steps} without a final answer"
        )
