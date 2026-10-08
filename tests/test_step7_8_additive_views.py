import copy
import json
from pathlib import Path
import tempfile
import unittest
from test_step7_candidate_selection_v2 import row
from test_step7_quality_coverage_v21 import version_metadata
from common.config import load_config
from common.candidate_selection_v22 import select
from step7_candidate_selection_v22 import publish_selection
from common.folder_review import row_views,accepted_ids
from test_step8_folder_review import materialize

class AdditiveReviewTests(unittest.TestCase):
    def settings(self):
        s=copy.deepcopy(load_config()['step7_candidates_v2'])
        s.update(pose_min={'PROFILE_RIGHT':2},scale_min={'FULL_BODY':2},vertical_min={},rare_profile_review_target=2)
        return s

    def rows(self):
        return [row(i,pose_bin='PROFILE_RIGHT' if i>=70 else 'FRONTAL',face_scale_bin='FULL_BODY' if i>=70 else 'CLOSE_UP',video_id='same_source',source_id='same_source') for i in range(150)]

    def test_base70_retained_and_coverage_added_despite_cap(self):
        rows=self.rows();full,pool,s=select(rows,self.settings())
        self.assertEqual(len(full),150)
        self.assertEqual({r['frame_id'] for r in pool if r['base_candidate']=='true'},{r['frame_id'] for r in rows[:70]})
        self.assertEqual(len(pool),72)
        self.assertEqual(s['coverage_additional_count'],2)
        self.assertTrue(s['source_concentration_warnings'])
        self.assertTrue(all(out[k]==v for old,out in zip(rows,full) for k,v in old.items()))
        self.assertEqual([r['best_score'] for r in full],[r['best_score'] for r in rows])

    def test_no_quality_guard_expansion_for_shortage(self):
        rows=self.rows()
        for r in rows[:140]:r.update(pose_bin='FRONTAL',face_scale_bin='CLOSE_UP')
        _,pool,s=select(rows,self.settings())
        self.assertEqual(len(pool),72)
        self.assertTrue(all(r['selection_reason']=='RARE_PROFILE_REVIEW' for r in pool if r['quality_guard_member']=='false'))

    def test_current_reject_excluded_without_base_loss(self):
        rows=self.rows();_,pool,s=select(rows,self.settings(),current_reject_ids={rows[0]['frame_id']})
        self.assertNotIn(rows[0]['frame_id'],{r['frame_id'] for r in pool})
        self.assertEqual(s['base_count'],70)

    def test_profile_fullbody_views_and_single_acceptance(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp),18)
            self.assertTrue(list((root/'01_BY_SHOT/FULL_BODY').iterdir()))
            self.assertTrue(list((root/'02_BY_POSE/PROFILE_RIGHT').iterdir()))
            self.assertEqual(accepted_ids(records,root,s)[0],set())
            r=records[0];shutil.copy2(r['full_review_path'],r['accept_review_path'])
            self.assertEqual(accepted_ids(records,root,s)[0],{r['frame_id']})
            self.assertTrue(all([p.name for p in sorted((root/v).iterdir())]==[r['review_filename'] for r in records if v in row_views(r)] for v in ['00_ALL_RANKED','01_BY_SHOT/FULL_BODY','02_BY_POSE/PROFILE_RIGHT']))

    def test_legacy_review_requires_explicit_reset_and_preserves_choices(self):
        import shutil
        from common.folder_review_v2 import stage_review as old_stage,install_review as old_install
        from common.folder_review import stage_review,install_review
        from test_step8_folder_review import fixture
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);settings,root,images,rows=fixture(base)
            old=dict(settings,version='step8_folder_review_v2')
            records,stage,_=old_stage(rows,old,root,images,base,{})
            old_install(stage,root,old)
            r=records[0];shutil.copy2(r['full_review_path'],r['accept_review_path'])
            with self.assertRaisesRegex(ValueError,'Legacy review preserved'):
                stage_review(rows,settings,root,images,base,{})
            _,stage,_=stage_review(rows,settings,root,images,base,{},reset=True)
            archive=install_review(stage,root,settings,reset=True)
            self.assertTrue((archive/Path(r['accept_review_path']).relative_to(root)).is_file())
            self.assertEqual(list((root/'99_ACCEPT').iterdir()),[])

    def test_synthetic_publication_html_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);images=root/'images';images.mkdir()
            rows=self.rows()
            targets={k:root/name for k,name in dict(output_csv='full.csv',candidates_csv='candidates.csv',summary='summary.json',markdown='summary.md',review_html='review.html').items()}
            s=publish_selection(rows,self.settings(),targets,images,version_metadata(root))
            self.assertEqual(s['base_count'],70)
            self.assertEqual(s['selected_review_pool'],72)
            self.assertTrue(targets['review_html'].is_file())

if __name__=='__main__':unittest.main()
