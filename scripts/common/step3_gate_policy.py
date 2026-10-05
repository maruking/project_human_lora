"""Approved STEP3 diagnostic families, separate from eligibility and selection A/B/C."""
FLAGS = ('global_blur_suspected', 'native_face_blur_suspected', 'eye_detail_suspected',
         'skin_detail_suspected', 'beauty_filter_suspected', 'plasticity_suspected',
         'half_eye_suspected', 'overexposure_white_haze_suspected', 'review_measurement_unavailable')
POLICY_COLUMNS = FLAGS + ('diagnostic_flags', 'diagnostic_concern_families', 'diagnostic_state',
                          'eye_diagnostic_state', 'skin_diagnostic_state', 'eye_presence_gate_state',
                          'left_eye_open_ratio', 'right_eye_open_ratio', 'eye_open_min', 'eye_open_asymmetry',
                          'eye_openness_state', 'face_highlight_clip_ratio', 'face_bright_region_ratio',
                          'face_dynamic_range', 'face_exposure_state', 'face_exposure_roi_method', 'face_exposure_diagnostic_error',
                          'review_diagnostic_config_path', 'review_diagnostic_config_sha256')

def diagnostic_evidence(row, args):
    flags = []
    if row.get('laplacian_score') and float(row['laplacian_score']) < args.min_global_laplacian:
        flags.append(FLAGS[0])
    if row.get('face_laplacian_score') and float(row['face_laplacian_score']) < args.min_face_laplacian:
        flags.append(FLAGS[1])
    eye_applicable = (row.get('facemesh_detected') == 'true' and row.get('eye_presence_valid') == 'true'
                      and row.get('anatomical_metric_status') == 'measured'
                      and row.get('shot_type') in ('CLOSE_UP', 'UPPER_BODY') and row.get('eye_sharpness') not in ('', None))
    if eye_applicable and float(row['eye_sharpness']) < args.min_eye_sharpness:
        flags.append(FLAGS[2])
    skin_applicable = (row.get('beauty_filter_applicability') == 'measured'
                       and row.get('shot_type') in ('CLOSE_UP', 'UPPER_BODY') and row.get('skin_texture_score') not in ('', None))
    if skin_applicable:
        threshold = args.min_skin_texture_close_up if row['shot_type'] == 'CLOSE_UP' else args.min_skin_texture_upper_body
        if float(row['skin_texture_score']) < threshold:
            flags.append(FLAGS[3])
    if row.get('beauty_filter_detected') == 'true':
        flags.append(FLAGS[4])
    if row.get('plasticity_ratio') and float(row['plasticity_ratio']) > args.max_plasticity_ratio:
        flags.append(FLAGS[5])
    if row.get("eye_openness_state") in ("CLOSED_OR_BLINK", "BORDERLINE"):
        flags.append("half_eye_suspected")
    if row.get("face_exposure_state") in ("OVEREXPOSED", "BORDERLINE"):
        flags.append("overexposure_white_haze_suspected")
    if row.get("face_exposure_diagnostic_error"):
        flags.append("review_measurement_unavailable")
    families = []
    if FLAGS[2] in flags:
        families.append('EYE_DETAIL')
    if skin_applicable and any(flag in flags for flag in FLAGS[3:6]):
        families.append('SKIN_PROCESSING')
    return dict({flag: str(flag in flags).lower() for flag in FLAGS},
                diagnostic_flags=';'.join(flags), diagnostic_concern_families=';'.join(families),
                eye_diagnostic_state='MEASURED_APPLICABLE' if eye_applicable else 'NOT_APPLICABLE_FULL_BODY' if row.get('shot_type') == 'FULL_BODY' else row.get('anatomical_metric_status', ''),
                skin_diagnostic_state='MEASURED_APPLICABLE' if skin_applicable else row.get('beauty_filter_applicability', ''))
