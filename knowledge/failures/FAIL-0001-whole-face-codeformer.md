---
id: FAIL-0001
title: Whole-Face Neural Restoration via Global CodeFormer
date: 2026-09-30
confidence: HIGH
components:
  - restoration
  - face-quality
tags:
  - codeformer
  - plastic-skin
  - ai-artifact
  - texture-loss
related_experiment: []
related_decision: DEC-0004
---

# Failure Record: FAIL-0001 - Whole-Face Neural Restoration

## 1. Context & Objective
We wanted to maximize image resolution and sharpness for small or slightly compressed video frames before feeding them into FLUX LoRA training. The objective was to eliminate blur across the entire face.

## 2. The Attempted Approach
Applied CodeFormer with fidelity weight $w = 0.6$ to the entire detected face bounding box, blending the entire restored face back into the source image with edge feathering.

## 3. Why It Looked Reasonable at the Time
- CodeFormer is a state-of-the-art face restoration model widely praised in the AI community.
- Visually, the restored full-face image looked extremely clear, smooth, and sharp on low-resolution previews.
- Standard computer vision metrics (PSNR, LPIPS, Laplacian variance) showed significant increases.

## 4. Observed Failure (Facts)
- **Loss of Micro-Texture**: Natural skin pores, fine vellus hair, authentic skin grain, and real camera sensor noise were completely wiped out from the cheeks, nose, and forehead.
- **AI-Veneer Artifacts**: The skin developed an unnatural waxy, painted sheen with uniform specular highlights.
- **Downstream Generation Catastrophe**: When a FLUX.1 LoRA was trained on these images, 100% of generated outputs had unmistakable "AI plastic skin". Prompts specifying "photorealistic 35mm film photography, visible pores" still generated cartoonish, airbrushed faces.

## 5. Root Cause Analysis (Interpretation)
CodeFormer relies on a VQGAN codebook trained on clean studio portraits. When confronted with complex real-world camera noise or mild video compression, it replaces true stochastic pixel distributions with smooth codebook priors. For LoRA training, the diffusion model memorizes this synthetic smoothness as an intrinsic feature of the subject.

## 6. Conditions Where It Failed
- Universal failure across all training datasets intended for photographic realism.
- Even at maximum fidelity ($w=0.9$), skin texture suffered unacceptable plastic degradation.

## 7. Conditions Where It May Still Work
- Anime, 3D render, or stylized character LoRAs where natural skin pores are not desired.
- Extreme archival image recovery (where original skin detail is already 100% destroyed).

## 8. DO NOT RETRY UNLESS (Mandatory Guardrail)
> [!CRITICAL]
> **DO NOT RETRY UNLESS ALL OF THE FOLLOWING ARE TRUE:**
> 1. The target model being trained is explicitly stylized, anime, or 3D cartoon (non-photographic).
> 2. Or, a breakthrough neural restorer is developed that provably reconstructs ground-truth stochastic epidermal pores without synthetic hallucination (must be verified by high-frequency spatial Fourier analysis).

## 9. Superseded By / Counter-measure
**`DEC-0004` (Selective Component Restoration)**: Confined restoration strictly to eyes, pupils, eyebrows, and lips using semantic masks, leaving 100% of cheek/forehead raw camera sensor pixels untouched.
