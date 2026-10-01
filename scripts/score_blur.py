"""Score image sharpness without modifying source images.

The filename column is relative to the input directory so that identically named
files in different subdirectories remain distinct.
"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SCORE_COLUMNS = [
    "step_name",
    "filename",
    "width",
    "height",
    "laplacian_score",
    "tenengrad_score",
    "brightness_mean",
    "brightness_std",
    "shadow_pixel_ratio",
    "highlight_pixel_ratio",
    "contrast_p90_p10",
    "file_size_bytes",
    "laplacian_percentile",
    "tenengrad_percentile",
    "quality_rank",
    "status",
    "error",
]


def score_image(path: Path) -> dict[str, object]:
    # imdecode/fromfile handles Windows paths containing non-ASCII characters.
    encoded = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("OpenCV could not decode the image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
    dx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    dy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    tenengrad = np.mean(dx * dx + dy * dy)
    height, width = gray.shape
    p10 = float(np.percentile(gray, 10))
    p90 = float(np.percentile(gray, 90))
    shadow_ratio = float(np.mean(gray < 40))
    highlight_ratio = float(np.mean(gray > 235))
    return {
        "step_name": "STEP2_TECHNICAL_METRICS",
        "width": width,
        "height": height,
        "laplacian_score": round(float(laplacian), 3),
        "tenengrad_score": round(float(tenengrad), 3),
        "brightness_mean": round(float(gray.mean()), 3),
        "brightness_std": round(float(gray.std()), 3),
        "shadow_pixel_ratio": round(shadow_ratio, 3),
        "highlight_pixel_ratio": round(highlight_ratio, 3),
        "contrast_p90_p10": round(p90 - p10, 3),
        "file_size_bytes": path.stat().st_size,
        "status": "ok",
    }


def percentiles(values: list[float]) -> dict[float, float]:
    unique = sorted(set(values))
    if len(unique) <= 1:
        return {item: 100.0 for item in unique}
    return {
        item: round(100.0 * index / (len(unique) - 1), 2)
        for index, item in enumerate(unique)
    }


def add_relative_ranks(rows: list[dict[str, object]]) -> None:
    valid = [row for row in rows if row["status"] == "ok"]
    if not valid:
        return

    laplacian_map = percentiles([float(row["laplacian_score"]) for row in valid])
    tenengrad_map = percentiles([float(row["tenengrad_score"]) for row in valid])
    for row in valid:
        lap = laplacian_map[float(row["laplacian_score"])]
        ten = tenengrad_map[float(row["tenengrad_score"])]
        row["laplacian_percentile"] = lap
        row["tenengrad_percentile"] = ten
        row["_combined"] = lap + ten

    ordered = sorted(valid, key=lambda row: float(row["_combined"]), reverse=True)
    for rank, row in enumerate(ordered, start=1):
        row["quality_rank"] = rank
        del row["_combined"]


def write_report(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=path.parent,
                                         prefix=".dataset_report_", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            writer = csv.DictWriter(output, fieldnames=SCORE_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            old_rows = {}
            if path.exists():
                with path.open("r", encoding="utf-8-sig", newline="") as previous:
                    old_rows = {
                        str(old["filename"]): old
                        for old in csv.DictReader(previous)
                        if "filename" in old
                    }
            for row in rows:
                writer.writerow(row)
                old_rows.pop(str(row["filename"]), None)
            for name in sorted(old_rows, key=str.casefold):
                writer.writerow(old_rows[name])
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def resolve_default_paths(project: Path) -> tuple[Path, Path]:
    if (project / "work" / "frames_raw").exists():
        default_input = project / "work" / "frames_raw"
    elif (project / "frames_raw").exists():
        default_input = project / "frames_raw"
    else:
        default_input = project / "work" / "frames_raw"

    if (project / "output" / "reports").exists():
        default_report = project / "output" / "reports" / "step2_dataset_report.csv"
    else:
        default_report = project / "reports" / "step2_dataset_report.csv"

    return default_input, default_report


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    default_input, default_report = resolve_default_paths(project)

    parser = argparse.ArgumentParser(description="Score blur and sharpness of images.")
    parser.add_argument("--input", type=Path, default=default_input, help="Input directory of images (e.g. work/frames_raw)")
    parser.add_argument("--report", type=Path, default=default_report, help="Output CSV report path")
    args = parser.parse_args()
    source = args.input.resolve()
    report = args.report.resolve()
    if not source.is_dir():
        parser.error(f"Input directory not found: {source}")

    images = sorted(
        (path for path in source.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda path: path.relative_to(source).as_posix().casefold(),
    )
    rows: list[dict[str, object]] = []
    for index, path in enumerate(images, start=1):
        name = path.relative_to(source).as_posix()
        print(f"[{index}/{len(images)}] {name}", flush=True)
        row: dict[str, object] = {
            column: "" for column in SCORE_COLUMNS if column != "filename"
        }
        row["filename"] = name
        try:
            row.update(score_image(path))
        except (OSError, ValueError, cv2.error) as exc:
            row.update({"status": "error", "error": str(exc)})
            print(f"WARNING: Failed to read {name}: {exc}", flush=True)
        rows.append(row)

    add_relative_ranks(rows)
    write_report(report, rows)
    success = sum(row["status"] == "ok" for row in rows)
    print(f"Total images: {len(rows)}")
    print(f"Success: {success}")
    print(f"Failed: {len(rows) - success}")
    print(f"CSV: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
