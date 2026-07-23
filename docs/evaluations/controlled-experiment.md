# Controlled Experiment — Keyword Matching

## Goal

Fix one evaluation false positive without changing Agent Loop logic, tool
implementations, prompts, or task answer keys.

## Setup

- Same three scripted tasks/traces: BC1, BC2, BC3
  (`evals/results/badcases/`)
- Same fixture: `evals/fixtures/sample_repository`
- Same ScriptedLLM policies (`scripts/generate_badcase_artifacts.py`)
- LLM stand-in is deterministic; this isolates the scorer change

## Baseline Version

- Commit family: evaluation runner with substring keyword matching
- Rule: `any(keyword.lower() in final_text.lower())`
- BC3 final text: `I know another approach might help, but results look unclear.`
- BC3 `keyword_match`: **true** (false positive via `no` inside `know`/`another`)

Baseline outcomes:

| Task | Passed | Failure reasons |
|------|--------|-----------------|
| BC1 | true | — |
| BC2 | false | `expected_tools` |
| BC3 | true | — (false positive) |

## Proposed Change (single variable)

Update only `mini_agent.evaluation.scorers.score_keyword_match`:

- plain tokens → `\bword\b` match
- tokens containing space / `.` / `_` / `/` / `-` → substring match
- still “any keyword succeeds”

No task JSON edits were made to inflate scores.

## Updated Version

Regenerate artifacts:

```bash
python scripts/generate_badcase_artifacts.py
```

Updated outcomes (also in `evals/results/controlled_experiment/summary.json`):

| Task | Passed | Failure reasons |
|------|--------|-----------------|
| BC1 | true | — |
| BC2 | false | `expected_tools` |
| BC3 | false | `keyword_match` |

## Improvement

- BC3 false positive removed: baseline `keyword_match=true` → updated `false`
- Evaluation now fails an answer that never clearly reported “no matches”

## Regression Checks

On the same keyword list `["no", "not found", "0"]`:

- `no matches found` → still passes
- `Found 0 matches` → still passes
- BC1 still passes
- BC2 still fails only on `expected_tools`

## Conclusion

A single scorer change improved evaluation honesty for short-token keywords
without changing agent behaviour or task labels. Overall “pass count” on this
tiny set decreased (3→2 with BC3 now correctly failing), which is expected:
**removing false passes is an improvement even when raw success rate drops.**

Next useful experiment (not done here): improve `search_text` description or
system prompt to address BC2 tool selection, measured on the same fixed tasks.
