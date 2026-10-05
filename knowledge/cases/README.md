# Cases & Counterexamples Index

This directory documents concrete input frames, anomalous edge cases, and counterexamples that challenged, invalidated, or refined automated heuristics.

---

## Case Ledger

| ID | Title | Key Sample | Key Phenomenon | Resulting Action |
| :--- | :--- | :--- | :--- | :--- |
| **`CASE-0001`** | [Extreme Beauty-Filter Edge-Sharpness Anomaly](file:///./CASE-0001-sash-v5-013-beauty-filter.md) | `Sash_v5_013` | High Laplacian edge score (185+) due to filter sharpening, but zero facial skin pores (plastic/drawn appearance). | Implemented dual-bandpass plasticity filter in Step 03 (`DEC-0003`). |
| **`CASE-0002`** | [Sharp Background with Defocused Foreground Face](file:///./CASE-0002-sharp-bg-defocused-face.md) | `Sample_Dof_042` | High global Laplacian score (320+) driven by brick wall texture behind subject, while face was in soft focus. | Mandated local face crop Tenengrad gating in Step 03 (`DEC-0002`). |

- [CASE-0003 — Low-resolution pixelation/high edges](CASE-0003-low-resolution-pixelated-high-edges.md), LOW, user-reported.

- [CASE-0004 — Large FULL_BODY eye-presence bypass](CASE-0004-large-fullbody-eye-bypass.md), MEDIUM; stored CSV evidence and regression fixture, no new inference.
