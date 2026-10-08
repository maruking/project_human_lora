---
topic: configuration
last_updated: 2026-10-02
confidence: MEDIUM
status: ACTIVE
related_decisions: [DEC-0006]
related_failures: []
related_cases: []
---

# Current Knowledge: Configuration Single Source of Truth

## STEP5 v2 SSOT — 2026-10-05

Explicit step5_dedup paths/version and frozen rules: phash_threshold10,
temporal_phash_threshold14 (64-bit Hamming distance), angle_threshold12 /
tight_angle_threshold8 (degrees), time_window6 (temporal_index distance, not
seconds). These are current config defaults, not independent Knowledge settings.
review_dir/representative copies are legacy; new HTML/summary paths are explicit.
No unrelated Gate/ranking setting changes. See
[DEC-0022](../decisions/DEC-0022-step5-conservative-dedup-clusters.md).

## STEP4 v3 — 2026-10-05

Active step4_pose_composition.version is step4_pose_composition_v3. Normal04 BAT
uses the existing .venv-step6 environment and the comparison-approved buffalo_l
CPU estimator. All step4_pose angle and face-gate scale thresholds are unchanged.
Paths remain unchanged; prior outputs archive on production publication. Schema
retains v2 compatibility for historical tests. See [DEC-0027](../decisions/DEC-0027-step4-buffalo-pose-v3.md).
STEP5 configuration is unchanged; its preflight now accepts v3 and validates
preserved STEP3 pose aliases (2026-10-06). STEP6+ was not changed in that bridge.

## Historical STEP4 v2 paths — 2026-10-05

step4_pose_composition adds output version and input/report/summary paths only.
Angle thresholds remain owned by step4_pose; face-scale area thresholds remain
owned by step3_face_gate. No numeric threshold changed or duplicated. Legacy
step4_pose input/output settings remain intact for historical classify_face_pose.py.
The normal STEP4 BAT now runs the stored-measurement v2 entrypoint. See
[DEC-0021](../decisions/DEC-0021-step4-stored-pose-face-scale.md).

## Current policy
Runtime settings are defined in `config/config.yaml`, loaded by `scripts/common/config.py`.
Explicit CLI > local YAML > internal fallback. If the local file is absent, load
`config/config.example.yaml`. A partial local file uses internal fallbacks for
missing settings, without merging the example. This preserves legacy discovery.

## Loading, validation and paths
Use `load_config`, `get_section`, `validate_config`, `resolve_project_path` and
`configure_parser`. All steps accept `--config` as an alternate file.
YAML and JSON Schema validation run before step argument defaults are applied.
PyYAML already existed; jsonschema was added. Invalid mappings, unknown keys,
bad types and out-of-range settings fail with an actionable error and nonzero exit.
Step00 additionally checks dependencies, FFmpeg/ffprobe, directory creation and
reference decoding/dimensions without loading identity models. Empty references
warn instead of blocking earlier steps; Step6 still requires reference images.

Relative paths, including explicit CLI paths, resolve from repository root;
escaping relative paths and ambiguous Windows drive-relative paths are rejected.
Absolute external input paths are allowed in ignored local configuration.
`@reports/` and `@candidates/` resolve from their corresponding shared path keys.
CLI paths themselves use normal filesystem notation, not these config tokens.

## Facts: defaults from config, not historical intended specifications
- STEP1 sampling: frame_extraction 2 FPS, max 120/video, policy_version 2; default trims zero. Fixed segment count was removed by DEC-0009.
- Step2 measures all images, retains legacy metrics/percentiles, and validates STEP1 IDs/counts; there is no standalone quality gate (DEC-0010). Summary/outlier paths are configurable; historical-row retention is prohibited (retain_missing_records permits false only).
- Step3 uses canonical192 face-core Laplacian as the approved Hard Gate; see DEC-0014 below. Native global/face 25/50, eye1.6, plasticity45 and skin0.050/0.035 remain diagnostics. Face dimensions140/110/80 remain Hard Gates.
- Step4 uses yaw 15/42, pitch +/-20, extreme pitch/roll 35.
- Step5 uses pHash 10, angle 12 and frame-index window 6.
- Step6 v2 uses InsightFace `buffalo_l`, fixed historical identity threshold0.55,
  confirmed references minimum3/maximum20 and explicit reference-only preflight.
  Legacy DINO dynamic settings are archived, not active v2 settings (DEC-0023).
