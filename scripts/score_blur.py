"""Measure technical image metrics without quality rejection or source modification.

The filename column is relative to the input directory so that identically named
files in different subdirectories remain distinct.
"""

from __future__ import annotations

from common.config import configure_parser, configure_constants, load_for_cli, get_section, resolve_project_path

import argparse
import csv
import os
import tempfile
import shutil
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from common.metric_report import (measure_images, build_summary, write_outliers,
                                  read_step1_counts, print_summary)
from common.video_manifest import write_json_atomic, natural_key, manifest_lock
from common.step2_inputs import preflight_inputs


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SCORE_COLUMNS = [
    "temporal_index", "extraction_policy_version", "sample_fps_requested", "sample_fps_effective",
    "laplacian_percentile_video", "tenengrad_percentile_video", "quality_rank_video",
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
    "video_id", "frame_id", "frame_name", "relative_path",
    "short_edge", "long_edge", "pixel_count", "aspect_ratio",
    "global_laplacian", "global_tenengrad", "mean_brightness", "processing_status",
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
        "short_edge": min(width, height),
        "long_edge": max(width, height),
        "pixel_count": width * height,
        "aspect_ratio": round(width / height, 6),
        "global_laplacian": round(float(laplacian), 3),
        "global_tenengrad": round(float(tenengrad), 3),
        "mean_brightness": round(float(gray.mean()), 3),
        "processing_status": "PASS",
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


def add_relative_ranks(rows: list[dict[str, object]], suffix="") -> None:
    valid = [row for row in rows if row["status"] == "ok"]
    if not valid:
        return

    laplacian_map = percentiles([float(row["laplacian_score"]) for row in valid])
    tenengrad_map = percentiles([float(row["tenengrad_score"]) for row in valid])
    for row in valid:
        lap = laplacian_map[float(row["laplacian_score"])]
        ten = tenengrad_map[float(row["tenengrad_score"])]
        row["laplacian_percentile" + suffix] = lap
        row["tenengrad_percentile" + suffix] = ten
        row["_combined"] = lap + ten

    ordered = sorted(valid, key=lambda row: (-float(row["_combined"]),
                     tuple(natural_key(Path(part)) for part in str(row["filename"]).split("/"))))
    for rank, row in enumerate(ordered, start=1):
        row["quality_rank" + suffix] = rank
        del row["_combined"]


def write_report(path: Path, rows: list[dict[str, object]], *, retain_missing_records: bool = False, columns=None) -> None:
    """Atomic snapshot. Missing historical filenames can never be retained."""
    if retain_missing_records:
        raise ValueError("Historical merging is prohibited; archive old reports separately")
    names = [row['filename'] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate report filenames")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=path.parent,
                                         prefix=".dataset_report_", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            writer = csv.DictWriter(output, fieldnames=columns or SCORE_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            output.flush()
            os.fsync(output.fileno())
        with temporary.open(encoding="utf-8-sig", newline="") as handle:
            written = list(csv.DictReader(handle))
        if [row['filename'] for row in written] != names:
            raise ValueError("Temporary report validation failed")
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
    config = load_for_cli()
    settings = get_section(config, 'step2_blur')
    configure_constants(globals(), config, 'step2_blur', [])
    default_input, default_report = resolve_default_paths(project)

    parser = argparse.ArgumentParser(description="Measure diagnostic image metrics; PASS is computation success, not face quality.")
    parser.add_argument("--input", type=Path, default=default_input, help="Input directory of images (e.g. work/frames_raw)")
    parser.add_argument("--report", type=Path, default=default_report, help="Output CSV report path")
    parser.add_argument("--config", type=Path, help="Alternate YAML config (relative to project root)")
    parser.add_argument("--supplemental-dir", type=Path, default=None, help="Explicit additional still subtree (project-relative); separate from formal STEP1 frames")
    parser.add_argument("--manifest-dir", type=Path, default=default_input.parent / "manifests", help="STEP1 manifests directory")
    parser.add_argument("--summary", type=Path, default=None, help="JSON summary (default: beside CSV)")
    parser.add_argument("--outliers", type=Path, default=None, help="Diagnostic outliers CSV (default: beside CSV)")
    parser.add_argument("--retain-missing-records", action=argparse.BooleanOptionalAction, default=False,
                        help="Deprecated compatibility option; true is prohibited")
    configure_parser(parser, config, 'step2_blur', aliases={},
                     paths={'input': 'raw_frames_dir', 'manifest_dir': 'manifests_dir'})
    args = parser.parse_args()
    source = args.input.resolve()
    report = args.report.resolve()
    if not source.is_dir():
        parser.error(f"Input directory not found: {source}")

    summary_path = args.summary or report.with_name("step2_summary.json")
    outliers_path = args.outliers or report.with_name("step2_diagnostic_outliers.csv")
    supplemental_path = report.with_name('step2_supplemental_report.csv')
    all_images_path = report.with_name('step2_all_images_report.csv')
    destinations = [report.resolve(), summary_path.resolve(), outliers_path.resolve()]
    if args.supplemental_dir is not None:
        destinations += [supplemental_path.resolve(), all_images_path.resolve()]
    if len(set(destinations)) != len(destinations):
        parser.error("CSV, summary and outliers destinations must be distinct")
    if any(path.is_relative_to(source) for path in destinations):
        parser.error("Reports must be outside the input image directory")
    if args.retain_missing_records:
        parser.error("Historical row merging is prohibited")
    try:
        with manifest_lock(args.manifest_dir / '.video_manifest.lock'):
            formal, supplemental_images, supplemental_generation = preflight_inputs(source, args.manifest_dir, args.supplemental_dir)
            expected, images, provenance, generation = formal
            print(f"Input: {source}\nSTEP1 expected frames: {sum(expected.values())}\nCSV: {report}\nJSON: {summary_path}", flush=True)
            print(f'Supplemental stills: {len(supplemental_images)}; total measurement input: {len(images)+len(supplemental_images)}', flush=True)
            rows = measure_images(source, project, SCORE_COLUMNS, score_image,
                                  images=images, provenance=provenance)
            add_relative_ranks(rows)
            groups = defaultdict(list)
            for row in rows:
                groups[row['video_id']].append(row)
            for group in groups.values():
                add_relative_ranks(group, '_video')
            summary = build_summary(rows, expected)
            additional = []
            if supplemental_generation is not None:
                still_rows = measure_images(source, project, SCORE_COLUMNS, score_image, images=supplemental_images)
                for row in still_rows:
                    row.update(video_id='', temporal_index='', extraction_policy_version='',
                               sample_fps_requested='', sample_fps_effective='', input_kind='SUPPLEMENTAL_STILL',
                               image_sha256=supplemental_generation['files'][row['filename']])
                add_relative_ranks(still_rows)
                combined = [dict(row,input_kind='VIDEO_FRAME') for row in rows]+[dict(row) for row in still_rows]
                add_relative_ranks(combined)
                columns = SCORE_COLUMNS+['input_kind','image_sha256']
                additional = [(supplemental_path,still_rows,columns),(all_images_path,combined,columns)]
                supplemental_failed = sum(r['processing_status'] != 'PASS' for r in still_rows)
                summary.update(supplemental_input_generation=supplemental_generation,
                               supplemental_records=len(still_rows), supplemental_failed=supplemental_failed,
                               total_measured_images=len(combined),
                               all_images_csv=str(all_images_path), supplemental_csv=str(supplemental_path),
                               rank_universes='formal CSV: video frames; supplemental CSV: stills; all-images CSV: combined images')
                if supplemental_failed:
                    summary['status'] = 'FAIL'
            summary.update(input_generation=generation, input_frame_count=len(images),
                           processed_count=len(rows), success_count=summary['processed'],
                           error_count=summary['failed'], video_count=len(expected),
                           csv_records=len(rows), historical_records_retained=0,
                           legacy_historical_merge=False,
                           global_blur_flag_count=None,
                           global_blur_flag_note='No STEP2 min_blur_score configured; no threshold invented')
            ranked = sorted((r for r in rows if r['status']=='ok'), key=lambda r:r['quality_rank'])
            summary['technical_highest10'] = [r['filename'] for r in ranked[:10]]
            summary['technical_lowest10'] = [r['filename'] for r in reversed(ranked[-10:])]
            # Revalidate content/inventory before publication, including external mutations.
            final_formal, _, final_supplemental = preflight_inputs(source, args.manifest_dir, args.supplemental_dir)
            if final_formal[3] != generation or final_supplemental != supplemental_generation:
                raise ValueError('Input generation changed during measurement')
            written_paths = publish(report, summary_path.resolve(), outliers_path.resolve(), rows, summary, additional=additional)
            print_summary(summary)
            print(f"Written CSV: {written_paths[0]}\nSummary: {written_paths[1]}\nDiagnostic outliers: {written_paths[2]}")
            for path in written_paths[3:]:
                print(f'Additional image report: {path}')
            return 0 if summary['status'] == 'PASS' else 1
    except (OSError, ValueError, KeyError, csv.Error) as exc:
        print(f"STEP2 FAIL: {exc}", flush=True)
        return 1


def publish(report, summary_path, outliers_path, rows, summary, *, additional=None):
    """Stage and validate every artifact; failures preserve the last successful set.

    A failed measurement set is retained in audit, including every error row.
    Ordinary publication exceptions roll back already replaced artifacts.
    """
    report.parent.mkdir(parents=True, exist_ok=True)
    audit = report.parent / 'step2_run_audit'
    audit.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.step2_stage_', dir=report.parent) as folder:
        staged = [Path(folder)/name for name in ('report.csv','summary.json','outliers.csv')]
        write_report(staged[0], rows)
        write_json_atomic(staged[1], summary)
        write_outliers(staged[2], rows)
        extra_destinations = []
        for index,(destination, extra_rows, columns) in enumerate(additional or []):
            path = Path(folder)/f'additional_{index}.csv'
            write_report(path, extra_rows, columns=columns)
            staged.append(path)
            extra_destinations.append(destination)
        if summary['status'] != 'PASS':
            failed = Path(tempfile.mkdtemp(prefix='failed_',dir=audit))
            for path in staged:
                shutil.copy2(path, failed/path.name)
            print(f'Failed run CSV/JSON/error records: {failed}', flush=True)
            return [failed/path.name for path in staged]
        destinations = [report,summary_path,outliers_path]+extra_destinations
        previous = Path(tempfile.mkdtemp(prefix='previous_',dir=audit))
        existed = []
        for index,dest in enumerate(destinations):
            dest.parent.mkdir(parents=True, exist_ok=True)
            existed.append(dest.exists())
            if dest.exists():
                shutil.copy2(dest, previous/str(index))
        replaced = []
        try:
            for index,(stage,dest) in enumerate(zip(staged,destinations)):
                # Stage beside each destination, so os.replace remains atomic across drives.
                with tempfile.NamedTemporaryFile(dir=dest.parent,delete=False) as handle:
                    temp = Path(handle.name)
                try:
                    shutil.copyfile(stage,temp)
                    os.replace(temp,dest)
                    replaced.append(index)
                finally:
                    temp.unlink(missing_ok=True)
        except OSError:
            for index in reversed(replaced):
                dest = destinations[index]
                if existed[index]:
                    shutil.copyfile(previous/str(index),dest)
                else:
                    dest.unlink(missing_ok=True)
            raise
        return destinations



if __name__ == "__main__":
    raise SystemExit(main())
