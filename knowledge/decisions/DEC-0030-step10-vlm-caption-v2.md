---
id: DEC-0030
title: Separate image-grounded VLM Caption V2 with preserved baseline
status: ACCEPTED
date: 2026-10-08
confidence: MEDIUM
components: [captioning, packaging, lineage]
tags: [vlm, baseline, human-review, no-fallback]
supersedes: []
superseded_by: []
related_experiments: []
related_failures: []
related_cases: []
---

User authorizes Caption V2 policy and approves Qwen3-VL-8B-Instruct instead of the
initial Qwen2.5-VL candidate. Keep v1 Dataset/LoRA as Baseline; separate export with
same selected identities/order/image bytes. No automatic model fallback.

Free image-grounded variable attributes only; configured trigger exactly once,
woman, no intrinsic face features, young girl or uncertain inferred attributes.
Record raw response and final caption for Human Review. Keep upstream selection,
sources and training untouched. DEC-0029 input lineage remains active; this does
not supersede its validated selection bridge or rewrite historical CLIP results.

Evidence: official four-shard SHA256 match,40-row preflight, eight synthetic tests,
two one-image GPU smoke checks. Full40 V2 captions not generated; higher accuracy
and visual correctness remain unvalidated. Lexical filtering is a guard, not proof
of semantic correctness. Human Review must precede retraining.

[Implementation and operational instruction](../../docs/STEP10_CAPTION_V2_IMPLEMENTATION.md).

## Supplement: natural final TXT

User requires trigger plus short natural sentences for final training TXT while
retaining raw structured VLM evidence. Normalize clear framing shorthand only;
omit unknown framing rather than guess. Existing V2 can be reformatted from saved
JSON with explicit --reformat-existing; prior V2 is archived before publication.
Three-response format smoke and12 tests PASS; no full reformat or training by Codex.
[Rendering revision](../../docs/STEP10_CAPTION_V2_NATURAL_FORMAT.md).
