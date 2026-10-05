# STEP3 canonical sharpness diagnostic experiment — 2026-10-03

**EXPERIMENTAL RESULT — NOT PRODUCTION-APPROVED.** Previous STOP/design reports are retained; this is a new result after explicitly authorized historical recovery.

## Observed / lineage

- Matched cohort: 1893 frames / 67 videos. OLD full reference remains2,001 rows, current formal NEW1,893 rows. Removed sources and supplementals are excluded without deletion.
- OLD pixels are explicitly re-extracted from SHA256-identical original videos using the historical policy2 recipe, not falsely described as recovered original PNG archives. All recovered sizes/counts matched historical records. Native global/face Laplacian and Tenengrad were verified against saved scalars for every available measurement (absolute error≤0.000501). All NEW image hashes match active extraction metadata.
- Pair identity means same source/video/sample schedule; exact pre/post-upscale PTS/content equivalence is not proven. Face bboxes are each generation's stored primary bbox; detector/ROI drift is a remaining confound. No detector or FaceMesh inference ran.

## Measurement design

- Global short-edge candidates: [720, 1080]. Face/core short-edge candidates: [192, 256, 320]. Long edge uses round(original_long×target_short/original_short), preserving aspect ratio with integer rounding; no square distortion.
- Measurement copies only: resize BGR, then production grayscale conversion and unchanged cv2.Laplacian(CV_64F).var and Sobel ksize3 mean(dx²+dy²). Face core/crop functions are AST-loaded directly from unchanged production source, using SSOT core0.8 and margin0.2. No source pixel file is resized/written.
- INTER_AREA for shrinking, INTER_CUBIC for enlargement, IDENTITY when dimensions unchanged. Enlargement cannot recover detail. Actual resize methods/dimensions and source hashes are recorded. Native values in the sidecar remain the original saved strings; verification is separate.
- Distributions use OLD/NEW common nonmissing rows per metric, linear numpy percentiles. Face common N differs from individual detection availability, listed below. No silent row deletion; wide comparison CSV keeps all matched frame identities and missing face scalars as blanks.
- Stability score = mean absolute log(NEWquantile/OLDquantile) over P10/P25/P50/P75/P90/P95/P99. Smaller means distributions are closer; minimum excluded from score. Scale ranking averages Laplacian and Tenengrad scores equally. Median ratios, signed percentile shifts and empirical KS distance are also provided. Eligibility counts are never a selection criterion.

## OLD vs NEW distributions

