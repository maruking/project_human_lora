# STEP3 canonical192 approved Gate implementation — 2026-10-03

Execution status: IMPLEMENTED / UNIT-SYNTHETIC CHECKS PASS; FULL PRODUCTION NOT RUN.
Algorithm validity: user-approved architecture implemented; whole-dataset quality accuracy not claimed.
Human calibration: prior experiment/transfer/simulation retained; no labels/history/A/B/C changed.

## Official Gate and measurement

`face_laplacian_canonical_192` is now the official face-sharpness metric for detected single-face rows. STEP3 SSOT adds `face_sharpness_canonical_short_edge: 192` and `min_face_laplacian_canonical: 36.901392`. Below rejects with `face_blurry`; equality/above pass this Gate. This was explicitly approved by the implementation request; it is no longer only a simulation proposal in the code.

The same existing face/core ROI is measured on a copy: preserve aspect ratio with integer rounding; AREA shrink, CUBIC enlarge, IDENTITY copy. Existing grayscale/Laplacian variance formula remains. Native Laplacian/Tenengrad and percentile columns remain unchanged diagnostics. Canonical Laplacian/Tenengrad store round-trip precision rather than three-decimal rounding; metadata records scale, threshold, interpolation, measured dimensions and metric identity.

no_face, multiple_faces, low_visibility/FaceMesh, one_eye_occluded, face_too_small, low_resolution_source, face_underexposed, face_backlit_underexposed and hair_covered_face retain their formulas and cutoffs. Canonical is not applied to no-face/multiple-face decisions, although the latter may retain a primary-face measurement for audit. Missing/nonfinite canonical evidence on an applicable row becomes an analysis error with full-row preservation.

## Diagnostic-only signals

Native global/face blur, eye sharpness, skin texture, beauty flag and plasticity no longer independently reject. Legacy native50/global25 settings retain diagnostic meaning; old CLI options/columns remain compatible. `--skip-beauty-filter` remains accepted for compatibility but does not suppress measured evidence or affect eligibility.

Flags: global_blur_suspected, native_face_blur_suspected, eye_detail_suspected, skin_detail_suspected, beauty_filter_suspected, plasticity_suspected. Eye diagnostics require actual measured/presence-valid non-FULL_BODY data; disabled/missing zero proxies are explicit states. Skin-family concerns require applicable measured CLOSE_UP/UPPER_BODY. Correlated skin/beauty/plasticity flags count as one family. FULL_BODY plasticity can remain descriptive context.

`diagnostic_state=BORDERLINE` requires no Hard Reject plus EYE_DETAIL and SKIN_PROCESSING. Otherwise state is PASS or REJECT; errors are UNKNOWN. This indicator does not change eligibility: BORDERLINE retains `face_eligible=true`, `face_gate_reason=eligible`, `face_gate_category=ELIGIBLE`. Native blur context and a single family cannot force BORDERLINE. No A/B/C selection is created.

## Outputs and operational path

Normal entry point remains `bat/03_face_quality_gate.bat`. It invokes the existing Python path and failure propagation. The production analysis adds canonical measurement columns and metadata; full source fields/IDs/rejected rows and lineage/publication handling remain. Derived distribution/video summaries include canonical metrics; generated Markdown and summary JSON explicitly audit the new Gate/diagnostic policy. Historical reasons/categories stay supported for CSV-only reconstruction.

Existing official reports have NOT been regenerated and still reflect the previous Gate architecture. Existing automatic generation/report handling is preserved; Codex performed no report relocation/cleanup. maru must run the normal STEP3 BAT to produce current reports.

## Exact changed files

- scripts/face_quality_gate.py
- scripts/common/step3_gate_policy.py (new)
- scripts/common/step3_audit.py
- bat/03_face_quality_gate.bat
- config/config.yaml
- config/config.example.yaml
- config/config.schema.json
- tests/test_step3_canonical_gate.py (new)
- docs/STEP3_CANONICAL192_IMPLEMENTATION.md (this file)
- docs/README.md
- README.md
- knowledge/current/face-quality.md
- knowledge/current/configuration.md
- knowledge/decisions/DEC-0002-face-sharpness-gate.md (supersession metadata; historical body retained)
- knowledge/decisions/DEC-0003-beauty-filter-rejection.md (supersession metadata; historical body retained)
- knowledge/decisions/DEC-0014-canonical192-face-gate.md (new user-approved Decision)
- knowledge/decisions/README.md

## Minimum validation

37 unit/synthetic checks PASS across canonical Gate, existing STEP3 audit and configuration suites. Coverage includes validated-experiment resize equivalence for shrink/enlarge/identity, source-copy preservation, threshold below/equal/above, missing/nonfinite errors, each downgraded diagnostic, eye-mask removal, all retained hard predicates, independent/correlated diagnostic families, config/CLI precedence, full-row/source-column preservation, mocked-backend canonical output, distributions/summary policy, CSV-only rebuild and publication rollback. Both local/example schemas validated. Normal BAT --help exits successfully with new CLI arguments and no inference. ROI/native/eye/skin/visibility kernels and retained Hard Gate predicate blocks are AST-identical to the prior implementation. Official/prior-analysis artifact SHA256 checks passed. No real dataset inference was executed.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, pipeline/data-lineage rules, relevant Current Knowledge, accepted Decisions and Failure/Case/History/Experiment records; Knowledge Maintenance used for scoped policy supersession. Rule conflicts: none (user explicitly authorized the Gate changes).

Data lineage preserved: YES (synthetic full audit; real production pending). Full-row preservation: YES in synthetic validation; NO production rerun claimed. Historical evidence preserved: YES. Config SSOT preserved: YES. README/current Knowledge/Decisions updated; Failure/Case/History/Experiments checked, no new empirical claim or update required. Deferred: full production execution and quality review; downstream readiness is not claimed.

Not changed: source pixels, existing official/derived report evidence, Human Review, A/B/C, STEP2, STEP4+, restoration, captions, training, Git commit/push.

Full batch executed: NO.

★maru
bat\03_face_quality_gate.bat を実行してください。
