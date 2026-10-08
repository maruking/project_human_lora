---
id: DEC-0026
title: STEP8 folder-based Human Final Review and validated CSV authority
status: SUPERSEDED
date: 2026-10-05
confidence: MEDIUM
components: [human-review, lineage, dataset-selection]
tags: [folder-review, explicit-accept, no-auto-selection]
supersedes: []
superseded_by: [DEC-0028]
related_experiments: []
related_failures: []
related_cases: [CASE-0005]
---

# DEC-0026 — STEP8 Folder Human Final Review

## Context / historical implementation

STEP7 v2.1 supplies bounded review options, not final training inclusion (DEC-0025).
Current authoritative pool is70 with4 current-version STEP3 Rejects excluded.
Legacy prepare_human_review.py can prepopulate work/selected and infer categories
from names. It remains historical/unchanged; new normal STEP8 entrypoints are
08_prepare_folder_review.bat and08_collect_folder_review.bat. Browser review remains
optional diagnostic context, not mandatory Human interaction.

## Decision / workflow

Validate current complete STEP7 version/config, output/input hashes, full inherited
rows, selected subset and authoritative current-version Reject history/feedback.
STOP on stale/missing patch; no older-pool fallback or STEP7 inference.
Materialize each candidate exactly once using stored STEP4 pose_bin. Config SSOT
defines6 pose guidance ranges12–17/7–10/7–10/1–3/1–3/0–2. Folder names derive from
those ranges. Each folder has FULL and initially empty ACCEPT. ★maru copies selected
images FULL→ACCEPT; no rename/deletion/notes needed. Frame_id remains identity;
metadata filenames map to frame/image/generation in the manifest.

Normal prepare refuses any existing ACCEPT entries; explicit --reset-review archives
the entire prior session/choices before rebuilding. Unknown folders, unsafe paths,
links/junctions and altered source/copy hashes stop. No source mutation, automatic
acceptance or image-quality Reject. Reviews/stages/archive copies cannot become
STEP1–7 inputs. Copy directories are disposable interaction surfaces.

Collect validates exact manifest, session, unchanged current upstream, complete FULL,
known correctly placed unchanged ACCEPT files, no double frame or current Reject.
Full1951 audit rows remain;70 candidates get STEP8_ACCEPT or STEP8_NOT_SELECTED,
other rows NOT_APPLICABLE_NOT_IN_REVIEW_POOL. NOT_SELECTED is not bad image.
Count35–45 is hard; below35 NEED_MORE_SELECTION, above45 TOO_MANY_SELECTED.
Both publish diagnostic summaries but are not finalized for STEP9. Soft pose/scale/
vertical guidance warnings never auto-add/remove or independently block valid total.
Identity is diagnostic and Human preferences intentionally belong here.

## Downstream authority / safety

Authoritative handoff is step8_human_selection.csv + summary with VALID count and
pinned input/CSV/preparation hashes. load_step9_selection yields STEP8_ACCEPT only,
using original-source identities/hashes. It does not infer selection from ACCEPT
filesystem, which can be disposed after collection. Preparing a new session invalidates
the previous handoff until re-collected. No STEP9+ run in this revision.

Legacy STEP9 scans work/selected and implements full-face restoration instead of
the component-mask policy. Normal STEP9 BAT now validates CSV then STOPs before
legacy model/inference. Old BAT snapshot and restoration code remain historical.
A separate scoped STEP9 CSV adapter/component-mask revision is required; no claim
that restoration is ready. Existing runner STOP afterSTEP5 remains unchanged.

## Validation / limitations

25 synthetic/tiny-file tests cover requested18 items, ACCEPT preservation/reset,
altered copies, stale Reject patch, source overlap, inventory exclusion and STEP9
guard. Current STEP7 preflight-only confirms1951 rows/70 candidates/4 excluded
Rejects; no production review copies or human decisions created by Codex.
Publication archives prior reports, replaces files atomically and publishes markers
last with caught-error rollback. Directory/report swaps are not a process-crash
transaction; session/hash mismatch requires inspection. Do not edit ACCEPT while
collect runs. Human visual selection/final LoRA usefulness remain unvalidated.

[Implementation](../../docs/STEP8_FOLDER_REVIEW_IMPLEMENTATION.md),
[current Knowledge](../current/human-final-review.md).

2026-10-07: presentation/selection policy superseded by [DEC-0028](DEC-0028-step7-base-additive-step8-views.md). Earlier evidence and review history preserved.
