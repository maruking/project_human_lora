---
id: EXP-20261002-004
date: 2026-10-02
status: VALIDATED
confidence: HIGH
related_decisions: [DEC-0010]
related_failures: [FAIL-0002]
related_cases: [CASE-0002, CASE-0003]
---

# STEP2 CSV-only report aggregation

## Objective and procedure
Add dataset/video/frame reporting without changing successful measurement output.
Validate source CSV identities, status, stored global rank coverage and STEP1/STEP2
metadata. Aggregate stored values with linear percentiles and population std; count
saved global-rank tails. Repeat derived report generation, compare bytes and hash
all existing scripts/tests/config/metadata/machine reports and current frames.
Independently verify actual quantiles by exact linear interpolation and mean/pstdev.

## Facts
71 videos / 2,001 successful unique frame rows / zero errors. Derived video CSV:
71 rows; distribution CSV: 7 rows. 63 prior + 12 new tests = 75 PASS.
Source CSV SHA256 a133656bf487f1d1c7f1add08e5943420254ca8270c499b3a87ce2a4b5602a63
remains unchanged. Derived CSV/Markdown bytes are deterministic; existing metadata,
code/config/baseline and all frame SHA256/size/mtime remain unchanged.

| Metric | P01 | P05 | P10 | P25 | P50 | P75 | P90 | P95 | P99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| laplacian_score | 2.684 | 4.075 | 5.598 | 9.501 | 27.021 | 97.97 | 244.22 | 632.503 | 938.078 |
| tenengrad_score | 145.393 | 271.564 | 387.196 | 607.995 | 1490.21 | 3561.73 | 7037.714 | 11229.839 | 19061.795 |

Global bottom 10%: 201 frames, 14 videos. Bottom 5%: 101/11; bottom 1%: 21/6.
Video52 has 57/57 frames in bottom 10%, video56 29/30, video21 27/29.

## Interpretation and limits
Technical tails and video medians locate patterns to inspect; they are not face,
identity or LoRA suitability. Frame totals are frame-weighted; video comparisons
are separate. Tail counts are cumulative/overlapping; percentile cutoff ties can
increase exposure counts. No metric/rank/Gate, selection, deletion or image changes.
No plots or new dependency. Report-file replacement is individually atomic, not a
multi-file power-loss transaction. See docs/STEP2_REPORT_REVISION_RESULT.md and
STEP2_REPORT_REVISION_VERIFICATION.json; private report audit holds full evidence.
