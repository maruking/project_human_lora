"""Synthetic full-row and descriptor invariants; no dataset inference."""
import sys
from pathlib import Path
import unittest
import tempfile
import csv
import json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from common.config import load_config
from common.pose_composition import settings_from,describe
from common.pose_composition_v3 import infer_rows,VERSION
from test_step4_pose_composition import fixture
from step4_pose_composition_v3 import publish


class Fake:
    def __init__(self,result=None,error=False):
        self.calls=0;self.error=error
        self.result=result or dict(status='MEASURED',yaw=-50.178443908691406,pitch=22.464284896850586,
                                   roll=-26.181455612182617,face_count=1,association_iou=.5)
    def measure(self,row,path):
        self.calls+=1
        if self.error:raise ValueError('model failure')
        return self.result


class V3Tests(unittest.TestCase):
    def setUp(self):self.settings=settings_from(load_config(ROOT/'config/config.example.yaml'))
    def test_full_rows_preserved_and_fatal_not_inferred(self):
        rows=[fixture(str(i),eligible=i%3!=0,kind='supplemental_still' if i%2 else 'formal_video') for i in range(100)]
        estimator=Fake();out=infer_rows(rows,self.settings,estimator,lambda r:Path('fake'))
        self.assertEqual([r['frame_id'] for r in rows],[r['frame_id'] for r in out])
        self.assertEqual(estimator.calls,66)
        for old,new in zip(rows,out):
            self.assertEqual(new['step4_version'],VERSION)
            for key in ('best_score','global_rank','ranking_eligible','image_sha256','dataset_generation_id','review_state'):
                self.assertEqual(old.get(key),new.get(key))
            self.assertEqual(new['face_scale_bin'],describe(old,self.settings)['face_scale_bin'])
            for key in ('yaw','pitch','roll','pose_status'):self.assertEqual(new['step3_'+key],old[key])
    def test_counterexample_alternative_not_frontal(self):
        row=fixture();row.update(yaw='-.8924490419025111',pitch='-81.47005902642142',roll='-24.144534812590955')
        out=infer_rows([row],self.settings,Fake(),lambda r:Path('fake'))[0]
        self.assertEqual(out['pose_bin'],'PROFILE_LEFT')
        self.assertEqual(out['vertical_pose'],'LOOKING_DOWN')
        self.assertEqual(out['yaw'],-50.178443908691406)
    def test_missing_new_pose_does_not_fall_back_to_old(self):
        estimator=Fake(dict(status='NO_FACE',face_count=0,association_iou=''))
        out=infer_rows([fixture()],self.settings,estimator,lambda r:Path('fake'))[0]
        self.assertEqual(out['pose_bin'],'NOT_EVALUABLE');self.assertEqual(out['yaw'],'')
        self.assertEqual(out['step3_yaw'],'0');self.assertEqual(out['step4_status'],'NOT_EVALUABLE')
    def test_error_preserves_row(self):
        out=infer_rows([fixture()],self.settings,Fake(error=True),lambda r:Path('fake'))[0]
        self.assertEqual(out['step4_status'],'ERROR');self.assertEqual(out['frame_id'],'frame')
    def test_boundaries_unchanged(self):
        for yaw,expected in [(15,'FRONTAL'),(-15,'FRONTAL'),(15.001,'THREE_QUARTER_RIGHT'),(41.999,'THREE_QUARTER_RIGHT'),(42,'PROFILE_RIGHT'),(-42,'PROFILE_LEFT')]:
            estimator=Fake(dict(status='MEASURED',yaw=yaw,pitch=20,roll=0,face_count=1,association_iou=.5))
            out=infer_rows([fixture()],self.settings,estimator,lambda r:Path('fake'))[0]
            self.assertEqual(out['pose_bin'],expected);self.assertEqual(out['vertical_pose'],'LEVEL')
    def test_synthetic_publication_preserves_previous_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            inputs=(base/'input.csv',base/'input.json')
            for path in inputs:path.write_text('fixture',encoding='utf-8')
            targets=dict(output=base/'step4.csv',summary=base/'summary.json',
                         video_summary=base/'video.csv',markdown=base/'summary.md')
            rows=[fixture('a'),fixture('fatal',eligible=False)]
            outputs=infer_rows(rows,self.settings,Fake(),lambda r:Path('fake'))
            estimator=Fake();estimator.metadata={'estimator':'synthetic'}
            first=publish(outputs,self.settings,estimator,inputs,targets)
            saved=targets['output'].read_bytes()
            second=publish(outputs,self.settings,estimator,inputs,targets)
            self.assertEqual(saved,targets['output'].read_bytes())
            self.assertEqual(second['step4_version'],VERSION);self.assertEqual(second['total_rows'],2)
            self.assertEqual(len(list((base/'bkup').glob('*/MANIFEST.json'))),1)
            with targets['output'].open(encoding='utf-8-sig') as handle:
                self.assertEqual(len(list(csv.DictReader(handle))),2)


if __name__=='__main__':unittest.main()
