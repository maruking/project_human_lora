"""STEP4 v3 inference descriptors; STEP3 scores, lineage and geometry stay intact."""
from .pose_composition import describe, describe_rows, summarize, markdown_summary, finite

VERSION = 'step4_pose_composition_v3'


def infer_rows(rows, settings, estimator, path_for):
    # Existing row validation and face-scale formulas retained verbatim.
    baseline = describe_rows(rows, settings)
    outputs = []
    for row, old in zip(rows, baseline):
        work = dict(row)
        for key in ('yaw','pitch','roll','pose_status'):
            work['step3_'+key] = row.get(key,'')
            work[key] = '' if key != 'pose_status' else 'NOT_EVALUABLE'
        result = dict(status='NOT_APPLICABLE_STEP3_FATAL',face_count='',association_iou='')
        error = ''
        if row['ranking_eligible'].lower() == 'true':
            try:
                if old['step4_geometry_source'] != 'STORED_STEP3_BBOX_AND_DIMENSIONS':
                    raise ValueError('Primary STEP3 bbox unavailable/invalid')
                result = estimator.measure(row,path_for(row))
                if result['status'] == 'MEASURED':
                    for key in ('yaw','pitch','roll'):
                        value = finite(result[key])
                        if value is None:
                            raise ValueError('Missing new pose '+key)
                        work[key] = value
                    work['pose_status'] = 'MEASURED'
            except Exception as exc:
                result = dict(status='ERROR',face_count='',association_iou='')
                error = str(exc)
                work.update(yaw='',pitch='',roll='',pose_status='NOT_EVALUABLE')
        out = describe(work,settings)
        out.update(step4_version=VERSION,step4_pose_source='INSIGHTFACE_BUFFALO_L_3D68',
                   step4_estimator_status=result['status'],step4_detected_face_count=result['face_count'],
                   step4_primary_face_iou=result['association_iou'])
        if result['status'] == 'ERROR':
            out.update(step4_status='ERROR',step4_error=error)
        elif result['status'] not in ('MEASURED','NOT_APPLICABLE_STEP3_FATAL'):
            out['step4_error'] = result['status']
        assert out['face_scale_bin'] == old['face_scale_bin']
        for key in row:
            if key not in ('yaw','pitch','roll','pose_status','shot_type'):
                assert out[key] == row[key], key
        outputs.append(out)
    assert [r['frame_id'] for r in outputs] == [r['frame_id'] for r in rows]
    return outputs


def summary_for(rows):
    summary,sources = summarize(rows)
    summary['step4_version'] = VERSION
    return summary,sources


def markdown_for(summary):
    text = markdown_summary(summary).replace('Version: step4_pose_composition_v2','Version: '+VERSION)
    return text + '\nEstimator: installed buffalo_l 68-point 3D; raw signed degrees, comparison-approved.\nSTEP3 angles preserved in step3_yaw/pitch/roll/pose_status.\nSTEP5+ remains unchanged and v2-only: do not run downstream until explicitly adapted for v3.\n'
