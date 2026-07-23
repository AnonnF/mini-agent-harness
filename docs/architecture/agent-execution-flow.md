# Agent Execution Flow

This document describes how Mini Agent Harness runs one agent task, how modules
depend on each other, and how tracing/evaluation observe the run.

## Module responsibilities

| Module | Owns | Does not own |
|--------|------|--------------|
| `config` | env loading via pydantic-settings | business loop |
| `llm` | HTTP/stream, provider JSON ↔ internal models | tool execution |
| `tools` | contracts, registry, workspace safety, file I/O | model prompting |
| `agent` | loop, message history, step limit, `AgentResult` | scoring / reports |
| `tracing` | structured run events (`AgentTrace`) | pass/fail judgment |
| `evaluation` | tasks, scorers, runner, reports | changing agent logic |
| `main` | smoke wiring for local demos | production serving |

## Dependency direction

```text
main
  → agent, llm, tools, config
agent
  → llm (LLMClient), tools (ToolRegistry), tracing (optional TraceRecorder)
evaluation
  → agent, tools, tracing, evaluation models
tracing
  → llm.models.Usage only (no agent import)
tools
  → exceptions / pydantic (no agent import)
```

Rule of thumb: **core runtime modules must not depend on evaluation**.

## One Agent Run (sequence)

```text
1. Build Agent(llm, registry, max_steps)
2. Optional TraceRecorder
3. agent.run(user_input, recorder=..., task_id=...)
4. Loop step = 1..max_steps:
     a. record model_request (optional)
     b. llm.complete(messages, tools)
     c. record model_response (optional)
     d. if tool_calls:
          append assistant message
          for each call:
            record tool_call
            execute tool (errors become tool message text)
            record tool_result
          continue
     e. if empty content and no tools → finish(failed) + raise
     f. else final answer → finish(success) + return AgentResult
5. if loop ends without final answer → finish(max_steps) + raise
```

## Tool Calling conversion boundary

Internal types live in project models (`Message`, `ToolCall`, `ChatResponse`).

At the DeepSeek client boundary:

- tools → OpenAI-compatible tool schema JSON
- assistant tool calls ← provider `tool_calls` JSON (arguments parsed to dict)
- tool results → `role=tool` messages with `tool_call_id`

Invalid provider payloads become `ModelRequestError` / parse errors rather than
silently continuing with partial state.

## Trace data flow

`TraceRecorder` is optional and in-memory:

- `start` creates `run_id`
- events: `model_request`, `model_response`, `tool_call`, `tool_result`,
  `agent_completed` / `agent_failed`
- long text is truncated (`sanitize.truncate_text`)
- `finish` stores `last_trace: AgentTrace`

Tracing records **what happened**. It does not decide whether a task passed.

## Evaluation data flow

```text
load EvaluationTask JSON
  → resolve fixture workspace
  → build Agent with tools rooted at fixture
  → run with TraceRecorder
  → score(Task, AgentResult|None, Trace|None)
  → TaskEvaluationResult
  → EvaluationReport (JSON + Markdown)
```

Runner guarantees:

- tasks run sequentially
- one task failure does not abort the batch
- optional `category` / `limit` filters

## Safety boundaries

- workspace containment after `Path.resolve`
- sensitive filenames denied (`.env`, SSH key names, …)
- read-only tools only
- output size / match caps on file tools
- max agent steps

## Known limitations

- one vendor client
- heuristic keyword scoring
- no memory / MCP / shell / parallel tools
- real-model eval is optional and non-deterministic
