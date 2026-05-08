# Requirements: Meta-Hermes KSG

## Functional Requirements

### 1. Hermes Native Integration
-   **Interface**: Replace the `subprocess` Claude-CLI wrapper with a `HermesWrapper` that interfaces with the `AIAgent` in `run_agent.py` or uses the `hermes -z` oneshot mode.
-   **Tool Registry**: Enable dynamic toolset selection based on the domain (e.g., enabling `legal_tools` vs `coding_tools`).
-   **Skill Generation**: The harness must be able to write and register new `.json` skills in `~/.hermes/skills/`.

### 2. Synapse Knowledge Pipeline
-   **Batch Ingestion**: Automate the ingestion of files from a `domain_seeds/<name>/raw/` directory into Neo4j using `synapse_wiki_ingest_raw`.
-   **Structured Extraction**: Use Hermes to extract "Static Knowledge" (entities/relations) and "Curated Workflows" (decision trees) from the ingested text.
-   **Wiki Sync**: Automatically generate `wiki/sources/` and `wiki/concepts/` pages for every new domain piece.

### 3. Domain-Agnostic Bootstrapping
-   **No Hardcoded Paths**: All domain-specific logic must reside in a `domain_seeds/<name>/` directory (config.yaml, prompts, initial seeds).
-   **Domain Template**: Provide a "Hello World" diagnostic domain to test the pipeline integrity.

### 4. Verification & Audit
-   **Formal Checks**: Pipe extracted decision trees into `mcp-logic` to find contradictions or circular dependencies.
-   **Audit Trail**: Maintain a `STATE.md` or a dedicated audit log tracking the provenance of every "Insight" generated.

## Technical Requirements
-   **Python Environment**: Manage with `uv`.
-   **Graph DB**: Local Neo4j instance accessible via `project-synapse`.
-   **LLM Provider**: Configurable via `~/.hermes/config.yaml` (favoring Anthropic/Claude for reasoning depth).
-   **Memory**: Utilize Hermes' internal SQLite session storage for evolution history.
