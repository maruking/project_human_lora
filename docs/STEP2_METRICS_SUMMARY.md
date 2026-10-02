# STEP2 Current Generation Metrics

## 1. Dataset Overview

Videos: 71 | Frames: 2001 | Errors: 0 | Status: PASS

Extraction policy: 2 | Requested FPS: 2.0 | Max frames/video: 120

Generation SHA256: `fc2a37abc81e44e456891ac7d268c2dc622255d120c944ac377dbefd491833c2`

Source CSV SHA256: `a133656bf487f1d1c7f1add08e5943420254ca8270c499b3a87ce2a4b5602a63`

CSV-only aggregation; no image decoding, metric/rank recalculation or selection. STEP1/STEP2 metadata and per-video counts agree.

## 2. Overall Distribution

| metric | count | min | p01 | p05 | p10 | p25 | p50 | p75 | p90 | p95 | p99 | max | mean | std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| laplacian_score | 2001 | 1.266 | 2.684 | 4.075 | 5.598 | 9.501 | 27.021 | 97.97 | 244.22 | 632.503 | 938.078 | 1806.418 | 104.030712 | 202.859328 |
| tenengrad_score | 2001 | 39.76 | 145.393 | 271.564 | 387.196 | 607.995 | 1490.21 | 3561.73 | 7037.714 | 11229.839 | 19061.795 | 23652.552 | 2876.382042 | 3695.455814 |
| brightness_mean | 2001 | 43.965 | 86.403 | 101.068 | 108.465 | 121.825 | 136.231 | 147.421 | 157.766 | 163.286 | 171.155 | 198.438 | 134.112721 | 19.723751 |
| brightness_std | 2001 | 26.439 | 30.316 | 35.766 | 40.38 | 48.987 | 56.249 | 63.157 | 66.924 | 70.722 | 92.093 | 93.83 | 55.525243 | 10.956325 |
| shadow_pixel_ratio | 2001 | 0.0 | 0.0 | 0.004 | 0.008 | 0.019 | 0.039 | 0.083 | 0.138 | 0.178 | 0.348 | 0.605 | 0.063333 | 0.076475 |
| highlight_pixel_ratio | 2001 | 0.0 | 0.0 | 0.0 | 0.0 | 0.003 | 0.017 | 0.034 | 0.067 | 0.088 | 0.127 | 0.247 | 0.02542 | 0.030044 |
| contrast_p90_p10 | 2001 | 57.0 | 69.0 | 89.0 | 100.0 | 128.0 | 149.0 | 168.0 | 182.0 | 193.0 | 213.0 | 221.0 | 146.261319 | 30.772103 |

Percentiles use NumPy linear interpolation of stored values; std is population std (ddof=0). Aggregates are rounded to 6 decimals; source metrics keep their existing precision.

## 3. Video-Level Overview

### Lowest Median Technical Quality Videos

| video_id | frame_count | laplacian_median | tenengrad_median | technical_median_rank | bottom_10pct_count |
| --- | --- | --- | --- | --- | --- |
| Sasha_v52 | 57 | 3.058 | 195.33 | 71 | 57 |
| Sasha_v56 | 30 | 3.767 | 200.3955 | 70 | 29 |
| Sasha_v21 | 29 | 4.452 | 354.13 | 69 | 27 |
| Sasha_v59 | 30 | 5.412 | 422.7645 | 68 | 14 |
| Sasha_v03 | 120 | 6.515 | 455.51 | 67 | 44 |
| Sasha_v70 | 24 | 8.3585 | 454.436 | 66 | 3 |
| Sasha_v57 | 44 | 7.16 | 473.6105 | 65 | 7 |
| Sasha_v30 | 27 | 7.062 | 487.764 | 64 | 7 |
| Sasha_v10 | 26 | 8.1205 | 547.0135 | 63 | 2 |
| Sasha_v50 | 30 | 8.451 | 565.673 | 62 | 0 |

### Highest Median Technical Quality Videos

