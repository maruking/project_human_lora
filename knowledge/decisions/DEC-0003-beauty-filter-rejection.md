---
id: DEC-0003
title: Dual-Bandpass Plasticity Metric for Beauty Filter Rejection
status: SUPERSEDED
date: 2026-10-01
confidence: HIGH
components:
  - face-quality
  - realism-filter
tags:
  - beauty-filter
  - plastic-skin
  - bandpass-filter
  - texture-preservation
supersedes: []
superseded_by: [DEC-0014]
related_experiments:
  - EXP-20261002-006
  - EXP-20261002-005
  - EXP-20261001-002
related_failures: []
related_cases:
  - CASE-0001
---

# Decision Record: DEC-0003 - Dual-Bandpass Plasticity Metric

## 1. Context & Problem Statement
Smartphone video apps (TikTok, Instagram, Douyin) routinely apply real-time beauty filters. These filters heavily bilateral-blur human skin to erase pores, wrinkles, and blemishes, while applying synthetic sharpening to eye and face contours. When evaluated by conventional sharpness metrics (Laplacian/Tenengrad), these filtered faces score anomalously high because of the over-sharpened edges. Training a LoRA on these images causes the model to generate artificial, doll-like, plastic skin that looks like digital illustration or CGI rather than a photograph.

## 2. Previous Approach
No filter detection. Only `face_sharpness` and `occlusion_ratio` were evaluated in Step 03. Consequently, extreme beauty-smoothed frames (e.g. `Sash_v5_013`) passed into the candidate pool with top sharpness ranks.

## 3. Hypothesis
Authentic photographic skin contains high-frequency stochastic micro-textures (pores, hair follicles, sensor noise) distributed evenly across the cheeks and forehead. Beauty filters create a severe discrepancy: high edge gradients alongside near-zero high-frequency skin texture.  
A dual-bandpass metric—measuring high-frequency skin texture response against macroscopic edge sharpness (`plasticity_ratio = edge_score / skin_texture_score`)—can mathematically identify and reject beauty-smoothed faces.

## 4. Alternatives Considered
- **Option A (Chosen)**: Dual-bandpass plasticity gate. Compute `skin_texture_score` on cheek/forehead patches and compute `plasticity_ratio`. Reject if `plasticity_ratio > 70.0` or `skin_texture_score < 15.0`.
- **Option B (Deep learning filter classifier)**: Train a binary CNN or ResNet classifier. (Rejected: Requires thousands of labeled training frames, adds heavy GPU dependencies, and does not generalize across diverse lighting).
- **Option C (Color variance / saturation analysis)**: (Rejected: Failed on fair-skinned subjects with natural porcelain skin in studio lighting).

## 5. Decision & Implementation
Implemented in `scripts/face_quality_gate.py` (Step 03).
```python
# Cheek and forehead skin ROI bandpass extraction
skin_texture_score = np.std(cv2.Laplacian(skin_roi, cv2.CV_64F))
plasticity_ratio = (face_sharpness / max(skin_texture_score, 0.1))
if plasticity_ratio > 70.0 or skin_texture_score < 15.0:
    rejection_reason = "beauty_filter_detected"
```

## 6. Reasoning & Evidence
- **Fact (EXP-20261001-002)**: Evaluated on 3,607 video frames:
  - Rejected 749 heavily filtered frames (20.8% of the dataset).
  - Pinpoint-identified `Sash_v5_013` (plasticity ratio: 138.0, visually confirmed as doll-like painting).
  - Retained 1,911 truly authentic photographic frames.
- **Interpretation**: The dual-bandpass ratio precisely separates edge-over-sharpened plastic skin from genuine optical sharpness.

## 7. Consequences
- **Positive**: Eradicates AI-sheen and plastic face generation in trained LoRAs; enforces photographic pore texture.
- **Negative / Trade-offs**: In extremely low-light or heavily compressed videos, genuine skin texture may be blurred by camera noise reduction, causing slight false rejections. This is acceptable as low-light compressed frames should not be in the training set anyway.


## STEP3 Revision1 implementation evidence (2026-10-02)
[EXP-20261002-005](../../experiments/EXP-20261002-005-step3-full-audit.md)
validates complete2001-row execution and deterministic existing Gate behavior. All Gate
values and kernels retained; this does not independently validate heuristic accuracy.
[Gate audit](../../docs/STEP3_GATE_AUDIT.md) separates historical descriptions/scales
from actual production configuration. Original decision evidence is preserved.


## Calibration evidence; no policy change
[EXP-20261002-006](../../experiments/EXP-20261002-006-step3-calibration-review.md) adds contribution/boundary/eye-disablement analysis and a human review package under unchanged Gates. Accuracy and tuning remain pending human labels; this is not a new accepted threshold decision.


## Superseded production Gate architecture — 2026-10-03

[DEC-0014](DEC-0014-canonical192-face-gate.md) supersedes the native sharpness / eye-first / beauty Hard Gate architecture. Earlier evidence and rationale remain historical. Local face measurement and source skin preservation principles remain; canonical192 is implemented following explicit user approval, full production rerun pending maru.
