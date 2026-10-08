---
topic: lora-dataset-flux
last_updated: 2026-10-01
confidence: HIGH
status: ACTIVE
related_decisions:
  - DEC-0005
related_failures: []
related_cases: []
---

# Current Knowledge: FLUX.1 LoRA Dataset Packaging & Captioning

> STEP0 implementation audit: current Step10 aligns existing dimensions to multiples of 16 and uses CLIP attributes with existing caption templates. Aspect buckets and caption cleanup below remain intended future work. See [configuration.md](configuration.md).


## 1. Current Policy
Format, bucket, and caption the finalized selected/restored dataset for optimal FLUX.1 Schnell/Dev LoRA fine-tuning. Prevent overfitting subject facial features to specific clothing or background items while preserving maximum generation flexibility.

## 2. Recommended Approach
- **Aspect-Ratio Bucketing (Step 10)**: Resize images into standard FLUX buckets (1:1, 9:16, 16:9, 3:4, 4:3) maintaining megapixels close to 1.0 MP ($1024 \times 1024$ equivalent) with zero stretching or distortion.
- **Trigger Strategy**: Use a unique trigger token prefix (e.g. `[trigger], ` or `ohwx person, `).
- **Caption Generation**: Generate descriptive context tags (lighting, clothing, background, camera framing) while intentionally **omitting descriptions of intrinsic facial features** (eye shape, nose, lips). This forces the LoRA to associate all facial identity cues exclusively with the trigger token.

## 3. Hard Rules (Enforced by Code)
- Resolutions must be divisible by 16 or 32 for latent diffusion autoencoders.
- Images and corresponding `.txt` caption files must share exact identical basenames in `output/dataset_flux/`.

## 4. Soft Rules (Guidelines for Human Review)
- Check that no captions inadvertently include watermarks, phone UI text, or timestamp tags.

## 5. Validated Conditions (Works When)
- Verified with standard Kohya-ss / AI-Toolkit / SimpleTuner FLUX LoRA training pipelines.

## 6. Known Failure Modes & Limitations (Unreliable When)
- **Over-captioning facial features**: Captioning "round brown eyes, thin lips" teaches the model that those features are variable rather than inherent to the trigger word. Keep facial identity bound to the trigger.

## 7. Do Not Use When
- Do NOT upscale 480p low-res frames to $1024 \times 1024$ without bucketing checks; ensure original quality is sufficient.

## 8. Not Yet Validated
- Extreme non-standard aspect ratios wider than 21:9 or taller than 9:21.

## 2026-10-07 current input bridge — DEC-0029

Missing STEP9 formal restoration report -> validated STEP8_ACCEPT originals only.
Verify exact frame IDs,source paths,image hashes; no directory scan. Current40
preflight PASS; SKIPPED_NOT_NEEDED recorded. Existing formalSTEP9 rows use restored
files after current source/generation/session/restored hashes verified; ambiguous
legacyCSV STOPs. Original/raw source remains unchanged; export alignment only affects
future output files. Current captions/CLIP classifier and16px functions unchanged.
--preflight-only loads no CLIP/model and creates no export.19 tests PASS.
Packaging not run; ★maru first runs10 BAT with--preflight-only and shares console
with Chappy. Earlier bucket/model quality claims above are historical policy,
not evidence that this40-image production export/training is validated.
[Implementation](../../docs/STEP10_STEP9_SKIP_IMPLEMENTATION.md).

## 2026-10-07 authorized STEP10 trigger rePackaging

The preceding no-packaging statement describes the implementation-stage preflight.
Subsequent explicit user authorization executed the existing10 BAT for selected40.
Local project.trigger_word now uses a unique literal token; all40 paired captions
contain it exactly once, with no old generic trigger. Export image hashes match the
previous40, original source hashes and36 upstream report hashes remain unchanged.
Historical export/report/baseline retained in output/bkup. No STEP1–9 rerun.
Current AI Toolkit Klein Base9B config passes get_config / typed constructors /
validate_configs; process/dataset trigger injection omitted because captions already
contain the literal trigger. Training and actual VRAM fit remain unvalidated.
[Preparation result](../../docs/STEP10_SASHA_RH_TRAINING_PREPARATION.md).

## 2026-10-08 Caption V2 — DEC-0030

Separate Qwen3-VL image-grounded caption export is implemented. No CLIP fixed
attribute choices or alternate-model fallback. Preserve v1 image bytes/order/frame
IDs and Dataset/LoRA Baseline. Only variable attributes, one configured trigger;
raw response/final text/omissions audited. Human Review required before retraining.
Four official shard hashes,40-input preflight,eight tests and two one-image smoke
checks PASS. Full40 generation pending ★maru; no accuracy claim from this small test.
[Implementation and BAT](../../docs/STEP10_CAPTION_V2_IMPLEMENTATION.md).

### Natural final-caption rendering revision

Final TXT now uses configured trigger followed by short natural sentences; stored
VLM JSON/attributes stay unchanged. Existing full V2 may be reformatted without
inference via --reformat-existing, archiving old V2 first. Three stored-response
smoke and12 tests PASS; full40 reformat pending ★maru. No training or V1 changes.
[Current rendering result and smoke instructions](../../docs/STEP10_CAPTION_V2_NATURAL_FORMAT.md).
