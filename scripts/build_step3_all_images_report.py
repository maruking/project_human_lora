"""Complete review listing: recorded STEP3 video results plus declared stills.

Stills without a same-generation STEP3 result remain explicitly NOT_EVALUATED.
No inference, A/B/C assignment or inferred acceptance occurs here.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from common.config import load_config, resolve_config_path
from common.step3_review import review_roots, require_source
from common.video_manifest import write_csv_atomic, write_json_atomic


def read_csv(path):
    data=path.read_bytes()
    rows=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    if len({r['filename'] for r in rows}) != len(rows):
        raise ValueError('Duplicate image identities')
    return rows,hashlib.sha256(data).hexdigest()


def combined_rows(formal, supplemental, formal_generation, supplemental_generation, root):
    if {r['filename'] for r in formal} & {r['filename'] for r in supplemental}:
        raise ValueError('Formal/supplemental identities overlap')
    result=[]
    for kind,rows,generation in (('VIDEO_FRAME',formal,formal_generation),
                                 ('SUPPLEMENTAL_STILL',supplemental,supplemental_generation)):
        for source in rows:
            row=dict(source)
            row.update(input_kind=kind,dataset_generation_id=generation)
            if kind=='SUPPLEMENTAL_STILL':
                row.update(step3_evaluation_status='NOT_EVALUATED',face_eligible='',
                           face_gate_status='not_evaluated',face_gate_reason='step3_not_evaluated',
                           face_gate_category='REVIEW_NOT_EVALUATED',diagnostic_state='NOT_EVALUATED')
            else:
                row['step3_evaluation_status']='EVALUATED'
            name=row['filename'];relative=Path(name);target=(root/relative).resolve()
            if relative.is_absolute() or '..' in relative.parts or not target.is_relative_to(root):
                raise ValueError('Image link escapes current input')
            require_source(target)
            row['image_path']=str(target)
            row['image_open']='=HYPERLINK("'+str(target).replace('"','""')+'","画像を開く")'
            result.append(row)
    return result


def build(config):
    reports=review_roots(config)[0].parent
    raw=resolve_config_path(config['paths']['raw_frames_dir'],config).resolve()
    require_source(raw)
    summary=json.loads((reports/'step3_summary.json').read_text(encoding='utf-8-sig'))
    step2_summary=json.loads((reports/'step2_summary.json').read_text(encoding='utf-8-sig'))
    formal,formal_hash=read_csv(reports/'step3_dataset_report.csv')
    step2,step2_hash=read_csv(reports/'step2_dataset_report.csv')
    if (summary['status']!='PASS' or summary['partial'] or summary['step3_csv_sha256']!=formal_hash or
        summary['step2_csv_sha256']!=step2_hash or summary['input_generation']!=step2_summary['input_generation'] or
        {r['filename'] for r in formal}!={r['filename'] for r in step2} or
        len(formal)!=summary['input_generation']['frame_count']):
        raise ValueError('Current formal STEP2/STEP3 results are not consistent')
    recorded=step2_summary.get('supplemental_input_generation')
    stills,stills_hash=read_csv(reports/'step2_supplemental_report.csv') if recorded else ([],None)
    if recorded:
        if {r['filename'] for r in stills}!=set(recorded['files']) or len(stills)!=recorded['image_count']:
            raise ValueError('Supplemental STEP2/receipt identities mismatch')
        directory=Path(recorded['directory']).resolve();require_source(directory)
        actual={p.relative_to(raw).as_posix() for p in directory.rglob('*')
                if p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.webp')}
        if actual!=set(recorded['files']):raise ValueError('Supplemental inventory changed since STEP2')
        for row in stills:
            path=(raw/row['filename']).resolve();require_source(path)
            if not path.is_relative_to(directory) or hashlib.sha256(path.read_bytes()).hexdigest()!=recorded['files'][row['filename']]:
                raise ValueError('Supplemental pixels changed since STEP2')
    rows=combined_rows(formal,stills,summary['input_generation']['sha256'],recorded['sha256'] if recorded else '',raw)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    output=reports/'step3_all_images_report.csv'
    write_csv_atomic(output,fields,[{k:r.get(k,'') for k in fields} for r in rows])
    receipt=dict(status='COMPLETE_LIST_WITH_PENDING_EVALUATION' if stills else 'COMPLETE_LIST',
                 total_images=len(rows),formal_images=len(formal),supplemental_images=len(stills),
                 review_counts=dict(Counter(r['diagnostic_state'] for r in rows)),
                 step3_csv_sha256=formal_hash,step2_supplemental_csv_sha256=stills_hash,
                 all_images_csv_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                 official_results_changed=False,inference_executed=False,selection_state_changed=False)
    write_json_atomic(reports/'step3_all_images_summary.json',receipt)
    print(json.dumps(receipt,ensure_ascii=True),flush=True)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path)
    args=parser.parse_args()
    build(load_config(args.config))
