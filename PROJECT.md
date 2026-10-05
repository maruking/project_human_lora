# Real Human LoRA Dataset Pipeline

## Mission

Build a reusable pipeline that constructs, evaluates and records training datasets
for multiple real people from videos and photographs. Each training asset should
be traceable from original source through evaluation, decisions and final inclusion.
The current local validation subject is a benchmark, not the architecture.

## Non-Goals

This is not a one-person, one-run script collection. Dataset evaluation does not
itself train a model or prove photographic face quality from whole-frame gradients.
Training adapters and the universal master audit remain outside the current validated scope.

## Multi-Subject Design

Subject data/configuration are environment-specific. Do not encode a current
person's name, video IDs or observed image/video counts as generic code/schema/rules.
Reuse the same pipeline by changing local configuration and formal source mappings.
Keep subjects and generations isolated; never join across them by a bare basename.
Concepts subject_id and dataset_generation_id are governance requirements; explicit
schema fields will be introduced compatibly in scoped later work.

## Pipeline Overview STEP0-10

| STEP | Responsibility | Current validation boundary |
| --- | --- | --- |
| 0 | Environment/configuration preflight | Local SSOT setup validated; not inference |
| 1 | Source mapping, normalized working copies, frame extraction | Duration-aware generation validated |
| 2 | Whole-frame technical metrics and derived human reports | Current generation/report layer validated |
| 3 | BEST v2.2 balanced critical quality and version-separated review (DEC-0020) | Production and 135-image Human Review completed; practical baseline approved for STEP4, general quality accuracy unvalidated; see [current Knowledge](knowledge/current/step3-best-ranking.md) |
| 4 | Stored pose / face-scale descriptors, full-row audit | Current production summary available; no pose accuracy/final selection claim |
| 5 | Source-aware duplicate clusters / BEST representatives | STEP5 v2 synthetic validation; production pending ★maru; no deletion/quality rescoring/quotas; [DEC-0022](knowledge/decisions/DEC-0022-step5-conservative-dedup-clusters.md) |
| 6 | Identity evaluation | Existing backend; no new backend implied |
| 7 | Candidate scoring/selection | Existing configured quota maps; full audit retained |
| 8 | Human decision/review | Existing review assistant; decision persistence needs audit review |
| 9 | Selective restoration, preserving source skin | Existing implementation differs from component-only policy |
| 10 | Training export/captions | Existing FLUX-oriented exporter; other adapters are planned |

See [Pipeline Rules](.agents/rules/lora_pipeline_rules.md) and the
[current scope/result](docs/STEP3_RESULT.md). Existing code and
historical validation are not proof of current STEP4-10 PASS or labeled STEP3 accuracy.

## Data Architecture

Original immutable sources -> current-generation frame inventory -> full evaluated
machine-readable data -> human-review summaries -> selected/materialized exports.
Filtering processing eligibility must preserve full-audit rows and their reasons.
Generation changes create a new universe with separately retained previous evidence;
do not carry stale rows into a current-generation report.

## Subject / Generation / Video / Frame concepts

| Key | Meaning |
| --- | --- |
| subject_id | Stable dataset owner/person identity |
| dataset_generation_id | Distinguishes source/sampling/regeneration changes for that subject |
| video_id | Stable source-video mapping from manifest, not enumeration position |
| frame_id | Stable frame identity inside a generation; preserved across STEP joins |

Existing subject_name, manifest video_id, relative frame_id/filename and generation
fingerprints supply partial lineage today. They do not imply that the four explicit
fields already exist everywhere. Retain compatible naming and evolve schemas gradually.
A photograph needs a source identity too; the generalized photo path is planned.

## Model Independence

Real Human Source -> Canonical Evaluated Dataset -> Training Adapter.
Planned adapters may target FLUX.2 Klein, FLUX.1, SDXL or future models. Keep
measurement/identity/decisions independent of training-format constraints. Current
FLUX export is existing code, not proof that all adapter contracts are implemented.
Do not implement those adapters during this revision.

## Machine Data vs Human Reports

Full machine data retains every frame in the active generation and all evaluation
states. Video/distribution/Markdown summaries derive from it and are regenerable;
top/bottom examples are examples only. A summary or selected export cannot replace
full audit data. [Data Lineage Rules](.agents/rules/data_lineage_rules.md) govern joins.

Planned master audit: output/reports/master_frame_audit.csv or equivalent. It should
join subject/generation/source/time identity to STEP1-10 states, reasons, restored
asset provenance and training inclusion. Separate STEP CSVs are acceptable if joins
are complete and generation-safe. No giant CSV migration is required now.

