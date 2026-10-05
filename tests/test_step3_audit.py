import ast
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np
import cv2
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import face_quality_gate as gate
from common.step3_audit import geometry_diagnostics,safe_output,build_artifacts,publish
from test_config import script_parser


class Backend:
    def __init__(self, result): self.result=result
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def process(self,rgb):return self.result


def backend(count):
    bbox=NS(xmin=.2,ymin=.2,width=.5,height=.5)
    detections=[NS(score=[.9],location_data=NS(relative_bounding_box=bbox)) for _ in range(count)]
    return NS(solutions=NS(face_detection=NS(FaceDetection=lambda **kw:Backend(NS(detections=detections))),
                           face_mesh=NS(FaceMesh=lambda **kw:Backend(NS(multi_face_landmarks=[])))))


def points(eye=.2,mouth=.1):
    p=[NS(x=.5,y=.5) for _ in range(468)]
    for a,b,c,d in [(33,133,159,145),(263,362,386,374)]:
        p[a]=NS(x=.3,y=.4);p[b]=NS(x=.5,y=.4)
        p[c]=NS(x=.4,y=.4-eye*.1);p[d]=NS(x=.4,y=.4+eye*.1)
    p[61]=NS(x=.3,y=.6);p[291]=NS(x=.7,y=.6)
    p[13]=NS(x=.5,y=.6-mouth*.2);p[14]=NS(x=.5,y=.6+mouth*.2)
    return p


