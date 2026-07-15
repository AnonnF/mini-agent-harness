import os
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel, Field

from mini_agent.exceptions import ToolExecutionError
from mini_agent.tools.workspace import SENSITIVE_NAMES, resolve_in_workspace


class SearchTextArgs(BaseModel):
    query: str = Field(min_length=1, description="Substring to search for.")
    path: str = Field(
        default=".",
        description="Workspace-relative path to a file or directory to search.",
    )


class SearchTextTool:
    MAX_MATCHES = 50
    MAX_FILE_BYTES = 1_000_000
    IGNORE_DIR_NAMES = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        "node_modules",
    }

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    @property
    def name(self) -> str:
        return "search_text"

    @property
    def description(self) -> str:
        return (
            "Recursively search UTF-8 text files under a workspace path for a "
            "substring. Skips common cache/dependency directories and binary files."
        )

    @property
    def parameters_model(self) -> type[BaseModel]:
        return SearchTextArgs

    def execute(self, arguments: BaseModel) -> str:
        args = SearchTextArgs.model_validate(arguments.model_dump())
        start = resolve_in_workspace(self._root, args.path)
        if not start.exists():
            raise ToolExecutionError(f"Path does not exist: {args.path!r}")

        matches: list[str] = []
        files = [start] if start.is_file() else list(self._iter_text_files(start))
        root = self._root.resolve()

        for file_path in sorted(files, key=lambda p: p.as_posix()):
            if file_path.name in SENSITIVE_NAMES:
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for line_no, line in enumerate(content.splitlines(), start=1):
                if args.query in line:
                    rel = file_path.relative_to(root).as_posix()
                    matches.append(f"{rel}:{line_no}:{line}")
                    if len(matches) >= self.MAX_MATCHES:
                        return "\n".join(matches)

        return "\n".join(matches) if matches else "No matches found"

    def _iter_text_files(self, root: Path) -> Iterator[Path]:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                name
                for name in dirnames
                if name not in self.IGNORE_DIR_NAMES and not name.startswith(".")
            ]
            for name in filenames:
                fpath = Path(dirpath) / name
                if name in SENSITIVE_NAMES:
                    continue
                try:
                    if (
                        not fpath.is_file()
                        or fpath.stat().st_size > self.MAX_FILE_BYTES
                    ):
                        continue
                except OSError:
                    continue
                yield fpath
