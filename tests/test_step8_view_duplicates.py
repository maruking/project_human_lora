import shutil
from pathlib import Path
import tempfile
import unittest
from common.folder_review import accepted_ids
from test_step8_folder_review import materialize

class ViewDuplicateTests(unittest.TestCase):
    def test_exact_same_view_duplicate_not_an_accept(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            r=records[0];duplicate=Path(r['full_review_path']).with_name('extra-copy.png')
            shutil.copy2(r['full_review_path'],duplicate)
            shutil.copy2(r['full_review_path'],r['accept_review_path'])
            ids,hashes=accepted_ids(records,root,s)
            self.assertEqual(ids,{r['frame_id']});self.assertIn(str(duplicate.resolve()),hashes)
    def test_extra_unknown_bytes_still_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            (root/'00_ALL_RANKED/unknown.png').write_bytes(b'unknown-image')
            with self.assertRaisesRegex(ValueError,'Unknown/changed extra VIEW file'):
                accepted_ids(records,root,s)
    def test_known_image_in_wrong_category_still_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            shutil.copy2(records[0]['full_review_path'],root/'01_BY_SHOT/FULL_BODY/extra.png')
            with self.assertRaisesRegex(ValueError,'Unknown/changed extra VIEW file'):
                accepted_ids(records,root,s)
    def test_missing_expected_copy_not_replaced_by_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            p=Path(records[0]['full_review_path']);shutil.copy2(p,p.with_name('extra-copy.png'));p.unlink()
            with self.assertRaisesRegex(ValueError,'missing 1'):
                accepted_ids(records,root,s)
    def test_accept_duplicate_filename_still_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            s,root,images,rows,records,_=materialize(Path(tmp))
            shutil.copy2(records[0]['full_review_path'],root/'99_ACCEPT/extra-copy.png')
            with self.assertRaisesRegex(ValueError,'Unknown ACCEPT file'):
                accepted_ids(records,root,s)

    def test_collect_reports_ignored_duplicate_without_changing_accept_count(self):
        import csv
        from unittest.mock import patch
        from test_step8_folder_review import fixture
        from step8_folder_review import prepare,collect
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);settings,root,images,rows=fixture(base,45)
            paths=dict(review_root=root,manifest=base/'manifest.csv',preparation_summary=base/'prep.json',selection_csv=base/'selection.csv',summary=base/'summary.json',markdown=base/'summary.md')
            config=dict(step8_folder_review=settings)
            with patch('step8_folder_review.preflight',return_value=(rows,rows,set(),{})),patch('step8_folder_review.ROOT',base):
                prepare(config,paths,images)
                with paths['manifest'].open(encoding='utf-8-sig') as f:records=list(csv.DictReader(f))
                for r in records[:40]:shutil.copy2(r['full_review_path'],r['accept_review_path'])
                shutil.copy2(records[0]['full_review_path'],root/'00_ALL_RANKED/extra-copy.png')
                summary=collect(config,paths,images)
                self.assertEqual(summary['accepted_total'],40)
                self.assertEqual(summary['view_duplicate_copies_ignored_count'],1)
                self.assertEqual(len(summary['view_duplicate_copies_ignored']),1)

if __name__=='__main__':unittest.main()
