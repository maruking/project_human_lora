# Empirical Experiments Index

This directory archives reproducible experiment records, benchmark logs, and empirical data points.  
Experiments record **facts and measurements** first, separating quantitative results from human and theoretical interpretations.

---

## Experiment Ledger

| ID | Title | Date | Status | Sample Size | Primary Finding |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`EXP-20260930-001`** | [Equidistant Frame Extraction Validation](file:///./EXP-20260930-001-equidistant-frame-sampling.md) | 2026-09-30 | VALIDATED | 82 MP4s (3,607 frames) | 50 segments captures full wardrobe & lighting diversity while reducing frame count by 92% vs 30fps. |
| **`EXP-20261001-002`** | [Beauty-Filter & Plasticity Gate Benchmark](file:///./EXP-20261001-002-beauty-filter-plasticity.md) | 2026-10-01 | VALIDATED | 3,607 frames | Successfully rejected 749 heavily filtered frames (20.8%) including Case 0001 (`Sash_v5_013`), leaving 1,911 high-quality frames. |

- [EXP-20261002-001 — Technical image metrics](EXP-20261002-001-technical-image-metrics.md), 3,550 images; formula/provenance/replay validated.

- [EXP-20261002-002 — Duration-aware extraction](EXP-20261002-002-duration-aware-extraction.md), 71 videos, variable counts and safe reuse.

- [EXP-20261002-003 — Current-generation technical metrics](EXP-20261002-003-current-generation-technical-metrics.md), 2,001 current PNG; exact coverage, old-formula regression and replay.

- [EXP-20261002-004 — STEP2 CSV report aggregation](EXP-20261002-004-step2-report-aggregation.md), 71 video/7 distribution rows; 75 tests, deterministic derived reports, frozen measurement.

- [EXP-20261002-005 — STEP3 full-generation face audit](EXP-20261002-005-step3-full-audit.md), 2001 rows; unchanged Gates, full lineage and deterministic replay.

- [EXP-20261002-006 — STEP3 calibration package](EXP-20261002-006-step3-calibration-review.md), derived analysis and180-frame review; accuracy awaiting human labels.

- [EXP-20261002-007 — REJECT-only boundary review](EXP-20261002-007-step3-reject-boundary-review.md),45 unique frames,81 Gate labels; production data unchanged, accuracy pending.

- [EXP-20261002-008 — Revision A diagnostics](EXP-20261002-008-step3-revision-a-diagnostics.md),138 rows, separate A/B/C and preservation verified; metric accuracy inconclusive.
