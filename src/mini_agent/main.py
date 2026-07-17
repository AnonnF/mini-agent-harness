"""Mini Agent Harness entry point"""

import sys
from pathlib import Path

from mini_agent.agent.loop import Agent
from mini_agent.config import load_settings
from mini_agent.exceptions import (
    ConfigurationError,
    MaxAgentStepsExceededError,
    ModelRequestError,
)
from mini_agent.llm.deepseek_client import DeepSeekClient
from mini_agent.llm.models import Message
from mini_agent.logging_config import get_logger, setup_logging
from mini_agent.tools.list_files import ListFilesTool
from mini_agent.tools.read_file import ReadFileTool
from mini_agent.tools.registry import ToolRegistry
from mini_agent.tools.search_text import SearchTextTool

DEFAULT_PROMPT = "请查看当前项目中的 Python 文件，并判断程序入口在哪里。"


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

    workspace = Path.cwd()
    client = DeepSeekClient.from_settings(settings=settings)

    registry = ToolRegistry()
    registry.register(ListFilesTool(workspace))
    registry.register(ReadFileTool(workspace))
    registry.register(SearchTextTool(workspace))

    agent = Agent(
        llm=client,
        registry=registry,
        max_steps=settings.max_agent_steps,
    )

    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_PROMPT

    try:
        print(f"workspace={workspace}")
        print(f"prompt={prompt}")
        print("--- agent ---")
        result = agent.run(prompt)
        print(result.final_text)
        print(f"--- steps={result.steps_used} reason={result.stop_reason} ---")
    except ModelRequestError as exc:
        logger.error("LLM request failed: %s", exc)
        sys.exit(1)
    except MaxAgentStepsExceededError as exc:
        logger.error("%s", exc)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
