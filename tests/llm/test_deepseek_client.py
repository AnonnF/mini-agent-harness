import httpx
import pytest

from mini_agent.exceptions import ModelRequestError
from mini_agent.llm.deepseek_client import DeepSeekClient
from mini_agent.llm.models import Message, MessageRole


def _make_client(handler) -> DeepSeekClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return DeepSeekClient(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        timeout=5.0,
        http_client=http_client,
    )


def test_complete_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "Hello"}}],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 2,
                    "total_tokens": 3,
                },
            },
        )

    client = _make_client(handler)
    resp = client.complete([Message(role=MessageRole.USER, content="Hi")])

    assert resp.content == "Hello"
    assert resp.usage is not None
    assert resp.usage.total_tokens == 3


def test_complete_empty_messages_raises() -> None:
    client = _make_client(lambda r: httpx.Response(200, json={}))
    with pytest.raises(ModelRequestError):
        client.complete([])


def test_complete_401_raises() -> None:
    client = _make_client(lambda r: httpx.Response(401, json={"error": "invalid key"}))
    with pytest.raises(ModelRequestError, match="Authentication"):
        client.complete([Message(role=MessageRole.USER, content="Hi")])


def test_api_key_not_in_error_message() -> None:
    secret = "super-secret-key"
    client = DeepSeekClient(
        api_key=secret,
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        timeout=5.0,
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(401, json={}))
        ),
    )
    with pytest.raises(ModelRequestError) as exc_info:
        client.complete([Message(role=MessageRole.USER, content="Hi")])
    assert secret not in str(exc_info.value)
