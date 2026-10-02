"""NEW STEP 3: face eligibility gate for every STEP 2 image.

Reads the original images and dataset_report.csv. MediaPipe landmarks are a PoC
visibility proxy: they cannot prove that hair or an object does not cover a face.
Review the output categories before using them for training.
"""

from __future__ import annotations

from common.config import configure_parser, configure_constants, load_for_cli, get_section, resolve_project_path
from common.video_manifest import manifest_lock
from common.step3_audit import validate_input, publish, geometry_diagnostics, safe_output, build_artifacts

import argparse
import csv
import hashlib
import io
import math
import os
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from statistics import median

try:
    import cv2
except ImportError:
    print("Missing dependency: opencv-python", file=sys.stderr)
    raise SystemExit(2)
try:
    import numpy as np
except ImportError:
    print("Missing dependency: numpy", file=sys.stderr)
    raise SystemExit(2)
try:
    import mediapipe as mp
except ImportError:
    mp = None



# PoC initial thresholds. Tune after visual inspection.
FACE_CROP_MARGIN = 0.20
FACE_CORE_SCALE = 0.80  # Scale for inner core face sharpness (avoids hair/background edges)
MIN_FACE_VISIBILITY_SCORE = 70.0
MIN_FACE_SHARPNESS_PERCENTILE = 20.0
MIN_GLOBAL_LAPLACIAN = 25.0  # Integrated STEP 2 pre-filter: drop severe whole-image motion blur
MIN_FACE_LAPLACIAN = 50.0    # Absolute face core blur threshold to eliminate hand/motion blur

# Shot classification thresholds (based on face_area_ratio)
SHOT_CLOSE_UP_THRESHOLD = 0.12
SHOT_FULL_BODY_THRESHOLD = 0.04

# Dynamic resolution requirements by shot type
MIN_SOURCE_SHORT_EDGE_FULLBODY = 720  # Full-body requires >=720p source to ensure body detail
MIN_FACE_DIM_CLOSE_UP = 140
MIN_FACE_DIM_UPPER_BODY = 110
MIN_FACE_DIM_FULL_BODY = 80

# Anatomical patch sharpness threshold (Normalized Tenengrad)
MIN_EYE_SHARPNESS = 1.60

# Hair strand density on central face & eye biological presence thresholds
MAX_FACE_CENTRAL_GRADIENT = 65.0       # Threshold for hair strand occlusion across central face
MIN_SINGLE_EYE_FEATURE_RATIO = 0.070   # Minimum (sclera + iris) for each individual eye (rejects one-eye occlusion)
MIN_AVG_EYE_FEATURE_RATIO = 0.080      # Minimum average (sclera + iris) across both eyes
MAX_EYE_ASYMMETRY_RATIO = 2.20         # Maximum allowed asymmetry ratio between left and right eye features

# Face exposure & backlit thresholds (rejects underexposed / backlit shadow faces)
MIN_FACE_BRIGHTNESS = 95.0             # Minimum face crop brightness mean to avoid dark/shadowed faces
MIN_FACE_TO_GLOBAL_RATIO = 0.65        # Minimum ratio of face brightness to global image brightness

# Beauty filter & skin over-smoothing detection thresholds (Plastic Skin Index)
MIN_SKIN_TEXTURE_CLOSEUP = 0.050       # Minimum normalized cheek skin texture for CLOSE_UP
MIN_SKIN_TEXTURE_UPPER_BODY = 0.035    # Minimum normalized cheek skin texture for UPPER_BODY
MAX_PLASTICITY_RATIO = 45.0            # Max eye_sharpness / skin_texture_score before flagging beauty filter

LAPLACIAN_WEIGHT = 0.50
TENENGRAD_WEIGHT = 0.50
DETECTION_CONFIDENCE = 0.50
MAX_FACES = 10

NEW_COLUMNS = (
    "step3_step_name",
    "shot_type",
    "source_short_edge",
    "face_detected", "face_count", "multiple_faces",
    "face_bbox_x", "face_bbox_y", "face_bbox_width", "face_bbox_height", "face_min_dimension", "face_area_ratio",
    "facemesh_detected",
    "face_brightness_mean", "face_to_global_brightness_ratio",
    "face_central_gradient",
    "left_eye_presence_ratio", "right_eye_presence_ratio", "eye_presence_valid",
    "eye_sharpness", "mouth_sharpness",
    "skin_texture_score", "plasticity_ratio", "beauty_filter_detected",
    "face_laplacian_score", "face_tenengrad_score",
    "face_laplacian_percentile", "face_tenengrad_percentile", "face_sharpness_score",
    "face_visibility_score", "occlusion_detected", "occlusion_level", "face_visibility_signals",
    "eye_ratio_left", "eye_ratio_right", "eye_brightness_ratio", "eye_texture_ratio",
    "face_eligible", "face_gate_category", "face_gate_reason", "face_gate_status", "face_gate_error",
)
DIAGNOSTIC_COLUMNS = ("left_eye_openness", "right_eye_openness", "eye_openness_mean", "blink_suspected", "mouth_open_ratio", "mouth_open_class", "primary_face_selection_method", "provisional_face_scale_class", "beauty_filter_applicability", "face_gate_error_category", "anatomical_metric_status")

REVIEW_FOLDERS = (
    "ELIGIBLE", "REJECT_OCCLUSION", "REJECT_BLUR", "REJECT_SMALL_FACE",
    "REJECT_LOW_RES", "REJECT_BEAUTY_FILTER", "REJECT_MULTIPLE_FACE", "REJECT_NO_FACE", "REVIEW_UNKNOWN",
)


