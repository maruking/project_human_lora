---
id: DEC-0005
title: Multi-Objective Quota Balancing for LoRA Training Datasets
status: ACCEPTED
date: 2026-09-30
confidence: HIGH
components:
  - candidate-selection
  - pose-classification
tags:
  - quota
  - aspect-ratio
  - composition
  - diversity
  - overfitting
supersedes: []
superseded_by: []
related_experiments: []
related_failures:
  - FAIL-0003
related_cases: []
---

# Decision Record: DEC-0005 - Multi-Objective Quota Balancing

## 1. Context & Problem Statement
When selecting top images based purely on composite quality scores (sharpness + identity similarity), candidate pools inevitably suffer from catastrophic distribution collapse:
1. **Frontal Bias**: 90%+ of selected images are direct frontal stares into the camera (which typically have the highest sharpness and face detector confidence).
2. **Close-Up Bias**: Close-up selfies score much higher than full-body or medium shots because the face occupies more pixels.  
Training a LoRA on such an unbalanced dataset creates a model that:
- Cannot generate profile, 3/4 angle, or looking-away poses ("angle lock").
- Destroys full-body prompting capabilities (always zooming in on the face).

## 2. Previous Approach
Greedy top-N ranking: Sort all passing frames by `composite_score` and pick the top 30 images.

## 3. Hypothesis
Enforcing strict composition and head pose quotas during Step 07 candidate selection will produce a robust, versatile LoRA capable of rendering any shot type and viewing angle on command.

## 4. Alternatives Considered
- **Option A (Chosen)**: Two-tier quota enforcement:
  1. **Shot Type Distribution**:
     - Close-up (Face $> 25\%$ frame height): **40%**
     - Medium Shot (Upper body / Face $10\% - 25\%$): **40%**
     - Full Body / Wide (Face $< 10\%$): **20%**
  2. **Head Pose Quotas**:
     - Frontal (Yaw $|\theta| \le 15^\circ$): ~50% max
     - Half-Profile ($15^\circ < |\theta| \le 45^\circ$): ~35%
     - Full Profile ($45^\circ < |\theta| \le 90^\circ$): ~15%
- **Option B (Uniform random sampling across clusters)**: (Rejected: Randomly picks soft or blurry images inside low-performing clusters).

## 5. Decision & Implementation
Implemented in `scripts/score_lora_candidates.py` (Step 07).  
Images are categorized by Shot Type and Pose Bin. Inside each quota bin, images are ranked by multi-objective score ($0.35 \times \text{Identity} + 0.25 \times \text{FaceSharpness} + 0.15 \times \text{GlobalBlur} + 0.25 \times \text{Diversity}$) to pick the best representation.

## 6. Reasoning & Evidence
- **Fact**: Testing on FLUX LoRA training confirmed that without quota enforcement, 28 out of 30 images were frontal close-ups. With quota enforcement, test generations accurately rendered side profiles, 3/4 poses, and full-length runway shots while maintaining subject likeness.
- **Interpretation**: Balanced representation in training data directly dictates diffusion model steering freedom.

## 7. Consequences
- **Positive**: Eliminates angle-lock and zoom-bias; produces commercial-grade, versatile LoRAs.
- **Negative**: Requires capturing video sources that actually contain full-body and profile shots.
