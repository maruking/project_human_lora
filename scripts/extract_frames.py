"""STEP 1: Stable video copies/manifest and per-video FFmpeg frame extraction.

Duration-aware sampling defaults to 2 FPS, capped at 120 across the full video.
Requires FFmpeg/ffprobe; policy metadata controls safe reuse and preservation.
Original downloads remain intact; video IDs and source names are durably mapped.
"""

from __future__ import annotations

from common.config import configure_parser, configure_constants, load_for_cli, get_section, resolve_project_path
from common.video_manifest import (MANIFEST_FIELDS, NormalizationError, ManifestLocked, manifest_lock,
                                   materialize_copy, plan_normalization, read_manifest,
                                   scan_videos, write_csv_atomic, write_json_atomic)

import argparse
import json
import math
import statistics

from common.frame_sampling import sampling_plan, policy_signature, generate_video, ExtractionFailure
import os
import shutil
import subprocess
import sys
from pathlib import Path

def get_known_ffmpeg_dirs() -> list[Path]:
    dirs = []
    env_dir = os.environ.get("FFMPEG_DIR")
    if env_dir:
        dirs.append(Path(env_dir))
    # Common default locations
    dirs.extend([
        Path(r"C:\ffmpeg\bin"),
        Path(r"C:\Program Files\ffmpeg\bin"),
    ])
    return [d for d in dirs if d.exists()]


def find_binary(name: str, explicit_path: Path | None = None) -> Path | None:
    if explicit_path and explicit_path.is_file():
        return explicit_path
    which_path = shutil.which(name)
    if which_path:
        return Path(which_path)
    ext = ".exe" if sys.platform == "win32" else ""
    target = f"{name}{ext}"
    for directory in get_known_ffmpeg_dirs():
        cand = directory / target
        if cand.is_file():
            return cand
    return None


