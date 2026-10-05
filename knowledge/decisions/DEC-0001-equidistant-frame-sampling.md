---
id: DEC-0001
title: Equidistant Video Frame Sampling (50 Segments)
status: SUPERSEDED
date: 2026-09-30
confidence: HIGH
components:
  - frame-extraction
tags:
  - ffmpeg
  - sampling
  - temporal-diversity
supersedes: []
superseded_by: [DEC-0009]
related_experiments:
  - EXP-20260930-001
related_failures: []
related_cases: []
---

# Decision Record: DEC-0001 - Equidistant Video Frame Sampling

> Historical policy, superseded by DEC-0009 on 2026-10-02. Original evidence below is retained; current STEP1 uses duration-aware sampling.

## 1. Context & Problem Statement
Raw smartphone/TikTok video footage typically runs at 30 to 60 frames per second. Extracting all frames across dozens of videos results in over 30,000 to 50,000 raw images. Processing this volume causes severe bottlenecks in disk I/O, face detection, blur scoring, and identity clustering. Furthermore, consecutive frames extracted at 30fps are 99% visually redundant.

## 2. Previous Approach
Extracting frames at a fixed 1 fps or extracting all keyframes (I-frames). Fixed 1 fps misses short dynamic action moments in short clips (e.g. 5-second videos) while generating thousands of nearly identical frames in long 3-minute talking videos.

## 3. Hypothesis
Sampling exactly 50 temporally equidistant frames per video—regardless of video duration—will provide maximum diversity in poses, expressions, camera angles, and background lighting, while capping the computational footprint to a predictable size (e.g., 80 videos $\times$ 50 = ~4,000 frames total).

## 4. Alternatives Considered
- **Option A (Chosen)**: 50 equidistant frame extractions computed dynamically via FFmpeg seeking (`-ss`).
- **Option B (Fixed FPS)**: Extract 1 frame per second. (Rejected: Video length variance from 4s to 180s leads to extreme skew in per-video representation).
- **Option C (Scene Change Detection)**: Using FFmpeg `select='gt(scene,0.4)'`. (Rejected: Phone camera TikTok videos rarely feature hard cuts; continuous slow camera movements yield inconsistent frame counts).

## 5. Decision & Implementation
Implemented in `scripts/extract_frames.py` and wrapped by `bat/01_extract_frames.bat`.  
The script probes total duration using `ffprobe`, computes timestamps $t_i = i \times \frac{\text{duration}}{N+1}$ for $i=1 \dots 50$, and extracts frames via single-frame seek.

## 6. Reasoning & Evidence
- **Fact**: On a test dataset of 82 video files, 50 segments produced exactly 3,607 valid frames in under 4 minutes.
- **Interpretation**: 3,607 frames is the sweet spot for batch computer vision pipelines, allowing subsequent filters to run rapidly while ensuring full temporal coverage of each video.

## 7. Consequences
- **Positive**: Predictable runtime and storage; uniform representation across all source videos.
- **Negative / Trade-offs**: In very long videos (> 5 minutes), 50 frames may occasionally skip brief high-quality poses.

## 8. Validated Conditions
- Works reliably on MP4, MOV, MKV, and WEBM video files from 3 seconds to 5 minutes duration.
