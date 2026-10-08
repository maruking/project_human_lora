# STEP10 Caption V2 — Qwen3-VL preparation / minimum validation

Date: 2026-10-08 (Asia/Tokyo).

Subsequent final-TXT rendering revision: [natural format, three-image smoke and
existing-JSON reformat instructions](STEP10_CAPTION_V2_NATURAL_FORMAT.md).
The initial preparation evidence below remains historical; V2 generation was
subsequently performed by ★maru, while Codex's full natural reformat remains pending.

## Model files / integration

Approved model: Qwen/Qwen3-VL-8B-Instruct (user reports Chappy approval).
Configured local root: `C:\Users\maruk\Documents\makeLora\caption_vl`.

Initially tokenizer_config.json was missing. Supplied the official file from
revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` without replacing other files.
All four safetensors SHA256 values match the official repository's LFS metadata.
Index/header validation: four shards, 750 tensors, 17,534,247,392 tensor bytes.
The directory now has the required model/config/tokenizer/processor files.
`download_provenance.json` in the model directory records download/hash evidence.

Physical consolidation into one huge safetensors file is unnecessary. The official
index maps tensors to the four files; Qwen3VLForConditionalGeneration.from_pretrained
loads the shards together as one model. This path passed actual GPU loading.
No Qwen2.5-VL/CLIP/alternate-model fallback. No dependency installation was needed.

## Entry point / outputs

Normal BAT: [10_caption_v2_gpu.bat](../bat/10_caption_v2_gpu.bat).
Main implementation: [step10_caption_v2.py](../scripts/step10_caption_v2.py).
Local step10_caption_v2 config supplies model directory and GPU Python interpreter.
BAT retains the ordinary project Python for configuration/lineage orchestration;
the worker uses the existing AI Toolkit GPU venv (torch2.13.0+cu130,
transformers5.5.3). No AI Toolkit code or Training YAML changes.

Normal full run creates:

- output/dataset_flux_caption_v2/: identical v1 PNG filenames/bytes, new paired TXT
- output/reports/step10_caption_v2.csv: original audit identities/order, v1 image
  SHA256, raw VLM JSON, final caption, parsed/omitted attributes, model/index/prompt
  provenance and generation settings, PENDING_HUMAN_REVIEW
- docs/STEP10_CAPTION_V2_REVIEW.html: clickable images, v1/v2 captions and raw output

The final selected export is linked to the unchanged full upstream audit; its
cardinality is the actual STEP8_ACCEPT count, never a hard-coded subject count.

## Caption behavior

VLM reads each v1 image directly; no CLIP candidate choices. JSON attributes are
free text: shot, pose, clothing, hair_style, background, lighting, expression.
Prompt asks for observed garment type/color/pattern, omitting uncertainty and
intrinsic facial features. Final caption starts with the configured trigger once
and woman. Forbidden facial/age/generic-trigger language and uncertain phrases are
omitted with audit reasons; malformed/truncated VLM output STOPs.
No new guesses or captions substituted when generation fails.

Prompt rules and lexical screening cannot prove visual correctness or catch every
possible hallucination/face-description synonym. Human Review remains required.
Even the small smoke sample uses profile for shot and describes the background as
window/shelves; framing/background wording should be checked by a human.
No claim that all40 captions are accurate has been made.

## Baseline and generation safety

Reads current STEP8 accepted lineage/source hashes and the v1 STEP10 audit; checks
the same identity/order/generation/session and paired-image inventory. V1 files are
pinned and rechecked after inference; copying uses byte-for-byte copyfile, with
SHA256 equality checked. No resize/re-encode of output/source images.
Processor preprocessing occurs only in memory for inference.

V1 Dataset and existing LoRA artifacts remain at their current locations untouched
as Baseline. No v1 overwrite, image transformation, STEP1–9 rerun or LoRA training.
Existing V2 output paths cause STOP rather than overwrite. Failed runs preserve
raw/job/prompt staging in ignored work/.caption_v2_stage_*/ for diagnosis.
Validated outputs publish from staging; the three-path publish is not a single
atomic transaction and a publication I/O failure can leave partial V2 artifacts.
Preserve them before a rerun; never delete source/baseline to recover.

## Minimum validation — observed

- Required files and official SHA256: PASS, four/four shards.
- Current authoritative input: preflight PASS, 40 images, exact accepted order.
- Unit tests: eight PASS (free clothing, trigger/face/uncertainty omission,
  invalid/missing JSON, missing tokenizer and truncated shard STOP).
- Real GPU smoke: one image tested with initial and refined prompts; both PASS.
  Final refined raw output correctly includes pink hoodie with text print and long
  straight hair; this is bounded evidence, not full-dataset visual validation.
- V1/source/input pins checked unchanged after smoke.
- Full40 VLM caption generation: NOT EXECUTED.
- Official V2 CSV/HTML/Dataset: NOT YET CREATED.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, Pipeline Rules,
Data Lineage Rules, applicable Knowledge/DEC-0029, Failures/Cases.
Data lineage preserved: YES. Full-row preservation: YES for unchanged upstream
audit; new selected40 export is pending. Historical evidence preserved: YES.
Config SSOT preserved: YES. Rule conflicts: none.
README/Decisions/Knowledge checked; new caption-policy Decision recorded as
DEC-0030. Earlier STEP10 implementation/preparation evidence remains unchanged.

## ★maru

Run from PowerShell:

```powershell
& "C:\Users\maruk\Documents\Genelate_img\Sasha_re_codex\real_human_lora\bat\10_caption_v2_gpu.bat"
```

After success open docs/STEP10_CAPTION_V2_REVIEW.html. Check clothing, hairstyle,
framing/pose and background. Share incorrect captions with Chappy.
Do not retrain until Human Review completes.
