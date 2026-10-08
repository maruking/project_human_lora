"""STEP5 v2: full-row duplicate annotation, source-referencing diagnostic galleries."""
import argparse
import csv
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import quote
import uuid

import cv2
import numpy as np
from common.config import load_for_cli, get_section, configure_parser, resolve_config_path
from common.dedup_v2 import (VERSION, RULE_KEYS, POOL_ROLES, FIELDS, annotate, summarize, ordering,
                             compute_phash, pose)
from common.pose_composition import POSE_BINS, SCALE_BINS, ADDED_FIELDS, geometry
from common.video_manifest import sha256_file, write_csv_atomic, write_json_atomic, manifest_lock
from step4_pose_composition import load_input as load_step3

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ('frame_id','filename','input_kind','source_id','video_id','temporal_index',
            'dataset_generation_id','image_sha256','ranking_eligible','best_score','global_rank',
            'ranking_version','step4_version','step4_status','pose_bin','face_scale_bin','yaw','pitch',
            'width','height','face_bbox')
PATH_DEFAULTS = dict(report='@reports/step4_pose_composition.csv',
    step4_summary='@reports/step4_pose_summary.json', step3_report='@reports/step3_best_ranking.csv',
    step3_summary='@reports/step3_best_ranking_summary.json', output_csv='@reports/step5_dataset_report.csv',
    summary='@reports/step5_dedup_summary.json', markdown='docs/STEP5_DEDUP_SUMMARY.md',
    review_html='docs/STEP5_DEDUP_REVIEW.html', pose_review='docs/STEP5_REPRESENTATIVE_POSE_REVIEW.html',
    pose_summary='@reports/step5_representative_pose_summary.csv')
OUTPUT_KEYS = ('output_csv','summary','markdown','review_html','pose_review','pose_summary')
STEP4_INPUT_VERSIONS = ('step4_pose_composition_v2', 'step4_pose_composition_v3')
V3_POSE_FIELDS = ('yaw', 'pitch', 'roll', 'pose_status')


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if len(set(columns)) != len(columns):
            raise ValueError('Duplicate CSV column name')
        return columns, list(reader)


def source_path(row, images):
    relative = Path(row['filename'].replace('\\', '/'))
    if relative.is_absolute() or '..' in relative.parts or ':' in str(relative):
        raise ValueError('Unsafe source filename: ' + row['frame_id'])
    result = (images / relative).resolve()
    if not result.is_relative_to(images.resolve()):
        raise ValueError('Source traversal: ' + row['frame_id'])
    return result


