"""Mini Agent Harness entry point"""

import asyncio
import sys

from mini_agent.config import load_settings
from mini_agent.exceptions import ConfigurationError, ModelRequestError
from mini_agent.llm.deepseek_client import DeepSeekClient
from mini_agent.llm.models import Message, MessageRole
from mini_agent.logging_config import get_logger, setup_logging


async def _stream_demo(client: DeepSeekClient, messages: list[Message]) -> None:
    print("--- stream ---")
    try:
        async for chunk in client.stream(messages=messages):
            print(chunk.content, end="", flush=True)
        print()
    finally:
        await client.aclose()


def main() -> None:
    setup_logging()
    logger = get_logger(__name__)

    try:
        settings = load_settings()
    except ConfigurationError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    client = DeepSeekClient.from_settings(settings=settings)
    messages = [Message(role=MessageRole.USER, content="用一句话介绍你自己")]

    try:
        print("--- complete ---")
        # non-streaming
        resp = client.complete(messages=messages)
        print(resp.content)
        # streaming
        asyncio.run(_stream_demo(client=client, messages=messages))
    except ModelRequestError as exc:
        logger.error("LLM request failed: %s", exc)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
