# STEP3 BEST ranking implementation — 2026-10-04

## Authorization and execution boundary

The current user request cancels the Tier B / STEP3 V2 absolute Hard Reject
calibration direction. STEP3 now measures the complete formal-video plus declared
supplemental-still universe, ranks promising face-learning review candidates and
copies review batches. Ranking is neither photographic acceptance nor final
dataset selection. A/B/C and all historical official STEP3/Human Review evidence
are untouched. Production has NOT run; no real-data quality claims are made.

Rules checked: root AGENTS, .agents/AGENTS, PROJECT, Pipeline Hard Rules and Data
Lineage Hard Rules. [DEC-0016](../knowledge/decisions/DEC-0016-best-candidate-ranking.md)
records the explicit change of STEP3 responsibility; the former canonical Gate
threshold remains unchanged in historical config and is not used by BEST.

Data lineage preserved: YES. Full-row preservation: YES by implemented contract,
synthetic validation only; production count/identity coverage remains unverified.
Historical evidence preserved: YES. Config SSOT preserved: YES.

## Files changed for this task

- scripts/step3_best_ranking.py
- scripts/common/best_inventory.py
- scripts/common/best_measurement.py
- scripts/common/best_pose.py
- scripts/common/best_ranking.py
- scripts/common/best_review.py
- scripts/common/step3_review.py (review-input guard extension)
- bat/03_face_quality_gate.bat (normal STEP3 now invokes BEST)
- bat/03_step3_best_ranking.bat (explicit BEST alias)
- bat/03_best_review_round.bat
- bat/03_best_review_feedback.bat
- config/config.yaml, config/config.example.yaml, config/config.schema.json
- .gitignore (disposable BEST copies only; history/reports remain trackable)
- tests/test_step3_best.py
- this report, README.md, PROJECT.md, knowledge/current/face-quality.md,
  knowledge/current/configuration.md, knowledge/current/README.md,
  knowledge/decisions/README.md, DEC-0015 successor metadata and DEC-0016.

Existing unrelated working-tree changes are preserved, not committed or pushed.

## Input and fatal failures

Validate STEP2 formal report/summary against STEP1 manifest, extraction receipts,
counts and actual content hashes. Read the declared supplemental directory and
content map from STEP2 summary, not a hardcoded subject folder. Require its CSV
to cover exactly those images. Repeat validation before publishing measurement
results, under the existing STEP1/2 manifest lock. Formal and still generation
IDs stay distinct. Relative frame_id, filename, source_id, video_id and SHA256
are present for every row. Source pixels are never changed.

Only analysis_error, no_face, confirmed multiple_faces, invalid_crop_geometry and
face_not_evaluable can stop ranking eligibility. Multiple faces means distinct
valid detection results above the configured detector confidence; evidence is
from a single MediaPipe backend, not agreement between independent detectors.
The crop's minimum three-pixel geometry is the numerical kernel support needed
for evaluation, not a face-quality resolution threshold. Missing FaceMesh alone
uses bbox exposure and missing detail/visibility values; it does not fatal-reject
a measurable face core. All fatal rows remain in the full CSV with no rank/score.

## Measurement and formula

Reuse original native/core Laplacian and Tenengrad kernels; canonical face core
has short edge 192, preserved aspect and existing AREA/CUBIC/IDENTITY resize.
Individual eyes/mouth use native anatomical patches and the existing normalized
Tenengrad kernel. Eye presence/openness, visibility, face-mask pixel statistics
and optional skin/plasticity measurements reuse current kernels. Head-pose
calculation is a copied, unchanged STEP4 measurement function; no STEP4
classification, quota or processing is performed.

Pixel bin boundaries in diagnostic JSON and shadow bin40 describe measurements;
they do not reject images. Old eye-presence validity is context only. Unavailable
measurements have blank raw/normalized components and explicit availability.
Unavailable does not mean measured zero. Missing positive components contribute
zero to the sum, with an explicit uncertainty penalty and without renormalizing
other weights upward. Partial paired-eye/canonical/exposure coverage attenuates
the corresponding contribution proportionally.

For each metric, rank only non-fatal current rows separately within formal_video
and supplemental_still. P(x) = (number strictly below x + number <= x)/(2*N).
Ties receive their midrank (all tied ->0.5). Values are relative evidence, not
absolute quality labels; two tiny/dissimilar pools do not guarantee comparable
perceptual quality. Score ties resolve deterministically by frame_id.

BEST = 100 * (sum(w_i * component_i * availability_i)
             - sum(v_j * penalty_j)). Scores may be negative.

