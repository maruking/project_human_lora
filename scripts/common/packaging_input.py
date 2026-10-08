"""Authoritative STEP8-selected packaging inputs; no directory enumeration."""
from pathlib import Path
from common.candidate_selection_v2 import priority
from step5_dedup_v2 import read_csv,source_path,sha256_file as digest

POSE_MAP={'FRONTAL':'FRONT','THREE_QUARTER_LEFT':'LEFT_3Q','THREE_QUARTER_RIGHT':'RIGHT_3Q',
    'PROFILE_LEFT':'LEFT_PROFILE','PROFILE_RIGHT':'RIGHT_PROFILE','NOT_EVALUABLE':'EXTREME_POSE'}
RESTORATION_STATUSES={'safely_restored','untouched_raw_camera','rollback_to_original'}


def verified_inputs(selected,images,step9_report,restored_dir):
    if not selected or len({r['frame_id'] for r in selected})!=len(selected):raise ValueError('Invalid accepted identity set')
    paths=[];pins={};accepted={r['frame_id']:r for r in selected}
    for row in selected:
        if row.get('step8_decision')!='STEP8_ACCEPT':raise ValueError('Only STEP8_ACCEPT may be packaged')
        path=source_path(row,images)
        if not path.is_file() or digest(path)!=row['image_sha256']:raise ValueError('Original source hash mismatch: '+row['frame_id'])
        pins[str(path)]=row['image_sha256']
    restoration={}
    if step9_report.exists():
        pins[str(step9_report)]=digest(step9_report)
        columns,rows=read_csv(step9_report)
        required={'frame_id','image_sha256','dataset_generation_id','step8_review_session_id','restoration_status','restored_path','restored_image_sha256'}
        if required-set(columns):raise ValueError('STEP9 report exists but formal current lineage/hash evidence is missing: '+','.join(sorted(required-set(columns))))
        if len({r['frame_id'] for r in rows})!=len(rows) or {r['frame_id'] for r in rows}!=set(accepted):
            raise ValueError('STEP9 frame identity set differs from STEP8_ACCEPT')
        restoration={r['frame_id']:r for r in rows}
    for row in sorted(selected,key=priority):
        original=source_path(row,images);record=restoration.get(row['frame_id'])
        path=original;status='SKIPPED_NOT_NEEDED';kind='STEP8_ORIGINAL'
        if record:
            for key in ('image_sha256','dataset_generation_id','step8_review_session_id'):
                if record[key]!=row[key]:raise ValueError('Stale STEP9 source/generation/session: '+row['frame_id'])
            if record['restoration_status'] not in RESTORATION_STATUSES:raise ValueError('Nonfinal STEP9 restoration status')
            relative=Path(record['restored_path'].replace('\\','/'))
            if relative.is_absolute() or '..' in relative.parts or ':' in str(relative):raise ValueError('Unsafe restored source path')
            path=(restored_dir/relative).resolve()
            if not path.is_relative_to(restored_dir.resolve()):raise ValueError('Restored path escapes configured root')
            if not path.is_file() or digest(path)!=record['restored_image_sha256']:raise ValueError('Restored image hash mismatch: '+row['frame_id'])
            status=record['restoration_status'];kind='STEP9_RESTORATION'
        value=digest(path);pins[str(path)]=value
        paths.append(dict(row,source_path=str(path),original_source_path=str(original),packaging_image_sha256=value,
            packaging_input_kind=kind,restoration_status=status,
            shot_type=row['face_scale_bin'],pose_bucket=row.get('pose_bucket') or POSE_MAP.get(row['pose_bin'],'EXTREME_POSE')))
    if len(paths)!=len(selected) or {r['frame_id'] for r in paths}!=set(accepted):raise ValueError('Packaging input lost accepted rows')
    return paths,pins


def load_inputs(config,step9_report,restored_dir):
    from step8_folder_review import load_step9_selection,paths_for
    _,paths,images=paths_for(config)
    pins={str(paths[k]):digest(paths[k]) for k in ('selection_csv','summary','manifest','preparation_summary')}
    selected=load_step9_selection(config)
    rows,source_pins=verified_inputs(selected,images,step9_report,restored_dir)
    pins.update(source_pins)
    return rows,pins