| Metric | Cohort | Common N | Available N | min | P10 | P25 | P50 | P75 | P90 | P95 | P99 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| global_laplacian_native | old | 1893.0 | 1893.0 | 1.266 | 5.469 | 9.232 | 26.28 | 99.125 | 253.86 | 669.43 | 940.7 |
| global_laplacian_native | new | 1893.0 | 1893.0 | 0.499 | 1.9274 | 2.558 | 3.865 | 6.069 | 15.514 | 22.95 | 111.28 |
| global_tenengrad_native | old | 1893.0 | 1893.0 | 39.76 | 374.87 | 589.39 | 1499.8 | 3650.9 | 7092.1 | 11399 | 19213 |
| global_tenengrad_native | new | 1893.0 | 1893.0 | 6.366 | 88.234 | 161.86 | 311.61 | 628.75 | 1733.5 | 2379.7 | 8740.5 |
| global_laplacian_canonical_720 | old | 1893.0 | 1893.0 | 0.92791 | 7.6854 | 14.327 | 32.536 | 70.424 | 256.23 | 403.36 | 1505.1 |
| global_laplacian_canonical_720 | new | 1893.0 | 1893.0 | 0.97786 | 8.0054 | 15.414 | 34.428 | 75.675 | 299.28 | 410.33 | 1976.8 |
| global_tenengrad_canonical_720 | old | 1893.0 | 1893.0 | 27.875 | 519.5 | 946.9 | 1748.8 | 3302.8 | 7133.2 | 9769.5 | 18838 |
| global_tenengrad_canonical_720 | new | 1893.0 | 1893.0 | 27.612 | 545.73 | 997.3 | 1818.9 | 3469.4 | 7318.7 | 10142 | 21604 |
| global_laplacian_canonical_1080 | old | 1893.0 | 1893.0 | 0.57377 | 3.4098 | 6.0423 | 11.736 | 25.887 | 98.659 | 157.03 | 872.79 |
| global_laplacian_canonical_1080 | new | 1893.0 | 1893.0 | 0.79702 | 4.0948 | 6.7694 | 13.109 | 26.983 | 106.71 | 160.19 | 858.29 |
| global_tenengrad_canonical_1080 | old | 1893.0 | 1893.0 | 14.737 | 271.34 | 503.87 | 957.12 | 1927.9 | 4535 | 6319.3 | 19213 |
| global_tenengrad_canonical_1080 | new | 1893.0 | 1893.0 | 15.36 | 284.62 | 527.25 | 1002.3 | 2002.9 | 4768.3 | 6863.4 | 19823 |
| face_laplacian_native | old | 1820.0 | 1823.0 | 2.503 | 6.3389 | 8.4943 | 14.317 | 29.522 | 58.68 | 92.89 | 169.29 |
| face_laplacian_native | new | 1820.0 | 1824.0 | 1.811 | 3.2 | 3.8327 | 4.7295 | 6.2075 | 8.5984 | 10.264 | 19.255 |
| face_tenengrad_native | old | 1820.0 | 1823.0 | 77.513 | 378.24 | 569.59 | 1031.7 | 1880.8 | 2999.4 | 3796.6 | 5940.1 |
| face_tenengrad_native | new | 1820.0 | 1824.0 | 28.963 | 94.131 | 131.74 | 204.55 | 343.01 | 542.87 | 694.61 | 1365.8 |
| face_laplacian_canonical_192 | old | 1820.0 | 1823.0 | 1.8482 | 4.733 | 6.4357 | 10.424 | 22.459 | 43.778 | 65.884 | 136.09 |
| face_laplacian_canonical_192 | new | 1820.0 | 1824.0 | 2.212 | 5.6253 | 7.6503 | 11.857 | 25.124 | 50.167 | 77.567 | 149.1 |
| face_tenengrad_canonical_192 | old | 1820.0 | 1823.0 | 105.15 | 456.13 | 708.47 | 1121.4 | 1701 | 2445.3 | 3034.2 | 4103.1 |
| face_tenengrad_canonical_192 | new | 1820.0 | 1824.0 | 112.01 | 478.6 | 750.14 | 1193.3 | 1817 | 2638 | 3227.7 | 4437 |
| face_laplacian_canonical_256 | old | 1820.0 | 1823.0 | 1.3146 | 2.9678 | 3.9064 | 6.1255 | 11.878 | 23.531 | 35.396 | 70.387 |
| face_laplacian_canonical_256 | new | 1820.0 | 1824.0 | 2.095 | 4.1499 | 5.2036 | 7.3036 | 13.802 | 26.406 | 41.058 | 77.906 |
| face_tenengrad_canonical_256 | old | 1820.0 | 1823.0 | 62.84 | 273 | 428.64 | 676.38 | 1071.3 | 1601.6 | 2038.8 | 2859.1 |
| face_tenengrad_canonical_256 | new | 1820.0 | 1824.0 | 69.716 | 288.65 | 457.15 | 721.15 | 1145.7 | 1707.9 | 2108.1 | 3048 |
| face_laplacian_canonical_320 | old | 1820.0 | 1823.0 | 1.0761 | 2.2469 | 2.7771 | 4.3178 | 7.698 | 14.146 | 22.051 | 47.985 |
| face_laplacian_canonical_320 | new | 1820.0 | 1824.0 | 1.5078 | 3.4683 | 4.1973 | 5.4643 | 8.8682 | 15.975 | 24.223 | 48.182 |
| face_tenengrad_canonical_320 | old | 1820.0 | 1823.0 | 41.796 | 182.28 | 285.56 | 456.75 | 744.01 | 1129.8 | 1461.4 | 2212.4 |
| face_tenengrad_canonical_320 | new | 1820.0 | 1824.0 | 51.75 | 195.68 | 309.15 | 485.96 | 788.03 | 1196.5 | 1521.1 | 2265.8 |

## Stability by scale

