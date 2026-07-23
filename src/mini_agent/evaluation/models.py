from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class TaskCategory(StrEnum):
    LOCATE = "locate"
    UNDERSTAND = "understand"
    MULTI_TOOL = "multi_tool"
    FAILURE = "failure"
    SAFETY = "safety"


class TaskDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class EvaluationTask(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: TaskCategory
    difficulty: TaskDifficulty
    prompt: str = Field(min_length=1)
    workspace_fixture: str = Field(min_length=1)
    expected_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    expected_keywords: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=10, ge=1)
    timeout_seconds: float = Field(default=60.0, gt=0)
    notes: str = ""

    @model_validator(mode="after")
    def forbidden_must_not_overlap_expected(self) -> "EvaluationTask":
        overlap = set(self.expected_tools) & set(self.forbidden_tools)
        if overlap:
            names = ", ".join(sorted(overlap))
            raise ValueError(f"forbidden_tools overlaps expected_tools: {names}")
        return self
