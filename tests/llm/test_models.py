import pytest
from pydantic import ValidationError

from mini_agent.llm.models import ChatResponse, Message, MessageRole, Usage
from mini_agent.tools.models import ToolCall


def test_create_valid_message() -> None:
    Message(role=MessageRole.SYSTEM, content="You are helpful.")
    Message(role=MessageRole.USER, content="Hi")
    Message(role=MessageRole.ASSISTANT, content="Hello")


def test_assistant_tool_call_message_allows_empty_content() -> None:
    msg = Message(
        role=MessageRole.ASSISTANT,
        content="",
        tool_calls=[ToolCall(id="call_1", name="echo", arguments={"text": "x"})],
    )
    assert msg.content == ""
    assert msg.tool_calls is not None
    assert msg.tool_calls[0].name == "echo"


def test_tool_result_message() -> None:
    msg = Message(role=MessageRole.TOOL, content="result", tool_call_id="call_1")
    assert msg.role == MessageRole.TOOL
    assert msg.tool_call_id == "call_1"


def test_invalid_role_rejected() -> None:
    with pytest.raises(ValidationError):
        Message(role="foo", content="x")  # type: ignore[arg-type]


def test_chat_response_with_usage() -> None:
    resp = ChatResponse(content="ok", usage=Usage(total_tokens=10))
    assert resp.content == "ok"
    assert resp.usage is not None
    assert resp.tool_calls == []


def test_models_have_no_api_key_field() -> None:
    assert "api_key" not in Message.model_fields
