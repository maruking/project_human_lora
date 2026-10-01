---
topic: identity-evaluation
last_updated: 2026-10-01
confidence: HIGH
status: ACTIVE
related_decisions: []
related_failures: []
related_cases: []
---

# Current Knowledge: Identity Evaluation & Imposter Exclusion

## 1. Current Policy
Automated identity verification guarantees that every frame selected for LoRA training depicts the intended target subject and eliminates strangers, friends, family members, or background bystanders.

## 2. Recommended Approach
- **Reference Gallery**: Place 3 to 10 confirmed high-resolution reference portraits of the target individual into `input/reference/`.
- **InsightFace Feature Vector Extraction (Step 06)**: Extract 512-dimensional normalized facial embedding vectors using the `buffalo_l` (ResNet50-based) model.
- **Cosine Centroid Matching**: Compute the cosine similarity against the centroid of the reference gallery.
- **Multi-Face Handling**: In frames with multiple detected people, identify the bounding box with the highest target similarity. If no face exceeds the threshold, or if an imposter dominates the center frame, reject the image.

## 3. Hard Rules (Enforced by Code)
- `min_similarity_threshold`: 0.55 cosine similarity against reference centroid.
- Frames failing this similarity are routed to `work/identity_review/` and excluded from candidate selection.

## 4. Soft Rules (Guidelines for Human Review)
- In Step 08 visual inspection, check for edge cases where the subject's twin sibling or lookalike might have passed the 0.55 threshold.
- Check that heavy makeup or cosplay costumes haven't degraded identity confidence below 0.55.

## 5. Validated Conditions (Works When)
- Tested across diverse lighting, hair colors, hairstyles, and facial expressions. 0.55 cosine similarity consistently rejects background bystanders and random individuals while retaining true subject frames across varied makeup styles.

## 6. Known Failure Modes & Limitations (Unreliable When)
- **Extreme Age Drift**: Comparing childhood photos against adult videos can fall below the 0.55 threshold. Ensure reference photos are contemporaneous with the video footage.

## 7. Do Not Use When
- Do NOT run identity evaluation with only a single reference image containing harsh shadows or sunglasses. Use multiple clean references.

## 8. Not Yet Validated
- Extreme SFX theatrical prosthetic makeup (e.g. fantasy prosthetics, full-face masks).
