# STEP 1 Revision 2 Result

Date: 2026-10-02 (Asia/Tokyo)

## Status

**PASS** — duration-aware extraction and integrity/reuse validation completed for
all 71 videos. No commit/push or downstream full measurement/inference performed.
Previous fixed-count evidence remains in [STEP1_RESULT_REVISION1](STEP1_RESULT_REVISION1.md).
Template report uses generic subject labels; formal local manifests retain actual IDs.

## Extraction Policy

```yaml
frame_extraction:
  sample_fps: 2.0
  max_frames_per_video: 120
  policy_version: 2
```

Defaults come from config and retain explicit CLI > local YAML > fallback.
Default start/end trims are now zero to cover the whole video. Optional explicit
trims operate on a positive usable interval; there is no short-video fallback or
artificial minimum. Fixed segments_per_video/--num-frames was removed; old configs
must migrate to frame_extraction. The original defaults fixture remains historical;
compatibility tests explicitly exempt only the authorized count/trim changes.

ffprobe inspects duration, failing explicitly with video ID on error. Effective FPS
is min(requested FPS, max_frames/duration), so capped videos still cover the full
time axis. FFmpeg fps round=up, PNG/native dimensions, existing -q:v 2; no added
pixel-format conversion, rescaling or face/quality decision. Nominal frame budget
is min(max_frames, ceil(duration*FPS)). EOF/container timestamp rounding can yield
one fewer; validated actual counts are recorded separately without padding.
Larger deficits, excess or zero-frame outputs fail and retain prior data.

## Videos

71 originals and 71 normalized standalone copies retained. Formal video IDs,
original/normalized filenames, index, source hashes and created_at mapping match
pre-revision manifests. Originals and copies remain independent files; no rename,
overwrite, delete or transcode was applied to source videos.

## Duration

| Statistic | Seconds |
| --- | ---: |
| min | 7.660998 |
| median | 13.372993 |
| max | 165.466667 |

## Frame Counts

| Statistic | Frames |
| --- | ---: |
| minimum per video | 15 |
| median per video | 27 |
| maximum per video | 120 |
| total | 2001 |
| zero-frame videos | 0 |
| failed videos | 0 |

Fewest:

| Video ID | Duration (s) | Frames | Effective FPS |
| --- | ---: | ---: | ---: |
| Sasha_v34 | 7.660998 | 15 | 2.000000 |
| Sasha_v37 | 8.938005 | 18 | 2.000000 |
| Sasha_v01 | 9.520000 | 19 | 2.000000 |
| Sasha_v06 | 9.309751 | 19 | 2.000000 |
| Sasha_v41 | 9.588005 | 19 | 2.000000 |


Most:

| Video ID | Duration (s) | Frames | Effective FPS |
| --- | ---: | ---: | ---: |
| Sasha_v03 | 165.466667 | 120 | 0.725222 |
| Sasha_v52 | 28.511995 | 57 | 2.000000 |
| Sasha_v57 | 21.940998 | 44 | 2.000000 |
| Sasha_v39 | 19.270998 | 39 | 2.000000 |
| Sasha_v36 | 19.270998 | 39 | 2.000000 |


The longest video's requested rate is 2, effective rate approximately 0.725222,
with 120 outputs across its entire 165.467 seconds. Its output-grid final timestamp
exceeds 98% of duration. Frames are not restricted to the first 60 seconds.

## Old

3,550 PNG frames, fixed 50/video. Archived under the execution root's sibling
`work/frames_step1_previous/<video_id>/<generation>/`; all original frame SHA256,
sizes and modification times match the previous measurement snapshot.
Historical result and original sampling Decision/History/experiments are retained.

## New

2,001 valid PNG frames in the configured `paths.raw_frames_dir` (local execution:
`work/frames_step1`, generic template: `work/frames_raw`). Each video keeps its
existing directory and `<video_id>_<index:03d>.png` filename grammar for downstream
scene/frame parsing. Video IDs are unchanged; frame pixels/indices belong to the
new generation and prior-generation metric rows must not be reused.

## Cache

