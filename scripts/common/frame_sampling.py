"""Duration-aware sampling and policy-verified staged extraction (DEC-0009)."""
from __future__ import annotations
import json
import math
from pathlib import Path
import subprocess
import uuid

from common.video_manifest import natural_key, sha256_file, write_json_atomic


def sampling_plan(duration: float, sample_fps: float, maximum: int,
                  trim_start: float = 0.0, trim_end: float = 0.0) -> dict:
    if not all(math.isfinite(value) for value in (duration, sample_fps, trim_start, trim_end)):
        raise ValueError('Duration, FPS and trims must be finite')
    usable = duration - trim_start - trim_end
    if duration <= 0 or usable <= 0 or sample_fps <= 0 or maximum < 1 or min(trim_start, trim_end) < 0:
        raise ValueError('Positive duration/FPS/max and nonnegative valid trims are required')
    nominal = usable * sample_fps
    count = maximum if nominal >= maximum else math.ceil(nominal)
    if count < 1:
        raise ValueError('Sampling interval contains no frame')
    return dict(duration_seconds=duration, sampling_duration_seconds=usable,
                sample_fps_requested=sample_fps, sample_fps_effective=min(sample_fps, maximum/usable),
                max_frames=maximum, planned_frames=count, trim_start=trim_start, trim_end=trim_end)


def policy_signature(plan: dict, source_sha256: str, version: int) -> dict:
    return dict(**plan, extraction_policy_version=version, source_sha256=source_sha256,
                recipe='ffmpeg-fps-round-up-png-q2-v2', naming='video_id_3digit_png')


def inspect_frames(folder: Path, video_id: str) -> list[dict]:
    from PIL import Image
    images = sorted(folder.glob('*.png'), key=natural_key)
    records = []
    for index, path in enumerate(images, 1):
        if path.name != f'{video_id}_{index:03d}.png' or path.is_symlink():
            raise ValueError('Unexpected/noncontiguous frame filename')
        with Image.open(path) as image:
            if image.format != 'PNG':
                raise ValueError('Output is not PNG')
            image.verify()
        records.append(dict(name=path.name, size=path.stat().st_size, sha256=sha256_file(path)))
    return records


def reusable_frames(folder: Path, signature: dict, video_id: str) -> list[dict] | None:
    try:
        metadata = json.loads((folder/'.extraction_metadata.json').read_text(encoding='utf-8'))
        if metadata['status'] != 'PASS' or metadata['policy'] != signature:
            return None
        frames = metadata['frames']
        if not 0 < len(frames) <= signature['planned_frames'] or len(frames) < signature['planned_frames'] - 1:
            return None
        if {p.name for p in folder.iterdir()} != {frame['name'] for frame in frames} | {'.extraction_metadata.json'}:
            return None
        for index, frame in enumerate(frames, 1):
            path = folder / frame['name']
            if frame['name'] != f'{video_id}_{index:03d}.png' or path.is_symlink() or not path.is_file():
                return None
            if path.stat().st_size != frame['size'] or sha256_file(path) != frame['sha256']:
                return None
        return frames
    except (OSError, ValueError, KeyError, TypeError):
        return None


def run_ffmpeg(ffmpeg: Path, video: Path, folder: Path, video_id: str, plan: dict) -> None:
    command = [str(ffmpeg), '-v', 'error', '-y', '-ss', str(plan['trim_start']),
               '-i', str(video), '-t', str(plan['sampling_duration_seconds']),
               '-vf', f"fps={plan['sample_fps_effective']:.15g}:round=up",
               '-frames:v', str(plan['planned_frames']), '-q:v', '2',
               str(folder / f'{video_id}_%03d.png')]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        stderr = result.stderr.decode('utf-8', errors='replace')[-2000:]
        raise ExtractionFailure(result.returncode, stderr or 'FFmpeg failed')


class ExtractionFailure(ValueError):
    def __init__(self, return_code, message):
        super().__init__(message)
        self.return_code = return_code


def generate_video(ffmpeg: Path, video: Path, folder: Path, manifest_dir: Path,
                   video_id: str, signature: dict, overwrite: bool = False) -> dict:
    """Keep old data until validated new output is ready; preserve every generation."""
    if folder.is_symlink() or not folder.resolve().is_relative_to(folder.parent.resolve()):
        raise ValueError('Frame folder must be a real directory beneath configured root')
    cached = None if overwrite else reusable_frames(folder, signature, video_id)
    if cached is not None:
        return dict(count=len(cached), created=0, reused=len(cached), archived_frames=0, archive_path='')
    generation = uuid.uuid4().hex
    staging = manifest_dir / '.extraction_staging' / f'{video_id}-{generation}'
    staging.mkdir(parents=True, exist_ok=False)
    # Failed staging generations stay outside the raw input tree for diagnosis.
    run_ffmpeg(ffmpeg, video, staging, video_id, signature)
    frames = inspect_frames(staging, video_id)
    if not 0 < len(frames) <= signature['planned_frames'] or len(frames) < signature['planned_frames'] - 1:
        raise ExtractionFailure(0, f"Output count {len(frames)} is outside expected FPS end-rounding range for {signature['planned_frames']}")
    write_json_atomic(staging/'.extraction_metadata.json',
                      dict(status='PASS', policy=signature, extracted_frame_count=len(frames), frames=frames))
    archive = None
    archived_frames = 0
    if folder.exists():
        if not folder.is_dir():
            raise ValueError('Frame destination is not a directory')
        archive = folder.parent.parent / (folder.parent.name + '_previous') / video_id / generation
        if not archive.resolve().is_relative_to(folder.parent.parent.resolve()):
            raise ValueError('Archive destination escapes configured work directory')
        archive.parent.mkdir(parents=True, exist_ok=True)
        archived_frames = len(list(folder.glob('*.png')))
        folder.rename(archive)
    try:
        folder.parent.mkdir(parents=True, exist_ok=True)
        # staging and destination are on the same configured workspace volume.
        staging.rename(folder)
    except OSError:
        if archive is not None and not folder.exists():
            archive.rename(folder)
        raise
    return dict(count=len(frames), created=len(frames), reused=0,
                archived_frames=archived_frames,
                archive_path=archive.relative_to(folder.parent.parent).as_posix() if archive else '')
