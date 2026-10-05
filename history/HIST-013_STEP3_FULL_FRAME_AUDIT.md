# HIST-013 — STEP3 Full Frame Audit

2026-10-02. STEP1/2 generation was already PASS. STEP3 still had a limit overwrite,
STEP2 step_name overwrite, legacy source-root fallback and success exit on analysis errors.
Revision1 fixes the audit/publication boundaries while preserving old formulas/Gates.
All2001 rows retain all36 STEP2 fields. Existing Gate finalization matches all measured
rows; repeat runs are byte-identical. Eligible62/2001, errors0; 94 tests PASS.

This is a computation/lineage audit, not a labeled accuracy experiment. Historical
threshold/formula differences remain explicit; no thresholds were tuned to raise the
3.10% eligibility rate. Review copies are optional/report-scoped; CSV is authoritative.
No STEP4+ processing or commit/push.

See [EXP-20261002-005](../experiments/EXP-20261002-005-step3-full-audit.md) and
[STEP3_RESULT](../docs/STEP3_RESULT.md).
