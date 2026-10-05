"""STEP1 organization tests use tiny byte fixtures and no AI/video inference."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common.video_manifest import (MANIFEST_FIELDS, ManifestLocked, NormalizationError,
    manifest_lock, materialize_copy, plan_normalization, read_manifest, scan_videos,
    sha256_file, video_id, write_csv_atomic)


class VideoManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'raw'
        self.source.mkdir()
        self.videos = self.root / 'work/videos'
        self.frames = self.root / 'work/frames_raw'
        self.manifest = self.root / 'work/manifests/video_manifest.csv'
        self.addCleanup(self.tmp.cleanup)

    def source_file(self, name, content=None):
        path = self.source / name
        path.write_bytes(content or name.encode())
        return path

    def plan(self, rows=None):
        sources, _ = scan_videos(self.source, {'.mp4', '.mov'})
        return plan_normalization(sources, rows or [], 'subject', self.videos, self.frames)

    def persist_and_copy(self, rows):
        write_csv_atomic(self.manifest, MANIFEST_FIELDS, rows)
        for row in rows:
            materialize_copy(row)

    def test_naming_1_71_100_and_unicode(self):
        for index, expected in [(1, 'subject_v01'), (71, 'subject_v71'), (100, 'subject_v100')]:
            self.assertEqual(video_id('subject', index) + '.mp4', expected + '.mp4')
        self.assertEqual(video_id('人物', 1), '人物_v01')
        for subject in ('../escape', '', 'bad:name', 'subject.', ' name'):
            with self.assertRaises(NormalizationError): video_id(subject, 1)

    def test_natural_stable_order(self):
        files = [self.source_file(n) for n in ('Clip10.mp4', 'clip2.mp4', 'clip01.mp4', 'clip1.mp4')]
        first = plan_normalization(files, [], 'subject', self.videos, self.frames)
        second = plan_normalization(list(reversed(files)), [], 'subject', self.videos, self.frames)
        self.assertEqual([(r['original_filename'], r['video_id']) for r in first],
                         [(r['original_filename'], r['video_id']) for r in second])
        self.assertEqual([r['original_filename'] for r in first], ['clip01.mp4', 'clip1.mp4', 'clip2.mp4', 'Clip10.mp4'])

    def test_manifest_idempotence_originals_retained_and_independent_copy(self):
        original = self.source_file('download.mp4', b'original bytes')
        rows = self.plan()
        self.persist_and_copy(rows)
        again = self.plan(read_manifest(self.manifest))
        self.assertEqual(again[0]['video_id'], 'subject_v01')
        self.assertEqual(again[0]['original_filename'], original.name)
        self.assertEqual(materialize_copy(again[0]), 'ALREADY_NORMALIZED')
        self.assertEqual(original.read_bytes(), b'original bytes')
        normalized = Path(rows[0]['normalized_path'])
        self.assertFalse(original.samefile(normalized))
        normalized.write_bytes(b'working edit')
        self.assertEqual(original.read_bytes(), b'original bytes')
        with self.assertRaisesRegex(NormalizationError, 'collision/incomplete'): self.plan(read_manifest(self.manifest))

    def test_new_video_appends_after_71(self):
        for index in range(1, 72): self.source_file(f'clip{index}.mp4')
        rows = self.plan()
        write_csv_atomic(self.manifest, MANIFEST_FIELDS, rows)
        # Even before copies complete, reserved indices remain durable.
        self.source_file('000-new.mp4')
        again = self.plan(read_manifest(self.manifest))
        self.assertEqual(again[-1]['video_id'], 'subject_v72')
        self.assertEqual(again[-1]['original_filename'], '000-new.mp4')
        self.assertEqual([r['original_filename'] for r in rows], [r['original_filename'] for r in again[:71]])

    def test_already_normalized_and_mixed_sources(self):
        self.source_file('subject_v01.mp4')
        self.source_file('subject_v71.mov')
        self.source_file('aaa-download.mp4')
        rows = self.plan()
        self.assertEqual([r['video_id'] for r in rows], ['subject_v01', 'subject_v71', 'subject_v72'])
        self.persist_and_copy(rows)
        self.assertEqual([r['video_id'] for r in self.plan(read_manifest(self.manifest))],
                         ['subject_v01', 'subject_v71', 'subject_v72'])

    def test_duplicate_normalized_id_across_extensions_rejected(self):
        self.source_file('subject_v01.mp4')
        self.source_file('subject_v01.mov')
        with self.assertRaisesRegex(NormalizationError, 'collision'): self.plan()

    def test_destination_collision_never_overwrites(self):
        self.source_file('download.mp4')
        self.videos.mkdir(parents=True)
        destination = self.videos / 'subject_v01.mp4'
        destination.write_bytes(b'unrelated')
        with self.assertRaisesRegex(NormalizationError, 'collision'): self.plan()
        self.assertEqual(destination.read_bytes(), b'unrelated')

    def test_untracked_existing_frames_not_adopted(self):
        self.source_file('download.mp4')
        directory = self.frames / 'subject_v01'
        directory.mkdir(parents=True)
        image = directory / 'subject_v01_001.png'
        image.write_bytes(b'older dataset frame')
        with self.assertRaisesRegex(NormalizationError, 'Untracked frame directory'): self.plan()
        self.assertEqual(image.read_bytes(), b'older dataset frame')

    def test_destination_appears_after_plan(self):
        self.source_file('download.mp4')
        row = self.plan()[0]
        self.videos.mkdir(parents=True)
        destination = Path(row['normalized_path'])
        destination.write_bytes(b'other')
        with self.assertRaisesRegex(NormalizationError, 'collision'): materialize_copy(row)
        self.assertEqual(destination.read_bytes(), b'other')

    def test_interrupted_execution_recovery(self):
        self.source_file('clip1.mp4')
        self.source_file('clip2.mp4')
        rows = self.plan()
        write_csv_atomic(self.manifest, MANIFEST_FIELDS, rows)
        materialize_copy(rows[0])
        # Crash between publication and manifest status update.
        resumed = self.plan(read_manifest(self.manifest))
        self.assertEqual(resumed[0]['_plan'], 'ALREADY_NORMALIZED')
        self.assertEqual(resumed[1]['_plan'], 'COPY')
        for row in resumed: materialize_copy(row)
        self.assertEqual([r['video_id'] for r in resumed], ['subject_v01', 'subject_v02'])

    def test_copy_failure_does_not_publish_partial_file(self):
        source = self.source_file('download.mp4')
        row = self.plan()[0]
        with patch('common.video_manifest.shutil.copyfileobj', side_effect=OSError('interrupted copy')):
            with self.assertRaises(OSError): materialize_copy(row)
        self.assertFalse(Path(row['normalized_path']).exists())
        self.assertEqual(source.read_bytes(), b'download.mp4')

    def test_manifest_source_change_fails(self):
        source = self.source_file('download.mp4', b'content-a')
        rows = self.plan()
        write_csv_atomic(self.manifest, MANIFEST_FIELDS, rows)
        source.write_bytes(b'content-b')
        with self.assertRaisesRegex(NormalizationError, 'contents changed'): self.plan(read_manifest(self.manifest))

    def test_missing_source_reserves_id(self):
        source = self.source_file('download.mp4')
        rows = self.plan()
        source.unlink()
        self.source_file('new.mp4')
        again = self.plan(rows)
        self.assertEqual(again[0]['_plan'], 'SOURCE_MISSING')
        self.assertEqual(again[1]['video_id'], 'subject_v02')

    def test_frame_directory_and_supported_extensions(self):
        self.source_file('download.MP4')
        self.source_file('notes.txt')
        files, skipped = scan_videos(self.source, {'.mp4'})
        self.assertEqual(len(files), 1)
        self.assertEqual(skipped, ['notes.txt'])
        row = self.plan()[0]
        self.assertEqual(row['_frame_directory'], str(self.frames / 'subject_v01'))
        self.assertEqual(row['normalized_filename'], 'subject_v01.mp4')

    def test_lock_excludes_other_process_and_releases(self):
        import subprocess
        lock = self.root / 'manifest.lock'
        code = 'import sys; sys.path.insert(0,sys.argv[1]); from common.video_manifest import manifest_lock;\nwith manifest_lock(__import__("pathlib").Path(sys.argv[2])): pass'
        with manifest_lock(lock):
            run = subprocess.run([sys.executable, '-c', code, str(ROOT/'scripts'), str(lock)], capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn(b'Another Step1 process', run.stderr)
        with manifest_lock(lock): pass


if __name__ == '__main__':
    unittest.main()
