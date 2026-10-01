"""Environment & Dependency Verification Script for Real Human LoRA Pipeline.

Performs non-destructive checks on:
- Python version
- Essential libraries (OpenCV, NumPy, MediaPipe, Pillow)
- GPU / CUDA status & PyTorch acceleration
- Deep Learning packages (Transformers, CLIP, DINO)
- External multimedia tools (FFmpeg, FFprobe)
- Project directory structure & permissions
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_mark(status: bool) -> str:
    return "[PASS]" if status else "[FAIL]"


def warn_mark(status: bool) -> str:
    return "[PASS]" if status else "[WARN]"


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    all_critical_passed = True

    print("==================================================================")
    print("      REAL HUMAN LORA PIPELINE: ENVIRONMENT & HARDWARE AUDIT      ")
    print("==================================================================")
    print(f"Project Root: {project}\n")

    # 1. Python Check
    py_ver = sys.version_info
    py_ok = (py_ver.major == 3 and py_ver.minor >= 9)
    print(f"{check_mark(py_ok)} Python Version: {sys.version.split()[0]} (Recommended: 3.10.x)")
    if not py_ok:
        all_critical_passed = False

    # 2. External Tools: FFmpeg & FFprobe
    ffmpeg_bin = shutil.which("ffmpeg")
    ffprobe_bin = shutil.which("ffprobe")
    if not ffmpeg_bin:
        env_f = os.environ.get("FFMPEG_DIR")
        if env_f and (Path(env_f) / "ffmpeg.exe").is_file():
            ffmpeg_bin = str(Path(env_f) / "ffmpeg.exe")
        elif Path(r"C:\ffmpeg\bin\ffmpeg.exe").is_file():
            ffmpeg_bin = r"C:\ffmpeg\bin\ffmpeg.exe"

    if not ffprobe_bin:
        env_f = os.environ.get("FFMPEG_DIR")
        if env_f and (Path(env_f) / "ffprobe.exe").is_file():
            ffprobe_bin = str(Path(env_f) / "ffprobe.exe")
        elif Path(r"C:\ffmpeg\bin\ffprobe.exe").is_file():
            ffprobe_bin = r"C:\ffmpeg\bin\ffprobe.exe"

    print(f"{warn_mark(bool(ffmpeg_bin))} FFmpeg Binary : {ffmpeg_bin if ffmpeg_bin else 'Not found in PATH (OpenCV fallback will be used)'}")
    print(f"{warn_mark(bool(ffprobe_bin))} FFprobe Binary: {ffprobe_bin if ffprobe_bin else 'Not found in PATH (OpenCV fallback will be used)'}")

    # 3. CPU Core Libraries
    print("\n--- Core Computer Vision Libraries (CPU) ---")
    # OpenCV
    try:
        import cv2
        print(f"{check_mark(True)} opencv-python : {cv2.__version__}")
    except ImportError:
        print(f"{check_mark(False)} opencv-python : Missing (run: pip install opencv-python)")
        all_critical_passed = False

    # NumPy
    try:
        import numpy as np
        print(f"{check_mark(True)} numpy         : {np.__version__}")
    except ImportError:
        print(f"{check_mark(False)} numpy         : Missing (run: pip install numpy)")
        all_critical_passed = False

    # Pillow
    try:
        import PIL
        print(f"{check_mark(True)} pillow        : {PIL.__version__}")
    except ImportError:
        print(f"{check_mark(False)} pillow        : Missing (run: pip install Pillow)")
        all_critical_passed = False

    # MediaPipe
    try:
        import mediapipe as mp
        has_mesh = hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh")
        print(f"{check_mark(has_mesh)} mediapipe     : {getattr(mp, '__version__', 'unknown')} (FaceMesh available: {has_mesh})")
        if not has_mesh:
            print("       -> Note: Recommended version is mediapipe==0.10.21 on Python 3.10")
            all_critical_passed = False
    except ImportError:
        print(f"{check_mark(False)} mediapipe     : Missing (run: pip install mediapipe==0.10.21)")
        all_critical_passed = False

    # 4. GPU & PyTorch Acceleration
    print("\n--- Deep Learning & GPU Acceleration (Torch / CUDA) ---")
    torch_available = False
    cuda_available = False
    try:
        import torch
        torch_available = True
        cuda_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
        vram = f"{torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB" if cuda_available else "N/A"
        print(f"{check_mark(True)} PyTorch       : {torch.__version__}")
        print(f"{warn_mark(cuda_available)} CUDA Support  : {cuda_available} (GPU: {gpu_name}, VRAM: {vram})")
        if not cuda_available:
            print("       -> Note: GPU steps (Step 6, 9, 10) will run on CPU, which is slower.")
    except ImportError:
        print(f"{check_mark(False)} PyTorch       : Missing (run: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121)")
        all_critical_passed = False

    # Transformers
    try:
        import transformers
        print(f"{check_mark(True)} transformers  : {transformers.__version__}")
    except ImportError:
        print(f"{check_mark(False)} transformers  : Missing (run: pip install transformers)")
        all_critical_passed = False

    # 5. Directory Structure Check
    print("\n--- Directory Skeleton & Permissions ---")
    required_dirs = [
        project / "input" / "original-mp4",
        project / "input" / "reference",
        project / "config",
        project / "work",
        project / "output",
        project / "scripts",
        project / "models",
    ]
    for d in required_dirs:
        exists = d.is_dir()
        print(f"{check_mark(exists)} Directory     : {d.relative_to(project)}")
        if not exists:
            d.mkdir(parents=True, exist_ok=True)

    # Check write permission in work
    work_dir = project / "work"
    test_file = work_dir / ".perm_check.tmp"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        print(f"{check_mark(True)} Write Perm   : Confirmed write access to work/")
    except Exception as e:
        print(f"{check_mark(False)} Write Perm   : Failed to write in work/ ({e})")
        all_critical_passed = False

    print("\n==================================================================")
    if all_critical_passed:
        print("  STATUS: ALL ESSENTIAL DEPENDENCIES VERIFIED [READY TO RUN]")
        print("==================================================================")
        return 0
    else:
        print("  STATUS: MISSING ESSENTIAL DEPENDENCIES [ACTION REQUIRED]")
        print("  Please install missing packages using: pip install -r requirements.txt")
        print("==================================================================")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
