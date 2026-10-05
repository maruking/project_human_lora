# HIST-014 — STEP3 Calibration Review

2026-10-02. Revision1's3.10% eligibility was a reproducible Gate result, not labeled
quality accuracy. Revision2 preserves its complete2001-row universe and all source
pixels/settings, adding contributions, conditional threshold CDFs, reason combinations,
blur/eye-state decomposition, counterfactuals and eligibility concentration.

180 unique frames across71 videos, max4/video; available59/60 boundary strata covered.
157 plain face crops,180 full-frame copies and offline label/export HTML produced.
No human labels were filled; no tuning/STEP4. The browser's file:// policy prevented
visual UI verification; fake-DOM/export tests and asset/crop checks verified the artifact.
109 Python tests plus Node export fixture PASS. No new ADR/Failure/Case without labels.

[Experiment](../experiments/EXP-20261002-006-step3-calibration-review.md),
[result](../docs/STEP3_CALIBRATION_RESULT.md),
[historical formula audit](../docs/STEP3_GATE_CALIBRATION_AUDIT.md).
