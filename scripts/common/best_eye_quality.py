"""Per-image eye evidence only. Review decisions and source names are not features."""
import math
from common.best_ranking_v1 import number


def bounded(value):return max(0.,min(1.,value))
def below(value,anchor):return None if value is None else bounded((anchor-value)/anchor)


def eye_quality(row,settings):
    e=settings['_evidence'];n=lambda k:number(row.get(k))
    yaw=n('yaw');expected=[];pose='POSE_UNAVAILABLE_ABSTAIN'
    if yaw is not None:
        if abs(yaw)<=e['profile_yaw_min']:
            expected=['left','right'];pose='BOTH_EYES_EXPECTED'
        else:
            widths=[n(side+'_eye_roi_width') for side in ('left','right')]
            if all(v is not None and v>0 for v in widths) and widths[0]!=widths[1]:
                # Use actual projection, not an uncalibrated signed-yaw convention.
                expected=['left' if widths[0]>widths[1] else 'right']
                pose='PROFILE_LARGER_PROJECTED_EYE_EXPECTED_FAR_SIDE_ABSTAIN'
            else:pose='PROFILE_SIDE_UNRESOLVED_ABSTAIN'
    audit=dict(pose_eye_expectation=pose,expected_eye_sides=';'.join(expected))
    failures=[];obstruction=[];opening=[];states=[]
    semantic=str(row.get('eye_openness_state','UNKNOWN')).upper()
    for side in ('left','right'):
        raw=n(side+'_eye_openness')
        if raw is None:raw=n(side+'_eye_open_ratio')
        presence=n(side+'_eye_presence');detail=n(side+'_eye_local_detail')
        audit[side+'_eye_openness_used']='' if raw is None else raw
        roi=row.get(side+'_eye_roi_status')
        # Numeric evidence is required even when a stale availability flag says measured.
        failed=(detail is None or roi=='UNAVAILABLE' or
                row.get('eye_measurement_availability')=='UNAVAILABLE' or
                row.get('landmark_status','').startswith('UNAVAILABLE'))
        if side not in expected:
            audit[side+'_eye_measurement_reliability']='NOT_EXPECTED_OR_POSE_UNRESOLVED'
            audit[side+'_eye_openness_evidence']='POSE_ABSTAIN'
            continue
        audit[side+'_eye_measurement_reliability']='UNAVAILABLE' if failed else 'MEASURED'
        failures.append(float(failed))
        # A numeric zero is observed low detail, not a missing measurement.
        if failed:obstruction.append(None)
        elif presence is None:obstruction.append(None)
        else:
            # Presence alone cannot prove obstruction; the same eye must also lose detail.
            obstruction.append(math.sqrt(below(presence,e['eye_presence_anchor'])*
                                         below(detail,e['eye_detail_anchor'])))
        if semantic=='OPEN':strength=0.;state='OPEN'
        elif semantic in ('CLOSED','BLINK','CLOSED_OR_BLINK'):
            strength=1.;state='CLOSED_OR_BLINK'
        elif semantic in ('HALF_OPEN','BORDERLINE'):
            if raw is not None and raw<e['eye_closed_max']:
                strength=1.;state='CLOSED_OR_BLINK_BY_EXISTING_RATIO_BIN'
            elif semantic=='BORDERLINE' and raw is not None and raw>=e['eye_borderline_max']:
                strength=0.;state='OPEN_RATIO_ASYMMETRY_NOT_A_DEFECT'
            else:
                weaker=0. if raw is None else bounded((e['eye_borderline_max']-raw)/
                                                      (e['eye_borderline_max']-e['eye_closed_max']))
                strength=.5+settings.get('weak_evidence_scale',.25)*weaker
                state='HALF_OPEN_EXISTING_DIAGNOSTIC'
        elif raw is not None:
            if raw<e['eye_closed_max']:strength=1.;state='CLOSED_OR_BLINK_BY_EXISTING_RATIO_BIN'
            elif raw<e['eye_borderline_max']:
                strength=.5+settings.get('weak_evidence_scale',.25)*bounded(
                    (e['eye_borderline_max']-raw)/(e['eye_borderline_max']-e['eye_closed_max']))
                state='HALF_OPEN_BY_EXISTING_RATIO_BIN'
            else:strength=0.;state='OPEN_BY_EXISTING_RATIO_BIN'
        else:strength=None;state='UNAVAILABLE'
        audit[side+'_eye_openness_evidence']=state
        opening.append(strength);states.append(state)
    measured_open=[v for v in opening if v is not None]
    open_loss=max(measured_open) if measured_open else None
    closed=1. if open_loss==1. else (0. if open_loss is not None else None)
    half=open_loss if open_loss is not None and open_loss<1. else (0. if open_loss==1. else None)
    obstructed=[v for v in obstruction if v is not None]
    obstruction_loss=max(obstructed) if obstructed else None
    measurement_loss=sum(failures)/len(failures) if failures else None
    quality=None
    if open_loss is not None and measurement_loss is not None:
        quality=(1-open_loss)*(1-(obstruction_loss or 0))*(1-measurement_loss)
    audit.update(eye_quality_score='' if quality is None else quality,
                 eye_measurement_failure=str(any(failures)).lower(),
                 eye_quality_state='MEASURED' if quality is not None else 'UNAVAILABLE',
                 eye_quality_reason=';'.join(states) or pose)
    strengths=dict(eye_closed=closed,eye_half_open=half,
                   eye_obstruction=obstruction_loss,eye_measurement=measurement_loss)
    evidence=dict(eye_closed='weaker_expected_eye_closed_existing_semantics',
                  eye_half_open='weaker_expected_eye_half_open_existing_bins',
                  eye_obstruction='same_expected_eye_presence_AND_local_detail_deficits',
                  eye_measurement='expected_eye_unavailable_not_assumed_obstruction')
    return strengths,evidence,audit
