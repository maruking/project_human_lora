"""STEP4 v2: describe stored geometry/pose; no inference or selection."""
from collections import Counter, defaultdict
import math
import statistics

VERSION = 'step4_pose_composition_v2'
INPUT_VERSION = 'best_rank_v2.2'
POSE_BINS = ('FRONTAL', 'THREE_QUARTER_LEFT', 'THREE_QUARTER_RIGHT',
             'PROFILE_LEFT', 'PROFILE_RIGHT', 'NOT_EVALUABLE')
VERTICAL_BINS = ('LOOKING_UP', 'LEVEL', 'LOOKING_DOWN', 'NOT_EVALUABLE')
SCALE_BINS = ('CLOSE_UP', 'UPPER_BODY', 'FULL_BODY', 'NOT_EVALUABLE')
ADDED_FIELDS = ('step4_version', 'step3_fatal_reason', 'pose_bin', 'vertical_pose',
                'roll_state', 'face_scale_bin', 'shot_type', 'face_height_ratio',
                'face_center_x_norm', 'face_center_y_norm', 'horizontal_position',
                'vertical_position', 'face_edge_left', 'face_edge_right',
                'face_edge_top', 'face_edge_bottom', 'face_edge_contact_any',
                'step4_geometry_source', 'step4_pose_source', 'step4_status', 'step4_error')


def finite(value):
    if value in (None, ''):
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Non-finite measurement')
    return number


def settings_from(config):
    """Thresholds have exactly one owner: existing STEP4 and Face Gate SSOT."""
    pose = config.get('step4_pose', {})
    gate = config.get('step3_face_gate', {})
    keys = ('front_yaw_max', 'three_quarter_yaw_max', 'profile_yaw_min',
            'pitch_looking_min', 'pitch_looking_max')
    result = {key: finite(pose[key]) for key in keys}
    result.update({key: finite(gate[key]) for key in
                   ('shot_close_up_threshold', 'shot_full_body_threshold')})
    if any(v is None for v in result.values()):
        raise ValueError('STEP4 requires explicit existing SSOT thresholds')
    if not (0 <= result['front_yaw_max'] < result['three_quarter_yaw_max']
            == result['profile_yaw_min']):
        raise ValueError('Yaw SSOT requires consistent contiguous boundaries')
    if result['pitch_looking_min'] >= result['pitch_looking_max']:
        raise ValueError('Invalid pitch SSOT boundaries')
    if not (0 <= result['shot_full_body_threshold'] < result['shot_close_up_threshold'] <= 1):
        raise ValueError('Invalid existing face-scale SSOT boundaries')
    return result


def yaw_bin(yaw, settings):
    if yaw is None:
        return 'NOT_EVALUABLE'
    if abs(yaw) <= settings['front_yaw_max']:
        return 'FRONTAL'
    side = 'RIGHT' if yaw > 0 else 'LEFT'
    return ('THREE_QUARTER_' if abs(yaw) < settings['profile_yaw_min'] else 'PROFILE_') + side


def pitch_bin(pitch, settings):
    if pitch is None:
        return 'NOT_EVALUABLE'
    if pitch < settings['pitch_looking_min']:
        return 'LOOKING_UP'
    return 'LOOKING_DOWN' if pitch > settings['pitch_looking_max'] else 'LEVEL'


def scale_bin(area, settings):
    if area is None:
        return 'NOT_EVALUABLE'
    if area >= settings['shot_close_up_threshold']:
        return 'CLOSE_UP'
    return 'UPPER_BODY' if area >= settings['shot_full_body_threshold'] else 'FULL_BODY'


