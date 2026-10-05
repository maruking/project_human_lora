# STEP7 Current-Version Human Reject Patch

2026-10-05 / step7_quality_coverage_v2 — narrow downstream eligibility correction.

## Observed evidence and authority

Formal source: `output/reports/step3_best_review_history_by_version.json` and
`step3_best_review_reject_feedback_best_rank_v2.2.csv`. Current summary version is
best_rank_v2.2; ranking SHA256 is
`6400f2a09d30b0a99488872c435c0fae039644cbc27619d90b09a31e0d7126ca`.

The existing feedback/history do not contain a standalone ranking-output hash.
The patch verifies summary's ranking hash, inherited upstream fields, all shared
immutable review-record columns against current rows, frame_id, dataset_generation_id,
image_sha256, completed rounds and summary counts. Feedback must exactly agree with
the history's explicit current-version Reject set. Current Reject source pixels are
hash-checked. New STEP7 summary records the evidence paths/hashes and binding method.
Missing or conflicting authoritative evidence stops before selection/publication.

## Correction and invariants

Only confirmed current-version REVIEW_REJECT is excluded from normal eligibility.
Full audit rows remain, with candidate_pool_eligible=false,
candidate_pool_selected=false, selection_reason=CURRENT_VERSION_HUMAN_REJECT.
STEP7 status remains an audit measurement state. No score penalty is applied.

PENDING, shown-only, old v1/v2/v2.1 Reject, historical_review_reject alone, favorites
and preferences do not exclude or alter priority. BEST/global_rank, identity weight0,
coverage minima, source caps and the two-phase algorithm are unchanged. A corrected
pool with shortage or cap conflict is isolated/BLOCKED; prior production outputs stay intact.

## Read-only correction audit — not formal publication

| Requested report field | Result |
|---|---|
| Current-version rejects found | 4 |
| Current-version rejects removed from prior 70-pool | 4 |
| Historical-version rejects left eligible | 9 unique current frames, old-version-only |
| Candidate count | 70 |
| Normal candidate universe after exclusion | 1,075 |
| Full-row audit | 1,951 |
| Coverage shortages | 0 |
| Source-cap conflicts | 0 |
| BEST score changed | NO |
| Identity weight changed | NO |
| Human preference scoring introduced | NO |
| STEP3–6 changed | NO |

Removed: Sasha_v05_003; Sasha_v08_004; Sasha_v08_008; Sasha_v08_018 (each within its video folder).

| Replacement frame_id | global_rank | Reason |
|---|---:|---|
| Sasha_v05/Sasha_v05_010.png | 117 | COVERAGE_OPTION |
| Sasha_v32/Sasha_v32_019.png | 171 | BEST_SCORE_FILL |
| Sasha_v53/Sasha_v53_028.png | 173 | BEST_SCORE_FILL |
| Sasha_v03/Sasha_v03_070.png | 730 | COVERAGE_OPTION |

These are deterministic in-memory audit results from current inputs, not new
official output files or final LoRA suitability decisions. The formal HTML still
shows the previous pool until ★maru reruns BAT. No source image/report/history was moved or overwritten.

## Changes and validation

- `scripts/common/candidate_review_exclusions.py`: version-scoped authoritative evidence validation.
- `scripts/common/candidate_selection_v2.py`: confirmed Reject ID exclusion, full audit reason/count.
- `scripts/step7_candidate_selection_v2.py`: runtime evidence validation/hash pinning, summary context, shortage-safe publication.
- `tests/test_step7_review_exclusions.py`: requested9 regression tests plus3 authority/mismatch tests.
- This report, DEC-0024 amendment, current candidate-selection Knowledge and docs index.

STEP7 tests:40 PASS (28 existing +12 new). Unit/synthetic tests and read-only
current-data correction audit only. Formal STEP7 publication was not run by Codex.
Rules checked:AGENTS.md,.agents/AGENTS.md,PROJECT.md,both Project Rules,relevant
Knowledge/Decisions/Failures/Cases/History/Experiments. Data lineage/full rows/history/
config SSOT preserved:YES. No new Failure/Case/Experiment/History record required.

## ★maru

Run `bat/07_score_lora_candidates.bat` again, then share the updated
`docs/STEP7_CANDIDATE_SUMMARY.md` with Chappy. Do not begin final35–45 selection yet.
