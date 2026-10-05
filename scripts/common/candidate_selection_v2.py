"""STEP7 review options: stored BEST quality plus coverage, no identity weighting."""
from collections import Counter
import math
import statistics

VERSION = 'step7_quality_coverage_v2'
POSES = ('FRONTAL','THREE_QUARTER_LEFT','THREE_QUARTER_RIGHT','PROFILE_LEFT','PROFILE_RIGHT','NOT_EVALUABLE')
SCALES = ('CLOSE_UP','UPPER_BODY','FULL_BODY','NOT_EVALUABLE')
VERTICALS = ('LOOKING_UP','LEVEL','LOOKING_DOWN','NOT_EVALUABLE')
FIELDS = ('step7_version','step7_status','candidate_pool_eligible','candidate_pool_selected',
    'selection_quality_score','selection_reason','step7_pool_order','coverage_pose_reason',
    'coverage_vertical_reason','coverage_scale_reason','source_cap_state','identity_context','step7_error')
CONTEXT = dict(IDENTITY_PASS='STRONGER_MEASURED_IDENTITY',IDENTITY_REVIEW='IDENTITY_MEASUREMENT_REVIEW',
    IDENTITY_REJECT='LOW_MEASURED_IDENTITY',IDENTITY_NOT_EVALUABLE='IDENTITY_NOT_EVALUABLE')
DIMENSIONS = (('pose_bin','pose_min','coverage_pose_reason'),
    ('vertical_pose','vertical_min','coverage_vertical_reason'),('face_scale_bin','scale_min','coverage_scale_reason'))


def priority(row):
    score = float(row['best_score'])
    if not math.isfinite(score) or not str(row['global_rank']).isdigit() or int(row['global_rank']) < 1:
        raise ValueError('Missing/nonfinite BEST quality or invalid global_rank: '+row['frame_id'])
    return (-score,int(row['global_rank']),row['frame_id'])


def normal(row):
    return str(row.get('ranking_eligible','')).lower()=='true' and row.get('dedup_role') in ('UNIQUE','REPRESENTATIVE') and not any(
        row.get(key)=='ERROR' for key in ('step4_status','step5_status','step6_status','analysis_status')) and row.get('identity_state')!='UPSTREAM_ERROR'


def source_key(row):
    if row['input_kind']=='formal_video':
        if not row['video_id']:
            raise ValueError('Missing formal video ID')
        return 'video:'+row['video_id']
    if row['input_kind']=='supplemental_still':
        return 'supplemental_still_collection'
    raise ValueError('Unknown input_kind')


def cap_for(row, settings):
    return settings['max_per_video'] if row['input_kind']=='formal_video' else settings['max_supplemental_still']


def validate_settings(settings):
    if settings['version']!=VERSION:
        raise ValueError('Wrong STEP7 version')
    low,target,high = (settings[k] for k in ('candidate_pool_min','candidate_pool_target','candidate_pool_max'))
    if not all(isinstance(v,int) and not isinstance(v,bool) and v>0 for v in (low,target,high,settings['max_per_video'],settings['max_supplemental_still'])) or not low<=target<=high:
        raise ValueError('Invalid review range/target/source caps')
    for key,labels in (('pose_min',POSES),('vertical_min',VERTICALS),('scale_min',SCALES)):
        if not isinstance(settings[key],dict) or set(settings[key])-set(labels) or any(
                not isinstance(v,int) or isinstance(v,bool) or v<0 for v in settings[key].values()):
            raise ValueError('Invalid coverage minima: '+key)


