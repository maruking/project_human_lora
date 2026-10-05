"""STEP7 full-audit review pool; never runs STEP8 or final dataset selection."""
import argparse
import csv
from contextlib import ExitStack
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import uuid
from collections import Counter

from common.config import load_for_cli, get_section, configure_parser, resolve_config_path
from common.candidate_selection_v21 import VERSION,FIELDS,POSES,SCALES,VERTICALS,priority,normal,select,validate_settings
from common.candidate_review_exclusions import confirmed_rejects,CURRENT_RANKING_VERSION
from common.identity_v2 import FIELDS as IDENTITY_FIELDS
from common.video_manifest import manifest_lock
from step6_identity_v2 import preflight as step5_preflight, publish, ensure_unchanged
from step5_dedup_v2 import read_csv, source_path, document, table, esc, link, sha256_file as digest

ROOT=Path(__file__).resolve().parents[1]
PATHS=dict(report='@reports/step6_dataset_report.csv',step6_summary='@reports/step6_identity_summary.json',
    output_csv='@reports/step7_candidate_selection.csv',candidates_csv='@reports/step7_review_candidates.csv',
    summary='@reports/step7_candidate_summary.json',markdown='docs/STEP7_CANDIDATE_SUMMARY.md',
    review_html='docs/STEP7_CANDIDATE_REVIEW.html')
OUTPUT_KEYS=('output_csv','candidates_csv','markdown','review_html','summary')
STATES={'IDENTITY_PASS','IDENTITY_REVIEW','IDENTITY_REJECT','IDENTITY_NOT_EVALUABLE',
    'NOT_APPLICABLE_DUPLICATE_MEMBER','NOT_APPLICABLE_UPSTREAM','UPSTREAM_ERROR'}


def review_exclusions(rows,config,images,hashes):
    reports=resolve_config_path(config['paths']['reports_dir'],config)
    history_path=reports/'step3_best_review_history_by_version.json'
    feedback_path=reports/f'step3_best_review_reject_feedback_{CURRENT_RANKING_VERSION}.csv'
    summary_path=resolve_config_path(config['step5_dedup']['step3_summary'],config)
    ranking_path=resolve_config_path(config['step5_dedup']['step3_report'],config)
    if config['step3_best_ranking']['ranking_version']!=CURRENT_RANKING_VERSION:
        raise ValueError('Unsupported current review version; explicit policy review required')
    for path in (history_path,feedback_path,summary_path,ranking_path):
        if not path.is_file():raise ValueError('Authoritative review evidence missing: '+str(path))
    summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
    if digest(ranking_path)!=summary.get('ranking_sha256'):
        raise ValueError('Current ranking output hash mismatch')
    history=json.loads(history_path.read_text(encoding='utf-8-sig'))
    legacy=history.get('legacy_source')
    if legacy:
        path=reports/legacy['filename']
        if digest(path)!=legacy['sha256']:raise ValueError('Historical review source changed')
        hashes[str(path)]=digest(path)
    _,feedback=read_csv(feedback_path)
    rejected,historical=confirmed_rejects(rows,history,feedback,summary)
    for row in rows:
        if row['frame_id'] in rejected:
            image=source_path(row,images)
            if digest(image)!=row['image_sha256']:raise ValueError('Rejected source image changed')
            hashes[str(image)]=row['image_sha256']
    for path in (history_path,feedback_path):hashes[str(path)]=digest(path)
    return rejected,dict(ranking_version=CURRENT_RANKING_VERSION,current_version_rejects_found=len(rejected),
        historical_version_rejects_left_eligible=sum(normal(r) and r['frame_id'] in historical for r in rows),
        history=str(history_path),feedback=str(feedback_path),ranking_sha256=summary['ranking_sha256'],
        binding='Pinned ranking hash + all shared immutable review-record columns + frame/image/generation identity')


