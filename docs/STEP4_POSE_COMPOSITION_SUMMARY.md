# STEP4 Pose / Composition Summary

Version: step4_pose_composition_v3

Full input rows: 1951; ranking eligible: 1880.

These are descriptive measurements, not quality, quotas or selection.
RIGHT/LEFT follows signed repository yaw; anatomical/mirror-independent direction is not asserted.
face_scale_bin uses face area, not verified torso/leg visibility. shot_type is its alias.
Missing values stay missing. Position and roll bins are NOT_CLASSIFIED.
Distributions below include all ranking-eligible rows, including missing measurements.

## statuses

| State | Count |
| --- | ---: |
| MEASURED | 1872 |
| NOT_APPLICABLE_STEP3_FATAL | 71 |
| NOT_EVALUABLE | 8 |

## input_kind_all_rows

| State | Count |
| --- | ---: |
| formal_video | 1893 |
| supplemental_still | 58 |

## input_kind

| State | Count |
| --- | ---: |
| formal_video | 1823 |
| supplemental_still | 57 |

## pose_bin

| State | Count |
| --- | ---: |
| FRONTAL | 1464 |
| THREE_QUARTER_LEFT | 141 |
| THREE_QUARTER_RIGHT | 224 |
| PROFILE_LEFT | 26 |
| PROFILE_RIGHT | 17 |
| NOT_EVALUABLE | 8 |

## vertical_pose

| State | Count |
| --- | ---: |
| LOOKING_UP | 37 |
| LEVEL | 1766 |
| LOOKING_DOWN | 69 |
| NOT_EVALUABLE | 8 |

## face_scale_bin

| State | Count |
| --- | ---: |
| CLOSE_UP | 329 |
| UPPER_BODY | 784 |
| FULL_BODY | 767 |
| NOT_EVALUABLE | 0 |

## pose_bin_x_face_scale_bin

| Row | Column | Count |
| --- | --- | ---: |
| FRONTAL | CLOSE_UP | 230 |
| FRONTAL | FULL_BODY | 625 |
| FRONTAL | UPPER_BODY | 609 |
| NOT_EVALUABLE | CLOSE_UP | 1 |
| NOT_EVALUABLE | FULL_BODY | 5 |
| NOT_EVALUABLE | UPPER_BODY | 2 |
| PROFILE_LEFT | CLOSE_UP | 2 |
| PROFILE_LEFT | FULL_BODY | 17 |
| PROFILE_LEFT | UPPER_BODY | 7 |
| PROFILE_RIGHT | FULL_BODY | 6 |
| PROFILE_RIGHT | UPPER_BODY | 11 |
| THREE_QUARTER_LEFT | CLOSE_UP | 32 |
| THREE_QUARTER_LEFT | FULL_BODY | 40 |
| THREE_QUARTER_LEFT | UPPER_BODY | 69 |
| THREE_QUARTER_RIGHT | CLOSE_UP | 64 |
| THREE_QUARTER_RIGHT | FULL_BODY | 74 |
| THREE_QUARTER_RIGHT | UPPER_BODY | 86 |

## pose_bin_x_input_kind

| Row | Column | Count |
| --- | --- | ---: |
| FRONTAL | formal_video | 1434 |
| FRONTAL | supplemental_still | 30 |
| NOT_EVALUABLE | formal_video | 7 |
| NOT_EVALUABLE | supplemental_still | 1 |
| PROFILE_LEFT | formal_video | 24 |
| PROFILE_LEFT | supplemental_still | 2 |
| PROFILE_RIGHT | formal_video | 14 |
| PROFILE_RIGHT | supplemental_still | 3 |
| THREE_QUARTER_LEFT | formal_video | 129 |
| THREE_QUARTER_LEFT | supplemental_still | 12 |
| THREE_QUARTER_RIGHT | formal_video | 215 |
| THREE_QUARTER_RIGHT | supplemental_still | 9 |

## face_scale_bin_x_input_kind

| Row | Column | Count |
| --- | --- | ---: |
| CLOSE_UP | formal_video | 315 |
| CLOSE_UP | supplemental_still | 14 |
| FULL_BODY | formal_video | 750 |
| FULL_BODY | supplemental_still | 17 |
| UPPER_BODY | formal_video | 758 |
| UPPER_BODY | supplemental_still | 26 |

Human Review dependency: NONE. Reject/quota introduced: NO.
STEP5+ is not executed. Inspect distribution before designing STEP5.

Estimator: installed buffalo_l 68-point 3D; raw signed degrees, comparison-approved.
STEP3 angles preserved in step3_yaw/pitch/roll/pose_status.
STEP5+ remains unchanged and v2-only: do not run downstream until explicitly adapted for v3.
