---
topic: deduplication
last_updated: 2026-10-05
confidence: MEDIUM
status: ACTIVE
related_decisions: [DEC-0022]
related_failures: []
related_cases: []
---

# Current Knowledge: STEP5 Deduplication v2

Normal entry: bat/05_face_deduplication.bat → scripts/step5_dedup_v2.py. Read the
complete authoritative STEP4 v2 CSV, verified against its summary and current
BEST v2.2. Analyze ranking_eligible, not legacy face_eligible. Keep every row/column,
including fatal and duplicate members. [DEC-0022](../decisions/DEC-0022-step5-conservative-dedup-clusters.md)

Exact SHA byte identity may cross kinds/sources. Near matching is limited to
same-video frames or stills within the declared supplemental universe. Separate
global/face 64-bit DCT pHash; missing face stays MISSING. Missing pose allows exact
only. Raw angles, not pose/face-scale category equality, gate near edges. All five
frozen rules live in step5_dedup SSOT: Hamming bits, degrees, temporal index distance
(not seconds). Human/identity, quotas and source-name exceptions never enter scoring.

Representative and cluster_rank use STEP3 best_score descending, global_rank
ascending, frame_id ascending. No face_quality_score. Every connected component,
including singleton, has a deterministic member-set SHA ID. Audit chaining, max
pose/hash spread and temporal span. DUPLICATE_MEMBER is a recoverable redundant
alternative, not bad quality. dedup_role is authoritative; duplicate_status/group
are aliases for legacy consumers.

Full CSV is authoritative. No new representative image copies; historical materialized
folders stay unchanged. Missing/stale/inconsistent input causes STOP. Error/partial
audits retain all rows separately, never overwrite good production reports. Atomic
file replacements, summary hashes and archived prior outputs expose interrupted
multi-file publication; this is not a crash-safe database transaction.

After ★maru runs STEP5, inspect summary and pose/cluster HTML. Main gallery contains
UNIQUE/REPRESENTATIVE only; cluster detail includes alternatives. Links reference
original images. Pose/face-scale use STEP4 labels. Before/after counts/ratios and
pose×scale table are diagnostic. Any reduction is highlighted without a new cutoff;
profiles get rare-pose context, not quota/bonus. Pool count is not final training count.

STEP6 default aliases are structurally compatible; legacy pose fields, eval-all-eligible
and identity safety need STEP6 review. Runner stops after STEP5. Synthetic/small
validation is complete; actual cluster/retention results and browser image display
await production review. [Implementation](../../docs/STEP5_DEDUP_V2_IMPLEMENTATION.md)
