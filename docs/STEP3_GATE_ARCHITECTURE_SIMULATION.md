# STEP3 canonical192 Gate architecture simulation

**ANALYSIS / SIMULATION ONLY — NOT PRODUCTION-APPROVED.**

Current generation: `bd72f194f62260fb728b77b26c75c5491b178908bff53393e197c11137bf9a40`. Full 1893 rows / 67 videos retained. No image decoding or inference.
## Simulated policy / reconstruction

Existing no_face, multiple_faces, low_visibility (missing/unusable FaceMesh or visibility below configured minimum), face_too_small, low_resolution_source, face_underexposed, face_backlit_underexposed, hair_covered_face and one_eye_occluded remain hard failures.
The existing stored-metric Gate block was AST-extracted from unchanged production source and run on dictionary copies only; recorded reasons and eligible values match all rows exactly. Retained reasons are then taken from authoritative records. No new severity threshold or occlusion/visibility formula is introduced. analysis_error/unknown reasons/missing single-face canonical evidence cause STOP.
Canonical192 from the prior validated comparison is evaluated directly on every detected single-face row, regardless of eye-sharpness failure. Missing FaceMesh does not mask a available canonical metric, but retains its independent low_visibility failure. Multiple/no-face rows retain their hard failure; the stored primary-face scalar on the multiple-face row is context only.
Thresholds are exactly the requested six-decimal simulation values (33.45853, 36.901392, 40.526298). Full-precision prior transfer anchor is recorded separately; no threshold selection/tuning occurs here.

### Diagnostic flags and explicit BORDERLINE grouping

Global suspicion: stored native global < 25.0; native-face suspicion: stored native face < 50.0. Both are descriptive scale-sensitive context and never force BORDERLINE, even together.
EYE_DETAIL: actually measured, eye-presence-valid non-FULL_BODY eye sharpness < 1.6. Disabled/missing zero proxies are excluded; their states remain visible. Eye-presence hard failures are still retained.
SKIN_PROCESSING: applicable measured CLOSE_UP/UPPER_BODY has skin below its existing configured cutoff (0.05/0.035), recorded beauty flag, or plasticity > 45.0. Correlated skin/beauty/plasticity flags constitute ONE family, not three independent votes. FULL_BODY plasticity may be flagged descriptively but is not an applicable skin-family vote.
**REJECT** if any hard reason; otherwise **BORDERLINE** only when both EYE_DETAIL and SKIN_PROCESSING are present; otherwise **PASS**. A single concern family does not block PASS. This explicit exploratory grouping has no hidden weighting and is not validated usability or A/B/C. Skin/plasticity diagnostics use stored rounded values (not reconstruction of unrounded causal beauty branches).

## Overall / sensitivity

| Threshold | PASS | BORDERLINE | REJECT | Canonical hard failures |
| ---: | ---: | ---: | ---: | ---: |
| 33.458530 | 75 (3.9620%) | 90 (4.7544%) | 1728 (91.2837%) | 1489 |
| 36.901392 | 70 (3.6978%) | 80 (4.2261%) | 1743 (92.0761%) | 1526 |
| 40.526298 | 64 (3.3809%) | 69 (3.6450%) | 1760 (92.9741%) | 1560 |

## Official-to-simulated transitions

Official eligible 1/1893; rejected 1892/1893.

| Original | Simulated | N |
| --- | --- | ---: |
| ELIGIBLE | PASS | 1 |
| REJECT | BORDERLINE | 80 |
| REJECT | PASS | 69 |
| REJECT | REJECT | 1743 |

## Retained hard cause contribution

Counts overlap; exclusive means that reason is the sole simulated hard failure, including canonical failure in the comparison.
| Cause | N | % all rows | Exclusive N |
| --- | ---: | ---: | ---: |
| no_face | 69 | 3.6450% | 69 |
| multiple_faces | 1 | 0.0528% | 0 |
| low_visibility | 205 | 10.8294% | 5 |
| face_too_small | 0 | 0.0000% | 0 |
| low_resolution_source | 0 | 0.0000% | 0 |
| face_underexposed | 167 | 8.8220% | 0 |
| face_backlit_underexposed | 31 | 1.6376% | 0 |
| hair_covered_face | 0 | 0.0000% | 0 |
| one_eye_occluded | 607 | 32.0655% | 133 |
| canonical192_face_blurry | 1526 | 80.6128% | 777 |

## Usability pressure

Canonical192-only rejects: **777**. Other-Hard-Gate-only rejects: **217**. Combined rejects: **749**. No hard failure: 150. These overlapping source conditions are partitioned exactly once here.

## Canonical face measurements / shot breakdown

Measured 1824; below 1527; at/above 297; videos with an above-threshold measurement 35. Measured includes the single multiple-face primary metric; simulated applicability excludes that row.

