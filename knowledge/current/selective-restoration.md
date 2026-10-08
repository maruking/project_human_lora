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

> STEP0 implementation audit: current Step9 restores full face crops in selected full-body shots with Gaussian feathering and rollback, not the component-only mask specified below. This gap remains for STEP9; STEP0 preserves existing behavior. See [configuration.md](configuration.md).


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

## 2026-10-07 diagnostic-only STEP9 branch

Current user request permits diagnostics only on validated STEP8_ACCEPT images;
restoration/inference/image copying andSTEP10 are forbidden. Normal legacy09 BAT
remains guarded;09_diagnose_selected.bat calls step9_diagnostic.py only. Config owns
STEP9_DIAGNOSTIC.csv andSTEP9_DIAGNOSTIC_SUMMARY.md output paths, existing thresholds
unchanged. Classify by legacy FULL_BODY scope with face-dimension/old eye triggers;
missing/disabled old eye metric means review, never invent a local-detail substitute.
canonical metrics remain visible, with no newSTEP9 canonical cutoff.

Observed40 selected rows:30 protected shots RESTORATION_NOT_NEEDED,10 FULL_BODY
REVIEW_RECOMMENDED because legacy eye_sharpness unavailable. All40 face min dimensions
>=229px,above existing190 threshold. This is uncertainty review, not10 proven blur
or restoration cases.18 tests PASS; source/STEP8 hashes preserved. No automatic skip
because review_count>0. Chappy/Human review required for these10 before a skip decision.
[Diagnostic result](../../docs/STEP9_DIAGNOSTIC_SUMMARY.md).
Earlier mask enforcement/accuracy claims above are historical policy language, not
current validated production behavior; legacy implementation mismatch remains.
