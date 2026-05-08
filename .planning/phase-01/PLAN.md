# PLAN.md — Phase 1: Hermes Core Integration (The Engine)

**Created:** 2026-05-07
**ROADMAP:** [ROADMAP.md](../ROADMAP.md)
**Status:** In progress (Task 1.1 done, 1.2 mostly done, 1.3 pending)

## Goal

Replace the Claude CLI subprocess wrapper with a native Hermes Agent integration for the evolution loop's propose step, port the benchmarking pipeline, and validate end-to-end with a simple diagnostic domain.

## Current State

Task 1.1 (`hermes_wrapper.py`) is substantially complete. The wrapper:
- Imports `AIAgent` from `run_agent`, `discover_mcp_tools`, and `registry`
- Mirrors the `SessionResult` dataclass and `run()` interface from `claude_wrapper.py`
- Maps Claude tool names to Hermes toolsets (`Read`→`file`, `Bash`→`terminal`, etc.)
- Auto-discovers MCP tools and includes them in enabled toolsets
- Logs sessions to `logs/hermes_sessions/<session_id>.json`
- Is already imported and used by `meta_harness.py`'s `propose_hermes()` function

The benchmarking pipeline (`benchmark.py`, `inner_loop.py`, `llm.py`) is wrapper-agnostic — it evaluates memory systems independently of the proposal mechanism. The only `claude_wrapper` reference remaining is a stale docstring comment.

## Remaining Tasks

### T1.2a: Clean up stale references ✅
- **File:** `reference_examples/text_classification/meta_harness.py` line 4
- **Change:** Updated docstring from "Uses claude_wrapper" to "Uses hermes_wrapper"
- **Also fixed:** 
  - `hermes_wrapper.py` now auto-detects model/provider/base_url from `~/.hermes/config.yaml` instead of hardcoding
  - Added `provider`, `base_url`, `api_key` parameters to `HermesWrapper.__init__()` 
  - `AIAgent` now receives provider/base_url for routing to arbitrary endpoints
  - `meta_harness.py` reads `HERMES_PROPOSER_MODEL`, `HERMES_PROPOSER_PROVIDER`, `HERMES_PROPOSER_BASE_URL` env vars for Ollama override
- **Verified:** Zero `claude_wrapper` references. Auto-detection resolves to `deepseek/deepseek-v4-pro` via OpenRouter by default. Ollama configurable via env vars.

### T1.2a-ollama: Ollama sub-agent support ✅
- **How it works:**
  ```bash
  # Default: proposer uses main Hermes model (deepseek-v4-pro via OpenRouter)
  uv run python meta_harness.py --iterations 20 --fresh
  
  # Ollama: proposer uses local gemma4:31b (free, GPU-accelerated on RTX 3060)
  HERMES_PROPOSER_MODEL=gemma4:31b \
  HERMES_PROPOSER_PROVIDER=ollama \
  HERMES_PROPOSER_BASE_URL=http://localhost:11434/v1 \
  uv run python meta_harness.py --iterations 20 --fresh
  ```
- **Model:** `gemma4:31b` — already pulled (19GB). Gemma 4 architecture is latency-optimized; be patient on first run.

### T1.2b: Verify proposer→benchmarker pipeline integrity
- Run a single iteration with `--iterations 1 --fresh --skip-baseline` to confirm:
  - `HermesWrapper.run()` succeeds without import errors
  - `pending_eval.json` is produced with valid candidate entries
  - Candidates pass import validation
  - Benchmarking completes and writes `val.json`
- **Verification:** Exit code 0, no MCP discovery errors, valid output files

### T1.3a: Add simple diagnostic dataset
- Add a sentiment classification dataset (e.g., SST-2 or IMDB subset) to `config.yaml` under `datasets:`
- Create a data loader with small splits (e.g., 100 train / 30 val / 50 test)
- **Verification:** `uv run python benchmark.py --memory no_memory` succeeds on the new dataset

### T1.3b: End-to-end diagnostic run
- Run a full evolution mini-loop (3 iterations) on the sentiment dataset only
- Confirm: propose → validate → benchmark → frontier update works
- **Verification:** `evolution_summary.jsonl` has 3+ rows with valid scores

## Verification Checklist

- [x] T1.2a: Docstring updated, no stale `claude_wrapper` references
- [x] Model auto-detection: `hermes_wrapper.py` reads model from `~/.hermes/config.yaml`
- [ ] T1.2b: Single-iteration pipeline test passes
- [ ] T1.3a: Sentiment dataset loads and benchmarks with baseline
- [ ] T1.3b: 3-iteration evolution loop completes on sentiment data
- [ ] No regressions: existing tests pass (`uv run pytest tests/`)

## Files to Modify

| File | Change |
|------|--------|
| `meta_harness.py` | L4 docstring: `claude_wrapper` → `hermes_wrapper` |
| `config.yaml` | Add sentiment dataset entry |
| `data/loaders.py` | Add sentiment data loader (if needed) |

## Risks

- **MCP discovery at runtime:** `discover_mcp_tools()` is called once per `HermesWrapper` instantiation. If MCP servers are unavailable, the wrapper may hang on startup. Mitigation: wrap in try/except with graceful fallback.
- **Model availability:** `hermes_wrapper.py` hardcodes `claude-3-5-sonnet-20241022` — this model may not match the Hermes config provider. Check against `~/.hermes/config.yaml` active provider/model.
- **Tool name mismatch:** The wrapper maps Claude tool names (`Read`, `Write`, `Bash`) to Hermes toolset names (`file`, `terminal`). If Hermes tool names differ from expected, tool calls will fail silently.

## Task Order

1. T1.2a (docstring fix — trivial, no risk)
2. T1.2b (pipeline test — validates current state before changes)
3. T1.3a (add dataset — prerequisite for diagnostic)
4. T1.3b (end-to-end diagnostic — final validation)
