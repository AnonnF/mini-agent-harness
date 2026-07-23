# Initial Agent Badcases

These cases were generated with **ScriptedLLM + real workspace tools** against
`evals/fixtures/sample_repository`, so each artifact contains a real
`AgentTrace` (run id, ordered events, tool metadata).

Reproduce:

```bash
python scripts/generate_badcase_artifacts.py
```

Artifacts live in `evals/results/badcases/`.

---

## Badcase 1 — Repeated `list_files`

### Task

- ID: `bc1_repeated_list_files`
- Prompt: list Python files under `src`
- Expected: use `list_files`, mention `main.py`

### Observed Behaviour

The agent called `list_files` on `src` **three times** with the same arguments,
then answered correctly. Automatic scorers all passed.

### Trace Evidence

- Artifact: `evals/results/badcases/bc1_repeated_list_files.json`
- `run_id`: see artifact (regenerated on each script run)
- Tool calls: `list_files`, `list_files`, `list_files`
- `model_call_count`: 4, `tool_call_count`: 3, `total_steps`: 4
- Final output mentioned `main.py`

### Failure Layer

- Primary: **model / policy behaviour** (not using previous tool results)
- Secondary: **Agent Loop control** (no repeat-call guard yet)

### Root Cause Hypothesis

Without an explicit anti-repeat rule or stronger system prompt, a model (or a
scripted stand-in that mimics a weak policy) can re-issue identical tool calls
and still satisfy coarse success metrics.

### Proposed Change

Add a single, narrow improvement later: either a system-prompt rule
(“do not repeat the same tool call with identical arguments”) or a loop-level
warning when identical calls repeat. **Not applied in the Task 4 experiment.**

### Regression Risk

Anti-repeat logic might block legitimate retries after a transient tool error.

### Verification

Same task set comparison in the controlled experiment shows this case still
passes after the keyword-scorer fix (unchanged behaviour).

---

## Badcase 2 — Wrong tool choice

### Task

- ID: `bc2_wrong_tool_choice`
- Prompt: find `ToolRegistry` definition using search
- Expected tools: `search_text`
- Expected keywords: `registry.py`, `ToolRegistry`

### Observed Behaviour

The agent read `README.md` and `src/main.py` instead of searching, then claimed
it could not locate `ToolRegistry`. Scorer failed on `expected_tools`.

### Trace Evidence

- Artifact: `evals/results/badcases/bc2_wrong_tool_choice.json`
- Tool calls: `read_file`, `read_file` only
- No `search_text` event
- Final text did not recover the missing tool usage requirement

### Failure Layer

- Primary: **tool selection / prompt-following**
- Possible contribution: **tool description clarity** (search vs read)

### Root Cause Hypothesis

When the task explicitly asks to search, reading likely files is a common
failure mode. Current tool descriptions may not push the model toward
`search_text` strongly enough for “find definition” prompts.

### Proposed Change

Improve the `search_text` tool description only (single variable), or strengthen
evaluation prompts. **Deferred**; this case is kept as a stable fail for
regression checking in the keyword experiment.

### Regression Risk

Over-emphasizing search might make simple “read this known path” tasks worse.

### Verification

Remains `expected_tools` failure before and after the keyword-scorer change.

---

## Badcase 3 — Keyword false positive (selected for experiment)

### Task

- ID: `bc3_keyword_false_positive`
- Category: `failure`
- Expected keywords: `no`, `not found`, `0`
- Expected tool: `search_text`

### Observed Behaviour

The agent correctly called `search_text`, then answered:

> I know another approach might help, but results look unclear.

Under the **baseline** keyword rule (raw substring + any keyword), this passed
because `no` appears inside `know` / `another`. The answer did **not** clearly
report zero matches.

### Trace Evidence

- Artifact: `evals/results/badcases/bc3_keyword_false_positive.json`
- Tool calls: `search_text` once
- Final text as above
- After the fix, scores show `keyword_match: false` (intended)

### Failure Layer

**Evaluation rule problem** (not model capability, not tool implementation).

### Root Cause Hypothesis

Short tokens like `no` are unsafe under naive substring matching and create
false passes that hide weak final answers.

### Proposed Change

Change only `score_keyword_match`:

- plain tokens → word-boundary match
- path/phrase tokens (`main.py`, `not found`) → substring match
- keep “any keyword” aggregation for v1

### Regression Risk

Stricter matching might fail answers that use punctuation-glued tokens; check
true positives like `no matches found` and `Found 0 matches`.

### Verification

See `docs/evaluations/controlled-experiment.md` and
`evals/results/controlled_experiment/summary.json`.

---

## Summary

| Badcase | Layer | Auto-score before fix | Used in experiment |
|---------|-------|------------------------|--------------------|
| BC1 repeated tools | Model / loop | Pass (quality issue) | Control (unchanged) |
| BC2 wrong tool | Tool choice | Fail `expected_tools` | Control (unchanged) |
| BC3 keyword FP | Evaluation rule | False pass | **Fixed** |
