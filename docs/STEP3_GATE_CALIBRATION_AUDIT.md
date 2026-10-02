# STEP3 Gate Calibration Audit — Historical Formula/Scale Mismatch

2026-10-02. Status: derived review; no Gate change. Refer to
[Revision1 Gate audit](STEP3_GATE_AUDIT.md) and [calibration result](STEP3_CALIBRATION_RESULT.md).
Sources: accepted DEC-0002/0003, Current historical rules, HIST-002/003,
EXP-20261001-002 and current local scripts/face_quality_gate.py/config. No historical
source revision proving the older70/15 implementation or the exact transition date was
established. The local STEP0 pre-SSOT snapshot was found and inspected; it already uses
50/1.6/45/.050/.035 and the same inspected kernel ASTs as current source. Historical prose/code examples are evidence of descriptions,
not proof of an executed formula. Their original records are retained.

| Historical item | Actual current definition | Classification | Consequence / certainty |
|---|---|---|---|
| min_face_size120px | min(clipped bbox width,height), per provisional face scale140/110/80; source short edge720 for FULL_BODY | unknown; historical documentation stale | Units are pixels, but historical ROI/dimension policy and change rationale are not proven. Cannot assert an approved same-metric threshold change. |
| face_sharpness18, face-bbox Tenengrad | Face-core80% crop Laplacian variance Gate50, mean Sobel squared energy as diagnostic; eyes use P90 sqrt(gx²+gy²)/(gray std+1e-4) Gate1.6 | changed metric definition; changed normalization scale | Face-core Laplacian and normalized anatomical eye metric are different operators/ROI/units from described bbox Tenengrad18. No numeric conversion inferred. |
| skin_texture15, std(Laplacian skin ROI), cheek/forehead or bandpass prose | mean of cheek Laplacian **variance / max(mean brightness,10)**; radius=max(int(min bbox dim*.07),6) | changed metric definition; changed normalization scale; historical documentation stale | std versus variance/brightness and patch domains differ. .050/.035 cannot be compared directly with15. |
| plasticity70, face_sharpness/max(skin,0.1) | anatomical eye sharpness/max(normalized cheek texture,0.005), max45; CLOSE_UP/UPPER_BODY only | changed metric definition; changed normalization scale | Numerator, denominator and floor changed; ratio is not the same metric merely with a lower cutoff. Raw-to-rounded CSV precision also differs. |
| global-only Laplacian selection | STEP2 measurement only; STEP3 coarse global Gate25 plus other face Gates | historical documentation stale / responsibility changed | DEC-0010 supersedes old STEP2 filtering intent. FAIL-0002 prohibits global-only selection; it was not retried. |
| occlusion ratio0.35 | visibility score penalties + required FaceMesh + separate gradient/presence heuristics | changed metric definition; unknown historical mapping | No calibrated mapping between fraction and heuristic score. Missing Mesh/disabled eye can affect several reasons simultaneously. |

No fully evidenced pair qualifies solely as **same metric / changed threshold**.
Descriptive similarity and dimensionless ratios do not establish formula equivalence.
The chronology/reason for changes remains **unknown** without historical runnable
source and labeled experiments. No historical authority/decision was rewritten to
claim approval for current numeric values.

## Current precision and control flow

Current face-blur Gate compares stored rounded eye/face Laplacian strings in an
if/elif chain. Concurrent low predicates do not mean two executed branches. For
CLOSE_UP/UPPER_BODY invalid presence disables anatomical eye sharpness before Gate
comparison, so many blur reasons do not identify measured optical blur.

Skin/plasticity flags are computed before CSV formatting: texture3 decimals and
plasticity1 decimal. Values at .050/.035 or45 can conceal which side of an unrounded
threshold the kernel occupied. Threshold/boundary reports explicitly analyze stored
values; exact beauty flag attribution at the boundary remains unresolved without
unrounded inference trace. Do not reverse-engineer or replace the authoritative flag.

Visibility distribution excludes205 missing-mesh proxy zeros. Eye/plasticity
quantiles exclude991 disabled eye metrics. This is measured-only distribution analysis,
not permission to ignore those Gates in production.

## Potential issues — NOT ACCEPTED / NOT APPLIED

Face Laplacian50 lies nearP93 in close/upper distributions. Existing eye presence
and sharpness disablement couple occlusion/blur reasons. FULL_BODY follows a different
Gate path. Low-light/compression/exposure and normalization may affect texture without
an actual beauty filter. These are review hypotheses. No threshold recommendation
or new accepted setting is justified until human labels identify specific errors.

Counterfactual removal of one stored reason is not removal/recalculation of an upstream
heuristic: removing one_eye_occluded leaves disabled sharpness and face_blurry intact.
Eligible count gains alone are not quality or calibration objectives.

Relevant Decisions/Failures/Cases checked; no new ADR, Failure or Case created.
Confidence: HIGH for inspected formula/control-flow differences; UNKNOWN for old
runtime chronology; UNVALIDATED for current precision/recall and visual error causes.


## Local runnable-snapshot evidence

output/reports/step0_audit/pre_ssot/face_quality_gate.py already contains current
face Laplacian50, normalized eye1.6, plasticity45, texture.050/.035 and pixel
140/110/80 defaults. Its sharpness/anatomical/normalized-patch/cheek/visibility/core
kernel ASTs equal current source. The numeric/formula discrepancy therefore was
not introduced by this calibration or STEP0 SSOT migration. Historical70/15/18
records remain descriptive evidence whose matching executable source was not established.
See output/reports/step3_calibration_audit/historical_source_comparison.json.
