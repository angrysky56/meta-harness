# Architecture

## Core Concept
The project implements an **Autonomous Evolution Loop** for LLM memory systems. It uses a "Meta-Harness" to iteratively propose, validate, and benchmark memory architectures (agents) against text classification tasks.

## Components

### 1. Evolution Orchestrator (`meta_harness.py`)
- Manages the lifecycle of the evolution: Propose -> Validate -> Benchmark -> Summarize.
- Maintains a "Frontier" of the best-performing memory systems.
- Handles signal interrupts and provides colored terminal output for monitoring.

### 2. Proposer Loop (`claude_wrapper.py`)
- Wraps the Claude CLI to perform "propose" steps.
- Uses a specific "skill" (`meta-harness`) to guide the LLM in generating valid Python code for new memory agents.

### 3. Benchmarker (`benchmark.py`)
- Evaluates specific memory systems on defined datasets.
- Computes metrics (accuracy) and handles logging of results.
- Supports both validation (during evolution) and test (final) evaluations.

### 4. Memory System (`memory_system.py`)
- Defines the base class and interfaces for memory implementations.
- Acts as the skeletal structure for generated "agents".

### 5. Agents / Candidates (`agents/`)
- Dynamically generated Python modules containing specific memory logic.
- These are the output of the evolution loop.

## Data Flow
1. **Config**: `config.yaml` defines datasets, models, and baseline systems.
2. **Proposal**: Proposer reads current state/summary and writes `pending_eval.json`.
3. **Benchmarking**: Benchmark results are stored in `logs/` as `val.json` or `test.json`.
4. **Analysis**: Summary statistics are appended to `evolution_summary.jsonl`.
