import copy
import json
from pathlib import Path
import tempfile
import unittest
from test_step7_candidate_selection_v2 import row
from test_step7_review_exclusions import evidence
from common.config import load_config
from common.candidate_selection_v21 import select,VERSION
from step7_candidate_selection_v21 import publish_selection


def cfg(target=6,core=3,**values):
    result=dict(version=VERSION,candidate_pool_min=core,candidate_pool_target=target,candidate_pool_max=target,
        quality_guard_multiplier=2.,quality_core_target=core,coverage_repair_slots_max=target-core,
        max_per_video=6,max_supplemental_still=15,pose_min={},vertical_min={},scale_min={})
    result.update(values);return result


def run(rows,settings=None,rejected=()):return select(rows,settings or cfg(),current_reject_ids=rejected)


class QualityCoverageTests(unittest.TestCase):
    def test_01_current_reject_excluded(self):
        rows,rejected,*_=evidence();full,pool,_=run(rows,rejected=rejected)
        self.assertNotIn('f000',{r['frame_id'] for r in pool});self.assertEqual(full[0]['selection_reason'],'CURRENT_VERSION_HUMAN_REJECT')

    def test_02_pending_eligible(self):
        rows,rejected,*_=evidence(state='PENDING');self.assertIn('f000',{r['frame_id'] for r in run(rows,rejected=rejected)[1]})

    def test_03_old_reject_eligible(self):
        for v in ('best_rank_v1','best_rank_v2','best_rank_v2.1'):
            rows,rejected,*_=evidence(version=v);self.assertIn('f000',{r['frame_id'] for r in run(rows,rejected=rejected)[1]})

    def test_04_preference_ignored(self):
        rows=[row(i) for i in range(8)];changed=copy.deepcopy(rows)
        for r in changed:r.update(human_favorite='yes',review_state='REVIEW_REJECT',historical_review_reject='true')
        self.assertEqual([r['frame_id'] for r in run(rows)[1]],[r['frame_id'] for r in run(changed)[1]])

    def test_05_guard_after_reject(self):
        rows=[row(i) for i in range(9)];full,_,_=run(rows,cfg(3,2),{'f000'})
        self.assertFalse(full[0]['quality_guard_member']=='true');self.assertEqual(full[6]['quality_guard_member'],'true')
        self.assertEqual(full[7]['quality_guard_member'],'false')

    def test_06_guard_derived_size(self):
        _,_,s=run([row(i) for i in range(20)],cfg(7,3,quality_guard_multiplier=1.5))
        self.assertEqual(s['quality_guard_size_requested'],11)

    def test_07_outside_guard_not_rescued(self):
        rows=[row(i) for i in range(20)];rows[18]['pose_bin']='PROFILE_LEFT'
        _,pool,s=run(rows,cfg(pose_min={'PROFILE_LEFT':2}))
        self.assertNotIn('f018',{r['frame_id'] for r in pool});self.assertTrue(s['soft_coverage_shortages'])

    def test_08_core_pure_best_constraints(self):
        rows=[row(i) for i in range(10)];rows[1]['dedup_cluster_id']=rows[0]['dedup_cluster_id'];rows[2]['video_id']=rows[0]['video_id']
        _,pool,_=run(rows,cfg(max_per_video=1))
        self.assertEqual([r['frame_id'] for r in pool if r['selection_reason']=='BEST_QUALITY_CORE'],['f000','f003','f004'])

    def test_09_default_core60(self):
        self.assertEqual(load_config()['step7_candidates_v2']['quality_core_target'],60)
        _,_,s=run([row(i) for i in range(150)],load_config()['step7_candidates_v2'])
        self.assertEqual(s['quality_core_count'],60)

    def test_10_default_repair_at_most10(self):
        settings=load_config()['step7_candidates_v2'];self.assertEqual(settings['coverage_repair_slots_max'],10)
        rows=[row(i) for i in range(150)]
        for r in rows[60:100]:r.update(pose_bin='PROFILE_LEFT',vertical_pose='LOOKING_UP',face_scale_bin='FULL_BODY')
        self.assertLessEqual(run(rows,settings)[2]['selection_reasons']['COVERAGE_REPAIR'],10)

    def test_11_core_never_replaced(self):
        rows=[row(i) for i in range(12)];rows[6]['pose_bin']='PROFILE_LEFT'
        _,pool,_=run(rows,cfg(pose_min={'PROFILE_LEFT':1}))
        self.assertEqual([r['frame_id'] for r in pool if r['selection_reason']=='BEST_QUALITY_CORE'],['f000','f001','f002'])

    def test_12_repair_from_guard_remainder(self):
        rows=[row(i) for i in range(14)];rows[7]['pose_bin']='PROFILE_LEFT'
        _,pool,_=run(rows,cfg(pose_min={'PROFILE_LEFT':1}))
        repair=[r for r in pool if r['selection_reason']=='COVERAGE_REPAIR']
        self.assertEqual([r['frame_id'] for r in repair],['f007']);self.assertEqual(repair[0]['quality_guard_member'],'true')

    def test_13_repair_tie_best(self):
        rows=[row(i) for i in range(12)]
        for r in rows[6:8]:r['pose_bin']='PROFILE_LEFT'
        self.assertEqual([r['frame_id'] for r in run(rows,cfg(pose_min={'PROFILE_LEFT':1}))[1] if r['selection_reason']=='COVERAGE_REPAIR'],['f006'])

    def test_14_profile_minima2_each(self):
        settings=load_config()['step7_candidates_v2']
        self.assertEqual(settings['pose_min']['PROFILE_LEFT'],2);self.assertEqual(settings['pose_min']['PROFILE_RIGHT'],2)

    def test_15_missing_profile_soft_shortage(self):
        _,_,s=run([row(i) for i in range(12)],cfg(pose_min={'PROFILE_LEFT':2}))
        self.assertEqual(s['soft_coverage_shortages'][0]['reason'],'COVERAGE_SHORTAGE');self.assertEqual(s['publication_status'],'COMPLETE')

    def test_16_unused_repairs_best_fill(self):
        _,pool,s=run([row(i) for i in range(12)])
        self.assertEqual(s['selection_reasons']['COVERAGE_REPAIR'],0);self.assertEqual(s['selection_reasons']['BEST_SCORE_FILL'],3)
        self.assertEqual([r['frame_id'] for r in pool],['f000','f001','f002','f003','f004','f005'])

    def test_17_fill_cannot_leave_guard(self):
        rows=[row(i,video_id='same') for i in range(12)]+[row(i) for i in range(12,20)]
        _,pool,s=run(rows,cfg(max_per_video=4))
        self.assertEqual(len(pool),4);self.assertTrue(all(int(r['quality_guard_order'])<=12 for r in pool))

    def test_18_60_to69_publish_warning(self):
        settings=load_config()['step7_candidates_v2'];_,_,s=run([row(i) for i in range(64)],settings)
        self.assertEqual(s['publication_status'],'COMPLETE');self.assertEqual(s['pool_quality_status'],'POOL_BELOW_TARGET_QUALITY_PRESERVED')

    def test_19_below60_no_expand(self):
        rows=[row(i,video_id='same') for i in range(140)]+[row(i) for i in range(140,220)]
        _,pool,s=run(rows,load_config()['step7_candidates_v2'])
        self.assertEqual(len(pool),6);self.assertEqual(s['publication_status'],'BLOCKED')
        self.assertIn('QUALITY_CORE_SHORTAGE',s['hard_shortages']);self.assertIn('QUALITY_POOL_INSUFFICIENT',s['hard_shortages'])

    def test_20_identity_zero(self):
        rows=[row(i,identity_state=('IDENTITY_REJECT','IDENTITY_NOT_EVALUABLE','IDENTITY_REVIEW')[i%3],identity_passed='false') for i in range(8)]
        _,pool,s=run(rows);self.assertEqual(len(pool),6);self.assertEqual(s['identity_selection_weight'],0)

    def test_21_best_rank_unchanged(self):
        rows=[row(i) for i in range(8)];full,_,_=run(rows)
        for old,out in zip(rows,full):
            self.assertEqual(old['best_score'],out['selection_quality_score']);self.assertEqual(old['global_rank'],out['global_rank'])

    def test_22_full_rows_columns(self):
        rows=[row(i) for i in range(8)];rows[1]['dedup_role']='DUPLICATE_MEMBER'
        full,_,_=run(rows);self.assertEqual(len(full),len(rows))
        self.assertTrue(all(all(out[k]==v for k,v in old.items()) for old,out in zip(rows,full)))

    def test_23_renaming_not_blacklist(self):
        rows=[row(i) for i in range(8)];renamed=copy.deepcopy(rows)
        for r in renamed:r.update(filename='renamed.png',video_id='rename'+r['video_id'])
        self.assertEqual([r['best_score'] for r in run(rows)[1]],[r['best_score'] for r in run(renamed)[1]])

    def test_soft_shortage_published_and_hard_failure_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);targets={k:root/name for k,name in dict(output_csv='step7_candidate_selection.csv',candidates_csv='step7_review_candidates.csv',summary='step7_candidate_summary.json',markdown='STEP7_CANDIDATE_SUMMARY.md',review_html='STEP7_CANDIDATE_REVIEW.html').items()}
            s=publish_selection([row(i) for i in range(8)],cfg(pose_min={'PROFILE_LEFT':2}),targets,root,{},review_evidence={})
            self.assertEqual(s['publication_status'],'COMPLETE');prior={k:p.read_bytes() for k,p in targets.items()}
            blocked=publish_selection([row(0)],cfg(),targets,root,{},review_evidence={})
            self.assertEqual(blocked['publication_status'],'BLOCKED');self.assertEqual(prior,{k:p.read_bytes() for k,p in targets.items()})

    def test_partial_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);targets={k:root/name for k,name in dict(output_csv='step7_candidate_selection.csv',candidates_csv='step7_review_candidates.csv',summary='step7_candidate_summary.json',markdown='STEP7_CANDIDATE_SUMMARY.md',review_html='STEP7_CANDIDATE_REVIEW.html').items()}
            for p in targets.values():p.write_bytes(b'previous')
            s=publish_selection([row(i) for i in range(12)],cfg(),targets,root,{},limit=4,review_evidence={})
            self.assertEqual(s['publication_status'],'PARTIAL');self.assertTrue(all(p.read_bytes()==b'previous' for p in targets.values()))


if __name__=='__main__':unittest.main()
