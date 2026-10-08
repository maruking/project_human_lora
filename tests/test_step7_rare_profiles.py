import copy
from pathlib import Path
import tempfile
import unittest
from test_step7_candidate_selection_v2 import row
from test_step7_quality_coverage_v21 import version_metadata
from common.config import load_config
from common.candidate_selection_v22 import select,review_scope_allowed
from step7_candidate_selection_v22 import publish_selection

class RareProfileTests(unittest.TestCase):
    def settings(self):
        s=copy.deepcopy(load_config()['step7_candidates_v2'])
        s.update(pose_min={'PROFILE_LEFT':2,'PROFILE_RIGHT':2},scale_min={'FULL_BODY':2},vertical_min={'LOOKING_UP':2})
        return s
    def rows(self):
        return [row(i,pose_bin='FRONTAL' if i<140 else 'PROFILE_LEFT' if i%2==0 else 'PROFILE_RIGHT',face_scale_bin='CLOSE_UP',vertical_pose='LEVEL') for i in range(160)]
    def test_01_each_side_top3_without_changing_base_or_scores(self):
        rows=self.rows();full,pool,s=select(rows,self.settings())
        self.assertEqual(len(full),160);self.assertEqual(s['base_count'],70)
        self.assertEqual([r['frame_id'] for r in pool if r['base_candidate']=='true'],[r['frame_id'] for r in rows[:70]])
        self.assertEqual([r['frame_id'] for r in pool if r['rare_profile_candidate']=='true'],[r['frame_id'] for r in rows[140:146]])
        self.assertEqual(s['rare_profile_outside_guard_count'],6)
        self.assertTrue(all(all(out[k]==v for k,v in old.items()) for old,out in zip(rows,full)))
        self.assertTrue(all(review_scope_allowed(r) for r in pool))
        self.assertTrue(s['soft_coverage_shortages'])
    def test_02_reject_fatal_duplicate_excluded_and_pending_allowed(self):
        rows=self.rows();rows[140]['ranking_eligible']='false';rows[141]['dedup_role']='DUPLICATE_MEMBER'
        rows[142]['step4_status']='ERROR';rows[143]['historical_review_reject']='true';rows[143]['review_state']='PENDING'
        _,pool,s=select(rows,self.settings(),current_reject_ids={rows[144]['frame_id']})
        ids={r['frame_id'] for r in pool}
        self.assertFalse(ids & {rows[i]['frame_id'] for i in (140,141,142,144)})
        self.assertIn(rows[143]['frame_id'],ids)
        self.assertEqual(s['rare_profile_review']['PROFILE_LEFT']['after'],3)
        self.assertEqual(s['rare_profile_review']['PROFILE_RIGHT']['after'],3)
    def test_03_shortage_stays_shortage(self):
        rows=self.rows()[:142];_,pool,s=select(rows,self.settings())
        self.assertEqual(s['rare_profile_added_count'],2)
        self.assertEqual(s['rare_profile_review']['PROFILE_LEFT']['shortage'],2)
        self.assertEqual(s['rare_profile_review']['PROFILE_RIGHT']['shortage'],2)
    def test_04_no_removal_when_base_already_has_many_profiles(self):
        rows=self.rows()
        for r in rows[:10]:r['pose_bin']='PROFILE_RIGHT'
        _,pool,s=select(rows,self.settings())
        self.assertEqual(s['rare_profile_review']['PROFILE_RIGHT']['after'],10)
        self.assertEqual(s['rare_profile_review']['PROFILE_RIGHT']['added'],0)
        self.assertEqual(s['base_count'],70)
    def test_05_non_profile_never_bypasses_guard(self):
        rows=[row(i,pose_bin='FRONTAL',face_scale_bin='FULL_BODY' if i>=140 else 'CLOSE_UP',vertical_pose='LOOKING_UP' if i>=140 else 'LEVEL') for i in range(160)]
        _,pool,s=select(rows,self.settings())
        self.assertEqual(len(pool),70);self.assertEqual(s['rare_profile_added_count'],0)
        self.assertFalse(review_scope_allowed(dict(pool[0],quality_guard_member='false',rare_profile_candidate='true',selection_reason='RARE_PROFILE_REVIEW')))
    def test_06_partial_limit_cannot_scan_entire_universe(self):
        _,pool,s=select(self.rows(),self.settings(),limit=140)
        self.assertEqual(s['publication_status'],'PARTIAL');self.assertEqual(s['rare_profile_added_count'],0)
    def test_07_synthetic_publication_contains_exception_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);images=root/'images';images.mkdir()
            targets={k:root/name for k,name in dict(output_csv='full.csv',candidates_csv='candidates.csv',summary='summary.json',markdown='summary.md',review_html='review.html').items()}
            s=publish_selection(self.rows(),self.settings(),targets,images,version_metadata(root))
            self.assertEqual(s['rare_profile_outside_guard_count'],6)
            self.assertIn('RARE_PROFILE_REVIEW',targets['review_html'].read_text(encoding='utf-8'))

    def test_08_step8_preflight_accepts_explicit_profile_exception(self):
        import hashlib,json
        from unittest.mock import patch
        from step8_folder_review import preflight,encoded_csv
        config=load_config();settings=config['step7_candidates_v2']
        rows=self.rows();full,pool,summary=select(rows,settings)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);paths={k:base/name for k,name in dict(full_csv='full.csv',candidates_csv='candidates.csv',step7_summary='summary.json').items()}
            paths['full_csv'].write_bytes(encoded_csv(full));paths['candidates_csv'].write_bytes(encoded_csv(pool))
            summary.update(settings=settings,input_hashes={},artifact_sha256={k:hashlib.sha256(paths[p].read_bytes()).hexdigest() for k,p in [('output_csv','full_csv'),('candidates_csv','candidates_csv')]})
            paths['step7_summary'].write_text(json.dumps(summary),encoding='utf-8')
            with patch('step8_folder_review.upstream_preflight',return_value=(rows,{})),patch('step8_folder_review.review_exclusions',return_value=(set(),{})):
                audit,candidates,_,_=preflight(config,paths,base/'images')
                self.assertEqual(len(audit),len(rows))
                self.assertEqual(sum(r['quality_guard_member']=='false' for r in candidates),6)
    def test_09_profile_target_validation(self):
        for value in (1,4,True,2.5):
            settings=self.settings();settings['rare_profile_review_target']=value
            with self.assertRaisesRegex(ValueError,'Rare Profile'):select(self.rows(),settings)

if __name__=='__main__':unittest.main()
