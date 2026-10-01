"""Face-Centric Deduplication using eye-sharpness (Tenengrad) and pose-aware burst clustering.

STEP 5: Face-Centric Deduplication & Representative Selection
- Reads step4_dataset_report.csv
- Targets eligible frames
- Detects video bursts and scene duplicate frames using temporal distance, pose angle proximity, and face/global pHash
- Selects the single best representative per cluster prioritizing:
  1. Biological eye presence (eye_presence_valid)
  2. Anatomical eye sharpness (eye_sharpness / Tenengrad)
  3. Core face resolution and sharpness (face_laplacian_score, mouth_sharpness)
  4. Optimal exposure (face_brightness_mean)
- Marks duplicates as 'duplicate' and winners as 'representative' / 'unique'
- Outputs step5_dataset_report.csv
- Copies representative frames to frames_deduplicated/
- Outputs cluster comparison reviews to reports/step5_duplicates_review/
"""

from __future__ import annotations

import argparse
import csv
import datetime
import math
import os
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

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

STEP5_COLUMNS = (
    "step_name",
    "duplicate_group",
    "group_size",
    "group_best",
    "duplicate_status",
    "face_quality_score",
    "phash_distance_to_group_best",
    "angle_distance_to_group_best",
    "duplicate_error",
)


def compute_phash(img: np.ndarray) -> int:
    """Compute 64-bit DCT perceptual hash."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    dct = cv2.dct(np.float32(resized))[:8, :8]
    med = float(np.median(dct[1:, :]))
    hash_val = 0
    for r in range(8):
        for c in range(8):
            if dct[r, c] > med:
                hash_val |= (1 << (r * 8 + c))
    return hash_val


def hamming_dist(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


def calculate_face_quality_score(row: dict[str, str]) -> float:
    score = 0.0

    # 1. Biological eye presence
    if row.get("eye_presence_valid") == "true":
        score += 1000.0

    # 2. Anatomical eye sharpness (Tenengrad)
    try:
        eye_s = float(row.get("eye_sharpness", 0.0))
        score += min(eye_s, 10.0) * 100.0
    except (ValueError, TypeError):
        pass

    # 3. Core face Laplacian
    try:
        lap = float(row.get("face_laplacian_score", 0.0))
        score += min(lap, 300.0) * 0.5
    except (ValueError, TypeError):
        pass

    # 4. Mouth sharpness
    try:
        mouth_s = float(row.get("mouth_sharpness", 0.0))
        score += min(mouth_s, 5.0) * 20.0
    except (ValueError, TypeError):
        pass

    # 5. Optimal face exposure bonus (115 ~ 155 is ideal studio lighting)
    try:
        br = float(row.get("face_brightness_mean", 0.0))
        if 110.0 <= br <= 160.0:
            score += 20.0
        elif br < 95.0 or br > 210.0:
            score -= 30.0
    except (ValueError, TypeError):
        pass

    return score


def write_csv_safely(path: Path, columns: list[str], rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp: Path | None = None
    target_path = path
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=path.parent,
                                         prefix=".step5_report_", suffix=".tmp", delete=False) as f:
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

    # Resolve default paths
    if (project / "output" / "reports" / "step4_dataset_report.csv").is_file():
        default_report = project / "output" / "reports" / "step4_dataset_report.csv"
    else:
        default_report = project / "reports" / "step4_dataset_report.csv"

    if (project / "work" / "frames_raw").exists():
        default_images = project / "work" / "frames_raw"
    elif (project / "frames_raw").exists():
        default_images = project / "frames_raw"
    else:
        default_images = project / "work" / "frames_raw"

    default_output_csv = (project / "output" / "reports" / "step5_dataset_report.csv"
                          if (project / "output").exists() else project / "reports" / "step5_dataset_report.csv")
    default_output_dir = (project / "work" / "frames_deduplicated"
                          if (project / "work").exists() else project / "frames_deduplicated")
    default_review_dir = (project / "output" / "reports" / "step5_duplicates_review"
                          if (project / "output").exists() else project / "reports" / "step5_duplicates_review")

    parser = argparse.ArgumentParser(description="STEP 5: Face-Centric Deduplication")
    parser.add_argument("--report", type=Path, default=default_report,
                        help="Input step4 dataset report CSV")
    parser.add_argument("--images", type=Path, default=default_images,
                        help="Images root directory")
    parser.add_argument("--output-csv", type=Path, default=default_output_csv,
                        help="Output step5 dataset report CSV")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir,
                        help="Directory to save representative frames")
    parser.add_argument("--review-dir", type=Path, default=default_review_dir,
                        help="Directory to save duplicate cluster review images")
    parser.add_argument("--phash-threshold", type=int, default=10,
                        help="Hamming distance threshold for pHash (default 10)")
    parser.add_argument("--angle-threshold", type=float, default=12.0,
                        help="Head pose Euclidean angle difference threshold (default 12.0 deg)")
    parser.add_argument("--time-window", type=int, default=6,
                        help="Frame index distance window within scene (default 6)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit processing to N eligible images for pre-check")
    args = parser.parse_args()

    report_file = args.report if args.report.is_absolute() else (project / args.report)
    images_dir = args.images if args.images.is_absolute() else (project / args.images)
    output_csv = args.output_csv if args.output_csv.is_absolute() else (project / args.output_csv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else (project / args.output_dir)
    review_dir = args.review_dir if args.review_dir.is_absolute() else (project / args.review_dir)

    if not report_file.exists():
        fallback_candidates = sorted(project.glob("reports/step4_dataset_report*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if fallback_candidates:
            report_file = fallback_candidates[0]
            print(f"Notice: Main report not found, using latest: {report_file.name}")
        else:
            print(f"ERROR: Input report not found: {report_file}", file=sys.stderr)
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
        row["step_name"] = "STEP5_FACE_DEDUPLICATION"
        for col in STEP5_COLUMNS:
            if col not in row:
                row[col] = ""

    # Filter target eligible rows
    target_indices = [i for i, r in enumerate(rows) if r.get("face_eligible") == "true"]
    if args.limit > 0:
        target_indices = target_indices[:args.limit]

    print(f"Eligible candidate images for deduplication: {len(target_indices)}")

    # Compute pHash and load images for eligible rows
    global_hashes: dict[int, int] = {}
    face_hashes: dict[int, int] = {}
    image_paths: dict[int, Path] = {}

    print("Computing perceptual hashes for eligible images...", flush=True)
    for count, idx in enumerate(target_indices, start=1):
        row = rows[idx]
        fn = row.get("filename", "")
        img_path = images_dir / fn
        if not img_path.is_file():
            for alt_root in [project / "work" / "frames_raw", project / "frames_raw", project / "input" / "original-mp4"]:
                if (alt_root / fn).is_file():
                    img_path = alt_root / fn
                    break

        image_paths[idx] = img_path

        if not img_path.is_file():
            row["duplicate_status"] = "error"
            row["duplicate_error"] = "image_not_found"
            continue

        try:
            encoded = np.fromfile(img_path, dtype=np.uint8)
            img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
            if img is None:
                row["duplicate_status"] = "error"
                row["duplicate_error"] = "decode_failed"
                continue

            gh = compute_phash(img)
            global_hashes[idx] = gh

            # Face crop pHash
            if row.get("face_bbox_x"):
                x = int(row["face_bbox_x"])
                y = int(row["face_bbox_y"])
                bw = int(row["face_bbox_width"])
                bh = int(row["face_bbox_height"])
                h, w = img.shape[:2]
                crop = img[max(0, y):min(h, y + bh), max(0, x):min(w, x + bw)]
                if crop.size > 0:
                    fh = compute_phash(crop)
                    face_hashes[idx] = fh
                else:
                    face_hashes[idx] = gh
            else:
                face_hashes[idx] = gh

            row["face_quality_score"] = f"{calculate_face_quality_score(row):.1f}"

        except Exception as e:
            row["duplicate_status"] = "error"
            row["duplicate_error"] = str(e)
            print(f"WARNING: Hash failed for {fn}: {e}")

        if count % 50 == 0 or count == len(target_indices):
            print(f"Hashed [{count}/{len(target_indices)}] images...", flush=True)

    # Cluster within the same scene
    valid_indices = [idx for idx in target_indices if idx in global_hashes]
    uf = UnionFind(len(rows))

    by_scene = defaultdict(list)
    for idx in valid_indices:
        by_scene[rows[idx].get("scene_group", "root")].append(idx)

    print("Analyzing scene burst duplicates...", flush=True)
    for scene, s_indices in by_scene.items():
        for i_pos in range(len(s_indices)):
            idx_a = s_indices[i_pos]
            row_a = rows[idx_a]
            for j_pos in range(i_pos + 1, len(s_indices)):
                idx_b = s_indices[j_pos]
                row_b = rows[idx_b]

                # Shot type must match to consider them duplicates
                if row_a.get("shot_type") != row_b.get("shot_type"):
                    continue

                # Temporal frame distance
                try:
                    dt = abs(int(row_a.get("temporal_index", 0)) - int(row_b.get("temporal_index", 0)))
                except ValueError:
                    dt = 999

                # 3D pose angle difference (Euclidean distance on yaw and pitch)
                try:
                    dy = float(row_a["pose_yaw"]) - float(row_b["pose_yaw"])
                    dp = float(row_a["pose_pitch"]) - float(row_b["pose_pitch"])
                    angle_dist = math.hypot(dy, dp)
                except (ValueError, KeyError):
                    angle_dist = 999.0

                h_glob = hamming_dist(global_hashes[idx_a], global_hashes[idx_b])
                h_face = hamming_dist(face_hashes[idx_a], face_hashes[idx_b])

                # Condition 1: Close temporal sequence in same video + similar angle + matching pHash
                is_duplicate = False
                if angle_dist <= args.angle_threshold and dt <= args.time_window and (h_glob <= 14 or h_face <= 14):
                    is_duplicate = True
                # Condition 2: Very close angle + very close pHash
                elif angle_dist <= 8.0 and (h_glob <= args.phash_threshold or h_face <= args.phash_threshold):
                    is_duplicate = True

                if is_duplicate:
                    uf.union(idx_a, idx_b)

    # Group into clusters
    clusters = defaultdict(list)
    for idx in valid_indices:
        root_parent = uf.find(idx)
        clusters[root_parent].append(idx)

    print(f"Total clusters identified: {len(clusters)} from {len(valid_indices)} images")

    unique_count = 0
    duplicate_count = 0
    output_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)

    for cluster_id, member_indices in enumerate(clusters.values(), start=1):
        # Best representative within cluster
        best_idx = max(member_indices, key=lambda i: float(rows[i].get("face_quality_score") or 0.0))
        best_row = rows[best_idx]
        best_fn = best_row.get("filename", "")
        best_h_glob = global_hashes[best_idx]
        try:
            best_y = float(best_row.get("pose_yaw") or 0.0)
            best_p = float(best_row.get("pose_pitch") or 0.0)
        except ValueError:
            best_y, best_p = 0.0, 0.0

        group_label = f"cluster_{cluster_id:04d}_{best_row.get('scene_group', 'scene')}"

        for idx in member_indices:
            row = rows[idx]
            row["duplicate_group"] = group_label
            row["group_size"] = str(len(member_indices))
            row["group_best"] = best_fn

            h_dist = hamming_dist(global_hashes[idx], best_h_glob)
            row["phash_distance_to_group_best"] = str(h_dist)

            try:
                cur_y = float(row.get("pose_yaw") or 0.0)
                cur_p = float(row.get("pose_pitch") or 0.0)
                a_dist = math.hypot(cur_y - best_y, cur_p - best_p)
                row["angle_distance_to_group_best"] = f"{a_dist:.2f}"
            except ValueError:
                row["angle_distance_to_group_best"] = ""

            if idx == best_idx:
                row["duplicate_status"] = "unique" if len(member_indices) == 1 else "representative"
                unique_count += 1
                # Copy representative image to output_dir
                src_path = image_paths[idx]
                if src_path.exists():
                    dst_name = f"{row.get('shot_type', 'SHOT')}_{row.get('pose_bucket', 'POSE')}_{Path(best_fn).name}"
                    shutil.copy2(src_path, output_dir / dst_name)
            else:
                row["duplicate_status"] = "duplicate"
                duplicate_count += 1

        # Save cluster visual review if size > 1
        if len(member_indices) > 1:
            c_dir = review_dir / group_label
            c_dir.mkdir(parents=True, exist_ok=True)
            for m_idx in member_indices:
                m_row = rows[m_idx]
                m_src = image_paths[m_idx]
                if m_src.exists():
                    prefix = "WINNER_" if m_idx == best_idx else "DUP_"
                    qs = m_row.get("face_quality_score", "0")
                    es = m_row.get("eye_sharpness", "0")
                    dst_f = f"{prefix}q{qs}_eye{es}_{Path(m_row.get('filename', '')).name}"
                    shutil.copy2(m_src, c_dir / dst_f)

    # Save CSV
    out_cols = columns + [c for c in STEP5_COLUMNS if c not in columns]
    saved_csv = write_csv_safely(output_csv, out_cols, rows)

    print("\n=== FACE-CENTRIC DEDUPLICATION SUMMARY ===")
    print(f"Total eligible images : {len(valid_indices)}")
    print(f"Unique / Rep. retained: {unique_count}")
    print(f"Duplicates pruned     : {duplicate_count}")
    print(f"Prune ratio           : {duplicate_count / max(len(valid_indices), 1) * 100:.1f}%")
    print(f"\nReport saved to       : {saved_csv}")
    print(f"Deduplicated images   : {output_dir}")
    print(f"Review folder         : {review_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