| Metric | NEW/OLD median | Mean abs log shift | KS distance |
| --- | ---: | ---: | ---: |
| global_laplacian_native | 0.1471 | 2.1913 | 0.6598 |
| global_tenengrad_native | 0.2078 | 1.4046 | 0.4929 |
| global_laplacian_canonical_720 | 1.0582 | 0.0982 | 0.0491 |
| global_tenengrad_canonical_720 | 1.0401 | 0.0557 | 0.0417 |
| global_laplacian_canonical_1080 | 1.1170 | 0.0806 | 0.0475 |
| global_tenengrad_canonical_1080 | 1.0473 | 0.0488 | 0.0354 |
| face_laplacian_native | 0.3303 | 1.4919 | 0.6720 |
| face_tenengrad_native | 0.1983 | 1.5789 | 0.6956 |
| face_laplacian_canonical_192 | 1.1374 | 0.1396 | 0.1005 |
| face_tenengrad_canonical_192 | 1.0641 | 0.0642 | 0.0489 |
| face_laplacian_canonical_256 | 1.1923 | 0.1876 | 0.1901 |
| face_tenengrad_canonical_256 | 1.0662 | 0.0590 | 0.0412 |
| face_laplacian_canonical_320 | 1.2655 | 0.2063 | 0.2967 |
| face_tenengrad_canonical_320 | 1.0639 | 0.0559 | 0.0467 |

Signed P10..P99 shifts (%) are included in the distribution CSV/audit JSON. KS is descriptive, not a statistical independence/causal test.

## Human Calibration comparison

- Answers are read-only joins validated by generation, frame/video identity and exact stored target value. Boundary JSON additionally binds the official report hash. Earlier schema2 JSON lacks the report hash due to its historical exporter; its generation/frame/value checks are explicit, and it is kept as a separate evidence group. Labels/notes are copied verbatim.
- IMAGE_SUITABILITY and TARGET_METRIC answers remain separate, as do the earlier vs boundary packages. No relabeling/averaging across question types. Concordance counts cross-label pairs REJECT<BORDERLINE<ACCEPT where the higher label has a higher scalar; ties count0.5. Whole-image labels may depend on exposure/eyes/skin, so this is ordering evidence, not blur classifier accuracy.
| Evidence group | Metric | N | Ordered pairs | Concordance |
| --- | --- | ---: | ---: | ---: |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | global_laplacian_native | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | global_tenengrad_native | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | global_laplacian_canonical_720 | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | global_tenengrad_canonical_720 | 6 | 5 | 0.6000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | global_laplacian_canonical_1080 | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | global_tenengrad_canonical_1080 | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_laplacian_native | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_tenengrad_native | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_laplacian_canonical_192 | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_tenengrad_canonical_192 | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_laplacian_canonical_256 | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_tenengrad_canonical_256 | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_laplacian_canonical_320 | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | face_tenengrad_canonical_320 | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | global_laplacian_native | 6 | 5 | 1.0000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | global_tenengrad_native | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | global_laplacian_canonical_720 | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | global_tenengrad_canonical_720 | 6 | 5 | 0.6000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | global_laplacian_canonical_1080 | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | global_tenengrad_canonical_1080 | 6 | 5 | 0.8000 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_laplacian_native | 6 | 8 | 0.8750 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_tenengrad_native | 6 | 8 | 0.6250 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_laplacian_canonical_192 | 6 | 8 | 0.8750 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_tenengrad_canonical_192 | 6 | 8 | 0.8750 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_laplacian_canonical_256 | 6 | 8 | 0.7500 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_tenengrad_canonical_256 | 6 | 8 | 0.8750 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_laplacian_canonical_320 | 6 | 8 | 0.8750 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | face_tenengrad_canonical_320 | 6 | 8 | 0.8750 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | global_laplacian_native | 7 | 15 | 1.0000 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | global_tenengrad_native | 7 | 15 | 0.4000 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | global_laplacian_canonical_720 | 7 | 15 | 0.5333 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | global_tenengrad_canonical_720 | 7 | 15 | 0.4667 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | global_laplacian_canonical_1080 | 7 | 15 | 0.2667 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | global_tenengrad_canonical_1080 | 7 | 15 | 0.4667 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_laplacian_native | 7 | 12 | 0.1667 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_tenengrad_native | 7 | 12 | 0.2500 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_laplacian_canonical_192 | 7 | 12 | 0.9167 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_tenengrad_canonical_192 | 7 | 12 | 0.7500 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_laplacian_canonical_256 | 7 | 12 | 0.9167 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_tenengrad_canonical_256 | 7 | 12 | 0.7500 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_laplacian_canonical_320 | 7 | 12 | 0.8333 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | face_tenengrad_canonical_320 | 7 | 12 | 0.7500 |

