# STEP3 Face Quality Summary

Status: PASS; rows: 2001; eligible: 62; errors: 0

Regenerated solely from STEP3 CSV values. Source SHA256: 2589176c4a2eb22d098a1f97500654cde0e0ce6dfda0873cdeac25893f6b0051

All STEP2 values retained. Reasons overlap; primary categories are exclusive. Rejected includes error rows.
Face percentiles use successful single-face rows (historical midrank formula). shot_type is provisional face scale, not STEP4 pose/composition.
Geometric blink and mouth bins are provisional diagnostics, not validated blink/expression/speech labels and never rejection gates.
Beauty/filter and occlusion outputs are heuristic flags, not verified causes. FULL_BODY bypasses beauty rejection. Missing metrics are blank, not measured zero.

## Detection and eligibility

```json
{
  "frame_count": 2001,
  "eligible_count": 62,
  "eligible_ratio": 0.030985,
  "rejected_count": 1939,
  "analysis_error_count": 0,
  "no_face_count": 77,
  "face_detected_count": 1924,
  "single_face_count": 1921,
  "multiple_faces_count": 3,
  "facemesh_detected_count": 1719,
  "blink_suspected_count": 2,
  "mouth_open_count": 358,
  "mouth_very_open_count": 90,
  "beauty_fullbody_skipped_count": 807
}
```

## Reasons (overlap and exclusive categories)

| Type | Reason | Frames | % | Videos |
|---|---|---:|---:|---:|
| overlapping_reason | analysis_error | 0 | 0.0 | 0 |
| overlapping_reason | beauty_filter_detected | 459 | 22.938531 | 54 |
| overlapping_reason | eligible | 62 | 3.098451 | 15 |
| overlapping_reason | face_backlit_underexposed | 24 | 1.1994 | 5 |
| overlapping_reason | face_blurry | 1691 | 84.507746 | 71 |
| overlapping_reason | face_too_small | 26 | 1.29935 | 4 |
| overlapping_reason | face_underexposed | 218 | 10.894553 | 23 |
| overlapping_reason | global_blurry | 953 | 47.626187 | 41 |
| overlapping_reason | hair_covered_face | 0 | 0.0 | 0 |
| overlapping_reason | low_resolution_source | 281 | 14.042979 | 18 |
| overlapping_reason | low_visibility | 241 | 12.043978 | 40 |
| overlapping_reason | multiple_faces | 3 | 0.149925 | 2 |
| overlapping_reason | no_face | 77 | 3.848076 | 20 |
| overlapping_reason | one_eye_occluded | 595 | 29.735132 | 59 |
| exclusive_primary_category | ELIGIBLE | 62 | 3.098451 | 15 |
| exclusive_primary_category | REJECT_BEAUTY_FILTER | 458 | 22.888556 | 54 |
| exclusive_primary_category | REJECT_BLUR | 547 | 27.336332 | 59 |
| exclusive_primary_category | REJECT_LOW_RES | 279 | 13.943028 | 18 |
| exclusive_primary_category | REJECT_MULTIPLE_FACE | 3 | 0.149925 | 2 |
| exclusive_primary_category | REJECT_NO_FACE | 77 | 3.848076 | 20 |
| exclusive_primary_category | REJECT_OCCLUSION | 575 | 28.735632 | 62 |
| exclusive_primary_category | REJECT_SMALL_FACE | 0 | 0.0 | 0 |
| exclusive_primary_category | REVIEW_UNKNOWN | 0 | 0.0 | 0 |

## STEP2 × STEP3

