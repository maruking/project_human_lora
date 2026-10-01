---
id: CASE-xxxx
title: [Short Descriptive Title of Case / Counterexample]
date: YYYY-MM-DD
confidence: [HIGH | MEDIUM | LOW]
components:
  - [Component, e.g., face-quality]
tags:
  - [e.g., beauty-filter, blur-anomaly]
related_experiment: EXP-YYYYMMDD-xxx
related_decision: DEC-xxxx
related_failure: FAIL-xxxx
---

# Case Record: [ID] - [Title]

## 1. Input & Source
- **Image Identifier / Sample**: `[Identifier, e.g., Sash_v5_013]`
- **Video Source**: `[Source descriptor, e.g., TikTok Vertical 1080x1920]`
- **Resolution / Crop**: `[e.g., 240x240 face crop from 1080x1920 frame]`
- **Artifact Reference**: `[Relative path to report or visual review dashboard]`

## 2. Relevant Metrics (Facts)
- Global Blur Score: `[value]`
- Face Sharpness: `[value]`
- Skin Texture Score: `[value]`
- Plasticity Ratio: `[value]`
- Identity Cosine Score: `[value]`

## 3. Expected Behavior vs. Actual Behavior
- **Expected**: [What standard heuristics or existing thresholds anticipated]
- **Actual**: [What human visual inspection or reality actually revealed]

## 4. Why This Case Matters
[Explain why this specific instance is significant and what rule it challenged.]

## 5. What Rule or Assumption It Breaks
[Identify the false assumption, e.g., "Assumed high gradient = high photographic detail".]

## 6. Technical Interpretation
[Analysis of the optical, algorithmic, or compression phenomenon causing the anomaly.]

## 7. Action Taken / Resolution
[How the pipeline, code, or thresholds were adjusted in response to this case.]