### Human-label separation conclusion

**Human-label separation improved: MIXED.** Distribution stability is improved; human ordering does not uniformly improve.
- Boundary whole-image evidence: global Laplacian native concordance1.000 (15 cross-label pairs) falls to0.533 at720 and0.267 at1080. The distribution-stable1080 scale makes ordering worse for these7 reviewed examples. It is not demonstrated as a suitable independent face-learning gate.
- Boundary whole-image evidence: face Laplacian native concordance0.167 (12 cross-label pairs) improves to0.917 at192/256 and0.833 at320. The mixed native9–11 ACCEPT/REJECT ordering becomes much clearer at192, with one discordant pair remaining.
- Earlier calibration whole-image evidence: global1.000 becomes0.800 at both scales (5 pairs); face stays1.000 at all scales (5 pairs). Target-only answers: global likewise worsens; face0.875 stays0.875 at192/320 but falls to0.750 at256 (8 pairs). No pooling across questions/packages.
- These samples were chosen around native thresholds, not random/exhaustive labels. Ordering improvement is descriptive on this small evidence set; it is neither classifier accuracy nor approval of a cutoff. Native boundary scores must not be transferred to the new measurement grid.

### Reviewed examples (values and immutable answers)

| Source / dimension | review_id | Target | Native | Label | Canonical values |
| --- | --- | --- | ---: | --- | --- |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB001 | global | 4.402 | REJECT | 720=104.1; 1080=30.86 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB003 | global | 4.421 | REJECT | 720=45.78; 1080=19.16 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB004 | global | 4.52 | REJECT | 720=38.94; 1080=17.25 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB006 | global | 4.676 | BORDERLINE | 720=44.11; 1080=14.69 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB007 | global | 4.829 | BORDERLINE | 720=57.62; 1080=18.23 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB008 | global | 4.858 | ACCEPT | 720=46.33; 1080=16.1 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB009 | global | 4.716 | BORDERLINE | 720=48.04; 1080=20.04 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB010 | face | 9.338 | ACCEPT | 192=41.36; 256=20.61; 320=12.83 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB012 | face | 9.254 | ACCEPT | 192=26.15; 256=14.44; 320=9.742 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB013 | face | 9.771 | ACCEPT | 192=38.29; 256=20.37; 320=12.39 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB014 | face | 10.048 | REJECT | 192=10.08; 256=8.412; 320=5.168 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB015 | face | 10.195 | REJECT | 192=23.64; 256=13.64; 320=8.454 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB017 | face | 10.926 | ACCEPT | 192=22.47; 256=12.21; 320=8.032 |
| STEP3_4K_LAPLACIAN_BOUNDARY_ANSWERS.json / IMAGE_SUITABILITY | LB018 | face | 10.984 | REJECT | 192=14.3; 256=8.702; 320=8.194 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL018 | face | 6.284 | REJECT | 192=7.741; 256=5.114; 320=5.275 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL018 | face | 6.284 | REJECT | 192=7.741; 256=5.114; 320=5.275 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL019 | face | 6.304 | REJECT | 192=8.746; 256=5.696; 320=4.291 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL019 | face | 6.304 | REJECT | 192=8.746; 256=5.696; 320=4.291 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL020 | face | 7.808 | REJECT | 192=10.96; 256=7.213; 320=5.464 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL020 | face | 7.808 | BORDERLINE | 192=10.96; 256=7.213; 320=5.464 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL021 | face | 7.797 | REJECT | 192=11.97; 256=7.522; 320=5.468 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL021 | face | 7.797 | REJECT | 192=11.97; 256=7.522; 320=5.468 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL022 | face | 10.049 | ACCEPT | 192=30.03; 256=15.69; 320=10.03 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL022 | face | 10.049 | BORDERLINE | 192=30.03; 256=15.69; 320=10.03 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL023 | face | 9.476 | REJECT | 192=9.201; 256=7.334; 320=4.592 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL023 | face | 9.476 | REJECT | 192=9.201; 256=7.334; 320=4.592 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL024 | global | 2.934 | REJECT | 720=8.151; 1080=5.252 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL024 | global | 2.934 | REJECT | 720=8.151; 1080=5.252 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL025 | global | 3.227 | REJECT | 720=17.9; 1080=8.662 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL025 | global | 3.227 | REJECT | 720=17.9; 1080=8.662 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL026 | global | 4.035 | REJECT | 720=36.47; 1080=15.09 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL026 | global | 4.035 | REJECT | 720=36.47; 1080=15.09 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL027 | global | 4.113 | REJECT | 720=30.86; 1080=13.14 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL027 | global | 4.113 | REJECT | 720=30.86; 1080=13.14 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL028 | global | 4.714 | ACCEPT | 720=39.35; 1080=17.36 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL028 | global | 4.714 | ACCEPT | 720=39.35; 1080=17.36 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / IMAGE_SUITABILITY | CAL029 | global | 4.434 | REJECT | 720=53.07; 1080=20.95 |
| STEP3_4K_CALIBRATION_ANSWERS (2).json / TARGET_METRIC | CAL029 | global | 4.434 | REJECT | 720=53.07; 1080=20.95 |

