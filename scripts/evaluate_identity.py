"""Evaluate identity consistency against High-Identity reference images using DINO ViT-B16.

STEP 6: Identity Evaluation & Dynamic Gate
- Reads step5_dataset_report.csv
- References High-Identity ground-truth images (input/reference or reference/)
- Computes 768-dim normalized face embeddings via DINO ViT-B16 (GPU accelerated if CUDA available)
- Computes cosine similarity to reference centroid and anchor bank
- Applies Dynamic Gate thresholds based on shot_type and head pose (Yaw/Pitch)
- Classifies into PASSED / REVIEW / REJECT_IDENTITY
- Outputs step6_dataset_report.csv
- Copies review images to identity_review/
"""

from __future__ import annotations

from common.config import configure_parser, configure_constants, load_for_cli, get_section, resolve_project_path

import argparse
import csv
import datetime
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path
from PIL import Image

try:
    import cv2
except ImportError:
    print("Missing dependency: opencv-python (py -3 -m pip install opencv-python)", file=sys.stderr)
    raise SystemExit(2)
try:
    import numpy as np
except ImportError:
    print("Missing dependency: numpy (py -3 -m pip install numpy)", file=sys.stderr)
    raise SystemExit(2)
try:
    import torch
except ImportError:
    print("Missing dependency: torch (py -3 -m pip install torch)", file=sys.stderr)
    raise SystemExit(2)
try:
    from transformers import AutoImageProcessor, AutoModel
except ImportError:
    print("Missing dependency: transformers (py -3 -m pip install transformers)", file=sys.stderr)
    raise SystemExit(2)

STEP6_COLUMNS = (
    "step_name",
    "identity_similarity_mean",
    "identity_similarity_max",
    "identity_threshold",
    "identity_passed",
    "identity_rank",
    "identity_error",
)

# Base Dynamic Thresholds by Shot Type & Pose
BASE_THRESHOLDS = {
    "CLOSE_UP": 0.62,
    "UPPER_BODY": 0.58,
    "FULL_BODY": 0.52,
}

POSE_MODIFIERS = {
    "FRONT": 0.00,
    "LOOKING_DOWN": -0.04,
    "LOOKING_UP": -0.04,
    "LEFT_3Q": -0.05,
    "RIGHT_3Q": -0.05,
    "LEFT_PROFILE": -0.10,
    "RIGHT_PROFILE": -0.10,
    "EXTREME_POSE": -0.12,
}


def get_dynamic_threshold(shot_type: str, pose_bucket: str, yaw: float) -> float:
    base = BASE_THRESHOLDS.get(shot_type, 0.58)
    mod = POSE_MODIFIERS.get(pose_bucket, -0.04)
    # Further slight relaxation for high yaw profiles (> 50 deg)
    if abs(yaw) > 50.0:
        mod -= 0.03
    return max(base + mod, 0.45)


def crop_face(img: np.ndarray, row: dict[str, str], margin: float = 0.25) -> np.ndarray:
    h, w = img.shape[:2]
    try:
        x = int(row.get("face_bbox_x", 0))
        y = int(row.get("face_bbox_y", 0))
        bw = int(row.get("face_bbox_width", 0))
        bh = int(row.get("face_bbox_height", 0))
    except (ValueError, TypeError):
        x, y, bw, bh = 0, 0, 0, 0

    if bw > 0 and bh > 0:
        mx = int(bw * margin)
        my = int(bh * margin)
        x1 = max(0, x - mx)
        y1 = max(0, y - my)
        x2 = min(w, x + bw + mx)
        y2 = min(h, y + bh + my)
        crop = img[y1:y2, x1:x2]
        if crop.size > 0:
            return crop

    # Fallback: center-upper crop for portrait framing
    cy, cx = int(h * 0.35), int(w * 0.50)
    rad = int(min(h, w) * 0.35)
    return img[max(0, cy - rad):min(h, cy + rad), max(0, cx - rad):min(w, cx + rad)]


