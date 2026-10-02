"""Deterministic report-only dataset selection; no inference or source mutation."""
from collections import Counter
import math


def truth(value):
    return str(value).lower() in ('true', 'yes', '1')


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Non-finite selection evidence')
    return number


def prepare(row, settings, pose_settings, identity_available):
    row = dict(row)
    group = row.get('selection_group', '').upper()
    if group not in ('A', 'B', 'C'):
        raise ValueError('Every input requires exactly one explicit A/B/C group')
    row['selection_group'] = group
    if row.get('human_accept', '').upper() == 'REJECT' and group != 'C':
        raise ValueError('Human Reject conflicts with selection group')
    pose = row.get('pose_bucket', '')
    angle = ('FRONTAL' if pose == 'FRONT' else 'THREE_QUARTER' if pose in ('LEFT_3Q','RIGHT_3Q')
             else 'SIDE' if pose in ('LEFT_PROFILE','RIGHT_PROFILE') else 'UNKNOWN')
    if pose in ('LOOKING_UP','LOOKING_DOWN') and row.get('pose_yaw'):
        yaw = abs(finite(row['pose_yaw']))
        angle = ('FRONTAL' if yaw <= pose_settings['front_yaw_max'] else
                 'THREE_QUARTER' if yaw <= pose_settings['three_quarter_yaw_max'] else 'SIDE')
    pitch = pose if pose in ('LOOKING_UP','LOOKING_DOWN') else 'LEVEL'
    expression = row.get('expression_bucket', 'UNKNOWN').upper() or 'UNKNOWN'
    # No guessed expression or new facial diagnostics. Optional authoritative labels only.
    source = row.get('video_id') or row.get('source_id') or 'STILL_COLLECTION:'+row['filename'].split('/')[0]
    duplicate = row.get('duplicate_group') or row['frame_id']
    row.update(selected='no', final_selection_role='EXCLUDED', promotion_reason='', exclusion_reason='',
               angle_bucket=angle, pitch_bucket=pitch, composition_bucket=row.get('shot_type','UNKNOWN'),
               expression_bucket=expression, distribution_source=source, selection_duplicate_group=duplicate,
               human_review_required='yes', selection_rank='', selection_score='')
    reasons = []
    if group == 'C': reasons.append('selection_group_C')
    if row.get('selection_group_source') != 'HUMAN_CONFIRMED' or row.get('selection_review_status') != 'CONFIRMED':
        reasons.append('selection_human_confirmation_pending')
    if group == 'B' and not truth(row.get('reserve_use_allowed')):
        reasons.append('borderline_reserve_not_confirmed')
    if row.get('pose_status') != 'ok' or angle == 'UNKNOWN' or row['composition_bucket'] not in settings['composition_min']:
        reasons.append('pose_composition_missing_or_unsupported')
    if row.get('duplicate_status') not in ('unique','representative','duplicate'):
        reasons.append('duplicate_evidence_missing_or_failed')
    if row.get('duplicate_status') == 'duplicate' and not row.get('duplicate_group'):
        reasons.append('duplicate_group_missing')
    if identity_available and not truth(row.get('identity_passed')):
        reasons.append('identity_failed_or_not_evaluated')
    if expression not in ('UNKNOWN','NEUTRAL','NATURAL','MILD_VARIATION'):
        reasons.append('expression_outside_natural_mild_scope')
    row['exclusion_reason'] = ';'.join(reasons)
    # Existing STEP5 quality evidence ranks within coverage. It never overrides A/B/C.
    row['selection_score'] = str(finite(row.get('face_quality_score') or 0))
    if not reasons: row['final_selection_role'] = 'RESERVE'
    elif group == 'B' and 'identity_failed_or_not_evaluated' not in reasons and ('selection_human_confirmation_pending' in reasons or 'borderline_reserve_not_confirmed' in reasons):
        row['final_selection_role'] = 'REVIEW_PENDING_RESERVE'
    return row


def counts(rows):
    return {key: Counter(r[key] for r in rows) for key in
            ('angle_bucket','pitch_bucket','composition_bucket','distribution_source','selection_duplicate_group','expression_bucket')}


def deficits(rows, settings):
    result = {}; current = counts(rows)
    for key, config_key in (('angle_bucket','angle_min'),('pitch_bucket','pitch_min'),('composition_bucket','composition_min')):
        for label, minimum in settings[config_key].items():
            if current[key][label] < minimum:
                result[key+':'+label] = minimum-current[key][label]
    return result


def permitted(rows, candidate, settings):
    current = counts(rows)
    if current['distribution_source'][candidate['distribution_source']] >= settings['max_per_source']: return False
    if current['selection_duplicate_group'][candidate['selection_duplicate_group']]: return False
    if current['angle_bucket'][candidate['angle_bucket']] >= settings['angle_max'][candidate['angle_bucket']]: return False
    if current['composition_bucket'][candidate['composition_bucket']] >= settings['composition_max'][candidate['composition_bucket']]: return False
    if candidate['expression_bucket'] == 'MILD_VARIATION' and current['expression_bucket']['MILD_VARIATION'] >= settings['max_mild_expression']: return False
    return True


def gain(rows, candidate, settings):
    return sum(deficits(rows,settings).values())-sum(deficits(rows+[candidate],settings).values())


