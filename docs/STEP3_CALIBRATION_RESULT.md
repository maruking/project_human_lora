# STEP 3 Revision 2 Calibration Result

> Historical180-frame review: superseded for active calibration by
> [REJECT Boundary Review](STEP3_BOUNDARY_CALIBRATION_RESULT.md).
> Prior validation evidence and artifacts remain preserved.

Date: 2026-10-02 (Asia/Tokyo). Local working tree is authoritative. No commit/push.

## Status

**CALIBRATION_READY** — package complete. **Gate Calibration Status: AWAITING HUMAN LABELS.**
This validates derived analysis, reproducible sampling and export logic, not Gate accuracy.
No human labels, precision/recall or tuning decisions were fabricated.

## Authoritative Data Changed

**NO.** All 2001 authoritative rows, STEP1/2/3 metadata/reports and original
images are retained byte-for-byte; source image mtimes retained. Source CSV SHA256:
`2589176c4a2eb22d098a1f97500654cde0e0ce6dfda0873cdeac25893f6b0051`. Generation: `fc2a37abc81e44e456891ac7d268c2dc622255d120c944ac377dbefd491833c2`.
Calibration is a derived subset and never replaces the complete audit.

## Gate Thresholds Changed

**NO.** Production code, config and BATs unchanged. No inference/recalculation of
production face measurements, frame deletion, restoration, selection, quota or STEP4 run.
Current SSOT plus recorded production CLI overrides supply analysis thresholds.
Verification: [STEP3_CALIBRATION_VERIFICATION.json](STEP3_CALIBRATION_VERIFICATION.json).

## Calibration Set

- Frames: 180 unique; videos: 71.
- CLOSE_UP: 52; UPPER_BODY: 53; FULL_BODY: 52.
- Face unclassified/no detection: 23 (no fabricated shot type/crop).
- Per-video cap: 5; actual maximum: 4.
- Eligible control: 25; top10% technical/rejected: 18.
- Rare multiple-face Gate: all3 frames included.
- Package: `fe12ba72980e02d4`.

Deterministic reservations cover each available scale/metric/boundary bin, then
video/scale-balanced category quotas, disabled/measured eye mechanisms, extreme low
Laplacian/high plasticity, rare multiple faces and video-diversity fill. No random seeds
or directory-order inference. Gate memberships overlap: face_blurry114, one_eye_occluded48,
beauty41, low_visibility25, exposure22, low-resolution/small-face23. Exclusive sampling
categories identify the reservation that added the unique frame; they do not replace
reason memberships. Thus memberships intentionally exceed category quota requests.

Stored-value bands: [0.7T,0.9T), [0.9T,1.0T), [1.0T,1.1T), [1.1T,1.3T).
59/60 boundary strata covered. CLOSE_UP visibility [70,77) has **no data**; no sample
or score was invented. Coverage CSV records availability and actual selected counts.
Rounded CSV boundaries are approximate for pre-rounding beauty decisions.
This stratified set is not an unbiased population sample; unweighted human error rates
must not be presented as precision/recall for all2001 frames without a sampling/weighting protocol.

## Gate Contributions

triggered_ratio is fraction of the entire dataset (0–1). Sole rejection means exactly
one stored reason; co-rejection means at least one other reason. Scale counts plus
unclassified count sum to triggered_count; reason totals overlap.

| gate_name | triggered_count | sole_rejection_count | co_rejection_count | videos_affected | close_up_count | upper_body_count | full_body_count | unclassified_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_blurry | 953 | 1 | 952 | 41 | 152 | 357 | 403 | 41 |
| face_blurry | 1691 | 249 | 1442 | 71 | 317 | 760 | 614 | 0 |
| one_eye_occluded | 595 | 0 | 595 | 59 | 187 | 408 | 0 | 0 |
| beauty_filter_detected | 459 | 8 | 451 | 54 | 191 | 268 | 0 | 0 |
| low_visibility | 241 | 21 | 220 | 40 | 10 | 18 | 213 | 0 |
| low_resolution_source | 281 | 90 | 191 | 18 | 0 | 0 | 281 | 0 |
| face_underexposed | 218 | 3 | 215 | 23 | 13 | 36 | 169 | 0 |
| face_backlit_underexposed | 24 | 0 | 24 | 5 | 0 | 9 | 15 | 0 |
| face_too_small | 26 | 0 | 26 | 4 | 0 | 0 | 26 | 0 |
| multiple_faces | 3 | 0 | 3 | 2 | 0 | 1 | 2 | 0 |
| no_face | 77 | 36 | 41 | 20 | 0 | 0 | 0 | 77 |
| hair_covered_face | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| analysis_error | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Face Blur Decomposition

