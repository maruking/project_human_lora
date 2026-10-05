"""CSV-only report aggregation, distributions and source-integrity regressions."""
import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_step2_reports as report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.manifests=self.root/'manifests';self.manifests.mkdir()
        self.source=self.root/'dataset.csv';self.summary=self.root/'step2_summary.json'
        self.dest=[self.root/'videos.csv',self.root/'distribution.csv',self.root/'human.md']

    def dataset(self, groups=None):
        groups=groups or {'video_v01':[1,2,3,4,5],'video_v02':[6,7,8,9,10]}
        n=sum(len(v) for v in groups.values());rows=[];rank=0
        for video,values in groups.items():
            for i,value in enumerate(values,1):
                rank+=1
                rows.append(dict(filename=f'{video}/{video}_{i:03d}.png',video_id=video,status='ok',
                    quality_rank=n-rank+1,laplacian_score=value,tenengrad_score=value*10,
                    brightness_mean=value,brightness_std=value,shadow_pixel_ratio=value/100,
                    highlight_pixel_ratio=value/100,contrast_p90_p10=value,
                    extraction_policy_version=2,sample_fps_requested=2,sample_fps_effective=2))
        self.write(rows)
        summary=dict(status='PASS',error_count=0,success_count=n,input_frame_count=n,processed_count=n,
                     csv_records=n,expected_frames=n,video_count=len(groups),
                     input_generation=dict(frame_count=n,video_count=len(groups),extraction_policy_version=2,
                         sample_fps_requested=2,max_frames_per_video=120,sha256='test-generation'),
                     per_video=[dict(video_id=v,records=len(vals)) for v,vals in groups.items()])
        self.summary.write_text(json.dumps(summary))
        for name in ('video_manifest.csv','video_extraction.csv'):
            records=[dict(video_id=v) if name=='video_manifest.csv' else dict(video_id=v,
                extracted_frame_count=len(vals),target_frames=len(vals),extraction_status='PASS',
                extraction_policy_version=2,sample_fps_requested=2,sample_fps_effective=2)
                for v,vals in groups.items()]
            with (self.manifests/name).open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
        (self.manifests/'step1_summary.json').write_text(json.dumps(dict(status='PASS',frames_extracted=n,
                total_videos=len(groups),failed=0,extraction_failed=0,extraction_policy_version=2,
                sample_fps=2,max_frames_per_video=120)))
        return rows

    def write(self, rows):
        with self.source.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

    def run_report(self):
        argv=['build_step2_reports.py','--dataset-report',str(self.source),'--summary',str(self.summary),
              '--manifest-dir',str(self.manifests),'--video-summary',str(self.dest[0]),
              '--distribution-summary',str(self.dest[1]),'--markdown',str(self.dest[2])]
        with patch.object(sys,'argv',argv),patch.object(report,'load_for_cli',return_value={}),contextlib.redirect_stdout(io.StringIO()):
            return report.main()

    def test_linear_percentiles_known_1_to_100(self):
        result=report.stats(list(range(1,101)))
        for key,expected in [('p01',1.99),('p05',5.95),('p10',10.9),('p50',50.5),
                             ('p90',90.1),('p95',95.05),('p99',99.01)]:
            self.assertAlmostEqual(result[key],expected)
        self.assertEqual(result['mean'],50.5)
        self.assertAlmostEqual(result['std'],28.86607,places=6)

    def test_three_video_aggregate_medians_and_tail_counts(self):
        self.dataset({'a':[1,2,3,4],'b':[5,6,7,8],'c':[9,10,11,12]})
        rows,_=report.read_dataset(self.source);videos=report.video_summary(rows)
        self.assertEqual([v['frame_count'] for v in videos],[4,4,4])
        self.assertEqual(videos[0]['laplacian_median'],2.5)
        self.assertEqual(videos[0]['laplacian_p10'],1.3)
        self.assertEqual(videos[0]['laplacian_p90'],3.7)
        self.assertEqual([v['bottom_10pct_count'] for v in videos],[2,0,0])
        self.assertEqual([v['top_10pct_count'] for v in videos],[0,0,2])
        self.assertEqual([v['technical_median_rank'] for v in videos],[3,2,1])
        self.assertEqual(sum(v['bottom_25pct_count'] for v in videos),3)

    def test_stale_free_outputs_only_use_current_csv(self):
        self.dataset();self.assertEqual(self.run_report(),0)
        self.dataset({'video_v01':[1,2]});self.assertEqual(self.run_report(),0)
        with self.dest[0].open(encoding='utf-8-sig') as f:videos=list(csv.DictReader(f))
        self.assertEqual(len(videos),1);self.assertEqual(videos[0]['frame_count'],'2')
        with self.dest[1].open(encoding='utf-8-sig') as f:
            self.assertTrue(all(row['count']=='2' for row in csv.DictReader(f)))
        self.assertNotIn('video_v02',self.dest[2].read_text(encoding='utf-8'))

    def test_duplicate_filename_fails_without_changing_good_outputs(self):
        rows=self.dataset();self.assertEqual(self.run_report(),0)
        before=[p.read_bytes() for p in self.dest]
        rows[1]['filename']=rows[0]['filename'];self.write(rows)
        self.assertEqual(self.run_report(),1);self.assertEqual(before,[p.read_bytes() for p in self.dest])

    def test_replay_is_byte_identical_and_source_is_unchanged(self):
        self.dataset();source_before=self.source.read_bytes()
        self.assertEqual(self.run_report(),0);before=[p.read_bytes() for p in self.dest]
        self.assertEqual(self.run_report(),0);self.assertEqual(before,[p.read_bytes() for p in self.dest])
        self.assertEqual(source_before,self.source.read_bytes())

    def test_error_and_missing_status_rows_fail(self):
        for status in ('error',''):
            rows=self.dataset();rows[0]['status']=status;self.write(rows)
            self.assertEqual(self.run_report(),1)
            self.assertFalse(any(p.exists() for p in self.dest))

    def test_missing_row_count_stops_publication(self):
        rows=self.dataset();self.write(rows[:-1])
        self.assertEqual(self.run_report(),1)
        self.assertFalse(any(p.exists() for p in self.dest))

    def test_nonfinite_metric_rejected(self):
        rows=self.dataset();rows[0]['laplacian_score']='nan';self.write(rows)
        self.assertEqual(self.run_report(),1)

    def test_metadata_counts_and_policy_must_agree(self):
        self.dataset();summary=json.loads(self.summary.read_text());summary['video_count']=99
        self.summary.write_text(json.dumps(summary));self.assertEqual(self.run_report(),1)
        self.dataset();step1=self.manifests/'step1_summary.json';data=json.loads(step1.read_text())
        data['extraction_policy_version']=1;step1.write_text(json.dumps(data));self.assertEqual(self.run_report(),1)

    def test_bucket_counts_and_video_spread(self):
        self.dataset({'a':list(range(1,51)),'b':list(range(51,101))})
        rows,_=report.read_dataset(self.source);buckets={b['bucket']:b for b in report.percentile_buckets(rows)}
        self.assertEqual(buckets['bottom_5_percent']['frame_count'],5)
        self.assertEqual(buckets['bottom_5_percent']['video_count'],1)
        self.assertEqual(sum(buckets[k]['frame_count'] for k in ('bottom_10_percent','percentile_10_25',
                'percentile_25_50','percentile_50_75','percentile_75_90','top_10_percent')),100)
        self.assertEqual(report.tail_size(2001,10),201)

    def test_replacement_failure_restores_all_previous_outputs(self):
        self.dataset();self.assertEqual(self.run_report(),0);before=[p.read_bytes() for p in self.dest]
        replace=report.os.replace
        def fail(src,dst):
            if Path(dst)==self.dest[1]:raise OSError('simulated disk error')
            return replace(src,dst)
        with patch.object(report.os,'replace',side_effect=fail):self.assertEqual(self.run_report(),1)
        self.assertEqual(before,[p.read_bytes() for p in self.dest])

    def test_unicode_csv_paths_and_no_opencv_dependency(self):
        self.source=self.root/'日本語の測定.csv';self.dataset()
        self.assertEqual(self.run_report(),0)
        source=Path(report.__file__).read_text(encoding='utf-8-sig')
        self.assertNotIn('import cv2',source);self.assertNotIn('score_blur',source)


if __name__=='__main__':
    unittest.main()
