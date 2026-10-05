# Face canonical192 historical threshold transfer

**ANALYSIS / SIMULATION ONLY — NOT PRODUCTION-APPROVED.**

## Historical reference

OLD reference is the matched 67-video cohort (1893 total rows). Measured face rows: 1823. Common OLD/NEW face measurements: 1820. Missing metrics are excluded from scalar distributions, never from the full NEW simulation CSV.
Historical production native threshold from OLD summary: 50. Counts below/equal/above: **1581/0/242**.

## Percentile transfer method

Primary rejection percentile is strict empirical CDF F<(50)=count(native<50)/N = **1581/1823 = 86.7251782776%**. Inclusive F<= is 86.7251782776%. Equality passes the original Gate; strict CDF therefore defines the transfer target. Stored rounded values are used exactly, not report prose.
OLD canonical192 uses the same OLD measured frame identities (not the smaller common-face subset). Quantile convention: numpy linear/type7, h=(N-1)*p, interpolate adjacent sorted values. Quantile interpolation may give a one-row rank difference from the empirical count; no adjustment to force counts.

## Derived threshold

**36.9013920732** (unrounded computation retained in JSON/CSV). Human answers and final eligible counts were not loaded or used to derive this value.

## Sensitivity analysis

| Historical percentile | Candidate | NEW executed face_blurry / total | Status changed | Branch rejection removed | Fully eligible rescued |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 84.72517828% | 33.4585297 | 1795/1893 (94.8230%) | 28 | 28 | 18 |
| 86.72517828% | 36.90139207 | 1799/1893 (95.0343%) | 24 | 24 | 16 |
| 88.72517828% | 40.52629788 | 1801/1893 (95.1400%) | 22 | 22 | 15 |

## OLD vs NEW stability

Scalar severity below is independent of eye masking; it is not the recorded face_blurry reason rate.
| Cohort | Scope | Percentile | N | native50 below | canonical below | canonical at/above | Videos measured / at-above |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| old | all_measured | 84.72517828% | 1823 | 1581 (86.7252%) | 1544 (84.6956%) | 279 | 67/33 |
| old | all_measured | 86.72517828% | 1823 | 1581 (86.7252%) | 1581 (86.7252%) | 242 | 67/32 |
| old | all_measured | 88.72517828% | 1823 | 1581 (86.7252%) | 1617 (88.6999%) | 206 | 67/32 |
| old | common_measured | 84.72517828% | 1820 | 1578 (86.7033%) | 1541 (84.6703%) | 279 | 67/33 |
| old | common_measured | 86.72517828% | 1820 | 1578 (86.7033%) | 1578 (86.7033%) | 242 | 67/32 |
| old | common_measured | 88.72517828% | 1820 | 1578 (86.7033%) | 1614 (88.6813%) | 206 | 67/32 |
| new | all_measured | 84.72517828% | 1824 | 1823 (99.9452%) | 1490 (81.6886%) | 334 | 67/37 |
| new | all_measured | 86.72517828% | 1824 | 1823 (99.9452%) | 1527 (83.7171%) | 297 | 67/35 |
| new | all_measured | 88.72517828% | 1824 | 1823 (99.9452%) | 1561 (85.5811%) | 263 | 67/32 |
| new | common_measured | 84.72517828% | 1820 | 1819 (99.9451%) | 1488 (81.7582%) | 332 | 67/37 |
| new | common_measured | 86.72517828% | 1820 | 1819 (99.9451%) | 1525 (83.7912%) | 295 | 67/35 |
| new | common_measured | 88.72517828% | 1820 | 1819 (99.9451%) | 1559 (85.6593%) | 261 | 67/32 |

### Shot-type scalar breakdown at derived threshold

| Cohort | Shot | N measured | Below | At/above |
| --- | --- | ---: | ---: | ---: |
| old | CLOSE_UP | 323 | 192 | 131 |
| old | FULL_BODY | 748 | 727 | 21 |
| old | UNCLASSIFIED | 0 | 0 | 0 |
| old | UPPER_BODY | 752 | 662 | 90 |
| new | CLOSE_UP | 315 | 167 | 148 |
| new | FULL_BODY | 750 | 728 | 22 |
| new | UNCLASSIFIED | 0 | 0 | 0 |
| new | UPPER_BODY | 759 | 632 | 127 |

