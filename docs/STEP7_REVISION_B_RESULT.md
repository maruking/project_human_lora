# STEP7 Revision B — implementation and minimum verification

Execution status: implementation and synthetic tests PASS; production NOT RUN.
Algorithm validity: deterministic coverage heuristic verified on synthetic inputs;
not an optimal solver or an empirical LoRA quality benchmark.
Human calibration: pending. Selection proposals require STEP8 human decisions.

## Inputs and prerequisite checks

The local working tree is authoritative. Inspected active reports contain STEP2
outputs only; current-generation STEP3/4/5 and complete reviewed A/B/C inputs were
not found there. No backup lookup, restoration, production evaluation or selection
was performed. The pipeline remains generic and contains no current-subject IDs,
observed counts or hard-coded subject paths.

`step7_revision_b` in the SSOT YAML declares STEP2 formal CSV/summary, STEP3 formal
CSV, Revision A `latest.json` pointer, STEP4 pose and STEP5 duplicate reports.
An explicit `--selection-groups <path>` or configured `selection_groups` overrides
the pointer. The sidecar must contain ALL current formal frames plus supplemental
stills with their image hashes and A/B/C state. Use an explicitly updated reviewed
sidecar when needed; this selector never edits Revision A classifications.

Formal generation is reconstructed from current manifest/extraction metadata and
matched against STEP2's fingerprint/inventory. STEP3's summary must prove that its
CSV derives from the current STEP2 CSV. Formal downstream CSVs must retain the full
formal universe and unchanged preceding STEP3 fields. STEP5 must also retain STEP4
evidence, and available STEP6 must retain STEP5 evidence. Extra/stale identities,
duplicate identities, missing formal records or conflicting historical fields
stop publication. Supplemental downstream rows, when present, require matching
image hashes and supplemental generation IDs. Missing supplemental evaluation
remains visible in the full selection audit and cannot silently become PASS.

All raw image names must match the formal plus explicit supplemental STEP2 universe.
Supplemental image hashes and final selected image hashes are checked at runtime.
Non-selected formal pixels rely on upstream STEP2/STEP3's content verification;
this selector does not rehash all of those pixels. Available lineage columns,
timestamps, temporal index, pose/body visibility and review reasons are retained.
Exact source timestamps are never inferred from index/FPS.

STEP6 is optional only when its configured file is absent or identity is null.
This produces an explicit identity-unavailable warning and requires human safety
review. If present, only `identity_passed=true` is selectable; failed/unevaluated
identity rows remain in the audit with reasons. No identity score threshold changes.

## Deterministic selection stages

1. Classify every audit row using its authoritative A/B/C state. Conflicting Human
   Reject/non-C state is an input error. All C is excluded permanently for this run.
2. Build A-only set toward the configured target. A must be human confirmed.
   Choose coverage improvements first, then less represented sources, known
   expressions, existing STEP5 face-quality score and stable frame ID tie-breaks.
3. Analyze angle/composition/up-down gaps. Confirmed B with explicit reserve
   permission can replace a redundant A or add a necessary image up to the maximum.
   A swap must reduce shortages without creating another coverage shortage.
4. If fewer than the configured minimum remain, fill only that count shortage from
   confirmed B. Do not fill arbitrary surplus slots with B just to reach 40.
5. Keep unused A/confirmed B as reserves and provisional B as REVIEW_PENDING_RESERVE.
   Do not convert B to C. Near-duplicate alternatives remain reserves with explicit
   reasons and cannot be added together with their selected group representative.

At most one selected image per existing STEP5 duplicate group. Hard source caps
apply to every stage; missing video IDs use explicit source identity or an auditable
still-collection key. No name-based high-identity exception. Pose groups reuse
existing STEP4 labels; up/down yaw is bucketed with existing STEP4 config bounds.
No STEP4 classification or STEP5/6 algorithms are modified.

Current defaults from `step7_revision_b` (selection design, NOT quality thresholds):

| Coverage | Minimum | Maximum |
| --- | ---: | ---: |
| Frontal / near frontal | 12 | 20 |
| Three quarter (left/right combined) | 12 | 24 |
| Side-ish (left/right combined) | 4 | 12 |
| Close-up | 12 | 16 |
| Upper-body / medium | 16 | 24 |
| Full-body | 6 | 12 |

Minimum up/down diversity: one each; source cap: six; mild expression cap: six.
Minimum / target / maximum total: 35 / 40 / 45. Change runtime targets only in SSOT
or the explicit `--target-count` override. Bucket minima overlap across dimensions;
they are soft coverage goals, while maxima, source caps and duplicate constraints
are never relaxed to force the count. Impossible coverage is reported honestly.

