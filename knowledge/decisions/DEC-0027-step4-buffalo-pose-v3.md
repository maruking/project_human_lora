---
id: DEC-0027
title: STEP4 v3 comparison-approved buffalo_l 3D pose
status: ACCEPTED
date: 2026-10-05
confidence: MEDIUM
components: [pose-classification, lineage]
tags: [step4-v3, buffalo-l, bounded-human-comparison]
supersedes: [DEC-0021]
superseded_by: []
related_experiments: []
related_failures: []
related_cases: []
---

# STEP4 v3 — buffalo_l pose

## Context and previous approach
STEP4 v2 reused STEP3 MediaPipe six-point solvePnP angles. The user reports
incorrect pose in the known comparison counterexample and approves replacing
the estimator after visually reviewing all 25 comparison images.

## Accepted implementation
Only STEP4 changes. Existing installed buffalo_l detection plus 68-point 3D
landmark pose runs on original images using the exact comparison CPU settings.
No new models/installations, sign inversion, angle normalization or threshold tuning.
Raw pose is pitch/yaw/roll; output yaw/pitch/roll is classified by existing SSOT
yaw and vertical boundaries. STEP3 primary bbox associates the unique maximal
positive IoU detection. Missing/ambiguous/error pose never falls back to solvePnP.
STEP3 yaw/pitch/roll/pose_status are retained in step3_* columns, and all other
inherited evidence, score/rank and source identity remain. Face-scale and geometry
use the unchanged STEP3 bbox/formulas. Fatal rows stay but are not inferred.

Normal 04 BAT uses the existing .venv-step6 runtime and new v3 driver. Historical
v2 driver/module remain unchanged. Production publication preserves old STEP4
outputs in reports/bkup; file replacement is individually atomic, summary last,
not a multi-file transaction. Per-row failures remain ERROR and return nonzero.

## Evidence and interpretation
User evidence: 25-image comparison reviewed; angle classification/distribution
acceptable to ★maru. Implementation check: all 25 angles match comparison exactly
(maximum absolute delta 0 degrees). Known counterexample: old yaw -0.892449,
FRONTAL; new yaw -50.178444, PROFILE_LEFT. Synthetic full-row, score, geometry,
missing/error, boundary and publication checks pass. No full inference executed.
Interpretation: this is a user-approved estimator change with bounded evidence,
not general labeled pose accuracy or anatomical/mirror-independent sign proof.

## Limits and downstream
Only current STEP4 production is authorized for ★maru. Existing STEP5 preflight
requires v2 and inherited STEP3 angle equality, so it intentionally blocks v3.
STEP5+ code/settings are not changed or run. Adapt downstream in a separate task
after Chappy reviews the new production summary. Human review/reject and A/B/C
are not changed. Source removal request was pending clarification; no deletion.

See [implementation](../../docs/STEP4_POSE_COMPOSITION_V3_IMPLEMENTATION.md).

2026-10-06 downstream update: the separately authorized STEP5 preflight bridge
now accepts v3 and checks preserved STEP3 angle aliases. Frozen dedup algorithms
are unchanged; read-only1951-row and synthetic checks only. STEP5 production is
pending ★maru. The earlier v2-only restriction above describes the v3 implementation
time; see [STEP5 compatibility](../../docs/STEP5_STEP4_V3_COMPATIBILITY.md).
