"""BEST v2: comparable bounded quality + small kind bonus - measured evidence.
All point-valued *_penalty fields and totals are on the same 0..100 score scale.
Historical v1 is retained only for audit, never used by the production entrypoint.
"""
from bisect import bisect_left, bisect_right
from collections import defaultdict, Counter
import math
from common.best_ranking_v1 import number, mean_available, fatal_reason, POSITIVE, PENALTIES, METRICS

VERSION = 'best_rank_v2'
QUALITY_METRICS = ('face_laplacian_canonical_192','face_tenengrad_canonical_192',
                   'left_eye_local_detail','right_eye_local_detail','mouth_local_detail',
                   'local_face_contrast','face_area_ratio')

def clip(value):return max(0.,min(1.,value))
def deficit(value,normal):return None if value is None else clip((normal-value)/normal)
def truth(value):return str(value).lower()

def percentile(values,q):
    if not values:return None
    position=(len(values)-1)*q;lo=int(position);hi=math.ceil(position)
    return values[lo]+(values[hi]-values[lo])*(position-lo)

def effective_settings(settings,config=None):
    from common.revision_a import load_review_settings
    from common.config import load_config
    config=config or load_config()
    diagnostic,path,digest=load_review_settings(settings.get('diagnostic_config'))
    gate=config['step3_face_gate']
    result=dict(settings)
    result['_evidence']=dict(diagnostic,
        face_detail_anchor=gate['min_face_laplacian_canonical'],
        eye_detail_anchor=gate['min_eye_sharpness'],
        eye_presence_anchor=gate['min_single_eye_feature_ratio'],
        face_brightness_anchor=gate['min_face_brightness'],
        frontal_yaw_max=config['step4_pose']['front_yaw_max'])
    result['_diagnostic_sha256']=digest
    return result

def fit_context(rows,settings):
    """Fit positive anchors/bonus pools only; no scores or production ranks."""
    eligible=[r for r in rows if not fatal_reason(r)]
    low=settings.get('anchor_low',.05);high=settings.get('anchor_high',.95)
    if not 0<=low<high<=1:raise ValueError('Invalid positive anchor quantiles')
    anchors={};pools=defaultdict(list)
    for metric in QUALITY_METRICS:
        values=sorted(v for r in eligible if (v:=number(r.get(metric))) is not None)
        anchors[metric]=dict(low=percentile(values,low),high=percentile(values,high),count=len(values))
    for r in eligible:
        for metric in QUALITY_METRICS+('face_visibility_score',):
            v=number(r.get(metric))
            if v is not None:pools[(r['input_kind'],metric)].append(v)
    for values in pools.values():values.sort()
    return dict(anchors=anchors,pools=pools)

def normalized(value,anchor):
    if value is None or anchor['low'] is None:return None
    if anchor['high']==anchor['low']:return .5 # Uninformative constant pool, no defect claim.
    return clip((value-anchor['low'])/(anchor['high']-anchor['low']))

