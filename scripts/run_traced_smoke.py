"""Smoke-run the agent with TraceRecorder and print a compact trace summary.

Requires DEEPSEEK_API_KEY in .env (real API).
"""

from __future__ import annotations

import json
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
from mini_agent.tools.list_files import ListFilesTool
from mini_agent.tools.read_file import ReadFileTool
from mini_agent.tools.registry import ToolRegistry
from mini_agent.tools.search_text import SearchTextTool
from mini_agent.tracing.recorder import TraceRecorder

DEFAULT_PROMPT = "List files under src and name the likely entrypoint file."


def main() -> None:
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_PROMPT
    workspace = Path.cwd()

    try:
        settings = load_settings()
    except ConfigurationError as exc:
        raise SystemExit(str(exc)) from exc

    registry = ToolRegistry()
    registry.register(ListFilesTool(workspace))
    registry.register(ReadFileTool(workspace))
    registry.register(SearchTextTool(workspace))

    client = DeepSeekClient.from_settings(settings=settings)
    recorder = TraceRecorder()
    agent = Agent(
        llm=client,
        registry=registry,
        max_steps=settings.max_agent_steps,
    )

    try:
        print(f"workspace={workspace}")
        print(f"prompt={prompt}")
        print("--- agent ---")
        result = agent.run(prompt, recorder=recorder, task_id="traced_smoke")
        print(result.final_text)
        print(f"--- steps={result.steps_used} reason={result.stop_reason} ---")
    except (ModelRequestError, MaxAgentStepsExceededError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        client.close()

    trace = recorder.last_trace
    if trace is None:
        raise SystemExit("No trace captured")

    summary = {
        "run_id": trace.run_id,
        "success": trace.success,
        "termination_reason": trace.termination_reason,
        "total_steps": trace.total_steps,
        "model_call_count": trace.model_call_count,
        "tool_call_count": trace.tool_call_count,
        "duration_ms": trace.duration_ms,
        "events": [
            {
                "sequence": event.sequence,
                "step": event.step,
                "event_type": event.event_type,
                "success": event.success,
                "metadata_keys": sorted(event.metadata.keys()),
            }
            for event in trace.events
        ],
    }
    print("--- trace summary ---")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
