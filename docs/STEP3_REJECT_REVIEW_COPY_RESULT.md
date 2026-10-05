# STEP3 Reject review copies — 2026-10-03

Authorization: ★maru reported completing STEP3 and explicitly requested placing Reject images from that result. This authorizes copying the recorded Reject subset, not new inference or Gate changes.

Observed successful official result:1893 formal frames; official eligible139; diagnostic PASS51 / BORDERLINE88 / REJECT1754; analysis errors0; partial=false. CSV hash matches successful summary; STEP1/STEP2 generation and STEP3 source hash/identity set agree.

Executed bat/03_copy_reject_review.bat, which runs scripts/copy_step3_reject_review.py.
Copied1754 images (7398214495 bytes) under configured output/reports/reject/, preserving source-relative paths. No source moves/deletes, Gate rerun, selection/A/B/C changes, Human Review updates or downstream execution. The entire Reject image-copy workload was explicitly authorized and completed; full STEP3 inference batch executed:NO.

Checks: exact Reject filename set and all copy/source sizes match; sampled byte hashes match; current official STEP3 CSV hash remains unchanged. Existing passed51/borderline88 inventories match the current result and were not refreshed by this utility.27 synthetic review regressions PASS. Reject paths/aliases are excluded as temporary review inputs and ignored by Git, as are other private review copies.

Changed:
- scripts/copy_step3_reject_review.py (new; existing successful CSV/summary only; dry-run supported)
- bat/03_copy_reject_review.bat (new reproducible copy entry point)
- scripts/common/step3_review.py (Reject added to input exclusions only; normal STEP3 automatic passed/borderline transaction unchanged)
- .gitignore (private output/reports/reject copies excluded; CSV reports still tracked)
- output/reports/step3_reject_review_receipt.json (derived copy receipt; never lineage authority)
- docs/STEP3_REJECT_REVIEW_COPY_RESULT.md
- docs/README.md
- knowledge/current/face-quality.md
- knowledge/decisions/DEC-0015-eye-applicability-review-outputs.md (supplemental execution note only)

The copy utility stages a complete new Reject folder and refuses to overwrite an existing one. It does not change normal STEP3 to automatically refresh Reject copies on future runs. Copies belong to the recorded CSV hash/generation; remove disposable copies manually after review or before a new requested copy operation. Reject is the official STEP3 review state, not a new dataset-selection C decision.

Rules checked:AGENTS.md/.agents/AGENTS.md, PROJECT.md, Pipeline and Data Lineage rules; relevant Current/Decision/Failure/Case/prior result/history reviewed.
Data lineage preserved:YES. Full-row preservation:YES (official1893-row report unchanged;1754-copy derived subset).
Historical evidence preserved:YES. Config SSOT preserved:YES. Documentation/memory checked; no new threshold decision, accuracy claim, empirical experiment or failure record required. Rule conflicts:none; new explicit request extends the earlier no-Reject-copy scope for this separate materialization operation only.
