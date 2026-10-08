import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from common.dedup_v2 import annotate, near_evidence, RULE_KEYS, VERSION, summarize, ordering, compute_phash
from common.config import load_config
from common.video_manifest import write_csv_atomic, sha256_file
from step5_dedup_v2 import preflight, hash_sources, publish, galleries, validate_targets, authoritative_input_versions


def rules():
    config = load_config(ROOT/'config/config.example.yaml')
    return {key:config['step5_dedup'][key] for key in RULE_KEYS}


def row(name='one', **changes):
    data = dict(frame_id=name, filename=name+'.png', input_kind='formal_video', source_id='source',
        video_id='video', temporal_index='1', dataset_generation_id='generation',
        image_sha256=hashlib.sha256(name.encode()).hexdigest(), ranking_eligible='true',
        best_score='80',global_rank='1',ranking_version='best_rank_v2.2',
        step4_version='step4_pose_composition_v2', step4_status='MEASURED',
        pose_bin='FRONTAL',face_scale_bin='FULL_BODY',yaw='0',pitch='0',roll='0',
        pose_status='MEASURED',fatal_reject_reason='',width='16',height='16',face_bbox='2,2,8,8')
    data.update(changes)
    return data


def hashed(rows, glob=0, face=0):
    return {r['frame_id']:{'global':glob,'face':face} for r in rows if r['ranking_eligible']=='true'}


