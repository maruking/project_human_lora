# STEP3 BEST Ranking v2.1 — implementation and limited regression check

2026-10-05. Algorithm Revision. Execution: implemented and minimum validation
complete; full production NOT executed. Algorithm validity: generic semantic/unit
properties tested, limited stored-metric comparison only. Human calibration: v2
history remains evidence; v2.1 review has not started. This is not a production
quality PASS or proof that all technical defects will leave the highest ranks.

## Changed

- scripts/common/best_ranking.py — v2.1 scoring, separate eye outputs, geometric
  blur/exposure agreement, weaker-eye credit and explicit unresolved blur scaling.
- scripts/common/best_eye_quality.py — independent opening/visibility/reliability,
  pose expectation, auditable eye quality.
- scripts/common/best_ranking_v2.py — exact pre-change v2 module preserved.
- scripts/common/best_review.py — current-version guidance; existing history
  buckets/copies remain isolated without v1/v2 exclusions in v2.1.
- scripts/step3_best_ranking.py — v2 archive compatibility, current-version checks,
  expanded diagnostic distributions. Stored-metric default and explicit extraction retained.
- bat/03_face_quality_gate.bat, bat/03_best_review_round.bat — v2.1 guidance.
- config/config.yaml, config/config.example.yaml, config/config.schema.json —
  ranking_version only; numerical values unchanged.
- tests/test_step3_best.py, tests/test_step3_best_v2.py,
  tests/test_step3_best_history_versions.py, tests/test_step3_best_v21.py,
  tests/fixtures/step3_best_v21_counterexamples.json — generic/current migration
  coverage; historical v2 semantic tests execute the preserved v2 module.
- README.md, PROJECT.md, knowledge/current/face-quality.md,
  knowledge/current/configuration.md, knowledge/decisions/README.md,
  DEC-0018 successor metadata, DEC-0019-general-eye-quality-best-v21.md,
  historical markers on the two prior v2 implementation/restart reports.
- This report, STEP3_BEST_RANKING_V21_REGRESSION.json and
  STEP3_BEST_RANKING_V21_PROTECTED_HASHES.json.

## Generalization and history safety

BEST_SCORE uses image measurements and the approved positive normalization only.
No filename, video/source ID, old rank, Human Review decision/reason/folder enters
scoring branches. Frame ID only breaks score ties; video ID is used only by the
review sampling cap. Human labels are test/report evidence. No blacklist or source
quarantine. Regression tests rename metadata and change decisions without changing
scores, and check scoring AST branches for forbidden feature reads.

Main positive normalization remains combined non-fatal-universe P5/P95; relative
percentiles remain positive bonuses by input kind. Configured shares90/10 and all
weights remain. No new fatal predicates/thresholds, Gate formula, image measurement
kernel, source pixels, official Gate report or A/B/C state is changed.

v1/v2 code/report/history semantics remain readable. This task does not publish or
overwrite production CSV/summary/history. On ★maru's next ranking publication,
existing archive_current copies previous CSV/summary under content-addressed
step3_best_history before replacing active ranking reports. v2.1 starts with no
active shown records; old buckets remain historical annotations only. New copies
go to step3_best_review/best_rank_v2.1/round_01. Normal ranking creates no copies.
Per-file atomic replacement is not a multi-file power-loss transaction.

## Eye Quality

Separate measurements preserved: left/right openness, minimum/asymmetry, semantic
state, presence, local detail, ROI status/width, landmark availability and yaw.
Existing diagnostic bins are used, not new cutoffs. OPEN gives zero openness
penalty. HALF_OPEN or BORDERLINE with a below-normal ratio has strength
0.5 + weak_evidence_scale × clip((normal_ratio - ratio)/(normal_ratio - closed_ratio)).
Both coefficients reuse v2's existing half-state base and configured weak scale.
CLOSED/BLINK has strength1, stronger than half; existing below-closed raw ratios
can supply that state. Asymmetry alone with normal ratios does not create a defect.
Worst expected-eye opening is used, not a mean. Existing CLOSED labels are not
silently invented for examples that currently measure BORDERLINE.

