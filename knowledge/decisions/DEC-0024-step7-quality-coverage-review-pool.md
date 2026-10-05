---
id: DEC-0024
title: STEP7 BEST quality and minimum-coverage Human Review pool
status: SUPERSEDED
date: 2026-10-05
confidence: MEDIUM
components: [candidate-selection, human-review, lineage]
tags: [best-authority, identity-diagnostic, review-options]
supersedes: [DEC-0013]
superseded_by: [DEC-0025]
related_experiments: []
related_failures: [FAIL-0003]
related_cases: []
---

# DEC-0024 — STEP7 Candidate Selection v2

## Context / previous approach

User explicitly replaces STEP7 Revision B for the current BEST2.2 / STEP4v2 /
STEP5v2 / STEP6v2 generation. DEC-0013's A-first/confirmed-B-reserve/35–45 proposal
is historical. DEC-0012's sidecar definitions and historical human evidence remain
intact, but are not runtime features/dependencies of STEP7 v2. Legacy
select_revision_b.py and common/revision_b.py remain unchanged. Older
score_lora_candidates.py mixes identity35%, local detail/resolution/exposure/rare
pose and gates identity_passed; it remains historical and is not run by normal BAT.

## Accepted architecture

STEP7 creates approximately70 HUMAN-REVIEW OPTIONS, configured range60–80.
STEP8 remains final35–45 human authority. STEP3 best_score is copied unchanged
as selection_quality_score; quality order is BEST DESC / global_rank ASC /
frame_id ASC. No secondary composite score, identity bonus/penalty, A/B/C gate,
expression/clothing/hair preference or historical Human Review feature.

Identity weight0: inherited PASS/REVIEW/REJECT/NOT_EVALUABLE are diagnostic context
only. Historical0.55 is not calibrated as a current-generation hard selection gate;
low measured similarity is not a wrong-person claim. STEP6 backend/state/results
are preserved. Current source ownership assertion is user evidence, not an
automatically inferred identity guarantee.

Normal universe: ranking_eligible and UNIQUE/REPRESENTATIVE, no upstream ERROR.
All rows survive; duplicate members are recoverable alternatives, never automatically
promoted on identity fallback. cluster_identity_fallback_needed is carried unchanged.

## Algorithm / SSOT

Phase A: empty pool, choose greatest NUMBER of deficit-reducing dimensions among
pose/vertical/scale, then unchanged BEST priority. Mark COVERAGE_OPTION and exact
deficits at selection time. Phase B: remaining slots by BEST priority only,
BEST_SCORE_FILL. No category maxima, percentage quotas or artificial coverage bonus.
Display pool order also uses BEST, independently of phase/selection chronology.

Config defaults: pose15 frontal/10 eachthree-quarter/4 eachprofile, vertical2 up/
2 down, scale12 close/18 upper/12 full. These are REVIEW MINIMUM OPTIONS, not
final training ratios. FULL_BODY remains STEP4 face-area scale, not body visibility.
Source caps:6 eachformal video,15 collective supplemental stills, one per cluster.
No source names/counts in logic. Unavailable categories produce shortages without
fabrication. Source-cap/cluster/target conflicts require review, no silent relaxation.
Phase A respects configured target slot budget; impossible simultaneous minima
report conflict and isolate BLOCKED output rather than silently grow beyond target.

## Lineage / publication / operational boundaries

Authoritative configured reports only. STEP6 COMPLETE report hash, unique frame
universe, inherited STEP3–5 fields, generations/states, upstream pinned hashes and
STEP5 representative membership are checked. Existing STEP3/4 schemas have no
literal COMPLETE field: their full expected count/identity and pinned hash contracts
prove structural completeness, without rewriting metadata or inventing a status.
Source existence and BEST score/rank/current pose enums are checked; no image/model
inference or STEP6 rerun. No latest-report fallback.

Full audit + selected subset + JSON/Markdown + grouped source-linked HTML.
Atomic individual files, prior archive and caught-error rollback reuse STEP6's
publication utility, summary last; not a process-crash multi-file transaction.
Partial/test/BLOCKED runs publish only isolated audit artifacts, never replace full
successful outputs. Not selected means NOT_NEEDED_FOR_REVIEW_POOL, not BAD_IMAGE.
Normal STEP7 BAT routes v2; runner retains existing STOP after STEP5. STEP8+ path
must be separately reviewed; no training/final selection is implemented here.

## Evidence / limits

28 synthetic/tiny-fixture tests and8 config tests PASS. Actual BAT metadata-only
preflight PASS for1951 upstream rows/1079 normal candidates. Category availability
and independent source-cap upper bounds exceed requested minima in current data;
this does not prove joint greedy feasibility,70-image output or candidate quality.
No full production STEP7 or STEP8+. Current-generation selection/shortages await
Chappy implementation review and ★maru's production BAT run. No final LoRA
suitability, greedy optimality or identity calibration claim.

[Implementation report](../../docs/STEP7_CANDIDATE_V2_IMPLEMENTATION.md),
[current Knowledge](../current/candidate-selection.md).

## Narrow eligibility amendment — 2026-10-05

User explicitly distinguishes an already-decided CURRENT-version REVIEW_REJECT
from subjective preference scoring. The original architecture/body above remains
the implementation-time record. Active eligibility now additionally excludes only
confirmed best_rank_v2.2 REVIEW_REJECT with frame/image/generation match and
current ranking-output evidence. The version-scoped history and reject feedback
must agree; immutable stored review columns must match the hash-verified current
ranking. Neither artifact contains its own ranking-output hash, so this explicit
cross-check supplies the binding; absence or disagreement stops STEP7.

PENDING, shown-only, old-version Rejects and historical_review_reject alone never
exclude. Score, global_rank, identity weight0, minima and caps remain unchanged.
Keep full audit rows with CURRENT_VERSION_HUMAN_REJECT; no new quality score or
automatic duplicate fallback. This is an eligibility correction, not a redesign.

40 tests PASS. Read-only current-data recomputation:4 prior-pool Rejects excluded,
4 replacements,70 candidates/no shortages or source-cap conflicts;9 historical-only
Rejects still eligible. No official STEP3–7 outputs or history changed by Codex.
Normal BAT republishes after ★maru reruns. [Patch report](../../docs/STEP7_CURRENT_VERSION_REJECT_PATCH.md).

## Supersession — 2026-10-05

DEC-0025 replaces coverage-first v2 selection with bounded QUALITY-FIRST v2.1.
Original body, tests, production evidence and current-version Reject amendment
remain historical; the authoritative Reject patch is carried forward unchanged.
