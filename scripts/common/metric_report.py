"""STEP2 provenance, diagnostics and completeness (no quality gates)."""
from __future__ import annotations
from common.step3_review import is_review_copy, require_source

from collections import Counter
import csv
from pathlib import Path

import cv2
import numpy as np

from common.video_manifest import natural_key, write_csv_atomic

DISTRIBUTION_METRICS = ("width", "height", "short_edge", "long_edge", "pixel_count",
                        "mean_brightness", "global_laplacian", "global_tenengrad",
                        "laplacian_score", "tenengrad_score", "brightness_mean", "brightness_std",
                        "shadow_pixel_ratio", "highlight_pixel_ratio", "contrast_p90_p10")


def read_step1_counts(directory: Path) -> dict[str, int]:
    """Never invent or renumber STEP1 IDs. Both formal manifests are required."""
    tables = []
    for name in ("video_manifest.csv", "video_extraction.csv"):
        with (directory / name).open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ids = [row.get("video_id", "") for row in rows]
        if not rows or any(not item or Path(item).name != item or item in (".", "..")
                           or "/" in item or "\\" in item for item in ids):
            raise ValueError(f"{name}: invalid or empty video IDs")
        if len(set(ids)) != len(ids):
            raise ValueError(f"{name}: duplicate video IDs")
        tables.append({row["video_id"]: row for row in rows})
    manifest, extraction = tables
    if set(manifest) != set(extraction):
        raise ValueError("STEP1 manifest and extraction video IDs differ")
    expected = {}
    for video in sorted(manifest, key=lambda value: natural_key(Path(value))):
        record = extraction[video]
        count = int(record["extracted_frame_count"])
        target = int(record["target_frames"])
        if record["extraction_status"] != "PASS" or count <= 0 or count != target:
            raise ValueError(f"STEP1 extraction incomplete: {video}")
        expected[video] = count
    return expected


def image_order(path: Path, source: Path) -> tuple:
    relative = path.relative_to(source)
    return tuple(natural_key(Path(part)) for part in relative.parts)


def measure_images(source: Path, project: Path, columns: list[str], scorer, *, images=None, provenance=None) -> list[dict]:
    images = images if images is not None else sorted((path for path in source.rglob("*")
                     if not is_review_copy(path) and path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}),
                    key=lambda path: image_order(path, source))
    require_source(source)
    if any(is_review_copy(p) for p in images):
        raise ValueError("Review copies cannot be measured as source images")
    rows = []
    previous_video = None
    for index, path in enumerate(images, start=1):
        name = path.relative_to(source).as_posix()
        video = name.split("/", 1)[0] if "/" in name else ""
        if previous_video is not None and previous_video != video:
            print(f"[{index-1}/{len(images)}] measured video {previous_video}", flush=True)
        previous_video = video
        row = {column: "" for column in columns}
        # input-root relative identity remains valid if the whole project is moved.
        row.update(filename=name, video_id=video, frame_id=name, frame_name=path.name,
                   relative_path=path.relative_to(project).as_posix()
                   if path.is_relative_to(project) else name,
                   step_name="STEP2_TECHNICAL_METRICS")
        row.update((provenance or {}).get(name, {}))
        try:
            row.update(scorer(path))
        except (OSError, ValueError, cv2.error) as exc:
            # Persist the relative identity and actionable category, not a machine path.
            category = "DECODE_ERROR" if isinstance(exc, (ValueError, cv2.error)) else "IO_ERROR"
            row.update(status="error", processing_status="FAIL", error=category)
        rows.append(row)
    if previous_video is not None:
        print(f"[{len(images)}/{len(images)}] measured video {previous_video}", flush=True)
    return rows


def distribution(values: list[float]) -> dict:
    if not values:
        return {key: None for key in ("min", "p25", "median", "p75", "max")}
    results = np.percentile(values, [0, 25, 50, 75, 100])
    return {key: round(float(value), 6)
            for key, value in zip(("min", "p25", "median", "p75", "max"), results)}


