"""STEP 10: Dataset Packaging & FLUX Anti-Overfitting Captioning.

- Standardizes final images into clean sequential naming (<trigger>_01.png ... <trigger>_N.png).
- Micro-aligns dimensions to multiples of 16 for optimal FLUX VAE / latent compatibility.
- Runs offline CLIP (openai/clip-vit-large-patch14) zero-shot attribute classification
  for clothing, hairstyle, expression, background, and lighting.
- Combines 3D head pose and shot type ground-truth into natural-language anti-overfitting captions.
- Generates paired .txt caption files, metadata.jsonl (ai-toolkit / diffusers format),
  reports/step10_dataset_report.csv, and FLUX training guide.
"""

from __future__ import annotations

from common.config import configure_parser, configure_constants, load_for_cli, get_section, resolve_project_path

import argparse
import csv
import datetime
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from PIL import Image

import cv2
import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

STEP10_COLUMNS = (
    "step_name",
    "final_filename",
    "original_filename",
    "shot_type",
    "pose_bucket",
    "width",
    "height",
    "aligned_width",
    "aligned_height",
    "restoration_status",
    "clothing_desc",
    "hair_desc",
    "expression_desc",
    "bg_desc",
    "lighting_desc",
    "flux_caption",
    "tags_caption",
)


