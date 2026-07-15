from pathlib import Path

from pydantic import BaseModel, Field

from mini_agent.exceptions import ToolExecutionError
from mini_agent.tools.workspace import resolve_in_workspace


class ReadFileArgs(BaseModel):
    path: str = Field(
        min_length=1,
        description="Path to a text file relative to the workspace root.",
    )


class ReadFileTool:
    MAX_BYTES = 100_000

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read a UTF-8 text file inside the workspace. "
            f"Rejects files larger than {self.MAX_BYTES} bytes."
        )

    @property
    def parameters_model(self) -> type[BaseModel]:
        return ReadFileArgs

    def execute(self, arguments: BaseModel) -> str:
        args = ReadFileArgs.model_validate(arguments.model_dump())
        target = resolve_in_workspace(self._root, args.path)

        if not target.exists():
            raise ToolExecutionError(f"Path does not exist: {args.path!r}")
        if not target.is_file():
            raise ToolExecutionError(f"Not a file: {args.path!r}")

        size = target.stat().st_size
        if size > self.MAX_BYTES:
            raise ToolExecutionError(
                f"File size exceeds maximum allowed: {args.path!r}"
            )

        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ToolExecutionError("File is not valid UTF-8 text") from exc
