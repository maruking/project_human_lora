"""Offline STEP3 calibration artifacts; never change Gates/authoritative data."""
import argparse
from collections import Counter
import csv
import hashlib
import html
import io
import json
import math
from pathlib import Path
import shutil
import os
import tempfile
import cv2
import numpy as np
from common.config import load_for_cli,get_section,resolve_project_path,resolve_config_path,configure_constants
from common.step3_audit import csv_bytes,validate_input
from common.video_manifest import manifest_lock
from common.step3_review_presentation import presentation
from build_step3_reports import rebuild
from build_step2_reports import stats
import face_quality_gate as gate

LABELS=('human_face_usable','human_face_blurry','human_eye_occlusion','human_beauty_filter','human_visibility_problem','human_exposure_problem','human_notes')
GATES=('global_blurry','face_blurry','one_eye_occluded','beauty_filter_detected','low_visibility','low_resolution_source','face_underexposed','face_backlit_underexposed','face_too_small','multiple_faces','no_face','hair_covered_face','analysis_error')
SCALES=('CLOSE_UP','UPPER_BODY','FULL_BODY')


def reasons(row): return set(row['face_gate_reason'].split(';'))-{'eligible'}
def num(row,key,default=0): return float(row[key]) if row.get(key) else default


def eye_state(row):
    if row['face_detected']!='true':return 'not_applicable_no_face'
    if row['facemesh_detected']!='true':return 'facemesh_unavailable'
    if row['eye_presence_valid']!='true':return 'eye_sharpness_disabled'
    return 'eye_sharpness_measured'


def blur_detail(row,settings):
    eye_low=row['shot_type']!='FULL_BODY' and num(row,'eye_sharpness')<settings['min_eye_sharpness']
    lap_low=num(row,'face_laplacian_score')<settings['min_face_laplacian']
    branch='not_applicable_no_face' if row['face_detected']!='true' else 'eye_sharpness' if eye_low else 'face_laplacian' if lap_low else 'none'
    expected=branch in ('eye_sharpness','face_laplacian')
    if expected!=('face_blurry' in reasons(row)):
        raise ValueError('Stored face_blurry differs from actual if/elif contract: '+row['filename'])
    return dict(filename=row['filename'],video_id=row['video_id'],shot_type=row['shot_type'],
                face_blurry_due_to_eye_sharpness=eye_low and row['face_detected']=='true',
                face_blurry_due_to_face_laplacian=lap_low and row['face_detected']=='true',
                face_blurry_due_to_both=eye_low and lap_low and row['face_detected']=='true',
                executed_blur_branch=branch,eye_metric_state=eye_state(row),
                eye_threshold_state=('measured_below_threshold' if num(row,'eye_sharpness')<settings['min_eye_sharpness'] else 'measured_at_or_above_threshold') if eye_state(row)=='eye_sharpness_measured' else eye_state(row),
                eye_presence_invalid=row['facemesh_detected']=='true' and row['eye_presence_valid']!='true',
                eye_sharpness=row['eye_sharpness'],face_laplacian=row['face_laplacian_score'])


