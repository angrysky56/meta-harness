# Meta-Harness Architecture

This document describes the high-level architecture of the Meta-Harness framework and its integration with the Hermes Agent proposer engine.

## Overview

Meta-Harness is designed to optimize the "harness" around an LLM — the code that manages memory, retrieval, and prompt construction. It follows an evolution loop:
1. **Propose**: An AI agent (proposer) generates new candidate harness implementations.
2. **Evaluate**: A domain-specific evaluator runs benchmarks on the candidates.
3. **Analyze**: The results are fed back to the proposer to inform the next iteration.

## Core Components

### 1. Evolution Engine (`src/meta_harness/engine.py`)
The central orchestrator that manages the evolution cycle. It interacts with the `Evaluator` protocol and the `HermesWrapper`.

### 2. Evaluator Protocol (`src/meta_harness/evaluator.py`)
A standardized interface for different domains. Any new task (e.g., text classification, coding, tool-use) must implement this protocol:
- `run_benchmark`: Execute the task suite for a candidate.
- `validate_candidate`: Ensure the candidate code is runnable.
- `get_frontier_score`: Extract the primary metric for comparison.

### 3. Hermes Wrapper (`src/meta_harness/wrapper.py`)
The bridge between Meta-Harness and the [Hermes Agent](https://hermes-agent.nousresearch.com/). It handles:
- **Environment Resolution**: Dynamically locates the Hermes installation (supporting local `.hermes` overrides).
- **Agent Invocation**: Launches Hermes as a subprocess to perform the "Propose" step.
- **Log Isolation**: Maintains clean execution traces for debugging.

## Reference Implementations

### Text Classification (`reference_examples/text_classification/`)
A mature implementation of the Meta-Harness loop for NLP tasks.
- **`MemorySystem`**: The base class for all agents. Defines the `predict(text: str)` and `learn_from_batch()` interface.
- **`inner_loop.py`**: The training/evaluation logic for a single agent.
- **`meta_harness.py`**: A specialized evolution loop for this domain.

## Code Standards and Quality

To ensure stability during autonomous evolution, the project adheres to strict standards:
- **Linting**: All code must pass `ruff` checks.
- **Type Safety**: Use of Python type hints is mandatory.
- **Namespace Integrity**: Avoid shadowing Python built-ins (e.g., use `text` instead of `input`).
- **Resilience**: Use `pathlib.Path` for all file operations and implement specific exception handling in LLM-facing code.

## Autonomous Domain Expansion

Meta-Harness is designed to be self-onboarding. New domains can be added by:
1. Creating a `domain_spec.md` (see `ONBOARDING.md`).
2. Implementing the `Evaluator` protocol.
3. Adding the domain to `run_evolution.py`.
