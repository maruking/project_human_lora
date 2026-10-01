---
id: FAIL-0003
title: Top-Score Greedy Selection Causing Frontal Angle Collapse
date: 2026-09-30
confidence: HIGH
components:
  - candidate-selection
tags:
  - greedy-ranking
  - angle-collapse
  - frontal-bias
  - diversity
related_experiment: []
related_decision: DEC-0005
---

# Failure Record: FAIL-0003 - Top-Score Greedy Selection

## 1. Context & Objective
Select the optimal 30 frames from a pool of 2,000+ candidates for FLUX LoRA fine-tuning.

## 2. The Attempted Approach
Sort all candidates descending by composite quality score ($\text{Score} = 0.5 \times \text{Identity} + 0.3 \times \text{FaceSharpness} + 0.2 \times \text{BlurScore}$) and select the top 30 images.

## 3. Why It Looked Reasonable at the Time
Choosing the mathematically highest quality images seems intuitively optimal: sharpest faces, highest confidence recognition, least blur.

## 4. Observed Failure (Facts)
- Out of 30 selected frames, **28 were direct frontal camera stares** and 29 were close-up selfie angles.
- Zero profile shots (looking left/right) and zero full-body shots were selected.
- **LoRA Angle Lock**: When the trained LoRA was prompted with "profile view, looking to the side" or "full body shot walking on street", the model repeatedly generated frontal headshots, completely ignoring prompt direction.

## 5. Root Cause Analysis (Interpretation)
Face detection models and landmark extractors naturally report significantly higher confidence and cleaner bounding boxes on frontal faces. Furthermore, facial features (both eyes, nose tip, lips) contribute maximal gradient response when facing directly forward. In contrast, profile poses only expose one eye and have less facial surface area, yielding slightly lower raw metric scores. Greedy sorting inevitably starves non-frontal poses.

## 6. Conditions Where It Failed
- Universal failure for general-purpose character LoRAs.

## 7. Conditions Where It May Still Work
- Passport photo or direct ID badge generation models where profile poses are forbidden by design.

## 8. DO NOT RETRY UNLESS (Mandatory Guardrail)
> [!CRITICAL]
> **DO NOT RETRY UNLESS:**
> The LoRA project explicitly requires a single fixed front-facing headshot (e.g. corporate passport photos) and explicitly forbids varied angles or wide shots.

## 9. Superseded By / Counter-measure
**`DEC-0005` (Multi-Objective Quota Balancing)**: Partitioning selection into explicit Shot Type bins (Close-up 40%, Medium 40%, Full-body 20%) and Head Pose bins (Frontal, Half-Profile, Profile), ranking candidates strictly *within* their allocated quota bucket.
