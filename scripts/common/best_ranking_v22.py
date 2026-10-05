"""BEST v2.2: base quality times balanced critical quality, minus geometry concern."""
import math
from common import best_ranking_v21 as previous
from common.best_ranking_v21 import (number, POSITIVE, PENALTIES, METRICS, QUALITY_METRICS,
    fit_context, effective_settings as previous_settings, normalized, clip, fatal_reason)
from common.best_quality_v22 import eye_factors, detail_factors, geometric, quality_ratio

VERSION = 'best_rank_v2.2'


def effective_settings(settings, config=None):
    from common.config import load_config
    config = config or load_config()
    result = previous_settings(settings, config)
    result['_evidence']['face_size_quality_anchor'] = config['step3_face_gate']['min_face_dim_upper_body']
    return result


def score_row(original, settings, context):
    if '_evidence' not in settings: settings = effective_settings(settings)
    row = previous.score_row(original, settings, context)
    row['ranking_version'] = VERSION
    factor_fields = ('eye_quality_factor', 'blur_quality_factor', 'exposure_quality_factor',
                     'measurement_reliability_factor', 'critical_face_quality', 'base_quality')
    row.update({k: '' for k in factor_fields})
    if row['fatal_reject'] == 'true': return row
    eye, eye_reliability, audit = eye_factors(row, settings); row.update(audit)
    expected = row['expected_eye_sides'].split(';') if row['expected_eye_sides'] else []
    detail, detail_coverage, detail_audit = detail_factors(row, context, [side+'_eye' for side in expected] or ['left_eye', 'right_eye'])
    row.update(detail_audit)
    # Detail helper uses region names; eye helper uses the same left_eye/right_eye names.
    exposure_strengths = previous.defect_evidence(row, settings)[0]
    losses = [exposure_strengths[k] for k in ('clipping', 'haze', 'dark_exposure')]
    exposure = None if any(v is None for v in losses) else 1-max(losses)
    exposure_keys = ('face_brightness_mean', 'highlight_clip_ratio', 'face_shadow_ratio',
                     'dynamic_range_p95_p5', 'local_face_contrast')
    exposure_coverage = sum(number(row.get(k)) is not None for k in exposure_keys)/len(exposure_keys)
    reliability = geometric([eye_reliability if eye_reliability is not None else 0.,
                             detail_coverage, exposure_coverage])
    row.update(exposure_quality_factor='' if exposure is None else exposure,
               measurement_reliability_factor=reliability,
               measurement_reliability_status='COMPLETE' if reliability == 1 else 'PARTIAL_OR_UNAVAILABLE',
               exposure_evidence_status='STORED_INFORMATION_LOSS_ONLY_VISUAL_HAZE_UNRESOLVED',
               exposure_shadow_ratio_context=row.get('face_shadow_ratio', ''))
    weights = settings.get('positive_weights', POSITIVE)
    a = settings.get('absolute_share', .9); b = settings.get('relative_share', .1)
    # Remove the old usability multiplier from positive eye credit. Eye defects
    # now act once through critical quality, not again as direct deductions.
    row['component_eye_detail'] = row['eye_detail_abs_unadjusted']
    row['eye_detail_abs'] = row['eye_detail_abs_unadjusted']
    row['contribution_eye_detail'] = 100*a*weights['eye_detail']*number(row['availability_eye_detail'])*(number(row['eye_detail_abs_unadjusted']) or 0)
    row['relative_quality_bonus_eye_detail'] = 100*b*weights['eye_detail']*number(row['availability_eye_detail'])*(number(row['eye_detail_relative_unadjusted']) or 0)
    row['eye_quality_positive_credit_loss'] = 0.
    row['component_exposure'] = '' if exposure is None else 1.
    row['contribution_exposure'] = 100*a*weights['exposure'] if exposure is not None else 0.
    # Brightness asymmetry is illumination evidence, not proved invisibility.
    visible = number(row.get('face_visibility_score'))
    corrected = None if visible is None else min(100., visible + (25 if 'asymmetric_eye_brightness' in str(row.get('face_visibility_signals','')).split(';') else 0))
    row['visibility_quality_score'] = '' if corrected is None else corrected
    row['visibility_brightness_adjustment'] = 0 if corrected is None else corrected-visible
    row['component_visibility'] = '' if corrected is None else corrected/100
    row['visibility_abs'] = row['component_visibility']
    row['contribution_visibility'] = 100*a*weights['visibility']*(corrected or 0)/100
    # Remove the legacy visibility group-rank bonus: lighting is not a quality rank.
    row['relative_quality_bonus_visibility'] = 0.
    face_size = quality_ratio(number(row.get('face_short_edge_px')), settings['_evidence']['face_size_quality_anchor'])
    row['component_face_size'] = '' if face_size is None else face_size
    row['contribution_face_size'] = 100*a*weights['face_size']*(face_size or 0)
    row['relative_quality_bonus_face_size'] = 0.
    row['face_size_quality_reference'] = settings['_evidence']['face_size_quality_anchor']
    contrast = quality_ratio(number(row.get('local_face_contrast')), settings['_evidence']['contrast_borderline_max'])
    dynamic = quality_ratio(number(row.get('dynamic_range_p95_p5')), settings['_evidence']['contrast_borderline_max'])
    info = geometric([contrast, dynamic])
    row['component_contrast'] = '' if info is None else info
    row['contrast_abs'] = row['component_contrast']
    row['contribution_contrast'] = 100*a*weights['contrast']*(info or 0)
    # Existing <=1.5 point contrast bonus stays small; no percentile defect deduction.
    row['absolute_quality_total'] = sum(number(row['contribution_'+k]) or 0 for k in weights)
    row['relative_quality_bonus'] = sum(number(row['relative_quality_bonus_'+k]) or 0 for k in weights)
    base = row['absolute_quality_total'] + row['relative_quality_bonus']
    axes = [eye, detail, exposure, reliability]
    # Unknown axes are exposed blank and delegated to measured coverage. A neutral
    # aggregation placeholder does not turn the unknown metric into perfect evidence.
    effective = [1. if value is None else value for value in axes]
    critical = geometric(effective)
    row['critical_quality_unavailable_axes'] = ';'.join(k for k,v in zip(factor_fields[:4], axes) if v is None)
    row.update(base_quality=base, critical_face_quality=critical,
               critical_quality_score_effect=base*(1-critical),
               eye_positive_contribution_effect=0.,
               detail_positive_contribution_effect=row['contribution_sharpness'],
               exposure_positive_contribution_effect=row['contribution_exposure'])
    for family, value in zip(('eye','detail','exposure','reliability'), axes):
        row[family+'_critical_quality_effect'] = '' if value is None else base*(1-value**.25)
        row[family+'_explicit_penalty_effect'] = 0.
    # Preserve recorded old evidence as audit only; no triple defect deductions.
    for key in tuple(row):
        if key.startswith('deduction_'):
            row['v21_evidence_'+key] = row[key]
            row[key] = 0.
    for k in ('eye_closed','eye_half_open','eye_obstruction','eye_measurement','half_eye',
              'blur','clipping','haze','dark_exposure','shadow','low_contrast','uncertainty'):
        row[k+'_penalty'] = 0.
    geometry = 100*settings.get('penalty_weights', PENALTIES)['obstruction']/2*(1-(corrected or 0)/100) if corrected is not None else 0.
    row['visibility_obstruction_penalty'] = geometry
    row['deduction_visibility_obstruction'] = geometry
    row.update(penalty_total=geometry, best_score=base*critical-geometry,
               ranking_explanation='base_quality * geometric_mean(eye, blur, exposure, reliability) - remaining_geometry_penalty',
               critical_defect_mechanism='EYE_EXPOSURE_RELIABILITY_FACTOR_ONLY_DETAIL_BASE_PLUS_FACTOR_NO_DIRECT_PENALTY')
    return row


def rank_rows(rows, settings, context=None):
    if '_evidence' not in settings: settings = effective_settings(settings)
    if len({r['frame_id'] for r in rows}) != len(rows): raise ValueError('Duplicate frame_id')
    context = context or fit_context(rows, settings)
    result = [score_row(r, settings, context) for r in rows]
    eligible = sorted((r for r in result if r['ranking_eligible']=='true'), key=lambda r:(-r['best_score'], r['frame_id']))
    for i,r in enumerate(eligible,1): r['global_rank']=i
    return eligible + sorted((r for r in result if r['fatal_reject']=='true'), key=lambda r:r['frame_id'])


def choose_round(rows, history, size=45, cap=4, min_stills=10, round_number=None):
    # Reuse immutable v2.1 sampling policy with only the version selector changed.
    # Pass histories filtered to the new version, translated into the helper's
    # version namespace. Inputs/results and their real lineage remain unchanged.
    adapted = [dict(r, ranking_version=previous.VERSION) for r in history if r.get('ranking_version')==VERSION]
    selected,info = previous.choose_round(rows, adapted, size, cap, min_stills, round_number)
    info['ranking_version']=VERSION
    return selected,info
