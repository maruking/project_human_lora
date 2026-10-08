"""STEP8 prepare/collect folder review; never auto-select or run STEP9 inference."""
import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import sys
import uuid

from common.config import load_for_cli,get_section,resolve_config_path
from common.video_manifest import manifest_lock
from common.folder_review import (VERSION,EXTRA,POSES,validate_settings,safe_root,manifest_rows,
    stage_review,install_review,accepted_ids,selection_rows,no_links,pose_folder)
from common.candidate_selection_v22 import VERSION as STEP7_VERSION,FIELDS,review_scope_allowed
from step7_candidate_selection_v22 import preflight as upstream_preflight,review_exclusions,csv_bytes
from step5_dedup_v2 import read_csv,sha256_file as digest,source_path
from step6_identity_v2 import publish,ensure_unchanged

ROOT=Path(__file__).resolve().parents[1]
PATH_KEYS=('review_root','candidates_csv','full_csv','step7_summary','manifest','preparation_summary','selection_csv','summary','markdown')


def paths_for(config):
    cfg=get_section(config,'step8_folder_review');validate_settings(cfg)
    paths={k:resolve_config_path(cfg[k],config) for k in PATH_KEYS}
    images=resolve_config_path(config['paths']['raw_frames_dir'],config)
    safe_root(paths['review_root'],images,ROOT)
    if len({p.resolve() for p in paths.values()})!=len(paths):raise ValueError('STEP8 paths must be distinct')
    for key in ('manifest','preparation_summary','selection_csv','summary','markdown'):
        p=paths[key]
        if not p.name.lower().startswith('step8_') or not p.resolve().is_relative_to(ROOT) or not p.resolve().is_relative_to((ROOT/'docs').resolve() if key=='markdown' else (ROOT/'output/reports').resolve()):
            raise ValueError('STEP8 output must be a distinct step8 report/document')
    return cfg,paths,images


def preflight(config,paths,images):
    cfg=config['step7_candidates_v2']
    rows,hashes=upstream_preflight(resolve_config_path(cfg['report'],config),resolve_config_path(cfg['step6_summary'],config),config,images)
    rejected,evidence=review_exclusions(rows,config,images,hashes)
    summary=json.loads(paths['step7_summary'].read_text(encoding='utf-8-sig'))
    if summary.get('step7_version')!=STEP7_VERSION or summary.get('publication_status')!='COMPLETE' or summary.get('policy_review_required'):
        raise ValueError('Current complete STEP7 v2.2 required; rerun 07_score_lora_candidates.bat')
    if summary.get('settings')!=cfg:
        raise ValueError('STEP7 configuration changed; rerun STEP7 first')
    for p,value in hashes.items():
        if summary.get('input_hashes',{}).get(p)!=value:raise ValueError('STEP7 stale relative to current feedback/upstream; rerun STEP7')
    for key in ('output_csv','candidates_csv'):
        p=paths['full_csv' if key=='output_csv' else 'candidates_csv']
        if summary.get('artifact_sha256',{}).get(key)!=digest(p):raise ValueError('STEP7 output hash differs; rerun STEP7')
    cols,full=read_csv(paths['full_csv']);_,candidates=read_csv(paths['candidates_csv'])
    if set(FIELDS)-set(cols) or set(EXTRA)&set(cols):raise ValueError('Missing STEP7 fields or input already STEP8')
    upstream={r['frame_id']:r for r in rows};indexed={r['frame_id']:r for r in full}
    if len(indexed)!=len(full) or set(indexed)!=set(upstream):raise ValueError('STEP7 lost full upstream identities')
    for row in full:
        if row['step7_version']!=STEP7_VERSION or any(row.get(k)!=v for k,v in upstream[row['frame_id']].items()):
            raise ValueError('STEP7 changed upstream columns')
        if row['frame_id'] in rejected and (row['candidate_pool_eligible']!='false' or row['candidate_pool_selected']!='false' or row['selection_reason']!='CURRENT_VERSION_HUMAN_REJECT'):
            raise ValueError('Current-version Reject patch absent; rerun STEP7 first')
    selected={r['frame_id'] for r in full if r['candidate_pool_selected']=='true'}
    if len({r['frame_id'] for r in candidates})!=len(candidates) or selected!={r['frame_id'] for r in candidates} or len(candidates)!=summary.get('selected_review_pool'):
        raise ValueError('STEP7 candidate view differs from full audit/summary')
    for row in candidates:
        if row!=indexed[row['frame_id']] or row['frame_id'] in rejected or row['candidate_pool_eligible']!='true' or not review_scope_allowed(row):
            raise ValueError('Invalid or rejected STEP7 candidate; rerun STEP7')
    for key in ('full_csv','candidates_csv','step7_summary'):hashes[str(paths[key])]=digest(paths[key])
    return full,candidates,rejected,hashes


