# Coding Conventions

## Python Standards
- **Version**: Python >= 3.11.
- **Typing**: Strong emphasis on type hints (PEP 484).
- **Docstrings**: Google or NumPy style (implied by descriptive module docstrings).

## Architecture & Design
- **Path Handling**: Use `pathlib.Path` instead of `os.path` for all filesystem operations.
- **Configuration**: Use `YAML` for static configuration (`config.yaml`) and `argparse` for CLI overrides.
- **Logging**: Rich CLI output with ANSI colors for status indicators (OK, FAIL, TS).

## LLM Interaction
- **Abstraction**: Use `litellm` for general benchmarks and `claude_wrapper` for autonomous loops.
- **Retry Logic**: Mandatory use of `tenacity` for any network/API calls.

## Tooling
- **Linting**: `ruff` is the standard linter/formatter.
- **Environment**: Managed via `uv`.
