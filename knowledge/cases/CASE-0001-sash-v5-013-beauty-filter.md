---
id: CASE-0001
title: Beauty-Filter Edge-Sharpness Anomaly on Sample Sash_v5_013
date: 2026-10-01
confidence: HIGH
components:
  - face-quality
tags:
  - beauty-filter
  - counterexample
  - plastic-skin
  - laplacian-anomaly
related_experiment: EXP-20261001-002
related_decision: DEC-0003
related_failure: []
---

# Case Record: CASE-0001 - Beauty-Filter Edge-Sharpness Anomaly

## 1. Input & Source
- **Image Identifier**: `Sash_v5_013`
- **Source**: Vertical smartphone video clip from TikTok / Instagram Reels
- **Resolution**: 1080x1920
- **Visual Description**: Subject looks directly into camera; facial outlines and makeup eyeliner are extremely sharp, but skin resembles a smooth digital painting or anime porcelain doll.

## 2. Relevant Metrics (Facts)
- **Global Blur Score (Step 02)**: 142.3 (Well above 80.0 passing threshold)
- **Face Sharpness (Tenengrad)**: 185.2 (Ranked in top 5% of dataset)
- **Occlusion Ratio**: 0.04 (Passed)
- **Skin Texture Score**: 1.34 (Abnormally low high-frequency energy)
- **Plasticity Ratio**: **138.2** (Massively exceeds threshold of 70.0)

## 3. Expected Behavior vs. Actual Behavior
- **Expected (Standard Heuristic)**: With a face sharpness of 185.2, the heuristic classified this frame as one of the best images in the entire dataset.
- **Actual (Human Review)**: Human reviewer flagged this frame as unusable: *"This frame looks like a drawing or plastic doll; skin pores are totally absent."*

## 4. Why This Case Matters
This frame broke the fundamental assumption of computer vision filters: **"Higher edge gradient equals sharper photographic quality."**  
Commercial mobile beauty filters aggressively boost contrast along facial boundaries while heavily smoothing skin surfaces. Treating edge gradient magnitude as a proxy for photographic quality caused the pipeline to actively prioritize filtered, doll-like faces over genuine photographs.

## 5. What Rule or Assumption It Breaks
- Broken Assumption: $\text{Gradient Variance} \propto \text{Photographic Quality}$.
- Reality: $\text{Gradient Variance}$ can be synthetically manufactured by digital edge sharpeners.

## 6. Technical Interpretation
Mobile beauty filters apply an edge-preserving bilateral or guided filter to luminance channels, stripping high spatial frequencies ($k > 15 \text{ cycles/degree}$) in epidermal regions, followed by an unsharp mask filter on chromatic boundaries. The high gradient comes from artificial filter coefficients, not optical photons striking a camera sensor.

## 7. Action Taken / Resolution
Created the Dual-Bandpass Plasticity Gate in `face_quality_gate.py` (`DEC-0003`). The ratio of `face_sharpness / skin_texture_score` flags this frame with `plasticity_ratio = 138.2`, successfully rejecting it automatically before Step 07 candidate selection.
