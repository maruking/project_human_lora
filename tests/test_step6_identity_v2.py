import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common.identity_v2 import (evaluate, centroid, normalized, identity_state, gallery,
    associate, AssociationAmbiguous, reference_inventory, digest)
from step6_identity_v2 import annotate, publish, preflight, safe_targets, review_html, reference_html


def face(vector=(1.,0.), box=(0,0,8,8)):
    return dict(embedding=np.array(vector),bbox=list(box),detection_score=.9)


def row(role='UNIQUE', frame='one'):
    return dict(frame_id=frame,filename=frame+'.png',dedup_role=role,face_bbox='0,0,8,8',
        width='8',height='8',pose_bin='NOT_EVALUABLE',yaw='',pitch='',face_scale_bin='FULL_BODY',
        best_score='3',video_id='source',global_rank='999',review_state='PENDING',
        input_kind='formal_video',dataset_generation_id='synthetic-generation')


class Backend:
    metadata = dict(model='buffalo_l',backend='insightface')
    def __init__(self, faces=None):
        self.result = [face()] if faces is None else faces
        self.calls = 0
    def faces(self, image):
        self.calls += 1
        return self.result


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.bank = [('anchor',np.array([1.,0.]),{})]
        self.center = np.array([1.,0.])
        self.backend = Backend()

    def evaluate(self, source=None, faces=None):
        return evaluate(source or row(),[face()] if faces is None else faces,self.bank,self.center,.55,self.backend.metadata)

    def test_01_unique_and_representative_targets(self):
        for role in ('UNIQUE','REPRESENTATIVE'):
            self.assertEqual(self.evaluate(row(role))['identity_state'],'IDENTITY_PASS')

    def test_02_duplicate_preserved_not_applicable(self):
        r=row('DUPLICATE_MEMBER'); out=self.evaluate(r)
        self.assertEqual(out['identity_state'],'NOT_APPLICABLE_DUPLICATE_MEMBER')
        self.assertEqual(out['identity_similarity_centroid'],'')
        self.assertTrue(all(out[k]==v for k,v in r.items()))

    def test_03_fatal_not_applicable(self):
        self.assertEqual(self.evaluate(row('NOT_APPLICABLE_STEP3_FATAL'))['identity_state'],'NOT_APPLICABLE_UPSTREAM')

    def test_04_face_eligible_not_target_control(self):
        r=row(); r['face_eligible']='false'
        self.assertEqual(self.evaluate(r)['identity_state'],'IDENTITY_PASS')

    def test_05_no_input_no_latest_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder); (p/'step5_dataset_report_old.csv').write_text('frame_id\nold\n')
            with self.assertRaises(FileNotFoundError): preflight(p/'missing.csv',p/'missing.json',{},p)

    def references(self, count, backend=None):
        with tempfile.TemporaryDirectory() as folder:
            files=[]
            for i in range(count):
                p=Path(folder)/f'{i}.png'; cv2.imwrite(str(p),np.full((8,8,3),i,np.uint8)); files.append(p)
            return gallery(files,backend or self.backend,.55,3,20)

    def test_06_reference_count_below3(self):
        self.assertEqual(self.references(2)[1]['reference_audit_status'],'BLOCKED')

    def test_07_reference_no_face_invalid(self):
        records,summary,_,_=self.references(3,Backend([]))
        self.assertEqual(summary['invalid_references'],3)

    def test_08_reference_multi_face_invalid(self):
        self.assertEqual(self.references(3,Backend([face(),face()]))[1]['invalid_references'],3)

    def test_09_outlier_blocks(self):
        class Sequence(Backend):
            def faces(self,image):
                self.calls+=1
                return [face((-1,0) if self.calls==3 else (1,0))]
        records,summary,bank,center=self.references(3,Sequence())
        self.assertGreater(summary['reference_outliers'],0)
        self.assertIsNone(center)

    def test_10_centroid_normalized(self):
        self.assertAlmostEqual(np.linalg.norm(centroid([[1,0],[1,1]])),1)

    def test_11_candidate_no_face_not_reject(self):
        self.assertEqual(self.evaluate(faces=[])['identity_state'],'IDENTITY_NOT_EVALUABLE')

    def test_12_single_face_evaluated(self):
        self.assertEqual(self.evaluate()['candidate_face_count'],1)

    def test_13_multi_face_max_iou_review(self):
        out=self.evaluate(faces=[face((0,1),(20,20,30,30)),face()])
        self.assertEqual(out['identity_state'],'IDENTITY_REVIEW')
        self.assertEqual(out['candidate_primary_face_iou'],1)

    def test_14_centroid_boundary_pass(self):
        self.assertEqual(identity_state(.55,.55,.55),'IDENTITY_PASS')

    def test_15_centroid_below_max_above_review(self):
        self.assertEqual(identity_state(.54,.55,.55),'IDENTITY_REVIEW')

    def test_16_both_below_reject(self):
        self.assertEqual(identity_state(.54,.54,.55),'IDENTITY_REJECT')

    def test_17_pose_does_not_lower_threshold(self):
        r=row(); r.update(yaw='89',pose_bin='PROFILE_RIGHT')
        out=self.evaluate(r,[face((0,1))]); self.assertEqual(out['identity_threshold'],.55)
        self.assertEqual(out['identity_state'],'IDENTITY_REJECT')

    def test_18_scale_does_not_lower_threshold(self):
        for scale in ('CLOSE_UP','UPPER_BODY','FULL_BODY'):
            r=row(); r['face_scale_bin']=scale
            self.assertEqual(self.evaluate(r,[face((0,1))])['identity_state'],'IDENTITY_REJECT')

    def test_19_missing_pose_preserved(self):
        self.assertEqual(self.evaluate()['yaw'],'')
        self.assertEqual(self.evaluate()['pose_bin'],'NOT_EVALUABLE')

    def test_20_no_crop_fallback(self):
        backend=Backend([])
        self.assertEqual(self.references(3,backend)[1]['valid_references'],0)
        self.assertEqual(backend.calls,3)

    def test_21_shared_backend_no_separate_preprocessing(self):
        import inspect
        from common.identity_v2 import InsightFaceBackend
        self.assertIn('self.app.get(image)',inspect.getsource(InsightFaceBackend.faces))
        import step6_identity_v2 as runtime
        self.assertIn('backend.faces(image)',inspect.getsource(runtime.annotate))

    def test_22_review_state_not_a_feature(self):
        r=row(); r['review_state']='REJECT'
        self.assertEqual(self.evaluate(r)['identity_similarity_centroid'],self.evaluate()['identity_similarity_centroid'])

    def test_23_source_id_does_not_alter_identity(self):
        r=row(); r.update(source_id='different',video_id='different')
        self.assertEqual(self.evaluate(r)['identity_similarity_centroid'],1)

    def test_24_different_filenames_same_embedding_same_result(self):
        self.assertEqual(self.evaluate(row(frame='x'))['identity_state'],self.evaluate(row(frame='y'))['identity_state'])

    def test_25_full_rows_including_upstream_error(self):
        sources=[row('DUPLICATE_MEMBER','d'),row('NOT_APPLICABLE_STEP3_FATAL','f'),row('ERROR','e')]
        outputs,errors=annotate(sources,Path('.'),self.backend,self.bank,self.center,.55)
        self.assertEqual(len(outputs),3); self.assertEqual(outputs[-1]['identity_state'],'UPSTREAM_ERROR')
        self.assertEqual(self.backend.calls,0)

    def test_26_partial_no_overwrite_official(self):
        import inspect,step6_identity_v2
        self.assertIn("if partial or errors:",inspect.getsource(step6_identity_v2.main))
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); official=root/'full.csv'; official.write_bytes(b'prior')
            source=row(); cv2.imwrite(str(root/'one.png'),np.zeros((8,8,3),np.uint8)); source['image_sha256']=digest(root/'one.png')
            r2=dict(source,frame_id='two')
            outputs,_=annotate([source,r2],root,self.backend,self.bank,self.center,.55,limit=1)
            self.assertEqual(outputs[1]['step6_status'],'PARTIAL_NOT_EVALUATED')
            self.assertEqual(official.read_bytes(),b'prior')

    def test_27_html_not_reference_input(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder); (p/'review.html').write_text('not reference')
            self.assertEqual(reference_inventory(p)[0],[])

    def test_28_cluster_fallback_without_promoting_duplicate(self):
        out=self.evaluate(row('REPRESENTATIVE'),[face((0,1))])
        self.assertEqual(out['cluster_identity_fallback_needed'],'true')
        self.assertEqual(self.evaluate(row('DUPLICATE_MEMBER'))['identity_state'],'NOT_APPLICABLE_DUPLICATE_MEMBER')

    def test_association_tie_or_no_overlap_stops(self):
        for faces in ([face(),face()],[face(box=(20,20,30,30)),face(box=(40,40,50,50))]):
            with self.assertRaises(AssociationAmbiguous): associate(faces,row())

    def test_invalid_embedding_not_zero_similarity(self):
        for vector in ((0,0),(float('nan'),1)):
            out=self.evaluate(faces=[face(vector)])
            self.assertEqual(out['identity_state'],'IDENTITY_NOT_EVALUABLE')
            self.assertEqual(out['identity_similarity_centroid'],'')

    def test_publication_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); a=root/'a.csv'; b=root/'b.json'
            a.write_bytes(b'old-a'); b.write_bytes(b'old-b')
            import os
            replace=os.replace
            def fail(src,dest):
                if Path(dest)==b: raise OSError('synthetic failure')
                return replace(src,dest)
            with patch('step6_identity_v2.os.replace',side_effect=fail):
                with self.assertRaises(OSError): publish({'csv':b'new','summary':b'new'},{'csv':a,'summary':b},'summary',{})
            self.assertEqual(a.read_bytes(),b'old-a'); self.assertEqual(b.read_bytes(),b'old-b')

    def test_reference_html_source_link_and_details(self):
        records,summary,_,_=self.references(3)
        html=reference_html(records,summary,Path('/anchors'),Path('/docs/review.html'))
        self.assertIn('leave_one_out_centroid_similarity',html)
        self.assertIn('../anchors/',html)

    def test_partial_cli_publication_is_isolated(self):
        import argparse
        import step6_identity_v2 as runtime
        from common.config import load_config
        config=load_config()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); images=root/'images'; images.mkdir(); refs=root/'refs'; refs.mkdir()
            source=row(); cv2.imwrite(str(images/'one.png'),np.zeros((8,8,3),np.uint8))
            source['image_sha256']=digest(images/'one.png')
            refs_files=[]
            for i in range(3):
                path=refs/f'{i}.png'; cv2.imwrite(str(path),np.full((8,8,3),i,np.uint8)); refs_files.append(path)
            backend=Backend(); records,summary,bank,center=gallery(refs_files,backend,.55,3,20)
            summary.update(step6_version='step6_identity_v2',reference_directory_sha256=reference_inventory(refs)[1])
            paths={k:root/Path(v).name for k,v in runtime.DEFAULT_PATHS.items()}
            for key in ('reference_csv','reference_markdown','reference_html'): paths[key].write_bytes(b'audit')
            summary['artifact_sha256']={k:digest(paths[k]) for k in ('reference_csv','reference_markdown','reference_html')}
            paths['reference_summary'].write_text(json.dumps(summary),encoding='utf-8')
            for key in runtime.FINAL_KEYS: paths[key].write_bytes(b'previous-full')
            args=argparse.Namespace(**paths,images=images,reference=refs,device='cpu',limit=1,
                reference_preflight_only=False,preflight_only=False)
            with patch.object(runtime,'load_for_cli',return_value=config), \
                 patch.object(runtime,'configure_parser'), \
                 patch.object(runtime.argparse.ArgumentParser,'parse_args',return_value=args), \
                 patch.object(runtime,'safe_targets'), \
                 patch.object(runtime,'preflight',return_value=([source,dict(source,frame_id='two')],{})), \
                 patch.object(runtime,'InsightFaceBackend',return_value=backend):
                self.assertEqual(runtime.main(),0)
            for key in runtime.FINAL_KEYS: self.assertEqual(paths[key].read_bytes(),b'previous-full')
            partial=list((root/'audit').glob('*/step6_identity_summary.json'))
            self.assertEqual(len(partial),1)
            self.assertEqual(json.loads(partial[0].read_text())['publication_status'],'PARTIAL')

    def test_runtime_failure_stops_preserving_pending_rows(self):
        backend=Backend()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); cv2.imwrite(str(root/'one.png'),np.zeros((8,8,3),np.uint8))
            r=row(); r['image_sha256']=digest(root/'one.png')
            with patch.object(backend,'faces',side_effect=RuntimeError('GPU failed')) as inference:
                outputs,errors=annotate([r,dict(r,frame_id='two')],root,backend,self.bank,self.center,.55)
            self.assertEqual(inference.call_count,1)
            self.assertEqual(len(outputs),2)
            self.assertTrue(errors)
            self.assertEqual(outputs[1]['step6_status'],'ABORTED_NOT_EVALUATED')


if __name__=='__main__': unittest.main()
