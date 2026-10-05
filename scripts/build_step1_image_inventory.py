"""Explicit STEP1 image listing: formal video frames + a declared still subtree.

No scoring, selection, deletion or image transformation. Stills do not change
the formal video extraction counts. Run only after successful STEP1 completion.
"""
from common.step3_review import is_review_copy, require_source

import argparse
import csv
import json
from pathlib import Path
from common.config import load_config, resolve_config_path, resolve_project_path
from common.video_manifest import natural_key, sha256_file, write_csv_atomic, write_json_atomic

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if len({r['video_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate video IDs')
    return rows


def build(raw, manifests, supplemental, reports):
    from common.step3_review import REGISTERED_ROOTS
    REGISTERED_ROOTS.update((Path(reports).resolve()/name for name in ("passed","borderline")))
    require_source(raw)
    require_source(supplemental)
    if not supplemental.is_dir() or supplemental == raw or not supplemental.is_relative_to(raw):
        raise ValueError('Declare an existing supplemental subtree inside the frame root')
    summary = json.loads((manifests/'step1_summary.json').read_text(encoding='utf-8-sig'))
    videos = read_csv(manifests/'video_manifest.csv')
    extraction = read_csv(manifests/'video_extraction.csv')
    if (summary['status'] != 'PASS' or summary['failed'] != 0 or
        len(videos) != summary['total_videos'] or {r['video_id'] for r in videos} != {r['video_id'] for r in extraction}):
        raise ValueError('STEP1 is not a complete successful generation')
    sources = {r['video_id']:r for r in videos}
    rows = []
    for record in extraction:
        video = record['video_id']
        if record['extraction_status'] != 'PASS':
            raise ValueError(f'Incomplete extraction: {video}')
        metadata = json.loads((raw/video/'.extraction_metadata.json').read_text(encoding='utf-8-sig'))
        frames, policy = metadata['frames'], metadata['policy']
        if (metadata['status'] != 'PASS' or len(frames) != int(record['extracted_frame_count'])
            or policy['source_sha256'] != sources[video]['sha256']):
            raise ValueError(f'Frame metadata count/source mismatch: {video}')
        for index, frame in enumerate(frames, 1):
            path = raw/video/frame['name']
            if frame['name'] != f'{video}_{index:03d}.png' or path.stat().st_size != frame['size']:
                raise ValueError(f'Frame filename/size differs from extraction receipt: {path}')
            name = path.relative_to(raw).as_posix()
            rows.append(dict(input_kind='VIDEO_FRAME', video_id=video, temporal_index=index,
                             frame_id=name, filename=name, image_path=str(path), file_size_bytes=frame['size'],
                             image_sha256=frame['sha256'], sha256_source='STEP1_EXTRACTION_METADATA',
                             source_video_path=sources[video]['original_path'], source_video_sha256=policy['source_sha256'],
                             extraction_policy_version=policy['extraction_policy_version'],
                             sample_fps_requested=policy['sample_fps_requested'], sample_fps_effective=policy['sample_fps_effective']))
    video_count = len(rows)
    if video_count != summary['frames_extracted']:
        raise ValueError('STEP1 summary/frame inventory mismatch')
    stills = sorted((p for p in supplemental.rglob('*') if not is_review_copy(p) and p.is_file() and p.suffix.lower() in EXTENSIONS), key=natural_key)
    if not stills:
        raise ValueError('No supplemental images found')
    for path in stills:
        if not path.resolve().is_relative_to(supplemental):
            raise ValueError('Supplemental symlink escapes declared source')
        name = path.relative_to(raw).as_posix()
        rows.append(dict(input_kind='SUPPLEMENTAL_STILL', video_id='', temporal_index='',
                         frame_id=name, filename=name, image_path=str(path), file_size_bytes=path.stat().st_size,
                         image_sha256=sha256_file(path), sha256_source='DIRECT_FILE_HASH', source_video_path='',
                         source_video_sha256='', extraction_policy_version='', sample_fps_requested='', sample_fps_effective=''))
    expected = {r['filename'] for r in rows}
    actual = {p.relative_to(raw).as_posix() for p in raw.rglob('*') if not is_review_copy(p) and p.is_file() and p.suffix.lower() in EXTENSIONS}
    if len(expected) != len(rows) or actual != expected:
        raise ValueError('Actual frame-root image inventory differs from declared formal + supplemental inputs')
    reports.mkdir(parents=True, exist_ok=True)
    output = reports/'step1_image_inventory.csv'
    write_csv_atomic(output, list(rows[0]), rows)
    receipt = dict(status='PASS_INVENTORY', raw_frames_dir=str(raw), supplemental_dir=str(supplemental),
                   video_count=len(videos), video_frames=video_count, supplemental_stills=len(stills), total_images=len(rows),
                   inventory_csv_sha256=sha256_file(output), step1_summary_sha256=sha256_file(manifests/'step1_summary.json'),
                   validation='STEP1 receipt hashes + current filename/size/count coverage; still hashes measured directly',
                   full_video_frame_hash_reread=False, images_modified=False)
    write_json_atomic(reports/'step1_image_inventory.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--supplemental-dir', type=Path, required=True)
    parser.add_argument('--images', type=Path)
    parser.add_argument('--manifest-dir', type=Path)
    parser.add_argument('--reports-dir', type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    def path(key): return resolve_config_path(config['paths'][key], config)
    raw = resolve_project_path(args.images) if args.images else path('raw_frames_dir')
    supplemental = args.supplemental_dir.resolve() if args.supplemental_dir.is_absolute() else (raw/args.supplemental_dir).resolve()
    manifests = resolve_project_path(args.manifest_dir) if args.manifest_dir else path('manifests_dir')
    reports = resolve_project_path(args.reports_dir) if args.reports_dir else path('reports_dir')
    build(raw, manifests, supplemental, reports)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        raise SystemExit(f'Image inventory failed: {exc}')
