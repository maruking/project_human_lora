import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common.candidate_selection_v2 import select,priority,normal,VERSION
from common.config import load_config
from common.identity_v2 import FIELDS as IDENTITY_FIELDS
from step7_candidate_selection_v2 import publish_selection,preflight,digest


def row(i,score=None,**values):
    record=dict(frame_id=f'f{i:03}',filename=f'f{i:03}.png',video_id=f'video{i}',source_id=f'source{i}',
        input_kind='formal_video',dataset_generation_id='fixture-generation',ranking_eligible='true',
        dedup_role='UNIQUE',dedup_cluster_id=f'cluster{i}',cluster_size='1',
        representative_frame_id=f'f{i:03}',best_score=str(100-i if score is None else score),global_rank=str(i+1),
        pose_bin='FRONTAL',vertical_pose='LEVEL',face_scale_bin='UPPER_BODY',yaw='',pitch='',
        identity_state='IDENTITY_PASS',identity_passed='true',step6_status='MEASURED',step6_version='step6_identity_v2',
        identity_similarity_centroid='.8',identity_similarity_max='.9',identity_similarity_median='.8')
    record.update(values);return record


def settings(target=3,**values):
    cfg=dict(version=VERSION,candidate_pool_min=1,candidate_pool_target=target,candidate_pool_max=max(target,5),
        max_per_video=6,max_supplemental_still=15,pose_min={},vertical_min={},scale_min={})
    cfg.update(values);return cfg


def picked(rows,cfg=None):return select(rows,cfg or settings())[1]


