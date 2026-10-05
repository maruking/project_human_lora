---
topic: human-final-review
last_updated: 2026-10-05
status: ACTIVE
confidence: MEDIUM
related_decisions: [DEC-0026]
related_failures: []
related_cases: [CASE-0005]
---

# STEP8 Folder-Based Human Final Review

step8_folder_review_v2 is the active Human final-selection workflow. STEP7 remains
BEST/coverage v2.1 options only. Validate full/current STEP7 evidence and current
best_rank_v2.2 Reject exclusion before preparation/collection. Current input observed
70 candidates/full1951 rows; counts are not pipeline constants.

Primary UI: Explorer, work/step8_review,6 pose folders, each FULL and ACCEPT.
★maru copies desired images into ACCEPT, leaving FULL complete. No auto-selection,
notes or browser needed. Config SSOT owns count35–45/target40, soft pose/scale/up-down
guidance and report paths; pose/scale labels are inherited, not recomputed.

Normal prepare STOPs if ACCEPT nonempty; explicit reset archives old copies/choices.
Unknown/duplicate/moved/wrong-pose/edited copies or changed input/session STOP.
Collection preserves every upstream row and all values. Candidate decisions are
STEP8_ACCEPT or STEP8_NOT_SELECTED; latter is not a bad-image Reject. Fatal/nonpool
rows remain non-applicable audit rows. Count shortages/excess require Human action;
soft guidance never overrides quality or chooses more images automatically.

Final source for downstream: validated step8_human_selection.csv + VALID summary,
STEP8_ACCEPT only. ACCEPT folders are not downstream SSOT. Identity stays diagnostic;
preferences are allowed only in ★maru's Human decisions. Review/stage/archive copies
are excluded from upstream source inventories. Do not edit folders during collection.

STEP9 handoff loader is implemented/tested, but normal legacy restoration route
STOPs after CSV validation because its directory input and full-face implementation
need a separate scoped revision. No STEP9+ execution/readiness claim. Legacy STEP8
code and old outputs remain history. Existing runner still STOPs afterSTEP5.

25 synthetic tests +8 config tests +27 shared review-guard regressions PASS.
Prepare/collect BAT preflight-only PASS against current metadata. Production folder
preparation and final Human selection are ★maru's next actions, not Codex's.
[DEC-0026](../decisions/DEC-0026-step8-folder-human-final-review.md),
[implementation/operation guide](../../docs/STEP8_FOLDER_REVIEW_IMPLEMENTATION.md).
