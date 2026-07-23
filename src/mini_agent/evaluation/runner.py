from __future__ import annotations

from pathlib import Path

from mini_agent.agent.loop import Agent
from mini_agent.agent.models import AgentResult
from mini_agent.evaluation.loader import resolve_fixture_path
from mini_agent.evaluation.models import (
    EvaluationReport,
    EvaluationTask,
    TaskCategory,
    TaskEvaluationResult,
)
from mini_agent.evaluation.report import build_report
from mini_agent.evaluation.scorers import overall_passed, score_task
from mini_agent.llm.base import LLMClient
from mini_agent.tools.list_files import ListFilesTool
from mini_agent.tools.read_file import ReadFileTool
from mini_agent.tools.registry import ToolRegistry
from mini_agent.tools.search_text import SearchTextTool
from mini_agent.tracing.models import AgentTrace
from mini_agent.tracing.recorder import TraceRecorder


class EvaluationRunner:
    def __init__(
        self,
        *,
        llm: LLMClient,
        fixtures_dir: Path,
        system_prompt: str | None = None,
    ) -> None:
        self._llm = llm
        self._fixtures_dir = fixtures_dir
        self._system_prompt = system_prompt

    def run(
        self,
        tasks: list[EvaluationTask],
        *,
        limit: int | None = None,
        category: TaskCategory | None = None,
    ) -> EvaluationReport:
        selected = list(tasks)
        if category is not None:
            selected = [task for task in selected if task.category == category]
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be >= 0")
            selected = selected[:limit]

        results: list[TaskEvaluationResult] = []
        for task in selected:
            results.append(self._run_one(task))
        return build_report(results)

    def _build_agent(self, task: EvaluationTask) -> Agent:
        workspace = resolve_fixture_path(
            task.workspace_fixture,
            fixtures_dir=self._fixtures_dir,
        )
        registry = ToolRegistry()
        registry.register(ListFilesTool(workspace))
        registry.register(ReadFileTool(workspace))
        registry.register(SearchTextTool(workspace))
        return Agent(
            llm=self._llm,
            registry=registry,
            max_steps=task.max_steps,
        )

    def _run_one(self, task: EvaluationTask) -> TaskEvaluationResult:
        recorder = TraceRecorder()
        agent = self._build_agent(task)
        result: AgentResult | None = None
        error: str | None = None

        try:
            result = agent.run(
                task.prompt,
                system_prompt=self._system_prompt,
                recorder=recorder,
                task_id=task.id,
            )
        except Exception as exc:  # noqa: BLE001 - isolate tasks in evaluation
            error = f"{type(exc).__name__}: {exc}"

        trace: AgentTrace | None = recorder.last_trace
        scores, failure_reasons = score_task(
            task,
            result=result,
            trace=trace,
            error=error,
        )
        passed = overall_passed(scores)

        steps_used = (
            result.steps_used
            if result is not None
            else (trace.total_steps if trace is not None else 0)
        )
        final_text = (
            result.final_text
            if result is not None
            else (trace.final_output if trace is not None else "")
        )

        return TaskEvaluationResult(
            task_id=task.id,
            category=task.category,
            difficulty=task.difficulty,
            passed=passed,
            scores=scores,
            run_id=trace.run_id if trace is not None else None,
            steps_used=steps_used,
            duration_ms=trace.duration_ms if trace is not None else 0,
            model_call_count=(trace.model_call_count if trace is not None else 0),
            tool_call_count=trace.tool_call_count if trace is not None else 0,
            final_text=final_text,
            error=error,
            failure_reasons=failure_reasons,
        )
