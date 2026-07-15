from pathlib import Path

import pytest

from mini_agent.exceptions import ToolExecutionError
from mini_agent.tools.read_file import ReadFileArgs, ReadFileTool


def test_read_file_returns_text(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    tool = ReadFileTool(workspace_root=tmp_path)
    assert tool.execute(ReadFileArgs(path="note.txt")) == "hello"


def test_read_file_empty(tmp_path: Path) -> None:
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    tool = ReadFileTool(workspace_root=tmp_path)
    assert tool.execute(ReadFileArgs(path="empty.txt")) == ""


def test_read_file_missing(tmp_path: Path) -> None:
    tool = ReadFileTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="does not exist"):
        tool.execute(ReadFileArgs(path="missing.txt"))


def test_read_file_rejects_directory(tmp_path: Path) -> None:
    (tmp_path / "dir").mkdir()
    tool = ReadFileTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="Not a file"):
        tool.execute(ReadFileArgs(path="dir"))


def test_read_file_rejects_oversized(tmp_path: Path) -> None:
    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * (ReadFileTool.MAX_BYTES + 1))
    tool = ReadFileTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="exceeds"):
        tool.execute(ReadFileArgs(path="big.txt"))


def test_read_file_rejects_sensitive(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=1", encoding="utf-8")
    tool = ReadFileTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="Sensitive"):
        tool.execute(ReadFileArgs(path=".env"))


def test_read_file_rejects_escape(tmp_path: Path) -> None:
    tool = ReadFileTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="escapes"):
        tool.execute(ReadFileArgs(path="../secret.txt"))