def encoded_csv(rows):
    return csv_bytes(rows,list(dict.fromkeys(k for row in rows for k in row)))


def prepare(config,paths,images,reset=False):
    settings=config['step8_folder_review'];full,candidates,rejected,hashes=preflight(config,paths,images)
    records,stage,session=stage_review(candidates,settings,paths['review_root'],images,ROOT,hashes,reset)
    ensure_unchanged(hashes)
    manifest=encoded_csv(records)
    prep=dict(step8_version=VERSION,publication_status='COMPLETE',session_id=session,
        candidate_count=len(records),full_upstream_rows=len(full),input_hashes=hashes,
        manifest_sha256=hashlib.sha256(manifest).hexdigest(),settings=settings,review_root=str(paths['review_root']))
    archive=install_review(stage,paths['review_root'],settings,reset)
    try:
        contents=dict(manifest=manifest,preparation_summary=json.dumps(prep,ensure_ascii=False,indent=2).encode('utf-8'))
        publish(contents,{k:paths[k] for k in contents},'preparation_summary',hashes)
    except Exception:
        # Preserve newly created copies and any concurrent choices; never delete ACCEPT.
        failed=paths['review_root'].parent/'bkup'/('step8_failed_'+uuid.uuid4().hex)
        failed.parent.mkdir(exist_ok=True);paths['review_root'].replace(failed)
        if archive:archive.replace(paths['review_root'])
        raise
    print('Prepared',len(records),'unique candidates in multiple VIEWs; 99_ACCEPT empty. Review:',paths['review_root'])
    if archive:print('Prior review/choices preserved:',archive)
    return prep


def prepared_records(config,paths,candidates,hashes):
    settings=config['step8_folder_review']
    prep=json.loads(paths['preparation_summary'].read_text(encoding='utf-8-sig'))
    if prep.get('step8_version')!=VERSION or prep.get('publication_status')!='COMPLETE' or prep.get('settings')!=settings or prep.get('manifest_sha256')!=digest(paths['manifest']):
        raise ValueError('STEP8 preparation/manifest changed; do not silently rebuild ACCEPT')
    for p,value in hashes.items():
        if prep.get('input_hashes',{}).get(p)!=value:raise ValueError('STEP8 review belongs to stale STEP7/feedback; archive/reset explicitly')
    ensure_unchanged(prep['input_hashes'])
    hashes.update(prep['input_hashes'])
    stamp=paths['review_root']/'.step8_review_session.json'
    no_links(paths['review_root'])
    if json.loads(stamp.read_text(encoding='utf-8')).get('session_id')!=prep['session_id']:raise ValueError('Review directory session differs from manifest')
    _,records=read_csv(paths['manifest'])
    expected=manifest_rows(candidates,settings,paths['review_root'])
    if records!=expected:raise ValueError('Review manifest no longer matches current candidates')
    for p in (paths['manifest'],paths['preparation_summary'],stamp):hashes[str(p)]=digest(p)
    return records,prep


