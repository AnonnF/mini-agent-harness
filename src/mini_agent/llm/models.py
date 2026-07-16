"""Internal data models for LLM communications"""

from enum import StrEnum

from pydantic import BaseModel, Field

from mini_agent.tools.models import ToolCall


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    role: MessageRole
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


class Usage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    content: str = ""
    usage: Usage | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)


class StreamChunk(BaseModel):
    content: str = ""
