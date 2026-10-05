"""Version-scoped review regressions. All images/reports are temporary fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_step3_best import row
from common.best_ranking import VERSION, rank_rows, choose_round
from common.best_review import (HISTORY_NAME, LEGACY_NAME, read_history, materialize,
                                feedback, historical_reviews)
from step3_best_ranking import annotate, review_summary


class VersionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'raw'
        self.review=self.root/'reports/step3_best_review'
        self.path=self.root/'reports'/HISTORY_NAME
        self.legacy=self.path.with_name(LEGACY_NAME)
        self.legacy.parent.mkdir(parents=True)
        self.rows=[]
        for i in range(9):
            r=row(i);p=self.source/r['filename'];p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(f'synthetic image {i}'.encode())
            r['image_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            self.rows.append(r)
        self.rows=rank_rows(self.rows,{})
        self.settings=dict(review_size=3,max_per_video=4,min_supplemental=0)
        records=[dict(r,ranking_version='best_rank_v1',review_round=1 if i<2 else 2,
                      review_round_rank=i%2+1,shown_to_maru=True,review_state='REVIEW_REJECT',
                      copy_relative=r['filename']) for i,r in enumerate(self.rows[:4])]
        self.old=dict(version=1,rounds=[dict(review_round=n,publication_status='COMPLETE')
                                      for n in (1,2)],records=records)
        self.legacy.write_text(json.dumps(self.old),encoding='utf-8')
        self.old_bytes=self.legacy.read_bytes()
        for r in records:
            p=self.review/f"round_{r['review_round']:02d}"/'review_reject'/r['filename']
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes((self.source/r['filename']).read_bytes())
        self.old_copies={p:p.read_bytes() for p in self.review.rglob('*.png')}

    def publish(self,n):
        return materialize(self.rows,self.source,self.review,self.path,n,self.settings)

    def assert_legacy_untouched(self):
        self.assertEqual(self.legacy.read_bytes(),self.old_bytes)
        for p,data in self.old_copies.items():self.assertEqual(p.read_bytes(),data)

    def test_version_buckets_and_legacy_bytes_separate(self):
        self.publish(1)
        stored=json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(set(stored['review_history']),{'best_rank_v1',VERSION})
        self.assertEqual(stored['review_history']['best_rank_v1'],self.old)
        self.assertNotIn('records',stored)
        self.assertEqual(len(read_history(self.path)['records']),3)
        self.assertTrue((self.review/VERSION/'round_01/candidates').is_dir())
        self.assert_legacy_untouched()

    def test_v1_shown_and_reject_do_not_exclude_v2_round1(self):
        h=self.publish(1)
        self.assertEqual([r['frame_id'] for r in h['records']],
                         [r['frame_id'] for r in self.rows[:3]])
        self.assertTrue(all(r['review_state']=='PENDING' for r in h['records']))
        self.assertEqual(review_summary(h)['shown_count'],3)
        self.assertEqual(review_summary(h)['review_reject_count'],0)

    def test_v2_round2_excludes_only_v2_round1(self):
        self.publish(1);h=self.publish(2)
        picked=[r['frame_id'] for r in h['records'] if r['review_round']==2]
        self.assertEqual(picked,[r['frame_id'] for r in self.rows[3:6]])
        self.assertIn(self.old['records'][3]['frame_id'],picked)

    def test_v2_round3_excludes_v2_round1_and_round2(self):
        self.publish(1);self.publish(2);h=self.publish(3)
        self.assertEqual([r['frame_id'] for r in h['records'] if r['review_round']==3],
                         [r['frame_id'] for r in self.rows[6:9]])
        self.assertEqual(len({r['frame_id'] for r in h['records']}),9)
        self.assertIsNone(review_summary(h)['next_review_round'])

    def test_v1_reject_is_visible_regression_evidence_not_current_reject(self):
        h=read_history(self.path);rows=copy.deepcopy(self.rows)
        annotate(rows,h)
        self.assertEqual(len(h['review_history']['best_rank_v1']['records']),4)
        self.assertEqual(rows[0]['historical_review_reject'],'true')
        evidence=json.loads(rows[0]['historical_reviews'])[0]
        self.assertEqual(evidence['ranking_version'],'best_rank_v1')
        self.assertEqual(evidence['review_state'],'REVIEW_REJECT')
        self.assertEqual(rows[0]['shown_to_maru'],'false')
        self.assertEqual(rows[0]['review_state'],'')
        self.assertFalse(self.path.exists())

    def test_restart_does_not_reset_lineage_scores_or_source(self):
        before=copy.deepcopy(self.rows)
        self.publish(1)
        self.assertEqual(self.rows,before)
        annotated=copy.deepcopy(self.rows);annotate(annotated,read_history(self.path))
        for original,current in zip(before,annotated):
            for key in ('frame_id','dataset_generation_id','image_sha256','source_id',
                        'global_rank','best_score','face_laplacian_canonical_192'):
                self.assertEqual(current[key],original[key])
            self.assertEqual(hashlib.sha256((self.source/original['filename']).read_bytes()).hexdigest(),
                             original['image_sha256'])
        self.assert_legacy_untouched()

    def test_round3_cannot_be_created_directly_despite_v1_round2(self):
        with self.assertRaisesRegex(ValueError,'Previous review round'):self.publish(3)
        self.assertFalse(self.path.exists())
        self.assertFalse((self.review/VERSION).exists())

    def test_feedback_only_updates_v2_and_preserves_v1_reject(self):
        h=self.publish(1);r=h['records'][0]
        candidate=self.review/VERSION/'round_01/candidates'/r['filename']
        rejected=self.review/VERSION/'round_01/review_reject'/r['filename']
        rejected.parent.mkdir(parents=True,exist_ok=True);candidate.rename(rejected)
        h,rejects=feedback(self.review,self.path)
        self.assertEqual(len(rejects),1)
        self.assertEqual(rejects[0]['ranking_version'],VERSION)
        self.assertEqual(h['review_history']['best_rank_v1'],self.old)
        self.assert_legacy_untouched()

    def test_lineage_change_does_not_silently_reuse_completed_round(self):
        self.publish(1);self.rows[0]['dataset_generation_id']='different generation'
        with self.assertRaisesRegex(ValueError,'lineage differs'):self.publish(1)

    def test_historical_annotation_requires_same_image_generation(self):
        changed=dict(self.rows[0],image_sha256='other image')
        self.assertEqual(historical_reviews(read_history(self.path),changed),[])

    def test_round_selection_ignores_other_versions_and_future_rounds(self):
        history=[dict(self.rows[0],shown_to_maru=True,review_round=1),
                 dict(self.rows[1],shown_to_maru=True,review_round=3),
                 dict(self.rows[2],ranking_version='best_rank_v1',shown_to_maru=True,review_round=1)]
        selected,_=choose_round(self.rows,history,size=3,min_stills=0,round_number=2)
        self.assertEqual([r['frame_id'] for r in selected],[r['frame_id'] for r in self.rows[1:4]])

    def test_v1_feedback_without_v2_round_is_read_only_failure(self):
        with self.assertRaisesRegex(ValueError,f'start {VERSION} Round 1'):feedback(self.review,self.path)
        self.assertFalse(self.path.exists());self.assert_legacy_untouched()

    def test_changed_legacy_source_fails_instead_of_overwriting_snapshot(self):
        self.publish(1);saved=self.path.read_bytes()
        self.legacy.write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'v1 evidence changed'):read_history(self.path)
        self.assertEqual(self.path.read_bytes(),saved)


if __name__=='__main__':unittest.main()
