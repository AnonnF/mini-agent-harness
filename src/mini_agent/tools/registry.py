from mini_agent.exceptions import ToolRegistryError
from mini_agent.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ToolRegistryError("Cannot register tool with no name")
        if tool.name in self._tools.keys():
            raise ToolRegistryError(f"Tool name {tool.name} already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolRegistryError(f"Tool name {name} not found")
        return self._tools[name]

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())