class Step3Tests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.root=Path(self.folder.name)
        self.args=script_parser('face_quality_gate',{}).parse_args([])
        self.rows=[]
        for i in range(10):
            name=f'person{ i%2 }/same_{i:03d}.png';p=self.root/name;p.parent.mkdir(exist_ok=True)
            ok,buf=cv2.imencode('.png',np.full((200,200,3),140,np.uint8));buf.tofile(p)
            self.rows.append(dict(filename=name,video_id=f'person{i%2}',temporal_index=str(i),quality_rank=str(i+1),laplacian_score='30.000',brightness_mean='140.000',step_name='STEP2_TECHNICAL_METRICS'))
    def tearDown(self):self.folder.cleanup()
    def analyze(self,count=0,rows=None):
        with patch.object(gate,'mp',backend(count)):
            return gate.analyze_rows([dict(r) for r in (rows or self.rows)],self.root,self.args)[0]
    def test_full_ten_rows_and_source_values(self):
        result=self.analyze()
        self.assertEqual(len(result),10)
        for before,after in zip(self.rows,result):
            for k,v in before.items():self.assertEqual(after[k],v)
    def test_no_face_is_reject_not_error(self):
        r=self.analyze()[0];self.assertEqual(r['face_gate_status'],'ok');self.assertEqual(r['face_gate_reason'],'no_face')
        self.assertEqual(r['face_eligible'],'false');self.assertEqual(r['eye_openness_mean'],'')
    def test_multiple_face_row_preserved(self):
        result=self.analyze(2)
        self.assertEqual(len(result),10)
        self.assertTrue(all('multiple_faces' in r['face_gate_reason'] for r in result))
        self.assertTrue(all(r['face_count']=='2' and r['face_eligible']=='false' for r in result))
    def test_decode_errors_preserved(self):
        (self.root/self.rows[0]['filename']).write_bytes(b'invalid')
        r=self.analyze()[0];self.assertEqual(r['face_gate_status'],'error');self.assertEqual(r['face_gate_reason'],'analysis_error')
    def test_processing_error_preserved(self):
        b=backend(1);b.solutions.face_mesh.FaceMesh=lambda **kw:Backend(None)
        with patch.object(gate,'mp',b):r=gate.analyze_rows([dict(self.rows[0])],self.root,self.args)[0][0]
        self.assertEqual(r['face_gate_status'],'error');self.assertEqual(r['face_gate_reason'],'analysis_error')
    def test_partial_never_normal_path(self):
        p=self.root/'step3_dataset_report.csv';self.assertEqual(safe_output(p,1,p).name,'step3_dataset_report.partial.csv')
    def test_relative_identity_collision(self):
        for video in ('a','b'):
            (self.root/video).mkdir();(self.root/video/'same.png').write_bytes(video.encode())
        self.assertNotEqual(gate.image_path(self.root,'a/same.png')[0],gate.image_path(self.root,'b/same.png')[0])
        with self.assertRaises(ValueError):gate.image_path(self.root,'same.png')
        with self.assertRaises(ValueError):gate.image_path(self.root,'../same.png')
    def test_unicode_path(self):
        p=self.root/'人物'/'画像.png';p.parent.mkdir();p.write_bytes((self.root/self.rows[0]['filename']).read_bytes())
        self.assertIsNotNone(cv2.imdecode(np.fromfile(gate.image_path(self.root,'人物/画像.png')[0],dtype=np.uint8),cv2.IMREAD_COLOR))
    def test_sharpness_deterministic(self):
        rng=np.random.default_rng(42);image=rng.integers(0,256,(180,160,3),dtype=np.uint8)
        self.assertEqual(gate.sharpness(image),gate.sharpness(image.copy()))
        self.assertEqual(gate.cheek_skin_texture_metrics(image,points(),(20,20,120,120),2,'CLOSE_UP',.05,.035,45),gate.cheek_skin_texture_metrics(image.copy(),points(),(20,20,120,120),2,'CLOSE_UP',.05,.035,45))
    def test_blink_geometry_fixture(self):
        self.assertEqual(geometry_diagnostics(points(.05),100,100)['blink_suspected'],'true')
        self.assertEqual(geometry_diagnostics(points(.25),100,100)['blink_suspected'],'false')
        self.assertEqual(geometry_diagnostics(None,100,100),{})
    def test_mouth_geometry_fixture(self):
        for value,label in [(0,'closed'),(.1,'slightly_open'),(.25,'open'),(.5,'very_open')]:
            self.assertEqual(geometry_diagnostics(points(mouth=value),100,100)['mouth_open_class'],label)
    def test_formula_functions_unchanged(self):
        import hashlib
        baseline=json.loads((ROOT/'tests/fixtures/step3_formula_baseline.json').read_text())
        new=ast.parse((ROOT/'scripts/face_quality_gate.py').read_text(encoding='utf-8'))
        for name,digest in baseline.items():
            node=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(hashlib.sha256(ast.dump(node).encode()).hexdigest(),digest,name)
    def test_reports_deterministic_and_counts(self):
        rows=self.analyze();gen=dict(frame_count=10,video_count=2)
        a=build_artifacts(rows,list(self.rows[0]),gen,'source',{})
        self.assertEqual(a,build_artifacts(rows,list(self.rows[0]),gen,'source',{}))
        videos=list(csv.DictReader(io.StringIO(a['step3_video_summary.csv'].decode('utf-8-sig'))))
        self.assertEqual(sum(int(r['frame_count']) for r in videos),10)
        self.assertEqual(json.loads(a['step3_summary.json'])['counts']['eligible_count'],0)
    def test_failed_publication_preserves_good(self):
        p=self.root/'step3.csv';p.write_bytes(b'good');rows=self.analyze()
        artifacts=build_artifacts(rows,list(self.rows[0]),dict(frame_count=10),'source',{})
        publish(p,artifacts,failed=True)
        self.assertEqual(p.read_bytes(),b'good');self.assertTrue(list((p.parent/'step3_revision1_audit/failed').rglob('dataset.csv')))
    def test_partial_publication_preserves_good(self):
        p=self.root/'step3.csv';p.write_bytes(b'good');rows=self.analyze()
        artifacts=build_artifacts(rows,list(self.rows[0]),dict(frame_count=10),'source',{},partial=True)
        publish(safe_output(p,5,p),artifacts,partial=True)
        self.assertEqual(p.read_bytes(),b'good')
    def test_incomplete_production_rejected(self):
        with self.assertRaises(ValueError):build_artifacts(self.analyze(),list(self.rows[0]),dict(frame_count=11),'source',{})

    def test_atomic_publication_failure_rolls_back(self):
        from common.step3_audit import os as module_os
        p=self.root/'step3.csv';p.write_bytes(b'previous-good')
        summary=self.root/'step3_summary.json';summary.write_bytes(b'previous-summary')
        real_replace=module_os.replace
        def fail_summary(src,dest):
            if Path(dest)==summary:raise PermissionError('locked summary fixture')
            return real_replace(src,dest)
        with patch('common.step3_audit.os.replace',side_effect=fail_summary):
            with self.assertRaises(PermissionError):publish(p,{'dataset.csv':b'new','step3_summary.json':b'new-summary'})
        self.assertEqual(p.read_bytes(),b'previous-good');self.assertEqual(summary.read_bytes(),b'previous-summary')
    def test_csv_only_rebuild_and_source_guard(self):
        import hashlib
        from common.step3_audit import csv_bytes
        from build_step3_reports import rebuild
        source=csv_bytes(self.rows);step2=self.root/'step2.csv';step2.write_bytes(source)
        rows=self.analyze();artifacts=build_artifacts(rows,list(self.rows[0]),dict(frame_count=10,video_count=2),hashlib.sha256(source).hexdigest(),{})
        report=self.root/'step3.csv';report.write_bytes(artifacts['dataset.csv'])
        summary=self.root/'step3_summary.json';summary.write_bytes(artifacts['step3_summary.json'])
        self.assertEqual(rebuild(report,summary,step2),artifacts)
        step2.write_bytes(source+b'\n')
        with self.assertRaises(ValueError):rebuild(report,summary,step2)

    def test_review_copies_preserve_source(self):
        import hashlib
        result=self.analyze();before={r['filename']:hashlib.sha256((self.root/r['filename']).read_bytes()).hexdigest() for r in self.rows}
        paths={i:gate.image_path(self.root,r['filename']) for i,r in enumerate(self.rows)}
        review=self.root/'review';crops=self.root/'crops'
        gate.materialize_review(result,paths,review,crops,'fixture')
        self.assertEqual(len(list(review.rglob('*.png'))),10)
        self.assertTrue(all(hashlib.sha256((self.root/name).read_bytes()).hexdigest()==digest for name,digest in before.items()))


if __name__=='__main__':unittest.main()
