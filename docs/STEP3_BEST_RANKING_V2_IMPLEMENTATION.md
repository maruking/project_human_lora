# STEP3 BEST Ranking v2 — implementation / minimum validation

Historical v2 implementation/evidence. Current operation is [best_rank_v2.1](STEP3_BEST_RANKING_V21_IMPLEMENTATION.md); v1/v2 review data remain unchanged.

Review policy update: [DEC-0018 / version-separated Round1 restart](STEP3_BEST_RANKING_V2_REVIEW_RESTART.md)
supersedes the original cross-version exclusion policy; scoring remains unchanged.

2026-10-04. Primary evidence: [v1 issue report](../backup/step3_approved_20261005_a8f7c74c/docs/STEP3_BEST_RANKING_SCORE_ISSUE_REPORT.txt).
User explicitly authorized implementation, semantic tests and small stored-metric
checks only. This is an Algorithm Revision, not approval of production quality.

Execution status: synthetic/minimum checks only; production v2 ranking and review extraction
NOT executed by Codex. Algorithm validity: required semantic properties tested; real ranking
quality remains unvalidated. Human calibration: historical Round1/2 evidence retained;
new rankings await maru review. No new fatal thresholds or A/B/C decisions.

## Changed files

- scripts/common/best_ranking.py — best_rank_v2 scoring and still review guarantee.
- scripts/common/best_ranking_v1.py — exact previous source preserved for historical audit.
- scripts/common/best_review.py — v2 requirement for new extraction, minimum still slots.
- scripts/step3_best_ranking.py — stored-metric rescore, version checks, historical report copy,
  rank-only default, explicit extraction and mode-specific completion messages.
- bat/03_face_quality_gate.bat — remove misleading fixed Round1 completion message.
- config/config.yaml, config/config.example.yaml, config/config.schema.json — v2 settings.
- tests/test_step3_best.py, tests/test_step3_best_v2.py,
  tests/fixtures/step3_best_v2_counterexamples.json.
- This report and STEP3_BEST_RANKING_V2_REFERENCE_CHECK.json,
  STEP3_BEST_RANKING_V2_COUNTEREXAMPLE_CHECK.json.
- README.md, PROJECT.md, knowledge/current/face-quality.md,
  knowledge/current/configuration.md, knowledge/decisions/README.md,
  DEC-0016 successor metadata and DEC-0017-best-ranking-evidence-penalties.md.

## Main score and common normalization

BEST_SCORE = absolute_quality_total + relative_quality_bonus - penalty_total.
All three totals and v2 *_penalty / contribution_* fields are score POINTS.
*_abs fields and penalty_strength_* are bounded [0,1] factors.
Historical v1 contribution/deduction columns were fractions; ranking_version
distinguishes these meanings. Round1/2 snapshots retain v1 values unchanged.

Default shares from config: common quality90%, small kind-specific bonus10%.
Preserve the existing positive weights: sharpness .20 (equal Laplacian/Tenengrad),
eyes .15, mouth .10, contrast .15, visibility .15, size .10, exposure .15.
Per-kind percentile is used only for positive bonuses, never for a penalty.
Exposure has no relative bonus; its .15 bonus weight stays unused, so the actual
maximum relative bonus is8.5 points. It is not redistributed to other components.

Canonical Laplacian/Tenengrad, eye detail, mouth detail and local contrast use one
combined non-fatal universe with P5/P95 anchors. Clip to anchors and map linearly
to[0,1]. No kind-specific anchors on the main quality scale. Missing stays blank;
a constant metric pool maps to0.5 as uninformative positive evidence, not a defect.
Anchors/counts are published in summary. They are positive score scaling only.
The name absolute_quality means a common comparison scale, not an independently
calibrated physical/photographic quality unit; anchors change with the dataset.

Visibility uses its existing natural0..100 domain directly. Size uses the measured
face_area_ratio in the combined P5/P95 domain, replacing raw face pixels so mere
upscaling does not earn size points. This is a size preference, not a pose quota.
Exposure quality is1−max(clipping,haze,shadow strengths), when all are measurable.
Incomplete paired sharpness/eye metrics attenuate contributions by coverage;
missing contributions are not renormalized upward or recorded as measured zero.

## Penalties: direct evidence only

defect_evidence() receives one measured row plus existing semantic settings;
it has no access to percentile pools or common positive anchors. Every penalty
has an evidence_* reason and penalty_strength_* factor. Unknown evidence produces
blank *_penalty, zero deduction contribution and explicit unavailable status.

