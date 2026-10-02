"""Derived REJECT boundary review. Never apply human labels or change STEP3 Gates."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
from collections import Counter
from functools import lru_cache
import cv2
import numpy as np
from common.config import load_for_cli, get_section, resolve_project_path, resolve_config_path
from common.step3_audit import validate_input, csv_bytes
from common.video_manifest import manifest_lock
from common.step3_review_presentation import presentation, backlight_ceiling
from build_step3_calibration import crop_bytes
from build_step3_reports import rebuild
import face_quality_gate as gate

boundary_ceiling = lru_cache(maxsize=1)(backlight_ceiling)

ORDER = ('eye_sharpness','face_laplacian','eye_presence','skin_texture','plasticity',
         'visibility','exposure','face_size','global_blur')
TARGETS = dict(zip(ORDER,(13,13,10,7,5,6,6,4,3)))
TITLES = dict(zip(ORDER,('Eye Sharpness','Face Laplacian','Eye Presence','Skin Texture',
                        'Plasticity','Visibility','Exposure','Face Size','Global Blur')))
QUESTIONS = dict(zip(ORDER,(
    'この程度の目の鮮明さはLoRA学習素材として許容できますか？',
    'この程度の顔の鮮明さはLoRA学習素材として許容できますか？',
    'この目の見え方はLoRA学習素材として許容できますか？',
    'この程度の肌の質感・加工は許容できますか？',
    'この程度の目と肌の質感差・加工は許容できますか？',
    'この程度の顔の見えやすさは許容できますか？',
    'この程度の顔の明るさ・逆光は許容できますか？',
    'この顔のサイズ・画像解像度は許容できますか？',
    'この程度の画像全体の鮮明さは許容できますか？')))


def num(r,k):
    return float(r[k]) if r.get(k) else None


def boundary_memberships(r,s):
    """Windows are user-requested REVIEW sampling bands, not rejection thresholds.

    Scale bands with recorded thresholds to keep the sampler reusable. Never
    sample invalid/zero-proxy anatomical metrics as measured blur boundaries.
    Eye presence values/derived asymmetry are rounded-source diagnostics only.
    """
    if r['face_eligible']!='false' or r.get('face_gate_status')!='ok' or r.get('face_detected')!='true':
        return {}
    mesh=r.get('facemesh_detected')=='true'; body=r['shot_type']=='FULL_BODY'
    valid=r.get('eye_presence_valid')=='true'; reasons=set(r['face_gate_reason'].split(';'))
    result={}
    def add(name, measured, threshold, distance, band):
        result[name]=dict(human_gate_name=name,title=TITLES[name],question=QUESTIONS[name],
                          measured_value=str(measured),threshold=threshold,distance=distance,band=band)
    e=num(r,'eye_sharpness'); t=s['min_eye_sharpness']
    if mesh and valid and not body and e is not None and .75*t<=e<=1.0625*t:
        # At the current 1.6 threshold: [1.2,1.4), [1.4,1.5), [1.5,1.6), [1.6,1.7].
        band=sum(e>=v*t for v in (.875,.9375,1))
        add('eye_sharpness',r['eye_sharpness'],f'>= {t:g}',abs(e/t-1),f'eye_band_{band}')
    lap=num(r,'face_laplacian_score');t=s['min_face_laplacian']
    if lap is not None and .5*t<=lap<t:
        add('face_laplacian',r['face_laplacian_score'],f'>= {t:g}',abs(lap/t-1),
            'lap_band_'+str(sum(lap>=v*t for v in (.7,.8,.9))))
    if mesh and not body and 'one_eye_occluded' in reasons:
        left=num(r,'left_eye_presence_ratio');right=num(r,'right_eye_presence_ratio')
        if left is not None and right is not None:
            single=min(left,right);avg=(left+right)/2;asym=max(left,right)/max(single,.0001)
            a=s['min_single_eye_feature_ratio'];b=s['min_avg_eye_feature_ratio'];c=s['max_eye_asymmetry_ratio']
            near=(.055/.07*a<=single<=.075/.07*a or .065/.08*b<=avg<=.085/.08*b or 1.8/2.2*c<=asym<=2.4/2.2*c)
            if near:
                add('eye_presence',f'left={left:g}; right={right:g}; min={single:g}; avg={avg:.6g}; asym={asym:.6g}',
                    f'single >= {a:g}; average >= {b:g}; asymmetry <= {c:g}',
                    min(abs(single/a-1),abs(avg/b-1),abs(asym/c-1)),'eye_presence')
    if mesh and not body and not s.get('skip_beauty_filter',False):
        skin=num(r,'skin_texture_score');t=s['min_skin_texture_close_up'] if r['shot_type']=='CLOSE_UP' else s['min_skin_texture_upper_body']
        low,high=(.7,1.2) if r['shot_type']=='CLOSE_UP' else (.025/.035,.045/.035)
        if skin is not None and low*t<=skin<=high*t:
            add('skin_texture',r['skin_texture_score'],f'>= {t:g}',abs(skin/t-1),r['shot_type'])
        plastic=num(r,'plasticity_ratio');t=s['max_plasticity_ratio']
        if plastic is not None and 35/45*t<=plastic<=55/45*t:
            add('plasticity',r['plasticity_ratio'],f'<= {t:g}',abs(plastic/t-1),'plasticity')
    visible=num(r,'face_visibility_score');t=s['min_face_visibility_score']
    if mesh and visible is not None and 55/70*t<=visible<=75/70*t:
        add('visibility',r['face_visibility_score'],f'>= {t:g}',abs(visible/t-1),'visibility')
    bright=num(r,'face_brightness_mean');ratio=num(r,'face_to_global_brightness_ratio');t=s['min_face_brightness'];c=s['min_face_to_global_ratio'];ceiling=boundary_ceiling()
    exposure_near=bright is not None and 80/95*t<=bright<=100/95*t
    backlight_near=bright is not None and ratio is not None and ceiling-10<=bright<=ceiling+5 and c-.1<=ratio<=c+.1
    if exposure_near or backlight_near:
        distance=min(abs(bright/t-1),abs(ratio/c-1) if backlight_near else 100)
        add('exposure',f'brightness={bright:g}; ratio={ratio if ratio is not None else "unavailable"}',f'brightness >= {t:g}; backlight reject: brightness < {ceiling:g} AND ratio < {c:g} (after brightness gate)',distance,'backlight' if backlight_near else 'brightness')
    t=s[{'CLOSE_UP':'min_face_dim_close_up','UPPER_BODY':'min_face_dim_upper_body','FULL_BODY':'min_face_dim_full_body'}[r['shot_type']]]
    dim=num(r,'face_min_dimension');edge=num(r,'source_short_edge');resolution=s['min_source_short_edge_fullbody']
    if (dim is not None and .85*t<=dim<=1.1*t) or (body and edge is not None and .85*resolution<=edge<=1.1*resolution):
        add('face_size',f'face short edge={dim:g}; source short edge={edge:g}',f'face >= {t:g}px; FULL_BODY source >= {resolution:g}px',min(abs(dim/t-1),abs(edge/resolution-1) if body else 100),r['shot_type'])
    glob=num(r,'laplacian_score');t=s['min_global_laplacian']
    if glob is not None and .8*t<=glob<=1.2*t:
        add('global_blur',r['laplacian_score'],f'>= {t:g}',abs(glob/t-1),'global')
    return result


def hard_failures(r,s):
    """Audit applicable predicates independently, including the masked blur branch.

    No production decision is changed. Stored beauty=False proves both OR
    conditions passed. With beauty=True, rounded intervals must establish which
    component failed; ambiguous attribution cannot qualify as isolated.
    """
    failures=set()
    body=r['shot_type']=='FULL_BODY'
    def minimum(name,key,threshold):
        value=num(r,key)
        if value is None or value<threshold:failures.add(name)
    if r.get('face_count')!='1':failures.add('face_count')
    if r.get('face_detected')!='true' or r.get('facemesh_detected')!='true':failures.add('facemesh')
    minimum('global_blur','laplacian_score',s['min_global_laplacian'])
    minimum('face_laplacian','face_laplacian_score',s['min_face_laplacian'])
    if not body:
        minimum('eye_sharpness','eye_sharpness',s['min_eye_sharpness'])
        if r.get('eye_presence_valid')!='true':failures.add('eye_presence')
    minimum('visibility','face_visibility_score',s['min_face_visibility_score'])
    minimum('face_brightness','face_brightness_mean',s['min_face_brightness'])
    bright=num(r,'face_brightness_mean');ratio=num(r,'face_to_global_brightness_ratio')
    if bright is None or ratio is None:failures.add('exposure_unknown')
    elif bright>=s['min_face_brightness'] and bright<boundary_ceiling() and ratio<s['min_face_to_global_ratio']:failures.add('backlight')
    size_key={'CLOSE_UP':'min_face_dim_close_up','UPPER_BODY':'min_face_dim_upper_body','FULL_BODY':'min_face_dim_full_body'}.get(r['shot_type'])
    if size_key:minimum('face_dimension','face_min_dimension',s[size_key])
    else:failures.add('scale_unknown')
    if body:minimum('source_resolution','source_short_edge',s['min_source_short_edge_fullbody'])
    gradient=num(r,'face_central_gradient')
    if gradient is None or gradient>s['max_face_central_gradient']:failures.add('hair_covered_face')
    if not body and not s.get('skip_beauty_filter',False):
        state=r.get('beauty_filter_detected')
        if state=='true':
            skin=num(r,'skin_texture_score');plastic=num(r,'plasticity_ratio')
            skin_min=s['min_skin_texture_close_up'] if r['shot_type']=='CLOSE_UP' else s['min_skin_texture_upper_body']
            if skin is None or plastic is None:failures.add('beauty_unresolved')
            else:
                # Half the stored precision is uncertainty, NOT a new Gate threshold.
                if skin+.0005<skin_min:failures.add('skin_texture')
                elif skin-.0005<skin_min:failures.add('beauty_unresolved')
                if plastic-.05>s['max_plasticity_ratio']:failures.add('plasticity')
                elif plastic+.05>s['max_plasticity_ratio']:failures.add('beauty_unresolved')
                if not failures&{'skin_texture','plasticity','beauty_unresolved'}:failures.add('beauty_unresolved')
        elif state=='false':
            skin=num(r,'skin_texture_score');plastic=num(r,'plasticity_ratio')
            skin_min=s['min_skin_texture_close_up'] if r['shot_type']=='CLOSE_UP' else s['min_skin_texture_upper_body']
            if skin is None or plastic is None or skin+.0005<skin_min or plastic-.05>s['max_plasticity_ratio']:failures.add('beauty_unresolved')
        else:failures.add('beauty_unresolved')
    return failures


def memberships(r,s):
    near=boundary_memberships(r,s)
    if not near:return {}
    failed=hard_failures(r,s)
    if len(failed)!=1:return {}
    predicate=next(iter(failed))
    name={'face_brightness':'exposure','backlight':'exposure','face_dimension':'face_size','source_resolution':'face_size'}.get(predicate,predicate)
    reason={'eye_sharpness':'face_blurry','face_laplacian':'face_blurry','eye_presence':'one_eye_occluded',
            'skin_texture':'beauty_filter_detected','plasticity':'beauty_filter_detected','visibility':'low_visibility',
            'face_brightness':'face_underexposed','backlight':'face_backlit_underexposed','face_dimension':'face_too_small',
            'source_resolution':'low_resolution_source','global_blur':'global_blurry'}.get(predicate)
    if name not in near or set(r['face_gate_reason'].split(';'))!={reason}:return {}
    # For grouped size/exposure families, require the failing component itself near.
    if predicate=='face_dimension':
        threshold=s[{'CLOSE_UP':'min_face_dim_close_up','UPPER_BODY':'min_face_dim_upper_body','FULL_BODY':'min_face_dim_full_body'}[r['shot_type']]]
        if num(r,'face_min_dimension')<.85*threshold:return {}
    if predicate=='source_resolution' and num(r,'source_short_edge')<.85*s['min_source_short_edge_fullbody']:return {}
    if predicate=='face_brightness' and num(r,'face_brightness_mean')<80/95*s['min_face_brightness']:return {}
    if predicate=='backlight' and not (boundary_ceiling()-10<=num(r,'face_brightness_mean')<=boundary_ceiling()+5 and s['min_face_to_global_ratio']-.1<=num(r,'face_to_global_brightness_ratio')<=s['min_face_to_global_ratio']+.1):return {}
    target=dict(near[name],target_predicate=predicate,target_result='FAIL',other_hard_gates='ALL PASS',other_failure_count=0)
    return {name:target}


def select(rows,s,target=45,video_cap=3):
    candidates={r['filename']:(r,memberships(r,s)) for r in rows}
    candidates={k:v for k,v in candidates.items() if v[1]}
    chosen={};counts=Counter();bands=Counter()
    def choose(name,quota):
        while sum(name in v[1] for v in chosen.values())<quota and len(chosen)<target:
            pool=[v for k,v in candidates.items() if k not in chosen and name in v[1] and counts[v[0]['video_id']]<video_cap]
            if not pool:break
            r,m=min(pool,key=lambda v:(bands[(name,v[1][name]['band'])],counts[v[0]['video_id']],v[1][name]['distance'],v[0]['filename']))
            chosen[r['filename']]=(r,m);counts[r['video_id']]+=1
            for g,d in m.items():bands[(g,d['band'])]+=1
    for name in ORDER:choose(name,TARGETS[name])
    # No quota filling or fallback: return only available isolated failures.
    return list(chosen.values()),{g:sum(g in m for _,m in candidates.values()) for g in ORDER}


def review_data(selected,s,generation,subjects):
    records=[];sidecar=[]
    for i,(r,m) in enumerate(selected,1):
        if len(m)!=1 or len(hard_failures(r,s))!=1 or not memberships(r,s):
            raise ValueError('Not an isolated failing boundary: '+r['filename'])
        record=dict(review_id=f'B{i:03d}',subject_context=subjects.get(r['video_id'],''),dataset_generation_id=generation,
                    video_id=r['video_id'],frame_id=r.get('frame_id',r['filename']),filename=r['filename'],shot_type=r['shot_type'],
                    face_eligible=r['face_eligible'],face_gate_reason=r['face_gate_reason'],boundaries=list(m.values()),presentation=presentation(r,s))
        # Every card distinguishes its diagnostic result from the recorded execution path.
        reasons=set(r['face_gate_reason'].split(';'));eye_branch=r['shot_type']!='FULL_BODY' and (num(r,'eye_sharpness') or 0)<s['min_eye_sharpness']
        mapping={'laplacian_score':'global_blurry','face_laplacian_score':'face_blurry','eye_sharpness':'face_blurry',
                 'eye_presence_valid':'one_eye_occluded','skin_texture_score':'beauty_filter_detected','plasticity_ratio':'beauty_filter_detected',
                 'face_visibility_score':'low_visibility','face_brightness_mean':'face_underexposed','face_to_global_brightness_ratio':'face_backlit_underexposed',
                 'face_min_dimension':'face_too_small','source_short_edge':'low_resolution_source','face_central_gradient':'hair_covered_face'}
        meanings={'laplacian_score':'画像全体の輪郭・細部の鮮明さ。背景にも影響されます。','face_laplacian_score':'顔中央部の輪郭・細部の鮮明さ。',
                  'eye_sharpness':'目のパッチの勾配から測る鮮明さ。','eye_presence_valid':'左右の目の特徴量・平均・左右差による遮蔽の疑い。',
                  'skin_texture_score':'頬の細かな質感を明るさで正規化した値。','plasticity_ratio':'目の鮮明さと頬の質感の比。',
                  'face_visibility_score':'顔のランドマークから推定する見えやすさ。','face_brightness_mean':'顔cropの平均輝度。',
                  'face_to_global_brightness_ratio':'顔の明るさ ÷ 画像全体の明るさ。','face_min_dimension':'顔bboxの短辺。STEP4の正式な構図分類ではありません。',
                  'source_short_edge':'元画像の幅・高さの小さい方。','face_central_gradient':'顔中央の強い勾配。髪の遮蔽を疑うheuristic。','face_count':'顔の検出人数とランドマーク取得状況。'}
        for c in record['presentation']['cards']:
            reason=mapping.get(c['field']);used=reason in reasons if reason else False
            if c['field']=='face_laplacian_score' and eye_branch:used=False
            if c['field']=='eye_sharpness' and not eye_branch:used=False
            c['meaning']=meanings[c['field']]
            if c['field']=='eye_presence_valid' and r.get('left_eye_presence_ratio') and r.get('right_eye_presence_ratio'):
                left=num(r,'left_eye_presence_ratio');right=num(r,'right_eye_presence_ratio');single=min(left,right)
                c['value']=f'左 {left:g} ／右 {right:g} ／平均 {(left+right)/2:.6g} ／左右比 {max(left,right)/max(single,.0001):.6g}'
                c['detail']+=' 平均・左右比は丸め後CSVからの参考再計算。正式判定は保存済みstateを維持。'
            c['pass_fail']={'bad':'FAIL','good':'PASS','off':'N/A','unknown':'UNKNOWN'}[c['status']]
            c['reject_used']=('YES：'+reason if used and reason else 'YES：人数・FaceMesh条件' if used else 'NO：今回の拒否には使用されていません')
            if reason=='beauty_filter_detected' and used:c['reject_used']='YES：beauty_filter_detected（肌・比率のOR条件。丸め後CSVでは原因の個別確定は不可）'
            if c['field'] in ('skin_texture_score','plasticity_ratio') and c['status']!='off':
                component='skin_texture' if c['field']=='skin_texture_score' else 'plasticity'
                is_target=next(iter(m.values()))['target_predicate']==component
                c.update(status='bad' if is_target else 'good',pass_fail='FAIL' if is_target else 'PASS',
                         judgment='単独の拒否原因' if is_target else '保存済みbeauty判定・丸め誤差範囲を確認してPASS',
                         reject_used='YES：beauty_filter_detected（'+component+'単独）' if is_target else 'NO：今回の拒否には使用されていません')
        records.append(record)
        for d in m.values():
            sidecar.append({k:record[k] for k in ('review_id','subject_context','dataset_generation_id','video_id','frame_id','filename')}|
                           dict(human_gate_name=d['human_gate_name'],measured_value=d['measured_value'],threshold=d['threshold'],sampling_band=d['band'],human_accept='',human_notes=''))
    return records,sidecar


def render(records,assets,package):
    template=(Path(__file__).parent/'templates/step3_boundary_review.html').read_text(encoding='utf-8')
    return template.replace('__DATA__',json.dumps(records,ensure_ascii=False).replace('<','\\u003c')).replace('__ASSETS__',json.dumps(assets)).replace('__PACKAGE__',package)


def publish(path,data):
    staged=path.with_name(path.name+'.tmp');staged.write_bytes(data);os.replace(staged,path)


def main():
    config=load_for_cli();parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--target',type=int,default=45);parser.add_argument('--video-cap',type=int,default=3);parser.add_argument('--config',type=Path);args=parser.parse_args()
    if not 1<=args.target<=60 or args.video_cap<1:parser.error('Review maximum must be 1–60; video cap positive')
    project=Path(__file__).resolve().parents[1];reports=resolve_project_path(get_section(config,'paths')['reports_dir']);root=resolve_project_path(get_section(config,'paths')['raw_frames_dir']);manifests=resolve_project_path(get_section(config,'paths')['manifests_dir'])
    source=resolve_config_path(get_section(config,'step3_face_gate')['output'],config);step2=resolve_config_path(get_section(config,'step3_face_gate')['report'],config)
    with manifest_lock(manifests/'.video_manifest.lock'):
        rebuild(source,source.with_name('step3_summary.json'),step2)
        _,generation,_=validate_input(step2,root,manifests)
        source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        with source.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        summary=json.loads(source.with_name('step3_summary.json').read_text(encoding='utf-8'))
        settings=dict(get_section(config,'step3_face_gate'));settings.update({k:v for k,v in summary['arguments'].items() if k in settings})
        selected,available=select(rows,settings,args.target,args.video_cap)
        with (manifests/'video_manifest.csv').open(encoding='utf-8-sig',newline='') as f:subjects={r['video_id']:r.get('subject_name','') for r in csv.DictReader(f)}
        records,labels=review_data(selected,settings,generation['sha256'],subjects)
        if len({r['frame_id'] for r in records})!=len(records):raise ValueError('Duplicate active frame IDs')
        package=hashlib.sha256((source_hash+json.dumps(records,sort_keys=True,ensure_ascii=False)).encode()).hexdigest()[:16]
        labels_path=reports/'step3_boundary_labels.csv'
        previous_boundary_path=reports/'step3_boundary_summary.json'
        if previous_boundary_path.exists():
            previous_boundary=json.loads(previous_boundary_path.read_text(encoding='utf-8'))
            if previous_boundary.get('package_id')!=package:
                old_package=previous_boundary['package_id'];archive=reports/'step3_boundary_audit/superseded'/old_package;archive.mkdir(parents=True,exist_ok=True)
                for name in ('step3_boundary_summary.json','step3_boundary_review.json','step3_boundary_labels.csv'):
                    old_file=reports/name;archived=archive/name
                    if old_file.exists() and not archived.exists():shutil.copy2(old_file,archived)
                    if old_file.exists() and archived.read_bytes()!=old_file.read_bytes():raise ValueError('Historical archive differs; protect existing labels')
                old_html=project/'docs'/f'STEP3_BOUNDARY_REVIEW_SUPERSEDED_{old_package}.html'
                active_html=project/'docs/STEP3_CALIBRATION_REVIEW.html'
                if active_html.exists() and not old_html.exists():shutil.copy2(active_html,old_html)
        if labels_path.exists():
            with labels_path.open(encoding='utf-8-sig',newline='') as f:existing=list(csv.DictReader(f))
            if any(r.get('human_accept') or r.get('human_notes') for r in existing):
                if [{k:v for k,v in r.items() if k not in ('human_accept','human_notes')} for r in existing]==[{k:v for k,v in r.items() if k not in ('human_accept','human_notes')} for r in labels]:labels=existing
                elif not previous_boundary_path.exists() or previous_boundary.get('package_id')==package:raise ValueError('Existing human labels protected; archive before changing package')
        gate.FACE_CROP_MARGIN=settings['face_crop_margin'];assets_root=reports/'step3_boundary_assets'/package;assets_root.mkdir(parents=True,exist_ok=True);assets={}
        for (r,_),record in zip(selected,records):
            source_image,_=gate.image_path(root,r['filename']);full=assets_root/(record['review_id']+'_full.png');shutil.copy2(source_image,full)
            image=cv2.imdecode(np.fromfile(source_image,dtype=np.uint8),cv2.IMREAD_COLOR)
            if image is None:raise ValueError('Cannot decode '+r['filename'])
            crop=crop_bytes(image,r);face=assets_root/(record['review_id']+'_face.png')
            if crop is not None:face.write_bytes(crop)
            assets[record['review_id']]=dict(full=os.path.relpath(full,project/'docs').replace('\\','/'),face=os.path.relpath(face,project/'docs').replace('\\','/') if crop is not None else '')
        assert all(r['face_eligible']=='false' for r in records)
        old_summary=reports/'step3_calibration_summary.json'
        previous=json.loads(old_summary.read_text(encoding='utf-8')) if old_summary.exists() else {}
        historic=project/'docs'/('STEP3_CALIBRATION_REVIEW_SUPERSEDED_'+previous.get('package_id','legacy')+'.html')
        active=project/'docs/STEP3_CALIBRATION_REVIEW.html'
        if active.exists() and not historic.exists() and 'REJECT Boundary Review' not in active.read_text(encoding='utf-8'):shutil.copy2(active,historic)
        counts={g:sum(g in m for _,m in selected) for g in ORDER};total_memberships=sum(counts.values())
        result=dict(status='READY_FOR_HUMAN_BOUNDARY_REVIEW',package_id=package,source_sha256=source_hash,generation=generation,
                    source_rows=len(rows),total_review_frames=len(records),eligible_included=0,boundary_samples=counts,available_boundary_samples=available,
                    duplicate_frames_removed=total_memberships-len(records),deduplication_definition='selected Gate memberships minus unique frames',
                    videos_represented=len({r['video_id'] for r in records}),max_frames_per_video=max(Counter(r['video_id'] for r in records).values(),default=0),
                    selection_rule='single failing target near threshold; all other applicable hard gates PASS',multi_hard_gate_failures_included=0,
                    effective_settings=settings,authoritative_step3_data_changed=False,gate_threshold_changed=False,ready_for_maru_boundary_review=True,
                    superseded_package_id=previous.get('package_id'),superseded_html=historic.name,sampling_targets=TARGETS,
                    sampling_shortfalls={g:TARGETS[g]-counts[g] for g in ORDER if counts[g]<TARGETS[g]},human_labels_applied=False)
        if hashlib.sha256(source.read_bytes()).hexdigest()!=source_hash:raise ValueError('Source changed during review generation')
        publish(reports/'step3_boundary_review.json',json.dumps(records,ensure_ascii=False,indent=2).encode('utf-8'))
        label_fields=['review_id','subject_context','dataset_generation_id','video_id','frame_id','filename','human_gate_name','measured_value','threshold','sampling_band','human_accept','human_notes']
        publish(labels_path,csv_bytes(labels,label_fields))
        publish(reports/'step3_boundary_summary.json',json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8'))
        publish(active,render(records,assets,package).encode('utf-8'))
        print(json.dumps({k:result[k] for k in ('status','total_review_frames','eligible_included','boundary_samples','videos_represented','sampling_shortfalls')}))


if __name__=='__main__':main()
