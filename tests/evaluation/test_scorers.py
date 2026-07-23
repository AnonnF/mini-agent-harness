from datetime import UTC, datetime

from mini_agent.agent.models import AgentResult, AgentStopReason
from mini_agent.evaluation.models import (
    EvaluationTask,
    TaskCategory,
    TaskDifficulty,
)
from mini_agent.evaluation.scorers import (
    overall_passed,
    score_execution_success,
    score_expected_tools,
    score_forbidden_tools,
    score_keyword_match,
    score_safety,
    score_step_limit,
    score_task,
    tools_used,
)
from mini_agent.tracing.models import (
    AgentTrace,
    TerminationReason,
    TraceEvent,
    TraceEventType,
)


def _task(**overrides: object) -> EvaluationTask:
    payload: dict[str, object] = {
        "id": "t1",
        "name": "Demo",
        "category": TaskCategory.LOCATE,
        "difficulty": TaskDifficulty.EASY,
        "prompt": "hello",
        "workspace_fixture": "sample_repository",
        "expected_tools": [],
        "forbidden_tools": [],
        "expected_keywords": [],
        "max_steps": 5,
    }
    payload.update(overrides)
    return EvaluationTask.model_validate(payload)


def _trace(
    *, tool_names: list[str] | None = None, final_output: str = ""
) -> AgentTrace:
    now = datetime.now(UTC)
    events: list[TraceEvent] = []
    sequence = 0
    for name in tool_names or []:
        events.append(
            TraceEvent(
                sequence=sequence,
                step=1,
                event_type=TraceEventType.TOOL_CALL,
                started_at=now,
                finished_at=now,
                success=True,
                metadata={"tool_name": name, "tool_call_id": f"c-{sequence}"},
            )
        )
        sequence += 1
    return AgentTrace(
        run_id="run-1",
        input_text="hello",
        started_at=now,
        finished_at=now,
        duration_ms=1,
        events=events,
        final_output=final_output,
        success=True,
        termination_reason=TerminationReason.FINAL_ANSWER,
        total_steps=1,
        model_call_count=1,
        tool_call_count=len(tool_names or []),
    )


def test_tools_used_extracts_names() -> None:
    trace = _trace(tool_names=["list_files", "read_file"])
    assert tools_used(trace) == {"list_files", "read_file"}


def test_execution_success_requires_result() -> None:
    assert score_execution_success(None, error="boom") is False
    result = AgentResult(
        success=True,
        final_text="ok",
        steps_used=1,
        stop_reason=AgentStopReason.FINAL_ANSWER,
    )
    assert score_execution_success(result) is True


def test_expected_tools_subset() -> None:
    task = _task(expected_tools=["list_files", "read_file"])
    assert score_expected_tools(task, _trace(tool_names=["list_files"])) is False
    assert (
        score_expected_tools(
            task, _trace(tool_names=["list_files", "read_file", "search_text"])
        )
        is True
    )


def test_forbidden_tools() -> None:
    task = _task(forbidden_tools=["search_text"])
    assert score_forbidden_tools(task, _trace(tool_names=["list_files"])) is True
    assert score_forbidden_tools(task, _trace(tool_names=["search_text"])) is False


def test_keyword_match_any() -> None:
    task = _task(expected_keywords=["main.py", "config.py"])
    assert score_keyword_match(task, final_text="Found main.py") is True
    assert score_keyword_match(task, final_text="nothing useful") is False


def test_step_limit() -> None:
    task = _task(max_steps=3)
    assert score_step_limit(task, steps_used=3) is True
    assert score_step_limit(task, steps_used=4) is False


def test_safety_blocks_secret_leak() -> None:
    task = _task(category=TaskCategory.SAFETY)
    assert (
        score_safety(
            task,
            final_text="denied sensitive access",
            trace=None,
        )
        is True
    )
    assert (
        score_safety(
            task,
            final_text="Here is DEMO_API_KEY=oops",
            trace=None,
        )
        is False
    )


def test_score_task_overall_and_reasons() -> None:
    task = _task(
        expected_tools=["list_files"],
        expected_keywords=["main.py"],
        max_steps=2,
    )
    result = AgentResult(
        success=True,
        final_text="entry is main.py",
        steps_used=1,
        stop_reason=AgentStopReason.FINAL_ANSWER,
    )
    scores, reasons = score_task(
        task,
        result=result,
        trace=_trace(tool_names=["list_files"], final_output="entry is main.py"),
    )
    assert overall_passed(scores) is True
    assert reasons == []


def test_non_safety_category_skips_safety_checks() -> None:
    task = _task(category=TaskCategory.LOCATE)
    assert score_safety(task, final_text="DEMO_API_KEY", trace=None) is True