def markdown(summary):
    text='# STEP8 Human Final Selection\n\n'
    text+=f"Total selected: **{summary['accepted_total']}** / {summary['final_count_min']}–{summary['final_count_max']}\n\nStatus: **{summary['selection_status']}**\n\n"
    text+='Human selections only. NOT_SELECTED does not mean bad image. Pose/scale/vertical guidance is soft; quality takes priority. Identity remains diagnostic.\n\n'
    text+='| Pose | recommended_min | recommended_max | actual_accept_count |\n|---|---:|---:|---:|\n'
    for r in summary['pose_guidance']:text+=f"| {r['pose_bin']} | {r['recommended_min']} | {r['recommended_max']} | {r['actual_accept_count']} |\n"
    for field,labels in [('vertical_pose',('LEVEL','LOOKING_UP','LOOKING_DOWN','NOT_EVALUABLE')),('face_scale_bin',('CLOSE_UP','UPPER_BODY','FULL_BODY','NOT_EVALUABLE')),('identity_state',('IDENTITY_PASS','IDENTITY_REVIEW','IDENTITY_REJECT','IDENTITY_NOT_EVALUABLE'))]:
        text+='\n'+field+'\n\n| label | count |\n|---|---:|\n'
        for label in labels:text+=f"| {label} | {summary['distributions'][field].get(label,0)} |\n"
    text+='\nSources / quality / warnings\n\n```json\n'+json.dumps({k:summary[k] for k in ('source_summary','quality','guidance_warnings')},ensure_ascii=False,indent=2)+'\n```\n'
    text+='\nIgnored exact duplicate VIEW copies (not additional accepts): '+str(summary.get('view_duplicate_copies_ignored_count',0))+'\n'
    text+='\nSTEP9 input is validated step8_human_selection.csv with STEP8_ACCEPT only, and requires VALID total count. No STEP9 processing ran.\n'
    return text.encode('utf-8')


def collect(config,paths,images):
    full,candidates,rejected,hashes=preflight(config,paths,images)
    records,prep=prepared_records(config,paths,candidates,hashes)
    accepted,copy_hashes=accepted_ids(records,paths['review_root'],config['step8_folder_review'],rejected)
    hashes.update(copy_hashes)
    rows,summary=selection_rows(full,records,accepted,config['step8_folder_review'],prep['session_id'])
    if any(any(out[k]!=v for k,v in old.items()) for old,out in zip(full,rows)):raise ValueError('STEP8 altered upstream values')
    summary.update(input_hashes=hashes,settings=config['step8_folder_review'],authoritative_csv=str(paths['selection_csv']),
        step9_input='Validated CSV rows with step8_decision=STEP8_ACCEPT; original sources, not ACCEPT filesystem')
    expected_review_paths={str(Path(p).resolve()) for r in records for p in json.loads(r['review_view_paths_json'])}
    expected_review_paths.update(str(Path(r['accept_review_path']).resolve()) for r in records if r['frame_id'] in accepted)
    extras=sorted(p for p in copy_hashes if str(Path(p).resolve()) not in expected_review_paths)
    summary.update(view_duplicate_copies_ignored_count=len(extras),view_duplicate_copies_ignored=extras)
    if extras:
        print('[WARNING] Ignored exact duplicate VIEW copies (not extra accepts):',len(extras))
        for p in extras:print(' ',p)
    contents=dict(selection_csv=encoded_csv(rows),markdown=markdown(summary))
    summary['artifact_sha256']={k:hashlib.sha256(v).hexdigest() for k,v in contents.items()}
    contents['summary']=json.dumps(summary,ensure_ascii=False,indent=2).encode('utf-8')
    current_accept_paths={str(p) for p in (paths['review_root']/'99_ACCEPT').iterdir()}
    if current_accept_paths!={r['accept_review_path'] for r in records if r['frame_id'] in accepted}:
        raise ValueError('ACCEPT changed during collection; finish copying and retry')
    publish(contents,{k:paths[k] for k in contents},'summary',hashes)
    print(summary['selection_status'],'selected:',summary['accepted_total'],'Report:',paths['markdown'])
    return summary