def analyze(rows,settings):
    contributions=[];cf=[]
    for name in GATES:
        hit=[r for r in rows if name in reasons(r)];sole=sum(reasons(r)=={name} for r in hit)
        contributions.append(dict(gate_name=name,triggered_count=len(hit),triggered_ratio=len(hit)/len(rows),
                                  sole_rejection_count=sole,co_rejection_count=len(hit)-sole,
                                  videos_affected=len({r['video_id'] for r in hit}),
                                  close_up_count=sum(r['shot_type']=='CLOSE_UP' for r in hit),
                                  upper_body_count=sum(r['shot_type']=='UPPER_BODY' for r in hit),
                                  full_body_count=sum(r['shot_type']=='FULL_BODY' for r in hit),
                                  unclassified_count=sum(not r['shot_type'] for r in hit)))
        count=sum(not (reasons(r)-{name}) for r in rows)
        cf.append(dict(ignored_reason=name,counterfactual_eligible_count=count,
                       additional_eligible=count-sum(r['face_eligible']=='true' for r in rows),
                       status='DIAGNOSTIC_ONLY_NOT_APPLIED'))
    combinations=Counter(';'.join(sorted(reasons(r))) or 'eligible' for r in rows)
    combos=[dict(reason_combination=k,frame_count=n,percentage=100*n/len(rows),video_count=len({r['video_id'] for r in rows if (';'.join(sorted(reasons(r))) or 'eligible')==k})) for k,n in sorted(combinations.items(),key=lambda x:(-x[1],x[0]))]
    threshold=[]
    spec=[('face_laplacian_score','min_face_laplacian','min'),('eye_sharpness','min_eye_sharpness','min'),
          ('skin_texture_score','skin','min'),('plasticity_ratio','max_plasticity_ratio','max'),
          ('face_brightness_mean','min_face_brightness','min'),('face_visibility_score','min_face_visibility_score','min')]
    for scale in SCALES:
        group=[r for r in rows if r['shot_type']==scale]
        for metric,key,direction in spec:
            valid=[r for r in group if r.get(metric) and (metric not in ('eye_sharpness','skin_texture_score','plasticity_ratio','face_visibility_score') or r['facemesh_detected']=='true') and (metric not in ('eye_sharpness','plasticity_ratio') or r['eye_presence_valid']=='true')]
            values=[num(r,metric) for r in valid]
            value=settings['min_skin_texture_close_up' if scale=='CLOSE_UP' else 'min_skin_texture_upper_body'] if key=='skin' else settings[key]
            active=not(scale=='FULL_BODY' and metric in ('eye_sharpness','skin_texture_score','plasticity_ratio')) and not(settings.get('skip_beauty_filter',False) and metric in ('skin_texture_score','plasticity_ratio'))
            data=stats(values) if values else {k:'' for k in ('count','mean','std','min','p01','p05','p10','p25','p50','p75','p90','p95','p99','max')}
            threshold.append(dict(shot_type=scale,metric=metric,**data,current_threshold=value if active else '',
                                  threshold_active=active,direction=direction,
                                  threshold_percentile_position=round(100*sum(v<value for v in values)/len(values),6) if values and active else '',
                                  values_equal_threshold=sum(v==value for v in values) if active else '',
                                  excluded_count=len(group)-len(valid),sample_policy='measured_valid_only; plasticity excludes disabled eye numerator; visibility excludes mesh-unavailable proxy zeros'))
    eligible=sum(r['face_eligible']=='true' for r in rows)
    concentration=[]
    for video in sorted({r['video_id'] for r in rows}):
        group=[r for r in rows if r['video_id']==video];n=sum(r['face_eligible']=='true' for r in group)
        concentration.append(dict(video_id=video,frame_count=len(group),eligible_count=n,eligible_ratio=n/len(group),share_of_all_eligible=n/eligible if eligible else 0))
    return contributions,threshold,combos,cf,concentration,[blur_detail(r,settings) for r in rows]


def boundary_pools(rows,settings):
    pools=[]
    metrics=[('face_laplacian_score','min_face_laplacian'),('eye_sharpness','min_eye_sharpness'),('skin_texture_score','skin'),('plasticity_ratio','max_plasticity_ratio'),('face_visibility_score','min_face_visibility_score'),('face_brightness_mean','min_face_brightness')]
    for scale in SCALES:
        for metric,key in metrics:
            if scale=='FULL_BODY' and metric in ('eye_sharpness','skin_texture_score','plasticity_ratio'):continue
            value=settings['min_skin_texture_close_up' if scale=='CLOSE_UP' else 'min_skin_texture_upper_body'] if key=='skin' else settings[key]
            valid=[r for r in rows if r['shot_type']==scale and r.get(metric) and (metric not in ('eye_sharpness','plasticity_ratio') or eye_state(r)=='eye_sharpness_measured') and (metric not in ('skin_texture_score','face_visibility_score') or r['facemesh_detected']=='true')]
            for band,lo,hi in [('below',.7,.9),('just_below',.9,1),('just_above',1,1.1),('above',1.1,1.3)]:
                group=sorted([r for r in valid if lo*value<=num(r,metric)<hi*value],key=lambda r:(abs(num(r,metric)-value),r['filename']))
                pools.append((f'{scale}:{metric}:{band}',group))
    return pools


