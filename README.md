# Mini Agent Harness

A minimal agent harness built from scratch for learning software engineering practices.

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
| `MAX_AGENT_STEPS` | no | `10` | Reserved for later agent loop |

## LLM Smoke Test (real API)

Calls DeepSeek for real (uses quota / may incur cost). Needs a valid `DEEPSEEK_API_KEY` in `.env`.

```bash
python -m mini_agent.main
```

This entrypoint demos:

1. **Non-streaming** `complete()` — prints the full reply once.
2. **Streaming** `stream()` — prints tokens/chunks as they arrive.

It is **not** collected by pytest and should not run in CI against a real key.

## Automated tests (mocked, no real API)

```bash
pytest
```

Unit tests use `httpx.MockTransport` (and pure parser tests). They must not hit the network or consume API quota.

## Quality checks

```bash
pytest
ruff check .
ruff format --check .
mypy src

# or run script: ./scripts/check.sh
```
