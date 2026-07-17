from collections.abc import Sequence
from pathlib import Path

from mini_agent.agent.loop import Agent
from mini_agent.llm.models import ChatResponse, Message
from mini_agent.tools.base import Tool
from mini_agent.tools.list_files import ListFilesTool
from mini_agent.tools.models import ToolCall
from mini_agent.tools.read_file import ReadFileTool
from mini_agent.tools.registry import ToolRegistry


class FakeLLM:
    def __init__(self, responses: list[ChatResponse]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[Tool] | None = None,
    ) -> ChatResponse:
        self.calls += 1
        if not self._responses:
            raise AssertionError("FakeLLM ran out of responses")
        return self._responses.pop(0)


def test_agent_list_then_read_with_real_tools(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("entry=main", encoding="utf-8")
    registry = ToolRegistry()
    registry.register(ListFilesTool(tmp_path))
    registry.register(ReadFileTool(tmp_path))

    llm = FakeLLM(
        [
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(id="c1", name="list_files", arguments={"path": "."}),
                ],
            ),
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id="c2", name="read_file", arguments={"path": "hello.txt"}
                    ),
                ],
            ),
            ChatResponse(content="The entry hint is main"),
        ]
    )
    agent = Agent(llm=llm, registry=registry, max_steps=5)
    result = agent.run("Where is the entry?")
    assert result.success
    assert "main" in result.final_text

    tool_msgs = [m for m in result.messages if m.role.value == "tool"]
    # 或：from mini_agent.llm.models import MessageRole
    assert any("hello.txt" in m.content for m in tool_msgs)  # list_files 输出
    assert any("entry=main" in m.content for m in tool_msgs)  # read_file 输出
    assert llm.calls == 3
