# Data Lineage Hard Rules

Status: ACTIVE governance requirements. Runtime compliance in legacy STEP3-10 is
not fully validated; staged schema/master-audit implementation is PLANNED.
See [PROJECT](../../PROJECT.md), [Pipeline Rules](lora_pipeline_rules.md) and
[governance Decision](../../knowledge/decisions/DEC-0011-agent-entry-and-full-frame-lineage.md).

## Rule A — Full Frame Preservation

For the same subject and dataset generation, every authoritative per-frame audit
STEP MUST retain the preceding frame universe. Expected row count and identity set
come from formal input/metadata, never a subject-specific constant. Rejected,
duplicate, skipped and not-selected frames remain present with status/passed/
eligible/selected, rejection_reason or decision_reason. Unknown/not evaluated is
not PASS and must have an explicit reason. Processing failure must not erase a row.

STEP0 has no frame universe; STEP1 creates a generation and its inventory. A source
or sampling-policy change intentionally creates a different generation; preserve
previous data separately rather than merge old frames into the active report.
Derived video/metric summaries have different cardinalities and are not frame audits.
Selected training exports may contain a subset only when identified as materialized
exports and linked to a full authoritative audit retaining every frame.

## Rule B — Filtering Is Not Deletion

REJECT / DUPLICATE / NOT_SELECTED changes eligibility for later processing, not
membership of the full audit. Keep the original frame/source identity and recorded
reason. No physical source deletion or silent report-row deletion is authorized by
a diagnostic/selection result. Diagnostic limits/subsets must be marked partial and
must not replace the formal full-generation report or claim full production PASS.

## Rule C — Stable Identity and Joins

Conceptual join key: (subject_id, dataset_generation_id, frame_id), with video_id
and filename/source mapping retained. subject_id identifies the person;
dataset_generation_id identifies a source/sampling/regeneration universe; video_id
identifies the source video; frame_id identifies the frame inside that universe.
A filename alone is not globally unique across subjects or generations.
Preserve current manifest IDs, relative filenames and temporal_index grammar.
Do not break existing schemas just to rename keys; introduce explicit fields and
compatibility mappings in later scoped work. Until then, supply reliable subject/
generation context through associated metadata and reject ambiguous joins.

STEP output adds evaluation data to the same identities. Separate CSVs are allowed,
but joins MUST be unique, complete and generation-safe. Never silently inner-join
away rejected/missing records, renumber IDs or guess identity from directory order.
Retain timestamps/source hashes where available; unavailable data stays explicitly
unavailable rather than being invented. Temporal index/effective FPS alone is not
proof of an exact source presentation timestamp.

## Rule D — Full Data vs Derived Report

The authoritative full dataset report is machine-readable source data. Video summary,
distribution summary, Markdown/dashboard and highest/lowest examples are derived
views. They MUST NOT replace full data, dictate deletion or invent Gate thresholds.
Regenerate views from full data whenever possible; preserve source bytes/metrics.
STEP2 exemplifies this with dataset CSV -> build_step2_reports.py -> video CSV,
distribution CSV and Markdown. Later STEPs must preserve the same separation.

## Rule E — Cross-Step Auditability

A training image must be traceable to original source/video/photo, source hash and
available time, STEP2 metrics, STEP3 face decisions, STEP4 pose, STEP5 duplicate
state, STEP6 identity, STEP7 selection, STEP8 human decision, STEP9 restoration and
STEP10 inclusion. Retain raw/restored paths and transformation provenance; an
exported or restored asset is not a new unlinked source frame.

PLANNED: output/reports/master_frame_audit.csv or equivalent machine-readable join,
including subject/generation/video/frame identity, timestamp_sec/source_hash when
available, step1_* through step10_* outcomes, reasons and final inclusion. The
contract is required; a single giant CSV or every explicit field is not claimed
implemented today. Audit legacy row coverage and STEP8/9/10 joins in scoped work.

## Rule F — Generation and Historical Preservation

Validate input generation, expected/discovered IDs/counts, uniqueness and relevant
metadata before production or joins. Active reports contain only current-generation
rows; never carry stale records forward. Preserve originals, prior generations,
baseline/Decision/Experiment/Failure/History evidence separately. Label HISTORICAL,
SUPERSEDED or STALE FOR CURRENT GENERATION instead of rewriting previous results.
Use staged validation and atomic publication for formal reports, and nonzero errors;
state multi-file crash/rollback limitations instead of claiming transactional safety.

## Rule G — Verification and Scope

Check counts AND frame identity sets before/after an authoritative full-frame STEP.
Verify full-column/state propagation, source/hash mapping and rejected/skip reasons.
State YES / NO / N/A for full-row preservation with the dataset universe. Missing
legacy enforcement is a documented gap, not permission to silently relax the rule.
Report mismatches and defer out-of-scope code changes; follow explicit user approval
for changes conflicting with Hard Rules. Future STEP changes must implement/test
these invariants without expanding their face/pose/identity/selection responsibilities.