- Legacy Step7 candidate pool default is 65; its old fixed maps remain preserved.
  Historical Revision B settings remain preserved. Normal STEP7 now uses
  `step7_candidates_v2`: target70 within60–80 review options, BEST quality only,
  minimum coverage/source caps; STEP8 final35–45. See DEC-0024.
- Step8 initial review default is 45, displayed percentages 18/62/20;
  final guidance is 30–45, controlled by human curation, not packaging truncation.
  No HTML dashboard currently exists.
- Step9 preserves the existing full-body face-crop restoration, feathering and
  rollback. The code does not implement the component-only mask promised by
  DEC-0004/current restoration policy. STEP0 neither endorses nor fixes this gap.
- Step10 preserves CLIP attributes, existing caption sentences and 16px alignment;
  it does not implement the example's former aspect buckets or artifact cleanup.

## Boundaries
Thresholds already defined as runtime constants/arguments, model names, device,
paths, quotas and CLIP prompt lists are configurable. Image kernels, landmark
geometry, scoring formulas and caption sentence templates remain algorithm code.
Fixed enum metadata identifies existing implementations rather than implementing
new backends. Do not independently redefine runtime defaults in BAT/docs.
When citing a value, identify it as a default value from config.

## STEP0 historical validation and limitations
Lightweight tests execute actual CLI declarations without importing AI models.
Pre-migration CLI/constants are frozen in `tests/pre_ssot_defaults.json`.
Synthetic comparisons verified Step2 CSV bytes, Step7 scores/selection/copied files
and Step8 selection/console output against the pre-migration scripts.
The original validated baseline file is unchanged. No GPU inference or full
production rerun was performed. Full pipeline validation requires dependencies
and confirmed references; no new empirical face-quality claims are made.


## Current STEP3 validation
STEP3 Revision1 now has full-generation execution/lineage evidence: [STEP3_RESULT](../../docs/STEP3_RESULT.md). Gate values remain unchanged. Isolated STEP3 dependencies prevent replacing the existing global STEP2 runtime. The earlier no-production-rerun statement applies to the historical STEP0 audit.


## STEP3 approved canonical update — 2026-10-03

[DEC-0014](../decisions/DEC-0014-canonical192-face-gate.md): STEP3 SSOT adds face_sharpness_canonical_short_edge=192 and min_face_laplacian_canonical=36.901392. Old min_face_laplacian=50 and min_global_laplacian=25 remain native diagnostic cutoffs, not Hard Gates. Eye1.6, skin.050/.035 and plasticity45 retain diagnostic meanings/formulas. CLI > YAML > documented compatibility fallback remains. Schema/CLI restrict the named canonical192 metric to short edge192. Production reports require maru rerun.

STEP3 review revision: optional step3_face_gate.review_diagnostic_config / CLI --review-diagnostic-config selects the existing Revision A JSON diagnostic bins. Null uses local then example; no bin value changed and these are not Hard Gate thresholds. JSON path/hash are audited per row. Eye presence reuses min_face_dim_upper_body; review copies use paths.reports_dir without an independent folder config. See [DEC-0015](../decisions/DEC-0015-eye-applicability-review-outputs.md).

## STEP3 BEST configuration (DEC-0016, 2026-10-04)

`step3_best_ranking` in config.yaml/example/schema is the new runtime section:
review_size45, max_per_video4, canonical_short_edge192, detector confidence,
measurement shadow bin and explicit positive/penalty weights. Positive weights
sum to1 (runtime validation). Historical step3_face_gate thresholds remain
unchanged but do not control BEST. Shared diagnostic JSON supplies measurement
bins only. New outputs/history live under configured reports_dir. See
[implementation report](../../docs/STEP3_BEST_RANKING_IMPLEMENTATION.md).

## Historical BEST v2.1 settings — DEC-0019

`step3_best_ranking.ranking_version=best_rank_v2.1`. All numerical settings remain
unchanged from v2: common quality .90, relative bonus .10, positive anchors .05/.95,
review45/minimum10 stills/cap4, weights and weak_evidence_scale .25. Existing eye
openness/detail/presence, brightness, contrast, clipping and yaw bins supply soft
ranking evidence, not new Hard Rejects. No new threshold is added. Eye measurement
and generic uncertainty split the existing uncertainty budget. Profile expectation
reuses step4_pose.three_quarter_yaw_max without changing STEP4 logic or that value.

