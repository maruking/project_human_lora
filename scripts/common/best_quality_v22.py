"""Bounded quality factors; names, review decisions and ranks are never evidence."""
import math
from statistics import median
from common.best_ranking_v1 import number
from common.best_eye_quality import eye_quality as previous_eye_quality


def clip(value):
    return max(0., min(1., value))


def geometric(values):
    """Unknown is not numeric zero or measured perfect quality."""
    if not values or any(v is None for v in values):
        return None
    return math.prod(values) ** (1 / len(values))


def quality_ratio(value, anchor):
    # Reuse the positive P95 reference. This is comparative quality, not an
    # approved physical defect threshold. Unlike P5 clipping it has no dead zone.
    if value is None or anchor is None or anchor <= 0:
        return None
    return clip(value / anchor)


def eye_factors(row, settings):
    _, _, audit = previous_eye_quality(row, settings)
    expected = audit['expected_eye_sides'].split(';') if audit['expected_eye_sides'] else []
    n = lambda key: number(row.get(key))
    opening = []; obstruction = []; reliability = []
    semantics = str(row.get('eye_openness_state', 'UNKNOWN')).upper()
    e = settings['_evidence']
    for side in ('left', 'right'):
        audit[side + '_eye_landmark_evidence_source'] = ('PER_EYE' if side + '_eye_landmark_status' in row else 'WHOLE_MESH_PROXY')
        audit[side + '_eye_roi_truth_status'] = 'NOT_VERIFIED_BY_STORED_ROI_COORDINATES'
        if side not in expected:
            audit[side + '_eye_measurement_status'] = 'NOT_EXPECTED_BY_POSE' if expected else 'POSE_UNRESOLVED'
            audit[side + '_eye_landmark_availability'] = row.get(side + '_eye_landmark_status', row.get('landmark_status', ''))
            continue
        detail = n(side + '_eye_local_detail'); presence = n(side + '_eye_presence')
        raw = n(side + '_eye_openness')
        if raw is None: raw = n(side + '_eye_open_ratio')
        landmark = row.get(side + '_eye_landmark_status', row.get('landmark_status', ''))
        roi = row.get(side + '_eye_roi_status', '')
        width = n(side + '_eye_roi_width'); height = n(side + '_eye_roi_height')
        status = 'VALID'
        if str(landmark).startswith('UNAVAILABLE') or not landmark:
            status = 'LANDMARK_MISSING'
        elif roi not in ('MEASURED', 'VALID') or width is None or height is None or min(width, height) < 3:
            status = 'ROI_INVALID'
        elif detail is None: status = 'DETAIL_UNAVAILABLE'
        elif raw is None or presence is None: status = 'MEASUREMENT_UNAVAILABLE'
        elif detail < 0 or raw < 0 or not 0 <= presence <= 1:
            status = 'INCONSISTENT'
        elif semantics == 'OPEN' and raw < e['eye_borderline_max']:
            status = 'INCONSISTENT'
        elif row.get(side + '_eye_landmark_inside_roi') == 'false':
            status = 'INCONSISTENT'
        audit[side + '_eye_measurement_status'] = status
        audit[side + '_eye_landmark_availability'] = landmark
        reliability.append(float(status == 'VALID'))
        if status != 'VALID':
            audit[side + '_eye_opening_quality'] = ''
            audit[side + '_eye_obstruction_concern'] = ''
            continue  # Failure goes through reliability, never invented occlusion.
        if semantics in ('CLOSED', 'BLINK', 'CLOSED_OR_BLINK') or raw < e['eye_closed_max']:
            op = 0.
        elif semantics == 'OPEN' or raw >= e['eye_borderline_max']:
            op = 1.
        elif len(expected) == 1:
            # A projected profile eye ratio is not directly comparable to a
            # frontal ratio. Use a continuous ratio, no fixed half-state jump.
            op = clip(raw / e['eye_borderline_max'])
        else:
            weaker = clip((e['eye_borderline_max'] - raw) /
                          (e['eye_borderline_max'] - e['eye_closed_max']))
            op = 1 - (.5 + settings.get('weak_evidence_scale', .25) * weaker)
        concern = math.sqrt(clip((e['eye_presence_anchor'] - presence) / e['eye_presence_anchor']) *
                            clip((e['eye_detail_anchor'] - detail) / e['eye_detail_anchor']))
        opening.append(op); obstruction.append(concern)
        audit[side + '_eye_opening_quality'] = op
        audit[side + '_eye_obstruction_concern'] = concern
    eye_reliability = sum(reliability) / len(reliability) if reliability else None
    opening_quality = min(opening) if opening else None
    obstruction_quality = 1 - max(obstruction) if obstruction else None
    eye = opening_quality * obstruction_quality if opening else None
    audit.update(eye_quality_factor='' if eye is None else eye,
                 eye_opening_quality='' if opening_quality is None else opening_quality,
                 eye_obstruction_quality='' if obstruction_quality is None else obstruction_quality,
                 eye_measurement_reliability='' if eye_reliability is None else eye_reliability,
                 eye_quality_score='' if eye is None else eye,
                 eye_quality_state='MEASURED' if eye is not None else 'UNAVAILABLE',
                 eye_measurement_failure=str(any(v == 0 for v in reliability)).lower())
    return eye, eye_reliability, audit


def detail_factors(row, context, expected):
    metrics = ('face_laplacian_canonical_192', 'face_tenengrad_canonical_192')
    local = [side + '_local_detail' for side in expected] + ['mouth_local_detail']
    ratios = {k: quality_ratio(number(row.get(k)), context['anchors'][k]['high'])
              for k in (*metrics, *local)}
    global_quality = geometric([ratios[k] for k in metrics])
    measured = [ratios[k] for k in local if ratios[k] is not None]
    local_quality = median(measured) if measured else None
    # Local edges cannot restore weak BOTH-canonical evidence. One weak local
    # region cannot dominate the robust median. Missing is recorded separately.
    blur = global_quality * local_quality if global_quality is not None and local_quality is not None else None
    coverage = sum(v is not None for v in ratios.values()) / len(ratios)
    return blur, coverage, dict(global_detail_quality='' if global_quality is None else global_quality,
        local_detail_quality='' if local_quality is None else local_quality,
        blur_quality_factor='' if blur is None else blur,
        blur_evidence_strength='' if blur is None else 1-blur,
        blur_scaling_state='COMPARATIVE_P95_QUALITY_NOT_CALIBRATED_PHYSICAL_BLUR_THRESHOLD',
        detail_measurement_coverage=coverage)
