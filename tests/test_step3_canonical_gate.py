"""Synthetic validation of approved architecture; no production dataset processing."""
import csv
import io
import json
from pathlib import Path
import runpy
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from test_config import script_parser
import test_step3_audit as fixtures
import face_quality_gate as gate
from common.step3_audit import build_artifacts

def clean():
    return dict(filename='sample/frame.png',frame_id='sample/frame.png',video_id='sample',temporal_index='1',quality_rank='1',
        face_gate_status='ok',face_detected='true',face_count='1',multiple_faces='false',facemesh_detected='true',
        shot_type='CLOSE_UP',source_short_edge='2160',face_min_dimension='500',face_visibility_score='100',
        face_central_gradient='0',eye_presence_valid='true',left_eye_presence_ratio='.2',right_eye_presence_ratio='.2',face_brightness_mean='140',face_to_global_brightness_ratio='1',
        face_laplacian_score='100',laplacian_score='100',eye_sharpness='2',skin_texture_score='1',plasticity_ratio='2',
        beauty_filter_detected='false',anatomical_metric_status='measured',beauty_filter_applicability='measured',
        face_laplacian_canonical_192='36.901392',face_tenengrad_canonical_192='100',
        face_sharpness_metric='face_laplacian_canonical_192',face_sharpness_canonical_short_edge='192',
        face_sharpness_gate_threshold='36.901392')

