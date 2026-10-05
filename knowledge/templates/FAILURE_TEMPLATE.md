---
id: FAIL-xxxx
title: [Short Descriptive Title of Failed Approach]
date: YYYY-MM-DD
confidence: [HIGH | MEDIUM | LOW]
components:
  - [Component affected]
tags:
  - [Tags]
related_experiment: EXP-YYYYMMDD-xxx
related_decision: DEC-xxxx
---

# Failure Record: [ID] - [Title]

## 1. Context & Objective
[What problem were we trying to solve, and what was the goal?]

## 2. The Attempted Approach
[What specific algorithm, threshold, or pipeline modification was implemented?]

## 3. Why It Looked Reasonable at the Time
[Explain the initial theoretical or intuitive justification for why this approach seemed sound.]

## 4. Observed Failure (Facts)
- **Measured Metrics**: [Specific numbers, scores, drop in quality]
- **Human Evaluation**: [Visual artifacts, loss of realism, identity drift]

## 5. Root Cause Analysis (Interpretation)
[Technical explanation of why this approach fundamentally broke down under real-world conditions.]

## 6. Conditions Where It Failed
- [Condition 1: e.g., All social media video sources]
- [Condition 2: e.g., High-frequency skin regions]

## 7. Conditions Where It May Still Work (Edge Validation)
- [Any theoretical niche where this approach might not fail, if any]

## 8. DO NOT RETRY UNLESS (Mandatory Guardrail)
> [!CRITICAL]
> **Do NOT re-attempt this approach unless all of the following conditions are met:**
> 1. [Prerequisite condition 1]
> 2. [Prerequisite condition 2]

## 9. Superseded By / Counter-measure
[What solution was ultimately implemented to resolve this failure?]
