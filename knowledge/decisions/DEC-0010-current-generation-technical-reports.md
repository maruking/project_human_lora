---
id: DEC-0010
title: Current Generation Technical Reports
status: ACCEPTED
date: 2026-10-02
confidence: HIGH
components: [technical-metrics, generation-integrity, reporting]
tags: [current-generation, no-stale-rows, diagnostics]
supersedes: [DEC-0008]
superseded_by: []
related_experiments: [EXP-20261002-003, EXP-20261002-004]
related_failures: [FAIL-0002]
related_cases: [CASE-0002, CASE-0003]
---

# Decision Record: DEC-0010

## Context and previous approach
DEC-0008 preserved formulas and made snapshot the default, but explicitly allowed
historical merging and checked completeness after scoring. STEP1 Revision 2 changed
the active generation. Even opt-in stale retention now contradicts the user's
unconditional current-generation contract. This supersession records that change;
it does not introduce another face-quality or global blur decision.

## Decision and implementation
Retain DEC-0008's measurement-only responsibility, formulas, decoding, rounding,
legacy fields and global relative algorithms. Require formal STEP1 CSVs, successful
summary and per-video metadata before scoring. Check total/per-video counts, frame
inventory, grammar, source identity and content hashes. Copy temporal index and
policy/FPS provenance to every row. Recheck the generation before publishing.
Prohibit historical merging through writer/config/CLI. Stage all output; archive
preceding good artifacts separately. Failed computation retains all rows and error
categories in failed audit CSV/JSON and exits nonzero, preserving active successful
artifacts. Add independently computed per-video percentiles/rank. No diagnostic
becomes selection or rejection; no threshold is invented.

## Alternatives
An explicit legacy merge option violates the active report contract. Deleting frames
or rejecting dark/low-resolution images is outside STEP2's authority. A population
percentile rewrite would break compatibility: existing percentiles index sorted
unique metric values, and that definition is preserved.

## Evidence and consequences
Facts: EXP-20261002-003 and docs/STEP2_RESULT.md record unit regressions, production
coverage, old-formula regression, media hashes and deterministic replay.
Interpretation: these validate generation/computation integrity, not face quality.
Hashing adds IO and formal metadata requirements. Ordinary publication errors roll
back; abrupt process/power loss between three atomic replacements is not a multi-file
transaction. Downstream consumers must check generation and counts.

## Validated conditions and limits
Current local STEP1 policy 2: 71 videos, 2,001 PNG; generic synthetic generations,
Unicode Windows paths, corrupted decodes and simulated publication failure.
STEP3+ and historical baseline remain unchanged. CASE-0002/0003 warn against using
global gradients as face suitability. Compression detection is not implemented or
validated here. Existing DEC-0006 config and DEC-0007/0009 STEP1 contracts remain.

## Report Layer Extension — 2026-10-02
Add a separate CSV-only aggregate builder; measurement/generation/rank policy above
remains unchanged. The four human-review layers are raw per-frame CSV, per-video
aggregate CSV, per-metric distribution CSV, and comprehensive Markdown. The existing
measurement JSON remains the provenance/completeness control. No new Decision is
needed for this additive report view; it introduces no scoring or Gate architecture.
Use distribution/video-level patterns for human review before individual examples.

Per-video technical median percentile averages two sorted-unique median percentile
positions across videos; use natural video_id ties for descending diagnostic ranks.
Global tail counts read stored quality_rank and use ceil(N*p/100), with cumulative
counts explicitly labeled. Distribution percentiles interpolate linearly; std is
population std, ddof=0. Exposure tails include ties at dataset percentile cutoffs;
Laplacian histogram bounds describe counts only. No frame is reevaluated or selected.
Source CSV/status/uniqueness/ranks and STEP1/STEP2 counts/policy must agree before
publishing derived reports. EXP-20261002-004 records synthetic/full-data aggregates,
deterministic replay and protected-file/media verification.