Top/bottom 10% use stored quality_rank with ceil(N × 0.10), ties already ordered by STEP2.
```json
{
  "global_top_10_percent": {
    "frame_count": 201,
    "eligible_count": 43,
    "eligible_ratio": 0.21393,
    "rejected_count": 158,
    "analysis_error_count": 0,
    "no_face_count": 7,
    "face_detected_count": 194,
    "single_face_count": 194,
    "multiple_faces_count": 0,
    "facemesh_detected_count": 162,
    "blink_suspected_count": 0,
    "mouth_open_count": 43,
    "mouth_very_open_count": 4,
    "beauty_fullbody_skipped_count": 102,
    "face_blurry_count": 102,
    "beauty_filter_count": 14
  },
  "global_bottom_10_percent": {
    "frame_count": 201,
    "eligible_count": 0,
    "eligible_ratio": 0.0,
    "rejected_count": 201,
    "analysis_error_count": 0,
    "no_face_count": 19,
    "face_detected_count": 182,
    "single_face_count": 181,
    "multiple_faces_count": 1,
    "facemesh_detected_count": 164,
    "blink_suspected_count": 1,
    "mouth_open_count": 23,
    "mouth_very_open_count": 3,
    "beauty_fullbody_skipped_count": 107,
    "face_blurry_count": 181,
    "beauty_filter_count": 47
  }
}
```

## Video concentration

| Video | Frames | Eligible | Ratio | No face | Multiple | Errors |
|---|---:|---:|---:|---:|---:|---:|
| Sasha_v01 | 19 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v02 | 26 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v03 | 120 | 0 | 0.0 | 14 | 1 | 0 |
| Sasha_v04 | 23 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v05 | 32 | 20 | 0.625 | 0 | 0 | 0 |
| Sasha_v06 | 19 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v07 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v08 | 20 | 2 | 0.1 | 7 | 0 | 0 |
| Sasha_v09 | 30 | 1 | 0.033333 | 0 | 0 | 0 |
| Sasha_v10 | 26 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v11 | 28 | 0 | 0.0 | 6 | 0 | 0 |
| Sasha_v12 | 24 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v13 | 26 | 1 | 0.038462 | 0 | 0 | 0 |
| Sasha_v14 | 29 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v15 | 24 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v16 | 30 | 1 | 0.033333 | 0 | 0 | 0 |
| Sasha_v17 | 26 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v18 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v19 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v20 | 20 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v21 | 29 | 0 | 0.0 | 5 | 0 | 0 |
| Sasha_v22 | 37 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v23 | 20 | 2 | 0.1 | 0 | 0 | 0 |
| Sasha_v24 | 28 | 3 | 0.107143 | 0 | 0 | 0 |
| Sasha_v25 | 29 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v26 | 24 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v27 | 26 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v28 | 29 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v29 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v30 | 27 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v31 | 29 | 2 | 0.068966 | 0 | 0 | 0 |
| Sasha_v32 | 21 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v33 | 33 | 3 | 0.090909 | 0 | 0 | 0 |
| Sasha_v34 | 15 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v35 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v36 | 39 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v37 | 18 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v38 | 27 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v39 | 39 | 0 | 0.0 | 6 | 0 | 0 |
| Sasha_v40 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v41 | 19 | 1 | 0.052632 | 0 | 0 | 0 |
| Sasha_v42 | 20 | 1 | 0.05 | 1 | 0 | 0 |
| Sasha_v43 | 26 | 0 | 0.0 | 6 | 2 | 0 |
| Sasha_v44 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v45 | 23 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v46 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v47 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v48 | 23 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v49 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v50 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v51 | 21 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v52 | 57 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v53 | 30 | 13 | 0.433333 | 0 | 0 | 0 |
| Sasha_v54 | 29 | 0 | 0.0 | 5 | 0 | 0 |
| Sasha_v55 | 21 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v56 | 30 | 0 | 0.0 | 3 | 0 | 0 |
| Sasha_v57 | 44 | 0 | 0.0 | 4 | 0 | 0 |
| Sasha_v58 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v59 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v60 | 20 | 4 | 0.2 | 1 | 0 | 0 |
| Sasha_v61 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v62 | 22 | 0 | 0.0 | 8 | 0 | 0 |
| Sasha_v63 | 20 | 1 | 0.05 | 0 | 0 | 0 |
| Sasha_v64 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v65 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v66 | 21 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v67 | 25 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v68 | 30 | 0 | 0.0 | 3 | 0 | 0 |
| Sasha_v69 | 26 | 7 | 0.269231 | 1 | 0 | 0 |
| Sasha_v70 | 24 | 0 | 0.0 | 2 | 0 | 0 |
| Sasha_v71 | 30 | 0 | 0.0 | 0 | 0 | 0 |

