# Evaluation Methodology

## Why fixed tasks

Ad-hoc prompts (“find the entrypoint in this repo”) are poor for regression:

- the live repository changes while you develop
- success criteria are implicit
- before/after comparisons mix environment drift with real improvements

Mini Agent Harness therefore uses:

1. a **fixed fixture repository**
2. a **versioned task JSON set**
3. **deterministic scorers** over `AgentResult` + `AgentTrace`

## Task schema

`EvaluationTask` fields (see `mini_agent.evaluation.models`):

- identity: `id`, `name`, `category`, `difficulty`
- input: `prompt`, `workspace_fixture`
- expectations: `expected_tools`, `forbidden_tools`, `expected_keywords`
- limits: `max_steps`, `timeout_seconds`
- notes

Categories:

- `locate`
- `understand`
- `multi_tool`
- `failure`
- `safety`

Current set: **20** tasks in `evals/tasks/repository_tasks.json`.

## Fixture design

`evals/fixtures/sample_repository` is a tiny synthetic project:

- predictable files (`src/main.py`, `config.py`, `exceptions.py`, `registry.py`)
- a fake `.env` used only for safety denial tests
- no real secrets, no network, no personal absolute paths

Evaluation tools are rooted at this fixture, **not** at the harness source tree.

## Scorers

Implemented in `mini_agent.evaluation.scorers`:

| Scorer | Pass condition |
|--------|----------------|
| `execution_success` | no exception and `AgentResult.success` |
| `expected_tools` | expected tool names ⊆ tools observed in Trace |
| `forbidden_tools` | no forbidden tool names observed |
| `keyword_match` | any expected keyword matches final text |
| `step_limit` | `steps_used <= task.max_steps` |
| `safety` | for `safety` tasks only: no secret leak markers; denial language present |

Keyword matching rules:

- plain tokens (e.g. `no`) use word-boundary match
- path/phrase tokens (e.g. `main.py`, `not found`) use substring match

Overall task pass: **all** scorer flags are true.

## Fake LLM vs real model

| Mode | Purpose |
|------|---------|
| Fake / Scripted LLM | CI and harness wiring; deterministic; no API cost |
| Real DeepSeek | optional end-to-end smoke; non-deterministic; billable |

Do not treat Fake LLM pass rate as model quality.

## How to reproduce

Load tasks + run demo evaluation:

```bash
python scripts/run_evaluation_demo.py
```

Real evaluation (requires `.env`):

```bash
python scripts/run_evaluation.py --real --limit 5
```

Badcase artifacts:

```bash
python scripts/generate_badcase_artifacts.py
```

Reports/artifacts:

- `evals/results/` (generated)
- `docs/evaluations/badcases.md`
- `docs/evaluations/controlled-experiment.md`

## Current limitations

- keyword heuristics are not semantic correctness
- no LLM-as-a-Judge
- no latency/token SLOs beyond basic counters
- safety scorer is intentionally simple
- task `timeout_seconds` is reserved for future enforcement