At |yaw| <= existing three_quarter_yaw_max, both eyes are expected. Beyond it,
the larger measured projected eye ROI is provisionally the near eye; the far eye
is omitted from failure/obstruction/opening aggregation. This avoids inventing a
signed yaw convention. Missing/equal ROI widths or missing yaw lead to explicit
pose abstention. ROI projection is a heuristic, not validated 3D eye visibility.

Obstruction concern requires the SAME expected eye's presence AND local detail
to be below their existing anchors: sqrt(presence_deficit × detail_deficit).
The largest such corroborated concern is used. Legacy eye-presence boolean alone
cannot penalize. This is suspected usable-eye loss, not confirmed hair causation.
An unavailable expected ROI/detail/landmark measurement instead records failure;
it is not relabeled obstruction and missing values remain missing.

eye_quality_score = (1 - openness_loss) × (1 - corroborated_obstruction_loss)
× (1 - fraction_of_expected_eyes_with_measurement_failure).
Unavailable evidence/pose abstention stays explicit rather than fabricated zero.
For eye positive credit, the weaker expected normalized eye detail replaces the
mean, multiplied by eye_quality_score where available. Profile side unknown
abstains from this usability multiplier. Coverage still accounts for missing detail.

Outputs: eye_quality_score, eye_closed_penalty, eye_half_open_penalty,
eye_obstruction_penalty, eye_measurement_penalty, failure/reliability/expectation
and per-eye semantic evidence. eye_detail_abs_unadjusted,
eye_detail_relative_unadjusted and eye_quality_positive_credit_loss explain removed
positive credit separately from penalties. The old half_eye_penalty is an alias
of closed+half points, not an extra deduction.

Closed and half penalties share the existing half_eye budget and are mutually
exclusive. Eye measurement gets half of the existing uncertainty budget; generic
missing-coverage uncertainty gets the other half. Obstruction/clipping budgets
retain their existing splits. No numeric budget setting was increased.

## Blur and exposure

For existing face Laplacian and individual-eye anchors, deficits are bounded
(anchor-value)/anchor. Blur strength is the maximum sqrt(a×b) over measured pairs
(face,left eye), (face,right eye), (left eye,right eye). One weak metric with all
others healthy gives0. Missing pairs cannot masquerade as zero observations.
This increases a corroborated penalty compared with the prior second-largest
deficit, without using inverse percentile or inventing a single-metric rejection.

STOPPED component: no compatible absolute defect anchors for canonical Tenengrad
or mouth-local detail are approved. Their raw measurements and positive scores
remain visible; no arbitrary new defect cutoff is added. The CSV reports
blur_scaling_state = EXISTING_LAPLACIAN_EYE_ANCHORS_ONLY_TENENGRAD_MOUTH_UNRESOLVED.
Directional blur is not measured by current stored data.

Dark strength = sqrt(existing brightness deficit × maximum(existing local
contrast deficit, existing dynamic-range deficit)). Brightness alone is insufficient.
Dynamic-range span reuses v2's same intensity-span reference, not a new cutoff.
Haze = existing high-brightness ramp × sqrt(dynamic-range deficit × contrast deficit).
Clipping retains existing slack/ramp; healthy tiny highlights receive0. Haze and
clipping are distinct. dark_exposure_penalty uses the existing shadow budget;
shadow_penalty remains a compatibility alias, excluded from penalty_total.

Scores expose all requested absolute components, eye components, blur/dark/clip/
haze/contrast/uncertainty penalties and totals. Sum deduction_* = penalty_total;
aliases are not counted twice. No expression/paint/upward-pose preference penalty.

## Stored-metric regression — 12 examples only

All positive anchors/bonus pools were reconstructed read-only from compatible
stored measurements; no population scoring or new inference was performed.
Before-values were verified against the stored v2 scores. Old global ranks are
not reused as features; new ranks were NOT calculated. Machine-readable point
changes: [regression JSON](STEP3_BEST_RANKING_V21_REGRESSION.json).

