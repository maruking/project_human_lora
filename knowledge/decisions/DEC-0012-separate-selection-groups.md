---
id: DEC-0012
title: Separate A B C dataset selection state
status: ACCEPTED
date: 2026-10-02
confidence: MEDIUM
components: [face-quality, selection-review]
tags: [human-review, reserve, diagnostics]
supersedes: []
superseded_by: []
related_experiments: [EXP-20261002-008]
related_failures: []
related_cases: []
---

# DEC-0012 — Separate dataset-selection groups

## Context / previous approach
Official face_eligible does not represent human suitability, and newly measured metrics lack calibrated acceptance thresholds. User explicitly requires a reserve group rather than binary selection.

## Decision / implementation
A CLEAN primary, B BORDERLINE reserve, C REJECT are separate sidecar fields; never rewrite official STEP3 labels. Explicit Human Reject takes precedence and remains C. Human-confirmed A/B is retained. New provisional metrics never confer A or C. Insufficient evidence is B with selection_review_status UNDECIDED and reserve_use_allowed false; confirmed B remains available for later human-assisted coverage balancing.
This accepts the user classification structure, not numeric diagnostic boundaries or LoRA suitability. No pose/angle quota optimization or C rescue.

## Evidence / alternatives
EXP-20261002-008 validates structure/preservation; current138 rows A0/B111/C27. Collapsing B into A/C would lose the user's reserve semantics. Automatic diagnostic finalization is excluded by explicit Revision A scope.

## Consequences / validated conditions
Human priority is preserved and unknowns remain visible. Works for current same-generation review CSV and declared supplemental still inventory; synthetic selection tests cover confirmed B, human priority and no diagnostic promotion.

## Limitations / counterexamples
No human-confirmed A/B examples exist in this run, so all non-Reject records remain provisional. OPEN/NORMAL can miss half-open eyes and v69 quality concerns. The diagnostic bins have no validated physical meaning or training fitness guarantee. Evidence confidence MEDIUM refers to implementation only.
