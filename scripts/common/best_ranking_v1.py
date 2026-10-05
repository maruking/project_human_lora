"""Transparent BEST ranking. No historical quality threshold controls eligibility."""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import math

VERSION = 'best_rank_v1'
POSITIVE = dict(sharpness=.20, eye_detail=.15, mouth_detail=.10, contrast=.15,
                visibility=.15, face_size=.10, exposure=.15)
PENALTIES = dict(blur=.15, obstruction=.15, half_eye=.10, low_contrast=.10,
                 shadow=.10, clipping_haze=.10, uncertainty=.10)
METRICS = ('face_laplacian_canonical_192','face_tenengrad_canonical_192',
           'left_eye_local_detail','right_eye_local_detail','mouth_local_detail',
           'local_face_contrast','face_visibility_score','face_short_edge_px',
           'face_brightness_mean','highlight_clip_ratio','face_shadow_ratio',
           'dynamic_range_p95_p5','eye_open_min','left_eye_presence','right_eye_presence',
           'eye_open_asymmetry')


def number(value):
    if value is None or value == '': return None
    try: value=float(value)
    except (TypeError, ValueError): return None
    return value if math.isfinite(value) else None


def mean_available(values):
    available=[v for v in values if v is not None]
    return sum(available)/len(available) if available else None


def fatal_reason(row):
    if row.get('analysis_status') == 'ERROR': return 'analysis_error'
    if row.get('face_detected') != 'true': return 'no_face'
    # Confirmed within the single configured detector: confidence + valid bbox.
    if int(row.get('confirmed_face_count') or 0) > 1: return 'multiple_faces'
    if row.get('crop_geometry_status') != 'VALID': return 'invalid_crop_geometry'
    if row.get('face_evaluability') == 'NOT_EVALUABLE': return 'face_not_evaluable'
    return ''


