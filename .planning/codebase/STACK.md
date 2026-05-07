# Tech Stack

## Language & Runtime
- **Python**: >= 3.11
- **Package Manager**: `uv` (standardized across the project)

## Core Dependencies
- **LLM Interfacing**:
  - `litellm`: Unified interface for multiple LLM providers.
  - `openai-harmony`: Possibly for specific OpenAI compatibility or enhanced features.
- **Data Handling**:
  - `datasets`: Hugging Face datasets library for benchmark data.
  - `yaml`: For configuration files (`config.yaml`).
- **Utilities**:
  - `tenacity`: For retry logic on API calls.
  - `tqdm`: Progress bars for long-running benchmarks.
  - `jsonl`: Used for evolution summaries.

## Tools & Quality Assurance
- **Linting/Formatting**: `ruff` (configured in `pyproject.toml`).
- **Execution**: `uv run` is the primary entry point for scripts.
- **Environment Management**: `.env` for API keys (e.g., `ANTHROPIC_API_KEY`).
