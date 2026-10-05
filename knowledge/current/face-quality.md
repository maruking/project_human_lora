---
topic: face-quality
last_updated: 2026-10-05
confidence: MEDIUM
status: ACTIVE
related_decisions:
  - DEC-0002
  - DEC-0003
  - DEC-0010
  - DEC-0016
  - DEC-0017
  - DEC-0018
  - DEC-0019
  - DEC-0020
related_failures:
  - FAIL-0002
related_cases:
  - CASE-0001
  - CASE-0002
  - CASE-0003
---

# Current Knowledge: Face Quality & Beauty Filter Rejection

## Active STEP3 — BEST v2.2 (DEC-0020)

[DEC-0020](../decisions/DEC-0020-balanced-critical-quality-best-v22.md) uses
base quality times equal geometric mean of eye/detail/exposure/reliability,
minus remaining geometry concern. Old eye credit loss/direct critical penalties
are removed. Both canonical measurements and a robust local median use existing
positive references, not a new physical blur threshold. Face size and useful
contrast saturate; lighting asymmetry is not visibility loss. Explicit measurement
coverage/statuses do not establish ROI truth. v05 ROI truth and visual haze remain
unresolved; no arbitrary threshold, source exception or Human scoring feature.

v2.2 starts Round1 independently of v1/v2/v2.1. Feedback reconciles only active
review duplicates after hash validation. Minimum/small-sample validation only;
production and Human calibration pending. See
[implementation](../../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md).

## Historical STEP3 — BEST v2.1 (DEC-0019)

[DEC-0019](../decisions/DEC-0019-general-eye-quality-best-v21.md) retains v2 common
positive scaling, positive-only kind bonus and minimal fatal predicates. Both eyes
are evaluated separately for opening, corroborated obstruction concern and missing
measurement. Weaker expected eye controls eye credit. Profile context uses existing
yaw boundary and measured ROI projection; it is not a pose preference. Soft blur
and exposure agreement use existing anchors only. No Human Reject or source name
is a scoring feature. Tenengrad/mouth defect scaling remains unresolved.

Normal BAT rescores stored measurements, then stops. best_rank_v2.1 review starts
at Round1 and ignores v1/v2 shown flags. Configured review45/minimum10 stills/cap4
rules remain sampling only. v1/v2 code, histories, copies and decisions are preserved.
[Implementation and 12-example comparison](../../docs/STEP3_BEST_RANKING_V21_IMPLEMENTATION.md).
Minimum tests pass; no production v2.1 ranking/extraction. Human observation can
still disagree with eye-state/ROI/exposure diagnostics; new arbitrary thresholds
were not invented to force those counterexamples down. STEP4+ remains unchanged.

## Historical policies and evidence

All Gate descriptions and numeric results below predate DEC-0017 and remain
historical context; they are not BEST eligibility/scoring controls.

> STEP0 implementation audit: the historical values below are not the current runtime defaults. Actual gates are recorded in `config/config.example.yaml` and [configuration.md](configuration.md), including global/face Laplacian 25/50 and plasticity maximum 45. Step2 itself computes metrics without an 80.0 rejection gate.


## 1. Current Policy
Face quality evaluation operates on a two-tier strategy: global technical measurement (Step 02) followed by localized face-crop anatomical sharpness and dual-bandpass plasticity gating (Step 03). The implementation rejects frames flagged by configured local heuristics; a flag alone does not prove physical blur or a beauty filter.

## 2. Recommended Approach
- **Technical Metrics (Step 02)**: Measure and record whole-image gradients, brightness and resolution; no standalone quality gate (DEC-0010). See [technical-image-metrics.md](technical-image-metrics.md).
- **Face Quality Gate (Step 03)**: Use `face_quality_gate.py` with MediaPipe face detection to evaluate local Tenengrad gradient, landmark occlusion, and the `plasticity_ratio` ($R = \frac{\text{EdgeSharpness}}{\text{SkinTexture}}$).

## 3. Historical Intended Rules (not current runtime defaults; see configuration.md)
- `min_face_size`: 120 pixels.
- `min_face_sharpness`: 18.0 (Tenengrad variance on face bounding box).
- `max_occlusion_ratio`: 0.35 (max 35% landmark occlusion).
- `max_plasticity_ratio`: 70.0 (anti-beauty-filter limit).
- `min_skin_texture_score`: 15.0 (cheek/forehead high-frequency micro-texture).

## 4. Soft Rules (Guidelines for Human Review)
- In Step 08 visual inspection, check for motion blur streaks on hair or jewelry even if the eyes passed sharpness thresholds.
- Check for sunglass occlusions or heavy hand occlusions that face detectors might occasionally miss.

## 5. Historical Baseline — Validated Conditions (prior generation)
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

## STEP2 interpretation boundary

Global Laplacian and Tenengrad are not perceptual face-quality truth. Background, clothes, hair, compression edges and low-resolution pixelation can inflate them. CASE-0003 records a user-reported small soft face with high edge values; it was not remeasured here. PASS means measurement success. No diagnostic metric becomes a hard quality rule without an ACCEPTED Decision and supporting experiment. STEP3 implementation remains unchanged.

