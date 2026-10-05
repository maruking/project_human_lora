---
id: DEC-0013
title: Revision B report-only candidate selection with confirmed reserves
status: SUPERSEDED
date: 2026-10-02
confidence: MEDIUM
components: [candidate-selection, data-lineage]
tags: [coverage, reserve, human-review, deterministic]
supersedes: []
superseded_by: [DEC-0024]
related_experiments: []
related_failures: [FAIL-0003]
related_cases: []
---

# DEC-0013 — Revision B candidate proposal

User explicitly authorizes a new downstream selection design targeting about 40
images within 35–45, distinct from the historical 65-candidate STEP7 implementation.
DEC-0005's diversity principle and DEC-0012's separate A/B/C policy remain applicable.
No upstream Gate/classifier/identity algorithm changes are authorized.

Use confirmed A first and confirmed usable B only for actual coverage or minimum
count shortages. Pending B stays review reserve and C is never resurrected.
Coverage-aware deterministic choice, duplicate-group limits and source caps apply
throughout; report unsatisfied constraints rather than forcing unsafe selections.
Expression unknown is not natural, and absent identity evidence requires review.

Consume complete current-generation audit/sidecar inputs with generation/hash and
retained-field checks. Publish full audit, selected and reserve subsets plus summary.
Report-only outputs do not directly materialize legacy STEP8 inputs; normal runner
stops after STEP7 until a separate STEP8 handoff revision. Preserve legacy code and
historical outputs. Runtime allocation settings live in SSOT, not this Decision.

Evidence: eight synthetic selection/join/publication tests plus configuration and
BAT-help validation in [implementation result](../../docs/STEP7_REVISION_B_RESULT.md).
Acceptance is of the explicit user design; production coverage, optimality,
calibration and resulting LoRA quality are unvalidated. No production run performed.

## Supersession — 2026-10-05

DEC-0024 supersedes this STEP7 runtime architecture for the current BEST2.2/STEP4–6 v2 generation. Original design/evidence above and legacy code remain historical. DEC-0012 sidecar history is preserved, not a dependency of new STEP7.
