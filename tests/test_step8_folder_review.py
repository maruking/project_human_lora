import copy
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from test_step7_candidate_selection_v2 import row
from common.config import load_config
from common.folder_review import (POSES,pose_folder,manifest_rows,stage_review,install_review,accepted_ids,selection_rows)
from step8_folder_review import prepare,collect,load_step9_selection,preflight,encoded_csv


def fixture(base,n=8):
    images=base/'images';images.mkdir();root=base/'work/step8_review'
    settings=copy.deepcopy(load_config()['step8_folder_review'])
    rows=[]
    for i in range(n):
        r=row(i,pose_bin=POSES[i%6],face_scale_bin=('CLOSE_UP','UPPER_BODY','FULL_BODY')[i%3],vertical_pose=('LEVEL','LOOKING_UP','LOOKING_DOWN')[i%3],
            ranking_version='best_rank_v2.2',step7_version='step7_quality_coverage_v2.2',candidate_pool_eligible='true',candidate_pool_selected='true',
            quality_guard_member='true',rare_profile_candidate='false',quality_guard_order=str(i+1),selection_reason='BEST_QUALITY_CORE')
        pixels=('synthetic'+str(i)).encode();(images/r['filename']).write_bytes(pixels);r['image_sha256']=hashlib.sha256(pixels).hexdigest();rows.append(r)
    return settings,root,images,rows


def materialize(base,n=8):
    settings,root,images,rows=fixture(base,n)
    records,stage,session=stage_review(rows,settings,root,images,base,{})
    install_review(stage,root,settings)
    return settings,root,images,rows,records,session


