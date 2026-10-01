# Architectural Decision Records (ADRs)

This directory catalogs all architectural, methodological, and algorithmic decisions made during pipeline development.  
Each record explains **why** a specific choice was made, what alternatives were considered, and under what conditions it remains valid.

---

## Decision Ledger

| ID | Title | Status | Date | Supersedes | Related Experiment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`DEC-0001`** | [Equidistant Video Frame Sampling](file:///./DEC-0001-equidistant-frame-sampling.md) | ACCEPTED | 2026-09-30 | - | EXP-20260930-001 |
| **`DEC-0002`** | [Anatomical Face Sharpness Gate](file:///./DEC-0002-face-sharpness-gate.md) | ACCEPTED | 2026-09-30 | - | EXP-20260930-002 |
| **`DEC-0003`** | [Beauty Filter & Plastic Skin Rejection](file:///./DEC-0003-beauty-filter-rejection.md) | ACCEPTED | 2026-10-01 | - | EXP-20261001-002 |
| **`DEC-0004`** | [Selective Component Restoration with Raw Camera Skin Preservation](file:///./DEC-0004-raw-skin-preservation.md) | ACCEPTED | 2026-09-30 | - | EXP-20260930-004 |
| **`DEC-0005`** | [Multi-Objective Quota Balancing for LoRA Training](file:///./DEC-0005-pose-composition-quotas.md) | ACCEPTED | 2026-09-30 | - | EXP-20260930-003 |

---

## Status Definitions
- `PROPOSED`: Under discussion; no production implementation yet.
- `EXPERIMENTAL`: Implemented and undergoing empirical validation.
- `ACCEPTED`: Active production architecture and standard practice.
- `REJECTED`: Formally considered and rejected based on empirical evidence.
- `SUPERSEDED`: Previously accepted, but replaced by a newer decision (referenced by ID).
