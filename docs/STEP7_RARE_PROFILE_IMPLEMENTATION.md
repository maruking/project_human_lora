# STEP7 v2.2 Rare Profile Human Review supplement

Date:2026-10-07. Implementation/minimum validation only; production pool not updated.

## Behavior

BASE configured top70 remains unchanged. Ordinary pose/shot/vertical coverage first
runs unchanged inside the Quality Guard. Then each PROFILE_LEFT/PROFILE_RIGHT is
topped up toward rare_profile_review_target (default3, configurable2–3), taking
highest-BEST unselected eligible rows. Guard candidates naturally come first;
if insufficient, eligible rows outside guard can supply profile-only choices.

Existing BASE/ordinary-coverage profiles count toward the target. If already3 or
more, no supplement; no existing image is removed even if above3 because BASE and
normal coverage are frozen. Thus3 caps the top-up target, not deletion of existing
BASE members. No candidate is automatically accepted. If fewer eligible profiles
exist, report the actual count/shortage; no current Reject, fatal/upstream error or
duplicate member recovery. Existing version/hash/generation-bound Human Reject
exclusion remains. Historical-only Rejects/PENDING do not exclude on their own.

Added rows have selection_reason=RARE_PROFILE_REVIEW and rare_profile_candidate=true.
quality_guard_member stays truthful (false outside guard). Summary records target,
before/after,added,shortage,eligible_available per side and outside-guard count.
Source caps remain diagnostic only. BEST/global_rank and identity weight0 unchanged.
Normal shot/vertical coverage never searches outside guard. Profile additions can
incidentally improve actual distributions, but do not trigger another coverage run.

STEP8 preflight now accepts an explicit eligible profile exception outside guard;
no generic bypass. Existing review/hash/99_ACCEPT authority unchanged. STEP8 prepare
has not been run. Previous production reports and Human Review remain untouched.

## Changed files

- scripts/common/candidate_selection_v22.py
- scripts/step7_candidate_selection_v22.py (summary/HTML explanation)
- scripts/step8_folder_review.py (profile exception input validation only)
- config/config.yaml,config/config.example.yaml,config/config.schema.json
- tests/test_step7_rare_profiles.py
- tests/test_step7_8_additive_views.py,tests/test_step8_folder_review.py
- README.md,PROJECT.md,docs/README.md,this report
- knowledge/current/candidate-selection.md,configuration.md,human-final-review.md
- knowledge/decisions/DEC-0028-step7-base-additive-step8-views.md (dated amendment)

Normal07 BAT already calls v2.2; no new entrypoint needed. STEP3 BEST, STEP4–6,
BASE settings,normal coverage goals,source images and prior production outputs unchanged.

## Minimum validation

48 scoped synthetic/config/regression tests PASS. Test cases include:
BASE70 retention; best-ranked eligible profiles from outside guard;3 per-side top-up;
current Reject/fatal/duplicate exclusion; existing greater-than3 BASE preservation;
shortage reporting; nonprofile guard enforcement; partial limit isolation; preserved
all rows/upstream fields; explicit STEP8 input acceptance; temporary-only derived
publication and review-copy tests. No actual source images processed/copied.

Current preflight-only PASS:1951 rows,762 normal eligible,4 current-version Rejects.
Upstream metadata:best_rank_v2.2 / step4_pose_composition_v3 / step5_dedup_v2 /
step6_identity_v2. This is metadata validation, not production selection.

Rules checked:AGENTS.md,.agents/AGENTS.md,PROJECT.md,pipeline/lineage rules;
relevant Current Knowledge/Decisions/Failures/Cases and earlier STEP results reviewed.
History/Experiments/Failures/Cases checked; no update required. Rules conflict:NO;
user explicitly authorizes the profile-only guard exception.
Data lineage preserved:YES. Full-row preservation:YES (synthetic); formal1951-row
input read only. Historical evidence preserved:YES. Config SSOT preserved:YES.
No claim of photographic profile quality or production availability. Actual pool
counts are pending ★maru's normal07 rerun.

Full batch executed:NO. STEP8 prepare executed:NO.

★maru: rerun bat/07_score_lora_candidates.bat and share the newly generated
STEP7_CANDIDATE_SUMMARY.md with Chappy. Do not run STEP8 prepare yet.
