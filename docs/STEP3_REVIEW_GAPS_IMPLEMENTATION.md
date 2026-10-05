# STEP3 eye applicability / review diagnostics revision

Implementation status: complete; unit/synthetic validation only. Full batch executed: NO.
Production Gate accuracy / Human Calibration: pending ★maru rerun and Chappy review.

## Scope and preserved evidence

Current authoritative formal input is the standardized 4K STEP1 generation (1893 video frames,
67 videos; generation bd72f194f62260fb728b77b26c75c5491b178908bff53393e197c11137bf9a40).
Existing official STEP3 CSV/summary are prior-run evidence, not new revision results. They were
read only; source images, Human Review, A/B/C, historical outputs and downstream decisions
were not rewritten. No image inference/production processing was executed.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md,
.agents/rules/lora_pipeline_rules.md, .agents/rules/data_lineage_rules.md;
Current Knowledge, Decisions, Failures/Cases/History and prior STEP results reviewed.
Data lineage preserved: YES. Full-row preservation: YES by synthetic full-universe tests;
production universe not rerun. Historical evidence preserved: YES. Config SSOT preserved: YES.
Rule conflicts: none; exclusion-only guards in common inventories are required to keep
review outputs out of STEP2/STEP4+ inputs; their measurement/classification algorithms are unchanged.

## Changed files

Runtime / entry / SSOT:
- .gitignore (private temporary review copies only; CSV reports remain tracked)
- scripts/face_quality_gate.py
- scripts/common/step3_gate_policy.py
- scripts/common/step3_audit.py
- scripts/common/step3_review.py (new)
- scripts/common/revision_a.py
- scripts/step3_revision_a_diagnostics.py
- scripts/common/config.py
- scripts/common/metric_generation.py
- scripts/common/metric_report.py
- scripts/common/step2_inputs.py
- scripts/build_step1_image_inventory.py
- scripts/select_revision_b.py (inventory exclusion only; selection rules unchanged)
- bat/03_face_quality_gate.bat
- config/config.yaml
- config/config.example.yaml
- config/config.schema.json

Tests / case evidence:
- tests/test_step3_review_gaps.py (new)
- tests/test_step3_canonical_gate.py (individual eye evidence added to synthetic fixture)
- tests/fixtures/step3_large_fullbody_eye_presence.json (new, observed pre-revision case)

Documentation / memory:
- docs/STEP3_REVIEW_GAPS_IMPLEMENTATION.md (this file)
- docs/README.md
- README.md (scoped current STEP3 note/diagram)
- knowledge/current/face-quality.md
- knowledge/current/configuration.md
- knowledge/decisions/DEC-0014-canonical192-face-gate.md (supersession metadata; body preserved)
- knowledge/decisions/DEC-0015-eye-applicability-review-outputs.md (new)
- knowledge/decisions/README.md
- knowledge/cases/CASE-0004-large-fullbody-eye-bypass.md (new)
- knowledge/cases/README.md

## Eye occlusion applicability

`eye_presence_gate_state=APPLICABLE` requires detected FaceMesh, finite individual left/right
presence ratios, measured validity and `face_min_dimension >= args.min_face_dim_upper_body`.
The existing configured upper-body minimum (currently110px) is reused; no new size cutoff.
Applicable invalid presence adds `one_eye_occluded` regardless of shot_type. Smaller faces
record SKIPPED_INSUFFICIENT_SCALE; unavailable measurements record
NOT_APPLICABLE_MISSING_MEASUREMENT; no face records NOT_APPLICABLE_NO_FACE.
Errors record REJECT review state, never review PASS.

The biological presence formula still tests minimum individual evidence, average evidence
and asymmetry. It is not replaced by openness, an average or a new formula.

Observed existing CSV case: Sasha_v03/Sasha_v03_118.png, FULL_BODY, face minimum545px,
left/right presence0.000/0.000, mesh=true, presence_valid=false, canonical19245.705250786410438;
old eligible=true / reason=eligible / diagnostic PASS. The recorded case fixture now
requires one_eye_occluded / REJECT. This is a policy regression test, not new inference or
human accuracy validation. Filename appears only in case/test evidence.

## Shared diagnostic measurements, never new Hard Gates

Shared Revision A eye_metrics / pixel_metrics formulas and native face oval mask are reused.
Revision A A/B/C and diagnostic semantics are unchanged. `review_diagnostic_config` is
optional in STEP3 config (CLI --review-diagnostic-config overrides); null uses existing
config/step3_revision_a.local.json, then config/step3_revision_a.example.json if local absent.
Explicit missing/invalid JSON fails, rather than silently substituting bins.
Path and SHA256 of settings are recorded for each row. Existing JSON bin values were not changed.

