"""Tiny file fixtures only: no FFmpeg, source videos, or frame processing."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import prepare_step1_upscale as prep
from common.video_manifest import MANIFEST_FIELDS, read_manifest, sha256_file, write_csv_atomic


class UpscaleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root/'original'
        self.upscale = self.source/'upscale'
        self.upscale.mkdir(parents=True)
        self.normalized = self.root/'work/videos'; self.normalized.mkdir(parents=True)
        self.manifests = self.root/'work/manifests'; self.manifests.mkdir()
        self.frames = self.root/'work/frames'; self.frames.mkdir()
        (self.frames/'human-still.png').write_bytes(b'keep')
        copy = self.normalized/'person_v07.mp4'; copy.write_bytes(b'original')
        self.output = self.upscale/'download.mp4'; self.output.write_bytes(b'upscaled')
        self.old = dict(video_id='person_v07',subject_name='person',index='7',
                        original_filename='download.mp4',normalized_filename=copy.name,
                        original_path=str(self.source/'download.mp4'),normalized_path=str(copy),
                        extension='.mp4',file_size='8',sha256=sha256_file(copy),created_at='historical',
                        normalization_status='READY',normalization_error='')
        write_csv_atomic(self.manifests/'video_manifest.csv',MANIFEST_FIELDS,[self.old])
        (self.manifests/'step1_summary.json').write_text('{"status":"PASS"}')

    def migrate(self):
        prep.prepare_manifest(self.manifests,self.normalized,self.frames,self.source,
                              self.upscale,[self.output],'person')

    def test_missing_original_can_use_existing_outputs_preserving_identity_and_evidence(self):
        self.migrate()
        row = read_manifest(self.manifests/'video_manifest.csv')[0]
        self.assertEqual(row['video_id'],'person_v07')
        self.assertEqual(row['created_at'],'historical')
        self.assertEqual(row['original_path'],str(self.output))
        self.assertEqual(row['sha256'],sha256_file(self.output))
        state=json.loads((self.manifests/'step1_upscale_transition.json').read_text())
        archive=Path(state['archive'])
        self.assertEqual(read_manifest(archive/'video_manifest.csv'),[self.old])
        self.assertEqual((archive/'videos/person_v07.mp4').read_bytes(),b'original')
        self.assertFalse(state['lineage'][0]['original_present'])
        self.assertEqual((self.frames/'human-still.png').read_bytes(),b'keep')
        self.assertFalse(self.normalized.exists())
        before=(self.manifests/'step1_upscale_transition.json').read_bytes()
        self.migrate()
        self.assertEqual(before,(self.manifests/'step1_upscale_transition.json').read_bytes())

    def test_interrupted_move_resumes_without_second_archive_or_renumber(self):
        with patch.object(prep,'write_csv_atomic',side_effect=OSError('interrupted checkpoint')):
            with self.assertRaises(OSError): self.migrate()
        self.assertFalse(self.normalized.exists())
        self.assertEqual(read_manifest(self.manifests/'video_manifest.csv'),[self.old])
        self.migrate()
        self.assertEqual(read_manifest(self.manifests/'video_manifest.csv')[0]['video_id'],'person_v07')

    def test_missing_output_fails_before_archive_and_tracked_changes_are_rejected(self):
        with self.assertRaises(ValueError):
            prep.prepare_manifest(self.manifests,self.normalized,self.frames,self.source,self.upscale,[],'person')
        self.assertTrue(self.normalized.exists())
        self.migrate()
        self.output.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.migrate()

    def test_declared_bat_output_not_guessed_and_parent_traversal_rejected(self):
        processor=self.root/'processor.py'; processor.write_text('# fixture only')
        bat=self.source/'run_upscale_4k.bat'
        text=('set "CURR_DIR=%~dp0"\nset "OUT_DIR=%CURR_DIR%\\prepared"\n'
              f'%PY_CMD% "{processor}" --input "%CURR_DIR%" --output "%OUT_DIR%" %*\n')
        bat.write_text(text)
        self.assertEqual(prep.upscale_contract(self.source)[1],self.source/'prepared')
        bat.write_text(text.replace('\\prepared','\\..'))
        with self.assertRaises(ValueError): prep.upscale_contract(self.source)

    def test_main_calls_existing_bat_then_extractor_with_upscaled_input_and_separate_arguments(self):
        (self.source/'download.mp4').write_bytes(b'original')
        bat=self.source/'run_upscale_4k.bat'
        config=dict(project={'subject_name':'person'}, paths={
            'input_video_dir':str(self.source), 'normalized_video_dir':str(self.normalized),
            'manifests_dir':str(self.manifests), 'raw_frames_dir':str(self.frames)},
            step1_extract={'supported_extensions':['.mp4']})
        module=SimpleNamespace(find_ffmpeg=lambda: ('ffmpeg','ffprobe'),
                               get_video_info=lambda *a: dict(width=2160,height=3840,duration=1))
        with patch.object(sys,'argv',['prepare','--overwrite','--sample-fps','1.0']), \
             patch.object(prep,'load_config',return_value=config), \
             patch.object(prep,'upscale_contract',return_value=(bat,self.upscale,self.root/'stub.py')), \
             patch.object(prep,'processor_module',return_value=module), \
             patch.object(prep.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual(prep.main(),0)
        self.assertEqual(run.call_count,2)
        stage=run.call_args_list[0].args[0]
        self.assertEqual(stage,f'call "{bat}"')
        self.assertNotIn('--overwrite',stage)
        extractor=run.call_args_list[1].args[0]
        self.assertEqual(extractor[extractor.index('--input')+1],str(self.upscale))
        self.assertIn('--overwrite',extractor)
        self.assertEqual(extractor[extractor.index('--sample-fps')+1],'1.0')

    def test_explicit_available_only_archives_absent_mapping_without_renumbering(self):
        missing = dict(self.old,video_id='person_v08',index='8',original_filename='absent.mp4',
                       original_path=str(self.source/'absent.mp4'),normalized_filename='person_v08.mp4',
                       normalized_path=str(self.normalized/'person_v08.mp4'))
        (self.normalized/'person_v08.mp4').write_bytes(b'original')
        write_csv_atomic(self.manifests/'video_manifest.csv',MANIFEST_FIELDS,[self.old,missing])
        prep.prepare_manifest(self.manifests,self.normalized,self.frames,self.source,self.upscale,
                              [self.output],'person',available_only=True)
        self.assertEqual([r['video_id'] for r in read_manifest(self.manifests/'video_manifest.csv')],['person_v07'])
        state=json.loads((self.manifests/'step1_upscale_transition.json').read_text())
        self.assertEqual(state['inactive_rows'],[missing])


if __name__ == '__main__':
    unittest.main()
