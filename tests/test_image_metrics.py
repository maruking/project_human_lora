"""STEP2 computation, provenance, failure accounting and replay; no AI models."""
import contextlib
import csv
import io
import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import score_blur as step
from common.metric_report import measure_images, build_summary, read_step1_counts, write_outliers
from common.config import load_config, validate_config


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / 'frames'
        self.input.mkdir()

    def image(self, video='subject_v01', frame='subject_v01_001.png', pixels=None):
        path = self.input / video / frame
        path.parent.mkdir(exist_ok=True)
        if pixels is None:
            pixels = np.zeros((12, 9, 3), dtype=np.uint8)
        encoded = cv2.imencode('.png', pixels)[1]
        encoded.tofile(path)
        return path

    def measure(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return measure_images(self.input, self.root, step.SCORE_COLUMNS, step.score_image)

    def manifests(self, videos):
        folder = self.root / 'manifests'
        folder.mkdir(exist_ok=True)
        for name, fields in [('video_manifest.csv', ['video_id']),
                             ('video_extraction.csv', ['video_id', 'extracted_frame_count', 'target_frames', 'extraction_status'])]:
            with (folder / name).open('w', encoding='utf-8-sig', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for video, count in videos.items():
                    row = {'video_id': video}
                    if len(fields) > 1:
                        row.update(extracted_frame_count=count, target_frames=count, extraction_status='PASS')
                    writer.writerow(row)
        return folder

    def generation(self):
        images=sorted(self.input.rglob('*.png'))
        counts={v:sum(p.parent.name==v for p in images) for v in {p.parent.name for p in images}}
        folder=self.manifests(counts)
        rows=[]
        for video,count in counts.items():
            frames=[dict(name=p.name,size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                    for p in images if p.parent.name==video]
            policy=dict(extraction_policy_version=2,sample_fps_requested=2.0,sample_fps_effective=2.0,
                        max_frames=120,source_sha256='source')
            (self.input/video/'.extraction_metadata.json').write_text(json.dumps(dict(status='PASS',policy=policy,frames=frames)))
            rows.append(dict(video_id=video,extracted_frame_count=count,target_frames=count,extraction_status='PASS',
                             **{k:policy[k] for k in ('extraction_policy_version','sample_fps_requested','sample_fps_effective')}))
        with (folder/'video_extraction.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        with (folder/'video_manifest.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=['video_id','sha256']);writer.writeheader()
            writer.writerows(dict(video_id=v,sha256='source') for v in counts)
        (folder/'step1_summary.json').write_text(json.dumps(dict(status='PASS',frames_extracted=len(images),
                total_videos=len(counts),failed=0,extraction_failed=0,successful=len(counts),
                extraction_policy_version=2,sample_fps=2.0,max_frames_per_video=120)))
        return folder

    def test_constant_brightness_black_white_gray(self):
        for value in (0, 128, 255):
            with self.subTest(value=value):
                row = step.score_image(self.image(pixels=np.full((12, 9, 3), value, np.uint8)))
                self.assertEqual(row['mean_brightness'], value)
                self.assertEqual(row['global_laplacian'], 0)
                self.assertEqual(row['global_tenengrad'], 0)
                self.assertEqual(row['processing_status'], 'PASS')

    def test_dimensions_low_resolution_no_rejection(self):
        row = step.score_image(self.image(pixels=np.zeros((848, 464, 3), np.uint8)))
        self.assertEqual([row[key] for key in ('width', 'height', 'short_edge', 'long_edge', 'pixel_count')],
                         [464, 848, 464, 848, 464*848])
        self.assertEqual(row['aspect_ratio'], round(464/848, 6))
        self.assertEqual(row['processing_status'], 'PASS')

    def test_old_math_and_aliases_exact(self):
        image = np.random.default_rng(42).integers(0, 256, (51, 39, 3), dtype=np.uint8)
        row = step.score_image(self.image(pixels=image))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F).var()
        dx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        dy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        self.assertEqual(row['laplacian_score'], round(float(lap), 3))
        self.assertEqual(row['tenengrad_score'], round(float(np.mean(dx*dx+dy*dy)), 3))
        self.assertEqual(row['brightness_mean'], round(float(gray.mean()), 3))
        for new, old in [('global_laplacian','laplacian_score'), ('global_tenengrad','tenengrad_score'), ('mean_brightness','brightness_mean')]:
            self.assertEqual(row[new], row[old])
        self.assertEqual(row['brightness_std'], round(float(gray.std()), 3))
        self.assertEqual(row['shadow_pixel_ratio'], round(float(np.mean(gray < 40)), 3))
        self.assertEqual(row['highlight_pixel_ratio'], round(float(np.mean(gray > 235)), 3))
        self.assertEqual(row['contrast_p90_p10'], round(float(np.percentile(gray,90)-np.percentile(gray,10)), 3))

    def test_natural_order_and_identity(self):
        for video in ('subject_v100', 'subject_v02', 'subject_v01'):
            for frame in ('frame10.png', 'frame2.png'):
                self.image(video, frame)
        rows = self.measure()
        self.assertEqual([row['video_id'] for row in rows], ['subject_v01']*2+['subject_v02']*2+['subject_v100']*2)
        self.assertEqual([row['frame_name'] for row in rows[:2]], ['frame2.png','frame10.png'])
        self.assertEqual(len({row['frame_id'] for row in rows}), 6)
        self.assertEqual(rows[0]['frame_id'], rows[0]['filename'])
        self.assertEqual(rows[0]['relative_path'], 'frames/'+rows[0]['filename'])

    def test_broken_input_retains_row_and_error(self):
        self.image()
        self.image(frame='broken.png').write_bytes(b'broken')
        rows = self.measure()
        summary = build_summary(rows, {'subject_v01':2})
        self.assertEqual(len(rows),2)
        self.assertEqual(summary['failed'],1)
        self.assertEqual(summary['processed'],1)
        self.assertEqual(summary['status'],'FAIL')
        self.assertTrue(summary['step1_count_match'])
        bad = next(row for row in rows if row['processing_status']=='FAIL')
        self.assertEqual(bad['error'],'DECODE_ERROR')
        self.assertEqual(bad['global_laplacian'],'')

    def test_io_failure_portable_error(self):
        self.image()
        with patch.object(step, 'score_image', side_effect=OSError('C:/private/file')):
            rows = self.measure()
        self.assertEqual(rows[0]['error'],'IO_ERROR')
        self.assertNotIn('private',json.dumps(rows))

    def test_counts_unknown_missing_video_and_empty_input(self):
        self.image()
        rows=self.measure()
        for expected in ({'subject_v01':2}, {'subject_v02':1}, {'subject_v01':1,'subject_v02':1}):
            self.assertEqual(build_summary(rows,expected)['status'],'FAIL')
        self.assertEqual(build_summary([],{'subject_v01':1})['status'],'FAIL')
        self.assertEqual(build_summary(rows,{'subject_v01':1})['status'],'PASS')

    def test_manifest_validation(self):
        folder=self.manifests({'subject_v01':1})
        self.assertEqual(read_step1_counts(folder),{'subject_v01':1})
        path=folder/'video_extraction.csv'
        path.write_text(path.read_text(encoding='utf-8-sig').replace('PASS','FAIL'),encoding='utf-8-sig')
        with self.assertRaisesRegex(ValueError,'incomplete'): read_step1_counts(folder)

    def test_manifest_duplicate_rejected(self):
        folder=self.manifests({'subject_v01':1})
        path=folder/'video_manifest.csv'
        with path.open('a',encoding='utf-8') as handle: handle.write('subject_v01\n')
        with self.assertRaisesRegex(ValueError,'duplicate'): read_step1_counts(folder)

    def test_manifest_id_sets_must_agree(self):
        folder=self.manifests({'subject_v01':1})
        path=folder/'video_manifest.csv'
        path.write_text('video_id\nsubject_v02\n',encoding='utf-8-sig')
        with self.assertRaisesRegex(ValueError,'IDs differ'): read_step1_counts(folder)

    def test_new_paths_and_boolean_cli_override(self):
        from test_config import script_parser
        config=load_config(ROOT/'config/config.example.yaml')
        config['paths']['reports_dir']='work/custom_reports'
        config['paths']['manifests_dir']='work/custom_manifests'
        config['step2_blur'].update(summary='@reports/summary.json',outliers='@reports/outliers.csv',retain_missing_records=False)
        parser=script_parser('score_blur',config)
        args=parser.parse_args([])
        self.assertEqual(args.summary,ROOT/'work/custom_reports/summary.json')
        self.assertEqual(args.outliers,ROOT/'work/custom_reports/outliers.csv')
        self.assertEqual(args.manifest_dir,ROOT/'work/custom_manifests')
        self.assertFalse(args.retain_missing_records)
        args=parser.parse_args(['--summary','output/override.json','--no-retain-missing-records'])
        self.assertEqual(args.summary,ROOT/'output/override.json')
        self.assertFalse(args.retain_missing_records)

    def test_current_snapshot_and_explicit_legacy_merge(self):
        self.image(frame='one.png'); self.image(frame='two.png')
        rows=self.measure(); step.add_relative_ranks(rows)
        report=self.root/'report.csv'; step.write_report(report,rows)
        with self.assertRaises(ValueError):
            step.write_report(report,rows[:1],retain_missing_records=True)
        with report.open(encoding='utf-8-sig') as f: self.assertEqual(len(list(csv.DictReader(f))),2)
        step.write_report(report,rows[:1])
        with report.open(encoding='utf-8-sig') as f: self.assertEqual(len(list(csv.DictReader(f))),1)

    def test_statistics_and_outliers_are_diagnostic(self):
        self.image()
        rows=self.measure(); summary=build_summary(rows,{'subject_v01':1})
        self.assertEqual(summary['resolution_buckets']['short_edge_lt720'],1)
        self.assertEqual(summary['status'],'PASS')
        path=self.root/'outliers.csv'; write_outliers(path,rows)
        with path.open(encoding='utf-8-sig') as f: self.assertEqual(len(list(csv.DictReader(f))),5)

    def test_main_replay_outputs_byte_identical(self):
        self.image(); manifests=self.generation()
        argv=['score_blur.py','--input',str(self.input),'--manifest-dir',str(manifests),'--report',str(self.root/'report.csv')]
        def run():
            with patch.object(sys,'argv',argv), patch.object(step,'load_for_cli',return_value={}), contextlib.redirect_stdout(io.StringIO()):
                return step.main()
        self.assertEqual(run(),0)
        paths=[self.root/name for name in ('report.csv','step2_summary.json','step2_diagnostic_outliers.csv')]
        first=[path.read_bytes() for path in paths]
        self.assertEqual(run(),0)
        self.assertEqual(first,[path.read_bytes() for path in paths])
        self.image(frame='subject_v01_002.png').write_bytes(b'broken')
        self.generation()
        self.assertEqual(run(),1)
        self.assertEqual(first,[path.read_bytes() for path in paths])
        failed=list((self.root/'step2_run_audit').glob('failed_*/report.csv'))
        self.assertEqual(len(failed),1)
        with failed[0].open(encoding='utf-8-sig') as f:
            self.assertEqual(sum(r['status']=='error' for r in csv.DictReader(f)),1)

    def run_generation(self, folder):
        argv=['score_blur.py','--input',str(self.input),'--manifest-dir',str(folder),'--report',str(self.root/'report.csv')]
        with patch.object(sys,'argv',argv), patch.object(step,'load_for_cli',return_value={}), contextlib.redirect_stdout(io.StringIO()):
            return step.main()

    def test_ten_current_files_exactly_ten_rows(self):
        for i in range(1,11): self.image(frame=f'subject_v01_{i:03d}.png')
        self.assertEqual(self.run_generation(self.generation()),0)
        with (self.root/'report.csv').open(encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),10)
        self.assertEqual([int(r['temporal_index']) for r in rows],list(range(1,11)))
        self.assertTrue(all(r['extraction_policy_version']=='2' for r in rows))

    def test_stale_abc_to_ab(self):
        rows=[dict(filename=x,status='ok') for x in ('A','B','C')]
        dest=self.root/'report.csv'
        step.write_report(dest,rows);step.write_report(dest,rows[:2])
        with dest.open(encoding='utf-8-sig') as f:
            self.assertEqual([r['filename'] for r in csv.DictReader(f)],['A','B'])

    def test_video_percentiles_independent_from_global(self):
        base=np.random.default_rng(7).integers(0,10,(16,16,3),dtype=np.uint8)
        for video,scales in [('a',(1,2)),('b',(10,20))]:
            for i,scale in enumerate(scales,1):
                self.image(video,f'{video}_{i:03d}.png',base*scale)
        self.assertEqual(self.run_generation(self.generation()),0)
        with (self.root/'report.csv').open(encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual([float(r['laplacian_percentile']) for r in rows],[0,33.33,66.67,100])
        self.assertEqual([float(r['laplacian_percentile_video']) for r in rows],[0,100,0,100])
        self.assertEqual([float(r['tenengrad_percentile_video']) for r in rows],[0,100,0,100])
        self.assertEqual([int(r['quality_rank_video']) for r in rows],[2,1,2,1])

    def test_rank_ties_use_filename_even_with_reordered_rows(self):
        rows=[dict(filename=f'a/a_{i:03d}.png',status='ok',laplacian_score=1,tenengrad_score=1) for i in (10,2,1)]
        step.add_relative_ranks(rows)
        self.assertEqual([r['quality_rank'] for r in rows],[3,2,1])

    def test_count_mismatch_stops_before_scoring_preserves_report(self):
        self.image();folder=self.generation()
        report=self.root/'report.csv';report.write_bytes(b'previous good report')
        self.image(frame='subject_v01_002.png')
        with patch.object(step,'score_image') as scorer:
            self.assertEqual(self.run_generation(folder),1)
            scorer.assert_not_called()
        self.assertEqual(report.read_bytes(),b'previous good report')

    def test_changed_content_stops_before_scoring(self):
        path=self.image();folder=self.generation();path.write_bytes(b'changed')
        with patch.object(step,'score_image') as scorer:
            self.assertEqual(self.run_generation(folder),1);scorer.assert_not_called()

    def test_unicode_generation_path_and_replay_ignores_mtime(self):
        import os
        self.input=self.root/'日本語の入力';self.input.mkdir()
        p=self.image(video='人物_v01',frame='人物_v01_001.png');folder=self.generation()
        self.assertEqual(self.run_generation(folder),0)
        before=(self.root/'report.csv').read_bytes()
        os.utime(p,(1000000000,1000000000))
        self.assertEqual(self.run_generation(folder),0)
        self.assertEqual((self.root/'report.csv').read_bytes(),before)

    def test_failed_csv_write_preserves_good_artifacts(self):
        self.image();folder=self.generation();self.assertEqual(self.run_generation(folder),0)
        paths=[self.root/n for n in ('report.csv','step2_summary.json','step2_diagnostic_outliers.csv')]
        before=[p.read_bytes() for p in paths]
        with patch.object(step,'write_report',side_effect=OSError('simulated disk failure')):
            self.assertEqual(self.run_generation(folder),1)
        self.assertEqual(before,[p.read_bytes() for p in paths])

    def test_partial_publication_rolls_back_all_artifacts(self):
        self.image();folder=self.generation();self.assertEqual(self.run_generation(folder),0)
        paths=[self.root/n for n in ('report.csv','step2_summary.json','step2_diagnostic_outliers.csv')]
        before=[p.read_bytes() for p in paths]
        replace=step.os.replace
        def fail_summary(src,dst):
            if Path(dst)==paths[1]: raise OSError('simulated replace failure')
            return replace(src,dst)
        with patch.object(step.os,'replace',side_effect=fail_summary):
            self.assertEqual(self.run_generation(folder),1)
        self.assertEqual(before,[p.read_bytes() for p in paths])

    def run_with_stills(self, folder, supplemental):
        argv=['score_blur.py','--input',str(self.input),'--manifest-dir',str(folder),
              '--report',str(self.root/'report.csv'),'--supplemental-dir',str(supplemental)]
        with patch.object(sys,'argv',argv), patch.object(step,'load_for_cli',return_value={}), contextlib.redirect_stdout(io.StringIO()):
            return step.main()

    def test_supplemental_stills_separate_lineage_and_complete_combined_report(self):
        self.image();folder=self.generation()
        still=self.image('extra_stills','portrait.png')
        self.assertEqual(self.run_with_stills(folder,still.parent),0)
        def read(name):
            with (self.root/name).open(encoding='utf-8-sig') as handle:
                return list(csv.DictReader(handle))
        self.assertEqual(len(read('report.csv')),1)
        supplemental=read('step2_supplemental_report.csv')
        self.assertEqual(len(supplemental),1)
        self.assertEqual(supplemental[0]['video_id'],'')
        self.assertEqual(supplemental[0]['temporal_index'],'')
        combined=read('step2_all_images_report.csv')
        self.assertEqual(len(combined),2)
        self.assertEqual({row['input_kind'] for row in combined},{'VIDEO_FRAME','SUPPLEMENTAL_STILL'})
        self.assertEqual({int(row['quality_rank']) for row in combined},{1,2})
        summary=json.loads((self.root/'step2_summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['input_frame_count'],1)
        self.assertEqual(summary['supplemental_records'],1)
        self.assertEqual(summary['total_measured_images'],2)
        names=('report.csv','step2_summary.json','step2_diagnostic_outliers.csv',
               'step2_supplemental_report.csv','step2_all_images_report.csv')
        before=[(self.root/name).read_bytes() for name in names]
        self.assertEqual(self.run_with_stills(folder,still.parent),0)
        self.assertEqual(before,[(self.root/name).read_bytes() for name in names])

    def test_supplemental_does_not_hide_formal_count_mismatch(self):
        formal=self.image();folder=self.generation()
        still=self.image('extra_stills','portrait.png')
        formal.unlink()
        with patch.object(step,'score_image') as scorer:
            self.assertEqual(self.run_with_stills(folder,still.parent),1)
            scorer.assert_not_called()
        self.assertFalse((self.root/'report.csv').exists())

    def test_supplemental_decode_failure_preserves_previous_reports(self):
        self.image();folder=self.generation()
        still=self.image('extra_stills','portrait.png')
        self.assertEqual(self.run_with_stills(folder,still.parent),0)
        names=('report.csv','step2_summary.json','step2_diagnostic_outliers.csv',
               'step2_supplemental_report.csv','step2_all_images_report.csv')
        before=[(self.root/name).read_bytes() for name in names]
        still.write_bytes(b'not an image')
        self.assertEqual(self.run_with_stills(folder,still.parent),1)
        self.assertEqual(before,[(self.root/name).read_bytes() for name in names])
        failed=list((self.root/'step2_run_audit').glob('failed_*/additional_0.csv'))
        self.assertEqual(len(failed),1)
        with failed[0].open(encoding='utf-8-sig') as handle:
            self.assertEqual(list(csv.DictReader(handle))[0]['processing_status'],'FAIL')

    def test_combined_publication_failure_rolls_back_all_five_artifacts(self):
        self.image();folder=self.generation()
        still=self.image('extra_stills','portrait.png')
        self.assertEqual(self.run_with_stills(folder,still.parent),0)
        names=('report.csv','step2_summary.json','step2_diagnostic_outliers.csv',
               'step2_supplemental_report.csv','step2_all_images_report.csv')
        before=[(self.root/name).read_bytes() for name in names]
        replace=step.os.replace
        def fail_combined(src,dst):
            if Path(dst)==self.root/'step2_all_images_report.csv':
                raise OSError('simulated combined publication failure')
            return replace(src,dst)
        with patch.object(step.os,'replace',side_effect=fail_combined):
            self.assertEqual(self.run_with_stills(folder,still.parent),1)
        self.assertEqual(before,[(self.root/name).read_bytes() for name in names])

    def test_true_retention_config_is_invalid(self):
        config=load_config(ROOT/'config/config.example.yaml')
        config['step2_blur']['retain_missing_records']=True
        with self.assertRaises(ValueError): validate_config(config)

    def test_new_config_validation(self):
        config=load_config(ROOT/'config/config.example.yaml')
        config['step2_blur'].update(summary='@reports/summary.json',outliers='@reports/outliers.csv',retain_missing_records=False)
        validate_config(config)
        config['step2_blur']['retain_missing_records']='false'
        with self.assertRaises(ValueError): validate_config(config)


if __name__=='__main__':
    unittest.main()
