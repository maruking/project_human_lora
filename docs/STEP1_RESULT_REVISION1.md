# STEP 1 Result

Date: 2026-10-02 (Asia/Tokyo)

## Status

**PASS** — implementation, real-data extraction, integrity verification and repeat
execution completed. All changes are local; no commit/push was performed.
Actual local subject: `Sasha`. Private config and generated manifests retain the original download mapping.

## Source Videos

71 supported videos detected, totaling 233,751,151 bytes. Original video filenames
and contents remain intact. No unsupported source files were found in this run.

## Video Naming

`{subject_name}_v{index:02d}.{extension}`, with `project.subject_name` from config
and explicit `--subject-name` taking priority. Actual local subject is `Sasha`:
`Sasha_v01.mp4`, `Sasha_v71.mp4`, `Sasha_v100.mp4`. Original extensions are
retained and lowercased; normalization does not transcode videos.

## Video ID

The filename stem is the formal video ID. Initial assignments use case-insensitive
natural sort with an explicit tie-breaker. Existing manifest assignments override
sorting; new originals append after the largest reserved index. Normalized source
IDs and missing-source gaps are retained. Existing Step4 scene/frame parsing
recognizes the new folder IDs without a downstream algorithm change.

## Rename / Normalization Result

Adopted original retention + standalone working copies, not source rename or
source hardlinks. Copies require approximately 234 MB for this dataset.

| Result | First run | Repeat run |
| --- | ---: | ---: |
| renamed original files | 0 | 0 |
| normalized copies created | 71 | 0 |
| skipped unsupported files | 0 | 0 |
| already-normalized working copies reused | 0 | 71 |
| failed | 0 | 0 |

All source and working-copy sizes/SHA256 hashes match; copies are independent
files. Collision, interruption, changed-source and copy-failure cases are covered
by lightweight tests. No destination video is overwritten.

## Manifest

`work/manifests/video_manifest.csv`, configurable via `paths.manifests_dir`.
Fields: video_id, subject_name, index, original_filename, normalized_filename,
original_path, normalized_path, extension, file_size, sha256, created_at,
normalization_status, normalization_error.

`video_extraction.csv` adds extraction_status, extracted_frame_count,
frame_directory, target_frames, duration_sec, frames_created, frames_reused,
FFmpeg return codes and error_summary. The legacy
`output/reports/step1_extract_report.csv` retains its old columns and includes
these provenance/diagnostic fields. `step1_summary.json` records each run's totals.

Manifest intent is checkpointed before copying; publication never replaces an
existing target. OS advisory locks serialize runs and release on process exit.
Completed byte-identical copies are recognized after interruption. Manifest,
normalized videos and private configuration are ignored by Git.

## Frame Directory

71 video directories under `work/frames_raw/`:

```text
work/frames_raw/Sasha_v01/Sasha_v01_001.png
work/frames_raw/Sasha_v01/Sasha_v01_050.png
...
work/frames_raw/Sasha_v71/Sasha_v71_050.png
```

Existing `<video_stem>_<index:03d>.png` grammar is preserved for compatibility;
the alternative JPG/six-digit proposal was not substituted. `--flat` is explicitly
rejected to enforce the requested per-video layout.

## FFmpeg Extraction

- processed videos: 71
- successful: 71
- failed: 0
- total frames: 3,550 (50 per video)
- first run frames created: 3,550
- repeat run frames created: 0; frames reused: 3,550
- standalone BAT exit code: 0 on both runs

Per-video failures continue through remaining videos, are logged with IDs and
FFmpeg return codes/errors, and cause a nonzero final exit. This retains the
continue-processing policy while enforcing the repository's failure-exit rule.

## Tests

- 30 lightweight unittest tests passed in both source and execution copies:
  STEP0 config/CLI compatibility; naming 1/71/100; natural stable order;
  manifest replay; append after 71; mixed/already-normalized inputs;
  destination/frame-directory collisions; race protection; source changes;
  missing source ID retention; copy failure; interruption recovery; locking;
  read-only dry-run; frame directories/reuse; FFmpeg errors/commands/timestamps;
  normalization-only execution and existing Step4 scene parsing.
- Real-data Dry Run: 71-video plan, no normalized/manifest directories created.
- Real first run: 71 videos, 3,550 frames, no failures.
- Real repeat run: 71 stable IDs, all 3,550 frames reused; paths, sizes and
  modification times unchanged.
- Every source/copy pair passed size/SHA256 checks and independent-file checks.
- All 3,550 PNG files passed format, dimensions and PNG integrity validation.
- Real pre-STEP1 extraction comparison: all 50 PNG files from one video were
  byte-identical to the normalized-copy extraction.
- Python compilation, Git diff whitespace and private-artifact ignore checks pass.
- `docs/VALIDATED_BASELINE.md` hash unchanged:
  `2175683b2dbc42169d509ba607713c0e6fd1c2bf4332bd0cfd13fe08134994e8`.

## Existing Behavior Preserved

Common loader, YAML/schema validation, root-relative/Windows paths and explicit
CLI > YAML > fallback remain. Extraction keeps default 50 frames, 0.5s trims,
short-video 5%–95% fallback, existing timestamps and
`-y -ss <t> -i <video> -vframes 1 -q:v 2`, PNG output and OpenCV fallback.
No FPS, codec, face/pose/identity/DINO/quota/review/caption/training change.
`01_extract_frames.bat` remains standalone; `run_all.bat` still calls the BAT.

## Knowledge Updated

- Current: `knowledge/current/video-frame-organization.md` and index
- Decision: `DEC-0007-stable-video-ids-and-working-copies.md` and index
- History: `HIST-007_VIDEO_ID_AND_MANIFEST.md` and index
- README: STEP1 input/copies/IDs/manifest/frame layout and command examples
- Example/schema: generic subject, normalized-video/manifests paths, per-video rule
- Added stdlib organization module and unit tests; no new library dependency

## Risks / Notes

Do not move/alter generated absolute mappings without deliberate migration.
Source changes and unrelated/corrupt destinations fail rather than overwrite.
New untracked nonempty frame folders are not silently adopted. Interruptions can
leave harmless temporary-copy files. Power-loss recovery and non-NTFS filesystem
fallback were not tested on actual media. Whole-machine source mutation during
processing is outside the pipeline lock; SHA256 checks reject changed copy data.

The old success exit despite failed/skipped videos was corrected to nonzero;
flat output is now rejected by the per-video requirement. No historical baseline
figures were changed. MediaPipe/imagehash prerequisites for later steps remain
outside STEP1; they are not required for standalone Step2 technical metrics.

## Ready for STEP 2

**YES** — 71 organized video IDs and 3,550 verified PNG frames are available.
STEP2 evaluation has not been run as part of this STEP1 request.
