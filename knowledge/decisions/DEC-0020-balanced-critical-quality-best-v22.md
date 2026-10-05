---
id: DEC-0020
title: Balanced critical face quality in BEST v2.2
status: ACCEPTED
date: 2026-10-05
confidence: MEDIUM
components: [face-quality, ranking, human-review, lineage]
tags: [best-v22, balanced-quality, measurement-reliability]
supersedes: [DEC-0019]
superseded_by: []
related_experiments: []
related_failures: [FAIL-0002]
related_cases: []
---

# DEC-0020 — Balanced BEST v2.2

## Context and previous approach

User reviewed v2.1 135 images and rejected4. Existing eye concerns could be
compensated by additive sharpness/exposure/visibility credit. Very weak canonical
face detail could have a tiny blur penalty when a local eye edge remained strong.
A suspected measurement failure and visually reported haze lacked conclusive
stored evidence. These are three different problems, not one weighting failure.

## Decision and alternatives

Keep all numeric SSOT settings and fatal predicates. The chosen score is
`base_quality * critical_face_quality - remaining_geometry_penalty`, where
critical quality is the equal geometric mean of eye/detail/exposure/reliability.
No new scalar strength, hard Gate or source/review feature is introduced.

Alternative `100*sqrt(base/100*critical)-geometry` was calculated on9 stored
examples only. It pulls severe critical loss back toward a high score (e.g.
current blur example45.149 vs alternative67.193), so the simple product is chosen.
No target rank or file-specific tuning was used. Additive compensation/minimum
axis selection were not chosen as the primary critical aggregator.

Eye defects act via the eye factor, failures via reliability; old eye credit
reduction/direct eye penalties are removed. Profile projected ratios use a
continuous ratio against the existing open boundary, avoiding the fixed half-state
jump. This profile assumption is provisional, not proof of natural-eye accuracy.

Global detail uses both actual canonical measurements divided by their existing
positive P95 references, geometrically combined. Local detail is the median of
expected eyes/mouth similarly scaled. Product global*local prevents strong local
edges from restoring poor global quality. This is comparative quality, NOT a
new calibrated physical blur threshold. Detail still influences the positive
sharpness term and critical balance, explicitly documented; no direct blur penalty.

Exposure formula/bins remain the stored v2.1 information-loss model; exposure
loss acts only through its critical factor. Visual haze correction is STOPPED
because stored metrics do not distinguish the human example. Eye ROI truth audit
is also STOPPED at absent per-eye coordinates/landmark provenance; no invented
occlusion or measurement error. Whole-mesh status is reported as a coarse proxy.

Face size saturates at the existing upper-body evaluable size reference. Contrast
credit saturates once contrast AND dynamic range meet the existing normal span;
the existing small contrast bonus remains. Brightness asymmetry's legacy25-point
visibility loss is removed from ranking visibility only; old raw values are kept.
Remaining geometric/detection visibility loss stays explicit.

## Facts, interpretation and limits

Facts:9 stored cases evaluated, no new population ranks, no new image inference.
v08_01163.886→56.208; v08_00462.801→60.255; v19_02458.484→45.149;
v05_00366.085→66.555 (measurement failure not established). Four supplemental
reference cases stay high. 11014645.620→70.458 by generic size/contrast/lighting/
profile changes, not a filename branch.

Interpretation: compensation is reduced and quality axes auditable. Population
quality/LoRA suitability and detector correctness remain unvalidated. P95 scaling
depends on the generation, and geometry-based pose may be inaccurate. Missing
factors stay blank; neutral aggregation placeholders rely on a separate reduced
measurement-coverage factor and are not perfect observed quality.

## History and operational consequences

Version best_rank_v2.2 starts Round1 independently of v1/v2/v2.1 shown decisions.
Old Rejects may appear as intentional regression evidence; not scoring features.
Historical scoring modules/reports/reviews stay readable. Publication copies old
active reports to history only at the next user-run BAT.

Feedback reconciles only active-version disposable copies after hash/path checks:
Reject wins, duplicate candidate removed after persisting decision, and a Reject
moved back to candidate is atomically moved to Reject again. Missing both copies
stays explicit MISSING (no source restoration). Multiple-file crash publication is
not transactional. Old v2.1 duplicate production copies remain untouched in this
implementation task.

Tests use synthetic/temp data; full production and Round1 copies belong to maru.
See [implementation and test result](../../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md).
