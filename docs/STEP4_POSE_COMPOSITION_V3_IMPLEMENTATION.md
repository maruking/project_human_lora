# STEP4 Pose / Composition v3 — implementation and minimum validation

2026-10-05. Execution: implementation/limited verification complete; full production
pending ★maru. Algorithm: buffalo_l alternative approved by ★maru on the original
25-image comparison; no general accuracy claim. Human calibration: user-reported
25-image angle/distribution acceptance, not new image-quality/selection labels.

## Flow and changed files
`bat/04_classify_face_pose.bat` → existing `.venv-step6` →
`scripts/step4_pose_composition_v3.py` → `common/buffalo_pose.py` and
`common/pose_composition_v3.py`. Config local/example version is v3; schema accepts
historical v2 and active v3. All angle/face-scale thresholds remain unchanged.
Original v2 production Python and legacy FaceMesh estimator stay in place.

STEP3 hash/count/unique ID preflight → same original source SHA256 checked on
decode → buffalo_l detector640 / threshold0.5 and 1k3d68 CPU model using existing
weights → persisted STEP3 primary bbox unique maximal positive IoU association →
raw pitch/yaw/roll → current SSOT bins. No sign inversion, pitch folding or fallback.
Detector defaults mirror the comparison exactly; no unrelated recognition model
or embedding/identity operation. No model downloads or environment installation.

Full STEP3 universe is retained; fatal rows are not inferred. NO_FACE/ambiguous
pose stays NOT_EVALUABLE; decode/association/model errors retain ERROR rows and
exit nonzero. face_scale_bin, face geometry and BEST score/global rank unchanged.
Old STEP3 angles and status are recorded as step3_yaw, step3_pitch, step3_roll,
step3_pose_status; v3 yaw/pitch/roll/pose_status describe the new measurement.

Prior official STEP4 outputs are backed up only when ★maru runs production.
Individual atomic files with summary marker/hash last; not a global transaction.
Published ERROR summary means execution needs investigation, not production PASS.

## Minimum validation
- Formal BAT `--preflight-only`: current authoritative universe1951, no inference/output.
- `--comparison-check output/reports/step4_pose_estimator_comparison.csv`: exactly
  25 source/hash/generation-matched samples; maximum absolute angle delta0.0°;
  bins also match. No official reports published by this check.
- Known old failure Sasha_v23/Sasha_v23_001.png: yaw -0.892449 FRONTAL →
  -50.178444 PROFILE_LEFT; pitch22.464285, roll-26.181456.
- Synthetic full-row/fatal/error/missing evidence/old-angle preservation, unchanged
  score/geometry, boundary and rerun-publication tests. Config and retained v2 tests.

Full batch executed: NO. STEP1–3, best_rank_v2.2, sources, Human Review and STEP5+
remain unchanged. Source pixels/history/lineage/config SSOT preserved. Rules checked:
AGENTS.md, .agents/AGENTS.md, PROJECT.md and both pipeline/data lineage rule files.
Full-row preservation: synthetic PASS; production not executed. Diagnostic inference
subset25 only; current formal reports were not rewritten.

## Next action and downstream restriction
★maru runs only `bat/04_classify_face_pose.bat`, then shares
`docs/STEP4_POSE_COMPOSITION_SUMMARY.md` with Chappy. STEP5 remains v2-only and
will reject v3 reports; do not run STEP5+ or run_all until separately adapted.
The v3 driver has no production limit/subset publication option. CPU provider
preserves comparison reproducibility; full processing will take longer than the
previous stored-data classification. No performance/accuracy promise is made.