def preflight(report, step4_summary, step3_report, step3_summary, images):
    columns, rows = read_csv(report)
    if set(REQUIRED)-set(columns):
        raise ValueError('STEP4 columns missing: ' + ','.join(sorted(set(REQUIRED)-set(columns))))
    if set(FIELDS) & set(columns):
        raise ValueError('STEP4 input already contains STEP5 output fields; do not merge generations')
    summary = json.loads(step4_summary.read_text(encoding='utf-8-sig'))
    input_version = summary.get('step4_version')
    if input_version not in STEP4_INPUT_VERSIONS:
        raise ValueError('Wrong authoritative STEP4 version')
    if input_version == 'step4_pose_composition_v3' and any('step3_'+key not in columns for key in V3_POSE_FIELDS):
        raise ValueError('STEP4 v3 lacks preserved STEP3 pose evidence')
    if summary.get('output_csv_sha256') != sha256_file(report) or summary.get('total_rows') != len(rows):
        raise ValueError('STEP4 count/content differs from summary')
    if summary.get('statuses', {}).get('ERROR', 0):
        raise ValueError('Authoritative STEP4 contains ERROR; resolve upstream first')
    original = load_step3(step3_report, step3_summary)
    if summary.get('input_report_sha256') != sha256_file(step3_report) or \
            summary.get('input_summary_sha256') != sha256_file(step3_summary):
        raise ValueError('STEP4 was not produced from current STEP3 artifacts')
    old = {r['frame_id']: r for r in original}
    if len({r['frame_id'] for r in rows}) != len(rows) or set(old) != {r['frame_id'] for r in rows}:
        raise ValueError('STEP4 frame universe is not complete/unique/current')
    generations = {}
    eligible_count = 0
    for row in rows:
        frame = row['frame_id']
        if row['step4_version'] != input_version:
            raise ValueError('Mixed STEP4 version')
        for key, value in old[frame].items():
            # Only v3's explicitly replaced pose columns may differ. Verify their
            # original values through the mandatory step3_* lineage columns.
            if input_version == 'step4_pose_composition_v3' and key in V3_POSE_FIELDS:
                if row.get('step3_'+key) != value:
                    raise ValueError('STEP4 v3 changed preserved STEP3 pose: ' + frame + '/' + key)
            elif key not in ADDED_FIELDS and row.get(key) != value:
                raise ValueError('STEP4 changed inherited STEP3 field: ' + frame + '/' + key)
        kind = row['input_kind']
        if kind not in ('formal_video', 'supplemental_still'):
            raise ValueError('Unknown input_kind: ' + frame)
        # Formal and declared supplemental universes may have different generation IDs.
        generations.setdefault(kind, set()).add(row['dataset_generation_id'])
        if not re.fullmatch('[0-9a-fA-F]{64}', row['image_sha256']):
            raise ValueError('Missing/invalid image SHA256: ' + frame)
        if row['ranking_eligible'].lower() == 'true':
            eligible_count += 1
            ordering(row)  # finite score validated by the authoritative STEP3 loader
            if row['step4_status'] not in ('MEASURED', 'NOT_EVALUABLE'):
                raise ValueError('Unsupported eligible STEP4 status: ' + frame)
            if row['pose_bin'] not in POSE_BINS or row['face_scale_bin'] not in SCALE_BINS:
                raise ValueError('Unknown stored pose/scale label: ' + frame)
            if row['step4_status'] == 'MEASURED' and pose(row) is None:
                raise ValueError('MEASURED pose lacks finite yaw/pitch: ' + frame)
            if row['step4_status'] == 'NOT_EVALUABLE' and row['pose_bin'] != 'NOT_EVALUABLE':
                raise ValueError('Inconsistent missing-pose state: ' + frame)
            if kind == 'formal_video' and (not row['video_id'] or not row['temporal_index'].isdigit()):
                raise ValueError('Formal video lineage missing: ' + frame)
            box = geometry(row)
            if box is None:
                raise ValueError('Cannot safely recover persisted face bbox: ' + frame)
            coords = [float(v) for v in row['face_bbox'].split(',')]
            if any(v != int(v) for v in coords):
                raise ValueError('Noninteger bbox requires an unapproved crop convention: ' + frame)
            if not source_path(row, images).is_file():
                raise ValueError('Source image missing: ' + frame)
        elif row['step4_status'] != 'NOT_APPLICABLE_STEP3_FATAL':
            raise ValueError('STEP4 fatal status differs: ' + frame)
    if any(len(values) != 1 or not next(iter(values)) for values in generations.values()):
        raise ValueError('Mixed/empty generation within input kind')
    if summary.get('ranking_eligible_rows') != eligible_count:
        raise ValueError('STEP4 eligible-count mismatch')
    return columns, rows


def hash_sources(rows, images, limit=0):
    candidates = [r for r in rows if r['ranking_eligible'].lower() == 'true']
    if limit:
        candidates = candidates[:limit]
    hashes, errors = {}, {}
    for index, row in enumerate(candidates, 1):
        try:
            path = source_path(row, images)
            encoded = path.read_bytes()
            import hashlib
            if hashlib.sha256(encoded).hexdigest() != row['image_sha256'].lower():
                raise ValueError('Source SHA256 differs from stored generation')
            image = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError('Image decode failed')
            if image.shape[:2] != (int(row['height']), int(row['width'])):
                raise ValueError('Decoded image dimensions differ from persisted bbox domain')
            x, y, w, h = [int(float(v)) for v in row['face_bbox'].split(',')]
            crop = image[y:y+h, x:x+w]
            hashes[row['frame_id']] = {'global': compute_phash(image),
                                       'face': compute_phash(crop) if crop.size else None}
        except (OSError, ValueError, cv2.error) as exc:
            hashes.pop(row['frame_id'], None)
            errors[row['frame_id']] = str(exc)
        if index % 50 == 0 or index == len(candidates):
            print(f'Hashing {index}/{len(candidates)}', flush=True)
    return hashes, errors


def esc(value):
    return html.escape('' if value is None else str(value), quote=True)


def link(source, page):
    try:
        return quote(os.path.relpath(source, page.parent).replace('\\','/'), safe='/:')
    except ValueError:  # different Windows volumes
        return source.as_uri()


def document(title, content):
    return '<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+esc(title)+'''</title>
