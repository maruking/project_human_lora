---
id: DEC-0016
title: STEP3 BEST relative ranking and durable three-round review
status: SUPERSEDED
date: 2026-10-04
confidence: MEDIUM
components: [face-quality, configuration, lineage, human-review]
tags: [best-ranking, relative-normalization, supplemental-stills]
supersedes: [DEC-0015]
superseded_by: [DEC-0017]
related_experiments: []
related_failures: [FAIL-0002]
related_cases: [CASE-0004]
---

# DEC-0016 — BEST Candidate Ranking & Review Extraction

## Context and decision

User explicitly cancels STEP3 V2 / complex Tier B reject calibration and requests
BEST ranking of the complete current formal-video plus declared-still universe.
Supersede DEC-0015's main Gate/review control flow, preserve its kernels and all
historical records. Old absolute blur/eye/beauty/skin/exposure thresholds are not
ranking eligibility controls. Minimal fatal detection/analysis/crop failures only.

Measure first, normalize each metric separately within formal_video/still pools,
then rank a visible composite of face detail, visibility, size, contrast/exposure
and concern penalties. Formula/settings/limitations are in
[implementation report](../../docs/STEP3_BEST_RANKING_IMPLEMENTATION.md).
Weights are provisional implementation choices, not validated quality decisions.

Three45-image review rounds use per-video cap4 with minimum recorded relaxation;
all shown frame_ids are durably excluded later. Review copies are disposable and
never production input; history stays outside them. Manual review_reject moves
are human counterexamples, not new fatal predicates or threshold training.
PENDING remains until explicit review; A/B/C and final selection remain separate.

## Facts and interpretation

Fact: user-authorized architecture and synthetic implementation; no production
ranking, real problematic-case audit or Round1 extraction executed by Codex.
Synthetic contract validation does not establish ranking perceptual quality.
Interpretation: balanced relative signals may overcome changed4K scale and
single-metric sharpness bias; actual effectiveness awaits maru/Chappy review.

## Consequences and limitations

Normal03 BAT now invokes BEST; old code/config/official reports remain historical
and untouched. STEP4+ consumer migration is deferred; use standalone BEST BAT.
Single detector confidence/valid geometry is the implemented multiple-face
confirmation boundary, not independent-model corroboration. Missing mesh/detail
reduces contributions, not automatic rejection. Separate pools can rank relatively
poor small pools highly; no guarantee of combined perceptual comparability.
History reservation prevents replay after interruption but requires explicit
recovery of a failed materialization. ACCEPTED history state is representable,
with no new automatic acceptance tool. Full pipeline execution belongs to maru.
