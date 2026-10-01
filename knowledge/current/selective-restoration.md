---
topic: selective-restoration
last_updated: 2026-10-01
confidence: HIGH
status: ACTIVE
related_decisions:
  - DEC-0004
related_failures:
  - FAIL-0001
related_cases: []
---

# Current Knowledge: Selective Face Restoration & Raw Skin Preservation

## 1. Current Policy
Whole-face neural upscaling or restoration is strictly forbidden. Restoration is confined exclusively to anatomically high-contrast components (eyes, pupils, eyebrows, lips). The cheeks, nose, forehead, neck, and background must retain 100% untouched camera sensor pixels to preserve authentic epidermal pores and film grain.

## 2. Recommended Approach
- **Step 09 Execution (`09_selective_restoration_gpu.bat`)**:
  1. Detect facial landmarks or parse facial semantic segments.
  2. Generate a dilated binary mask covering only:
     - Left and right eye orbits (including iris, pupils, eyelashes).
     - Eyebrows.
     - Vermilion border and mucosal surface of upper/lower lips.
  3. Apply CodeFormer with fidelity weight $w = 0.8$ to the localized crop.
  4. Perform soft Gaussian-feathered alpha compositing:
     $$\text{Output} = (\text{Raw Image} \times (1 - M)) + (\text{CodeFormer Image} \times M)$$
  5. If CodeFormer weights are absent, execute fail-safe fallback: copy untouched raw images directly to `work/restored/`.

## 3. Hard Rules (Enforced by Code)
- Never blend restored pixels into cheek, forehead, or neck masks.
- Preserved regions must mathematically match source camera pixel values ($M = 0$).

## 4. Soft Rules (Guidelines for Human Review)
- In Step 08 / post-Step 09 review, inspect eye pupils to ensure gaze direction was not subtly shifted by CodeFormer.

## 5. Validated Conditions (Works When)
- Verified to produce sharp, realistic portrait LoRAs that render genuine skin micro-details (pores, fine lines) while retaining crisp eye reflections.

## 6. Known Failure Modes & Limitations (Unreliable When)
- **Whole-Face CodeFormer**: Applying CodeFormer globally destroys skin pores and produces plastic AI skin (`FAIL-0001`).

## 7. Do Not Use When
- Do NOT apply to stylized 2D illustration datasets where skin pores are inappropriate.

## 8. Not Yet Validated
- Subjects with intricate facial tattoos across cheek regions.
