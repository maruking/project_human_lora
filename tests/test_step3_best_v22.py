"""Synthetic general properties, no production inference/ranking or candidate copies."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from test_step3_best import ROOT
from test_step3_best_v21 import clean
from common.best_ranking import VERSION, effective_settings, fit_context, score_row, rank_rows, choose_round
from common.best_review import HISTORY_NAME, materialize, feedback, read_history


def good(i=1):
    r=clean(i)
    r.update(left_eye_roi_height=90,right_eye_roi_height=90,face_short_edge_px=300)
    return r


class V22QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings=effective_settings({})
        cls.context=fit_context([good()],cls.settings)

    def score(self,**changes):
        r=good();r.update(changes)
        return score_row(r,self.settings,self.context)

    def test_open_half_closed_order_and_no_hard_reject(self):
        a=self.score();b=self.score(left_eye_openness=.2,eye_openness_state='BORDERLINE')
        c=self.score(left_eye_openness=.05,eye_openness_state='CLOSED')
        self.assertEqual(a['eye_quality_factor'],1)
        self.assertLess(b['eye_quality_factor'],a['eye_quality_factor'])
        self.assertLess(c['eye_quality_factor'],b['eye_quality_factor'])
        self.assertLess(c['best_score'],b['best_score'])
        self.assertEqual(c['ranking_eligible'],'true')

    def test_bad_eye_not_hidden_by_mean_or_other_positive_components(self):
        bad=self.score(left_eye_openness=.2,right_eye_openness=.6,eye_openness_state='BORDERLINE')
        boosted=self.score(left_eye_openness=.2,right_eye_openness=.6,eye_openness_state='BORDERLINE',
                           face_laplacian_canonical_192=1e6,face_tenengrad_canonical_192=1e6,
                           local_face_contrast=200,face_short_edge_px=2000)
        self.assertEqual(bad['eye_quality_factor'],boosted['eye_quality_factor'])
        self.assertLess(boosted['critical_face_quality'],1)
        self.assertLess(boosted['best_score'],self.score()['best_score'])

    def test_presence_alone_not_obstruction(self):
        r=self.score(left_eye_presence=0)
        self.assertEqual(r['left_eye_obstruction_concern'],0)

    def test_correlated_same_eye_evidence_lowers_quality(self):
        a=self.score(left_eye_presence=0,left_eye_local_detail=.1)
        b=self.score(left_eye_presence=0,right_eye_local_detail=.1)
        self.assertGreater(a['left_eye_obstruction_concern'],0)
        self.assertEqual(b['left_eye_obstruction_concern'],0)
        self.assertLess(a['eye_quality_factor'],b['eye_quality_factor'])

    def test_missing_expected_eye_not_zero_or_perfect_or_occlusion(self):
        missing=self.score(left_eye_local_detail='',left_eye_roi_status='UNAVAILABLE')
        zero=self.score(left_eye_local_detail=0)
        self.assertEqual(missing['left_eye_local_detail'],'')
        self.assertEqual(missing['left_eye_measurement_status'],'ROI_INVALID')
        self.assertLess(missing['measurement_reliability_factor'],1)
        self.assertEqual(missing['left_eye_obstruction_concern'],'')
        self.assertEqual(zero['left_eye_measurement_status'],'VALID')
        self.assertEqual(zero['measurement_reliability_factor'],1)

    def test_landmark_failure_and_inconsistent_roi_are_reliability_only(self):
        for change,status in [({'left_eye_landmark_status':'UNAVAILABLE'},'LANDMARK_MISSING'),
                              ({'left_eye_landmark_inside_roi':'false'},'INCONSISTENT'),
                              ({'left_eye_openness':.2,'eye_openness_state':'OPEN'},'INCONSISTENT')]:
            r=self.score(**change)
            self.assertEqual(r['left_eye_measurement_status'],status)
            self.assertLess(r['eye_measurement_reliability'],1)
            self.assertEqual(r['left_eye_obstruction_concern'],'')

    def test_profile_far_side_missing_is_not_failure(self):
        r=self.score(yaw=60,right_eye_roi_width=50,right_eye_roi_status='UNAVAILABLE',
                     right_eye_local_detail='',right_eye_openness=.02)
        self.assertEqual(r['right_eye_measurement_status'],'NOT_EXPECTED_BY_POSE')
        self.assertEqual(r['eye_measurement_reliability'],1)
        self.assertEqual(r['measurement_reliability_factor'],1)

    def test_high_global_and_local_detail_healthy(self):
        r=self.score()
        self.assertEqual(r['global_detail_quality'],1)
        self.assertEqual(r['local_detail_quality'],1)
        self.assertEqual(r['blur_quality_factor'],1)

    def test_both_weak_global_not_restored_by_one_local_edge(self):
        a=self.score(face_laplacian_canonical_192=1,face_tenengrad_canonical_192=40)
        b=self.score(face_laplacian_canonical_192=1,face_tenengrad_canonical_192=40,left_eye_local_detail=100)
        self.assertLess(a['global_detail_quality'],.02)
        self.assertLess(b['blur_quality_factor'],.02)
        self.assertEqual(a['blur_quality_factor'],b['blur_quality_factor'])

    def test_single_weak_local_roi_not_severe_blur(self):
        self.assertEqual(self.score(left_eye_local_detail=.01)['blur_quality_factor'],1)

    def test_tiny_clip_is_not_defect(self):
        self.assertEqual(self.score(highlight_clip_ratio=.0001)['exposure_quality_factor'],1)

    def test_dark_good_information_preserved(self):
        self.assertEqual(self.score(face_brightness_mean=20,face_shadow_ratio=.8)['exposure_quality_factor'],1)

    def test_dark_low_information_reduces_quality(self):
        r=self.score(face_brightness_mean=20,local_face_contrast=2,dynamic_range_p95_p5=4)
        self.assertLess(r['exposure_quality_factor'],1)
        self.assertLess(r['critical_face_quality'],1)

    def test_bright_information_loss_haze_is_not_clipping(self):
        r=self.score(face_brightness_mean=250,local_face_contrast=2,dynamic_range_p95_p5=4)
        self.assertLess(r['exposure_quality_factor'],1)
        self.assertEqual(r['v21_evidence_deduction_clipping'],0)
        self.assertGreater(r['v21_evidence_deduction_haze'],0)

    def test_face_size_saturates_at_existing_evaluability_reference(self):
        self.assertEqual(self.score(face_short_edge_px=300)['contribution_face_size'],
                         self.score(face_short_edge_px=1500)['contribution_face_size'])

    def test_lighting_asymmetry_is_not_visibility_obstruction(self):
        r=self.score(face_visibility_score=75,face_visibility_signals='asymmetric_eye_brightness')
        self.assertEqual(r['visibility_quality_score'],100)
        self.assertEqual(r['visibility_obstruction_penalty'],0)

    def test_profile_natural_eye_continuous_not_half_state_jump(self):
        r=self.score(yaw=60,left_eye_openness=.271,eye_openness_state='BORDERLINE')
        self.assertGreater(r['eye_quality_factor'],.9)
        self.assertLess(r['eye_quality_factor'],1)

    def test_contrast_healthy_information_saturates_not_harsh_advantage(self):
        self.assertEqual(self.score(local_face_contrast=30)['contribution_contrast'],
                         self.score(local_face_contrast=200)['contribution_contrast'])

    def test_each_factor_is_bounded_and_score_is_auditable(self):
        r=self.score(left_eye_openness=.2,eye_openness_state='BORDERLINE')
        for k in ('eye_quality_factor','blur_quality_factor','exposure_quality_factor',
                  'measurement_reliability_factor','critical_face_quality'):
            self.assertTrue(0<=r[k]<=1)
        self.assertAlmostEqual(r['best_score'],r['base_quality']*r['critical_face_quality']-r['penalty_total'])
        self.assertEqual(r['eye_half_open_penalty'],0)
        self.assertEqual(r['eye_quality_positive_credit_loss'],0)
        self.assertEqual(r['penalty_total'],sum(v for k,v in r.items() if k.startswith('deduction_')))

    def test_names_and_human_review_are_not_score_features(self):
        r=good();a=score_row(r,self.settings,self.context)
        for change in ({'filename':'other.jpg','video_id':'other','source_id':'other','frame_id':'other'},
                       {'human_reject':True,'review_state':'REVIEW_REJECT','review_round':99,'global_rank':1}):
            b=score_row(dict(r,**change),self.settings,self.context)
            self.assertEqual(a['best_score'],b['best_score'])

    def test_scoring_ast_has_no_named_or_history_branches(self):
        forbidden={'filename','frame_id','video_id','source_id','human_reject','review_state','review_round','global_rank'}
        for name in ('best_ranking_v22.py','best_quality_v22.py'):
            source=(ROOT/'scripts/common'/name).read_text();self.assertNotIn('Sasha',source)
            for fn in ast.walk(ast.parse(source)):
                if isinstance(fn,ast.FunctionDef) and fn.name in ('score_row','eye_factors','detail_factors'):
                    for node in ast.walk(fn):
                        if isinstance(node,ast.Subscript) and isinstance(node.slice,ast.Constant):
                            self.assertNotIn(node.slice.value,forbidden)
                        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='get' and node.args and isinstance(node.args[0],ast.Constant):
                            self.assertNotIn(node.args[0].value,forbidden)


class V22ReviewTests(unittest.TestCase):
    def test_v21_stored_migration_preserves_old_report_and_history_without_inference(self):
        import step3_best_ranking as entry
        from common.config import load_config
        from common.best_ranking_v21 import rank_rows as rank_previous
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reports=root/'reports';reports.mkdir();config=load_config()
            config['paths'].update(reports_dir=str(reports),raw_frames_dir=str(root/'raw'),manifests_dir=str(root/'manifests'))
            settings=config['step3_best_ranking'];effective=effective_settings(settings,config)
            raw=[good(i) for i in range(3)]
            for r in raw:r['diagnostic_config_sha256']=effective['_diagnostic_sha256']
            old=rank_previous(raw,settings);ranking=reports/'step3_best_ranking.csv'
            entry.write_rows(ranking,old);saved=ranking.read_bytes()
            (reports/'step3_best_ranking_summary.json').write_text(json.dumps(dict(version='best_rank_v2.1',
                input_snapshot={'fixture':1},settings=dict(settings,ranking_version='best_rank_v2.1'),
                ranking_sha256=hashlib.sha256(saved).hexdigest())))
            history=reports/HISTORY_NAME
            history.write_text(json.dumps(dict(version=2,review_history={'best_rank_v2.1':dict(rounds=[],
                records=[dict(old[0],shown_to_maru=True,review_state='REVIEW_REJECT',review_round=1)])})))
            saved_history=history.read_bytes()
            with patch.object(entry,'load_config',return_value=config),patch.object(entry,'load_inventory',return_value=(raw,{'fixture':1})),patch('common.best_measurement.measure_rows',side_effect=AssertionError('No inference')):
                self.assertEqual(entry.main([]),0)
            self.assertEqual(history.read_bytes(),saved_history)
            summary=json.loads((reports/'step3_best_ranking_summary.json').read_text())
            self.assertEqual(summary['next_review_round'],1);self.assertEqual(summary['version'],VERSION)
            self.assertFalse((reports/'step3_best_review').exists())
            self.assertEqual(list((reports/'step3_best_history').glob('best_rank_v2.1_*/step3_best_ranking.csv'))[0].read_bytes(),saved)

    def test_old_versions_do_not_exclude_new_round_and_current_rounds_do(self):
        rows=[dict(good(i),ranking_version=VERSION,ranking_eligible='true',global_rank=i+1) for i in range(6)]
        old=[dict(r,ranking_version=v,review_round=1,shown_to_maru=True,review_state='REVIEW_REJECT')
             for v in ('best_rank_v1','best_rank_v2','best_rank_v2.1') for r in rows]
        selected,_=choose_round(rows,old,size=2,min_stills=0,round_number=1)
        self.assertEqual(selected,rows[:2])
        history=[dict(r,review_round=1,shown_to_maru=True) for r in selected]
        second,_=choose_round(rows,history,size=2,min_stills=0,round_number=2)
        self.assertEqual(second,rows[2:4])
        history.extend(dict(r,review_round=2,shown_to_maru=True) for r in second)
        third,_=choose_round(rows,history,size=2,min_stills=0,round_number=3)
        self.assertEqual(third,rows[4:6])

    def test_duplicate_review_copies_reconcile_without_source_or_history_loss(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'raw';r=good()
            path=src/r['filename'];path.parent.mkdir(parents=True);path.write_bytes(b'source')
            r['image_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            rows=rank_rows([r],{});hist=root/HISTORY_NAME;review=root/'review'
            old={'best_rank_v2.1':{'rounds':[],'records':[dict(rows[0],ranking_version='best_rank_v2.1',review_state='REVIEW_REJECT')]}}
            hist.write_text(json.dumps({'version':2,'review_history':old}))
            materialize(rows,src,review,hist,1,{'review_size':1,'min_supplemental':0})
            folder=review/VERSION/'round_01';candidate=folder/'candidates'/r['filename'];reject=folder/'review_reject'/r['filename']
            reject.parent.mkdir(parents=True);shutil.copy2(candidate,reject)
            h,rs=feedback(review,hist)
            self.assertEqual(len(rs),1);self.assertFalse(candidate.exists());self.assertTrue(reject.exists())
            self.assertEqual(path.read_bytes(),b'source');self.assertEqual(h['review_history']['best_rank_v2.1'],old['best_rank_v2.1'])
            feedback(review,hist) # Rerunnable.
            self.assertFalse(candidate.exists())


if __name__=='__main__':unittest.main()