def build_summary(rows: list[dict], expected: dict[str, int]) -> dict:
    valid = [row for row in rows if row["processing_status"] == "PASS"]
    counts = Counter(row["video_id"] for row in rows)
    failed_counts = Counter(row["video_id"] for row in rows if row["processing_status"] != "PASS")
    per_video = []
    for video in sorted(set(expected) | set(counts), key=lambda value: natural_key(Path(value))):
        wanted = expected.get(video)
        per_video.append({"video_id": video, "expected": wanted, "records": counts[video],
                          "processed": counts[video] - failed_counts[video],
                          "failed": failed_counts[video],
                          "count_match": wanted is not None and counts[video] == wanted})
    unique = len({row["frame_id"] for row in rows}) == len(rows)
    layout_valid = all(row["video_id"] in expected and
                       row["filename"].count("/") == 1 for row in rows)
    count_match = bool(rows) and all(item["count_match"] for item in per_video)
    passed = len(valid) == len(rows) and unique and layout_valid and count_match
    sizes = Counter((row["width"], row["height"]) for row in valid)
    return {
        "step_name": "STEP2_TECHNICAL_METRICS", "status": "PASS" if passed else "FAIL",
        "status_meaning": "measurement and provenance completeness only; no face/LoRA quality judgment",
        "input_records": len(rows), "processed": len(valid), "failed": len(rows) - len(valid),
        "video_directories": len(counts), "expected_videos": len(expected),
        "expected_frames": sum(expected.values()), "frame_ids_unique": unique,
        "step1_count_match": count_match, "step1_layout_match": layout_valid,
        "relative_path_base": "project_root for internal input, input_root for external input",
        "per_video": per_video,
        "distributions": {key: distribution([float(row[key]) for row in valid])
                          for key in DISTRIBUTION_METRICS},
        "statistics_note": "Diagnostic only; linear percentiles of stored (3-decimal metric) values",
        "resolution_buckets_note": "Descriptive short-edge counts; these are not rejection thresholds",
        "resolution_buckets": {
            "short_edge_lt720": sum(row["short_edge"] < 720 for row in valid),
            "short_edge_720_to1079": sum(720 <= row["short_edge"] < 1080 for row in valid),
            "short_edge_ge1080": sum(row["short_edge"] >= 1080 for row in valid)},
        "resolution_counts": [{"width": width, "height": height, "count": count}
                              for (width, height), count in sorted(sizes.items())],
        "errors": [{"frame_id": row["frame_id"], "error": row["error"]}
                   for row in rows if row["processing_status"] != "PASS"],
    }


def write_outliers(path: Path, rows: list[dict]) -> None:
    valid = [row for row in rows if row["processing_status"] == "PASS"]
    selections = []
    for label, key, descending in (
        ("laplacian_top20", "global_laplacian", True),
        ("laplacian_bottom20", "global_laplacian", False),
        ("brightness_darkest20", "mean_brightness", False),
        ("brightness_brightest20", "mean_brightness", True),
        ("smallest_resolution20", "pixel_count", False)):
        ordered = sorted(valid, key=lambda row: (-float(row[key]) if descending else float(row[key]),
                                                row["frame_id"]))
        for rank, row in enumerate(ordered[:20], start=1):
            selections.append(dict(row, diagnostic_group=label, diagnostic_rank=rank))
    write_csv_atomic(path,
                     ["diagnostic_group", "diagnostic_rank", "video_id", "frame_id", "relative_path",
                      "width", "height", "short_edge", "pixel_count", "global_laplacian",
                      "global_tenengrad", "mean_brightness"], selections)


def print_summary(summary: dict) -> None:
    print(f"Measurement: {summary['status']} | processed={summary['processed']} failed={summary['failed']} "
          f"input={summary['input_records']} videos={summary['video_directories']}")
    print(f"STEP1 count match: {summary['step1_count_match']} | Unique frame IDs: {summary['frame_ids_unique']}")
    print("Diagnostic statistics only (min / p25 / median / p75 / max):")
    for key, values in summary["distributions"].items():
        print(f"  {key}: " + " / ".join(str(value) for value in values.values()))
    print("Resolution buckets (no rejection):", summary["resolution_buckets"])