def write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> Path:
    """Safely write CSV handling potential Windows file locks."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    target_path = path

    def do_write(dst: Path) -> None:
        nonlocal temp_path
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=dst.parent, delete=False) as handle:
            temp_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_path, dst)

    try:
        do_write(target_path)
    except PermissionError:
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = path.parent / f"{path.stem}_{now_str}{path.suffix}"
        print(f"WARNING: '{path.name}' is locked by Excel. Writing to '{target_path.name}'.")
        do_write(target_path)
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
    return target_path


def align_dimension_16(val: int) -> int:
    """Align dimension to closest multiple of 16 for optimal VAE compression."""
    rem = val % 16
    if rem == 0:
        return val
    if rem >= 8:
        return val + (16 - rem)
    return max(val - rem, 16)


def align_image_16x(img: np.ndarray) -> np.ndarray:
    """Resize image to dimensions that are multiples of 16."""
    h, w = img.shape[:2]
    new_w = align_dimension_16(w)
    new_h = align_dimension_16(h)
    if new_w == w and new_h == h:
        return img
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


CLOTHING_PROMPTS = [
    "wearing an elegant black evening dress",
    "wearing a stylish black top",
    "wearing a casual white t-shirt",
    "wearing a warm knitted sweater",
    "wearing a denim jacket and pants",
    "wearing an oversized comfortable hoodie",
    "wearing a floral summer dress",
    "wearing casual modern streetwear",
    "wearing athletic sportswear",
    "wearing stylish casual clothes",
]

HAIR_PROMPTS = [
    "long dark hair falling over shoulders",
    "hair tied up in a neat ponytail",
    "hair styled in a messy bun",
    "wavy brunette hair with natural texture",
    "sleek straight dark hair",
    "short bob hairstyle",
    "natural textured hair",
]

EXPRESSION_PROMPTS = [
    "gentle warm smile looking at camera",
    "subtle cheerful smile",
    "calm neutral expression with soft gaze",
    "serious focused expression",
    "candid smiling laughter",
    "pensive contemplative look",
]

BACKGROUND_PROMPTS = [
    "clean modern indoor apartment with soft interior",
    "cozy living room with warm wooden furniture",
    "bright contemporary room with white minimalist background",
    "urban city street with subtle bokeh",
    "outdoor cafe patio with natural ambiance",
    "studio environment with neutral clean background",
    "sunlit room with window shadows in background",
]

LIGHTING_PROMPTS = [
    "soft diffused natural daylight",
    "warm cinematic indoor ambient lighting",
    "soft golden hour sunlight with gentle shadows",
    "clean professional studio lighting",
    "cool atmospheric interior lighting",
    "bright airy window light",
]


def classify_clip_attributes(
    image_bgr: np.ndarray,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: torch.device,
) -> dict[str, str]:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    categories = {
        "clothing": CLOTHING_PROMPTS,
        "hair": HAIR_PROMPTS,
        "expression": EXPRESSION_PROMPTS,
        "bg": BACKGROUND_PROMPTS,
        "lighting": LIGHTING_PROMPTS,
    }

    results = {}
    for cat_name, candidate_texts in categories.items():
        inputs = processor(
            text=candidate_texts,
            images=pil_img,
            return_tensors="pt",
            padding=True,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).squeeze(0)
            best_idx = int(torch.argmax(probs))
            results[cat_name] = candidate_texts[best_idx]

    return results


def build_flux_caption(
    trigger: str,
    shot_type: str,
    pose_bucket: str,
    attr: dict[str, str],
) -> tuple[str, str]:
    shot_desc_map = {
        "CLOSE_UP": "extreme close-up portrait of",
        "UPPER_BODY": "upper body portrait of",
        "FULL_BODY": "full body wide shot of",
    }
    shot_prefix = shot_desc_map.get(shot_type, "photograph of")

    pose_desc_map = {
        "FRONT": "facing forward towards camera",
        "LEFT_3Q": "turned slightly in three-quarter view to the left",
        "RIGHT_3Q": "turned slightly in three-quarter view to the right",
        "LEFT_PROFILE": "in full left side profile view",
        "RIGHT_PROFILE": "in full right side profile view",
        "LOOKING_DOWN": "looking gently downward with lowered gaze",
        "LOOKING_UP": "looking slightly upward towards light",
        "EXTREME_POSE": "dynamic candid angle",
    }
    pose_desc = pose_desc_map.get(pose_bucket, "natural candid pose")

    flux_prompt = (
        f"{shot_prefix} {trigger}, a young woman, {pose_desc}, "
        f"{attr['expression']}, {attr['clothing']}, {attr['hair']}, "
        f"{attr['bg']}, {attr['lighting']}, high detail, authentic raw skin texture, 8k photo"
    )

    tags = (
        f"{trigger}, 1girl, solo, {shot_type.lower().replace('_', ' ')}, {pose_bucket.lower().replace('_', ' ')}, "
        f"{attr['expression']}, {attr['clothing']}, {attr['hair']}, {attr['bg']}, {attr['lighting']}, photorealistic"
    )

    return flux_prompt, tags


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    config = load_for_cli()
    settings = get_section(config, 'step10_packaging')
    configure_constants(globals(), config, 'step10_packaging', ['CLOTHING_PROMPTS', 'HAIR_PROMPTS', 'EXPRESSION_PROMPTS', 'BACKGROUND_PROMPTS', 'LIGHTING_PROMPTS'])

    # Default paths
    if (project / "work" / "restored").exists():
        default_restored = project / "work" / "restored"
    elif (project / "restored").exists():
        default_restored = project / "restored"
    elif (project / "work" / "selected").exists():
        default_restored = project / "work" / "selected"
    else:
        default_restored = project / "selected"

    if (project / "output" / "reports" / "step7_dataset_report.csv").is_file():
        default_step7 = project / "output" / "reports" / "step7_dataset_report.csv"
    else:
        default_step7 = project / "reports" / "step7_dataset_report.csv"

    if (project / "output" / "reports" / "step9_restoration_report.csv").is_file():
        default_step9 = project / "output" / "reports" / "step9_restoration_report.csv"
    else:
        default_step9 = project / "reports" / "step9_restoration_report.csv"

    default_output_dir = (project / "output" / "dataset_flux"
                          if (project / "output").exists() else project / "dataset_flux")
    default_output_csv = (project / "output" / "reports" / "step10_dataset_report.csv"
                          if (project / "output").exists() else project / "reports" / "step10_dataset_report.csv")

    parser = argparse.ArgumentParser(description="STEP 10: FLUX Dataset Packaging & Anti-Overfitting Captioning")
    parser.add_argument("--restored-dir", type=Path, default=default_restored,
                        help="Input directory containing restored or selected images")
    parser.add_argument("--step7-report", type=Path, default=default_step7,
                        help="Step 7 report CSV")
    parser.add_argument("--step9-report", type=Path, default=default_step9,
                        help="Step 9 report CSV")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir,
                        help="Output directory for final packaged FLUX LoRA dataset")
    parser.add_argument("--output-csv", type=Path, default=default_output_csv,
                        help="Output step 10 audit CSV")
    parser.add_argument("--trigger", type=str, default="character",
                        help="Subject trigger token (default: 'character')")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process only N images for pre-check")
    parser.add_argument("--config", type=Path, help="Alternate YAML config (relative to project root)")
    configure_parser(parser, config, 'step10_packaging', aliases={'trigger': 'trigger_word'}, paths={'restored_dir': 'restored_dir', 'output_dir': 'output_dataset_dir'})
    parser.set_defaults(trigger=get_section(config, "project").get("trigger_word", parser.get_default("trigger")))
    args = parser.parse_args()

    restored_dir = args.restored_dir if args.restored_dir.is_absolute() else (project / args.restored_dir)
    step7_file = args.step7_report if args.step7_report.is_absolute() else (project / args.step7_report)
    step9_file = args.step9_report if args.step9_report.is_absolute() else (project / args.step9_report)
    output_dir = args.output_dir if args.output_dir.is_absolute() else (project / args.output_dir)
    output_csv = args.output_csv if args.output_csv.is_absolute() else (project / args.output_csv)

    if not restored_dir.is_dir():
        print(f"ERROR: Images directory not found: {restored_dir}", file=sys.stderr)
        return 1

    restored_files = sorted([f for f in restored_dir.glob("*.png")] + [f for f in restored_dir.glob("*.jpg")])
    if not restored_files:
        print(f"ERROR: No images found in {restored_dir}", file=sys.stderr)
        return 1

    print(f"Found {len(restored_files)} images to package.")

    # Load Step 7 metadata
    step7_map = {}
    if step7_file.exists():
        with open(step7_file, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                step7_map[Path(r.get("filename", "")).name] = r

    # Load Step 9 metadata
    step9_map = {}
    if step9_file.exists():
        with open(step9_file, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                step9_map[Path(r.get("filename", "")).name] = r

    device_setting = settings.get("device", "auto")
    device = torch.device(("cuda" if torch.cuda.is_available() else "cpu") if device_setting == "auto" else device_setting)
    print(f"Using device: {device}")

    # Load CLIP model
    print("Loading CLIP (openai/clip-vit-large-patch14) for attribute tagging...", flush=True)
    try:
        clip_model = CLIPModel.from_pretrained(settings.get("model_name", "openai/clip-vit-large-patch14"), local_files_only=True)
        clip_processor = CLIPProcessor.from_pretrained(settings.get("model_name", "openai/clip-vit-large-patch14"), local_files_only=True)
    except Exception:
        print("Model cache not found locally; downloading openai/clip-vit-large-patch14 from HuggingFace...")
        clip_model = CLIPModel.from_pretrained(settings.get("model_name", "openai/clip-vit-large-patch14"))
        clip_processor = CLIPProcessor.from_pretrained(settings.get("model_name", "openai/clip-vit-large-patch14"))
    clip_model.to(device)
    clip_model.eval()

    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_records = []
    report_rows = []

    target_files = restored_files[:args.limit] if args.limit > 0 else restored_files
    print(f"Packaging {len(target_files)} images with trigger token '{args.trigger}'...\n")

    for idx, img_path in enumerate(target_files, start=1):
        # Match metadata
        fn_match = None
        for k, v in step7_map.items():
            if k and k in img_path.name:
                fn_match = v
                break

        r_status = "untouched_raw_camera"
        if img_path.name in step9_map:
            r_status = step9_map[img_path.name].get("restoration_status", r_status)

        shot_type = fn_match.get("shot_type", "") if fn_match else ""
        if not shot_type:
            if "CLOSE_UP" in img_path.name:
                shot_type = "CLOSE_UP"
            elif "FULL_BODY" in img_path.name:
                shot_type = "FULL_BODY"
            else:
                shot_type = "UPPER_BODY"

        pose_bucket = fn_match.get("pose_bucket", "") if fn_match else ""
        if not pose_bucket:
            for pb in ("FRONT", "LEFT_3Q", "RIGHT_3Q", "LEFT_PROFILE", "RIGHT_PROFILE", "LOOKING_DOWN", "LOOKING_UP"):
                if pb in img_path.name:
                    pose_bucket = pb
                    break
            if not pose_bucket:
                pose_bucket = "FRONT"

        encoded = np.fromfile(img_path, dtype=np.uint8)
        img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if img is None:
            continue

        orig_h, orig_w = img.shape[:2]
        aligned_img = align_image_16x(img)
        align_h, align_w = aligned_img.shape[:2]

        # Classify attributes via CLIP
        attr = classify_clip_attributes(aligned_img, clip_model, clip_processor, device)
        flux_caption, tags_caption = build_flux_caption(args.trigger, shot_type, pose_bucket, attr)

        # Standardized sequential naming
        final_stem = f"{args.trigger}_{idx:02d}"
        final_img_name = f"{final_stem}.png"
        final_txt_name = f"{final_stem}.txt"

        final_img_path = output_dir / final_img_name
        final_txt_path = output_dir / final_txt_name

        # Save 16x aligned image
        is_success, buf = cv2.imencode(".png", aligned_img)
        if is_success:
            with open(final_img_path, "wb") as f:
                buf.tofile(f)

        # Save paired caption text file
        with open(final_txt_path, "w", encoding="utf-8") as f:
            f.write(flux_caption)

        # JSONL entry
        jsonl_records.append({
            "image": final_img_name,
            "text": flux_caption,
            "tags": tags_caption,
            "width": align_w,
            "height": align_h,
            "shot_type": shot_type,
            "pose": pose_bucket,
            "restoration": r_status,
        })

        report_rows.append({
            "step_name": "STEP10_PACKAGING",
            "final_filename": final_img_name,
            "original_filename": img_path.name,
            "shot_type": shot_type,
            "pose_bucket": pose_bucket,
            "width": str(orig_w),
            "height": str(orig_h),
            "aligned_width": str(align_w),
            "aligned_height": str(align_h),
            "restoration_status": r_status,
            "clothing_desc": attr["clothing"],
            "hair_desc": attr["hair"],
            "expression_desc": attr["expression"],
            "bg_desc": attr["bg"],
            "lighting_desc": attr["lighting"],
            "flux_caption": flux_caption,
            "tags_caption": tags_caption,
        })

        if idx % 10 == 0 or idx == len(target_files):
            print(f"[{idx}/{len(target_files)}] -> {final_img_name} ({align_w}x{align_h})")

    # Save metadata.jsonl
    jsonl_path = output_dir / "metadata.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in jsonl_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Save README_TRAINING_GUIDE.md inside packaged dataset folder
    guide_path = output_dir / "README_TRAINING_GUIDE.md"
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(f"""# FLUX.2 / FLUX.1 Dev LoRA Training Guide: {args.trigger.upper()}

