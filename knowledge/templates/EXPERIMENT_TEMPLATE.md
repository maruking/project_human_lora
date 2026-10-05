---
id: EXP-YYYYMMDD-xxx
title: [Short Descriptive Title of Experiment]
date: YYYY-MM-DD
hypothesis_status: [VALIDATED | REFUTED | INCONCLUSIVE]
confidence: [HIGH | MEDIUM | LOW]
components:
  - [Component, e.g., face-quality]
tags:
  - [e.g., benchmark, plastic-skin]
related_decisions:
  - DEC-xxxx
related_failures:
  - FAIL-xxxx
related_cases:
  - CASE-xxxx
---

# Experiment Record: [ID] - [Title]

## 1. Objective & Hypothesis
- **Objective**: [What question are we testing?]
- **Hypothesis**: [What do we expect will happen?]

## 2. Experimental Setup
- **Code Revision / Script**: `[e.g., scripts/face_quality_gate.py]`
- **Dataset / Inputs**: `[e.g., 3,607 extracted frames from 82 real MP4s]`
- **Environment**: `[OS: Windows, Python 3.10.11, CPU / GPU: CUDA]`
- **Parameters Tested**:
  ```yaml
  [Parameter block]
  ```
- **Execution Command**:
  ```cmd
  [Exact reproducible CLI command]
  ```

## 3. Measured Results (Facts)
- **Quantitative Metrics**:
  - Total Samples Evaluated: `[count]`
  - Passed / Retained: `[count (%)]`
  - Rejected: `[count (%)]`
  - Rejection Breakdown:
    - [Reason 1]: `[count]`
    - [Reason 2]: `[count]`
- **Statistical Distribution**:
  - Metric A Min / Max / Mean / Median: `[...]`

## 4. Human Visual Evaluation
- **True Positives**: [Were high quality targets properly retained?]
- **False Positives**: [Did any unwanted/low-quality samples slip through?]
- **False Negatives**: [Were any genuine high-quality samples mistakenly rejected?]

## 5. Interpretation & Conclusions
[Technical analysis connecting observed numbers to the hypothesis.]

## 6. Resulting Actions
- [Did this trigger a new Decision, Failure, or Case record?]