| Evidence group | Frame | v2 | v2.1 | Why changed / remaining limitation |
| --- | --- | ---: | ---: | --- |
| EYE | Sasha_v08_011 | 78.242 | 63.886 | Half-eye severity, same-eye presence/detail concern, less eye credit |
| EYE | Sasha_v08_004 | 76.770 | 62.801 | Expected near-eye concern and half-eye; raw state does not prove closed eyes |
| EYE | Sasha_v05_003 | 69.209 | 66.085 | Weaker-eye positive credit; stored ROIs both MEASURED, so no invented failure |
| EYE | Sasha_v08_008 | 63.257 | 54.954 | Half-eye and reduced eye credit; presence/detail do not agree on the same eye |
| EYE | Sasha_v08_005 | 61.119 | 54.634 | Weaker half-eye, changed local-detail agreement and eye credit |
| BLUR / EXPOSURE | Sasha_v19_024 | 62.452 | 58.484 | Blur penalty0.154→1.355 plus eye-detail concern; haze evidence absent |
| BLUR / EXPOSURE | Sasha_v19_025 | 61.180 | 54.175 | Blur penalty0.679→2.765 plus eye-detail concern; haze evidence absent |
| EXPOSURE | Sasha_v33_006 | 61.506 | 59.975 | Detail agreement changes; dark penalty stays0 because information-loss bins do not agree |
| BLUR regression | Sasha_v44_019 | 60.666 | 54.136 | Corroborated eye/detail and blur deficits; blur2.623→4.092 |
| BLUR regression | Sasha_v30_010 | 57.637 | 48.858 | Corroborated eye/detail and blur deficits; blur3.337→5.437 |
| BLUR regression | Sasha_v63_020 | 39.534 | 35.465 | Half-eye/weak detail; no automatic Human Reject feature |
| Clean still reference | 652794808_18008722232838431_6335316425841053458_n.jpg | 88.437 | 88.409 | All penalties0; slight weaker-eye positive-credit difference |

Only current v2 Rejects and prior technical/reference examples were sampled.
No preference-only paint/upward example was targeted for automated correction.
v38 has no exact safely identified reviewed frame in the supplied current evidence;
no filename or source-wide substitute was invented.

## Unresolved observations

- Human-reported closed eyes in v08_004/008 measure BORDERLINE, not CLOSED. New
  scoring can lower poor usable-eye evidence, but cannot correct detector truth.
- v05_003 reports both ROIs measured and individual presence/detail do not jointly
  identify a failed eye. Suspected extraction failure remains unconfirmed.
- v19_024/025 brightness~159/~150, contrast~70/~67, dynamic range102/106, clip0:
  existing haze bins do not establish haze despite the user's visual observation.
- v33_006 brightness~61, contrast~60, dynamic range110: darkness is measured, but
  existing information-loss bins do not establish lost facial information. New
  arbitrary thresholds/scaling for those exposure examples were STOPPED, not guessed.
- Current local-eye detail can stay near/above its old anchor in a blurred upscaled
  face. Stronger calibrated canonical Tenengrad/mouth or directional evidence is
  unresolved. The 12-case comparison is not proof all blurred faces leave BEST.

## Minimum validation and scope

87 BEST unit/synthetic/regression tests + 8 config tests =95 PASS. Required15
invariants are covered, including source/review feature independence, open/half/
closed semantics, expected-eye failure, profile abstention, same-eye corroboration,
multi-detail blur, contrast-preserved darkness, actual exposure loss, missing vs0
and independent v2.1 Round1. Historical v2 semantics retain their own test module.
BAT --help PASS; no production processing. Numeric config values compared with
stored v2 settings are unchanged. Protected production ranking CSV/summary, all
review histories/feedback reports and preserved v2 code hashes are unchanged.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, both Project Rules,
relevant Current Knowledge, Decisions, Failures, Cases, History and prior results.
Knowledge Maintenance skill used for DEC-0019/supersession; no new empirical
quality-validity record is warranted. Data lineage preserved: YES. Full-row
preservation: YES in synthetic paths; actual1951 production rows untouched.
Historical evidence preserved: YES. Config SSOT preserved: YES. No Rule conflict.
STEP4+, source images, historical Human decisions and A/B/C unchanged.

Full production executed: NO. Production v2.1 candidate copies created: NO.

## ★maru next action

Run bat/03_step3_best_ranking.bat to publish best_rank_v2.1 from stored metrics.
Then inspect its summary and run bat/03_best_review_round.bat 1. Human Review
restarts at best_rank_v2.1 / Round1. v1/v2 Human Rejects remain regression history;
they are neither score inputs nor current shown exclusions.
