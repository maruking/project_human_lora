"""Official STEP4 v3. Full inference belongs to maru; bounded comparison check supported."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys
import uuid

from common.config import load_for_cli, get_section, configure_parser, resolve_config_path
from common.buffalo_pose import BuffaloPose
from common.identity_v2 import digest
from common.pose_composition import settings_from
from common.pose_composition_v3 import VERSION, infer_rows, summary_for, markdown_for
from common.video_manifest import manifest_lock, write_csv_atomic, write_json_atomic
from step4_pose_composition import load_input, write_text_atomic

ROOT = Path(__file__).resolve().parents[1]


def source_path(row, images):
    relative = Path(row['filename'].replace('\\','/'))
    if relative.is_absolute() or '..' in relative.parts or ':' in str(relative):
        raise ValueError('Unsafe source path')
    result = (images/relative).resolve()
    if not result.is_relative_to(images.resolve()):
        raise ValueError('Source path escapes image root')
    return result


def validate_targets(targets, inputs):
    paths = [p.resolve() for p in (*targets.values(),*inputs)]
    if len(paths) != len(set(paths)):
        raise ValueError('Distinct inputs/outputs required')
    for key,path in targets.items():
        suffix = '.md' if key=='markdown' else '.json' if key=='summary' else '.csv'
        if path.suffix != suffix or path.name.startswith(('step1_','step2_','step3_','step5_','step6_','step7_','step8_')):
            raise ValueError('Unsafe STEP4 output')
        if any(path.resolve().is_relative_to(ROOT/part) for part in ('scripts','bat','config','input','work','knowledge','.agents','tests')):
            raise ValueError('STEP4 cannot overwrite code/source')


def publish(outputs, settings, estimator, inputs, targets):
    summary,sources = summary_for(outputs)
    summary.update(input_report_sha256=digest(inputs[0]),input_summary_sha256=digest(inputs[1]),
        input_ranking_version='best_rank_v2.2',thresholds=settings,estimator=estimator.metadata,
        output_paths={key:str(path) for key,path in targets.items()},
        yaw_sign_convention='Raw buffalo_l yaw, positive RIGHT/negative LEFT; same as approved comparison',
        face_scale_semantics='Unchanged STEP3 bbox area/image area; not body visibility')
    existing = {key:p for key,p in targets.items() if p.exists()}
    if existing:
        archive = targets['output'].parent/'bkup'/(VERSION+'_'+uuid.uuid4().hex)
        archive.mkdir(parents=True,exist_ok=False)
        records=[]
        for key,path in existing.items():
            dest=archive/(key+path.suffix)
            shutil.copy2(path,dest)
            assert digest(dest)==digest(path)
            records.append(dict(original_path=str(path),archived_path=str(dest),sha256=digest(path)))
        write_json_atomic(archive/'MANIFEST.json',dict(files=records))
    write_csv_atomic(targets['output'],list(dict.fromkeys(k for r in outputs for k in r)),outputs)
    summary['output_csv_sha256']=digest(targets['output'])
    write_csv_atomic(targets['video_summary'],list(sources[0]),sources)
    summary['video_summary_sha256']=digest(targets['video_summary'])
    write_text_atomic(targets['markdown'],markdown_for(summary))
    summary['markdown_sha256']=digest(targets['markdown'])
    write_json_atomic(targets['summary'],summary) # individually atomic, marker last; not global transaction
    return summary


def comparison_check(rows, settings, estimator, images, comparison):
    with comparison.open(encoding='utf-8-sig',newline='') as handle:
        expected=list(csv.DictReader(handle))
    if len(expected)!=25 or len({r['frame_id'] for r in expected})!=25:
        raise ValueError('Approved comparison requires exactly 25 unique rows')
    by_id={r['frame_id']:r for r in rows}
    subset=[]
    for record in expected:
        row=by_id[record['frame_id']]
        if any(row[k]!=record[k] for k in ('image_sha256','dataset_generation_id')):
            raise ValueError('Comparison belongs to another generation')
        if any(row[k]!=record['current_'+k] for k in ('yaw','pitch','roll')):
            raise ValueError('Comparison current angles differ from authoritative STEP3')
        subset.append(row)
    outputs=infer_rows(subset,settings,estimator,lambda r:source_path(r,images))
    maximum=0.0
    for actual,record in zip(outputs,expected):
        if actual['step4_estimator_status']!='MEASURED':
            raise ValueError('Comparison sample no longer measurable')
        for key in ('yaw','pitch','roll'):
            delta=abs(float(actual[key])-float(record['alternative_'+key]))
            maximum=max(maximum,delta)
            if delta>1e-6:
                raise ValueError('Alternative comparison mismatch: '+actual['frame_id']+'/'+key)
        if actual['pose_bin']!=record['alternative_pose_bin']:
            raise ValueError('Alternative pose bin mismatch')
    # Counterexample identity is supplied in comparison, never a production special case.
    print('COMPARISON CHECK PASS:',len(outputs),'rows; maximum angle delta:',maximum)
    print('No official output published. Full batch executed: NO')
    return outputs


def main():
    config=load_for_cli()
    parser=argparse.ArgumentParser(description=__doc__)
    defaults=dict(report='@reports/step3_best_ranking.csv',step3_summary='@reports/step3_best_ranking_summary.json',
        output='@reports/step4_pose_composition.csv',summary='@reports/step4_pose_summary.json',
        video_summary='@reports/step4_video_pose_summary.csv',markdown='docs/STEP4_POSE_COMPOSITION_SUMMARY.md')
    for name,value in defaults.items():
        parser.add_argument('--'+name.replace('_','-'),type=Path,default=resolve_config_path(value,config))
    parser.add_argument('--config',type=Path)
    parser.add_argument('--preflight-only',action='store_true')
    parser.add_argument('--comparison-check',type=Path)
    configure_parser(parser,config,'step4_pose_composition')
    args=parser.parse_args()
    if get_section(config,'step4_pose_composition').get('version')!=VERSION:
        raise ValueError('STEP4 v3 configuration required')
    settings=settings_from(config)
    images=resolve_config_path(config['paths']['raw_frames_dir'],config)
    inputs=(args.report,args.step3_summary)
    targets={key:getattr(args,key) for key in ('output','summary','video_summary','markdown')}
    validate_targets(targets,inputs)
    with manifest_lock(args.report.parent/'.step3_best_operation.lock'),manifest_lock(args.output.parent/'.step4_pose_operation.lock'):
        rows=load_input(*inputs)
        before={p:digest(p) for p in inputs}
        if args.preflight_only:
            pack=Path.home()/'.insightface/models/buffalo_l'
            if not all((pack/name).is_file() for name in ('det_10g.onnx','1k3d68.onnx')):
                raise ValueError('Existing buffalo_l weights missing; no automatic download')
            print('PREFLIGHT PASS: current STEP3 full rows:',len(rows),'; v3 BAT wired; no inference/publication')
            return 0
        estimator=BuffaloPose()
        if args.comparison_check:
            comparison_check(rows,settings,estimator,images,args.comparison_check)
            assert all(digest(p)==sha for p,sha in before.items())
            return 0
        outputs=infer_rows(rows,settings,estimator,lambda r:source_path(r,images))
        assert all(digest(p)==sha for p,sha in before.items())
        summary=publish(outputs,settings,estimator,inputs,targets)
    print('STEP4',VERSION,'rows:',summary['total_rows'],'statuses:',summary['statuses'])
    return 1 if summary['statuses'].get('ERROR',0) else 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('[ERROR]',str(exc),file=sys.stderr)
        sys.exit(1)
