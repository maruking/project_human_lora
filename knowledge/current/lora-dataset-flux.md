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
