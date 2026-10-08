# STEP7 v2.1 upstream version metadata fix

2026-10-06. Metadata/lineage compatibility only, no selection revision.

Changed: scripts/step7_candidate_selection_v21.py, its synthetic regression tests,
and this result/Current Knowledge note. input_versions reads hash-verified official
STEP3/4/5/6 summaries; missing/duplicate/modified metadata fails rather than guessing.
No output version labels are hard-coded in the version-recording function.

Normal07 BAT --preflight-only PASS:1951 full rows,762 normal candidates after4
confirmed current-version Human Reject exclusions. Recorded versions:

```json
["best_rank_v2.2", "step4_pose_composition_v3", "step5_dedup_v2", "step6_identity_v2"]
```

Preflight initially exposed existing Human Review binding to downstream STEP6
yaw/pitch/roll, which changed legitimately in STEP4 v3. The binding now compares
review records to the hash-verified authoritative STEP3 ranking, while still
checking complete current frame universe, image hash/generation/ranking version,
BEST score/global rank. Reject eligibility criteria are unchanged;4 explicit
current-version Rejects remain excluded. No review history is rewritten.

28 quality-coverage tests PASS, including version derivation with arbitrary test
metadata, missing/hash-changed metadata blocking and legitimate new-pose binding
with ranking/hash mutation rejection. Production selection was not run or published.
The existing STEP7 summary remains prior evidence until ★maru reruns07.

Not changed: common candidate_selection_v21 selection code, Quality Guard, core60,
max10 optional repairs, BEST score, identity weight0, source caps, STEP3–6 outputs,
source images/config thresholds. No image inference/copies.

Rules checked: AGENTS/.agents protocol, PROJECT, pipeline/data-lineage rules and
DEC-0025/STEP7 Current Knowledge; prior Failures/Cases/History reviewed. Lineage,
historical evidence and config SSOT preserved. Full rows verified read-only;
publication tested only with synthetic fixtures. No new algorithm Decision needed.
Full production executed: NO.

★maru: run bat/07_score_lora_candidates.bat, then share
docs/STEP7_CANDIDATE_SUMMARY.md with Chappy.
