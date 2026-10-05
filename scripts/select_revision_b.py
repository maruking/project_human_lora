"""STEP7 Revision B: generation-safe CSV joins and report-only selection."""
from common.step3_review import is_review_copy, require_source

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile

from common.config import load_for_cli, get_section, configure_parser
from common.revision_b import select
from common.video_manifest import sha256_file


def read_csv(path):
    content = path.read_bytes()
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
        raise ValueError(f'Invalid CSV header: {path}')
    result = {}
    for row in reader:
        name = row.get('frame_id') or row.get('filename')
        if not name or name in result or row.get('filename',name) != name or None in row:
            raise ValueError(f'Missing, duplicate or conflicting frame identity: {path}')
        parts = Path(name.replace('\\','/'))
        if parts.is_absolute() or '..' in parts.parts or ':' in name or '\\' in name:
            raise ValueError('Frame identity must be a portable input-relative path')
        result[name]=dict(row,frame_id=name,filename=name)
    if not result: raise ValueError(f'Empty input: {path}')
    return result,hashlib.sha256(content).hexdigest()


def load_inputs(args, config):
    """Pin current inventory and reject incomplete/stale formal downstream reports."""
    fingerprints = {}
    def table(path):
        rows,digest = read_csv(path); fingerprints[str(path)]=digest; return rows
    def document(path):
        content=path.read_bytes();fingerprints[str(path)]=hashlib.sha256(content).hexdigest()
        return json.loads(content.decode('utf-8-sig'))
    summary2=document(args.step2_summary)
    if summary2['status']!='PASS': raise ValueError('STEP2 is not PASS')
    step1=document(args.manifests/'step1_summary.json')
    if step1['status']!='PASS' or step1['frames_extracted'] != summary2['input_generation']['frame_count']:
        raise ValueError('STEP1/STEP2 count or status mismatch')
    formal=table(args.universe)
    hashes={};fingerprint=[]
    with (args.manifests/'video_manifest.csv').open(encoding='utf-8-sig',newline='') as handle:
        manifest=list(csv.DictReader(handle))
    fingerprints[str(args.manifests/'video_manifest.csv')]=sha256_file(args.manifests/'video_manifest.csv')
    if len({r['video_id'] for r in manifest}) != len(manifest): raise ValueError('Duplicate manifest video IDs')
    for source in manifest:
        video=source['video_id'];metadata=document(args.images/video/'.extraction_metadata.json')
        policy=metadata['policy']
        if metadata['status']!='PASS' or policy['source_sha256']!=source['sha256']:
            raise ValueError('STEP1 source metadata mismatch')
        trace={key:policy[key] for key in ('extraction_policy_version','sample_fps_requested','sample_fps_effective')}
        for frame in sorted(metadata['frames'],key=lambda f:f['name']):
            name=video+'/'+frame['name'];hashes[name]=frame['sha256']
            fingerprint.append([name,frame['sha256'],policy['source_sha256'],trace])
    # STEP2 preflight orders videos naturally and preserves natural frame order.
    from common.video_manifest import natural_key
    fingerprint.sort(key=lambda item:tuple(natural_key(Path(part)) for part in Path(item[0]).parts))
    generation=hashlib.sha256(json.dumps(fingerprint,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if generation != summary2['input_generation']['sha256'] or set(formal)!=set(hashes):
        raise ValueError('STEP2 formal universe differs from current STEP1 generation')
    inventory=set(p.relative_to(args.images).as_posix() for p in args.images.rglob('*')
                  if not is_review_copy(p) and p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.webp'))
    supplemental=summary2.get('supplemental_input_generation',{}).get('files',{})
    if inventory != set(formal)|set(supplemental): raise ValueError('Raw inventory differs from current STEP2 universe')
    hashes.update(supplemental)
    for name,digest in supplemental.items():
        if sha256_file(args.images/name)!=digest: raise ValueError('Supplemental content changed after STEP2')
    groups_path=args.selection_groups
    if groups_path is None:
        pointer=document(args.selection_pointer)
        groups_path=Path(pointer['directory'])/'selection_groups.csv'
    groups=table(groups_path)
    if set(groups)!=set(hashes): raise ValueError('A/B/C sidecar must cover every current formal and supplemental image exactly')
    for name,row in groups.items():
        if row.get('image_sha256')!=hashes[name]: raise ValueError('A/B/C sidecar image hash differs from current generation')
        if name in formal and row.get('dataset_generation_id')!=generation: raise ValueError('Stale A/B/C formal generation')
    step3=table(args.step3)
    summary3=document(args.step3.with_name('step3_summary.json'))
    if (summary3['status']!='PASS' or summary3.get('partial') or summary3['input_generation']['sha256']!=generation
            or summary3['step3_csv_sha256']!=fingerprints[str(args.step3)]
            or summary3['step2_csv_sha256']!=fingerprints[str(args.universe)] or set(step3)!=set(formal)):
        raise ValueError('STEP3 formal generation/provenance mismatch')
    downstream=[('pose',table(args.pose)),('duplicate',table(args.duplicates))]
    identity_available=args.identity is not None and args.identity.is_file()
    if identity_available: downstream.append(('identity',table(args.identity)))
    for label,records in downstream:
        if not set(formal).issubset(records) or not set(records).issubset(groups):
            raise ValueError(f'{label}: incomplete formal audit or stale/extra identities')
        for name,row in records.items():
            anchor=step3.get(name)
            if anchor:
                for key,value in anchor.items():
                    if key!='step_name' and row.get(key)!=value:
                        raise ValueError(f'{label}: retained STEP3 evidence differs: {name} / {key}')
            elif row.get('image_sha256')!=hashes[name] or row.get('dataset_generation_id')!=groups[name].get('dataset_generation_id'):
                raise ValueError(f'{label}: supplemental lineage missing or stale')
    for (previous_label,previous),(label,records) in zip(downstream,downstream[1:]):
        for name,anchor in previous.items():
            if name not in records:
                if name in formal: raise ValueError(f'{label}: missing preceding formal record')
                continue
            if any(records[name].get(key)!=value for key,value in anchor.items() if key!='step_name'):
                raise ValueError(f'{label}: retained {previous_label} evidence differs: {name}')
    merged=[]
    for name,group in groups.items():
        row=dict(step3.get(name,{}))
        for _,records in downstream:
            row.update(records.get(name,{}))
        # Selection authority cannot rewrite machine identity/pose/duplicate evidence.
        for key,value in group.items():
            selection_field = key.startswith(('selection_','human_','official_')) or key in (
                'reserve_use_allowed','dataset_generation_id','image_sha256','input_kind','frame_id','filename')
            if not selection_field and key in row and row[key]!=value:
                raise ValueError(f'Selection sidecar conflicts with retained machine evidence: {name} / {key}')
            row[key]=value
        if name in formal:
            for field in ('video_id','temporal_index','relative_path','sample_fps_effective'):
                if field in formal[name]: row[field]=formal[name][field]
        row['subject_id']=get_section(config,'project').get('subject_name','UNSPECIFIED')
        row['image_sha256']=hashes[name]
        merged.append(row)
    return merged,fingerprints,identity_available


def csv_bytes(rows,fields):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader();writer.writerows(rows)
    return ('\ufeff'+stream.getvalue()).encode('utf-8')


def artifacts(rows,summary,settings,fingerprints):
    fields=sorted(set().union(*(set(row) for row in rows)))
    selected=sorted((r for r in rows if r['selected']=='yes'),key=lambda r:int(r['selection_rank']))
    reserve=[r for r in rows if r['final_selection_role'] in ('RESERVE','REVIEW_PENDING_RESERVE')]
    lines=['# STEP7 Revision B Selection Summary','',f"Status: {summary['status']}",
           'Candidate proposal only. STEP8 Human Review remains required; no training suitability guarantee.',
           '',f"All input images: {summary['total_images']}; usable A+B candidates: {summary['total_candidates']}",
           f"A/B/C counts: {json.dumps(summary['group_counts'],sort_keys=True)}",
           f"Selected: {summary['selected_count']}; B promotions: {summary['B_promotions']}; reserves: {len(reserve)}",
           f"Configured minimum / target / maximum: {settings['min_count']} / {settings['target_count']} / {settings['max_count']}",
           f"Identity safety: {summary['identity_safety']}",
           f"Duplicate alternatives pruned: {summary['duplicate_pruned']}",
           f"Remaining shortages: {json.dumps(summary['remaining_shortages'],sort_keys=True)}",'',
           'B promotions use confirmed reserves only; pending B remains B and cannot be automatically promoted.',
           'Unknown expression needs human confirmation. Optional body visibility fields are retained without inference.',
           'Missing pose/dedup evidence excludes a candidate with a reason; C is never selected.','']
    for key,distribution in summary['distributions'].items():
        lines += [f'## {key}','', '| Bucket | Selected |','| --- | ---: |']
        lines += [f'| {label} | {count} |' for label,count in sorted(distribution.items())]
        lines += ['']
    lines += ['## Selection settings','', '```json',json.dumps(settings,sort_keys=True,indent=2),'```','',
              '## Input report fingerprints','']+[f'- {Path(path).name}: `{digest}`' for path,digest in sorted(fingerprints.items())]
    return {'step7_candidate_selection.csv':csv_bytes(rows,fields),
            'step7_final_selected_35_45.csv':csv_bytes(selected,fields),
            'step7_reserve_candidates.csv':csv_bytes(reserve,fields),
            'STEP7_SELECTION_SUMMARY.md':('\n'.join(lines)+'\n').encode('utf-8')}


def publish(output,contents):
    """Immutable audit snapshot plus rollback of ordinary multi-file publication errors."""
    output.mkdir(parents=True,exist_ok=True)
    signature=hashlib.sha256(b''.join(name.encode()+body for name,body in sorted(contents.items()))).hexdigest()
    run=output/'step7_revision_b_runs'/signature;run.mkdir(parents=True,exist_ok=True)
    for name,body in contents.items():
        path=run/name
        if path.exists() and path.read_bytes()!=body: raise ValueError('Immutable selection run mismatch')
        if not path.exists(): path.write_bytes(body)
    with tempfile.TemporaryDirectory(prefix='.step7_stage_',dir=output) as folder:
        previous={};replaced=[]
        for name in contents:
            dest=output/name;previous[name]=dest.read_bytes() if dest.exists() else None
        # Preserve historical active bytes without relocating reports.
        if any(body is not None for body in previous.values()):
            archive=Path(tempfile.mkdtemp(prefix='previous_',dir=output/'step7_revision_b_runs'))
            for name,body in previous.items():
                if body is not None: (archive/name).write_bytes(body)
        try:
            for name,body in contents.items():
                staged=Path(folder)/name;staged.write_bytes(body);os.replace(staged,output/name);replaced.append(name)
        except OSError:
            for name in reversed(replaced):
                if previous[name] is None: (output/name).unlink(missing_ok=True)
                else: (output/name).write_bytes(previous[name])
            raise
    return run


def main():
    config=load_for_cli();settings=get_section(config,'step7_revision_b')
    parser=argparse.ArgumentParser(description='STEP7 Revision B: A/B/C report-only selection; no inference or image copying')
    parser.add_argument('--config',type=Path)
    for name in ('selection-groups','selection-pointer','universe','step2-summary','step3','pose','duplicates','identity','output-dir','images','manifests'):
        parser.add_argument('--'+name,type=Path,default=None)
    parser.add_argument('--target-count',type=int,default=None)
    configure_parser(parser,config,'step7_revision_b',paths={'images':'raw_frames_dir','manifests':'manifests_dir','output_dir':'reports_dir'})
    args=parser.parse_args()
    try:
        if not settings: raise ValueError('Missing step7_revision_b SSOT settings; use updated config example')
        settings=dict(settings)
        if args.target_count is not None: settings['target_count']=args.target_count
        for key in ('universe','step2_summary','step3','pose','duplicates','selection_pointer'):
            if getattr(args,key) is None: raise ValueError(f'Missing configured input: {key}')
        if args.images is None or args.manifests is None or args.output_dir is None: raise ValueError('Missing shared paths')
        if args.output_dir.is_relative_to(args.images): raise ValueError('Output must be outside raw input')
        print('STEP7 Revision B: report-only selection; no image copies or downstream processing.',flush=True)
        rows,pins,identity_available=load_inputs(args,config)
        audit,summary=select(rows,settings,get_section(config,'step4_pose'),identity_available)
        if {r['frame_id'] for r in audit}!={r['frame_id'] for r in rows} or len(audit)!=len(rows): raise ValueError('Full audit coverage changed')
        for row in audit:
            if row['selected']=='yes' and sha256_file(args.images/row['filename'])!=row['image_sha256']:
                raise ValueError('Selected image content differs from current generation')
        for path,digest in pins.items():
            if sha256_file(Path(path))!=digest: raise ValueError('Input evidence changed during selection')
        destinations={args.output_dir/name for name in ('step7_candidate_selection.csv','step7_final_selected_35_45.csv','step7_reserve_candidates.csv','STEP7_SELECTION_SUMMARY.md')}
        if destinations & {Path(path) for path in pins}: raise ValueError('Output overlaps input evidence')
        run=publish(args.output_dir,artifacts(audit,summary,settings,pins))
        print(f"Selected={summary['selected_count']}; B promotions={summary['B_promotions']}; status={summary['status']}; audit={run}")
        return 2 if summary['remaining_shortages'] else 0
    except (OSError,ValueError,KeyError,csv.Error) as exc:
        print(f'STEP7 FAIL: {exc}',file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