## Current STEP2 generation contract
Global technical metrics only; no face-level decision, identity or beauty-filter
inference. STEP1 Revision 2's 71 videos / 2,001 PNG receive exact current-generation
coverage. Stale CSV rows are prohibited. Global plus per-video relative ranks are
stored for diagnostics, without selection, deletion or hard gates. Preflight compares
formal STEP1 counts and content inventory before scoring; failed runs are isolated
in audit. See DEC-0010, EXP-20261002-003 and docs/STEP2_RESULT.md. Previous 3,550
technical rows and 3,607 face-baseline frames are Historical Baseline; current STEP2
success does not revalidate historical face gates. STEP3 gate values remain unchanged.

## Human evaluation of STEP2 reports
STEP2 stores full-frame technical metrics. Human evaluation should use the whole
dataset distribution and video-level reports, not only highest/lowest examples.
Compare video medians and the concentration of saved global-rank bottom percentiles
before inspecting individual frames. scripts/build_step2_reports.py regenerates
these summaries from the successful measurement CSV without decoding images or
changing metrics/ranks. Whole-frame technical metrics are not face quality, identity
quality or LoRA suitability. STEP3 must measure facial regions separately; no Gate,
threshold, deletion or candidate selection follows from this report revision.
See DEC-0010 Report Layer and EXP-20261002-004.


## STEP3 Revision1 current-generation audit
[Result](../../docs/STEP3_RESULT.md): 2001 full rows/36 retained STEP2 fields; errors0;
face detected1924, matched FaceMesh1719; eligible62, rejected1939. Same inputs produce
identical metrics/reasons/reports; original Gate block matches all2001 decisions. This
validates execution/lineage, not labeled quality accuracy. Gate values/formulas unchanged.

Actual skin kernel is cheek Laplacian variance divided by mean brightness; plasticity
is anatomical eye sharpness / max(skin texture,0.005). Local config max45, skin
min.050/.035 (close/upper); FULL_BODY skips beauty rejection. Historical bandpass,
forehead and 70/15 descriptions above remain historical, not current formula defaults.
Visibility/eye-presence/hair/filter causal interpretations are heuristic and not revalidated.

No FaceMesh -> anatomical blanks + explicit missing state; invalid eye presence ->
legacy eye-sharpness disablement0 explicitly flagged. Geometry eye/mouth ratios and
provisional diagnostic classes never become new rejection Gates. shot_type is provisional
face scale, not STEP4 composition. --limit writes partial artifacts; errors return nonzero
without replacing good reports. CSV-only human reports include per-video concentration,
full distributions, overlapping reasons and exclusive primary categories. 56/71 videos
have zero eligible; review/tuning requires human evidence in Revision2, not this run.
See [Gate audit](../../docs/STEP3_GATE_AUDIT.md),
[EXP-20261002-005](../../experiments/EXP-20261002-005-step3-full-audit.md).


## STEP3 Revision2 calibration stage — historical180-frame package
[Calibration result](../../docs/STEP3_CALIBRATION_RESULT.md):180 unique frames across71
videos with scale/video/boundary coverage, offline labels and JSON/CSV export. All2001
source rows/pixels/Gates unchanged. Face_blurry executed eye808/Laplacian883; eye991
disabled versus728 measured. Static reason-removal counterfactuals are NOT applied and
are not threshold-effect predictions. Current source and pre-SSOT kernels match; old
70/15/18 prose does not prove an interchangeable metric scale or approved current cutoff.
[Formula audit](../../docs/STEP3_GATE_CALIBRATION_AUDIT.md) records distinctions/unknowns.
Gate Calibration Status: AWAITING HUMAN LABELS. No tuning or STEP4 readiness; no
precision/recall or new annotated Case. See EXP-20261002-006. Browser file:// visual
verification was blocked; static/export/crop tests are not a real-browser UI PASS.


## Historical45-frame STEP3 REJECT boundary calibration

[Boundary result](../../docs/STEP3_BOUNDARY_CALIBRATION_RESULT.md) supersedes the
180-frame review purpose without changing its historical evidence. Active review
contains45 unique REJECT frames/45 videos, Eligible0, with81 independent Gate
acceptability questions. Only requested near-threshold windows are sampled;
measured eye boundaries exclude disabled/missing proxies and FULL_BODY.
Cards distinguish diagnostic FAIL from the actually executed rejection branch.
Skin/Plasticity rounded-source individual attribution remains explicitly uncertain.
JSON schema2 and long-format CSV retain generation/frame identity and per-Gate
human_accept; ACCEPT is boundary tolerance, not final image adoption.
Production CSV/config/Gates/source pixels remain unchanged; no human labels applied.
114 tests/static exports,45 copy/crop checks and deterministic replay PASS;
browser visual QA still unavailable. Gate accuracy/tuning/STEP4 await human evidence.
See [EXP-20261002-007](../../experiments/EXP-20261002-007-step3-reject-boundary-review.md).


