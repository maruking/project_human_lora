---
topic: project-governance
last_updated: 2026-10-02
status: ACTIVE
confidence: MEDIUM
related_decisions: [DEC-0011, DEC-0006, DEC-0007, DEC-0009, DEC-0010]
---

# Current Knowledge: Agent Entry and Full Frame Lineage

Start with root [AGENTS](../../AGENTS.md), then canonical
[.agents/AGENTS](../../.agents/AGENTS.md), [PROJECT](../../PROJECT.md),
[Pipeline Rules](../../.agents/rules/lora_pipeline_rules.md) and
[Data Lineage Rules](../../.agents/rules/data_lineage_rules.md).
Knowledge is consulted after Project Rules, not instead of them.

ACTIVE governance: reusable multi-subject/model-independent evaluation, full-frame
audit preservation within a generation, rejection/skip reasons, generation-safe
joins and derived reports distinct from authoritative data. Existing STEP2 exact
coverage is validated; universal legacy enforcement and explicit identity schema,
master audit and additional model/photo adapters remain PLANNED.
Do not infer code compliance from a historical policy or accepted intent. Check
[documented gaps](../../docs/AGENT_RULES_REVISION_RESULT.md) before STEP3-10 changes.
No duplicate quota/default values are prescribed here; Config SSOT remains DEC-0006.
The current subject and data counts are local validation evidence, not architecture.

Execution ownership (user policy, 2026-10-02): the canonical
[Codex Execution Policy](../../.agents/AGENTS.md#codex-execution-policy) assigns
normal full processing to ★maru using BAT + Python. Codex implements the pipeline
and performs only minimum implementation validation by default. Explicit user
investigation/audit/debug/verification requests allow scoped execution; they do
not authorize silently expanding to a full production rerun. This documents
the operating policy, not evidence that a processing run has completed.
