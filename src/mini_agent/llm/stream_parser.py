# 返回值语义：
# - str: 文本增量（可以是 ""）
# - 特殊 sentinel: 流结束 [DONE]
# - None: 忽略此行（空行、注释行等）
# - 非法 JSON/结构 → raise ModelRequestError

import json

from mini_agent.exceptions import ModelRequestError
from mini_agent.llm.models import StreamChunk


def parse_sse_line(line: str) -> StreamChunk | None:
    line = line.strip()
    if not line or line.startswith(":"):
        return None
    if not line.startswith("data:"):
        return None

    payload = line.removeprefix("data:").strip()
    if payload == "[DONE]":
        return None

    chunk, _is_done = parse_data_payload(payload=payload)
    return chunk


def parse_data_payload(payload: str) -> tuple[StreamChunk | None, bool]:
    """Returns (chunk, is_done). is_done=True means stream finished."""
    if payload == "[DONE]":
        return None, True

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ModelRequestError("Invalid stream event") from exc

    try:
        delta = data["choices"][0]["delta"]
        content = delta.get("content", "")
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelRequestError("Invalid stream event format") from exc

    if content is None:
        content = ""
    if not isinstance(content, str):
        raise ModelRequestError("Invalid stream event format")

    return StreamChunk(content=content), False
