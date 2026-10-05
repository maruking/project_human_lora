# STEP4 Pose / Composition Summary

Version: step4_pose_composition_v2

Full input rows: 1951; ranking eligible: 1880.

These are descriptive measurements, not quality, quotas or selection.
RIGHT/LEFT follows signed repository yaw; anatomical/mirror-independent direction is not asserted.
face_scale_bin uses face area, not verified torso/leg visibility. shot_type is its alias.
Missing values stay missing. Position and roll bins are NOT_CLASSIFIED.
Distributions below include all ranking-eligible rows, including missing measurements.

## statuses

| State | Count |
| --- | ---: |
| MEASURED | 1698 |
| NOT_APPLICABLE_STEP3_FATAL | 71 |
| NOT_EVALUABLE | 182 |

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
| FRONTAL | 1153 |
| THREE_QUARTER_LEFT | 274 |
| THREE_QUARTER_RIGHT | 245 |
| PROFILE_LEFT | 15 |
| PROFILE_RIGHT | 11 |
| NOT_EVALUABLE | 182 |

## vertical_pose

| State | Count |
| --- | ---: |
| LOOKING_UP | 488 |
| LEVEL | 1161 |
| LOOKING_DOWN | 49 |
| NOT_EVALUABLE | 182 |

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
| FRONTAL | CLOSE_UP | 231 |
| FRONTAL | FULL_BODY | 363 |
| FRONTAL | UPPER_BODY | 559 |
| NOT_EVALUABLE | FULL_BODY | 169 |
| NOT_EVALUABLE | UPPER_BODY | 13 |
| PROFILE_LEFT | CLOSE_UP | 1 |
| PROFILE_LEFT | FULL_BODY | 7 |
| PROFILE_LEFT | UPPER_BODY | 7 |
| PROFILE_RIGHT | CLOSE_UP | 1 |
| PROFILE_RIGHT | FULL_BODY | 5 |
| PROFILE_RIGHT | UPPER_BODY | 5 |
| THREE_QUARTER_LEFT | CLOSE_UP | 44 |
| THREE_QUARTER_LEFT | FULL_BODY | 124 |
| THREE_QUARTER_LEFT | UPPER_BODY | 106 |
| THREE_QUARTER_RIGHT | CLOSE_UP | 52 |
| THREE_QUARTER_RIGHT | FULL_BODY | 99 |
| THREE_QUARTER_RIGHT | UPPER_BODY | 94 |

## pose_bin_x_input_kind

| Row | Column | Count |
| --- | --- | ---: |
| FRONTAL | formal_video | 1123 |
| FRONTAL | supplemental_still | 30 |
| NOT_EVALUABLE | formal_video | 179 |
| NOT_EVALUABLE | supplemental_still | 3 |
| PROFILE_LEFT | formal_video | 13 |
| PROFILE_LEFT | supplemental_still | 2 |
| PROFILE_RIGHT | formal_video | 10 |
| PROFILE_RIGHT | supplemental_still | 1 |
| THREE_QUARTER_LEFT | formal_video | 265 |
| THREE_QUARTER_LEFT | supplemental_still | 9 |
| THREE_QUARTER_RIGHT | formal_video | 233 |
| THREE_QUARTER_RIGHT | supplemental_still | 12 |

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
