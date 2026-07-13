"""DeepSeek chat-completions client (OpenAI-compatible API).

Translates internal Message/ChatResponse models to HTTP calls.
Network and vendor errors are wrapped as ModelRequestError.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Sequence

import httpx
from pydantic import ValidationError

from mini_agent.config import Settings
from mini_agent.exceptions import ModelRequestError
from mini_agent.llm.models import ChatResponse, Message, StreamChunk, Usage
from mini_agent.logging_config import get_logger

logger = get_logger(__name__)

class DeepSeekClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._timeout = timeout
        # Tests inject a MockTransport client; only self-created clients are closed.
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.Client(timeout=timeout)

    @classmethod
    def from_settings(
        cls, settings: Settings, http_client: httpx.Client | None = None
    ) -> DeepSeekClient:
        return cls(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout=settings.request_timeout,
            http_client=http_client,
        )

    def complete(self, messages: Sequence[Message]) -> ChatResponse:
        if not messages:
            raise ModelRequestError("message must not be empty!")

        url = f"{self._base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [
                # API expects "user", not MessageRole.USER
                {"role": m.role.value, "content": m.content} for m in messages 
            ],
            "stream": False, # Non-streaming
        }

        logger.info("LLM request started model=%s", self._model)
        start = time.perf_counter()

        try:
            response = self._http_client.post(url, headers=headers, json=body)
        except httpx.TimeoutException as exc: # subclass of HTTPError; catch first
            raise ModelRequestError("Request timeout") from exc
        except httpx.HTTPError as exc:
            raise ModelRequestError("Network error") from exc

        elapsed = time.perf_counter() - start

        # Map HTTP status to ModelRequestError explicitly; do not leak httpx exceptions.
        if response.is_success:  # 2xx
            try:
                data = response.json()
            except ValueError as exc:
                raise ModelRequestError("Invalid JSON response") from exc

            try:
                # DeepSeek chat/completions response (OpenAI-compatible):
                # choices[0].message.content
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                raise ModelRequestError("Invalid response format")

            if not isinstance(content, str):
                raise ModelRequestError("Invalid response format")

            usage_data = data.get("usage")
            try:
                usage = Usage.model_validate(usage_data) if usage_data else None
            except ValidationError:
                raise ModelRequestError("Invalid response format")
        elif response.status_code == 401:
            logger.warning(
                "LLM request failed model=%s status=%s elapsed=%.3fs",
                self._model,
                response.status_code,
                elapsed,
            )
            raise ModelRequestError("Authentication failed")
        elif response.status_code == 429:
            logger.warning(
                "LLM request failed model=%s status=%s elapsed=%.3fs",
                self._model,
                response.status_code,
                elapsed,
            )
            raise ModelRequestError("Rate limited")
        elif 500 <= response.status_code < 600:
            logger.warning(
                "LLM request failed model=%s status=%s elapsed=%.3fs",
                self._model,
                response.status_code,
                elapsed,
            )
            raise ModelRequestError("Server error")
        else:  # 其他 4xx
            raise ModelRequestError(
                f"Request failed with status {response.status_code}"
            )

        logger.info(
            "LLM request finished model=%s status=%s elapsed=%.3fs usage=%s",
            self._model,
            response.status_code,
            elapsed,
            usage.model_dump() if usage else None,
        )

        return ChatResponse(content=content, usage=usage)

    async def stream(self, messages: Sequence[Message]) -> AsyncIterator[StreamChunk]:
        raise NotImplementedError("Streaming will be implemented in Task 3")

    def close(self) -> None:
        if self._owns_client:
            self._http_client.close()