def defect_evidence(row,settings):
    """No percentile/normalization context enters this function."""
    e=settings['_evidence'];n=lambda k:number(row.get(k))
    states={};strength={}
    def put(k,value,reason):strength[k]=value;states[k]=reason if value is not None else 'UNAVAILABLE'
    visibility=n('face_visibility_score')
    put('visibility_obstruction',None if visibility is None else 1-clip(visibility/100),'measured_visibility_deficit_proxy')
    # Pixel presence is only weak evidence, requiring measured OPEN frontal eyes.
    left=n('left_eye_presence');right=n('right_eye_presence');yaw=n('yaw')
    eye_state=row.get('eye_openness_state','UNKNOWN')
    if truth(row.get('legacy_eye_presence_valid'))=='true':
        put('eye_obstruction',0.,'presence_valid_no_external_occlusion_evidence')
    elif left is None or right is None or yaw is None:
        put('eye_obstruction',None,'UNAVAILABLE')
    elif (truth(row.get('legacy_eye_presence_valid'))=='false' and eye_state=='OPEN'
          and abs(yaw)<=e['frontal_yaw_max'] and row.get('eye_measurement_availability')=='MEASURED'):
        put('eye_obstruction',settings.get('weak_evidence_scale',.25)*deficit(min(left,right),e['eye_presence_anchor']),
            'weak_frontal_open_eye_pixel_presence_deficit_not_confirmed_occluder')
    else:put('eye_obstruction',0.,'insufficient_external_occlusion_evidence')
    if eye_state=='OPEN':put('half_eye',0.,'OPEN')
    elif eye_state=='CLOSED_OR_BLINK':put('half_eye',1.,'existing_CLOSED_OR_BLINK_diagnostic')
    elif eye_state=='BORDERLINE':put('half_eye',.5,'existing_BORDERLINE_diagnostic')
    else:put('half_eye',None,'UNAVAILABLE')
    # Existing 2%/10% diagnostic bins supply the slack/ramp, never new rejection.
    clipping=n('highlight_clip_ratio')
    put('clipping',None if clipping is None else clip((clipping-e['clip_borderline'])/(e['clip_overexposed']-e['clip_borderline'])),
        'measured_clip_ratio_existing_diagnostic_slack')
    brightness=n('face_brightness_mean');dynamic=n('dynamic_range_p95_p5');contrast=n('local_face_contrast')
    loss=deficit(contrast,e['contrast_borderline_max'])
    put('low_contrast',loss,'local_contrast_below_existing_diagnostic_normal_boundary')
    # Same pixel-span units: a small dynamic range must corroborate low contrast.
    haze=None
    if all(v is not None for v in (brightness,dynamic,contrast)):
        haze=clip((brightness-e['bright_pixel_min'])/(255-e['bright_pixel_min']))*deficit(dynamic,e['contrast_borderline_max'])*loss
    put('haze',haze,'bright_face_AND_low_dynamic_range_AND_low_local_contrast')
    shadow=n('face_shadow_ratio')
    shadow_strength=None
    if all(v is not None for v in (shadow,brightness,contrast)):
        shadow_strength=clip(shadow)*deficit(brightness,e['face_brightness_anchor'])*loss
    put('shadow',shadow_strength,'shadow_area_AND_low_brightness_AND_low_local_contrast')
    # Two independently located measurements must agree. The second-largest
    # deficit enforces agreement: Laplacian alone or one weak eye cannot penalize.
    detail=[deficit(n('face_laplacian_canonical_192'),e['face_detail_anchor']),
            deficit(n('left_eye_local_detail'),e['eye_detail_anchor']),
            deficit(n('right_eye_local_detail'),e['eye_detail_anchor'])]
    measured=sorted((v for v in detail if v is not None),reverse=True)
    put('blur',measured[1] if len(measured)>=2 else None,'two_of_canonical_laplacian_left_eye_right_eye_agree_low_detail')
    return strength,states

