# Integrations

## LLM Providers
- **Anthropic**: Primarily used via `claude_wrapper.py` for the evolution loop's proposer (proposing new memory systems).
- **Multi-Provider (via LiteLLM)**: Supports various models for the benchmarking phase, allowing comparison across different LLM backends.

## Data Sources
- **Hugging Face Hub**: Integrated via the `datasets` library to pull text classification benchmarks.

## Internal Components
- **Claude CLI**: The `meta_harness.py` logic interacts with the `claude` CLI tool for its autonomous reasoning steps.
- **Custom Skills**: Uses a `meta-harness` skill within the Claude sessions to provide domain-specific capabilities.
