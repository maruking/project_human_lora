# Mandatory Agent Operating Protocol

Before modifying this repository, you MUST read the following in order. All links
below are relative to this file. The root [AGENTS.md](../AGENTS.md) routes here;
this is the canonical protocol, not a second independent set of Project Rules.

## Required read order

1. [PROJECT.md](../PROJECT.md): mission, reusable multi-subject design, scope and status.
2. [Pipeline Hard Rules](rules/lora_pipeline_rules.md).
3. [Data Lineage Hard Rules](rules/data_lineage_rules.md), plus every additional
   applicable document in [rules/](rules/). Do not skip rules after reading Knowledge.
4. Relevant [Current Knowledge](../knowledge/current/README.md), including active
   configuration, frame organization and the responsibility of the STEP being changed.
5. Relevant ACCEPTED [Decisions](../knowledge/decisions/README.md): inspect actual
   record status/supersession, not only index labels. Separate policy intent from
   implementation and validated evidence.
6. Relevant [Failures](../knowledge/failures/README.md), including retry prerequisites.
7. Relevant [Cases](../knowledge/cases/README.md), including confidence and counterexamples.
8. The current/previous STEP result in [docs/](../docs/) and relevant
   [History](../history/README.md). Review [experiments](../experiments/README.md)
   and superseded records when needed to understand boundaries.

## Codex Execution Policy

To reduce Codex credit usage and keep pipeline execution reproducible,
Codex should not normally perform production or batch processing directly.

Default responsibility:

- Codex designs and implements the required Python processing.
- Codex creates or updates the corresponding BAT entry point.
- Repeated, dataset-wide, batch, evaluation and regeneration work must be runnable
  through BAT + Python.
- Codex may perform only the minimum execution necessary to verify that the
  implementation or BAT entry point works.

Codex must not consume credits by directly performing the full production workload
when the same work can be performed deterministically by the project's BAT + Python
pipeline.

Exceptions:

- ★maru explicitly instructs Codex to execute the processing.
- ★maru explicitly asks Codex to investigate, inspect, audit, debug or verify data.
- A very small execution is necessary to validate newly implemented code.
- The task cannot reasonably be delegated to the deterministic local pipeline.

Investigation and audit requests are therefore allowed to execute when explicitly
requested, but they must not silently expand into a full production rerun.

Default workflow:

```text
Chappy
  → defines architecture / STEP / evaluation requirement

Codex
  → implements or updates BAT + Python
  → performs minimum implementation validation
  → STOP

★maru
  → runs the BAT for normal full processing
```

Codex must not replace an existing BAT + Python operational path with a Codex-only
execution workflow.

## Before coding or documentation changes

- Verify repository root and current local working tree; do not replace local work
  with remote contents or silently create a checkout from an older generation.
- State the task scope, current subject/generation, input/source report and affected
  STEP. Validate formal metadata/counts before production, never infer a fixed size.
- Check both rule documents, relevant accepted Decisions, failure retry conditions
  and existing implementation. Mark ACTIVE requirements, PLANNED implementation
  and HISTORICAL evidence separately. A policy is not proof of enforcement.
- Preserve existing user work and authorized boundaries. Do not change Hard Rules
  contrary to the user's direction; a conflicting change requires explicit user
  authorization. Existing explicit authorization counts; do not request it again.
- Inspect identity keys, current-generation coverage and selected-output versus
  full-audit roles. Identify limits or known legacy gaps before editing a later STEP.
- Do not force code to match a documentation mismatch outside the authorized task.
  Record Rule / implementation / accepted knowledge / recommendation / deferred STEP.
- Runtime settings follow Config SSOT. Do not invent thresholds, subject names,
  fixed dataset counts, model adapters or face-quality claims from diagnostics.

## During work

Use the linked rules as authoritative policy; do not copy their settings here.
Maintain source/generation identity, every full-audit row and rejection/skip reasons.
No STEP may exceed its responsibility. Preserve source pixels and historical data.
Keep changes scoped and run appropriate checks within the Codex Execution Policy.
Documentation-only changes need
link/routing/integrity checks, not new pipeline inference or algorithm tests.
Separate measured facts from interpretation. Never promote a diagnostic metric to
a hard quality rule without an accepted Decision and supporting experiment.

## After work

Review README, Current Knowledge, Decisions, Failures, Cases, Experiments, History
and affected STEP result. Update only documents warranted by the change; if none,
record `Documentation checked; no update required` in the result. Preserve earlier
results and baseline evidence rather than rewriting them to imply current success.
For memory updates, use [Knowledge Maintenance](skills/knowledge-maintenance/SKILL.md):
audit existing records before assigning the next unused ID; avoid duplicate Decisions.

The result MUST include:

- Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md and applicable rule files.
- Data lineage preserved: YES / NO.
- Full-row preservation: YES / NO / N/A, with the universe and any diagnostic subset.
- Historical evidence preserved: YES / NO.
- Config SSOT preserved: YES / NO.
- Changed files, verification, rule conflicts, deferred implementation and readiness
  limited to what was actually validated. Do not imply STEP3+ production PASS.

## Development memory discipline

Do not repeat past failures. Search prior records before proposing a discarded method.
Keep facts separate from interpretations; confidence HIGH requires broad empirical
support, MEDIUM covers limited/synthetic validation, LOW covers unverified cases.
The documentation's architectural acceptance does not validate future implementations.