def sample(rows,settings,target=180,cap=5):
    selected={};video_counts=Counter();scale_counts=Counter();coverage=[]
    def choose(pool,category,why,amount):
        taken=0
        while taken<amount:
            candidates=[r for r in pool if r['filename'] not in selected and video_counts[r['video_id']]<cap]
            if not candidates:break
            # Preserve boundary-distance priority within each balanced video/scale choice.
            positions={r['filename']:i for i,r in enumerate(pool)}
            r=min(candidates,key=lambda r:(video_counts[r['video_id']],scale_counts[r['shot_type']],positions[r['filename']],r['filename']))
            selected[r['filename']]=dict(row=r,category=category,sampling_reason=why)
            video_counts[r['video_id']]+=1;scale_counts[r['shot_type']]+=1;taken+=1
        return taken
    # Boundary reservations first; shared samples receive explicit memberships.
    for name,pool in boundary_pools(rows,settings):
        old=[r for r in pool if r['filename'] in selected]
        if not old:choose(pool,'boundary',name,1)
        covered=[r for r in pool if r['filename'] in selected]
        for r in covered:
            item=selected[r['filename']]
            if name not in item['sampling_reason']:item['sampling_reason']+=';'+name
        coverage.append(dict(boundary_stratum=name,available_count=len(pool),selected_count=len(covered),status='covered' if covered else 'empty_in_dataset' if not pool else 'cap_constrained'))
    tail=math.ceil(len(rows)*.1)
    groups=[('eligible_control',25,[r for r in rows if r['face_eligible']=='true']),
            ('face_blurry',30,[r for r in rows if 'face_blurry' in reasons(r)]),
            ('one_eye_occluded',23,[r for r in rows if 'one_eye_occluded' in reasons(r)]),
            ('beauty_filter',23,[r for r in rows if 'beauty_filter_detected' in reasons(r)]),
            ('low_visibility',18,[r for r in rows if 'low_visibility' in reasons(r)]),
            ('exposure',13,[r for r in rows if reasons(r)&{'face_underexposed','face_backlit_underexposed'}]),
            ('low_resolution_small_face',13,[r for r in rows if reasons(r)&{'low_resolution_source','face_too_small'}]),
            ('top_technical_reject',18,[r for r in rows if int(r['quality_rank'])<=tail and r['face_eligible']!='true'])]
    for category,quota,pool in groups:
        existing=sum(item['row'] in pool for item in selected.values())
        # Quotas are overlapping memberships, not exclusive selected-category totals.
        choose(sorted(pool,key=lambda r:(r['video_id'],int(r['temporal_index']))),category,category+' stratified video/scale',max(0,quota-existing))
    choose([r for r in rows if 'multiple_faces' in reasons(r)],'multiple_faces','rare multiple-face Gate coverage',3)
    # Reserve distinct blur mechanism/extremes (diagnostic, not visual truth).
    for name,predicate in [('eye_disabled',lambda r:eye_state(r)=='eye_sharpness_disabled'),('mesh_unavailable',lambda r:eye_state(r)=='facemesh_unavailable'),('eye_measured_low',lambda r:eye_state(r)=='eye_sharpness_measured' and num(r,'eye_sharpness')<settings['min_eye_sharpness']),('laplacian_branch',lambda r:blur_detail(r,settings)['executed_blur_branch']=='face_laplacian'),('extreme_plasticity',lambda r:eye_state(r)=='eye_sharpness_measured' and num(r,'plasticity_ratio')>settings['max_plasticity_ratio']*2)]:
        pool=sorted([r for r in rows if predicate(r)],key=lambda r:(num(r,'plasticity_ratio') if name=='extreme_plasticity' else -num(r,'face_laplacian_score'),r['filename']),reverse=True)
        choose(pool,'mechanism',name,3)
    choose(sorted(rows,key=lambda r:(r['video_id'],int(r['temporal_index']))),'diversity_fill','video/scale coverage',max(0,target-len(selected)))
    result=list(selected.values())[:target]
    # Recalculate final memberships; retain all available-boundary gaps, no fabricated samples.
    for record,(name,pool) in zip(coverage,boundary_pools(rows,settings)):
        record['selected_count']=sum(r['filename'] in {x['row']['filename'] for x in result} for r in pool)
        record['status']='covered' if record['selected_count'] else 'empty_in_dataset' if not pool else 'cap_or_target_constrained'
    return result,coverage