<style>body{font-family:system-ui;margin:24px;background:#f4f6fa;color:#17243a}table{border-collapse:collapse;margin:12px 0}th,td{border:1px solid #bbc6d5;padding:6px} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}.card{background:white;padding:12px;border-radius:8px;overflow-wrap:anywhere}img{width:100%;height:340px;object-fit:contain} .warn{background:#fff1cf;padding:10px}h2,h3{scroll-margin-top:20px}</style>
<body><h1>'''+esc(title)+'</h1>'+content+'</body></html>'


def table(headers, values):
    return '<table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in values)+'</tbody></table>'


def card(row, images, page, cluster_page=None):
    source = link(source_path(row, images), page)
    values = [(key, row.get(key)) for key in ('frame_id','video_id','source_id','input_kind','best_score','global_rank',
        'pose_bin','yaw','pitch','face_scale_bin','dedup_cluster_id','cluster_size','dedup_role',
        'global_phash_distance_to_representative','face_phash_distance_to_representative',
        'temporal_distance_to_representative','duplicate_evidence','cluster_chain_warning')]
    more = ''
    if row['dedup_role'] == 'REPRESENTATIVE':
        more = '<p>Duplicate alternatives: '+str(int(row['cluster_size'])-1)+'</p>'
        if cluster_page:
            more += '<a href="'+esc(link(cluster_page, page)+'#'+row['dedup_cluster_id'])+'">Cluster members / representative理由</a>'
    return '<article class="card" data-role="'+row['dedup_role']+'"><a href="'+esc(source)+'" target="_blank"><img loading="lazy" src="'+esc(source)+'" alt="'+esc(row['frame_id'])+'"></a>'+table(('項目','値'), values)+more+'</article>'


def galleries(rows, clusters, summary, cross, images, cluster_page, pose_page):
    cluster_body = '<p>Diagnostic clustering only. All members remain in the full CSV. Representative: best_score descending, global_rank ascending, frame_id ascending.</p>'
    for members in clusters:
        if len(members) < 2:
            continue
        rep = members[0]
        cluster_body += '<section id="'+rep['dedup_cluster_id']+'"><h2>'+rep['dedup_cluster_id']+'</h2><p>Evidence: '+esc(rep['cluster_evidence_types'])+'; maximum pose spread: '+esc(rep['cluster_max_pose_spread'])+'</p>'
        if rep['cluster_chain_warning'] == 'true':
            cluster_body += '<p class="warn">SINGLE_LINK_CHAIN_WARNING: confirmed pair edges do not establish homogeneous endpoints.</p>'
        cluster_body += '<div class="grid">'+''.join(card(r, images, cluster_page) for r in members)+'</div></section>'
    pose_body = '<p>This STEP5 review shows what pose/composition diversity remains after deduplication. It is NOT the final LoRA angle quota or final dataset selection. STEP7 will decide coverage/balance using this measured pool.</p>'
    pose_body += '<p>顔の面積から得たface_scale_binであり、体や脚が見えることの認定ではありません。PoseはSTEP4保存値です。</p>'
    for label, values in (('TABLE A — Before STEP5 (ranking-eligible)', summary['before']),
                          ('TABLE B — After STEP5 (UNIQUE + REPRESENTATIVE)', summary['after'])):
        pose_body += '<h2>'+label+'</h2>'+table(('分類','Count'), [(p,values['pose'][p]) for p in POSE_BINS]+
                                             [(s,values['face_scale'][s]) for s in SCALE_BINS])
    pose_body += '<h2>After: pose × face scale</h2>'+table(('Pose',*SCALE_BINS),
        [(p,*(next(r['after_count'] for r in cross if r['pose_bin']==p and r['face_scale_bin']==s) for s in SCALE_BINS)) for p in POSE_BINS])
    pose_body += '<h2>Pose retention — Profileを重点確認</h2><p>閾値は設けず、減少があるクラスを確認用にhighlightします。自動quota/Rejectではありません。</p>'+table(
        ('Pose','Before','After','Retention','Status','Rare profile'), [(p,*(summary['pose_retention'][p][k] for k in
          ('before_count','after_count','retention_ratio','status','rare_pose_context'))) for p in POSE_BINS])
    pool = [r for r in rows if r['dedup_role'] in POOL_ROLES]
    for p in POSE_BINS:
        pose_body += '<h2>'+p+'</h2>'
        for s in SCALE_BINS:
            members = sorted((r for r in pool if r['pose_bin']==p and r['face_scale_bin']==s), key=ordering)
            pose_body += '<h3>'+s+' ('+str(len(members))+')</h3><div class="grid">'+''.join(
                card(r, images, pose_page, cluster_page) for r in members)+'</div>'
    return document('STEP5 duplicate cluster review', cluster_body), document('STEP5 representative pose review', pose_body)


def markdown(summary):
    paths = summary['outputs']
    page = Path(paths['markdown'])
    return '# STEP5 Deduplication v2 Summary\n\n'+\
        'Clusters annotate redundancy, not image quality or final training selection.\n\n'+\
        'Pose/scale before includes every ranking-eligible row; after is UNIQUE + REPRESENTATIVE.\n'+\
        'POSE_RETENTION_WARNING highlights any count reduction without a magnitude cutoff.\n\n'+\
        'See [pose gallery]('+link(Path(paths['pose_review']),page)+') and [cluster review]('+link(Path(paths['review_html']),page)+').\n\n'+\
        '```json\n'+json.dumps(summary, ensure_ascii=False, indent=2)+'\n```\n'


def validate_targets(targets, inputs, images):
    all_paths = [*inputs, *targets.values()]
    if len({p.resolve() for p in all_paths}) != len(all_paths):
        raise ValueError('Input/output report paths must be distinct')
    suffixes = dict(output_csv='.csv',summary='.json',markdown='.md',review_html='.html',pose_review='.html',pose_summary='.csv')
    for key, path in targets.items():
        resolved = path.resolve()
        if path.suffix.lower() != suffixes[key] or path.name.startswith(('step1_', 'step2_', 'step3_', 'step4_')):
            raise ValueError('Unsafe STEP5 output name: ' + str(path))
        if resolved.is_relative_to(images.resolve()) or any(resolved.is_relative_to(ROOT/p) for p in
                ('scripts','bat','config','knowledge','history','tests','.agents','work','input')):
            raise ValueError('Output cannot overwrite source/code/history: ' + str(path))


def authoritative_input_versions(rows, input_hashes):
    """Read versions from hash-bound input summaries, never output-version literals."""
    ranking_versions, pose_versions = [], []
    for name, expected_hash in input_hashes.items():
        path = Path(name)
        if path.suffix.lower() != '.json':
            continue
        if sha256_file(path) != expected_hash:
            raise ValueError('Input metadata changed before summary generation')
        metadata = json.loads(path.read_text(encoding='utf-8-sig'))
        if 'step4_version' in metadata:
            pose_versions.append(metadata['step4_version'])
        elif 'version' in metadata and 'ranking_sha256' in metadata:
            ranking_versions.append(metadata['version'])
    if len(ranking_versions) != 1 or len(pose_versions) != 1:
        raise ValueError('Unique authoritative STEP3/4 version metadata required')
    if {r['ranking_version'] for r in rows} != set(ranking_versions) or \
            {r['step4_version'] for r in rows} != set(pose_versions):
        raise ValueError('Input summary versions disagree with dataset rows')
    return ranking_versions + pose_versions


def publish(rows, hashes, errors, rules, targets, images, input_hashes, partial=False):
    input_versions = authoritative_input_versions(rows, input_hashes)
    outputs, clusters, edges = annotate(rows, hashes, errors, rules, partial)
    assert len(outputs) == len(rows)
    assert all(all(out[k] == v for k,v in original.items()) for out,original in zip(outputs,rows))
    summary, cross = summarize(outputs, clusters, edges, partial)
    summary.update(rules=rules,input_hashes=input_hashes, input_versions=input_versions,
                   dataset_generations_by_kind={kind:sorted({r['dataset_generation_id'] for r in rows if r['input_kind']==kind})
                                                for kind in sorted({r['input_kind'] for r in rows})},
                   outputs={key:str(value) for key,value in targets.items()},
                   phash_kernel='legacy 64-bit DCT, 32x32 AREA, upper-left8x8, median(dct[1:,:]) unchanged')
    if partial or errors:
        directory = targets['output_csv'].parent/'audit'/(VERSION+'_'+uuid.uuid4().hex)
        targets = {key: directory/path.name for key,path in targets.items()}
        summary['outputs'] = {key:str(value) for key,value in targets.items()}
    cluster_html, pose_html = galleries(outputs, clusters, summary, cross, images, targets['review_html'], targets['pose_review'])
    targets['output_csv'].parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.step5_stage_', dir=targets['output_csv'].parent) as temporary:
        stage = Path(temporary)
        staged = {key:stage/(key+path.suffix) for key,path in targets.items()}
        columns = list(dict.fromkeys(k for r in outputs for k in r))
        write_csv_atomic(staged['output_csv'], columns, outputs)
        write_csv_atomic(staged['pose_summary'], list(cross[0]), cross)
        staged['review_html'].write_text(cluster_html, encoding='utf-8')
        staged['pose_review'].write_text(pose_html, encoding='utf-8')
        summary['artifact_sha256'] = {key:sha256_file(path) for key,path in staged.items() if key not in ('summary','markdown')}
        staged['markdown'].write_text(markdown(summary), encoding='utf-8')
        summary['artifact_sha256']['markdown'] = sha256_file(staged['markdown'])
        write_json_atomic(staged['summary'], summary)  # completion marker, last to publish
        for path,digest in input_hashes.items():
            if sha256_file(Path(path)) != digest:
                raise ValueError('Upstream report changed during STEP5')
        existing = {key:path for key,path in targets.items() if path.exists()}
        backup = {}
        if existing:
            archive = targets['output_csv'].parent/'bkup'/(VERSION+'_'+uuid.uuid4().hex)
            archive.mkdir(parents=True,exist_ok=False)
            for key,path in existing.items():
                saved = archive/(key+path.suffix)
                shutil.copy2(path,saved)
                if sha256_file(path) != sha256_file(saved):
                    raise ValueError('Historical STEP5 archive mismatch')
                backup[key] = saved
            write_json_atomic(archive/'MANIFEST.json',dict(files=[dict(path=str(existing[k]),backup=str(v),sha256=sha256_file(v)) for k,v in backup.items()]))
        changed = []
        try:
            for key in (*[k for k in OUTPUT_KEYS if k != 'summary'], 'summary'):
                path = targets[key]
                path.parent.mkdir(parents=True,exist_ok=True)
                # A temp file on the destination volume preserves atomic replace.
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    temp = Path(handle.name)
                    handle.write(staged[key].read_bytes())
                try:
                    os.replace(temp,path)
                    changed.append(key)
                finally:
                    temp.unlink(missing_ok=True)
        except OSError:
            for key in reversed(changed):
                path = targets[key]
                if key in backup:
                    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as handle:
                        restore = Path(handle.name)
                        handle.write(backup[key].read_bytes())
                    try:
                        os.replace(restore,path)
                    finally:
                        restore.unlink(missing_ok=True)
                else:
                    path.unlink(missing_ok=True)
            raise
    return summary


def main():
    config = load_for_cli()
    section = get_section(config,'step5_dedup')
    parser = argparse.ArgumentParser(description='STEP5 v2 duplicate clustering; no quality rescoring, deletion or selection')
    for name,default in PATH_DEFAULTS.items():
        parser.add_argument('--'+name.replace('_','-'),type=Path,default=resolve_config_path(default,config))
    parser.add_argument('--images',type=Path,default=resolve_config_path(config['paths']['raw_frames_dir'],config))
    for key in RULE_KEYS:
        parser.add_argument('--'+key.replace('_','-'),type=int if key in ('phash_threshold','temporal_phash_threshold','time_window') else float)
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--preflight-only',action='store_true',help='Read/check metadata and source existence; no image decoding/hashing/output')
    configure_parser(parser,config,'step5_dedup',paths={'images':'raw_frames_dir'})
    args = parser.parse_args()
    if section.get('version') != VERSION:
        raise ValueError('Config must explicitly declare '+VERSION)
    rules = {key:getattr(args,key) for key in RULE_KEYS}
    if any(v is None or not np.isfinite(v) or v < 0 for v in rules.values()) or args.limit < 0:
        raise ValueError('Missing/invalid explicit STEP5 SSOT rule')
    if rules['phash_threshold'] > 64 or rules['temporal_phash_threshold'] > 64 or \
            rules['tight_angle_threshold'] > rules['angle_threshold']:
        raise ValueError('Inconsistent STEP5 thresholds')
    targets = {key:getattr(args,key) for key in OUTPUT_KEYS}
    inputs = [args.report,args.step4_summary,args.step3_report,args.step3_summary]
    validate_targets(targets, inputs, args.images)
    print(VERSION, '\nInput:', args.report, '\nOutput:', args.output_csv, flush=True)
    with manifest_lock(args.step3_report.parent/'.step3_best_operation.lock'), \
         manifest_lock(args.report.parent/'.step4_pose_operation.lock'), \
         manifest_lock(args.output_csv.parent/'.step5_dedup_operation.lock'):
        columns,rows = preflight(*inputs,args.images)
        if args.preflight_only:
            print('Preflight PASS. Rows:',len(rows),'No images decoded; no outputs published.')
            return 0
        input_hashes = {str(path):sha256_file(path) for path in inputs}
        hashes,errors = hash_sources(rows,args.images,args.limit)
        summary = publish(rows,hashes,errors,rules,targets,args.images,input_hashes,args.limit>0)
    print(summary['publication_status'], 'roles:',summary['roles'], '\nSummary:',summary['outputs']['markdown'])
    return 1 if errors else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('[ERROR] '+str(exc),file=sys.stderr)
        sys.exit(1)
