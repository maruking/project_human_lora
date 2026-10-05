# Pretrained Model Weights Guide

This repository does **not** bundle large model weight binary files to keep git clone fast, lightweight, and clean.  
All models are standard open weights and can be automatically or manually downloaded into this `models/` directory.

---

## 1. Directory Layout

Place downloaded weight files in the following layout:

```text
models/
├── codeformer/
│   └── codeformer.pth                    # Face Restoration (Step 9)
├── facexlib/
│   ├── detection_Resnet50_20200713.pth   # Face Alignment / Landmark Detection
│   └── parsing_parsenet.pth              # Facial Component Mask Parsing
└── insightface/
    └── models/
        └── buffalo_l/                    # Face Identity Embedding (Step 6)
            ├── 1k3d68.onnx
            ├── 2d106det.onnx
            ├── genderage.onnx
            ├── glintr100.onnx
            └── w600k_r50.onnx
```

---

## 2. Automatic Fallback Behavior

- **Step 06 (Identity Evaluation)**:  
  If InsightFace weights are not found, the script automatically attempts on-demand downloading via the InsightFace API, or falls back to standard facial landmark cosine comparison.
- **Step 09 (Selective Restoration)**:  
  If `codeformer.pth` is not present, `scripts/selective_restoration.py` **will not crash**. It gracefully falls back to passing through 100% untouched raw camera frames (`work/selected/` $\to$ `work/restored/`) and logs a clear notice.

---

## 3. Manual Download Instructions

### A. CodeFormer Weights (Step 09)
- **Official Hugging Face Mirror**:  
  https://huggingface.co/sczhou/CodeFormer/resolve/main/codeformer.pth
- **Direct Download via PowerShell**:
  ```powershell
  New-Item -ItemType Directory -Force -Path "models\codeformer"
  Invoke-WebRequest -Uri "https://huggingface.co/sczhou/CodeFormer/resolve/main/codeformer.pth" -OutFile "models\codeformer\codeformer.pth"
  ```

### B. facexlib Face Parsing Weights (Step 09 Masking)
- **Face Parsing**:  
  https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/parsing_parsenet.pth
- **Face Detection (ResNet50)**:  
  https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/detection_Resnet50_20200713.pth

### C. InsightFace Buffalo_l Weights (Step 06)
- **Hugging Face / Google Drive**:  
  InsightFace automatically downloads `buffalo_l.zip` to `~/.insightface/models/buffalo_l/` upon first run.  
  Alternatively, download from:  
  https://github.com/deepinsight/insightface/releases/tag/v0.7
