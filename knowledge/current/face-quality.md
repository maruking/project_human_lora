---
topic: face-quality
last_updated: 2026-10-01
confidence: HIGH
status: ACTIVE
related_decisions:
  - DEC-0002
  - DEC-0003
related_failures:
  - FAIL-0002
related_cases:
  - CASE-0001
  - CASE-0002
---

# Current Knowledge: Face Quality & Beauty Filter Rejection

## 1. Current Policy
Face quality evaluation operates on a two-tier strategy: global canvas blur detection (Step 02) followed by localized face-crop anatomical sharpness and dual-bandpass plasticity gating (Step 03). Any frame with blurry facial features or artificial beauty-filter skin smoothing is systematically rejected.

## 2. Recommended Approach
- **Global Blur (Step 02)**: Use `score_blur.py` to flag grossly blurred frames (`min_blur_score = 80.0`).
- **Face Quality Gate (Step 03)**: Use `face_quality_gate.py` with MediaPipe face detection to evaluate local Tenengrad gradient, landmark occlusion, and the `plasticity_ratio` ($R = \frac{\text{EdgeSharpness}}{\text{SkinTexture}}$).

## 3. Hard Rules (Enforced by Code)
- `min_face_size`: 120 pixels.
- `min_face_sharpness`: 18.0 (Tenengrad variance on face bounding box).
- `max_occlusion_ratio`: 0.35 (max 35% landmark occlusion).
- `max_plasticity_ratio`: 70.0 (anti-beauty-filter limit).
- `min_skin_texture_score`: 15.0 (cheek/forehead high-frequency micro-texture).

## 4. Soft Rules (Guidelines for Human Review)
- In Step 08 visual inspection, check for motion blur streaks on hair or jewelry even if the eyes passed sharpness thresholds.
- Check for sunglass occlusions or heavy hand occlusions that face detectors might occasionally miss.

## 5. Validated Conditions (Works When)
- Tested across 3,607 frames from 82 real smartphone vertical videos (1080p, 720p).
- Accurately discriminates true photographic skin texture from TikTok/Instagram beauty filters (20.8% filter rejection rate).

## 6. Known Failure Modes & Limitations (Unreliable When)
- **High-texture backgrounds with out-of-focus faces**: Global blur alone fails completely (`FAIL-0002`, `CASE-0002`); always require Step 03 local face sharpness.
- **Overexposed studio lighting**: Blown-out highlights on skin can cause artificial texture dropouts; inspect in Step 08.

## 7. Do Not Use When
- Do NOT use whole-image Laplacian variance as the sole arbiter of portrait quality.
- Do NOT use edge-gradient metrics without the dual-bandpass plasticity check on social media video sources.

## 8. Not Yet Validated
- Extreme low-light footage shot in near pitch black with heavy phone ISO noise reduction.
- Anamorphic or heavy barrel-distortion camera lenses.
