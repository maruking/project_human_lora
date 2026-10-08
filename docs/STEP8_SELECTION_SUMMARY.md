# STEP8 Human Final Selection

Total selected: **40** / 35–45

Status: **VALID**

Human selections only. NOT_SELECTED does not mean bad image. Pose/scale/vertical guidance is soft; quality takes priority. Identity remains diagnostic.

| Pose | recommended_min | recommended_max | actual_accept_count |
|---|---:|---:|---:|
| FRONTAL | 12 | 17 | 20 |
| THREE_QUARTER_LEFT | 7 | 10 | 7 |
| THREE_QUARTER_RIGHT | 7 | 10 | 9 |
| PROFILE_LEFT | 1 | 3 | 3 |
| PROFILE_RIGHT | 1 | 3 | 1 |
| NOT_EVALUABLE | 0 | 2 | 0 |

vertical_pose

| label | count |
|---|---:|
| LEVEL | 37 |
| LOOKING_UP | 2 |
| LOOKING_DOWN | 1 |
| NOT_EVALUABLE | 0 |

face_scale_bin

| label | count |
|---|---:|
| CLOSE_UP | 12 |
| UPPER_BODY | 18 |
| FULL_BODY | 10 |
| NOT_EVALUABLE | 0 |

identity_state

| label | count |
|---|---:|
| IDENTITY_PASS | 35 |
| IDENTITY_REVIEW | 1 |
| IDENTITY_REJECT | 4 |
| IDENTITY_NOT_EVALUABLE | 0 |

Sources / quality / warnings

```json
{
  "source_summary": {
    "video_count": 7,
    "supplemental_still_count": 31,
    "max_selected_from_one_video": 2,
    "video_distribution": {
      "Sasha_v23": 2,
      "Sasha_v05": 1,
      "Sasha_v22": 2,
      "Sasha_v41": 1,
      "Sasha_v08": 1,
      "Sasha_v16": 1,
      "Sasha_v11": 1
    }
  },
  "quality": {
    "best_min": 60.80408873541634,
    "best_median": 86.1354070198023,
    "best_max": 94.6240253411306,
    "global_rank_min": 3,
    "global_rank_max": 125
  },
  "guidance_warnings": [
    {
      "reason": "POSE_GUIDANCE_WARNING",
      "label": "FRONTAL",
      "actual": 20,
      "recommended": [
        12,
        17
      ]
    }
  ]
}
```

Ignored exact duplicate VIEW copies (not additional accepts): 2

STEP9 input is validated step8_human_selection.csv with STEP8_ACCEPT only, and requires VALID total count. No STEP9 processing ran.
