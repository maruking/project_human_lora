---
id: CASE-0002
title: Sharp High-Texture Background Masking Blurry Subject Face
date: 2026-09-30
confidence: HIGH
components:
  - face-quality
  - technical-metrics
tags:
  - blur
  - depth-of-field
  - counterexample
  - bokeh
related_experiment: []
related_decision: DEC-0002
related_failure: FAIL-0002
---

# Case Record: CASE-0002 - Sharp Background Masking Blurry Face

## 1. Input & Source
- **Sample Identifier**: `Sample_Dof_042`
- **Source**: Outdoor street walking video, subject in foreground against an exposed brick wall background.
- **Resolution**: 1080x1920

## 2. Relevant Metrics (Facts)
- **Global Blur Score (Step 02)**: **324.5** (Far exceeds passing threshold of 80.0; ranks in top 10% overall)
- **Face Sharpness (Tenengrad)**: **6.4** (Far below passing threshold of 18.0)
- **Face Bounding Box Area**: Occupies 14% of canvas area.

## 3. Expected Behavior vs. Actual Behavior
- **Expected (Global Metric)**: Passed with flying colors as a prime candidate based on whole-image Laplacian score.
- **Actual (Human Review)**: The subject's face is completely blurred due to autofocus tracking hunting backward onto the brick wall.

## 4. Why This Case Matters
Proves that whole-image Laplacian variance is completely decoupled from subject focus when the background contains dense high-frequency textures (brick mortar, tree leaves, chain-link fences).

## 5. What Rule or Assumption It Breaks
- Broken Assumption: "A high Laplacian score on the canvas implies the subject is in focus."

## 6. Technical Interpretation
The brick wall occupies 86% of the frame pixels and contains hundreds of sharp high-contrast mortar lines, generating massive second-derivative gradient spikes. The out-of-focus face contributes negligible negative variance relative to the overpowering background signal.

## 7. Action Taken / Resolution
Formalized `DEC-0002`: Established localized facial bounding box Tenengrad gradient evaluation as an independent mandatory gate in Step 03, immediately rejecting `Sample_Dof_042`.
