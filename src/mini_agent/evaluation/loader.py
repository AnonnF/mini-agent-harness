from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from mini_agent.evaluation.models import EvaluationTask
from mini_agent.exceptions import EvaluationError

DEFAULT_FIXTURES_DIR = Path("evals") / "fixtures"
MINIMUM_TASK_COUNT = 20


def resolve_fixture_path(
    fixture_name: str,
    *,
    fixtures_dir: Path | None = None,
) -> Path:
    root = fixtures_dir if fixtures_dir is not None else DEFAULT_FIXTURES_DIR
    path = (root / fixture_name).resolve()
    if not path.is_dir():
        raise EvaluationError(f"Workspace fixture not found: {fixture_name}")
    return path


def load_tasks(
    path: Path,
    *,
    fixtures_dir: Path | None = None,
    require_minimum: bool = False,
) -> list[EvaluationTask]:
    if not path.is_file():
        raise EvaluationError(f"Task file not found: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"Invalid task JSON: {path}") from exc

    if not isinstance(raw, list):
        raise EvaluationError("Task file must contain a JSON array")

    tasks: list[EvaluationTask] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(raw):
        try:
            task = EvaluationTask.model_validate(item)
        except ValidationError as exc:
            raise EvaluationError(
                f"Invalid task at index {index} in {path}: {exc}"
            ) from exc

        if task.id in seen_ids:
            raise EvaluationError(f"Duplicate task id: {task.id}")
        seen_ids.add(task.id)

        resolve_fixture_path(task.workspace_fixture, fixtures_dir=fixtures_dir)
        tasks.append(task)

    if require_minimum and len(tasks) < MINIMUM_TASK_COUNT:
        raise EvaluationError(
            f"Expected at least {MINIMUM_TASK_COUNT} tasks, found {len(tasks)}"
        )

    return tasks
