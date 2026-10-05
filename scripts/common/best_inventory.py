"""Exact STEP2 formal/supplemental inventory with STEP1 content validation."""
import csv
import json
from pathlib import Path
from common.step3_audit import validate_input
from common.video_manifest import sha256_file


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def assemble(formal,stills,generation,supplemental,formal_hashes):
    expected_stills=(supplemental or {}).get('files',{})
    if {r['filename'] for r in stills}!=set(expected_stills):raise ValueError('STEP2 supplemental report inventory mismatch')
    result=[]
    for kind,rows,digest,hashes in (('formal_video',formal,generation['sha256'],formal_hashes),
                                   ('supplemental_still',stills,(supplemental or {}).get('sha256',''),expected_stills)):
        for original in rows:
            row=dict(original);filename=row['filename']
            if row.get('processing_status',row.get('status')) not in (None,'','MEASURED','measured','PASS','success','ok'):
                raise ValueError('Unmeasured STEP2 row: '+filename)
            if filename not in hashes:raise ValueError('Missing image checksum: '+filename)
            video=row.get('video_id','') if kind=='formal_video' else ''
            row.update(frame_id=row.get('frame_id') or filename,filename=filename,input_kind=kind,video_id=video,
                       source_id=video if video else 'still:'+hashes[filename],
                       dataset_generation_id=digest,image_sha256=hashes[filename])
            result.append(row)
    if len({r['frame_id'] for r in result})!=len(result):raise ValueError('Duplicate combined frame_id')
    return result


def load_inventory(reports,raw,manifests):
    formal_path=reports/'step2_dataset_report.csv'
    _,generation,_=validate_input(formal_path,raw,manifests)
    summary=json.loads((reports/'step2_summary.json').read_text(encoding='utf-8-sig'))
    supplemental=summary.get('supplemental_input_generation')
    formal=csv_rows(formal_path)
    stills=csv_rows(reports/'step2_supplemental_report.csv') if supplemental else []
    hashes={}
    for video in sorted({r['video_id'] for r in formal}):
        meta=json.loads((raw/video/'.extraction_metadata.json').read_text(encoding='utf-8-sig'))
        hashes.update({video+'/'+f['name']:f['sha256'] for f in meta['frames']})
    rows=assemble(formal,stills,generation,supplemental,hashes)
    snapshot={p.name:sha256_file(p) for p in (formal_path,reports/'step2_summary.json',
                  *((reports/'step2_supplemental_report.csv',) if supplemental else ()))}
    return rows,snapshot
