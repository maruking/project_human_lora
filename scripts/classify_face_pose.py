"""Classify face pose (Yaw, Pitch, Roll) and prepare clustering metadata for LoRA dataset.

STEP 4: Pose & Orientation Classification + Diversity Clustering Preparation
- Reads step3_dataset_report.csv
- Focuses on eligible frames (or all frames if requested)
- Computes 3D head pose angles via solvePnP on MediaPipe FaceMesh landmarks
- Classifies into pose buckets (FRONT, LEFT_3Q, RIGHT_3Q, LEFT_PROFILE, RIGHT_PROFILE, LOOKING_UP, LOOKING_DOWN, OTHER)
- Generates pose_cluster_key (e.g. UPPER_BODY_FRONT) and scene_group for balanced selection
- Copies categorized images into pose_review/ with descriptive filenames
- Outputs step4_dataset_report.csv
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
from collections import Counter
from pathlib import Path, PurePosixPath

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
    import mediapipe as mp
except ImportError:
    print("Missing dependency: mediapipe (py -3 -m pip install mediapipe==0.10.21)", file=sys.stderr)
    raise SystemExit(2)

if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "face_mesh"):
    print("This script requires MediaPipe with mp.solutions.face_mesh.", file=sys.stderr)
    raise SystemExit(2)

# Pose angle thresholds (degrees)
FRONT_YAW_MAX = 15.0
THREE_QUARTER_YAW_MAX = 42.0
PROFILE_YAW_MIN = 42.0
PITCH_LOOKING_MAX = 20.0
PITCH_LOOKING_MIN = -20.0
EXTREME_PITCH_THRESHOLD = 35.0
EXTREME_ROLL_THRESHOLD = 35.0

POSE_BUCKETS = (
    "FRONT",
    "LEFT_3Q",
    "RIGHT_3Q",
    "LEFT_PROFILE",
    "RIGHT_PROFILE",
    "LOOKING_UP",
    "LOOKING_DOWN",
    "EXTREME_POSE",
)

NEW_COLUMNS = (
    "pose_yaw",
    "pose_pitch",
    "pose_roll",
    "pose_bucket",
    "pose_cluster_key",
    "scene_group",
    "temporal_index",
    "pose_status",
    "pose_error",
)

# Standard 3D facial model points (metric coordinate system)
MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),          # Nose tip (landmark 1)
    (0.0, -330.0, -65.0),     # Chin (landmark 152)
    (-225.0, 170.0, -135.0),  # Left eye left corner (landmark 33)
    (225.0, 170.0, -135.0),   # Right eye right corner (landmark 263)
    (-150.0, -150.0, -125.0), # Left Mouth corner (landmark 61)
    (150.0, -150.0, -125.0),  # Right mouth corner (landmark 291)
], dtype=np.float64)

KEY_LANDMARK_INDICES = [1, 152, 33, 263, 61, 291]


def estimate_head_pose(landmarks: list, width: int, height: int) -> tuple[float, float, float] | None:
    image_points = np.array([
        (landmarks[idx].x * width, landmarks[idx].y * height)
        for idx in KEY_LANDMARK_INDICES
    ], dtype=np.float64)

    focal_length = width
    center = (width / 2.0, height / 2.0)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1],
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    success, rotation_vector, translation_vector = cv2.solvePnP(
        MODEL_POINTS_3D,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )

    if not success:
        return None

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    proj_matrix = np.hstack((rotation_matrix, translation_vector))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)

    pitch = float(euler_angles[0, 0])
    yaw = float(euler_angles[1, 0])
    roll = float(euler_angles[2, 0])

    if pitch > 90.0:
        pitch = 180.0 - pitch
    elif pitch < -90.0:
        pitch = -180.0 - pitch

    return yaw, pitch, roll


def classify_pose_bucket(yaw: float, pitch: float, roll: float) -> str:
    if abs(pitch) > EXTREME_PITCH_THRESHOLD or abs(roll) > EXTREME_ROLL_THRESHOLD:
        return "EXTREME_POSE"

    if pitch > PITCH_LOOKING_MAX:
        return "LOOKING_DOWN"
    elif pitch < PITCH_LOOKING_MIN:
        return "LOOKING_UP"

    abs_yaw = abs(yaw)
    if abs_yaw <= FRONT_YAW_MAX:
        return "FRONT"
    elif abs_yaw <= THREE_QUARTER_YAW_MAX:
        return "RIGHT_3Q" if yaw > 0 else "LEFT_3Q"
    else:
        return "RIGHT_PROFILE" if yaw > 0 else "LEFT_PROFILE"


def parse_scene_info(filename: str) -> tuple[str, int]:
    clean = filename.replace("\\", "/")
    parts = clean.split("/")
    if len(parts) > 1:
        scene = parts[0]
        name = parts[-1]
    else:
        name = clean
        stem = Path(name).stem
        tokens = stem.split("_")
        scene = "_".join(tokens[:2]) if len(tokens) >= 2 else stem

    idx = 0
    stem = Path(name).stem
    tokens = stem.split("_")
    for tok in reversed(tokens):
        if tok.isdigit():
            idx = int(tok)
            break

    return scene, idx


def write_csv_safely(path: Path, columns: list[str], rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=path.parent,
                                         prefix=".step4_report_", suffix=".tmp", delete=False) as f:
            temp = Path(f.name)
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        try:
            os.replace(temp, path)
            return path
        except (PermissionError, OSError):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = path.with_name(f"{path.stem}_{ts}{path.suffix}")
            print(f"Notice: Main report was locked. Saved safely to: {fallback.name}")
            os.replace(temp, fallback)
            return fallback
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def copy_image(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(src, dst)
    except OSError as e:
        print(f"WARNING: Could not copy {src.name} to {dst}: {e}")


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    config = load_for_cli()
    settings = get_section(config, 'step4_pose')
    configure_constants(globals(), config, 'step4_pose', ['FRONT_YAW_MAX', 'THREE_QUARTER_YAW_MAX', 'PROFILE_YAW_MIN', 'PITCH_LOOKING_MAX', 'PITCH_LOOKING_MIN', 'EXTREME_PITCH_THRESHOLD', 'EXTREME_ROLL_THRESHOLD'])

    # Resolve default paths
    if (project / "output" / "reports" / "step3_dataset_report.csv").is_file():
        default_report = project / "output" / "reports" / "step3_dataset_report.csv"
    else:
        default_report = project / "reports" / "step3_dataset_report.csv"

    if (project / "work" / "frames_raw").exists():
        default_images = project / "work" / "frames_raw"
    elif (project / "frames_raw").exists():
        default_images = project / "frames_raw"
    else:
        default_images = project / "work" / "frames_raw"

    default_output = (project / "output" / "reports" / "step4_dataset_report.csv"
                      if (project / "output").exists() else project / "reports" / "step4_dataset_report.csv")
    default_review = (project / "work" / "pose_review"
                      if (project / "work").exists() else project / "pose_review")

    parser = argparse.ArgumentParser(description="STEP 4: Pose & Orientation Classification")
    parser.add_argument("--report", type=Path, default=default_report,
                        help="Path to step3 dataset report CSV")
    parser.add_argument("--images", type=Path, default=default_images,
                        help="Root directory of images")
    parser.add_argument("--output", type=Path, default=default_output,
                        help="Output path for step4 dataset report CSV")
    parser.add_argument("--review", type=Path, default=default_review,
                        help="Directory to save categorized pose review images")
    parser.add_argument("--all-images", action="store_true",
                        help="Process pose for all images instead of only eligible images")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit processing to N images (0 for all)")
    parser.add_argument("--overwrite-review", action="store_true",
                        help="Overwrite images in pose review directory")
    parser.add_argument("--config", type=Path, help="Alternate YAML config (relative to project root)")
    configure_parser(parser, config, 'step4_pose', aliases={}, paths={'images': 'raw_frames_dir', 'review': 'pose_review_dir'})
    args = parser.parse_args()

    report_file = args.report if args.report.is_absolute() else (project / args.report)
    images_dir = args.images if args.images.is_absolute() else (project / args.images)
    output_file = args.output if args.output.is_absolute() else (project / args.output)
    review_dir = args.review if args.review.is_absolute() else (project / args.review)

    if not report_file.exists():
        fallback_candidates = sorted(project.glob("reports/step3_dataset_report*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if fallback_candidates:
            report_file = fallback_candidates[0]
            print(f"Notice: Main report not found, using latest: {report_file.name}")
        else:
            print(f"ERROR: STEP 3 report not found: {report_file}", file=sys.stderr)
            return 1

    if not images_dir.is_dir():
        for cand in [project / "work" / "frames_raw", project / "frames_raw"]:
            if cand.is_dir():
                images_dir = cand
                break
        else:
            print(f"ERROR: Images directory not found: {images_dir}", file=sys.stderr)
            return 1

    print(f"Loading input report: {report_file}")
    with open(report_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)

    print(f"Total rows in report: {len(rows)}")

    # Initialize new columns
    for row in rows:
        row["step_name"] = "STEP4_POSE_CLASSIFICATION"
        for col in NEW_COLUMNS:
            if col not in row:
                row[col] = ""

    # Determine target rows
    if args.all_images:
        target_indices = [i for i, r in enumerate(rows) if r.get("face_detected") == "true"]
    else:
        target_indices = [i for i, r in enumerate(rows) if r.get("face_eligible") == "true"]

    if args.limit > 0:
        target_indices = target_indices[:args.limit]

    print(f"Target images to classify: {len(target_indices)} (eligible_only={not args.all_images})")

    pose_counter: Counter[str] = Counter()
    cluster_counter: Counter[str] = Counter()

    with mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
    ) as mesh:
        for count, idx in enumerate(target_indices, start=1):
            row = rows[idx]
            fn = row.get("filename", "")
            img_path = images_dir / fn
            if not img_path.is_file():
                for alt_root in [project / "work" / "frames_raw", project / "frames_raw", project / "input" / "original-mp4"]:
                    if (alt_root / fn).is_file():
                        img_path = alt_root / fn
                        break

            scene, temp_idx = parse_scene_info(fn)
            row["scene_group"] = scene
            row["temporal_index"] = str(temp_idx)

            if not img_path.is_file():
                row["pose_status"] = "error"
                row["pose_error"] = "image_not_found"
                continue

            try:
                encoded = np.fromfile(img_path, dtype=np.uint8)
                img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                if img is None:
                    row["pose_status"] = "error"
                    row["pose_error"] = "decode_failed"
                    continue

                h, w = img.shape[:2]
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                res = mesh.process(rgb)

                if not res.multi_face_landmarks:
                    row["pose_status"] = "error"
                    row["pose_error"] = "mesh_no_face"
                    row["pose_bucket"] = "NO_FACE"
                    pose_counter["NO_FACE"] += 1
                    continue

                landmarks = res.multi_face_landmarks[0].landmark
                angles = estimate_head_pose(landmarks, w, h)
                if angles is None:
                    row["pose_status"] = "error"
                    row["pose_error"] = "pnp_failed"
                    row["pose_bucket"] = "ESTIMATION_FAILED"
                    pose_counter["ESTIMATION_FAILED"] += 1
                    continue

                yaw, pitch, roll = angles
                bucket = classify_pose_bucket(yaw, pitch, roll)

                row["pose_yaw"] = f"{yaw:.2f}"
                row["pose_pitch"] = f"{pitch:.2f}"
                row["pose_roll"] = f"{roll:.2f}"
                row["pose_bucket"] = bucket
                row["pose_status"] = "ok"

                shot_type = row.get("shot_type") or "UPPER_BODY"
                cluster_key = f"{shot_type}_{bucket}"
                row["pose_cluster_key"] = cluster_key

                pose_counter[bucket] += 1
                cluster_counter[cluster_key] += 1

                # Save copy into pose_review/
                dst_fn = f"{bucket}_{Path(fn).name}"
                dst_path = review_dir / bucket / dst_fn
                if args.overwrite_review or not dst_path.exists():
                    copy_image(img_path, dst_path)

                if count % 50 == 0 or count == len(target_indices):
                    print(f"[{count}/{len(target_indices)}] {fn}: bucket={bucket} (Y={yaw:.1f}, P={pitch:.1f}, R={roll:.1f})")

            except Exception as e:
                row["pose_status"] = "error"
                row["pose_error"] = str(e)

    # Save CSV
    out_cols = columns + [c for c in NEW_COLUMNS if c not in columns]
    saved_csv = write_csv_safely(output_file, out_cols, rows)

    print("\n=== POSE CLASSIFICATION SUMMARY ===")
    print(f"Processed: {len(target_indices)} images")
    print("Pose Buckets:")
    for b in POSE_BUCKETS + ("NO_FACE", "EXTREME_POSE"):
        cnt = pose_counter.get(b, 0)
        if cnt > 0:
            print(f"  {b:15s}: {cnt:4d} ({cnt/len(target_indices)*100:.1f}%)")

    print("\nTop 5 Pose Clusters:")
    for c_key, cnt in cluster_counter.most_common(5):
        print(f"  {c_key:25s}: {cnt:4d}")

    print(f"\nReport saved to : {saved_csv}")
    print(f"Review folder   : {review_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