| video_id | frame_count | laplacian_median | tenengrad_median | technical_median_rank | bottom_10pct_count |
| --- | --- | --- | --- | --- | --- |
| Sasha_v53 | 30 | 924.775 | 17632.18 | 1 | 0 |
| Sasha_v23 | 20 | 651.645 | 18812.069 | 2 | 0 |
| Sasha_v67 | 25 | 877.138 | 12416.462 | 3 | 0 |
| Sasha_v05 | 32 | 751.875 | 11774.2195 | 4 | 0 |
| Sasha_v08 | 20 | 650.5625 | 8718.348 | 5 | 0 |
| Sasha_v32 | 21 | 342.461 | 10798.007 | 6 | 0 |
| Sasha_v60 | 20 | 385.8055 | 6866.8715 | 7 | 0 |
| Sasha_v19 | 30 | 266.8905 | 6929.7065 | 8 | 0 |
| Sasha_v13 | 26 | 187.5555 | 7779.423 | 9 | 0 |
| Sasha_v63 | 20 | 188.845 | 6586.256 | 10 | 0 |

### Videos With Highest Bottom-10% Concentration

| video_id | frame_count | bottom_10pct_count | bottom_10pct_ratio |
| --- | --- | --- | --- |
| Sasha_v52 | 57 | 57 | 1.0 |
| Sasha_v56 | 30 | 29 | 0.966667 |
| Sasha_v21 | 29 | 27 | 0.931034 |
| Sasha_v59 | 30 | 14 | 0.466667 |
| Sasha_v03 | 120 | 44 | 0.366667 |
| Sasha_v30 | 27 | 7 | 0.259259 |
| Sasha_v57 | 44 | 7 | 0.159091 |
| Sasha_v49 | 30 | 4 | 0.133333 |
| Sasha_v48 | 23 | 3 | 0.130435 |
| Sasha_v70 | 24 | 3 | 0.125 |

Video technical median percentile is the average of the Laplacian and Tenengrad median percentiles across videos. Each median percentile indexes sorted unique video medians from 0 to 100 (singleton/all-equal = 100). Diagnostic ranks descend these values; ties use natural video_id order. Ratios are fractions (1 = 100%). No existing frame ranking changes.

## 4. Global Percentile Distribution

| bucket | frame_count | percentage | video_count |
| --- | --- | --- | --- |
| bottom_1_percent | 21 | 1.049475 | 6 |
| bottom_5_percent | 101 | 5.047476 | 11 |
| bottom_10_percent | 201 | 10.044978 | 14 |
| percentile_10_25 | 300 | 14.992504 | 28 |
| percentile_25_50 | 500 | 24.987506 | 43 |
| percentile_50_75 | 500 | 24.987506 | 45 |
| percentile_75_90 | 299 | 14.942529 | 23 |
| top_10_percent | 201 | 10.044978 | 12 |
| top_5_percent | 101 | 5.047476 | 6 |
| top_1_percent | 21 | 1.049475 | 4 |

Tail membership uses the saved global quality_rank (1 = highest), with ceil(N * percentage / 100) frames at each tail. The 1/5/10% tails are cumulative and overlap; do not add them. Middle bands exclude both 10% tails and divide at ceil(N * 25/50/75%). On tiny datasets tails may overlap. Stored filename tie-breaks can split equal scores. These are diagnostic counts, not rejection rules.

### Absolute Laplacian Histogram (diagnostic only)

| bucket | frame_count | percentage | video_count |
| --- | --- | --- | --- |
| [0, 5) | 163 | 8.145927 | 13 |
| [5, 10) | 361 | 18.04098 | 29 |
| [10, 20) | 330 | 16.491754 | 34 |
| [20, 40) | 323 | 16.141929 | 29 |
| [40, 80) | 215 | 10.744628 | 32 |
| [80, 160) | 328 | 16.391804 | 26 |
| [160, 320) | 117 | 5.847076 | 13 |
| 320+ | 164 | 8.195902 | 9 |

Intervals are lower-inclusive/upper-exclusive. Histogram boundaries are not Gate thresholds.

## 5. Exposure Distribution

| metric | p05 | p25 | p50 | p75 | p95 |
| --- | --- | --- | --- | --- | --- |
| brightness_mean | 101.068 | 121.825 | 136.231 | 147.421 | 163.286 |

