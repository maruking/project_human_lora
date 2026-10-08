# STEP10 STEP9-SKIP input bridge — implementation / minimum preflight

Date:2026-10-07. Packaging executed:NO.

## New input flow

Normal10_package_flux_dataset_gpu.bat retains the existing exporter. If configured
step9_report is absent, load validated step8_human_selection.csv and onlySTEP8_ACCEPT.
The shared STEP8 handoff validates current selection/config/session, input/output
hashes, full inherited audit and current-version Reject exclusion. Source paths come
from configured raw_frames_dir plus stored relative filenames; no directory scan.
Validate each frame ID/unique accepted set/original image hash. Input count and ID
set exactly match the accepted set, without a subject-specific40 constant.

SKIP input rows use originals with restoration_status=SKIPPED_NOT_NEEDED,
packaging_input_kind=STEP8_ORIGINAL. This is the user-requested no-restoration path,
not a new image-quality conclusion or override of the earlier STEP9 diagnostic report.
The10 REVIEW_RECOMMENDED diagnostic cases/history remain unchanged.

When a formal current STEP9 CSV exists, retain restoration-output input and original
recorded restoration status. Require exactly current accepted IDs and per-row
image_sha256 (original),dataset_generation_id,step8_review_session_id,restoration_status,
restored_path (relative to restored_dir),restored_image_sha256. Validate restored
file hashes and path containment. Existing ambiguous/stale/hashless legacy report
STOPs; it is not silently ignored or substituted. Old restoration code/CSV unchanged.
No new restoration writer/model/mask implementation in this task.

## Preflight and export boundary

--preflight-only validates inputs then returns before heavy model imports, model
loading, output-directory creation, images/alignment/captions/report generation.
Console explicitly prints count,input route,status and Packaging:NO. BAT prints
PREFLIGHT ONLY instead of packaging-complete for the documented command.

Future authorized packaging uses this exact validated list; filenames/JPEG suffixes
and duplicate basenames cannot cause extra/substituted picks. Input hashes rechecked
per image and after processing; new audit fields retain frame/source paths,original
and packaging hashes,generation/session/input kind. Source pixels remain immutable;
export copies still undergo existing16px alignment. Cannot decode/encode an accepted
image ->STOP instead of silently reducing dataset count. Nonempty export directories
STOP to avoid mixing previous output; source/output overlap and evidence overwrite
are refused. Partial export rollback remains a legacy limitation, not transactional
publication. No dataset/model download/export was run now.

Caption attribute classifier,caption template,align_dimension_16 andalign_image_16x
AST match original code exactly. Pose/shot input comes from accepted authoritative
metadata, mapping stored pose labels to the existing caption vocabulary.

## Changed

- scripts/package_flux_dataset.py
- scripts/common/packaging_input.py
- bat/10_package_flux_dataset_gpu.bat
- tests/test_step10_packaging_input.py
- README.md,PROJECT.md,docs/README.md,this report
- knowledge/current/lora-dataset-flux.md,configuration.md
- knowledge/decisions/DEC-0029-step10-step8-original-input.md,decisions/README.md

Config values,Caption/16px formulas,STEP3–9 data,Human selections and source images
unchanged. Existing CLI step7-report is retained for compatibility; current caption
metadata is sourced from validated accepted rows, not basename substring guesses.

## Minimum validation

19 tests PASS (11 input/caption/alignment +8 config). Test absence of STEP9; exactly
accepted inputs despite extra/stale files; duplicate basenames; original/restored
hash mismatch STOP; selected-only unique IDs; formal restoration route; ambiguous
legacy report STOP; stale session/extra row/path traversal STOP; preflight cannot
run caption/model processing or create output directory. Caption/alignment AST check
PASS unchanged. Actual read-only preflight result:

```text
Validated40 STEP8_ACCEPT images; input=STEP8_ORIGINAL
STEP10 PREFLIGHT PASS; accepted count:40 input count:40
restoration_status:SKIPPED_NOT_NEEDED
Packaging:NO;CLIP/model load:NO;image change:NO;caption generation:NO
```

Rules checked:AGENTS.md,.agents/AGENTS.md,PROJECT.md,pipeline/lineage rules;
Current Knowledge/Decisions/Failures/Cases/History/Experiments reviewed.
Data lineage preserved:YES. Full-row preservation:YES within40 accepted export
inputs; official1951-row STEP8 full audit remains unchanged. Historical evidence:YES.
Config SSOT:YES (existingSTEP8/10 paths). Rules conflict:NO; explicit user requests
this raw-input path. Failures/Cases/History/Experiments checked,no update required.
No full-generation production packaging/inference or STEP9 restoration performed.

## ★maru next action

```powershell
.\bat\10_package_flux_dataset_gpu.bat --preflight-only
```

Share this preflight console result with Chappy. Do not run without--preflight-only
until production packaging is separately authorized.
