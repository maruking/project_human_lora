---
id: DEC-0011
title: Mandatory Project Entry and Full Frame Lineage
status: ACCEPTED
date: 2026-10-02
confidence: MEDIUM
components: [agent-governance, data-lineage, multi-subject]
tags: [project-entry, full-audit, model-independence]
supersedes: []
superseded_by: []
related_experiments: []
related_failures: [FAIL-0001, FAIL-0002, FAIL-0003]
related_cases: [CASE-0002, CASE-0003]
---

# Decision Record: DEC-0011

## Context and existing Decisions
Root AGENTS previously routed first to Knowledge without requiring Project Rules;
.agents/AGENTS.md did not exist. Rules mixed intended quotas/component restoration
with implementation claims. DEC-0006/7/9/10 already cover config, stable video IDs,
extraction generations and current STEP2 reports; do not duplicate them.
The generic multi-subject mission, mandatory Project/Rules read order and full
cross-STEP audit universe were not recorded as a complete governance contract.

## Decision
Root AGENTS is a thin explicit router to canonical .agents/AGENTS.md. Require PROJECT,
pipeline/data lineage rules before Current/accepted Decisions/Failures/Cases/results.
Separate project purpose, operating protocol, pipeline rules and lineage rules.
All full-frame audit STEPs retain the same generation's identities and rejection/
skip/selection reasons. Selected exports/summaries cannot replace the full audit.
Conceptual subject/generation/video/frame keys allow complete generation-safe joins;
introduce missing schema fields compatibly later. Dataset evaluation remains
independent of training adapters; generalized photos/master audit/adapters are planned.

## Alternatives and consequences
Knowledge-only routing can omit Hard Rules. Copying every rule into root AGENTS
creates conflicting sources. Forcing legacy code to obey new documentation now
exceeds documentation scope; record gaps and defer scoped implementations instead.
Preserve historic policy/evidence and distinguish ACTIVE requirements from enforcement.
No prior sampling/Gate/quota Decision or algorithm is silently superseded.

## Evidence and limits
Facts: local file/link/routing and protected-source checks validate this documentation
structure; no algorithm or inference test is needed or claimed. The result lists
existing quota, restoration, subset-report and runner-bypass gaps.
Interpretation: explicit root routing makes required references discoverable within
this repository's agent protocol; it is not a guarantee that an unrelated session
starting outside the repository will automatically load them. Start here and follow
root instructions. Acceptance covers governance, not implemented STEP3-10 lineage,
multiple-subject production validation or training adapter completeness.


## STEP3 implementation evidence
[STEP3_RESULT](../../docs/STEP3_RESULT.md) and [EXP-20261002-005](../../experiments/EXP-20261002-005-step3-full-audit.md) validate full-row preservation for STEP3 only. Later STEP/master audit gaps remain planned.