Default positive weights: canonical sharpness .20, eye detail .15, mouth detail
.10, local contrast .15, visibility .15, face size .10, exposure .15.
Sharpness is the mean of available P(canonical Laplacian/Tenengrad); eye detail
is the available left/right mean. Exposure is the available mean of
P(dynamic range), 1-P(highlight clip), 1-P(shadow). Other components use their
named percentile directly. Larger face size is favored relatively, never gated.

Default penalty weights: blur .15, obstruction .15, half-eye .10, low contrast
.10, shadow .10, clipping/haze .10, uncertainty .10.

- Blur: available mean of inverse sharpness and inverse local eye/mouth detail.
- Obstruction: available mean of inverse visibility and eye concern. Eye concern
  is mean(inverse mean eye presence, P(openness asymmetry)), multiplied by
  abs(cos(yaw)); missing yaw uses0.5 and is explicitly marked unavailable.
- Half-eye: inverse P(minimum eye openness); no absolute blink rejection.
- Low contrast: inverse P(local face contrast).
- Shadow: P(face shadow ratio).
- Haze: P(brightness)*(1-P(dynamic range))*(1-P(local contrast)); clipping/haze
  is available mean of P(highlight clip) and haze.
- Uncertainty: 1 minus total positive-weighted measurement availability.

All raw values, normalized values, components, availability, contributions,
penalties, deductions and totals are CSV columns. Weights are visible provisional
design choices in config, not empirically approved quality guarantees. Skin,
plasticity, native global Laplacian and legacy validity are diagnostic context.

## Review rounds and outputs

Normal entry: bat/03_step3_best_ranking.bat (alias of normal03 BAT).
It produces step3_best_ranking.csv, step3_best_ranking_summary.json and Round1.
Summary includes per-kind metric/component/penalty/score distributions, universe
counts, fatal reasons, top sources and top45 video concentration. Old official
step3_dataset_report.csv and summary remain unchanged.

Each round requests45 copies, cap4 per video. Stills are exempt. If necessary
increase the cap one at a time, report effective cap/shortage, never change score
or global_rank. Persist review_round_rank independently. This is review diversity,
not deduplication, pose quota optimization or final35–45 selection.

Copies: output/reports/step3_best_review/round_01/candidates and review_reject;
round_02 and round_03 follow the same structure. Original relative directories
are preserved to prevent basename collisions. Moving images must preserve the
relative subpath (e.g. candidates/video/file.png ->review_reject/video/file.png).
Copies and resolved aliases are excluded by the shared discovery guard.

Durable history: output/reports/step3_best_review_history.json, outside the copy
tree; includes full ranking snapshot, lineage, SHA, shown_to_maru, PENDING state,
optional reason and copy status. It is never inferred from folder contents.
History is reserved before copying to prevent reshow after interruption. A
failed copy leaves RESERVED evidence and stops reruns of that round for explicit
inspection/recovery. A completed round is never rematerialized automatically,
even if its folders were deleted. Do not delete the durable history file.

After manual moves, bat/03_best_review_feedback.bat records REVIEW_REJECT and
writes step3_best_review_reject_feedback.csv with components, penalties, metrics,
largest positive contributions and explicitly hypothetical failure explanations.
No automatic threshold fitting, A/B/C or official rejection changes occur.
Remaining candidates stay PENDING; absence never means ACCEPTED. ACCEPTED is a
reserved explicit-human history state, not currently inferred by a command/UI.

Only after Chappy's approval: bat/03_best_review_round.bat 2 (later3). It loads
the existing current-generation ranking with checksum/settings validation; no
new inference, and all previously shown frame_ids are excluded. Exhaustion may
produce fewer than45 copies, explicitly reported. Normal BAT never advances
automatically to Round2 or3.

## Validation / unresolved scope

23 BEST synthetic tests passed: all12 required
contract cases plus balanced-quality ranking, checksum protection, interrupted
copy history, input mismatch and five-row temporary CLI round/feedback wiring.
Two synthetic200px image measurements use a mocked detector; no real model
inference. Existing config tests8 and review-guard tests27 also passed (58 total).
The BEST BAT --help check passed and exercised argument/environment routing only.

Real Sasha_v10/v08/v38/v63/v33 examples have NOT been rerun or visually assessed
in this task. Their intended failure patterns have synthetic tests; empirical
ranking quality and the provisional weights await Round1 Human Review.
BEST does not feed unchanged legacy STEP4–10 consumers automatically; their
historical face_eligible report contract is deferred. Run STEP3 standalone,
not the full pipeline runner, and do not proceed to STEP4+ in this task.

Full production executed: NO.

Failures, Cases, Experiments and History checked: no new empirical records warranted; earlier evidence preserved.

Final source-only checks: Python syntax PASS; copied STEP4 pose model/indices/kernel AST equality PASS; new report/Decision links PASS. No production reports, images or Human Review files were modified by this task.
