---
id: DEC-0028
title: Immutable BEST BASE and additive coverage with multi-view Human Review
status: ACCEPTED
date: 2026-10-07
confidence: MEDIUM
components: [candidate-selection, human-review, lineage]
tags: [best-authority, additive-coverage, multi-view]
supersedes: [DEC-0025, DEC-0026]
superseded_by: []
related_experiments: []
related_failures: [FAIL-0003]
related_cases: [CASE-0005]
---

# Decision / rationale

User authorized STEP7/8 redesign: caps and fixed70 total previously hid useful
category options. Keep top configured70 eligible BEST as BASE. Never evict it for
coverage. Add highest-BEST deficient pose/shot/vertical options only inside existing
Quality Guard (default140 normal eligible rows). Source caps are diagnostic only;
no maximum10 repair budget. No guard expansion or invented candidates. Deficits
remain warnings; BASE shortage prevents formal publication. BEST/global_rank,
identity0, eligibility/current-version Human Reject exclusion, STEP3–6 unchanged.

STEP8 v3 materializes ALL plus shot/pose/vertical views; duplicate appearances allowed.
Only99_ACCEPT determines unique frame decisions. Count35–45/target40 and guidance
remain unchanged. All source/manifest hashes and full audit preserved. NOT_EVALUABLE
is visible in ALL. Old v2 source preserved as folder_review_v2.py, old settings as
step7_candidates_v21_legacy.json. Future migration requires explicit reset/archive.

# Evidence / limitations

59 scoped tests pass using temporary synthetic data, including retained BASE70,
source cap warnings, profile/full-body additions, multi-view single acceptance,
legacy-choice archive, unchanged upstream fields and derived publication.
Current STEP7 preflight-only passed1951 rows/762 normal eligible/4 current Rejects.
No current-data selection or STEP8 prepare/collect ran. No claim of photographic
quality or sufficient actual production coverage. Source cap warnings may increase;
views consume more disk copies. FULL_BODY is inherited face-scale classification,
not a new body visibility detector. CASE-0005 residual remains outside scope.

★maru reruns07, shares summary with Chappy. STEP8 prepare remains deferred.
[Implementation](../../docs/STEP7_STEP8_REVIEW_REDESIGN.md).

## 2026-10-07 user-authorized Rare Profile amendment

Supersedes only the original all-additions-inside-guard restriction for profiles.
BASE and normal pose/shot/vertical coverage remain unchanged. After normal coverage,
fill each PROFILE_LEFT/RIGHT toward config rare_profile_review_target (default3,
allowed2–3), searching all eligible rows by unchanged BEST. Mark RARE_PROFILE_REVIEW,
rare_profile_candidate=true and actual guard membership. Human Reject/fatal/duplicate
members cannot qualify; image/generation/current-review hash proof unchanged.
Already selected BASE/coverage profiles are not removed if above3; top-up simply adds0.
No automatic adoption or quality assertion. Shortage remains if eligible data lacks
options. STEP8 validates the explicit profile-only exception for future preparation;
no preparation performed. This extends candidate scope, not physical quality claims.
[Patch implementation/validation](../../docs/STEP7_RARE_PROFILE_IMPLEMENTATION.md).

## 2026-10-07 VIEW duplicate-copy collection repair

Observed:74 candidates/294 expected copies all present;2 Explorer-style extra copies
match expected candidate hashes in their own shot views;99_ACCEPT contains40 known
filenames. Previous exact inventory check rejected these harmless duplicate views.
A redundant VIEW copy may be ignored only when its SHA256 matches a candidate
expected in the same VIEW. Record paths/count and pin hashes during collection;
never infer an ACCEPT from it. Missing/edited/unknown/misplaced images remain errors;
99_ACCEPT filenames remain exact manifest matches. No duplicate deletion/rename,
prepare reset, upstream processing or production collect performed by Codex.
[Repair evidence](../../docs/STEP8_VIEW_COPY_COLLECTION_FIX.md).