class CanonicalGateTests(unittest.TestCase):
    def setUp(self):self.args=script_parser('face_quality_gate',{}).parse_args([])
    def apply(self,**changes):
        row=clean();row.update(changes);return gate.apply_gate(row,self.args)
    def test_config_and_cli_threshold_precedence(self):
        parser=script_parser('face_quality_gate',{'step3_face_gate':{'min_face_laplacian_canonical':40}})
        self.assertEqual(parser.parse_args([]).min_face_laplacian_canonical,40)
        self.assertEqual(parser.parse_args(['--min-face-laplacian-canonical','42']).min_face_laplacian_canonical,42)
        self.assertEqual(parser.parse_args([]).face_sharpness_canonical_short_edge,192)
    def test_threshold_boundary_and_missing(self):
        for value,eligible in [('36.901391','false'),('36.901392','true'),('36.901393','true')]:
            with self.subTest(value=value):self.assertEqual(self.apply(face_laplacian_canonical_192=value)['face_eligible'],eligible)
        for value in ('','nan'):
            r=self.apply(face_laplacian_canonical_192=value)
            self.assertEqual(r['face_gate_reason'],'analysis_error');self.assertEqual(r['face_gate_status'],'error')
    def test_each_former_gate_is_diagnostic_only(self):
        for change in (dict(eye_sharpness='0.1'),dict(laplacian_score='0'),dict(face_laplacian_score='0'),
                       dict(skin_texture_score='0'),dict(beauty_filter_detected='true'),dict(plasticity_ratio='100')):
            with self.subTest(change=change):
                r=self.apply(**change);self.assertEqual(r['face_eligible'],'true');self.assertEqual(r['diagnostic_state'],'PASS')
                self.assertTrue(r['diagnostic_flags'])
    def test_borderline_is_separate_eligible_state(self):
        r=self.apply(eye_sharpness='.1',skin_texture_score='0',beauty_filter_detected='true',plasticity_ratio='100')
        self.assertEqual(r['diagnostic_state'],'BORDERLINE');self.assertEqual(r['face_eligible'],'true')
        self.assertEqual(r['face_gate_reason'],'eligible');self.assertEqual(r['face_gate_category'],'ELIGIBLE')
        self.assertEqual(r['diagnostic_concern_families'],'EYE_DETAIL;SKIN_PROCESSING')
        self.assertEqual(self.apply(skin_texture_score='0',beauty_filter_detected='true',plasticity_ratio='100')['diagnostic_state'],'PASS')
    def test_eye_does_not_mask_canonical_failure(self):
        r=self.apply(eye_sharpness='.1',face_laplacian_canonical_192='30')
        self.assertEqual(r['face_gate_reason'],'face_blurry');self.assertEqual(r['face_eligible'],'false')
    def test_retained_hard_conditions(self):
        cases=[('no_face',dict(face_detected='false',face_count='0')),('multiple_faces',dict(face_count='2')),
            ('low_visibility',dict(facemesh_detected='false')),('low_visibility',dict(face_visibility_score='69')),
            ('one_eye_occluded',dict(eye_presence_valid='false')),('face_too_small',dict(face_min_dimension='10')),
            ('low_resolution_source',dict(shot_type='FULL_BODY',source_short_edge='719')),
            ('face_underexposed',dict(face_brightness_mean='94')),
            ('face_backlit_underexposed',dict(face_brightness_mean='100',face_to_global_brightness_ratio='.5')),
            ('hair_covered_face',dict(face_central_gradient='66'))]
        for reason,changes in cases:
            with self.subTest(reason=reason):
                r=self.apply(**changes);self.assertIn(reason,r['face_gate_reason'].split(';'));self.assertEqual(r['face_eligible'],'false')
    def test_disabled_eyes_are_not_measured_zero(self):
        r=self.apply(eye_presence_valid='false',eye_sharpness='0',anatomical_metric_status='eye_sharpness_disabled_by_existing_presence_gate')
        self.assertEqual(r['eye_detail_suspected'],'false');self.assertIn('one_eye_occluded',r['face_gate_reason'])
    def test_experiment_resize_equivalence_and_immutable_input(self):
        resize=runpy.run_path(str(ROOT/'docs/STEP3_CANONICAL_EXPERIMENT/compare_sharpness.py'),run_name='resize_reference')['resize']
        rng=np.random.default_rng(3)
        for dims,expected in [((400,600),'INTER_AREA'),((100,150),'INTER_CUBIC'),((192,288),'IDENTITY')]:
            image=rng.integers(0,256,(*dims,3),dtype=np.uint8);before=image.copy()
            resized,method=gate.canonical_face_copy(image,192);reference,ref_method,_=resize(image,192)
            self.assertEqual(method,expected);self.assertEqual(method,ref_method)
            np.testing.assert_array_equal(resized,reference);np.testing.assert_array_equal(image,before)
            self.assertEqual(min(resized.shape[:2]),192);self.assertEqual(gate.sharpness(resized),gate.sharpness(reference))
    def test_official_report_schema_and_lineage(self):
        row=self.apply();original=dict(filename=row['filename'],video_id='sample',frame_id=row['frame_id'],quality_rank='1')
        r2=self.apply(filename='sample/frame2.png',frame_id='sample/frame2.png',quality_rank='2',face_laplacian_canonical_192='30')
        artifacts=build_artifacts([row,r2],list(original),dict(frame_count=2,video_count=1),'fixture',vars(self.args))
        output=list(csv.DictReader(io.StringIO(artifacts['dataset.csv'].decode('utf-8-sig'))))
        self.assertEqual({r['frame_id'] for r in output},{row['frame_id'],r2['frame_id']})
        self.assertEqual(output[0]['face_laplacian_canonical_192'],row['face_laplacian_canonical_192'])
        for field in ('face_laplacian_score','eye_sharpness','skin_texture_score','beauty_filter_detected','plasticity_ratio','diagnostic_flags'):
            self.assertEqual(output[0][field],row[field])
        summary=json.loads(artifacts['step3_summary.json'])
        self.assertTrue(summary['full_row_preservation']);self.assertEqual(summary['face_gate_architecture']['metric'],'face_laplacian_canonical_192')
        self.assertIn(b'face_laplacian_canonical_192',artifacts['step3_distribution_summary.csv'])

class CanonicalMeasurementPipelineTests(unittest.TestCase):
    def test_actual_analysis_populates_canonical_metadata(self):
        fixture=fixtures.Step3Tests();fixture.setUp()
        try:r=fixture.analyze(1,rows=[fixture.rows[0]])[0]
        finally:fixture.tearDown()
        self.assertEqual(r['face_sharpness_canonical_short_edge'],'192')
        self.assertNotEqual(r['face_laplacian_canonical_192'],'')
        self.assertEqual(min(int(r['face_core_canonical_width']),int(r['face_core_canonical_height'])),192)
        self.assertNotEqual(r['face_sharpness_resize_method'],'')

if __name__=='__main__':unittest.main()
