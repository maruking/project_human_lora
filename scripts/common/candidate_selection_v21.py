"""Bounded BEST quality core, optional soft coverage repair, then BEST fill."""
from collections import Counter
import math
import statistics
from common.candidate_selection_v2 import (FIELDS as V2_FIELDS, POSES,SCALES,VERTICALS,
    CONTEXT,DIMENSIONS,priority,normal,source_key,cap_for,validate_settings as validate_v2)

VERSION='step7_quality_coverage_v2.1'
FIELDS=(*V2_FIELDS,'quality_guard_member','quality_guard_order')


def validate_settings(settings):
    if settings['version']!=VERSION:raise ValueError('Wrong STEP7 v2.1 version')
    validate_v2(dict(settings,version='step7_quality_coverage_v2'))
    multiplier=settings['quality_guard_multiplier']
    core=settings['quality_core_target'];repair=settings['coverage_repair_slots_max']
    if isinstance(multiplier,bool) or not isinstance(multiplier,(int,float)) or not math.isfinite(multiplier) or multiplier<1:
        raise ValueError('Invalid quality guard multiplier')
    if any(not isinstance(v,int) or isinstance(v,bool) for v in (core,repair)) or not settings['candidate_pool_min']<=core<=settings['candidate_pool_target'] or not 0<=repair<=settings['candidate_pool_target']-core:
        raise ValueError('Invalid core target or coverage repair budget')


