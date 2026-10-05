# STEP3 V2 FROZEN SPEC
Version: 1.0
Status: FROZEN FOR IMPLEMENTATION REVIEW
Scope: STEP3 Face Quality Gate only
Project: REAL_HUMAN_LORA / project_human_lora

---

## 1. Purpose

STEP3 removes only images that are **clearly unsuitable for LoRA face learning**.

STEP3 is NOT:
- final dataset selection
- pose quota management
- duplicate removal
- identity verification
- final 35–45 image selection
- restoration
- captioning
- training

Final candidate reduction and approval remain downstream:
STEP4 Pose / STEP5 Dedup / STEP6 Identity / STEP7 Candidate Selection / STEP8 Human Review.

Primary design goal:

> Minimize False Reject and False Accept while keeping the Gate deterministic, auditable, resolution-stable, and simple enough to maintain.

---

## 2. Input Universe

STEP3 V2 evaluates the complete current image universe in one schema:

- Formal video frames: current generation 1,893
- Supplemental stills: `Sash_high_identity-img` current generation 58
- Expected total: 1,951

Counts are metadata-derived and MUST NOT be hard-coded.

Required identity fields:
- `frame_id`
- `filename`
- `input_kind`
- `source_id`
- `video_id` when applicable
- `dataset_generation_id`
- image SHA256

`frame_id` must be unique across video and still inputs.

Supplemental stills are NOT a separate bypass pipeline. They are part of STEP3 V2 output.

However:
- video and still diagnostic distributions MUST be reported separately
- kind-specific thresholds MUST NOT be auto-learned from the 58 stills
- common Hard Reject semantics remain shared unless a later Decision explicitly changes this

---

## 3. Review Outputs Are Never Inputs

Temporary review directories:

- `output/reports/passed/`
- `output/reports/borderline/`

These are disposable copies for ★maru only.

They MUST NEVER be used as:
- STEP1/2/3 inputs
- supplemental inputs
- manifests
- lineage evidence
- candidate pools
- STEP4+ inputs

Deletion of these folders MUST NOT invalidate any formal generation.

All generic image discovery must explicitly exclude `output/reports/**`.

---

## 4. Gate Architecture

STEP3 V2 uses three levels:

### Tier A — Immediate Hard Reject
Only machine-closed conditions that do not require ambiguous visual interpretation.

### Tier B — Composite Hard Reject
Ambiguous visual defects that become Hard Reject only when multiple independent measurements agree.

### Diagnostic Only
Signals useful for review or downstream inspection but insufficient by themselves to reject.

No Diagnostic-only signal may independently set `face_eligible=false`.

---

# 5. Tier A — Immediate Hard Reject

## 5.1 No Face
Reject when no valid primary face is detected.

Output:
- `hard_reject_reason=no_face`

## 5.2 Confirmed Multiple Faces
Do not use one weak detector count alone.

Preferred behavior:
- detector count >1 AND detections satisfy configured confidence/size rules
- if detector disagreement exists, record `detector_disagreement` diagnostic instead of immediate reject until confirmation logic is available

If current implementation has only one detector, multiple-face rejection may remain temporarily, but the limitation MUST be documented.

Output:
- `hard_reject_reason=multiple_faces`

## 5.3 Face Not Evaluable
Reject only if face quality cannot be meaningfully evaluated.

Examples:
- no usable face bbox
- no usable landmark solution after permitted fallback
- invalid crop geometry
- face partly outside frame such that required ROI cannot be measured

Do NOT treat "landmark uncertain" and "occluded" as the same state.

Required states:
- `MEASURED`
- `NOT_EVALUABLE_LANDMARK`
- `NOT_EVALUABLE_FRAME_EDGE`
- `NOT_EVALUABLE_SCALE`

## 5.4 Face Too Small To Evaluate
This is a measurement-availability rule, not a quality judgment.

Use real face pixel size, not shot type alone.

The threshold MUST be configured in SSOT and documented in pixels.

A face that is too small to evaluate eye/mouth detail is:
- not evidence of occlusion
- not evidence of blur
- not evidence of closed eyes

---

# 6. Tier B — Composite Hard Reject

Tier B conditions MUST use explicit AND/OR formulas.
A single weak heuristic cannot cause Hard Reject.

## 6.1 External Eye / Face Occlusion

### Required semantic states
For each eye separately:
- `VISIBLE`
- `CLOSED_OR_BLINK`
- `EXTERNALLY_OCCLUDED`
- `OUT_OF_FRAME`
- `NOT_EVALUABLE`

Do not collapse these into one `one_eye_occluded` state.

