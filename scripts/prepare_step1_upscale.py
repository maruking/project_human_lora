"""STEP1 orchestration only: existing upscale BAT -> unchanged extractor.

Never invokes processing for --dry-run/--help. No source video is modified here.
The one-time source transition archives old copies/metadata and preserves IDs.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from common.config import load_config, resolve_config_path, resolve_project_path
from common.video_manifest import (MANIFEST_FIELDS, manifest_lock, path_key,
                                  read_manifest, scan_videos, sha256_file,
                                  video_id, write_csv_atomic, write_json_atomic)

ROOT = Path(__file__).resolve().parents[1]


def upscale_contract(source):
    bat = source/'run_upscale_4k.bat'
    text = bat.read_text(encoding='utf-8-sig')
    # Fail closed if the external BAT's observed input/output contract changes.
    folder = re.search(r'^set "OUT_DIR=%CURR_DIR%\\([^"\\]+)"\s*$', text, re.M | re.I)
    script = re.search(r'^%PY_CMD% "([^"]+)" --input "%CURR_DIR%" --output "%OUT_DIR%" %\*\s*$', text, re.M | re.I)
    if not folder or not script or 'set "CURR_DIR=%~dp0"' not in text:
        raise ValueError('Upscale BAT contract changed; inspect it before proceeding')
    processor = Path(script[1])
    if not processor.is_file():
        raise ValueError(f'Upscale processor missing: {processor}')
    output = (source/folder[1]).resolve()
    if output.parent != source or output == source:
        raise ValueError('Upscale output must be a distinct direct subfolder of the source')
    return bat, output, processor


def processor_module(path):
    spec = importlib.util.spec_from_file_location('existing_upscale_processor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resume_transition(manifests, normalized, frames):
    journal = manifests/'step1_upscale_transition.json'
    if not journal.exists():
        return
    state = json.loads(journal.read_text(encoding='utf-8'))
    if state['status'] == 'COMPLETE':
        return
    if state['normalized_dir'] != str(normalized) or state['frames_dir'] != str(frames):
        raise ValueError('Pending transition belongs to different configured outputs')
    for row in state['new_rows']:
        if sha256_file(Path(row['original_path'])) != row['sha256']:
            raise ValueError('Upscaled source changed during pending transition')
    archive = Path(state['archive'])
    if archive.parent != normalized.parent/(normalized.name+'_previous'):
        raise ValueError('Invalid transition archive target')
    current = read_manifest(manifests/'video_manifest.csv')
    if current != state['old_rows'] and current != state['new_rows']:
        raise ValueError('Manifest changed during pending transition')
    # Snapshot immutable evidence before moving any working files.
    archive.mkdir(parents=True, exist_ok=True)
    for name in ('video_manifest.csv', 'video_extraction.csv', 'step1_summary.json'):
        src, dst = manifests/name, archive/name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
    archived_videos = archive/'videos'
    if current == state['old_rows']:
        if normalized.exists():
            if archived_videos.exists():
                raise ValueError('Both old and archived copy directories exist; investigate')
            normalized.rename(archived_videos)
        write_csv_atomic(manifests/'video_manifest.csv', MANIFEST_FIELDS, state['new_rows'])
    write_json_atomic(manifests/'step1_summary.json', {
        'status': 'IN_PROGRESS', 'reason': 'UPSCALED_SOURCE_TRANSITION_PENDING_EXTRACTION',
        'previous_generation_archive': str(archive)})
    state['status'] = 'COMPLETE'
    write_json_atomic(journal, state)


def prepare_manifest(manifests, normalized, frames, source, upscale, outputs, subject, available_only=False):
    with manifest_lock(manifests/'.video_manifest.lock'):
        resume_transition(manifests, normalized, frames)
        old = read_manifest(manifests/'video_manifest.csv')
        if not old:
            return  # Existing extractor assigns the initial IDs.
        output_by_name = {p.name.casefold(): p for p in outputs}
        if len(output_by_name) != len(outputs):
            raise ValueError('Case-insensitive duplicate upscaled filenames')
        new, lineage, inactive = [], [], []
        indices = set()
        for row in old:
            index = int(row['index'])
            if (row['subject_name'] != subject or row['video_id'] != video_id(subject, index)
                or index in indices or Path(row['normalized_path']).resolve() != normalized/row['normalized_filename']):
                raise ValueError('Existing manifest subject/ID/output mapping mismatch')
            indices.add(index)
            old_path = Path(row['original_path']).resolve()
            if old_path.parent not in (source, upscale):
                raise ValueError('Manifest source is outside the declared original/upscale folders')
            output = output_by_name.get(row['original_filename'].casefold())
            if output is None:
                if available_only:
                    inactive.append(dict(row))
                    continue
                raise ValueError(f'Missing upscaled source for existing ID: {row["video_id"]}')
            sha = sha256_file(output)
            if old_path.parent == upscale:
                if sha != row['sha256'] or output.stat().st_size != int(row['file_size']):
                    raise ValueError('Tracked upscaled source changed; investigate instead of overwrite')
                new.append(dict(row))
                continue
            replacement = dict(row, original_path=str(output), original_filename=output.name,
                               file_size=str(output.stat().st_size), sha256=sha,
                               normalization_status='PLANNED', normalization_error='')
            new.append(replacement)
            lineage.append(dict(video_id=row['video_id'], original_path=row['original_path'],
                                original_sha256=row['sha256'], original_file_size=row['file_size'],
                                original_present=old_path.is_file(), upscaled_path=str(output),
                                upscaled_sha256=sha, upscaled_file_size=output.stat().st_size))
        if not lineage and not inactive:
            return  # Already migrated; the extractor verifies/reuses matching copies.
        if lineage and len(lineage) + len(inactive) != len(old):
            raise ValueError('Mixed original/upscaled manifest is not an automatic transition')
        if normalized.exists():
            allowed = {row['normalized_filename'].casefold() for row in old}
            if any(not p.is_file() or p.name.casefold() not in allowed for p in normalized.iterdir()):
                raise ValueError('Untracked files in normalized directory; archive not attempted')
        archive = normalized.parent/(normalized.name+'_previous')/('upscale_'+uuid.uuid4().hex)
        state = dict(status='PREPARED', archive=str(archive), normalized_dir=str(normalized),
                     frames_dir=str(frames), old_rows=old, new_rows=new, lineage=lineage,
                     inactive_rows=inactive, selection_scope='AVAILABLE_UPSCALED_ONLY' if available_only else 'ALL_TRACKED_SOURCES')
        write_json_atomic(manifests/'step1_upscale_transition.json', state)
        resume_transition(manifests, normalized, frames)
        print(f'Previous STEP1 source mapping/copies preserved: {archive}', flush=True)


def main():
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--normalized-dir', type=Path)
    parser.add_argument('--manifest-dir', type=Path)
    parser.add_argument('--subject-name')
    parser.add_argument('--skip-upscale', action='store_true', help='Use existing outputs; never invoke upscale BAT')
    parser.add_argument('--available-upscaled-only', action='store_true', help='Explicit new source generation using available outputs; archive absent prior mappings')
    parser.add_argument('--supplemental-dir', type=Path, help='Explicit one-run still subtree to include in a separate image inventory')
    args, other = parser.parse_known_args()
    if '--help' in other or '-h' in other:
        return subprocess.run([sys.executable, str(ROOT/'scripts/extract_frames.py'), *sys.argv[1:]]).returncode
    config = load_config(args.config)
    paths = config['paths']
    def configured(arg, key):
        return resolve_project_path(arg) if arg else resolve_config_path(paths[key], config)
    source = configured(args.input, 'input_video_dir')
    normalized = configured(args.normalized_dir, 'normalized_video_dir')
    manifests = configured(args.manifest_dir, 'manifests_dir')
    frames = configured(args.output, 'raw_frames_dir')
    subject = args.subject_name or config['project']['subject_name']
    bat, upscale, processor = upscale_contract(source)
    for target in (source, upscale, frames, manifests):
        if normalized.is_relative_to(target) or target.is_relative_to(normalized):
            raise ValueError('Normalized-copy directory must not overlap source/frame/manifest directories')
    print(f'STEP1 flow: {bat} -> {upscale} -> {normalized} -> {frames}', flush=True)
    if '--dry-run' in other:
        print('DRY RUN: path/control-flow inspection only; no upscale, hashes, manifest writes or extraction.')
        print('Existing IDs retained; old working copies/manifests archived only during the real source transition.')
        return 0
    stage_extensions = {'.mp4', '.mov', '.mkv', '.webm'}  # Observed existing processor contract.
    supported = set(config.get('step1_extract', {}).get('supported_extensions', stage_extensions))
    originals, _ = scan_videos(source, supported)
    if any(p.suffix.lower() not in stage_extensions for p in originals):
        raise ValueError('Source format is unsupported by the existing upscale processor')
    # Never pass extraction --overwrite/--input arguments to the upscale BAT.
    if args.skip_upscale:
        print('Upscale explicitly skipped: use existing upscaled source videos.', flush=True)
    elif originals:
        code = subprocess.run(f'call "{bat}"', shell=True, cwd=source).returncode
        if code:
            return code
    else:
        print('No original-root videos; reuse existing upscale outputs (no recursive upscale).', flush=True)
    if not upscale.is_dir():
        raise ValueError('Upscale output directory missing')
    outputs, _ = scan_videos(upscale, stage_extensions & supported)
    if not outputs or (not args.available_upscaled_only and not {p.name.casefold() for p in originals} <= {p.name.casefold() for p in outputs}):
        raise ValueError('Upscale outputs empty/incomplete; extraction not started')
    # The external processor can return zero after a per-video FFmpeg failure.
    # Readability validation therefore precedes any manifest transition.
    module = processor_module(processor)
    ffmpeg, ffprobe = module.find_ffmpeg()
    for output in outputs:
        info = module.get_video_info(ffprobe, output)
        if (output.stat().st_size < 1 or min(info['width'], info['height']) <= 0
            or not math.isfinite(info['duration']) or info['duration'] <= 0):
            raise ValueError(f'Invalid upscaled video: {output}')
    prepare_manifest(manifests, normalized, frames, source, upscale, outputs, subject, args.available_upscaled_only)
    command = [sys.executable, str(ROOT/'scripts/extract_frames.py'), *other, '--input', str(upscale),
               '--output', str(frames), '--normalized-dir', str(normalized), '--manifest-dir', str(manifests),
               '--subject-name', subject]
    if args.config:
        command += ['--config', str(resolve_project_path(args.config))]
    for name, binary in (('ffmpeg', ffmpeg), ('ffprobe', ffprobe)):
        if not config.get('step1_extract', {}).get(name) and not any(
            a == '--'+name or a.startswith('--'+name+'=') for a in other):
            command += ['--'+name, str(binary)]
    code = subprocess.run(command).returncode
    if code or args.supplemental_dir is None:
        return code
    inventory = [sys.executable, str(ROOT/'scripts/build_step1_image_inventory.py'),
                 '--images', str(frames), '--manifest-dir', str(manifests),
                 '--reports-dir', str(resolve_config_path(paths['reports_dir'], config)),
                 '--supplemental-dir', str(args.supplemental_dir)]
    if args.config:
        inventory += ['--config', str(resolve_project_path(args.config))]
    return subprocess.run(inventory).returncode


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print(f'ERROR: STEP1 upscale preparation failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