def get_video_duration(video_path: Path, ffprobe_bin: Path | None) -> float:
    if not ffprobe_bin:
        raise ValueError("ffprobe is required for duration inspection")
    result = subprocess.run([str(ffprobe_bin), "-v", "error", "-show_entries",
                             "format=duration", "-of", "json", str(video_path)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise ValueError(f"ffprobe return_code={result.returncode}: {result.stderr[-1000:]}")
    try:
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("ffprobe returned no valid duration") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("ffprobe returned nonpositive/nonfinite duration")
    return duration


def resolve_default_paths(project: Path) -> tuple[Path, Path, Path]:
    # Input
    if (project / "input" / "original-mp4").exists():
        default_input = project / "input" / "original-mp4"
    elif (project / "original-mp4").exists():
        default_input = project / "original-mp4"
    else:
        default_input = project / "input" / "original-mp4"

    # Output frames
    if (project / "work" / "frames_raw").exists():
        default_output = project / "work" / "frames_raw"
    elif (project / "frames_raw").exists():
        default_output = project / "frames_raw"
    else:
        default_output = project / "work" / "frames_raw"

    # Reports
    if (project / "output" / "reports").exists():
        default_reports = project / "output" / "reports"
    else:
        default_reports = project / "reports"

    return default_input, default_output, default_reports


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    config = load_for_cli()
    settings = get_section(config, 'step1_extract')
    configure_constants(globals(), config, 'step1_extract', [])
    default_input, default_output, default_reports = resolve_default_paths(project)
    default_normalized = project / "work/videos"
    default_manifests = project / "work/manifests"

    parser = argparse.ArgumentParser(description="Duration-aware FFmpeg sampling with verified policy cache.")
    parser.add_argument("--input", type=Path, default=default_input, help="Input directory containing MP4 videos")
    parser.add_argument("--output", type=Path, default=default_output, help="Output directory for raw frames")
    parser.add_argument("--sample-fps", type=float, default=2.0, help="Requested temporal sampling FPS")
    parser.add_argument("--max-frames-per-video", type=int, default=120, help="Per-video limit, spread over full duration")
    parser.add_argument("--policy-version", type=int, default=2, help="Supported extraction policy version: 2")
    parser.add_argument("--trim-start", type=float, default=0.0, help="Optional start trim (default: full duration)")
    parser.add_argument("--trim-end", type=float, default=0.0, help="Optional end trim (default: full duration)")
    parser.add_argument("--subfolders", action="store_true", default=True, help="Store in <output>/<video_stem>/ subfolders")
    parser.add_argument("--flat", dest="subfolders", action="store_false", help="Store all frames directly in <output>/")
    parser.add_argument("--ffmpeg", type=Path, default=None, help="Explicit path to ffmpeg executable")
    parser.add_argument("--ffprobe", type=Path, default=None, help="Explicit path to ffprobe executable")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing extracted frames")
    parser.add_argument("--subject-name", default=get_section(config, "project").get("subject_name", "subject"),
                        help="Video ID prefix (default from project.subject_name)")
    parser.add_argument("--normalized-dir", type=Path, default=default_normalized,
                        help="Standalone normalized video copies; original videos are retained")
    parser.add_argument("--manifest-dir", type=Path, default=default_manifests,
                        help="Persistent video manifest and Step1 summary directory")
    parser.add_argument("--dry-run", action="store_true", help="Read-only naming/collision/directory plan")
    parser.add_argument("--normalize-only", action="store_true", help="Create copies/manifest/folders without extraction")
    parser.add_argument("--config", type=Path, help="Alternate YAML config (relative to project root)")
    configure_parser(parser, config, 'step1_extract', aliases={}, paths={'input': 'input_video_dir', 'output': 'raw_frames_dir', 'normalized_dir': 'normalized_video_dir', 'manifest_dir': 'manifests_dir'})
    configure_parser(parser, config, 'frame_extraction')
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_dir = args.output.resolve()

    if not input_dir.is_dir():
        print(f"ERROR: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1
    if not args.subfolders:
        parser.error("STEP1 requires per-video folders; --flat/subfolders=false is incompatible with video IDs")
    if args.policy_version != 2:
        parser.error("Only duration-aware policy_version=2 is supported")
    if not math.isfinite(args.sample_fps) or args.sample_fps <= 0 or args.max_frames_per_video < 1:
        parser.error("sample_fps and max_frames_per_video must be positive")
    if not all(math.isfinite(value) and value >= 0 for value in (args.trim_start, args.trim_end)):
        parser.error("Trim seconds must be finite and nonnegative")

    ffmpeg_bin = find_binary("ffmpeg", args.ffmpeg)
    ffprobe_bin = find_binary("ffprobe", args.ffprobe)

    if not args.normalize_only and (not ffmpeg_bin or not ffprobe_bin):
        parser.error("FFmpeg and ffprobe are required; no fixed-count/OpenCV duration fallback")
    print(f"Using FFmpeg : {ffmpeg_bin}")

    extensions = set(settings.get("supported_extensions", [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]))
    video_files, skipped_files = scan_videos(input_dir, extensions)

    print(f"Found {len(video_files)} video(s) in {input_dir.name}")
    print(f"Sampling: {args.sample_fps} FPS; max={args.max_frames_per_video}; policy={args.policy_version}")
    print(f"Trim start / end        : {args.trim_start:.2f}s / {args.trim_end:.2f}s")
    print(f"Output directory        : {output_dir}\n")

    normalized_dir = args.normalized_dir.resolve()
    manifest_dir = args.manifest_dir.resolve()
    report_dir = resolve_project_path(get_section(config, "paths").get("reports_dir", default_reports))
    print(f"Normalized working videos: {normalized_dir}")
    print(f"Video manifest          : {manifest_dir / 'video_manifest.csv'}")
    for name in skipped_files:
        print(f"SKIP unsupported extension: {name}")
    try:
        if args.dry_run:
            rows = plan_normalization(video_files, read_manifest(manifest_dir / 'video_manifest.csv'),
                                      args.subject_name, normalized_dir, output_dir)
            print_plan(rows)
            print(f"DRY RUN: {len(video_files)} supported videos; no files/directories changed.")
            return 0
        with manifest_lock(manifest_dir / '.video_manifest.lock'):
            rows = plan_normalization(video_files, read_manifest(manifest_dir / 'video_manifest.csv'),
                                      args.subject_name, normalized_dir, output_dir)
            print_plan(rows)
            # Durable intent precedes all copy operations. IDs survive interruptions.
            write_csv_atomic(manifest_dir / 'video_manifest.csv', MANIFEST_FIELDS, rows)
            return process_videos(rows, args, ffmpeg_bin, ffprobe_bin, report_dir, skipped_files,
                                  len(video_files))
    except (NormalizationError, OSError) as exc:
        print(f"ERROR: STEP1 organization failed: {exc}", file=sys.stderr)
        if not args.dry_run and not isinstance(exc, ManifestLocked):
            write_json_atomic(manifest_dir / 'step1_summary.json', {
                'subject_name': args.subject_name, 'total_videos': len(video_files),
                'status': 'FAIL', 'failed': 1, 'frames_extracted': 0,
                'error_summary': str(exc), 'normalization_method': 'copy',
            })
        return 1


def print_plan(rows: list[dict]) -> None:
    for row in rows:
        print(f"{row['_plan']}: {row['original_filename']} -> {row['normalized_filename']} "
              f"[video_id={row['video_id']}; frames={row['_frame_directory']}]")


def process_videos(rows: list[dict], args, ffmpeg_bin: Path | None, ffprobe_bin: Path | None,
                   report_dir: Path, skipped_files: list[str], source_count: int) -> int:
    output_dir, manifest_dir = args.output.resolve(), args.manifest_dir.resolve()
    extraction_rows = []
    result = dict(subject_name=args.subject_name, total_videos=source_count,
                  normalization_method='copy', renamed=0, normalized_copies_created=0,
                  already_normalized=0, normalization_failed=0, skipped_files=skipped_files,
                  skipped=len(skipped_files), failed=0, processed_videos=0, successful=0,
                  extraction_failed=0, frames_extracted=0, frames_created=0,
                  frames_reused=0, archived_frames=0, normalize_only=args.normalize_only,
                  extraction_policy_version=args.policy_version, sample_fps=args.sample_fps,
                  max_frames_per_video=args.max_frames_per_video)

    for v_idx, row in enumerate(rows, 1):
        stem = row['video_id']
        video = Path(row['normalized_path'])
        v_out_dir = output_dir / stem
        report = dict(video=video.name, video_id=stem, normalized_filename=video.name,
                      original_filename=row['original_filename'], duration_sec='',
                      frames_extracted=0, extracted_frame_count=0, target_frames=0, planned_frame_count=0, duration_seconds='', sample_fps_requested=args.sample_fps,
                      sample_fps_effective='', max_frames=args.max_frames_per_video,
                      extraction_policy_version=args.policy_version, archived_frames=0, archive_path='',
                      output_folder=v_out_dir.name, frame_directory=str(v_out_dir),
                      extraction_status='NOT_STARTED', ffmpeg_return_codes='', error_summary='',
                      frames_created=0, frames_reused=0)
        extraction_rows.append(report)
        try:
            operation = materialize_copy(row)
            row['normalization_status'] = 'READY'
            row['normalization_error'] = ''
            result['already_normalized' if operation == 'ALREADY_NORMALIZED' else 'normalized_copies_created'] += 1
            v_out_dir.mkdir(parents=True, exist_ok=True)
        except (NormalizationError, OSError) as exc:
            row['normalization_status'] = 'FAILED'
            row['normalization_error'] = str(exc)
            report.update(extraction_status='NORMALIZATION_FAILED', error_summary=str(exc))
            result['normalization_failed'] += 1
            result['failed'] += 1
            print(f"ERROR: {stem} normalization failed: {exc}", file=sys.stderr)
            write_csv_atomic(manifest_dir / 'video_manifest.csv', MANIFEST_FIELDS, rows)
            continue
        write_csv_atomic(manifest_dir / 'video_manifest.csv', MANIFEST_FIELDS, rows)
        if args.normalize_only:
            report['extraction_status'] = 'NOT_REQUESTED'
            continue

        result['processed_videos'] += 1
        try:
            duration = get_video_duration(video, ffprobe_bin)
            plan = sampling_plan(duration, args.sample_fps, args.max_frames_per_video,
                                 args.trim_start, args.trim_end)
            report.update(duration_sec=f"{duration:.2f}", duration_seconds=duration,
                          sample_fps_effective=plan['sample_fps_effective'],
                          target_frames=plan['planned_frames'], planned_frame_count=plan['planned_frames'])
            signature = policy_signature(plan, row['sha256'], args.policy_version)
            outcome = generate_video(ffmpeg_bin, video, v_out_dir, manifest_dir, stem,
                                     signature, args.overwrite)
            count = outcome['count']
            report.update(frames_extracted=count, extracted_frame_count=count, target_frames=count,
                          extraction_status='PASS', frames_created=outcome['created'],
                          frames_reused=outcome['reused'], archived_frames=outcome['archived_frames'],
                          archive_path=outcome['archive_path'])
            result['frames_extracted'] += count
            result['frames_created'] += outcome['created']
            result['frames_reused'] += outcome['reused']
            result['archived_frames'] += outcome['archived_frames']
            result['successful'] += 1
            print(f"[{v_idx}/{len(rows)}] {stem}: PASS duration={duration:.3f}s "
                  f"fps={plan['sample_fps_effective']:.6g} frames={count} "
                  f"created={outcome['created']} reused={outcome['reused']}", flush=True)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            report.update(extraction_status='FAIL', error_summary=f"{stem}: {exc}",
                          ffmpeg_return_codes=str(getattr(exc, 'return_code', '')))
            result['failed'] += 1
            result['extraction_failed'] += 1
            print(f"[{v_idx}/{len(rows)}] ERROR: {stem}: {exc}; old data retained", flush=True)
        # Checkpoint each completed video for interruption diagnostics.
        write_csv_atomic(manifest_dir / 'video_extraction.csv', list(report), extraction_rows)
        write_json_atomic(manifest_dir / 'step1_summary.json', {**result, 'status': 'IN_PROGRESS'})

    # Save summary report
    report_file = report_dir / "step1_extract_report.csv"
    fields = list(extraction_rows[0]) if extraction_rows else ["video", "video_id", "extraction_status"]
    write_csv_atomic(report_file, fields, extraction_rows)
    write_csv_atomic(manifest_dir / 'video_extraction.csv', fields, extraction_rows)
    durations = [float(item['duration_seconds']) for item in extraction_rows if item['duration_seconds'] != '']
    counts = [item['extracted_frame_count'] for item in extraction_rows if item['extraction_status'] == 'PASS']
    result['duration_statistics'] = dict(min=min(durations), median=statistics.median(durations), max=max(durations)) if durations else {}
    result['frame_count_statistics'] = dict(min=min(counts), median=statistics.median(counts), max=max(counts), total=sum(counts)) if counts else {}
    ordered = sorted((item for item in extraction_rows if item['extraction_status']=='PASS'), key=lambda item:(item['extracted_frame_count'],item['video_id']))
    result['fewest'] = [dict(video_id=item['video_id'], frames=item['extracted_frame_count'], duration=item['duration_seconds']) for item in ordered[:5]]
    result['most'] = [dict(video_id=item['video_id'], frames=item['extracted_frame_count'], duration=item['duration_seconds']) for item in reversed(ordered[-5:])]
    result['status'] = 'FAIL' if result['failed'] else 'PASS'
    write_json_atomic(manifest_dir / 'step1_summary.json', result)
    print(f"\nCompleted! Status: {result['status']}; processed videos: {result['processed_videos']}")
    print("Durations:", result["duration_statistics"])
    print("Frame counts:", result["frame_count_statistics"])
    print("Fewest:", result["fewest"])
    print("Most:", result["most"])
    print(f"Report saved to: {report_file}")
    print(f"Summary saved to: {manifest_dir / 'step1_summary.json'}")
    return 1 if result['failed'] else 0


if __name__ == "__main__":
    raise SystemExit(main())