def preflight(report,summary_path,config,images):
    settings=get_section(config,'step6_identity')
    upstream=[resolve_config_path(settings[k],config) for k in ('report','step5_summary')]
    original,hashes=step5_preflight(*upstream,config,images)
    columns,rows=read_csv(report)
    if set(IDENTITY_FIELDS)-set(columns) or set(FIELDS)&set(columns):
        raise ValueError('STEP6 columns missing or report is already STEP7')
    summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
    if summary.get('step6_version')!='step6_identity_v2' or summary.get('publication_status')!='COMPLETE' or summary.get('errors'):
        raise ValueError('STEP6 requires COMPLETE step6_identity_v2 without measurement errors')
    if summary.get('artifact_sha256',{}).get('output_csv')!=digest(report) or summary.get('total_rows')!=len(rows):
        raise ValueError('STEP6 CSV content/count differs from summary')
    expected={r['frame_id']:r for r in original}
    if len({r['frame_id'] for r in rows})!=len(rows) or set(expected)!={r['frame_id'] for r in rows}:
        raise ValueError('STEP6 identity universe is not unique/full/current')
    for path,value in hashes.items():
        if summary.get('input_hashes',{}).get(path)!=value:
            raise ValueError('STEP6 has stale upstream evidence: '+path)
    generations={}
    for row in rows:
        frame=row['frame_id']
        if row['step6_version']!='step6_identity_v2':
            raise ValueError('Mixed STEP6 versions')
        if any(row.get(k)!=v for k,v in expected[frame].items()):
            raise ValueError('STEP6 changed inherited STEP3–5 columns: '+frame)
        if row['identity_state'] not in STATES or row['step6_status'] not in ('MEASURED','NOT_APPLICABLE'):
            raise ValueError('Invalid/incomplete STEP6 identity state: '+frame)
        if normal(row):
            priority(row)
            if row['pose_bin'] not in POSES or row['vertical_pose'] not in VERTICALS or row['face_scale_bin'] not in SCALES:
                raise ValueError('Pose/scale missing without explicit NOT_EVALUABLE state')
            if row['identity_state'] not in ('IDENTITY_PASS','IDENTITY_REVIEW','IDENTITY_REJECT','IDENTITY_NOT_EVALUABLE'):
                raise ValueError('Normal candidate lacks evaluated identity diagnostic state')
        for key in ('identity_similarity_centroid','identity_similarity_max','identity_similarity_median'):
            if row[key] and (not math.isfinite(float(row[key])) or not -1.000001<=float(row[key])<=1.000001):
                raise ValueError('Nonfinite/out-of-domain stored cosine diagnostic')
        generations.setdefault(row['input_kind'],set()).add(row['dataset_generation_id'])
        if not source_path(row,images).is_file():
            raise ValueError('Source image missing: '+frame)
    if dict(Counter(r['identity_state'] for r in rows))!=summary.get('states'):
        raise ValueError('STEP6 identity state counts differ from summary')
    if {k:sorted(v) for k,v in generations.items()}!=summary.get('dataset_generations_by_kind'):
        raise ValueError('STEP6 generation IDs differ from summary')
    # STEP3/4 lack literal COMPLETE fields; existing hash/full-universe contracts
    # establish completeness instead of fabricating a status or requiring a migration.
    step4_path=resolve_config_path(config['step5_dedup']['step4_summary'],config)
    step4=json.loads(step4_path.read_text(encoding='utf-8-sig'))
    if step4.get('statuses',{}).get('ERROR',0):
        raise ValueError('STEP4 has errors')
    hashes.update({str(report):digest(report),str(summary_path):digest(summary_path)})
    return rows,hashes


def safe_targets(targets,inputs,images):
    paths=[*targets.values(),*inputs]
    if len({p.resolve() for p in paths})!=len(paths):
        raise ValueError('STEP7 input/output paths must be distinct')
    for key,path in targets.items():
        extension='.csv' if key in ('output_csv','candidates_csv') else '.json' if key=='summary' else '.html' if key=='review_html' else '.md'
        if path.suffix.lower()!=extension or not path.name.lower().startswith('step7_') or not path.resolve().is_relative_to(ROOT):
            raise ValueError('Unsafe STEP7 output path')
        if any(path.resolve().is_relative_to(p.resolve()) for p in [images,*(ROOT/k for k in ('scripts','bat','config','knowledge','tests','.agents','input','work','history'))]):
            raise ValueError('STEP7 output cannot overwrite source/code/history')


