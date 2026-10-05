"""Complete listing preserves existing results and explicitly includes pending stills."""
import tempfile
from pathlib import Path
import unittest
from build_step3_all_images_report import combined_rows


class AllImagesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()

    def test_all_stills_included_without_invented_acceptance(self):
        video=dict(filename='video/frame.png',diagnostic_state='PASS',face_eligible='true',face_gate_reason='eligible',face_laplacian_canonical_192='40')
        still=dict(filename='stills/photo.jpg',laplacian_score='200',image_sha256='photo-hash')
        rows=combined_rows([video],[still],'formal-generation','still-generation',self.root)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['face_laplacian_canonical_192'],'40')
        self.assertEqual(rows[0]['diagnostic_state'],'PASS')
        self.assertEqual(rows[1]['diagnostic_state'],'NOT_EVALUATED')
        self.assertEqual(rows[1]['face_eligible'],'')
        self.assertEqual(rows[1]['dataset_generation_id'],'still-generation')
        self.assertEqual(rows[1]['laplacian_score'],'200')
        self.assertIn('HYPERLINK',rows[1]['image_open'])
        self.assertNotIn('selection_group',rows[1])
        self.assertNotIn('input_kind',video)

    def test_duplicate_input_identity_rejected(self):
        with self.assertRaises(ValueError):
            combined_rows([dict(filename='same.png')],[dict(filename='same.png')],'v','s',self.root)

    def test_link_escape_and_review_outputs_rejected(self):
        for filename in ('../outside.png','reports/reject/copy.png'):
            with self.subTest(filename=filename),self.assertRaises(ValueError):
                combined_rows([], [dict(filename=filename)],'v','s',self.root)
