# STEP5 dedup v2 — STEP4 v3 input compatibility

2026-10-06. Scope: input compatibility only; no dedup algorithm revision.

## Changed
- `scripts/step5_dedup_v2.py`: permit authoritative STEP4 v2/v3, require each row
  to match its summary version. For v3, compare original STEP3 yaw/pitch/roll/
  pose_status through mandatory step3_* columns; all other inherited fields remain
  strictly checked. New v3 yaw/pitch feed existing dedup functions without remapping.
- `tests/test_step5_dedup_v2.py`: v3 input/lineage, missing pose, use of new angles,
  unchanged BEST representative priority, full-row and mixed-version checks.
- Relevant README/Current Knowledge/Decision appendices document the narrow bridge.

## Minimum validation
Formal `bat/05_face_deduplication.bat --preflight-only` PASS:1951 rows, current
STEP4 v3 report/summary hashes, current STEP3 identity/inherited fields and source
existence verified. No images decoded, no pHash generation, no outputs published.
All8 current eligible rows with missing yaw/pitch return missing pose and cannot
form a near edge, even with synthetic identical pHashes. Existing exact-SHA path
still applies after normal integrity/decode checks during ★maru's production run.

32 STEP5 tests PASS, including5 new v3 compatibility tests. Synthetic full-row
test preserves all columns/IDs including fatal/missing records. Synthetic exact
duplicates with missing pose still choose BEST score90 over80 as before.

Production artifacts/config and common dedup/phash modules remain hash-identical
to their pre-task snapshots. STEP5 version remains step5_dedup_v2. No source name,
specific missing count or video ID is hard-coded into production logic.

## Not changed / limits
STEP1–3, STEP4 v3 source/report/formulas, pHash/temporal/tight-angle thresholds,
Union-Find clustering, BEST-first ordering, source images and STEP6+ code/settings.
No v3 full-dataset clusters or distribution results are claimed. Existing STEP5
production reports still represent their previous input until ★maru runs the BAT.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, pipeline and lineage rules.
Data lineage preserved: YES. Full-row preservation: YES in input verification and
synthetic annotation; full production not executed. Historical evidence: YES.
Config SSOT: YES. No new Decision or rule conflict: this extends DEC-0022 input
compatibility while preserving its frozen semantics. Other Failures/Cases/History/
Experiments checked; no new algorithm evidence record warranted.

Full batch executed: NO.

## 2026-10-06 metadata-only summary correction
The production summary retained a hard-coded v2 input version despite actual v3
input. Version generation now reads the hash-bound authoritative STEP3/4 summary
metadata and checks consistency with rows. Current JSON/Markdown input_versions
is best_rank_v2.2 + step4_pose_composition_v3. Old JSON/Markdown preserved in
reports/bkup with a hash manifest; Markdown companion hash refreshed. Cluster CSV,
cluster/pose HTML, pose CSV, rules, roles, input hashes and upstream files remain
byte-identical. No image decode, pHash calculation or clustering rerun.34 synthetic
tests PASS, including version derivation/mismatch checks. No new Decision warranted.

★maru: run only `bat/05_face_deduplication.bat`, then share
`docs/STEP5_DEDUP_SUMMARY.md` with Chappy. STEP6+ regeneration is outside this task.
