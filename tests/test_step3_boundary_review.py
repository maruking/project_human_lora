import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from common.config import load_config
from build_step3_boundary_review import memberships, select, review_data, render, hard_failures


class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s=load_config(ROOT/'config/config.example.yaml')['step3_face_gate']
    def row(self,**kwargs):
        return dict(filename='subject_v01/subject_v01_001.png',video_id='subject_v01',frame_id='frame1',shot_type='CLOSE_UP',face_gate_status='ok',face_eligible='false',face_detected='true',facemesh_detected='true',face_count='1',multiple_faces='false',eye_presence_valid='true',eye_sharpness='1.589',face_laplacian_score='55',left_eye_presence_ratio='.1',right_eye_presence_ratio='.1',beauty_filter_detected='false',skin_texture_score='.09',plasticity_ratio='12',face_visibility_score='100',face_brightness_mean='150',face_to_global_brightness_ratio='1',face_min_dimension='200',source_short_edge='1080',face_central_gradient='10',laplacian_score='100',face_gate_reason='face_blurry')|kwargs
    def test_eligible_and_extreme_not_sampled(self):
        self.assertEqual(memberships(self.row(face_eligible='true'),self.s),{})
        self.assertEqual(memberships(self.row(eye_sharpness='.1',face_laplacian_score='2'),self.s),{})
    def test_proxy_and_fullbody_not_eye_boundaries(self):
        for extra in [dict(eye_presence_valid='false',eye_sharpness='0'),dict(facemesh_detected='false'),dict(shot_type='FULL_BODY')]:
            self.assertNotIn('eye_sharpness',memberships(self.row(**extra),self.s))
    def test_actual_if_elif_not_both_reject_causes(self):
        row=self.row();before=json.dumps(row,sort_keys=True);settings=dict(self.s)
        records,labels=review_data([(row,memberships(row,self.s))],self.s,'generation',{})
        cards={c['field']:c for c in records[0]['presentation']['cards']}
        self.assertTrue(cards['eye_sharpness']['reject_used'].startswith('YES'))
        self.assertTrue(cards['face_laplacian_score']['reject_used'].startswith('NO'))
        self.assertEqual({r['human_gate_name'] for r in labels},{'eye_sharpness'})
        self.assertTrue(all(r['human_accept']=='' for r in labels))
        self.assertEqual(json.dumps(row,sort_keys=True),before);self.assertEqual(settings,self.s)
    def test_unique_deterministic_bounded_sampling(self):
        rows=[self.row(filename=f'v{i//3}/f{i}.png',video_id=f'v{i//3}',frame_id=str(i)) for i in range(100)]
        a,_=select(rows,self.s,target=45,video_cap=2);b,_=select(rows,self.s,target=45,video_cap=2)
        self.assertEqual(a,b);self.assertEqual(len(a),13);self.assertEqual(len({r['filename'] for r,_ in a}),13)
        self.assertTrue(all(r['face_eligible']=='false' for r,_ in a))
    def test_single_gate_invariant_and_masked_blur(self):
        r=self.row(eye_sharpness='1.598',face_laplacian_score='26.247',face_visibility_score='60')
        self.assertEqual(hard_failures(r,self.s),{'eye_sharpness','face_laplacian','visibility'})
        self.assertEqual(memberships(r,self.s),{})
        with self.assertRaises(ValueError):review_data([(r,{'eye_sharpness':{}})],self.s,'generation',{})
        for r in (self.row(),self.row(eye_sharpness='2',face_laplacian_score='49')):
            target=memberships(r,self.s);self.assertEqual(len(target),1)
            self.assertEqual(hard_failures(r,self.s),{next(iter(target))})
            self.assertEqual(next(iter(target.values()))['other_failure_count'],0)
    def test_beauty_causes_and_rounding_not_mixed(self):
        r=self.row(eye_sharpness='2',face_gate_reason='beauty_filter_detected',beauty_filter_detected='true',plasticity_ratio='46')
        self.assertEqual(set(memberships(r,self.s)),{'plasticity'})
        r['skin_texture_score']='.049';self.assertEqual(memberships(r,self.s),{})
        r['plasticity_ratio']='45.0';r['skin_texture_score']='.050';self.assertEqual(memberships(r,self.s),{})
    def test_no_fill_for_sparse_category(self):
        rows=[self.row(filename=str(i),frame_id=str(i),video_id=str(i)) for i in range(6)]
        selected,_=select(rows,self.s);self.assertEqual(len(selected),6)
        self.assertEqual(select([self.row(face_eligible='true')],self.s)[0],[])
    def test_render_safe_and_offline(self):
        row=self.row();records,_=review_data([(row,memberships(row,self.s))],self.s,'generation',{'subject_v01':'</script>'})
        html=render(records,{},'fixture');self.assertNotIn('"subject_context": "</script>"',html)
        for unsafe in ('fetch(', 'http://', 'https://', '<script src='):self.assertNotIn(unsafe,html)
        self.assertIn("connect-src 'none'",html);self.assertIn('human_gate_name',html)


if __name__=='__main__':unittest.main()
