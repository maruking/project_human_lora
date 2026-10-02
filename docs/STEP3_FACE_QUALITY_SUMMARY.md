# STEP3 Face Quality Summary

Status: PASS; rows: 1893; eligible: 1; errors: 0

Regenerated solely from STEP3 CSV values. Source SHA256: de7d772bba8017fb4079698864539ab274452347db74ecf3e8624454d129523d

All STEP2 values retained. Reasons overlap; primary categories are exclusive. Rejected includes error rows.
Face percentiles use successful single-face rows (historical midrank formula). shot_type is provisional face scale, not STEP4 pose/composition.
Geometric blink and mouth bins are provisional diagnostics, not validated blink/expression/speech labels and never rejection gates.
Beauty/filter and occlusion outputs are heuristic flags, not verified causes. FULL_BODY bypasses beauty rejection. Missing metrics are blank, not measured zero.

## Detection and eligibility

```json
{
  "frame_count": 1893,
  "eligible_count": 1,
  "eligible_ratio": 0.000528,
  "rejected_count": 1892,
  "analysis_error_count": 0,
  "no_face_count": 69,
  "face_detected_count": 1824,
  "single_face_count": 1823,
  "multiple_faces_count": 1,
  "facemesh_detected_count": 1645,
  "blink_suspected_count": 2,
  "mouth_open_count": 345,
  "mouth_very_open_count": 90,
  "beauty_fullbody_skipped_count": 750
}
```

## Reasons (overlap and exclusive categories)

| Type | Reason | Frames | % | Videos |
|---|---|---:|---:|---:|
| overlapping_reason | analysis_error | 0 | 0.0 | 0 |
| overlapping_reason | beauty_filter_detected | 939 | 49.603803 | 57 |
| overlapping_reason | eligible | 1 | 0.052826 | 1 |
| overlapping_reason | face_backlit_underexposed | 31 | 1.637612 | 5 |
| overlapping_reason | face_blurry | 1823 | 96.302166 | 67 |
| overlapping_reason | face_too_small | 0 | 0.0 | 0 |
| overlapping_reason | face_underexposed | 167 | 8.821976 | 16 |
| overlapping_reason | global_blurry | 1806 | 95.40412 | 65 |
| overlapping_reason | hair_covered_face | 0 | 0.0 | 0 |
| overlapping_reason | low_resolution_source | 0 | 0.0 | 0 |
| overlapping_reason | low_visibility | 205 | 10.829371 | 35 |
| overlapping_reason | multiple_faces | 1 | 0.052826 | 1 |
| overlapping_reason | no_face | 69 | 3.645008 | 19 |
| overlapping_reason | one_eye_occluded | 607 | 32.065504 | 56 |
| exclusive_primary_category | ELIGIBLE | 1 | 0.052826 | 1 |
| exclusive_primary_category | REJECT_BEAUTY_FILTER | 938 | 49.550977 | 57 |
| exclusive_primary_category | REJECT_BLUR | 553 | 29.21289 | 48 |
| exclusive_primary_category | REJECT_LOW_RES | 0 | 0.0 | 0 |
| exclusive_primary_category | REJECT_MULTIPLE_FACE | 1 | 0.052826 | 1 |
| exclusive_primary_category | REJECT_NO_FACE | 69 | 3.645008 | 19 |
| exclusive_primary_category | REJECT_OCCLUSION | 331 | 17.485473 | 46 |
| exclusive_primary_category | REJECT_SMALL_FACE | 0 | 0.0 | 0 |
| exclusive_primary_category | REVIEW_UNKNOWN | 0 | 0.0 | 0 |

## STEP2 × STEP3

Top/bottom 10% use stored quality_rank with ceil(N × 0.10), ties already ordered by STEP2.
```json
{
  "global_top_10_percent": {
    "frame_count": 190,
    "eligible_count": 1,
    "eligible_ratio": 0.005263,
    "rejected_count": 189,
    "analysis_error_count": 0,
    "no_face_count": 9,
    "face_detected_count": 181,
    "single_face_count": 181,
    "multiple_faces_count": 0,
    "facemesh_detected_count": 152,
    "blink_suspected_count": 0,
    "mouth_open_count": 41,
    "mouth_very_open_count": 4,
    "beauty_fullbody_skipped_count": 82,
    "face_blurry_count": 180,
    "beauty_filter_count": 39
  },
  "global_bottom_10_percent": {
    "frame_count": 190,
    "eligible_count": 0,
    "eligible_ratio": 0.0,
    "rejected_count": 190,
    "analysis_error_count": 0,
    "no_face_count": 18,
    "face_detected_count": 172,
    "single_face_count": 172,
    "multiple_faces_count": 0,
    "facemesh_detected_count": 160,
    "blink_suspected_count": 0,
    "mouth_open_count": 27,
    "mouth_very_open_count": 3,
    "beauty_fullbody_skipped_count": 111,
    "face_blurry_count": 172,
    "beauty_filter_count": 58
  }
}
```

