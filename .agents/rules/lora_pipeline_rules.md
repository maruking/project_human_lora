# Real Human LoRA Pipeline - Core Project Rules

This document establishes the inviolable architectural and operational rules for any developer or AI coding agent modifying this repository.

---

## Rule 1: Pipeline Architecture & Non-Breaking Invariance
1. **Preserve Individual STEP Batch Files**:
   - `01_extract_frames.bat` through `10_package_flux_dataset_gpu.bat` must remain standalone executable.
   - Do NOT delete, combine, or abstract away step-level BAT files into a single monolithic script. They are critical for isolated debugging, threshold tuning, and error triage.
2. **GPU Step Explicit Naming**:
   - Any batch file executing CUDA/GPU-intensive workloads must carry the `_gpu.bat` suffix (`06_evaluate_identity_gpu.bat`, `09_selective_restoration_gpu.bat`, `10_package_flux_dataset_gpu.bat`).
3. **Strict Exit Codes**:
   - Every script and batch file must exit with a non-zero code upon failure (`exit /b 1` / `sys.exit(1)`).
   - Monolithic runners (`run_all.bat`) must check `if errorlevel 1` after every step and abort immediately.

---

## Rule 2: Skin Texture & Anti-Artificial Quality Standard
1. **Zero Tolerance for Plastic / Beauty-Smoothed Skin**:
   - Real Human LoRA requires photographic realism (pores, fine vellus hair, authentic camera sensor grain).
   - Frames processed by TikTok/Instagram beauty filters (smoothed skin with aggressive edge sharpening) must be systematically rejected via Step 03's `plasticity_ratio` and `skin_texture_score`.
2. **Prohibition of Whole-Face AI Upscaling**:
   - In Step 09, CodeFormer or any neural restoration model must **never** be applied to the whole face or cheek/forehead skin.
   - Restoration is strictly restricted to fine anatomical features: eyes, pupils, eyebrows, and lips. The cheeks, forehead, and neck must retain 100% untouched raw camera pixel data.

---

## Rule 3: Diversity & Quota Enforcement
1. **Strict Composition Balancing**:
   - The final candidate pool must strictly conform to:
     - Close-up (face focus): **40%**
     - Medium shot (upper body): **40%**
     - Full-body / Wide (environmental): **20%**
   - A dataset skewed solely toward close-ups causes catastrophic angle collapse and prevents generating medium/wide shots.
2. **Multi-Angle Head Pose Distribution**:
   - Do not select exclusively frontal head poses. Half-profile (15°–45°) and profile (45°–90°) angles must be actively preserved.

---

## Rule 4: Human-in-the-Loop Gateway
1. **Mandatory Step 08 Inspection**:
   - Automated candidate scoring (Step 07) produces a curated set in `work/selected/`.
   - The pipeline runner (`run_all.bat`) must pause after Step 08 to allow human visual review and manual culling before proceeding to destructive/upscaling stages (Step 09 & 10).

---

## Rule 5: Zero Data Leakage & Strict Portability
1. **No Personal or Absolute Paths**:
   - Never commit code containing machine-specific paths (e.g., `C:\Users\maruk\...`) or personal identifiers.
   - All paths must resolve dynamically relative to `PROJECT_ROOT` or via `config/config.yaml`.
2. **No Private Assets in Git**:
   - Never commit raw videos, extracted faces, training datasets, or `.pth` model weights. Keep `.gitignore` strictly enforced.
   - Distribute configuration only via `config/config.example.yaml`.

---

## Rule 6: Windows CMD & Shell Safety
1. **UTF-8 Code Page**:
   - Always invoke `chcp 65001 >nul` at the beginning of all batch scripts to handle Japanese filenames and Unicode characters safely.
2. **Command Separator Escaping**:
   - In Windows CMD batch files, unquoted `&` acts as a command separator. Always use `^&` or write `and` in `echo` statements.
