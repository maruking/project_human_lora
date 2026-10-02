> HISTORICAL / STALE for current frames: this report describes the previous fixed-count generation. STEP1 Revision 2 now records variable actual counts (2,001 in the latest run). Current-generation STEP2 metrics have not been run. Prior outputs are preserved in the private revision audit; run STEP2 on STEP1 actual counts before STEP3.

# STEP 2 Result

Date: 2026-10-02 (Asia/Tokyo)

## Status

**PASS** — measurement, STEP1 provenance/count alignment, full legacy regression
and deterministic repeated execution completed. PASS is successful computation
and completeness, not photographic face quality or LoRA suitability. Local changes
only; no commit/push, training, face inference or identity model execution.

## Input

71 per-video directories, 3,550 PNG frames (50 per video), selected through
`paths.raw_frames_dir`. Formal IDs come from `work/manifests/video_manifest.csv`,
counts from `video_extraction.csv`. Frame identities are the existing input-relative
`<video_id>/<frame_name>.png` paths; no frame names or video IDs were reassigned.

At execution the previously verified PNGs were absent: `work/frames_raw` contained
58 other images in one untracked folder. STEP2 correctly returned FAIL for that
mismatch, despite all 58 decoding successfully. The 71 normalized video copies
remained. To preserve those alternate images, unchanged STEP1 extraction was rerun
into `work/frames_step1`; private config now selects that root and STEP1 extraction
metadata points there. The template still defaults to `work/frames_raw`.
The alternate 58 files remain at their existing paths with unchanged sizes/mtimes.
Input mismatch and recovery evidence is in private `output/reports/step2_audit/`.

## Metrics

- width, height, short_edge, long_edge, pixel_count, aspect_ratio (width/height, six decimals).
- global_laplacian = existing CV_64F Laplacian variance (default kernel).
- global_tenengrad = existing mean(dx²+dy²), CV_64F Sobel, ksize=3.
- mean_brightness = existing BGR2GRAY gray.mean().
- Existing brightness_std, shadow_pixel_ratio (<40), highlight_pixel_ratio (>235),
  contrast_p90_p10, file_size_bytes, Laplacian/Tenengrad percentiles and quality_rank remain.

Existing metric precision stays three decimals. New global/brightness aliases
exactly equal laplacian_score/tenengrad_score/brightness_mean. Existing color decode
and grayscale conversion remain, without resize or enhancement. quality_rank is a
legacy diagnostic column, not GoodFace. No resolution, brightness or sharpness gate.

## Output

- `output/reports/step2_dataset_report.csv`: exactly 3,550 rows; all old columns plus
  video_id, frame_id, frame_name, relative_path, dimension descriptors, aliases and processing_status.
- `output/reports/step2_summary.json`: totals, STEP1 validation, per-video counts,
  distributions, resolution buckets/counts and explicit processing errors.
- `output/reports/step2_diagnostic_outliers.csv`: 100 diagnostic rows (five groups
  of 20; the same frame may appear in multiple groups). Highest/lowest Laplacian,
  darkest/brightest, smallest pixel count. No quality accept/reject labels.
- `docs/STEP2_METRICS_SUMMARY.md`: readable distributions and resolution inventory.
- Private audit: pre-STEP2 code/config/manifests, mismatch/recovery logs, full
  regression and repeat verification JSON, measured frame SHA256/size/mtime snapshots.

filename/frame_id remain input-relative; relative_path is project-relative for
internal inputs, input-relative for external roots. Formal CSV/JSON contain no
machine-specific absolute paths. Console/audit logs are private. Output destinations
are configurable; omitted summary/outlier paths follow the effective CSV directory.

## Processing Result

```text
input_records  3550
processed      3550
failed         0
video_folders  71
per_video      50
unique_ids     3550
```

All per-video counts match STEP1. CSV has no stale historical records. Each broken
image would still produce one FAIL record with relative identity and error category;
processing continues, and decode/completeness failures cause a nonzero final exit.

## Distribution

| Metric | min | p25 | median | p75 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| width | 464.0 | 576.0 | 720.0 | 1080.0 | 1080.0 |
| height | 772.0 | 1024.0 | 1280.0 | 1920.0 | 1920.0 |
| short_edge | 464.0 | 576.0 | 720.0 | 1080.0 | 1080.0 |
| long_edge | 772.0 | 1024.0 | 1280.0 | 1920.0 | 1920.0 |
| pixel_count | 393472.0 | 589824.0 | 921600.0 | 2073600.0 | 2073600.0 |
| mean_brightness | 43.965 | 121.7475 | 135.571 | 146.77925 | 194.282 |
| global_laplacian | 1.285 | 12.209 | 32.2545 | 105.766 | 1447.088 |
| global_tenengrad | 39.31 | 783.74625 | 1671.9645 | 3721.34225 | 24462.748 |


Linear quartiles are calculated from stored metric values. All statistics below
are descriptive; a short edge of 464 is recorded and never rejected by STEP2.

