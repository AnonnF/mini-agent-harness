"""Generate reproducible badcase traces with ScriptedLLM + real tools.

Run from repo root (package installed editable):

    python scripts/generate_badcase_artifacts.py
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from mini_agent.agent.loop import Agent
from mini_agent.evaluation.models import (
    EvaluationTask,
    TaskCategory,
    TaskDifficulty,
)
from mini_agent.evaluation.scorers import overall_passed, score_task
from mini_agent.llm.models import ChatResponse, Message
from mini_agent.tools.base import Tool
from mini_agent.tools.list_files import ListFilesTool
from mini_agent.tools.models import ToolCall
from mini_agent.tools.read_file import ReadFileTool
from mini_agent.tools.registry import ToolRegistry
from mini_agent.tools.search_text import SearchTextTool
from mini_agent.tracing.recorder import TraceRecorder

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "evals" / "fixtures" / "sample_repository"
OUT_DIR = REPO_ROOT / "evals" / "results" / "badcases"


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


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ListFilesTool(FIXTURE))
    registry.register(ReadFileTool(FIXTURE))
    registry.register(SearchTextTool(FIXTURE))
    return registry


def _run(
    *,
    task: EvaluationTask,
    responses: list[ChatResponse],
) -> dict[str, object]:
    recorder = TraceRecorder()
    agent = Agent(
        llm=ScriptedLLM(responses),
        registry=_registry(),
        max_steps=task.max_steps,
    )
    error: str | None = None
    result = None
    try:
        result = agent.run(task.prompt, recorder=recorder, task_id=task.id)
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"

    trace = recorder.last_trace
    scores, reasons = score_task(task, result=result, trace=trace, error=error)
    return {
        "task": task.model_dump(mode="json"),
        "error": error,
        "passed": overall_passed(scores),
        "scores": scores.model_dump(mode="json"),
        "failure_reasons": reasons,
        "final_text": result.final_text if result is not None else "",
        "trace": trace.model_dump(mode="json") if trace is not None else None,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    scenarios: list[tuple[str, EvaluationTask, list[ChatResponse]]] = [
        (
            "bc1_repeated_list_files",
            EvaluationTask(
                id="bc1_repeated_list_files",
                name="Repeated list_files",
                category=TaskCategory.LOCATE,
                difficulty=TaskDifficulty.EASY,
                prompt="List Python files under src.",
                workspace_fixture="sample_repository",
                expected_tools=["list_files"],
                expected_keywords=["main.py"],
                max_steps=6,
            ),
            [
                ChatResponse(
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            name="list_files",
                            arguments={"path": "src"},
                        )
                    ],
                ),
                ChatResponse(
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="c2",
                            name="list_files",
                            arguments={"path": "src"},
                        )
                    ],
                ),
                ChatResponse(
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="c3",
                            name="list_files",
                            arguments={"path": "src"},
                        )
                    ],
                ),
                ChatResponse(content="Under src I see main.py and other modules."),
            ],
        ),
        (
            "bc2_wrong_tool_choice",
            EvaluationTask(
                id="bc2_wrong_tool_choice",
                name="Wrong tool choice",
                category=TaskCategory.LOCATE,
                difficulty=TaskDifficulty.MEDIUM,
                prompt="Find where ToolRegistry is defined using search.",
                workspace_fixture="sample_repository",
                expected_tools=["search_text"],
                expected_keywords=["registry.py", "ToolRegistry"],
                max_steps=6,
            ),
            [
                ChatResponse(
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            name="read_file",
                            arguments={"path": "README.md"},
                        )
                    ],
                ),
                ChatResponse(
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="c2",
                            name="read_file",
                            arguments={"path": "src/main.py"},
                        )
                    ],
                ),
                ChatResponse(
                    content=(
                        "It seems related to tools, but I could not "
                        "locate ToolRegistry."
                    )
                ),
            ],
        ),
        (
            "bc3_keyword_false_positive",
            EvaluationTask(
                id="bc3_keyword_false_positive",
                name="Keyword false positive",
                category=TaskCategory.FAILURE,
                difficulty=TaskDifficulty.EASY,
                prompt="Search for definitely_missing_function_xyz.",
                workspace_fixture="sample_repository",
                expected_tools=["search_text"],
                expected_keywords=["no", "not found", "0"],
                max_steps=5,
            ),
            [
                ChatResponse(
                    content="",
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            name="search_text",
                            arguments={
                                "query": "definitely_missing_function_xyz",
                                "path": ".",
                            },
                        )
                    ],
                ),
                # "no" inside "know"/"another" caused a false pass before the fix.
                ChatResponse(
                    content=(
                        "I know another approach might help, "
                        "but results look unclear."
                    )
                ),
            ],
        ),
    ]

    index: list[dict[str, object]] = []
    for filename, task, responses in scenarios:
        artifact = _run(task=task, responses=responses)
        path = OUT_DIR / f"{filename}.json"
        path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
        trace = artifact["trace"]
        run_id = trace.get("run_id") if isinstance(trace, dict) else None
        index.append(
            {
                "file": path.name,
                "task_id": task.id,
                "passed": artifact["passed"],
                "failure_reasons": artifact["failure_reasons"],
                "run_id": run_id,
            }
        )
        print(f"wrote {path}")

    (OUT_DIR / "index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUT_DIR / 'index.json'}")


if __name__ == "__main__":
    main()