Actual production order is:

```python
if shot != "FULL_BODY" and eye_sharpness < configured_min_eye:
    face_blurry
elif face_laplacian < configured_min_face_laplacian:
    face_blurry
```

Executed eye branch808; executed Laplacian branch883; total face_blurry1691.
Both predicates fail764: these execute the **eye branch only**. The independently
low face-Laplacian predicate applies to1647, not1647 executed Laplacian rejections.
Eye-only44; Laplacian-only883; both764 are disjoint predicate combinations. No
causal visual blur label is inferred. The derived per-frame CSV retains the selected
branch, concurrent predicate booleans and eye metric state. Its results are checked
against every stored face_blurry reason before artifacts are produced.

## Eye Metric Analysis

| State | Frames |
|---|---:|
| No face / N/A | 77 |
| FaceMesh unavailable | 205 |
| Eye presence invalid / sharpness disabled | 991 |
| Eye sharpness measured | 728 |
| Measured below1.6 | 223 |
| Measured at/above1.6 | 505 |

Measured-low223 includes10 FULL_BODY samples where eye sharpness is not a Gate.
The executed eye branch808 comprises585 disabled-eye,10 mesh-unavailable and213
measured-low samples. Among991 disabled-eye frames,406 are FULL_BODY and do not
trigger the eye-sharpness Gate. one_eye_occluded595 includes585 invalid-presence
close/upper frames plus10 missing-mesh upper frames. Missing FaceMesh and disabled
sharpness are not described as measured optical blur.

## Threshold Position

Empirical strict-below CDF: 100 × count(stored valid metric < threshold)/valid_count.
Ties are separately counted. Quantiles use linear interpolation; these are different
operations. FULL_BODY eye/skin/plasticity thresholds are inactive. Visibility excludes
missing-mesh proxy zeros; skin requires mesh; eye/plasticity exclude invalid/disabled
eye metrics. Their excluded counts are explicit; these conditional distributions do
not represent whole-dataset rejection rates.

| shot_type | metric | count | p01 | p10 | p50 | p90 | p99 | current_threshold | threshold_active | threshold_percentile_position |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLOSE_UP | face_laplacian_score | 325 | 3.1654 | 5.1142 | 9.739 | 41.3068 | 118.11184 | 50.0 | True | 92.923077 |
| CLOSE_UP | eye_sharpness | 138 | 0.77729 | 1.0213 | 1.3285 | 2.2012 | 2.89153 | 1.6 | True | 66.666667 |
| CLOSE_UP | skin_texture_score | 325 | 0.0072 | 0.017 | 0.045 | 0.1416 | 0.83028 | 0.05 | True | 57.846154 |
| CLOSE_UP | plasticity_ratio | 138 | 2.396 | 10.51 | 27.15 | 63.2 | 105.945 | 45.0 | True | 78.26087 |
| CLOSE_UP | face_brightness_mean | 325 | 82.12 | 103.94 | 132.5 | 151.26 | 161.184 | 95.0 | True | 4.0 |
| CLOSE_UP | face_visibility_score | 325 | 58.12 | 80.0 | 100.0 | 100.0 | 100.0 | 70.0 | True | 3.076923 |
| UPPER_BODY | face_laplacian_score | 792 | 3.78642 | 6.344 | 13.5185 | 43.81 | 145.41177 | 50.0 | True | 92.29798 |
| UPPER_BODY | eye_sharpness | 384 | 1.08166 | 1.293 | 1.969 | 3.0157 | 3.95016 | 1.6 | True | 31.510417 |
| UPPER_BODY | skin_texture_score | 782 | 0.013 | 0.023 | 0.051 | 0.2429 | 1.27565 | 0.035 | True | 26.598465 |
| UPPER_BODY | plasticity_ratio | 384 | 1.583 | 6.96 | 34.65 | 74.77 | 131.218 | 45.0 | True | 67.447917 |
| UPPER_BODY | face_brightness_mean | 792 | 86.382 | 100.83 | 124.65 | 143.1 | 161.707 | 95.0 | True | 4.545455 |
| UPPER_BODY | face_visibility_score | 782 | 72.05 | 100.0 | 100.0 | 100.0 | 100.0 | 70.0 | True | 1.023018 |
| FULL_BODY | face_laplacian_score | 807 | 5.07102 | 7.4262 | 22.597 | 92.1138 | 207.99868 | 50.0 | True | 76.084263 |
| FULL_BODY | eye_sharpness | 206 | 1.4135 | 1.6565 | 2.8905 | 4.204 | 5.26485 |  | False |  |
| FULL_BODY | skin_texture_score | 612 | 0.02011 | 0.032 | 0.095 | 0.5078 | 2.28101 |  | False |  |
| FULL_BODY | plasticity_ratio | 206 | 2.305 | 6.0 | 29.25 | 67.8 | 110.505 |  | False |  |
| FULL_BODY | face_brightness_mean | 807 | 65.344 | 79.2 | 115.2 | 146.8 | 167.164 | 95.0 | True | 20.94176 |
| FULL_BODY | face_visibility_score | 612 | 55.55 | 85.0 | 100.0 | 100.0 | 100.0 | 70.0 | True | 2.941176 |

