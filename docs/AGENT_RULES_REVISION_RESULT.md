# Agent Rules Revision Result

Date: 2026-10-02. Status: PASS — documentation/routing revision only.
Local working tree is authoritative; no checkout reset, commit or push.

## Added

- [PROJECT.md](../PROJECT.md): multi-subject mission, STEP responsibilities, model independence and planned audit architecture.
- [.agents/AGENTS.md](../.agents/AGENTS.md): canonical mandatory read/before/after protocol.
- [data_lineage_rules.md](../.agents/rules/data_lineage_rules.md): full-frame audit, stable keys and joins, derived views and generation/historical preservation.
- [DEC-0011](../knowledge/decisions/DEC-0011-agent-entry-and-full-frame-lineage.md): one minimal governance Decision extending existing config/identity/generation policy.
- Current project-governance knowledge, HIST-012 and this result/verification.

## Updated

Root [AGENTS.md](../AGENTS.md) routes explicitly to the canonical .agents protocol.
[Pipeline Rules](../.agents/rules/lora_pipeline_rules.md) retain BAT/privacy/shell/
real-skin/diversity/review principles and distinguish requirements from enforcement.
README and Current configuration knowledge link the project policy; stale STEP2
historical-merge text is corrected to accepted DEC-0010. Decision/history indexes
are maintained; original Decision/Experiment/History/Baseline evidence is preserved.

## Codex Read Order

Root AGENTS -> .agents/AGENTS -> PROJECT -> pipeline rules -> data lineage and
other applicable rules -> relevant Current -> accepted Decisions -> Failures ->
Cases -> current/previous STEP result and History -> supporting experiments as needed.
The .agents file did not previously exist; it is added, not falsely reported as
updated. Root routing is explicit so the nested file is not assumed auto-discovered.
This is a mandatory repository protocol, not a technical guarantee that an unrelated
outside-root session automatically loads it. Start work in this repository and follow
its root instructions before editing.

## New Hard Rules

Multi-subject reuse and model-independent evaluation; no current-subject/count
constants in generic code/schema/rules. Full-frame audit identity universe remains
complete within a generation, including rejected/duplicate/not-selected/failed rows.
Filtering eligibility is not deleting audit rows or source media. Machine source
and derived human summaries are separate; examples never replace full data.
Preserve subject/generation/video/frame context, unique complete joins, available
source hashes/times and cross-STEP reasons. Preserve historical evidence and Config
SSOT. Runtime enforcement, explicit schema keys, photo generalization, adapters and
master_frame_audit remain planned where implementation is missing.

## Existing Rule Conflicts Found

Each entry records Rule / current implementation / accepted knowledge /
recommended resolution / deferred STEP. No algorithm was changed to resolve it.

| Rule mismatch found | Current implementation | Current accepted knowledge | Recommended resolution | Deferred STEP |
| --- | --- | --- | --- | --- |
| Mandatory .agents entry was assumed present | Only root AGENTS existed; Knowledge preceded Rules | DEC-0006/7/9/10 concern runtime policy, not this routing | Root router + explicit nested protocol/PROJECT/Rules links; implemented in docs | None |
| Fixed composition target described as strict runtime allocator | score_lora_candidates uses config shot/pose min/max; prepare_human_review uses a separate review target | DEC-0005 records historical intended quota; configuration.md/DEC-0006 record actual defaults | Label historical target; retain SSOT; request scoped policy choice before changing selection | STEP7/8 |
| STEP7 said to put final selections directly in selected | STEP7 candidates; STEP8 prepares the selected subset | Current configuration distinguishes candidate pool/review/final guidance | Correct current path ownership in Rules; do not change paths/code | No code change; STEP7/8 audit |
| Component-only restoration claimed enforced | selective_restoration loops selected files, restores full-body face crops with feathering/rollback | DEC-0004 and FAIL-0001 prohibit whole-face restoration; current restoration knowledge acknowledges gap | Keep prohibition as required policy; scope mask enforcement before restoration production | STEP9 |
| Human gateway implied no bypass/persisted decision record | bat/run_all pauses normally but supports --skip-pause; prepare_human_review is a directory/review assistant | DEC-0006 preserves pause/behavior; historical review intent is not persisted audit proof | Separate bypass/human decision evidence; do not claim a pause proves review | STEP8 / runner policy |
| Full-row audit universal enforcement not implemented/validated | face_quality_gate truncates rows with explicit --limit; STEP9/10 reports are selected/restored-file subsets; STEP9 can continue on decode failure | DEC-0010 exact coverage is validated for STEP2 only; new DEC-0011 extends full-audit requirements | Mark diagnostic subsets partial; retain a full authoritative sidecar, skip/error reasons and original universe | STEP3 limit mode; STEP8-10 full audit |
| Generation-safe stable joins assumed universal | STEP9 source matching uses substring filenames; explicit subject_id/generation fields are not universal | DEC-0007 stable video IDs, DEC-0009 source/policy fingerprints, DEC-0010 STEP2 generation checks | Compatible compound context keys, exact joins and audit all unresolved/error states | STEP3-10 schema/join work |
| STEP2 historical merge described configurable in Current | STEP2 schema rejects true; writer/CLI prohibit retention | DEC-0010 supersedes DEC-0008 reporting policy | Correct stale Current sentence, preserve original records | None; docs corrected |
| Index still labeled fixed sampling accepted | Actual DEC-0001 record is superseded by DEC-0009 | DEC-0009 duration-aware sampling is accepted | Correct index status only; retain historical record/results | None; index corrected |

## Deferred

No quota choice, Gate tuning, restoration mask, limit semantics, runner bypass,
subject/generation schema migration, master audit, photo pipeline or training adapter
is implemented here. Later scoped STEP work must check/implement its applicable
lineage invariants before claiming compliance. In particular resolve STEP9 component
mask gap before claiming skin preservation. User policy choices remain deferred;
this task provides concrete mismatches rather than forcing code to match Rules.

## Checks

Markdown target existence and root-to-canonical-to-Project/Rules routing checked.
Rule topics have a canonical owner; root contains no duplicate configuration or
independent Hard Rules. New/edited documentation is scanned for private absolute
paths and new generic rules for current-subject/count constants. Protected code,
BAT, tests, config, metadata, machine reports, existing STEP results and baseline
hashes match the pre-task snapshot. Pipeline algorithm tests/inference: N/A, explicitly
unnecessary for this documentation-only revision. See AGENT_RULES_REVISION_VERIFICATION.json.

## Rules Checked

AGENTS.md; .agents/AGENTS.md; PROJECT.md; .agents/rules/lora_pipeline_rules.md;
.agents/rules/data_lineage_rules.md. Relevant Current, Decisions, failures/cases,
STEP0-2 results and History were reviewed. Knowledge Maintenance skill applied.

Data lineage preserved: YES — existing full/machine data and metadata unchanged.
Full-row preservation: N/A — no STEP run/row transformation; full dataset reports unchanged.
Historical evidence preserved: YES.
Config SSOT preserved: YES — no config/runtime value changed; stale description corrected.

## Pipeline Logic Changed

NO. No image processing, scoring/rank/Gate, selection/restoration/caption or training change.

## Ready for STEP3

YES — ready for scoped STEP3 development with mandatory Project/Rules and lineage
checks. This does not declare legacy STEP3-10 full-audit compliance or production PASS.