### Required evidence
At minimum retain:
- left/right eye openness
- left/right eye presence
- left/right eye ROI size
- left/right eye local contrast / gradient
- yaw / pitch / roll
- face visibility
- face short-edge pixels

### Pose-aware applicability
Yaw must modify eye expectations.

- frontal / mild 3/4:
  - both eyes expected to be measurable if face scale is sufficient
- strong 3/4 / profile:
  - far-side eye may be naturally reduced or absent
  - do NOT label this as occlusion solely because of left/right asymmetry

FULL_BODY must NOT automatically skip eye checks.
Applicability depends on actual face pixel size and pose.

### Hard Reject condition
External eye/face occlusion may Hard Reject only when:
- face scale is evaluable
AND
- pose does not explain missing visibility
AND
- at least two independent occlusion indicators agree

Example independent families:
- landmark / openness inconsistency
- eye-region contrast / feature visibility
- segmentation / object overlap if available later

Until a robust external-occlusion detector exists, uncertain cases remain Diagnostic.

---

## 6.2 Motion Blur / Sharpness

### Resolution normalization
Native pixel-grid Laplacian thresholds are NOT used for Hard Reject.

Canonical face quality measurement is required.

### Canonical ROI
Face quality ROI must:
- contain both eyes, nose, and mouth
- exclude as much hair/background as practical
- preserve geometry consistently
- use fixed, documented landmarks/margins

Current frozen canonical baseline:
- face/core canonical short edge: **192 px**

Resize:
- shrink: `INTER_AREA`
- enlarge only when unavoidable: `INTER_CUBIC`
- preserve aspect ratio
- source image remains unchanged

### Required metrics
At minimum:
- canonical192 Laplacian variance
- canonical192 Tenengrad
- gradient directionality / anisotropy
- local eye-region detail
- local mouth-region detail

### Composite blur logic
Do NOT reject on Laplacian alone.

Motion blur candidate requires:
- canonical Laplacian low
AND
- canonical Tenengrad low

Hard Reject should additionally require at least one:
- strong directional gradient concentration consistent with motion blur
- both eye and mouth local detail simultaneously degraded

The exact thresholds MUST be frozen in config before production use.

### Diagnostic-only
Retain native:
- global Laplacian
- native face Laplacian
as historical/context diagnostics only.

---

## 6.3 Exposure

Use face-internal ROI only.
Do not mix bright background or hair highlights into face exposure judgment.

### Required categories
- `UNDEREXPOSED`
- `OVEREXPOSED_CLIPPED`
- `WHITE_HAZE`
- `NORMAL`
- `NOT_EVALUABLE`

### Required metrics
Use a reduced stable set:
- highlight clipping ratio
- dynamic range (`P95 - P5`)
- local facial contrast

Optional supporting metrics:
- shadow ratio
- black-level lift
- eye/nose/mouth local contrast

### Underexposure Hard Reject
Only when multiple signs agree, e.g.:
- low face brightness / high shadow ratio
AND
- compressed dynamic range or very low local contrast

### Overexposure Hard Reject
Only when:
- highlight clipping ratio is high
AND
- clipped region is spatially substantial within skin/face ROI

### White Haze Hard Reject
White haze is not the same as clipping.

Candidate when:
- mean/median brightness elevated
- highlight clipping not necessarily high
- dynamic range low
- local eye/nose/mouth contrast low

Hard Reject only when at least two independent haze indicators agree.

All thresholds must be fixed in SSOT before production.

---

# 7. Diagnostic-only Signals

The following MUST remain Diagnostic in STEP3 V2 unless separately approved:

- half-eye / blink suspicion
- eye sharpness alone
- skin texture
- beauty filter suspicion
- plasticity ratio
- mild blur
- mild exposure concern
- detector disagreement
- native global blur
- native face blur
- expression state

They may affect `diagnostic_state`, but not `face_eligible` alone.

---

# 8. Pose Handling Boundary

STEP3 may calculate and preserve:
- yaw
- pitch
- roll

Only for:
- eye/occlusion context
- measurement applicability
- audit

STEP3 MUST NOT:
- enforce pose quotas
- reject ordinary profile/3Q poses because they are underrepresented
- optimize angle coverage

Pose diversity selection belongs to STEP4/STEP7.

---

# 9. PASS / BORDERLINE / REJECT Truth Table

## REJECT
At least one Tier A Hard Reject
OR
at least one confirmed Tier B composite Hard Reject.

`face_eligible=false`

## BORDERLINE
No Hard Reject
AND one or more meaningful Diagnostic concerns.

Examples:
- half-eye suspicion
- mild blur
- mild exposure concern
- uncertain occlusion
- skin/beauty concern

