import pytest
from pydantic import BaseModel, Field

from mini_agent.exceptions import ToolRegistryError
from mini_agent.tools.registry import ToolRegistry


class EchoArgs(BaseModel):
    text: str = Field(min_length=1)


class ShowArgs(BaseModel):
    text: str = Field(min_length=1)


class EchoTool:
    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "Echo the input text"

    @property
    def parameters_model(self) -> type[BaseModel]:
        return EchoArgs

    def execute(self, arguments: BaseModel) -> str:
        args = EchoArgs.model_validate(arguments.model_dump())
        return args.text


class ShowTool:
    @property
    def name(self) -> str:
        return "show"

    @property
    def description(self) -> str:
        return "Show the input text"

    @property
    def parameters_model(self) -> type[BaseModel]:
        return ShowArgs

    def execute(self, arguments: BaseModel) -> str:
        args = ShowArgs.model_validate(arguments.model_dump())
        return args.text


class EmptyNameTool(EchoTool):
    @property
    def name(self) -> str:
        return ""


def test_register_and_get_tool() -> None:
    registry = ToolRegistry()
    tool = EchoTool()

    registry.register(tool=tool)
    found = registry.get("echo")

    assert found is tool
    assert found.name == "echo"


def test_get_missing_tool_raises() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolRegistryError):
        registry.get("echo")


def test_list_tools() -> None:
    registry = ToolRegistry()
    tool1 = EchoTool()
    tool2 = ShowTool()

    registry.register(tool=tool1)
    registry.register(tool=tool2)

    result = registry.list_tools()

    assert tool1 in result and tool2 in result


def test_duplicate_name() -> None:
    registry = ToolRegistry()
    tool = EchoTool()

    registry.register(tool=tool)

    with pytest.raises(ToolRegistryError):
        registry.register(tool=tool)


def test_register_empty_name() -> None:
    registry = ToolRegistry()
    tool = EmptyNameTool()

    with pytest.raises(ToolRegistryError):
        registry.register(tool=tool)