## Distributions

Population std, linear percentiles of stored values; missing includes N/A and errors (not additive categories).

| Metric | Count | Missing | N/A (no face) | Errors | Min | P50 | P90 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| face_laplacian_score | 1924 | 77 | 77 | 0 | 2.3 | 15.0265 | 60.6552 | 2618.358 |
| face_tenengrad_score | 1924 | 77 | 77 | 0 | 38.896 | 1075.609 | 3085.6045 | 13118.968 |
| face_sharpness_score | 1921 | 80 | 77 | 0 | 0.05 | 50.13 | 89.58 | 99.97 |
| eye_sharpness | 1719 | 282 | 77 | 0 | 0.0 | 0.0 | 2.823 | 5.473 |
| mouth_sharpness | 1719 | 282 | 77 | 0 | 0.567 | 1.763 | 3.4418 | 6.199 |
| face_visibility_score | 1924 | 77 | 77 | 0 | 0.0 | 100.0 | 100.0 | 100.0 |
| face_brightness_mean | 1924 | 77 | 77 | 0 | 49.0 | 122.3 | 146.07 | 181.0 |
| face_min_dimension | 1924 | 77 | 77 | 0 | 48.0 | 244.0 | 480.7 | 977.0 |
| face_area_ratio | 1924 | 77 | 77 | 0 | 0.00454 | 0.05016 | 0.15668 | 0.52904 |
| skin_texture_score | 1719 | 282 | 77 | 0 | 0.003 | 0.058 | 0.3272 | 5.178 |
| plasticity_ratio | 1719 | 282 | 77 | 0 | 0.0 | 0.0 | 49.54 | 158.9 |
| eye_openness_mean | 1719 | 282 | 77 | 0 | 0.09318 | 0.324372 | 0.389968 | 0.771217 |
| mouth_open_ratio | 1719 | 282 | 77 | 0 | 0.000724 | 0.051935 | 0.280571 | 0.647511 |

## Review examples

Examples are audit references only; no selection or verified causal labels.

### analysis_error


### beauty_filter_detected

- `Sasha_v02/Sasha_v02_026.png`: global Lap=14.447, face Lap=23.930, eye=2.587, skin=0.045, plasticity=57.3, openness=0.368200, mouth=0.001955; global_blurry;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_001.png`: global Lap=5.506, face Lap=10.942, eye=0.000, skin=0.032, plasticity=0.0, openness=0.299351, mouth=0.018094; multiple_faces;global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_004.png`: global Lap=4.287, face Lap=8.648, eye=0.000, skin=0.034, plasticity=0.0, openness=0.294660, mouth=0.011913; global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry

### eligible

- `Sasha_v05/Sasha_v05_001.png`: global Lap=975.088, face Lap=101.554, eye=0.000, skin=1.969, plasticity=0.0, openness=0.383156, mouth=0.185788; eligible
- `Sasha_v05/Sasha_v05_006.png`: global Lap=717.972, face Lap=126.637, eye=0.000, skin=0.282, plasticity=0.0, openness=0.365784, mouth=0.016712; eligible
- `Sasha_v05/Sasha_v05_007.png`: global Lap=759.109, face Lap=95.713, eye=0.000, skin=4.147, plasticity=0.0, openness=0.340627, mouth=0.011595; eligible

### face_backlit_underexposed

- `Sasha_v04/Sasha_v04_004.png`: global Lap=33.335, face Lap=48.488, eye=0.000, skin=1.567, plasticity=0.0, openness=0.228195, mouth=0.249551; low_visibility;face_backlit_underexposed;face_blurry
- `Sasha_v04/Sasha_v04_005.png`: global Lap=25.432, face Lap=16.167, eye=2.619, skin=0.050, plasticity=52.3, openness=0.307522, mouth=0.302822; face_backlit_underexposed;face_blurry
- `Sasha_v25/Sasha_v25_003.png`: global Lap=5.184, face Lap=35.211, eye=3.926, skin=0.195, plasticity=20.1, openness=0.297654, mouth=0.032156; global_blurry;low_resolution_source;face_backlit_underexposed;face_blurry

### face_blurry

