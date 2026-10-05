---
id: DEC-0009
title: Duration-Aware Temporal Sampling With Per-Video Cap
status: ACCEPTED
date: 2026-10-02
confidence: MEDIUM
components: [frame-extraction, configuration]
tags: [ffmpeg, fps, cache, duration]
supersedes: [DEC-0001]
superseded_by: []
related_experiments: [EXP-20261002-002]
related_failures: []
related_cases: []
---

# Decision Record: DEC-0009

## Previous and problem
DEC-0001 used exactly 50 frames per video. Temporal density depended on duration:
short clips produced many nearby candidates while long clips were undersampled.
No earlier accepted fixed-second-interval rule was found. The old unbounded 1 FPS
experiment is historical, not the specification for this bounded 2 FPS revision.

## Decision
Duration-aware extraction; defaults from frame_extraction config: sample_fps=2.0,
max_frames_per_video=120, policy_version=2. No fixed count or artificial minimum.
Default trims are zero, so the full duration is sampled. Optional nonnegative
step1_extract trims explicitly select a shorter usable interval; a nonpositive
interval fails rather than using the historical short-video fallback.

ffprobe supplies finite positive duration D; with default trims, effective FPS is
min(requested FPS, max_frames/D). The nominal budget is min(max_frames, ceil(D*FPS)).
Use FFmpeg fps with round=up, preserving PNG, -q:v 2 and native dimensions/pixel
format (no added format conversion or scale). A safety frame limit enforces the
budget after reducing the rate across the whole video, not the first 120 at 2 FPS.
Container duration and video end timestamps can differ by one output interval.
Validate actual output as positive and within nominal budget or budget minus one;
larger deficits/excess fail. Record nominal planned_frame_count separately from
actual extracted_frame_count and target_frames used by STEP2 completeness checks.
Never duplicate extra frames merely to fill the nominal budget.

## Cache and data safety
Working copies, video IDs and formal mapping remain. Metadata records policy,
source SHA256, duration, FPS, cap, trims, naming/encoder recipe and validated frame
hashes. Reuse only exact policy/source matches plus exact file inventory and hashes.
Old metadata-free policy-1 frames or changed/corrupt cache must not be reused.
Generate into a staging directory outside STEP2's image root, validate PNGs/counts,
then archive the previous per-video directory in a sibling *_previous root and
publish the new generation. Preserve failed staging and old generations for
inspection; never recursively delete data. A rename failure restores the old folder.
--overwrite also preserves an archived generation. OS manifest locking remains.

## Reason and consequences
Approximate consistent temporal density while limiting long-video dominance.
Total candidates now depend on actual durations. Hypothesized pose/diversity gains
are not a measured face-quality result. 2 FPS/120 is a user-authorized initial
policy, not an experimentally optimized threshold. Prior frame IDs can refer to
new pixels under the revised sampling, so old STEP2 results are historical/stale
and must be regenerated separately. STEP2 must derive input counts from STEP1.

## Evidence and limits
EXP-20261002-002 verifies 71 videos, variable counts, full-axis capped rate, policy
reuse and old-data retention. Synthetic 3/10/30/100-second plans test 6/20/60/120.
Duration probe failure is explicit per video; no silent fixed-count/OpenCV fallback.
No downstream quality/identity/pose algorithm or validated baseline was changed.
Publication is per video; a mid-run crash can leave mixed generations and failed
staging. STEP1's non-PASS summary blocks STEP2 until successful completion/replay.
Multi-file publication is not a power-loss transaction; preserved archives permit
recovery. Staging and configured outputs must support rename on the same volume.
