import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from collections import Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from common.config import load_config
from common.step3_audit import csv_bytes
from build_step3_calibration import sample,manifest,analyze,blur_detail,crop_bytes,review_html,LABELS,boundary_pools


class CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings=load_config(ROOT/'config/config.example.yaml')['step3_face_gate']
        cls.rows=[]
        for i in range(120):
            scale=('CLOSE_UP','UPPER_BODY','FULL_BODY')[i%3];mult=(.8,.95,1.05,1.2)[(i//3)%4]
            r=dict(filename=f'person_v{i//6:02d}/frame_{i:03d}.png',video_id=f'person_v{i//6:02d}',frame_id=f'frame{i}',temporal_index=str(i),shot_type=scale,face_detected='true',facemesh_detected='true',eye_presence_valid='true',eye_sharpness=str(1.6*mult),face_laplacian_score=str(50*mult),face_tenengrad_score='500',skin_texture_score=str((.05 if scale=='CLOSE_UP' else .035)*mult),plasticity_ratio=str(45*mult),face_brightness_mean=str(95*mult),face_visibility_score=str(70*mult),laplacian_score='35',quality_rank=str(i+1),face_gate_reason='face_blurry' if mult<1 else 'eligible',face_gate_category='REJECT_BLUR' if mult<1 else 'ELIGIBLE',face_eligible='false' if mult<1 else 'true',face_bbox_x='20',face_bbox_y='20',face_bbox_width='80',face_bbox_height='90')
            cls.rows.append(r)
    def test_sampling_deterministic(self):
        self.assertEqual(sample(self.rows,self.settings,target=80,cap=5),sample(self.rows,self.settings,target=80,cap=5))
    def test_no_duplicate_frames(self):
        selected,_=sample(self.rows,self.settings,target=80,cap=5)
        self.assertEqual(len(selected),len({i['row']['filename'] for i in selected}))
    def test_video_cap(self):
        selected,_=sample(self.rows,self.settings,target=40,cap=2)
        self.assertLessEqual(max(Counter(i['row']['video_id'] for i in selected).values()),2)
    def test_boundary_selection(self):
        selected,coverage=sample(self.rows,self.settings,target=100,cap=5)
        self.assertTrue(all(c['selected_count']>0 for c in coverage if c['available_count']))
    def test_manifest_complete_labels_empty(self):
        selected,_=sample(self.rows,self.settings,target=80,cap=5);records=manifest(selected,'subject','generation')
        self.assertTrue(all(all(k in r and r[k]=='' for k in LABELS) for r in records))
        self.assertTrue(all(r['filename'] and r['frame_id'] and r['dataset_generation_id']=='generation' for r in records))
        parsed=list(csv.DictReader(io.StringIO(csv_bytes(records).decode('utf-8-sig'))))
        self.assertEqual(parsed,records)
    def test_crops_deterministic(self):
        image=np.random.default_rng(4).integers(0,256,(200,200,3),dtype=np.uint8)
        self.assertEqual(crop_bytes(image,self.rows[0]),crop_bytes(image.copy(),self.rows[0]))
    def test_original_pixels_unchanged(self):
        image=np.zeros((200,200,3),dtype=np.uint8);before=image.tobytes();crop_bytes(image,self.rows[0]);self.assertEqual(image.tobytes(),before)
    def test_offline_html_no_external_resources(self):
        selected,_=sample(self.rows,self.settings,target=80,cap=5);records=manifest(selected,'subject','generation')
        html=review_html(records,{},'fixture')
        for value in ('http://','https://','fetch(','XMLHttpRequest','WebSocket','<iframe','<script src='):self.assertNotIn(value,html)
        self.assertIn("connect-src 'none'",html);self.assertIn('JSON出力',html);self.assertIn('CSV出力',html)
    def test_counterfactual_source_unchanged(self):
        before=json.dumps(self.rows,sort_keys=True);tables=analyze(self.rows,self.settings)
        self.assertEqual(json.dumps(self.rows,sort_keys=True),before)
        face=next(r for r in tables[3] if r['ignored_reason']=='face_blurry');self.assertEqual(face['counterfactual_eligible_count'],len(self.rows))
    def test_if_elif_branch_vs_both(self):
        r=dict(self.rows[0]);d=blur_detail(r,self.settings)
        self.assertTrue(d['face_blurry_due_to_both']);self.assertEqual(d['executed_blur_branch'],'eye_sharpness')
        r['shot_type']='FULL_BODY';self.assertEqual(blur_detail(r,self.settings)['executed_blur_branch'],'face_laplacian')
    def test_disabled_eye_distinct(self):
        r=dict(self.rows[0],eye_presence_valid='false',eye_sharpness='0')
        self.assertEqual(blur_detail(r,self.settings)['eye_metric_state'],'eye_sharpness_disabled')
        r['facemesh_detected']='false';self.assertEqual(blur_detail(r,self.settings)['eye_metric_state'],'facemesh_unavailable')
    def test_gate_values_unchanged(self):
        before=dict(self.settings);analyze(self.rows,self.settings);sample(self.rows,self.settings,target=80,cap=5);self.assertEqual(self.settings,before)
    def test_threshold_measured_only(self):
        rows=[dict(self.rows[0]),dict(self.rows[0],filename='other',eye_presence_valid='false',eye_sharpness='0')]
        tables=analyze(rows,self.settings);r=next(r for r in tables[1] if r['shot_type']=='CLOSE_UP' and r['metric']=='eye_sharpness')
        self.assertEqual(r['count'],1);self.assertEqual(r['excluded_count'],1)
    def test_html_safe_embedded_strings(self):
        selected,_=sample(self.rows,self.settings,target=80,cap=5);records=manifest(selected,'</script>','generation')
        html=review_html(records,{},'fixture');self.assertNotIn('"subject_context": "</script>"',html)

    def test_measured_eye_threshold_relation(self):
        r=dict(self.rows[0]);self.assertEqual(blur_detail(r,self.settings)['eye_threshold_state'],'measured_below_threshold')
        r['eye_sharpness']='1.7';r['face_laplacian_score']='55';r['face_gate_reason']='eligible'
        self.assertEqual(blur_detail(r,self.settings)['eye_threshold_state'],'measured_at_or_above_threshold')


if __name__=='__main__':unittest.main()
