---
id: DEC-0025
title: STEP7 bounded BEST quality core with optional soft coverage repair
status: SUPERSEDED
date: 2026-10-05
confidence: MEDIUM
components: [candidate-selection, human-review, lineage]
tags: [quality-guard, best-authority, soft-coverage]
supersedes: [DEC-0024]
superseded_by: [DEC-0028]
related_experiments: []
related_failures: [FAIL-0003]
related_cases: [CASE-0005]
---

# DEC-0025 — STEP7 quality coverage v2.1

## Context / previous approach

DEC-0024 seeded coverage before quality. Current v2 production after the Reject
patch records47 COVERAGE_OPTION /23 BEST_SCORE_FILL. Its full-universe coverage
search could descend deeply; the documented global_rank730 replacement is regression
evidence, not a filename exception. v2 code, reports and patch documentation remain historical.

## Decision / rejected alternatives

Active version step7_quality_coverage_v2.1. Preserve authoritative same-version
best_rank_v2.2 Human Reject exclusion. Reject/PENDING/favorite history is never a
score feature; old-version Reject is not an exclusion. BEST/global_rank unchanged;
STEP6 identity weight0. Normal universe remains eligible UNIQUE/REPRESENTATIVE
without upstream errors, minus confirmed current Rejects; all audit rows remain.

Before any coverage: sort normal candidates BEST DESC/global_rank ASC/frame_id ASC.
Guard size = ceil(configured target × multiplier). Defaults target70 ×2.0=140.
The guard is a bounded candidate-order region, not a physical quality threshold
or global_rank<=140 requirement. Never expand it to rescue coverage/count.

Select configured60 BEST_QUALITY_CORE by pure BEST, cap6 per video/15 collective
stills/one per cluster. Freeze the core; no coverage substitution. Fewer than core
target produces QUALITY_CORE_SHORTAGE and blocks formal publication. Fewer than
minimum60 also produces QUALITY_POOL_INSUFFICIENT. Partial/blocked output isolated.

At most10 COVERAGE_REPAIR from the same guard's unselected remainder: greatest
number of unmet pose/vertical/scale dimensions, then BEST tie. Stop if no useful
allowed candidate. Fill unused slots by BEST_SCORE_FILL within the same guard.
No score bonus/new ranking or final training selection. Review target70/min60/max70.
60–69 can publish with POOL_BELOW_TARGET_QUALITY_PRESERVED; no forced weak fillers.

Soft desired options: pose15/10/10/2/2, up/down2 each, face scale12/18/12.
Unmet targets are COVERAGE_SHORTAGE, including source-cap conflicts; they alone
do not BLOCK. Caps are never relaxed. Remaining meaningful coverage is reported
for Chappy/STEP8. Historical minimum-quota failure FAIL-0003 remains relevant;
the accepted quality boundary explicitly permits shortage rather than inventing options.

Rejected alternatives: larger automatic guard, profile quota rescue outside guard,
filename blacklist, replacing BEST core, rushed semantic occlusion inference.
CASE-0005 records semantic obstruction as deferred evidence, not a new detector.

## Evidence / validated scope / limitations

Read-only current-data simulation:1951 full rows,1075 normal candidates after4
current-version Rejects; guard140 with minBEST49.75513992839904/deepest rank232;
core60/repair0/fill10, selected70/deepest rank181. PROFILE_LEFT0 of desired2:
two guard options are blocked by the supplemental-still source cap. Soft shortage
is reported and cap retained. No hard quality shortage. No official publication.

65 STEP7 tests (v2/history retained plus25 v2.1 tests) validate bounded behavior,
core/repair/fill, soft shortage, blocked/partial publication, full rows and unchanged
scores. Config/BAT minimum checks are recorded in implementation report.
This does not prove photographic quality, semantic occlusion accuracy, identity
calibration, greedy optimality or final LoRA suitability. STEP8+ remains deferred.

[Implementation report](../../docs/STEP7_CANDIDATE_V21_IMPLEMENTATION.md).

2026-10-07: presentation/selection policy superseded by [DEC-0028](DEC-0028-step7-base-additive-step8-views.md). Earlier evidence and review history preserved.
