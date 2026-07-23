from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from mini_agent.evaluation.models import (
    EvaluationReport,
    TaskEvaluationResult,
)
from mini_agent.exceptions import EvaluationError


def build_report(results: list[TaskEvaluationResult]) -> EvaluationReport:
    total = len(results)
    passed_count = sum(1 for item in results if item.passed)
    failed_count = total - passed_count
    success_rate = (passed_count / total) if total else 0.0

    by_category: dict[str, list[bool]] = defaultdict(list)
    by_difficulty: dict[str, list[bool]] = defaultdict(list)
    for item in results:
        by_category[item.category.value].append(item.passed)
        by_difficulty[item.difficulty.value].append(item.passed)

    def _rate(values: list[bool]) -> float:
        return (sum(1 for value in values if value) / len(values)) if values else 0.0

    average_steps = sum(item.steps_used for item in results) / total if total else 0.0
    max_steps = max((item.steps_used for item in results), default=0)
    average_duration_ms = (
        sum(item.duration_ms for item in results) / total if total else 0.0
    )

    return EvaluationReport(
        results=list(results),
        total_tasks=total,
        passed_count=passed_count,
        failed_count=failed_count,
        success_rate=success_rate,
        success_rate_by_category={
            key: _rate(values) for key, values in sorted(by_category.items())
        },
        success_rate_by_difficulty={
            key: _rate(values) for key, values in sorted(by_difficulty.items())
        },
        average_steps=average_steps,
        max_steps=max_steps,
        average_duration_ms=average_duration_ms,
        total_model_calls=sum(item.model_call_count for item in results),
        total_tool_calls=sum(item.tool_call_count for item in results),
        failed_task_ids=[item.task_id for item in results if not item.passed],
    )


def report_to_markdown(report: EvaluationReport) -> str:
    lines = [
        "# Evaluation Report",
        "",
        f"- Total tasks: {report.total_tasks}",
        f"- Passed: {report.passed_count}",
        f"- Failed: {report.failed_count}",
        f"- Success rate: {report.success_rate:.1%}",
        f"- Average steps: {report.average_steps:.2f}",
        f"- Max steps: {report.max_steps}",
        f"- Average duration (ms): {report.average_duration_ms:.1f}",
        f"- Total model calls: {report.total_model_calls}",
        f"- Total tool calls: {report.total_tool_calls}",
        "",
        "## Success rate by category",
        "",
    ]
    if report.success_rate_by_category:
        for name, rate in report.success_rate_by_category.items():
            lines.append(f"- {name}: {rate:.1%}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Success rate by difficulty", ""])
    if report.success_rate_by_difficulty:
        for name, rate in report.success_rate_by_difficulty.items():
            lines.append(f"- {name}: {rate:.1%}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Failed tasks", ""])
    if report.failed_task_ids:
        for task_id in report.failed_task_ids:
            lines.append(f"- {task_id}")
    else:
        lines.append("- (none)")

    lines.append("")
    return "\n".join(lines)


def write_report_json(report: EvaluationReport, path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            report.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise EvaluationError(f"Failed to write report JSON: {path}") from exc


def write_report_markdown(report: EvaluationReport, path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report_to_markdown(report), encoding="utf-8")
    except OSError as exc:
        raise EvaluationError(f"Failed to write report Markdown: {path}") from exc
