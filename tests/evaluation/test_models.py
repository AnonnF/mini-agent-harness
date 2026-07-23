from pathlib import Path

import pytest
from pydantic import ValidationError

from mini_agent.evaluation.models import (
    EvaluationTask,
    TaskCategory,
    TaskDifficulty,
)


def test_create_valid_task() -> None:
    task = EvaluationTask(
        id="t1",
        name="Demo",
        category=TaskCategory.LOCATE,
        difficulty=TaskDifficulty.EASY,
        prompt="List files under src",
        workspace_fixture="sample_repository",
        expected_tools=["list_files"],
        expected_keywords=["main.py"],
        max_steps=5,
    )
    assert task.id == "t1"
    assert task.category == TaskCategory.LOCATE
    assert task.max_steps == 5


def test_missing_prompt_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluationTask(
            id="t1",
            name="Demo",
            category=TaskCategory.LOCATE,
            difficulty=TaskDifficulty.EASY,
            prompt="",
            workspace_fixture="sample_repository",
        )


def test_invalid_difficulty_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluationTask.model_validate(
            {
                "id": "t1",
                "name": "Demo",
                "category": "locate",
                "difficulty": "extreme",
                "prompt": "hello",
                "workspace_fixture": "sample_repository",
            }
        )


def test_invalid_max_steps_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluationTask(
            id="t1",
            name="Demo",
            category=TaskCategory.LOCATE,
            difficulty=TaskDifficulty.EASY,
            prompt="hello",
            workspace_fixture="sample_repository",
            max_steps=0,
        )


def test_forbidden_and_expected_tools_conflict() -> None:
    with pytest.raises(ValidationError):
        EvaluationTask(
            id="t1",
            name="Demo",
            category=TaskCategory.SAFETY,
            difficulty=TaskDifficulty.EASY,
            prompt="hello",
            workspace_fixture="sample_repository",
            expected_tools=["read_file"],
            forbidden_tools=["read_file"],
        )


def test_task_round_trip_json(tmp_path: Path) -> None:
    task = EvaluationTask(
        id="t1",
        name="Demo",
        category=TaskCategory.FAILURE,
        difficulty=TaskDifficulty.MEDIUM,
        prompt="Search missing token",
        workspace_fixture="sample_repository",
    )
    payload = task.model_dump(mode="json")
    restored = EvaluationTask.model_validate(payload)
    assert restored == task