## Recommendations — experimental, not approved

- Most distribution-stable tested global short edge: **1080 px**. Joint scores: {'720': 0.07694259428462422, '1080': 0.0646717334992409}. This is the best among tested candidates, not invariance or production approval.
- Most distribution-stable tested face short edge: **192 px**. Joint scores: {'192': 0.10189355298604538, '256': 0.12329935542653006, '320': 0.1310649679666854}. This is the best among tested candidates, not invariance or production approval.

Global1080 is recommended only as the most comparable distribution among tested scales, with negative human-ordering evidence preventing a production quality-gate recommendation. Face192 is a promising experimental diagnostic: improved distribution stability and clearer boundary ordering, still requiring independent review/validation. Neither recommendation authorizes changing production thresholds.

Distribution similarity and human-label separation must be judged separately. Residual scale/codec/upscaler smoothing, native sampling information loss, bbox geometry and enlargement/downsampling still affect measurements. A single dataset and few reviewed examples cannot establish a universal cutoff; do not transfer current25/50 or invented4K-specific thresholds to canonical columns.
Eye/skin remain spatially sensitive per the prior audit, but their algorithms/thresholds/applicability are unchanged. No promotion to Hard Gates, no A/B/C decision, and no beauty/identity claim from canonical gradients.

## Validation / artifacts / unchanged production

- Native reproduction checked for all available OLD/NEW measurements; source/config/code/report/answer hashes checked before and after, including every decoded input image. All cohort rows preserved, mutually missing face data explicit. BAT+Python runs are diagnostic only, output collision refuses overwrite. No official STEP3 inference or downstream pipeline.
- Created experimental compare_sharpness.py / comparison_settings.json / compare_sharpness.bat in docs/STEP3_CANONICAL_EXPERIMENT plus comparison/distribution/human CSVs, audit JSON and this report. Historical STOP/design/recovery reports and Human Review are not rewritten.
- Rules checked: AGENTS/.agents AGENTS, PROJECT, pipeline/data-lineage rules, current face-quality/configuration knowledge, accepted sharpness/beauty Decisions, relevant failure/case and History/Experiments already reviewed. Documentation checked; no other update required. Rule conflicts: none.
- Data lineage preserved: YES. Full-row preservation: YES for matched1,893-row comparison (OLD71→matched67 subset explicitly declared); official OLD/NEW full reports unchanged. Historical evidence preserved: YES. Config SSOT preserved: YES.
- Production STEP3 changed: NO. Thresholds changed: NO. A/B/C changed: NO. Full production batch executed: NO. No Revision A, STEP4+, commit or push.
