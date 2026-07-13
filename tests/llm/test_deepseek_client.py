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


def _user_message(content: str = "Hi") -> Message:
    return Message(role=MessageRole.USER, content=content)


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


def test_complete_429_raises() -> None:
    client = _make_client(lambda r: httpx.Response(429, json={"error": "rate limit"}))
    with pytest.raises(ModelRequestError, match="Rate limited"):
        client.complete([_user_message()])


def test_complete_500_raises() -> None:
    client = _make_client(lambda r: httpx.Response(500, json={"error": "internal"}))
    with pytest.raises(ModelRequestError, match="Server error"):
        client.complete([_user_message()])


def test_complete_timeout_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    client = _make_client(handler)
    with pytest.raises(ModelRequestError, match="(?i)timeout"):
        client.complete([_user_message()])


def test_complete_connection_error_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    client = _make_client(handler)
    with pytest.raises(ModelRequestError, match="Network error"):
        client.complete([_user_message()])


def test_complete_invalid_json_raises() -> None:
    client = _make_client(lambda r: httpx.Response(200, content=b"not-json"))
    with pytest.raises(ModelRequestError, match="Invalid JSON"):
        client.complete([_user_message()])


def test_complete_missing_content_raises() -> None:
    client = _make_client(
        lambda r: httpx.Response(200, json={"choices": [{"message": {}}]})
    )
    with pytest.raises(ModelRequestError, match="Invalid response format"):
        client.complete([_user_message()])


def test_complete_other_4xx_raises() -> None:
    client = _make_client(lambda r: httpx.Response(400, json={"error": "bad request"}))
    with pytest.raises(ModelRequestError, match="status 400"):
        client.complete([_user_message()])

@pytest.mark.anyio
async def test_stream_success() -> None:
    sse = (
        'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sse)
    transport = httpx.MockTransport(handler)
    client = DeepSeekClient(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        timeout=5.0,
        async_http_client=httpx.AsyncClient(transport=transport),
    )
    chunks = []
    async for chunk in client.stream([_user_message()]):
        chunks.append(chunk.content)
    assert chunks == ["Hel", "lo"]