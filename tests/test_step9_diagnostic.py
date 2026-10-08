import copy
import unittest
from step9_diagnostic import diagnose

class Step9DiagnosticTests(unittest.TestCase):
    def row(self,**extra):
        row=dict(frame_id='f1',filename='f1.png',step8_decision='STEP8_ACCEPT',face_scale_bin='FULL_BODY',
            face_bbox_width='300',face_bbox_height='200',face_laplacian_canonical_192='40',eye_sharpness='2.5',best_score='80',global_rank='1')
        row.update(extra);return row
    def settings(self):return dict(restoration_face_dim_threshold=190.,restoration_eye_threshold=2.)
    def test_clear_existing_metrics(self):
        self.assertEqual(diagnose(self.row(),self.settings())['step9_diagnostic_state'],'RESTORATION_NOT_NEEDED')
    def test_existing_face_trigger_and_bbox_formula(self):
        result=diagnose(self.row(face_bbox_height='189'),self.settings())
        self.assertEqual(result['face_min_dimension'],189)
        self.assertIn('EXISTING_STEP9_FACE_DIMENSION_TRIGGER',result['diagnostic_reason'])
    def test_existing_eye_trigger(self):
        self.assertIn('EXISTING_STEP9_EYE_TRIGGER',diagnose(self.row(eye_sharpness='1.9'),self.settings())['diagnostic_reason'])
    def test_boundary_is_strictly_less_than(self):
        self.assertEqual(diagnose(self.row(face_bbox_height='190',eye_sharpness='2'),self.settings())['step9_diagnostic_state'],'RESTORATION_NOT_NEEDED')
    def test_missing_legacy_eye_not_replaced_with_local_detail(self):
        result=diagnose(self.row(eye_sharpness='',left_eye_local_detail='3',right_eye_local_detail='4'),self.settings())
        self.assertEqual(result['legacy_eye_metric_state'],'UNAVAILABLE');self.assertEqual(result['step9_diagnostic_state'],'REVIEW_RECOMMENDED')
    def test_disabled_eye_not_treated_as_real_zero(self):
        result=diagnose(self.row(eye_sharpness='0',anatomical_metric_status='eye_sharpness_disabled_by_existing_presence_gate'),self.settings())
        self.assertIn('EXISTING_STEP9_EYE_METRIC_UNAVAILABLE',result['diagnostic_reason']);self.assertNotIn('EXISTING_STEP9_EYE_TRIGGER',result['diagnostic_reason'])
    def test_protected_shots_no_new_canonical_cutoff(self):
        for scale in ('CLOSE_UP','UPPER_BODY'):
            result=diagnose(self.row(face_scale_bin=scale,eye_sharpness='',face_laplacian_canonical_192='20'),self.settings())
            self.assertEqual(result['step9_diagnostic_state'],'RESTORATION_NOT_NEEDED')
    def test_only_accept_rows(self):
        with self.assertRaisesRegex(ValueError,'STEP8_ACCEPT'):diagnose(self.row(step8_decision='STEP8_NOT_SELECTED'),self.settings())
    def test_missing_required_metric_review_not_pass(self):
        self.assertIn('CANONICAL_SHARPNESS_UNAVAILABLE',diagnose(self.row(face_laplacian_canonical_192=''),self.settings())['diagnostic_reason'])
    def test_source_row_unchanged(self):
        row=self.row();before=copy.deepcopy(row);out=diagnose(row,self.settings());self.assertEqual(row,before)
        self.assertEqual(out['best_score'],row['best_score']);self.assertEqual(out['global_rank'],row['global_rank'])

if __name__=='__main__':unittest.main()
