from enum import StrEnum

from pydantic import BaseModel, Field

from mini_agent.llm.models import Message


class AgentStopReason(StrEnum):
    FINAL_ANSWER = "final_answer"
    MAX_STEPS = "max_steps"


class AgentResult(BaseModel):
    success: bool
    final_text: str = ""
    steps_used: int = Field(ge=0)
    stop_reason: AgentStopReason
    messages: list[Message] = Field(default_factory=list)
