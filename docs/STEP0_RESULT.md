# STEP 0 Result

## Status
PASS — configuration migration completed. Full production inference is unverified;
the environment preflight correctly reports existing missing prerequisites.

## Changed Files
- `config/config.example.yaml`, `config/config.schema.json`, `requirements.txt`
- `scripts/extract_frames.py`, `score_blur.py`, `face_quality_gate.py`,
  `classify_face_pose.py`, `face_deduplication.py`, `evaluate_identity.py`,
  `score_lora_candidates.py`, `prepare_human_review.py`,
  `selective_restoration.py`, `package_flux_dataset.py`, `verify_environment.py`
- All Step00–10 BAT entrypoints and `bat/run_all.bat`; `_common.bat` unchanged
- `README.md`; `knowledge/current/README.md` and its five existing policy documents;
  `knowledge/decisions/README.md`; `history/README.md`

## Added Files
- `scripts/common/__init__.py`, `scripts/common/config.py`
- `tests/test_config.py`, `tests/pre_ssot_defaults.json`
- `knowledge/current/configuration.md`
- `knowledge/decisions/DEC-0006-config-single-source-of-truth.md`
- `history/HIST-006_CONFIG_SSOT.md`
- `docs/STEP0_VERIFICATION.json`, this report
- Execution workspace only: ignored `config/config.yaml`, local audit logs,
  pre-migration script copies and a reproducible synthetic comparison runner

## Config Architecture
Explicit CLI > local YAML > internal fallback. Missing local YAML loads the
example. Partial local YAML leaves omitted settings on code fallbacks. Shared
loader validates YAML/schema and resolves relative config/CLI paths from root;
absolute source paths and UTF-8/Windows paths are supported. Relative traversal
is rejected. `@reports/` and `@candidates/` follow shared directory settings.

The execution workspace is a code/document copy with its own private config;
it uses the user's existing sibling `original-mp4` directory (71 supported videos).
Source videos/images were neither copied nor processed for training.

## Existing Behavior Preserved
- Extraction count 50, trims 0.5/0.5 and all six existing video extensions
- Global/face Laplacian 25/50; eye 1.6; plasticity 45; texture 0.050/0.035
- Pose yaw 15/42, pitch +/-20, extreme pitch/roll 35
- Dedup pHash 10, angle 12, frame window 6
- DINO model and dynamic identity gates
- Step7 65 candidates and existing fixed quota maps/scoring algorithm
- Step8 45 initial images, displayed 18/62/20, final human guidance 30–45
- Existing Step9 restoration criteria/rollback and Step10 CLIP/caption logic
- `docs/VALIDATED_BASELINE.md` unchanged; no empirical numbers rewritten

## Documentation Updated
README configuration/priority/migration guide, current knowledge and indexes,
DEC-0006 and HIST-006. Existing policy pages now explicitly distinguish actual
implementation from intended InsightFace, quotas, restoration masks and buckets.

## Tests
- test: lightweight unittest suite on source and execution copies
  result: PASS, 8 tests; all ten real CLI declarations checked without AI imports
- test: synthetic Step2 before/after comparison
  result: PASS, identical CSV bytes
- test: synthetic Step7 before/after comparison (147 input rows)
  result: PASS, 65 selected, identical CSV/scores/selection/copied files
- test: synthetic Step8 before/after comparison
  result: PASS, 45 selected, identical files and normalized console output
- test: Python compilation and Git diff whitespace check
  result: PASS
- test: baseline hash/content comparison
  result: PASS; SHA256 in `STEP0_VERIFICATION.json`
- test: real Step00 BAT in execution workspace
  result: correctly exits 1; system Python 3.10 lacks MediaPipe/imagehash;
  Torch is CPU-only; reference count is zero. YAML/schema/FFmpeg pass.

## Existing inconsistencies fixed
YAML/schema now reflect consumed runtime values. Candidate pool, initial review
and final guidance are separate. BAT output type claims now match CSV; non-existent
HTML claims removed; effective paths are reported by the Python step. Unescaped
echo ampersands and repeated hardcoded frame-count display claims were removed.

## Deferred to later STEP
- Step1 scene-aware extraction
- Step3 TikTok blink / mouth metrics
- Step4 body visibility
- Step6 DINO → InsightFace
- Step7 quota redesign
- Step8 HTML dashboard
- Step9 restoration redesign / component mask policy gap
- Step10 caption cleanup / aspect buckets
- Step11 trained LoRA evaluation

## Risks / Notes
No model download, GPU inference or full real-data pipeline rerun was performed.
Existing profile-priority quota edge cases and the ineffective Step8 population
flag were preserved. Historical intended policy conflicts remain documented.
Old never-consumed YAML keys now fail schema validation; migrate from the new
example. Explicit relative CLI paths now consistently resolve from project root.
Reference photos have not been inferred from arbitrary images: confirmed subject
references are still needed before Step6. Dependencies must be completed before
`run_all.bat` can pass Step00. Changes are local and have not been committed/pushed.

STEP 1へ進める状態: READY (for the next implementation step and standalone frame
extraction; full `run_all` readiness remains blocked by environment prerequisites).
