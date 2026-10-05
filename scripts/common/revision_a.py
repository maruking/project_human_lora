"""Separate provisional diagnostics and human-authoritative selection state."""
from common.step3_review import is_review_copy, require_source

import math
from pathlib import Path
import cv2
import numpy as np


def face_mask(points, box, height, width, oval_indices):
    """Shared native-pixel face oval; identical Revision A bbox fallback."""
    mask = np.zeros((height, width), dtype=np.uint8)
    if points is not None:
        coords = np.array([(round(points[i].x*width), round(points[i].y*height))
                           for i in sorted(oval_indices)], dtype=np.int32)
        cv2.fillConvexPoly(mask, cv2.convexHull(coords), 255)
        return mask, 'FACEMESH_FACE_OVAL_CONVEX_HULL'
    x, y, bw, bh = box
    mask[y:y+bh, x:x+bw] = 255
    return mask, 'BBOX_FALLBACK_NO_MESH'


def load_review_settings(path=None):
    import hashlib
    import json
    root = Path(__file__).resolve().parents[2]
    if path is None:
        path = root / 'config/step3_revision_a.local.json'
        if not path.is_file():
            path = root / 'config/step3_revision_a.example.json'
    else:
        path = Path(path)
        if not path.is_absolute():
            path = root / path
    data = path.read_bytes()
    settings = json.loads(data.decode('utf-8-sig'))
    validate_settings(settings)
    return settings, str(path.resolve()), hashlib.sha256(data).hexdigest()


class FormalInventory:
    """Exclude only an explicitly declared supplemental subtree from STEP1 audit."""
    def __init__(self, root, supplemental):
        require_source(root)
        require_source(supplemental)
        self.root = Path(root).resolve()
        self.supplemental = Path(supplemental).resolve()
        if self.supplemental == self.root or not self.supplemental.is_relative_to(self.root):
            raise ValueError('Supplemental directory must be a distinct subtree of raw frames')

    def __fspath__(self):
        return str(self.root)

    def __truediv__(self, name):
        return self.root / name

    def rglob(self, pattern):
        return (p for p in self.root.rglob(pattern) if not is_review_copy(p) and not p.resolve().is_relative_to(self.supplemental))


def validate_settings(s):
    required = ('eye_closed_max', 'eye_borderline_max', 'eye_asymmetry_max',
                'clip_pixel_min', 'bright_pixel_min', 'clip_borderline', 'clip_overexposed',
                'bright_borderline', 'contrast_lost_max', 'contrast_borderline_max',
                'texture_lost_max', 'texture_borderline_max')
    if any(not isinstance(s.get(k), (int, float)) or isinstance(s[k], bool)
           or not math.isfinite(s[k]) or s[k] < 0 for k in required):
        raise ValueError('Diagnostic settings require finite nonnegative numbers')
    for low, high in (('eye_closed_max', 'eye_borderline_max'),
                      ('clip_borderline', 'clip_overexposed'),
                      ('contrast_lost_max', 'contrast_borderline_max'),
                      ('texture_lost_max', 'texture_borderline_max'),
                      ('bright_pixel_min', 'clip_pixel_min')):
        if s[low] >= s[high]:
            raise ValueError(f'Invalid diagnostic ordering: {low}/{high}')
    if s['clip_pixel_min'] > 255 or s['eye_asymmetry_max'] < 1:
        raise ValueError('Invalid pixel/asymmetry setting')
    if any(s[k] > 1 for k in ('clip_borderline', 'clip_overexposed', 'bright_borderline')):
        raise ValueError('Pixel ratios must be in [0,1]')