Per-video `.extraction_metadata.json` stores policy version, requested/effective
FPS, cap, duration, trims, source SHA256, naming/encoder recipe and frame hashes.
Folder existence alone never enables reuse. Old metadata-free fixed-count frames,
changed config or corrupted files require regeneration. New output is staged
outside the raw input root, PNG/count validated, then old folders are archived and
new data published. Failed staging is retained for diagnosis; no recursive deletion.
Explicit --overwrite also archives its prior generation. On publish-rename failure,
the old folder is restored; crash/power-loss recovery is not fully transactional.

Same-config standalone BAT replay: 71 copies reused, 2,001 frames reused,
0 frames created, 0 failed. Every current frame matches the published metadata
SHA256 and passes PNG integrity verification. Unit tests verify FPS 2→1 forces
new output and preserves old data. Alternate 58 images at their original paths
remain unchanged; they were not adopted into this input generation.

## Manifest / Output

`video_manifest.csv` retains the formal mapping unchanged. `video_extraction.csv`
and legacy `output/reports/step1_extract_report.csv` include duration_seconds,
sample_fps_requested/effective, max_frames, extraction_policy_version,
planned_frame_count, extracted_frame_count, target_frames, archive fields and
created/reused counts. On PASS, target_frames is validated actual count, which
STEP2 reads automatically. The nominal budget remains separately traceable.
`step1_summary.json` adds duration/count statistics and fewest/most videos.
Private logs, old metadata/config/result, failed staging and verification are in
`output/reports/step1_revision2_audit/`. Source `docs/STEP1_VERIFICATION.json` records
portable verification totals; the historical revision-1 verification is retained.

## Tests

53 lightweight unittest tests pass in both copies: current config/CLI/schema,
stable mapping/copies/locks, sampling 3/10/30/100 seconds, full-duration cap,
invalid durations, policy reuse/mismatch, legacy cache, corruption, failed-generation
preservation, explicit overwrite archive, normalize-only/dry-run, EOF rounding,
under/excess output rejection, downstream scene grammar and existing STEP2 metric
formula/report tests on synthetic fixtures. No full STEP2 production run occurred.

Actual FFmpeg synthetic clips: 3 seconds→6, 10→20, 30→60, 100→120 (effective FPS 1.2).
Real-data validation: 71 videos/2,001 PNGs, all hashes/integrity/budgets match;
3,550 archived old frames match original hash/size/mtime; mapping and 71 original/copy
hashes match; baseline hash unchanged. Initial strict nominal count checks failed
safely on one-frame EOF differences; final validation/run and repeat both pass.
Python compile, Git whitespace and private artifact ignore checks pass.
STEP BAT remains standalone; run_all still calls 01_extract_frames.bat.

## Knowledge / Decision

DEC-0009 ACCEPTED supersedes only DEC-0001's fixed-count sampling. Current video
organization/configuration/metrics policy, README, architecture, HIST-009 and
EXP-20261002-002 are updated. Historical records remain distinguishable from
current defaults. No face/pose/dedup/identity/DINO/quota/review/caption/training
algorithm changed; STEP2 metric formulas and production code remain unchanged.

Baseline SHA256 unchanged:
`2175683b2dbc42169d509ba607713c0e6fd1c2bf4332bd0cfd13fe08134994e8`.

## STEP2 State

Previous STEP2 CSV/JSON/outliers were preserved under private
`output/reports/step1_revision2_audit/step2_previous/` and removed from active report
paths to prevent stale use. Historical STEP2 docs are explicitly marked stale for
this generation. The STEP2 input-count reader was validated against actual STEP1
counts (2,001); no fixed 3,550 or 50/video assumption exists in production code.
New technical metrics are pending; STEP2 full measurement was **not executed**.

## Risks / Notes

The policy is user-authorized; pose/diversity improvement is a motivation, not a
new visual-quality benchmark. FFmpeg fps may differ from the nominal ceil budget
by one at EOF; that allowed difference is explicit and hashed in metadata. Zero or
larger differences still fail. Failed staging files are retained outside raw inputs
and consume disk space; no cleanup was performed. Publication is per video rather
than a single all-video transaction. Complete successful STEP1/replay is required
before using this generation. Staging/publication must support same-volume rename.

## Ready for STEP 2

**YES** — revised frame generation is complete and verified; run STEP2 separately
when requested. This correction stops before production technical measurement.
