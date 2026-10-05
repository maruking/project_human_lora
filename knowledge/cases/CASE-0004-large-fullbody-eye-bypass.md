---
id: CASE-0004
title: Large FULL_BODY face bypassing measured eye presence failure
date: 2026-10-03
confidence: MEDIUM
components: [face-quality]
tags: [eye-presence, full-body, applicability]
related_experiment: []
related_decision: DEC-0015
related_failure: []
---

# CASE-0004 — Large FULL_BODY eye-presence bypass

Observed existing official canonical192 CSV: Sasha_v03/Sasha_v03_118.png,
FULL_BODY, face_min_dimension545px, FaceMesh=true, left/right presence0.000/0.000,
eye_presence_valid=false, canonical19245.705250786410438,
face_eligible=true, reason=eligible, diagnostic_state=PASS.
This case was reported by the user and confirmed by reading stored CSV; no inference rerun.

Interpretation: shot_type alone bypassed the Hard Gate despite measurable face scale.
The approved correction applies existing individual presence validation at the configured
upper-body size regime irrespective of shot. The regression fixture requires
one_eye_occluded/REJECT, preserving individual evidence. It does not establish biological
occlusion accuracy from one stored heuristic case or change canonical thresholds.

Fixture: tests/fixtures/step3_large_fullbody_eye_presence.json;
test: tests/test_step3_review_gaps.py. Minimum synthetic validation only.
