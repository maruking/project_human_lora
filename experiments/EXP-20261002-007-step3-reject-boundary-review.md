---
id: EXP-20261002-007
title: REJECT Only Boundary Calibration Review
date: 2026-10-02
hypothesis_status: VALIDATED
confidence: MEDIUM
components: [face-quality, derived-human-review, data-lineage]
tags: [boundary-sampling, reject-only, long-format-labels]
related_decisions: [DEC-0002, DEC-0003, DEC-0006, DEC-0011]
related_failures: [FAIL-0002]
related_cases: [CASE-0002, CASE-0003]
---

# Experiment Record: EXP-20261002-007

## Objective and Hypothesis
Validate structural REJECT-only boundary sampling and independent Gate answers
under unchanged production data. This hypothesis concerns artifact correctness,
not human acceptability, Gate accuracy or training suitability.

## Setup
Windows/Python3.10.11. Local current STEP3 CSV:2,001 rows from71 videos;
1939 rejected/62 eligible. STEP1 generation policy2,2,001 current PNG.
`py -3.10 scripts/build_step3_boundary_review.py --target 45 --video-cap 3`.
Recorded STEP3 effective settings supply thresholds. Review windows follow the
user instruction; they are sample bands, not new production thresholds.

## Measured Results
45 unique REJECT frames/45 videos, Eligible0;81 Gate memberships,36 duplicate
memberships collapsed. Eye14, face Laplacian16, presence10, skin11, plasticity8,
visibility6, exposure7, face size5, global4. Combined beauty14 unique images.
All requested Gate families represented. Shared memberships slightly exceed some
approximate targets. Every selected image is inside at least one requested window.
Disabled/missing eye proxies do not become measured eye boundary examples.

114 Python tests and new/historical fake-DOM exports pass. Independent Gate labels,
reopen, old namespace isolation and CSV/JSON roundtrip verified using synthetic labels.
45 full copies byte-identical;45 plain crops match existing code.94 active artifact
files identical on replay.3,081 protected file hashes match, including2,001 source
images, config, production code, manifests, BAT and pre-existing STEP3 reports.
Previous180-frame HTML retained byte-for-byte; old CSV/assets/settings untouched.
See [result](../docs/STEP3_BOUNDARY_CALIBRATION_RESULT.md) and
output/reports/step3_boundary_audit/verification.json.

## Human Evaluation
Pending. No actual human labels inspected or applied; no false-positive/negative
claims. Browser file policy blocks visual QA; synthetic DOM does not validate layout.

## Interpretation and Actions
The boundary package is structurally ready for human tolerance labeling. No new
threshold Decision, Failure or Case is warranted. Historical180-frame mode is
superseded for active review. Tuning, automatic application and STEP4 remain deferred.
Per-file publication is atomic; multi-file crash consistency is not transactional.
