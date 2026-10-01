"""Score LoRA candidates and select balanced dataset using 2D Shot x Pose Quotas.

STEP 7: LoRA Candidate Scoring & Quota Selection
- Reads step6_dataset_report.csv
- Focuses on identity-passed candidates
- Scores each candidate across 4 pillars:
  1. Identity Consistency (35%)
  2. Anatomical Sharpness (25%)
  3. Shot Resolution Utility (20%)
  4. Exposure & Contrast Quality (20%)
  + Rare pose bonus (Profile / 3Q)
- Enforces 2D Quota System (Shot Type x Head Pose Angle)
- Caps maximum images per video scene to maximize diversity
- Outputs step7_dataset_report.csv
- Copies organized candidates into candidates/ (overall and by_shot/by_pose)
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
from collections import Counter, defaultdict
from pathlib import Path

STEP7_COLUMNS = (
    "step_name",
    "lora_candidate_score",
    "candidate_selected",
    "candidate_rank",
    "quota_cell",
    "quota_status",
    "selection_reason",
)

# Quota targets
DEFAULT_TARGET_COUNT = 65

SHOT_MIN = {"CLOSE_UP": 10, "UPPER_BODY": 25, "FULL_BODY": 18}
SHOT_MAX = {"CLOSE_UP": 14, "UPPER_BODY": 35, "FULL_BODY": 25}

POSE_MIN = {
    "FRONT": 15,
    "LEFT_3Q": 12,
    "RIGHT_3Q": 12,
    "LOOKING_DOWN": 6,
    "RIGHT_PROFILE": 3,
    "LEFT_PROFILE": 1,
    "OTHER": 1,
}
POSE_MAX = {
    "FRONT": 22,
    "LEFT_3Q": 20,
    "RIGHT_3Q": 20,
    "LOOKING_DOWN": 12,
    "RIGHT_PROFILE": 3,
    "LEFT_PROFILE": 1,
    "OTHER": 2,
}


def calculate_candidate_score(row: dict[str, str]) -> tuple[float, str]:
    """Calculate multi-criteria LoRA candidate quality score (0 to 100+)."""
    # 1. Identity Consistency (35%)
    sim = float(row.get("identity_similarity_mean") or 0.55)
    id_score = min(max((sim - 0.50) / 0.35, 0.0), 1.0) * 35.0

    # 2. Anatomical Sharpness (25%)
    eye_s = float(row.get("eye_sharpness") or 0.0)
    mouth_s = float(row.get("mouth_sharpness") or 0.0)
    eye_norm = min(eye_s / 4.0, 1.0) * 18.0
    mouth_norm = min(mouth_s / 2.5, 1.0) * 7.0
    sharp_score = eye_norm + mouth_norm

    # 3. Shot Resolution Utility (20%)
    shot = row.get("shot_type") or "UPPER_BODY"
    min_dim = float(row.get("face_min_dimension") or 100.0)
    if shot == "CLOSE_UP":
        res_score = min(min_dim / 280.0, 1.0) * 20.0
    elif shot == "UPPER_BODY":
        res_score = min(min_dim / 180.0, 1.0) * 20.0
    else:  # FULL_BODY
        res_score = min(min_dim / 110.0, 1.0) * 20.0

    # 4. Exposure & Lighting Quality (20%)
    br = float(row.get("face_brightness_mean") or 120.0)
    backlit = float(row.get("face_to_global_brightness_ratio") or 1.0)
    if 115.0 <= br <= 165.0:
        exp_score = 15.0
    elif 95.0 <= br <= 190.0:
        exp_score = 10.0
    else:
        exp_score = 4.0
    if backlit >= 0.90:
        exp_score += 5.0
    elif backlit >= 0.75:
        exp_score += 3.0

    base_score = id_score + sharp_score + res_score + exp_score

    # Bonus: Rare pose preservation
    pose = row.get("pose_bucket") or "FRONT"
    bonus = 0.0
    if "PROFILE" in pose:
        bonus += 10.0
    elif "3Q" in pose:
        bonus += 3.0
    elif pose == "LOOKING_DOWN":
        bonus += 2.0

    total_score = base_score + bonus
    reason = f"ID={id_score:.1f}+Sharp={sharp_score:.1f}+Res={res_score:.1f}+Exp={exp_score:.1f}+Bonus={bonus:.0f}"
    return total_score, reason


def write_csv_safely(path: Path, columns: list[str], rows: list[dict[str, str]]) -> Path:
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


def main() -> int:
    project = Path(__file__).resolve().parent.parent

    # Resolve default paths
    if (project / "output" / "reports" / "step6_dataset_report.csv").is_file():
        default_report = project / "output" / "reports" / "step6_dataset_report.csv"
    else:
        default_report = project / "reports" / "step6_dataset_report.csv"

    if (project / "work" / "frames_raw").exists():
        default_images = project / "work" / "frames_raw"
    elif (project / "frames_raw").exists():
        default_images = project / "frames_raw"
    else:
        default_images = project / "work" / "frames_raw"

    default_output_csv = (project / "output" / "reports" / "step7_dataset_report.csv"
                          if (project / "output").exists() else project / "reports" / "step7_dataset_report.csv")
    default_output_dir = (project / "work" / "candidates"
                          if (project / "work").exists() else project / "candidates")

    parser = argparse.ArgumentParser(description="STEP 7: LoRA Candidate Scoring & Quota Selection")
    parser.add_argument("--report", type=Path, default=default_report,
                        help="Input step6 dataset report CSV")
    parser.add_argument("--images", type=Path, default=default_images,
                        help="Root directory of images")
    parser.add_argument("--output-csv", type=Path, default=default_output_csv,
                        help="Output step7 dataset report CSV")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir,
                        help="Directory to save selected candidates")
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT,
                        help="Target candidate count (default 65)")
    parser.add_argument("--max-scene-burst", type=int, default=8,
                        help="Max images from standard video scenes (default 8)")
    parser.add_argument("--max-reference-burst", type=int, default=15,
                        help="Max images from high-identity reference collection (default 15)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit processing to N candidates for pre-check")
    args = parser.parse_args()

    report_file = args.report if args.report.is_absolute() else (project / args.report)
    images_dir = args.images if args.images.is_absolute() else (project / args.images)
    output_csv = args.output_csv if args.output_csv.is_absolute() else (project / args.output_csv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else (project / args.output_dir)

    if not report_file.exists():
        fallback_candidates = sorted(project.glob("reports/step6_dataset_report*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
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
        row["step_name"] = "STEP7_LORA_CANDIDATE_SELECTION"
        for col in STEP7_COLUMNS:
            if col not in row:
                row[col] = ""

    # Filter candidate pool: must have passed identity evaluation in Step 6
    target_indices = [i for i, r in enumerate(rows) if r.get("identity_passed") == "true"]
    if args.limit > 0:
        target_indices = target_indices[:args.limit]

    print(f"Identity-passed candidates available: {len(target_indices)}")

    # Score all target candidates
    for idx in target_indices:
        r = rows[idx]
        score, reason = calculate_candidate_score(r)
        r["lora_candidate_score"] = f"{score:.2f}"
        r["selection_reason"] = reason
        r["quota_cell"] = f"{r.get('shot_type')}_{r.get('pose_bucket')}"

    def max_for_scene(sc: str) -> int:
        sc_low = sc.lower()
        if "reference" in sc_low or "identity" in sc_low:
            return args.max_reference_burst
        return args.max_scene_burst

    # Sort candidates by score descending
    sorted_candidate_indices = sorted(target_indices, key=lambda i: float(rows[i]["lora_candidate_score"]), reverse=True)

    selected_indices: list[int] = []
    shot_counts: Counter[str] = Counter()
    pose_counts: Counter[str] = Counter()
    scene_counts: Counter[str] = Counter()

    # Phase 1: Guarantee rare poses (PROFILE)
    for idx in sorted_candidate_indices:
        r = rows[idx]
        pose = r.get("pose_bucket") or ""
        if "PROFILE" in pose and idx not in selected_indices:
            selected_indices.append(idx)
            shot_counts[r.get("shot_type", "")] += 1
            pose_counts[pose] += 1
            scene_counts[r.get("scene_group", "")] += 1
            r["quota_status"] = "selected_profile_priority"

    # Phase 2: Satisfy Minimum Quotas for Shot Type and Pose
    for idx in sorted_candidate_indices:
        if idx in selected_indices:
            continue
        r = rows[idx]
        s = r.get("shot_type", "")
        p = r.get("pose_bucket", "")
        sc = r.get("scene_group", "")

        if scene_counts[sc] >= max_for_scene(sc):
            continue

        needs_shot = shot_counts[s] < SHOT_MIN.get(s, 0)
        needs_pose = pose_counts[p] < POSE_MIN.get(p, 0)

        if needs_shot or needs_pose:
            selected_indices.append(idx)
            shot_counts[s] += 1
            pose_counts[p] += 1
            scene_counts[sc] += 1
            r["quota_status"] = "selected_quota_minimum"
            if len(selected_indices) >= args.target_count:
                break

    # Phase 3: Fill up to target_count by score respecting maximum limits
    for idx in sorted_candidate_indices:
        if len(selected_indices) >= args.target_count:
            break
        if idx in selected_indices:
            continue

        r = rows[idx]
        s = r.get("shot_type", "")
        p = r.get("pose_bucket", "")
        sc = r.get("scene_group", "")

        if scene_counts[sc] >= max_for_scene(sc):
            continue
        if shot_counts[s] >= SHOT_MAX.get(s, 999):
            continue
        if pose_counts[p] >= POSE_MAX.get(p, 999):
            continue

        selected_indices.append(idx)
        shot_counts[s] += 1
        pose_counts[p] += 1
        scene_counts[sc] += 1
        r["quota_status"] = "selected_score_fill"

    # Mark selection status
    for idx in target_indices:
        r = rows[idx]
        if idx in selected_indices:
            r["candidate_selected"] = "true"
        else:
            r["candidate_selected"] = "false"
            if not r["quota_status"]:
                r["quota_status"] = "rejected_quota_exceeded"

    # Assign rank among selected
    selected_sorted = sorted(selected_indices, key=lambda i: float(rows[i]["lora_candidate_score"]), reverse=True)
    for rank, idx in enumerate(selected_sorted, start=1):
        rows[idx]["candidate_rank"] = str(rank)

    # Save candidates to output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "all_ranked").mkdir(exist_ok=True)
    (output_dir / "by_shot").mkdir(exist_ok=True)
    (output_dir / "by_pose").mkdir(exist_ok=True)

    copied_count = 0
    for rank, idx in enumerate(selected_sorted, start=1):
        r = rows[idx]
        fn = r.get("filename", "")
        src = images_dir / fn
        if not src.is_file():
            for alt_root in [project / "work" / "frames_raw", project / "frames_raw", project / "input" / "original-mp4"]:
                if (alt_root / fn).is_file():
                    src = alt_root / fn
                    break

        if not src.is_file():
            print(f"WARNING: Image not found for copy: {src}")
            continue

        score_val = float(r["lora_candidate_score"])
        shot = r.get("shot_type", "SHOT")
        pose = r.get("pose_bucket", "POSE")
        clean_name = f"{rank:02d}_score{score_val:05.1f}_{shot}_{pose}_{src.name}"

        # 1. all_ranked
        shutil.copy2(src, output_dir / "all_ranked" / clean_name)

        # 2. by_shot
        shot_sub = output_dir / "by_shot" / shot
        shot_sub.mkdir(exist_ok=True)
        shutil.copy2(src, shot_sub / clean_name)

        # 3. by_pose
        pose_sub = output_dir / "by_pose" / pose
        pose_sub.mkdir(exist_ok=True)
        shutil.copy2(src, pose_sub / clean_name)

        copied_count += 1

    # Save CSV
    out_cols = columns + [c for c in STEP7_COLUMNS if c not in columns]
    saved_csv = write_csv_safely(output_csv, out_cols, rows)

    print("\n=== STEP 7 QUOTA SELECTION SUMMARY ===")
    print(f"Total Selected Candidates : {len(selected_indices)} / {len(target_indices)} (Target: {args.target_count})")
    print(f"Images Copied to Review   : {copied_count}")
    print("\nShot Type Quota Distribution:")
    for s, count in shot_counts.items():
        min_v = SHOT_MIN.get(s, 0)
        max_v = SHOT_MAX.get(s, 0)
        pct = (count / len(selected_indices) * 100) if selected_indices else 0.0
        print(f"  {s:15s}: {count:2d} ({pct:5.1f}%) [Target Range: {min_v}~{max_v}]")

    print("\nPose Quota Distribution:")
    for p, count in pose_counts.items():
        min_v = POSE_MIN.get(p, 0)
        max_v = POSE_MAX.get(p, 0)
        pct = (count / len(selected_indices) * 100) if selected_indices else 0.0
        print(f"  {p:15s}: {count:2d} ({pct:5.1f}%) [Target Range: {min_v}~{max_v}]")

    print(f"\nUnique Video Scenes Selected: {len(scene_counts)}")
    print(f"Report saved to             : {saved_csv}")
    print(f"Candidates folder           : {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
