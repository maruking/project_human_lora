"""Validate the complete STEP1 generation before any image metric computation."""
from common.step3_review import is_review_copy, require_source

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
from common.metric_report import read_step1_counts, image_order


def read_json(path):
    with path.open(encoding='utf-8-sig') as handle:
        return json.load(handle)


def preflight(source: Path, directory: Path):
    require_source(source)
    expected = read_step1_counts(directory)
    summary = read_json(directory / 'step1_summary.json')
    if (summary['status'] != 'PASS' or summary['frames_extracted'] != sum(expected.values())
            or summary['total_videos'] != len(expected) or summary['failed'] != 0
            or summary['extraction_failed'] != 0 or summary['successful'] != len(expected)):
        raise ValueError('STEP1 summary and extraction counts/status differ')
    images = sorted((p for p in source.rglob('*') if not is_review_copy(p) and p.is_file() and
                     p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}),
                    key=lambda p: image_order(p, source))
    counts = Counter(p.relative_to(source).parts[0] for p in images)
    if dict(counts) != expected:
        raise ValueError(f'STEP1 expected {sum(expected.values())} frames; discovered {len(images)}; per-video count mismatch')
    with (directory/'video_extraction.csv').open(encoding='utf-8-sig', newline='') as f:
        extraction = {row['video_id']: row for row in csv.DictReader(f)}
    with (directory/'video_manifest.csv').open(encoding='utf-8-sig', newline='') as f:
        manifest = {row['video_id']: row for row in csv.DictReader(f)}
    provenance = {}; fingerprint = []
    for video, count in expected.items():
        metadata = read_json(source/video/'.extraction_metadata.json')
        policy = metadata['policy']; frames = metadata['frames']; record = extraction[video]
        if metadata['status'] != 'PASS' or len(frames) != count or metadata.get('extracted_frame_count',count) != count:
            raise ValueError(f'{video}: metadata count/status mismatch')
        inventory = {item['name']: item for item in frames}
        actual = [p for p in images if p.parent == source/video]
        if len(inventory) != count or set(inventory) != {p.name for p in actual}:
            raise ValueError(f'{video}: STEP1 frame inventory mismatch')
        if policy['source_sha256'] != manifest[video]['sha256']:
            raise ValueError(f'{video}: source generation mismatch')
        trace = {}
        for key in ('extraction_policy_version','sample_fps_requested','sample_fps_effective'):
            value = policy[key]
            if float(record[key]) != float(value):
                raise ValueError(f'{video}: extraction policy mismatch: {key}')
            trace[key] = value
        if (policy['extraction_policy_version'] != summary['extraction_policy_version']
                or policy['sample_fps_requested'] != summary['sample_fps']
                or policy['max_frames'] != summary['max_frames_per_video']):
            raise ValueError(f'{video}: summary policy mismatch')
        for p in actual:
            match = re.fullmatch(re.escape(video)+r'_(\d{3,})\.png', p.name)
            if not match or p.name != f'{video}_{int(match[1]):03d}.png' or int(match[1]) < 1:
                raise ValueError(f'{video}: invalid STEP1 filename grammar')
            item = inventory[p.name]
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if p.stat().st_size != item['size'] or digest != item['sha256']:
                raise ValueError(f'{video}: frame content differs from STEP1: {p.name}')
            name = p.relative_to(source).as_posix()
            provenance[name] = dict(trace, temporal_index=int(match[1]))
            fingerprint.append([name,digest,policy['source_sha256'],trace])
    generation = {'sha256': hashlib.sha256(json.dumps(fingerprint,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                  'extraction_policy_version': summary['extraction_policy_version'],
                  'sample_fps_requested': summary['sample_fps'],
                  'max_frames_per_video':summary['max_frames_per_video'],
                  'frame_count':len(images), 'video_count':len(expected),
                  'metadata':'STEP1 manifests, summary and per-video extraction metadata'}
    return expected, images, provenance, generation
