# STEP3 Revision A — Result

> Correction: the 138-row run below is historical partial-scope evidence, NOT completion of full A/B/C coverage. Current code covers ALL formal frames + supplemental stills. The corrected pipeline has NOT been executed by Codex; execution belongs to maru. See [Maru execution instructions](STEP3_REVISION_A_MARU_RUN.md). Counts below must not be used as full-input selection counts.

Revision A diagnostics only completed. Official STEP3 is unchanged; no final selection performed.

## Scope / facts

- Authoritative local working tree, formal STEP1 generation `fc2a37abc81e44e456891ac7d268c2dc622255d120c944ac377dbefd491833c2`.
- Formal STEP1 metadata + content hashes: 2,001 frames / 71 videos, PASS; STEP2/STEP3 CSV hashes and generation verified.
- Diagnostic input: 81 formal frames = auto-OK62 +19 additional human-review frames; supplemental stills57. Total138, unique138, errors0.
- Supplemental root explicitly declared in private diagnostic config; excluded only from formal STEP1 inventory and audited separately. Other unexpected formal images still stop the run. Supplemental originals retain relative filenames and image hashes, with their own generation fingerprint and empty video_id.
- A=0; B=111 PROVISIONAL_DIAGNOSTIC / UNDECIDED; C=27 HUMAN_REJECT / CONFIRMED.
- Provisional B is not confirmed usable. `reserve_use_allowed=false` until human confirmation. Explicit HUMAN_CONFIRMED B remains a reserve, distinct from A/C.
- Known human Reject27 (all26 v69 plus v63_020) stays C, including8 official auto-OK images. Pending half-eye3 stays B/UNDECIDED.

## Measured diagnostic outcomes / limitations

| Input | Eye | Exposure | Detail |
|---|---|---|---|
| Formal81 | OPEN48 / BORDERLINE23 / UNKNOWN10 | NORMAL75 / BORDERLINE3 / OVEREXPOSED2 / UNKNOWN1 | NORMAL70 / BORDERLINE1 / UNKNOWN10 |
| Supplemental57 | OPEN44 / BORDERLINE10 / UNKNOWN3 | NORMAL56 / UNKNOWN1 | NORMAL50 / BORDERLINE4 / UNKNOWN3 |

Known pending examples: v05_012 min0.279662 BORDERLINE; v05_013 min0.310626 OPEN; v08_005 min0.245669 BORDERLINE.
All26 v69 are represented: exposure NORMAL20 / BORDERLINE3 / OVEREXPOSED2 / UNKNOWN1; detail NORMAL15 / BORDERLINE1 / UNKNOWN10.
These misses demonstrate that numeric NORMAL/OPEN cannot override human concerns or prove LoRA suitability. There is no validated beauty-filter / identity determination here. Thresholds were not tuned. Missing face/mesh stays visible as UNKNOWN, not an automatic accept/reject. FULL_BODY is measured without the production applicability skips.

## Execution / outputs

```cmd
bat\03_revision_a_diagnostics.bat
```

Python equivalent: `py -3.10 scripts/step3_revision_a_diagnostics.py`.
Generic setup: copy `config/step3_revision_a.example.json` to `config/step3_revision_a.local.json`, declare supplemental_dir relative to raw frames; alternate settings via `--diagnostic-config` and supplemental override via `--supplemental-dir`. Missing/empty supplemental input stops execution. The local file is ignored.
Numbers are diagnostic bins only, from this separate settings file; official YAML and Gate formulas/thresholds are unchanged. Formulas/boundaries appear in each run REPORT.md and summary.json.
Immutable content-addressed runs preserve history. Errors retain every row in an audit run and do not advance the latest pointer. Reruns check identical bytes. `output/reports/step3_revision_a/latest.json` points to the latest successful run.

- [Diagnostic report](../output/reports/step3_revision_a/runs/b2c4cb22c41b5e91a9bd4edd3f04d310b486e691aba9cee6fd31d3b1ab5d5b07/REPORT.md)
- [Diagnostic CSV](../output/reports/step3_revision_a/runs/b2c4cb22c41b5e91a9bd4edd3f04d310b486e691aba9cee6fd31d3b1ab5d5b07/diagnostics.csv)
- [Diagnostic JSON](../output/reports/step3_revision_a/runs/b2c4cb22c41b5e91a9bd4edd3f04d310b486e691aba9cee6fd31d3b1ab5d5b07/diagnostics.json)
- [Summary / provenance](../output/reports/step3_revision_a/runs/b2c4cb22c41b5e91a9bd4edd3f04d310b486e691aba9cee6fd31d3b1ab5d5b07/summary.json)
- [Verification](../output/reports/step3_revision_a_audit/verification.json)

## Verification / governance

123 unittest checks PASS (6 new tests); BAT execution end-to-end PASS and identical-byte rerun PASS.
3,259 pre-existing protected files checked by SHA256, changed0: source images, formal metadata, configs, production scripts/BATs, official CSV/JSON and historical STEP3 review artifacts.
Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, .agents/rules/lora_pipeline_rules.md, .agents/rules/data_lineage_rules.md; Current Knowledge, accepted Decisions, Failures/Cases read.
Data lineage preserved: YES. Full-row preservation: YES (formal2,001 audited; declared diagnostic subset138 retained including unknowns). Historical evidence preserved: YES. Config SSOT preserved: YES.
Changed files: new `scripts/step3_revision_a_diagnostics.py`, `scripts/common/revision_a.py`, `bat/03_revision_a_diagnostics.bat`, `config/step3_revision_a.example.json`, private local config, `tests/test_revision_a.py`; .gitignore local-config exclusion; this result, scoped README/Current/Decision/Experiment/History additions; new diagnostic/audit artifacts only.
Documentation checked: Failures/Cases, historic Decisions and STEP results need no rewrite. New selection policy recorded separately; existing production thresholds remain authoritative.
Rule conflicts: none. Generic raw-root preflight in the old production entrypoint still includes supplemental images; diagnostic-only exclusion does not silently alter that entrypoint. Production rerun handling of supplemental organization is deferred.
Readiness: diagnostic execution and preservation only. Metric accuracy, LoRA fitness, Chappy pending decisions and final selection remain unvalidated. Stop before STEP4.
