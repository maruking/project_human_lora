# STEP6 Identity Verification v2 implementation — 2026-10-05

## Result / scope

Execution: implementation and minimum validation complete. Reference-only GPU
preflight PASS (7 confirmed anchors). Full candidate production executed: **NO**.
Algorithm validity: state/lineage/publication logic tested synthetically; current
candidate identity accuracy, FAR/FRR and impostor separation **not validated**.
Human calibration: reference anchors explicitly placed by ★maru; candidate
identity Human Review pending production. No STEP7+, quotas, quality scoring,
A/B/C decisions, source edits or duplicate fallback promotion.

## Changed

- scripts/common/identity_v2.py: independent identity kernel, InsightFace runtime,
  reference audit, normalized centroid/anchor bank, IoU association, state logic.
- scripts/step6_identity_v2.py: strict STEP3/4/5 input audit, reference-only phase,
  prior reference PASS/hash gate, full-row output, isolated partial/error audits,
  source-linked HTML, summaries, archive/atomic publication/rollback.
- bat/06_evaluate_identity_gpu.bat: new v2 entrypoint and dedicated interpreter.
- bat/setup_step6_identity.bat, requirements-step6.txt, requirements-step6.lock.txt:
  reproducible Python3.10 setup with exact dependency constraints.
- config/config.yaml, config/config.example.yaml, config/config.schema.json:
  v2 backend/frozen boundary/reference policy/explicit paths; active legacy dynamic
  settings removed. config/step6_identity_legacy_dino.json retains prior template.
- tests/test_step6_identity_v2.py, tests/test_config.py: new tests/current defaults
  plus preservation of archived DINO model expectation.
- .gitignore: STEP6 advisory lock; existing .venv*/ protection covers local environment.
- PROJECT.md, README.md, docs/README.md, Current Knowledge/indexes, DEC-0023:
  current routing, scoped evidence and independent BAT operational path.
- Derived reference-only artifacts: output/reports/step6_reference_audit.csv,
  step6_reference_summary.json, docs/STEP6_REFERENCE_AUDIT.md,
  docs/STEP6_REFERENCE_REVIEW.html. No source copies.

STEP6 version: step6_identity_v2.
Legacy runtime audit: DINO generic embedding, pose/shot dynamic boundary,
center-upper fallback crop and old schema. evaluate_identity.py preserved unchanged;
the normal STEP6 BAT never runs it.

## Runtime / references

Backend: InsightFace0.7.3 / buffalo_l, ONNX Runtime-GPU1.23.2, RTX4090 CUDA.
Dedicated .venv-step6 has include-system-site-packages=false. Existing STEP2–5
packages remain intact. Python's built-in venv launcher files were absent;
virtualenv was installed as a user-level setup tool to create the dedicated environment.
Dependency check passes with no broken requirements in STEP6 environment.

Initial GPU session load succeeded, but first actual inference exposed missing
cuDNN sublibrary search paths. Windows DLL directories plus PATH now include the
environment's NVIDIA bin directories. Silent ORT provider fallback is disabled.
Corrected actual GPU reference inference succeeds; CPU trial values are not the
formal reference audit. No CUDA toolkit or existing model weights were overwritten.

Reference design: user-confirmed images only, minimum3/maximum20, no auto injection
of supplemental stills/ranked frames. Each anchor: decode, exactly one face,
finite nonzero embedding, bbox/detection score/source SHA/model/library/dimension
provenance. Independent-byte anchors only, pairwise matrix and leave-one-out audit.

Reference count:7 total /7 valid /0 invalid /0 outliers. Reference preflight:PASS.
Reference consistency (GPU LOO cosine): min0.6627492630, median0.6990476401,
max0.7623835238. These describe only the seven references, not candidate performance.
Full reference audit records all exact values.

Identity threshold: historical_identity_threshold=0.55, inherited user policy.
Not empirically tuned, no current-generation FAR/FRR guarantee. No DINO threshold
transfer (0.62/0.58/0.52), no pose/face-scale relaxation.

## Inputs / states / outputs

Candidate target pool:1079 current rows =877 UNIQUE +202 REPRESENTATIVE.
STEP5 connection: current COMPLETE step5_dedup_v2; full1951 rows, duplicate801,
upstream fatal71. Counts are metadata observations, never constants in runtime.
Preflight verifies current STEP3 BEST2.2/STEP4 v2 hashes/IDs/lineage/inherited data,
STEP5 summary/hash/role/cluster integrity, all source existence and target bbox.
Production validates **all source byte hashes** before candidate inference;
target decode also rechecks hashes/dimensions. Reference audit inventory/model/version
and artifact hashes must match; reference embeddings are rebuilt with the same backend.