Only existing optional expression labels NATURAL, NEUTRAL and MILD_VARIATION are
used. UNKNOWN is retained and requires review; it is not relabeled as natural.
Other expression labels stay excluded with a reason. Expression inference is not
implemented and naturalness cannot be guaranteed from current STEP4 alone.
Unknown/failed pose or duplicate evidence excludes selection without changing A/B/C.

## Outputs and operation

Run only the normal STEP7 entry point once the prerequisites above are ready:

```cmd
bat\07_score_lora_candidates.bat
```

The same config loader/path conventions and explicit CLI overrides are supported.
The optional reviewed sidecar override is:

```cmd
bat\07_score_lora_candidates.bat --selection-groups output\reports\reviewed_selection_groups.csv
```

Four outputs under configured reports_dir:

- `step7_candidate_selection.csv`: full input universe, including all C, skipped,
  pending B and non-selected rows. Includes selected yes/no, final_selection_role,
  original selection_group, promotion/exclusion reasons, angle/pitch/composition,
  duplicate-group and source-selected-count context.
- `step7_final_selected_35_45.csv`: selected candidate proposal only, ordered by rank.
  If fewer than 35 are possible it is explicitly incomplete; no false count claim.
- `step7_reserve_candidates.csv`: remaining A/B and pending B, with their distinct
  roles and eligibility reasons. No C or explicit identity-failed reserves.
- `STEP7_SELECTION_SUMMARY.md`: counts, B promotions, coverage/source/duplicate and
  expression distributions, remaining gaps, settings and input fingerprints.

Exit 0: reports generated without count/coverage shortages (human review still
required). Exit 2: reports generated with explicit shortages. Exit 1: invalid inputs
or publication failure; existing reports remain preserved. Available immutable
run snapshots and copies of previous active report bytes are retained separately.
Publication uses per-file atomic replacement and ordinary-error rollback; abrupt
process termination between replacements is not a multi-file transaction.

The old `score_lora_candidates.py` is preserved as historical implementation and
is no longer called by the normal STEP7 BAT. Its old 65-image quotas and old
`step7_dataset_report.csv`/materialized folders are not overwritten by Revision B.
No restoration or captioning follows. `run_all.bat` now stops after STEP7; existing
STEP8–10 entry points remain intact. Their handoff to the new reports needs separate
scoped work, preventing reuse of stale legacy candidate directories.

## Minimum verification

- Eight synthetic Revision B tests PASS: deterministic shuffled-input replay,
  A-only coverage, necessary B swap, B minimum-count fill, pending B/C exclusion,
  duplicate/identity/pose/expression handling, empty subsets/publication rollback,
  and end-to-end tiny-image joins including supplemental lineage, stale sidecar
  rejection and conflicting historical STEP3 evidence rejection.
- Eight shared configuration tests PASS; legacy defaults and SSOT schema remain valid.
- `cmd /c bat\07_score_lora_candidates.bat --help`: exit 0, actual BAT initialization,
  local config reading and CLI routing verified; no selection executed by this command.
- No full production pipeline, full dataset selection, inference, image copying,
  deleted-folder restoration, captions or training.
- **Full batch executed: NO.**

## Rule/result obligations

Rules checked: root and canonical AGENTS, PROJECT, pipeline/data-lineage rules,
configuration/pose/identity/face-quality knowledge, DEC-0005/0006/0011/0012,
FAIL-0003 and relevant case/results/history records. Existing knowledge maintenance
protocol followed; DEC-0013 supplements diversity principles and separate groups.

- Data lineage preserved: YES, synthetically verified; production joins pending.
- Full-row preservation: YES, formal plus supplemental universe; selected/reserve
  CSVs are explicitly derived subsets, full candidate CSV retains all rows.
- Historical evidence preserved: YES; existing source/report bytes were not moved
  or regenerated by Codex. Legacy algorithm remains unchanged.
- Config SSOT preserved: YES; new settings, optional inputs and schema isolated.
- No threshold or upstream algorithm conflict. STEP8 handoff deferred explicitly.

Changed: `scripts/common/revision_b.py`, `scripts/select_revision_b.py`,
`bat/07_score_lora_candidates.bat`, `bat/run_all.bat`, `config/config.yaml`,
`config/config.example.yaml`, `config/config.schema.json`, `tests/test_revision_b.py`,
this result, README, scoped Current Knowledge and DEC-0013/index.

Not changed: STEP3 thresholds/formulas/classifications, STEP4 classification,
STEP5/STEP6 algorithms, Human Review history, source images, STEP8–10 processing.
Documentation checked: prior Failures/Cases/Experiments/History evidence preserved;
no production or empirical quality experiment claimed.
