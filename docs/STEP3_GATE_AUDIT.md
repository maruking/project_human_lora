# STEP3 Revision 1 — Existing Gate Audit

Compared before implementation: local production source, config/config.yaml,
configuration and face-quality Current Knowledge, DEC-0002/0003/0006/0011,
FAIL-0002, CASE-0002/0003 and STEP1/STEP2 results. Local values below are observations
of current configuration, not a new source of settings. Historical intended values
remain in their original records. No Gate tuning is authorized in Revision 1.

| Metric / Gate | Production code fallback / literal | Local config | Historical Knowledge | Decision source | Enforced? |
|---|---|---|---|---|---|
| Global Laplacian | 25 | 25 | Historical global-only selection was rejected; STEP2 has no hard Gate | DEC-0002, DEC-0010, FAIL-0002 | Yes, STEP3 only |
| Face-core Laplacian | 50 | 50 | Historical local sharpness 18 used a different description/scale | DEC-0002 | Yes |
| Anatomical eye sharpness | 1.60 | 1.60 | No same-scale historical cutoff established | DEC-0002 | Yes for CLOSE_UP/UPPER_BODY; FULL_BODY uses face Lap |
| Face size | 140 / 110 / 80 px | Same | Historical min_face_size 120 px | DEC-0002; configuration.md implementation audit | Yes by provisional scale |
| FULL_BODY source short edge | 720 px | 720 | Historical not independently revalidated | Configuration SSOT DEC-0006 | Yes |
| Visibility | 70 | 70 | Historical occlusion ratio 0.35 is not this score | DEC-0002 | Yes |
| Eye feature presence | min 0.070, avg 0.080, max asymmetry 2.20 | Same | Not a scientifically confirmed hair/occlusion detector | Existing implementation; DEC-0002 scope | Yes except FULL_BODY |
| Central-face gradient | max 65 | 65 | Heuristic hair proxy; causal interpretation unvalidated | Existing implementation; DEC-0002 scope | Yes |
| Face brightness | min 95 | 95 | Current implementation evidence; not new threshold study | Existing implementation; DEC-0006 | Yes |
| Backlight ratio | min 0.65 when face brightness <105 and >=95 | 0.65; 105 is existing literal | No independent historical validation | Existing implementation; DEC-0006 | Yes |
| Cheek skin texture | min 0.050 CLOSE_UP / 0.035 UPPER_BODY | Same | Historical 15.0 and broader cheek/forehead/bandpass description differ | DEC-0003, HIST-003 | Yes; FULL_BODY skipped |
| Plasticity | eye sharpness / max(skin texture,0.005), max 45 | max 45 | Historical max 70; historical denominator 0.1 and face sharpness description differ | DEC-0003, HIST-003 | Yes; FULL_BODY skipped |
| Multiple faces | face_count !=1 | No independent configurable policy | Single-target policy | Existing code | Yes; largest clipped bbox used only for measurement |
| FaceMesh | required | No disable switch | Landmark proxy, not proof of unobstructed face | Existing code; DEC-0002 | Yes via low_visibility |
| Face sharpness percentile | min fallback 20 | 20 | Historical 18 is not this rank formula | Configuration audit | NO: value is configured but not used as Gate |
| Eye/mouth geometry | New provisional diagnostic bins only | No Gate setting added | No ground truth validation | Revision 1 request | Never eligibility Gates |

Unchanged formulas: face crop/core geometry; Laplacian variance; Sobel energy;
normalized anatomical patch gradients; cheek Laplacian divided by mean brightness;
plasticity denominator; visibility penalties; tied midrank percentiles. AST hashes
are frozen in tests/fixtures/step3_formula_baseline.json.

Missing FaceMesh leaves anatomical metrics blank and marks missing_landmarks. Its
legacy visibility score is zero with landmarks_not_found, an explicit failure proxy,
not normal visibility. Invalid eye presence disables eye sharpness to zero by the
existing formula; anatomical_metric_status explicitly records this disablement.

No additional SSOT Gate values were introduced. The existing fixed visibility
penalties and backlight brightness 105 remain kernel/policy literals and are audited;
migrating/tuning them is outside this validation. Diagnostic bins are disclosed
algorithm constants, not quality thresholds: blink min-eye ratio <0.10, mouth ratio
bins 0.03/0.15/0.35. Their accuracy is not validated. No semantic expression or speech
recognition is claimed.
