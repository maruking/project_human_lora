---
topic: technical-image-metrics
last_updated: 2026-10-02
confidence: HIGH
status: ACTIVE
related_decisions: [DEC-0010, DEC-0006, DEC-0007]
related_failures: [FAIL-0002]
related_cases: [CASE-0002, CASE-0003]
---

# Current Knowledge: STEP2 Technical Image Metrics

## Policy
STEP2 measures every supported image in the configured raw-frame root. It does
not classify GoodFace, Use/Reject, identity, pose or face quality. PASS means
measurement and STEP1 completeness, including unique relative frame identities.
Width, height, short/long edge, pixel count, aspect ratio and file size describe
the input. Brightness, global Laplacian and global Tenengrad are diagnostics.

## Definitions and compatibility
OpenCV IMREAD_COLOR -> BGR2GRAY, with no resize, denoise or enhancement.
Laplacian: `cv2.Laplacian(gray, CV_64F).var()` with existing default kernel.
Tenengrad: mean of squared x/y Sobel gradients, CV_64F, ksize=3; no square root.
Brightness: `gray.mean()`. Existing rounding to 3 decimals is preserved.
Aliases global_laplacian/laplacian_score, global_tenengrad/tenengrad_score and
mean_brightness/brightness_mean contain identical values. Existing brightness
std, shadow (<40), highlight (>235), p90-p10 contrast, percentile and quality_rank
columns remain. The legacy name quality_rank is diagnostic; it is not suitability.
Tied relative ranks inherit the deterministic natural input order; datasets with
numeric names whose lexical order differs can therefore receive different tie ranks.

## Identity, ordering and completeness
Video IDs come from STEP1 video_manifest.csv; expected counts come from matching
video_extraction.csv. Duration-aware STEP1 counts are variable; use actual recorded
counts, never a fixed total or per-video count. Prior-generation metric reports
are historical until STEP2 is rerun after an extraction-policy change. Neither ID nor frame filename is reassigned. frame_id and
legacy filename are input-root-relative paths; relative_path is project-relative
for internal inputs (input-relative for external roots). Natural numeric ordering
with explicit raw-name tie-breakers is stable across enumeration orders.
Each image produces one record, including decode/IO failures with portable error
categories. Snapshot CSV has exactly current input rows. Historical merging is prohibited, including explicit
retain_missing_records=true. Previous good outputs are archived; failed runs retain
error rows and summaries in audit and leave the active successful set untouched.
There was no computation-skipping cache; every current image is measured again.

## Interpretation boundary
Sharp background, clothes, hair, compression blocks or pixelation can inflate
whole-image edge metrics. Small faces can look soft despite high values. Metrics
are not perceptual face quality, even when calculated on a face crop. CASE-0003 is
a LOW-confidence user-reported case, not a new measured face-quality experiment.
No standalone hard gate may be introduced without an ACCEPTED Decision and
supporting experiment. Resolution buckets <720, 720–1079 and >=1080 are descriptive.
Neither low resolution nor dark/bright outliers are rejected in STEP2.

## Evidence and limits
See docs/STEP2_RESULT.md and EXP-20261002-001. Thousands of measurements establish
computation/provenance correctness, not the validity of any face-quality threshold.
STEP3 and later algorithms remain unchanged; their prerequisites are independent.

## Current generation and relative diagnostics
The earlier STEP1 Revision 2 baseline supplied 71 videos / 2,001 PNGs (historical after the upscale transition). Formal
manifests, summary and per-video metadata are validated before scoring and again
before publication; mismatched counts, inventory or hashes stop the run.
The existing three percentile/rank columns are global. Matching _video columns
are computed independently within each video with the same formulas. temporal_index
and extraction policy/FPS come from STEP1 grammar and official metadata. Filename
tie-breaks are explicit; mtime never influences metrics/rank. No STEP2 blur threshold
is configured, so flag count is null, not zero or a borrowed STEP3 gate.
See EXP-20261002-003 and DEC-0010. Earlier 3,550-frame results and the 3,607-frame /
82-video face baseline are Historical Baseline, not active-generation measurements.

## Human report layer
The unchanged raw frame CSV feeds two derived reports: one aggregate row per video
and one full-distribution row per metric. Expanded STEP2_METRICS_SUMMARY.md shows
video median diagnostics, concentration of global-rank tails and exposure tails.
Regenerate with build_step2_reports.py; no image decoding/scoring is involved.
Linear percentiles/population std describe stored values. Global tail sizes use
ceil(N*p/100) saved ranks, cumulative and overlapping. Video technical median ranks
average sorted-unique median percentiles; natural video IDs break ties. These are
human diagnostics only, not frame selection or Gate definitions. EXP-20261002-004
adds report-layer validation evidence to existing DEC-0010 without superseding its
measurement or generation-integrity policy.

## Explicit supplemental still input (2026-10-02)
The current upscale-transition STEP1 metadata records 67 videos / 1,893 frames.
The separately supplied still subtree contains 58 additional images. These counts
describe the inspected input; they are not constants in processing code.
`step2_blur.supplemental_dir` explicitly declares the still subtree inside raw input.
Only that subtree is excluded from formal STEP1 validation and is measured separately
with the same formulas. Unknown additional directories still fail formal validation.
The formal CSV and its ranks retain their video-only contract; supplemental and
combined CSVs expose additional images, input kind and their separate rank universes.
Both inventories are revalidated before publication. The report builder continues
to consume the formal CSV; combined human reports and STEP3 still-image integration
are outside this correction. Production measurement has not been run for this fix.
See [STEP2 supplemental input fix](../../docs/STEP2_SUPPLEMENTAL_INPUT_FIX.md) for
outputs, synthetic verification and execution ownership.
