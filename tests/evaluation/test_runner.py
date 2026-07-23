from collections.abc import Sequence
from pathlib import Path

import pytest

from mini_agent.evaluation.models import (
    EvaluationTask,
    TaskCategory,
    TaskDifficulty,
)
from mini_agent.evaluation.runner import EvaluationRunner
from mini_agent.llm.models import ChatResponse, Message
from mini_agent.tools.base import Tool
from mini_agent.tools.models import ToolCall

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "evals" / "fixtures"


class ScriptedLLM:
    """Returns canned responses; scripts keyed by call index across the run."""

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
            raise AssertionError("ScriptedLLM ran out of responses")
        return self._responses.pop(0)


def _task(
    task_id: str,
    *,
    category: TaskCategory = TaskCategory.LOCATE,
    expected_tools: list[str] | None = None,
    expected_keywords: list[str] | None = None,
    max_steps: int = 5,
) -> EvaluationTask:
    return EvaluationTask(
        id=task_id,
        name=task_id,
        category=category,
        difficulty=TaskDifficulty.EASY,
        prompt="List files under src and mention main.py",
        workspace_fixture="sample_repository",
        expected_tools=expected_tools or ["list_files"],
        expected_keywords=expected_keywords or ["main.py"],
        max_steps=max_steps,
    )


def test_runner_empty_task_set() -> None:
    runner = EvaluationRunner(llm=ScriptedLLM([]), fixtures_dir=FIXTURES_DIR)
    report = runner.run([])
    assert report.total_tasks == 0
    assert report.success_rate == 0.0


def test_runner_all_pass_with_scripted_llm() -> None:
    llm = ScriptedLLM(
        [
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(id="c1", name="list_files", arguments={"path": "src"})
                ],
            ),
            ChatResponse(content="The entry file is main.py"),
        ]
    )
    runner = EvaluationRunner(llm=llm, fixtures_dir=FIXTURES_DIR)
    report = runner.run([_task("pass-1")])
    assert report.total_tasks == 1
    assert report.passed_count == 1
    assert report.results[0].run_id is not None
    assert report.results[0].passed is True


def test_runner_continues_after_failure() -> None:
    # First task: model explodes. Second task: succeeds.
    class SwitchingLLM:
        def __init__(self) -> None:
            self.calls = 0

        def complete(
            self,
            messages: Sequence[Message],
            tools: Sequence[Tool] | None = None,
        ) -> ChatResponse:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("boom")
            if self.calls == 2:
                return ChatResponse(
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            name="list_files",
                            arguments={"path": "src"},
                        )
                    ],
                )
            return ChatResponse(content="Found main.py")

    runner = EvaluationRunner(llm=SwitchingLLM(), fixtures_dir=FIXTURES_DIR)
    report = runner.run([_task("fail-1"), _task("pass-2")])
    assert report.total_tasks == 2
    assert report.failed_count == 1
    assert report.passed_count == 1
    assert report.results[0].task_id == "fail-1"
    assert report.results[0].passed is False
    assert report.results[0].error is not None
    assert report.results[1].task_id == "pass-2"
    assert report.results[1].passed is True


def test_runner_category_filter_and_limit() -> None:
    llm = ScriptedLLM(
        [
            ChatResponse(content="Found main.py"),
            ChatResponse(content="Found main.py"),
        ]
    )
    tasks = [
        _task("locate-a", category=TaskCategory.LOCATE, expected_tools=[]),
        _task("safety-a", category=TaskCategory.SAFETY, expected_tools=[]),
        _task("locate-b", category=TaskCategory.LOCATE, expected_tools=[]),
    ]
    runner = EvaluationRunner(llm=llm, fixtures_dir=FIXTURES_DIR)
    report = runner.run(tasks, category=TaskCategory.LOCATE, limit=1)
    assert report.total_tasks == 1
    assert report.results[0].task_id == "locate-a"


def test_runner_keyword_failure() -> None:
    llm = ScriptedLLM(
        [
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(id="c1", name="list_files", arguments={"path": "src"})
                ],
            ),
            ChatResponse(content="I looked around but found nothing"),
        ]
    )
    runner = EvaluationRunner(llm=llm, fixtures_dir=FIXTURES_DIR)
    report = runner.run([_task("kw-miss", expected_keywords=["main.py"])])
    assert report.passed_count == 0
    assert "keyword_match" in report.results[0].failure_reasons


def test_runner_result_order_stable() -> None:
    llm = ScriptedLLM(
        [
            ChatResponse(content="main.py"),
            ChatResponse(content="main.py"),
            ChatResponse(content="main.py"),
        ]
    )
    tasks = [
        _task("z", expected_tools=[]),
        _task("a", expected_tools=[]),
        _task("m", expected_tools=[]),
    ]
    runner = EvaluationRunner(llm=llm, fixtures_dir=FIXTURES_DIR)
    first = runner.run(tasks)
    # Need fresh responses for second run
    runner2 = EvaluationRunner(
        llm=ScriptedLLM(
            [
                ChatResponse(content="main.py"),
                ChatResponse(content="main.py"),
                ChatResponse(content="main.py"),
            ]
        ),
        fixtures_dir=FIXTURES_DIR,
    )
    second = runner2.run(tasks)
    assert [item.task_id for item in first.results] == ["z", "a", "m"]
    assert [item.task_id for item in second.results] == ["z", "a", "m"]


def test_negative_limit_raises() -> None:
    runner = EvaluationRunner(llm=ScriptedLLM([]), fixtures_dir=FIXTURES_DIR)
    with pytest.raises(ValueError):
        runner.run([], limit=-1)