## Development Memory

[Current Knowledge](knowledge/current/README.md), [Decisions](knowledge/decisions/README.md),
[Failures](knowledge/failures/README.md), [Cases](knowledge/cases/README.md),
[Experiments](experiments/README.md) and [History](history/README.md) preserve facts,
interpretations and validation limits. Keep historical/superseded/stale evidence.
Agent changes begin with [AGENTS.md](AGENTS.md) and [.agents/AGENTS.md](.agents/AGENTS.md).

## Current Validation Subject

Current local validation data is environment-specific and is not part of repository
architecture. Subject names, private paths and media belong in ignored local config,
formal local manifests and private artifacts. Use current STEP results to learn the
actual validation envelope; do not turn its counts into constants.
PROJECT.md PATCH — Codex Execution + STEP Improvement Semantics
Add the following sections to PROJECT.md.
Revision Semantics
Use explicit revision types.
- Infrastructure Revision:
  reproducibility, lineage, reports, deterministic execution, auditability.
  It does NOT imply Gate quality improvement.
- Algorithm Revision:
  changes formulas, thresholds, detection logic or classification behavior.
- Calibration Revision:
  collects measurements and Human Review evidence to decide algorithm changes.
A STEP must not be described simply as "improved" when only infrastructure/reproducibility changed.
Every STEP result must separately state:
- Execution status
- Algorithm validity status
- Human calibration status
Codex Execution Policy
Codex is primarily an implementation agent.
Default workflow:
Chappy
→ defines STEP / architecture / evaluation requirement
Codex
→ implements or updates BAT + Python
→ performs only minimum implementation validation
→ stops
★maru
→ runs the normal full batch
→ performs Human Review
→ returns calibration evidence
Codex must not normally execute full production/batch processing when the same work can be run deterministically through project BAT + Python.
Exceptions are allowed only when ★maru explicitly requests:
- investigation
- audit
- debug
- inspection
- verification
- full execution
An explicit investigation/audit request authorizes the necessary direct execution for that investigation, but must not expand into unrelated production reruns.
Implementation prompts do not implicitly authorize full-dataset execution.
Human Calibration Safety
Machine PASS/REJECT is provisional until the relevant Gate has Human Calibration evidence.
For candidate quality review use:
- A = CLEAN / PRIMARY
- B = BORDERLINE / RESERVE
- C = REJECT
Do not collapse B into C.
Do not promote a diagnostic metric into a Hard Gate until:
1. boundary examples are reviewed,
2. ★maru provides accept/reject criteria,
3. Chappy summarizes the calibration tendency,
4. Codex implements only the approved rule.
STEP3 Current Boundary
Historical Revision1 boundary below is retained as the earlier policy context.
Current status: best_rank_v2.2 production/review completed; ★maru/Chappy approved
the practical baseline for STEP4 while retaining unresolved quality limitations.
See [current STEP3 Knowledge](knowledge/current/step3-best-ranking.md).
STEP3 Revision 1 established reproducible processing and audit outputs, but did not validate that the existing Gate thresholds match LoRA face-learning suitability.
Known current concerns:
- half-open/blink frames may pass,
- white-clipped/detail-lost faces may pass,
- useful low-native-resolution frames may be rejected,
- Laplacian blur judgments can disagree with Human Review.
STEP4 must not be treated as the next active improvement target until STEP3 Human Calibration and the current false-positive / false-reject review are resolved.
Execution Authorization Boundary
Questions about safety, feasibility, or whether ★maru may perform an action are NOT authorization for Codex to execute that action.
Examples:
- "こちらで行って問題ないですか？"
- "実行してよいですか？"
- "この方法で大丈夫ですか？"
- "移動しても平気？"
- "削除していい？"
For these messages, Codex must:
1. answer the question,
2. explain risks if any,
3. perform no mutating operation,
4. STOP.
If the same user message contains both an action phrase and a confirmation question,
Codex must not infer execution authority from the action phrase when the intended executor is ambiguous.
Mutating operations include:
- file/folder move
- delete
- overwrite
- rename
- restore
- backup cleanup
- bulk reorganization
- report relocation
- source replacement
- production/batch execution
Technical safety, reversibility, backups, or hash validation do not substitute for explicit execution permission.
A commentary notice such as "移動します" or "実行します" is not approval and must not be treated as user consent.
When authorization is ambiguous, default to:
READ / EXPLAIN / STOP
