---
topic: candidate-selection
last_updated: 2026-10-05
status: ACTIVE
confidence: MEDIUM
related_decisions: [DEC-0025]
related_failures: [FAIL-0003]
related_cases: [CASE-0005]
---

# STEP7 quality / coverage review options

step7_quality_coverage_v2.1 is the active normal STEP7 BAT path. It replaces v2/Revision B
for this pipeline generation, preserving old code/sidecars/Decisions. STEP3 BEST
is the sole quality authority; identity similarity/state/preferences/A-B-C contribute0
to quality priority. Only authoritative, same-version explicit REVIEW_REJECT decisions
with current image/generation/ranking evidence exclude from candidate eligibility.
Historical-version Rejects and PENDING remain eligible. Quality copy stays byte-value equivalent to best_score.
Tie:BEST DESC/global_rank ASC/frame_id ASC. Human preferences belong to STEP8.

Normal pool:ranking_eligible + UNIQUE/REPRESENTATIVE without upstream errors.
Exclude confirmed current best_rank_v2.2 Human Rejects without changing BEST or
global_rank; preserve their audit rows as CURRENT_VERSION_HUMAN_REJECT.
All STEP3–6 rows/columns preserved, duplicates/fatal/errors not deleted. STEP6
REJECT/REVIEW/NOT_EVALUABLE remain eligible diagnostics; LOW_MEASURED_IDENTITY is
not a wrong-person label. Identity fallback flag never promotes cluster members.

Config defaults target70/min60/max70; quality guard=ceil(target ×2.0), normally140
BEST-ordered eligible rows after authoritative exclusions. Guard order is not
global_rank<=140. Core60 is fixed first by BEST under source/cluster constraints.
At most10 optional repairs maximize unmet soft axes then BEST; unused slots return
to BEST fill inside the same guard. Core images are never replaced for coverage.
Soft pose15/10/10/2/2, up/down2 each, scale12/18/12. Caps6 eachformal video,
15 collective stills, one per cluster remain diversity constraints, not penalties.

Unavailable soft coverage/source-cap conflicts become COVERAGE_SHORTAGE warnings;
do not BLOCK solely for coverage. Core shortage blocks formal publication; below60
also reports QUALITY_POOL_INSUFFICIENT.60–69 can publish with quality-preserved
warning. No automatic guard expansion, cap relaxation or weak fillers.
Partial/test output is isolated and cannot replace full successful reports.
Source-linked pose→scale HTML is STEP8 handoff, not automatic final35–45 selection.
FULL_BODY is face area, not literal body visibility. No image copying/inference.

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

## Active v2.1 read-only validation / residual

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
