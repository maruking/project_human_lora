# Single-Gate Boundary Calibration Fix

Status: PASS

Active samples:

- Eye Sharpness: 3
- Face Laplacian: 13
- Eye Presence: 0
- Skin Texture: 0
- Plasticity: 3
- Visibility: 3
- Exposure: 3
- Face Size / Resolution: 0

Eligible included: 0

Multi-hard-gate failures included: 0

Authoritative STEP3 CSV changed: NO
Gate thresholds changed: NO
Gate formulas changed: NO
STEP4+ changed: NO

## Scoped Verification
25 unique frames/17 videos; each has exactly one target, target FAIL and all
other applicable hard gates PASS. Global Blur has0 isolated boundary samples.
Current-generation preflight validates2,001 frames/71 videos, policy2.
Face Laplacian has66 available isolated boundary candidates;13 are sampled using
the existing small per-category review maximum. Other available counts equal
the active counts. No quota-filling or fallback samples are used.

Selection checks both blur predicates independently, even though production
records only one face_blurry reason through if/elif. Thus an eye boundary with
low face Laplacian is excluded. Eye-presence invalidation commonly also produces
an eye-sharpness failure; no waiver is introduced to obtain presence examples.
Beauty components are separated; ambiguous attribution at rounded thresholds is
excluded, using the existing CSV precision and saved beauty flag. These checks
change only the review selection; no production formula or threshold is modified.
Grouped exposure and size/resolution targets require the failing component itself
near its threshold; another component cannot supply the boundary membership.

UI displays Calibration Target, Target FAIL and Other Hard Gates ALL PASS.
Each image has one Gate question. Human answers are not applied to machine data.
117 Python tests PASS, including sparse/no-fill, multi-failure, masked blur and
beauty-cause isolation invariants. Synthetic DOM verifies one question per frame,
target metadata, label reload and JSON/CSV export. All25 actual sample invariants
and frame ID uniqueness are verified;3,068 protected hashes match, including raw
images, config, manifests, production Gate/STEP4+ source and full STEP3 CSV/summary.
Evidence: output/reports/step3_single_gate_audit/sample_invariants.json and verification.json.
Browser visual QA remains unperformed because file access is blocked by browser policy.

The previous45-frame package6f379c92773278f1 is preserved under
output/reports/step3_boundary_audit/superseded/6f379c92773278f1/, including its
summary, manifest and label sidecar. Its assets and browser namespace remain;
[historical UI](STEP3_BOUNDARY_REVIEW_SUPERSEDED_6f379c92773278f1.html) is retained.
Previous180-frame debug material is also retained. No human answers are migrated
to the new single-target package. Active output names remain compatible.

Changed files: scripts/build_step3_boundary_review.py,
scripts/templates/step3_boundary_review.html, tests/test_step3_boundary_review.py,
tests/check_step3_boundary_exports.cjs, active HTML/boundary outputs and minimal
README/Current/result routing. No unrelated optimization or new calibration mode.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md,
.agents/rules/lora_pipeline_rules.md, .agents/rules/data_lineage_rules.md;
Current face quality, accepted DEC-0002/0003/0006/0011, FAIL-0002, CASE-0003,
prior STEP3/calibration result and HIST-015 reviewed.
Data lineage preserved: YES. Full-row preservation: YES (2,001 source;25 review).
Historical evidence preserved: YES. Config SSOT preserved: YES.
README/Current/result updated only to describe this correction. Decisions, Failures,
Cases, Experiments and History checked; no new records required for this narrow fix.
No rule conflict. No threshold tuning or STEP4 work. STOP after this fix.
