# STEP1 upscale integration — implementation only

Normal user entry remains `bat/01_extract_frames.bat`.

## Flow / actual existing contract

The new orchestration helper loads the existing config/CLI source directory, reads
`run_upscale_4k.bat` there and verifies its declared output-folder and processor path.
The inspected BAT uses its own folder as input and `upscale` as output; its external
processor scans only direct children and keeps the same source basenames/extensions.
It skips existing outputs unless explicitly overwritten. This integration passes
no frame-extractor arguments to that BAT, including extraction `--overwrite`.

Original-root videos present: call the existing BAT, propagate a nonzero exit, then
check expected output presence and readable dimensions/positive duration with the
existing processor's ffprobe helper. Its current per-video failure handling can
return zero, so presence/readability is checked independently. This is not a full
decode/visual-quality/completeness guarantee.

No original-root videos: reuse the existing upscale outputs. This matches the
currently inspected layout: BAT at source root, video files in its upscale folder.
Neither this helper nor the original processor scans that folder recursively.
Empty/missing upscaled input or missing outputs for tracked IDs stops extraction.
Original files are not overwritten, restored, moved or deleted by this integration.

Then invoke unchanged `scripts/extract_frames.py --input <declared upscale folder>`.
Existing frame output, sampling, PNG generation, IDs and per-video generation/cache
handling remain. `--config`, source/output directory overrides and remaining extraction
arguments are forwarded/resolved through the shared config conventions.

## Necessary one-time source transition

Old manifest source paths/hashes and working copies refer to pre-upscale originals.
Changing only the extractor input would collide with those copies or append new IDs.
The helper therefore retains each existing ID/index/created_at/normalized filename,
maps its original filename to the upscaled file, and records both historical original
hash/path and current upscaled hash/path in `step1_upscale_transition.json`.
If an original is missing, its historical manifest provenance is preserved explicitly;
no missing original is recreated and no current-original hash is fabricated.

Before publishing the changed source manifest, previous manifest/extraction/summary
files are copied into `<normalized_dir>_previous/upscale_<unique-id>/`; the previous
working-copy directory is moved there as `videos`. The configured active directories
remain the same. The journal and existing manifest lock allow an interrupted move/
manifest checkpoint to resume, without deleting archived evidence. Unknown working
files, mixed source mappings or changed tracked upscale hashes stop instead.

The source switch marks STEP1 IN_PROGRESS until the existing extractor completes.
Existing raw-frame replacement/archive handling stays in the extractor; source hashes
force a new extraction generation rather than reuse old pixels. STEP2/STEP3 reports
are not regenerated or modified by this integration. Prior reports remain prior-
generation evidence and must not be treated as measurements of newly generated frames.

## Minimum validation performed

- `bat/01_extract_frames.bat --dry-run`: actual BAT/bootstrap/config/path flow;
  no upscale, media hashing, manifest transition, copying or frame extraction.
- Five tiny synthetic-file tests only: missing-original output reuse, stable IDs and
  archived provenance, interrupted transition resume, missing/changed output refusal,
  declared BAT output-path handling, and mocked BAT -> extractor argument routing.
  No FFmpeg processing, real videos or dataset-wide hashes were used by these tests.

Changed: `bat/01_extract_frames.bat`, new `scripts/prepare_step1_upscale.py`,
new `tests/test_step1_upscale_integration.py`, this scoped implementation note.
The external upscale BAT/processor and STEP1 extractor/common manifest implementation
are unchanged. No local config changes or deleted-image restoration.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md and both Project Rules,
relevant configuration/video organization Decisions, Knowledge and prior STEP1 result.
Data lineage preserved: YES by implementation and tiny fixture verification; live
new-generation verification awaits maru execution.
Full-row preservation: N/A (no frame production run).
Historical evidence preserved: YES. Config SSOT preserved: YES.
Documentation checked; no unrelated documentation update required.
No rule conflicts; no full production PASS claimed.

Full batch executed: NO.
Normal production execution belongs to ★maru through `01_extract_frames.bat`.

## Subsequent explicit execution authorization

The implementation-only status above is historical. The user then authorized
Codex to extract existing upscale outputs into `work/frames_raw`.
`--skip-upscale` guarantees no upscale BAT invocation; `--available-upscaled-only`
uses the available source generation and archives absent prior mappings.
`--supplemental-dir` optionally adds declared stills to a separate image inventory
after successful extraction. It does not transform stills or change video counts.
The existing processor's located FFmpeg/ffprobe binaries provide fallback paths
only when config and CLI do not specify them.
See [authorized result](STEP1_UPSCALED_EXTRACTION_RESULT.md).
