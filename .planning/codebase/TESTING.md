# Testing & Evaluation

## Unit Testing
- **Framework**: `unittest` (standard library).
- **Location**: `tests/` directory.
- **Coverage**: Primarily focuses on data loading, evaluator logic, and prompt template integrity.
- **Execution**: Can be run via `uv run python -m unittest discover tests`.

## Benchmark Evaluation
- **Framework**: Custom implementation in `benchmark.py`.
- **Purpose**: Evaluates memory systems on text classification datasets.
- **Modes**:
  - **Val**: Used during the evolution loop to select the best candidates.
  - **Test**: Final evaluation on held-out test sets to verify generalization.
- **Metrics**: Accuracy is the primary metric, with task-specific metrics (Jaccard, TP/FP) for complex tasks like USPTO or LawBench.

## Validation Loop
- The evolution loop includes a mandatory `validate_candidates` step that checks if generated Python code can be imported and initialized without errors before benchmarking.
- Uses `subprocess` to isolate import checks.