def score_row(original,settings,context):
    # Remove derived v1/v2 score fields; preserve measurements, lineage and diagnostics.
    prefixes=('norm_','component_','contribution_','availability_','penalty_','deduction_',
              'relative_quality_bonus_','evidence_','quality_anchor_')
    old_fields={'positive_total','penalty_total','best_score','global_rank','metric_availability',
                'pose_eye_expectation','analysis_uncertainty_context','ranking_explanation',
                'absolute_quality_total','relative_quality_bonus','ranking_version'}
    row={k:v for k,v in original.items() if not k.startswith(prefixes) and k not in old_fields and not k.endswith(('_abs','_penalty'))}
    reason=fatal_reason(row)
    row.update(ranking_version=VERSION,fatal_reject=str(bool(reason)).lower(),fatal_reject_reason=reason,
               ranking_eligible=str(not reason).lower(),global_rank='',best_score='')
    # Keep a stable audit schema even for an all-fatal generation.
    for key in ('absolute_quality_total','relative_quality_bonus','penalty_total',
                'sharpness_abs','tenengrad_abs','eye_detail_abs','mouth_detail_abs','contrast_abs','visibility_abs'):
        row[key]=''
    for key in ('visibility_obstruction','eye_obstruction','half_eye','clipping','haze','shadow','low_contrast','blur','uncertainty'):
        row[key+'_penalty']=''
    for key in POSITIVE:
        row['relative_quality_bonus_'+key]=''
    if reason:return row
    n=lambda k:number(row.get(k));abs_values={};relative={}
    for metric in QUALITY_METRICS:
        abs_values[metric]=normalized(n(metric),context['anchors'][metric])
        row['norm_'+metric]='' if abs_values[metric] is None else abs_values[metric]
    abs_values['face_visibility_score']=None if n('face_visibility_score') is None else clip(n('face_visibility_score')/100)
    for metric in QUALITY_METRICS+('face_visibility_score',):
        values=context['pools'].get((row['input_kind'],metric),[]);v=n(metric)
        relative[metric]=(bisect_left(values,v)+bisect_right(values,v))/(2*len(values)) if v is not None and values else None
    strengths,states=defect_evidence(row,settings)
    exposure_values=[strengths[k] for k in ('clipping','haze','shadow')]
    exposure=None if any(v is None for v in exposure_values) else 1-max(exposure_values)
    def components(values):
        return dict(sharpness=mean_available([values[QUALITY_METRICS[0]],values[QUALITY_METRICS[1]]]),
                    eye_detail=mean_available([values[QUALITY_METRICS[2]],values[QUALITY_METRICS[3]]]),
                    mouth_detail=values['mouth_local_detail'],contrast=values['local_face_contrast'],
                    visibility=values['face_visibility_score'],face_size=values['face_area_ratio'],exposure=exposure)
    absolute=components(abs_values);bonus=components(relative)
    # Exposure is already semantic, not a group-rank bonus; keep its weight unused in bonus.
    bonus['exposure']=None
    coverage={k:float(v is not None) for k,v in absolute.items()}
    coverage['sharpness']=sum(abs_values[k] is not None for k in QUALITY_METRICS[:2])/2
    coverage['eye_detail']=sum(abs_values[k] is not None for k in QUALITY_METRICS[2:4])/2
    weights=settings.get('positive_weights',POSITIVE);penalties=settings.get('penalty_weights',PENALTIES)
    a_scale=settings.get('absolute_share',.9);r_scale=settings.get('relative_share',.1)
    if set(weights)!=set(POSITIVE) or set(penalties)!=set(PENALTIES):raise ValueError('Unexpected score weights')
    if not math.isclose(sum(weights.values()),1) or not math.isclose(a_scale+r_scale,1) or a_scale<.8 or not 0<=r_scale<=.2:
        raise ValueError('Absolute quality must dominate; positive weights/shares must sum to one')
    if any(number(v) is None or v<0 for v in (*weights.values(),*penalties.values())):raise ValueError('Invalid weights')
    absolute_total=relative_total=0.
    for k in weights:
        value=absolute[k];bv=bonus[k]
        row['component_'+k]='' if value is None else value
        row['availability_'+k]=coverage[k]
        row['contribution_'+k]=100*a_scale*weights[k]*(value or 0)*coverage[k]
        row['relative_quality_bonus_'+k]=100*r_scale*weights[k]*(bv or 0)*coverage[k]
        absolute_total+=row['contribution_'+k];relative_total+=row['relative_quality_bonus_'+k]
    for k,metric in (('sharpness',QUALITY_METRICS[0]),('tenengrad',QUALITY_METRICS[1]),('mouth_detail','mouth_local_detail'),('contrast','local_face_contrast'),('visibility','face_visibility_score')):
        row[k+'_abs']='' if abs_values[metric] is None else abs_values[metric]
    row['eye_detail_abs']='' if absolute['eye_detail'] is None else absolute['eye_detail']
    available=sum(weights[k]*coverage[k] for k in weights)
    strengths['uncertainty']=settings.get('weak_evidence_scale',.25)*(1-available)
    states['uncertainty']='missing_positive_measurement_coverage'
    # Split the existing obstruction/clipping_haze budgets; do not increase them.
    pw=dict(blur=penalties['blur'],visibility_obstruction=penalties['obstruction']/2,
            eye_obstruction=penalties['obstruction']/2,half_eye=penalties['half_eye'],
            clipping=penalties['clipping_haze']/2,haze=penalties['clipping_haze']/2,
            shadow=penalties['shadow'],low_contrast=penalties['low_contrast'],uncertainty=penalties['uncertainty'])
    penalty_total=0.
    for k,value in strengths.items():
        row['evidence_'+k]=states[k];row['penalty_strength_'+k]='' if value is None else value
        row[k+'_penalty']='' if value is None else 100*pw[k]*value
        row['deduction_'+k]=100*pw[k]*(value or 0)
        penalty_total+=row['deduction_'+k]
    row.update(absolute_quality_total=absolute_total,relative_quality_bonus=relative_total,
               penalty_total=penalty_total,best_score=absolute_total+relative_total-penalty_total,
               metric_availability=available,ranking_explanation='absolute_quality_total + relative_quality_bonus - penalty_total; all in points')
    return row