| metric | p50 | p90 | p95 | p99 | max |
| --- | --- | --- | --- | --- | --- |
| shadow_pixel_ratio | 0.039 | 0.138 | 0.178 | 0.348 | 0.605 |
| highlight_pixel_ratio | 0.017 | 0.067 | 0.088 | 0.127 | 0.247 |

| bucket | dataset_cutoff | frame_count | percentage | video_count |
| --- | --- | --- | --- | --- |
| brightness_mean <= P05 | 101.068 | 101 | 5.047476 | 15 |
| brightness_mean >= P95 | 163.286 | 101 | 5.047476 | 13 |
| shadow_pixel_ratio >= P95 | 0.178 | 101 | 5.047476 | 8 |
| shadow_pixel_ratio >= P99 | 0.348 | 21 | 1.049475 | 2 |
| highlight_pixel_ratio >= P95 | 0.088 | 104 | 5.197401 | 12 |
| highlight_pixel_ratio >= P99 | 0.127 | 23 | 1.149425 | 6 |

Exposure tails include ties, so counts can exceed the nominal percentage; P95/P99 groups overlap. Cutoffs come only from this dataset and are not exposure Gates.

## 6. Highest 10 Individual Frames

| filename | laplacian_score | tenengrad_score | quality_rank |
| --- | --- | --- | --- |
| Sasha_v53/Sasha_v53_005.png | 1357.995 | 23652.552 | 1 |
| Sasha_v53/Sasha_v53_022.png | 1312.916 | 23282.417 | 2 |
| Sasha_v53/Sasha_v53_007.png | 1256.792 | 22242.35 | 3 |
| Sasha_v53/Sasha_v53_004.png | 1246.895 | 22114.942 | 4 |
| Sasha_v53/Sasha_v53_006.png | 1167.608 | 21498.824 | 5 |
| Sasha_v53/Sasha_v53_003.png | 1114.828 | 21091.617 | 6 |
| Sasha_v53/Sasha_v53_015.png | 1141.421 | 20453.379 | 7 |
| Sasha_v53/Sasha_v53_019.png | 1124.58 | 20523.849 | 8 |
| Sasha_v53/Sasha_v53_009.png | 1161.255 | 20055.442 | 9 |
| Sasha_v53/Sasha_v53_008.png | 1125.586 | 19730.357 | 10 |

## 7. Lowest 10 Individual Frames

| filename | laplacian_score | tenengrad_score | quality_rank |
| --- | --- | --- | --- |
| Sasha_v25/Sasha_v25_001.png | 1.266 | 39.76 | 2001 |
| Sasha_v48/Sasha_v48_004.png | 1.545 | 63.841 | 2000 |
| Sasha_v70/Sasha_v70_001.png | 1.827 | 64.772 | 1999 |
| Sasha_v48/Sasha_v48_003.png | 1.837 | 66.857 | 1998 |
| Sasha_v70/Sasha_v70_002.png | 2.092 | 71.662 | 1997 |
| Sasha_v52/Sasha_v52_031.png | 2.308 | 128.561 | 1996 |
| Sasha_v52/Sasha_v52_032.png | 2.357 | 126.882 | 1995 |
| Sasha_v52/Sasha_v52_042.png | 2.417 | 129.764 | 1994 |
| Sasha_v52/Sasha_v52_057.png | 2.67 | 108.717 | 1993 |
| Sasha_v52/Sasha_v52_052.png | 2.409 | 137.454 | 1992 |

## 8. Interpretation

- These are whole-frame global technical diagnostics.
- Face quality, identity quality and LoRA candidate selection require later evaluation.
- STEP3 must evaluate facial regions separately; no Gate was changed.
- Background, hair, clothing, resolution and compression can affect gradients.
- A low median or concentrated tail suggests where to inspect; it does not authorize deletion.
- STEP2 blur flag count remains unconfigured (null); no threshold is invented.

## 9. Files

Source: step2_dataset_report.csv and step2_summary.json. Generated: step2_video_summary.csv, step2_distribution_summary.csv, and this Markdown. Full paths are printed by the generator; CLI overrides may relocate outputs.
