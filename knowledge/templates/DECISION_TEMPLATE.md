---
id: DEC-xxxx
title: [Short Descriptive Title]
status: [PROPOSED | EXPERIMENTAL | ACCEPTED | REJECTED | SUPERSEDED]
date: YYYY-MM-DD
confidence: [HIGH | MEDIUM | LOW]
components:
  - [e.g., face-quality, pose-classification]
tags:
  - [e.g., sharpness, blur, beauty-filter]
supersedes: []
superseded_by: []
related_experiments:
  - EXP-YYYYMMDD-xxx
related_failures:
  - FAIL-xxxx
related_cases:
  - CASE-xxxx
---

# Decision Record: [ID] - [Title]

## 1. Context & Problem Statement
[Describe the problem encountered, why existing approaches failed, and the driving motivation.]

## 2. Previous Approach
[How was this handled previously before this decision?]

## 3. Hypothesis
[What was hypothesized would solve the problem?]

## 4. Alternatives Considered
- **Option A (Chosen)**: [Description]
- **Option B (Rejected)**: [Why rejected]
- **Option C (Rejected)**: [Why rejected]

## 5. Decision & Implementation
[Exact description of what was accepted, implemented, and configured.]

## 6. Reasoning & Evidence
- **Fact / Observed Metrics**: [Data points, benchmark results, experiment IDs]
- **Interpretation**: [Why this evidence justifies the decision]

## 7. Consequences
- **Positive**: [Benefits gained]
- **Negative / Trade-offs**: [New constraints, execution time increase, dependencies]

## 8. Validated Conditions (Works When)
- [List specific operational bounds where this decision is confirmed to work]

## 9. Known Limitations (Unreliable When)
- [List bounds where this decision degrades or fails]

## 10. Counterexamples
- [List any cases from knowledge/cases/ that test the boundaries of this decision]