Potential issues for human review, not accepted tuning recommendations:
- Face Laplacian50 is nearP93 for close/upper andP76 for full-body; inspect just-below/above cases.
- Eye sharpness can be zero because another heuristic disabled it, independently of actual blur.
- Close-up valid-eye1.6 is nearP67; upper-body nearP32. Face-scale differences matter.
- Plasticity distributions depend on the validity/normalization of their eye numerator.
- Measured visibility distributions look permissive nearP3, but205 mesh-unavailable
  rows fail visibility separately and were correctly excluded from measured-only quantiles.
- Beauty flags are produced before CSV rounding; .050/.035 texture and45 plasticity
  boundary agreement cannot be reconstructed exactly from rounded scalars alone.

## Reason Combinations

Full CSV contains every combination, including eligible controls. Sorted TOP30:

| Reason combination | Frames | % of all | Videos |
|---|---:|---:|---:|
| face_blurry;global_blurry | 297 | 14.84 | 34 |
| face_blurry | 249 | 12.44 | 39 |
| face_blurry;one_eye_occluded | 199 | 9.95 | 36 |
| beauty_filter_detected;face_blurry;global_blurry;one_eye_occluded | 145 | 7.25 | 25 |
| face_blurry;global_blurry;one_eye_occluded | 117 | 5.85 | 29 |
| beauty_filter_detected;face_blurry;global_blurry | 112 | 5.60 | 23 |
| low_resolution_source | 90 | 4.50 | 11 |
| beauty_filter_detected;face_blurry;one_eye_occluded | 88 | 4.40 | 21 |
| beauty_filter_detected;face_blurry | 78 | 3.90 | 25 |
| face_blurry;low_resolution_source | 67 | 3.35 | 11 |
| eligible | 62 | 3.10 | 15 |
| face_blurry;global_blurry;low_visibility | 59 | 2.95 | 13 |
| global_blurry;no_face | 41 | 2.05 | 13 |
| face_blurry;face_underexposed;global_blurry;low_visibility | 37 | 1.85 | 2 |
| no_face | 36 | 1.80 | 9 |
| face_blurry;face_underexposed;global_blurry | 35 | 1.75 | 10 |
| face_blurry;face_underexposed | 24 | 1.20 | 7 |
| face_blurry;low_visibility | 24 | 1.20 | 4 |
| face_blurry;face_underexposed;global_blurry;low_resolution_source | 21 | 1.05 | 2 |
| low_visibility | 21 | 1.05 | 3 |
| face_blurry;face_underexposed;low_resolution_source;low_visibility | 20 | 1.00 | 3 |
| face_blurry;global_blurry;low_resolution_source | 16 | 0.80 | 4 |
| face_blurry;face_underexposed;global_blurry;one_eye_occluded | 13 | 0.65 | 4 |
| low_resolution_source;low_visibility | 13 | 0.65 | 5 |
| face_too_small;face_underexposed;low_resolution_source;low_visibility | 12 | 0.60 | 3 |
| face_backlit_underexposed;face_blurry;global_blurry;low_resolution_source | 11 | 0.55 | 2 |
| face_blurry;face_too_small;face_underexposed;low_resolution_source;low_visibility | 9 | 0.45 | 3 |
| beauty_filter_detected | 8 | 0.40 | 5 |
| face_backlit_underexposed;face_blurry;global_blurry | 8 | 0.40 | 3 |
| beauty_filter_detected;face_blurry;global_blurry;low_visibility;one_eye_occluded | 7 | 0.35 | 3 |