class FolderReviewTests(unittest.TestCase):
    def test_01_each_candidate_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            self.assertEqual(len(list((root/'00_ALL_RANKED').iterdir())),len(rows))
            self.assertEqual({r['frame_id'] for r in records},{r['frame_id'] for r in rows})

    def test_02_stored_pose_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            self.assertTrue(all(Path(r['full_review_path']).parent.name=='00_ALL_RANKED' for r in records))

    def test_03_accept_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,*_=materialize(Path(tmp))
            self.assertTrue(not list((root/'99_ACCEPT').iterdir()))

    def test_04_nonempty_accept_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);s,root,images,rows,records,_=materialize(base)
            shutil.copy2(records[0]['full_review_path'],records[0]['accept_review_path'])
            before=Path(records[0]['accept_review_path']).read_bytes()
            with self.assertRaisesRegex(ValueError,'ACCEPT is non-empty'):stage_review(rows,s,root,images,base,{})
            self.assertEqual(Path(records[0]['accept_review_path']).read_bytes(),before)

    def test_05_source_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);s,root,images,rows=fixture(base)
            before={p.name:p.read_bytes() for p in images.iterdir()};records,stage,_=stage_review(rows,s,root,images,base,{})
            install_review(stage,root,s);self.assertEqual(before,{p.name:p.read_bytes() for p in images.iterdir()})

    def test_06_filename_manifest_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            self.assertTrue(records[0]['review_filename'].startswith('O0001_R0001_B100.0_'))
            self.assertEqual(records[0]['frame_id'],rows[0]['frame_id'])

    def test_07_duplicate_frame_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            first=records[0];shutil.copy2(first['full_review_path'],first['accept_review_path'])
            shutil.copy2(first['full_review_path'],root/'99_ACCEPT'/('extra_'+first['review_filename']))
            with self.assertRaisesRegex(ValueError,'Unknown ACCEPT'):accepted_ids(records,root,s)

    def test_08_unknown_file_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            (root/'99_ACCEPT/unknown.png').write_bytes(b'unknown')
            with self.assertRaisesRegex(ValueError,'Unknown ACCEPT'):accepted_ids(records,root,s)

    def test_09_current_reject_not_finalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp));r=records[0]
            shutil.copy2(r['full_review_path'],r['accept_review_path'])
            with self.assertRaisesRegex(ValueError,'Human Reject'):accepted_ids(records,root,s,{r['frame_id']})

    def test_10_below35_status(self):
        s=load_config()['step8_folder_review'];rows=[row(i,selection_reason='BEST_QUALITY_CORE') for i in range(50)]
        records=manifest_rows(rows,s,Path('fixture'))
        self.assertEqual(selection_rows(rows,records,{r['frame_id'] for r in rows[:34]},s,'fixture')[1]['selection_status'],'NEED_MORE_SELECTION')

    def test_11_35_to45_valid(self):
        s=load_config()['step8_folder_review'];rows=[row(i,selection_reason='BEST_QUALITY_CORE') for i in range(50)];records=manifest_rows(rows,s,Path('fixture'))
        for count in (35,40,45):self.assertTrue(selection_rows(rows,records,{r['frame_id'] for r in rows[:count]},s,'fixture')[1]['finalization_allowed'])

    def test_12_above45_status(self):
        s=load_config()['step8_folder_review'];rows=[row(i,selection_reason='BEST_QUALITY_CORE') for i in range(50)];records=manifest_rows(rows,s,Path('fixture'))
        self.assertEqual(selection_rows(rows,records,{r['frame_id'] for r in rows[:46]},s,'fixture')[1]['selection_status'],'TOO_MANY_SELECTED')

    def test_13_guidance_warning_not_block(self):
        s=load_config()['step8_folder_review'];rows=[row(i,selection_reason='BEST_QUALITY_CORE') for i in range(35)];records=manifest_rows(rows,s,Path('fixture'))
        full,summary=selection_rows(rows,records,{r['frame_id'] for r in rows},s,'fixture')
        self.assertTrue(summary['finalization_allowed']);self.assertTrue(summary['guidance_warnings'])

    def test_14_scale_counts(self):
        self.check_distribution('face_scale_bin','UPPER_BODY')

    def test_15_vertical_counts(self):
        self.check_distribution('vertical_pose','LEVEL')

    def check_distribution(self,field,label):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,session=materialize(Path(tmp));accepted={r['frame_id'] for r in rows}
            summary=selection_rows(rows,records,accepted,s,session)[1]
            self.assertEqual(summary['distributions'][field][label],sum(r[field]==label for r in rows))

    def test_16_not_selected_not_bad(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,session=materialize(Path(tmp))
            full,_=selection_rows(rows,records,set(),s,session)
            self.assertTrue(all(r['step8_decision']=='STEP8_NOT_SELECTED' for r in full))

    def test_17_full_row_traceability(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,session=materialize(Path(tmp))
            full,_=selection_rows(rows+[row(20,dedup_role='DUPLICATE_MEMBER')],records,set(),s,session)
            self.assertEqual(len(full),len(rows)+1);self.assertEqual(full[-1]['step8_decision'],'NOT_APPLICABLE_NOT_IN_REVIEW_POOL')
            self.assertTrue(all(all(out[k]==v for k,v in old.items()) for old,out in zip(rows,full)))

    def test_18_validated_csv_handoff_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);s,root,images,rows=fixture(base,45)
            paths=dict(review_root=root,manifest=base/'step8_review_manifest.csv',preparation_summary=base/'step8_review_preparation.json',selection_csv=base/'step8_human_selection.csv',summary=base/'step8_selection_summary.json',markdown=base/'STEP8_SELECTION_SUMMARY.md')
            config=dict(step8_folder_review=s)
            upstream=patch('step8_folder_review.preflight',return_value=(rows,rows,set(),{}))
            with upstream,patch('step8_folder_review.ROOT',base):
                prepare(config,paths,images)
                with paths['manifest'].open(encoding='utf-8-sig') as handle:records=list(csv.DictReader(handle))
                for r in records[:35]:shutil.copy2(r['full_review_path'],r['accept_review_path'])
                summary=collect(config,paths,images);self.assertTrue(summary['finalization_allowed'])
                with patch('step8_folder_review.paths_for',return_value=(s,paths,images)):
                    selected=load_step9_selection(config)
                    self.assertEqual(len(selected),35);self.assertTrue(all(r['step8_decision']=='STEP8_ACCEPT' for r in selected))
                    # Interaction surface is disposable; CSV controls downstream.
                    for r in records[:35]:Path(r['accept_review_path']).unlink()
                    self.assertEqual(len(load_step9_selection(config)),35)

    def test_reset_archives_human_choices(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);s,root,images,rows,records,_=materialize(base)
            r=records[0];shutil.copy2(r['full_review_path'],r['accept_review_path'])
            _,stage,_=stage_review(rows,s,root,images,base,{},reset=True)
            archive=install_review(stage,root,s,reset=True)
            self.assertTrue((archive/Path(r['accept_review_path']).relative_to(root)).is_file())
            self.assertFalse(Path(r['accept_review_path']).exists())

    def test_full_missing_stops_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp));Path(records[0]['full_review_path']).unlink()
            with self.assertRaisesRegex(ValueError,'VIEW must retain'):accepted_ids(records,root,s)

    def test_edited_accept_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp));Path(records[0]['accept_review_path']).write_bytes(b'edited')
            with self.assertRaisesRegex(ValueError,'edited/replaced'):accepted_ids(records,root,s)

    def test_source_overlapping_root_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);s,root,images,rows=fixture(base)
            with self.assertRaises(ValueError):stage_review(rows,s,images,images,base,{})

    def test_stale_step7_reject_patch_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);s,root,images,rows=fixture(base,1)
            from common.candidate_selection_v22 import FIELDS
            upstream={k:v for k,v in rows[0].items() if k not in FIELDS}
            full=dict(upstream,**{k:rows[0].get(k,'') for k in FIELDS})
            paths={k:base/name for k,name in dict(full_csv='full.csv',candidates_csv='candidates.csv',step7_summary='summary.json').items()}
            paths['full_csv'].write_bytes(encoded_csv([full]));paths['candidates_csv'].write_bytes(encoded_csv([full]))
            paths['step7_summary'].write_text(json.dumps(dict(step7_version='step7_quality_coverage_v2.2',publication_status='COMPLETE',settings=load_config()['step7_candidates_v2'],input_hashes={},selected_review_pool=1,artifact_sha256={'output_csv':hashlib.sha256(paths['full_csv'].read_bytes()).hexdigest(),'candidates_csv':hashlib.sha256(paths['candidates_csv'].read_bytes()).hexdigest()})))
            config=load_config()
            with patch('step8_folder_review.upstream_preflight',return_value=([upstream],{})),patch('step8_folder_review.review_exclusions',return_value=({full['frame_id']},{})):
                with self.assertRaisesRegex(ValueError,'Reject patch absent'):preflight(config,paths,images)

    def test_review_surface_never_pipeline_input(self):
        from common.step3_review import require_source,review_roots
        cfg=load_config();review_roots(cfg)
        for p in (Path('work/step8_review/FULL/image.png'),Path('work/.step8_stage_example/image.png')):
            with self.assertRaises(ValueError):require_source(p)

    def test_normal_step9_is_guarded_before_legacy_inference(self):
        text=(Path(__file__).resolve().parents[1]/'bat/09_selective_restoration_gpu.bat').read_text(encoding='utf-8')
        check=text.index('handoff-check');stop=text.index('exit /b 1',check);legacy=text.index('scripts\\selective_restoration.py')
        self.assertLess(check,stop);self.assertLess(stop,legacy)


if __name__=='__main__':unittest.main()
