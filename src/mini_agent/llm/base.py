"""LLM client interface contracts."""

from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from mini_agent.llm.models import ChatResponse, Message, StreamChunk


class LLMClient(Protocol):
    def complete(self, messages: Sequence[Message]) -> ChatResponse: ...

    def stream(self, messages: Sequence[Message]) -> AsyncIterator[StreamChunk]: ...