- `Sasha_v01/Sasha_v01_004.png`: global Lap=70.211, face Lap=47.129, eye=4.172, skin=0.038, plasticity=108.4, openness=0.263772, mouth=0.034171; low_resolution_source;face_blurry
- `Sasha_v01/Sasha_v01_008.png`: global Lap=97.97, face Lap=25.687, eye=0.000, skin=0.045, plasticity=0.0, openness=0.206682, mouth=0.132358; low_resolution_source;face_blurry
- `Sasha_v01/Sasha_v01_009.png`: global Lap=99.392, face Lap=28.744, eye=3.692, skin=0.030, plasticity=121.5, openness=0.287629, mouth=0.076096; low_resolution_source;face_blurry

### face_too_small

- `Sasha_v19/Sasha_v19_026.png`: global Lap=420.091, face Lap=112.937, eye=0.000, skin=0.116, plasticity=0.0, openness=0.345027, mouth=0.306623; low_resolution_source;face_too_small
- `Sasha_v19/Sasha_v19_028.png`: global Lap=158.854, face Lap=45.213, eye=0.000, skin=0.886, plasticity=0.0, openness=0.172869, mouth=0.178070; low_resolution_source;face_too_small;face_blurry
- `Sasha_v19/Sasha_v19_029.png`: global Lap=417.949, face Lap=152.471, eye=0.000, skin=0.210, plasticity=0.0, openness=0.273125, mouth=0.131813; low_resolution_source;face_too_small

### face_underexposed

- `Sasha_v04/Sasha_v04_001.png`: global Lap=40.309, face Lap=38.110, eye=3.313, skin=0.126, plasticity=26.4, openness=0.306592, mouth=0.547331; face_underexposed;face_blurry
- `Sasha_v04/Sasha_v04_002.png`: global Lap=35.81, face Lap=56.203, eye=0.000, skin=0.392, plasticity=0.0, openness=0.273510, mouth=0.125757; face_underexposed
- `Sasha_v04/Sasha_v04_003.png`: global Lap=36.451, face Lap=92.874, eye=, skin=, plasticity=, openness=, mouth=; low_visibility;face_underexposed

### global_blurry

- `Sasha_v02/Sasha_v02_001.png`: global Lap=10.36, face Lap=18.635, eye=2.627, skin=0.081, plasticity=32.5, openness=0.343480, mouth=0.342225; global_blurry;face_blurry
- `Sasha_v02/Sasha_v02_002.png`: global Lap=11.269, face Lap=38.118, eye=3.064, skin=0.215, plasticity=14.2, openness=0.373755, mouth=0.141311; global_blurry;face_blurry
- `Sasha_v02/Sasha_v02_003.png`: global Lap=15.088, face Lap=94.287, eye=0.000, skin=2.095, plasticity=0.0, openness=0.217833, mouth=0.150929; global_blurry;low_resolution_source

### hair_covered_face


### low_resolution_source

- `Sasha_v01/Sasha_v01_001.png`: global Lap=98.376, face Lap=113.083, eye=4.629, skin=0.152, plasticity=30.5, openness=0.319774, mouth=0.030753; low_resolution_source
- `Sasha_v01/Sasha_v01_002.png`: global Lap=87.214, face Lap=58.760, eye=4.477, skin=0.095, plasticity=47.1, openness=0.293416, mouth=0.043356; low_resolution_source
- `Sasha_v01/Sasha_v01_003.png`: global Lap=89.623, face Lap=55.160, eye=0.000, skin=0.078, plasticity=0.0, openness=0.316440, mouth=0.023966; low_resolution_source

### low_visibility