## Video concentration

| Video | Frames | Eligible | Ratio | No face | Multiple | Errors |
|---|---:|---:|---:|---:|---:|---:|
| Sasha_v01 | 19 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v03 | 120 | 0 | 0.0 | 14 | 1 | 0 |
| Sasha_v04 | 23 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v05 | 32 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v06 | 19 | 0 | 0.0 | 2 | 0 | 0 |
| Sasha_v07 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v08 | 20 | 0 | 0.0 | 5 | 0 | 0 |
| Sasha_v09 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v10 | 26 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v11 | 28 | 0 | 0.0 | 6 | 0 | 0 |
| Sasha_v12 | 24 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v13 | 26 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v14 | 29 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v15 | 24 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v16 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v17 | 26 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v19 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v20 | 20 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v21 | 29 | 0 | 0.0 | 5 | 0 | 0 |
| Sasha_v22 | 37 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v23 | 20 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v24 | 28 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v25 | 29 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v26 | 24 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v27 | 26 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v28 | 29 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v29 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v30 | 27 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v31 | 29 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v32 | 21 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v33 | 33 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v34 | 15 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v35 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v36 | 39 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v37 | 18 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v38 | 27 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v39 | 39 | 0 | 0.0 | 5 | 0 | 0 |
| Sasha_v40 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v41 | 19 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v42 | 20 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v44 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v45 | 23 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v46 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v47 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v48 | 23 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v49 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v50 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v51 | 21 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v52 | 57 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v53 | 30 | 1 | 0.033333 | 0 | 0 | 0 |
| Sasha_v54 | 29 | 0 | 0.0 | 5 | 0 | 0 |
| Sasha_v55 | 21 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v56 | 30 | 0 | 0.0 | 3 | 0 | 0 |
| Sasha_v57 | 44 | 0 | 0.0 | 4 | 0 | 0 |
| Sasha_v58 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v59 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v60 | 20 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v61 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v62 | 22 | 0 | 0.0 | 7 | 0 | 0 |
| Sasha_v63 | 20 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v64 | 30 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v65 | 22 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v66 | 21 | 0 | 0.0 | 1 | 0 | 0 |
| Sasha_v67 | 25 | 0 | 0.0 | 0 | 0 | 0 |
| Sasha_v68 | 30 | 0 | 0.0 | 3 | 0 | 0 |
| Sasha_v70 | 24 | 0 | 0.0 | 3 | 0 | 0 |
| Sasha_v71 | 30 | 0 | 0.0 | 0 | 0 | 0 |

## Distributions

Population std, linear percentiles of stored values; missing includes N/A and errors (not additive categories).

| Metric | Count | Missing | N/A (no face) | Errors | Min | P50 | P90 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| face_laplacian_score | 1824 | 69 | 69 | 0 | 1.811 | 4.735 | 8.6459 | 67.62 |
| face_tenengrad_score | 1824 | 69 | 69 | 0 | 28.963 | 204.8095 | 543.9851 | 5463.593 |
| face_sharpness_score | 1823 | 70 | 69 | 0 | 0.03 | 49.18 | 89.86 | 100.0 |
| eye_sharpness | 1645 | 248 | 69 | 0 | 0.0 | 0.0 | 1.006 | 2.381 |
| mouth_sharpness | 1645 | 248 | 69 | 0 | 0.31 | 0.765 | 1.1866 | 2.17 |
| face_visibility_score | 1824 | 69 | 69 | 0 | 0.0 | 100.0 | 100.0 | 100.0 |
| face_brightness_mean | 1824 | 69 | 69 | 0 | 54.9 | 126.25 | 150.27 | 184.9 |
| face_min_dimension | 1824 | 69 | 69 | 0 | 216.0 | 651.0 | 1138.1 | 1989.0 |
| face_area_ratio | 1824 | 69 | 69 | 0 | 0.00562 | 0.05133 | 0.158273 | 0.53319 |
| skin_texture_score | 1645 | 248 | 69 | 0 | 0.001 | 0.022 | 0.051 | 0.42 |
| plasticity_ratio | 1645 | 248 | 69 | 0 | 0.0 | 0.0 | 46.52 | 145.4 |
| eye_openness_mean | 1645 | 248 | 69 | 0 | 0.090944 | 0.330617 | 0.392446 | 0.830397 |
| mouth_open_ratio | 1645 | 248 | 69 | 0 | 0.000351 | 0.051314 | 0.283234 | 0.638419 |

