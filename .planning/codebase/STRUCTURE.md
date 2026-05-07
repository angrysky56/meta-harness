# Codebase Structure

## Root
- `.planning/`: GSD planning and codebase map (this directory).
- `reference_examples/`: Contains the primary implementation examples.
  - `text_classification/`: The main focus area for the meta-harness.
- `ONBOARDING.md`: High-level project onboarding.
- `README.md`: General overview.

## Text Classification Framework (`reference_examples/text_classification/`)

### Core Logic
- `meta_harness.py`: The evolution loop orchestrator.
- `benchmark.py`: Benchmarking and evaluation suite.
- `claude_wrapper.py`: Interface for Claude-driven code generation.
- `inner_loop.py`: Likely contains the execution logic for a single inference step.
- `llm.py`: LLM abstraction layer.
- `memory_system.py`: Memory system base classes and common logic.

### Components
- `agents/`: Contains memory system implementations.
  - `no_memory.py`: Baseline (zero-shot).
  - `fewshot_memory.py`: Baseline (standard RAG/few-shot).
- `data/`: Dataset handling and local data caches.
  - `loaders.py`: Utilities for loading various classification datasets.
  - `evaluators.py`: Logic for scoring model outputs.
  - `<dataset_name>/`: Local `.jsonl` files for train/val/test splits.

### Infrastructure
- `tests/`: Automated unit tests.
- `config.yaml`: Central configuration for the evolution runs.
- `pyproject.toml`: Dependency management via `uv`.
