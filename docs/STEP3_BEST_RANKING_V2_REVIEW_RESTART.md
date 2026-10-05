# best_rank_v2 — version-separated Human Review restart

Historical v2 implementation/evidence. Current operation is [best_rank_v2.1](STEP3_BEST_RANKING_V21_IMPLEMENTATION.md); v1/v2 review data remain unchanged.

2026-10-04. Infrastructure / review-policy revision. Execution: implementation and
synthetic validation complete. Algorithm validity: unchanged v2 scoring, no new
quality claim. Human calibration: new v2 rounds pending. The saved active ranking
already identified itself as v2 before this change; it was not regenerated here.

## Changed

- scripts/common/best_review.py: versioned history store, read-only v1 import,
  source-checksum guard, v2-only feedback and generation-safe historical evidence.
- scripts/common/best_ranking.py: shown exclusions scoped to v2 and earlier rounds.
- scripts/step3_best_ranking.py: separate history/feedback paths, active versus
  historical review annotations/counts, next-round guidance and v2 copy paths.
- bat/03_best_review_round.bat: allow Round1; bat/03_face_quality_gate.bat: corrected guidance.
- tests/test_step3_best.py, tests/test_step3_best_v2.py: revised history expectations.
- tests/test_step3_best_history_versions.py: 13 focused version-isolation regressions.
- README.md, PROJECT.md, knowledge/current/face-quality.md,
  knowledge/current/configuration.md, knowledge/decisions/README.md,
  DEC-0017-best-ranking-evidence-penalties.md,
  DEC-0018-version-scoped-best-review.md, STEP3_BEST_RANKING_V2_IMPLEMENTATION.md
  and this report: current policy and historical supersession.

Config files, scoring formulas, thresholds, official Gate reports, Human Review
decisions, A/B/C and STEP4+ are unchanged in this revision.

## History and output contract

Configured reports_dir contains the new store, created on ★maru's first explicit
v2 review extraction:

```text
step3_best_review_history_by_version.json
  review_history
    best_rank_v1: original round_01 / round_02 records and decisions
    best_rank_v2: new round_01, then round_02, then round_03 records
```

Each bucket has rounds and records lists; record keys include ranking_version,
review_round, frame_id and review_state, plus existing generation/hash/scores.
Legacy JSON and flat round folders are never moved or overwritten. The store
retains their original snapshot and checksum. New copies go to:

```text
step3_best_review/best_rank_v2/round_01/candidates
step3_best_review/best_rank_v2/round_01/review_reject
```

Round2/3 use the same version prefix. Feedback writes
step3_best_review_reject_feedback_best_rank_v2.csv; the legacy feedback CSV stays
unchanged. Ranking CSV historical_reviews contains version/round/frame/state evidence;
historical_review_reject is a reference flag, not an exclusion or current decision.
Historical annotations require identical frame_id, generation and image checksum.
The summary separates active v2 counts from historical_review_counts.

Round1 ignores all v1 shown/reject flags. Round2 excludes v2 Round1 only. Round3
excludes v2 Round1/2 only and cannot be generated before v2 Round2. Completed rounds
are not regenerated when copies are deleted. Interrupted RESERVED rounds stop for
inspection. Active-generation mismatch stops reuse instead of resetting lineage.
The history store is not written by ranking-only execution. No production history
migration, ranking, or review extraction was performed during this implementation.

## Score and extraction design retained

Ranking version: best_rank_v2. Root bug fixed previously: relative position was
incorrectly used as defect evidence; this revision fixes cross-version shown-state
leakage. Absolute quality: shared combined-universe P5/P95 positive scale (not an
independently calibrated photographic unit). Relative bonus: small positive-only
kind percentiles. Penalties: measured defects/diagnostic evidence, not percentile
inferiority. Video/still share the main scale; kind-specific bonus remains separate.
Configured defaults remain review_size45, min_supplemental10 where eligible stills
remain, and soft cap4/video with recorded minimum relaxation if needed. These review
constraints do not rewrite scores/global ranks; Round1 is ranked selection under
these constraints, not an unconstrained first45 CSV slice.

Reference still old/new score: 41.002473 -> 88.436829, from the preceding limited
stored-metric check in STEP3_BEST_RANKING_V2_REFERENCE_CHECK.json. It was not
remeasured or rescored here. No claim of final rank or calibrated suitability.

## Minimum validation

62 BEST unit/synthetic tests PASS. All six requested invariants covered:
version separation; v1 shown does not exclude v2 Round1; v2 Round2 excludes only
v2 Round1; v2 Round3 excludes only v2 Round1/2; v1 Reject remains regression evidence;
restart preserves lineage/ranking/source bytes. Additional cases cover feedback
isolation, unchanged legacy bytes/copies, generation mismatch, changed legacy
checksum, direct Round3 prevention and no implicit acceptance.

A disposable copy of the round BAT with a stub child confirms Round1 forwards
--from-existing --review-round 1. No real BAT production entry was executed.
Production ranking CSV, summary, legacy review JSON and feedback CSV retain their
pre-edit hashes. Existing report content was not changed to reflect the new policy;
★maru's next ranking execution publishes updated annotations and summary guidance.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, both Project Rules, relevant
Current Knowledge, Decisions, Failures, Cases, History and implementation reports.
Knowledge Maintenance skill used for supersession. Data lineage preserved: YES.
Full-row preservation: YES in synthetic ranking tests; production rows untouched.
Historical evidence preserved: YES. Config SSOT preserved: YES. No conflicting
rules remain; the explicit latest user instruction supersedes old review sequencing.
Failures/Cases/Experiments/History checked; no new quality-evaluation record warranted.

Unresolved: production review has not been validated with real copies in this
revision; existing occlusion/detail comparability limitations still require Human
Review. Per-file publication is not a multi-file atomic transaction.

Full production executed: NO.

## ★maru next action

Run bat/03_step3_best_ranking.bat. Inspect the summary, then run
bat/03_best_review_round.bat 1. Human Review restarts at best_rank_v2 / Round1.
Preserve best_rank_v1 Round1/2 as historical evidence; never use them as v2 shown
exclusions. Normal ranking stops before candidate extraction.
