# STEP1 — Upscaled source extraction result

2026-10-02 (Asia/Tokyo). Explicitly authorized by the user.

- Input: `original-mp4/upscale`,67 videos already upscaled.
- Active output: `work/frames_raw`,1,893 new PNG frames; STEP1 PASS, failed0.
- Config sampling unchanged:2 FPS, maximum120/video, policy2; existing FFmpeg/native-dimension PNG implementation unchanged.
- Additional stills:58 under `Sash_high_identity-img`, unchanged by SHA256/name/size.
- Complete inventory:1,951 rows =1,893 VIDEO_FRAME +58 SUPPLEMENTAL_STILL.
- Upscale processing: NO. STEP2/STEP3/4+, thresholds, review recreation, selection: not performed.

The current source folder lacks previous v02/v18/v43/v69. Available videos retain
their established IDs, including gaps. All old71-source mappings/extraction/summary
and normalized copies were retained in
`work/videos_previous/upscale_92dd538644254cd898215d47a74bc02e/`.
`work/manifests/step1_upscale_transition.json` retains absent mappings as inactive_rows
and links old original hashes/paths to new upscaled sources. Missing originals and
deleted selected-image folders were not recreated.

## Commands / reusable BAT route

Actual extraction:

```cmd
bat\01_extract_frames.bat --skip-upscale --available-upscaled-only
```

Actual inventory creation:

```cmd
py -3.10 scripts/build_step1_image_inventory.py --supplemental-dir Sash_high_identity-img
```

Both operations are now available through the normal single BAT entry:

```cmd
bat\01_extract_frames.bat --skip-upscale --available-upscaled-only --supplemental-dir Sash_high_identity-img
```

No extra production replay was run for validation. Local Config SSOT now points
raw_frames_dir to `work/frames_raw`; the supplemental input is explicitly supplied
for this listing, not made a global default.

## Verification / evidence

- [Complete image CSV](../output/reports/step1_image_inventory.csv)
- [Inventory receipt](../output/reports/step1_image_inventory.json)
- [Execution verification](../output/reports/step1_upscaled_execution_audit/verification.json)
- [Extraction log](../output/reports/step1_upscaled_execution_audit/extraction.log)
- [STEP1 summary](../work/manifests/step1_summary.json)

The extractor verified generated PNGs and hashes. The inventory checked exact
current filename/size/count coverage against these receipts; formal hashes were
read from extraction metadata rather than recomputed again. Supplemental hashes
were measured directly and all58 match the before-execution snapshot.
STEP2/STEP3 report hashes are unchanged. These reports remain prior-generation
evidence and are not current metrics for newly generated frames.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, both Project Rules and
previously consulted STEP1 Knowledge/Decisions/result. Data lineage preserved: YES.
Full-row preservation: YES for the new67-video generation and explicit complete
1,951-image listing. Historical evidence preserved: YES. Config SSOT preserved: YES.
No visual-quality/LoRA-fitness claim. Full frame-extraction batch: YES (authorized).
Full upscale batch: NO.
