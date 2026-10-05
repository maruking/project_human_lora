---
id: DEC-0019
title: Generic per-image eye quality and corroborated BEST v2.1 penalties
status: SUPERSEDED
date: 2026-10-05
confidence: MEDIUM
components: [face-quality, ranking, human-review, lineage]
tags: [best-rank-v21, eye-quality, generic-defect-evidence]
supersedes: [DEC-0018]
superseded_by: [DEC-0020]
related_experiments: []
related_failures: [FAIL-0002]
related_cases: []
---

# DEC-0019 — Generic BEST v2.1

## Context and previous approach

User completed v2 review: 135 shown, 8 Reject. The supplied technical descriptions
identify eye opening/visibility, blur and exposure counterexamples. These labels
are regression evidence, not runtime features. v2's mean eye credit and modest
half-eye penalty allowed positive detail to conceal weak usable-eye evidence.

## Decision and alternatives

Retain v2 absolute-quality + small relative-bonus - evidence-penalty architecture,
unchanged minimal fatal predicates and all numeric configuration values. Evaluate
expected eyes independently. Weaker expected eye and an explicit usability factor
control eye credit. Closed/half-open, same-eye presence/detail agreement and missing
expected measurement have separate outputs. Existing yaw boundary and actual eye
ROI widths provide profile measurement context only. No source quarantine, filename
exception, learned Human Reject feature or new Hard Reject is accepted.

Blur uses geometric agreement of existing actual detail deficits, rather than
the smaller deficit suppressing the penalty. Dark exposure requires low brightness
plus contrast/dynamic-range loss; haze requires high brightness plus both losses.
Existing anchors are reused. Tenengrad/mouth defect scaling is STOPPED/unresolved
because no compatible approved absolute defect anchors exist. No arbitrary cutoff
is added to force specific reviewed images down.

v2 code is preserved byte-for-byte in best_ranking_v2.py, beside preserved v1.
v2.1 review starts at Round1, with v1/v2 history read-only and non-excluding.
Full publication belongs to ★maru, using existing BAT/Python paths.

## Facts and interpretation

Facts: 87 BEST tests plus 8 configuration tests PASS; BAT --help PASS. Twelve
stored-metric examples scored only; no inference/full population ranking. Four
eye cases lose roughly6-14 points; the clean reference stays88.437 ->88.409.
Current dark/haze examples do not support an exposure penalty under existing
measurements. v05 eye extraction is recorded measured, so suspected failure cannot
be asserted from those values. Full real-world ranking quality remains unvalidated.

Interpretation: scoring invariants and explanation have improved. Detector truth,
physical blur comparability and LoRA suitability are not established by this check.
Weak presence/detail can arise from blur or closure, not necessarily hair.

## Validation boundary and consequences

No production ranking, candidate extraction, source mutation, historical decision
change, A/B/C or STEP4+ work. Version changes archive active old reports at future
user publication and append a new history bucket without rewriting old buckets.
Per-file replacement remains nontransactional across files. Profile ROI projection
is provisional; ambiguous side abstains. Missing stays blank, not observed zero.
Human preference-only makeup/upward poses remain manual decisions.

See [implementation, formulas and limits](../../docs/STEP3_BEST_RANKING_V21_IMPLEMENTATION.md)
and [small regression evidence](../../docs/STEP3_BEST_RANKING_V21_REGRESSION.json).
