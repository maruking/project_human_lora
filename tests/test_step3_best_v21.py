"""Generic quality invariants; no real inference or production ranking."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_step3_best import ROOT,row
from common.best_ranking import VERSION,choose_round,rank_rows
from common.best_ranking_v21 import effective_settings,fit_context,score_row
from common.best_ranking_v2 import score_row as old_score
from common.best_review import HISTORY_NAME,read_history,materialize


def clean(i=1):
    r=row(i)
    r.update(face_laplacian_canonical_192=100,face_tenengrad_canonical_192=4000,
             left_eye_local_detail=3,right_eye_local_detail=3,mouth_local_detail=3,
             local_face_contrast=80,face_visibility_score=100,face_area_ratio=.14,
             face_brightness_mean=160,highlight_clip_ratio=0,face_shadow_ratio=.001,
             dynamic_range_p95_p5=120,left_eye_openness=.4,right_eye_openness=.4,
             eye_open_min=.4,eye_open_asymmetry=1,left_eye_presence=.2,right_eye_presence=.2,
             eye_openness_state='OPEN',exposure_diagnostic_state='NORMAL',landmark_status='MEASURED',
             left_eye_roi_status='MEASURED',right_eye_roi_status='MEASURED',
             left_eye_roi_width=180,right_eye_roi_width=170,
             legacy_eye_presence_valid='true',eye_measurement_availability='MEASURED',yaw=0)
    return r


class V21QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.settings=effective_settings({})
    def score(self,**changes):
        r=clean();r.update(changes)
        return score_row(r,self.settings,fit_context([clean(),r],self.settings))

    def test_both_open_no_half_or_closed(self):
        r=self.score()
        self.assertEqual(r['eye_closed_penalty'],0);self.assertEqual(r['eye_half_open_penalty'],0)
        self.assertEqual(r['eye_quality_score'],1)

    def test_one_half_open_mean_cannot_hide_weaker_eye(self):
        a=self.score(left_eye_openness=.2,right_eye_openness=.6,eye_openness_state='BORDERLINE')
        b=self.score(left_eye_openness=.29,right_eye_openness=.6,eye_openness_state='BORDERLINE')
        self.assertGreater(a['eye_half_open_penalty'],b['eye_half_open_penalty'])
        self.assertLess(a['eye_quality_score'],b['eye_quality_score'])
        self.assertLess(a['best_score'],self.score()['best_score']-5)

    def test_closed_stronger_than_half_without_hard_rejection(self):
        half=self.score(left_eye_openness=.2,eye_openness_state='HALF_OPEN')
        closed=self.score(left_eye_openness=.05,eye_openness_state='CLOSED_OR_BLINK')
        self.assertGreater(closed['eye_closed_penalty'],half['eye_half_open_penalty'])
        self.assertLess(closed['eye_quality_score'],half['eye_quality_score'])
        self.assertEqual(closed['fatal_reject'],'false')

    def test_pose_expected_missing_eye_is_failure_not_obstruction(self):
        r=self.score(left_eye_local_detail='',left_eye_roi_status='UNAVAILABLE')
        self.assertEqual(r['left_eye_local_detail'],'')
        self.assertEqual(r['eye_measurement_failure'],'true')
        self.assertGreater(r['eye_measurement_penalty'],0)
        self.assertEqual(r['eye_obstruction_penalty'],0)

    def test_profile_far_eye_not_a_defect(self):
        r=self.score(yaw=60,right_eye_roi_width=70,right_eye_local_detail='',
                     right_eye_roi_status='UNAVAILABLE',right_eye_presence=0,right_eye_openness=.02,
                     eye_openness_state='BORDERLINE',eye_measurement_availability='PARTIAL')
        self.assertEqual(r['expected_eye_sides'],'left')
        self.assertEqual(r['eye_measurement_failure'],'false')
        self.assertEqual(r['eye_obstruction_penalty'],0)
        self.assertEqual(r['eye_closed_penalty'],0)
        self.assertEqual(r['eye_half_open_penalty'],0)

    def test_profile_side_unknown_abstains(self):
        r=self.score(yaw=-60,left_eye_roi_width='',right_eye_roi_width='',left_eye_presence=0)
        self.assertEqual(r['pose_eye_expectation'],'PROFILE_SIDE_UNRESOLVED_ABSTAIN')
        self.assertEqual(r['eye_obstruction_penalty'],'')

    def test_legacy_presence_alone_cannot_penalize(self):
        r=self.score(left_eye_presence=0,right_eye_presence=0,legacy_eye_presence_valid='false')
        self.assertEqual(r['eye_obstruction_penalty'],0)
        self.assertEqual(r['eye_measurement_failure'],'false')

    def test_same_eye_agreement_penalizes_open_obstructed_eye(self):
        r=self.score(left_eye_presence=0,left_eye_local_detail=.1)
        self.assertGreater(r['eye_obstruction_penalty'],5)
        self.assertEqual(r['eye_half_open_penalty'],0)
        self.assertLess(r['eye_quality_score'],.2)
        self.assertEqual(r['fatal_reject'],'false')

    def test_other_eye_detail_does_not_falsely_corroborate_presence(self):
        r=self.score(left_eye_presence=0,right_eye_local_detail=.1)
        self.assertEqual(r['eye_obstruction_penalty'],0)

    def test_blur_requires_two_actual_detail_deficits(self):
        self.assertEqual(self.score(face_laplacian_canonical_192=1)['blur_penalty'],0)
        self.assertEqual(self.score(left_eye_local_detail=.1)['blur_penalty'],0)
        self.assertGreater(self.score(face_laplacian_canonical_192=1,left_eye_local_detail=.1)['blur_penalty'],10)

    def test_strong_details_cannot_blur_from_pool_position(self):
        r=clean();others=[clean(i+3) for i in range(20)]
        for other in others:
            other.update(face_laplacian_canonical_192=10000,left_eye_local_detail=100,right_eye_local_detail=100)
        result=score_row(r,self.settings,fit_context([r,*others],self.settings))
        self.assertEqual(result['blur_penalty'],0)

    def test_tiny_highlights_no_clipping_penalty(self):
        self.assertEqual(self.score(highlight_clip_ratio=.000134)['clipping_penalty'],0)

    def test_dark_with_preserved_information_abstains(self):
        self.assertEqual(self.score(face_brightness_mean=20,face_shadow_ratio=.8)['dark_exposure_penalty'],0)

    def test_dark_information_loss_increases_penalty(self):
        r=self.score(face_brightness_mean=20,dynamic_range_p95_p5=4,local_face_contrast=2)
        self.assertGreater(r['dark_exposure_penalty'],5)
        self.assertEqual(r['shadow_penalty'],r['dark_exposure_penalty'])
        self.assertEqual(r['fatal_reject'],'false')

    def test_haze_distinct_from_clipping(self):
        r=self.score(face_brightness_mean=250,dynamic_range_p95_p5=4,local_face_contrast=2)
        self.assertGreater(r['haze_penalty'],0)
        self.assertEqual(r['clipping_penalty'],0)

    def test_missing_not_numeric_zero(self):
        missing=self.score(left_eye_local_detail=None)
        measured=self.score(left_eye_local_detail=0)
        self.assertIsNone(missing['left_eye_local_detail'])
        self.assertEqual(missing['eye_measurement_failure'],'true')
        self.assertEqual(measured['eye_measurement_failure'],'false')
        self.assertGreater(missing['eye_measurement_penalty'],measured['eye_measurement_penalty'])

    def test_review_and_source_metadata_not_scoring_features(self):
        r=clean();context=fit_context([r],self.settings);baseline=score_row(r,self.settings,context)
        changed=dict(r,frame_id='someone/other.jpg',filename='random.jpg',video_id='another-video',source_id='other',
                     human_reject=True,review_state='REVIEW_REJECT',review_round=3,review_reason='any preference',
                     global_rank=999,review_folder='old/review_reject',previous_rank=1)
        result=score_row(changed,self.settings,context)
        for k in ('best_score','absolute_quality_total','relative_quality_bonus','penalty_total'):
            self.assertEqual(result[k],baseline[k])

    def test_production_scoring_ast_has_no_source_or_review_conditions(self):
        forbidden={'filename','video_id','source_id','frame_id','human_reject','review_state','review_round',
                   'review_reason','global_rank','previous_rank','review_folder'}
        for name in ('best_ranking.py','best_eye_quality.py'):
            source=(ROOT/'scripts/common'/name).read_text(encoding='utf-8')
            self.assertNotIn('Sasha',source)
            tree=ast.parse(source)
            functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)
                       and n.name in ('score_row','defect_evidence','eye_quality')]
            for fn in functions:
                for node in ast.walk(fn):
                    if isinstance(node,ast.Subscript) and isinstance(node.slice,ast.Constant):
                        self.assertNotIn(node.slice.value,forbidden)
                    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='get' and node.args:
                        if isinstance(node.args[0],ast.Constant):self.assertNotIn(node.args[0].value,forbidden)

    def test_total_is_auditable_without_alias_double_counting(self):
        r=self.score(left_eye_openness=.2,eye_openness_state='BORDERLINE',face_brightness_mean=20,
                     local_face_contrast=2,dynamic_range_p95_p5=4)
        self.assertAlmostEqual(r['penalty_total'],sum(v for k,v in r.items() if k.startswith('deduction_')))
        self.assertAlmostEqual(r['best_score'],r['absolute_quality_total']+r['relative_quality_bonus']-r['penalty_total'])

    def test_clean_absolute_quality_components_retained(self):
        raw=clean();context=fit_context([raw],self.settings)
        old=old_score(raw,self.settings,context);new=score_row(raw,self.settings,context)
        for field in ('sharpness_abs','tenengrad_abs','mouth_detail_abs','contrast_abs','visibility_abs',
                      'absolute_quality_total','relative_quality_bonus'):
            self.assertEqual(new[field],old[field])

    def test_fatal_predicate_identity_preserved(self):
        from common.best_ranking import fatal_reason
        from common.best_ranking_v1 import fatal_reason as old
        self.assertIs(fatal_reason,old)

    def test_stored_counterexamples_are_features_only_not_blacklists(self):
        fixture=json.loads((ROOT/'tests/fixtures/step3_best_v21_counterexamples.json').read_text(encoding='utf-8'))
        originals=copy.deepcopy(fixture['rows']);context=fit_context(originals,self.settings)
        for i,raw in enumerate(originals):
            result=score_row(raw,self.settings,context)
            renamed=dict(raw,frame_id=f'anonymous/{i}.jpg',filename=f'{i}.jpg',video_id='anonymous',
                         source_id='arbitrary',review_state='PENDING',review_round=99,
                         human_reject=False,review_reason='different reason')
            second=score_row(renamed,self.settings,context)
            self.assertEqual(result['best_score'],second['best_score'])
            self.assertEqual(result['fatal_reject'],'false')
            self.assertAlmostEqual(result['penalty_total'],sum(v for k,v in result.items() if k.startswith('deduction_')))
        self.assertEqual(originals,fixture['rows'])


class V21MigrationTests(unittest.TestCase):
    def test_v1_v2_shown_do_not_exclude_v21_round1(self):
        rows=[dict(clean(i),ranking_version=VERSION,ranking_eligible='true',global_rank=i+1) for i in range(9)]
        histories=[dict(r,ranking_version=v,shown_to_maru=True,review_round=1,review_state='REVIEW_REJECT')
                   for v in ('best_rank_v1','best_rank_v2') for r in rows]
        selected,_=choose_round(rows,histories,size=3,min_stills=0)
        self.assertEqual([r['frame_id'] for r in selected],[r['frame_id'] for r in rows[:3]])

    def test_v21_publication_does_not_change_v1_v2_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'raw';history=root/HISTORY_NAME;rows=[]
            for i in range(4):
                r=clean(i);p=source/r['filename'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(str(i).encode())
                r['image_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();rows.append(r)
            rows=rank_rows(rows,{})
            old={v:dict(rounds=[dict(review_round=1,publication_status='COMPLETE')],
                        records=[dict(rows[0],ranking_version=v,shown_to_maru=True,review_round=1,
                                      review_state='REVIEW_REJECT')]) for v in ('best_rank_v1','best_rank_v2')}
            history.write_text(json.dumps(dict(version=2,review_history=old)),encoding='utf-8')
            before=copy.deepcopy(old)
            h=materialize(rows,source,root/'reviews',history,1,dict(review_size=2,min_supplemental=0))
            for v in before:self.assertEqual(h['review_history'][v],before[v])
            self.assertEqual(h['records'][0]['frame_id'],rows[0]['frame_id'])
            self.assertTrue((root/'reviews'/VERSION/'round_01/candidates').is_dir())

    def test_stored_v2_migrates_without_inference_history_or_copies(self):
        import step3_best_ranking as entry
        from common.config import load_config
        from common.best_ranking_v2 import rank_rows as rank_v2
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reports=root/'reports';reports.mkdir();config=load_config()
            config['paths'].update(reports_dir=str(reports),raw_frames_dir=str(root/'raw'),manifests_dir=str(root/'manifests'))
            settings=config['step3_best_ranking'];effective=effective_settings(settings,config)
            raw=[clean(i) for i in range(5)]
            for r in raw:r['diagnostic_config_sha256']=effective['_diagnostic_sha256']
            old=rank_v2(raw,settings);ranking=reports/'step3_best_ranking.csv'
            entry.write_rows(ranking,old);saved=ranking.read_bytes()
            (reports/'step3_best_ranking_summary.json').write_text(json.dumps(dict(version='best_rank_v2',
                 input_snapshot={'fixture':1},settings=dict(settings,ranking_version='best_rank_v2'),
                 ranking_sha256=hashlib.sha256(saved).hexdigest())))
            history=reports/HISTORY_NAME
            history.write_text(json.dumps(dict(version=2,review_history={'best_rank_v2':dict(
                 rounds=[dict(review_round=1,publication_status='COMPLETE')],
                 records=[dict(old[0],shown_to_maru=True,review_state='REVIEW_REJECT',review_round=1)])})))
            old_history=history.read_bytes()
            with patch.object(entry,'load_config',return_value=config),patch.object(entry,'load_inventory',return_value=(raw,{'fixture':1})),patch('common.best_measurement.measure_rows',side_effect=AssertionError('Inference forbidden')):
                self.assertEqual(entry.main([]),0)
            self.assertEqual(history.read_bytes(),old_history)
            self.assertFalse((reports/'step3_best_review').exists())
            summary=json.loads((reports/'step3_best_ranking_summary.json').read_text())
            self.assertEqual(summary['next_review_round'],1);self.assertEqual(summary['shown_count'],0)
            self.assertEqual(summary['historical_review_counts']['best_rank_v2']['review_reject'],1)
            archived=list((reports/'step3_best_history').glob('best_rank_v2_*/step3_best_ranking.csv'))
            self.assertEqual(archived[0].read_bytes(),saved)


if __name__=='__main__':unittest.main()
