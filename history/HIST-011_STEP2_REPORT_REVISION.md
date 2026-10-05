# HIST-011 — STEP2 Report Revision

Date: 2026-10-02. Current generation: 71 videos, 2,001 successful measured frames.

## Trigger
The original human report exposed min/median/max and top/bottom frame examples,
which did not describe whole-dataset distribution or distinguish isolated weak
frames from video-wide technical patterns.

## Changes and rationale
Add independent CSV-only build_step2_reports.py: raw frame CSV feeds per-video CSV,
per-metric distribution CSV and comprehensive Markdown. No existing measurement,
frame rank, image, STEP1 metadata, STEP3 Gate or Historical Baseline changes.
Show P01..P99, mean/population std, video medians, cumulative saved-rank tail counts,
concentration by video, exposure distributions and descriptive Laplacian bins.
DEC-0010 is extended with this additive report view; no duplicate/new Decision.

## Results and verification
71 video rows / 7 distribution rows, sourced from exactly 2,001 unique successful
CSV rows. Global bottom 10%: 201 frames in 14 videos. v52: 57/57; v56: 29/30;
v21: 27/29. These are technical diagnostics only, not face-quality findings.
63 existing + 12 new tests = 75 PASS. Independent real-data percentile, mean/std,
per-video aggregate and tail checks PASS. Repeated derived outputs match bytes;
source reports, pre-existing scripts/tests/config/metadata/baseline and frame SHA256/
size/mtime are unchanged. EXP-20261002-004 and report revision verification provide evidence.

## Files and limits
New script/test, two report CSVs, expanded STEP2_METRICS_SUMMARY.md, additive
STEP2_RESULT revision and dedicated revision result/verification, README, Current
Knowledge, DEC-0010, experiment/history indexes. Existing measurement PASS remains.
Tail counts overlap; exposure ties may broaden tails; diagnostic video ranks do not
select frames. Multi-file abrupt-crash atomicity remains a limitation. No image is
decoded/recomputed and no plotting dependency, HTML, restoration or training added.
