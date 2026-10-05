"""STEP3 BEST v2.2. Default: rescore stored measurements, stop before review extraction."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
from common.config import load_config,get_section,resolve_config_path
from common.best_inventory import load_inventory,csv_rows
from common.best_ranking import VERSION,rank_rows,fit_context,effective_settings,METRICS,number,POSITIVE,PENALTIES
from common.best_review import (HISTORY_NAME,materialize,feedback,read_history,
                                historical_reviews,validate_history_rows)
from common.step3_review import review_roots,require_source
from common.video_manifest import manifest_lock,write_csv_atomic,write_json_atomic,sha256_file


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path)
    p.add_argument('--review-round',type=int,choices=(1,2,3))
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--from-existing',action='store_true',help='Extract an explicit review round from current ranking-version scores')
    mode.add_argument('--feedback-only',action='store_true',help='Record review_reject moves only')
    mode.add_argument('--remeasure',action='store_true',help='Explicit full measurement run; normally reuse stored metrics')
    return p


def write_rows(path,rows):
    fields=sorted(set().union(*(set(r) for r in rows))) if rows else ['frame_id']
    write_csv_atomic(path,fields,[{k:r.get(k,'') for k in fields} for r in rows])


def distributions(rows,metrics):
    from build_step2_reports import stats
    out=[]
    for kind in ['ALL',*sorted({r['input_kind'] for r in rows})]:
        group=rows if kind=='ALL' else [r for r in rows if r['input_kind']==kind]
        for metric in metrics:
            values=[number(r.get(metric)) for r in group];valid=[v for v in values if v is not None]
            out.append(dict(input_kind=kind,metric=metric,missing=len(values)-len(valid),**(stats(valid) if valid else {'count':0})))
    return out


def annotate(rows,history):
    validate_history_rows(rows,history)
    shown={r['frame_id']:r for r in history['records']}
    for row in rows:
        previous=shown.get(row['frame_id'])
        row['review_selected']=str(previous is not None).lower()
        row['shown_to_maru']=str(previous is not None).lower()
        for key in ('review_round','review_round_rank','review_state'):
            row[key]=previous[key] if previous else ''
        row['review_ranking_version']=previous.get('ranking_version','UNKNOWN') if previous else ''
        evidence=historical_reviews(history,row)
        row['historical_reviews']=json.dumps(evidence,ensure_ascii=False,sort_keys=True)
        row['historical_review_reject']=str(any(r['review_state']=='REVIEW_REJECT' for r in evidence)).lower()


def review_summary(history):
    completed={int(r['review_round']) for r in history['rounds'] if r['publication_status']=='COMPLETE'}
    next_round=next((n for n in (1,2,3) if n not in completed),None)
    return dict(review_ranking_version=VERSION,review_rounds=history['rounds'],
                shown_count=len(history['records']),
                review_reject_count=sum(r['review_state']=='REVIEW_REJECT' for r in history['records']),
                historical_review_counts={v:dict(shown=len(g['records']),
                    review_reject=sum(r['review_state']=='REVIEW_REJECT' for r in g['records']))
                    for v,g in history['review_history'].items() if v!=VERSION},
                next_review_round=next_round,
                next_action=(f'Inspect summary; run 03_best_review_round.bat {next_round} for {VERSION}. '
                             'Previous-version shown flags do not exclude candidates.' if next_round else
                             f'{VERSION} review rounds 1-3 are already published.'))


def archive_current(ranking,summary_path):
    """Immutable report copy, never move/delete evidence. Called only on production publication."""
    if not ranking.exists():return
    summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
    version=summary['version']
    if version not in ('best_rank_v1','best_rank_v2','best_rank_v2.1',VERSION):raise ValueError('Unknown previous ranking version')
    digest=sha256_file(ranking)
    if digest!=summary['ranking_sha256']:raise ValueError('Previous ranking checksum mismatch')
    folder=ranking.parent/'step3_best_history'/f'{version}_{digest}'
    folder.mkdir(parents=True,exist_ok=True)
    for source in (ranking,summary_path):
        target=folder/source.name
        # Summary can change after human feedback while score bytes stay identical.
        if target.exists() and sha256_file(target)!=sha256_file(source):
            target=folder/(source.stem+'_'+sha256_file(source)+source.suffix)
        if not target.exists():shutil.copy2(source,target)
        if sha256_file(source)!=sha256_file(target):raise ValueError('Historical report copy mismatch')


def validate_stored(ranking,summary_path,inventory,snapshot):
    summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
    if summary['input_snapshot']!=snapshot or sha256_file(ranking)!=summary['ranking_sha256']:
        raise ValueError('Stored BEST ranking is stale/changed; no reuse permitted')
    rows=csv_rows(ranking)
    keys=lambda rs:{(r['frame_id'],r['image_sha256'],r['dataset_generation_id']) for r in rs}
    if len(rows)!=len(inventory) or len({r['frame_id'] for r in rows})!=len(rows) or keys(rows)!=keys(inventory):
        raise ValueError('Stored BEST ranking inventory mismatch')
    return rows,summary


def main(argv=None):
    args=parser().parse_args(argv)
    if args.review_round is not None and not args.from_existing:
        raise ValueError('Review extraction requires --from-existing; inspect current-version summary first')
    if args.from_existing and args.review_round is None:raise ValueError('Specify --review-round explicitly')
    config=load_config(args.config);review_roots(config)
    paths=get_section(config,'paths');settings=get_section(config,'step3_best_ranking')
    if settings.get('ranking_version')!=VERSION:raise ValueError(f'Configure {VERSION} before running')
    raw=resolve_config_path(paths['raw_frames_dir'],config);require_source(raw)
    reports=resolve_config_path(paths['reports_dir'],config)
    manifests=resolve_config_path(paths['manifests_dir'],config)
    ranking=reports/'step3_best_ranking.csv';summary_path=reports/'step3_best_ranking_summary.json'
    history_path=reports/HISTORY_NAME;review_root=reports/'step3_best_review'
    mode='feedback' if args.feedback_only else 'review extraction' if args.from_existing else 'measurement + ranking' if args.remeasure else 'stored-metric ranking only'
    print(f'STEP3 {VERSION}: {mode}\nreports={reports}',flush=True)
    reports.mkdir(parents=True,exist_ok=True)
    with manifest_lock(manifests/'.video_manifest.lock'),manifest_lock(reports/'.step3_best_operation.lock'):
        if args.feedback_only:
            if not history_path.exists():raise ValueError('No BEST review history')
            summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
            if summary['version']!=VERSION:raise ValueError(f'Feedback requires current {VERSION} summary')
            history,rejected=feedback(review_root,history_path)
            write_rows(reports/f'step3_best_review_reject_feedback_{VERSION}.csv',rejected)
            if summary_path.exists():
                summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
                summary.update(review_summary(history))
                write_json_atomic(summary_path,summary)
            print(f'Feedback recorded: {len(rejected)} REVIEW_REJECT; no new round.',flush=True)
            return 0
        if args.from_existing:
            preliminary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
            if preliminary['version']!=VERSION:
                raise ValueError(f'Review extraction from {preliminary["version"]} is disabled. Run {VERSION} ranking, inspect summary, then extract.')
        inventory,snapshot=load_inventory(reports,raw,manifests)
        effective=effective_settings(settings,config)
        if not args.remeasure:
            if not ranking.exists():raise ValueError('No stored metrics. Use --remeasure explicitly for a new generation')
            rows,previous=validate_stored(ranking,summary_path,inventory,snapshot)
            for key in ('canonical_short_edge','detection_confidence','shadow_pixel_max'):
                if previous['settings'].get(key)!=settings.get(key):raise ValueError('Measurement settings changed; explicit remeasurement required')
            if any(r.get('diagnostic_config_sha256')!=effective['_diagnostic_sha256'] for r in rows):
                raise ValueError('Stored diagnostic settings differ; explicit remeasurement required')
        else:
            from common.best_measurement import measure_rows
            import face_quality_gate as kernels
            rows=measure_rows(inventory,raw,settings,kernels)
        history=read_history(history_path)
        if args.from_existing:
            if previous['settings']!=settings or previous.get('effective_evidence')!=effective['_evidence']:
                raise ValueError('Current score settings changed; rerank before review extraction')
            annotate(rows,history)
            history=materialize(rows,raw,review_root,history_path,args.review_round,settings)
            annotate(rows,history);write_rows(ranking,rows)
            previous.update(ranking_sha256=sha256_file(ranking),**review_summary(history))
            write_json_atomic(summary_path,previous)
            print(f'{VERSION} review round {args.review_round:02d} ready: {review_root / VERSION / f"round_{args.review_round:02d}" / "candidates"}',flush=True)
            return 0
        context=fit_context(rows,effective)
        ranked=rank_rows(rows,effective,context);annotate(ranked,history)
        refreshed,new_snapshot=load_inventory(reports,raw,manifests)
        if new_snapshot!=snapshot or {(r['frame_id'],r['image_sha256']) for r in refreshed}!={(r['frame_id'],r['image_sha256']) for r in inventory}:
            raise ValueError('Input changed before publication')
        eligible=[r for r in ranked if r['ranking_eligible']=='true'];top=eligible[:settings.get('review_size',45)]
        summary=dict(version=VERSION,input_snapshot=snapshot,settings=settings,effective_evidence=effective['_evidence'],
            diagnostic_config_sha256=effective['_diagnostic_sha256'],normalization_anchors=context['anchors'],
            normalization_domain='combined ranking-eligible universe; P5/P95 positive only',
            formula='best_score = base_quality * critical_face_quality - penalty_total (points)',
            total_universe=len(ranked),input_kind_counts=dict(Counter(r['input_kind'] for r in ranked)),
            fatal_reject_counts=dict(Counter(r['fatal_reject_reason'] for r in ranked if r['fatal_reject']=='true')),
            ranking_eligible=len(eligible),review_rounds=history['rounds'],shown_count=len(history['records']),
            review_reject_count=sum(r['review_state']=='REVIEW_REJECT' for r in history['records']),
            positive_weights=settings['positive_weights'],penalty_weights=settings['penalty_weights'],
            top45_kind_distribution=dict(Counter(r['input_kind'] for r in top)),
            top45_video_concentration=dict(Counter(r['video_id'] for r in top if r['input_kind']=='formal_video')),
            top_ranked_sources=[{k:r.get(k,'') for k in ('frame_id','source_id','input_kind','global_rank','best_score')} for r in top],
            distributions=distributions(ranked,(*METRICS,'left_eye_openness','right_eye_openness',
                'eye_quality_score','eye_quality_positive_credit_loss','eye_closed_penalty','eye_half_open_penalty',
                'eye_obstruction_penalty','eye_measurement_penalty','blur_penalty','dark_exposure_penalty',
                'clipping_penalty','haze_penalty','low_contrast_penalty','uncertainty_penalty',
                'eye_quality_factor','blur_quality_factor','exposure_quality_factor','measurement_reliability_factor','critical_face_quality','base_quality','absolute_quality_total','relative_quality_bonus','penalty_total','best_score')),
            )
        summary.update(review_summary(history))
        archive_current(ranking,summary_path)
        write_rows(ranking,ranked);summary['ranking_sha256']=sha256_file(ranking)
        write_json_atomic(summary_path,summary)
        print(f'Current ranking saved: {len(ranked)} rows. No review copies extracted. Inspect {summary_path}',flush=True)
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(f'[ERROR] {type(exc).__name__}: {exc}',flush=True)
        raise SystemExit(1)
