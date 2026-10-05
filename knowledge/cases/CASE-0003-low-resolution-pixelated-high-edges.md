---
id: CASE-0003
title: Low Resolution Pixelation With High Edge Metrics
date: 2026-10-02
confidence: LOW
components: [technical-metrics, face-quality]
tags: [pixelation, low-resolution, counterexample]
related_experiment: []
related_decision: DEC-0008
related_failure: FAIL-0002
---

# Case Record: CASE-0003

## Input and source
User-reported historical sample: `02_Sash_v1_014.png`.
The exact historical input/crop was not supplied for this STEP2 run. It has not
been equated with a newly extracted frame with a similar name or frame index.

## Reported facts (not newly measured)
User reports: image 464x848; face approximately 103 pixels; global Laplacian
approximately 102; face Laplacian approximately 135. User visual assessment:
soft/pixelated face. These approximations and assessment are attributed to the
user, not an automated STEP2 face crop, recalculation or new validation result.

## Interpretation
Pixel boundaries, compression and sharpening may produce strong derivatives
without recovering perceptual facial detail. A high global or face-crop Laplacian
value alone therefore does not prove suitability. This is a hypothesis informed
by a single reported case; artifacts and broader experiments are still needed.

## Action
Record resolution and global metrics; do not hard-reject or accept the sample by
these values. STEP2 introduces no face-crop, detection or new quality gate.
See CASE-0002 for the separate sharp-background/defocused-face counterexample.
