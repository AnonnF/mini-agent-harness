"""LLM client interface contracts."""

from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from mini_agent.llm.models import ChatResponse, Message, StreamChunk
from mini_agent.tools.base import Tool


class LLMClient(Protocol):
    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[Tool] | None = None,
    ) -> ChatResponse: ...

    def stream(self, messages: Sequence[Message]) -> AsyncIterator[StreamChunk]: ...
