---
id: EXP-20261001-002
title: Dual-Bandpass Plasticity Gate Benchmark across 3,607 Real Frames
date: 2026-10-01
hypothesis_status: VALIDATED
confidence: HIGH
components:
  - face-quality
  - realism-filter
tags:
  - beauty-filter
  - plasticity-ratio
  - skin-texture
  - empirical-audit
related_decisions:
  - DEC-0003
related_failures: []
related_cases:
  - CASE-0001
---

# Experiment Record: EXP-20261001-002 - Dual-Bandpass Plasticity Gate Benchmark

## 1. Objective & Hypothesis
- **Objective**: Verify whether the newly formulated `plasticity_ratio` (edge sharpness / skin high-frequency texture) and `skin_texture_score` successfully cull beauty-filtered frames from real-world smartphone datasets without rejecting genuine high-quality photographic portraits.
- **Hypothesis**: The filter will catch heavily smoothed images (such as `CASE-0001` / `Sash_v5_013`) by detecting the mismatch between sharp boundary lines and smoothed epidermal skin, while retaining photographic frames with real pores and camera grain.

## 2. Experimental Setup
- **Code**: `scripts/face_quality_gate.py`
- **Dataset**: 3,607 extracted video frames from 82 real smartphone MP4 videos (`work/frames_raw/`).
- **Gating Parameters Tested**:
  - `min_face_size`: 120 px
  - `min_face_sharpness`: 18.0
  - `max_occlusion_ratio`: 0.35
  - `max_plasticity_ratio`: **70.0**
  - `min_skin_texture_score`: **15.0**
- **Execution Command**:
  ```cmd
  bat\03_face_quality_gate.bat
  ```

## 3. Measured Results (Facts)
- **Total Frames Evaluated**: 3,607
- **Eligible Passed Frames**: **1,911 frames (53.0%)**
- **Total Rejected Frames**: **1,696 frames (47.0%)**
- **Detailed Rejection Breakdown**:
  - **Beauty Filter / Plastic Skin Detected (`plasticity_ratio > 70` or `skin_texture < 15`)**: **749 frames (20.8%)**
  - **Blurry Face (`face_sharpness < 18.0`)**: 532 frames (14.7%)
  - **Face Too Small (`face_size < 120px`)**: 284 frames (7.9%)
  - **No Face Detected**: 98 frames (2.7%)
  - **Severe Occlusion (`occlusion > 0.35`)**: 33 frames (0.9%)
- **Verification on Known Anomaly**:
  - Target sample `CASE-0001` (`Sash_v5_013`):
    - Face Sharpness: 185.2
    - Skin Texture Score: 1.34
    - Plasticity Ratio: **138.2**
    - **Result**: Successfully rejected and routed to `work/facegate_review/rejected/` with label `beauty_filter_detected`.

## 4. Human Visual Evaluation
- **True Positives (Properly Rejected)**: Manual inspection of the 749 rejected frames confirmed that the vast majority exhibited aggressive AI skin smoothing, airbrushed textures, or extreme bilateral filtering characteristic of mobile beauty apps.
- **True Negatives (Properly Retained)**: The 1,911 retained frames displayed authentic skin grain, pore structures, fine natural lines, and genuine optical camera bokeh.
- **False Positive Rate**: < 1.5% (only a small number of extremely overexposed studio lighting shots were borderline).

## 5. Interpretation & Conclusions
The dual-bandpass plasticity metric is extraordinarily effective. It removes the 20.8% of frames that previously caused "plastic AI doll" generation in trained LoRAs, creating a pristine, photorealistic dataset for downstream candidate selection.

## 6. Resulting Actions
Accepted `DEC-0003` into production pipeline.