- `Sasha_v02/Sasha_v02_013.png`: global Lap=23.883, face Lap=93.836, eye=, skin=, plasticity=, openness=, mouth=; global_blurry;low_resolution_source;low_visibility
- `Sasha_v03/Sasha_v03_017.png`: global Lap=5.041, face Lap=4.115, eye=0.000, skin=0.030, plasticity=0.0, openness=0.380500, mouth=0.015554; global_blurry;low_visibility;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_027.png`: global Lap=8.719, face Lap=7.928, eye=0.000, skin=0.037, plasticity=0.0, openness=0.381710, mouth=0.016958; global_blurry;low_visibility;one_eye_occluded;beauty_filter_detected;face_blurry

### multiple_faces

- `Sasha_v03/Sasha_v03_001.png`: global Lap=5.506, face Lap=10.942, eye=0.000, skin=0.032, plasticity=0.0, openness=0.299351, mouth=0.018094; multiple_faces;global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v43/Sasha_v43_020.png`: global Lap=261.398, face Lap=83.064, eye=, skin=, plasticity=, openness=, mouth=; multiple_faces;low_resolution_source;face_too_small;low_visibility;face_underexposed
- `Sasha_v43/Sasha_v43_022.png`: global Lap=229.681, face Lap=96.781, eye=, skin=, plasticity=, openness=, mouth=; multiple_faces;low_resolution_source;face_too_small;low_visibility;face_underexposed

### no_face

- `Sasha_v03/Sasha_v03_018.png`: global Lap=5.954, face Lap=, eye=, skin=, plasticity=, openness=, mouth=; no_face;global_blurry
- `Sasha_v03/Sasha_v03_030.png`: global Lap=4.718, face Lap=, eye=, skin=, plasticity=, openness=, mouth=; no_face;global_blurry
- `Sasha_v03/Sasha_v03_031.png`: global Lap=4.674, face Lap=, eye=, skin=, plasticity=, openness=, mouth=; no_face;global_blurry

### one_eye_occluded

- `Sasha_v03/Sasha_v03_001.png`: global Lap=5.506, face Lap=10.942, eye=0.000, skin=0.032, plasticity=0.0, openness=0.299351, mouth=0.018094; multiple_faces;global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_002.png`: global Lap=5.56, face Lap=9.817, eye=0.000, skin=0.036, plasticity=0.0, openness=0.302427, mouth=0.004240; global_blurry;one_eye_occluded;face_blurry
- `Sasha_v03/Sasha_v03_003.png`: global Lap=5.999, face Lap=11.404, eye=0.000, skin=0.037, plasticity=0.0, openness=0.290818, mouth=0.009354; global_blurry;one_eye_occluded;face_blurry

### blink_suspected

- `Sasha_v28/Sasha_v28_017.png`: global Lap=32.507, face Lap=15.896, eye=0.000, skin=0.115, plasticity=0.0, openness=0.093180, mouth=0.076906; low_resolution_source;low_visibility;face_blurry
- `Sasha_v56/Sasha_v56_018.png`: global Lap=5.153, face Lap=12.012, eye=0.000, skin=0.069, plasticity=0.0, openness=0.109582, mouth=0.104592; global_blurry;face_blurry

### mouth_open

- `Sasha_v01/Sasha_v01_019.png`: global Lap=80.45, face Lap=33.948, eye=0.000, skin=0.060, plasticity=0.0, openness=0.366542, mouth=0.319123; low_resolution_source;face_blurry
- `Sasha_v02/Sasha_v02_001.png`: global Lap=10.36, face Lap=18.635, eye=2.627, skin=0.081, plasticity=32.5, openness=0.343480, mouth=0.342225; global_blurry;face_blurry
- `Sasha_v02/Sasha_v02_003.png`: global Lap=15.088, face Lap=94.287, eye=0.000, skin=2.095, plasticity=0.0, openness=0.217833, mouth=0.150929; global_blurry;low_resolution_source

### mouth_very_open

- `Sasha_v03/Sasha_v03_028.png`: global Lap=9.403, face Lap=11.947, eye=1.412, skin=0.140, plasticity=10.1, openness=0.356440, mouth=0.406822; global_blurry;face_blurry
- `Sasha_v03/Sasha_v03_059.png`: global Lap=8.03, face Lap=22.961, eye=2.349, skin=0.064, plasticity=36.6, openness=0.403276, mouth=0.552372; global_blurry;face_blurry
- `Sasha_v03/Sasha_v03_070.png`: global Lap=6.704, face Lap=10.215, eye=0.000, skin=0.175, plasticity=0.0, openness=0.643947, mouth=0.516734; global_blurry;one_eye_occluded;face_blurry