def rank_rows(rows, settings):
    rows=[dict(r) for r in rows]
    if len({r['frame_id'] for r in rows}) != len(rows): raise ValueError('Duplicate frame_id')
    positive=settings.get('positive_weights',POSITIVE);penalties=settings.get('penalty_weights',PENALTIES)
    for weights,keys in ((positive,POSITIVE),(penalties,PENALTIES)):
        if set(weights)!=set(keys) or any(number(v) is None or float(v)<0 for v in weights.values()):
            raise ValueError('Invalid ranking component weights')
    if not math.isclose(sum(positive.values()),1): raise ValueError('Positive weights must sum to one')
    pools=defaultdict(list)
    for row in rows:
        reason=fatal_reason(row)
        row.update(fatal_reject=str(bool(reason)).lower(),fatal_reject_reason=reason,
                   ranking_eligible=str(not reason).lower(),ranking_version=VERSION,
                   review_selected='false',global_rank='',best_score='')
        if not reason:
            for metric in METRICS:
                value=number(row.get(metric))
                if value is not None: pools[(row['input_kind'],metric)].append(value)
    for values in pools.values():values.sort()
    for row in rows:
        if row['fatal_reject']=='true': continue
        norm={}
        for metric in METRICS:
            value=number(row.get(metric));pool=pools.get((row['input_kind'],metric),[])
            # Midrank ties; zero remains a measured zero, missing remains blank.
            norm[metric]=((bisect_left(pool,value)+bisect_right(pool,value))/(2*len(pool))) if value is not None and pool else None
            row['norm_'+metric]='' if norm[metric] is None else norm[metric]
        n=lambda key:norm[key]
        sharp=mean_available([n('face_laplacian_canonical_192'),n('face_tenengrad_canonical_192')])
        eyes=mean_available([n('left_eye_local_detail'),n('right_eye_local_detail')])
        context=mean_available([n('dynamic_range_p95_p5'),1-n('highlight_clip_ratio') if n('highlight_clip_ratio') is not None else None,
                                1-n('face_shadow_ratio') if n('face_shadow_ratio') is not None else None])
        pos=dict(sharpness=sharp,eye_detail=eyes,mouth_detail=n('mouth_local_detail'),contrast=n('local_face_contrast'),
                 visibility=n('face_visibility_score'),face_size=n('face_short_edge_px'),exposure=context)
        # Partial eye/sharpness/exposure measurement contributes proportionally.
        coverage=dict(sharpness=sum(n(k) is not None for k in METRICS[:2])/2,
                      eye_detail=sum(n(k) is not None for k in METRICS[2:4])/2,
                      exposure=sum(n(k) is not None for k in ('dynamic_range_p95_p5','highlight_clip_ratio','face_shadow_ratio'))/3)
        for k in pos:coverage.setdefault(k,float(pos[k] is not None))
        weighted=sum(positive[k]*(pos[k] or 0)*coverage[k] for k in pos)
        available=sum(positive[k]*coverage[k] for k in pos)
        for k in pos:
            row['component_'+k]='' if pos[k] is None else pos[k]
            row['contribution_'+k]=positive[k]*(pos[k] or 0)*coverage[k]
            row['availability_'+k]=coverage[k]
        inverse=lambda v:None if v is None else 1-v
        # Profiles attenuate eye obstruction/asymmetry evidence continuously;
        # no pose bucket/quota and no angle can fatal-reject.
        yaw=number(row.get('yaw'))
        eye_expectation=abs(math.cos(math.radians(yaw))) if yaw is not None else .5
        presence=mean_available([n('left_eye_presence'),n('right_eye_presence')])
        obstruction=mean_available([inverse(presence),n('eye_open_asymmetry')])
        obstruction=mean_available([obstruction*eye_expectation if obstruction is not None else None,
                                    inverse(n('face_visibility_score'))])
        local=mean_available([eyes,n('mouth_local_detail')])
        blur=mean_available([inverse(sharp),inverse(local)])
        haze=(n('face_brightness_mean')*(1-n('dynamic_range_p95_p5'))*(1-n('local_face_contrast'))
              if all(n(k) is not None for k in ('face_brightness_mean','dynamic_range_p95_p5','local_face_contrast')) else None)
        pen=dict(blur=blur,obstruction=obstruction,half_eye=inverse(n('eye_open_min')),
                 low_contrast=inverse(n('local_face_contrast')),shadow=n('face_shadow_ratio'),
                 clipping_haze=mean_available([n('highlight_clip_ratio'),haze]),
                 uncertainty=1-available)
        if row.get('measurement_warnings'):
            # Availability already reduces positives; warning proportion is audit context.
            row['analysis_uncertainty_context']=row['measurement_warnings']
        penalty_sum=0
        for k,value in pen.items():
            row['penalty_'+k]='' if value is None else value
            row['deduction_'+k]=penalties[k]*(value or 0)
            penalty_sum+=row['deduction_'+k]
        row.update(positive_total=weighted,penalty_total=penalty_sum,metric_availability=available,
                   best_score=100*(weighted-penalty_sum),pose_eye_expectation=eye_expectation,
                   ranking_explanation='weighted relative quality minus visible relative concern penalties; not acceptance')
    ranked=sorted((r for r in rows if r['ranking_eligible']=='true'),key=lambda r:(-r['best_score'],r['frame_id']))
    for i,row in enumerate(ranked,1):row['global_rank']=i
    return sorted(rows,key=lambda r:(r['ranking_eligible']!='true',r['global_rank'] or math.inf,r['frame_id']))


def choose_round(rows, history, size=45, cap=4):
    if size<1 or cap<1:raise ValueError('Positive review size and cap required')
    # Exclude by stable frame_id, even when source pixels/generation change.
    shown={r['frame_id'] for r in history if r.get('shown_to_maru') in (True,'true')}
    available=sorted((r for r in rows if r['ranking_eligible']=='true' and r['frame_id'] not in shown),key=lambda r:int(r['global_rank']))
    selected=[];counts=Counter();effective=cap
    while len(selected)<min(size,len(available)):
        selected_ids={r['frame_id'] for r in selected}
        for row in available:
            if row['frame_id'] in selected_ids:continue
            video=row.get('video_id') if row['input_kind']=='formal_video' else None
            if video and counts[video]>=effective:continue
            selected.append(row);selected_ids.add(row['frame_id'])
            if video:counts[video]+=1
            if len(selected)==size:break
        if len(selected)>=min(size,len(available)):break
        effective+=1
    # Selection follows cap passes, presentation follows unchanged global rank.
    selected.sort(key=lambda r:int(r['global_rank']))
    return selected,dict(requested=size,selected=len(selected),already_shown=len(shown),
                         configured_video_cap=cap,effective_video_cap=effective,cap_relaxed=effective>cap,
                         shortage=max(0,size-len(selected)),video_counts=dict(counts))