Identity state logic:
- IDENTITY_PASS: centroid>=0.55 and unambiguous measurement.
- IDENTITY_REVIEW: centroid below0.55 but max anchor>=0.55, or multi-face association.
- IDENTITY_REJECT: valid measurement, centroid and max both below0.55.
- IDENTITY_NOT_EVALUABLE: no usable face/embedding, never artificial similarity0.
- NOT_APPLICABLE_DUPLICATE_MEMBER / NOT_APPLICABLE_UPSTREAM / UPSTREAM_ERROR:
  full audit survives, no representative result copied onto members.

Multi-face: unique positive maximum IoU against persisted primary bbox, never
largest/center/first/identity-best-face. Tie/no-overlap STOP and isolated failed audit;
no new arbitrary IoU threshold. No center-upper fallback. Representative REJECT or
NOT_EVALUABLE sets cluster_identity_fallback_needed, never auto-promotes members.
Pose/face-scale handling: stored pose_bin/yaw/pitch/roll/face_scale_bin remain context;
missing remains missing. best_score/quality/rank/review are not identity features.
identity_rank is descriptive centroid/max/frame-ID ordering only.

Review output: source-linked STEP6_IDENTITY_REVIEW.html groups REJECT / REVIEW /
NOT_EVALUABLE plus20 lowest PASS similarities; original image links and requested
lineage/quality-context/identity fields. Identity calibration only; no image copies.
STEP6_REFERENCE_REVIEW.html audits anchors. HTML is never runtime/source input.

Full-row preservation: all upstream identities/columns survive; asserted for1951-row
input contract and synthetic runs. New production CSV has not been produced by Codex.
Production CSV/summary and human reports are published together with prior backups,
individual atomic replacement, completion marker last and caught-failure rollback.
Multi-file process-crash atomicity is not guaranteed; hashes reveal interruption.
--limit even above target size remains PARTIAL in isolated audit directories.
Failed inference cannot overwrite successful production. Reference reports have
the same archive/atomic mechanism; rerunning preserves prior reference evidence.

STEP7 boundary: no quotas,35–45 selection, source caps, still/video rebalance,
identity override by quality, restoration or training. Runner retains STOP afterSTEP5.

## Minimum validation

- 34 STEP6 unit/synthetic/tiny-image tests PASS. Cover all28 requested cases plus
  ambiguity stop, invalid embeddings, source-linked HTML, caught publication rollback
  and actual mocked partial CLI publication leaving previous full files unchanged.
- 8 config tests PASS, schema validation and legacy snapshot expectation.
- STEP6 dedicated pip check PASS; CUDA real reference detection/recognition PASS.
- Actual BAT --preflight-only PASS: current1951 rows /1079 targets, no image inference.
- Actual BAT --reference-preflight-only PASS: seven anchors only, no candidate inference.
- Full candidate production executed:NO; STEP7+ executed:NO.

Rules checked: root AGENTS.md, .agents/AGENTS.md, PROJECT.md, Pipeline/Data Lineage
rules, relevant Knowledge/Decisions/Failures/Cases/History/experiments and maintenance skill.
Data lineage preserved:YES. Full-row preservation:YES for input contract/synthetic
outputs; full production not executed. Historical evidence preserved:YES.
Config SSOT preserved:YES. No rule conflicts. README/current/Decision updated;
Failures/Cases/Experiments/History checked, no new separate record required for
bounded installation troubleshooting or candidate accuracy not yet measured.

## Unresolved / next action

Candidate inference runtime duration and actual identity outcomes await ★maru.
Current threshold remains a historical starting boundary, not measured correctness.
Fresh Windows install may require InsightFace build tooling if no matching wheel
is available; the current machine used its cached cp310 Windows wheel successfully.
No browser visual QA beyond source-link/metadata structure validation.

★maru: run bat/06_evaluate_identity_gpu.bat for production. Afterwards share
docs/STEP6_IDENTITY_SUMMARY.md and docs/STEP6_IDENTITY_REVIEW.html with Chappy.
For future reference changes, first rerun BAT with --reference-preflight-only.