def image_path(root: Path, filename: str) -> tuple[Path, Path]:
    if "\\" in filename or any(part in ("", ".", "..") for part in filename.split("/")):
        raise ValueError("Invalid relative filename")
    relative = Path(filename)
    source = (root / relative).resolve()
    if relative.is_absolute() or not source.is_relative_to(root.resolve()) or not source.is_file():
        raise ValueError("Frame is outside the active generation or missing")
    return source, relative


def face_box(detection: object, width: int, height: int) -> tuple[int, int, int, int]:
    box = detection.location_data.relative_bounding_box
    x1 = max(0, min(width, math.floor(box.xmin * width)))
    y1 = max(0, min(height, math.floor(box.ymin * height)))
    x2 = max(0, min(width, math.ceil((box.xmin + box.width) * width)))
    y2 = max(0, min(height, math.ceil((box.ymin + box.height) * height)))
    return x1, y1, max(0, x2 - x1), max(0, y2 - y1)


def crop_with_margin(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x, y, width, height = box
    image_height, image_width = image.shape[:2]
    mx, my = int(width * FACE_CROP_MARGIN), int(height * FACE_CROP_MARGIN)
    crop = image[max(0, y - my):min(image_height, y + height + my),
                 max(0, x - mx):min(image_width, x + width + mx)]
    if crop.size == 0:
        raise ValueError("empty face crop")
    return crop


def crop_face_core(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Crop inner face core to isolate face texture from hair/background edges for sharpness."""
    x, y, width, height = box
    image_height, image_width = image.shape[:2]
    cx, cy = x + width / 2.0, y + height / 2.0
    cw, ch = int(width * FACE_CORE_SCALE), int(height * FACE_CORE_SCALE)
    x1 = max(0, int(cx - cw / 2.0))
    y1 = max(0, int(cy - ch / 2.0))
    x2 = min(image_width, int(cx + cw / 2.0))
    y2 = min(image_height, int(cy + ch / 2.0))
    crop = image[y1:y2, x1:x2]
    return crop if crop.size > 0 else crop_with_margin(image, box)


def sharpness(crop: np.ndarray) -> tuple[float, float]:
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    laplacian = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    dx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    dy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    tenengrad = float(np.mean(dx * dx + dy * dy))
    return laplacian, tenengrad


def classify_shot_type(face_area_ratio: float) -> str:
    """Classify framing into CLOSE_UP, UPPER_BODY, or FULL_BODY."""
    if face_area_ratio >= SHOT_CLOSE_UP_THRESHOLD:
        return "CLOSE_UP"
    elif face_area_ratio >= SHOT_FULL_BODY_THRESHOLD:
        return "UPPER_BODY"
    else:
        return "FULL_BODY"


def extract_patch(image: np.ndarray, center: tuple[float, float], size: tuple[float, float]) -> np.ndarray:
    cx, cy = center
    w, h = size
    ih, iw = image.shape[:2]
    x1 = max(0, int(cx - w / 2.0))
    y1 = max(0, int(cy - h / 2.0))
    x2 = min(iw, int(cx + w / 2.0))
    y2 = min(ih, int(cy + h / 2.0))
    return image[y1:y2, x1:x2]


def patch_normalized_tenengrad(gray_patch: np.ndarray) -> float:
    """Compute contrast-normalized Tenengrad: P90(gradient) / (local_std + eps)."""
    if gray_patch.size == 0 or min(gray_patch.shape) < 3:
        return 0.0
    gx = cv2.Sobel(gray_patch, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_patch, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    p90 = float(np.percentile(mag, 90))
    std = float(np.std(gray_patch))
    return float(p90 / (std + 1e-4))


def central_face_gradient(image: np.ndarray, landmarks: list | None, width: int, height: int) -> float:
    """Measure gradient density on central face polygon. High gradient indicates hair covering face."""
    if landmarks is None:
        return 0.0
    poly = np.array([
        (int(landmarks[10].x * width), int(landmarks[10].y * height)),    # Forehead
        (int(landmarks[234].x * width), int(landmarks[234].y * height)),  # Left cheek
        (int(landmarks[152].x * width), int(landmarks[152].y * height)),  # Chin
        (int(landmarks[454].x * width), int(landmarks[454].y * height)),  # Right cheek
    ], dtype=np.int32)
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask, poly, 255)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    face_pixels = mask > 0
    if not np.any(face_pixels):
        return 0.0
    return float(np.mean(mag[face_pixels]))


def eye_presence_metrics(image: np.ndarray, landmarks: list | None, width: int, height: int) -> tuple[float, float, bool]:
    """Verify biological eye presence (sclera and iris) in eye patches to reject occluded eyes."""
    if landmarks is None:
        return 0.0, 0.0, False
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat, val = hsv[:, :, 1], hsv[:, :, 2]
    eye_ratios = []
    for (outer, inner) in ((33, 133), (263, 362)):
        cx = (landmarks[outer].x + landmarks[inner].x) * width / 2.0
        cy = (landmarks[outer].y + landmarks[inner].y) * height / 2.0
        span = math.hypot((landmarks[outer].x - landmarks[inner].x) * width,
                          (landmarks[outer].y - landmarks[inner].y) * height)
        rw = max(int(span * 0.8), 8)
        rh = max(int(span * 0.5), 6)
        x1, y1 = max(0, int(cx - rw)), max(0, int(cy - rh))
        x2, y2 = min(width, int(cx + rw)), min(height, int(cy + rh))
        patch_sat = sat[y1:y2, x1:x2]
        patch_val = val[y1:y2, x1:x2]
        if patch_sat.size == 0:
            eye_ratios.append(0.0)
            continue
        # Sclera: low saturation (< 55) & bright (> 115)
        sclera = np.mean((patch_sat < 55) & (patch_val > 115))
        # Iris: dark pixels (< 75)
        iris = np.mean(patch_val < 75)
        eye_ratios.append(float(sclera + iris))
    
    l_ratio, r_ratio = eye_ratios[0], eye_ratios[1]
    min_feature = min(l_ratio, r_ratio)
    avg_feature = (l_ratio + r_ratio) / 2.0
    asymmetry = max(l_ratio, r_ratio) / max(min_feature, 1e-4)
    # Both eyes must individually satisfy the single eye threshold, average must be high, and no severe asymmetry
    is_valid = (min_feature >= MIN_SINGLE_EYE_FEATURE_RATIO) and (avg_feature >= MIN_AVG_EYE_FEATURE_RATIO) and (asymmetry <= MAX_EYE_ASYMMETRY_RATIO)
    return l_ratio, r_ratio, is_valid


def anatomical_sharpness(image: np.ndarray, landmarks: list | None, box: tuple[int, int, int, int], eye_valid: bool = True) -> tuple[float, float]:
    """Measure sharpness strictly on anatomical patches (eyes and mouth) avoiding hair/clothing edges."""
    if landmarks is None:
        return 0.0, 0.0
    ih, iw = image.shape[:2]
    _, _, bw, bh = box
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Mouth patch: left corner 61, right corner 291
    m_cx = (landmarks[61].x + landmarks[291].x) * iw / 2.0
    m_cy = (landmarks[61].y + landmarks[291].y) * ih / 2.0
    m_span = math.hypot((landmarks[61].x - landmarks[291].x) * iw, (landmarks[61].y - landmarks[291].y) * ih)
    m_patch = extract_patch(gray, (m_cx, m_cy), (max(m_span * 1.4, 10.0), max(m_span * 0.8, 8.0)))
    m_sharp = patch_normalized_tenengrad(m_patch)

    if not eye_valid:
        # If either eye is occluded by hair/hands/shadow, disable eye sharpness calculation
        return 0.0, m_sharp

    # Left eye patch: outer 33, inner 133
    l_cx = (landmarks[33].x + landmarks[133].x) * iw / 2.0
    l_cy = (landmarks[33].y + landmarks[133].y) * ih / 2.0
    l_span = math.hypot((landmarks[33].x - landmarks[133].x) * iw, (landmarks[33].y - landmarks[133].y) * ih)
    l_patch = extract_patch(gray, (l_cx, l_cy), (max(l_span * 1.5, 8.0), max(l_span * 1.2, 8.0)))

    # Right eye patch: outer 263, inner 362
    r_cx = (landmarks[263].x + landmarks[362].x) * iw / 2.0
    r_cy = (landmarks[263].y + landmarks[362].y) * ih / 2.0
    r_span = math.hypot((landmarks[263].x - landmarks[362].x) * iw, (landmarks[263].y - landmarks[362].y) * ih)
    r_patch = extract_patch(gray, (r_cx, r_cy), (max(r_span * 1.5, 8.0), max(r_span * 1.2, 8.0)))

    l_sharp = patch_normalized_tenengrad(l_patch)
    r_sharp = patch_normalized_tenengrad(r_patch)

    # Require BOTH eyes to have valid gradients
    if l_sharp <= 0.0 or r_sharp <= 0.0:
        return 0.0, m_sharp

    eye_sharp = (l_sharp + r_sharp) / 2.0
    return eye_sharp, m_sharp


def cheek_skin_texture_metrics(
    image: np.ndarray,
    landmarks: list | None,
    box: tuple[int, int, int, int],
    eye_sharpness: float,
    shot_type: str,
    min_skin_texture_close_up: float,
    min_skin_texture_upper_body: float,
    max_plasticity_ratio: float,
) -> tuple[float, float, bool]:
    """Measure micro-texture on cheek patches to detect beauty-filter over-smoothing (plastic skin)."""
    if landmarks is None:
        return 0.0, 0.0, False

    ih, iw = image.shape[:2]
    _, _, bw, bh = box
    min_dim = min(bw, bh)

    # Face scale radius for cheek patch (avoiding nostrils and eyes)
    rad = max(int(min_dim * 0.07), 6)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    scores = []
    # Left cheek: landmark 50, Right cheek: landmark 280
    for idx in (50, 280):
        cx = int(landmarks[idx].x * iw)
        cy = int(landmarks[idx].y * ih)
        x1, y1 = max(0, cx - rad), max(0, cy - rad)
        x2, y2 = min(iw, cx + rad), min(ih, cy + rad)
        patch = gray[y1:y2, x1:x2]
        if patch.size == 0 or min(patch.shape) < 3:
            continue
        lap_var = float(cv2.Laplacian(patch, cv2.CV_64F).var())
        mean_br = max(float(patch.mean()), 10.0)
        norm_lap = float(lap_var / mean_br)
        scores.append(norm_lap)

    if not scores:
        return 0.0, 0.0, False

    skin_texture = float(np.mean(scores))
    plasticity = float(eye_sharpness / max(skin_texture, 0.005))

    # Dynamic threshold by shot type:
    # In FULL_BODY, optical resolution is naturally low, so we do not reject for beauty filter.
    is_filter = False
    if shot_type == "CLOSE_UP":
        if skin_texture < min_skin_texture_close_up or plasticity > max_plasticity_ratio:
            is_filter = True
    elif shot_type == "UPPER_BODY":
        if skin_texture < min_skin_texture_upper_body or plasticity > max_plasticity_ratio:
            is_filter = True

    return skin_texture, plasticity, is_filter


def matching_landmarks(mesh_result: object, box: tuple[int, int, int, int], width: int, height: int) -> list | None:
    faces = mesh_result.multi_face_landmarks or []
    if not faces:
        return None
    x, y, w, h = box
    center_x, center_y = x + w / 2, y + h / 2
    return min(
        (face.landmark for face in faces),
        key=lambda points: (points[1].x * width - center_x) ** 2 + (points[1].y * height - center_y) ** 2,
    )


def eye_ratio(points: list, outer: int, inner: int, upper: int, lower: int, width: int, height: int) -> float:
    horizontal = math.hypot((points[outer].x - points[inner].x) * width,
                            (points[outer].y - points[inner].y) * height)
    vertical = math.hypot((points[upper].x - points[lower].x) * width,
                          (points[upper].y - points[lower].y) * height)
    return vertical / max(horizontal, 1.0)


def visibility(detection: object, landmarks: list | None, box: tuple[int, int, int, int],
               image: np.ndarray) -> tuple[float, str, str, dict[str, str]]:
    height, width = image.shape[:2]
    metrics: dict[str, str] = {
        "facemesh_detected": "false",
        "eye_ratio_left": "",
        "eye_ratio_right": "",
        "eye_brightness_ratio": "",
        "eye_texture_ratio": "",
    }
    # HARD GATE: FaceMesh (468 points) is strictly required.
    # If FaceMesh fails, it is an extreme angle, severe occlusion, or false positive (e.g. hair/back of head).
    if landmarks is None:
        return 0.0, "unknown", "landmarks_not_found", metrics
    x, y, w, h = box
    if w <= 0 or h <= 0:
        return 0.0, "unknown", "empty_face_box", metrics

    metrics["facemesh_detected"] = "true"
    score = 100.0
    signals: list[str] = []
    confidence = float(detection.score[0]) if detection.score else 0.0
    if confidence < 0.60:
        score -= 25
        signals.append("low_detection_confidence")
    elif confidence < 0.75:
        score -= 12
        signals.append("moderate_detection_confidence")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Dense Face Mesh geometric check
    key_points = (33, 263, 1, 61, 291, 152)  # eyes, nose, mouth, chin
    outside = sum(
        not (0 <= landmarks[index].x <= 1 and 0 <= landmarks[index].y <= 1 and
             x - 0.15 * w <= landmarks[index].x * width <= x + 1.15 * w and
             y - 0.15 * h <= landmarks[index].y * height <= y + 1.15 * h)
        for index in key_points
    )
    if outside:
        score -= min(45, outside * 15)
        signals.append("implausible_face_landmarks")

    left_eye = eye_ratio(landmarks, 33, 133, 159, 145, width, height)
    right_eye = eye_ratio(landmarks, 263, 362, 386, 374, width, height)
    metrics["eye_ratio_left"] = f"{left_eye:.3f}"
    metrics["eye_ratio_right"] = f"{right_eye:.3f}"

    if min(left_eye, right_eye) < 0.07 and max(left_eye, right_eye) > 0.16:
        score -= 35
        signals.append("asymmetric_eye_visibility")

    eye_patches = []
    for outer, inner in ((33, 133), (263, 362)):
        cx = int((landmarks[outer].x + landmarks[inner].x) * width / 2)
        cy = int((landmarks[outer].y + landmarks[inner].y) * height / 2)
        rx, ry = max(2, int(0.10 * w)), max(2, int(0.08 * h))
        patch = gray[max(0, cy - ry):min(height, cy + ry), max(0, cx - rx):min(width, cx + rx)]
        if patch.size:
            eye_patches.append((float(patch.mean()), float(patch.std())))
    if len(eye_patches) == 2:
        brightness = [item[0] for item in eye_patches]
        texture = [item[1] for item in eye_patches]
        br_ratio = abs(brightness[0] - brightness[1]) / max(max(brightness), 1.0)
        tx_ratio = min(texture) / max(max(texture), 1.0)
        metrics["eye_brightness_ratio"] = f"{br_ratio:.3f}"
        metrics["eye_texture_ratio"] = f"{tx_ratio:.3f}"
        if br_ratio > 0.35:
            score -= 25
            signals.append("asymmetric_eye_brightness")
        if tx_ratio < 0.30:
            score -= 15
            signals.append("asymmetric_eye_detail")

    if x <= 1 or y <= 1 or x + w >= width - 1 or y + h >= height - 1:
        score -= 20
        signals.append("face_touches_image_edge")

    score = max(0.0, min(100.0, score))
    level = "none" if score >= 90 else "mild" if score >= 80 else "moderate" if score >= 70 else "heavy"
    return score, level, ";".join(signals), metrics


def percentiles(items: list[tuple[int, float]]) -> dict[int, float]:
    ordered = sorted(items, key=lambda item: item[1])
    result: dict[int, float] = {}
    count = len(ordered)
    start = 0
    while start < count:
        end = start + 1
        while end < count and ordered[end][1] == ordered[start][1]:
            end += 1
        value = 100.0 if count == 1 else 100.0 * ((start + end - 1) / 2) / (count - 1)
        for index, _ in ordered[start:end]:
            result[index] = value
        start = end
    return result


def category(row: dict[str, str]) -> str:
    if row["face_eligible"] == "true":
        return "ELIGIBLE"
    reasons = row["face_gate_reason"].split(";")
    if "analysis_error" in reasons:
        return "REVIEW_UNKNOWN"
    if "no_face" in reasons:
        return "REJECT_NO_FACE"
    if "multiple_faces" in reasons:
        return "REJECT_MULTIPLE_FACE"
    if "low_resolution_source" in reasons:
        return "REJECT_LOW_RES"
    if "beauty_filter_detected" in reasons or "plastic_skin" in reasons:
        return "REJECT_BEAUTY_FILTER"
    if "low_visibility" in reasons or "hair_covered_face" in reasons or "eye_occluded" in reasons or "one_eye_occluded" in reasons or "face_underexposed" in reasons or "face_backlit_underexposed" in reasons:
        return "REJECT_OCCLUSION"
    if "face_blurry" in reasons or "global_blurry" in reasons:
        return "REJECT_BLUR"
    if "face_too_small" in reasons:
        return "REJECT_SMALL_FACE"
    return "REVIEW_UNKNOWN"


def copy_image(source: Path, destination: Path, overwrite: bool = False) -> None:
    if destination.exists() and not overwrite:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def save_crop_image(crop: np.ndarray, destination: Path, overwrite: bool = False) -> None:
    if destination.exists() and not overwrite:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    success, encoded = cv2.imencode(".png", crop)
    if not success:
        raise ValueError("could not encode face crop")
    with destination.open("wb") as output:
        output.write(encoded.tobytes())


def write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", dir=path.parent,
                                         prefix=".dataset_report_facegate_", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
        return path
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def summary_stats(rows: list[dict[str, str]], column: str) -> str:
    values = [float(row[column]) for row in rows if row.get(column)]
    return f"{min(values):.2f} / {median(values):.2f} / {max(values):.2f}" if values else "n/a"


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    config = load_for_cli()
    settings = get_section(config, 'step3_face_gate')
    configure_constants(globals(), config, 'step3_face_gate', ['FACE_CROP_MARGIN', 'FACE_CORE_SCALE', 'MIN_FACE_VISIBILITY_SCORE', 'MIN_FACE_SHARPNESS_PERCENTILE', 'MIN_GLOBAL_LAPLACIAN', 'MIN_FACE_LAPLACIAN', 'SHOT_CLOSE_UP_THRESHOLD', 'SHOT_FULL_BODY_THRESHOLD', 'MIN_SOURCE_SHORT_EDGE_FULLBODY', 'MIN_FACE_DIM_CLOSE_UP', 'MIN_FACE_DIM_UPPER_BODY', 'MIN_FACE_DIM_FULL_BODY', 'MIN_EYE_SHARPNESS', 'MAX_FACE_CENTRAL_GRADIENT', 'MIN_SINGLE_EYE_FEATURE_RATIO', 'MIN_AVG_EYE_FEATURE_RATIO', 'MAX_EYE_ASYMMETRY_RATIO', 'MIN_FACE_BRIGHTNESS', 'MIN_FACE_TO_GLOBAL_RATIO', 'MIN_SKIN_TEXTURE_CLOSEUP', 'MIN_SKIN_TEXTURE_UPPER_BODY', 'MAX_PLASTICITY_RATIO', 'LAPLACIAN_WEIGHT', 'TENENGRAD_WEIGHT', 'DETECTION_CONFIDENCE', 'MAX_FACES'])
    # Resolve default paths supporting both template structure and flat structure
    if (project / "output" / "reports" / "step2_dataset_report.csv").is_file():
        default_report = project / "output" / "reports" / "step2_dataset_report.csv"
    elif (project / "reports" / "step2_dataset_report.csv").is_file():
        default_report = project / "reports" / "step2_dataset_report.csv"
    elif (project / "output" / "reports" / "dataset_report.csv").is_file():
        default_report = project / "output" / "reports" / "dataset_report.csv"
    else:
        default_report = (project / "output" / "reports" / "step2_dataset_report.csv"
                          if (project / "output").exists() else project / "reports" / "step2_dataset_report.csv")

    if (project / "work" / "frames_raw").exists():
        default_images = project / "work" / "frames_raw"
    elif (project / "frames_raw").exists():
        default_images = project / "frames_raw"
    else:
        default_images = project / "work" / "frames_raw"

    default_output = (project / "output" / "reports" / "step3_dataset_report.csv"
                      if (project / "output").exists() else project / "reports" / "step3_dataset_report.csv")
    default_review = (project / "work" / "facegate_review"
                      if (project / "work").exists() else project / "facegate_review")
    default_crops = (project / "work" / "facegate_face_crops"
                     if (project / "work").exists() else project / "facegate_face_crops")

    parser = argparse.ArgumentParser(description="NEW STEP 3 face quality gate.")
    parser.add_argument("--report", type=Path, default=default_report)
    parser.add_argument("--images", type=Path, default=default_images)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--review", type=Path, default=default_review)
    parser.add_argument("--crops", type=Path, default=default_crops)
    parser.add_argument("--limit", type=int, default=None, help="Limit number of images to process (useful for verification)")
    parser.add_argument("--min-global-laplacian", type=float, default=MIN_GLOBAL_LAPLACIAN, help="Minimum global laplacian score (drops severe whole-image motion blur)")
    parser.add_argument("--min-face-laplacian", type=float, default=MIN_FACE_LAPLACIAN, help="Minimum face core laplacian score (drops blurry faces)")
    parser.add_argument("--min-source-short-edge-fullbody", type=int, default=MIN_SOURCE_SHORT_EDGE_FULLBODY,
                        help="Minimum source image short edge for FULL_BODY shots (default: 720)")
    parser.add_argument("--min-face-dim-close-up", type=int, default=MIN_FACE_DIM_CLOSE_UP,
                        help="Minimum face width/height in pixels for CLOSE_UP (default: 140)")
    parser.add_argument("--min-face-dim-upper-body", type=int, default=MIN_FACE_DIM_UPPER_BODY,
                        help="Minimum face width/height in pixels for UPPER_BODY (default: 110)")
    parser.add_argument("--min-face-dim-full-body", type=int, default=MIN_FACE_DIM_FULL_BODY,
                        help="Minimum face width/height in pixels for FULL_BODY (default: 80)")
    parser.add_argument("--min-eye-sharpness", type=float, default=MIN_EYE_SHARPNESS,
                        help="Minimum normalized Tenengrad on eye patches (default: 1.60)")
    parser.add_argument("--min-skin-texture-close-up", type=float, default=MIN_SKIN_TEXTURE_CLOSEUP,
                        help="Minimum normalized cheek skin texture for CLOSE_UP (default: 0.050)")
    parser.add_argument("--min-skin-texture-upper-body", type=float, default=MIN_SKIN_TEXTURE_UPPER_BODY,
                        help="Minimum normalized cheek skin texture for UPPER_BODY (default: 0.035)")
    parser.add_argument("--max-plasticity-ratio", type=float, default=MAX_PLASTICITY_RATIO,
                        help="Maximum eye/skin ratio before rejecting as beauty filter (default: 45.0)")
    parser.add_argument("--skip-beauty-filter", action="store_true",
                        help="Skip rejection for beauty filters/plastic skin")
    parser.add_argument("--copy-review", action="store_true", help="Copy generation-scoped review images and crops; CSV remains authoritative")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing review and crop files")
    parser.add_argument("--config", type=Path, help="Alternate YAML config (relative to project root)")
    configure_parser(parser, config, 'step3_face_gate', aliases={}, paths={'images': 'raw_frames_dir', 'review': 'facegate_review_dir', 'crops': 'facegate_crops_dir'})
    args = parser.parse_args()
    report, root = args.report.resolve(), args.images.resolve()
    output, review, crops = args.output.resolve(), args.review.resolve(), args.crops.resolve()
    if not report.is_file() or not root.is_dir():
        parser.error("STEP 2 CSV or image source folder is missing")
    if output == report:
        parser.error("Output CSV must differ from STEP 2 CSV")
    if any(folder == root or folder.is_relative_to(root) for folder in (review, crops)):
        parser.error("Review folders must be outside the source image folder")
    input_bytes = report.read_bytes()
    loaded_sha = hashlib.sha256(input_bytes).hexdigest()
    with io.StringIO(input_bytes.decode("utf-8-sig"), newline="") as input_file:
        reader = csv.DictReader(input_file)
        columns = reader.fieldnames or []
        if "filename" not in columns:
            parser.error("STEP 2 CSV needs a filename column")
        rows = list(reader)

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if not mp or not hasattr(mp, "solutions"):
        parser.error("MediaPipe solutions required; install requirements-step3.txt into .step3_packages")
    manifests = resolve_project_path(get_section(config, 'paths').get('manifests_dir', 'work/manifests'))
    expected, generation, source_sha = validate_input(report, root, manifests)
    print(f"STEP3 formal video input: {generation['frame_count']} frames. "
          "Supplemental stills, when recorded by STEP2, are validated separately; "
          "their face diagnostics use 03_revision_a_diagnostics.bat.", flush=True)
    if set(columns) & (set(NEW_COLUMNS) | set(DIAGNOSTIC_COLUMNS)):
        parser.error("Input already contains STEP3 columns")
    if loaded_sha != source_sha:
        raise ValueError("STEP2 changed during input loading")
    original_rows = [dict(row) for row in rows]
    output = safe_output(output, args.limit, args.output.resolve())
    if args.limit is not None and args.limit > 0:
        print(f"Limiting execution to first {args.limit} images for verification.", flush=True)
        rows = rows[:args.limit]

    with manifest_lock(manifests / ".video_manifest.lock"):
        _, locked_generation, locked_sha = validate_input(report, root, manifests)
        if locked_generation != generation or locked_sha != source_sha:
            raise ValueError("Generation changed before inference")
        rows, paths = analyze_rows(rows, root, args)
        if any(original_rows[i].get(k) != r.get(k) for i,r in enumerate(rows) for k in columns):
            raise ValueError("STEP2 values changed")
        _, generation_after, source_after = validate_input(report, root, manifests)
        if generation_after != generation or source_after != source_sha:
            raise ValueError("Generation changed during inference")
        failed = any(r["face_gate_status"] == "error" for r in rows)
        artifacts = build_artifacts(rows, columns, generation, source_sha, vars(args), partial=args.limit is not None)
        publish(output, artifacts, failed=failed, partial=args.limit is not None)
        if args.copy_review and not failed:
            materialize_review(rows, paths, review, crops, hashlib.sha256(artifacts["dataset.csv"]).hexdigest()[:16], args.overwrite)
        print(f"STEP3: {len(rows)} rows, eligible={sum(r['face_eligible']=='true' for r in rows)}, errors={sum(r['face_gate_status']=='error' for r in rows)}; {output}")
        return 1 if failed else 0


def materialize_review(rows, paths, review, crops, report_key, overwrite=False):
    """Optional copies grouped by report hash; never move/delete source pixels."""
    for index,row in enumerate(rows):
        if index not in paths: continue
        source,relative=paths[index]
        try:
            copy_image(source, review / report_key / category(row) / relative, overwrite)
            if row.get("face_bbox_width") and row.get("face_bbox_height"):
                image=cv2.imdecode(np.fromfile(source,dtype=np.uint8),cv2.IMREAD_COLOR)
                if image is None:raise ValueError("Review image decode failed")
                box=tuple(int(row[k]) for k in ("face_bbox_x","face_bbox_y","face_bbox_width","face_bbox_height"))
                save_crop_image(crop_with_margin(image,box),crops/report_key/("ELIGIBLE" if row["face_eligible"]=="true" else "REJECTED")/relative,overwrite)
        except (OSError,ValueError) as exc:
            print(f"WARNING: Optional review copy failed: {relative}: {exc}",flush=True)


def analyze_rows(rows, root, args):
    paths: dict[int, tuple[Path, Path]] = {}
    metrics: list[int] = []
    with mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=DETECTION_CONFIDENCE) as detector, \
         mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=MAX_FACES,
                                         refine_landmarks=False, min_detection_confidence=DETECTION_CONFIDENCE) as mesh:
        for index, row in enumerate(rows):
            row.update({column: "" for column in NEW_COLUMNS})
            row["step3_step_name"] = "STEP3_FACE_GATE"
            row["face_eligible"] = "false"
            row.update({k: "" for k in DIAGNOSTIC_COLUMNS})
            row["anatomical_metric_status"] = "not_applicable_no_face"
            row["primary_face_selection_method"] = "largest_clipped_bbox_area_first_detection_tie"
            name = row.get("filename") or ""
            print(f"[{index + 1}/{len(rows)}] {name}", flush=True)
            try:
                source, relative = image_path(root, name)
                paths[index] = source, relative
                image = cv2.imdecode(np.fromfile(source, dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError("OpenCV could not decode the image")
                height, width = image.shape[:2]
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                detections = detector.process(rgb).detections or []
                count = len(detections)
                row.update({"face_detected": str(bool(count)).lower(), "face_count": str(count),
                            "multiple_faces": str(count > 1).lower()})
                if not count:
                    row["face_gate_status"] = "ok"
                    continue
                boxes = [face_box(detection, width, height) for detection in detections]
                primary = max(range(count), key=lambda i: boxes[i][2] * boxes[i][3])
                box = boxes[primary]
                x, y, box_width, box_height = box
                min_dim = min(box_width, box_height)
                area_ratio = box_width * box_height / (width * height)
                shot_type = classify_shot_type(area_ratio)
                row["provisional_face_scale_class"] = shot_type
                source_short = min(width, height)

                row.update({
                    "shot_type": shot_type,
                    "source_short_edge": str(source_short),
                    "face_bbox_x": str(x), "face_bbox_y": str(y),
                    "face_bbox_width": str(box_width), "face_bbox_height": str(box_height),
                    "face_min_dimension": str(min_dim),
                    "face_area_ratio": f"{area_ratio:.5f}"
                })

                # Process FaceMesh and extract anatomical patches strictly (eyes, mouth)
                mesh_result = mesh.process(rgb)
                landmarks = matching_landmarks(mesh_result, box, width, height)
                row.update(geometry_diagnostics(landmarks, width, height))
                row["anatomical_metric_status"] = "measured" if landmarks else "missing_landmarks"
                row["beauty_filter_applicability"] = "not_applicable_full_body" if shot_type == "FULL_BODY" else "measured" if landmarks else "missing_landmarks"

                # Measure central face hair occlusion gradient & eye biological presence
                face_grad = central_face_gradient(image, landmarks, width, height)
                l_pres, r_pres, eye_valid = eye_presence_metrics(image, landmarks, width, height)
                row["face_central_gradient"] = f"{face_grad:.1f}" if landmarks else ""
                row["left_eye_presence_ratio"] = f"{l_pres:.3f}" if landmarks else ""
                row["right_eye_presence_ratio"] = f"{r_pres:.3f}" if landmarks else ""
                row["eye_presence_valid"] = str(eye_valid).lower() if landmarks else ""
                if landmarks and not eye_valid:
                    row["anatomical_metric_status"] = "eye_sharpness_disabled_by_existing_presence_gate"

                eye_s, mouth_s = anatomical_sharpness(image, landmarks, box, eye_valid=eye_valid)
                row["eye_sharpness"] = f"{eye_s:.3f}" if landmarks else ""
                row["mouth_sharpness"] = f"{mouth_s:.3f}" if landmarks else ""

                skin_tex, plasticity, is_filter = cheek_skin_texture_metrics(
                    image, landmarks, box, eye_s, shot_type,
                    args.min_skin_texture_close_up,
                    args.min_skin_texture_upper_body,
                    args.max_plasticity_ratio,
                )
                row["skin_texture_score"] = f"{skin_tex:.3f}" if landmarks else ""
                row["plasticity_ratio"] = f"{plasticity:.1f}" if landmarks else ""
                row["beauty_filter_detected"] = str(is_filter).lower() if landmarks else ""

                # Face crop brightness & backlit ratio
                face_crop_img = crop_with_margin(image, box)
                face_gray = cv2.cvtColor(face_crop_img, cv2.COLOR_BGR2GRAY)
                face_br = float(face_gray.mean())
                global_br = float(row["brightness_mean"]) if row.get("brightness_mean") else float(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).mean())
                backlit_ratio = face_br / max(global_br, 1.0)
                row["face_brightness_mean"] = f"{face_br:.1f}"
                row["face_to_global_brightness_ratio"] = f"{backlit_ratio:.3f}"

                # Core face crop sharpness (auxiliary feature)
                core_crop = crop_face_core(image, box)
                lap, ten = sharpness(core_crop)
                row["face_laplacian_score"] = f"{lap:.3f}"
                row["face_tenengrad_score"] = f"{ten:.3f}"
                if count == 1:
                    metrics.append(index)

                visible, level, signals, vis_metrics = visibility(detections[primary], landmarks, box, image)
                row.update({
                    "face_visibility_score": f"{visible:.2f}",
                    "occlusion_detected": str(level in ("moderate", "heavy") or level == "unknown").lower(),
                    "occlusion_level": level, "face_visibility_signals": signals,
                    "face_gate_status": "ok"
                })
                row.update(vis_metrics)
            except Exception as exc:
                row["face_gate_status"] = "error"
                row["face_gate_error"] = str(exc)
                row["face_gate_error_category"] = type(exc).__name__
                print(f"WARNING: Face analysis failed: {name}: {exc}", flush=True)

    lap_pct = percentiles([(i, float(rows[i]["face_laplacian_score"])) for i in metrics if rows[i]["face_gate_status"] == "ok"])
    ten_pct = percentiles([(i, float(rows[i]["face_tenengrad_score"])) for i in metrics if rows[i]["face_gate_status"] == "ok"])
    for index, row in enumerate(rows):
        if index in lap_pct:
            lap, ten = lap_pct[index], ten_pct[index]
            row["face_laplacian_percentile"] = f"{lap:.2f}"
            row["face_tenengrad_percentile"] = f"{ten:.2f}"
            sharp = (LAPLACIAN_WEIGHT * lap + TENENGRAD_WEIGHT * ten) / (LAPLACIAN_WEIGHT + TENENGRAD_WEIGHT)
            row["face_sharpness_score"] = f"{sharp:.2f}"
        reasons: list[str] = []
        if row["face_gate_status"] == "error":
            row.update(face_gate_reason="analysis_error", face_eligible="false", face_gate_category="REVIEW_UNKNOWN")
            continue
        if row["face_gate_status"] != "error" and row["face_detected"] != "true":
            reasons.append("no_face")
        elif row["face_count"] != "1":
            reasons.append("multiple_faces")

        # 1. Global blur pre-filter (drop severe whole-image motion blur)
        global_lap = float(row["laplacian_score"]) if row.get("laplacian_score") else 0.0
        if global_lap < args.min_global_laplacian:
            reasons.append("global_blurry")

        # 2. Shot type & Dynamic resolution gate
        shot = row.get("shot_type") or ""
        src_short = int(row["source_short_edge"]) if row.get("source_short_edge") else 0
        min_dim = int(row["face_min_dimension"]) if row.get("face_min_dimension") else 0

        if row["face_detected"] == "true":
            if shot == "FULL_BODY":
                if src_short < args.min_source_short_edge_fullbody:
                    reasons.append("low_resolution_source")
                if min_dim < args.min_face_dim_full_body:
                    reasons.append("face_too_small")
            elif shot == "UPPER_BODY":
                if min_dim < args.min_face_dim_upper_body:
                    reasons.append("face_too_small")
            else:  # CLOSE_UP
                if min_dim < args.min_face_dim_close_up:
                    reasons.append("face_too_small")

        # 3. Face visibility & FaceMesh confirmation (Hard Gate)
        if row["face_detected"] == "true" and (row.get("facemesh_detected") != "true" or not row["face_visibility_score"] or
                                                float(row["face_visibility_score"]) < MIN_FACE_VISIBILITY_SCORE):
            reasons.append("low_visibility")

        # 3.5 Central face hair occlusion & Eye biological presence (Hard Gate)
        if row["face_detected"] == "true":
            face_g = float(row["face_central_gradient"]) if row.get("face_central_gradient") else 0.0
            if face_g > MAX_FACE_CENTRAL_GRADIENT:
                reasons.append("hair_covered_face")
            if shot != "FULL_BODY" and row.get("eye_presence_valid") != "true":
                reasons.append("one_eye_occluded")

        # 3.8 Face underexposure & Backlit shadow check (Hard Gate)
        if row["face_detected"] == "true":
            face_br = float(row["face_brightness_mean"]) if row.get("face_brightness_mean") else 0.0
            backlit_r = float(row["face_to_global_brightness_ratio"]) if row.get("face_to_global_brightness_ratio") else 1.0
            if face_br < MIN_FACE_BRIGHTNESS:
                reasons.append("face_underexposed")
            elif face_br < 105.0 and backlit_r < MIN_FACE_TO_GLOBAL_RATIO:
                reasons.append("face_backlit_underexposed")

        # 3.9 Beauty filter & plastic skin smoothing check (Hard Gate)
        if row["face_detected"] == "true" and not args.skip_beauty_filter:
            if row.get("beauty_filter_detected") == "true":
                reasons.append("beauty_filter_detected")

        # 4. Anatomical eye sharpness & Face blur
        eye_s = float(row["eye_sharpness"]) if row.get("eye_sharpness") else 0.0
        face_lap = float(row["face_laplacian_score"]) if row.get("face_laplacian_score") else 0.0
        if row["face_detected"] == "true":
            # For upper-body and close-up, eyes must have sharp gradients
            if shot != "FULL_BODY" and eye_s < args.min_eye_sharpness:
                reasons.append("face_blurry")
            elif face_lap < args.min_face_laplacian:
                reasons.append("face_blurry")

        row["face_gate_reason"] = ";".join(reasons) if reasons else "eligible"
        row["face_eligible"] = str(not reasons).lower()
        row["face_gate_category"] = category(row)

    return rows, paths


if __name__ == "__main__":
    raise SystemExit(main())
