# Knowledge System & Development Memory

This directory stores the **Development Memory** for the Real Human LoRA Dataset Pipeline.  
Unlike standard documentation that merely states the current instructions, this knowledge base tracks:
- **What is currently validated and recommended** (`current/`)
- **Why specific architectural and threshold decisions were accepted** (`decisions/`)
- **What approaches failed, why they failed, and when NOT to retry them** (`failures/`)
- **Concrete edge cases and counterexamples that challenged heuristics** (`cases/`)
- **Standardized templates for recording new engineering knowledge** (`templates/`)

---

## Navigation & Retrieval Order

When searching for information or preparing code modifications:

1. **Start Here**: [`knowledge/current/`](file:///./current/README.md) - Active policies, validated operational envelopes, and hard rules.
2. **Context & Why**: [`knowledge/decisions/`](file:///./decisions/README.md) - Accepted architectural decision records (ADRs).
3. **Guardrails**: [`knowledge/failures/`](file:///./failures/README.md) - Anti-patterns and failed experiments (check before proposing changes).
4. **Boundary Tests**: [`knowledge/cases/`](file:///./cases/README.md) - Real images that broke previous assumptions.
5. **Empirical Data**: [`experiments/`](file:///../experiments/README.md) - Raw measurement data and benchmark results.

---

## Core Rules for Contributors and AI Agents
- **Never delete failed attempts**: Failed approaches are vital institutional knowledge.
- **Do not overwrite superseded decisions**: Keep the old record and mark it `status: SUPERSEDED`, then link to the new record via `supersedes: [OLD_ID]`.
- **Separate Fact from Interpretation**: Raw sensor and algorithm metrics are facts; causal explanations are interpretations.
- **Follow ID Polices**: IDs (`DEC-xxxx`, `FAIL-xxxx`, `CASE-xxxx`, `EXP-YYYYMMDD-xxx`) are permanent and never reused.
