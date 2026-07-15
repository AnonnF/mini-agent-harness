from pathlib import Path

import pytest

from mini_agent.exceptions import ToolExecutionError
from mini_agent.tools.workspace import resolve_in_workspace


def test_resolve_accepts_relative_path(tmp_path: Path) -> None:
    (tmp_path / "safe.txt").write_text("ok", encoding="utf-8")
    resolved = resolve_in_workspace(tmp_path, "safe.txt")
    assert resolved == (tmp_path / "safe.txt").resolve()


def test_resolve_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ToolExecutionError, match="escapes"):
        resolve_in_workspace(tmp_path, "../outside")


def test_resolve_rejects_absolute_path_outside(tmp_path: Path) -> None:
    with pytest.raises(ToolExecutionError, match="escapes"):
        resolve_in_workspace(tmp_path, "/etc/passwd")


def test_resolve_rejects_sensitive_name(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=1", encoding="utf-8")
    with pytest.raises(ToolExecutionError, match="Sensitive"):
        resolve_in_workspace(tmp_path, ".env")


def test_resolve_dot_means_root(tmp_path: Path) -> None:
    assert resolve_in_workspace(tmp_path, ".") == tmp_path.resolve()
    assert resolve_in_workspace(tmp_path, "  ") == tmp_path.resolve()