Version-separated history starts v2.1 at Round1. v1/v2 decisions and shown flags
remain historical, never scoring features or current-version exclusions. Default
BAT rescoring uses stored measurements and stops before review copies. See
[DEC-0019](../decisions/DEC-0019-general-eye-quality-best-v21.md).

## Active BEST v2.2 settings — DEC-0020

`step3_best_ranking.ranking_version=best_rank_v2.2`. Numeric SSOT values are
unchanged. Equal geometric critical aggregation introduces no strength coefficient.
Existing min_face_dim_upper_body supplies saturating face-size quality reference
only. Existing contrast span and positive P95 references supply bounded quality,
not new physical Tenengrad/mouth/haze thresholds. See
[DEC-0020](../decisions/DEC-0020-balanced-critical-quality-best-v22.md).
Normal BAT reuses stored measurements and stops; Human Review starts Round1
independently of older versions. Historical Gate thresholds and STEP4 unchanged.

## STEP6 v2 SSOT — 2026-10-05

step6_identity declares step6_identity_v2/insightface/buffalo_l and explicit
reference/candidate audit paths. Schema forbids legacy dynamic thresholds/modifiers/
face_eligible settings when versionv2 is declared. Config defaults threshold0.55,
references3–20; no subject tuning. Legacy config snapshot: config/step6_identity_legacy_dino.json.
Dedicated environment dependencies: requirements-step6.txt and exact lock file.
See [DEC-0023](../decisions/DEC-0023-step6-insightface-identity.md).

## STEP7 v2 SSOT — 2026-10-05

step7_candidates_v2 owns review range/target, pose/vertical/scale minima, source caps and input/output paths. Defaults reflect DEC-0024 user specification, not new quality thresholds. Legacy step7_selection and step7_revision_b sections remain historical and unused by normal BAT. Identity has no scoring configuration because its selection weight is fixed0 in this architecture.

## Active STEP7/8 presentation SSOT — DEC-0028

step7_candidates_v2.version=step7_quality_coverage_v2.2. Target70 is immutable BASE;
Quality Guard multiplier2.0 stays. candidate_pool_max140 reflects additive options,
not a new quality threshold. Old core60/repair10 settings are archived in
config/step7_candidates_v21_legacy.json for historical tests. Coverage goals unchanged;
source caps6/15 are diagnostic only. Scores/identity/STEP3–6 settings unchanged.

step8_folder_review.version=step8_folder_review_v3. Paths and count35/40/45 plus
pose/scale/vertical guidance unchanged. VIEW categories come from inherited labels;
only99_ACCEPT determines acceptance. Old sessions preserved; explicit reset needed
for future migration, not performed in this task.

2026-10-07 Rare Profile supplement: step7_candidates_v2.rare_profile_review_target=3
(allowed2–3) controls profile-only top-up. Existing pose_min, scale_min, vertical_min,
BASE/guard settings unchanged. Pool max140 is not a removal gate; profile exceptions
may add beyond guard size. STEP8 preflight accepts only explicit eligible profile
exception rows outside guard. No STEP8 prepare or production result updated.

STEP9 diagnostic-only output paths added to step9_restoration: diagnostic_csv and
diagnostic_summary. Existing190px/2.0 settings unchanged; no new score/threshold.
Normal restoration BAT remains guarded; diagnostics read accepted rows only.

STEP10 input bridge uses existing step10_packaging.step9_report/restored_dir and
step8_folder_review authoritative paths. No new threshold or runtime setting.
--preflight-only exits before model/output processing; missing STEP9 selects originals
from STEP8_ACCEPT only. Caption/alignment settings unchanged (DEC-0029).

## Current Training Contract

config/config.yaml:training is the formal active Training Target. The example is
bootstrap only. Adapter/model/trigger/dataset/caption format+version/LoRA/target
values come from this section, not PROJECT or BAT. Project/training trigger mismatch
raises ConfigError. STEP10 prints the contract and refuses missing contracts without
historical-model fallback. Other STEPs retain partial-config compatibility.
External AI Toolkit YAML is not automatically synchronized; current external dataset
still references V1 and requires explicit future alignment before Training.
[Implementation/preflight snapshot](../../docs/TRAINING_CONTRACT_IMPLEMENTATION.md).
