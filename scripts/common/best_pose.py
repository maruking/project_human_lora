"""Pose context only: existing STEP4 solvePnP formula, no bucket/quota logic.
Source: classify_face_pose.py; model/indices/kernel retained verbatim.
"""
import cv2
import numpy as np

MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),          # Nose tip (landmark 1)
    (0.0, -330.0, -65.0),     # Chin (landmark 152)
    (-225.0, 170.0, -135.0),  # Left eye left corner (landmark 33)
    (225.0, 170.0, -135.0),   # Right eye right corner (landmark 263)
    (-150.0, -150.0, -125.0), # Left Mouth corner (landmark 61)
    (150.0, -150.0, -125.0),  # Right mouth corner (landmark 291)
], dtype=np.float64)

KEY_LANDMARK_INDICES = [1, 152, 33, 263, 61, 291]

def estimate_head_pose(landmarks: list, width: int, height: int) -> tuple[float, float, float] | None:
    image_points = np.array([
        (landmarks[idx].x * width, landmarks[idx].y * height)
        for idx in KEY_LANDMARK_INDICES
    ], dtype=np.float64)

    focal_length = width
    center = (width / 2.0, height / 2.0)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1],
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    success, rotation_vector, translation_vector = cv2.solvePnP(
        MODEL_POINTS_3D,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )

    if not success:
        return None

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    proj_matrix = np.hstack((rotation_matrix, translation_vector))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)

    pitch = float(euler_angles[0, 0])
    yaw = float(euler_angles[1, 0])
    roll = float(euler_angles[2, 0])

    if pitch > 90.0:
        pitch = 180.0 - pitch
    elif pitch < -90.0:
        pitch = -180.0 - pitch

    return yaw, pitch, roll