## Review examples

Examples are audit references only; no selection or verified causal labels.

### analysis_error


### beauty_filter_detected

- `Sasha_v03/Sasha_v03_001.png`: global Lap=2.074, face Lap=4.962, eye=0.000, skin=0.016, plasticity=0.0, openness=0.304805, mouth=0.023015; multiple_faces;global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_002.png`: global Lap=2.468, face Lap=5.491, eye=0.000, skin=0.022, plasticity=0.0, openness=0.304573, mouth=0.002398; global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_003.png`: global Lap=2.673, face Lap=6.186, eye=0.000, skin=0.022, plasticity=0.0, openness=0.289727, mouth=0.009345; global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry

### eligible

- `Sasha_v53/Sasha_v53_004.png`: global Lap=158.925, face Lap=67.620, eye=0.000, skin=0.104, plasticity=0.0, openness=0.308242, mouth=0.262573; eligible

### face_backlit_underexposed

- `Sasha_v04/Sasha_v04_004.png`: global Lap=6.202, face Lap=16.525, eye=0.000, skin=0.420, plasticity=0.0, openness=0.141048, mouth=0.376287; global_blurry;low_visibility;face_backlit_underexposed;face_blurry
- `Sasha_v04/Sasha_v04_005.png`: global Lap=5.146, face Lap=7.342, eye=1.353, skin=0.040, plasticity=33.4, openness=0.291757, mouth=0.351943; global_blurry;face_backlit_underexposed;face_blurry
- `Sasha_v25/Sasha_v25_003.png`: global Lap=1.202, face Lap=6.057, eye=1.169, skin=0.048, plasticity=24.2, openness=0.313608, mouth=0.031887; global_blurry;face_backlit_underexposed;face_blurry

### face_blurry

- `Sasha_v01/Sasha_v01_001.png`: global Lap=3.06, face Lap=4.688, eye=0.000, skin=0.025, plasticity=0.0, openness=0.329130, mouth=0.031902; global_blurry;face_blurry
- `Sasha_v01/Sasha_v01_002.png`: global Lap=3.59, face Lap=4.848, eye=0.000, skin=0.021, plasticity=0.0, openness=0.293566, mouth=0.048901; global_blurry;face_blurry
- `Sasha_v01/Sasha_v01_003.png`: global Lap=3.642, face Lap=4.581, eye=0.000, skin=0.010, plasticity=0.0, openness=0.329330, mouth=0.024823; global_blurry;face_blurry

### face_too_small


### face_underexposed

- `Sasha_v04/Sasha_v04_001.png`: global Lap=6.769, face Lap=7.744, eye=1.778, skin=0.043, plasticity=41.8, openness=0.309756, mouth=0.534775; global_blurry;face_underexposed;face_blurry
- `Sasha_v04/Sasha_v04_002.png`: global Lap=6.543, face Lap=12.821, eye=0.000, skin=0.077, plasticity=0.0, openness=0.256747, mouth=0.120246; global_blurry;face_underexposed;face_blurry
- `Sasha_v04/Sasha_v04_003.png`: global Lap=6.861, face Lap=17.143, eye=, skin=, plasticity=, openness=, mouth=; global_blurry;low_visibility;face_underexposed;face_blurry

### global_blurry

- `Sasha_v01/Sasha_v01_001.png`: global Lap=3.06, face Lap=4.688, eye=0.000, skin=0.025, plasticity=0.0, openness=0.329130, mouth=0.031902; global_blurry;face_blurry
- `Sasha_v01/Sasha_v01_002.png`: global Lap=3.59, face Lap=4.848, eye=0.000, skin=0.021, plasticity=0.0, openness=0.293566, mouth=0.048901; global_blurry;face_blurry
- `Sasha_v01/Sasha_v01_003.png`: global Lap=3.642, face Lap=4.581, eye=0.000, skin=0.010, plasticity=0.0, openness=0.329330, mouth=0.024823; global_blurry;face_blurry

