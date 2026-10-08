# STEP10 Caption V2 — final TXT natural sentence format

Date: 2026-10-08. This revision changes final text rendering, not VLM inference.

## Changes

- scripts/step10_caption_v2.py: trigger followed by short natural sentences;
  normalize observed shot shorthand (medium → medium shot, head and shoulders →
  head-and-shoulders shot), preserve free clothing/hair/context wording.
- Uncertain/prohibited attributes still omitted with audit reasons. A direction-only
  shot such as profile is not guessed into medium/close-up; recorded as omitted.
- Raw VLM JSON and original parsed attributes remain untouched. Existing generation
  prompt/model/settings/index provenance is preserved on reformat, with separate
  caption_format=natural_sentence_v1. Finalizer does not infer new image attributes.
- Tests updated for natural grammar, trigger uniqueness, raw preservation and
  unknown framing. Existing model/missing-file checks remain active.
- Added --format-smoke (three stored raw responses; no VLM/export) and
  --reformat-existing (all current V2 raw responses; no VLM).

Example test input/output:

```text
shot=medium, pose=sitting,
clothing=black one-piece swimsuit with a Mickey Mouse graphic

test_token. A woman is sitting in a medium shot, wearing a black one-piece swimsuit with a Mickey Mouse graphic.
```

The example is a unit fixture, not a claimed observation of a production image.

## Existing outputs and safe update path

Current V2 already contains the same selected40. Do not regenerate its VLM JSON.
--reformat-existing validates current accepted IDs/order, generation/session/source
hashes, model provenance and V1/V2 image hashes. Stage new caption/audit/HTML;
archive previous V2 Dataset/CSV/HTML under output/bkup/caption_v2_before_natural_*/.
Then publish the updated V2, preserving raw JSON exactly.
This archive occurs only when ★maru explicitly invokes --reformat-existing.
V1 Dataset, LoRA artifacts, original images and STEP1–9 remain untouched.
The three output paths are not an atomic transaction; publication failures leave
the staged/new artifacts and previous backup for recovery, not source deletion.

## Minimum validation

- 12 unit tests PASS.
- Existing accepted40 lineage/model/image checks PASS.
- Three stored raw responses formatted into a separate smoke HTML; production
  Dataset/CSV/HTML not changed. No new Qwen inference, no training.
- Same raw JSON / parsed attributes, trigger once and nonempty captions verified
  for smoke; original V2/V1 inputs pinned unchanged.
- Visual correctness of clothing/background etc. still requires Human Review.

Latest smoke: `work/.caption_v2_stage_t0_8907j/smoke_review.html`.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, Pipeline/Data Lineage Rules,
current STEP10 Knowledge and DEC-0030. Data lineage preserved:YES.
Full-row preservation:YES (unchanged full upstream audit; selected40 unchanged).
Historical evidence preserved:YES. Config SSOT preserved:YES.
Rule conflicts:none. Full batch executed:NO. Training executed:NO.
README/Knowledge/Decisions checked; update the existing Caption V2 record with
this supplementary rendering policy rather than create a duplicate Decision.

## ★maru

1. Open the latest three-image smoke HTML and confirm the natural text.
2. If acceptable, run:

```powershell
& "C:\Users\maruk\Documents\Genelate_img\Sasha_re_codex\real_human_lora\bat\10_caption_v2_gpu.bat" --reformat-existing
```

3. Review docs/STEP10_CAPTION_V2_REVIEW.html after completion. Keep training paused
   until Human Review is finished. There is no need to rerun the same Qwen inference.

Optional new smoke from the stored raw JSON:

```powershell
& "C:\Users\maruk\Documents\Genelate_img\Sasha_re_codex\real_human_lora\bat\10_caption_v2_gpu.bat" --format-smoke
```
