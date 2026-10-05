---
id: EXP-20261002-008
title: STEP3 Revision A diagnostics and selection sidecar
date: 2026-10-02
hypothesis_status: INCONCLUSIVE
confidence: MEDIUM
components: [face-quality, selection-review]
tags: [eye-openness, exposure, face-detail, lineage]
related_decisions: [DEC-0012]
related_failures: []
related_cases: []
---

# EXP-20261002-008

Scope correction: the facts below describe the historical138-row run only. User requires ALL formal frames + supplemental images and maru-owned execution. Corrected code is prepared, not executed; old test/replay results do not establish corrected full-input success. See [Maru instructions](../docs/STEP3_REVISION_A_MARU_RUN.md).

## Objective / setup
Measure eyes, clipping and face detail without changing official STEP3. Windows/Python3.10.11, isolated MediaPipe0.10.21/OpenCV4.11/numpy1.26.4. Run `bat\03_revision_a_diagnostics.bat`; separate provisional config, no tuning. 81 formal diagnostic frames and57 supplemental originals; full formal2,001-generation audit precedes inference.

## Facts
138 unique output rows,0 errors; A0/B111 provisional undecided/C27 human reject. Half-eye examples present3; v69 frames26 present and C. BAT repeated identical bytes.123 unit checks PASS;3,259 protected pre-existing files unchanged by SHA256.

## Human evidence / interpretation
v05_013 eye min0.310626 remains OPEN despite human half-open concern. v69 exposure NORMAL20 and detail NORMAL15. Numeric states are incomplete evidence and must not override human labels. Diagnostic accuracy/LoRA suitability is INCONCLUSIVE; no new human review or Chappy answer claimed.

## Actions / result
Separate A/B/C preservation policy DEC-0012 accepted. No threshold tuning, auto rescue/reject, quotas or STEP4. Detailed counts, inputs and artifact links in [Revision A result](../docs/STEP3_REVISION_A_RESULT.md). Integrity and determinism verified; accuracy not established. No discarded-method Failure record warranted.