def rank_rows(rows,settings,context=None):
    if '_evidence' not in settings:settings=effective_settings(settings)
    if len({r['frame_id'] for r in rows})!=len(rows):raise ValueError('Duplicate frame_id')
    context=context or fit_context(rows,settings)
    result=[score_row(r,settings,context) for r in rows]
    eligible=sorted((r for r in result if r['ranking_eligible']=='true'),key=lambda r:(-r['best_score'],r['frame_id']))
    for i,r in enumerate(eligible,1):r['global_rank']=i
    return eligible+sorted((r for r in result if r['fatal_reject']=='true'),key=lambda r:r['frame_id'])

def choose_round(rows,history,size=45,cap=4,min_stills=10,round_number=None):
    if size<1 or cap<1 or min_stills<0:raise ValueError('Invalid review settings')
    shown={r['frame_id'] for r in history
           if r.get('ranking_version')==VERSION and r.get('shown_to_maru') in (True,'true')
           and (round_number is None or int(r['review_round'])<round_number)}
    available=sorted((r for r in rows if r['ranking_eligible']=='true' and r['frame_id'] not in shown),key=lambda r:int(r['global_rank']))
    stills=[r for r in available if r['input_kind']=='supplemental_still']
    selected=stills[:min(size,min_stills,len(stills))]
    counts=Counter();effective=cap
    while len(selected)<min(size,len(available)):
        ids={r['frame_id'] for r in selected}
        for r in available:
            if r['frame_id'] in ids:continue
            video=r['video_id'] if r['input_kind']=='formal_video' else None
            if video and counts[video]>=effective:continue
            selected.append(r);ids.add(r['frame_id'])
            if video:counts[video]+=1
            if len(selected)==size:break
        if len(selected)>=min(size,len(available)):break
        effective+=1
    selected.sort(key=lambda r:int(r['global_rank']))
    return selected,dict(requested=size,selected=len(selected),already_shown=len(shown),
        configured_video_cap=cap,effective_video_cap=effective,cap_relaxed=effective>cap,
        shortage=max(0,size-len(selected)),video_counts=dict(counts),
        supplemental_minimum_requested=min_stills,supplemental_unseen_available=len(stills),
        supplemental_reserved=min(size,min_stills,len(stills)),
        supplemental_selected=sum(r['input_kind']=='supplemental_still' for r in selected),
        ranking_version=VERSION)
