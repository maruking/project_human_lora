# HIST-007 — STEP 1 Video ID, Manifest and Per-Video Frames

- Date: 2026-10-02 (Asia/Tokyo)
- Related decisions: DEC-0007, DEC-0006, DEC-0001
- Confidence: MEDIUM

## Before
STEP0 provided common config loading but extraction still used input stems as
scene names. Subfolders already existed by default; PNG names included the stem
and a three-digit frame index. Downloads were not normalized or durably mapped.
The local source dataset has 71 videos, about 234 MB, with existing numeric names.

## After
STEP1 now assigns a configured subject's stable video IDs, retains all sources
and creates standalone working copies. A durable manifest preserves original
filenames and content hashes. Natural sorting applies only to initial/new inputs;
existing IDs, normalized names and missing-source gaps remain stable.
Per-video frame folders use IDs and retain the existing PNG naming grammar.

## Safety choice and rationale
Adopted working copies instead of raw rename or source hardlinks. Available disk
space makes the extra 234 MB acceptable; editing a copy cannot edit the raw file.
Exclusive publication, durable intent, checksums and advisory locks prevent
overwrites, reassignment after interruption and concurrent manifest corruption.

## Validation
Lightweight tests cover config compatibility, naming, natural order, append after
71, mixed/already-normalized sources, collisions/races, changed/missing sources,
copy failure, interruption, locks, read-only dry-run, original retention, folder
layout, frame reuse, FFmpeg command/timestamps, failure reporting and Step4 scene
parsing. Actual results and counts are recorded in `docs/STEP1_RESULT.md`.

## Scope boundaries / remaining issues
No face/pose/identity/quota/review/caption algorithm changes. No scene-aware
sampling. Existing PNG encoding/FFmpeg conditions remain intact. Source subjects
and generated provenance remain in private local artifacts only. Historical
validated baseline files and STEP0 verification records are preserved.

Old failure handling continued processing but returned success after skipped
videos. STEP1 continues processing and records all failures, then exits nonzero
to comply with repository rules. Flat output is now explicitly rejected.
OS crash recovery is exercised through intent/copy checkpoint tests; power-loss
durability and non-NTFS Windows volumes remain outside real-data validation.
