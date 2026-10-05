---
id: EXP-20260930-001
title: Equidistant Frame Extraction Validation across 82 Source Videos
date: 2026-09-30
hypothesis_status: VALIDATED
confidence: HIGH
components:
  - frame-extraction
tags:
  - ffmpeg
  - frame-sampling
  - dataset-scale
related_decisions:
  - DEC-0001
related_failures: []
related_cases: []
---

# Experiment Record: EXP-20260930-001 - Equidistant Frame Extraction Validation

## 1. Objective & Hypothesis
- **Objective**: Determine whether sampling exactly 50 equidistant frames per source video provides comprehensive temporal and aesthetic coverage without overwhelming disk storage and computation time.
- **Hypothesis**: 50 frames per video will capture all wardrobe changes, camera angle transitions, and natural expression variations while keeping total candidate frames within manageable bounds (~3,500 frames).

## 2. Experimental Setup
- **Code**: `scripts/extract_frames.py`
- **Input Corpus**: 82 vertical mobile MP4 video files (total duration ~65 minutes, average duration 48 seconds, sizes from 5MB to 85MB).
- **Environment**: Windows 11, FFmpeg 7.x, Python 3.10.11.
- **Execution Command**:
  ```cmd
  bat\01_extract_frames.bat
  ```

## 3. Measured Results (Facts)
- **Extraction Time**: 3 minutes 42 seconds total runtime.
- **Total Valid Frames Extracted**: **3,607 frames**.
- **Average Extraction Rate**: 44.0 frames per video (shorter 3-second clips yielded slightly fewer distinct frames due to duration constraints).
- **Disk Footprint**: ~4.2 GB of PNG frames.

## 4. Human Visual Evaluation
Visual spot checks confirmed that key actions, dance movements, close-up glances, and environmental switches were all represented. No critical scene moments were omitted across tested clips.

## 5. Interpretation & Conclusions
Equidistant sampling mathematically guarantees uniform representation across diverse video lengths, eliminating the bias where 3-minute talking videos dominate 10-second action clips.

## 6. Resulting Actions
Accepted `DEC-0001` as the production standard for Step 01 frame extraction.