def geometry(row):
    width, height = finite(row.get('width')), finite(row.get('height'))
    named = [finite(row.get(k)) for k in
             ('face_bbox_x', 'face_bbox_y', 'face_bbox_width', 'face_bbox_height')]
    packed = row.get('face_bbox', '')
    box = None
    if packed:
        parts = str(packed).split(',')
        if len(parts) != 4:
            raise ValueError('Malformed stored face_bbox')
        box = [finite(p) for p in parts]
        if any(v is None for v in box):
            raise ValueError('Incomplete stored face_bbox')
    if all(v is not None for v in named):
        if box is not None and named != box:
            raise ValueError('Stored bbox representations disagree')
        box = named
    if box is None or width is None or height is None:
        return None
    x, y, bw, bh = box
    if width <= 0 or height <= 0 or bw <= 0 or bh <= 0:
        raise ValueError('Non-positive image/bbox dimensions')
    if not (0 <= x <= x+bw <= width and 0 <= y <= y+bh <= height):
        raise ValueError('Stored bbox is outside image; no clipping invented')
    computed_area = bw*bh/(width*height)
    area = finite(row.get('face_area_ratio'))
    short = finite(row.get('face_short_edge_px'))
    if area is not None and not math.isclose(area, computed_area, abs_tol=1e-9, rel_tol=1e-6):
        raise ValueError('Stored face_area_ratio disagrees with stored bbox')
    if short is not None and short != min(bw, bh):
        raise ValueError('Stored face_short_edge_px disagrees with stored bbox')
    # Exact contact only. No unapproved near-edge distance threshold.
    left, right, top, bottom = x/width == 0, (x+bw)/width == 1, y/height == 0, (y+bh)/height == 1
    return dict(face_area_ratio=row.get('face_area_ratio') if area is not None else computed_area,
                face_short_edge_px=row.get('face_short_edge_px') if short is not None else min(bw, bh),
                face_height_ratio=bh/height, face_center_x_norm=(x+bw/2)/width,
                face_center_y_norm=(y+bh/2)/height,
                face_edge_left=str(left).lower(), face_edge_right=str(right).lower(),
                face_edge_top=str(top).lower(), face_edge_bottom=str(bottom).lower(),
                face_edge_contact_any=str(left or right or top or bottom).lower(),
                step4_geometry_source='STORED_STEP3_BBOX_AND_DIMENSIONS')


def describe(row, settings):
    result = dict(row)  # preserve STEP3 lineage, score, rank and audit evidence verbatim
    result.update({key: '' for key in ADDED_FIELDS})
    result.update(step4_version=VERSION, step3_fatal_reason=row.get('fatal_reject_reason', ''),
                  pose_bin='NOT_EVALUABLE', vertical_pose='NOT_EVALUABLE',
                  face_scale_bin='NOT_EVALUABLE', shot_type='NOT_EVALUABLE',
                  roll_state='NOT_CLASSIFIED', horizontal_position='NOT_CLASSIFIED',
                  vertical_position='NOT_CLASSIFIED', step4_status='NOT_EVALUABLE')
    if row.get('shot_type') not in (None, ''):
        result['step3_shot_type'] = row['shot_type']
    eligible = str(row.get('ranking_eligible', '')).lower()
    if eligible == 'false':
        result['step4_status'] = 'NOT_APPLICABLE_STEP3_FATAL'
        return result
    if eligible != 'true':
        result.update(step4_status='ERROR', step4_error='Invalid ranking_eligible')
        return result
    issues, errors = [], []
    angles = {}
    for name in ('yaw', 'pitch', 'roll'):
        try:
            angles[name] = finite(row.get(name))
        except (ValueError, TypeError) as exc:
            angles[name] = None
            errors.append(name + ': ' + str(exc))
    if row.get('pose_status') == 'MEASURED':
        result.update(pose_bin=yaw_bin(angles['yaw'], settings),
                      vertical_pose=pitch_bin(angles['pitch'], settings),
                      step4_pose_source='STORED_STEP3_MEASURED')
        issues.extend('missing_' + key for key, value in angles.items() if value is None)
    else:
        issues.append('stored_pose_not_measured')
        result['step4_pose_source'] = 'STORED_STEP3_UNAVAILABLE'
    try:
        geom = geometry(row)
        if geom is None:
            issues.append('missing_bbox_or_image_dimensions')
        else:
            result.update(geom)
            result['face_scale_bin'] = scale_bin(finite(geom['face_area_ratio']), settings)
            result['shot_type'] = result['face_scale_bin']  # compatibility alias, not body visibility
    except (ValueError, TypeError) as exc:
        errors.append('geometry: ' + str(exc))
    result['step4_error'] = ';'.join(errors + issues)
    result['step4_status'] = 'ERROR' if errors else 'NOT_EVALUABLE' if issues else 'MEASURED'
    return result


