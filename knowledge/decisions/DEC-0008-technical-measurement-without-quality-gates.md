---
id: DEC-0008
title: STEP2 Technical Measurement Without Quality Gates
status: SUPERSEDED
date: 2026-10-02
confidence: HIGH
components: [technical-metrics, reporting]
tags: [diagnostics, provenance, compatibility]
supersedes: []
superseded_by: [DEC-0010]
related_experiments: [EXP-20261002-001]
related_failures: [FAIL-0002]
related_cases: [CASE-0002, CASE-0003]
---

# Decision Record: DEC-0008

## Context and previous approach
STEP2 code already measured metrics without filtering. Historical documentation
incorrectly described an 80.0 standalone gate. Its atomic CSV writer also merged
missing historical filenames, so a smaller current input could have extra rows.
Global gradients cannot establish perceptual face focus (FAIL-0002/CASE-0002).

## Decision
Preserve image decoding, gray conversion, Laplacian/Tenengrad/brightness formulas,
rounding, all legacy columns and relative ranks. Add descriptive dimensions,
explicit aliases and STEP1 provenance/completeness checks. Default CSV is a current
input snapshot; keep explicit legacy merge for users needing historical retention.
Separate JSON summary and outlier CSV from the downstream-compatible formal CSV.
All records survive measurement failure; processing_status identifies computation.
Exit nonzero on decoding or completeness failure, never on a diagnostic value.

## Alternatives
Increasing global thresholds, rejecting short_edge<720 or using quality_rank as a
GoodFace gate is rejected: no accepted experimental support. Removing legacy
columns/ranks would break consumers. Keeping stale rows silently in the formal
snapshot would violate the requested one-input/one-record invariant.

## Relation to existing decisions
DEC-0002 remains the historical local-face decision. Its STEP2 coarse-gate wording
is clarified by this decision; STEP3 implementation is not changed or revalidated.
No face-quality threshold is introduced. DEC-0006 loader and DEC-0007 ID mappings
remain authoritative. The validated historical baseline remains untouched.

## Evidence and consequences
EXP-20261002-001 records formula regression, deterministic replay, completeness
and the input-recovery observation. Confidence HIGH covers technical measurement
and provenance only. CASE-0003's reported values remain LOW-confidence evidence.
Default reports drop stale input rows; --retain-missing-records reproduces prior
historical merging and exposes a separate historical count. No new dependency,
identity model, face inference, sampling method or training behavior is introduced.

## Supersession — 2026-10-02
DEC-0010 prohibits the explicit legacy merge path and establishes generation preflight,
failed-run isolation and global/per-video diagnostics. Original rationale and
EXP-20261002-001 evidence are preserved above as history; metric formulas remain.