## Counterfactual Analysis

Remove one stored reason only, leave all other stored reasons/metrics unchanged.
This is **DIAGNOSTIC ONLY / NOT APPLIED**, not threshold tuning or a rerun of the
pipeline. In particular removing one_eye_occluded does not restore eye measurements;
its dependent face_blurry reason remains. Counts are not precision/recall or evidence
that newly included frames would be usable.

| ignored_reason | counterfactual_eligible_count | additional_eligible | status |
| --- | --- | --- | --- |
| global_blurry | 63 | 1 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| face_blurry | 311 | 249 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| one_eye_occluded | 62 | 0 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| beauty_filter_detected | 70 | 8 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| low_visibility | 83 | 21 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| low_resolution_source | 152 | 90 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| face_underexposed | 65 | 3 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| face_backlit_underexposed | 62 | 0 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| face_too_small | 62 | 0 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| multiple_faces | 62 | 0 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| no_face | 98 | 36 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| hair_covered_face | 62 | 0 | DIAGNOSTIC_ONLY_NOT_APPLIED |
| analysis_error | 62 | 0 | DIAGNOSTIC_ONLY_NOT_APPLIED |

## Current Eligible Concentration

62 eligible frames appear in15 videos;56 videos have zero eligible. Top3 videos
account for40/62 (64.52%). The71-row concentration CSV records video_id, eligible_count,
eligible_ratio and share_of_all_eligible, including zero-eligible videos. This is a
Gate-bias diagnostic, not candidate ranking or identity/diversity suitability.

## Review Artifacts

- [Offline HTML](STEP3_CALIBRATION_REVIEW.html): full-frame copy and plain face crop side by side,
  current Gate/reasons, global/face metrics, disabled/missing eye state, six human selectors and notes.
- output/reports/step3_calibration_review.csv:180 unique frame identities/context and empty human labels.
- output/reports/step3_calibration_assets/<package_id>/:180 original full-frame copies,157 plain face crops.
- output/reports/step3_gate_contribution.csv
- output/reports/step3_gate_threshold_audit.csv
- output/reports/step3_reason_combinations.csv
- output/reports/step3_counterfactual_analysis.csv
- output/reports/step3_eligible_concentration.csv
- output/reports/step3_blur_decomposition.csv
- output/reports/step3_calibration_boundary_coverage.csv
- output/reports/step3_calibration_summary.json
- [Historical/formula audit](STEP3_GATE_CALIBRATION_AUDIT.md)
- output/reports/step3_calibration_audit/:tests, export fixture, replay and protected-data verification.

Open HTML directly in a local browser. No server, external dependencies or network
requests. Labels persist in that browser's localStorage, isolated by package ID;
export JSON/CSV at the end. Exports include every sampled row, including unlabeled
rows. Visibility/Exposure use OK/BAD/UNSURE; other selectors YES/NO/UNSURE; empty
means unreviewed. Notes support Unicode/quotes/newlines. No automatic label import,
Gate update or authoritative CSV overwrite. Exported JSON status is
HUMAN_LABELS_NOT_APPLIED; preserve the original export for the later review stage.

## Tests

Previous94 retained; new15 Python tests; total **109 PASS**.
Additional Node fake-DOM/export harness and Python CSV↔JSON schema/Unicode/newline
roundtrip PASS. Synthetic test labels are explicitly fixture-only and never written
to the actual manifest. All180 human-label fields remain blank.
Tests cover deterministic stratification, no duplicates, per-video caps, available
boundary coverage, complete manifest, immutable pixels, deterministic crops, offline
HTML resources/CSP, immutable counterfactuals, exact if/elif and concurrent predicates,
disabled versus unavailable eyes, measured-only thresholds, unchanged settings and
safe embedded strings. Full artifact/crop byte replay and raw SHA/mtime preservation
are checked on the actual generation.

