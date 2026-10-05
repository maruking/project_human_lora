"""Stored STEP3 BEST -> full-row STEP4 descriptors. No image/model imports."""
import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from common.config import load_for_cli, get_section, configure_parser, resolve_config_path
from common.pose_composition import (VERSION, INPUT_VERSION, settings_from, describe_rows,
                                     summarize, markdown_summary, finite)
from common.video_manifest import manifest_lock, sha256_file, write_csv_atomic, write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ('frame_id', 'filename', 'input_kind', 'source_id', 'video_id',
            'dataset_generation_id', 'image_sha256', 'ranking_version',
            'ranking_eligible', 'best_score', 'global_rank', 'fatal_reject_reason',
            'yaw', 'pitch', 'roll', 'pose_status')


def load_input(report, summary_path):
    with report.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if set(REQUIRED) - set(reader.fieldnames or []):
            raise ValueError('STEP3 columns missing: ' + ','.join(sorted(set(REQUIRED)-set(reader.fieldnames or []))))
        rows = list(reader)
    summary = json.loads(summary_path.read_text(encoding='utf-8-sig'))
    if summary.get('version') != INPUT_VERSION:
        raise ValueError('STEP4 requires current ' + INPUT_VERSION + ' summary')
    if summary.get('ranking_sha256') != sha256_file(report):
        raise ValueError('STEP3 CSV hash differs from authoritative summary')
    if summary.get('total_universe') != len(rows):
        raise ValueError('STEP3 expected/discovered universe mismatch')
    if not rows or len({r['frame_id'] for r in rows}) != len(rows):
        raise ValueError('Empty/duplicate STEP3 frame universe')
    for row in rows:
        if row['ranking_version'] != INPUT_VERSION:
            raise ValueError('Mixed STEP3 ranking versions')
        if any(not row[key] for key in ('frame_id', 'filename', 'input_kind', 'source_id',
                                        'dataset_generation_id', 'image_sha256')):
            raise ValueError('Incomplete source lineage: ' + row['frame_id'])
        if row['ranking_eligible'].lower() not in ('true', 'false'):
            raise ValueError('Invalid ranking_eligible: ' + row['frame_id'])
        if row['ranking_eligible'].lower() == 'true':
            if finite(row['best_score']) is None or not row['global_rank'].isdigit():
                raise ValueError('Incomplete eligible STEP3 score/rank: ' + row['frame_id'])
        elif not row['fatal_reject_reason']:
            raise ValueError('Non-ranking STEP3 row lacks fatal reason: ' + row['frame_id'])
    return rows


def write_text_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(text)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def publish(rows, settings, report, step3_summary, targets):
    paths = [report, step3_summary, *targets.values()]
    if len(set(p.resolve() for p in paths)) != len(paths):
        raise ValueError('Input/output paths must be distinct')
    for key, path in targets.items():
        expected_suffix = '.md' if key == 'markdown' else '.json' if key == 'summary' else '.csv'
        if path.suffix.lower() != expected_suffix or path.name.startswith(('step2_', 'step3_')):
            raise ValueError('Unsafe STEP4 output path: ' + str(path))
        if any(path.resolve().is_relative_to(ROOT / part) for part in
               ('scripts', 'bat', 'config', 'knowledge', '.agents', 'tests', 'input', 'work')):
            raise ValueError('STEP4 report cannot overwrite code/config/source: ' + str(path))
    outputs = describe_rows(rows, settings)
    assert [r['frame_id'] for r in outputs] == [r['frame_id'] for r in rows]
    assert all(o['best_score'] == r['best_score'] and o['ranking_eligible'] == r['ranking_eligible']
               for o, r in zip(outputs, rows))
    summary, sources = summarize(outputs)
    summary.update(input_report_sha256=sha256_file(report), input_summary_sha256=sha256_file(step3_summary),
                   input_ranking_version=INPUT_VERSION, thresholds=settings,
                   yaw_sign_convention='positive RIGHT; negative LEFT; repository convention, not anatomical',
                   face_scale_semantics='face bbox area / image area; not literal body visibility',
                   output_paths={key: str(value) for key, value in targets.items()})
    # Preserve prior outputs before individually atomic publication. This is not a
    # multi-file transaction; output CSV hash in summary detects interrupted runs.
    existing = {key: path for key, path in targets.items() if path.exists()}
    if existing:
        archive = targets['output'].parent / 'bkup' / (VERSION + '_' + uuid.uuid4().hex)
        archive.mkdir(parents=True, exist_ok=False)
        audit = []
        for key, source in existing.items():
            destination = archive / (key + source.suffix)
            shutil.copy2(source, destination)
            digest = sha256_file(source)
            if sha256_file(destination) != digest:
                raise ValueError('STEP4 historical output copy mismatch')
            audit.append(dict(original_path=str(source), archived_path=str(destination), sha256=digest))
        write_json_atomic(archive / 'MANIFEST.json', dict(files=audit))
    columns = list(dict.fromkeys(key for row in outputs for key in row))
    write_csv_atomic(targets['output'], columns, outputs)
    summary['output_csv_sha256'] = sha256_file(targets['output'])
    write_csv_atomic(targets['video_summary'], list(sources[0]), sources)
    summary['video_summary_sha256'] = sha256_file(targets['video_summary'])
    write_text_atomic(targets['markdown'], markdown_summary(summary))
    summary['markdown_sha256'] = sha256_file(targets['markdown'])
    write_json_atomic(targets['summary'], summary)  # completion marker written last
    return summary


def main():
    config = load_for_cli()
    settings = settings_from(config)
    parser = argparse.ArgumentParser(description='STEP4 v2: classify stored pose/face scale, no inference or selection')
    for name, default in (
        ('report', '@reports/step3_best_ranking.csv'),
        ('step3-summary', '@reports/step3_best_ranking_summary.json'),
        ('output', '@reports/step4_pose_composition.csv'),
        ('summary', '@reports/step4_pose_summary.json'),
        ('video-summary', '@reports/step4_video_pose_summary.csv'),
        ('markdown', 'docs/STEP4_POSE_COMPOSITION_SUMMARY.md')):
        parser.add_argument('--' + name, type=Path, default=resolve_config_path(default, config))
    parser.add_argument('--config', type=Path)
    configure_parser(parser, config, 'step4_pose_composition')
    args = parser.parse_args()
    section = get_section(config, 'step4_pose_composition')
    if section.get('version', VERSION) != VERSION:
        raise ValueError('Unsupported STEP4 output version')
    targets = {key: getattr(args, key) for key in ('output', 'summary', 'video_summary', 'markdown')}
    print('STEP4 version:', VERSION)
    print('Input:', args.report)
    for key, path in targets.items():
        print(key + ':', path)
    with manifest_lock(args.report.parent / '.step3_best_operation.lock'), \
         manifest_lock(args.output.parent / '.step4_pose_operation.lock'):
        rows = load_input(args.report, args.step3_summary)
        summary = publish(rows, settings, args.report, args.step3_summary, targets)
    print('Rows:', summary['total_rows'], 'statuses:', summary['statuses'])
    return 1 if summary['statuses'].get('ERROR', 0) else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('[ERROR] ' + str(exc), file=sys.stderr)
        sys.exit(1)