def gallery(rows,summary,images,page):
    body='<p>STEP7は約70枚のHuman Review候補です。最終35〜45枚はSTEP8で★maruが決めます。ここでは最終採用・画像品質Rejectを作りません。</p>'
    reasons=summary['selection_reasons']
    body+='<h2>QUALITY GUARD — 品質優先の候補範囲</h2><p>通常候補をBEST順に並べた上位 '+str(summary['quality_guard_size_actual'])+' 枚（設定上限 '+str(summary['quality_guard_size_requested'])+' 枚）だけから選びます。</p>'
    body+='<p>品質コア：'+str(reasons['BEST_QUALITY_CORE'])+' 枚 ／ Coverage補完：'+str(reasons['COVERAGE_REPAIR'])+' 枚 ／ BEST補充：'+str(reasons['BEST_SCORE_FILL'])+' 枚。選定した最も低いglobal rank：'+str(summary['deepest_global_rank_selected'])+'。</p>'
    body+='<p>Coverage不足は品質範囲を広げず記録します。'+esc(json.dumps(summary['soft_coverage_shortages'],ensure_ascii=False))+'</p>'
    body+='<p>品質順はSTEP3 BESTのみ。Identityの重みは0です。現行版の正式REVIEW_REJECTは候補除外であり、スコア減点ではありません。旧版RejectやPENDINGはそれだけで除外しません。LOW_MEASURED_IDENTITYは別人の断定ではありません。FULL_BODYは顔の面積区分で、脚・体の視認性認定ではありません。</p>'
    body+=table(('項目','値'),[(k,json.dumps(summary[k],ensure_ascii=False)) for k in ('selected_review_pool','best_score','global_rank_range','source_count','video_count','coverage_achieved','identity_state_distribution','quality_guard_size_requested','quality_guard_size_actual','quality_guard_best_score_min','quality_guard_global_rank_max','selection_reasons','deepest_global_rank_selected','pool_quality_status','soft_coverage_shortages','source_cap_conflicts','source_distribution')])
    body+='<p>QUALITY GUARD内からBEST_QUALITY_COREを先に固定します。COVERAGE_REPAIRは残り枠での補完、BEST_SCORE_FILLはBEST順の追加です。Coverageを理由に品質優先度を上げません。cluster_identity_fallback_neededは後の人間確認用で、自動差替えしません。</p>'
    keys=('frame_id','best_score','global_rank','step7_pool_order','pose_bin','yaw','pitch','vertical_pose','face_scale_bin',
        'quality_guard_member','quality_guard_order','dedup_role','cluster_size','identity_state','identity_context','identity_similarity_centroid','identity_similarity_max',
        'identity_similarity_median','cluster_identity_fallback_needed','selection_reason','coverage_pose_reason','coverage_vertical_reason',
        'coverage_scale_reason','video_id','source_id','input_kind')
    for pose in POSES:
        body+='<h2>'+pose+'</h2>'
        for scale in SCALES:
            members=sorted((r for r in rows if r['pose_bin']==pose and r['face_scale_bin']==scale),key=priority)
            body+='<h3>'+scale+' ('+str(len(members))+')</h3><div class="grid">'
            for row in members:
                source=link(source_path(row,images),page)
                body+='<article class="card"><a href="'+esc(source)+'" target="_blank"><img loading="lazy" src="'+esc(source)+'" alt="'+esc(row['frame_id'])+'"></a>'
                body+=table(('項目','値'),[(k,row.get(k,'')) for k in keys])+'</article>'
            body+='</div>'
    return document('STEP7 Candidate Review — STEP8 handoff',body)


def csv_bytes(rows,columns):
    buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=columns)
    writer.writeheader();writer.writerows(rows)
    return buffer.getvalue().encode('utf-8-sig')