**Browser verification limitation:** Codex browser security rejected file:// navigation.
No alternate surface/server workaround was used. Real-browser layout, file-origin
localStorage and download dialogs could not be visually verified. Static asset paths,
script syntax, fake-DOM control behavior, export schemas and crop pixels were verified;
human opening/labeling is still required. This is not a claimed browser UI PASS.

## Human Review Required

**YES.** Gate Calibration Status: **AWAITING HUMAN LABELS**. Review whether the face
is usable, actually blurred, occluded, filtered, poorly visible or exposed. Use UNSURE
when the evidence is insufficient. Profile/3Q, hair, shadows and normal visible eyes
are hypotheses for human notes, not machine labels. No Cases or precision/recall claims
are created before annotated evidence. Relevant existing Decisions/Failures/Cases were
checked; no new Decision/Failure/Case is warranted by derived counts alone.

## Ready for Gate Tuning

**NO.** Await human labels and error analysis. No proposed numeric threshold is applied.

## Ready for STEP4

**NO.** Stop at the completed calibration package as instructed.

## Rules and Preservation

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, both rules files; relevant
Current configuration/frame/face Knowledge; DEC-0002/0003/0006/0011; FAIL-0002;
CASE-0002/0003; STEP3_RESULT/SUMMARY/GATE_AUDIT; HIST-013/EXP-005. Knowledge maintenance
uses .agents/skills/knowledge-maintenance/SKILL.md. Local working tree remains authoritative.
Data lineage preserved: YES. Full-row preservation: YES (source2001 unchanged;
review180 explicitly derived). Historical evidence preserved: YES. Config SSOT: YES.
No rule conflict/tuning; later STEP enforcement and universal master audit remain deferred.

Changed implementation: scripts/build_step3_calibration.py,
scripts/templates/step3_calibration.html, tests/test_step3_calibration.py,
tests/check_step3_calibration_exports.cjs. Added derived reports/HTML/assets and
STEP3_CALIBRATION_RESULT/GATE_CALIBRATION_AUDIT. README/Current Knowledge, existing DEC-0002/0003 supplementary experiment links and
new experiment/history records updated; production code/config/BAT/Revision1 docs unchanged.


## Review UI threshold clarification (2026-10-02)

Measurement cards now show recorded values, actual run thresholds, applicability
and diagnostic comparison in Japanese. Rejection explanations follow the recorded
Gate reason and the executed eye/face if/elif branch. Invalid eye measurements,
FaceMesh absence, FULL_BODY exclusions and rounded beauty metrics are explicit.
For Sasha_v22_004: eye 1.589 < 1.6 is the executed face_blurry branch;
face Laplacian 15.296 < 50 is also low. No threshold/production change.
Human questions and option captions are Japanese; stored values and keys unchanged.

Changed: scripts/common/step3_review_presentation.py,
scripts/build_step3_calibration.py, scripts/templates/step3_calibration.html,
docs/STEP3_CALIBRATION_REVIEW.html, tests/check_step3_calibration_exports.cjs.
Only the existing HTML was refreshed; records, package ID, assets, calibration CSV
and existing browser-label cache key were preserved. Current labels were not read
or written. Protected file hashes match; all 2,001 rows checked for presentation
applicability. Existing 109 tests pass; fake DOM checks threshold explanations,
synthetic saved-label reload and JSON/CSV compatibility. Browser visual QA remains
unperformed because file access is blocked by the browser policy.
Audit: output/reports/step3_review_ui_audit/verification.json.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md,
.agents/rules/lora_pipeline_rules.md, .agents/rules/data_lineage_rules.md.
Data lineage preserved: YES. Full-row preservation: YES (2,001 source;180 review).
Historical evidence preserved: YES. Config SSOT preserved: YES.
README, Current Knowledge, Decisions, Failures, Cases, Experiments and History
reviewed: Documentation checked; no update required for the presentation-only change.
No rule conflicts, new Gate decision or quality claim. Gate tuning/STEP4 readiness
remain unchanged: awaiting human labels.