def manifest(samples,subject,generation,settings=None):
    result=[]
    for i,item in enumerate(samples,1):
        r=item['row']
        record=dict(review_id=f'R{i:03d}',subject_context=subject.get(r['video_id'],'') if isinstance(subject,dict) else subject,dataset_generation_id=generation,
                    video_id=r['video_id'],frame_id=r.get('frame_id',r['filename']),filename=r['filename'],
                    review_category=item['category'],sampling_reason=item['sampling_reason'],shot_type=r['shot_type'],
                    global_laplacian=r['laplacian_score'],global_quality_rank=r['quality_rank'],
                    face_laplacian=r['face_laplacian_score'],face_tenengrad=r['face_tenengrad_score'],
                    eye_presence_valid=r['eye_presence_valid'],eye_sharpness=r['eye_sharpness'],
                    eye_metric_state=eye_state(r),eye_threshold_state=blur_detail(r,settings)['eye_threshold_state'] if settings else '',skin_texture=r['skin_texture_score'],plasticity=r['plasticity_ratio'],
                    face_visibility=r['face_visibility_score'],face_brightness=r['face_brightness_mean'],
                    face_gate_reason=r['face_gate_reason'],face_gate_category=r['face_gate_category'],face_eligible=r['face_eligible'])
        record.update({label:'' for label in LABELS});result.append(record)
    return result


def crop_bytes(image,row):
    if not row.get('face_bbox_width'):return None
    box=tuple(int(row[k]) for k in ('face_bbox_x','face_bbox_y','face_bbox_width','face_bbox_height'))
    crop=gate.crop_with_margin(image,box)
    success,data=cv2.imencode('.png',crop)
    if not success:raise ValueError('Crop encoding failed')
    return data.tobytes()


def review_html(records,assets,prefix,settings=None,source_rows=None):
    data=json.dumps(records,ensure_ascii=False).replace('<',chr(92)+'u003c')
    template=(Path(__file__).parent/'templates/step3_calibration.html').read_text(encoding='utf-8')
    source={r['filename']:r for r in (source_rows or [])}
    descriptions={r['review_id']:presentation(source[r['filename']],settings) for r in records} if settings is not None and source_rows is not None else {}
    descriptions_json=json.dumps(descriptions,ensure_ascii=False).replace('<',chr(92)+'u003c')
    return template.replace('__RECORDS__',data).replace('__ASSETS__',json.dumps(assets)).replace('__PACKAGE__',prefix).replace('__PRESENTATIONS__',descriptions_json)