def describe_rows(rows, settings):
    identifiers = [r.get('frame_id') for r in rows]
    if not identifiers or any(not k for k in identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError('Empty or non-unique STEP3 frame universe')
    return [describe(row, settings) for row in rows]


def distribution(rows, field, categories=()):
    counts = Counter(str(row.get(field) or 'NOT_EVALUABLE') for row in rows)
    return {key: counts[key] for key in dict.fromkeys((*categories, *sorted(counts)))}


def cross(rows, left, right):
    counts = defaultdict(Counter)
    for row in rows:
        counts[row[left]][row[right]] += 1
    return {key: dict(sorted(value.items())) for key, value in sorted(counts.items())}


def summarize(rows):
    eligible = [r for r in rows if str(r['ranking_eligible']).lower() == 'true']
    summary = dict(step4_version=VERSION, total_rows=len(rows), ranking_eligible_rows=len(eligible),
                   input_kind_all_rows=distribution(rows, 'input_kind'),
                   input_kind=distribution(eligible, 'input_kind'),
                   statuses=distribution(rows, 'step4_status'),
                   pose_bin=distribution(eligible, 'pose_bin', POSE_BINS),
                   vertical_pose=distribution(eligible, 'vertical_pose', VERTICAL_BINS),
                   face_scale_bin=distribution(eligible, 'face_scale_bin', SCALE_BINS),
                   distribution_scope='ranking_eligible=true, including missing/error records',
                   cross_tables={'pose_bin_x_face_scale_bin': cross(eligible, 'pose_bin', 'face_scale_bin'),
                                 'pose_bin_x_input_kind': cross(eligible, 'pose_bin', 'input_kind'),
                                 'face_scale_bin_x_input_kind': cross(eligible, 'face_scale_bin', 'input_kind')},
                   human_review_dependency='NONE', reject_or_quota_introduced=False)
    groups = defaultdict(list)
    for row in rows:
        groups[(row['input_kind'], row['source_id'], row.get('video_id', ''))].append(row)
    sources = []
    for (kind, source, video), group in sorted(groups.items()):
        accepted = [r for r in group if str(r['ranking_eligible']).lower() == 'true']
        yaw = [finite(r['yaw']) for r in accepted if r['pose_bin'] != 'NOT_EVALUABLE']
        scores = [finite(r.get('best_score')) for r in accepted]
        scores = [s for s in scores if s is not None]
        record = dict(input_kind=kind, source_id=source, video_id=video, total_rows=len(group),
                      ranking_eligible_rows=len(accepted),
                      total_measured=sum(r['step4_status'] == 'MEASURED' for r in accepted),
                      not_evaluable=sum(r['step4_status'] == 'NOT_EVALUABLE' for r in accepted),
                      errors=sum(r['step4_status'] == 'ERROR' for r in accepted),
                      median_yaw=statistics.median(yaw) if yaw else '',
                      min_yaw=min(yaw) if yaw else '', max_yaw=max(yaw) if yaw else '',
                      best_step3_score=max(scores) if scores else '')
        record.update({'pose_' + k: v for k, v in distribution(accepted, 'pose_bin', POSE_BINS).items()})
        record.update({'face_scale_' + k: v for k, v in distribution(accepted, 'face_scale_bin', SCALE_BINS).items()})
        sources.append(record)
    return summary, sources


def markdown_summary(summary):
    lines = ['# STEP4 Pose / Composition Summary', '', 'Version: ' + VERSION,
             '', f"Full input rows: {summary['total_rows']}; ranking eligible: {summary['ranking_eligible_rows']}.",
             '', 'These are descriptive measurements, not quality, quotas or selection.',
             'RIGHT/LEFT follows signed repository yaw; anatomical/mirror-independent direction is not asserted.',
             'face_scale_bin uses face area, not verified torso/leg visibility. shot_type is its alias.',
             'Missing values stay missing. Position and roll bins are NOT_CLASSIFIED.',
             'Distributions below include all ranking-eligible rows, including missing measurements.', '']
    for field in ('statuses', 'input_kind_all_rows', 'input_kind', 'pose_bin', 'vertical_pose', 'face_scale_bin'):
        lines.extend(['## ' + field, '', '| State | Count |', '| --- | ---: |'])
        lines.extend(f'| {key} | {value} |' for key, value in summary[field].items())
        lines.append('')
    for name, table in summary['cross_tables'].items():
        lines.extend(['## ' + name, '', '| Row | Column | Count |', '| --- | --- | ---: |'])
        lines.extend(f'| {left} | {right} | {count} |' for left, columns in table.items()
                     for right, count in columns.items())
        lines.append('')
    lines.extend(['Human Review dependency: NONE. Reject/quota introduced: NO.',
                  'STEP5+ is not executed. Inspect distribution before designing STEP5.', ''])
    return '\n'.join(lines)
