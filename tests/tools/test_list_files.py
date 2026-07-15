from pathlib import Path

import pytest

from mini_agent.exceptions import ToolExecutionError
from mini_agent.tools.list_files import ListFilesArgs, ListFilesTool


def test_list_files_one_level_sorted(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "sub").mkdir()

    tool = ListFilesTool(workspace_root=tmp_path)
    result = tool.execute(ListFilesArgs(path="."))

    assert result.splitlines() == ["a.txt", "b.txt", "sub/"]


def test_list_files_empty_directory(tmp_path: Path) -> None:
    tool = ListFilesTool(workspace_root=tmp_path)
    assert tool.execute(ListFilesArgs(path=".")) == "(empty)"


def test_list_files_missing_path(tmp_path: Path) -> None:
    tool = ListFilesTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="does not exist"):
        tool.execute(ListFilesArgs(path="missing"))


def test_list_files_rejects_file_path(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    tool = ListFilesTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="Not a directory"):
        tool.execute(ListFilesArgs(path="a.txt"))


def test_list_files_rejects_escape(tmp_path: Path) -> None:
    tool = ListFilesTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="escapes"):
        tool.execute(ListFilesArgs(path="../"))