The existing penalty budgets are retained. Obstruction .15 is split equally into
visibility and eye concern. Clipping/haze .10 is split equally. Blur .15,
half-eye .10, shadow .10, low contrast .10, uncertainty .10 remain their budgets.
No preference-only paint/product/upward-pose rules were added.

- Visibility obstruction: (100−visibility)/100, bounded. Visibility100 produces0.
  This is still a visibility proxy, not detection of surrounding hats/backgrounds.
- Eye obstruction: legacy validity=true yields0. A weak concern is possible only
  with measured OPEN eyes, failed pixel-presence validity, a frontal yaw within
  the existing STEP4 front_yaw_max, and individual presence below the existing
  STEP3 min_single_eye_feature_ratio. Severity is the raw presence deficit times
  weak_evidence_scale=.25. Maximum eye penalty1.875 points. Asymmetry alone, pose
  asymmetry, group percentile, missing yaw, or unknown measurement cannot create
  this penalty. This cannot establish actual external occlusion.
- Half-eye: existing OPEN=0, BORDERLINE=.5, CLOSED_OR_BLINK=1 strength.
  UNKNOWN remains unavailable. No relative openness penalty and no fatal gate.
- Clipping: use the existing shared diagnostic clip_borderline/clip_overexposed
  bins as slack and full-strength endpoints. Current settings .02/.10:
  strength=clip((ratio−.02)/(.10−.02),0,1). Ratio0 and tiny values yield0.
  These are reused soft diagnostic bins, not newly approved rejection limits.
  An inconsistent NORMAL label cannot override directly large measured clipping;
  percentile never participates. Current stored diagnostic checksum is required.
- Haze: elevated actual brightness above existing bright_pixel_min (230), low
  dynamic range and low local contrast must all agree. Multiply brightness ramp
  toward255 by deficits of dynamic range and local contrast below the existing
  contrast_borderline_max (15, both are grayscale intensity-span units). This is
  a conservative provisional corroboration rule, not a validated haze detector.
- Shadow: measured shadow area fraction × brightness deficit below the existing
  STEP3 brightness anchor95 × local contrast deficit below15. A tiny shadow ratio
  has only a tiny possible effect; normal brightness/contrast give0 shadow penalty.
- Low contrast: direct local contrast deficit below existing diagnostic normal
  boundary15. No percentile or new Hard Reject.
- Blur: continuous deficits below existing canonical anchor36.901392 and eye
  detail anchor1.6. Use the second-largest deficit among canonical Laplacian,
  left eye and right eye: two actual measurements must agree. One weak metric
  alone cannot penalize; a high canonical edge value cannot conceal two weak eyes.
  Tenengrad/mouth remain positive quality/context because no calibrated defect
  boundary for those kernels is available. No new directional blur metric is
  invented. Blur penalty maximum15 points; no eligibility change.
- Uncertainty: .25 × unavailable positive-weighted coverage, under the retained
  .10 budget. Maximum2.5 points, not automatic maximum defect penalties.

Measurement kernels and fatal_reason() are unchanged; the latter is reused from
the preserved v1 module. Old numeric anchors above are diagnostic references for
soft ranking evidence only, not validated absolute defect truth or Hard Gates.

## Version transition and operation

Default bat/03_step3_best_ranking.bat -> normal03 BAT -> step3_best_ranking.py:
validate current STEP1/2 inventory/content and stored BEST checksum; reuse stored
measurements, fit common anchors and score v2. No inference by default. For a new
generation without compatible stored metrics, explicit --remeasure is required.
Measurement-setting or diagnostic-checksum mismatch stops reuse.

At future production publication, preserve the old CSV/summary by copying into
output/reports/step3_best_history/<old_version>_<csv_sha256>/ before replacing active
BEST reports. Existing archive bytes are never overwritten. New active report
has best_rank_v2; old Round1/2 records keep best_rank_v1 snapshots and decisions.
History bytes are not rewritten by rank-only operation. A per-file atomic replace
is used; this is not a power-loss-safe multi-file transaction. Checksum mismatch
stops reuse; archived prior reports remain available for recovery.

Ranking stops without copying a review batch. First inspect
output/reports/step3_best_ranking_summary.json and step3_best_ranking.csv.
Summary reports common anchors, effective evidence settings, version, top45 kinds,
top sources, distributions, fatal counts and existing review history.

Only after maru reviews the summary:

```powershell
.\03_best_review_round.bat 1
```

