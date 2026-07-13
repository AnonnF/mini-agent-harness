import pytest
from pydantic import ValidationError

from mini_agent.llm.models import ChatResponse, Message, MessageRole, Usage


def test_create_valid_message() -> None:
    Message(role=MessageRole.SYSTEM, content="You are helpful.")
    Message(role=MessageRole.USER, content="Hi")
    Message(role=MessageRole.ASSISTANT, content="Hello")


def test_invalid_role_rejected() -> None:
    with pytest.raises(ValidationError):
        Message(role="tool", content="x")  # type: ignore[arg-type]


def test_chat_response_with_usage() -> None:
    resp = ChatResponse(content="ok", usage=Usage(total_tokens=10))
    assert resp.content == "ok"
    assert resp.usage is not None


def test_models_have_no_api_key_field() -> None:
    assert "api_key" not in Message.model_fields
