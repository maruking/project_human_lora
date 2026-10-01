---
id: DEC-0002
title: Anatomical Face Sharpness Gate via Local Tenengrad Gradient
status: ACCEPTED
date: 2026-09-30
confidence: HIGH
components:
  - face-quality
tags:
  - sharpness
  - blur
  - face-crop
  - depth-of-field
supersedes: []
superseded_by: []
related_experiments: []
related_failures:
  - FAIL-0002
related_cases:
  - CASE-0002
---

# Decision Record: DEC-0002 - Anatomical Face Sharpness Gate

## 1. Context & Problem Statement
In smartphone photography with shallow depth-of-field or portrait mode, backgrounds (such as textured brick walls, trees, or crowd patterns) are often razor sharp while the subject's face is out of focus or motion-blurred. Evaluating image sharpness solely across the global canvas lets through hundreds of blurry-faced images.

## 2. Previous Approach
Relying solely on Step 02 Global Laplacian Variance (`score_blur.py`) over the entire full-resolution frame.

## 3. Hypothesis
Evaluating high-frequency gradients specifically inside the tightly cropped facial bounding box (using Sobel/Tenengrad gradient magnitude) will isolate true facial focus from background clutter.

## 4. Alternatives Considered
- **Option A (Chosen)**: Two-stage evaluation: Global blur check in Step 02, followed by localized face-crop Tenengrad gradient scoring in Step 03 (`face_sharpness >= 18.0`).
- **Option B (Whole-image gradient threshold increase)**: Raising global Laplacian threshold to 300+. (Rejected: Rejects perfectly sharp close-up portraits with naturally creamy bokeh backgrounds).

## 5. Decision & Implementation
Implemented in `scripts/face_quality_gate.py` (Step 03).  
The face bounding box detected by MediaPipe is cropped, converted to grayscale, and evaluated using Tenengrad gradient variance $\frac{1}{N} \sum (G_x^2 + G_y^2)$. Any face with `face_sharpness < 18.0` is discarded.

## 6. Reasoning & Evidence
- **Fact**: Images like `Sample_Dof_042` had global Laplacian scores > 320 due to sharp background tiles, but facial sharpness scored only 6.4.
- **Interpretation**: Localized face sharpness gating prevents blurry faces from corrupting LoRA facial detail learning.

## 7. Consequences
- **Positive**: Guarantees that only in-focus eyes and skin textures reach candidate selection.
- **Negative**: Adds face detection compute overhead, which is mitigated by running lightweight MediaPipe.
