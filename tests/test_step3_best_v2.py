"""Semantic regressions: bounded positive quality is not defect evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_step3_best import row,ROOT
from common.best_ranking_v2 import (VERSION,rank_rows,fit_context,score_row,effective_settings,
                                  defect_evidence,choose_round,fatal_reason)


def normal(i=1,kind='formal_video'):
    r=row(i,kind)
    r.update(face_laplacian_canonical_192=100,face_tenengrad_canonical_192=4000,
        left_eye_local_detail=3,right_eye_local_detail=3,mouth_local_detail=3,
        local_face_contrast=80,face_visibility_score=100,face_area_ratio=.14,
        face_brightness_mean=160,highlight_clip_ratio=0,face_shadow_ratio=.001,
        dynamic_range_p95_p5=120,eye_open_min=.4,left_eye_presence=.2,right_eye_presence=.2,
        eye_open_asymmetry=1.1,eye_openness_state='OPEN',exposure_diagnostic_state='NORMAL',
        legacy_eye_presence_valid='true',eye_measurement_availability='MEASURED',yaw=0)
    return r


class V2SemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.settings=effective_settings({})
    def scored(self,**kw):
        a=normal();a.update(kw)
        return rank_rows([a,normal(2)],self.settings)[0] if not kw else score_row(a,self.settings,fit_context([a,normal(2)],self.settings))
    def test_visibility_100_no_obstruction(self):
        self.assertEqual(self.scored()['visibility_obstruction_penalty'],0)
    def test_zero_clipping_zero_penalty(self):
        self.assertEqual(self.scored()['clipping_penalty'],0)
    def test_tiny_clipping_highest_group_stays_zero(self):
        a=normal(50,'supplemental_still');a['highlight_clip_ratio']=.000134316384
        rows=[normal(i,'supplemental_still') for i in range(20)]+[a]
        result=next(r for r in rank_rows(rows,self.settings) if r['frame_id']==a['frame_id'])
        self.assertEqual(result['clipping_penalty'],0)
    def test_open_even_lowest_openness_no_half_eye(self):
        r=self.scored(eye_open_min=.01,eye_openness_state='OPEN',blink_suspected='true')
        self.assertEqual(r['half_eye_penalty'],0)
    def test_presence_valid_and_asymmetry_no_eye_obstruction(self):
        r=self.scored(left_eye_presence=.001,right_eye_presence=.9,eye_open_asymmetry=100)
        self.assertEqual(r['eye_obstruction_penalty'],0)
    def test_normal_pose_asymmetry_abstains(self):
        r=self.scored(legacy_eye_presence_valid='false',left_eye_presence=0,yaw=50)
        self.assertEqual(r['eye_obstruction_penalty'],0)
    def test_frontal_measured_deficit_weak_nonfatal(self):
        r=self.scored(legacy_eye_presence_valid='false',left_eye_presence=0)
        self.assertGreater(r['eye_obstruction_penalty'],0)
        self.assertLessEqual(r['eye_obstruction_penalty'],1.875)
        self.assertEqual(r['fatal_reject'],'false')
    def test_normal_exposure_tiny_shadow_no_penalty(self):
        r=self.scored(face_shadow_ratio=.00635,highlight_clip_ratio=.000134)
        for name in ('clipping','haze','shadow','low_contrast'):self.assertEqual(r[name+'_penalty'],0)
    def test_low_detail_agreement_nonfatal(self):
        r=self.scored(face_laplacian_canonical_192=3,left_eye_local_detail=.1,right_eye_local_detail=.1)
        self.assertGreater(r['blur_penalty'],10);self.assertEqual(r['fatal_reject'],'false')
    def test_one_metric_cannot_create_blur(self):
        self.assertEqual(self.scored(face_laplacian_canonical_192=0)['blur_penalty'],0)
    def test_high_canonical_does_not_hide_two_weak_eyes(self):
        r=self.scored(face_laplacian_canonical_192=10000,left_eye_local_detail=.1,right_eye_local_detail=.1)
        self.assertGreater(r['blur_penalty'],10)
    def test_defect_scores_independent_of_other_images(self):
        a=normal();a.update(highlight_clip_ratio=.04,eye_openness_state='BORDERLINE')
        first=score_row(a,self.settings,fit_context([a],self.settings))
        extreme=normal(999,'supplemental_still');extreme.update({k:100000 for k in ('face_laplacian_canonical_192','face_tenengrad_canonical_192')})
        second=score_row(a,self.settings,fit_context([a,extreme],self.settings))
        self.assertEqual({k:v for k,v in first.items() if k.endswith('_penalty')},
                         {k:v for k,v in second.items() if k.endswith('_penalty')})
    def test_missing_not_measured_zero(self):
        r=self.scored(left_eye_local_detail=None,right_eye_local_detail='',highlight_clip_ratio=None)
        self.assertEqual(r['eye_detail_abs'],'');self.assertEqual(r['clipping_penalty'],'')
        self.assertGreater(r['uncertainty_penalty'],0);self.assertLessEqual(r['uncertainty_penalty'],2.5)
        self.assertEqual(self.scored(highlight_clip_ratio=0)['clipping_penalty'],0)
    def test_common_absolute_domain(self):
        a=normal();b=normal(2,'supplemental_still')
        context=fit_context([a,b],self.settings)
        x,y=[score_row(r,self.settings,context) for r in (a,b)]
        for k in ('sharpness_abs','tenengrad_abs','eye_detail_abs','visibility_abs','absolute_quality_total'):
            self.assertEqual(x[k],y[k])
    def test_normalization_bounded_monotonic(self):
        rs=[normal(i) for i in range(100)]
        for i,r in enumerate(rs):r['face_laplacian_canonical_192']=i
        context=fit_context(rs,self.settings)
        values=[score_row(r,self.settings,context)['sharpness_abs'] for r in rs]
        self.assertEqual(values,sorted(values));self.assertEqual(values[0],0);self.assertEqual(values[-1],1)
    def test_shadow_requires_information_loss(self):
        good=self.scored(face_shadow_ratio=.5)
        bad=self.scored(face_shadow_ratio=.5,face_brightness_mean=20,local_face_contrast=1)
        self.assertEqual(good['shadow_penalty'],0);self.assertGreater(bad['shadow_penalty'],0)
    def test_haze_separate_from_clipping(self):
        r=self.scored(highlight_clip_ratio=0,face_brightness_mean=250,dynamic_range_p95_p5=2,local_face_contrast=1)
        self.assertEqual(r['clipping_penalty'],0);self.assertGreater(r['haze_penalty'],0)
    def test_preference_names_never_change_scores(self):
        context=fit_context([normal()],self.settings)
        a=score_row(normal(),self.settings,context)
        for name in ('Sasha_v03/face_paint.png','Sasha_v49/upward.png','anything.jpg'):
            r=normal();r.update(filename=name,frame_id=name,human_preference='paint_or_upward',review_state='REVIEW_REJECT')
            self.assertEqual(score_row(r,self.settings,context)['best_score'],a['best_score'])
    def test_fatal_predicate_identical_to_v1(self):
        from common.best_ranking_v1 import fatal_reason as previous
        self.assertIs(fatal_reason,previous)
    def test_stored_reference_and_motion_blur_counterexamples(self):
        fixture=json.loads((ROOT/'tests/fixtures/step3_best_v2_counterexamples.json').read_text(encoding='utf-8'))
        rows=fixture['rows'];before=copy.deepcopy(rows)
        # Small regression fixture only; does not calculate current production ranks.
        context=fit_context(rows,self.settings)
        for raw in rows:
            result=score_row(raw,self.settings,context)
            self.assertEqual(result['fatal_reject'],'false')
            if raw['filename'].endswith('652794808_18008722232838431_6335316425841053458_n.jpg'):
                self.assertTrue(all(v==0 for k,v in result.items() if k.endswith('_penalty')))
            if raw['filename'] in ('Sasha_v30/Sasha_v30_010.png','Sasha_v44/Sasha_v44_019.png'):
                self.assertGreater(result['blur_penalty'],0)
            if raw['eye_openness_state']=='OPEN':self.assertEqual(result['half_eye_penalty'],0)
        self.assertEqual(rows,before)


from common.best_ranking import VERSION, choose_round


class ReviewV2Tests(unittest.TestCase):
    def test_default_migrates_stored_v1_without_inference_or_history_reset(self):
        import hashlib
        import step3_best_ranking as entry
        from common.config import load_config
        from common.best_ranking_v1 import rank_rows as rank_v1
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reports=root/'reports';reports.mkdir()
            config=load_config();settings=config['step3_best_ranking']
            config['paths'].update(reports_dir=str(reports),manifests_dir=str(root/'manifests'),raw_frames_dir=str(root/'raw'))
            effective=effective_settings(settings,config);raw=[normal(i) for i in range(5)]
            for r in raw:r['diagnostic_config_sha256']=effective['_diagnostic_sha256']
            old=rank_v1(raw,settings);ranking=reports/'step3_best_ranking.csv'
            entry.write_rows(ranking,old);before=ranking.read_bytes()
            old_settings=dict(settings,ranking_version='best_rank_v1')
            (reports/'step3_best_ranking_summary.json').write_text(json.dumps(dict(version='best_rank_v1',input_snapshot={'fixture':'1'},settings=old_settings,ranking_sha256=hashlib.sha256(before).hexdigest())))
            history={'version':1,'rounds':[{'review_round':1,'publication_status':'COMPLETE'},{'review_round':2,'publication_status':'COMPLETE'}],
                     'records':[dict(old[i],shown_to_maru=True,review_state='REVIEW_REJECT',review_round=i+1,review_round_rank=1) for i in range(2)]}
            hp=reports/'step3_best_review_history.json';hp.write_text(json.dumps(history));history_before=hp.read_bytes()
            with patch.object(entry,'load_config',return_value=config),patch.object(entry,'load_inventory',return_value=(raw,{'fixture':'1'})),patch('common.best_measurement.measure_rows',side_effect=AssertionError('No inference permitted')):
                self.assertEqual(entry.main([]),0)
            self.assertEqual(hp.read_bytes(),history_before)
            self.assertFalse((reports/'step3_best_review').exists())
            self.assertEqual(json.loads((reports/'step3_best_ranking_summary.json').read_text())['version'],VERSION)
            archived=list((reports/'step3_best_history').glob('best_rank_v1_*/step3_best_ranking.csv'))
            self.assertEqual(len(archived),1);self.assertEqual(archived[0].read_bytes(),before)

    def candidates(self,stills=20):
        rows=[]
        for i in range(100+stills):
            r=normal(i,'formal_video' if i<100 else 'supplemental_still')
            r.update(ranking_version=VERSION,ranking_eligible='true',global_rank=i+1)
            rows.append(r)
        return rows
    def test_ten_stills_and_video_cap(self):
        selected,info=choose_round(self.candidates(),[])
        self.assertEqual(len(selected),45);self.assertGreaterEqual(info['supplemental_selected'],10)
        self.assertLessEqual(max(info['video_counts'].values()),4)
    def test_still_guarantee_is_not_exact_quota(self):
        rows=self.candidates(60)
        for r in rows:
            if r['input_kind']=='supplemental_still':r['global_rank']-=100
            else:r['global_rank']+=100
        selected,info=choose_round(rows,[])
        self.assertEqual(info['supplemental_selected'],45)
    def test_shortage_uses_all_remaining_stills(self):
        selected,info=choose_round(self.candidates(3),[])
        self.assertEqual(info['supplemental_selected'],3);self.assertEqual(len(selected),45)
    def test_round3_excludes_both_rounds_rejects_preserved(self):
        rows=self.candidates(20)
        history=[dict(r,review_round=1 if i<20 else 2,shown_to_maru=True,review_state='REVIEW_REJECT',ranking_version=VERSION) for i,r in enumerate(rows[:40])]
        before=copy.deepcopy(history);selected,info=choose_round(rows,history)
        self.assertFalse({r['frame_id'] for r in selected}&{r['frame_id'] for r in history})
        self.assertEqual(history,before);self.assertGreaterEqual(info['supplemental_selected'],10)
    def test_v1_round3_blocked_before_inventory(self):
        import step3_best_ranking as entry
        from common.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=load_config()
            config['paths'].update(reports_dir=str(root/'reports'),manifests_dir=str(root/'manifests'),raw_frames_dir=str(root/'raw'))
            (root/'reports').mkdir();(root/'reports/step3_best_ranking_summary.json').write_text(json.dumps({'version':'best_rank_v1'}))
            with patch.object(entry,'load_config',return_value=config),patch.object(entry,'load_inventory',side_effect=AssertionError('Must not discover production inputs')):
                with self.assertRaisesRegex(ValueError,'best_rank_v1 is disabled'):entry.main(['--from-existing','--review-round','3'])


if __name__=='__main__':unittest.main()
