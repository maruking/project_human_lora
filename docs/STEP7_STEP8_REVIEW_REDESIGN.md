# STEP7 / STEP8 Human Review redesign — implementation only

Date:2026-10-07. STEP7 version:step7_quality_coverage_v2.2;
STEP8 version:step8_folder_review_v3. This document is implementation evidence,
not a new production candidate summary.

## Behavior

STEP7 sorts the existing eligible UNIQUE/REPRESENTATIVE pool by unchanged STEP3
BEST DESC, global_rank ASC, frame_id ASC. Current-version proven Human Rejects
remain excluded; historical/PENDING state alone does not exclude. Identity weight0.

BASE is configured target70, frozen before coverage. Quality Guard remains
ceil(target × multiplier), currently140 eligible candidates, not global_rank<=140.
Missing pose/vertical/face-scale goals add highest-BEST remaining guard candidates.
No BASE eviction, source cap exclusion or10-repair-slot budget. Caps are warnings.
No good option in guard means shortage remains. Coverage goals/final guidance unchanged.
Candidate total can exceed70; every upstream row/value retained in full audit.

STEP8 directories:

```text
00_ALL_RANKED
01_BY_SHOT/{CLOSE_UP,UPPER_BODY,FULL_BODY}
02_BY_POSE/{FRONTAL,THREE_QUARTER_LEFT,THREE_QUARTER_RIGHT,PROFILE_LEFT,PROFILE_RIGHT}
03_BY_VERTICAL/{LOOKING_UP,LEVEL,LOOKING_DOWN}
99_ACCEPT
```

Each view has BEST-descending copies with O-prefixed filenames. One frame can
appear in several views; one manifest row per frame. Only99_ACCEPT determines
unique-frame acceptance. NOT_EVALUABLE stays in ALL. Review copies must remain
unchanged. Count35–45/target40 and guidance unchanged. FULL_BODY is the inherited
face-scale label, not new physical body detection. Old review history/choices stay
untouched. Future v2→v3 migration requires explicit --reset-review and archives
prior review before rebuild. STEP8 prepare is not the current next action.

## Changed files in this task

- bat/07_score_lora_candidates.bat
- scripts/step7_candidate_selection_v22.py (new normal driver)
- scripts/common/candidate_selection_v22.py (new selection layer)
- scripts/step8_folder_review.py
- scripts/common/folder_review.py
- scripts/common/folder_review_v2.py (historical implementation preserved)
- config/config.yaml, config/config.example.yaml, config/config.schema.json
- config/step7_candidates_v21_legacy.json (historical settings snapshot)
- tests/test_step7_8_additive_views.py, tests/test_step8_folder_review.py,
  tests/test_step7_quality_coverage_v21.py (historical settings isolation)
- README.md, PROJECT.md, docs/README.md, this document
- knowledge/current/candidate-selection.md, human-final-review.md, configuration.md
- knowledge/decisions/DEC-0025*, DEC-0026*, DEC-0028*, decisions/README.md

## Minimum validation

59 scoped synthetic/regression tests +8 configuration tests PASS (67 total), including temporary-only image copying,
publication/collection and legacy migration. Synthetic70 BASE +2 additions retains
all70 and displays PROFILE_RIGHT/FULL_BODY despite source concentration. No weak
candidate outside guard admitted; full rows/BEST unchanged. Multi-view copies do
not count as accepts;99_ACCEPT counts each frame once. Current preflight-only PASS:
1951 upstream rows,762 normal eligible,4 authoritative current-version Rejects.
Versions read from bound upstream summaries:
best_rank_v2.2 / step4_pose_composition_v3 / step5_dedup_v2 / step6_identity_v2.
No image inference or actual production selection/publication in this task.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, both pipeline/lineage rules;
related Current Knowledge/Decisions/Failures/Cases/History/Experiments reviewed.
Data lineage preserved:YES. Full-row preservation:YES (synthetic verification;
current1951-row formal input read only). Historical evidence preserved:YES.
Config SSOT preserved:YES. STEP3–6, source images, previous production reports,
Human Review choices and BEST/rank unchanged by this task. Remaining readiness:
actual coverage depends on ★maru's production rerun. No additional detector or quality
threshold introduced. Failures/Cases/History/Experiments checked; no updates required.

Full production executed:NO. STEP8 prepare executed:NO.

★maru: run bat/07_score_lora_candidates.bat and share the newly generated
STEP7_CANDIDATE_SUMMARY.md with Chappy. Do not run STEP8 prepare yet.
