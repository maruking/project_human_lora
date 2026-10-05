---
id: DEC-0002
title: Anatomical Face Sharpness Gate via Local Tenengrad Gradient
status: SUPERSEDED
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
superseded_by: [DEC-0014]
related_experiments:
  - EXP-20261002-006
  - EXP-20261002-005
related_failures:
  - FAIL-0002
related_cases:
  - CASE-0002
---

# Decision Record: DEC-0002 - Anatomical Face Sharpness Gate

> STEP2 clarification (DEC-0008): historical coarse global-gate wording below is not an active STEP2 rule. STEP2 measures only; no STEP3 code or local threshold was changed or revalidated.

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