def main():
    config=load_for_cli();parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=int,default=180);parser.add_argument('--video-cap',type=int,default=5)
    parser.add_argument('--config',type=Path);args=parser.parse_args()
    if args.target<1 or args.video_cap<1:parser.error('Positive sampling parameters required')
    project=Path(__file__).resolve().parents[1];reports=resolve_project_path(get_section(config,'paths')['reports_dir'])
    if (reports/'step3_boundary_summary.json').exists():
        raise ValueError('The 180-frame package is superseded. Use scripts/build_step3_boundary_review.py for active review; historical artifacts are preserved.')
    report=resolve_config_path(get_section(config,'step3_face_gate')['output'],config)
    root=resolve_project_path(get_section(config,'paths')['raw_frames_dir']);manifests=resolve_project_path(get_section(config,'paths')['manifests_dir'])
    with manifest_lock(manifests/'.video_manifest.lock'):
        summary=json.loads(report.with_name('step3_summary.json').read_text(encoding='utf-8'))
        step2=resolve_config_path(get_section(config,'step3_face_gate')['report'],config)
        rebuild(report,report.with_name('step3_summary.json'),step2) # validation only, no writes
        _,generation,_=validate_input(step2,root,manifests)
        source_bytes=report.read_bytes();source_sha=hashlib.sha256(source_bytes).hexdigest()
        with io.StringIO(source_bytes.decode('utf-8-sig'),newline='') as f:rows=list(csv.DictReader(f))
        settings=dict(get_section(config,'step3_face_gate'));settings.update({k:v for k,v in summary['arguments'].items() if k in settings})
        gate.FACE_CROP_MARGIN=settings.get('face_crop_margin',gate.FACE_CROP_MARGIN)
        tables=analyze(rows,settings);samples,coverage=sample(rows,settings,args.target,args.video_cap)
        with (manifests/'video_manifest.csv').open(encoding='utf-8-sig',newline='') as f:
            subjects={r['video_id']:r.get('subject_name','') for r in csv.DictReader(f)}
        records=manifest(samples,subjects,generation['sha256'],settings)
        package=hashlib.sha256((source_sha+json.dumps(records,sort_keys=True)+str(args.video_cap)).encode()).hexdigest()[:16]
        assets_root=reports/'step3_calibration_assets'/package;assets_root.mkdir(parents=True,exist_ok=True)
        assets={}
        for item,record in zip(samples,records):
            row=item['row'];source,_=gate.image_path(root,row['filename']);image=cv2.imdecode(np.fromfile(source,dtype=np.uint8),cv2.IMREAD_COLOR)
            if image is None:raise ValueError('Review image decode failed')
            full=assets_root/(record['review_id']+'_full.png');shutil.copy2(source,full)
            crop=crop_bytes(image,row);crop_path=assets_root/(record['review_id']+'_face.png')
            if crop is not None:crop_path.write_bytes(crop)
            assets[record['review_id']]={'full':os.path.relpath(full,project/'docs').replace('\\','/'),'face':os.path.relpath(crop_path,project/'docs').replace('\\','/') if crop is not None else ''}
        names=['step3_gate_contribution.csv','step3_gate_threshold_audit.csv','step3_reason_combinations.csv','step3_counterfactual_analysis.csv','step3_eligible_concentration.csv','step3_blur_decomposition.csv']
        outputs={reports/name:csv_bytes(table) for name,table in zip(names,tables)}
        outputs[reports/'step3_calibration_review.csv']=csv_bytes(records)
        outputs[reports/'step3_calibration_boundary_coverage.csv']=csv_bytes(coverage)
        outputs[project/'docs/STEP3_CALIBRATION_REVIEW.html']=review_html(records,assets,package,settings,rows).encode('utf-8')
        stats_summary=dict(status='PARTIAL' if any(c['available_count'] and not c['selected_count'] for c in coverage) else 'CALIBRATION_READY',gate_calibration_status='AWAITING HUMAN LABELS',source_sha256=source_sha,
                           source_row_count=len(rows),generation=generation,frames=len(records),videos=len({r['video_id'] for r in records}),
                           scales=dict(Counter(r['shot_type'] for r in records)),categories=dict(Counter(r['review_category'] for r in records)),
                           video_cap=args.video_cap,max_samples_per_video=max(Counter(r['video_id'] for r in records).values()),
                           category_memberships={name:sum(predicate(r) for r in records) for name,predicate in [('eligible_control',lambda r:r['face_eligible']=='true'),('face_blurry',lambda r:'face_blurry' in r['face_gate_reason']),('one_eye_occluded',lambda r:'one_eye_occluded' in r['face_gate_reason']),('beauty_filter',lambda r:'beauty_filter_detected' in r['face_gate_reason']),('low_visibility',lambda r:'low_visibility' in r['face_gate_reason']),('exposure',lambda r:'underexposed' in r['face_gate_reason']),('low_resolution_small_face',lambda r:'low_resolution_source' in r['face_gate_reason'] or 'face_too_small' in r['face_gate_reason']),('top_technical_reject',lambda r:int(r['global_quality_rank'])<=math.ceil(len(rows)*.1) and r['face_eligible']=='false')]},
                           eye_states=dict(Counter(r['eye_metric_state'] for r in tables[-1])),eye_threshold_states=dict(Counter(r['eye_threshold_state'] for r in tables[-1])),blur_branches=dict(Counter(r['executed_blur_branch'] for r in tables[-1])),labels_filled=0,thresholds_changed=False,authoritative_data_changed=False,
                           boundary_coverage=coverage,package_id=package,effective_settings=settings)
        outputs[reports/'step3_calibration_summary.json']=(json.dumps(stats_summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
        # Every output is derived. Refuse overwriting labels or prior package drift.
        for destination,data in outputs.items():
            if destination.name=='step3_calibration_review.csv' and destination.exists():
                with destination.open(encoding='utf-8-sig',newline='') as f:old=list(csv.DictReader(f))
                if any(r.get(k) for r in old for k in LABELS):raise ValueError('Existing human labels: preserve/export them before regeneration')
        _,after,_=validate_input(step2,root,manifests)
        if after!=generation or report.read_bytes()!=source_bytes:raise ValueError('Source changed during calibration')
        for destination,data in outputs.items():
            destination.parent.mkdir(parents=True,exist_ok=True)
            fd,temp=tempfile.mkstemp(dir=destination.parent,prefix='.calibration-');os.close(fd)
            try:Path(temp).write_bytes(data);os.replace(temp,destination)
            finally:Path(temp).unlink(missing_ok=True)
        print(json.dumps({k:stats_summary[k] for k in ('status','frames','videos','scales','category_memberships','max_samples_per_video')},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
