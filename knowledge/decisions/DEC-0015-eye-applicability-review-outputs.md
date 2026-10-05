---
id: DEC-0015
title: Scale-based eye presence and disposable diagnostic review outputs
status: SUPERSEDED
date: 2026-10-03
confidence: MEDIUM
components: [face-quality, configuration, lineage]
tags: [eye-presence, diagnostic-review, disposable-copies]
supersedes: [DEC-0014]
superseded_by: [DEC-0016]
related_experiments: []
related_failures: [FAIL-0002]
related_cases: [CASE-0004]
---

# DEC-0015 — Scoped STEP3 review gaps revision

## Authorization / decision

User explicitly authorized the three-goal implementation and synthetic validation only.
Retain DEC-0014 canonical192 metric/SSOT threshold36.901392 and retained Hard Gate
formulas. Supersede its shot-dependent eye applicability and two-family-only review grouping.
Eye-presence applicability uses available individual measurements and the existing configured
upper-body minimum face dimension, including large FULL_BODY faces. Unreliable/missing
measurements are explicit N/A, never fabricated failure.

Reuse Revision A eye/exposure formulas/settings as official STEP3 diagnostics only.
Eligible rows become review BORDERLINE for EYE_DETAIL+SKIN_PROCESSING or half-eye/blink
or exposure concern; unavailable new exposure measurements remain review concerns, not Hard Rejects. Native blur alone is context. Keep A/B/C/Human Review separate.

Successful complete normal STEP3 materializes disposable PASS/BORDERLINE copies below
configured reports/passed and reports/borderline. Stage and roll back exceptions around
report publication; failed/partial analysis preserves the previous successful review output.
These paths/aliases/staging are excluded from inventories and explicit source input paths.
No source deletion or other report cleanup is authorized.

## Evidence and limits

[CASE-0004](../cases/CASE-0004-large-fullbody-eye-bypass.md) records the observed bypass.
[Implementation](../../docs/STEP3_REVIEW_GAPS_IMPLEMENTATION.md) documents synthetic tests,
shared-formula compatibility and exception rollback. No new production inference or human
accuracy evidence. Power-loss atomicity across files/directories is not guaranteed.
Prior Decision body and production reports remain historical evidence.

## Supplemental Reject-copy authorization

After the user-run STEP3 result, ★maru explicitly requested Reject review copies. A separate existing-result BAT/Python utility copied the recorded Reject subset; no inference/threshold/A/B/C change. Reject copies share disposable output/input-exclusion rules. Normal STEP3 passed/borderline publication ownership remains unchanged. See [copy result](../../docs/STEP3_REJECT_REVIEW_COPY_RESULT.md).
