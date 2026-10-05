---
id: DEC-0014
title: Canonical192 face-core sharpness and diagnostic-only native signals
status: SUPERSEDED
date: 2026-10-03
confidence: MEDIUM
components: [face-quality, configuration, lineage]
tags: [canonical-scale, sharpness, diagnostics]
supersedes: [DEC-0002, DEC-0003]
superseded_by: [DEC-0015]
related_experiments: []
related_failures: [FAIL-0002]
related_cases: [CASE-0002]
---

# DEC-0014 — Approved canonical192 face Gate

## Decision / authorization

The user explicitly approved implementing canonical face-core Laplacian for the standardized STEP1 4K pipeline. Use existing face/core ROI, resize a measurement copy with preserved aspect ratio: AREA shrinking, CUBIC enlargement, IDENTITY copy. Existing Laplacian variance and native/eye/skin/plasticity formulas are retained. Canonical scale/threshold are STEP3 config SSOT settings; no eligible-count targeting.

Canonical sharpness is evaluated directly for each detected single-face row. Eye sharpness cannot mask it. Native global/face, eye/skin/beauty/plasticity become diagnostic-only. no_face/multiple_faces, FaceMesh/visibility, face size/resolution, exposure/backlight, hair/one-eye occlusion retain their predicates/thresholds. Missing/nonfinite required canonical measurement is an auditable analysis error, never PASS.

Separate diagnostic BORDERLINE requires no Hard Reject and both EYE_DETAIL and SKIN_PROCESSING. Skin/beauty/plasticity count as one correlated family; native blur is context only. BORDERLINE does not alter face_eligible=true and is not dataset-selection B. A/B/C/Human Review/downstream logic are unchanged. Diagnostic cutoffs retain legacy settings and explicit applicability/disabled states.

## Historical reference and measured evidence

- [Upscale audit](../../docs/STEP3_UPSCALE_RECALIBRATION_AUDIT.md) found native scale dependence.
- [Canonical experiment](../../docs/STEP3_CANONICAL_SHARPNESS_RESULT.md) compared matched OLD/NEW measurements. Face192 was most distribution-stable of the tested face scales; human ordering improved on the small face boundary set, with mixed global evidence.
- [Threshold transfer](../../docs/STEP3_CANONICAL192_THRESHOLD_TRANSFER.md) mapped historical native50 CDF to OLD canonical192 without human-label fitting.
- [Architecture simulation](../../docs/STEP3_GATE_ARCHITECTURE_SIMULATION.md) evaluated the approved policy without production inference. Its hypothetical counts are not actual new production counts or labeled accuracy.

## Implementation / validation boundary

[Implementation result](../../docs/STEP3_CANONICAL192_IMPLEMENTATION.md): canonical measurement, eligibility, diagnostic columns, schema/config/BAT and derived reporting implemented. Unit/synthetic checks only; full STEP3 BAT execution belongs to maru. Old decision bodies and official production reports remain historical evidence. This decision supersedes their Gate implementation, not source-pixel preservation or local-face-evaluation principles.

## Limitations / deferred work

Acceptance of architecture is distinct from empirical validation of every LoRA-quality decision. Resizing cannot recover lost native detail; bbox/upscaler/codec effects remain. Full production execution and Human Review are pending. No new restoration, eye/skin formula, A/B/C, selection, caption or training work.

Scoped successor: [DEC-0015](DEC-0015-eye-applicability-review-outputs.md) retains the canonical metric/threshold and updates eye applicability, review grouping and disposable outputs. This prior body records the original policy.