| Short edge (diagnostic only) | Frames |
| --- | ---: |
| short_edge_lt720 | 1250 |
| short_edge_720_to1079 | 650 |
| short_edge_ge1080 | 1650 |


| Width | Height | Frames |
| ---: | ---: | ---: |
| 464 | 848 | 50 |
| 540 | 960 | 300 |
| 540 | 972 | 50 |
| 576 | 772 | 100 |
| 576 | 1024 | 700 |
| 576 | 1040 | 50 |
| 720 | 1280 | 650 |
| 1080 | 1450 | 50 |
| 1080 | 1920 | 1600 |


## Regression Test

All 3,550 images were compared against the untouched pre-STEP2 scorer: zero
differences in 13 legacy fields (dimensions, base metrics,
file size, percentiles and relative rank). New aliases exactly match legacy columns.
The second standalone BAT run produced byte-identical CSV, JSON and outlier CSV.
All 3,550 measured PNG SHA256 values, sizes and modification times were unchanged
across measurement and replay. The formal STEP1 video mapping and frame identities
match pre-recovery records. Source and normalized SHA256 values match for all
71 videos. Recovered frame sizes match all 3550 historical STEP1 records;
this does not prove prior PNG byte identity because the original PNGs were absent.

## Tests

45 lightweight unittest tests pass in both source and execution copies, including
15 STEP2 tests: constant brightness, known 464x848 dimensions, exact formulas and
aliases, broken/IO inputs, natural ordering, relative identity, manifest mismatch,
duplicate IDs, missing counts, empty inputs, distributions/outliers, snapshot and
explicit legacy merge, schema validation, CLI path/boolean precedence and replay.
Python compilation, Git whitespace checks and generated-artifact ignore checks pass.
Standalone `bat/02_technical_metrics.bat` exits 0 on both complete runs;
`run_all.bat` continues to call that BAT. Full pipeline execution was not performed.

## Existing Behavior Preserved

Old decoding/grayscale math, Sobel kernel/datatype/normalization, precision,
auxiliary diagnostics, relative-rank algorithm and legacy CSV fields remain.
Common config loader, schema validation and CLI > local YAML > fallback remain.
No dependency was added. STEP1 sampling/trim/codec/PNG algorithms and STEP3+ code
were unchanged. Rank ties inherit natural numeric input order; for names whose
lexical order differs (such as video 100), tied rank assignments can differ from
the old lexical enumeration. Snapshot output deliberately replaces silent stale-row merging;
`--retain-missing-records` or its config boolean retains that legacy mechanism.
It is historical row retention, not a cache. Retained rows are counted separately
and excluded from current-input statistics; use default false for strict snapshots.

Validated baseline SHA256 remains:
`2175683b2dbc42169d509ba607713c0e6fd1c2bf4332bd0cfd13fe08134994e8`.

## Agent Instruction Updated

Moved the misplaced instruction file to root `AGENTS.md`; one authoritative root
file per checkout, with original Knowledge Maintenance rules preserved. Root
`.AGENTS.md` is preferred if present, otherwise root `AGENTS.md`. Retrieval order:
root instructions, Current, relevant Decisions, Failures, Cases, previous STEP Result,
then supporting experiments/history. Old README/architecture links were corrected.
Added the requirement for an ACCEPTED Decision and supporting experiment before
a diagnostic metric can become a hard quality rule, and the explicit warning that
Laplacian/Tenengrad do not equal perceptual face quality.

## Knowledge Updated

- Current: technical-image-metrics, face-quality clarification, configuration and index.
- Decision: DEC-0008; clarifies STEP2 wording in DEC-0002 without changing STEP3.
- Case: CASE-0003, LOW confidence, user-reported historical `02_Sash_v1_014.png`:
  464x848, face about 103px, global Laplacian about 102, face Laplacian about 135,
  visually soft/pixelated. No new face crop/measurement or filename equivalence claimed.
- History: HIST-008, deterministic metrics/provenance and input recovery.
- Experiment: EXP-20261002-001, formula/replay/completeness evidence.
- README, architecture STEP2 row, config example/schema and private local config.

## Risks / Notes

Gradient magnitude cannot establish facial detail: background, hair, clothing,
compression and pixel boundaries can inflate metrics. The user-reported case was
not supplied as an exact historical input/crop, so it is not newly validated.
Repeated execution is deterministic for unchanged inputs/config/runtime; concurrent
external mutation of source images during measurement is outside this validation.
Individual files are atomically replaced; there is no transaction across all three
output files if the process crashes between writes. A complete repeat run repairs it.

The recovered frame root differs from the template's default; follow config rather
than hardcoding `work/frames_raw`. MediaPipe and imagehash are currently absent;
STEP2 does not need them. Later-step dependency setup, reference confirmation and
GPU inference are outside this STEP2 measurement result. No quality thresholds,
Face Mesh, face-local blur, pose, DINO, identity, dedup, quotas or captions changed.

## Ready for STEP 3

**YES** — 71 stable video IDs, 3,550 measured frames and compatible formal CSV are
ready as STEP3 inputs. STEP3 execution additionally requires its own dependencies.
