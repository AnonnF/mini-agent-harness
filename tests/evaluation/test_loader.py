import json
from pathlib import Path

import pytest

from mini_agent.evaluation.loader import (
    MINIMUM_TASK_COUNT,
    load_tasks,
    resolve_fixture_path,
)
from mini_agent.evaluation.models import TaskCategory
from mini_agent.exceptions import EvaluationError

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_PATH = REPO_ROOT / "evals" / "tasks" / "repository_tasks.json"
FIXTURES_DIR = REPO_ROOT / "evals" / "fixtures"


def test_load_all_repository_tasks() -> None:
    tasks = load_tasks(
        TASKS_PATH,
        fixtures_dir=FIXTURES_DIR,
        require_minimum=True,
    )
    assert len(tasks) >= MINIMUM_TASK_COUNT
    assert len({task.id for task in tasks}) == len(tasks)

    categories = {task.category for task in tasks}
    assert TaskCategory.LOCATE in categories
    assert TaskCategory.UNDERSTAND in categories
    assert TaskCategory.MULTI_TOOL in categories
    assert TaskCategory.FAILURE in categories
    assert TaskCategory.SAFETY in categories


def test_load_single_task_shape() -> None:
    tasks = load_tasks(TASKS_PATH, fixtures_dir=FIXTURES_DIR)
    first = tasks[0]
    assert first.prompt
    assert first.workspace_fixture == "sample_repository"
    assert first.max_steps >= 1


def test_resolve_fixture_path() -> None:
    path = resolve_fixture_path("sample_repository", fixtures_dir=FIXTURES_DIR)
    assert path.is_dir()
    assert (path / "src" / "main.py").is_file()


def test_missing_fixture_raises(tmp_path: Path) -> None:
    task_file = tmp_path / "tasks.json"
    task_file.write_text(
        json.dumps(
            [
                {
                    "id": "t1",
                    "name": "Demo",
                    "category": "locate",
                    "difficulty": "easy",
                    "prompt": "hello",
                    "workspace_fixture": "missing_fixture",
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(EvaluationError, match="fixture"):
        load_tasks(task_file, fixtures_dir=tmp_path / "fixtures")


def test_duplicate_task_id_raises(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures" / "sample_repository"
    fixtures.mkdir(parents=True)
    task_file = tmp_path / "tasks.json"
    item = {
        "id": "dup",
        "name": "Demo",
        "category": "locate",
        "difficulty": "easy",
        "prompt": "hello",
        "workspace_fixture": "sample_repository",
    }
    task_file.write_text(json.dumps([item, item]), encoding="utf-8")

    with pytest.raises(EvaluationError, match="Duplicate"):
        load_tasks(task_file, fixtures_dir=tmp_path / "fixtures")


def test_invalid_json_raises(tmp_path: Path) -> None:
    task_file = tmp_path / "tasks.json"
    task_file.write_text("{not-json", encoding="utf-8")
    with pytest.raises(EvaluationError, match="Invalid task JSON"):
        load_tasks(task_file, fixtures_dir=tmp_path)


def test_non_array_json_raises(tmp_path: Path) -> None:
    task_file = tmp_path / "tasks.json"
    task_file.write_text(json.dumps({"id": "t1"}), encoding="utf-8")
    with pytest.raises(EvaluationError, match="JSON array"):
        load_tasks(task_file, fixtures_dir=tmp_path)


def test_require_minimum_raises(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures" / "sample_repository"
    fixtures.mkdir(parents=True)
    task_file = tmp_path / "tasks.json"
    task_file.write_text(
        json.dumps(
            [
                {
                    "id": "only-one",
                    "name": "Demo",
                    "category": "locate",
                    "difficulty": "easy",
                    "prompt": "hello",
                    "workspace_fixture": "sample_repository",
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(EvaluationError, match="at least"):
        load_tasks(
            task_file,
            fixtures_dir=tmp_path / "fixtures",
            require_minimum=True,
        )
