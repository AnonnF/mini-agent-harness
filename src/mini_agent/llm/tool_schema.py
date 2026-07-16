"""Convert between internal Tool types and OpenAI-compatible tool schemas."""

from __future__ import annotations

import json
from typing import Any

from mini_agent.exceptions import ModelRequestError
from mini_agent.tools.base import Tool
from mini_agent.tools.models import ToolCall


def tool_to_openai_tool(tool: Tool) -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters_model.model_json_schema(),
        },
    }


def parse_tool_calls(raw_tool_calls: Any) -> list[ToolCall]:
    if raw_tool_calls is None:
        return []
    if not isinstance(raw_tool_calls, list):
        raise ModelRequestError("Invalid tool_calls format")

    result: list[ToolCall] = []
    for item in raw_tool_calls:
        if not isinstance(item, dict):
            raise ModelRequestError("Invalid tool_calls format")
        call_id = item.get("id")
        function = item.get("function")
        if not isinstance(call_id, str) or not call_id:
            raise ModelRequestError("Tool call missing id")
        if not isinstance(function, dict):
            raise ModelRequestError("Tool call missing function")
        name = function.get("name")
        if not isinstance(name, str) or not name:
            raise ModelRequestError("Tool call missing name")

        raw_args = function.get("arguments", "{}")
        if raw_args is None or raw_args == "":
            raw_args = "{}"
        if not isinstance(raw_args, str):
            raise ModelRequestError("Tool call arguments must be a JSON string")
        try:
            parsed = json.loads(raw_args)
        except json.JSONDecodeError as exc:
            raise ModelRequestError("Invalid tool call arguments JSON") from exc
        if not isinstance(parsed, dict):
            raise ModelRequestError("Tool call arguments must be a JSON object")

        result.append(ToolCall(id=call_id, name=name, arguments=parsed))

    return result
