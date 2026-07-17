# Mini Agent Harness

A minimal agent harness built from scratch for learning software engineering practices.

It wires a small **Agent Loop** to an OpenAI-compatible LLM client (DeepSeek) and a **read-only tool system**, without hiding the control flow behind LangChain/LangGraph.

## What it supports today

- LLM chat completions (non-streaming and streaming client APIs)
- Tool calling contracts (internal models ↔ provider JSON)
- Tool registry (register / lookup / duplicate rejection)
- Read-only workspace tools: `list_files`, `read_file`, `search_text`
- Minimal agent loop with `MAX_AGENT_STEPS`
- Automated tests with mocks / temp dirs (no real API in CI)

## Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `agent/` | Loop control, message history, step limit, `AgentResult` |
| `llm/` | HTTP client, streaming parser, tool schema ↔ API adapter |
| `tools/` | Tool contract, registry, workspace path safety, file tools |
| `main.py` | Assemble settings + client + tools + agent for smoke runs |

## Built-in tools

All paths are interpreted **relative to a workspace root** (smoke test uses `Path.cwd()`).

| Tool | Behavior |
|------|----------|
| `list_files` | List one directory level (non-recursive), stable sort |
| `read_file` | Read a UTF-8 text file (size limit enforced) |
| `search_text` | Substring search under a path; skips common cache/venv dirs |

## Safety boundaries

- Paths are resolved and must stay inside the workspace root (`Path.resolve` + containment check). Absolute paths or `../` escapes are rejected.
- Sensitive names such as `.env` / SSH key filenames are denied.
- Tools are **read-only** (no write / delete / shell).
- `read_file` rejects oversized files; `search_text` caps match count and skips large/binary-ish files.
- The agent stops with a clear error when `MAX_AGENT_STEPS` is exceeded.

## Requirements

- Python 3.12+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Configuration

```bash
cp .env.example .env
```

Edit `.env`. **Do not commit `.env`.**

| Variable | Required | Default | Meaning |
|----------|----------|---------|---------|
| `DEEPSEEK_API_KEY` | yes | — | API key |
| `DEEPSEEK_BASE_URL` | no | `https://api.deepseek.com` | API base URL |
| `DEEPSEEK_MODEL` | no | `deepseek-v4-flash` | Model name |
| `REQUEST_TIMEOUT` | no | `30.0` | HTTP timeout (seconds) |
| `MAX_AGENT_STEPS` | no | `10` | Max LLM turns in one agent run |

## Run the agent (Smoke Test, real API)

Uses DeepSeek for real (quota / cost). Needs a valid `DEEPSEEK_API_KEY` in `.env`.

Run from the **repository root** so the workspace root is this project:

```bash
python -m mini_agent.main
```

Optional custom prompt:

```bash
python -m mini_agent.main "List Python modules under src and summarize main.py"
```

Expected flow: the model may call `list_files` / `read_file` / `search_text`, then return a final answer. Press `Ctrl+C` to interrupt.

This entrypoint is **not** collected by pytest and should not run in CI against a real key.

## Automated tests (mocked, no real API)

```bash
pytest
```

Tests use:

- `httpx.MockTransport` for the LLM HTTP client
- `FakeLLM` for the agent loop
- `tmp_path` for file tools

They must not hit the network, read personal home directories, or consume API quota.

## Quality checks

```bash
pytest
ruff check .
ruff format --check .
mypy src

# or:
./scripts/check.sh
```

## Explicitly out of scope (for now)

- Write / delete / shell / git tools
- MCP, RAG, memory, planning, multi-agent
- Parallel tool execution
- Full tracing, token cost dashboards, desktop/web UI
- Long-lived session persistence
