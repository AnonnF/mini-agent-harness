# Demo Script (2–4 minutes)

This is a recording checklist for a short demo. Prefer showing tracing and
evaluation, not only a successful chat answer.

## Prep

```bash
source .venv/bin/activate
pip install -e ".[dev]"
cp -n .env.example .env   # if needed
pytest -q
```

Have two terminals or split panes ready.

## Suggested timeline

### 1. Project structure (20–30s)

Show:

- `src/mini_agent/{agent,llm,tools,tracing,evaluation}`
- `evals/fixtures/sample_repository`
- `evals/tasks/repository_tasks.json`

One sentence: “This is a harness, not a hidden LangChain graph.”

### 2. Agent smoke run (45–60s)

```bash
python -m mini_agent.main "Find the entrypoint under src and summarize what it imports."
```

Call out:

- tool calls (`list_files` / `read_file` / `search_text`)
- final answer
- step count / stop reason

### 3. Trace (30–45s)

Run the traced demo helper:

```bash
python scripts/run_traced_smoke.py "List files under src and name the entrypoint."
```

Show:

- `run_id`
- ordered events (`model_request` → `model_response` → `tool_*` → `agent_completed`)
- truncated metadata fields

### 4. Evaluation demo (45–60s)

```bash
python scripts/run_evaluation_demo.py
```

Show:

- per-task pass/fail
- score breakdown
- written JSON + Markdown under `evals/results/`

Optional real-model slice (costs money):

```bash
python scripts/run_evaluation.py --real --limit 3 --category locate
```

### 5. One Badcase (30–45s)

Open `docs/evaluations/badcases.md` and one artifact, e.g.:

- `evals/results/badcases/bc3_keyword_false_positive.json`

Explain:

- failure layer was the **evaluation rule**, not the tool system
- controlled fix tightened keyword matching
- success rate can drop when false positives are removed

## Closing line

“Week-04 goal: execute → trace → evaluate → improve with evidence.”
