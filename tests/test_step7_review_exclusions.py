import copy
import unittest
from test_step7_candidate_selection_v2 import row,settings,select,normal
from common.candidate_review_exclusions import confirmed_rejects,CURRENT_RANKING_VERSION


def evidence(state='REVIEW_REJECT',version=CURRENT_RANKING_VERSION):
    rows=[row(i,ranking_version=CURRENT_RANKING_VERSION,image_sha256='hash'+str(i)) for i in range(6)]
    record=dict(rows[0],ranking_version=version,review_state=state,review_round=1)
    rounds=[dict(review_round=1,ranking_version=CURRENT_RANKING_VERSION,publication_status='COMPLETE')]
    records=[record] if version==CURRENT_RANKING_VERSION else []
    history=dict(version=2,review_history={CURRENT_RANKING_VERSION:dict(records=records,rounds=rounds)})
    if version!=CURRENT_RANKING_VERSION:history['review_history'][version]=dict(records=[record],rounds=[])
    feedback=[dict(record)] if state=='REVIEW_REJECT' and records else []
    summary=dict(version=CURRENT_RANKING_VERSION,review_ranking_version=CURRENT_RANKING_VERSION,
        review_rounds=rounds,shown_count=len(records),review_reject_count=len(feedback))
    rejected,old=confirmed_rejects(rows,history,feedback,summary)
    return rows,rejected,old,history,feedback,summary


class ReviewExclusionTests(unittest.TestCase):
    def test_01_current_reject_excluded(self):
        rows,rejected,*_=evidence();full,pool,_=select(rows,settings(),current_reject_ids=rejected)
        self.assertNotIn('f000',{r['frame_id'] for r in pool})
        self.assertEqual(full[0]['selection_reason'],'CURRENT_VERSION_HUMAN_REJECT')
        self.assertEqual(full[0]['candidate_pool_eligible'],'false')

    def test_02_pending_eligible(self):
        rows,rejected,*_=evidence(state='PENDING')
        self.assertIn('f000',{r['frame_id'] for r in select(rows,settings(),current_reject_ids=rejected)[1]})

    def test_03_old_versions_eligible(self):
        for version in ('best_rank_v1','best_rank_v2','best_rank_v2.1'):
            rows,rejected,old,*_=evidence(version=version)
            self.assertEqual(old,{'f000'});self.assertFalse(rejected)
            self.assertIn('f000',{r['frame_id'] for r in select(rows,settings(),current_reject_ids=rejected)[1]})

    def test_04_historical_flag_alone_ignored(self):
        rows,rejected,*_=evidence(state='PENDING');rows[0]['historical_review_reject']='true'
        self.assertIn('f000',{r['frame_id'] for r in select(rows,settings(),current_reject_ids=rejected)[1]})

    def test_05_favorite_does_not_change_order(self):
        rows,rejected,*_=evidence();changed=copy.deepcopy(rows)
        for r in changed:r.update(human_favorite='yes',subjective_preference='reject')
        self.assertEqual(select(rows,settings(),current_reject_ids=rejected)[1],
            [{k:v for k,v in r.items() if k not in ('human_favorite','subjective_preference')} for r in select(changed,settings(),current_reject_ids=rejected)[1]])

    def test_06_best_and_rank_unchanged(self):
        rows,rejected,*_=evidence();full,_,_=select(rows,settings(),current_reject_ids=rejected)
        for old,out in zip(rows,full):
            self.assertEqual(old['best_score'],out['selection_quality_score'])
            self.assertEqual(old['global_rank'],out['global_rank'])

    def test_07_deterministic_replacement(self):
        rows,rejected,*_=evidence();cfg=settings(3)
        expected=['f001','f002','f003']
        for source in (rows,list(reversed(rows))):
            self.assertEqual(expected,[r['frame_id'] for r in select(source,cfg,current_reject_ids=rejected)[1]])

    def test_08_coverage_and_caps_preserved(self):
        rows,rejected,*_=evidence();cfg=settings(3,pose_min={'FRONTAL':2},max_per_video=1)
        before=copy.deepcopy(cfg)
        for r in rows[:3]:r['video_id']='same'
        _,pool,s=select(rows,cfg,current_reject_ids=rejected)
        self.assertEqual(cfg,before);self.assertFalse(s['coverage_shortages'])
        self.assertLessEqual(sum(r['video_id']=='same' for r in pool),1)

    def test_09_full_audit_preserved(self):
        rows,rejected,*_=evidence();full,_,_=select(rows,settings(),current_reject_ids=rejected)
        self.assertEqual(len(rows),len(full))
        self.assertTrue(all(all(out[k]==v for k,v in old.items()) for old,out in zip(rows,full)))

    def test_hash_or_score_mismatch_stops(self):
        for key in ('image_sha256','dataset_generation_id','best_score','global_rank'):
            rows,_,_,h,f,s=evidence();h['review_history'][CURRENT_RANKING_VERSION]['records'][0][key]='different'
            with self.assertRaises(ValueError):confirmed_rejects(rows,h,f,s)

    def test_feedback_disagreement_stops(self):
        rows,_,_,h,f,s=evidence();f[0]['review_state']='PENDING'
        with self.assertRaises(ValueError):confirmed_rejects(rows,h,f,s)

    def test_missing_authority_stops(self):
        rows,_,_,h,f,s=evidence();h['review_history'].pop(CURRENT_RANKING_VERSION)
        with self.assertRaises(ValueError):confirmed_rejects(rows,h,f,s)


if __name__=='__main__':unittest.main()
