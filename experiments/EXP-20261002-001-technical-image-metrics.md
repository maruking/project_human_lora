---
id: EXP-20261002-001
title: STEP2 Metric Formula, Provenance and Replay Validation
date: 2026-10-02
hypothesis_status: VALIDATED
confidence: HIGH
components: [technical-metrics, reporting]
tags: [regression, deterministic, provenance]
related_decisions: [DEC-0008]
related_failures: [FAIL-0002]
related_cases: [CASE-0002, CASE-0003]
---

# Experiment Record: EXP-20261002-001

## Objective and hypothesis
Verify that additional provenance/reporting preserves existing numeric metrics,
tracks every current frame, and produces deterministic snapshots. This experiment
does not test perceptual face quality or justify a new rejection threshold.

## Setup
Windows, Python 3.10, OpenCV 4.12 and NumPy 2.2.3, CPU only. 71 normalized videos,
3,550 recovered PNG frames using unchanged STEP1 settings (50, trim 0.5 seconds).
Effective paths come from private config; the template stays generic.

```cmd
bat\02_technical_metrics.bat
py -3.10 -m unittest discover -s tests -q
```

The complete run was repeated. Private audit preserves the pre-STEP2 scorer,
compares all legacy fields across every image and hashes the three output files.

## Measured facts
- Initially 58 alternate images occupied the configured root; STEP1 alignment failed.
- Prior PNGs were absent, while all 71 normalized videos remained. Recovery to a
  separate configured root retained the alternate images and prior ID mapping.
- 3,550 records/unique IDs; 71 directories, 50 each; decode failures 0.
- Full old-scorer comparison: 3,550 images, 13 fields, zero differences.
- Repeated CSV/JSON/outlier CSV bytes match; all measured PNG hashes/sizes/mtimes match.
- All 71 original/copy hashes and baseline hash match; 58 alternate files retained.
- 45 tests pass; compact distributions are in docs/STEP2_METRICS_SUMMARY.md.

## Human visual evaluation and interpretation
No new perceptual-quality labels were collected. CASE-0003's face/global values
are user-reported historical approximations, not remeasured here. Technical
correctness and replay are validated; no standalone gradient/resolution quality
gate or GoodFace inference follows from these measurements.

## Actions and limitations
DEC-0008, Current metrics policy and HIST-008 record the reporting contract.
Historical baseline remains unchanged. Missing prior PNGs prevent retrospective
byte-identity proof; matching prior sizes is weaker supporting evidence only.
Concurrent source mutation, cross-output crash transactions and STEP3+ inference
were not tested. See docs/STEP2_RESULT.md for output/provenance details.
