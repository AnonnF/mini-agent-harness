# Mini Agent Harness

A minimal **agent harness** built from scratch for learning software engineering
practices around LLM tools and agent loops.

It is **not** a full product agent. It is a small, explicit runtime that wires:

- an OpenAI-compatible LLM client (DeepSeek)
- a read-only tool system
- a minimal agent loop
- structured execution tracing
- fixed-task evaluation

Control flow is kept visible on purpose. This project does **not** use
LangChain or LangGraph, so you can inspect Tool Calling, message history, step
limits, tracing, and scoring without a large framework hiding the mechanics.

## Features (current)

- DeepSeek LLM client (non-streaming + streaming APIs)
- Tool Calling contracts (internal models ↔ provider JSON)
- Tool Registry (register / lookup / duplicate rejection)
- Read-only workspace tools: `list_files`, `read_file`, `search_text`
- Workspace-root path safety (escape + sensitive name denial)
- Minimal Agent Loop with `MAX_AGENT_STEPS`
- Structured Execution Trace (`TraceRecorder` / `AgentTrace`)
- Fixed evaluation tasks (20 prompts + sample fixture)
- Deterministic scorers + JSON/Markdown evaluation reports
- Automated tests with mocks / Fake LLM (no real API in CI)

## Architecture (overview)

```text
User
  ↓
Agent Loop
  ↓
LLM Client
  ↓
Model Response
  ├── Final Answer
  └── Tool Call
        ↓
     Tool Registry
        ↓
     Read-only Tool
        ↓
     Tool Result
        ↓
     Agent Loop
```

Tracing observes the run:

```text
Agent Loop  ──→ TraceRecorder
LLM calls   ──→ TraceRecorder
Tool calls  ──→ TraceRecorder
```

Evaluation consumes results:

```text
Task + AgentResult + Trace
            ↓
         Scorers
            ↓
    Evaluation Report
```

More detail: [docs/architecture/agent-execution-flow.md](docs/architecture/agent-execution-flow.md)

## Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `agent/` | Loop control, message history, step limit, `AgentResult` |
| `llm/` | HTTP client, streaming parser, tool schema ↔ API adapter |
| `tools/` | Tool contract, registry, workspace path safety, file tools |
| `tracing/` | In-memory trace events and `AgentTrace` |
| `evaluation/` | Task schema/loader, scorers, runner, reports |
| `main.py` | Smoke entrypoint: settings + client + tools + agent |

## Built-in tools

Paths are relative to a **workspace root**.

| Tool | Behavior |
|------|----------|
| `list_files` | List one directory level (non-recursive), stable sort |
| `read_file` | Read a UTF-8 text file (size limit enforced) |
| `search_text` | Substring search; skips common cache/venv dirs |

## Safety boundaries

- Tools are **read-only** (no write / delete / shell / browser).
- Paths must stay inside the workspace root (`Path.resolve` + containment).
- Sensitive names such as `.env` / `id_rsa` / `id_ed25519` are denied.
- `read_file` rejects oversized files; `search_text` caps matches.
- The agent stops when `MAX_AGENT_STEPS` is exceeded.

## Requirements

- Python 3.12+

## Quick start

```bash
git clone <your-fork-or-clone-url>
cd mini-agent-harness

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

cp .env.example .env
# edit .env and set DEEPSEEK_API_KEY (needed only for real-model smoke/eval)
```

### Run tests (no real API)

```bash
pytest
# or
./scripts/check.sh
```

### Run the agent smoke test (real API)

Run from the **repository root** so the workspace is this project:

```bash
python -m mini_agent.main
python -m mini_agent.main "List Python modules under src and summarize main.py"
```

### Run evaluation

Deterministic demo (Fake/Scripted LLM, no API cost):

```bash
python scripts/run_evaluation_demo.py
```

Full fixed task set with DeepSeek (quota / cost):

```bash
python scripts/run_evaluation.py --real
python scripts/run_evaluation.py --real --limit 5 --category locate
```

Reports are written under `evals/results/`.

Reproduce documented badcases:

```bash
python scripts/generate_badcase_artifacts.py
```

## Configuration

Create `.env` from `.env.example`. **Do not commit `.env`.**

| Variable | Required | Default | Meaning |
|----------|----------|---------|---------|
| `DEEPSEEK_API_KEY` | for real API | — | API key |
| `DEEPSEEK_BASE_URL` | no | `https://api.deepseek.com` | API base URL |
| `DEEPSEEK_MODEL` | no | `deepseek-v4-flash` | Model name |
| `REQUEST_TIMEOUT` | no | `30.0` | HTTP timeout (seconds) |
| `MAX_AGENT_STEPS` | no | `10` | Max LLM turns in one agent run |

## Evaluation

- **20** fixed tasks in `evals/tasks/repository_tasks.json`
- Categories: locate / understand / multi_tool / failure / safety
- Fixture: `evals/fixtures/sample_repository` (stable, not the live app tree)
- Scorers: execution success, expected tools, forbidden tools, keyword match,
  step limit, safety
- Overall pass requires **all** scorer flags true
- Keyword matching uses word boundaries for plain tokens (avoids `no` matching
  inside `another`)

Fake LLM / Scripted LLM tests verify harness wiring. Real-model evaluation
measures end-to-end behaviour and is optional, flaky, and billable.

See:

- [docs/evaluations/evaluation-methodology.md](docs/evaluations/evaluation-methodology.md)
- [docs/evaluations/badcases.md](docs/evaluations/badcases.md)
- [docs/evaluations/controlled-experiment.md](docs/evaluations/controlled-experiment.md)

## Demo script

A 2–4 minute walkthrough outline lives in [docs/demo.md](docs/demo.md).

## Quality checks

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

## Known limitations

- Single model vendor integration (DeepSeek / OpenAI-compatible)
- Keyword scorers are heuristics, not semantic judges
- No long-term memory / context compression
- No MCP, RAG, planning, multi-agent, or parallel tool calls
- No shell / write / network-browsing tools
- No OpenTelemetry / web dashboard / DB-backed traces

## Roadmap (not done yet)

- Deeper LLM/agent mechanism study (tokens, sampling, KV cache, prompts)
- Stronger tool-use policies and better failure explanations
- Optional richer evaluation signals without jumping to LLM-as-a-Judge first

## Explicitly out of scope (for now)

- Write / delete / shell / git automation tools
- MCP, RAG, vector DB, multi-agent orchestration
- Cloud deployment and desktop UI
- Model fine-tuning
