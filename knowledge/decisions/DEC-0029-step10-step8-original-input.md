---
id: DEC-0029
title: STEP10 validated STEP8 original-image input when STEP9 is skipped
status: ACCEPTED
date: 2026-10-07
confidence: MEDIUM
components: [packaging, lineage, human-review]
tags: [step9-skip, explicit-accept, source-hash, preflight]
supersedes: []
superseded_by: []
related_experiments: []
related_failures: [FAIL-0001]
related_cases: []
---

# Context / decision

User chooses no restoration and requests packaging bridge, preflight first only.
Legacy STEP10 directory enumeration could ingest unselected/stale assets and require
an absent restored directory. Use validated STEP8_ACCEPT originals whenSTEP9 formal
CSV is absent. Preserve current generation/session/frame/source hashes and exact
accepted set. Do not choose by basename/substring/directory membership. Mark SKIP
explicitly. User-requested SKIP is not a diagnostic quality claim; prior10 review
recommendations are still recorded and not overwritten.

FormalSTEP9 route retains restored data/status after exact accepted-set/source
hash/session/generation/restored-file hash verification. An existing report lacking
this proof STOPs as ambiguous; do not silently fall back. No STEP9 writer changes.

Preflight returns before model load/caption/alignment/output mutation. Captions and
16px alignment functions unchanged. Output audit adds lineage. Future export uses
validated list only; invalid image decode/encode stops, source/output overlap refused,
nonempty export directory refused to avoid mixing previous outputs.

# Evidence / scope

19 synthetic/config tests PASS and actual40-row preflight PASS. Caption/alignment
AST equal to original. No actual packaging,AI inference or model cache verification.
Readiness is input preflight only, not production export or LoRA quality. Legacy
export can leave partial outputs on midrun failure; separate transactional-export
work is outside scope. STEP3–9,selected originals,Human Review unchanged.

[Implementation](../../docs/STEP10_STEP9_SKIP_IMPLEMENTATION.md).
