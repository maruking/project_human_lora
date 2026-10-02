# STEP 3 Revision 1 Result

Date: 2026-10-02 (Asia/Tokyo). Authoritative local working tree; no commit/push.

## Status

**PASS — full-generation computation, lineage and reproducibility.** This does not
validate the precision/recall of the face-quality, occlusion or beauty heuristics.
Existing thresholds/formulas were retained. No STEP4+, identity, quotas, selection,
restoration, caption generation or training was run.

## Rules Checked

Read AGENTS.md -> .agents/AGENTS.md -> PROJECT.md ->
.agents/rules/lora_pipeline_rules.md and data_lineage_rules.md -> relevant Current
(configuration, frame organization, face quality, technical metrics) -> ACCEPTED
DEC-0002/0003/0006/0010/0011 -> FAIL-0002 -> CASE-0002/0003 -> STEP1_RESULT,
STEP2_RESULT, STEP2_REPORT_REVISION_RESULT, relevant History and Experiments.
Knowledge maintenance followed .agents/skills/knowledge-maintenance/SKILL.md.

Rules checked: YES. Full-row preservation: YES. Config SSOT preserved: YES.
Runtime CLI > local config > fallback; no subject-specific constants or fixed counts.
See [Gate audit](STEP3_GATE_AUDIT.md) for code/config/knowledge comparison.

## Input Generation

- Subjects: 1 configured local subject; generic code derives input from configuration.
- Videos: 71; frames: 2001.
- Active input: paths.raw_frames_dir -> work/frames_step1.
- Policy version 2, requested sample FPS 2.0, max frames/video 120.
- Generation SHA256: `fc2a37abc81e44e456891ac7d268c2dc622255d120c944ac377dbefd491833c2`.
- STEP2 CSV SHA256: `a133656bf487f1d1c7f1add08e5943420254ca8270c499b3a87ce2a4b5602a63`.

Validated formal STEP1 summary, both manifests, per-video extraction metadata,
exact relative filename inventory, per-video counts, frame sizes/content hashes,
policy/source hashes and STEP2 summary/provenance before and after inference.
The shared manifest lock protects STEP1/2/3 processing. Bare-basename joins and
alternate legacy image-root fallback are prohibited. Formal counts are metadata-derived.

## Full Row Integrity

| Check | Result |
|---|---:|
| STEP2 rows | 2001 |
| STEP3 rows | 2001 |
| Unique relative filenames | 2001 |
| Missing / duplicate rows | 0 / 0 |
| Preserved STEP2 columns | 36, every stored value identical |
| Processed / successful | 2001 / 2001 |
| Analysis error rows | 0 |

All rejected/no-face/multiple-face frames remain in CSV. Original step_name stays
STEP2; step3_step_name identifies the added evaluation. --limit writes a separate
.partial.csv and PARTIAL audit artifacts; it cannot replace the authoritative CSV.
Error rows retain values and analysis_error with error category; failed runs return
nonzero and isolate audit results without replacing good active reports.

## Face Detection Funnel

| State | Frames |
|---|---:|
| Face detected | 1924 |
| No face | 77 |
| Single face | 1921 |
| Multiple faces | 3 |
| Matched FaceMesh | 1719 |

Largest clipped bbox area, with first detection on ties, remains the primary-face
measurement method. FaceMesh is matched by nearest nose landmark to that bbox
center. This is not identity selection. Multiple-face rows remain rejected.
shot_type/provisional_face_scale_class is face-scale adaptation only, not STEP4 pose.

## Eligibility

Eligible: **62 / 2001 (3.10%)**.
Rejected: **1939 (96.90%)**.
No rejection deletes/moves any source image. No quota or desired pass rate influenced Gates.

## Rejection Reasons

Reasons overlap. Do not sum reason counts as a rejection total; exclusive primary
categories are separately retained in step3_reason_summary.csv.

| Reason | Frames | % of all frames | Videos |
|---|---:|---:|---:|
| analysis_error | 0 | 0.00 | 0 |
| beauty_filter_detected | 459 | 22.94 | 54 |
| eligible | 62 | 3.10 | 15 |
| face_backlit_underexposed | 24 | 1.20 | 5 |
| face_blurry | 1691 | 84.51 | 71 |
| face_too_small | 26 | 1.30 | 4 |
| face_underexposed | 218 | 10.89 | 23 |
| global_blurry | 953 | 47.63 | 41 |
| hair_covered_face | 0 | 0.00 | 0 |
| low_resolution_source | 281 | 14.04 | 18 |
| low_visibility | 241 | 12.04 | 40 |
| multiple_faces | 3 | 0.15 | 2 |
| no_face | 77 | 3.85 | 20 |
| one_eye_occluded | 595 | 29.74 | 59 |