def select(rows, settings, partial=False, limit=0, current_reject_ids=()):
    validate_settings(settings)
    if not isinstance(limit,int) or limit<0:
        raise ValueError('Invalid partial limit')
    partial=partial or limit>0
    if len({r['frame_id'] for r in rows})!=len(rows):
        raise ValueError('Duplicate frame IDs')
    current_reject_ids=set(current_reject_ids)
    if current_reject_ids-{r['frame_id'] for r in rows}:
        raise ValueError('Confirmed reject outside current universe')
    if any(set(r)&set(FIELDS) for r in rows):
        raise ValueError('Input already contains STEP7 fields')
    outputs=[]
    for row in rows:
        human_reject=row['frame_id'] in current_reject_ids
        eligible=normal(row) and not human_reject
        if eligible:
            priority(row)
        out=dict(row,**{key:'' for key in FIELDS})
        out.update(step7_version=VERSION,step7_status='PARTIAL' if partial else 'MEASURED',
            candidate_pool_eligible=str(eligible).lower(),candidate_pool_selected='false',
            selection_quality_score=row.get('best_score',''),
            selection_reason='CURRENT_VERSION_HUMAN_REJECT' if human_reject else 'NOT_NEEDED_FOR_REVIEW_POOL' if eligible else
                ('NOT_APPLICABLE_DUPLICATE_MEMBER' if row.get('dedup_role')=='DUPLICATE_MEMBER' else 'NOT_APPLICABLE_UPSTREAM'),
            identity_context=CONTEXT.get(row.get('identity_state'),row.get('identity_state','')),
            source_cap_state='NOT_APPLICABLE' if not eligible else 'AVAILABLE')
        outputs.append(out)
    pool=sorted((r for r in outputs if r['candidate_pool_eligible']=='true'),key=priority)
    normal_count=len(pool)
    if limit:
        for row in pool[limit:]:
            row['selection_reason']='PARTIAL_NOT_CONSIDERED'
        pool=pool[:limit]
    counts={field:Counter() for field,_,_ in DIMENSIONS}
    source_counts=Counter(); used_clusters=set(); selected=[]

    def deficits(row):
        return [(field,label,reason) for field,key,reason in DIMENSIONS
            if (label:=row.get(field,'')) in settings[key] and counts[field][label]<settings[key][label]]

    def allowed(row):
        return row['dedup_cluster_id'] not in used_clusters and source_counts[source_key(row)]<cap_for(row,settings)

    def add(row, reason):
        gaps=deficits(row) if reason=='COVERAGE_OPTION' else []
        row.update(candidate_pool_selected='true',selection_reason=reason)
        for field,label,column in gaps:
            row[column]='MINIMUM_OPTION:'+label
        for field,_,_ in DIMENSIONS:
            counts[field][row.get(field,'')]+=1
        source_counts[source_key(row)]+=1
        used_clusters.add(row['dedup_cluster_id']); selected.append(row)

    # Review-pool target is a slot budget; never silently enlarge/relax it.
    while len(selected)<settings['candidate_pool_target']:
        improving=[r for r in pool if r['candidate_pool_selected']=='false' and allowed(r) and deficits(r)]
        if not improving:
            break
        winner=min(improving,key=lambda r:(-len(deficits(r)),*priority(r)))
        add(winner,'COVERAGE_OPTION')
    for row in pool:
        if len(selected)>=settings['candidate_pool_target']:
            break
        if row['candidate_pool_selected']=='false' and allowed(row):
            add(row,'BEST_SCORE_FILL')
    selected.sort(key=priority)
    for order,row in enumerate(selected,1):
        row['step7_pool_order']=order
    for row in pool:
        if source_counts[source_key(row)]>=cap_for(row,settings):
            row['source_cap_state']='AT_CAP_SELECTED' if row['candidate_pool_selected']=='true' else 'SOURCE_CAP_BLOCKED'

    shortages=[]
    for field,key,_ in DIMENSIONS:
        for label,request in settings[key].items():
            achieved=counts[field][label]
            if achieved>=request:
                continue
            available=[r for r in pool if r.get(field)==label]
            remaining=[r for r in available if r['candidate_pool_selected']=='false' and r['dedup_cluster_id'] not in used_clusters]
            source_blocked=[r for r in remaining if source_counts[source_key(r)]>=cap_for(r,settings)]
            issue='UNAVAILABLE_COVERAGE'
            if len(available)>=request and source_blocked:
                issue='SOURCE_CAP_COVERAGE_CONFLICT'
            elif len(available)>=request and len(selected)>=settings['candidate_pool_target']:
                issue='POOL_TARGET_COVERAGE_CONFLICT'
            elif len(available)>=request:
                issue='CLUSTER_COVERAGE_CONFLICT'
            shortages.append(dict(dimension=field,label=label,requested=request,achieved=achieved,
                shortage=request-achieved,available=len(available),reason=issue,source_blocked_count=len(source_blocked)))
    scores=[float(r['best_score']) for r in selected]
    conflicts=[r for r in shortages if r['reason'].endswith('_CONFLICT')]
    summary=dict(step7_version=VERSION,publication_status='PARTIAL' if partial else ('BLOCKED' if conflicts else 'COMPLETE'),
        full_upstream_rows=len(rows),normal_candidate_universe=normal_count,considered_candidate_count=len(pool),selected_review_pool=len(selected),
        current_version_human_reject_count=len(current_reject_ids),
        selection_reasons=dict(Counter(r['selection_reason'] for r in selected)),
        candidate_pool_target=settings['candidate_pool_target'],candidate_pool_min=settings['candidate_pool_min'],
        candidate_pool_max=settings['candidate_pool_max'],pool_range_status='IN_RANGE' if settings['candidate_pool_min']<=len(selected)<=settings['candidate_pool_max'] else 'SHORTFALL',
        coverage_requested={field:settings[key] for field,key,_ in DIMENSIONS},
        coverage_achieved={field:dict(counts[field]) for field,_,_ in DIMENSIONS},
        coverage_shortages=shortages,source_cap_conflicts=[s for s in conflicts if s['reason']=='SOURCE_CAP_COVERAGE_CONFLICT'],
        source_distribution=dict(source_counts),source_caps={k:settings[k] for k in ('max_per_video','max_supplemental_still')},
        source_count=len({r['source_id'] for r in selected}),video_count=len({r['video_id'] for r in selected if r['input_kind']=='formal_video'}),
        identity_state_distribution=dict(Counter(r['identity_state'] for r in selected)),identity_selection_weight=0,
        best_score=dict(min=min(scores) if scores else None,median=statistics.median(scores) if scores else None,max=max(scores) if scores else None),
        global_rank_range=[min(int(r['global_rank']) for r in selected),max(int(r['global_rank']) for r in selected)] if selected else [],
        final_training_selection=False,step8_final_authority=True,policy_review_required=bool(conflicts),
        count_note='Review options only; not-selected is NOT_NEEDED_FOR_REVIEW_POOL, never a new image-quality Reject')
    return outputs,selected,summary
