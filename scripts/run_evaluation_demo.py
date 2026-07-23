"""Deterministic evaluation demo (no real API).

Writes JSON + Markdown reports under evals/results/demo/.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from mini_agent.evaluation.models import (
    EvaluationTask,
    TaskCategory,
    TaskDifficulty,
)
from mini_agent.evaluation.report import write_report_json, write_report_markdown
from mini_agent.evaluation.runner import EvaluationRunner
from mini_agent.llm.models import ChatResponse, Message
from mini_agent.tools.base import Tool
from mini_agent.tools.models import ToolCall

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "evals" / "fixtures"
OUT_DIR = REPO_ROOT / "evals" / "results" / "demo"


class ScriptedLLM:
    def __init__(self, responses: list[ChatResponse]) -> None:
        self._responses = list(responses)

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[Tool] | None = None,
    ) -> ChatResponse:
        if not self._responses:
            raise AssertionError("ScriptedLLM ran out of responses")
        return self._responses.pop(0)


def main() -> None:
    tasks = [
        EvaluationTask(
            id="demo_pass_list",
            name="Demo pass",
            category=TaskCategory.LOCATE,
            difficulty=TaskDifficulty.EASY,
            prompt="List files under src and mention main.py",
            workspace_fixture="sample_repository",
            expected_tools=["list_files"],
            expected_keywords=["main.py"],
            max_steps=5,
        ),
        EvaluationTask(
            id="demo_fail_wrong_tool",
            name="Demo fail wrong tool",
            category=TaskCategory.LOCATE,
            difficulty=TaskDifficulty.MEDIUM,
            prompt="Search for ToolRegistry definition",
            workspace_fixture="sample_repository",
            expected_tools=["search_text"],
            expected_keywords=["ToolRegistry"],
            max_steps=5,
        ),
    ]

    llm = ScriptedLLM(
        [
            # task 1
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(id="c1", name="list_files", arguments={"path": "src"})
                ],
            ),
            ChatResponse(content="The entrypoint is main.py"),
            # task 2
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(id="c2", name="read_file", arguments={"path": "README.md"})
                ],
            ),
            ChatResponse(content="I could not find ToolRegistry from README alone."),
        ]
    )

    runner = EvaluationRunner(llm=llm, fixtures_dir=FIXTURES_DIR)
    report = runner.run(tasks)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "report.json"
    md_path = OUT_DIR / "report.md"
    write_report_json(report, json_path)
    write_report_markdown(report, md_path)

    print(f"total={report.total_tasks}")
    print(f"passed={report.passed_count} failed={report.failed_count}")
    print(f"success_rate={report.success_rate:.1%}")
    for item in report.results:
        status = "PASS" if item.passed else "FAIL"
        reasons = ",".join(item.failure_reasons) if item.failure_reasons else "-"
        print(f"  [{status}] {item.task_id} reasons={reasons}")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