def publish_selection(rows,settings,targets,images,hashes,limit=0,current_reject_ids=(),review_evidence=None):
    outputs,pool,summary=select(rows,settings,partial=limit>0,limit=limit,current_reject_ids=current_reject_ids)
    if review_evidence is not None:
        summary['current_version_review_exclusions']=review_evidence
        # Only hard quality/core failures block publication; coverage is soft.
    if len(rows)!=len(outputs) or any(any(out[k]!=v for k,v in old.items()) for out,old in zip(outputs,rows)):
        raise ValueError('STEP7 lost inherited rows/fields')
    if summary['publication_status']!='COMPLETE':
        directory=targets['summary'].parent/'audit'/(VERSION+'_'+uuid.uuid4().hex)
        targets={key:directory/path.name for key,path in targets.items()}
    summary.update(input_hashes=hashes,settings=settings,outputs={k:str(p) for k,p in targets.items()},
        input_versions=['best_rank_v2.2','step4_pose_composition_v2','step5_dedup_v2','step6_identity_v2'],
        completeness_evidence='STEP3/4 complete hash and full-row contract; STEP5/6 explicit COMPLETE markers',
        dataset_generations_by_kind={kind:sorted({r['dataset_generation_id'] for r in rows if r['input_kind']==kind}) for kind in sorted({r['input_kind'] for r in rows})})
    columns=list(dict.fromkeys(k for row in outputs for k in row))
    contents=dict(output_csv=csv_bytes(outputs,columns),candidates_csv=csv_bytes(pool,columns),
        review_html=gallery(pool,summary,images,targets['review_html']).encode('utf-8'))
    text='# STEP7 Candidate Pool Summary\n\nBounded QUALITY-FIRST review options. STEP8 decides final35–45. Identity weight0; BEST is the only quality score.\n\n'
    text+='[Source-linked candidate review]('+link(targets['review_html'],targets['markdown'])+')\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n'
    contents['markdown']=text.encode('utf-8')
    summary['artifact_sha256']={k:hashlib.sha256(v).hexdigest() for k,v in contents.items()}
    contents['summary']=json.dumps(summary,ensure_ascii=False,indent=2).encode('utf-8')
    publish(contents,targets,'summary',hashes)
    return summary


def main():
    config=load_for_cli();settings=dict(get_section(config,'step7_candidates_v2'))
    validate_settings(settings)
    parser=argparse.ArgumentParser(description='STEP7 BEST + minimum coverage review pool; no final selection')
    parser.add_argument('--config',type=Path)
    parser.add_argument('--preflight-only',action='store_true',help='Check reports/source existence only; no selection or publication')
    parser.add_argument('--limit',type=int,default=0,help='Partial test subset; always isolated audit output')
    parser.add_argument('--images',type=Path,default=resolve_config_path(config['paths']['raw_frames_dir'],config))
    for key,path in PATHS.items():parser.add_argument('--'+key.replace('_','-'),type=Path,default=resolve_config_path(path,config))
    configure_parser(parser,config,'step7_candidates_v2',paths={'images':'raw_frames_dir'})
    args=parser.parse_args()
    if args.limit<0:raise ValueError('limit must be nonnegative')
    targets={k:getattr(args,k) for k in OUTPUT_KEYS}
    safe_targets(targets,[args.report,args.step6_summary],args.images)
    print(VERSION,'\nInput:',args.report,'\nReview:',targets['review_html'],flush=True)
    with ExitStack() as stack:
        for name in ('.step3_best_operation.lock','.step4_pose_operation.lock','.step5_dedup_operation.lock','.step6_identity_operation.lock','.step7_candidate_operation.lock'):
            stack.enter_context(manifest_lock(args.report.parent/name))
        rows,hashes=preflight(args.report,args.step6_summary,config,args.images)
        rejected,evidence=review_exclusions(rows,config,args.images,hashes)
        if args.preflight_only:
            print('PREFLIGHT PASS; full rows:',len(rows),'normal candidate universe:',sum(normal(r) and r['frame_id'] not in rejected for r in rows),'Confirmed current-version rejects:',len(rejected),'No selection/output/image inference.')
            return 0
        summary=publish_selection(rows,settings,targets,args.images,hashes,args.limit,rejected,evidence)
        print(summary['publication_status'],'selected review options:',summary['selected_review_pool'],'\nReport:',summary['outputs']['markdown'])
        return 1 if summary['policy_review_required'] else 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('[ERROR]',type(exc).__name__,str(exc),file=sys.stderr);sys.exit(1)