### Video scalar coverage at derived threshold

| Video | OLD measured / at-above | NEW measured / at-above |
| --- | ---: | ---: |
| Sasha_v01 | 19/0 | 19/0 |
| Sasha_v03 | 106/6 | 106/14 |
| Sasha_v04 | 23/1 | 23/1 |
| Sasha_v05 | 32/13 | 32/13 |
| Sasha_v06 | 18/0 | 17/0 |
| Sasha_v07 | 22/1 | 22/2 |
| Sasha_v08 | 13/11 | 15/13 |
| Sasha_v09 | 30/0 | 30/0 |
| Sasha_v10 | 26/16 | 26/17 |
| Sasha_v11 | 22/2 | 22/4 |
| Sasha_v12 | 24/2 | 24/7 |
| Sasha_v13 | 26/0 | 26/0 |
| Sasha_v14 | 29/0 | 29/0 |
| Sasha_v15 | 24/7 | 24/10 |
| Sasha_v16 | 30/14 | 30/15 |
| Sasha_v17 | 25/0 | 25/0 |
| Sasha_v19 | 30/0 | 30/0 |
| Sasha_v20 | 20/0 | 20/0 |
| Sasha_v21 | 24/0 | 24/0 |
| Sasha_v22 | 37/30 | 37/32 |
| Sasha_v23 | 20/4 | 20/7 |
| Sasha_v24 | 28/4 | 28/5 |
| Sasha_v25 | 28/0 | 28/0 |
| Sasha_v26 | 24/0 | 24/0 |
| Sasha_v27 | 26/7 | 26/8 |
| Sasha_v28 | 29/0 | 29/0 |
| Sasha_v29 | 22/6 | 22/8 |
| Sasha_v30 | 26/2 | 26/1 |
| Sasha_v31 | 29/3 | 29/3 |
| Sasha_v32 | 21/0 | 21/0 |
| Sasha_v33 | 33/25 | 33/30 |
| Sasha_v34 | 15/6 | 15/9 |
| Sasha_v35 | 30/3 | 30/7 |
| Sasha_v36 | 39/0 | 39/0 |
| Sasha_v37 | 18/0 | 18/0 |
| Sasha_v38 | 27/0 | 27/1 |
| Sasha_v39 | 33/0 | 34/0 |
| Sasha_v40 | 30/0 | 30/0 |
| Sasha_v41 | 19/17 | 19/17 |
| Sasha_v42 | 19/7 | 19/6 |
| Sasha_v44 | 22/0 | 22/0 |
| Sasha_v45 | 23/0 | 23/1 |
| Sasha_v46 | 30/0 | 30/0 |
| Sasha_v47 | 30/0 | 30/0 |
| Sasha_v48 | 22/0 | 22/0 |
| Sasha_v49 | 30/2 | 30/2 |
| Sasha_v50 | 30/0 | 30/0 |
| Sasha_v51 | 21/0 | 21/0 |
| Sasha_v52 | 57/1 | 57/2 |
| Sasha_v53 | 30/22 | 30/25 |
| Sasha_v54 | 24/2 | 24/2 |
| Sasha_v55 | 21/0 | 21/1 |
| Sasha_v56 | 27/0 | 27/0 |
| Sasha_v57 | 40/0 | 40/0 |
| Sasha_v58 | 30/2 | 30/2 |
| Sasha_v59 | 30/0 | 30/0 |
| Sasha_v60 | 19/15 | 19/18 |
| Sasha_v61 | 30/1 | 30/1 |
| Sasha_v62 | 14/0 | 15/0 |
| Sasha_v63 | 20/1 | 20/1 |
| Sasha_v64 | 30/0 | 30/0 |
| Sasha_v65 | 22/2 | 22/3 |
| Sasha_v66 | 21/7 | 20/9 |
| Sasha_v67 | 25/0 | 25/0 |
| Sasha_v68 | 27/0 | 27/0 |
| Sasha_v70 | 22/0 | 21/0 |
| Sasha_v71 | 30/0 | 30/0 |

## Current 4K simulation result

