import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from mini_agent.llm.models import Usage


class TraceEventType(StrEnum):
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"


class TerminationReason(StrEnum):
    FINAL_ANSWER = "final_answer"
    MAX_STEPS = "max_steps"
    INVALID_MODEL_RESPONSE = "invalid_model_response"
    LLM_ERROR = "llm_error"
    TOOL_SYSTEM_ERROR = "tool_system_error"
    CANCELLED = "cancelled"
    UNKNOWN_ERROR = "unknown_error"


class TraceEvent(BaseModel):
    sequence: int = Field(ge=0)
    step: int = Field(ge=0)
    event_type: TraceEventType
    started_at: datetime.datetime
    finished_at: datetime.datetime
    success: bool
    metadata: dict[str, object] = Field(default_factory=dict)


class AgentTrace(BaseModel):
    run_id: str
    task_id: str | None = None
    input_text: str
    started_at: datetime.datetime
    finished_at: datetime.datetime
    duration_ms: int = Field(ge=0)
    events: list[TraceEvent]
    final_output: str = ""
    success: bool
    termination_reason: TerminationReason
    total_steps: int = Field(ge=0)
    model_call_count: int
    tool_call_count: int
    usage: Usage | None = None