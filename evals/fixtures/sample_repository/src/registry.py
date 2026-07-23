"""Minimal tool registry used by the sample app."""

from exceptions import RegistryError


class ToolRegistry:
    """Registers and looks up tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, str] = {}

    def register(self, name: str, description: str) -> None:
        if not name:
            raise RegistryError("tool name must not be empty")
        if name in self._tools:
            raise RegistryError(f"duplicate tool: {name}")
        self._tools[name] = description

    def get(self, name: str) -> str:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise RegistryError(f"unknown tool: {name}") from exc

    def list_names(self) -> list[str]:
        return sorted(self._tools)
