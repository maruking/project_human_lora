# STEP 2 Report Revision Result

Date: 2026-10-02 (Asia/Tokyo). Authoritative local working tree; no commit/push.

## Status
PASS. Existing STEP2 measurement PASS is retained. Report-only aggregation completed;
no image metric, saved global/per-video rank, image or Gate was recalculated/modified.

## Source Dataset
- Videos: 71; frames/CSV rows/successful rows/unique filenames: 2,001; errors: 0.
- Policy version 2, requested FPS 2.0, max frames/video 120.
- Formal source: output/reports/step2_dataset_report.csv.
- Source CSV SHA256: a133656bf487f1d1c7f1add08e5943420254ca8270c499b3a87ce2a4b5602a63.
- STEP1/STEP2 summaries, manifest IDs, per-video counts and policy/FPS traceability agree.

## Added Reports
- output/reports/step2_video_summary.csv: 71 video aggregate rows; requested statistics,
  median diagnostic percentiles/ranks and saved global-rank tail counts/ratios.
- output/reports/step2_distribution_summary.csv: 7 metric rows; min, P01/P05/P10/P25/
  P50/P75/P90/P95/P99, max, mean and population std.
- docs/STEP2_METRICS_SUMMARY.md: expanded dataset/video/frame human report, percentile
  bucket frame/video counts, exposure tails, diagnostic histogram and preserved examples.
- scripts/build_step2_reports.py: independent CSV-only regeneration command.

## Distribution Summary

| Metric | P01 | P05 | P10 | P25 | P50 | P75 | P90 | P95 | P99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| laplacian_score | 2.684 | 4.075 | 5.598 | 9.501 | 27.021 | 97.97 | 244.22 | 632.503 | 938.078 |
| tenengrad_score | 145.393 | 271.564 | 387.196 | 607.995 | 1490.21 | 3561.73 | 7037.714 | 11229.839 | 19061.795 |


Linear interpolation of stored CSV values; population std (ddof=0); 6-decimal aggregates.
The wide gradient tails are visible in P90..P99, not just extremes. They do not establish
face sharpness or a rejection threshold. All seven distributions and exposure counts
are in [STEP2_METRICS_SUMMARY](STEP2_METRICS_SUMMARY.md).

## Video-Level Findings
Lowest diagnostic median videos (ascending technical tendency): Sasha_v52, Sasha_v56, Sasha_v21, Sasha_v59, Sasha_v03, Sasha_v70, Sasha_v57, Sasha_v30, Sasha_v10, Sasha_v50.

Highest diagnostic median videos: Sasha_v53, Sasha_v23, Sasha_v67, Sasha_v05, Sasha_v08, Sasha_v32, Sasha_v60, Sasha_v19, Sasha_v13, Sasha_v63.

Highest bottom-10% concentration:

| video_id | Frames | Bottom 10% count | Ratio |
| --- | ---: | ---: | ---: |
| Sasha_v52 | 57 | 57 | 100.0000% |
| Sasha_v56 | 30 | 29 | 96.6667% |
| Sasha_v21 | 29 | 27 | 93.1034% |
| Sasha_v59 | 30 | 14 | 46.6667% |
| Sasha_v03 | 120 | 44 | 36.6667% |
| Sasha_v30 | 27 | 7 | 25.9259% |
| Sasha_v57 | 44 | 7 | 15.9091% |
| Sasha_v49 | 30 | 4 | 13.3333% |
| Sasha_v48 | 23 | 3 | 13.0435% |
| Sasha_v70 | 24 | 3 | 12.5000% |


The global bottom 10% contains 201 frames from 14 videos; bottom 5% contains 101
from 11 videos and bottom 1% contains 21 from 6 videos. Sasha_v52 has all 57 frames
in bottom 10%; v56 has 29/30 and v21 has 27/29. These are whole-frame technical
patterns for inspection, not proof of poor faces or authorization to delete frames.
The three median/concentration lists are presented separately in the human report.

## Method and Integrity
Use saved quality_rank only (1 = highest); a tail p% contains ceil(N*p/100) frames.
Tail counts are cumulative and overlap. Middle bands exclude both 10% tails and
split at ceil(N*25/50/75%). Exposure tails use inclusive dataset-percentile cutoffs,
so ties can exceed nominal percentages. Histogram bins are descriptive, not Gates.
Video diagnostic technical median percentile averages Laplacian/Tenengrad median
percentiles across videos. Each indexes sorted unique medians 0..100 (single/all-equal
=100); natural video IDs break rank ties. Existing frame scores/ranks stay untouched.
The builder validates CSV statuses, identity/uniqueness/saved rank coverage and formal
STEP1/STEP2 counts/policy before staging and publishing reports. Bad input leaves
previous successful derived reports unchanged and exits nonzero.

## Tests
Previous: 63 PASS, unchanged. New: 12 PASS. Total: 75 PASS.
Tests cover known 1..100 percentiles, 3-video aggregates/tails, stale-free replacement,
duplicate filenames, byte-identical replay/source preservation, missing/error rows,
missing-count/nonfinite/metadata mismatch, bucket counts/video spread, publication
rollback and Unicode CSV paths. Real-data distributions were independently checked
with exact linear interpolation plus statistics.mean/pstdev; all per-video aggregates
and tail counts were checked. Repeated CSV/Markdown output is byte-identical.

## Documentation
README: regeneration command, output roles, CLI and formulas updated.
Knowledge: face-quality.md and technical-image-metrics.md emphasize distribution/
video overview before isolated examples, and separate technical from face quality.
Decision: existing DEC-0010 extended with report architecture and EXP-20261002-004;
no duplicate Decision or new threshold record added.
History: HIST-011_STEP2_REPORT_REVISION.md added. STEP2_RESULT.md has an additive
Report Revision section; existing measurement PASS and historical evidence remain.
Evidence: [report verification](STEP2_REPORT_REVISION_VERIFICATION.json); private
output/reports/step2_report_revision_audit/ holds snapshots, logs and prior report.

## Existing Metrics Changed
NO. Source CSV/summary/outliers, all pre-existing scripts/tests/config and formal
STEP1 metadata are byte-identical to before this revision. All 2,001 frames preserve
SHA256, size and mtime. Historical Baseline and original STEP2 verification are unchanged.

## STEP3 Logic Changed
NO. No STEP3 Gate, face/identity/selection logic or blur threshold changed.

## Ready for STEP3
YES — existing technical measurement remains PASS and human-review summaries are ready.
STEP3 facial-region evaluation has not been run or revalidated by this report revision.

## Notes
No plotting/HTML/dashboard or additional dependency. Derived files use individually
atomic replacements and rollback on ordinary failures; abrupt power/process loss
between files is not a multi-file transaction. Rerun aggregation if interrupted.
No underlying image file is opened by the generator; integrity hashing is a separate
read-only verification. No face evaluation, selection, deletion, restoration or training.