### hair_covered_face


### low_resolution_source


### low_visibility

- `Sasha_v03/Sasha_v03_017.png`: global Lap=2.228, face Lap=2.571, eye=0.000, skin=0.016, plasticity=0.0, openness=0.379612, mouth=0.021249; global_blurry;low_visibility;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_027.png`: global Lap=3.165, face Lap=4.057, eye=0.000, skin=0.021, plasticity=0.0, openness=0.384099, mouth=0.015124; global_blurry;low_visibility;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_071.png`: global Lap=2.91, face Lap=3.381, eye=, skin=, plasticity=, openness=, mouth=; global_blurry;low_visibility;one_eye_occluded;face_blurry

### multiple_faces

- `Sasha_v03/Sasha_v03_001.png`: global Lap=2.074, face Lap=4.962, eye=0.000, skin=0.016, plasticity=0.0, openness=0.304805, mouth=0.023015; multiple_faces;global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry

### no_face

- `Sasha_v03/Sasha_v03_018.png`: global Lap=2.596, face Lap=, eye=, skin=, plasticity=, openness=, mouth=; no_face;global_blurry
- `Sasha_v03/Sasha_v03_030.png`: global Lap=1.719, face Lap=, eye=, skin=, plasticity=, openness=, mouth=; no_face;global_blurry
- `Sasha_v03/Sasha_v03_031.png`: global Lap=1.397, face Lap=, eye=, skin=, plasticity=, openness=, mouth=; no_face;global_blurry

### one_eye_occluded

- `Sasha_v03/Sasha_v03_001.png`: global Lap=2.074, face Lap=4.962, eye=0.000, skin=0.016, plasticity=0.0, openness=0.304805, mouth=0.023015; multiple_faces;global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_002.png`: global Lap=2.468, face Lap=5.491, eye=0.000, skin=0.022, plasticity=0.0, openness=0.304573, mouth=0.002398; global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_003.png`: global Lap=2.673, face Lap=6.186, eye=0.000, skin=0.022, plasticity=0.0, openness=0.289727, mouth=0.009345; global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry

### blink_suspected

- `Sasha_v28/Sasha_v28_017.png`: global Lap=2.199, face Lap=3.853, eye=0.000, skin=0.026, plasticity=0.0, openness=0.094580, mouth=0.088489; global_blurry;low_visibility;face_blurry
- `Sasha_v56/Sasha_v56_018.png`: global Lap=2.848, face Lap=7.012, eye=0.000, skin=0.029, plasticity=0.0, openness=0.090944, mouth=0.172463; global_blurry;face_blurry

### mouth_open

- `Sasha_v01/Sasha_v01_019.png`: global Lap=2.374, face Lap=3.527, eye=0.000, skin=0.013, plasticity=0.0, openness=0.335334, mouth=0.285468; global_blurry;face_blurry
- `Sasha_v03/Sasha_v03_009.png`: global Lap=2.124, face Lap=4.010, eye=0.000, skin=0.021, plasticity=0.0, openness=0.280746, mouth=0.263465; global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry
- `Sasha_v03/Sasha_v03_019.png`: global Lap=2.629, face Lap=3.323, eye=0.000, skin=0.013, plasticity=0.0, openness=0.328127, mouth=0.176573; global_blurry;one_eye_occluded;beauty_filter_detected;face_blurry

### mouth_very_open

- `Sasha_v03/Sasha_v03_028.png`: global Lap=3.389, face Lap=5.985, eye=0.772, skin=0.037, plasticity=21.0, openness=0.367761, mouth=0.398534; global_blurry;face_blurry
- `Sasha_v03/Sasha_v03_059.png`: global Lap=2.497, face Lap=7.451, eye=1.299, skin=0.025, plasticity=51.2, openness=0.405814, mouth=0.539142; global_blurry;face_blurry
- `Sasha_v03/Sasha_v03_070.png`: global Lap=2.492, face Lap=4.347, eye=0.000, skin=0.057, plasticity=0.0, openness=0.635674, mouth=0.539616; global_blurry;one_eye_occluded;face_blurry

