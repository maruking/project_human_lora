---
id: EXP-20261002-005
title: STEP3 Full-Generation Face Gate Audit
date: 2026-10-02
hypothesis_status: VALIDATED
confidence: MEDIUM
components: [face-quality, data-lineage]
related_decisions: [DEC-0002, DEC-0003, DEC-0006, DEC-0011]
related_failures: [FAIL-0002]
related_cases: []
---

# STEP3 Full-Generation Face Gate Audit

## Objective and setup
Validate deterministic full-row audit under unchanged existing Gates, not face-quality
precision/recall. Current STEP1 generation: 71 videos, 2001 PNG, policy2, 2 FPS.
Windows/Python3.10.11; isolated MediaPipe0.10.21, NumPy1.26.4, OpenCV4.11.0.
Command: `bat\03_face_quality_gate.bat`; CSV-only replay:
`py -3.10 scripts/build_step3_reports.py`.

## Measured facts
2001 processed/successful rows, errors0; all36 STEP2 columns unchanged; missing/duplicate0.
Face detected1924; noface77; single1921; multiple3; FaceMesh1719.
Eligible62 (3.10%), rejected1939. Face_blurry1691; global_blurry953;
one_eye_occluded595; beauty_flag459; visibility241; underexposed218.
Blink2; mouth open358/very_open90; FULL_BODY beauty rejection skipped807.
Global top10%: eligible43/reject158; face_blurry102 and beauty_flag14.
Bottom10%: eligible0/reject201. Eligible15videos; zero-eligible56.
Two full runs produce identical CSV and derived report bytes. Old Gate block matches
all2001 eligibility/reasons/ranks. Original kernel ASTs match; 94 tests PASS.

## Human evaluation and interpretation
No annotated visual accuracy study. Flags are proxies, not proof of blur/filter causality.
Blink/mouth bins are unvalidated diagnostic geometry; never Gates. Current rejection
rate and concentration need human review, not silent tuning. Historical 3607-frame
benchmark and 70/15 thresholds were not revalidated or numerically converted.

## Actions
Implementation/lineage validated; Gate values unchanged; Revision2 review ready.
No new ADR, Failure or Case without new policy or annotated counterexample.
See [result](../docs/STEP3_RESULT.md), [Gate audit](../docs/STEP3_GATE_AUDIT.md),
[human summary](../docs/STEP3_FACE_QUALITY_SUMMARY.md).
