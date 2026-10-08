# Current Training Contract — implementation / preflight

Date: 2026-10-08 (Asia/Tokyo). Training executed:NO.

## SSOT / changed files

`config/config.yaml:training` is the authoritative Project Training Contract.
`config/config.example.yaml` carries the requested current bootstrap values.
The example project trigger was aligned to its training trigger as explicitly
requested; no subject/count constants were added to generic processing code.

Changed:

- config/config.yaml and config/config.example.yaml: training section
- config/config.schema.json: required fields/types within an optional training object
- scripts/common/config.py: trigger consistency error, training dataset path
  validation, shared Training Target printer (no historical-model fallback)
- scripts/package_flux_dataset.py and scripts/step10_caption_v2.py: startup display
- bat/10_package_flux_dataset_gpu.bat: remove hard-coded FLUX.1 banner
- package_flux_dataset.py generated guide: current model/adapter/rank/caption
  settings now read from contract; obsolete hard-coded Training recommendations
  removed from future guides. Existing exported guides are not rewritten.
- PROJECT.md: Current Training Target references config without copied runtime values
- tests/test_training_contract.py and tests/test_config.py: Contract tests/current
  configured trigger expectation; frozen historical defaults retained
- This report and related configuration Knowledge/Decision supplement

## Config snapshot (observed, not a second runtime configuration)

```yaml
training:
  adapter: ai-toolkit
  base_model:
    name_or_path: black-forest-labs/FLUX.2-klein-base-9B
    arch: flux2_klein_9b
  trigger_word: sasha_rh
  dataset:
    path: output/dataset_flux_caption_v2
    caption_format: natural_language
    caption_version: step10_caption_v2
  lora:
    rank: 16
    alpha: 16
  target:
    final_images: 40
```

## Preflight output (observed)

Both normal STEP10 entrypoints display:

```text
TRAINING TARGET
Base Model: black-forest-labs/FLUX.2-klein-base-9B | arch: flux2_klein_9b
Adapter: ai-toolkit
Trigger: sasha_rh
Dataset: output/dataset_flux_caption_v2
Caption Version: step10_caption_v2 | format: natural_language
```

Caption V2 preflight: PASS, same40 accepted rows, four-shard index validation.
Original packaging preflight: PASS, accepted40/input40, STEP8_ORIGINAL,
SKIPPED_NOT_NEEDED. Packaging/model load/image changes/caption generation:NO.

## Minimum validation / boundaries

- Local config and example: schema + application validation PASS.
- Training Contract5 + config8 + STEP10 input11 tests:24 PASS.
- project.trigger_word != training.trigger_word: explicit ConfigError.
- Missing training section: STEP10 STOP, no fallback to old Training defaults.
  Other STEPs can still read partial legacy configs; training is optional at the
  root schema for compatibility, while its fields are required when present.
- Training dataset path is validated against normal path/traversal rules.
- No full packaging, reformat, VLM inference, model download or Training performed.
- STEP1–9 programs/results,40 images,V1/V2 image content,AI Toolkit application
  and its existing Training YAML are unchanged.

This task declares/displays the Training Target; it does not automatically change
STEP10 Baseline export paths or synchronize external adapter files. In particular,
the existing AI Toolkit YAML `config/sasha_realhuman_flux2_klein9b.yaml` still points
to `output/dataset_flux` (V1), verified read-only. Before any future Training that
external Dataset path must be synchronized with this contract in separate scoped
work. Display/preflight PASS does not mean adapter synchronization, Human Review
completion or Training readiness.

Rules checked: AGENTS.md,.agents/AGENTS.md,PROJECT.md,Pipeline/Data Lineage Rules,
relevant configuration/STEP10 Knowledge, DEC-0006/DEC-0030 and Failures/Cases.
Data lineage preserved:YES. Full-row preservation:YES (all existing audit rows
unchanged; no dataset processing). Historical evidence preserved:YES.
Config SSOT preserved:YES. User-specific example values were explicitly requested;
no other rule conflict. Documentation checked; existing Decision supplemented.

## ★maru

Share this report, the updated config.yaml training section, and the preflight
display above with Chappy. No production BAT rerun or Training is needed for this
Contract implementation confirmation.