| Shot | Total | Measured | Measured below | Measured at/above | Applicable single-face | Canonical hard failures | State counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CLOSE_UP | 315 | 315 | 167 | 148 | 315 | 167 | {'REJECT': 255, 'BORDERLINE': 58, 'PASS': 2} |
| FULL_BODY | 750 | 750 | 728 | 22 | 750 | 728 | {'REJECT': 732, 'PASS': 18} |
| UNCLASSIFIED | 69 | 0 | 0 | 0 | 0 | 0 | {'REJECT': 69} |
| UPPER_BODY | 759 | 759 | 632 | 127 | 758 | 631 | {'REJECT': 687, 'PASS': 50, 'BORDERLINE': 22} |

Videos with at least one measured above-threshold row: Sasha_v03, Sasha_v04, Sasha_v05, Sasha_v07, Sasha_v08, Sasha_v10, Sasha_v11, Sasha_v12, Sasha_v15, Sasha_v16, Sasha_v22, Sasha_v23, Sasha_v24, Sasha_v27, Sasha_v29, Sasha_v30, Sasha_v31, Sasha_v33, Sasha_v34, Sasha_v35, Sasha_v38, Sasha_v41, Sasha_v42, Sasha_v45, Sasha_v49, Sasha_v52, Sasha_v53, Sasha_v54, Sasha_v55, Sasha_v58, Sasha_v60, Sasha_v61, Sasha_v63, Sasha_v65, Sasha_v66

## Diagnostic-only signals

| Flag | N (all states) |
| --- | ---: |
| global_blur_suspected | 1806 |
| native_face_blur_suspected | 1823 |
| eye_detail_suspected | 464 |
| skin_detail_suspected | 935 |
| beauty_filter_suspected | 939 |
| plasticity_suspected | 179 |

### Top exact diagnostic combinations

| Combination | N |
| --- | ---: |
| global_blur_suspected;native_face_blur_suspected | 729 |
| global_blur_suspected;native_face_blur_suspected;skin_detail_suspected;beauty_filter_suspected | 530 |
| global_blur_suspected;native_face_blur_suspected;eye_detail_suspected;skin_detail_suspected;beauty_filter_suspected | 256 |
| global_blur_suspected;native_face_blur_suspected;eye_detail_suspected;skin_detail_suspected;beauty_filter_suspected;plasticity_suspected | 133 |
| global_blur_suspected | 69 |
| global_blur_suspected;native_face_blur_suspected;eye_detail_suspected | 49 |
| native_face_blur_suspected | 43 |
| global_blur_suspected;native_face_blur_suspected;plasticity_suspected | 36 |
| native_face_blur_suspected;eye_detail_suspected | 20 |
| native_face_blur_suspected;skin_detail_suspected;beauty_filter_suspected | 10 |
| native_face_blur_suspected;plasticity_suspected | 7 |
| global_blur_suspected;native_face_blur_suspected;beauty_filter_suspected | 3 |
| native_face_blur_suspected;eye_detail_suspected;skin_detail_suspected;beauty_filter_suspected | 3 |
| native_face_blur_suspected;eye_detail_suspected;skin_detail_suspected;beauty_filter_suspected;plasticity_suspected | 2 |
| native_face_blur_suspected;skin_detail_suspected;beauty_filter_suspected;plasticity_suspected | 1 |

## Interpretation / limitations

Canonical sharpness remains a historical severity-transfer candidate, not human-validated correctness. This simulation cannot establish whether its pressure is too restrictive for LoRA. The new diagnostic grouping changes the meaning of PASS/BORDERLINE; both require human quality/identity review before dataset selection. Neither restores C nor finalizes A/B/C.
Prior experiment found clearer face boundary ordering but mixed global ordering. Human Review was not loaded or used to select/tune thresholds or grouping. No new review package. Recorded rounded diagnostics have boundary uncertainty; retained hard predicates were checked against the exact current stored-metric production block, not guessed from prose.
Original source/ROI/detection and recovered OLD limitations remain those of the canonical experiment. Images are not resized/recomputed here. Every original state/reason/category is retained in separate CSV columns.

## Validation / changed artifacts

Created only docs/STEP3_CANONICAL_EXPERIMENT/simulate_architecture.py/.bat; this derived report; output/reports/step3_gate_architecture_simulation.csv and its audit JSON. BAT initializes the existing _common environment, then executes the diagnostic script; output collisions refuse overwrite.
Rules checked: AGENTS.md/.agents/AGENTS.md, PROJECT.md, pipeline/data-lineage rules, relevant current face/config/lineage Knowledge, accepted DEC-0002/0003/0006 and relevant Failure/Case/History/Experiments reviewed in this session. Rule conflicts: none. Documentation checked; no other update required under derived-analysis-only scope.
Data lineage preserved: YES. Full-row preservation: YES (current formal generation, no supplemental/OLD merge). Historical evidence preserved: YES. Config SSOT preserved: YES. Protected input/config/production code/official BAT/official reports/prior experiment hashes unchanged before/after. No production-ready claim.
Production STEP3 changed: NO. Thresholds changed: NO. A/B/C changed: NO. Full production batch executed: NO. No Revision A/STEP4+, cleanup, source mutation, commit or push.
