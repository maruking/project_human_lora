# HIST-010 — STEP2 Current Generation Technical Metrics

Date: 2026-10-02. STEP1 Revision 2 active generation: 71 videos / 2,001 PNG.

## Trigger and implementation
The optional legacy CSV merge in DEC-0008 could carry old-generation rows after
sampling-policy changes. DEC-0010 supersedes that contract; all retained metric
formulas and measurement-only responsibilities remain. Preflight now checks formal
STEP1 total/per-video counts, inventory, grammar and content before scoring, with
postflight and a shared lock. Metadata traceability and independently computed
per-video percentiles/ranks are added. Report sets are staged, historical artifacts
archived, and failed runs isolated without overwriting the previous good set.

## Changed files
score_blur.py, common/metric_report.py, new common/metric_generation.py,
config.schema.json, test_image_metrics.py, STEP2 BAT, README, relevant Current
Knowledge/Decision/experiment/history indexes and STEP2 result/metrics/verification.
See docs/STEP2_RESULT.md for the full change list and actual distributions/examples.

## Evidence
63 tests PASS; 2,001/2,001 processed successfully with zero errors and 71 video-count
matches. All old formulas/global ranks and per-video old-formula rankings match.
Repeated CSV/JSON/outlier bytes match. Media hashes, current/archived frame timestamps,
local config, STEP1 docs/code, STEP3+ code and Historical Baseline are preserved.
EXP-20261002-003 and docs/STEP2_VERIFICATION.json supply the evidence.

## Preserved history and remaining risks
Previous 3,550 technical results and 3,607-frame face evidence remain Historical
Baseline, with fixed50 result docs saved separately. No quality gate, deletion,
restoration, quota or face/identity/pose assessment is added. Compression detection
is unvalidated. Abrupt power loss between individually atomic report replacements
can mix artifacts; downstream must check generation/counts and rerun when needed.
Ready for STEP3 means technical input complete, not face/suitability approval.