## Face Metric Distribution

Full distribution CSV stores min, P01/P05/P10/P25/P50/P75/P90/P95/P99, max,
mean, population std, measured count, missing/N/A/error counts for 13 metrics.
Percentiles describe stored, rounded values, not latent unrounded kernels.
Face relative sharpness preserves historical midranks on successful single-face rows;
the configured min_face_sharpness_percentile=20 is **not an enforced Gate**.

| Metric | Measured | Missing | Median | P90 |
|---|---:|---:|---:|---:|
| face_laplacian_score | 1924 | 77 | 15.0265 | 60.6552 |
| face_tenengrad_score | 1924 | 77 | 1075.609 | 3085.6045 |
| face_sharpness_score | 1921 | 80 | 50.13 | 89.58 |
| eye_sharpness | 1719 | 282 | 0.0 | 2.823 |
| mouth_sharpness | 1719 | 282 | 1.763 | 3.4418 |
| face_visibility_score | 1924 | 77 | 100.0 | 100.0 |
| face_brightness_mean | 1924 | 77 | 122.3 | 146.07 |
| face_min_dimension | 1924 | 77 | 244.0 | 480.7 |
| face_area_ratio | 1924 | 77 | 0.05016 | 0.15668 |
| skin_texture_score | 1719 | 282 | 0.058 | 0.3272 |
| plasticity_ratio | 1719 | 282 | 0.0 | 49.54 |
| eye_openness_mean | 1719 | 282 | 0.324372 | 0.389968 |
| mouth_open_ratio | 1719 | 282 | 0.051935 | 0.280571 |

Missing FaceMesh leaves anatomical/geometry metrics blank. Legacy visibility returns
zero with explicit landmarks_not_found/unknown (not normal visibility). Invalid eye
presence disables eye sharpness to zero under the unchanged formula; the new
anatomical_metric_status distinguishes that disablement from ordinary measurement.
No silently inferred UPPER_BODY/FRONT states are introduced.

## TikTok Diagnostics

- Blink suspected: 2.
- Mouth open: 358; very open: 90.
- Eye/mouth geometry available: 1719; missing: 282.
- FULL_BODY beauty rejection skipped: 807.

Diagnostic-only bins: min eye openness <0.10; mouth ratio bins 0.03/0.15/0.35.
These are disclosed provisional geometric labels, not validated blink/speech/expression
classifiers and never new rejection conditions. Continuous ratios remain available.
No smile/neutral/laugh semantics, identity, pose or compression detector was added.

## STEP2 × STEP3 Cross Analysis

Stored global quality_rank; ceil(N × 0.10) gives 201 frames per tail.

| Tail | Frames | Eligible | Reject | Error | Face blurry | Beauty flag |
|---|---:|---:|---:|---:|---:|---:|
| global_bottom_10_percent | 201 | 0 | 201 | 0 | 181 | 47 |
| global_top_10_percent | 201 | 43 | 158 | 0 | 102 | 14 |

Top global technical quality does not imply face eligibility. Bottom-tail eligible
is zero under current global/face Gates; this dataset does not demonstrate a usable
low-global-quality counterexample. Flag counts do not prove causal blur/filtering.

## Video-Level Findings

Eligible frames occur in 15/71 videos; 56 videos have zero eligible. The three videos
with most eligible frames contain 40/62 (64.52%) of eligible frames. This is Gate
concentration evidence only, not identity/diversity suitability or candidate selection.
The full 71-row video report includes counts/ratios/reasons, median face Laplacian,
Tenengrad, eye sharpness, skin texture/plasticity, and blink/mouth diagnostic counts.

## Tests

Previous tests: 75 retained. New tests: 19. Total: **94 PASS**.
Coverage includes full ten-row/source-column retention, no-face, multiple-face,
decode and mesh-processing errors, --limit publication, relative identity collision,
Unicode paths, repeated same-image metrics, blink/mouth fixtures, AST formula
regression, CSV-only report replay/source guards, incomplete production rejection,
failed-run preservation, partial isolation, publication rollback and immutable review copies.

