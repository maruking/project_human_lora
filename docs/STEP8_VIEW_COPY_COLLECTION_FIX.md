# STEP8 collect VIEW copy repair — 2026-10-07

## Observed cause

Current review manifest has74 candidates and294 expected VIEW copies. All are present.
Two extra VIEW files have Explorer-style "- copy" names; each is byte-identical
(SHA256) to a candidate expected in that same VIEW.99_ACCEPT contains40 known names.
The old actual==expected VIEW inventory guard stopped on these2 extras and emitted
only "VIEW must retain every candidate copy", misleadingly suggesting missing copies.

## Correction

Ignore only byte-identical redundant VIEW copies in their correct VIEW. They create
neither new candidates nor accepts. Pin their hashes for collection integrity;
record ignored paths/count in summary JSON, count in Markdown and console warning.
Unknown bytes, wrong-category extras, missing/edited required copies, unknown or
renamed99_ACCEPT files still stop. Missing-copy errors now report count/paths.
No image deletion/movement, no reprepare/reset, no change to score/selection/thresholds.

Changed: scripts/common/folder_review.py, scripts/step8_folder_review.py,
tests/test_step8_view_duplicates.py, knowledge/current/human-final-review.md,
knowledge/decisions/DEC-0028-step7-base-additive-step8-views.md, docs/README.md,
this report. Config and BAT unchanged.

Minimum validation:31 STEP8 synthetic tests PASS. Read-only current-data verification
PASS:1951 full rows,74 candidates,40 accepted,VALID. Checked input/preparation/manifest,
all required VIEW and ACCEPT hashes; computed selection in memory only. No report
publication or production collect performed. Tests use disposable temporary folders.

Rules checked:AGENTS.md,.agents/AGENTS.md,PROJECT.md,both pipeline/lineage rules;
relevant Current Knowledge/Decision/Failures/Cases and earlier results reviewed.
History/Experiments checked; no updates needed. Data lineage preserved:YES.
Full-row preservation:YES (1951 rows verified in memory). Historical evidence:YES.
Config SSOT:YES. Rules conflict:NO. Existing reviews/choices/report evidence unchanged.

Full production executed:NO. Prepare/reset executed:NO. STEP3–7 unchanged.

★maru: rerun bat/08_collect_folder_review.bat. Do not reprepare/reset the review.
