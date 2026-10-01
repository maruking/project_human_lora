---
id: FAIL-0002
title: Global-Blur-Only Frame Selection
date: 2026-09-30
confidence: HIGH
components:
  - face-quality
  - technical-metrics
tags:
  - blur
  - laplacian
  - false-positive
  - depth-of-field
related_experiment: []
related_decision: DEC-0002
---

# Failure Record: FAIL-0002 - Global-Blur-Only Frame Selection

## 1. Context & Objective
Filter out out-of-focus and motion-blurred video frames using an ultra-fast OpenCV Laplacian variance pass (`cv2.Laplacian(img, cv2.CV_64F).var()`).

## 2. The Attempted Approach
Discard any frame where the full image global Laplacian variance fell below threshold $T = 100.0$, assuming passing frames possessed sharp subjects.

## 3. Why It Looked Reasonable at the Time
- Whole-image Laplacian is standard industry practice in rapid video frame deduplication.
- Highly efficient (takes < 10ms per 1080p frame on CPU).

## 4. Observed Failure (Facts)
- **High False Positive Rate**: Numerous frames with Laplacian scores exceeding 300+ were accepted, but upon inspection, the subject's face was completely out-of-focus or motion-blurred (e.g. `Sample_Dof_042`).
- **High False Negative Rate**: Gorgeous, close-up portraits shot with a wide-aperture lens ($f/1.4$) where the subject's eyes were tack-sharp but the background was smoothly blurred (bokeh) scored only 45–60 globally and were erroneously discarded.

## 5. Root Cause Analysis (Interpretation)
The Laplacian operator measures high-frequency intensity transitions across the entire 2D matrix. In shots where the background contains high-frequency textures (brick walls, tree foliage, fabric weaves, crowds), the background pixels dominate the global variance calculation, completely obscuring a blurry face in the foreground. Conversely, creamy bokeh backgrounds depress the global average even when the face is crisp.

## 6. Conditions Where It Failed
- Any video featuring shallow depth of field, portrait mode, or textured backgrounds.
- Any medium or full-body shot where the face occupies less than 30% of total canvas area.

## 7. Conditions Where It May Still Work
- Studio shots on flat gray seamless backdrops where the background has zero texture.
- Macro photography where the subject occupies 95%+ of the image frame.

## 8. DO NOT RETRY UNLESS (Mandatory Guardrail)
> [!CRITICAL]
> **DO NOT RETRY UNLESS:**
> The input video pipeline guarantees that 100% of footage is shot on uniform zero-texture studio cycloramas, or faces are guaranteed to occupy >= 90% of the canvas.

## 9. Superseded By / Counter-measure
**`DEC-0002` (Anatomical Face Sharpness Gate)**: Retained global blur solely as a coarse pre-filter, while establishing localized face bounding box Tenengrad gradient evaluation (`face_sharpness >= 18.0`) as the authoritative quality gate.
