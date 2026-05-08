# Meta-Hermes: Knowledge Substrate Generator (KSG)

## Vision
To build a self-adaptive, autonomous evolution harness that leverages the **Hermes Agent** ecosystem and the **Project Synapse** pipeline to create and maintain "structured, verifiable, domain-complete knowledge substrates."

This project moves beyond simple agent refinement into "picks and shovels" territory—building the foundational knowledge graphs and decision-workflows that specialized LLMs need to reason without hallucination.

## Core Pillars
1.  **Autonomous Evolution**: A continuous loop that proposes, validates, and benchmarks agent configurations (tools, prompts, skills).
2.  **Synapse Pipeline Integration**: Ingesting raw domain literature into a graph-structured knowledge base (Neo4j) and a human-readable wiki layer (Obsidian).
3.  **Domain-Agnosticism**: A "Seed-to-Skill" onboarding process where pointing the agent at a directory of documents triggers the autonomous creation of a specialized Hermes Skill.
4.  **Formal Verification**: Utilizing `mcp-logic` (Prover9/Mace4) to verify the logical consistency of generated decision trees and knowledge relationships.

## Success Metrics
-   **Time-to-Skill**: Onboard a new domain (e.g., Legal, Medical) from raw PDFs to a functional Hermes Skill in < 15 minutes.
-   **Provenance**: Every fact in the generated knowledge base must link back to a specific source in the `Clippings/` directory.
-   **Logic Integrity**: 0% contradictions in the verified sub-graphs of the domain decision trees.

## Stakeholders
-   **Owner**: Ty (angrysky56)
-   **System**: Hermes Agent + Project Synapse + mcp-logic
