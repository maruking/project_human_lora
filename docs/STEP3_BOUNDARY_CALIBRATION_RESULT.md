# STEP3 Boundary Calibration Set Revision

> Historical45-frame set: superseded by the scoped
> [Single-Gate Boundary Fix](STEP3_SINGLE_GATE_BOUNDARY_FIX.md). Previous evidence is retained.

## Status
READY_FOR_HUMAN_BOUNDARY_REVIEW

## Total Review Frames
45 unique images. Only current REJECT rows; no extreme-only or diversity filler.

## Eligible Included
0

## Boundary Samples
Gate memberships overlap; each image is displayed once.

| Boundary | Images |
| --- | ---: |
| Eye Sharpness | 14 |
| Face Laplacian | 16 |
| Eye Presence | 10 |
| Skin Texture | 11 |
| Plasticity | 8 |
| Visibility | 6 |
| Exposure / Backlight | 7 |
| Face Size / Resolution | 5 |
| Global Blur | 4 |

Beauty boundaries cover 14 unique images in total; some overlap skin/plasticity.
Approximate per-Gate targets are exceeded slightly by shared boundary memberships
(Face Laplacian16, combined Beauty14); review still contains only45 unique frames.
Eye bands1.20–<1.40 /1.40–<1.50 /1.50–<1.60 /1.60–1.70 contain3/3/4/4.
Laplacian bands25–<35 /35–<40 /40–<45 /45–<50 contain4 each.
No fabricated or fallback non-boundary samples. Recorded settings are used as
Gate thresholds; user-requested review windows do not change production settings.
Requested windows are scaled relative to recorded settings for generic reuse.
Eye invalid/missing states and FULL_BODY are excluded from measured eye boundaries.
Eye Presence includes only rejected presence heuristics with measured landmarks
near at least one feature/average/asymmetry threshold. Its rounded-source average
and asymmetry are reference calculations, not new production decisions.

## Duplicate Frames Removed
36 repeated Gate memberships collapsed:81 memberships ->45 unique frames.
This is presentation deduplication; no images or authoritative rows were deleted.

## Videos Represented
45 videos;1 image per represented video (configured review cap3).

## Authoritative STEP3 Data Changed
NO. All2,001 source rows, metrics, face_eligible and face_gate_reason remain intact.

## Gate Threshold Changed
NO. Formula, config, production code and STEP4+ unchanged.

## Ready for ★maru Boundary Review
YES

## Active Review and Labels
[Review](STEP3_CALIBRATION_REVIEW.html) replaces the active180-frame UI. Header
explains REJECT boundary calibration and explicitly excludes final selection.
Every card shows value, recorded threshold, PASS/FAIL (UNKNOWN/N/A when appropriate),
meaning and actual rejection use. The eye/face if/elif branch is respected: a low
face Laplacian is not called the executed cause when the eye branch fired.
Beauty OR-attribution remains uncertain from rounded values and is marked accordingly.

Only relevant boundary Gates are questioned. ACCEPT/REJECT/UNSURE mean human
acceptability of that Gate boundary, not image adoption and not machine eligibility.
45 images produce81 independent Gate questions/long-format label rows. Optional notes
are per Gate. JSON schema2/CSV exports include subject context, generation, video,
frame identity, human_gate_name, measured_value, threshold, human_accept and human_notes.
Input is initially empty. Browser-local storage uses a separate package namespace;
the old six-question labels are neither reinterpreted nor automatically applied.
No actual human labels were read, written or migrated by this revision.

Machine-readable artifacts under output/reports:

- step3_boundary_review.json: unique review frame manifest, memberships and explanations.
- step3_boundary_labels.csv:81 long-format Gate labels, blank initial human fields.
- step3_boundary_summary.json: active package, recorded settings, availability/counts.
- step3_boundary_assets/&lt;package&gt;/:45 byte-identical full copies and45 plain crops.
- step3_boundary_audit/verification.json: integrity/replay/static export evidence.

Regenerate with `py -3.10 scripts/build_step3_boundary_review.py --target 45 --video-cap 3`.
Populated sidecars are preserved for the same schema and rejected on package drift.
Browser input is saved locally; export JSON/CSV to retain a portable copy. Exported
labels are not automatically written into the initial server-side CSV or Gate data.

## Superseded Calibration Set
The previous180-image CSV, summary, assets, label namespace and result remain historical.
[Preserved180-frame HTML](STEP3_CALIBRATION_REVIEW_SUPERSEDED_fe12ba72980e02d4.html)
is an exact byte copy of the previous active UI. The old generator now refuses
to overwrite the active boundary UI; use the boundary generator above.
Earlier CALIBRATION_READY/109-test evidence remains historical, not current scope.

## Verification and Limits
114 Python tests PASS; synthetic fake-DOM tests validate REJECT-only rendering,
Gate-specific questions, independent labels, reload, legacy isolation and JSON/CSV
roundtrip. Preserved historical UI export tests PASS. All45 full copies match source
bytes; all45 face assets match plain existing crop logic. Repeated generation yields
identical94 active artifact bytes. All3,081 protected files, including2,001 raw images,
config, manifests, BAT and existing STEP3 reports match pre-change SHA256 hashes.
STEP1/STEP2/current raw generation preflight succeeds:2,001 images/71 videos/policy2.
Source CSV SHA256:2589176c4a2eb22d098a1f97500654cde0e0ce6dfda0873cdeac25893f6b0051.

Real-browser visual QA was not performed because the browser tool blocks file access;
no localhost or alternate-surface bypass was used. Static tests are not visual UI PASS.
No human acceptability or false-positive accuracy claim is made. Publication is atomic
per file, not a transactional multi-file commit. Boundary sampling is a small review
subset, not a representative accuracy estimate or universal dataset audit.

## Rules and Documentation
Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md,
.agents/rules/lora_pipeline_rules.md, .agents/rules/data_lineage_rules.md;
relevant Current Knowledge, ACCEPTED DEC-0002/0003/0006/0011, FAIL-0002,
CASE-0002/0003, STEP1/STEP3/calibration results and HIST-014 reviewed.
Knowledge Maintenance skill applied; no new architectural Decision, Failure or Case
is warranted before human evidence. README, Current Knowledge, Experiments and
History updated; existing Decisions/Failures/Cases checked, no update required.

Data lineage preserved: YES.
Full-row preservation: YES (2,001 authoritative rows;45 explicitly derived frames).
Historical evidence preserved: YES.
Config SSOT preserved: YES.
No rule conflicts. Gate tuning, automatic human-label application, final candidate
selection and STEP4+ remain deferred. Readiness is only for human boundary review.

Changed implementation: scripts/build_step3_boundary_review.py,
scripts/templates/step3_boundary_review.html, scripts/build_step3_calibration.py
(historical generator guard), tests/test_step3_boundary_review.py,
tests/check_step3_boundary_exports.cjs. Active HTML and new boundary artifacts added;
prior production results/config/formulas preserved.
