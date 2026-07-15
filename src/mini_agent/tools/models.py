from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, object]


class ToolResult(BaseModel):
    call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    success: bool
    output: str = ""
    error: str | None = None
