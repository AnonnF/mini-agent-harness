import pytest
from pydantic import BaseModel, Field

from mini_agent.exceptions import ModelRequestError
from mini_agent.llm.tool_schema import parse_tool_calls, tool_to_openai_tool


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


def test_tool_to_openai_tool_schema() -> None:
    schema = tool_to_openai_tool(EchoTool())
    assert schema["type"] == "function"
    function = schema["function"]
    assert isinstance(function, dict)
    assert function["name"] == "echo"
    assert function["description"] == "Echo text"
    assert "parameters" in function


def test_parse_tool_calls_valid() -> None:
    calls = parse_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "echo",
                    "arguments": '{"text": "hi"}',
                },
            }
        ]
    )
    assert len(calls) == 1
    assert calls[0].id == "call_1"
    assert calls[0].name == "echo"
    assert calls[0].arguments == {"text": "hi"}


def test_parse_tool_calls_empty_arguments() -> None:
    calls = parse_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "echo", "arguments": "{}"},
            }
        ]
    )
    assert calls[0].arguments == {}


def test_parse_tool_calls_invalid_json_raises() -> None:
    with pytest.raises(ModelRequestError, match="Invalid tool call arguments JSON"):
        parse_tool_calls(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "echo", "arguments": "{bad"},
                }
            ]
        )


def test_parse_tool_calls_missing_id_raises() -> None:
    with pytest.raises(ModelRequestError, match="missing id"):
        parse_tool_calls(
            [
                {
                    "type": "function",
                    "function": {"name": "echo", "arguments": "{}"},
                }
            ]
        )


def test_parse_tool_calls_missing_name_raises() -> None:
    with pytest.raises(ModelRequestError, match="missing name"):
        parse_tool_calls(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"arguments": "{}"},
                }
            ]
        )


def test_parse_tool_calls_none_returns_empty() -> None:
    assert parse_tool_calls(None) == []
