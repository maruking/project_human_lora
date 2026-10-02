> HISTORICAL / STALE for current frames: this report describes the previous fixed-count generation. STEP1 Revision 2 now records variable actual counts (2,001 in the latest run). Current-generation STEP2 metrics have not been run. Prior outputs are preserved in the private revision audit; run STEP2 on STEP1 actual counts before STEP3.

# STEP2 Metrics Summary

Diagnostic measurement only; PASS is not a face/LoRA quality classification.
Input: 71 videos, 3,550 PNG frames, 50 each; computed 3,550, failed 0.
Configured execution root: `work/frames_step1` (original alternate images retained).

## Distribution

| Metric | min | p25 | median | p75 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| width | 464.0 | 576.0 | 720.0 | 1080.0 | 1080.0 |
| height | 772.0 | 1024.0 | 1280.0 | 1920.0 | 1920.0 |
| short_edge | 464.0 | 576.0 | 720.0 | 1080.0 | 1080.0 |
| long_edge | 772.0 | 1024.0 | 1280.0 | 1920.0 | 1920.0 |
| pixel_count | 393472.0 | 589824.0 | 921600.0 | 2073600.0 | 2073600.0 |
| mean_brightness | 43.965 | 121.7475 | 135.571 | 146.77925 | 194.282 |
| global_laplacian | 1.285 | 12.209 | 32.2545 | 105.766 | 1447.088 |
| global_tenengrad | 39.31 | 783.74625 | 1671.9645 | 3721.34225 | 24462.748 |


Metric columns retain three decimals; quartiles use linear interpolation of stored
values. Resolution values and buckets describe the inventory and do not reject images.

## Short-edge buckets

| Short edge (diagnostic only) | Frames |
| --- | ---: |
| short_edge_lt720 | 1250 |
| short_edge_720_to1079 | 650 |
| short_edge_ge1080 | 1650 |


## Resolution inventory

| Width | Height | Frames |
| ---: | ---: | ---: |
| 464 | 848 | 50 |
| 540 | 960 | 300 |
| 540 | 972 | 50 |
| 576 | 772 | 100 |
| 576 | 1024 | 700 |
| 576 | 1040 | 50 |
| 720 | 1280 | 650 |
| 1080 | 1450 | 50 |
| 1080 | 1920 | 1600 |


## Diagnostic outliers

`output/reports/step2_diagnostic_outliers.csv` contains five groups of 20:
Laplacian highest/lowest, brightness darkest/brightest, and smallest pixel counts.
Rows retain video_id, frame_id and relative_path for inspection. Overlap is expected.
No HTML viewer, face inference or quality gate is introduced. Global edges may be
high in images with soft faces due to backgrounds, texture, compression or pixelation.

See [STEP2_RESULT](STEP2_RESULT.md) for regression, replay and input recovery.
