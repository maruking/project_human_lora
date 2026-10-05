---
topic: [Topic Name, e.g., face-quality]
last_updated: YYYY-MM-DD
confidence: [HIGH | MEDIUM | LOW]
status: ACTIVE
related_decisions:
  - DEC-xxxx
related_failures:
  - FAIL-xxxx
related_cases:
  - CASE-xxxx
---

# Current Knowledge: [Topic Name]

## 1. Current Policy
[Concise 2-3 sentence summary of the active standard policy.]

## 2. Recommended Approach
- [Primary method and step-by-step guidance currently in production]

## 3. Hard Rules (Enforced by Code)
- [Rule 1: Exact threshold or constraint]
- [Rule 2: Inviolable parameter]

## 4. Soft Rules (Guidelines for Human Review)
- [Visual inspection criteria or heuristic balance]

## 5. Validated Conditions (Works When)
- [Condition 1: e.g., Native camera footage >= 1080p]
- [Condition 2: e.g., Subject face size >= 120px]

## 6. Known Failure Modes & Limitations (Unreliable When)
- [Limitation 1: e.g., Heavy motion blur with specular highlights]
- [Limitation 2: e.g., Extreme profile poses beyond 80 degrees]

## 7. Do Not Use When
- [Anti-pattern or scenario where this approach breaks down]

## 8. Not Yet Validated
- [Unexplored conditions, e.g., Low-light iPhone night mode, Fisheye lenses]
