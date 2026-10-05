"""Policy v2 integration and durable source/video organization, no AI inference."""
import ast
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import extract_frames as step
from common.frame_sampling import sampling_plan, run_ffmpeg, reusable_frames, policy_signature
from common.video_manifest import read_manifest


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.raw=self.root/'raw'; self.raw.mkdir()
        for name in ('clip10.mp4','clip2.mp4'): (self.raw/name).write_bytes(name.encode())
        self.frames=self.root/'frames'; self.normalized=self.root/'videos'
        self.manifests=self.root/'manifests'; self.reports=self.root/'reports'
        self.argv=['extract_frames.py','--input',str(self.raw),'--output',str(self.frames),
                   '--normalized-dir',str(self.normalized),'--manifest-dir',str(self.manifests)]

    def run_step(self,extra=(),duration=3,extract=None):
        def generate(binary,video,folder,identifier,plan):
            for index in range(1,plan['planned_frames']+1):
                Image.new('RGB',(12,16),(index,0,0)).save(folder/f'{identifier}_{index:03d}.png')
        with patch.object(sys,'argv',self.argv+list(extra)), \
             patch.object(step,'load_for_cli',return_value={'paths':{'reports_dir':str(self.reports)}}), \
             patch.object(step,'find_binary',return_value=Path('ffmpeg')), \
             patch.object(step,'get_video_duration',side_effect=duration if callable(duration) else None,return_value=duration if not callable(duration) else 0), \
             patch('common.frame_sampling.run_ffmpeg',side_effect=extract or generate) as extract_mock, \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return step.main(),extract_mock.call_args_list

    def test_plan_seconds_and_full_axis_cap(self):
        for duration,count in [(3,6),(10,20),(30,60),(100,120)]:
            plan=sampling_plan(duration,2,120)
            self.assertEqual(plan['planned_frames'],count)
            self.assertEqual(plan['sample_fps_effective'],2 if duration<=60 else 1.2)
            self.assertEqual(plan['sampling_duration_seconds'],duration)
        self.assertEqual(sampling_plan(0.1,2,120)['planned_frames'],1)
        for duration in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): sampling_plan(duration,2,120)

    def test_dry_run_is_read_only(self):
        before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        code,calls=self.run_step(['--dry-run'])
        self.assertEqual(code,0); self.assertFalse(calls)
        self.assertEqual(before,{p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_policy_cache_same_config_reuses(self):
        code,calls=self.run_step(); self.assertEqual(code,0); self.assertEqual(len(calls),2)
        before={p:p.read_bytes() for p in self.frames.rglob('*') if p.is_file()}
        code,calls=self.run_step(); self.assertEqual(code,0); self.assertFalse(calls)
        self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))
        summary=json.loads((self.manifests/'step1_summary.json').read_text())
        self.assertEqual(summary['frames_reused'],12); self.assertEqual(summary['frames_created'],0)
        self.assertEqual(read_manifest(self.manifests/'video_manifest.csv')[0]['original_filename'],'clip2.mp4')

    def test_config_change_rebuilds_and_archives(self):
        self.run_step(); code,calls=self.run_step(['--sample-fps','1'])
        self.assertEqual(code,0); self.assertEqual(len(calls),2)
        self.assertEqual(len(list(self.frames.rglob('*.png'))),6)
        self.assertEqual(len(list((self.root/'frames_previous').rglob('*.png'))),12)
        summary=json.loads((self.manifests/'step1_summary.json').read_text())
        self.assertEqual(summary['frames_reused'],0); self.assertEqual(summary['archived_frames'],12)

    def test_old_folder_without_metadata_not_reused(self):
        self.run_step()
        for path in self.frames.rglob('.extraction_metadata.json'): path.unlink()
        code,calls=self.run_step(); self.assertEqual(code,0); self.assertEqual(len(calls),2)
        self.assertEqual(len(list((self.root/'frames_previous').rglob('*.png'))),12)

    def test_corrupt_cached_frame_rebuilds(self):
        self.run_step(); path=next(self.frames.rglob('*.png')); path.write_bytes(b'corrupt')
        code,calls=self.run_step(); self.assertEqual(code,0); self.assertEqual(len(calls),1)
        with Image.open(path) as image: image.verify()

    def test_failure_preserves_old_data(self):
        self.run_step(); before={p:p.read_bytes() for p in self.frames.rglob('*') if p.is_file()}
        def fail(*args): raise step.ExtractionFailure(7,'fixture decoder failure')
        code,_=self.run_step(['--sample-fps','1'],extract=fail)
        self.assertEqual(code,1)
        self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))
        import csv
        with (self.manifests/'video_extraction.csv').open(encoding='utf-8-sig') as handle:
            report=list(csv.DictReader(handle))[0]
        self.assertEqual(report['ffmpeg_return_codes'],'7'); self.assertIn('subject_v01',report['error_summary'])

    def test_duration_failure_continues(self):
        def probe(video,binary):
            if video.stem=='subject_v01': raise ValueError('ffprobe duration unavailable')
            return 3
        code,calls=self.run_step(duration=probe)
        self.assertEqual(code,1); self.assertEqual(len(calls),1)
        summary=json.loads((self.manifests/'step1_summary.json').read_text())
        self.assertEqual(summary['successful'],1); self.assertEqual(summary['failed'],1)

    def test_normalize_only_and_resume(self):
        code,calls=self.run_step(['--normalize-only']); self.assertEqual(code,0); self.assertFalse(calls)
        code,calls=self.run_step(); self.assertEqual(code,0); self.assertEqual(len(calls),2)

    def test_ffmpeg_fps_command_preserves_png_q2(self):
        plan=sampling_plan(100,2,120)
        with patch('common.frame_sampling.subprocess.run') as run:
            run.return_value.returncode=0
            run_ffmpeg(Path('ffmpeg'),Path('video.mp4'),self.root,'subject_v01',plan)
        command=run.call_args.args[0]
        self.assertEqual(command[command.index('-vf')+1],'fps=1.2:round=up')
        self.assertEqual(command[command.index('-frames:v')+1],'120')
        self.assertEqual(command[command.index('-q:v')+1],'2')
        self.assertTrue(command[-1].endswith('subject_v01_%03d.png'))

    def test_end_rounding_actual_count_and_reuse(self):
        def generate(binary,video,folder,identifier,plan):
            for index in range(1,plan['planned_frames']):
                Image.new('RGB',(12,16)).save(folder/f'{identifier}_{index:03d}.png')
        code,calls=self.run_step(extract=generate)
        self.assertEqual(code,0)
        from common.metric_report import read_step1_counts
        self.assertEqual(read_step1_counts(self.manifests),{'subject_v01':5,'subject_v02':5})
        code,calls=self.run_step(extract=generate)
        self.assertEqual(code,0); self.assertFalse(calls)

    def test_incomplete_or_excess_outputs_rejected(self):
        for delta in (-2,1):
            def generate(binary,video,folder,identifier,plan):
                for index in range(1,plan['planned_frames']+delta+1):
                    Image.new('RGB',(12,16)).save(folder/f'{identifier}_{index:03d}.png')
            code,calls=self.run_step(extract=generate)
            self.assertEqual(code,1)
            self.assertFalse(list(self.frames.rglob('*.png')))

    def test_explicit_overwrite_preserves_generation(self):
        self.run_step(); code,calls=self.run_step(['--overwrite'])
        self.assertEqual(code,0); self.assertEqual(len(calls),2)
        self.assertEqual(len(list((self.root/'frames_previous').rglob('*.png'))),12)

    def test_existing_scene_parser_retains_video_id(self):
        tree=ast.parse((ROOT/'scripts/classify_face_pose.py').read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse_scene_info')
        namespace={'Path':Path}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'<scene>', 'exec'),namespace)
        self.assertEqual(namespace['parse_scene_info']('subject_v01/subject_v01_001.png'),('subject_v01',1))

    def test_policy_config_cli(self):
        from test_config import script_parser
        config={'frame_extraction':{'sample_fps':1,'max_frames_per_video':80,'policy_version':2}}
        args=script_parser('extract_frames',config).parse_args([])
        self.assertEqual((args.sample_fps,args.max_frames_per_video),(1,80))
        self.assertEqual(script_parser('extract_frames',config).parse_args(['--sample-fps','2']).sample_fps,2)
        from common.config import validate_config
        for key,value in [('sample_fps',0),('max_frames_per_video',0),('policy_version',1)]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError): validate_config({'frame_extraction':{key:value}})

if __name__=='__main__': unittest.main()
