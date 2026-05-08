# Roadmap: Meta-Hermes KSG

## Phase 1: Hermes Core Integration (The Engine)
- [ ] **Task 1.1**: Implement `hermes_wrapper.py`. This should mimic the `run()` interface of `claude_wrapper.py` but use `hermes -z` or direct `AIAgent` calls.
- [ ] **Task 1.2**: Port the existing `Text Classification` benchmarking logic to use the new wrapper.
- [ ] **Task 1.3**: Validate the engine with a "Diagnostic Domain" (simple sentiment classification).

## Phase 2: Synapse Pipeline (The Knowledge)
- [ ] **Task 2.1**: Integrate `mcp_project-synapse` tools into the evolution loop.
- [ ] **Task 2.2**: Implement "Autonomous Ingestion" — a loop that watches a directory and triggers the Synapse pipeline.
- [ ] **Task 2.3**: Automate the creation of `wiki/sources/` summary pages from Hermes trajectories.

## Phase 3: Domain-Agnostic Onboarding (The Substrate)
- [ ] **Task 3.1**: Define the `domain_seeds/` directory structure and `config.yaml` schema.
- [ ] **Task 3.2**: Implement the "Seed-to-Skill" compiler — converting graph relationships into Hermes `.json` skills.
- [ ] **Task 3.3**: Bootstrap a "Legal/Regulatory" domain substrate as a high-stakes stress test.

## Phase 4: Formal Verification (The Moat)
- [ ] **Task 4.1**: Integrate `mcp-logic` to verify extracted decision trees.
- [ ] **Task 4.2**: Implement "Reasoning Audits" — using Hermes to audit the logic of another agent's output based on the verified substrate.
- [ ] **Task 4.3**: Final end-to-end benchmark of the "Picks and Shovels" pipeline.