Eye columns: left/right_eye_open_ratio, eye_open_min, eye_open_asymmetry,
eye_openness_state, half_eye_suspected. Existing left/right presence and eye openness
columns remain. CLOSED_OR_BLINK/BORDERLINE openness are review concerns only.
Exposure: face_highlight_clip_ratio, face_bright_region_ratio, face_dynamic_range,
face_exposure_state, face_exposure_roi_method, overexposure_white_haze_suspected.
Face oval convex hull is measured at native pixels; missing mesh uses explicit bbox fallback.
Skin/detail outputs from Revision A are not introduced as Hard Gates or substituted for
existing production skin metrics. Dynamic range is context; no new haze rejection formula.
These heuristics do not prove blink, beauty filtering, white haze or LoRA suitability.
Unavailable exposure diagnostics record an error/UNKNOWN and a review concern; they never
create an eligibility Hard Reject.

Review state:
- REJECT: not officially eligible (including processing errors).
- BORDERLINE: eligible and EYE_DETAIL+SKIN_PROCESSING, or half-eye/blink concern,
  or exposure concern (including unavailable exposure measurements needing review).
- PASS: eligible without those review concerns.
Native global/native face blur alone never forces BORDERLINE. No A/B/C is assigned.
Canonical192 formula/threshold36.901392 and retained no_face/multiple_faces,
visibility, size/resolution, underexposure/backlight/hair formulas/cutoffs remain unchanged.
Only eye-presence applicability and separate review grouping change.

## Disposable review outputs and failure behavior

Every complete successful normal STEP3 run (without requiring --copy-review) creates:
- configured reports/passed/<source-relative-path>: diagnostic PASS copies only.
- configured reports/borderline/<source-relative-path>: diagnostic BORDERLINE copies only.
Reject images are not included in these folders. Copies preserve raw source paths/pixels.
Full audit CSV continues retaining every row. Supplemental stills remain on the existing
Revision A path and are not silently added to the official formal STEP3 universe.

Owned staging copies are completed before official publication; both old review directories
are retained in owned staging until the official report publisher returns successfully.
Copy/swap/report exceptions restore both prior directories. Failed inference or --limit
partial runs never enter temporary review publication. Old review sets in that situation
still correspond to the previous successful run; consult the current successful report,
not a failed diagnostic attempt. No source/other existing report/archive folder is cleaned.
Only the two authorized destination directories and this function's owned staging are refreshed.

This is exception-safe rollback, not a power-loss-atomic multi-directory transaction.
If process termination or rollback failure occurs, owned staging can retain recovery data;
do not claim newly published review directories are authoritative evidence.

Configured review paths, conventional reports/passed and reports/borderline, their aliases
and owned review staging are excluded from formal/supplemental recursive inventories.
Shared input-path guards reject them as explicit image/source inputs across normal STEP
CLIs. STEP4+ still consumes authoritative CSV rows/raw paths; no candidate pool is created.
The fixture confirms deleting copies changes neither formal identities nor generation hash.

## Summary outputs and minimum validation

Normal STEP3 summary and Markdown report now expose official eligible and review PASS /
BORDERLINE / REJECT counts, half-eye and exposure concern counts, eye-presence applicable /
skipped-insufficient-scale counts; all diagnostic columns/reasons remain in the full CSV.
Production counts will be obtained only after ★maru reruns the BAT.

Validation:113 unit/synthetic tests PASS (27 new review regressions, plus existing canonical,
STEP3 audit, config, Revision A, technical metrics, Revision B and STEP1 integration tests).
Tests cover recorded large FULL_BODY bypass, threshold applicability boundary, independent
presence evidence/unchanged minimum-average-asymmetry, shared real analysis wiring with
mocked detector/mesh, half-eye/exposure diagnostic-only semantics, existing Hard Reject
precedence, native blur alone, canonical threshold/resize preservation, exact group copies,
stale refresh, copy/report/second-swap rollback, successful/failed/partial main control flow,
input exclusion and deletion-independent generation. All images/output mutations were
controlled synthetic fixtures in temporary folders. No real passed/borderline folders refreshed.

README/Current/Decisions/Failures/Cases/Experiments/History reviewed. New scope warrants
Decision/Case/current/result updates only; no new empirical experiment/failure/history record
is claimed from synthetic validation. Earlier records remain readable.

Full batch executed: NO. STEP3 production inference / Revision A / STEP4+ not executed.

★maru
bat\03_face_quality_gate.bat を実行してください。
実行後 output\reports\passed\ と output\reports\borderline\ を確認してください。
Chappyが新しいSTEP3結果を確認するまで03_revision_a_diagnostics.batを実行しないでください。
