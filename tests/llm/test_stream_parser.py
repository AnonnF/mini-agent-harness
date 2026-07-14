import pytest

from mini_agent.exceptions import ModelRequestError
from mini_agent.llm.stream_parser import parse_sse_line


def test_blank_and_comment_ignored() -> None:
    assert parse_sse_line("") is None
    assert parse_sse_line("   ") is None
    assert parse_sse_line(": ping") is None


def test_non_data_line_ignored() -> None:
    assert parse_sse_line("event: message") is None


def test_done_returns_none() -> None:
    assert parse_sse_line("data: [DONE]") is None


def test_text_delta() -> None:
    line = 'data: {"choices":[{"delta":{"content":"Hi"}}]}'
    chunk = parse_sse_line(line)
    assert chunk is not None
    assert chunk.content == "Hi"


def test_missing_content_becomes_empty_string() -> None:
    line = 'data: {"choices":[{"delta":{}}]}'
    chunk = parse_sse_line(line)
    assert chunk is not None
    assert chunk.content == ""


def test_null_content_becomes_empty_string() -> None:
    line = 'data: {"choices":[{"delta":{"content":null}}]}'
    chunk = parse_sse_line(line)
    assert chunk is not None
    assert chunk.content == ""


def test_invalid_json_raises() -> None:
    with pytest.raises(ModelRequestError, match="Invalid stream"):
        parse_sse_line("data: not-json")


def test_invalid_shape_raises() -> None:
    with pytest.raises(ModelRequestError, match="Invalid stream"):
        parse_sse_line('data: {"choices":[]}')
