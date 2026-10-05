---
id: EXP-20261002-006
title: STEP3 Gate Contribution and Human Calibration Package
date: 2026-10-02
hypothesis_status: INCONCLUSIVE
confidence: MEDIUM
components: [face-quality, calibration, data-lineage]
related_decisions: [DEC-0002, DEC-0003, DEC-0006, DEC-0011]
related_failures: [FAIL-0002]
related_cases: []
---

# STEP3 Calibration Review

## Objective/setup
Prepare human-verifiable calibration of the unchanged2001-row Gate universe, not
increase eligibility. Source CSV SHA2562589176c4a2eb22d098a1f97500654cde0e0ce6dfda0873cdeac25893f6b0051.
Command: `py -3.10 scripts/build_step3_calibration.py --target 180 --video-cap 5`.
Windows/Python3.10.11; no new inference/dependencies/server/Gate changes.

## Measured facts
Current face_blurry1691 decomposes into executed eye808 / Laplacian883; concurrent
low predicates764 execute eye branch only. Eye sharpness728 measured,991 disabled,
205 mesh-unavailable,77 noface. Executed eye branch includes585 disabled,10 missing
mesh,213 measured-low. Removing face_blurry reason only adds249 to baseline62;
removing global_blurry adds1, one_eye_occluded adds0, beauty adds8. Counterfactuals
leave dependencies and all source decisions unchanged; none are applied.

Review:180 unique frames,71 videos, max4/video under cap5; close52, upper53, full52,
no-face23. Eligible controls25; top-technical/reject18; all3 multiple-face frames.
59 available boundary strata covered; one stratum empty in data. Plain157 face crops
and180 full-frame copies. All human label fields empty.109 Python tests PASS plus
Node fake-DOM/export schema fixture; full artifact replay and source hash/mtime checked.

## Human evaluation and interpretation
AWAITING HUMAN LABELS. No precision/recall, false-positive/negative rate or new visual
Case established. Browser security blocks file:// agent navigation, so no real-browser
visual QA claimed; assets and JS/control/export behavior verified statically/with fake DOM.
Close/upper face-Laplacian50 lies nearP93; eye-disablement coupling needs human review.
Old70/15 metric prose differs; local pre-SSOT source already matches current kernels/values.
Unknown older runnable implementation/date; no numerical threshold conversion.

## Actions
Calibration package ready; Gate tuning and STEP4 NOT ready. No new ADR/Failure/Case.
[Result](../docs/STEP3_CALIBRATION_RESULT.md),
[formula audit](../docs/STEP3_GATE_CALIBRATION_AUDIT.md),
[offline review](../docs/STEP3_CALIBRATION_REVIEW.html).
