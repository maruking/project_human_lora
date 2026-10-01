"""STEP 1: Extract equally spaced high-quality raw frames from video files using FFmpeg.

Extracts N (default: 50) frames per video, automatically trimming the head and tail
(default: 0.5s) to eliminate touch/shake/transition artifacts.
Supports automatic discovery of ffmpeg/ffprobe and OpenCV fallback.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import cv2
except ImportError:
    cv2 = None


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
    if ffprobe_bin and ffprobe_bin.is_file():
        cmd = [
            str(ffprobe_bin),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(res.stdout)
            dur = float(info["format"]["duration"])
            if dur > 0:
                return dur
        except Exception:
            pass

    if cv2 is not None:
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            if fps > 0 and count > 0:
                return float(count / fps)

    return 0.0


def extract_frame_ffmpeg(ffmpeg_bin: Path, video_path: Path, timestamp: float, output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-ss", f"{timestamp:.3f}",
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path.is_file() and output_path.stat().st_size > 0
    except Exception:
        return False


def extract_frame_cv2(video_path: Path, timestamp: float, output_path: Path) -> bool:
    if cv2 is None:
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return False
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_no = int(timestamp * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    cap.release()
    if ret and frame is not None:
        return cv2.imwrite(str(output_path), frame)
    return False


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
    default_input, default_output, default_reports = resolve_default_paths(project)

    parser = argparse.ArgumentParser(description="Extract N equally spaced frames from videos.")
    parser.add_argument("--input", type=Path, default=default_input, help="Input directory containing MP4 videos")
    parser.add_argument("--output", type=Path, default=default_output, help="Output directory for raw frames")
    parser.add_argument("--num-frames", type=int, default=50, help="Number of frames to extract per video (default: 50)")
    parser.add_argument("--trim-start", type=float, default=0.5, help="Seconds to trim from start (default: 0.5s)")
    parser.add_argument("--trim-end", type=float, default=0.5, help="Seconds to trim from end (default: 0.5s)")
    parser.add_argument("--subfolders", action="store_true", default=True, help="Store in <output>/<video_stem>/ subfolders")
    parser.add_argument("--flat", dest="subfolders", action="store_false", help="Store all frames directly in <output>/")
    parser.add_argument("--ffmpeg", type=Path, default=None, help="Explicit path to ffmpeg executable")
    parser.add_argument("--ffprobe", type=Path, default=None, help="Explicit path to ffprobe executable")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing extracted frames")
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_dir = args.output.resolve()

    if not input_dir.is_dir():
        print(f"ERROR: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    ffmpeg_bin = find_binary("ffmpeg", args.ffmpeg)
    ffprobe_bin = find_binary("ffprobe", args.ffprobe)

    if ffmpeg_bin:
        print(f"Using FFmpeg : {ffmpeg_bin}")
    else:
        print("WARNING: FFmpeg binary not found. Falling back to OpenCV video reader.", file=sys.stderr)

    extensions = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
    video_files = sorted([f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions])

    if not video_files:
        print(f"No video files found in: {input_dir}")
        print(f"Supported formats: {', '.join(sorted(extensions))}")
        return 0

    print(f"Found {len(video_files)} video(s) in {input_dir.name}")
    print(f"Target frames per video : {args.num_frames}")
    print(f"Trim start / end        : {args.trim_start:.2f}s / {args.trim_end:.2f}s")
    print(f"Output directory        : {output_dir}\n")

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = []

    for v_idx, video in enumerate(video_files, 1):
        stem = video.stem
        duration = get_video_duration(video, ffprobe_bin)

        if duration <= 0.0:
            print(f"[{v_idx}/{len(video_files)}] WARNING: Could not determine duration for {video.name}. Skipping.")
            continue

        start_t = args.trim_start
        end_t = duration - args.trim_end
        if end_t <= start_t:
            start_t = duration * 0.05
            end_t = duration * 0.95

        n = max(args.num_frames, 1)
        if n == 1:
            timestamps = [(start_t + end_t) / 2.0]
        else:
            step = (end_t - start_t) / (n - 1)
            timestamps = [start_t + i * step for i in range(n)]

        v_out_dir = output_dir / stem if args.subfolders else output_dir
        v_out_dir.mkdir(parents=True, exist_ok=True)

        extracted_count = 0
        for f_idx, t in enumerate(timestamps, 1):
            out_file = v_out_dir / f"{stem}_{f_idx:03d}.png"
            if out_file.exists() and not args.overwrite:
                extracted_count += 1
                continue

            success = False
            if ffmpeg_bin:
                success = extract_frame_ffmpeg(ffmpeg_bin, video, t, out_file)
            if not success:
                success = extract_frame_cv2(video, t, out_file)

            if success:
                extracted_count += 1

        print(f"[{v_idx}/{len(video_files)}] {video.name} ({duration:.1f}s) -> Extracted {extracted_count}/{n} frames to {v_out_dir.name}/")
        summary.append({
            "video": video.name,
            "duration_sec": f"{duration:.2f}",
            "frames_extracted": extracted_count,
            "target_frames": n,
            "output_folder": v_out_dir.name,
        })

    # Save summary report
    report_file = default_reports / "step1_extract_report.csv"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with report_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["video", "duration_sec", "frames_extracted", "target_frames", "output_folder"])
        writer.writeheader()
        writer.writerows(summary)

    print(f"\nCompleted! Total processed videos: {len(summary)}")
    print(f"Report saved to: {report_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
