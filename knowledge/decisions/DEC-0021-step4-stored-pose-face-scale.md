---
id: DEC-0021
title: STEP4 v2 stored pose and authoritative face-scale descriptors
status: SUPERSEDED
date: 2026-10-05
confidence: MEDIUM
components: [pose-classification, composition, lineage]
tags: [step4-v2, measurement-only, face-scale]
supersedes: []
superseded_by: [DEC-0027]
related_experiments: []
related_failures: []
related_cases: []
---

# DEC-0021 — STEP4 Pose / Composition v2

## Context and previous implementation

STEP3 BEST v2.2 stores signed yaw/pitch/roll and face bbox geometry but no shot_type.
Legacy STEP4 re-inferred pose from the older Gate report, combined pitch/yaw into
one bucket, and used UPPER_BODY for absent shot_type. Face Gate uses face area;
DEC-0005 and historical pose knowledge describe face height. These are different
quantities, so silently joining/classifying them would obscure lineage.

The initial implementation correctly stopped at this ambiguity. Chappy/★maru
explicitly resolved it: reuse current Face Gate SSOT area boundaries, preserve
height ratio as raw data only, and keep historical DEC-0005/Knowledge intact.
This decision changes STEP4 descriptors only, not STEP7 quotas or BEST scoring.

## Accepted design

Version step4_pose_composition_v2 reads the complete authoritative best_rank_v2.2
CSV and verifies its version, count, unique frame identities and SHA256 against
its summary. It does not infer images or consume Human Review as a feature.
Every input row/column remains, including supplemental stills and fatal rows.
Fatal rows receive NOT_APPLICABLE_STEP3_FATAL; incomplete measured evidence receives
NOT_EVALUABLE. Malformed/inconsistent geometry receives ERROR without dropping
the row. Non-ranking input must have its recorded fatal reason.

face_scale_bin is authoritative: area >= configured shot_close_up_threshold
is CLOSE_UP; area >= shot_full_body_threshold is UPPER_BODY; smaller is FULL_BODY.
Current SSOT values are 0.12/0.04. shot_type is an explicit compatibility alias.
These labels do not establish actual torso/leg visibility. Face height ratio is
stored, never classified by the historical 25%/10% boundaries.

Pose uses stored MEASURED angles. Configured yaw semantics are <=front FRONTAL,
front<abs(yaw)<profile THREE_QUARTER, abs(yaw)>=profile PROFILE; current boundaries
15/42 and three_quarter_yaw_max=profile_yaw_min must agree. Positive yaw RIGHT,
negative LEFT follows repository convention, not anatomical direction independent
of mirroring. Pitch below min LOOKING_UP, above max LOOKING_DOWN, endpoints LEVEL;
current SSOT -20/+20. Roll is retained, not newly binned.

Centers and face height use stored bbox/image dimensions. Edge fields describe
exact bbox contact with each frame edge. No near-edge distance or position-bin
threshold is introduced. Missing geometry is not 0. Stored area and short edge
are reused and consistency-checked, not silently replaced with another formula.

## Implementation and evidence

Normal BAT is bat/04_classify_face_pose.bat -> scripts/step4_pose_composition.py.
Legacy classify_face_pose.py remains byte-identical in-place for historical code
and tests. Existing legacy STEP4 reports are not overwritten. Repeated new output
publication preserves prior files under reports/bkup with path/hash manifests.
Individual file replacement is atomic, not a multi-file transaction; the summary
is published last with hashes of all its companion outputs to expose interruption.

Facts: the old/current pose function ASTs match. Synthetic tests and a six-row
stored sample cover boundaries, missing/fatal evidence, geometry, stills, score
preservation, history independence and rerun archives. BAT help validates the path.
Interpretation: the descriptor contract is implemented, not an empirical guarantee
of pose accuracy, body framing or dataset suitability. Full production is pending
★maru. STEP5 still reads legacy fields/report names; its new integration is deferred.
run_all stops after STEP4 rather than silently reading stale STEP4 evidence in STEP5.

## Consequences and limits

No quality ranking, Reject, A/B/C, quotas, deduplication, identity or final selection
is introduced. Missing pose remains missing; full production may have many
NOT_EVALUABLE rows. Summary distributions explicitly include ranking-eligible
missing/error records and distinguish all-row source totals. Historical height
classification remains evidence, not the active v2 rule. DEC-0005 is not globally
superseded or edited because its STEP7 selection context lies outside this task.

See [implementation and validation](../../docs/STEP4_POSE_COMPOSITION_IMPLEMENTATION.md).
