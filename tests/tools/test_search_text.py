from pathlib import Path

import pytest

from mini_agent.exceptions import ToolExecutionError
from mini_agent.tools.search_text import SearchTextArgs, SearchTextTool


def test_search_text_finds_match(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("hello world\n", encoding="utf-8")
    tool = SearchTextTool(workspace_root=tmp_path)
    result = tool.execute(SearchTextArgs(query="hello", path="."))
    assert result == "a.py:1:hello world"


def test_search_text_no_matches(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("hello\n", encoding="utf-8")
    tool = SearchTextTool(workspace_root=tmp_path)
    assert tool.execute(SearchTextArgs(query="missing", path=".")) == "No matches found"


def test_search_text_skips_ignored_dirs(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("findme\n", encoding="utf-8")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "pkg.py").write_text("findme\n", encoding="utf-8")

    tool = SearchTextTool(workspace_root=tmp_path)
    result = tool.execute(SearchTextArgs(query="findme", path="."))
    assert result == "src/app.py:1:findme"


def test_search_text_skips_sensitive_files(tmp_path: Path) -> None:
    (tmp_path / "ok.txt").write_text("secret-token\n", encoding="utf-8")
    (tmp_path / ".env").write_text("secret-token\n", encoding="utf-8")

    tool = SearchTextTool(workspace_root=tmp_path)
    result = tool.execute(SearchTextArgs(query="secret-token", path="."))
    assert result == "ok.txt:1:secret-token"


def test_search_text_respects_max_matches(tmp_path: Path) -> None:
    lines = "\n".join(f"hit {i}" for i in range(SearchTextTool.MAX_MATCHES + 10))
    (tmp_path / "many.txt").write_text(lines + "\n", encoding="utf-8")

    tool = SearchTextTool(workspace_root=tmp_path)
    result = tool.execute(SearchTextArgs(query="hit", path="."))
    assert len(result.splitlines()) == SearchTextTool.MAX_MATCHES


def test_search_text_rejects_escape(tmp_path: Path) -> None:
    tool = SearchTextTool(workspace_root=tmp_path)
    with pytest.raises(ToolExecutionError, match="escapes"):
        tool.execute(SearchTextArgs(query="x", path="../"))