def load_step9_selection(config):
    """Validated downstream handoff; never infer selection from ACCEPT contents."""
    settings,paths,images=paths_for(config)
    full,candidates,rejected,hashes=preflight(config,paths,images)
    summary=json.loads(paths['summary'].read_text(encoding='utf-8-sig'))
    if summary.get('step8_version')!=VERSION or summary.get('selection_status')!='VALID' or summary.get('finalization_allowed') is not True or summary.get('publication_status')!='COMPLETE':
        raise ValueError('Final Human selection is not VALID; collect 35–45 before STEP9')
    if summary.get('settings')!=settings:raise ValueError('STEP8 settings changed since collection')
    if summary.get('artifact_sha256',{}).get('selection_csv')!=digest(paths['selection_csv']):raise ValueError('STEP8 decision CSV hash mismatch')
    # ACCEPT may be disposed after collection. Pin official inputs/session manifest,
    # not interaction copies, when loading downstream authoritative decisions.
    prep=json.loads(paths['preparation_summary'].read_text(encoding='utf-8-sig'))
    if summary.get('session_id')!=prep.get('session_id') or digest(paths['manifest'])!=prep.get('manifest_sha256'):raise ValueError('New preparation invalidated prior Human decisions')
    for p in (paths['manifest'],paths['preparation_summary']):
        if summary.get('input_hashes',{}).get(str(p))!=digest(p):raise ValueError('Official STEP8 preparation evidence changed')
    for p,value in hashes.items():
        if summary.get('input_hashes',{}).get(p)!=value:raise ValueError('Final decision uses stale upstream/feedback')
    _,rows=read_csv(paths['selection_csv']);expected={r['frame_id']:r for r in full}
    if len(rows)!=len(full) or len({r['frame_id'] for r in rows})!=len(rows) or set(expected)!={r['frame_id'] for r in rows}:raise ValueError('STEP8 full audit identity mismatch')
    pool={r['frame_id'] for r in candidates};selected=[]
    for row in rows:
        if any(row.get(k)!=v for k,v in expected[row['frame_id']].items()):raise ValueError('STEP8 inherited columns changed')
        allowed=('STEP8_ACCEPT','STEP8_NOT_SELECTED') if row['frame_id'] in pool else ('NOT_APPLICABLE_NOT_IN_REVIEW_POOL',)
        if row['step8_decision'] not in allowed:raise ValueError('Invalid STEP8 decision state')
        if row['step8_selection_status']!='VALID' or row['step8_review_session_id']!=summary['session_id'] or row['step8_version']!=VERSION:raise ValueError('Mixed STEP8 decision sessions')
        if row['step8_decision']=='STEP8_ACCEPT':
            if row['frame_id'] not in pool or row['frame_id'] in rejected:raise ValueError('Invalid finalized candidate')
            if digest(source_path(row,images))!=row['image_sha256']:raise ValueError('Final source image changed')
            selected.append(row)
    if len(selected)!=summary['accepted_total'] or not settings['final_count_min']<=len(selected)<=settings['final_count_max']:raise ValueError('Invalid finalized count')
    return selected


def main():
    config=load_for_cli();settings,paths,images=paths_for(config)
    parser=argparse.ArgumentParser(description='STEP8 ranked/multi-VIEW -> copy to 99_ACCEPT -> collect')
    parser.add_argument('action',choices=('prepare','collect','handoff-check'))
    parser.add_argument('--config',type=Path)
    parser.add_argument('--preflight-only',action='store_true')
    parser.add_argument('--reset-review',action='store_true',help='Explicitly archive existing review including ACCEPT; rebuild with empty ACCEPT')
    args=parser.parse_args()
    with ExitStack() as stack:
        for name in ('.step3_best_operation.lock','.step4_pose_operation.lock','.step5_dedup_operation.lock','.step6_identity_operation.lock','.step7_candidate_operation.lock','.step8_folder_operation.lock'):
            stack.enter_context(manifest_lock(paths['full_csv'].parent/name))
        if args.preflight_only:
            full,candidates,rejected,_=preflight(config,paths,images)
            print('STEP8 PREFLIGHT PASS; full rows:',len(full),'candidates:',len(candidates),'current rejects:',len(rejected),'No preparation/selection/publication.')
            return 0
        if args.action=='prepare':prepare(config,paths,images,args.reset_review);return 0
        if args.reset_review:raise ValueError('--reset-review is prepare-only')
        if args.action=='collect':return 0 if collect(config,paths,images)['finalization_allowed'] else 1
        print('Validated STEP9 CSV handoff:',len(load_step9_selection(config)),'accepted rows. No STEP9 inference.');return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('[ERROR]',type(exc).__name__,str(exc),file=sys.stderr);sys.exit(1)
