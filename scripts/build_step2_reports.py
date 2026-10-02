"""Build human STEP2 reports from the frozen CSV; never decode or score images."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from fractions import Fraction
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile

import numpy as np

from common.config import configure_parser, load_for_cli, get_section, resolve_config_path
from common.video_manifest import natural_key, manifest_lock, write_csv_atomic

METRICS = ('laplacian_score', 'tenengrad_score', 'brightness_mean', 'brightness_std',
           'shadow_pixel_ratio', 'highlight_pixel_ratio', 'contrast_p90_p10')
QUANTILES = (('min', 0), ('p01', 1), ('p05', 5), ('p10', 10), ('p25', 25),
             ('p50', 50), ('p75', 75), ('p90', 90), ('p95', 95), ('p99', 99), ('max', 100))
DISTRIBUTION_COLUMNS = ['metric', 'count'] + [key for key, _ in QUANTILES] + ['mean', 'std']
VIDEO_METRICS = {'laplacian': 'laplacian_score', 'tenengrad': 'tenengrad_score',
                 'brightness': 'brightness_mean', 'shadow_ratio': 'shadow_pixel_ratio',
                 'highlight_ratio': 'highlight_pixel_ratio', 'contrast': 'contrast_p90_p10'}
VIDEO_STATS = ('min', 'p10', 'p25', 'median', 'p75', 'p90', 'max', 'mean')
VIDEO_COLUMNS = ['video_id', 'frame_count'] + [f'{name}_{stat}' for name in VIDEO_METRICS for stat in VIDEO_STATS]
VIDEO_COLUMNS += ['laplacian_median_percentile', 'tenengrad_median_percentile', 'technical_median_percentile',
                  'laplacian_median_rank', 'tenengrad_median_rank', 'technical_median_rank']
VIDEO_COLUMNS += [f'{side}_{pct}pct_count' for side in ('bottom', 'top') for pct in (1, 5, 10, 25)]
VIDEO_COLUMNS += ['bottom_10pct_ratio']


def video_key(value):
    return natural_key(Path(value))


def stats(values):
    """Linear interpolation of stored CSV values; population std (ddof=0)."""
    data = np.asarray(values, dtype=np.float64)
    if not len(data) or not np.isfinite(data).all():
        raise ValueError('Statistics require nonempty finite values')
    result = {key: round(float(value), 6) for (key, _), value in
              zip(QUANTILES, np.percentile(data, [p for _, p in QUANTILES], method='linear'))}
    result.update(count=len(data), mean=round(float(data.mean()), 6), std=round(float(data.std(ddof=0)), 6))
    return result


def read_dataset(path):
    content = path.read_bytes()
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig'), newline=''))
    fields = reader.fieldnames or []
    required = set(METRICS) | {'filename', 'video_id', 'status', 'quality_rank'}
    if len(fields) != len(set(fields)) or not required <= set(fields):
        raise ValueError('Dataset CSV has duplicate/missing required columns')
    rows = []
    for number, record in enumerate(reader, 2):
        if None in record or any(record.get(key) is None for key in required):
            raise ValueError(f'Dataset CSV malformed row {number}')
        if record['status'] != 'ok' or record.get('processing_status', 'PASS') != 'PASS' or record.get('error', ''):
            raise ValueError(f'Dataset CSV contains an error/missing-status row: {number}')
        video, name = record['video_id'], record['filename']
        match = re.fullmatch(re.escape(video) + r'/' + re.escape(video) + r'_(\d{3,})\.png', name)
        if not video or '/' in video or '\\' in video or video in ('.','..') or not match or name != f'{video}/{video}_{int(match[1]):03d}.png' or int(match[1]) < 1:
            raise ValueError(f'Dataset CSV invalid filename/video identity: row {number}')
        if record.get('temporal_index',str(int(match[1]))) != str(int(match[1])):
            raise ValueError('Dataset temporal_index differs from filename')
        if record.get('frame_id', name) != name:
            raise ValueError('Dataset frame_id differs from filename')
        rank = int(record['quality_rank'])
        row = dict(record, quality_rank=rank)
        for metric in METRICS:
            value = float(record[metric])
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'Invalid numeric metric {metric}: row {number}')
            if metric.endswith('_pixel_ratio') and value > 1:
                raise ValueError(f'Invalid pixel ratio: row {number}')
            row[metric] = value
        rows.append(row)
    if not rows:
        raise ValueError('Dataset CSV is empty')
    if len({row['filename'] for row in rows}) != len(rows):
        raise ValueError('Dataset CSV has duplicate filenames')
    if sorted(row['quality_rank'] for row in rows) != list(range(1, len(rows) + 1)):
        raise ValueError('Stored global quality_rank must be a complete unique 1..N ordering')
    rows.sort(key=lambda row: (video_key(row['video_id']), video_key(row['filename'])))
    return rows, hashlib.sha256(content).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def validate_generation(rows, summary_path, manifests):
    """CSV/metadata-only validation, without opening any frame image."""
    summary = read_json(summary_path)
    count = len(rows); counts = Counter(row['video_id'] for row in rows)
    if summary['status'] != 'PASS' or summary['error_count'] != 0 or summary['success_count'] != count:
        raise ValueError('STEP2 summary is failed or does not match successful CSV rows')
    for key in ('input_frame_count', 'processed_count', 'csv_records', 'expected_frames'):
        if summary[key] != count:
            raise ValueError(f'STEP2 summary count mismatch: {key}')
    generation = summary['input_generation']
    if summary['video_count'] != len(counts) or generation['frame_count'] != count or generation['video_count'] != len(counts):
        raise ValueError('STEP2 summary video/generation count mismatch')
    if len(summary['per_video']) != len(counts) or {item['video_id']: item['records'] for item in summary['per_video']} != dict(counts):
        raise ValueError('STEP2 per-video summary differs from CSV')
    tables = []
    for name in ('video_manifest.csv', 'video_extraction.csv'):
        with (manifests/name).open(encoding='utf-8-sig', newline='') as handle:
            records = list(csv.DictReader(handle))
        ids = [row['video_id'] for row in records]
        if len(ids) != len(set(ids)) or set(ids) != set(counts):
            raise ValueError(f'STEP1 {name} video IDs differ from CSV')
        tables.append({row['video_id']: row for row in records})
    expected = {}
    for video, record in tables[1].items():
        n = int(record['extracted_frame_count'])
        if record['extraction_status'] != 'PASS' or n <= 0 or int(record['target_frames']) != n or counts[video] != n:
            raise ValueError(f'STEP1 frame count/status mismatch: {video}')
        indices=sorted(int(row['filename'].rsplit('_',1)[1][:-4]) for row in rows if row['video_id']==video)
        if indices != list(range(1,n+1)):
            raise ValueError(f'STEP1/CSV temporal inventory mismatch: {video}')
        expected[video] = n
    step1 = read_json(manifests/'step1_summary.json')
    if (step1['status'] != 'PASS' or step1['frames_extracted'] != count or step1['total_videos'] != len(counts)
            or step1['failed'] != 0 or step1['extraction_failed'] != 0):
        raise ValueError('STEP1 summary does not match source CSV generation')
    if (step1['extraction_policy_version'] != generation['extraction_policy_version']
            or step1['sample_fps'] != generation['sample_fps_requested']
            or step1['max_frames_per_video'] != generation['max_frames_per_video']):
        raise ValueError('STEP1/STEP2 extraction policy mismatch')
    for row in rows:
        metadata = tables[1][row['video_id']]
        for key in ('extraction_policy_version', 'sample_fps_requested', 'sample_fps_effective'):
            if key not in row or float(row[key]) != float(metadata[key]):
                raise ValueError(f'STEP1/CSV traceability mismatch: {key}')
    return summary


def tail_size(total, percent):
    # Exact integer ceiling, including for small synthetic generations.
    return (total * percent + 99) // 100


def video_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['video_id']].append(row)
    total = len(rows); result = []
    for video in sorted(groups, key=video_key):
        group = groups[video]; out = dict(video_id=video, frame_count=len(group))
        for name, metric in VIDEO_METRICS.items():
            summary = stats([r[metric] for r in group])
            for stat in VIDEO_STATS:
                out[f'{name}_{stat}'] = summary['p50' if stat == 'median' else stat]
        for percent in (1, 5, 10, 25):
            size = tail_size(total, percent)
            out[f'bottom_{percent}pct_count'] = sum(r['quality_rank'] > total-size for r in group)
            out[f'top_{percent}pct_count'] = sum(r['quality_rank'] <= size for r in group)
        out['bottom_10pct_ratio'] = round(out['bottom_10pct_count']/len(group), 6)
        result.append(out)
    exact = {}
    for name in ('laplacian', 'tenengrad'):
        values = sorted({row[f'{name}_median'] for row in result})
        mapping = {value: Fraction(100*i, len(values)-1) if len(values)>1 else Fraction(100)
                   for i, value in enumerate(values)}
        for row in result:
            exact[row['video_id'], name] = mapping[row[f'{name}_median']]
            row[f'{name}_median_percentile'] = round(float(mapping[row[f'{name}_median']]), 6)
        ordered = sorted(result, key=lambda row: (-row[f'{name}_median'], video_key(row['video_id'])))
        for rank, row in enumerate(ordered, 1):
            row[f'{name}_median_rank'] = rank
    for row in result:
        score = (exact[row['video_id'], 'laplacian'] + exact[row['video_id'], 'tenengrad'])/2
        exact[row['video_id'], 'technical'] = score
        row['technical_median_percentile'] = round(float(score), 6)
    for rank, row in enumerate(sorted(result, key=lambda r: (-exact[r['video_id'], 'technical'], video_key(r['video_id']))), 1):
        row['technical_median_rank'] = rank
    return result


def describe_bucket(label, selected, total):
    return dict(bucket=label, frame_count=len(selected), percentage=round(100*len(selected)/total, 6),
                video_count=len({row['video_id'] for row in selected}))


def percentile_buckets(rows):
    n = len(rows); ascending = sorted(rows, key=lambda r: -r['quality_rank'])
    results = [describe_bucket(f'bottom_{p}_percent', ascending[:tail_size(n,p)], n) for p in (1,5,10)]
    # Exclusive middle ranges partition the complement of the cumulative bottom/top 10%.
    low, high = tail_size(n,10), n-tail_size(n,10)
    boundaries = [low] + [max(low,min(high,tail_size(n,p))) for p in (25,50,75)] + [max(low,high)]
    for label,start,end in zip(('percentile_10_25','percentile_25_50','percentile_50_75','percentile_75_90'),boundaries,boundaries[1:]):
        results.append(describe_bucket(label, ascending[start:end], n))
    for p in (10,5,1):
        results.append(describe_bucket(f'top_{p}_percent', ascending[n-tail_size(n,p):], n))
    return results


def table(columns, rows):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    return '| ' + ' | '.join(columns) + ' |\n| ' + ' | '.join('---' for _ in columns) + ' |\n' + ''.join(
        '| ' + ' | '.join(cell(row[col]) for col in columns) + ' |\n' for row in rows)


def markdown_report(rows, videos, distributions, summary, csv_sha):
    generation = summary['input_generation']; n = len(rows)
    text = '# STEP2 Current Generation Metrics\n\n'
    text += '## 1. Dataset Overview\n\n'
    text += f"Videos: {len(videos)} | Frames: {n} | Errors: 0 | Status: PASS\n\n"
    text += f"Extraction policy: {generation['extraction_policy_version']} | Requested FPS: {generation['sample_fps_requested']} | Max frames/video: {generation['max_frames_per_video']}\n\n"
    text += f"Generation SHA256: `{generation['sha256']}`\n\nSource CSV SHA256: `{csv_sha}`\n\n"
    text += 'CSV-only aggregation; no image decoding, metric/rank recalculation or selection. STEP1/STEP2 metadata and per-video counts agree.\n\n'
    text += '## 2. Overall Distribution\n\n'
    text += table(DISTRIBUTION_COLUMNS, distributions)
    text += '\nPercentiles use NumPy linear interpolation of stored values; std is population std (ddof=0). Aggregates are rounded to 6 decimals; source metrics keep their existing precision.\n\n'
    text += '## 3. Video-Level Overview\n\n'
    columns = ['video_id','frame_count','laplacian_median','tenengrad_median','technical_median_rank','bottom_10pct_count']
    ordered = sorted(videos, key=lambda r:r['technical_median_rank'])
    for heading, selected in [('Lowest Median Technical Quality Videos',list(reversed(ordered[-10:]))),
                              ('Highest Median Technical Quality Videos',ordered[:10])]:
        text += f'### {heading}\n\n' + table(columns,selected) + '\n'
    concentrated = sorted(videos, key=lambda r:(-Fraction(r['bottom_10pct_count'],r['frame_count']),-r['bottom_10pct_count'],video_key(r['video_id'])))
    text += '### Videos With Highest Bottom-10% Concentration\n\n'
    text += table(['video_id','frame_count','bottom_10pct_count','bottom_10pct_ratio'],concentrated[:10]) + '\n'
    text += 'Video technical median percentile is the average of the Laplacian and Tenengrad median percentiles across videos. Each median percentile indexes sorted unique video medians from 0 to 100 (singleton/all-equal = 100). Diagnostic ranks descend these values; ties use natural video_id order. Ratios are fractions (1 = 100%). No existing frame ranking changes.\n\n'
    text += '## 4. Global Percentile Distribution\n\n'
    text += table(['bucket','frame_count','percentage','video_count'],percentile_buckets(rows))
    text += '\nTail membership uses the saved global quality_rank (1 = highest), with ceil(N * percentage / 100) frames at each tail. The 1/5/10% tails are cumulative and overlap; do not add them. Middle bands exclude both 10% tails and divide at ceil(N * 25/50/75%). On tiny datasets tails may overlap. Stored filename tie-breaks can split equal scores. These are diagnostic counts, not rejection rules.\n\n'
    buckets=[]
    for lower,upper in zip((0,5,10,20,40,80,160,320),(5,10,20,40,80,160,320,float('inf'))):
        selected=[r for r in rows if lower<=r['laplacian_score']<upper]
        buckets.append(describe_bucket(f'[{lower}, {upper})' if math.isfinite(upper) else '320+',selected,n))
    text += '### Absolute Laplacian Histogram (diagnostic only)\n\n' + table(['bucket','frame_count','percentage','video_count'],buckets)
    text += '\nIntervals are lower-inclusive/upper-exclusive. Histogram boundaries are not Gate thresholds.\n\n'
    text += '## 5. Exposure Distribution\n\n'
    by_metric={row['metric']:row for row in distributions}
    text += table(['metric','p05','p25','p50','p75','p95'],[by_metric['brightness_mean']])+'\n'
    text += table(['metric','p50','p90','p95','p99','max'],[by_metric[k] for k in ('shadow_pixel_ratio','highlight_pixel_ratio')])+'\n'
    tails=[]
    for metric,key,side in [('brightness_mean','p05','lower'),('brightness_mean','p95','upper'),
                            ('shadow_pixel_ratio','p95','upper'),('shadow_pixel_ratio','p99','upper'),
                            ('highlight_pixel_ratio','p95','upper'),('highlight_pixel_ratio','p99','upper')]:
        # Compare unrounded interpolated cutoffs; exported cutoffs are displayed at 6 decimals.
        cutoff=float(np.percentile([r[metric] for r in rows],int(key[1:]),method='linear'))
        selected=[r for r in rows if (r[metric]<=cutoff if side=='lower' else r[metric]>=cutoff)]
        out=describe_bucket(f'{metric} {"<=" if side=="lower" else ">="} {key.upper()}',selected,n)
        out['dataset_cutoff']=round(cutoff,6);tails.append(out)
    text += table(['bucket','dataset_cutoff','frame_count','percentage','video_count'],tails)
    text += '\nExposure tails include ties, so counts can exceed the nominal percentage; P95/P99 groups overlap. Cutoffs come only from this dataset and are not exposure Gates.\n\n'
    ranked=sorted(rows,key=lambda r:r['quality_rank'])
    for heading,selected in [('6. Highest 10 Individual Frames',ranked[:10]),('7. Lowest 10 Individual Frames',list(reversed(ranked[-10:])) )]:
        text += f'## {heading}\n\n'+table(['filename','laplacian_score','tenengrad_score','quality_rank'],selected)+'\n'
    text += '## 8. Interpretation\n\n'
    text += '- These are whole-frame global technical diagnostics.\n- Face quality, identity quality and LoRA candidate selection require later evaluation.\n- STEP3 must evaluate facial regions separately; no Gate was changed.\n- Background, hair, clothing, resolution and compression can affect gradients.\n- A low median or concentrated tail suggests where to inspect; it does not authorize deletion.\n- STEP2 blur flag count remains unconfigured (null); no threshold is invented.\n\n'
    text += '## 9. Files\n\n'
    text += 'Source: step2_dataset_report.csv and step2_summary.json. Generated: step2_video_summary.csv, step2_distribution_summary.csv, and this Markdown. Full paths are printed by the generator; CLI overrides may relocate outputs.\n'
    return text


def publish_reports(destinations, videos, distributions, markdown):
    """Stage all reports and roll back ordinary replacement failures."""
    if len(set(destinations)) != 3:
        raise ValueError('Report destinations must be distinct')
    with tempfile.TemporaryDirectory(prefix='step2_reports_') as folder:
        stage=Path(folder); staged=[stage/'videos.csv',stage/'distribution.csv',stage/'report.md']
        write_csv_atomic(staged[0],VIDEO_COLUMNS,videos)
        write_csv_atomic(staged[1],DISTRIBUTION_COLUMNS,distributions)
        staged[2].write_text(markdown,encoding='utf-8')
        for path,wanted in zip(staged[:2],(len(videos),len(distributions))):
            with path.open(encoding='utf-8-sig',newline='') as f:
                if len(list(csv.DictReader(f))) != wanted:raise ValueError('Staged report row count mismatch')
        existed=[];replaced=[]
        for i,dest in enumerate(destinations):
            dest.parent.mkdir(parents=True,exist_ok=True);existed.append(dest.exists())
            if dest.exists():shutil.copy2(dest,stage/f'old_{i}')
        try:
            for i,(source,dest) in enumerate(zip(staged,destinations)):
                with tempfile.NamedTemporaryFile(dir=dest.parent,delete=False) as handle:
                    temporary=Path(handle.name)
                try:
                    shutil.copyfile(source,temporary);os.replace(temporary,dest);replaced.append(i)
                finally:temporary.unlink(missing_ok=True)
        except OSError:
            for i in reversed(replaced):
                if existed[i]:shutil.copyfile(stage/f'old_{i}',destinations[i])
                else:destinations[i].unlink(missing_ok=True)
            raise


def main():
    root=Path(__file__).resolve().parents[1];config=load_for_cli()
    parser=argparse.ArgumentParser(description='Aggregate existing STEP2 CSV only; no image scoring or selection.')
    parser.add_argument('--config',type=Path)
    parser.add_argument('--dataset-report',type=Path,default=root/'output/reports/step2_dataset_report.csv')
    parser.add_argument('--summary',type=Path,default=None,help='Existing STEP2 summary JSON')
    parser.add_argument('--manifest-dir',type=Path,default=root/'work/manifests')
    parser.add_argument('--video-summary',type=Path,default=None)
    parser.add_argument('--distribution-summary',type=Path,default=None)
    parser.add_argument('--markdown',type=Path,default=root/'docs/STEP2_METRICS_SUMMARY.md')
    configure_parser(parser,config,'step2_blur',aliases={'dataset_report':'report'},paths={'manifest_dir':'manifests_dir'})
    args=parser.parse_args();source=args.dataset_report.resolve()
    summary_path=args.summary or source.with_name('step2_summary.json')
    destinations=[(args.video_summary or source.with_name('step2_video_summary.csv')).resolve(),
                  (args.distribution_summary or source.with_name('step2_distribution_summary.csv')).resolve(),args.markdown.resolve()]
    try:
        if len(set(destinations))!=3 or any(p in (source,summary_path.resolve()) or p.is_relative_to(args.manifest_dir.resolve()) for p in destinations):
            raise ValueError('Outputs must be distinct and cannot overwrite source data/metadata')
        if [p.suffix.lower() for p in destinations]!=['.csv','.csv','.md']:
            raise ValueError('Output suffixes must be CSV, CSV, Markdown')
        raw=get_section(config,'paths').get('raw_frames_dir')
        if raw and any(p.is_relative_to(resolve_config_path(raw,config)) for p in destinations):
            raise ValueError('Reports must be outside the raw-frame directory')
        with manifest_lock(args.manifest_dir/'.video_manifest.lock'):
            rows,digest=read_dataset(source)
            summary=validate_generation(rows,summary_path,args.manifest_dir)
            videos=video_summary(rows)
            distributions=[dict(stats([r[key] for r in rows]),metric=key) for key in METRICS]
            markdown=markdown_report(rows,videos,distributions,summary,digest)
            if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
                raise ValueError('Source CSV changed during aggregation')
            publish_reports(destinations,videos,distributions,markdown)
        print(f'Report aggregation PASS: videos={len(videos)} frames={len(rows)} errors=0')
        print(f'Source CSV (unchanged): {source}')
        for path in destinations:print(f'Generated: {path}')
        return 0
    except (OSError,ValueError,KeyError,csv.Error) as exc:
        print(f'STEP2 Report FAIL: {exc}')
        return 1


if __name__=='__main__':
    raise SystemExit(main())
