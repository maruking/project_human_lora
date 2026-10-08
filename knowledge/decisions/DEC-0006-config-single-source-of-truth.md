---
id: DEC-0006
title: Config Single Source of Truth Without Algorithm Changes
status: ACCEPTED
date: 2026-10-02
confidence: MEDIUM
components: [configuration, pipeline]
tags: [config, ssot, compatibility]
supersedes: []
superseded_by: []
related_experiments: []
related_failures: [FAIL-0001, FAIL-0002, FAIL-0003]
related_cases: [CASE-0001, CASE-0002]
---

# Decision Record: DEC-0006 — Config Single Source of Truth

## Context / Problem
Example YAML/schema, runtime code, BAT and documentation independently described
different values. Old example settings were not consumed by the scripts. Applying
documented ideals would change candidate counts, quotas, identity and restoration.

## Decision
Capture existing runtime defaults in the example and schema; share one loader
across Step00–10. Explicit CLI overrides YAML, which overrides code fallback.
Use the example only when local YAML is absent; permit partial local settings.
Resolve relative paths from root, accept explicit absolute local source paths,
and reject relative traversal. Keep all standalone BAT entrypoints and the
existing human-review pause. Record counts separately: Step7 pool, Step8 initial
review, and human-curated final guidance.

## Alternatives
- Force old YAML/docs defaults into code: rejected because it changes behavior.
- Remove all constants at once: rejected because safe fallbacks remain useful.
- Silent acceptance of old unused keys: rejected because it implies false control.
- Implement InsightFace, new quotas or HTML now: deferred beyond STEP0 scope.

## Evidence (facts)
Frozen defaults and real argument declarations pass lightweight comparison.
Synthetic Step2/7/8 comparisons preserve reports, scores, choices and copied files.
`docs/STEP0_VERIFICATION.json` records the comparison and unchanged baseline hash.
No new GPU/model inference result is claimed.

## Consequences
Configuration validation is now mandatory (jsonschema dependency). Invalid local
settings fail early; old template-only keys require migration to the new example.
Explicit relative CLI paths now consistently use project root even from other cwd.
Historical intended policies remain distinguishable from actual code.

## Do not violate
Pipeline runtime settings must not be independently redefined in Python/BAT/docs.
Code constants are explicit compatibility fallbacks; docs cite defaults from config.
Do not optimize thresholds or change algorithms as part of configuration cleanup.
Keep DINO, existing quotas, scoring, extraction, restoration and caption behavior
until an explicitly scoped later step authorizes changes. Preserve baseline metrics.

## 2026-10-08 Training Contract supplement

Explicit user scope adds training adapter/base model/trigger/dataset/caption
format+version/LoRA/image target to config SSOT. Project/training triggers must
match; STEP10 prints the formal target and refuses a missing contract. PROJECT
references config without independent runtime values. Existing results and
external Training adapter files are not rewritten or assumed synchronized.
Local/example validation,24 tests and both STEP10 preflights PASS; no production
processing or Training. [Implementation](../../docs/TRAINING_CONTRACT_IMPLEMENTATION.md).
