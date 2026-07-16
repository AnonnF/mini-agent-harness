import json

import httpx
import pytest
from pydantic import BaseModel, Field

from mini_agent.exceptions import ModelRequestError
from mini_agent.llm.deepseek_client import DeepSeekClient
from mini_agent.llm.models import Message, MessageRole
from mini_agent.tools.models import ToolCall


def _make_client(handler, *, max_retries: int = 2) -> DeepSeekClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return DeepSeekClient(
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        timeout=5.0,
        http_client=http_client,
        max_retries=max_retries,
    )


def _user_message(content: str = "Hi") -> Message:
    return Message(role=MessageRole.USER, content=content)


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
    assert resp.tool_calls == []


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


def test_complete_non_object_message_raises() -> None:
    client = _make_client(
        lambda r: httpx.Response(200, json={"choices": [{"message": []}]})
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


def test_complete_retries_on_500_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(500, json={"error": "x"})
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                "usage": None,
            },
        )

    client = _make_client(handler)
    resp = client.complete([_user_message()])
    assert resp.content == "ok"
    assert calls["n"] == 2


def test_complete_401_does_not_retry() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, json={"error": "invalid key"})

    client = _make_client(handler=handler)

    with pytest.raises(ModelRequestError, match="Authentication"):
        client.complete([_user_message()])

    assert calls["n"] == 1


def test_complete_exhausts_retries_on_500() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, json={"error": "internal"})

    client = _make_client(handler, max_retries=2)
    with pytest.raises(ModelRequestError, match="Server error"):
        client.complete([_user_message()])

    assert calls["n"] == 3


def test_complete_max_retries_zero_does_not_retry() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, json={"error": "internal"})

    client = _make_client(handler, max_retries=0)
    with pytest.raises(ModelRequestError, match="Server error"):
        client.complete([_user_message()])

    assert calls["n"] == 1


def test_complete_sends_tools_in_request_body() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    client = _make_client(handler)
    client.complete([_user_message()], tools=[EchoTool()])

    body = captured["body"]
    assert "tools" in body
    assert body["tool_choice"] == "auto"
    assert body["tools"][0]["function"]["name"] == "echo"


def test_complete_without_tools_omits_tools_field() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    client = _make_client(handler)
    client.complete([_user_message()])

    assert "tools" not in captured["body"]


def test_complete_parses_tool_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "echo",
                                        "arguments": '{"text": "hi"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    client = _make_client(handler)
    resp = client.complete([_user_message()], tools=[EchoTool()])

    assert resp.content == ""
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].id == "call_1"
    assert resp.tool_calls[0].name == "echo"
    assert resp.tool_calls[0].arguments == {"text": "hi"}


def test_complete_invalid_tool_arguments_json_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "echo",
                                        "arguments": "{not-json",
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    client = _make_client(handler)
    with pytest.raises(ModelRequestError, match="Invalid tool call arguments JSON"):
        client.complete([_user_message()], tools=[EchoTool()])


def test_complete_sends_tool_result_message() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "done"}}]},
        )

    messages = [
        _user_message("list files"),
        Message(
            role=MessageRole.ASSISTANT,
            content="",
            tool_calls=[ToolCall(id="call_1", name="echo", arguments={"text": "x"})],
        ),
        Message(role=MessageRole.TOOL, content="x", tool_call_id="call_1"),
    ]
    client = _make_client(handler)
    client.complete(messages)

    api_messages = captured["body"]["messages"]
    assert api_messages[-1]["role"] == "tool"
    assert api_messages[-1]["tool_call_id"] == "call_1"
    assert api_messages[1]["tool_calls"][0]["id"] == "call_1"
