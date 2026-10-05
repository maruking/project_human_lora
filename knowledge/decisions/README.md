# Architectural Decision Records (ADRs)

This directory catalogs all architectural, methodological, and algorithmic decisions made during pipeline development.  
Each record explains **why** a specific choice was made, what alternatives were considered, and under what conditions it remains valid.

---

## Decision Ledger

| ID | Title | Status | Date | Supersedes | Related Experiment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`DEC-0001`** | [Equidistant Video Frame Sampling](DEC-0001-equidistant-frame-sampling.md) | SUPERSEDED by DEC-0009 | 2026-09-30 | - | EXP-20260930-001 |
| **`DEC-0002`** | [Anatomical Face Sharpness Gate](DEC-0002-face-sharpness-gate.md) | SUPERSEDED by DEC-0014 | 2026-09-30 | - | EXP-20260930-002 |
| **`DEC-0003`** | [Beauty Filter & Plastic Skin Rejection](DEC-0003-beauty-filter-rejection.md) | SUPERSEDED by DEC-0014 | 2026-10-01 | - | EXP-20261001-002 |
| **`DEC-0004`** | [Selective Component Restoration with Raw Camera Skin Preservation](DEC-0004-raw-skin-preservation.md) | ACCEPTED | 2026-09-30 | - | EXP-20260930-004 |
| **`DEC-0005`** | [Multi-Objective Quota Balancing for LoRA Training](DEC-0005-pose-composition-quotas.md) | ACCEPTED | 2026-09-30 | - | EXP-20260930-003 |
| **`DEC-0006`** | [Config Single Source of Truth](DEC-0006-config-single-source-of-truth.md) | ACCEPTED | 2026-10-02 | - | Lightweight/synthetic validation |
| **`DEC-0007`** | [Stable Video IDs and Working Copies](DEC-0007-stable-video-ids-and-working-copies.md) | ACCEPTED | 2026-10-02 | - | STEP1 unit/real-data validation |

---

## Status Definitions
- `PROPOSED`: Under discussion; no production implementation yet.
- `EXPERIMENTAL`: Implemented and undergoing empirical validation.
- `ACCEPTED`: Active production architecture and standard practice.
- `REJECTED`: Formally considered and rejected based on empirical evidence.
- `SUPERSEDED`: Previously accepted, but replaced by a newer decision (referenced by ID).

- [DEC-0008 — Technical measurement without quality gates](DEC-0008-technical-measurement-without-quality-gates.md), SUPERSEDED by DEC-0010.

- [DEC-0009 — Duration-aware frame extraction](DEC-0009-duration-aware-frame-extraction.md), ACCEPTED; supersedes DEC-0001 sampling.

- [DEC-0010 — Current-generation technical reports](DEC-0010-current-generation-technical-reports.md), ACCEPTED; supersedes DEC-0008 reporting contract.

- [DEC-0011 — Mandatory Project entry and full-frame lineage](DEC-0011-agent-entry-and-full-frame-lineage.md), ACCEPTED governance; legacy enforcement gaps are deferred.

- [DEC-0012 — Separate A/B/C selection groups](DEC-0012-separate-selection-groups.md), ACCEPTED user policy; provisional diagnostics do not finalize selection.

- [DEC-0013 — Revision B candidate proposals](DEC-0013-revision-b-candidate-selection.md), ACCEPTED user selection design; synthetic validation only, production pending.

- [DEC-0014 — Approved canonical192 face Gate](DEC-0014-canonical192-face-gate.md), SUPERSEDED by DEC-0015; canonical metric/threshold retained by successor. Original architecture and synthetic implementation evidence preserved.

- [DEC-0015 — Eye applicability / diagnostic review outputs](DEC-0015-eye-applicability-review-outputs.md), SUPERSEDED by DEC-0016; historical implementation preserved.

- [DEC-0016 — BEST relative ranking and durable review](DEC-0016-best-candidate-ranking.md), SUPERSEDED by DEC-0017 for v2 scoring and review extraction.

- [DEC-0017 — BEST v2 evidence-based penalties](DEC-0017-best-ranking-evidence-penalties.md), SUPERSEDED by DEC-0018; v2 scoring retained, review restart policy replaced.

- [DEC-0018 — Version-scoped BEST review](DEC-0018-version-scoped-best-review.md), SUPERSEDED by DEC-0019; version-scoped history design retained.

- [DEC-0019 — Generic eye quality / BEST v2.1](DEC-0019-general-eye-quality-best-v21.md), SUPERSEDED by DEC-0020; old implementation and review evidence preserved.

- [DEC-0020 — Balanced critical quality / BEST v2.2](DEC-0020-balanced-critical-quality-best-v22.md), ACCEPTED design; original decision records synthetic/9-case validation and then-pending production. Subsequent production/135-image review is recorded in [current Knowledge](../current/step3-best-ranking.md) and [review report](../../docs/STEP3_BEST_RANKING_V22_ROUND1_3_CHAPPY_REPORT.md); original Decision body/status unchanged.

- [DEC-0021 — STEP4 stored pose / authoritative face scale](DEC-0021-step4-stored-pose-face-scale.md), ACCEPTED user definition; measurement-only, synthetic/six-row validation. Historical DEC-0005 unchanged; STEP4 production pending ★maru.

- [DEC-0022 — STEP5 conservative duplicate clusters](DEC-0022-step5-conservative-dedup-clusters.md), ACCEPTED user architecture; full-row audit, BEST representatives, source-aware pHash and diagnostic pose review. Synthetic validation; full STEP5 production pending ★maru.
