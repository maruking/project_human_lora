# Pipeline Architecture & Data Flow

This document details the modular software architecture, file directories, data flows, and batch script mappings of the **Real Human LoRA Dataset Pipeline**.

---

## 1. Pipeline Stage Matrix

| Step | Script | Batch File | Hardware | Input | Output | Gate / Filter |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- |
| **00** | `verify_environment.py` | `00_environment_check.bat` | CPU | Environment & PATH | Console Audit | Python, FFmpeg, CUDA, Libs |
| **01** | `extract_frames.py` | `01_extract_frames.bat` | CPU | `input/original-mp4/` | `work/frames_raw/` | 50 equidistant segments/video |
| **02** | `score_blur.py` | `02_technical_metrics.bat` | CPU | `work/frames_raw/` | `output/reports/step2_*.json` | Laplacian variance $\ge 80.0$ |
| **03** | `face_quality_gate.py` | `03_face_quality_gate.bat` | CPU | `work/frames_raw/` | `output/reports/step3_*.json` | Sharpness $\ge 18$, Plasticity $\le 70$, Texture $\ge 15$ |
| **04** | `classify_face_pose.py` | `04_classify_face_pose.bat` | CPU | `work/frames_raw/` | `output/reports/step4_*.json` | Yaw/Pitch angles, Shot ratios |
| **05** | `face_deduplication.py` | `05_face_deduplication.bat` | CPU | `work/frames_raw/` | `output/reports/step5_*.json` | dHash / pHash distance $\le 5$ |
| **06** | `evaluate_identity.py` | `06_evaluate_identity_gpu.bat` | **GPU** | `input/reference/` | `output/reports/step6_*.json` | Cosine similarity $\ge 0.55$ |
| **07** | `score_lora_candidates.py` | `07_score_lora_candidates.bat` | CPU | All Step Reports | `work/selected/` | Multi-objective quota balancing (30 imgs) |
| **08** | `prepare_human_review.py` | `08_prepare_human_review.bat` | CPU | `work/selected/` | `output/reports/*.html` | Visual Human Review Dashboard |
| **09** | `selective_restoration.py`| `09_selective_restoration_gpu.bat` | **GPU** | `work/selected/` | `work/restored/` | Component-only mask (Eyes/Lips) + Raw Skin |
| **10** | `package_flux_dataset.py` | `10_package_flux_dataset_gpu.bat` | **GPU** | `work/restored/` | `output/dataset_flux/` | Aspect-ratio bucketing + Anti-overfitting captioning |

---

## 2. Directory Structure Conventions

```text
project_human_lora/
├── .agents/                      # AI Coding Agent guidance and rules
│   ├── AGENTS.md                 # Agent operation protocol
│   ├── rules/                    # Inviolable project rules
│   └── skills/                   # Knowledge maintenance skills
├── config/                       # Pipeline configuration
│   ├── config.example.yaml       # Template configuration
│   └── config.schema.json        # Schema validation
├── bat/                          # Individual and consolidated execution scripts
│   ├── _common.bat               # UTF-8 & Python environment initialization
│   ├── 00_environment_check.bat  # Pre-flight environment auditor
│   ├── 01_extract_frames.bat ... 10_package_flux_dataset_gpu.bat
│   └── run_all.bat               # Consolidated runner with Human Review pause
├── scripts/                      # Core Python implementations
├── input/
│   ├── original-mp4/             # Source video files (.mp4, .mov, etc.)
│   └── reference/                # High-res ground-truth target subject photos
├── work/                         # Intermediate workspaces (git-ignored)
│   ├── frames_raw/               # Extracted frames from Step 01
│   ├── facegate_review/          # Visual audit of passed / rejected faces
│   ├── identity_review/          # Low similarity imposter review
│   ├── selected/                 # Curated 30 training candidates
│   └── restored/                 # Mask-restored photographic candidates
├── output/
│   ├── dataset_flux/             # Finalized training images and .txt captions
│   └── reports/                  # JSON metrics and HTML review dashboards
├── knowledge/                    # Long-term development memory
│   ├── current/                  # Active production policies
│   ├── decisions/                # Architectural Decision Records (ADRs)
│   ├── failures/                 # Failed experiments and anti-patterns
│   ├── cases/                    # Counterexamples and edge cases
│   └── templates/                # Standardized documentation templates
├── experiments/                  # Reproducible empirical benchmark logs
├── artifacts/                    # Benchmark tables and confusion matrices
└── docs/                         # Architecture and benchmark specifications
```
