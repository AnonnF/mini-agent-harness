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


class ScoreBreakdown(BaseModel):
    execution_success: bool
    expected_tools: bool
    forbidden_tools: bool
    keyword_match: bool
    step_limit: bool
    safety: bool


class TaskEvaluationResult(BaseModel):
    task_id: str
    category: TaskCategory
    difficulty: TaskDifficulty
    passed: bool
    scores: ScoreBreakdown
    run_id: str | None = None
    steps_used: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)
    model_call_count: int = Field(default=0, ge=0)
    tool_call_count: int = Field(default=0, ge=0)
    final_text: str = ""
    error: str | None = None
    failure_reasons: list[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    results: list[TaskEvaluationResult]
    total_tasks: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    success_rate: float = Field(ge=0.0, le=1.0)
    success_rate_by_category: dict[str, float] = Field(default_factory=dict)
    success_rate_by_difficulty: dict[str, float] = Field(default_factory=dict)
    average_steps: float = Field(ge=0.0)
    max_steps: int = Field(ge=0)
    average_duration_ms: float = Field(ge=0.0)
    total_model_calls: int = Field(ge=0)
    total_tool_calls: int = Field(ge=0)
    failed_task_ids: list[str] = Field(default_factory=list)