class CandidateTests(unittest.TestCase):
    def test_01_full_row_and_column_preservation(self):
        rows=[row(i) for i in range(6)];rows[2]['custom_history']='untouched'
        full,_,_=select(rows,settings());self.assertEqual(len(full),6)
        self.assertTrue(all(all(out[k]==v for k,v in old.items()) for out,old in zip(full,rows)))

    def test_02_normal_pool_unique_and_representative(self):
        self.assertTrue(normal(row(0)));self.assertTrue(normal(row(1,dedup_role='REPRESENTATIVE')))

    def test_03_no_duplicate_member(self):
        self.assertFalse(picked([row(0,dedup_role='DUPLICATE_MEMBER')]))

    def test_04_quality_equals_stored_best(self):
        out=picked([row(0,score='72.1234567')])[0]
        self.assertEqual(out['selection_quality_score'],'72.1234567')

    def test_05_no_legacy_score_use(self):
        rows=[row(0,10,lora_candidate_score='999'),row(1,90,lora_candidate_score='0')]
        self.assertEqual(picked(rows,settings(1))[0]['frame_id'],'f001')

    def test_06_identity_never_changes_order(self):
        rows=[row(i) for i in range(6)]; changed=copy.deepcopy(rows)
        for r in changed:r.update(identity_state='IDENTITY_REJECT',identity_similarity_centroid='0',identity_passed='false')
        self.assertEqual([r['frame_id'] for r in picked(rows)],[r['frame_id'] for r in picked(changed)])

    def test_07_identity_reject_eligible(self):self.assertTrue(normal(row(0,identity_state='IDENTITY_REJECT')))

    def test_08_identity_not_evaluable_eligible(self):self.assertTrue(normal(row(0,identity_state='IDENTITY_NOT_EVALUABLE')))

    def test_09_history_not_a_feature(self):
        rows=[row(i,review_state='REJECT',human_favorite='no') for i in range(5)]
        self.assertEqual([r['frame_id'] for r in picked(rows)],[r['frame_id'] for r in picked([row(i) for i in range(5)])])

    def test_10_filename_video_name_do_not_change_score(self):
        r=row(0,filename='other.png',video_id='other');out=picked([r])[0]
        self.assertEqual(out['selection_quality_score'],r['best_score'])

    def test_11_phase_a_greatest_deficit_axes_first(self):
        rows=[row(0,99),row(1,5,pose_bin='PROFILE_LEFT',face_scale_bin='FULL_BODY')]
        out=picked(rows,settings(1,pose_min={'PROFILE_LEFT':1},scale_min={'FULL_BODY':1}))[0]
        self.assertEqual(out['frame_id'],'f001');self.assertEqual(out['selection_reason'],'COVERAGE_OPTION')

    def test_12_phase_a_quality_tie_break(self):
        rows=[row(0,20),row(1,80)]
        self.assertEqual(picked(rows,settings(1,pose_min={'FRONTAL':1}))[0]['frame_id'],'f001')

    def test_13_phase_b_best_fill(self):
        rows=[row(0,20),row(1,80),row(2,90)]
        self.assertEqual([r['frame_id'] for r in picked(rows,settings(2))],['f002','f001'])
        self.assertTrue(all(r['selection_reason']=='BEST_SCORE_FILL' for r in picked(rows)))

    def test_14_source_caps_video_and_stills(self):
        rows=[row(i,video_id='same') for i in range(20)]
        self.assertEqual(len(picked(rows,settings(10))),6)
        stills=[row(i,input_kind='supplemental_still') for i in range(30)]
        self.assertEqual(len(picked(stills,settings(20))),15)

    def test_15_one_per_cluster(self):
        rows=[row(i,dedup_cluster_id='same') for i in range(4)]
        self.assertEqual(len(picked(rows)),1)

    def test_16_rare_profile_options_met(self):
        rows=[row(i) for i in range(6)]+[row(9,1,pose_bin='PROFILE_RIGHT')]
        full,pool,summary=select(rows,settings(3,pose_min={'PROFILE_RIGHT':1}))
        self.assertIn('f009',{r['frame_id'] for r in pool});self.assertFalse(summary['coverage_shortages'])

    def test_17_unavailable_category_shortage(self):
        full,pool,summary=select([row(i) for i in range(5)],settings(pose_min={'PROFILE_RIGHT':2}))
        self.assertEqual(summary['coverage_shortages'][0]['reason'],'UNAVAILABLE_COVERAGE')
        self.assertEqual(len(full),5)

    def test_18_no_historical_percent_maximum(self):
        self.assertEqual(len(picked([row(i) for i in range(5)],settings(5))),5)

    def test_19_no_abc_dependency(self):
        rows=[row(i,selection_group='C',reserve_use_allowed='false') for i in range(3)]
        self.assertEqual(len(picked(rows)),3)

    def test_20_no_identity_passed_gate(self):
        self.assertEqual(len(picked([row(0,identity_passed='false')])),1)

    def test_21_coverage_no_score_bonus(self):
        result=picked([row(0,20,pose_bin='PROFILE_LEFT')],settings(pose_min={'PROFILE_LEFT':1}))[0]
        self.assertEqual(result['selection_quality_score'],'20')

    def test_22_configured70_default(self):
        cfg=json.loads((Path(__file__).resolve().parents[1]/'config/step7_candidates_v2_legacy.json').read_text(encoding='utf-8'));rows=[row(i,pose_bin=('FRONTAL','THREE_QUARTER_LEFT','THREE_QUARTER_RIGHT','PROFILE_LEFT','PROFILE_RIGHT')[i%5],
            face_scale_bin=('CLOSE_UP','UPPER_BODY','FULL_BODY')[i%3],vertical_pose=('LEVEL','LOOKING_UP','LOOKING_DOWN')[i%3]) for i in range(120)]
        self.assertEqual(len(picked(rows,cfg)),70)

    def test_23_partial_publication_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);targets={k:root/name for k,name in dict(output_csv='step7_candidate_selection.csv',candidates_csv='step7_review_candidates.csv',summary='step7_candidate_summary.json',markdown='STEP7_CANDIDATE_SUMMARY.md',review_html='STEP7_CANDIDATE_REVIEW.html').items()}
            for p in targets.values():p.write_bytes(b'previous-full')
            summary=publish_selection([row(i) for i in range(5)],settings(),targets,root,{},limit=2)
            self.assertEqual(summary['publication_status'],'PARTIAL')
            self.assertTrue(all(p.read_bytes()==b'previous-full' for p in targets.values()))
            self.assertEqual(len(list((root/'audit').glob('*/step7_candidate_selection.csv'))),1)

    def test_24_upstream_hash_mismatch_stops(self):
        from step7_candidate_selection_v2 import csv_bytes
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);r=row(0)
            for key in IDENTITY_FIELDS:r.setdefault(key,'')
            report=root/'step6.csv';report.write_bytes(csv_bytes([r],list(r)))
            summary=root/'step6.json';summary.write_text(json.dumps(dict(step6_version='step6_identity_v2',publication_status='COMPLETE',total_rows=1,artifact_sha256={'output_csv':'wrong'})))
            cfg={'step6_identity':dict(report=str(root/'step5.csv'),step5_summary=str(root/'step5.json'))}
            with patch('step7_candidate_selection_v2.step5_preflight',return_value=([row(0)],{})):
                with self.assertRaisesRegex(ValueError,'content/count'):preflight(report,summary,cfg,root)

    def test_source_conflict_is_not_relaxed(self):
        rows=[row(i,video_id='same',pose_bin='PROFILE_LEFT') for i in range(8)]
        full,pool,summary=select(rows,settings(8,pose_min={'PROFILE_LEFT':7}))
        self.assertEqual(len(pool),6);self.assertEqual(summary['publication_status'],'BLOCKED')
        self.assertEqual(summary['coverage_shortages'][0]['reason'],'SOURCE_CAP_COVERAGE_CONFLICT')

    def test_unselected_is_not_bad_image(self):
        full,_,_=select([row(i) for i in range(6)],settings(2))
        self.assertTrue(all(r['selection_reason']=='NOT_NEEDED_FOR_REVIEW_POOL' for r in full[2:]))

    def test_fatal_and_error_not_pool(self):
        self.assertFalse(normal(row(0,ranking_eligible='false')))
        self.assertFalse(normal(row(1,step6_status='ERROR')))

    def test_display_order_does_not_boost_coverage(self):
        rows=[row(0,99),row(1,10,pose_bin='PROFILE_LEFT')]
        pool=picked(rows,settings(2,pose_min={'PROFILE_LEFT':1}))
        self.assertEqual(pool[0]['frame_id'],'f000');self.assertEqual(pool[0]['step7_pool_order'],1)


if __name__=='__main__':unittest.main()
