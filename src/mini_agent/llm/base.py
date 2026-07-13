"""LLM client interface contracts."""

from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from mini_agent.llm.models import ChatResponse, Message, StreamChunk


class LLMClient(Protocol):
    def complete(self, message: Sequence[Message]) -> ChatResponse: ...

    def stream(self, message: Sequence[Message]) -> AsyncIterator[StreamChunk]: ...