## Active isolated single-Gate boundary correction

[Scoped fix](../../docs/STEP3_SINGLE_GATE_BOUNDARY_FIX.md):25 unique REJECT frames;
exactly one target FAIL and all other applicable hard gates PASS. No multi-failure
samples or quota filling. Both blur predicates are checked despite the production
if/elif reason suppression. Beauty causes are separated; rounded ambiguous attribution
is excluded. Eye Presence/Skin Texture/Face Size have0 isolated boundary samples.
Thresholds/formulas/production CSV/source pixels/STEP4+ unchanged.117 tests plus
all actual sample invariants verified. Earlier45-frame set is superseded/debug;
no human-label accuracy claim or tuning follows from this correction.

## Revision A diagnostic / selection sidecar (2026-10-02)

Official STEP3 supplemental preflight now follows the formal/still split recorded
by STEP2, reusing its validated input helper. Only the explicitly recorded still
subtree is separated; its inventory/hashes must remain identical to STEP2. Official
Gate output remains formal-video-only; the existing Revision A path handles all
formal plus supplemental diagnostics. Gates/thresholds are unchanged. Minimum tests
PASS, production rerun pending ★maru. See [scoped fix result](../../docs/STEP3_SUPPLEMENTAL_PREFLIGHT_FIX.md).

Execution/scope correction: maru executes BAT/Python. Current code includes ALL formal STEP1 images + supplemental images; the previous138-row diagnostic run is partial historical evidence only. Corrected full-input execution is pending. See [Maru instructions](../../docs/STEP3_REVISION_A_MARU_RUN.md). No all-input A/B/C counts are validated yet.

[DEC-0012](../decisions/DEC-0012-separate-selection-groups.md) keeps dataset-selection A/B/C separate from official face_eligible. Human Reject C takes priority. B/CONFIRMED is a usable reserve; B/UNDECIDED is provisional and requires human confirmation before use. Diagnostic NORMAL/OPEN never silently promotes to A. The new eye/exposure/detail bins are unvalidated, not Gates, and are applied to all scales including FULL_BODY. [EXP-20261002-008](../../experiments/EXP-20261002-008-step3-revision-a-diagnostics.md) verifies138-row preservation and repeatability, not LoRA suitability (confidence MEDIUM, accuracy INCONCLUSIVE). Supplementals have their own inventory/generation, not formal STEP1 identities.


## Historical initial canonical192 architecture — 2026-10-03 (review policy superseded by DEC-0015)

[DEC-0014](../decisions/DEC-0014-canonical192-face-gate.md) supersedes native/eye-first/beauty Hard Gates described historically above. Official sharpness metric is face-core Laplacian at aspect-preserved canonical short edge192; approved threshold comes from STEP3 config SSOT. Native global/face, eye, skin, beauty and plasticity retain their formulas/columns as diagnostics. Existing face/FaceMesh/visibility, size/resolution, exposure/backlight and hair/one-eye predicates are unchanged. A separate diagnostic BORDERLINE (EYE_DETAIL plus SKIN_PROCESSING) keeps face_eligible true. No A/B/C. Implementation/synthetic validation complete; full production execution pending maru. Existing official reports still describe the prior architecture until rerun. See [implementation result](../../docs/STEP3_CANONICAL192_IMPLEMENTATION.md).

## Active STEP3 review gaps revision — 2026-10-03

[DEC-0015](../decisions/DEC-0015-eye-applicability-review-outputs.md) retains canonical192 Gate/SSOT threshold and supersedes the preceding review/applicability policy. Eye presence applies at measured face scale >= existing configured upper-body minimum regardless of shot; small/missing measurements remain explicit N/A. Shared Revision A half-eye/exposure diagnostics add review BORDERLINE only, alongside the existing two-family concern. Full successful runs always refresh disposable reports/passed and reports/borderline copies; failed/partial runs keep the prior successful copies. Copies/aliases/staging are excluded from pipeline source inventories and generation identity. A/B/C unchanged. Synthetic tests complete; production rerun and Chappy/Human Review pending. See [result](../../docs/STEP3_REVIEW_GAPS_IMPLEMENTATION.md).

Supplemental user-authorized operation: [Reject review copy result](../../docs/STEP3_REJECT_REVIEW_COPY_RESULT.md) records current PASS51/BORDERLINE88/REJECT1754. Existing results were copied via separate03_copy_reject_review.bat; no Gate rerun or A/B/C changes. Configured reports/reject is also a disposable private review output, excluded from inputs/lineage and Git. Normal STEP3 still automatically refreshes passed/borderline only.

Complete listing correction: STEP2 includes58 declared stills that normal STEP3 currently does not evaluate. [All-images list result](../../docs/STEP3_ALL_IMAGES_LIST_RESULT.md) creates step3_all_images_report.csv with1951 rows, including58 explicit NOT_EVALUATED stills and image links. Missing evaluation is not PASS/REJECT/A/B/C. Formal STEP3 results and review copies are unchanged. Scope clarification on same-Gate supplemental evaluation is pending; no production inference performed.
