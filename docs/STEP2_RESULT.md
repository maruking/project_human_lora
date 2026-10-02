# STEP2 Revision 1 Result — Current STEP1 Generation

Date: 2026-10-02 (Asia/Tokyo). Local working tree is authoritative; no commit/push.

## Status
PASS: every current image was measured successfully. STEP2 PASS means computation
and generation integrity, not face quality, identity, beauty filtering or LoRA suitability.

## Input Generation
STEP1 Revision 2 PASS: 71 videos, extraction policy 2, requested FPS 2.0,
max frames/video 120, 2,001 current PNG, zero failed/zero-frame videos.
Configured active input: work/frames_step1; unrelated 58 images in work/frames_raw
remain outside this generation. Existing video IDs and
<video_id>/<video_id>_<index:03d>.png names are preserved.
STEP1_RESULT.md and STEP1_VERIFICATION.json were read; runtime validation uses
work/manifests/video_manifest.csv, video_extraction.csv, step1_summary.json and
all per-video .extraction_metadata.json files. An optional extracted_frame_count
in per-video metadata is checked when present; frames inventory remains required.

Generation SHA256: `fc2a37abc81e44e456891ac7d268c2dc622255d120c944ac377dbefd491833c2`.

## Changes
- scripts/score_blur.py: prohibit stale merging; add temporal/policy provenance and
  per-video ranks; stage/publish reports with failed-run isolation and rollback.
- scripts/common/metric_generation.py: preflight exact counts, inventory, grammar,
  source SHA mapping, policy agreement, frame size/content hashes; recheck before publish.
- scripts/common/metric_report.py: accept validated inventory/provenance and include
  exposure/contrast distributions. Existing measurement formulas are preserved.
- config/config.schema.json: retain_missing_records permits false only; existing
  false config/CLI compatibility remains. Local config and STEP3 gates are unchanged.
- tests/test_image_metrics.py: preserve 53 test cases with obsolete merge expectations
  corrected and formal metadata fixtures extended; add 10 required regression cases.
- bat/02_technical_metrics.bat and README.md: current input/expected count/CSV/JSON,
  strict failure handling and relative-ranking responsibilities.
- Current Knowledge, Decisions/index, experiment/index, History/index and STEP2
  result/metrics/verification docs synchronized; historical docs retained separately.

## Metrics
Decoding is np.fromfile -> cv2.imdecode(IMREAD_COLOR), BGR2GRAY; no resizing or enhancement.
Laplacian is cv2.Laplacian(gray,CV_64F).var(); Tenengrad is mean(dx*dx+dy*dy)
for ksize=3 CV_64F Sobel x/y. Existing rounding is unchanged (3 decimals).
Width, height, file_size_bytes, brightness mean/std, shadow gray<40, highlight gray>235
and p90-p10 contrast remain. The entire score_image AST is identical to the pre-change
local version; all stored values were compared independently for all 2,001 frames.

| Metric | Min | Median | Max |
| --- | ---: | ---: | ---: |
| laplacian_score | 1.266 | 27.021 | 1806.418 |
| tenengrad_score | 39.76 | 1490.21 | 23652.552 |
| brightness_mean | 43.965 | 136.231 | 198.438 |
| brightness_std | 26.439 | 56.249 | 93.83 |
| shadow_pixel_ratio | 0.0 | 0.039 | 0.605 |
| highlight_pixel_ratio | 0.0 | 0.017 | 0.247 |
| contrast_p90_p10 | 57.0 | 149.0 | 221.0 |


STEP2 min_blur_score is absent in current SSOT; global_blur_flag_count=null means
not configured, not zero flagged frames. No threshold was invented or borrowed
from STEP3. Exposure/contrast are measurements only; no hard rejection or deletion.

## Global vs Per-Video Ranking
laplacian_percentile, tenengrad_percentile, quality_rank remain global. Corresponding
_video columns use the same calculation independently in each video. Percentile maps
sorted unique stored values to 0..100, with singleton/all-equal groups receiving 100.
Rank sorts descending sum of both percentiles, with natural filename tie-breaks.
No mtime is used. These diagnostics do not select frames or judge faces.
Highest/lowest ten filenames and values are in [STEP2_METRICS_SUMMARY](STEP2_METRICS_SUMMARY.md).