`face_eligible=true`

## PASS
No Hard Reject
AND no meaningful Diagnostic concern.

`face_eligible=true`

A/B/C selection state is NOT created in STEP3.

---

# 10. Required Output Schema

Every one of the 1,951 inputs must produce one row.

Minimum fields:

## Identity / lineage
- frame_id
- filename
- input_kind
- source_id
- video_id
- dataset_generation_id
- image_sha256

## Detection
- face_detected
- face_count
- detector_status
- detector_disagreement
- face_bbox
- face_short_edge_px
- frame_edge_contact

## Pose context
- yaw
- pitch
- roll

## Eye
- left_eye_state
- right_eye_state
- left_eye_openness
- right_eye_openness
- left_eye_presence
- right_eye_presence
- eye_applicability
- eye_occlusion_confidence / supporting flags

## Sharpness
- face_laplacian_canonical_192
- face_tenengrad_canonical_192
- gradient_directionality
- left_eye_local_detail
- right_eye_local_detail
- mouth_local_detail
- native_face_laplacian (diagnostic only)
- native_global_laplacian (diagnostic only)

## Exposure
- highlight_clip_ratio
- dynamic_range_p95_p5
- local_face_contrast
- exposure_state

## Decisions
- hard_reject_reasons
- diagnostic_flags
- face_eligible
- diagnostic_state
- analysis_status
- analysis_error

Empty measurement, zero measurement, and `NOT_EVALUABLE` MUST be distinguishable.

---

# 11. Formal vs Supplemental Reporting

Use one combined audit CSV.

Also publish distributions separately for:
- `formal_video`
- `supplemental_still`
- combined universe

No percentile-based Hard Gate may silently mix video and still populations.

Still count is too small for automatic kind-specific threshold learning.

---

# 12. Review Materialization

After a successful full STEP3 run:

- copy PASS to `output/reports/passed/`
- copy BORDERLINE to `output/reports/borderline/`

Preserve relative paths when practical.

These are temporary copies only.

Do not generate REJECT copies by default unless explicitly requested.

Review is used to find:
- False Accept
- False Reject
- new failure modes
- unexpected metric behavior

Human Review is NOT the primary threshold-fitting mechanism.

---

# 13. Threshold Governance

All production thresholds must:
- live in SSOT config
- have units
- have metric/version names
- have a Decision / calibration record
- not be silently inherited from old pixel scales

No threshold may be changed merely to reach a desired final image count.

Threshold changes require:
1. distribution analysis
2. deterministic simulation
3. regression examples
4. explicit approval

---

# 14. Required Regression Cases

At minimum preserve tests for:

- visible eyes falsely labeled `one_eye_occluded` (Sasha_v10-type)
- heavy hair/hand occlusion incorrectly passing (Sasha_v08-type)
- strong motion blur passing sharpness Gate (Sasha_v38 / Sasha_v63-type)
- dark-but-currently-passing source concentration (Sasha_v33-type)
- supplemental still omitted from STEP3 universe
- FULL_BODY with large measurable face
- profile pose where far-side eye is naturally reduced
- review folders accidentally rediscovered as inputs

Named subject examples are regression evidence only, never subject-specific production rules.

---

# 15. STEP3 V2 Completion Criteria

STEP3 V2 is complete only when:

- all 1,951 current inputs are represented exactly once
- supplemental 58 stills are included
- no report/review copy is re-ingested
- Tier A/Tier B formulas are explicit and tested
- eye state distinguishes closed / occluded / out-of-frame / not-evaluable
- blur uses canonical composite evidence, not native Laplacian alone
- exposure distinguishes under / clipping / haze
- video/still distributions are separately auditable
- regression cases pass
- no full-dataset lineage mismatch
- output is sufficient for STEP4 without performing STEP4 responsibilities

---

# 16. Explicitly Deferred

Not part of STEP3 V2 initial implementation unless later evidence requires it:

- full semantic face parsing
- FFT blur estimator
- multi-scale 128/192/256 production ensemble
- temporal consistency between adjacent frames
- learned beauty-filter classifier
- skin-color gamut model
- automatic per-input-kind threshold learning

These remain future options to avoid over-engineering.

---

# 17. Implementation Rule

This document is the Frozen Spec.

Codex implementation must NOT:
- invent new thresholds
- add new Hard Reject reasons
- promote Diagnostic signals to Hard Reject
- change STEP4+ responsibilities
- exclude supplemental stills
- add subject-specific exceptions
- reinterpret review folders as input

If an implementation detail is not fixed by this document and materially affects eligibility, STOP and report the unresolved specification instead of guessing.

