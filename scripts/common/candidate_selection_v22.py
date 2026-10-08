"""Immutable BEST BASE plus additive coverage options inside the Quality Guard."""
from collections import Counter
import math
import statistics
from common.candidate_selection_v2 import (FIELDS as OLD_FIELDS,POSES,SCALES,VERTICALS,
    CONTEXT,DIMENSIONS,priority,normal,source_key,cap_for,validate_settings as validate_old)

VERSION='step7_quality_coverage_v2.2'
FIELDS=(*OLD_FIELDS,'quality_guard_member','quality_guard_order','base_candidate','coverage_additional_candidate','rare_profile_candidate')
PROFILES=('PROFILE_LEFT','PROFILE_RIGHT')


def validate_settings(settings):
    if settings['version']!=VERSION:raise ValueError('Wrong STEP7 version')
    validate_old(dict(settings,version='step7_quality_coverage_v2'))
    profile_target=settings['rare_profile_review_target']
    if isinstance(profile_target,bool) or not isinstance(profile_target,int) or not 2<=profile_target<=3:
        raise ValueError('Rare Profile review target must be 2 or 3')
    multiplier=settings['quality_guard_multiplier']
    if isinstance(multiplier,bool) or not isinstance(multiplier,(int,float)) or not math.isfinite(multiplier) or multiplier<1:
        raise ValueError('Invalid Quality Guard multiplier')


