from collections.abc import Sequence

import pytest
from pydantic import BaseModel, Field

from mini_agent.agent.loop import Agent
from mini_agent.agent.models import AgentStopReason
from mini_agent.exceptions import (
    InvalidModelResponseError,
    MaxAgentStepsExceededError,
)
from mini_agent.llm.models import ChatResponse, Message, MessageRole
from mini_agent.tools.base import Tool
from mini_agent.tools.models import ToolCall
from mini_agent.tools.registry import ToolRegistry


class EchoArgs(BaseModel):
    text: str = Field(min_length=1)


class EchoTool:
    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "Echo text"

    @property
    def parameters_model(self) -> type[BaseModel]:
        return EchoArgs

    def execute(self, arguments: BaseModel) -> str:
        return EchoArgs.model_validate(arguments.model_dump()).text


class FakeLLM:
    def __init__(self, responses: list[ChatResponse]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[Tool] | None = None,
    ) -> ChatResponse:
        self.calls += 1
        if not self._responses:
            raise AssertionError("FakeLLM ran out of responses")
        return self._responses.pop(0)


def test_final_answer_on_first_turn() -> None:
    llm = FakeLLM([ChatResponse(content="hello")])
    registry = ToolRegistry()
    agent = Agent(llm=llm, registry=registry, max_steps=3)

    result = agent.run("Hi")

    assert result.success is True
    assert result.final_text == "hello"
    assert result.steps_used == 1
    assert result.stop_reason == AgentStopReason.FINAL_ANSWER
    assert llm.calls == 1


def test_single_tool_then_answer() -> None:
    llm = FakeLLM(
        [
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="echo",
                        arguments={"text": "pong"},
                    )
                ],
            ),
            ChatResponse(content="done"),
        ]
    )
    registry = ToolRegistry()
    registry.register(EchoTool())
    agent = Agent(llm=llm, registry=registry, max_steps=5)

    result = agent.run("echo please")

    assert result.success is True
    assert result.final_text == "done"
    assert result.steps_used == 2
    assert llm.calls == 2

    # 消息里应有 assistant(tool_calls) + tool 结果
    roles = [m.role for m in result.messages]
    assert MessageRole.TOOL in roles
    tool_msgs = [m for m in result.messages if m.role == MessageRole.TOOL]
    assert tool_msgs[0].tool_call_id == "call_1"
    assert tool_msgs[0].content == "pong"


def test_max_steps_raises() -> None:
    tool_response = ChatResponse(
        content="",
        tool_calls=[ToolCall(id="call_x", name="echo", arguments={"text": "x"})],
    )
    llm = FakeLLM([tool_response, tool_response, tool_response])

    registry = ToolRegistry()
    registry.register(EchoTool())
    agent = Agent(llm=llm, registry=registry, max_steps=3)

    with pytest.raises(MaxAgentStepsExceededError):
        agent.run("loop forever")

    assert llm.calls == 3


def test_missing_tool_error_fed_back_then_answer() -> None:
    llm = FakeLLM(
        [
            ChatResponse(
                content="",
                tool_calls=[ToolCall(id="call_1", name="nope", arguments={})],
            ),
            ChatResponse(content="I could not find that tool"),
        ]
    )
    agent = Agent(llm=llm, registry=ToolRegistry(), max_steps=5)

    result = agent.run("use nope")

    tool_msgs = [m for m in result.messages if m.role == MessageRole.TOOL]
    assert tool_msgs[0].content.startswith("Error:")
    assert result.final_text == "I could not find that tool"


def test_empty_model_response_raises() -> None:
    llm = FakeLLM([ChatResponse(content="", tool_calls=[])])
    agent = Agent(llm=llm, registry=ToolRegistry(), max_steps=3)

    with pytest.raises(InvalidModelResponseError):
        agent.run("Hi")
