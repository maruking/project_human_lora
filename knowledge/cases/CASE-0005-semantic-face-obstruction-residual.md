---
id: CASE-0005
title: Semantic facial obstruction can evade visual geometry quality metrics
date: 2026-10-05
confidence: LOW
components: [face-quality, candidate-selection]
tags: [semantic-occlusion, residual, human-evidence]
related_experiment: []
related_decision: DEC-0025
related_failure: []
---

# CASE-0005 — Semantic facial obstruction residual

## Input / source / facts

The user's STEP7 v2.1 request reports a residual issue: current STEP3 visual and
geometry metrics can miss a hand/object obstructing important central facial features.
The semantic-obstruction exemplar's frame_id, image hash and independent human
annotation are not supplied in this request. No image inspection or semantic
inference was performed here. Individual metrics/resolution are unavailable for
that exemplar; do not fabricate them or bind it to a named frame by assumption.

Separately, the prior STEP7 patch report documents Sasha_v03/Sasha_v03_070.png,
global_rank730, as deep coverage rescue evidence. That proves the coverage-depth
problem, not semantic obstruction of that specific image.

## Expected / observed / interpretation

Important central facial features should remain assessable in final training review.
Stored sharpness/geometry scores alone cannot establish semantic unobstructedness.
The reported counterexample is human evidence with LOW confidence and incomplete
image linkage, not measured detector accuracy or an approved threshold.

## Action / residual work

Record the generic limitation in Current Knowledge. No blacklist, new obstruction
detector, STEP3 formula/threshold change or source deletion. STEP7 v2.1 bounds
coverage search but does not solve semantic occlusion. Future explicitly scoped
post-pipeline work could examine hand-to-face overlap, semantic object/face overlap
and landmark-region obstruction with labeled counterexamples. Identity/quality
claims require further evidence; STEP8 remains human final authority.

[STEP7 implementation](../../docs/STEP7_CANDIDATE_V21_IMPLEMENTATION.md),
[previous coverage regression report](../../docs/STEP7_CURRENT_VERSION_REJECT_PATCH.md).