Review extraction refuses v1, stale settings, stale generation or checksum mismatch.
From unseen non-fatal rows, reserve the best10 supplemental stills (all remaining
if fewer), then fill globally. Stills can exceed10. Each video has soft cap4;
relax minimally only if needed to fill45, with shortage/relaxation recorded.
Score and global rank never change for the review guarantee. Review starts at
best_rank_v2 / Round1. Only previous rounds of the same ranking version exclude
shown IDs. v1 Round1/2 are read-only history and do not prevent reappearance.

New rounds receive v2 score snapshots; historical REVIEW_REJECT remains human evidence,
not a new fatal condition or source-specific scoring rule. No source images move.

## Reference image: stored-metric check, not a full rerank

652794808_18008722232838431_6335316425841053458_n.jpg:

| Quantity | v1 | v2 |
| --- | ---: | ---: |
| Score | 41.002473 | 88.436829 |
| Common quality | n/a | 82.516995 |
| Relative bonus | n/a | 5.919834 |
| Total penalty, points | 23.853765 | 0 |
| Obstruction (v1 combined / v2 visibility+eye) | 6.805908 | 0+0 |
| Clipping/haze (v1 combined / v2 separate) | 5.041278 | 0+0 |
| Blur | 4.652778 | 0 |
| Shadow | 3.596491 | 0 |
| Low contrast | 2.368421 | 0 |
| Half-eye | 1.388889 | 0 |
| Uncertainty | 0 | 0 |

Stored metrics were read to fit the combined positive anchors; only this image and
13 selected counterexamples were scored. No full1951 scoring/rank sorting/inference
or production publication occurred. The reference's new global rank is UNKNOWN.
Score scales changed, so the numeric increase alone is not proof of improvement.
The semantic improvement here is removal of unsupported penalties and a common
positive quality domain. No filename-specific boost or guaranteed rank1.

See [reference evidence](../backup/step3_approved_20261005_a8f7c74c/docs/STEP3_BEST_RANKING_V2_REFERENCE_CHECK.json) and
[13 counterexamples](../backup/step3_approved_20261005_a8f7c74c/docs/STEP3_BEST_RANKING_V2_COUNTEREXAMPLE_CHECK.json).
Sasha_v44_019 receives2.623356 blur points; Sasha_v30_010 receives3.336879.
Sasha_v23/v34/v47 BORDERLINE diagnostics produce half-eye penalty5; OPEN rows do
not. Historical human rejects remain untouched even when their diagnostic says OPEN.
Sasha_v08_011 still scores78.241829 with only half-eye penalty5; external eye
obstruction is not established by the available proxies. This is an unresolved
detector limitation, not evidence that its human rejection is wrong.
Sasha_v03/v49 gain no paint/upward-preference rules; existing metric concerns may
still affect them. No stored v38/v63 or v10 image was newly inferred in this task;
their general failure patterns are covered by semantic synthetic properties.

## Verification and remaining limits

Required13 semantic properties are covered: perfect visibility, zero/tiny clipping,
OPEN eyes, valid presence, normal exposure, missing vs zero, common normalization,
minimum still visibility, video cap, historical exclusion, rejection preservation,
and preference neutrality. Existing inventory/copy safety tests remain in place.
Small synthetic migration verifies v1 archive preservation, unchanged history,
stored-metric-only scoring and no automatic Round3. Exact test results recorded
after the final check below.

The existing detectors can miss hair/eye occlusion, eye closure and directional
motion blur. Reused soft evidence anchors and weights still require human review.
Native eye/mouth metrics may retain scale/content sensitivity; common normalization
does not prove perfect physical comparability. Do not claim all rejected examples
will disappear from top ranks or that v2 is production-calibrated.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, both Project Rules,
relevant Current Knowledge, Decisions, Failures, Cases and prior implementation.
Data lineage preserved: YES. Full-row preservation: YES by contract/tests;
existing1951 production rows untouched in this task. Historical evidence preserved:
YES. Config SSOT preserved: YES. STEP4+ and A/B/C untouched.
Full production executed: NO. Round3 extracted: NO.

Final validation: 49 BEST tests + 8 config tests = 57 PASS. BEST BAT --help PASS.
Syntax and new-document links PASS. Protected production CSV, summary, review
history and feedback CSV SHA256 unchanged from pre-edit snapshots; Round3 folder
absent. Stored-metric check scored14 selected examples only (reference1 + others13).
No image inference or complete production scoring performed.
Failures/Cases/Experiments/History reviewed: no new quality-validity claims or
additional ledger records; DEC-0017 and this implementation report capture the change.