def choose(rows, pool, settings):
    current = counts(rows)
    available = [r for r in pool if r not in rows and permitted(rows,r,settings)]
    return min(available, key=lambda r:(-gain(rows,r,settings),
               current['distribution_source'][r['distribution_source']],
               r['expression_bucket']=='UNKNOWN', -finite(r['selection_score']), r['frame_id']), default=None)


def select(rows, settings, pose_settings, identity_available=False):
    if not 35 <= settings['min_count'] <= settings['target_count'] <= settings['max_count'] <= 45:
        raise ValueError('Revision B requires 35 <= minimum <= target <= maximum <= 45')
    for low, high in (('angle_min','angle_max'),('composition_min','composition_max')):
        if set(settings[low]) != set(settings[high]) or any(settings[low][k] > settings[high][k] for k in settings[low]):
            raise ValueError('Coverage minimum/maximum keys or values differ')
        if sum(settings[low].values()) > settings['max_count']:
            raise ValueError('Disjoint coverage minimums exceed maximum dataset count')
    audit = sorted((prepare(r,settings,pose_settings,identity_available) for r in rows),key=lambda r:r['frame_id'])
    primary = [r for r in audit if r['selection_group']=='A' and not r['exclusion_reason']]
    borderline = [r for r in audit if r['selection_group']=='B' and not r['exclusion_reason']]
    selected = []
    while len(selected) < settings['target_count']:
        candidate = choose(selected,primary,settings)
        if candidate is None: break
        selected.append(candidate)
    stage1 = [r['frame_id'] for r in selected]
    # Coverage repair: only necessary confirmed B, replacing redundant A at target.
    while deficits(selected,settings):
        options = []
        old = sum(deficits(selected,settings).values())
        for candidate in borderline:
            if candidate in selected: continue
            bases = [(selected,None)] if len(selected) < settings['target_count'] else []
            bases += [(selected[:i]+selected[i+1:],r) for i,r in enumerate(selected) if r['selection_group']=='A']
            if len(selected) < settings['max_count']: bases += [(selected,None)]
            for base, removed in bases:
                if not permitted(base,candidate,settings): continue
                after = base+[candidate]
                improvement = old-sum(deficits(after,settings).values())
                if improvement <= 0: continue
                # Never exchange one fulfilled coverage minimum for a new shortage.
                if any(value > deficits(selected,settings).get(key,0) for key,value in deficits(after,settings).items()): continue
                options.append(((-improvement,removed is None,counts(base)['distribution_source'][candidate['distribution_source']],
                                 -finite(candidate['selection_score']),candidate['frame_id'],removed['frame_id'] if removed else ''),base,candidate))
        if not options: break
        _, base, candidate = min(options,key=lambda item:item[0])
        needs = deficits(base,settings)
        candidate['promotion_reason'] = ';'.join('coverage:'+key for key in needs if key.endswith(':'+candidate[key.split(':')[0]]))
        selected = base+[candidate]
    # B fills only the minimum viable size, never arbitrary extra slots to reach 40.
    while len(selected) < settings['min_count']:
        candidate = choose(selected,primary,settings) or choose(selected,borderline,settings)
        if candidate is None: break
        if candidate['selection_group']=='B': candidate['promotion_reason']='minimum_count_shortage'
        selected.append(candidate)
    selected_ids = {r['frame_id'] for r in selected}
    current = counts(selected)
    for row in audit:
        row['source_selected_count'] = str(current['distribution_source'][row['distribution_source']])
        if row['frame_id'] in selected_ids:
            row.update(selected='yes',final_selection_role='PRIMARY' if row['selection_group']=='A' else 'BORDERLINE_PROMOTED')
        elif not row['exclusion_reason']:
            row['exclusion_reason'] = ('near_duplicate_of_selected' if current['selection_duplicate_group'][row['selection_duplicate_group']]
                                       else 'source_cap_reached' if current['distribution_source'][row['distribution_source']] >= settings['max_per_source']
                                       else 'not_needed_for_current_coverage')
    for rank,row in enumerate(sorted(selected,key=lambda r:(r['selection_group'],-finite(r['selection_score']),r['frame_id'])),1):
        row['selection_rank']=str(rank)
    remaining = deficits(selected,settings)
    if len(selected) < settings['min_count']: remaining['total_count']=settings['min_count']-len(selected)
    group_counts=Counter(r['selection_group'] for r in audit)
    summary = dict(total_images=len(audit),group_counts={g:group_counts[g] for g in ('A','B','C')},
                   total_candidates=len(primary)+len(borderline),stage1_A_frame_ids=stage1,
                   selected_count=len(selected),B_promotions=sum(r['selection_group']=='B' for r in selected),
                   distributions={k:dict(v) for k,v in current.items()},remaining_shortages=remaining,
                   duplicate_pruned=sum(r['exclusion_reason']=='near_duplicate_of_selected' for r in audit),
                   identity_safety='AVAILABLE_ENFORCED' if identity_available else 'UNAVAILABLE_REQUIRES_HUMAN_REVIEW',
                   status='NEEDS_REVIEW' if remaining or not identity_available or current['expression_bucket']['UNKNOWN'] else 'CANDIDATE_SET_READY_FOR_HUMAN_REVIEW')
    return audit,summary