def select(rows,settings,partial=False,limit=0,current_reject_ids=()):
    validate_settings(settings)
    if not isinstance(limit,int) or isinstance(limit,bool) or limit<0:raise ValueError('Invalid partial limit')
    partial=partial or limit>0
    ids={r['frame_id'] for r in rows};rejected=set(current_reject_ids)
    if len(ids)!=len(rows) or rejected-ids:raise ValueError('Ambiguous frame or reject identities')
    if any(set(r)&set(FIELDS) for r in rows):raise ValueError('Input already contains STEP7 fields')
    outputs=[]
    for row in rows:
        human_reject=row['frame_id'] in rejected
        eligible=normal(row) and not human_reject
        if eligible:priority(row)
        out=dict(row,**{key:'' for key in FIELDS})
        out.update(step7_version=VERSION,step7_status='PARTIAL' if partial else 'MEASURED',
            candidate_pool_eligible=str(eligible).lower(),candidate_pool_selected='false',
            selection_quality_score=row.get('best_score',''),quality_guard_member='false',
            selection_reason='CURRENT_VERSION_HUMAN_REJECT' if human_reject else
                'NOT_NEEDED_FOR_REVIEW_POOL' if eligible else
                'NOT_APPLICABLE_DUPLICATE_MEMBER' if row.get('dedup_role')=='DUPLICATE_MEMBER' else 'NOT_APPLICABLE_UPSTREAM',
            identity_context=CONTEXT.get(row.get('identity_state'),row.get('identity_state','')),
            source_cap_state='NOT_CONSIDERED_QUALITY_GUARD' if eligible else 'NOT_APPLICABLE')
        outputs.append(out)
    eligible=sorted((r for r in outputs if r['candidate_pool_eligible']=='true'),key=priority)
    considered=eligible[:limit] if limit else eligible
    if limit:
        for row in eligible[limit:]:row['selection_reason']='PARTIAL_NOT_CONSIDERED'
    requested=math.ceil(settings['candidate_pool_target']*settings['quality_guard_multiplier'])
    guard=considered[:requested]
    for order,row in enumerate(guard,1):
        row.update(quality_guard_member='true',quality_guard_order=order,source_cap_state='AVAILABLE')
    counts={field:Counter() for field,_,_ in DIMENSIONS}
    source_counts=Counter();clusters=set();selected=[]

    def deficits(row):
        return [(field,label,column) for field,key,column in DIMENSIONS
            if (label:=row.get(field,'')) in settings[key] and counts[field][label]<settings[key][label]]

    def allowed(row):
        return row['candidate_pool_selected']=='false' and row['dedup_cluster_id'] not in clusters and source_counts[source_key(row)]<cap_for(row,settings)

    def add(row,reason):
        gaps=deficits(row) if reason=='COVERAGE_REPAIR' else []
        row.update(candidate_pool_selected='true',selection_reason=reason)
        for field,label,column in gaps:row[column]='SOFT_COVERAGE:'+label
        for field,_,_ in DIMENSIONS:counts[field][row.get(field,'')]+=1
        source_counts[source_key(row)]+=1;clusters.add(row['dedup_cluster_id']);selected.append(row)

    # No pose deficit is considered until the BEST core is immutable.
    for row in guard:
        if len(selected)>=settings['quality_core_target']:break
        if allowed(row):add(row,'BEST_QUALITY_CORE')
    core_count=len(selected)
    if core_count==settings['quality_core_target']:
        for _ in range(settings['coverage_repair_slots_max']):
            if len(selected)>=settings['candidate_pool_target']:break
            useful=[r for r in guard if allowed(r) and deficits(r)]
            if not useful:break
            add(min(useful,key=lambda r:(-len(deficits(r)),*priority(r))),'COVERAGE_REPAIR')
        for row in guard:
            if len(selected)>=settings['candidate_pool_target']:break
            if allowed(row):add(row,'BEST_SCORE_FILL')
    selected.sort(key=priority)
    for order,row in enumerate(selected,1):row['step7_pool_order']=order
    for row in guard:
        if source_counts[source_key(row)]>=cap_for(row,settings):
            row['source_cap_state']='AT_CAP_SELECTED' if row['candidate_pool_selected']=='true' else 'SOURCE_CAP_BLOCKED'
    shortages=[]
    for field,key,_ in DIMENSIONS:
        for label,goal in settings[key].items():
            if counts[field][label]>=goal:continue
            available=[r for r in guard if r.get(field)==label]
            blocked=sum(r['candidate_pool_selected']=='false' and r['dedup_cluster_id'] not in clusters and
                source_counts[source_key(r)]>=cap_for(r,settings) for r in available)
            shortages.append(dict(dimension=field,label=label,requested=goal,achieved=counts[field][label],
                shortage=goal-counts[field][label],reason='COVERAGE_SHORTAGE',guard_available=len(available),
                source_blocked_count=blocked,detail='SOURCE_CAP_COVERAGE_CONFLICT' if blocked else
                    'UNAVAILABLE_INSIDE_QUALITY_GUARD' if len(available)<goal else 'SOFT_REPAIR_BUDGET_OR_CLUSTER_CONSTRAINT'))
    hard=[]
    if core_count<settings['quality_core_target']:hard.append('QUALITY_CORE_SHORTAGE')
    if len(selected)<settings['candidate_pool_min']:hard.append('QUALITY_POOL_INSUFFICIENT')
    quality_status=('QUALITY_POOL_INSUFFICIENT' if len(selected)<settings['candidate_pool_min'] else
        'QUALITY_CORE_SHORTAGE' if hard else
        'POOL_BELOW_TARGET_QUALITY_PRESERVED' if len(selected)<settings['candidate_pool_target'] else 'TARGET_MET_QUALITY_PRESERVED')
    scores=[float(r['best_score']) for r in selected]
    guard_rank=max((int(r['global_rank']) for r in guard),default=None)
    selected_rank=max((int(r['global_rank']) for r in selected),default=None)
    reasons=Counter(r['selection_reason'] for r in selected)
    for name in ('BEST_QUALITY_CORE','COVERAGE_REPAIR','BEST_SCORE_FILL'):reasons.setdefault(name,0)
    achieved={field:dict(counts[field]) for field,_,_ in DIMENSIONS}
    for field,key,_ in DIMENSIONS:
        for label in settings[key]:achieved[field].setdefault(label,0)
    summary=dict(step7_version=VERSION,publication_status='PARTIAL' if partial else 'BLOCKED' if hard else 'COMPLETE',
        full_upstream_rows=len(rows),normal_candidate_universe=len(eligible),considered_candidate_count=len(considered),
        selected_review_pool=len(selected),actual_pool_count=len(selected),pool_target=settings['candidate_pool_target'],
        current_version_human_reject_count=len(rejected),current_version_human_reject_removed_from_pool=sum(normal(r) and r['frame_id'] in rejected for r in rows),
        human_reject_removal_scope='Normal eligibility before quality guard; not a prior-publication difference',
        quality_guard_size_requested=requested,quality_guard_size_actual=len(guard),
        quality_guard_best_score_min=min((float(r['best_score']) for r in guard),default=None),
        quality_guard_global_rank_max=guard_rank,deepest_global_rank_in_quality_guard=guard_rank,
        deepest_global_rank_selected=selected_rank,quality_core_target=settings['quality_core_target'],
        quality_core_count=core_count,quality_core_status='COMPLETE' if core_count==settings['quality_core_target'] else 'QUALITY_CORE_SHORTAGE',
        coverage_repair_slots_max=settings['coverage_repair_slots_max'],selection_reasons=dict(reasons),
        candidate_pool_target=settings['candidate_pool_target'],candidate_pool_min=settings['candidate_pool_min'],candidate_pool_max=settings['candidate_pool_max'],
        pool_range_status='IN_RANGE' if settings['candidate_pool_min']<=len(selected)<=settings['candidate_pool_max'] else 'SHORTFALL',
        pool_quality_status=quality_status,hard_shortages=hard,
        soft_coverage_requested={field:settings[key] for field,key,_ in DIMENSIONS},
        soft_coverage_achieved=achieved,soft_coverage_shortages=shortages,
        coverage_requested={field:settings[key] for field,key,_ in DIMENSIONS},coverage_achieved=achieved,
        coverage_shortages=shortages,source_cap_conflicts=[s for s in shortages if s['source_blocked_count']],
        source_distribution=dict(source_counts),source_caps={k:settings[k] for k in ('max_per_video','max_supplemental_still')},
        source_count=len({r['source_id'] for r in selected}),video_count=len({r['video_id'] for r in selected if r['input_kind']=='formal_video'}),
        identity_state_distribution=dict(Counter(r['identity_state'] for r in selected)),identity_selection_weight=0,
        best_score=dict(min=min(scores) if scores else None,median=statistics.median(scores) if scores else None,max=max(scores) if scores else None),
        global_rank_range=[min(int(r['global_rank']) for r in selected),selected_rank] if selected else [],
        final_training_selection=False,step8_final_authority=True,policy_review_required=bool(hard),
        count_note='Review options only; soft coverage never expands guard or replaces quality core')
    assert all(r['quality_guard_member']=='true' for r in selected)
    assert reasons['COVERAGE_REPAIR']<=settings['coverage_repair_slots_max']
    return outputs,selected,summary