Three full production runs returned zero and yielded byte-identical 2001-row
STEP3 CSV, three derived CSVs and Markdown. All19 added tests also PASS in the
isolated STEP3 runtime. CSV-only regeneration matches published reports.
The untouched original Gate-finalization block was evaluated against all 2001 measured
rows: eligibility, reasons, categories, both percentiles and sharpness matched exactly.

## Documentation

Updated README, PROJECT, Current face-quality/configuration Knowledge, existing
DEC-0002/0003/0011 evidence links, FAIL-0002 evidence, History and Experiments.
No duplicate ADR or unsupported Case was created; CASE-0002/0003 were checked but
no image-annotated ground truth was produced here. Their historical confidence is
not promoted from current machine flag counts.

Changed implementation: scripts/face_quality_gate.py, scripts/common/step3_audit.py,
scripts/build_step3_reports.py, bat/03_face_quality_gate.bat, requirements-step3.txt,
.gitignore, tests/test_step3_audit.py and tests/fixtures/step3_formula_baseline.json.
Documentation changes are listed above; other pipeline code/configuration is unchanged.

Primary artifacts:
- output/reports/step3_dataset_report.csv (full authoritative audit)
- output/reports/step3_video_summary.csv (71 videos)
- output/reports/step3_reason_summary.csv (overlap + exclusive categories, including zeros)
- output/reports/step3_distribution_summary.csv (13 metrics)
- output/reports/step3_summary.json (generation, counts, source hashes, diagnostics, CLI)
- [STEP3_FACE_QUALITY_SUMMARY.md](STEP3_FACE_QUALITY_SUMMARY.md)
- [STEP3_GATE_AUDIT.md](STEP3_GATE_AUDIT.md)
- [STEP3_VERIFICATION.json](STEP3_VERIFICATION.json)
- output/reports/step3_revision1_audit/ (logs, original source, regression, runtime/models,
  test results, replay/protected-data checks, partial and archived good reports)

Runtime: Python 3.10.11, MediaPipe 0.10.21, NumPy 1.26.4, OpenCV-contrib 4.11.0,
isolated in .step3_packages. Existing global STEP2 environment is unchanged.
Recreate with requirements-step3.txt and run the independent STEP3 BAT.
Optional --copy-review produces copies/crops grouped by report hash outside raw input;
default production emits reports only. Historical review folders are not current truth.

Publication stages all artifacts, atomically replaces each file and rolls back ordinary
publication errors. A process/OS crash between different-file replacements is not a
filesystem transaction; summary hashes support detecting inconsistency. Analysis failures
are retained in separate failed audit folders and return nonzero. No false crash-safety claim.

## Existing Gate Thresholds Changed

**NO.** Config/CLI defaults and kernels retained. Existing hard-coded backlight face
brightness 105 and visibility penalties remain audited algorithm literals. Historical
Knowledge values 120 px / sharpness 18 / plasticity 70 / skin 15 differ from current
140/110/80 px, face Laplacian 50, anatomical eye 1.6, plasticity 45, skin .050/.035.
Their historical formula descriptions/scales are not interchangeable. No tuning or
conversion was attempted. See the Gate audit for every enforced/not-enforced entry.

## Historical Evidence Preserved

**YES.** Prior baseline, STEP1/STEP2 code/results/manifests/CSV and historical records
remain intact except scoped additive Knowledge evidence. Previously active STEP3
reports are archived on successful replacement. Original face_quality_gate.py saved
for regression. No remote reset or historical generation merge.

## Data Lineage Preserved

**YES.** Same 2001 relative frame IDs and all 36 STEP2 fields preserved; exact
metadata-derived inventory, per-video counts, policy/source/content hashes validated.
Raw pixels and source mtime are unchanged. No frame deletion/restoration or renumbering.
Timestamp cannot be invented from temporal index alone. Generation remains associated
through the summary; the universal master audit/four explicit lineage fields remain planned.

## Ready for STEP3 Revision 2 Review

**YES — for human review of existing Gate behavior.** The 96.90% rejection rate,
large eye-presence/face-blur effect, 15-video eligibility concentration and historical
formula/value mismatches justify careful review. They do not prove erroneous Gates
without labeled examples. No Gate was tuned to improve this outcome. Future STEP4-10
and empirical accuracy/LoRA suitability remain unvalidated.
