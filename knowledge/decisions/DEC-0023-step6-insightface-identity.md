---
id: DEC-0023
title: STEP6 v2 InsightFace identity and audited reference gallery
status: ACCEPTED
date: 2026-10-05
confidence: MEDIUM
components: [identity, reference-gallery, lineage]
tags: [insightface, buffalo-l, fixed-boundary, full-row]
supersedes: []
superseded_by: []
related_experiments: []
related_failures: []
related_cases: []
---

# DEC-0023 — STEP6 Identity Verification v2

## Context / legacy audit

User-authorized STEP6 revision follows BEST v2.2, STEP4 stored pose v2 and DEC-0022
STEP5 v2. Legacy evaluate_identity.py uses DINO generic embeddings, dynamic
shot/pose thresholds, center-upper crop fallback, old pose aliases and review copies.
That file remains byte-identical. Its configuration defaults are retained in
config/step6_identity_legacy_dino.json as HISTORICAL_NOT_ACTIVE, never transferred
to InsightFace. No prior separate identity Decision exists to supersede.

## Accepted design

InsightFace buffalo_l detection/recognition processes original references and
candidates through the same five-point alignment/recognition pipeline. References
are explicitly user-confirmed anchors placed in the configured reference directory;
no automatic supplemental/Human Review/top-rank references. No fabricated crop.
Reference audit requires3–20 independently hashed valid images, exactly one face,
finite nonzero embeddings; every reference must agree with its leave-one-out
normalized centroid at the historical configured0.55 boundary. Invalid/outlier
references block production without silently excluding them. Audit phase generates
pairwise/LOO/source/model provenance, CSV/JSON/Markdown/source-linked HTML.
Production remeasures references and checks prior PASS audit hashes, gallery inventory,
model hashes and library versions before any candidate inference.

Centroid: normalize each embedding, average, normalize the average. Individual
anchors retained in memory. Candidate single-face detections use that aligned face;
multiple detections use unique positive maximum IoU against persisted primary bbox,
then REVIEW regardless of similarity. A tie/no-overlap association stops processing
without introducing an arbitrary confidence threshold. Missing/failed embeddings
remain NOT_EVALUABLE, with similarities blank rather than zero.

Fixed historical0.55: centroid>=boundary passes unless ambiguous; centroid below
and maximum anchor above/equal routes REVIEW; both below rejects valid measurement.
Quality scores, review history, pose/scale, filenames and video IDs never alter
embedding similarity or acceptance. identity_state is authoritative; identity_passed
is a compatibility projection, blank for non-applicable rows.

## Lineage / publication

Explicit STEP5 report/summary only, COMPLETE current version/hash/count/IDs,
STEP3/4 generation and inherited columns validated. All source paths exist;
all source bytes verified before production candidate inference, target bytes and
dimensions rechecked on decode. Default targets UNIQUE/REPRESENTATIVE only.
Duplicate members and fatal/upstream/error rows survive without copied identity
results. Rejected/not-evaluable representatives flag cluster fallback need;
no alternative is automatically evaluated/promoted. Full row/column invariants checked.

Outputs prepared before publication, per-file atomic replace, archived prior files,
completion summary last, rollback on caught filesystem failure. Process crash is
not an all-file transaction; artifact hashes expose interruption. Partial/error
runs publish to isolated audit paths, never replace successful production reports.
Review HTML is source-linked and is never an image/reference/pipeline input.

## Evidence / limitations

Dedicated Python3.10 .venv-step6 avoids STEP2–5 dependency changes. InsightFace0.7.3,
ORT-GPU1.23.2 and installed NVIDIA DLLs successfully run reference detection and
512-dimensional recognition on RTX4090. Windows PATH/DLL directories are required
for cuDNN sublibraries; runtime disables silent GPU-to-CPU retries. CPU is explicit
or used by auto only when CUDA provider is absent.

Seven user-confirmed references pass real GPU reference-only audit; LOO minimum
approximately0.66275, maximum0.76238. Synthetic tests validate state boundaries,
association, reference failures, full rows, partial publication and rollback.
No production candidate identity execution, FAR/FRR/impostor benchmark or general
accuracy claim. STEP7+, upstream reports, review history, A/B/C and sources unchanged.
Runner still stops after STEP5; STEP6 has its independent two-phase BAT path.

[Implementation](../../docs/STEP6_IDENTITY_V2_IMPLEMENTATION.md),
[current Knowledge](../current/identity-evaluation.md).
