---
id: DEC-0022
title: STEP5 v2 conservative duplicate clusters and BEST representatives
status: ACCEPTED
date: 2026-10-05
confidence: MEDIUM
components: [deduplication, lineage, review]
tags: [step5-v2, cluster-not-delete, phash, best-score]
supersedes: []
superseded_by: []
related_experiments: []
related_failures: []
related_cases: []
---

# DEC-0022 — STEP5 Deduplication v2

## Previous approach and authority

Legacy face_deduplication.py reads old STEP4/face_eligible, recalculates quality
from eye/gradient/exposure heuristics, groups by scene_group, requires shot equality,
substitutes global hash for missing face crop, copies representatives and permits
latest-report fallback. This is not the current BEST/STEP4 contract. The legacy
file is retained byte-identical; its deterministic DCT pHash kernel is reused.
There was no separate STEP5 Decision to supersede in the ledger.

★maru's implementation request freezes duplicate clustering and representative
annotation, not quality evaluation, identity, pose quotas, pruning or final selection.
Full STEP4 v2 input survives; only ranking_eligible=true is analyzed. Fatal rows
remain NOT_APPLICABLE_STEP3_FATAL. No Human Review/identity/source-name exception.

## Accepted design

Exact SHA256 byte identity creates edges across filenames/kinds/sources after
source-integrity/decode checks. Near edges require measured raw yaw/pitch, valid
global pHash and permitted source context. Same-video temporal uses index gap,
angle and global OR face hash; same-video tight has no time requirement. Stills
require tight angle AND global AND face hash. Different videos and video/still
have exact-only matching; the declared supplemental universe permits still-to-still
comparison while preserving individual source provenance. Missing face hash stays
MISSING; missing pose permits exact only. No category equality or invented angle.

Frozen rules reside in step5_dedup Config SSOT: Hamming10/temporal14,
angle12/tight8 degrees, temporal_index distance6. These reuse requested legacy
rules, not fitted quality thresholds. Legacy 64-bit DCT kernel (32x32 AREA resize,
8x8 low-frequency block, median(dct[1:,:])) is unchanged.

Union-Find components receive full SHA256 IDs of sorted newline-joined frame IDs,
scoped to the validated input universe, independent of row order/representative.
Singletons also receive IDs. Representative and cluster_rank use best_score DESC,
global_rank ASC, frame_id ASC only. dedup_role is authoritative; duplicate_status
and duplicate_group are compatibility aliases. Members remain recoverable alternatives.

Audit maximum pairwise measured pose spread, temporal span for one-video clusters,
maximum hash distances to representative, incident/cluster edge types and chaining.
A near-edge component warns if spread exceeds its largest applicable frozen angle
bound (temporal bound if present, otherwise tight bound). No arbitrary split rule;
exact-only components are not misrepresented as near-edge chaining.

## Lineage, publication and visual review

Preflight validates STEP3/4 version/hash/count/identity, inherited fields, score/rank,
declared generation consistency per kind, source/hash metadata, formal video/time
lineage and safe stored bbox. Formal/supplemental generation IDs may differ but
must match current STEP3. No latest fallback. Hash/decode errors retain ERROR rows
in isolated failed audits; --limit keeps all rows with PARTIAL_NOT_ANALYZED/ERROR
role for unprocessed rows in isolated partial audits, never quality Reject.

Reports are staged; prior outputs are copied with hashes to reports/bkup. Each
replace is atomic, summary last; caught errors attempt rollback. Process crash or
rollback filesystem failure is not a multi-file transaction. Summary hashes and
retained manifests make interruption detectable and support recovery.

No representative materialization: full CSV is authoritative, source images remain
immutable. Cluster HTML shows all alternatives; main pose HTML shows only UNIQUE/
REPRESENTATIVE, stored STEP4 pose/scale and deterministic BEST order within each
subgroup. Before/after counts/cross-table/ratios expose all pose reductions as
POSE_RETENTION_WARNING without a magnitude cutoff. Profiles receive visual context,
not protection/bonus/quota. Pool count is not final LoRA selection.

## Evidence and deferred work

Synthetic/tiny-fixture tests validate pair boundaries, exact cross-source matching,
missing evidence, stable ordering, chaining, full rows, source immutability,
partial/failed isolation, rollback and galleries. BAT preflight-only checks the
current1951-row metadata/existence contract without production image decode/hash.
No full STEP5/STEP6+ processing. pHash false merges, single-link chains and actual
rare-pose retention need production review; HTML static tests are not browser QA.

STEP6 default duplicate_status=unique/representative reads raw filename/named bbox,
so no copies or STEP6 edit is required for that structural bridge. Legacy STEP6
pose_bucket/pose_yaw, eval-all-eligible and report safety remain next-STEP audit
items; identity readiness is not claimed. run_all stops after STEP5.

[Implementation](../../docs/STEP5_DEDUP_V2_IMPLEMENTATION.md),
[Current Knowledge](../current/deduplication.md). Legacy code/results, historical
Decisions, STEP3/4 outputs, Human Review and A/B/C remain unchanged.
