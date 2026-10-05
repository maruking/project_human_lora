"""BEST contract tests, synthetic rows/images only; never production inference."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from common.best_ranking import VERSION,rank_rows,choose_round,METRICS,POSITIVE,PENALTIES
from common.best_inventory import assemble
from common.best_review import materialize,feedback,read_history
from common.step3_review import is_review_copy,require_source


def row(i=0,kind='formal_video',video=None):
    video=video or f'video{i%15}'
    r=dict(frame_id=f'{video}/frame{i}.png',filename=f'{video}/frame{i}.png',input_kind=kind,
           source_id=video,video_id=video if kind=='formal_video' else '',dataset_generation_id='synthetic',
           analysis_status='MEASURED',face_detected='true',confirmed_face_count=1,
           crop_geometry_status='VALID',face_evaluability='MEASURED',image_sha256='test',yaw=0)
    r.update({k:i+1 for k in METRICS})
    return r


class RankingTests(unittest.TestCase):
    def test_supplemental_inventory(self):
        formal=[dict(filename='v/a.png',frame_id='authoritative-frame-key',video_id='v',status='ok')]
        stills=[dict(filename='photos/a.jpg',status='ok')]
        r=assemble(formal,stills,{'sha256':'video-gen'},{'sha256':'still-gen','files':{'photos/a.jpg':'still-sha'}},{'v/a.png':'video-sha'})
        self.assertEqual(len(r),2);self.assertEqual(r[1]['input_kind'],'supplemental_still')
        self.assertEqual(r[1]['image_sha256'],'still-sha');self.assertEqual(r[1]['dataset_generation_id'],'still-gen')
        self.assertEqual(r[1]['video_id'],'')
        self.assertEqual(r[0]['frame_id'],'authoritative-frame-key')
    def test_inventory_mismatch_stops(self):
        with self.assertRaises(ValueError):assemble([],[],{'sha256':'g'},{'files':{'missing':'hash'}},{})
    def test_review_input_guard(self):
        p=ROOT/'output/reports/step3_best_review/round_01/review_reject/a.jpg'
        self.assertTrue(is_review_copy(p))
        with self.assertRaises(ValueError):require_source(p)
    def test_fatal_excluded_full_rows_kept(self):
        rows=[row(i) for i in range(6)]
        rows[0]['face_detected']='false';rows[1]['confirmed_face_count']=2
        rows[2]['analysis_status']='ERROR';rows[3]['crop_geometry_status']='INVALID'
        rows[4]['face_evaluability']='NOT_EVALUABLE'
        r=rank_rows(rows,{})
        self.assertEqual(len(r),6);self.assertEqual(sum(x['ranking_eligible']=='true' for x in r),1)
        self.assertTrue(all(x['global_rank']=='' for x in r if x['fatal_reject']=='true'))
    def test_weak_diagnostics_never_fatal(self):
        r=row();r.update(face_gate_reason='face_blurry;one_eye_occluded;face_underexposed;beauty_filter_detected',
                         eye_openness_state='CLOSED_OR_BLINK',legacy_eye_presence_valid='false')
        r.update({k:0 for k in METRICS})
        self.assertEqual(rank_rows([r],{})[0]['fatal_reject'],'false')
    def test_old_one_eye_does_not_control(self):
        a=row();b=dict(a,legacy_eye_presence_valid='false',one_eye_occluded='true',face_eligible='false')
        self.assertEqual(rank_rows([a],{})[0]['best_score'],rank_rows([b],{})[0]['best_score'])
        self.assertEqual(rank_rows([b],{})[0]['ranking_eligible'],'true')
    def test_auditable_score(self):
        r=rank_rows([row()],{})[0]
        self.assertTrue(all('component_'+k in r and 'contribution_'+k in r for k in POSITIVE))
        self.assertTrue(all(k in r for k in ('blur_penalty','clipping_penalty','eye_obstruction_penalty')))
        self.assertAlmostEqual(r['best_score'],r['base_quality']*r['critical_face_quality']-r['penalty_total'])
    def test_missing_not_zero(self):
        a=row();a['left_eye_local_detail']=None;a['right_eye_local_detail']=''
        r=rank_rows([a],{})[0]
        self.assertEqual(r['norm_left_eye_local_detail'],'');self.assertEqual(r['component_eye_detail'],'')
        self.assertEqual(r['contribution_eye_detail'],0);self.assertLess(r['measurement_reliability_factor'],1)
    def test_separate_normalization(self):
        videos=[row(i) for i in range(3)]
        before={r['frame_id']:r['relative_quality_bonus_sharpness'] for r in rank_rows(videos,{})}
        still=row(100,'supplemental_still');still['face_laplacian_canonical_192']=100000
        after={r['frame_id']:r['relative_quality_bonus_sharpness'] for r in rank_rows(videos+[still],{}) if r['input_kind']=='formal_video'}
        self.assertEqual(before,after)
    def test_video_cap(self):
        r=rank_rows([row(i) for i in range(100)],{})
        chosen,info=choose_round(r,[])
        self.assertEqual(len(chosen),45);self.assertLessEqual(max(info['video_counts'].values()),4)
        self.assertFalse(info['cap_relaxed'])
    def test_cap_minimal_relaxation(self):
        r=rank_rows([row(i,video='single') for i in range(50)],{})
        chosen,info=choose_round(r,[])
        self.assertEqual(len(chosen),45);self.assertEqual(info['effective_video_cap'],45)
        self.assertTrue(info['cap_relaxed'])
    def test_shown_never_reappears(self):
        r=rank_rows([row(i) for i in range(150)],{})
        first,_=choose_round(r,[]);history=[dict(x,shown_to_maru=True) for x in first]
        second,_=choose_round(r,history)
        self.assertFalse({x['frame_id'] for x in first}&{x['frame_id'] for x in second})
    def test_sharp_but_dark_obstructed_loses(self):
        clean=row(1);bad=row(2)
        for k in ('left_eye_local_detail','right_eye_local_detail','mouth_local_detail','local_face_contrast','face_visibility_score','eye_open_min','left_eye_presence','right_eye_presence','dynamic_range_p95_p5'):bad[k]=0
        for k in ('face_shadow_ratio','highlight_clip_ratio','eye_open_asymmetry'):bad[k]=10
        r=rank_rows([clean,bad],{})
        self.assertEqual(r[0]['frame_id'],clean['frame_id'])


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'raw';self.review=self.root/'reports/step3_best_review'
        self.history=self.root/'reports/step3_best_review_history_by_version.json'
        self.rows=[]
        for i in range(6):
            r=row(i);p=self.source/r['filename'];p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(('source'+str(i)).encode());r['image_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();self.rows.append(r)
        self.rows=rank_rows(self.rows,{})
    def tearDown(self):self.temp.cleanup()
    def publish(self):return materialize(self.rows,self.source,self.review,self.history,1,{'review_size':2,'max_per_video':4})
    def test_move_is_copy_only_and_feedback(self):
        h=self.publish();r=h['records'][0];relative=Path(r['copy_relative'])
        src=self.source/relative;before=src.read_bytes()
        old=self.review/VERSION/'round_01/candidates'/relative;new=self.review/VERSION/'round_01/review_reject'/relative
        new.parent.mkdir(parents=True,exist_ok=True);old.rename(new)
        h,rejected=feedback(self.review,self.history)
        self.assertEqual(src.read_bytes(),before);self.assertEqual(len(rejected),1)
        self.assertEqual(rejected[0]['review_state'],'REVIEW_REJECT');self.assertIn('why_ranked_high',rejected[0])
    def test_delete_copies_preserves_history(self):
        h=self.publish();ids={r['frame_id'] for r in h['records']}
        shutil.rmtree(self.review)
        h,rejected=feedback(self.review,self.history)
        self.assertEqual({r['frame_id'] for r in h['records']},ids)
        self.assertTrue(all(r['copy_status']=='MISSING' for r in h['records']))
        self.assertTrue(all((self.source/r['filename']).exists() for r in self.rows))
        self.assertEqual(self.publish()['records'],h['records']);self.assertFalse(self.review.exists())
    def test_round_two_excludes_history(self):
        h=self.publish();ids={r['frame_id'] for r in h['records']}
        h=materialize(self.rows,self.source,self.review,self.history,2,{'review_size':2})
        self.assertFalse(ids&{r['frame_id'] for r in h['records'] if r['review_round']==2})
    def test_tampered_source_does_not_publish(self):
        (self.source/self.rows[0]['filename']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.publish()
        self.assertFalse(self.history.exists())
    def test_unregistered_folder_not_overwritten(self):
        (self.review/VERSION/'round_01/candidates').mkdir(parents=True)
        with self.assertRaises(ValueError):self.publish()
    def test_partial_copy_failure_never_reshows(self):
        with patch('common.best_review.shutil.copy2',side_effect=OSError('synthetic copy failure')):
            with self.assertRaises(OSError):self.publish()
        self.assertEqual(len(read_history(self.history)['records']),2)
        with self.assertRaises(ValueError):self.publish()


class MeasurementTests(unittest.TestCase):
    def test_native_kernel_measurement_with_missing_mesh(self):
        import cv2,numpy as np
        import face_quality_gate as gate
        from common.best_measurement import measure_rows
        from test_step3_audit import backend
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=row();p=root/r['filename'];p.parent.mkdir()
            cv2.imencode('.png',np.full((200,200,3),140,np.uint8))[1].tofile(p)
            with patch.object(gate,'mp',backend(1)):
                measured=measure_rows([r],root,{},gate)[0]
            self.assertEqual(measured['analysis_status'],'MEASURED')
            self.assertEqual(measured['landmark_status'],'UNAVAILABLE_BBOX_FALLBACK')
            self.assertEqual(measured['face_visibility_score'],'')
            self.assertIn('highlight_clip_ratio',measured)
            self.assertEqual(rank_rows([measured],{})[0]['ranking_eligible'],'true')
    def test_measured_eye_presence_failure_is_diagnostic(self):
        import cv2,numpy as np
        import face_quality_gate as gate
        from common.best_measurement import measure_rows
        from test_step3_audit import backend,points
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=row();p=root/r['filename'];p.parent.mkdir()
            cv2.imencode('.png',np.full((200,200,3),140,np.uint8))[1].tofile(p)
            b=backend(1);b.solutions.face_mesh.FACEMESH_FACE_OVAL={(33,133),(61,291)}
            with patch.object(gate,'mp',b),patch.object(gate,'matching_landmarks',return_value=points()),patch.object(gate,'eye_presence_metrics',return_value=(0,.8,False)):
                measured=measure_rows([r],root,{},gate)[0]
            self.assertEqual(measured['legacy_eye_presence_valid'],'false')
            self.assertEqual(measured['eye_measurement_availability'],'MEASURED')
            self.assertEqual(rank_rows([measured],{})[0]['fatal_reject'],'false')


class EntryPointTests(unittest.TestCase):
    def test_synthetic_production_path_and_existing_round(self):
        import step3_best_ranking as entry
        from common.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';reports=root/'reports';manifests=root/'manifests'
            config=load_config();config['paths'].update(raw_frames_dir=str(raw),reports_dir=str(reports),manifests_dir=str(manifests))
            config['step3_best_ranking']['review_size']=2
            inventory=[]
            for i in range(5):
                r=row(i);r['diagnostic_config_sha256']=entry.effective_settings(config['step3_best_ranking'],config)['_diagnostic_sha256'];p=raw/r['filename'];p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(str(i).encode());r['image_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();inventory.append(r)
            with patch.object(entry,'load_config',return_value=config),patch.object(entry,'load_inventory',return_value=(inventory,{'synthetic':'snapshot'})),patch('common.best_measurement.measure_rows',side_effect=lambda rows,*args:rows):
                self.assertEqual(entry.main(['--remeasure']),0)
                self.assertFalse((reports/'step3_best_review').exists())
                self.assertEqual(entry.main(['--from-existing','--review-round','1']),0)
                self.assertEqual(entry.main(['--from-existing','--review-round','2']),0)
                h=read_history(reports/'step3_best_review_history_by_version.json')
                self.assertEqual(len(h['records']),4)
                self.assertEqual(len({r['frame_id'] for r in h['records']}),4)
                self.assertFalse((reports/'step3_dataset_report.csv').exists())
                self.assertEqual(entry.main(['--feedback-only']),0)
    def test_settings_schema_and_bat_wiring(self):
        from common.config import load_config
        config=load_config();self.assertEqual(config['step3_best_ranking']['canonical_short_edge'],192)
        bat=(ROOT/'bat/03_face_quality_gate.bat').read_text(encoding='utf-8-sig')
        self.assertIn('scripts\\step3_best_ranking.py',bat)
        self.assertNotIn('scripts\\face_quality_gate.py',bat)
        self.assertIn('03_face_quality_gate.bat',(ROOT/'bat/03_step3_best_ranking.bat').read_text())


if __name__=='__main__':unittest.main()
