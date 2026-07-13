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

Required: `DEEPSEEK_API_KEY`. Do not commit `.env`.

## Run

```bash
python3 -m mini_agent.main
```

## Quality Checks

```bash
pytest
ruff check .
ruff format --check .
mypy src
```
