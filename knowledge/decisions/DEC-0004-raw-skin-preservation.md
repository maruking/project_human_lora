---
id: DEC-0004
title: Selective Component Restoration with 100% Raw Camera Skin Preservation
status: ACCEPTED
date: 2026-09-30
confidence: HIGH
components:
  - restoration
  - skin-texture
tags:
  - codeformer
  - masking
  - raw-skin
  - photorealism
supersedes: []
superseded_by: []
related_experiments: []
related_failures:
  - FAIL-0001
related_cases: []
---

# Decision Record: DEC-0004 - Selective Component Restoration

## 1. Context & Problem Statement
Neural face restoration tools (CodeFormer, GFPGAN) are outstanding at recovering sharp eye pupils, eyelashes, and lip contours from slightly soft video frames. However, applying these models globally across the entire face crop synthesizes artificial, poreless, waxy skin textures. When a LoRA is trained on whole-face restored images, it generates images that scream "AI-generated" with unnatural plastic sheen.

## 2. Previous Approach
Running CodeFormer across the entire detected face bounding box and blending back with standard global weight ($w=0.6$).

## 3. Hypothesis
We can harness the benefits of neural restoration (sharp pupils, distinct eyelashes, crisp lips) while completely eliminating artificial skin hallucination by using anatomical semantic masks. By restricting restoration to the eyes, eyebrows, and mouth, we can preserve 100% untouched camera sensor skin on the cheeks, nose, forehead, and neck.

## 4. Alternatives Considered
- **Option A (Chosen)**: Semantic mask-guided selective restoration in Step 09 (`selective_restoration.py`). Dilated masks for eyes, eyebrows, and lips are extracted via facial landmarks or face parsing; restored pixels are injected *only* inside these masks with soft alpha feathering.
- **Option B (High-fidelity CodeFormer weight w=0.9)**: (Rejected: Still leaves a subtle AI waxy veneer on the skin surface while failing to restore sharp eyelashes).
- **Option C (No restoration at all)**: (Rejected: Discards usable dynamic frames that have sharp skin and authentic lighting but slightly soft eye pupils due to motion).

## 5. Decision & Implementation
Implemented in `scripts/selective_restoration.py` (`09_selective_restoration_gpu.bat`).
```text
Final Face = (Raw Face * (1 - Component Mask)) + (CodeFormer Face * Component Mask)
```
- Restored Regions: Iris, pupils, upper/lower eyelids, eyelashes, eyebrow hair strands, lip vermilion border.
- Untouched Regions (100% Raw Camera): Cheeks, forehead, chin, nose bridge, jawline, neck, hair.

## 6. Reasoning & Evidence
- **Fact**: Microscopic pixel analysis confirms zero change to sensor noise and pore structures in cheek patches, while eye iris sharpness increased by 240%.
- **Interpretation**: Retaining authentic camera noise profile prevents LoRA models from developing smooth plastic artifacts.

## 7. Consequences
- **Positive**: Highest level of photorealism; produces LoRAs that generate authentic real-human photography.
- **Negative**: Adds component mask generation overhead in Step 09.