## Generation Integrity
Preflight occurs before scoring: expected 2,001 == discovered 2,001, and every one
of 71 per-video counts matches. Example: Sasha_v01 expected/discovered 19/19.
Each filename/inventory/size/SHA256 matches official STEP1 metadata. The STEP1 manifest
lock spans scoring/publication and postflight rechecks the generation.
Active CSV has exactly 2,001 unique filenames and exactly the current inventory;
no stale rows and no historical merging path remain. Writer, CLI and schema prohibit
true retention. temporal_index, policy version, requested/effective FPS are explicit
and copied from STEP1 metadata/filename grammar without independent FPS guesses.

## Tests
63/63 PASS (53 existing cases maintained, 10 added). Covered: exact 10-file snapshot;
A/B/C -> A/B stale-row removal; independent global/per-video ranks; deterministic
filename ties/replay; corrupt-image error row and nonzero exit; Unicode Windows
paths/mtime independence; count/content mismatch stopping before scorer invocation;
CSV staging failure preserving good artifacts; partial replace rollback; true retention
config rejection. Existing config, STEP1 and formula tests remain passing.

## Production Run
Standalone BAT succeeded on all 2,001 images: input/processed/success=2,001,
error=0, video=71. All 71 expected counts match and all frame identities are unique.
Initial and repeated CSV, JSON and outlier CSV are byte-identical. Final BAT on the
final code also succeeds and reproduces the same bytes. Old local formula regression
covers all 2,001 images, global ranks and independently recomputed per-video ranks.
Private logs and evidence: output/reports/step2_generation_audit/.
Formal report: output/reports/step2_dataset_report.csv;
summary: output/reports/step2_summary.json;
diagnostics: output/reports/step2_diagnostic_outliers.csv.
Failed runs retain error rows/summary in step2_run_audit/failed_*/ and preserve the
previous successful active report. Ordinary write/replace failures return nonzero.

## Documentation
Updated README, knowledge/current/face-quality.md and technical-image-metrics.md.
DEC-0010 supersedes DEC-0008's optional historical merge contract; DEC-0008's original
rationale/evidence remain as history. EXP-20261002-003 and HIST-010 record this generation.
DEC-0006 config and DEC-0007/0009 STEP1 contracts remain authoritative.

## Preserved Historical Evidence
Historical Baseline docs/VALIDATED_BASELINE.md is byte-identical (SHA256 2175683b2dbc42169d509ba607713c0e6fd1c2bf4332bd0cfd13fe08134994e8).
The older 82-video/3,607-frame face baseline is not the current generation.
Prior 71-video/3,550-PNG technical result/metrics/verification docs are preserved as
*_FIXED50_HISTORICAL files; old report CSV/JSON/outliers remain in STEP1 Revision 2 audit.
All 3,550 archived PNG match previous SHA256/size/mtime. Current 2,001 PNG match the
STEP1 Revision 2 SHA256/mtime snapshot. All 71 original videos and 71 normalized
copies match formal manifest hashes. The alternate 58 images remain present.
STEP1_RESULT, local config, baseline and all pre-existing Python scripts except
score_blur.py/common/metric_report.py remain byte-identical to pre-task snapshots.

## Risks / Notes
Hash preflight adds IO and requires complete STEP1 metadata. Reports are individually
atomic; an abrupt process/power loss between three replacements can leave a mixed
set (ordinary exceptions roll back). Check generation/counts and rerun before use.
Actors outside the shared STEP1 lock can still mutate files after final validation.
Whole-image gradients can be inflated by backgrounds, hair, clothes or compression.
No compression-artifact detector, face inference, threshold validation, candidate
selection, quotas, deletion, restoration or captions were implemented/executed.
STEP3+ algorithms and Gate values remain unchanged and were not revalidated here.

## Ready for STEP3
YES — technical report and current-generation coverage are complete. STEP3 execution
and runtime dependencies must be checked separately; this report does not claim
face quality, identity or suitability validation.

## Report Revision — 2026-10-02

PASS; the preceding STEP2 measurement PASS remains valid. Added separate CSV-only
scripts/build_step2_reports.py, step2_video_summary.csv (71 rows),
step2_distribution_summary.csv (7 metrics) and expanded STEP2_METRICS_SUMMARY.md.
Human evaluation now covers whole-dataset distributions, video median/concentration
patterns and individual examples. Existing source metrics, global/per-video ranks,
summary JSON, images, STEP1 metadata, STEP3 Gates and Historical Baseline are unchanged.
No production images were decoded or rescored. Existing 63 tests plus 12 new tests = 75 PASS.
Derived CSV/Markdown replay is byte-identical; source/media preservation is verified.
See [Report Revision Result](STEP2_REPORT_REVISION_RESULT.md),
[human report](STEP2_METRICS_SUMMARY.md) and
[report verification](STEP2_REPORT_REVISION_VERIFICATION.json).
