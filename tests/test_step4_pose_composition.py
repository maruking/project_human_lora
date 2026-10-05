"""Synthetic only; no production image/model execution."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common.config import load_config, validate_config
from common.pose_composition import (settings_from, describe, describe_rows, summarize,
                                     yaw_bin, pitch_bin, scale_bin, VERSION)
from step4_pose_composition import load_input, publish


def fixture(identifier='frame', kind='formal_video', eligible=True):
    return dict(frame_id=identifier, filename=identifier+'.png', input_kind=kind,
                source_id='source:'+identifier if kind=='supplemental_still' else 'video',
                video_id='' if kind=='supplemental_still' else 'video', temporal_index='1',
                dataset_generation_id='g'*64, image_sha256='a'*64,
                ranking_version='best_rank_v2.2', ranking_eligible=str(eligible).lower(),
                best_score='81.123456789', global_rank='1' if eligible else '',
                fatal_reject_reason='' if eligible else 'no_face',
                yaw='0', pitch='0', roll='0', pose_status='MEASURED',
                width='1000', height='1000', face_bbox='100,100,200,200',
                face_bbox_x='100', face_bbox_y='100', face_bbox_width='200', face_bbox_height='200',
                face_area_ratio='0.04', face_short_edge_px='200')


class Step4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config(ROOT/'config/config.example.yaml')
        cls.settings = settings_from(cls.config)

    def test_full_rows_stills_fatal_and_duplicate_pixels_preserved(self):
        rows = [fixture('a'), fixture('b', 'supplemental_still'), fixture('fatal', eligible=False)]
        rows[1]['image_sha256'] = rows[0]['image_sha256']  # identical pixels are not deduplicated
        result = describe_rows(rows, self.settings)
        self.assertEqual([r['frame_id'] for r in result], ['a', 'b', 'fatal'])
        self.assertEqual(result[1]['input_kind'], 'supplemental_still')
        self.assertEqual(result[2]['step4_status'], 'NOT_APPLICABLE_STEP3_FATAL')
        self.assertEqual(result[2]['step3_fatal_reason'], 'no_face')
        self.assertEqual(rows[0]['ranking_eligible'], result[0]['ranking_eligible'])

    def test_yaw_boundaries_and_sign(self):
        for value, expected in [(15,'FRONTAL'),(-15,'FRONTAL'),(15.001,'THREE_QUARTER_RIGHT'),
                                (-15.001,'THREE_QUARTER_LEFT'),(41.999,'THREE_QUARTER_RIGHT'),
                                (42,'PROFILE_RIGHT'),(-42,'PROFILE_LEFT')]:
            with self.subTest(value=value):
                self.assertEqual(yaw_bin(value,self.settings),expected)

    def test_pitch_boundaries(self):
        for value, expected in [(-20,'LEVEL'),(20,'LEVEL'),(-20.001,'LOOKING_UP'),(20.001,'LOOKING_DOWN')]:
            self.assertEqual(pitch_bin(value,self.settings),expected)

    def test_area_boundaries(self):
        for value, expected in [(0.12,'CLOSE_UP'),(0.11999,'UPPER_BODY'),(0.04,'UPPER_BODY'),(0.03999,'FULL_BODY')]:
            self.assertEqual(scale_bin(value,self.settings),expected)

    def test_face_height_does_not_classify(self):
        a=fixture();b=fixture()
        b.update(face_bbox='100,100,100,400',face_bbox_width='100',face_bbox_height='400',face_short_edge_px='100')
        ra,rb=describe(a,self.settings),describe(b,self.settings)
        self.assertEqual(ra['face_scale_bin'],rb['face_scale_bin'])
        self.assertEqual(ra['face_height_ratio'],.2)
        self.assertEqual(rb['face_height_ratio'],.4)

    def test_raw_angles_score_and_extreme_pose_not_rejected(self):
        row=fixture();row.update(yaw='-80.12345',pitch='-89.987',roll='95.432')
        result=describe(row,self.settings)
        for key in ('yaw','pitch','roll','best_score','global_rank','ranking_eligible'):
            self.assertEqual(result[key],row[key])
        self.assertEqual(result['step4_status'],'MEASURED')
        self.assertEqual(result['pose_bin'],'PROFILE_LEFT')
        self.assertEqual(result['vertical_pose'],'LOOKING_UP')
        self.assertEqual(result['roll_state'],'NOT_CLASSIFIED')

    def test_review_has_no_effect_on_descriptors(self):
        a=fixture();b=copy.deepcopy(a)
        a.update(review_state='PENDING',review_round='1',historical_review_reject='false')
        b.update(review_state='REVIEW_REJECT',review_round='3',historical_review_reject='true')
        ra,rb=describe(a,self.settings),describe(b,self.settings)
        for key in set(ra)|set(rb):
            if key not in ('review_state','review_round','historical_review_reject'):
                self.assertEqual(ra.get(key),rb.get(key),key)

    def test_missing_yaw_is_not_zero_or_frontal(self):
        row=fixture();row['yaw']=''
        result=describe(row,self.settings)
        self.assertEqual(result['yaw'],'')
        self.assertEqual(result['pose_bin'],'NOT_EVALUABLE')
        self.assertEqual(result['step4_status'],'NOT_EVALUABLE')
        self.assertEqual(result['vertical_pose'],'LEVEL')

    def test_missing_pose_status_is_not_measured(self):
        row=fixture();row['pose_status']='UNAVAILABLE'
        result=describe(row,self.settings)
        self.assertEqual(result['pose_bin'],'NOT_EVALUABLE')
        self.assertEqual(result['vertical_pose'],'NOT_EVALUABLE')

    def test_missing_geometry_stays_blank(self):
        row=fixture()
        for key in ('face_bbox','face_bbox_x','face_bbox_y','face_bbox_width','face_bbox_height'):
            row[key]=''
        result=describe(row,self.settings)
        self.assertEqual(result['face_center_x_norm'],'')
        self.assertEqual(result['face_scale_bin'],'NOT_EVALUABLE')

    def test_center_edge_and_zero_coordinate_valid(self):
        row=fixture();row.update(face_bbox='0,0,200,200',face_bbox_x='0',face_bbox_y='0')
        result=describe(row,self.settings)
        self.assertEqual(result['face_center_x_norm'],.1)
        self.assertEqual(result['face_center_y_norm'],.1)
        self.assertEqual(result['face_edge_left'],'true')
        self.assertEqual(result['face_edge_top'],'true')
        self.assertEqual(result['face_edge_right'],'false')
        self.assertEqual(result['face_edge_contact_any'],'true')
        self.assertEqual(result,describe(row,self.settings))

    def test_invalid_bbox_is_error_not_dropped_or_clipped(self):
        row=fixture();row['face_bbox']='-10,100,200,200';row['face_bbox_x']='-10'
        result=describe_rows([row],self.settings)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['step4_status'],'ERROR')
        self.assertEqual(result[0]['ranking_eligible'],'true')

    def test_area_disagreement_is_error(self):
        row=fixture();row['face_area_ratio']='0.12'
        self.assertEqual(describe(row,self.settings)['step4_status'],'ERROR')

    def test_nan_is_error_and_preserves_raw(self):
        row=fixture();row['yaw']='nan'
        result=describe(row,self.settings)
        self.assertEqual(result['yaw'],'nan')
        self.assertEqual(result['step4_status'],'ERROR')

    def test_summary_scope_cross_tables_and_source_still(self):
        rows=describe_rows([fixture('a'),fixture('b','supplemental_still'),fixture('c',eligible=False)],self.settings)
        summary,sources=summarize(rows)
        self.assertEqual(summary['total_rows'],3)
        self.assertEqual(summary['ranking_eligible_rows'],2)
        self.assertEqual(summary['pose_bin']['FRONTAL'],2)
        self.assertEqual(summary['cross_tables']['pose_bin_x_input_kind']['FRONTAL']['supplemental_still'],1)
        self.assertEqual(len(sources),2)
        self.assertFalse(summary['reject_or_quota_introduced'])

    def test_duplicate_ids_fail_not_silent_drop(self):
        with self.assertRaises(ValueError):describe_rows([fixture(),fixture()],self.settings)

    def test_ssot_missing_or_inconsistent_fails(self):
        with self.assertRaises(KeyError):settings_from({})
        custom=copy.deepcopy(self.config);custom['step4_pose']['profile_yaw_min']=43
        with self.assertRaises(ValueError):settings_from(custom)

    def test_no_model_inference_or_selection_dependencies(self):
        import ast
        forbidden={'cv2','mediapipe','numpy','face_deduplication','evaluate_identity','select_revision_b'}
        for name in ['scripts/common/pose_composition.py','scripts/step4_pose_composition.py']:
            tree=ast.parse((ROOT/name).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertTrue(forbidden.isdisjoint(a.name for a in node.names))
                if isinstance(node,ast.ImportFrom):self.assertNotIn(node.module,forbidden)

    def test_temp_cli_publication_history_and_bad_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);report=base/'input.csv';snapshot=base/'input.json'
            rows=[fixture('a'),fixture('b','supplemental_still'),fixture('c',eligible=False)]
            with report.open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            digest=hashlib.sha256(report.read_bytes()).hexdigest()
            snapshot.write_text(json.dumps(dict(version='best_rank_v2.2',total_universe=3,ranking_sha256=digest)),encoding='utf-8')
            targets={key:base/name for key,name in [('output','step4.csv'),('summary','summary.json'),('video_summary','sources.csv'),('markdown','summary.md')]}
            argv=[sys.executable,str(ROOT/'scripts/step4_pose_composition.py'),'--config',str(ROOT/'config/config.example.yaml'),
                  '--report',str(report),'--step3-summary',str(snapshot)]
            for key,path in targets.items():argv.extend(['--'+key.replace('_','-'),str(path)])
            result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            before=targets['output'].read_bytes()
            summary=publish(load_input(report,snapshot),self.settings,report,snapshot,targets)
            self.assertEqual(summary['total_rows'],3)
            archived=list((base/'bkup').glob('*/output.csv'))
            self.assertEqual(len(archived),1)
            self.assertEqual(archived[0].read_bytes(),before)
            self.assertEqual(hashlib.sha256(report.read_bytes()).hexdigest(),digest)
            bad=json.loads(snapshot.read_text());bad['total_universe']=2;snapshot.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):load_input(report,snapshot)


if __name__=='__main__':unittest.main()