## 1. Dataset Overview
- **Total Images**: {len(target_files)} pristine images
- **Subject Trigger**: `{args.trigger}`
- **Resolution**: Native aspect ratios aligned to multiples of 16 (VAE-compatible)
- **Composition Quota**:
  - CLOSE_UP: High pore detail & facial structure
  - UPPER_BODY: Torso, clothing flexibility & natural gestures
  - FULL_BODY: Full silhouette, legs & distant perspective

## 2. Anti-Overfitting Mechanism
All captions explicitly describe:
1. Clothing (`wearing a ...`)
2. Hairstyle & styling
3. Background environment
4. Lighting & shadows
5. Pose & eye orientation

**Result**: FLUX binds only the subject's unique facial bone structure, eyes, and skin texture to the token `{args.trigger}`.
At inference time, you can freely change clothes, hairstyles, and scenery without dataset bleed.

## 3. Recommended Training Hyperparameters (Kohya / ai-toolkit)
| Parameter | Recommended Value | Note |
| :--- | :--- | :--- |
| **Model** | FLUX.1-dev / FLUX.2-dev | fp8 or bfloat16 base |
| **Network Type** | LoRA (Linear + Attention) | Standard rank |
| **Network Rank (dim)** | 16 or 32 | 16 is optimal for single human face |
| **Network Alpha** | 16 | alpha = rank or rank/2 |
| **Learning Rate** | `1e-4` to `2e-4` | With cosine scheduler |
| **Batch Size** | 1 (or 2 with gradient accum 2) | |
| **Resolution / Buckets** | Max resolution 1024 or 1536 | Enable aspect ratio bucketing |
| **Total Steps** | 1,500 ~ 2,200 steps | ~35 to 50 epochs |
| **Text Encoder LR** | 0.0 (Freeze T5) or `5e-5` (CLIP only) | Keeping T5 frozen prevents style corruption |

## 4. Inference Prompt Templates
- **Standard Portrait**:
  `photo of {args.trigger}, a young woman, upper body portrait, smiling gently, wearing an elegant dress, hotel lobby, cinematic lighting, 8k, photorealistic`
- **Casual Outdoor**:
  `a candid street photograph of {args.trigger}, a young woman, full body shot, walking through a sunny street, casual clothes, natural skin texture`
- **Close-up Beauty**:
  `extreme close-up portrait of {args.trigger}, a young woman, looking directly at the camera, soft studio lighting, highly detailed eyes, natural skin pores, masterpiece`
""")

    actual_csv = write_csv(output_csv, list(STEP10_COLUMNS), report_rows)

    print("\n" + "=" * 60)
    print("STEP 10: FLUX DATASET PACKAGING COMPLETE")
    print("=" * 60)
    print(f"Packaged dataset directory:        {output_dir}")
    print(f"Total image-text pairs:            {len(target_files)}")
    print(f"Metadata JSONL:                    {jsonl_path}")
    print(f"Training Guide:                    {guide_path}")
    print(f"Step 10 Audit CSV:                 {actual_csv}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