Reconstructed only the existing eye-first if/elif blur block from stored rounded eye/face values, shot and face/status fields. Original face_blurry reasons match the reconstruction on every row. All non-blur reasons remain exactly recorded; no exposure/beauty/occlusion formulas are re-executed.
Executed branch counts: `{'FACE_LAPLACIAN_FULL_BODY': 750, 'EYE_SHARPNESS_MASKS_FACE_LAPLACIAN': 1071, 'NO_FACE_NOT_APPLICABLE': 69, 'FACE_LAPLACIAN_NON_FULL_BODY': 3}`.
Original face_blurry: 1823/1893. Simulated face_blurry: **1799/1893 (95.0343%)**. Changed: **24**; removed 24, added 0.
Branch-only rescue (face_blurry removed): 24. Of these, 8 still fail other Gates; 16 become fully eligible. Simulated total eligible: 17. This is not a quality-validation claim.

| Shot | Total | Eye masked | Face actually executed | Original blur | Simulated blur | Changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CLOSE_UP | 315 | 315 | 0 | 315 | 315 | 0 |
| FULL_BODY | 750 | 0 | 750 | 749 | 728 | 21 |
| UNCLASSIFIED | 69 | 0 | 0 | 0 | 0 | 0 |
| UPPER_BODY | 759 | 756 | 3 | 759 | 756 | 3 |

## Limitations / interpretation

This transfers historical scalar rejection severity, not old final eligible counts, frame-by-frame equivalent decisions, LoRA suitability or the correctness of the old Gate. Eye-masked rows retain their original eye rejection even if canonical face sharpness passes. FULL_BODY directly uses face Laplacian. Changed shot types/ROI/detection between generations remain confounders.
OLD pixels were source-hash-verified historical recipe re-extractions. Canonical experiment verified native metrics against archived scalars. Historical original PNG byte identity and exact pre/post-upscale presentation timestamp equivalence are not proven. Resize cannot restore missing source detail. Rounded historical scalars limit sub-rounding CDF precision; reported empirical position is exact for stored measurements.
Similarity of canonical distributions does not imply identical tail severity. Above/below counts, sensitivity percentiles, common-face subset and video/shot breakdowns expose residual shifts. The mathematical candidate must not be applied to production without separate approval/validation.

## Human-label sanity-check

Not performed in this task. No Human Review answer file was loaded. Prior canonical experiment remains separate descriptive evidence; no label-fit adjustment is made here.

## Validation / scope

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, .agents/rules/lora_pipeline_rules.md and data_lineage_rules.md; relevant Current Knowledge, ACCEPTED DEC-0002/0003/0006, Failures/Cases, History/Experiments and source audit/results.
Data lineage preserved: YES. Full-row preservation: YES for the full current NEW generation; matched OLD reference explicitly separated. Historical evidence preserved: YES. Config SSOT preserved: YES. Source/config/code/official reports/prior experimental artifacts SHA256 unchanged before/after. Rules conflicts: none.
Created only experimental transfer_canonical192.py/.bat, derived simulation CSV, audit JSON and this report. README/Knowledge/Decisions/Failures/Cases/History/Experiments checked; no other update required under analysis-only scope. Production readiness and threshold application deferred.
Human labels used for threshold derivation: NO. Production STEP3 changed: NO. Thresholds changed: NO. A/B/C changed: NO. Full production batch executed: NO. No inference, image decode, Revision A, STEP4+, commit or push.

## Explicit severity interpretation

OLD severity preserved: YES for marginal scalar rejection fraction: native50 1581/1823 vs canonical192 1581/1823. This does not preserve frame identities or final eligible counts.
OLD actually executed face_blurry: native50 1622/1893 (85.6841%) vs canonical192 1726/1893 (91.1780%). Eye-first masking retained. Branch counts: `{'FACE_LAPLACIAN_FULL_BODY': 748, 'original_blur': 1622, 'canonical_simulated_blur': 1726, 'EYE_SHARPNESS_MASKS_FACE_LAPLACIAN': 791, 'NO_FACE_NOT_APPLICABLE': 70, 'FACE_LAPLACIAN_NON_FULL_BODY': 284}`.
Common-face threshold CDF shift NEW minus OLD: canonical192 -2.9121 percentage points, vs native50 +13.2418 points. Canonical192 is closer in severity on this cohort; similarity is not proof of Gate correctness. Sensitivity +/-2 historical percentile points is reported above without tuning the candidate.
Human labels used for threshold derivation: NO. Official production, thresholds and A/B/C remain unchanged.