def eye_metrics(left, right, settings):
    if left is None or right is None or min(left, right) < 0 or not all(map(math.isfinite, (left, right))):
        return dict(left_eye_open_ratio=left, right_eye_open_ratio=right,
                    eye_open_min=None, eye_open_asymmetry=None, eye_openness_state='UNKNOWN')
    minimum = min(left, right)
    asymmetry = max(left, right) / minimum if minimum > 0 else None
    state = ('CLOSED_OR_BLINK' if minimum < settings['eye_closed_max'] else
             'BORDERLINE' if minimum < settings['eye_borderline_max'] or
             (asymmetry is not None and asymmetry > settings['eye_asymmetry_max']) else 'OPEN')
    return dict(left_eye_open_ratio=left, right_eye_open_ratio=right,
                eye_open_min=minimum, eye_open_asymmetry=asymmetry, eye_openness_state=state)


def pixel_metrics(gray, mask, texture, settings):
    pixels = gray[mask > 0]
    if not len(pixels):
        raise ValueError('Empty face ROI')
    clip = float(np.mean(pixels >= settings['clip_pixel_min']))
    bright = float(np.mean(pixels >= settings['bright_pixel_min']))
    dynamic = float(np.percentile(pixels, 95) - np.percentile(pixels, 5))
    ys, xs = np.where(mask > 0)
    local = []
    # Equal spatial 3x3 cells within the face-mask bounding rectangle.
    yedges = np.linspace(ys.min(), ys.max() + 1, 4, dtype=int)
    xedges = np.linspace(xs.min(), xs.max() + 1, 4, dtype=int)
    for ya, yb in zip(yedges[:-1], yedges[1:]):
        for xa, xb in zip(xedges[:-1], xedges[1:]):
            values = gray[ya:yb, xa:xb][mask[ya:yb, xa:xb] > 0]
            if len(values):
                local.append(float(np.percentile(values, 90)-np.percentile(values, 10)))
    contrast = float(np.mean(local))
    exposure = ('OVEREXPOSED' if clip >= settings['clip_overexposed'] else
                'BORDERLINE' if clip >= settings['clip_borderline'] or bright >= settings['bright_borderline'] else 'NORMAL')
    # A missing cheek metric keeps the detail diagnostic unknown.
    detail = ('UNKNOWN' if texture is None else
              'DETAIL_LOST' if contrast < settings['contrast_lost_max'] or texture < settings['texture_lost_max'] else
              'BORDERLINE' if contrast < settings['contrast_borderline_max'] or texture < settings['texture_borderline_max'] else 'NORMAL')
    return dict(face_highlight_clip_ratio=clip, face_bright_region_ratio=bright,
                face_dynamic_range=dynamic, face_local_contrast=contrast,
                skin_texture_score=texture, face_exposure_state=exposure, face_detail_state=detail)


def selection_state(human, diagnostics):
    """New numeric bins never confer acceptance or rejection."""
    human = human or {}
    decision = human.get('human_accept', '').upper()
    group = human.get('selection_group', '').upper()
    source = human.get('selection_group_source', '')
    reason = human.get('selection_group_reason', '') or human.get('human_notes', '')
    if decision == 'REJECT' or (group == 'C' and source in ('HUMAN_REJECT', 'HUMAN_CONFIRMED')):
        return dict(selection_group='C', selection_group_source='HUMAN_REJECT',
                    selection_group_reason=reason or 'explicit_human_reject',
                    selection_review_status='CONFIRMED', reserve_use_allowed=False)
    if group in ('A', 'B') and source == 'HUMAN_CONFIRMED':
        return dict(selection_group=group, selection_group_source=source,
                    selection_group_reason=reason or 'explicit_human_selection_group',
                    selection_review_status='CONFIRMED', reserve_use_allowed=group == 'B')
    flags = [f"{key}={diagnostics.get(key, 'UNKNOWN')}" for key in
             ('eye_openness_state', 'face_exposure_state', 'face_detail_state')
             if diagnostics.get(key) not in ('OPEN', 'NORMAL')]
    return dict(selection_group='B', selection_group_source='PROVISIONAL_DIAGNOSTIC',
                selection_group_reason=reason or '; '.join(flags) or 'insufficient_human_evidence',
                selection_review_status='UNDECIDED', reserve_use_allowed=False)
