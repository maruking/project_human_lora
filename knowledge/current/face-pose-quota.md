---
topic: face-pose-quota
last_updated: 2026-10-01
confidence: HIGH
status: ACTIVE
related_decisions:
  - DEC-0005
related_failures:
  - FAIL-0003
related_cases: []
---

# Current Knowledge: Face Pose & Composition Quota Distribution

## Active STEP4 v2 — measurement only (2026-10-05)

[DEC-0021](../decisions/DEC-0021-step4-stored-pose-face-scale.md) defines
step4_pose_composition_v2: full BEST v2.2 input, stored measured yaw/pitch/roll,
no inference/ranking/rejection/quotas/Human Review features. face_scale_bin uses
existing Face Gate SSOT area thresholds (current0.12/0.04); shot_type is its alias,
not literal body visibility. Face height ratio remains raw, not 25%/10% categories.
Yaw <=15 frontal, 15<abs<42 three-quarter, >=42 profile under current SSOT;
positive RIGHT/negative LEFT is repository convention, not mirror-independent
anatomy. Pitch endpoints -20/+20 are LEVEL. Roll/position bins are NOT_CLASSIFIED.
Fatal/missing/error rows stay in the full audit. Synthetic/six-row checks only;
production distribution pending ★maru. Old STEP4 code and the historical sections
below are retained; height-based categories are not active STEP4 v2 semantics.
The subsequent [production summary](../../docs/STEP4_POSE_COMPOSITION_SUMMARY.md)
now supplies the complete measured/missing-pose distribution; the implementation-time
pending description above is historical. STEP7 quotas remain out of scope.
Normal run_all now runs STEP5 v2, then stops before STEP6 for cluster/pose review;
see [deduplication Knowledge](deduplication.md).

## Historical STEP7 Revision B (2026-10-02; superseded by DEC-0024)

The former STEP7 BAT selected report-only proposals using `step7_revision_b` SSOT
settings and complete reviewed A/B/C state. A is primary; confirmed B fills actual
coverage/minimum-count shortages; pending B remains a review reserve; C is excluded.
Current configured target is 40 within 35–45. Duplicate-group/source caps and angle,
composition and small up/down diversity apply; unknown expression requires review.
The historical 65-pool implementation and older numeric recommendations below
remain evidence, not the new allocator. STEP4/5/6 logic is unchanged. Full production
selection has not been executed by Codex. See [DEC-0013](../decisions/DEC-0013-revision-b-candidate-selection.md)
and [result/prerequisites](../../docs/STEP7_REVISION_B_RESULT.md). Normal runner stops
after STEP7 until the legacy STEP8 handoff is revised separately.

> STEP0 implementation audit: current Step4 uses yaw 15/42 and pitch +/-20; Step7 uses fixed min/max maps with a 65-image pool; Step8 defaults to 45 with displayed 18/62/20. The 40/40/20 policy below is not a current runtime allocator. See [configuration.md](configuration.md).


## 1. Current Policy
A high-performance LoRA must avoid "frontal angle lock" and "close-up bias". The pipeline enforces a two-tier quota: Shot Type (Close-up, Medium, Full Body) and Head Pose Angle (Frontal, Half-Profile, Profile) during candidate selection (Step 07).

## 2. Recommended Approach
- **Pose Classification (Step 04)**: Classify each frame into discrete Yaw bins (Frontal: $\pm 15^\circ$, Half-Profile: $15^\circ-45^\circ$, Profile: $45^\circ-90^\circ$) and Pitch bins using facial landmark 3D projection.
- **Shot Composition (Step 04)**: Categorize frames based on face area ratio relative to image canvas:
  - Close-up: Face height $> 25\%$ of canvas.
  - Medium Shot: Face height $10\% - 25\%$.
  - Full Body / Wide: Face height $< 10\%$.
- **Quota Balancing (Step 07)**: Pick candidates according to target allocation before filling residual slots with top general quality scores.

## 3. Hard Rules (Enforced by Code)
- Target dataset size: **25 to 35 images** (optimal for FLUX.1 LoRA fine-tuning).
- Shot Type Target Quota:
  - Close-up: **40%**
  - Medium shot: **40%**
  - Full body / Wide: **20%**
- Head Pose Constraint: Frontal staring poses must not exceed 50% of the selected dataset.

## 4. Soft Rules (Guidelines for Human Review)
- Verify that non-frontal poses still clearly exhibit the subject's distinctive features (nose profile, jawline, eye shape).
- If source videos completely lack full-body shots, fill the 20% slot with lower-angle medium shots rather than more close-ups.

## 5. Validated Conditions (Works When)
- Produces balanced FLUX LoRA models that respond cleanly to prompts for side profiles, 3/4 angles, and full-length walking shots.

## 6. Known Failure Modes & Limitations (Unreliable When)
- **Extreme Profile (>80 degrees)**: Face detection landmarks become unstable when one eye is completely occluded. The pipeline relies on single-eye fallback geometry.

## 7. Do Not Use When
- Do NOT use top-N score greedy ranking without quota partitioning (`FAIL-0003`).

## 8. Not Yet Validated
- Drone aerial footage or severe overhead bird's-eye camera angles ($> 60^\circ$ pitch).

## Active STEP7 v2.1 — 2026-10-05

Bounded BEST guard/core plus optional soft review options replaces old quotas/A-B-C runtime dependence for this generation. Missing pose options remain shortages; guard/core/caps are not relaxed. Source caps and one-per-cluster constrain options; no pose percentage maximum. STEP8 final35–45 human authority. FULL_BODY remains face-area scale. See [candidate selection](candidate-selection.md) and DEC-0025.