def select(rows,settings,partial=False,limit=0,current_reject_ids=()):
    validate_settings(settings)
    if not isinstance(limit,int) or isinstance(limit,bool) or limit<0:raise ValueError('Invalid partial limit')
    rejected=set(current_reject_ids);ids={r['frame_id'] for r in rows}
    if len(ids)!=len(rows) or rejected-ids:raise ValueError('Ambiguous frame identities')
    outputs=[]
    for row in rows:
        if set(row)&set(FIELDS):raise ValueError('Input already contains STEP7 fields')
        eligible=normal(row) and row['frame_id'] not in rejected
        if eligible:priority(row)
        out=dict(row,**{k:'' for k in FIELDS})
        out.update(step7_version=VERSION,step7_status='PARTIAL' if partial or limit else 'MEASURED',
            candidate_pool_eligible=str(eligible).lower(),candidate_pool_selected='false',
            selection_quality_score=row.get('best_score',''),quality_guard_member='false',
            base_candidate='false',coverage_additional_candidate='false',rare_profile_candidate='false',
            selection_reason='CURRENT_VERSION_HUMAN_REJECT' if row['frame_id'] in rejected else
                'NOT_NEEDED_FOR_REVIEW_POOL' if eligible else 'NOT_APPLICABLE_UPSTREAM',
            identity_context=CONTEXT.get(row.get('identity_state'),row.get('identity_state','')),
            source_cap_state='DIAGNOSTIC_ONLY' if eligible else 'NOT_APPLICABLE')
        outputs.append(out)
    eligible=sorted((r for r in outputs if r['candidate_pool_eligible']=='true'),key=priority)
    considered=eligible[:limit] if limit else eligible
    target=settings['candidate_pool_target'];requested=math.ceil(target*settings['quality_guard_multiplier'])
    guard=considered[:requested]
    for i,r in enumerate(guard,1):r.update(quality_guard_member='true',quality_guard_order=i)
    base=guard[:target];selected=[];counts={field:Counter() for field,_,_ in DIMENSIONS}
    def add(row,role):
        row.update(candidate_pool_selected='true',selection_reason=role,
            base_candidate=str(role=='BASE_BEST').lower(),coverage_additional_candidate=str(role=='COVERAGE_ADDITIONAL').lower())
        if role=='RARE_PROFILE_REVIEW':
            row.update(rare_profile_candidate='true',coverage_pose_reason='RARE_PROFILE_REVIEW:'+row['pose_bin'])
        for field,key,column in DIMENSIONS:
            label=row.get(field,'')
            if role=='COVERAGE_ADDITIONAL' and counts[field][label]<settings[key].get(label,0):row[column]='ADDITIONAL_COVERAGE:'+label
            counts[field][label]+=1
        selected.append(row)
    for r in base:add(r,'BASE_BEST')
    # Each deficit takes its highest-BEST remaining options. No source caps or
    # repair-slot budget can evict BASE or hide an available rare category.
    for field,key,_ in DIMENSIONS:
        for label,goal in settings[key].items():
            for row in guard:
                if counts[field][label]>=goal:break
                if row['candidate_pool_selected']=='false' and row.get(field)==label:add(row,'COVERAGE_ADDITIONAL')
    # The user-authorized profile-only exception runs after unchanged coverage.
    # Existing BASE/coverage rows are never evicted, even if already above target.
    profile_target=settings['rare_profile_review_target']
    profile_before={label:counts['pose_bin'][label] for label in PROFILES}
    for label in PROFILES:
        for row in considered:
            if counts['pose_bin'][label]>=profile_target:break
            if row['candidate_pool_selected']=='false' and row.get('pose_bin')==label:add(row,'RARE_PROFILE_REVIEW')
    selected.sort(key=priority)
    for i,row in enumerate(selected,1):row['step7_pool_order']=i
    source_counts=Counter(source_key(r) for r in selected)
    for row in considered:
        if source_counts[source_key(row)]>cap_for(row,settings):row['source_cap_state']='SOURCE_CONCENTRATION_WARNING_ONLY'
    shortages=[]
    for field,key,_ in DIMENSIONS:
        for label,goal in settings[key].items():
            if counts[field][label]<goal:
                shortages.append(dict(dimension=field,label=label,requested=goal,achieved=counts[field][label],
                    shortage=goal-counts[field][label],reason='INSUFFICIENT_ELIGIBLE_PROFILE' if field=='pose_bin' and label in PROFILES else 'UNAVAILABLE_INSIDE_QUALITY_GUARD'))
    hard=['BASE_SHORTAGE'] if len(base)<target else []
    summary=dict(step7_version=VERSION,publication_status='PARTIAL' if partial or limit else 'BLOCKED' if hard else 'COMPLETE',
        full_upstream_rows=len(rows),normal_candidate_universe=len(eligible),selected_review_pool=len(selected),
        base_target=target,base_count=len(base),coverage_additional_count=sum(r['selection_reason']=='COVERAGE_ADDITIONAL' for r in selected),
        rare_profile_added_count=sum(r['rare_profile_candidate']=='true' for r in selected),
        rare_profile_outside_guard_count=sum(r['rare_profile_candidate']=='true' and r['quality_guard_member']=='false' for r in selected),
        rare_profile_review={label:dict(target=profile_target,before=profile_before[label],after=counts['pose_bin'][label],
            added=sum(r['rare_profile_candidate']=='true' and r['pose_bin']==label for r in selected),
            shortage=max(0,profile_target-counts['pose_bin'][label]),
            eligible_available=sum(r['pose_bin']==label for r in considered)) for label in PROFILES},
        base_frame_ids=[r['frame_id'] for r in base],base_preserved=True,
        quality_guard_size_requested=requested,quality_guard_size_actual=len(guard),
        deepest_global_rank_selected=max((int(r['global_rank']) for r in selected),default=None),
        quality_guard_best_score_min=min((float(r['best_score']) for r in guard),default=None),
        selection_reasons=dict(Counter(r['selection_reason'] for r in selected)),
        soft_coverage_requested={field:settings[key] for field,key,_ in DIMENSIONS},
        soft_coverage_achieved={field:dict(counts[field]) for field,_,_ in DIMENSIONS},
        soft_coverage_shortages=shortages,coverage_shortages=shortages,
        source_distribution=dict(source_counts),source_caps_diagnostic_only=True,
        source_concentration_warnings=[dict(source=key,count=count,configured_cap=cap_for(next(r for r in selected if source_key(r)==key),settings)) for key,count in source_counts.items()
            if count>cap_for(next(r for r in selected if source_key(r)==key),settings)],
        identity_selection_weight=0,current_version_human_reject_count=len(rejected),
        final_training_selection=False,step8_final_authority=True,hard_shortages=hard,policy_review_required=bool(hard),
        count_note='BASE retained; normal coverage inside guard; Profile-only review top-up from eligible; source caps diagnostic; no auto-accept')
    assert {r['frame_id'] for r in base}<={r['frame_id'] for r in selected}
    scores=[float(r['best_score']) for r in selected]
    summary.update(considered_candidate_count=len(considered),actual_pool_count=len(selected),
        candidate_pool_target=target,candidate_pool_min=settings['candidate_pool_min'],candidate_pool_max=settings['candidate_pool_max'],
        quality_guard_global_rank_max=max((int(r['global_rank']) for r in guard),default=None),
        coverage_achieved=summary['soft_coverage_achieved'],source_cap_conflicts=[],
        source_count=len({r['source_id'] for r in selected}),video_count=len({r['video_id'] for r in selected if r['input_kind']=='formal_video'}),
        identity_state_distribution=dict(Counter(r['identity_state'] for r in selected)),
        best_score=dict(min=min(scores) if scores else None,median=statistics.median(scores) if scores else None,max=max(scores) if scores else None),
        global_rank_range=[min(int(r['global_rank']) for r in selected),summary['deepest_global_rank_selected']] if selected else [],
        pool_quality_status='BASE_SHORTAGE' if hard else 'BASE_PRESERVED_ADDITIVE_COVERAGE')
    assert all(review_scope_allowed(r) for r in selected)
    return outputs,selected,summary


def review_scope_allowed(row):
    """Explicit profile exception, not a general bypass of the Quality Guard."""
    return row.get('quality_guard_member')=='true' or (
        row.get('rare_profile_candidate')=='true' and row.get('pose_bin') in PROFILES
        and row.get('selection_reason')=='RARE_PROFILE_REVIEW'
        and row.get('base_candidate')=='false' and row.get('candidate_pool_eligible')=='true'
        and normal(row))
