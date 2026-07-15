from pathlib import Path

from pydantic import BaseModel, Field

from mini_agent.exceptions import ToolExecutionError
from mini_agent.tools.workspace import resolve_in_workspace


class ListFilesArgs(BaseModel):
    path: str = Field(
        default=".",
        description=(
            "Path relative to the workspace root; defaults to the workspace root."
        ),
    )


class ListFilesTool:
    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return (
            "List files and directories one level under a workspace path. "
            "Does not recurse."
        )

    @property
    def parameters_model(self) -> type[BaseModel]:
        return ListFilesArgs

    def execute(self, arguments: BaseModel) -> str:
        args = ListFilesArgs.model_validate(arguments.model_dump())
        target = resolve_in_workspace(self._root, args.path)
        if not target.exists():
            raise ToolExecutionError(f"Path does not exist: {args.path!r}")
        if not target.is_dir():
            raise ToolExecutionError(f"Not a directory: {args.path!r}")

        root = self._root.resolve()
        lines: list[str] = []
        for entry in sorted(target.iterdir(), key=lambda p: p.name.lower()):
            rel = entry.relative_to(root).as_posix()
            lines.append(f"{rel}/" if entry.is_dir() else rel)

        return "\n".join(lines) if lines else "(empty)"
