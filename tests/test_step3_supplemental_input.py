"""Tiny temporary inputs only; no production inference."""
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import test_image_metrics as fixtures
import test_step3_audit as audit_fixtures
import face_quality_gate as gate
from common.config import load_config
from common.step3_audit import validate_input


class SupplementalInputTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.MetricsTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.formal=self.fixture.image()
        self.manifests=self.fixture.generation()
        self.still=self.fixture.image('additional_stills','portrait.png')
        self.assertEqual(self.fixture.run_with_stills(self.manifests,self.still.parent),0)
        self.report=self.fixture.root/'report.csv'

    def validate(self):
        return validate_input(self.report,self.fixture.input,self.manifests)

    def test_formal_universe_excludes_only_explicit_recorded_still_input(self):
        expected,generation,digest=self.validate()
        self.assertEqual(expected,{'subject_v01':1})
        self.assertEqual(generation['frame_count'],1)
        self.assertEqual(len(digest),64)

    def test_changed_or_missing_still_blocks_validation(self):
        self.still.write_bytes(b'changed after STEP2')
        with self.assertRaisesRegex(ValueError,'supplemental input generation mismatch'): self.validate()
        self.still.unlink()
        with self.assertRaisesRegex(ValueError,'no supported images'): self.validate()

    def test_unknown_directory_and_corrupt_formal_frame_still_fail(self):
        unexpected=self.fixture.image('undeclared_stills','portrait.png')
        with self.assertRaisesRegex(ValueError,'per-video count mismatch'): self.validate()
        unexpected.unlink()
        self.formal.write_bytes(b'corrupt formal frame')
        with self.assertRaisesRegex(ValueError,'frame content differs'): self.validate()

    def test_gate_main_small_mocked_inference_after_real_preflight(self):
        still_before=self.still.read_bytes()
        config=load_config(ROOT/'config/config.example.yaml')
        config['paths'].update(raw_frames_dir=str(self.fixture.input),manifests_dir=str(self.manifests),
                               facegate_review_dir=str(self.fixture.root/'review'),facegate_crops_dir=str(self.fixture.root/'crops'))
        config['step3_face_gate'].update(report=str(self.report),output=str(self.fixture.root/'step3_dataset_report.csv'))
        with patch.object(gate,'load_for_cli',return_value=config),patch.object(gate,'mp',audit_fixtures.backend(0)),patch.object(sys,'argv',['face_quality_gate.py','--limit','1']),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(),0)
        partial=self.fixture.root/'step3_dataset_report.partial.csv'
        self.assertTrue(partial.is_file())
        self.assertFalse((self.fixture.root/'step3_dataset_report.csv').exists())
        self.assertEqual(self.still.read_bytes(),still_before)


if __name__=='__main__': unittest.main()
