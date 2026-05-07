# Technical Concerns & Debt

## 1. Environmental Dependencies
- **Claude CLI**: The evolution loop depends on the `claude` CLI being installed and authenticated. This makes it difficult to run in generic CI/CD environments.
- **Python Pathing**: Heavy reliance on `Path(__file__).parent` makes the code sensitive to how it's executed (e.g., as a module vs. a script).

## 2. Resource Management
- **LLM Costs**: Evolution runs with many iterations and high `effort="max"` can be expensive.
- **Timeouts**: Extremely long timeouts (40 minutes for proposal) can lead to stalled processes if not monitored.

## 3. Reliability & Monitoring
- **Error Handling**: Many failures (e.g., benchmark crashes) are caught but only reported via print statements. There is no persistent error log or alert system.
- **State Management**: The loop state is stored in multiple JSON/JSONL files. Corrupting one (e.g., `evolution_summary.jsonl`) could break the resume logic.

## 4. Code Quality of Generated Agents
- **Validation**: Currently, validation only checks if the agent can be *imported*. It doesn't check if it actually follows the `MemorySystem` interface or if it has logical flaws that only appear during execution.
- **Cleanup**: `fresh_start()` deletes files in `agents/`. If a user manually added a file there without naming it in `BASELINE_FILES`, it would be lost.

## 5. Security
- **Subprocess Execution**: `validate_candidates` and `benchmark.py` run generated code using `uv run python`. While necessary for the project's goal, it poses a risk if the LLM generates malicious code.
