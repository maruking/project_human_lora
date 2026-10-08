# STEP5 Deduplication v2 Summary

Clusters annotate redundancy, not image quality or final training selection.

Pose/scale before includes every ranking-eligible row; after is UNIQUE + REPRESENTATIVE.
POSE_RETENTION_WARNING highlights any count reduction without a magnitude cutoff.

See [pose gallery](STEP5_REPRESENTATIVE_POSE_REVIEW.html) and [cluster review](STEP5_DEDUP_REVIEW.html).

```json
{
  "step5_version": "step5_dedup_v2",
  "publication_status": "COMPLETE",
  "total_rows": 1951,
  "ranking_eligible_count": 1880,
  "fatal_not_applicable_count": 71,
  "total_analyzed": 1880,
  "roles": {
    "REPRESENTATIVE": 186,
    "UNIQUE": 580,
    "DUPLICATE_MEMBER": 1114,
    "NOT_APPLICABLE_STEP3_FATAL": 71
  },
  "total_clusters": 766,
  "unique_clusters": 580,
  "multi_member_clusters": 186,
  "exact_duplicate_count": 0,
  "near_duplicate_count": 1300,
  "duplicate_member_ratio": 0.5925531914893617,
  "cluster_sizes": {
    "size_1": 580,
    "size_2": 75,
    "size_3_5": 46,
    "size_6_plus": 65,
    "largest_cluster": 34
  },
  "evidence_edges": {
    "SUPPLEMENTAL_STILL_NEAR": 1,
    "VIDEO_TEMPORAL_NEAR": 1802,
    "VIDEO_STRONG_SIMILARITY": 941
  },
  "exact_sha_clusters": 0,
  "chain_warning_clusters": 80,
  "before": {
    "pose": {
      "FRONTAL": 1464,
      "THREE_QUARTER_LEFT": 141,
      "THREE_QUARTER_RIGHT": 224,
      "PROFILE_LEFT": 26,
      "PROFILE_RIGHT": 17,
      "NOT_EVALUABLE": 8
    },
    "face_scale": {
      "CLOSE_UP": 329,
      "UPPER_BODY": 784,
      "FULL_BODY": 767,
      "NOT_EVALUABLE": 0
    }
  },
  "after": {
    "pose": {
      "FRONTAL": 468,
      "THREE_QUARTER_LEFT": 108,
      "THREE_QUARTER_RIGHT": 140,
      "PROFILE_LEFT": 25,
      "PROFILE_RIGHT": 17,
      "NOT_EVALUABLE": 8
    },
    "face_scale": {
      "CLOSE_UP": 163,
      "UPPER_BODY": 347,
      "FULL_BODY": 256,
      "NOT_EVALUABLE": 0
    }
  },
  "pose_retention": {
    "FRONTAL": {
      "before_count": 1464,
      "after_count": 468,
      "retention_ratio": 0.319672131147541,
      "status": "POSE_RETENTION_WARNING",
      "rare_pose_context": false
    },
    "THREE_QUARTER_LEFT": {
      "before_count": 141,
      "after_count": 108,
      "retention_ratio": 0.7659574468085106,
      "status": "POSE_RETENTION_WARNING",
      "rare_pose_context": false
    },
    "THREE_QUARTER_RIGHT": {
      "before_count": 224,
      "after_count": 140,
      "retention_ratio": 0.625,
      "status": "POSE_RETENTION_WARNING",
      "rare_pose_context": false
    },
    "PROFILE_LEFT": {
      "before_count": 26,
      "after_count": 25,
      "retention_ratio": 0.9615384615384616,
      "status": "POSE_RETENTION_WARNING",
      "rare_pose_context": true
    },
    "PROFILE_RIGHT": {
      "before_count": 17,
      "after_count": 17,
      "retention_ratio": 1.0,
      "status": "NO_REDUCTION",
      "rare_pose_context": true
    },
    "NOT_EVALUABLE": {
      "before_count": 8,
      "after_count": 8,
      "retention_ratio": 1.0,
      "status": "NO_REDUCTION",
      "rare_pose_context": false
    }
  },
  "sources": [
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v01",
      "eligible_members": 19,
      "resulting_clusters": 4,
      "duplicate_members": 15,
      "representative_unique_count": 4,
      "largest_cluster": 13,
      "best_step3_score": 41.38910663221478
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v03",
      "eligible_members": 105,
      "resulting_clusters": 66,
      "duplicate_members": 39,
      "representative_unique_count": 66,
      "largest_cluster": 29,
      "best_step3_score": 53.49203101088773
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v04",
      "eligible_members": 23,
      "resulting_clusters": 7,
      "duplicate_members": 16,
      "representative_unique_count": 7,
      "largest_cluster": 16,
      "best_step3_score": 50.456295111175045
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v05",
      "eligible_members": 32,
      "resulting_clusters": 14,
      "duplicate_members": 18,
      "representative_unique_count": 14,
      "largest_cluster": 12,
      "best_step3_score": 79.630833519236
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v06",
      "eligible_members": 17,
      "resulting_clusters": 15,
      "duplicate_members": 2,
      "representative_unique_count": 15,
      "largest_cluster": 3,
      "best_step3_score": 32.41430259111688
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v07",
      "eligible_members": 22,
      "resulting_clusters": 17,
      "duplicate_members": 5,
      "representative_unique_count": 17,
      "largest_cluster": 4,
      "best_step3_score": 48.97089663390877
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v08",
      "eligible_members": 15,
      "resulting_clusters": 14,
      "duplicate_members": 1,
      "representative_unique_count": 14,
      "largest_cluster": 2,
      "best_step3_score": 63.769343541698035
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v09",
      "eligible_members": 30,
      "resulting_clusters": 8,
      "duplicate_members": 22,
      "representative_unique_count": 8,
      "largest_cluster": 20,
      "best_step3_score": 53.54685203396035
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v10",
      "eligible_members": 26,
      "resulting_clusters": 17,
      "duplicate_members": 9,
      "representative_unique_count": 17,
      "largest_cluster": 8,
      "best_step3_score": 45.703609077652146
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v11",
      "eligible_members": 22,
      "resulting_clusters": 14,
      "duplicate_members": 8,
      "representative_unique_count": 14,
      "largest_cluster": 6,
      "best_step3_score": 60.842726417918925
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v12",
      "eligible_members": 24,
      "resulting_clusters": 6,
      "duplicate_members": 18,
      "representative_unique_count": 6,
      "largest_cluster": 17,
      "best_step3_score": 57.436726041471275
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v13",
      "eligible_members": 26,
      "resulting_clusters": 12,
      "duplicate_members": 14,
      "representative_unique_count": 12,
      "largest_cluster": 12,
      "best_step3_score": 40.928699914050966
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v14",
      "eligible_members": 29,
      "resulting_clusters": 12,
      "duplicate_members": 17,
      "representative_unique_count": 12,
      "largest_cluster": 12,
      "best_step3_score": 38.54280043001664
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v15",
      "eligible_members": 24,
      "resulting_clusters": 13,
      "duplicate_members": 11,
      "representative_unique_count": 13,
      "largest_cluster": 5,
      "best_step3_score": 51.138703141276935
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v16",
      "eligible_members": 30,
      "resulting_clusters": 13,
      "duplicate_members": 17,
      "representative_unique_count": 13,
      "largest_cluster": 16,
      "best_step3_score": 62.276622424525875
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v17",
      "eligible_members": 25,
      "resulting_clusters": 9,
      "duplicate_members": 16,
      "representative_unique_count": 9,
      "largest_cluster": 9,
      "best_step3_score": 45.460488599757056
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v19",
      "eligible_members": 30,
      "resulting_clusters": 14,
      "duplicate_members": 16,
      "representative_unique_count": 14,
      "largest_cluster": 13,
      "best_step3_score": 45.980302837811344
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v20",
      "eligible_members": 20,
      "resulting_clusters": 9,
      "duplicate_members": 11,
      "representative_unique_count": 9,
      "largest_cluster": 9,
      "best_step3_score": 29.06681315011883
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v21",
      "eligible_members": 24,
      "resulting_clusters": 6,
      "duplicate_members": 18,
      "representative_unique_count": 6,
      "largest_cluster": 16,
      "best_step3_score": 38.06357397733307
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v22",
      "eligible_members": 37,
      "resulting_clusters": 6,
      "duplicate_members": 31,
      "representative_unique_count": 6,
      "largest_cluster": 30,
      "best_step3_score": 67.93940427836182
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v23",
      "eligible_members": 20,
      "resulting_clusters": 13,
      "duplicate_members": 7,
      "representative_unique_count": 13,
      "largest_cluster": 7,
      "best_step3_score": 93.49110222038465
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v24",
      "eligible_members": 28,
      "resulting_clusters": 9,
      "duplicate_members": 19,
      "representative_unique_count": 9,
      "largest_cluster": 15,
      "best_step3_score": 60.46272583263042
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v25",
      "eligible_members": 28,
      "resulting_clusters": 6,
      "duplicate_members": 22,
      "representative_unique_count": 6,
      "largest_cluster": 23,
      "best_step3_score": 48.526092667872945
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v26",
      "eligible_members": 24,
      "resulting_clusters": 8,
      "duplicate_members": 16,
      "representative_unique_count": 8,
      "largest_cluster": 16,
      "best_step3_score": 51.67827485674388
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v27",
      "eligible_members": 26,
      "resulting_clusters": 19,
      "duplicate_members": 7,
      "representative_unique_count": 19,
      "largest_cluster": 3,
      "best_step3_score": 47.06875638105909
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v28",
      "eligible_members": 29,
      "resulting_clusters": 21,
      "duplicate_members": 8,
      "representative_unique_count": 21,
      "largest_cluster": 6,
      "best_step3_score": 33.943445657892035
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v29",
      "eligible_members": 22,
      "resulting_clusters": 5,
      "duplicate_members": 17,
      "representative_unique_count": 5,
      "largest_cluster": 11,
      "best_step3_score": 39.419861899671126
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v30",
      "eligible_members": 26,
      "resulting_clusters": 10,
      "duplicate_members": 16,
      "representative_unique_count": 10,
      "largest_cluster": 15,
      "best_step3_score": 53.56378108633143
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v31",
      "eligible_members": 29,
      "resulting_clusters": 15,
      "duplicate_members": 14,
      "representative_unique_count": 15,
      "largest_cluster": 9,
      "best_step3_score": 59.61455104244102
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v32",
      "eligible_members": 21,
      "resulting_clusters": 6,
      "duplicate_members": 15,
      "representative_unique_count": 6,
      "largest_cluster": 16,
      "best_step3_score": 54.4549496978678
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v33",
      "eligible_members": 33,
      "resulting_clusters": 9,
      "duplicate_members": 24,
      "representative_unique_count": 9,
      "largest_cluster": 18,
      "best_step3_score": 69.81331775542897
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v34",
      "eligible_members": 15,
      "resulting_clusters": 6,
      "duplicate_members": 9,
      "representative_unique_count": 6,
      "largest_cluster": 5,
      "best_step3_score": 68.44201126202647
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v35",
      "eligible_members": 30,
      "resulting_clusters": 16,
      "duplicate_members": 14,
      "representative_unique_count": 16,
      "largest_cluster": 7,
      "best_step3_score": 52.04754285769519
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v36",
      "eligible_members": 39,
      "resulting_clusters": 8,
      "duplicate_members": 31,
      "representative_unique_count": 8,
      "largest_cluster": 29,
      "best_step3_score": 36.41633799528882
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v37",
      "eligible_members": 18,
      "resulting_clusters": 4,
      "duplicate_members": 14,
      "representative_unique_count": 4,
      "largest_cluster": 15,
      "best_step3_score": 55.11505197545317
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v38",
      "eligible_members": 27,
      "resulting_clusters": 12,
      "duplicate_members": 15,
      "representative_unique_count": 12,
      "largest_cluster": 8,
      "best_step3_score": 38.01442393413006
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v39",
      "eligible_members": 34,
      "resulting_clusters": 11,
      "duplicate_members": 23,
      "representative_unique_count": 11,
      "largest_cluster": 20,
      "best_step3_score": 35.342717035577394
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v40",
      "eligible_members": 30,
      "resulting_clusters": 10,
      "duplicate_members": 20,
      "representative_unique_count": 10,
      "largest_cluster": 13,
      "best_step3_score": 39.08988510152941
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v41",
      "eligible_members": 19,
      "resulting_clusters": 7,
      "duplicate_members": 12,
      "representative_unique_count": 7,
      "largest_cluster": 8,
      "best_step3_score": 65.73900558954591
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v42",
      "eligible_members": 19,
      "resulting_clusters": 5,
      "duplicate_members": 14,
      "representative_unique_count": 5,
      "largest_cluster": 14,
      "best_step3_score": 59.758844619129654
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v44",
      "eligible_members": 22,
      "resulting_clusters": 6,
      "duplicate_members": 16,
      "representative_unique_count": 6,
      "largest_cluster": 17,
      "best_step3_score": 50.569251164077514
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v45",
      "eligible_members": 23,
      "resulting_clusters": 9,
      "duplicate_members": 14,
      "representative_unique_count": 9,
      "largest_cluster": 14,
      "best_step3_score": 47.813046987968995
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v46",
      "eligible_members": 30,
      "resulting_clusters": 10,
      "duplicate_members": 20,
      "representative_unique_count": 10,
      "largest_cluster": 19,
      "best_step3_score": 47.550075893782406
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v47",
      "eligible_members": 30,
      "resulting_clusters": 12,
      "duplicate_members": 18,
      "representative_unique_count": 12,
      "largest_cluster": 17,
      "best_step3_score": 36.99936703154284
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v48",
      "eligible_members": 22,
      "resulting_clusters": 8,
      "duplicate_members": 14,
      "representative_unique_count": 8,
      "largest_cluster": 14,
      "best_step3_score": 38.86401956997336
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v49",
      "eligible_members": 30,
      "resulting_clusters": 18,
      "duplicate_members": 12,
      "representative_unique_count": 18,
      "largest_cluster": 8,
      "best_step3_score": 49.312854010153536
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v50",
      "eligible_members": 30,
      "resulting_clusters": 9,
      "duplicate_members": 21,
      "representative_unique_count": 9,
      "largest_cluster": 22,
      "best_step3_score": 46.16851638281423
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v51",
      "eligible_members": 21,
      "resulting_clusters": 3,
      "duplicate_members": 18,
      "representative_unique_count": 3,
      "largest_cluster": 19,
      "best_step3_score": 53.047117562487415
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v52",
      "eligible_members": 57,
      "resulting_clusters": 14,
      "duplicate_members": 43,
      "representative_unique_count": 14,
      "largest_cluster": 34,
      "best_step3_score": 39.63138860769979
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v53",
      "eligible_members": 30,
      "resulting_clusters": 8,
      "duplicate_members": 22,
      "representative_unique_count": 8,
      "largest_cluster": 23,
      "best_step3_score": 95.13703613736767
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v54",
      "eligible_members": 24,
      "resulting_clusters": 8,
      "duplicate_members": 16,
      "representative_unique_count": 8,
      "largest_cluster": 17,
      "best_step3_score": 49.45679463486605
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v55",
      "eligible_members": 21,
      "resulting_clusters": 6,
      "duplicate_members": 15,
      "representative_unique_count": 6,
      "largest_cluster": 14,
      "best_step3_score": 46.18871527388367
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v56",
      "eligible_members": 27,
      "resulting_clusters": 13,
      "duplicate_members": 14,
      "representative_unique_count": 13,
      "largest_cluster": 15,
      "best_step3_score": 41.965753896511245
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v57",
      "eligible_members": 40,
      "resulting_clusters": 13,
      "duplicate_members": 27,
      "representative_unique_count": 13,
      "largest_cluster": 23,
      "best_step3_score": 29.266788265256096
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v58",
      "eligible_members": 30,
      "resulting_clusters": 13,
      "duplicate_members": 17,
      "representative_unique_count": 13,
      "largest_cluster": 17,
      "best_step3_score": 47.40282584572495
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v59",
      "eligible_members": 30,
      "resulting_clusters": 5,
      "duplicate_members": 25,
      "representative_unique_count": 5,
      "largest_cluster": 26,
      "best_step3_score": 37.48539916358632
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v60",
      "eligible_members": 19,
      "resulting_clusters": 2,
      "duplicate_members": 17,
      "representative_unique_count": 2,
      "largest_cluster": 18,
      "best_step3_score": 73.24186517058268
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v61",
      "eligible_members": 30,
      "resulting_clusters": 8,
      "duplicate_members": 22,
      "representative_unique_count": 8,
      "largest_cluster": 16,
      "best_step3_score": 53.07274255668514
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v62",
      "eligible_members": 15,
      "resulting_clusters": 7,
      "duplicate_members": 8,
      "representative_unique_count": 7,
      "largest_cluster": 8,
      "best_step3_score": 20.410806169555194
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v63",
      "eligible_members": 20,
      "resulting_clusters": 5,
      "duplicate_members": 15,
      "representative_unique_count": 5,
      "largest_cluster": 15,
      "best_step3_score": 37.08741543511781
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v64",
      "eligible_members": 30,
      "resulting_clusters": 5,
      "duplicate_members": 25,
      "representative_unique_count": 5,
      "largest_cluster": 25,
      "best_step3_score": 32.30886392447538
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v65",
      "eligible_members": 22,
      "resulting_clusters": 9,
      "duplicate_members": 13,
      "representative_unique_count": 9,
      "largest_cluster": 13,
      "best_step3_score": 39.52716552098919
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v66",
      "eligible_members": 20,
      "resulting_clusters": 10,
      "duplicate_members": 10,
      "representative_unique_count": 10,
      "largest_cluster": 8,
      "best_step3_score": 42.535510515346296
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v67",
      "eligible_members": 25,
      "resulting_clusters": 7,
      "duplicate_members": 18,
      "representative_unique_count": 7,
      "largest_cluster": 18,
      "best_step3_score": 36.06090731046431
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v68",
      "eligible_members": 27,
      "resulting_clusters": 3,
      "duplicate_members": 24,
      "representative_unique_count": 3,
      "largest_cluster": 25,
      "best_step3_score": 36.91925830918031
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v70",
      "eligible_members": 21,
      "resulting_clusters": 9,
      "duplicate_members": 12,
      "representative_unique_count": 9,
      "largest_cluster": 10,
      "best_step3_score": 36.72151965925913
    },
    {
      "input_kind": "formal_video",
      "source_id": "Sasha_v71",
      "eligible_members": 30,
      "resulting_clusters": 14,
      "duplicate_members": 16,
      "representative_unique_count": 14,
      "largest_cluster": 14,
      "best_step3_score": 24.40676193819548
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:039598d8883d320f0faf23e0a92e89930e7c8f4431dc8e385b759b5862aaab20",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 83.83930702031297
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:049d74a0967de03b00b4962c072c78fe213dfb707f06c29ccaa9b434081a00c7",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 2,
      "best_step3_score": 94.66301169590643
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:0a344fd2e2cd601eb381b694c3e5d867d8cc9a1eb68dffedc8cb1657843071fe",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 87.15768911526912
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:0eada9a3cf06146442f336116d5d12c367c7a9eff1948b7c58e6c467749e0a9b",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 86.65856292946249
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:0fbe7db8f9b6c52430dac8268b2b5fff54db7e78244c242b2c6666b0f878d2aa",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.92763157894737
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:169c7e586e4f0dbdb5a24a043c8377c5be3007db70a5c0124b416cbf145370e7",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 69.17381741423424
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:16bb9d481f23ed13e9e856fbe29858cf11db3a1f314dcac577aed1066e270119",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 91.97532674515003
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:1cb1bd26a0b52d41017659f7c3be69469be5b3f0a01aeec689bee81e6b04d0db",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 94.578216374269
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:1d4ff76f0841980ed89b5dcd3499d2625ae80463771e515302853811d29336f0",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 84.48003194076945
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:2144136bb1d9e3e9bd4b1b132b88c224f8c54962ba06dfdbe6b597572002482d",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 71.59585842386116
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:29965b319177addbe26daa605bbb2333a7a1d71be92677c4baa2f8cca41fc4b5",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 52.84214960543947
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:2a1b6fa8f24cc5ea4a658d6851c65c5f986488949ccb7d07c7d09d4e390151cd",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 74.88297635846313
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:32aa884ff668c9053c4e857e687a2b244d608ae28018dca86e5aff375e6f0c28",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 90.5149769560551
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:39f50451c23a76c75723bfcbf9b8ca3bdf2d6932d66b2be28894cbe17f5c3da1",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 64.04175957274241
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:3c87f029ac71000d6e12774197f3c38cd61e2f7b4ac95437ca25f93628b2c901",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 60.96181090646887
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:416c8530d72728390876e184a12d8ca4e09af0c71ffeed3b89f3a4c2a8885d59",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.02100440328104
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:42d1c0835c99d8c65838be3837379c1b787341efd5be8282aa94540a17ba85a5",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 94.0582358674464
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:4dbced93c1e4d05b516c65feef30da7cc9bfa6917f24e4e54927dfdd2e592a85",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.5796783625731
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:4dcea64e759071488186391c35a7cca65df7deafc8386a2adcc3db30a5476efb",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 85.61679005762052
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:53a9bb64b93e84e63b25f4c6082ea85125e566c01fb1d525ca12be4c56cdcc56",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 0.0
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:572862e0937b5ab122f78853f6db2b5d3acdc3b1b2bc2662762e086a03b5107a",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 78.34830229512767
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:58c342a9abcf28674abf22911d8e2425fadcb8fa603bb677ab6b5cb4dc61e082",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 92.3949805068226
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:5973edb6ea5a111bd4b9449ecfa121de07721899997b351e95ca61d0ca3bbe6b",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 59.94175002909078
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:6187956f2c2acf6538a9b62fa5073b99285dc12f297420b33493ee67313cbbb3",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 57.6715595872019
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:645715ef7039298124ede051f9acef8af90304ecc9979798a26c02640bb78e67",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 46.37069842625328
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:6a6adfe01ab3f532088b9fddfff186e13aebcf6f76b944ba93e3b05bb1858b0a",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 71.77630164312025
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:6ffe9d03f9da2515801fad6dfb9f8cf045d65c4b9afff09930e42745a586d558",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 94.6240253411306
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:75b2c74ead988b567ea3050291c24c8a23df99de5822c1d04bef2b3b060bdf2e",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 73.54166967817076
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:7e79954866df79ee93eb2603785c36d6dc37308bb7965c8f72d004fc1da683f1",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 94.20492202729045
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:82329e6ebf99d44898b69126cd292a9b8a604eaf6df70247fdbbea04ecb551c8",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.04507797270955
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:860c29b3669de73f5dd4c370b3fc068de4a68c99d64d343dca4f27cac079addf",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 60.80408873541634
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:8a0196bb5640a5fba0510741f1cdb5f6faaa258ae90716a61349945c95a035ec",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 87.16833336914982
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:8ad01e4df7a74e7d3c853f1976fff086c8607af47f79d8bf0c4212b7f367932a",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 94.08114035087719
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:8c65e6116b08f0e265bae2e1cfc82c99b8a1afad978aa49b041b635477344d26",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 0.0
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:8eddea217ac67630f87aa72c7322ab5c14f654135e0a7c2102687c4a173b1086",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 92.98172514619883
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:8fc91b287245c84dacf198e8926168a23dafec8e757c6fb4d124a44895af10fb",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 70.45823215981204
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:90f9728e27c63cb400814958a792456cc85a50949473cc5a0b9c5630608d743b",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 1,
      "representative_unique_count": 0,
      "largest_cluster": 2,
      "best_step3_score": 94.60745614035088
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:914f8228e99602a9d71ae2f4f9796ddcc5122a5011fc49b05dd4a079bea8b5b7",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.76486354775828
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:929f498adea2a9e6b64e3ab3efb5f3c751db5b7a45df2883e4012473e993cd8d",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 69.22017335127389
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:9d0903274b427c66e064f12ca61d2902ec4177fc3c665aa9917ebadf66c973f6",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.36232943469786
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:9f4b634a607a78ba43ccadab3bd406113bae311413d986245238c4d14bf6902c",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.68104288499025
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:a0187e624e4d50d20edcb5cd1acc1e6c644a896dae14b98fdc748d2daa502645",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 92.32172920560801
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:b00b7424e495a3008ed527dad58967eb5ec58d47c7126c9388c29d4821b1a608",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 94.45735867446393
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:b3239ae3f3571b39c42e48cf3e6a3a2ca0f78f19a0620f6f8c8715187ef2835e",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 87.02262851259289
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:c10bde558c9ee0e1d92019cd35725988a13099309e682aa93395101c19f27f03",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 70.89358632437208
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:c2fcbe37c8c289aacb378c9fa17cc89df816d72d3a96c50f69bb2660d850368e",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 0.0
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:c4ddd636159cacc32e7d0fab42fd6069d8c5aba60b930399c5f2d3ea49bf2e5e",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.51778752436647
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:c57f8bd0fcb184c2fffa1c85b8fadbe6768b8f8b3835c50c6c583b8677d957f1",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 70.26161144230497
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:ca5b6f723dff330e6dcaa087927cc16683eff75cae8019b43c04386117c9c931",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 78.79251770102839
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:ccbea4421970d01964abd42afc4edb6a730d04e12206af8eb7494f82553bade6",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 91.81949399934288
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:ce96ca9f1169a10beac00bc5e098f956629374b3d62bd63f6d3fbfd03de1b6fe",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 92.3740253411306
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:da9f2740e721b0ee72b797b2b74cb69a24c4171736edb29eb07eeac6a2a726ca",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 84.22362621278778
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:dc9ea3ccdfa2b31227715069579327efef5b183f906bd7a613b2916404b02595",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.95540935672514
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:e08a6b7a2c2c68f6a312a5d6edadd218afdb9c13197e19148413e123c322c05b",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 80.0111335023752
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:eccda1ac898b0071e7a7e5e555b6a5950d377ddba1bd62d84c5dcbb4de5bec42",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 86.65402398198408
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:ee9dddef4cb239ed4ee462efab5f1c298c382ceb3d46b9c0bc739671b40af700",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 94.2838693957115
    },
    {
      "input_kind": "supplemental_still",
      "source_id": "still:eec26220770cc91fb2d77dc2718a6f4c6752ccb07e02fe03b31dab942f3c9094",
      "eligible_members": 1,
      "resulting_clusters": 1,
      "duplicate_members": 0,
      "representative_unique_count": 1,
      "largest_cluster": 1,
      "best_step3_score": 93.82383040935673
    }
  ],
  "warning_policy": "Any observed pose-count reduction is highlighted for review; no magnitude threshold, quota or automatic protection.",
  "count_semantics": "Evidence counts are incident rows, not disjoint duplicate classes; edge types can overlap.",
  "final_training_selection": false,
  "quotas_applied": false,
  "rules": {
    "phash_threshold": 10,
    "temporal_phash_threshold": 14,
    "angle_threshold": 12.0,
    "tight_angle_threshold": 8.0,
    "time_window": 6
  },
  "input_hashes": {
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step4_pose_composition.csv": "ed5a213b4487132bc19915a6aa12a4008d9535a7cebf0cf752166c9c421d4634",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step4_pose_summary.json": "b6e8dd1fc1937a0d8443020061421136f2bc674dcb217c955374209949d44b07",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step3_best_ranking.csv": "6400f2a09d30b0a99488872c435c0fae039644cbc27619d90b09a31e0d7126ca",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step3_best_ranking_summary.json": "afe320e6385abf268b560ab05b7125f936a034cbd4754097221b9e5c22c16d87"
  },
  "input_versions": [
    "best_rank_v2.2",
    "step4_pose_composition_v3"
  ],
  "dataset_generations_by_kind": {
    "formal_video": [
      "bd72f194f62260fb728b77b26c75c5491b178908bff53393e197c11137bf9a40"
    ],
    "supplemental_still": [
      "b09674fe16b281285380bd5ae7c3d3585b2f787347d7672c74dd053bbbc968c4"
    ]
  },
  "outputs": {
    "output_csv": "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step5_dataset_report.csv",
    "summary": "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step5_dedup_summary.json",
    "markdown": "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\docs\\STEP5_DEDUP_SUMMARY.md",
    "review_html": "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\docs\\STEP5_DEDUP_REVIEW.html",
    "pose_review": "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\docs\\STEP5_REPRESENTATIVE_POSE_REVIEW.html",
    "pose_summary": "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step5_representative_pose_summary.csv"
  },
  "phash_kernel": "legacy 64-bit DCT, 32x32 AREA, upper-left8x8, median(dct[1:,:]) unchanged",
  "artifact_sha256": {
    "output_csv": "c9daf2a1615fca973abee9beb381c198dbb9f24042ff7953b2a7c81ca60d72d2",
    "review_html": "bbbb5892e7c0bbbdbc17f80a1b40eb8e8212c6cc0f86bcd73bb0ec596138269f",
    "pose_review": "71631adfa37761996a26106c1c57ea2de8e9f41975c07154bc5441f70a1b0f7a",
    "pose_summary": "e65df9d476e53bd286e60e02c308fad992d3915dda23f2a3e684c038f2b2f03c",
    "markdown": "8165f0dff920a29b6b74ed4d2c510c79c7b7e33f2313821fc0c9a45b34addb25"
  }
}
```
