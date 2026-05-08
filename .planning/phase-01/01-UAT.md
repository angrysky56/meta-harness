---
status: gaps-found
phase: 01-hermes-core-integration
source: phase-01/PLAN.md
started: 2026-05-08T03:50:00Z
updated: 2026-05-08T04:09:00Z
---

## Tests

### 1. HermesWrapper imports and auto-detects config
expected: HermesWrapper auto-detects model/provider from `~/.hermes/config.yaml`.
result: pass

### 2. Zero claude_wrapper references in text_classification Python files
expected: No `claude_wrapper` references in text_classification `*.py` files.
result: pass

### 3. meta_harness.py docstring references hermes_wrapper
expected: Line 4 reads "Uses hermes_wrapper + meta-harness skill to propose new memory systems."
result: pass

### 4. Ollama override env vars are wired into propose_hermes()
expected: `HERMES_PROPOSER_MODEL/PROVIDER/BASE_URL` env vars read and passed to `HermesWrapper()`.
result: pass

### 5. SessionResult interface matches claude_wrapper contract
expected: All 12 fields plus `to_dict/from_dict/show` methods present.
result: pass

### 6. Sentiment dataset exists and is configured
expected: `data/sentiment/{train,val,test}.jsonl` exists; `config.yaml` lists `Sentiment`.
result: pass

### 7. Smoke test: pipeline produces non-zero results
expected: `--iterations 1 --fresh --skip-baseline` produces val.json files with non-zero accuracy.
result: **FAIL**
details: |
  All 3 proposed candidates (rule_synthesis, error_correction, contrastive_pairs) scored 0.0%.
  Root cause: `openai_harmony.HarmonyError` uncaught in `parse_harmony_response()` → predict() crashes → no val.json written.
  Three bugs identified and fixed (see Gaps).

## Summary

total: 7
passed: 6
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

### GAP-001: HarmonyError uncaught in parse_harmony_response [FIXED]
severity: critical
file: `reference_examples/text_classification/llm.py`
fix: Added `HarmonyError` to `except` clause and imported it from `openai_harmony`.

### GAP-002: evaluate_memory crashes on single prediction failure [FIXED]
severity: high
file: `reference_examples/text_classification/inner_loop.py`
fix: Wrapped `future.result()` in try/except, marking failed predictions as incorrect instead of crashing. Added logging module.

### GAP-003: meta_harness reports OK when val.json not produced [FIXED]
severity: moderate
file: `reference_examples/text_classification/meta_harness.py`
fix: Added post-benchmark check verifying val.json existence; reports FAIL if missing despite exit code 0.
