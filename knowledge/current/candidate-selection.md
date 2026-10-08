---
topic: candidate-selection
last_updated: 2026-10-07
status: ACTIVE
confidence: MEDIUM
related_decisions: [DEC-0028]
related_failures: [FAIL-0003]
related_cases: [CASE-0005]
---

# STEP7 quality / coverage review options

2026-10-06 metadata bridge: input_versions derives from official upstream summary
hashes (current STEP4 v3), not fixed labels. Human Review binds to authoritative
STEP3 ranking; valid downstream pose replacement is not ranking-history mutation.
Full current frame/image/generation/score/rank checks and the4 current Rejects
remain. Normal07 preflight PASS1951 rows;28 synthetic tests; no production selection.
See [result](../../docs/STEP7_UPSTREAM_VERSION_METADATA_FIX.md).

## Active STEP7 v2.2 — BASE plus additive coverage

Normal BAT runs step7_quality_coverage_v2.2. Eligibility remains ranking_eligible +
UNIQUE/REPRESENTATIVE, no upstream errors, minus proven current-version Human Rejects.
PENDING/historical-only Rejects remain eligible. BEST DESC/global_rank ASC/frame_id
ASC remains the sole priority; identity weight0, upstream score/rank unchanged.

Take configured target70 as immutable BASE. Quality Guard remains ceil(target ×2)
normal candidates (default140). Fill deficient stored pose/vertical/face-scale goals
with highest-BEST remaining candidates inside that guard, adding rather than replacing.
Source caps6/15 are concentration warnings only. No repair-slot budget.
Profile-only exception: after ordinary coverage, fill each side toward configured
rare_profile_review_target (default3, allowed2–3), from all eligible rows by BEST.
Mark RARE_PROFILE_REVIEW / rare_profile_candidate, preserving truthful guard membership.
Never drop existing BASE/coverage rows even if a profile already exceeds3; no extra
top-up then. Normal shot/vertical coverage cannot search outside guard. No auto-accept. BASE shortage blocks publication; coverage shortages warn.
Full upstream rows/values remain; source images and previous reviews are unchanged.

STEP8 v3 shows ALL/SHOT/POSE/VERTICAL copies and uses only99_ACCEPT for decisions.
Count35–45/target40 and guidance stay unchanged. Synthetic validation and preflight
only; production candidate counts await ★maru rerun07, then Chappy review.
[Decision](../decisions/DEC-0028-step7-base-additive-step8-views.md),
[implementation](../../docs/STEP7_STEP8_REVIEW_REDESIGN.md).

## Historical v2 implementation-time snapshot

Observed then:1951 full rows,1079 normal candidates. Category-level
availability/cap bounds support requested minima; joint selection not run by Codex.
28 synthetic tests +8 config tests, normal BAT preflight-only PASS. Production
pool size/remaining shortages/visual review pending ★maru after Chappy review.
STEP8+ remains deferred; normal runner still stops after STEP5.
[DEC-0024](../decisions/DEC-0024-step7-quality-coverage-review-pool.md),
[implementation](../../docs/STEP7_CANDIDATE_V2_IMPLEMENTATION.md).

## Current-version Human Reject eligibility correction — 2026-10-05

Read-only recomputation found4 current Rejects in the prior70 pool;9 old-version-only
Rejects remain normal candidates. With the correction:1075 normal candidates,
70 review options, no coverage shortage/source-cap conflict.40 tests PASS. Formal
publication is pending ★maru's BAT rerun; original reports/history are unchanged.
See [patch report](../../docs/STEP7_CURRENT_VERSION_REJECT_PATCH.md) and DEC-0024 amendment.

## Historical v2.1 read-only validation / residual

1951 full rows/1075 normal candidates;4 current-version Rejects excluded,9
historical-only Rejects remain eligible. Guard140/deepest rank232/minBEST49.75514;
core60/repair0/fill10, selected70/deepest rank181. PROFILE_LEFT lacks2 options
because its2 guard candidates are source-cap blocked. Soft shortage preserved,
not a production result or photographic suitability claim.65 STEP7 tests PASS.
v2.1 production publication awaits Chappy confirmation and ★maru BAT execution.

STEP3 visual/geometry metrics can miss semantic hand/object obstruction of central
face regions. User-reported residual, exemplar identity not provided, no detector
inference/filename rule introduced. Post-pipeline generic work remains deferred:
[CASE-0005](../cases/CASE-0005-semantic-face-obstruction-residual.md).
[DEC-0025](../decisions/DEC-0025-step7-bounded-quality-first.md),
[v2.1 implementation](../../docs/STEP7_CANDIDATE_V21_IMPLEMENTATION.md).

[Rare Profile patch](../../docs/STEP7_RARE_PROFILE_IMPLEMENTATION.md): synthetic tests and preflight only; production07 rerun pending, STEP8 prepare deferred.
