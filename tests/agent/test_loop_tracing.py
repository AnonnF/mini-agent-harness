from collections.abc import Sequence

import pytest
from pydantic import BaseModel, Field

from mini_agent.agent.loop import Agent
from mini_agent.agent.models import AgentStopReason
from mini_agent.exceptions import (
    InvalidModelResponseError,
    MaxAgentStepsExceededError,
)
from mini_agent.llm.models import ChatResponse, Message
from mini_agent.tools.base import Tool
from mini_agent.tools.models import ToolCall
from mini_agent.tools.registry import ToolRegistry
from mini_agent.tracing.models import TerminationReason, TraceEventType
from mini_agent.tracing.recorder import TraceRecorder


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


def test_run_without_recorder_keeps_existing_behavior() -> None:
    llm = FakeLLM([ChatResponse(content="hello")])
    agent = Agent(llm=llm, registry=ToolRegistry(), max_steps=3)

    result = agent.run("Hi")

    assert result.success is True
    assert result.final_text == "hello"
    assert result.steps_used == 1
    assert result.stop_reason == AgentStopReason.FINAL_ANSWER


def test_final_answer_records_model_and_completed_events() -> None:
    llm = FakeLLM([ChatResponse(content="hello")])
    agent = Agent(llm=llm, registry=ToolRegistry(), max_steps=3)
    recorder = TraceRecorder()

    result = agent.run("Hi", recorder=recorder)

    assert result.final_text == "hello"
    assert recorder.last_trace is not None

    trace = recorder.last_trace
    assert trace.input_text == "Hi"
    assert trace.success is True
    assert trace.termination_reason == TerminationReason.FINAL_ANSWER
    assert trace.total_steps == 1
    assert trace.model_call_count == 1
    assert trace.tool_call_count == 0
    assert trace.final_output == "hello"

    event_types = [event.event_type for event in trace.events]
    assert TraceEventType.MODEL_REQUEST in event_types
    assert TraceEventType.MODEL_RESPONSE in event_types
    assert event_types[-1] == TraceEventType.AGENT_COMPLETED


def test_single_tool_records_tool_call_and_result() -> None:
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
    recorder = TraceRecorder()

    result = agent.run("echo please", recorder=recorder)

    assert result.final_text == "done"
    assert recorder.last_trace is not None

    trace = recorder.last_trace
    assert trace.success is True
    assert trace.model_call_count == 2
    assert trace.tool_call_count == 1

    event_types = [event.event_type for event in trace.events]
    assert TraceEventType.TOOL_CALL in event_types
    assert TraceEventType.TOOL_RESULT in event_types
    assert event_types[-1] == TraceEventType.AGENT_COMPLETED

    tool_call = next(
        event for event in trace.events if event.event_type == TraceEventType.TOOL_CALL
    )
    tool_result = next(
        event
        for event in trace.events
        if event.event_type == TraceEventType.TOOL_RESULT
    )
    assert tool_call.metadata["tool_name"] == "echo"
    assert tool_call.metadata["tool_call_id"] == "call_1"
    assert tool_result.success is True
    assert tool_result.metadata["tool_call_id"] == "call_1"
    assert tool_result.metadata["output_preview"] == "pong"


def test_missing_tool_records_failed_tool_result_but_completed_run() -> None:
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
    recorder = TraceRecorder()

    result = agent.run("use nope", recorder=recorder)

    assert result.final_text == "I could not find that tool"
    assert recorder.last_trace is not None

    trace = recorder.last_trace
    assert trace.success is True
    assert trace.termination_reason == TerminationReason.FINAL_ANSWER

    tool_result = next(
        event
        for event in trace.events
        if event.event_type == TraceEventType.TOOL_RESULT
    )
    assert tool_result.success is False
    assert "Error:" in str(tool_result.metadata["output_preview"])


def test_max_steps_raises_and_records_failed_trace() -> None:
    tool_response = ChatResponse(
        content="",
        tool_calls=[ToolCall(id="call_x", name="echo", arguments={"text": "x"})],
    )
    llm = FakeLLM([tool_response, tool_response, tool_response])
    registry = ToolRegistry()
    registry.register(EchoTool())
    agent = Agent(llm=llm, registry=registry, max_steps=3)
    recorder = TraceRecorder()

    with pytest.raises(MaxAgentStepsExceededError):
        agent.run("loop forever", recorder=recorder)

    assert recorder.last_trace is not None
    trace = recorder.last_trace
    assert trace.success is False
    assert trace.termination_reason == TerminationReason.MAX_STEPS
    assert trace.total_steps == 3
    assert trace.events[-1].event_type == TraceEventType.AGENT_FAILED


def test_empty_model_response_raises_and_records_failed_trace() -> None:
    llm = FakeLLM([ChatResponse(content="", tool_calls=[])])
    agent = Agent(llm=llm, registry=ToolRegistry(), max_steps=3)
    recorder = TraceRecorder()

    with pytest.raises(InvalidModelResponseError):
        agent.run("Hi", recorder=recorder)

    assert recorder.last_trace is not None
    trace = recorder.last_trace
    assert trace.success is False
    assert trace.termination_reason == TerminationReason.INVALID_MODEL_RESPONSE
    assert trace.events[-1].event_type == TraceEventType.AGENT_FAILED
