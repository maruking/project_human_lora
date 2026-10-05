---
topic: identity-evaluation
last_updated: 2026-10-05
confidence: MEDIUM
status: ACTIVE
related_decisions: [DEC-0023]
related_failures: []
related_cases: []
---

# Current Knowledge: Identity Evaluation & Imposter Exclusion

## ACTIVE — STEP6 Identity Verification v2 / DEC-0023

Normal `06_evaluate_identity_gpu.bat` runs `step6_identity_v2.py` in dedicated
`.venv-step6` (Python3.10). `setup_step6_identity.bat` installs frozen local runtime;
legacy evaluate_identity.py and its DINO config snapshot remain historical.
InsightFace buffalo_l detection/recognition uses the same original-image alignment
for confirmed reference anchors and target candidates. Config SSOT historical
identity threshold0.55 is fixed, with no pose/scale relaxation or quality/review
features. No current-generation FAR/FRR or universal accuracy claim.

Reference-only phase requires3–20 valid, independent confirmed images, exactly one
face each, finite nonzero embeddings and all leave-one-out similarities>=0.55.
Invalid/outlier references STOP; never silently drop. Production requires matching
PASS reference audit, inventory/model/library/report hashes and remeasured gallery.
L2-normalize vectors -> mean -> L2-normalize centroid; retain anchor bank in memory.

Unique/representative STEP5 v2 targets only. All upstream rows/columns are retained;
duplicate members are NOT_APPLICABLE_DUPLICATE_MEMBER, not identity rejects.
Fatal rows are NOT_APPLICABLE_UPSTREAM, errors UPSTREAM_ERROR. No legacy
face_eligible target control. Multi-face candidate association uses unique positive
maximum IoU to persisted bbox then REVIEW; ties/no-overlap STOP without new thresholds.
No face/invalid embedding is NOT_EVALUABLE with blank similarity, never artificial0.
Centroid>=threshold PASS, centroid below but max anchor>=threshold REVIEW,
both below REJECT if measurement valid. identity_state is authoritative.

Source-linked reference/identity HTML is derived human calibration material,
not source/ref/training data. PASS boundary section shows lowest20 similarities.
Representative REJECT/NOT_EVALUABLE flags fallback-needed, never promotes/evaluates
members automatically. Partial/error runs isolated; atomic files, summary last,
archive+rollback; process-crash multi-file transaction not guaranteed.

Observed: current upstream1951 rows, default identity targets1079 (not code constants).
Seven references PASS real GPU reference-only audit; LOO0.66275–0.76238.
34 synthetic tests +8 config tests PASS. Full candidate production NOT run.
Sources/STEP3–5/history/A/B/C unchanged; STEP7 handoff/selection is deferred.
[DEC-0023](../decisions/DEC-0023-step6-insightface-identity.md),
[implementation](../../docs/STEP6_IDENTITY_V2_IMPLEMENTATION.md),
[reference audit](../../docs/STEP6_REFERENCE_AUDIT.md).


> STEP0 implementation audit: actual Step6 uses DINO `facebook/dino-vitb16` and dynamic shot/pose gates. InsightFace/buffalo_l and the fixed 0.55 threshold below describe intended policy, not current runtime. See [configuration.md](configuration.md). InsightFace migration is deferred.


## HISTORICAL intended policy below (not current runtime evidence)

The original text is retained as historical evidence. Its claimed guarantees and
validated conditions were not supported by the legacy DINO runtime and are not
current-generation accuracy claims. DEC-0023 and the active section above govern.

## 1. Historical Policy
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
