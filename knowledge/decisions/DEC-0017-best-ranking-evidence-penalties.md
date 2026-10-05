---
id: DEC-0017
title: BEST v2 common quality scale and evidence-based ranking penalties
status: SUPERSEDED
date: 2026-10-04
confidence: MEDIUM
components: [face-quality, ranking, human-review, lineage]
tags: [best-rank-v2, semantic-penalties, supplemental-review]
supersedes: [DEC-0016]
superseded_by: [DEC-0018]
related_experiments: []
related_failures: [FAIL-0002]
related_cases: [CASE-0004]
---

# DEC-0017 — BEST Ranking v2

Superseded by [DEC-0018](DEC-0018-version-scoped-best-review.md): scoring below is
retained, but cross-version shown exclusion and direct Round3 progression are
historical. Current v2 Human Review restarts at Round1. Original rationale follows.

User explicitly authorizes correction of percentile-as-defect semantics, not a
return to threshold-heavy rejection. Preserve minimal fatal_reason unchanged.
Supersede DEC-0016 scoring/extraction defaults, retain complete combined input,
immutable images and durable review evidence.

Main positive quality uses a common combined-universe bounded P5/P95 scale for
comparable measurements; visibility uses0..100 directly. Smaller kind-specific
percentile bonuses remain positive only. Default90/10 shares preserve existing
component weights. Exposure receives no kind bonus; native pixel face size becomes
scale-independent face area ratio. Penalties require actual measured deficits or
explicit existing diagnostics. Existing anchors are reused for soft ranking only.
Visibility100 -> zero visibility obstruction; OPEN -> zero half-eye; zero/tiny
clip -> zero clipping. Missing evidence remains unavailable, not maximum defect.

Round review minimum10 unseen stills, then global fill; cap4/video with minimum
reported relaxation. Prior shown IDs remain excluded; Human Reject is unchanged
evidence, never an automatically learned hard predicate or filename-specific rule.

Default BAT rescores compatible stored metrics and stops before review extraction.
At production publication, copy old versioned reports into content-addressed history.
Do not reset Round1/2 history. Round3 refuses v1 and requires explicit extraction
after maru checks v2 summary. Neither production rerank nor Round3 executed here.

Observed: v1 reference score41.002473 with23.853765 unsupported relative penalty
points. Small stored-metric v2 check gives88.436829, penalty0, global rank unknown.
This is not proof of population-wide improvement. External occlusion detection
remains weak (v08 example still high); native local detail comparability and soft
anchors need Human Review. Semantic and synthetic safety tests are evidence of
implementation properties, not confirmed LoRA quality.

See [full formula, evidence and operation](../../docs/STEP3_BEST_RANKING_V2_IMPLEMENTATION.md).
The earlier issue report, v1 code/report copies and review snapshots remain historical.
