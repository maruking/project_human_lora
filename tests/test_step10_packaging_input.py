import csv
import hashlib
import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common.packaging_input import verified_inputs
from common.config import load_config
import package_flux_dataset as packaging

class PackagingInputTests(unittest.TestCase):
    def fixture(self,base):
        images=base/'raw';images.mkdir();restored=base/'restored';restored.mkdir();rows=[]
        for i in range(2):
            directory=images/f'video{i}';directory.mkdir();path=directory/'same.png';path.write_bytes(('original'+str(i)).encode())
            rows.append(dict(frame_id=f'video{i}/same.png',filename=f'video{i}/same.png',image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                dataset_generation_id='g1',step8_review_session_id='session1',step8_decision='STEP8_ACCEPT',face_scale_bin='UPPER_BODY',
                pose_bin='THREE_QUARTER_RIGHT',best_score=str(90-i),global_rank=str(i+1)))
        return rows,images,base/'step9.csv',restored
    def write_report(self,path,rows):
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    def formal(self,rows,restored):
        records=[]
        for i,r in enumerate(rows):
            path=restored/f'v{i}.png';path.write_bytes(('restored'+str(i)).encode())
            records.append(dict(frame_id=r['frame_id'],image_sha256=r['image_sha256'],dataset_generation_id=r['dataset_generation_id'],
                step8_review_session_id=r['step8_review_session_id'],restoration_status='safely_restored',restored_path=path.name,
                restored_image_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        return records
    def test_absent_step9_uses_all_accept_originals_not_directory_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));(images/'extra.png').write_bytes(b'not-selected');(restored/'stale.png').write_bytes(b'old')
            inputs,_=verified_inputs(rows,images,report,restored)
            self.assertEqual(len(inputs),2);self.assertEqual({r['frame_id'] for r in inputs},{r['frame_id'] for r in rows})
            self.assertTrue(all(r['restoration_status']=='SKIPPED_NOT_NEEDED' and r['packaging_image_sha256']==r['image_sha256'] for r in inputs))
            self.assertEqual(inputs[0]['pose_bucket'],'RIGHT_3Q')
    def test_original_hash_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));(images/rows[0]['filename']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Original source hash mismatch'):verified_inputs(rows,images,report,restored)
    def test_only_accept_and_unique_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));rows[0]['step8_decision']='STEP8_NOT_SELECTED'
            with self.assertRaisesRegex(ValueError,'STEP8_ACCEPT'):verified_inputs(rows,images,report,restored)
            with self.assertRaisesRegex(ValueError,'identity set'):verified_inputs([rows[1],rows[1]],images,report,restored)
    def test_formal_step9_route_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));records=self.formal(rows,restored);self.write_report(report,records)
            inputs,_=verified_inputs(rows,images,report,restored)
            self.assertTrue(all(r['packaging_input_kind']=='STEP9_RESTORATION' and r['restoration_status']=='safely_restored' for r in inputs))
    def test_ambiguous_legacy_report_stops_not_silent_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));self.write_report(report,[dict(filename='same.png',restoration_status='safely_restored')])
            with self.assertRaisesRegex(ValueError,'formal current lineage'):verified_inputs(rows,images,report,restored)
    def test_restored_hash_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));records=self.formal(rows,restored);self.write_report(report,records);(restored/'v0.png').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Restored image hash mismatch'):verified_inputs(rows,images,report,restored)
    def test_stale_restoration_session_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));records=self.formal(rows,restored);records[0]['step8_review_session_id']='old';self.write_report(report,records)
            with self.assertRaisesRegex(ValueError,'Stale STEP9'):verified_inputs(rows,images,report,restored)
    def test_extra_restoration_row_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));records=self.formal(rows,restored);records.append(dict(records[0],frame_id='unknown'));self.write_report(report,records)
            with self.assertRaisesRegex(ValueError,'identity set differs'):verified_inputs(rows,images,report,restored)
    def test_path_traversal_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));records=self.formal(rows,restored);records[0]['restored_path']='../outside.png';self.write_report(report,records)
            with self.assertRaisesRegex(ValueError,'Unsafe restored'):verified_inputs(rows,images,report,restored)
    def test_preflight_exits_before_caption_or_model_load_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,images,report,restored=self.fixture(Path(tmp));inputs,pins=verified_inputs(rows,images,report,restored)
            with patch('sys.argv',['package_flux_dataset.py','--preflight-only','--output-dir',str(Path(tmp)/'export')]),patch.object(packaging,'load_inputs',return_value=(inputs,pins)),patch.object(packaging,'classify_clip_attributes',side_effect=AssertionError('inference forbidden')),redirect_stdout(io.StringIO()) as log:
                self.assertEqual(packaging.main(),0)
            self.assertFalse((Path(tmp)/'export').exists());self.assertIn('Packaging:NO',log.getvalue())
    def test_alignment_and_caption_template_unchanged(self):
        self.assertEqual([packaging.align_dimension_16(v) for v in (16,17,23,24,31,32)],[16,16,16,32,32,32])
        attrs=dict(expression='e',clothing='c',hair='h',bg='b',lighting='l')
        flux,tags=packaging.build_flux_caption('trigger','UPPER_BODY','RIGHT_3Q',attrs)
        self.assertEqual(flux,'upper body portrait of trigger, a young woman, turned slightly in three-quarter view to the right, e, c, h, b, l, high detail, authentic raw skin texture, 8k photo')
        self.assertEqual(tags,'trigger, 1girl, solo, upper body, right 3q, e, c, h, b, l, photorealistic')

if __name__=='__main__':unittest.main()
