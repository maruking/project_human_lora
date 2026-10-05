---
id: EXP-20261002-003
date: 2026-10-02
status: VALIDATED
confidence: HIGH
related_decisions: [DEC-0010]
related_cases: [CASE-0002, CASE-0003]
---

# Current generation technical metrics experiment

## Objective and procedure
Measure the complete STEP1 Revision 2 generation without changing formulas or images.
Preflight formal metadata/counts/content, measure and independently compare old local
formulas on every frame. Apply the old relative formula separately per video; compare
all global and per-video ranks. Repeat standalone BAT and compare CSV/JSON/outliers bytes.

## Facts
71 videos, 2,001 measured PNG, zero errors, exact formal inventory/count coverage.
63 unit tests PASS, including stale rows, mismatch preflight, corrupted decode audit,
Unicode paths, replay and write failure/rollback. score_image AST and all 2,001 old
metric/rank calculations match. Repeated output bytes match. Current PNG hashes/mtime,
3,550 archived PNG hashes/size/mtime, baseline and STEP3+ code remain unchanged.

| Metric | Min | Median | Max |
| --- | ---: | ---: | ---: |
| laplacian_score | 1.266 | 27.021 | 1806.418 |
| tenengrad_score | 39.76 | 1490.21 | 23652.552 |
| brightness_mean | 43.965 | 136.231 | 198.438 |
| brightness_std | 26.439 | 56.249 | 93.83 |
| shadow_pixel_ratio | 0.0 | 0.039 | 0.605 |
| highlight_pixel_ratio | 0.0 | 0.017 | 0.247 |
| contrast_p90_p10 | 57.0 | 149.0 | 221.0 |

## Interpretation
HIGH confidence covers technical computation and provenance integrity only. Global
and per-video ranks are diagnostics. CASE-0002/0003 prevent treating these gradients
as face or LoRA suitability. No additional face-quality threshold is validated.

## Limits and artifacts
No compression detector, face/identity/pose inference, selection, deletion or restoration.
Hashing costs IO; multi-file crash atomicity is not guaranteed. See docs/STEP2_RESULT.md,
docs/STEP2_VERIFICATION.json and private output/reports/step2_generation_audit evidence.
Previous 3,550 measurements and 3,607 face-baseline frames are Historical Baseline.
