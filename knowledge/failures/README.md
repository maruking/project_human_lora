# Failure Records Index

This directory documents **failed approaches, false hypotheses, and discarded methods**.  
The primary goal is to prevent future developers and AI agents from repeatedly proposing solutions that have already been empirically proven ineffective or harmful.

---

## Failure Ledger

| ID | Title | Component | Observed Failure | Do Not Retry Unless |
| :--- | :--- | :--- | :--- | :--- |
| **`FAIL-0001`** | [Whole-Face Neural Restoration](file:///./FAIL-0001-whole-face-codeformer.md) | Step 09 (Restoration) | Replaces real camera pores with plastic AI sheen; ruins photorealism. | Pores and fine skin microstructure can be generated with ground-truth fidelity without hallucination. |
| **`FAIL-0002`** | [Global-Blur-Only Frame Selection](file:///./FAIL-0002-global-blur-only-selection.md) | Step 02 (Blur Metric) | Retains frames with sharp backgrounds but completely out-of-focus faces. | Target faces occupy >= 90% of the entire frame consistently. |
| **`FAIL-0003`** | [Top-Score Unconstrained Greedy Selection](file:///./FAIL-0003-frontal-only-selection.md) | Step 07 (Selection) | 90%+ frontal bias causing LoRA angle-lock (cannot generate profile/body shots). | The objective is an avatar headshot LoRA with no requirement for body or profile angles. |

---

## Critical Requirement: "Do Not Retry Unless"
Every failure record contains an explicit prerequisite condition. If an AI agent or human proposes an approach listed here, they must first demonstrate that the prerequisite condition has been satisfied.
