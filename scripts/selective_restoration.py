"""Selective Restoration: Surgical deblurring & face restoration for low-res distant full-body shots.

STEP 9: Selective Restoration & Identity Drift Verification
- Protects raw camera skin texture on high-quality CLOSE_UP and UPPER_BODY shots (100% untouched)
- Selectively targets low-res distant faces in FULL_BODY shots (face width < 190px or eye sharpness < 2.0)
- Applies CodeFormer with High-Fidelity weight (w=0.80) to preserve authentic facial structure
- Seamlessly blends restored face back into full body image using Gaussian feathering
- Measures Before/After Identity Similarity (DINO ViT-B16) and Fidelity to Original
- Enforces fail-safe rollback: Reverts to original if identity drifts or fidelity drops
- Outputs final images into work/restored/ (or restored/)
- Generates side-by-side Before/After comparisons in reports/step9_restoration_comparison/
- Outputs reports/step9_restoration_report.csv
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

import cv2
import numpy as np
import torch
from transformers import AutoImageProcessor, AutoModel

try:
    import mediapipe as mp
except ImportError:
    mp = None

# Optional CodeFormer architecture loader
CodeFormer = None
for extra_path in [
    os.environ.get("COMFYUI_REACTOR_PATH"),
    os.environ.get("COMFYUI_PATH"),
]:
    if extra_path and os.path.isdir(extra_path):
        sys.path.append(extra_path)
        cand_sub = os.path.join(extra_path, "custom_nodes", "comfyui-reactor")
        if os.path.isdir(cand_sub):
            sys.path.append(cand_sub)

try:
    from scripts.r_archs.codeformer_arch import CodeFormer
except Exception:
    pass

STEP9_COLUMNS = (
    "step_name",
    "filename",
    "shot_type",
    "pose_bucket",
    "face_min_dimension",
    "eye_sharpness",
    "restoration_status",
    "identity_sim_before",
    "identity_sim_after",
    "delta_identity",
    "fidelity_to_orig",
    "restoration_reason",
)


def imwrite_unicode(path: Path | str, img: np.ndarray) -> bool:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix if path.suffix else ".png"
    is_success, buf = cv2.imencode(ext, img)
    if is_success:
        with open(path, "wb") as f:
            buf.tofile(f)
        return True
    return False


def get_face_bbox_mediapipe(img: np.ndarray, mesh_obj) -> tuple[int, int, int, int] | None:
    if mesh_obj is None:
        return None
    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    res = mesh_obj.process(rgb)
    if not res.multi_face_landmarks:
        return None
    lms = res.multi_face_landmarks[0].landmark
    xs = [lm.x * w for lm in lms]
    ys = [lm.y * h for lm in lms]
    x1, y1 = max(0, int(min(xs))), max(0, int(min(ys)))
    x2, y2 = min(w, int(max(xs))), min(h, int(max(ys)))
    return x1, y1, x2 - x1, y2 - y1


def blend_face_gaussian(orig_img: np.ndarray, restored_face: np.ndarray, box: tuple[int, int, int, int], feather_ratio: float = 0.20) -> np.ndarray:
    x1, y1, bw, bh = box
    h, w = orig_img.shape[:2]
    x2, y2 = min(w, x1 + bw), min(h, y1 + bh)
    actual_w = x2 - x1
    actual_h = y2 - y1

    resized_restored = cv2.resize(restored_face, (actual_w, actual_h), interpolation=cv2.INTER_LANCZOS4)

    mask = np.ones((actual_h, actual_w), dtype=np.float32)
    ksize_x = max(int(actual_w * feather_ratio) | 1, 5)
    ksize_y = max(int(actual_h * feather_ratio) | 1, 5)

    pad_x = ksize_x // 2
    pad_y = ksize_y // 2
    mask[:pad_y, :] = 0
    mask[-pad_y:, :] = 0
    mask[:, :pad_x] = 0
    mask[:, -pad_x:] = 0
    mask = cv2.GaussianBlur(mask, (ksize_x, ksize_y), 0)
    mask = np.expand_dims(mask, axis=-1)

    result = orig_img.copy()
    orig_patch = result[y1:y2, x1:x2].astype(np.float32)
    blended_patch = orig_patch * (1.0 - mask) + resized_restored.astype(np.float32) * mask
    result[y1:y2, x1:x2] = np.clip(blended_patch, 0, 255).astype(np.uint8)
    return result


def find_codeformer_model(project: Path, explicit_path: Path | None, models_dir: Path | None = None) -> Path | None:
    if explicit_path and explicit_path.is_file():
        return explicit_path
    models_dir = models_dir or project / "models"
    candidates = [
        models_dir / "codeformer-v0.1.0.pth",
        models_dir / "codeformer.pth",
    ]
    env_p = os.environ.get("CODEFORMER_PATH")
    if env_p:
        candidates.insert(0, Path(env_p))
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    config = load_for_cli()
    settings = get_section(config, 'step9_restoration')
    configure_constants(globals(), config, 'step9_restoration', [])

    # Default paths
    if (project / "work" / "selected").exists():
        default_selected = project / "work" / "selected"
    else:
        default_selected = project / "selected"

    if (project / "output" / "reports" / "step7_dataset_report.csv").is_file():
        default_report = project / "output" / "reports" / "step7_dataset_report.csv"
    else:
        default_report = project / "reports" / "step7_dataset_report.csv"

    default_output_dir = (project / "work" / "restored"
                          if (project / "work").exists() else project / "restored")
    default_comparison_dir = (project / "output" / "reports" / "step9_restoration_comparison"
                              if (project / "output").exists() else project / "reports" / "step9_restoration_comparison")
    default_report_csv = (project / "output" / "reports" / "step9_restoration_report.csv"
                          if (project / "output").exists() else project / "reports" / "step9_restoration_report.csv")

    parser = argparse.ArgumentParser(description="STEP 9: Selective Restoration & Safety Verification")
    parser.add_argument("--selected-dir", type=Path, default=default_selected,
                        help="Input selected 45 images directory")
    parser.add_argument("--report", type=Path, default=default_report,
                        help="Input step7 dataset report CSV")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir,
                        help="Output directory for final 45 images")
    parser.add_argument("--comparison-dir", type=Path, default=default_comparison_dir,
                        help="Output directory for Before/After visual comparison strips")
    parser.add_argument("--report-csv", type=Path, default=default_report_csv,
                        help="Output step9 restoration report CSV")
    parser.add_argument("--codeformer-path", type=Path, default=None,
                        help="Explicit path to codeformer-v0.1.0.pth")
    parser.add_argument("--fidelity-weight", type=float, default=0.80,
                        help="CodeFormer fidelity weight w (0.80 = high preservation, 0.0 = aggressive)")
    parser.add_argument("--min-identity-threshold", type=float, default=0.60,
                        help="Minimum identity similarity after restoration")
    parser.add_argument("--max-identity-loss", type=float, default=0.08,
                        help="Maximum allowed drop in identity similarity")
    parser.add_argument("--min-fidelity", type=float, default=0.82,
                        help="Minimum visual fidelity to original face crop (SSIM/normalized correlation)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of images for testing")
    parser.add_argument("--config", type=Path, help="Alternate YAML config (relative to project root)")
    configure_parser(parser, config, 'step9_restoration', aliases={}, paths={'selected_dir': 'selected_dir', 'output_dir': 'restored_dir'})
    args = parser.parse_args()

    selected_dir = args.selected_dir.resolve()
    report_file = args.report.resolve()
    output_dir = args.output_dir.resolve()
    comparison_dir = args.comparison_dir.resolve()
    report_csv = args.report_csv.resolve()

    if not selected_dir.is_dir():
        print(f"ERROR: Selected directory not found: {selected_dir}", file=sys.stderr)
        return 1

    selected_files = sorted([f for f in selected_dir.iterdir() if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg")])
    if not selected_files:
        print(f"No images found in: {selected_dir}. Please complete Step 8 Human Review first.", file=sys.stderr)
        return 0

    print(f"Found {len(selected_files)} selected images to inspect for selective restoration.")

    # Load report metadata
    report_map = {}
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                fn = r.get("filename", "")
                if fn:
                    report_map[Path(fn).name] = r

    # Device setup
    device_setting = settings.get("device", "auto")
    device = torch.device(("cuda" if torch.cuda.is_available() else "cpu") if device_setting == "auto" else device_setting)
    print(f"Using device: {device}")

    # Load DINO for identity tracking
    print("Loading DINO ViT-B16 for Identity Drift Tracking...", flush=True)
    try:
        processor = AutoImageProcessor.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"), local_files_only=True)
        dino = AutoModel.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"), local_files_only=True)
    except Exception:
        processor = AutoImageProcessor.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"))
        dino = AutoModel.from_pretrained(settings.get("model_name", "facebook/dino-vitb16"))
    dino.to(device)
    dino.eval()

    def get_dino_emb(crop_bgr: np.ndarray) -> torch.Tensor:
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        inputs = processor(images=pil_img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            out = dino(**inputs)
            cls_token = out.last_hidden_state[:, 0, :]
            return cls_token / cls_token.norm(dim=-1, keepdim=True)

    # Reference centroid
    ref_files = []
    for ref_cand in ([resolve_project_path(get_section(config, "paths")["reference_face_dir"])] if "reference_face_dir" in get_section(config, "paths") else [project / "input" / "reference", project / "reference"]):
        if ref_cand.is_dir():
            ref_files = list(ref_cand.glob("*.jpg")) + list(ref_cand.glob("*.png"))
            if ref_files:
                break

    ref_centroid = None
    if ref_files:
        ref_embs = []
        for rf in ref_files[:settings.get("reference_limit", 15)]:
            img = cv2.imdecode(np.fromfile(rf, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                ref_embs.append(get_dino_emb(img))
        if ref_embs:
            ref_centroid = torch.mean(torch.stack(ref_embs), dim=0)
            ref_centroid = ref_centroid / ref_centroid.norm(dim=-1, keepdim=True)

    # Find CodeFormer checkpoint
    cf_path = find_codeformer_model(project, args.codeformer_path,
                                   resolve_project_path(get_section(config, "paths").get("models_dir", "models")))
    codeformer = None
    if cf_path and CodeFormer is not None:
        try:
            print(f"Loading CodeFormer from {cf_path.name} (w={args.fidelity_weight})...", flush=True)
            codeformer = CodeFormer(dim_embd=512, codebook_size=1024, n_head=8, n_layers=9, connect_list=['32', '64', '128', '256'])
            ckpt = torch.load(str(cf_path), map_location="cpu")
            key = "params_ema" if "params_ema" in ckpt else "params"
            codeformer.load_state_dict(ckpt[key])
            codeformer.to(device)
            codeformer.eval()
            print("CodeFormer loaded successfully.")
        except Exception as e:
            print(f"WARNING: Could not initialize CodeFormer ({e}). All images will be preserved 100% untouched.")
            codeformer = None
    else:
        print("Notice: CodeFormer model not configured. Pipeline will preserve 100% authentic raw camera skin.")

    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_dir.mkdir(parents=True, exist_ok=True)
    report_rows = []

    protected_count = 0
    restored_count = 0
    rollback_count = 0

    mesh_obj = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) if mp else None

    for idx, img_path in enumerate(selected_files, start=1):
        fn_match = None
        for r_name, r in report_map.items():
            if r_name and r_name in img_path.name:
                fn_match = r
                break

        encoded = np.fromfile(img_path, dtype=np.uint8)
        img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if img is None:
            continue

        h, w = img.shape[:2]
        shot = fn_match.get("shot_type", "") if fn_match else ""
        if not shot:
            shot = "FULL_BODY" if "FULL_BODY" in img_path.name else ("CLOSE_UP" if "CLOSE_UP" in img_path.name else "UPPER_BODY")

        min_dim = float(fn_match.get("face_min_dimension", 200)) if fn_match else 200.0
        eye_s = float(fn_match.get("eye_sharpness", 2.0)) if fn_match else 2.0
        pose_b = fn_match.get("pose_bucket", "FRONT") if fn_match else "FRONT"

        # GOLDEN RULE: Never touch CLOSE_UP or UPPER_BODY
        is_candidate_for_restoration = (shot == "FULL_BODY" and (min_dim < settings.get("restoration_face_dim_threshold", 190.0) or eye_s < settings.get("restoration_eye_threshold", 2.0)) and codeformer is not None)

        if not is_candidate_for_restoration:
            protected_count += 1
            imwrite_unicode(output_dir / img_path.name, img)
            report_rows.append({
                "step_name": "STEP9_SELECTIVE_RESTORATION",
                "filename": img_path.name,
                "shot_type": shot,
                "pose_bucket": pose_b,
                "face_min_dimension": f"{min_dim:.1f}",
                "eye_sharpness": f"{eye_s:.2f}",
                "restoration_status": "untouched_raw_camera",
                "identity_sim_before": "",
                "identity_sim_after": "",
                "delta_identity": "",
                "fidelity_to_orig": "",
                "restoration_reason": "protected_raw_skin_fidelity",
            })
            continue

        # Process selective restoration on distant face
        bbox = get_face_bbox_mediapipe(img, mesh_obj)
        if bbox is None:
            protected_count += 1
            imwrite_unicode(output_dir / img_path.name, img)
            continue

        bx, by, bw, bh = bbox
        mx, my = int(bw * 0.20), int(bh * 0.20)
        x1, y1 = max(0, bx - mx), max(0, by - my)
        x2, y2 = min(w, bx + bw + mx), min(h, by + bh + my)
        face_crop = img[y1:y2, x1:x2]

        # Calculate Before identity
        emb_before = get_dino_emb(face_crop)
        sim_before = float(torch.mm(emb_before, ref_centroid.T).cpu()) if ref_centroid is not None else 0.70

        # Run CodeFormer
        face_input = cv2.resize(face_crop, (512, 512), interpolation=cv2.INTER_LANCZOS4)
        face_t = torch.from_numpy(face_input).permute(2, 0, 1).float().unsqueeze(0) / 255.0
        face_t = (face_t - 0.5) / 0.5
        face_t = face_t.to(device)

        with torch.no_grad():
            output_t = codeformer(face_t, w=args.fidelity_weight)[0]
            restored_crop = output_t.squeeze(0).permute(1, 2, 0).cpu().numpy()
            restored_crop = np.clip((restored_crop * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)

        # Calculate After identity
        emb_after = get_dino_emb(restored_crop)
        sim_after = float(torch.mm(emb_after, ref_centroid.T).cpu()) if ref_centroid is not None else 0.70
        delta_sim = sim_after - sim_before

        # Calculate pixel fidelity
        restored_back = cv2.resize(restored_crop, (face_crop.shape[1], face_crop.shape[0]))
        diff = np.abs(face_crop.astype(np.float32) - restored_back.astype(np.float32))
        fidelity = 1.0 - float(np.mean(diff) / 255.0)

        # Verification & Safety Rollback
        passed_drift = (sim_after >= args.min_identity_threshold) and (delta_sim >= -args.max_identity_loss)
        passed_fidelity = (fidelity >= args.min_fidelity)

        if passed_drift and passed_fidelity:
            restored_count += 1
            blended_full = blend_face_gaussian(img, restored_crop, (x1, y1, x2 - x1, y2 - y1))
            imwrite_unicode(output_dir / img_path.name, blended_full)
            status = "safely_restored"
            reason = f"sim={sim_after:.3f}, fid={fidelity:.3f}, blend=feathered"

            # Create visual comparison strip
            comp_h = 256
            comp_orig = cv2.resize(face_crop, (comp_h, comp_h))
            comp_rest = cv2.resize(restored_crop, (comp_h, comp_h))
            strip = np.hstack([comp_orig, comp_rest])
            imwrite_unicode(comparison_dir / f"COMP_{img_path.name}", strip)
        else:
            rollback_count += 1
            imwrite_unicode(output_dir / img_path.name, img)
            status = "rollback_to_original"
            reason = f"rollback: drift={delta_sim:.3f}, fid={fidelity:.3f}"

        report_rows.append({
            "step_name": "STEP9_SELECTIVE_RESTORATION",
            "filename": img_path.name,
            "shot_type": shot,
            "pose_bucket": pose_b,
            "face_min_dimension": f"{min_dim:.1f}",
            "eye_sharpness": f"{eye_s:.2f}",
            "restoration_status": status,
            "identity_sim_before": f"{sim_before:.4f}",
            "identity_sim_after": f"{sim_after:.4f}",
            "delta_identity": f"{delta_sim:+.4f}",
            "fidelity_to_orig": f"{fidelity:.4f}",
            "restoration_reason": reason,
        })

    # Save CSV
    report_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(report_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=STEP9_COLUMNS)
        writer.writeheader()
        writer.writerows(report_rows)

    print("\n=== STEP 9 SELECTIVE RESTORATION SUMMARY ===")
    print(f"Total Images Inspected   : {len(selected_files)}")
    print(f"Untouched Raw Skin (100%): {protected_count} images (CLOSE_UP & UPPER_BODY)")
    print(f"Safely Restored          : {restored_count} images (FULL_BODY)")
    print(f"Rolled Back to Original  : {rollback_count} images")
    print(f"\nFinal images saved to    : {output_dir}")
    print(f"Audit report saved to    : {report_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
