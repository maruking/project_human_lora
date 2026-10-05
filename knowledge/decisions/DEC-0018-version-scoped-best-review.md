---
id: DEC-0018
title: Version-scoped BEST review restart with immutable v1 evidence
status: SUPERSEDED
date: 2026-10-04
confidence: MEDIUM
components: [face-quality, ranking, human-review, lineage]
tags: [best-rank-v2, review-history, round-restart]
supersedes: [DEC-0017]
superseded_by: [DEC-0019]
related_experiments: []
related_failures: []
related_cases: []
---

# DEC-0018 — Version-scoped review

Superseded by [DEC-0019](DEC-0019-general-eye-quality-best-v21.md): the same
version-scoped history design continues, with independent best_rank_v2.1 Round1.
v2 architecture and evidence below remain historical.

## Context and previous approach

DEC-0017 retained v1 shown exclusions and proposed proceeding directly to Round3.
The user explicitly supersedes that policy: changed ranking semantics require a
new review sequence, including intentional reappearance of previously rejected
images. All DEC-0017 scoring, fatal predicates and configured settings are retained.

## Decision and alternatives

Chosen: start best_rank_v2 at Round1, retain separate per-version history. Round2
excludes only v2 Round1, Round3 excludes only v2 Round1/2. Reject is not automatic
ranking exclusion. Rejected alternatives: deleting/resetting v1 history, overwriting
old decisions, or continuing v1 Round3 under v2 semantics.

Persist version buckets in step3_best_review_history_by_version.json. The legacy
step3_best_review_history.json is imported read-only, with its source checksum;
its nested snapshot preserves original records. The store is first written only
on explicit review publication. Old flat review folders remain untouched; new
copies live in step3_best_review/best_rank_v2/round_XX. Feedback updates v2 only,
with its own feedback CSV. Historical decisions remain visible separately from
current review_selected/shown/review_state, matched on generation/frame/hash.

## Evidence and interpretation

Observed: 62 BEST synthetic/unit tests pass, including the six requested history
invariants. A temporary BAT with a stub downstream entry forwards Round1 correctly.
No production execution or candidate copies. Four existing production report/history
files retain pre-edit SHA256 values. No score or source lineage reset is performed.
Interpretation: version isolation permits a fair new review; it does not prove
improved image quality or successful production execution.

## Consequences and limits

Old and new reviews may show the same image intentionally. Generation/hash mismatch
in active history stops reuse; changed legacy evidence stops implicit migration.
Failed/reserved copy publication still requires inspection before recovery.
Atomic replacement is per file, not a multi-file transaction. ★maru owns full
ranking and review extraction. No STEP4+, A/B/C or threshold changes.

See [implementation and validation](../../docs/STEP3_BEST_RANKING_V2_REVIEW_RESTART.md).