def write_csv_safely(path: Path, columns: list[str], rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp: Path | None = None
    target_path = path
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=path.parent,
                                         prefix=".step6_report_", suffix=".tmp", delete=False) as f:
            temp = Path(f.name)
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        try:
            os.replace(temp, target_path)
            return target_path
        except (PermissionError, OSError):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = path.with_name(f"{path.stem}_{ts}{path.suffix}")
            print(f"Notice: Main report was locked. Saved safely to: {fallback.name}")
            os.replace(temp, fallback)
            return fallback
    finally:
        if temp is not None and temp.exists():
            try:
                temp.unlink()
            except OSError:
                pass
    return target_path


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    config = load_for_cli()
    settings = get_section(config, 'step6_identity')
    configure_constants(globals(), config, 'step6_identity', ['BASE_THRESHOLDS', 'POSE_MODIFIERS'])

    # Resolve default paths
    if (project / "output" / "reports" / "step5_dataset_report.csv").is_file():
        default_report = project / "output" / "reports" / "step5_dataset_report.csv"
    else:
        default_report = project / "reports" / "step5_dataset_report.csv"

    if (project / "work" / "frames_raw").exists():
        default_images = project / "work" / "frames_raw"
    elif (project / "frames_raw").exists():
        default_images = project / "frames_raw"
    else:
        default_images = project / "work" / "frames_raw"

    if (project / "input" / "reference").exists():
        default_ref = project / "input" / "reference"
    else:
        default_ref = project / "reference"

    default_output_csv = (project / "output" / "reports" / "step6_dataset_report.csv"
                          if (project / "output").exists() else project / "reports" / "step6_dataset_report.csv")
    default_review_dir = (project / "work" / "identity_review"
                          if (project / "work").exists() else project / "identity_review")

    parser = argparse.ArgumentParser(description="STEP 6: Identity Evaluation & Dynamic Gate")
    parser.add_argument("--report", type=Path, default=default_report,
                        help="Input step5 dataset report CSV")
    parser.add_argument("--images", type=Path, default=default_images,
                        help="Root directory of images")
    parser.add_argument("--reference-dir", type=Path, default=default_ref,
                        help="Directory of ground truth reference images")
    parser.add_argument("--output-csv", type=Path, default=default_output_csv,
                        help="Output step6 dataset report CSV")
    parser.add_argument("--review-dir", type=Path, default=default_review_dir,
                        help="Directory to save review images by identity status")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "cpu"],
                        help="Inference device: 'cuda', 'cpu', or 'auto' (default: auto)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit processing to N images for pre-check")
    parser.add_argument("--eval-all-eligible", action="store_true",
                        help="Evaluate all eligible images instead of representatives only")
    parser.add_argument("--config", type=Path, help="Alternate YAML config (relative to project root)")
    configure_parser(parser, config, 'step6_identity', aliases={}, paths={'images': 'raw_frames_dir', 'reference_dir': 'reference_face_dir', 'review_dir': 'identity_review_dir'})
    args = parser.parse_args()

    report_file = args.report if args.report.is_absolute() else (project / args.report)
    images_dir = args.images if args.images.is_absolute() else (project / args.images)
    ref_dir = args.reference_dir if args.reference_dir.is_absolute() else (project / args.reference_dir)
    output_csv = args.output_csv if args.output_csv.is_absolute() else (project / args.output_csv)
    review_dir = args.review_dir if args.review_dir.is_absolute() else (project / args.review_dir)

    if not report_file.exists():
        fallback_candidates = sorted(project.glob("reports/step5_dataset_report*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if fallback_candidates:
            report_file = fallback_candidates[0]
            print(f"Notice: Main report not found, using latest: {report_file.name}")
        else:
            print(f"ERROR: Input report not found: {report_file}", file=sys.stderr)
            return 1

    print(f"Loading input report: {report_file}")
    with open(report_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)

    print(f"Total rows in report: {len(rows)}")

    # Initialize new columns
    for row in rows:
        row["step_name"] = "STEP6_IDENTITY_EVALUATION"
        for col in STEP6_COLUMNS:
            if col not in row:
                row[col] = ""

    # Setup device
    if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()):
        device = torch.device("cuda")
        print(f"Using device: CUDA ({torch.cuda.get_device_name(0)})")
    else:
        device = torch.device("cpu")
        print("Using device: CPU")

    # Load DINO ViT-B16 model
    print("Loading DINO ViT-B16 model...", flush=True)
    try:
        processor = AutoImageProcessor.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"), local_files_only=True)
        model = AutoModel.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"), local_files_only=True)
    except Exception:
        print("Model cache not found locally; downloading facebook/dino-vitb16 from HuggingFace...")
        processor = AutoImageProcessor.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"))
        model = AutoModel.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"))

    model.to(device)
    model.eval()

    def get_embedding(img_cv2: np.ndarray) -> torch.Tensor:
        rgb = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        inputs = processor(images=pil_img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
            cls_token = outputs.last_hidden_state[:, 0, :]
            normed = cls_token / cls_token.norm(dim=-1, keepdim=True)
            return normed

    # 1. Build Reference Embedding Bank
    print("Building High-Identity reference representation...", flush=True)
    ref_files = []
    if ref_dir.is_dir():
        ref_files = sorted(list(ref_dir.glob("*.jpg")) + list(ref_dir.glob("*.png")) + list(ref_dir.glob("*.webp")))

    if not ref_files:
        # Fallback check input/reference or reference
        for alt_ref in [project / "input" / "reference", project / "reference"]:
            if alt_ref.is_dir():
                ref_files = sorted(list(alt_ref.glob("*.jpg")) + list(alt_ref.glob("*.png")) + list(alt_ref.glob("*.webp")))
                if ref_files:
                    break

    if not ref_files:
        print(f"ERROR: No reference images found in {ref_dir}. Please place clear ground-truth photos in input/reference/", file=sys.stderr)
        return 1

    print(f"Found {len(ref_files)} reference images in {ref_dir.name}")
    ref_embs = []
    for p in ref_files[:20]:
        encoded = np.fromfile(p, dtype=np.uint8)
        img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if img is None:
            continue
        fn_match = [r for r in rows if Path(r.get("filename", "")).name == p.name]
        row_ref = fn_match[0] if fn_match else {}
        crop = crop_face(img, row_ref)
        emb = get_embedding(crop)
        ref_embs.append(emb)

    if not ref_embs:
        print("ERROR: Failed to extract embeddings from reference images", file=sys.stderr)
        return 1

    ref_tensor = torch.cat(ref_embs, dim=0) # [K, 768]
    ref_centroid = torch.mean(ref_tensor, dim=0, keepdim=True)
    ref_centroid = ref_centroid / ref_centroid.norm(dim=-1, keepdim=True)
    print(f"Reference bank ready with {len(ref_embs)} anchor images.", flush=True)

    # 2. Select target rows to evaluate
    if args.eval_all_eligible:
        target_indices = [i for i, r in enumerate(rows) if r.get("face_eligible") == "true"]
    else:
        target_indices = [i for i, r in enumerate(rows) if r.get("duplicate_status") in ("representative", "unique")]

    if args.limit > 0:
        target_indices = target_indices[:args.limit]

    print(f"Target frames to evaluate: {len(target_indices)} (representatives_only={not args.eval_all_eligible})")

    if review_dir.exists():
        shutil.rmtree(review_dir)
    for cat in ("PASSED", "REVIEW", "REJECT_IDENTITY"):
        (review_dir / cat).mkdir(parents=True, exist_ok=True)

    passed_count = 0
    review_count = 0
    rejected_count = 0
    scores = []

    for count, idx in enumerate(target_indices, start=1):
        row = rows[idx]
        fn = row.get("filename", "")
        img_path = images_dir / fn
        if not img_path.is_file():
            for alt_root in [project / "work" / "frames_raw", project / "frames_raw", project / "input" / "original-mp4"]:
                if (alt_root / fn).is_file():
                    img_path = alt_root / fn
                    break

        if not img_path.is_file():
            row["identity_passed"] = "false"
            row["identity_error"] = "image_not_found"
            continue

        try:
            encoded = np.fromfile(img_path, dtype=np.uint8)
            img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
            if img is None:
                row["identity_passed"] = "false"
                row["identity_error"] = "decode_failed"
                continue

            crop = crop_face(img, row)
            emb = get_embedding(crop)

            # Cosine similarity to centroid and anchor bank
            sim_centroid = float(torch.mm(emb, ref_centroid.T).cpu())
            sim_anchors = torch.mm(emb, ref_tensor.T).cpu()
            sim_max = float(torch.max(sim_anchors))

            shot = row.get("shot_type") or "UNKNOWN"
            pose = row.get("pose_bucket") or "FRONT"
            try:
                yaw = float(row.get("pose_yaw") or 0.0)
            except ValueError:
                yaw = 0.0

            threshold = get_dynamic_threshold(shot, pose, yaw)

            is_passed = sim_centroid >= threshold
            is_review = (not is_passed) and (sim_centroid >= threshold - 0.05)

            row["identity_similarity_mean"] = f"{sim_centroid:.4f}"
            row["identity_similarity_max"] = f"{sim_max:.4f}"
            row["identity_threshold"] = f"{threshold:.4f}"
            row["identity_passed"] = str(is_passed).lower()

            scores.append((idx, sim_centroid))

            if is_passed:
                passed_count += 1
                cat = "PASSED"
            elif is_review:
                review_count += 1
                cat = "REVIEW"
            else:
                rejected_count += 1
                cat = "REJECT_IDENTITY"

            # Copy review image
            safe_name = f"sim{sim_centroid:.3f}_th{threshold:.2f}_{shot}_{pose}_{img_path.name}"
            shutil.copy2(img_path, review_dir / cat / safe_name)

        except Exception as e:
            row["identity_passed"] = "false"
            row["identity_error"] = str(e)
            print(f"WARNING: Identity evaluation failed for {fn}: {e}")

        if count % 25 == 0 or count == len(target_indices):
            print(f"Evaluated [{count}/{len(target_indices)}] images...", flush=True)

    # Compute identity rank among passed
    scores_sorted = sorted([s for s in scores if rows[s[0]]["identity_passed"] == "true"], key=lambda x: x[1], reverse=True)
    for rank, (idx, _) in enumerate(scores_sorted, start=1):
        rows[idx]["identity_rank"] = str(rank)

    # Save CSV
    out_cols = columns + [c for c in STEP6_COLUMNS if c not in columns]
    saved_csv = write_csv_safely(output_csv, out_cols, rows)

    print("\n=== IDENTITY EVALUATION SUMMARY ===")
    print(f"Total evaluated      : {len(target_indices)}")
    print(f"Passed (High-Identity): {passed_count} ({passed_count/max(len(target_indices), 1)*100:.1f}%)")
    print(f"Borderline (Review)  : {review_count} ({review_count/max(len(target_indices), 1)*100:.1f}%)")
    print(f"Rejected             : {rejected_count} ({rejected_count/max(len(target_indices), 1)*100:.1f}%)")
    print(f"\nReport saved to      : {saved_csv}")
    print(f"Review gallery       : {review_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