class DedupRules(unittest.TestCase):
    def setUp(self):
        self.settings = rules()
        self.a,self.b = row('a'),row('b',temporal_index='7',yaw='12')

    def edge(self,a=None,b=None,g=14,f=None):
        return near_evidence(a or self.a,b or self.b,{'global':0,'face':0},{'global':(1<<g)-1,'face':f},self.settings)

    def test_temporal_boundary_and_each_required_failure(self):
        self.assertIn('VIDEO_TEMPORAL_NEAR',self.edge())
        for b,g in [(row('b',temporal_index='8',yaw='12'),14),(row('b',yaw='12.01'),14),(self.b,15)]:
            self.assertNotIn('VIDEO_TEMPORAL_NEAR',self.edge(b=b,g=g))

    def test_tight_non_temporal_and_or_face(self):
        b=row('b',temporal_index='999',yaw='8')
        self.assertIn('VIDEO_STRONG_SIMILARITY',self.edge(b=b,g=10))
        self.assertIn('VIDEO_STRONG_SIMILARITY',self.edge(b=b,g=64,f=0))
        self.assertEqual(self.edge(b=row('b',temporal_index='999',yaw='8.01'),g=10),[])

    def test_cross_video_and_cross_kind_no_near(self):
        self.assertEqual(self.edge(b=row('b',video_id='other'),g=0),[])
        self.assertEqual(self.edge(b=row('b',input_kind='supplemental_still'),g=0),[])

    def test_missing_pose_and_not_evaluable_not_zero(self):
        for b in (row('b',yaw=''),row('b',pitch=''),row('b',step4_status='NOT_EVALUABLE',pose_bin='NOT_EVALUABLE')):
            self.assertEqual(self.edge(b=b,g=0),[])

    def test_still_requires_both_hashes_and_pose(self):
        a=row('a',input_kind='supplemental_still')
        b=row('b',input_kind='supplemental_still',yaw='8')
        self.assertIn('SUPPLEMENTAL_STILL_NEAR',self.edge(a,b,g=10,f=(1<<10)-1))
        for g,f in ((11,0),(0,(1<<11)-1),(0,None)):
            self.assertEqual(self.edge(a,b,g=g,f=f),[])
        self.assertEqual(self.edge(a,row('b',input_kind='supplemental_still',yaw='8.01'),g=0,f=0),[])

    def test_scale_and_pose_category_boundaries_do_not_gate(self):
        a=row('a',yaw='15',face_scale_bin='CLOSE_UP')
        b=row('b',yaw='16',pose_bin='THREE_QUARTER_RIGHT',face_scale_bin='UPPER_BODY')
        self.assertTrue(self.edge(a,b,g=0))
        self.assertTrue(self.edge(row('a',yaw='41'),row('b',yaw='42',pose_bin='PROFILE_RIGHT'),g=0))

    def test_materially_different_raw_pose_prevents_near(self):
        for yaw,pitch in (('42','0'),('-30','0'),('0','20')):
            self.assertFalse(self.edge(row('a',yaw='20'),row('b',yaw=yaw,pitch=pitch),g=0))

    def test_exact_cross_kind_and_missing_pose(self):
        a=row('a',step4_status='NOT_EVALUABLE',pose_bin='NOT_EVALUABLE',yaw='')
        b=row('b',input_kind='supplemental_still',image_sha256=a['image_sha256'])
        out,clusters,edges=annotate([a,b],hashed([a,b]),{},self.settings)
        self.assertEqual(len(clusters),1)
        self.assertEqual(edges[0][2],['EXACT_DUPLICATE'])
        self.assertTrue(all(r['exact_sha_duplicate']=='true' for r in out))

    def test_same_filename_is_not_exact(self):
        a,b=row('a'),row('b',filename='a.png',video_id='other')
        out,clusters,edges=annotate([a,b],hashed([a,b]),{},self.settings)
        self.assertEqual(len(clusters),2)
        self.assertFalse(edges)

    def test_full_rows_fatal_no_clustering_or_quality_reject(self):
        a,b=row('a'),row('b',ranking_eligible='false',step4_status='NOT_APPLICABLE_STEP3_FATAL')
        out,clusters,_=annotate([a,b],hashed([a,b]),{},self.settings)
        self.assertEqual(len(out),2)
        self.assertEqual(out[1]['dedup_role'],'NOT_APPLICABLE_STEP3_FATAL')
        self.assertEqual(out[1]['global_phash'],'')
        self.assertEqual(out[0]['dedup_role'],'UNIQUE')
        self.assertTrue(out[0]['dedup_cluster_id'])
        for original,result in zip([a,b],out):
            self.assertTrue(all(result[k]==v for k,v in original.items()))

    def test_representative_ties_and_all_alternatives_survive(self):
        rows=[row('b',best_score='91',global_rank='2'),row('a',best_score='91',global_rank='2'),
              row('c',best_score='91',global_rank='1'),row('d',best_score='90',global_rank='1')]
        out,clusters,_=annotate(rows,hashed(rows),{},self.settings)
        self.assertEqual([r['frame_id'] for r in clusters[0]],['c','a','b','d'])
        self.assertEqual(out[2]['dedup_role'],'REPRESENTATIVE')
        self.assertEqual(sum(r['dedup_role']=='DUPLICATE_MEMBER' for r in out),3)

    def test_history_identity_and_renaming_are_not_features(self):
        rows=[row('a'),row('b',best_score='90')]
        first=annotate(rows,hashed(rows),{},self.settings)[0]
        changed=copy.deepcopy(rows)
        for r in changed:
            r.update(review_state='REVIEW_REJECT',identity_similarity_mean='0',historical_review_reject='true',source_id='other_subject',video_id='renamed_video',filename='different/'+r['filename'])
        second=annotate(changed,hashed(changed),{},self.settings)[0]
        self.assertEqual([(r['dedup_role'],r['cluster_rank']) for r in first],[(r['dedup_role'],r['cluster_rank']) for r in second])

    def test_stable_cluster_id_row_order_and_chain_warning(self):
        rows=[row('a',yaw='0'),row('b',yaw='10'),row('c',yaw='20')]
        out,clusters,_=annotate(rows,hashed(rows),{},self.settings)
        rev=annotate(rows[::-1],hashed(rows),{},self.settings)[0]
        self.assertEqual(out[0]['dedup_cluster_id'],rev[0]['dedup_cluster_id'])
        self.assertEqual(out[0]['cluster_max_pose_spread'],20)
        self.assertEqual(out[0]['cluster_chain_warning'],'true')

    def test_subject_frame_renaming_does_not_create_exception(self):
        rows=[row('subject_a/frame_01',best_score='80'),row('subject_a/frame_02',best_score='90')]
        other=[dict(r,frame_id=r['frame_id'].replace('subject_a','subject_b'),filename=r['filename'].replace('subject_a','subject_b'),video_id='another_video') for r in rows]
        first=annotate(rows,hashed(rows),{},self.settings)[0]
        second=annotate(other,hashed(other),{},self.settings)[0]
        self.assertEqual([r['dedup_role'] for r in first],[r['dedup_role'] for r in second])
        self.assertEqual([r['cluster_size'] for r in first],[r['cluster_size'] for r in second])

    def test_errors_preserved_and_missing_face_is_missing(self):
        rows=[row('a'),row('b')]
        out,_,_=annotate(rows,{'a':{'global':0,'face':None}},{'b':'decode_failed'},self.settings)
        self.assertEqual(out[0]['face_phash'],'MISSING')
        self.assertIsNone(out[0]['face_phash_distance_to_representative'])
        self.assertEqual(out[1]['dedup_role'],'ERROR')

    def test_legacy_phash_kernel_deterministic_64_bit(self):
        image=np.arange(16*16*3,dtype=np.uint8).reshape(16,16,3)
        self.assertEqual(compute_phash(image),compute_phash(image.copy()))
        self.assertTrue(0<=compute_phash(image)<2**64)


class PipelineSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.images=self.root/'images'
        self.images.mkdir()
        self.rows=[row('a'),row('b',best_score='90',face_scale_bin='UPPER_BODY'),
                   row('fatal',ranking_eligible='false',fatal_reject_reason='no_face',
                       step4_status='NOT_APPLICABLE_STEP3_FATAL')]
        for r in self.rows[:2]:
            path=self.images/r['filename']
            cv2.imwrite(str(path),np.full((16,16,3),100,dtype=np.uint8))
            r['image_sha256']=sha256_file(path)
        self.input_paths=[self.root/n for n in ('step4.csv','step4.json','step3.csv','step3.json')]
        self.write_inputs()
        self.targets={k:self.root/'reports'/name for k,name in dict(output_csv='step5_dataset_report.csv',
            summary='step5_dedup_summary.json',markdown='STEP5_DEDUP_SUMMARY.md',review_html='STEP5_DEDUP_REVIEW.html',
            pose_review='STEP5_REPRESENTATIVE_POSE_REVIEW.html',pose_summary='step5_representative_pose_summary.csv').items()}
        self.snapshots={str(p):sha256_file(p) for p in self.input_paths}

    def tearDown(self):
        self.temp.cleanup()

    def write_inputs(self):
        p4,s4,p3,s3=self.input_paths
        for path in (p3,p4):
            write_csv_atomic(path,list(self.rows[0]),self.rows)
        s3.write_text(json.dumps(dict(version='best_rank_v2.2',ranking_sha256=sha256_file(p3),total_universe=len(self.rows))),encoding='utf-8')
        s4.write_text(json.dumps(dict(step4_version='step4_pose_composition_v2',total_rows=len(self.rows),ranking_eligible_rows=2,
            input_report_sha256=sha256_file(p3),input_summary_sha256=sha256_file(s3),output_csv_sha256=sha256_file(p4),statuses={})),encoding='utf-8')

    def test_preflight_missing_authority_and_score_stop(self):
        preflight(*self.input_paths,self.images)
        self.rows[0]['best_score']=''
        self.write_inputs()
        with self.assertRaises(ValueError): preflight(*self.input_paths,self.images)
        self.input_paths[0].unlink()
        with self.assertRaises(FileNotFoundError): preflight(*self.input_paths,self.images)

    def v3_inputs(self):
        # STEP3 stays as originally written; only the STEP4 fixture changes pose.
        for r in self.rows:
            for key in ('yaw','pitch','roll','pose_status'):
                r['step3_'+key]=r[key]
            r['step4_version']='step4_pose_composition_v3'
        self.rows[0].update(yaw='-50',pitch='22',pose_bin='PROFILE_LEFT')
        self.write_v3_report()

    def write_v3_report(self):
        p4,s4,_,_=self.input_paths
        write_csv_atomic(p4,list(self.rows[0]),self.rows)
        summary=json.loads(s4.read_text(encoding='utf-8'))
        summary.update(step4_version='step4_pose_composition_v3',output_csv_sha256=sha256_file(p4))
        s4.write_text(json.dumps(summary),encoding='utf-8')

    def test_v3_preflight_preserves_full_rows_and_new_angles(self):
        self.v3_inputs()
        columns,rows=preflight(*self.input_paths,self.images)
        self.assertEqual([r['frame_id'] for r in rows],['a','b','fatal'])
        self.assertEqual(rows[0]['yaw'],'-50');self.assertEqual(rows[0]['step3_yaw'],'0')
        result,_,_=annotate(rows,hashed(rows),{},rules())
        for before,after in zip(rows,result):
            for key,value in before.items():self.assertEqual(after[key],value)

    def test_v3_missing_alias_and_tampered_score_blocked(self):
        self.v3_inputs()
        for key in ('step3_yaw','best_score','image_sha256'):
            saved=self.rows[0][key];self.rows[0][key]='tampered'
            self.write_v3_report()
            with self.assertRaises(ValueError):preflight(*self.input_paths,self.images)
            self.rows[0][key]=saved
        for row in self.rows:row.pop('step3_roll')
        self.write_v3_report()
        with self.assertRaises(ValueError):preflight(*self.input_paths,self.images)

    def test_v3_missing_pose_remains_exact_only(self):
        self.v3_inputs()
        self.rows[0].update(yaw='',pitch='',roll='',pose_status='NOT_EVALUABLE',
                            pose_bin='NOT_EVALUABLE',step4_status='NOT_EVALUABLE')
        self.write_v3_report()
        _,rows=preflight(*self.input_paths,self.images)
        self.assertEqual(near_evidence(rows[0],rows[1],{'global':0,'face':0},{'global':0,'face':0},rules()),[])
        out,_,edges=annotate(rows,hashed(rows),{},rules())
        # Identical fixture images still form the established exact-SHA edge.
        self.assertTrue(any('EXACT_DUPLICATE' in edge[2] for edge in edges))
        self.assertEqual(len(out),3)
        self.assertEqual(out[0]['representative_frame_id'],'b') # unchanged BEST90 priority

    def test_v3_angle_uses_new_pose_not_step3_alias(self):
        self.v3_inputs()
        _,rows=preflight(*self.input_paths,self.images)
        self.assertEqual(near_evidence(rows[0],rows[1],{'global':0,'face':0},{'global':0,'face':0},rules()),[])
        old=copy.deepcopy(rows[0]);old.update(yaw=old['step3_yaw'],pitch=old['step3_pitch'])
        self.assertTrue(near_evidence(old,rows[1],{'global':0,'face':0},{'global':0,'face':0},rules()))

    def test_mixed_v2_v3_is_rejected(self):
        self.v3_inputs();self.rows[1]['step4_version']='step4_pose_composition_v2'
        self.write_v3_report()
        with self.assertRaises(ValueError):preflight(*self.input_paths,self.images)

    def test_published_versions_follow_authoritative_summary(self):
        for version in ('step4_pose_composition_v2','step4_pose_composition_v3'):
            if version.endswith('v3'):self.v3_inputs()
            snapshots={str(p):sha256_file(p) for p in self.input_paths}
            summary=publish(self.rows,hashed(self.rows),{},rules(),self.targets,self.images,snapshots)
            self.assertEqual(summary['input_versions'],['best_rank_v2.2',version])

    def test_version_metadata_mismatch_stops_publication(self):
        self.v3_inputs()
        snapshots={str(p):sha256_file(p) for p in self.input_paths}
        self.assertEqual(authoritative_input_versions(self.rows,snapshots)[1],'step4_pose_composition_v3')
        self.rows[0]['step4_version']='step4_pose_composition_v2'
        with self.assertRaises(ValueError):authoritative_input_versions(self.rows,snapshots)

    def test_preflight_lineage_unique_and_bbox_blockers(self):
        for key,value in (('temporal_index',''),('video_id',''),('face_bbox',''),('image_sha256','bad')):
            original=self.rows[0][key]
            self.rows[0][key]=value
            self.write_inputs()
            with self.assertRaises(ValueError): preflight(*self.input_paths,self.images)
            self.rows[0][key]=original

    def test_stale_input_missing_source_duplicate_identity_stop(self):
        p4,s4,p3,s3=self.input_paths
        p4.write_bytes(p4.read_bytes()+b'\n')
        with self.assertRaises(ValueError): preflight(*self.input_paths,self.images)
        self.write_inputs()
        (self.images/'a.png').unlink()
        with self.assertRaises(ValueError): preflight(*self.input_paths,self.images)
        self.rows[1]['frame_id']='a'
        self.write_inputs()
        with self.assertRaises(ValueError): preflight(*self.input_paths,self.images)

    def test_pose_retention_and_cluster_accounting_no_rare_pose_boost(self):
        rows=[row('a',pose_bin='PROFILE_LEFT'),row('b',pose_bin='PROFILE_LEFT',best_score='90')]
        out,clusters,edges=annotate(rows,hashed(rows),{},rules())
        summary,cross=summarize(out,clusters,edges)
        self.assertEqual(summary['pose_retention']['PROFILE_LEFT']['retention_ratio'],.5)
        self.assertEqual(summary['pose_retention']['PROFILE_LEFT']['status'],'POSE_RETENTION_WARNING')
        self.assertEqual(summary['total_analyzed'],2)
        self.assertEqual(sum(summary['roles'].values()),2)
        self.assertEqual(sum(r['after_count'] for r in cross),1)

    def test_actual_tiny_image_hash_read_only_and_fatal_skip(self):
        before={p.name:sha256_file(p) for p in self.images.iterdir()}
        hashes,errors=hash_sources(self.rows,self.images)
        self.assertFalse(errors)
        self.assertEqual(set(hashes),{'a','b'})
        self.assertEqual(before,{p.name:sha256_file(p) for p in self.images.iterdir()})

    def test_sha_and_decode_errors_are_explicit(self):
        self.rows[0]['image_sha256']='a'*64
        _,errors=hash_sources(self.rows,self.images)
        self.assertIn('SHA256',errors['a'])
        path=self.images/'b.png'
        path.write_bytes(b'not_image')
        self.rows[1]['image_sha256']=sha256_file(path)
        _,errors=hash_sources(self.rows,self.images)
        self.assertIn('decode',errors['b'])

    def publish(self, partial=False, errors=None):
        hashes=hashed(self.rows)
        if partial: hashes.pop('b')
        if errors: hashes.pop('b')
        return publish(self.rows,hashes,errors or {},rules(),self.targets,self.images,self.snapshots,partial)

    def test_full_partial_and_failure_do_not_replace_good_output(self):
        self.publish()
        before={key:sha256_file(p) for key,p in self.targets.items()}
        summary=self.publish(partial=True)
        self.assertEqual(summary['publication_status'],'PARTIAL')
        self.assertEqual(before,{key:sha256_file(p) for key,p in self.targets.items()})
        summary=self.publish(errors={'b':'decode_failed'})
        self.assertEqual(summary['publication_status'],'FAILED')
        self.assertEqual(before,{key:sha256_file(p) for key,p in self.targets.items()})

    def test_publication_rollback_after_replace_failure(self):
        self.publish()
        before={key:sha256_file(p) for key,p in self.targets.items()}
        import step5_dedup_v2 as module
        real=module.os.replace
        fail_target=self.targets['pose_review']
        failed=[]
        def replacement(src,dst):
            if Path(dst)==fail_target and not failed:
                failed.append(True)
                raise PermissionError('synthetic locked gallery')
            return real(src,dst)
        with patch.object(module.os,'replace',side_effect=replacement):
            with self.assertRaises(PermissionError): self.publish()
        self.assertEqual(before,{key:sha256_file(p) for key,p in self.targets.items()})

    def test_galleries_roles_order_source_links_no_selection(self):
        self.rows[1]['review_state']='REVIEW_REJECT'
        out,clusters,edges=annotate(self.rows,hashed(self.rows),{},rules())
        summary,cross=summarize(out,clusters,edges)
        cluster,gallery=galleries(out,clusters,summary,cross,self.images,self.targets['review_html'],self.targets['pose_review'])
        self.assertNotIn('data-role="DUPLICATE_MEMBER"',gallery)
        self.assertIn('data-role="REPRESENTATIVE"',gallery)
        self.assertIn('data-role="DUPLICATE_MEMBER"',cluster)
        self.assertIn('>b</td>',gallery)
        self.assertNotIn('>a</td>',gallery)
        self.assertIn('UPPER_BODY',gallery)
        positions=[gallery.index('<h2>'+p+'</h2>') for p in ('FRONTAL','THREE_QUARTER_LEFT','THREE_QUARTER_RIGHT','PROFILE_LEFT','PROFILE_RIGHT','NOT_EVALUABLE')]
        self.assertEqual(positions,sorted(positions))
        self.assertIn('../images/b.png',gallery)
        self.assertIn('STEP5_DEDUP_REVIEW.html#DUP_',gallery)
        self.assertFalse(summary['quotas_applied'])
        self.assertFalse(summary['final_training_selection'])

    def test_gallery_preserves_stored_bins_sort_and_no_human_membership(self):
        rows=[row('z',video_id='z',pose_bin='PROFILE_LEFT',face_scale_bin='CLOSE_UP',best_score='90'),
              row('y',video_id='y',pose_bin='PROFILE_LEFT',face_scale_bin='CLOSE_UP',best_score='80')]
        out,clusters,edges=annotate(rows,hashed(rows),{},rules())
        summary,cross=summarize(out,clusters,edges)
        _,gallery=galleries(out,clusters,summary,cross,self.images,self.targets['review_html'],self.targets['pose_review'])
        self.assertEqual(out[0]['pose_bin'],'PROFILE_LEFT')  # yaw0 is deliberately not reclassified
        self.assertLess(gallery.index('>z</td>'),gallery.index('>y</td>'))
        self.assertEqual(summary['after']['pose']['PROFILE_LEFT'],2)

    def test_output_source_and_input_overlap_rejected(self):
        targets=dict(self.targets,output_csv=self.input_paths[0])
        with self.assertRaises(ValueError): validate_targets(targets,self.input_paths,self.images)
        targets=dict(self.targets,pose_review=self.images/'review.html')
        with self.assertRaises(ValueError): validate_targets(targets,self.input_paths,self.images)


if __name__=='__main__': unittest.main()
