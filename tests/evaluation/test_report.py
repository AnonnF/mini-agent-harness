from pathlib import Path

from mini_agent.evaluation.models import (
    ScoreBreakdown,
    TaskCategory,
    TaskDifficulty,
    TaskEvaluationResult,
)
from mini_agent.evaluation.report import (
    build_report,
    report_to_markdown,
    write_report_json,
    write_report_markdown,
)


def _result(
    task_id: str,
    *,
    passed: bool,
    category: TaskCategory = TaskCategory.LOCATE,
    difficulty: TaskDifficulty = TaskDifficulty.EASY,
    steps: int = 1,
) -> TaskEvaluationResult:
    scores = ScoreBreakdown(
        execution_success=passed,
        expected_tools=True,
        forbidden_tools=True,
        keyword_match=passed,
        step_limit=True,
        safety=True,
    )
    return TaskEvaluationResult(
        task_id=task_id,
        category=category,
        difficulty=difficulty,
        passed=passed,
        scores=scores,
        steps_used=steps,
        duration_ms=10,
        model_call_count=1,
        tool_call_count=1,
    )


def test_build_report_aggregates() -> None:
    results = [
        _result("a", passed=True, category=TaskCategory.LOCATE, steps=2),
        _result("b", passed=False, category=TaskCategory.SAFETY, steps=4),
        _result(
            "c",
            passed=True,
            category=TaskCategory.LOCATE,
            difficulty=TaskDifficulty.HARD,
            steps=1,
        ),
    ]
    report = build_report(results)
    assert report.total_tasks == 3
    assert report.passed_count == 2
    assert report.failed_count == 1
    assert report.failed_task_ids == ["b"]
    assert report.max_steps == 4
    assert report.success_rate_by_category["locate"] == 1.0
    assert report.success_rate_by_category["safety"] == 0.0


def test_empty_report() -> None:
    report = build_report([])
    assert report.total_tasks == 0
    assert report.success_rate == 0.0
    assert report.failed_task_ids == []


def test_markdown_and_json_writers(tmp_path: Path) -> None:
    report = build_report(
        [
            _result("ok", passed=True),
            _result("bad", passed=False),
        ]
    )
    md = report_to_markdown(report)
    assert "Evaluation Report" in md
    assert "bad" in md

    json_path = tmp_path / "out" / "report.json"
    md_path = tmp_path / "out" / "report.md"
    write_report_json(report, json_path)
    write_report_markdown(report, md_path)
    assert json_path.is_file()
    assert md_path.is_file()
    assert "ok" in json_path.read_text(encoding="utf-8")
