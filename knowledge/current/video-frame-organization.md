---
topic: video-frame-organization
last_updated: 2026-10-02
confidence: MEDIUM
status: ACTIVE
related_decisions: [DEC-0007, DEC-0006, DEC-0009]
related_failures: []
related_cases: []
---

# Current Knowledge: Video IDs and Per-Video Frames

## Current policy
STEP1 retains downloaded source videos and creates standalone normalized copies
in `paths.normalized_video_dir` (default from config: `work/videos`). Subject is
`project.subject_name`; the generic template value is `subject`. Local subjects
belong only in ignored `config/config.yaml` and private generated artifacts.

IDs are `{subject_name}_v{index:02d}`. Keep each video's extension (lowercase),
without transcoding or pretending MOV/MKV is MP4. Extract PNG frames into
`paths.raw_frames_dir/<video_id>/<video_id>_001.png`. The established three-digit
frame suffix and duplicated ID in the filename are intentional compatibility:
Step4 reads the first folder as `scene_group` and the final numeric token as
`scene_frame_index`; later dedup/selection depend on these fields.

## Ordering and mapping
Initial assignments use case-insensitive natural filename order with an explicit
raw-name tie-breaker. Already-normalized source IDs are reserved first. Thereafter
`work/manifests/video_manifest.csv` is authoritative: preserve all prior IDs and
gaps; append new original videos after the largest reserved index. Never renumber
old IDs because new files sort earlier or an old source is missing.

Manifest fields: video_id, subject_name, index, original_filename,
normalized_filename, original_path, normalized_path, extension, file_size, sha256,
created_at, normalization_status and normalization_error. Full original download
names remain traceable even after normalization. SHA256 verifies source and
working-copy integrity; original and normalized files do not share an inode.

## Safety and interruption recovery
Validate the complete naming plan and refuse untracked destination collisions.
An OS advisory lock serializes manifest operations and extraction, releasing on
process exit. Write the manifest atomically before copies, then checkpoint after
each normalization and extraction. Copy into a private temporary file, verify
the bytes, and publish without replacing an existing target. A crash can leave
temporary files, but completed matching copies are reused on the next run.

Changed source contents, corrupt destinations, duplicate normalized IDs or a
different subject/configured output directory fail explicitly. Missing source
records retain their IDs and are reported as failures. Do not manually edit
mapping CSVs to bypass these checks or use a new manifest to reshuffle existing
working copies.

## Execution and outputs
`bat/01_extract_frames.bat` independently performs normalization and extraction;
`run_all.bat` still calls it. `--dry-run` prints a read-only plan, including skipped
extensions, collisions and frame directories. `--normalize-only` creates copies,
manifest and per-video directories without invoking extraction.

`video_extraction.csv` records IDs, original/normalized filenames, duration,
frame_directory, extraction_status, extracted_frame_count, target count,
created/reused frames, FFmpeg return codes and error summaries.
`step1_summary.json` distinguishes renamed (always zero for this copy policy),
new copies, reused normalized copies, processed/successful/failed videos and
created/reused/total available requested frames. The legacy Step1 CSV report
retains its original columns and adds ID/provenance/error fields.

Per-video failures continue through remaining videos and return nonzero at the
end. This preserves continue-processing behavior and complies with repository
failure-exit rules; the old success exit despite skipped/failed videos is not
retained. `--flat` is rejected because it violates per-video organization.

## Duration-aware extraction (DEC-0009)

frame_extraction defaults: sample_fps=2.0, max_frames_per_video=120, policy_version=2.
Default trims are zero: short clips produce fewer frames, while clips exceeding
120 nominal outputs use effective FPS=120/duration across the full timeline.
FFmpeg fps round=up retains PNG, native dimensions/pixel format and -q:v 2.
Nominal count is ceil(duration*requested FPS), capped at max. Actual output may be
one fewer due to container/video EOF timestamps. Zero/larger deficits/excess fail;
no padding or fixed minimum. Optional trims operate on a validated usable interval.

Per-video .extraction_metadata.json fingerprints source SHA256, duration, requested
and effective FPS, cap, policy version, trims, recipe and frame hashes. Existence
alone is insufficient. Changed policy or corrupt/missing metadata regenerates into
manifest-dir staging, validates PNGs, archives the old folder under a sibling
*_previous root and publishes the new generation. Failed staging stays outside
raw inputs; original/previous data is retained. Explicit overwrite also archives.

video_extraction.csv adds duration_seconds, sample_fps_requested/effective,
max_frames, extraction_policy_version, planned_frame_count, actual count and archive
provenance. target_frames on PASS is the validated actual count, so STEP2 reads
STEP1 actual frames rather than a fixed dataset size. Old STEP2 reports become stale.
The summary reports duration and count min/median/max/total, fewest/most videos,
created/reused/archive counts. Per-video failures continue and final exit is nonzero.

DEC-0001's fixed-count policy remains historical; DEC-0007 identity/copy safety
and DEC-0006 config precedence remain active. No face/pose/identity/quota/caption
algorithm changed. Current real evidence: docs/STEP1_RESULT.md revision 2.

Latest user-authorized source generation: see [upscaled extraction result](../../docs/STEP1_UPSCALED_EXTRACTION_RESULT.md).
The prior2,001-frame result is historical. Current local frames_raw contains1,893
video frames from67 available upscaled sources;58 declared stills are added only
to the separate1,951-image inventory, not to formal video counts. Prior source
mappings/copies are archived, available IDs are preserved, and STEP2/STEP3 have not
been rerun for this generation. The image listing is not a quality/selection result.
