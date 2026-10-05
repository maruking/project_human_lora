"""STEP3 lineage checks and deterministic CSV-only reports; no selection."""
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from collections import Counter
from build_step2_reports import read_dataset, validate_generation, stats, video_key
from common.step2_inputs import preflight_inputs

# Provisional geometric diagnostic bins, NOT quality Gates or validated blink/speech labels.
BLINK_DIAGNOSTIC_RATIO = 0.10
MOUTH_DIAGNOSTIC_BINS = (0.03, 0.15, 0.35)
METRICS = ('face_laplacian_score','face_tenengrad_score','face_sharpness_score',
           'face_laplacian_canonical_192','face_tenengrad_canonical_192',
           'eye_sharpness','mouth_sharpness','face_visibility_score','face_brightness_mean',
           'face_min_dimension','face_area_ratio','skin_texture_score','plasticity_ratio',
           'eye_openness_mean','mouth_open_ratio','eye_open_min','eye_open_asymmetry',
           'face_highlight_clip_ratio','face_bright_region_ratio','face_dynamic_range')


def validate_input(report, root, manifests):
    parsed, digest = read_dataset(report)
    summary = validate_generation(parsed, report.with_name('step2_summary.json'), manifests)
    # STEP2 keeps explicit still input separate from its formal video CSV. Reuse
    # that recorded boundary without accepting arbitrary non-manifest folders.
    recorded_stills = summary.get('supplemental_input_generation')
    supplemental = Path(recorded_stills['directory']) if recorded_stills is not None else None
    formal, _, current_stills = preflight_inputs(root, manifests, supplemental)
    expected, images, provenance, generation = formal
    if current_stills != recorded_stills:
        raise ValueError('STEP2 supplemental input generation mismatch; rerun STEP2 before STEP3')
    if summary['input_generation'] != generation:
        raise ValueError('STEP1/STEP2 generation fingerprint mismatch')
    if {r['filename'] for r in parsed} != set(provenance):
        raise ValueError('STEP2/raw inventory mismatch')
    return expected, generation, digest


def safe_output(output, limit, authoritative):
    if limit is not None:
        return output.with_name(output.stem + '.partial.csv')
    return output


def geometry_diagnostics(points, width, height):
    if points is None:
        return {}
    def ratio(outer, inner, upper, lower):
        horizontal = math.hypot((points[outer].x-points[inner].x)*width,(points[outer].y-points[inner].y)*height)
        if horizontal <= 0:
            raise ValueError('Degenerate landmark geometry')
        return math.hypot((points[upper].x-points[lower].x)*width,(points[upper].y-points[lower].y)*height)/horizontal
    left=ratio(33,133,159,145); right=ratio(263,362,386,374)
    mouth=ratio(61,291,13,14)
    label=('closed','slightly_open','open','very_open')[sum(mouth >= v for v in MOUTH_DIAGNOSTIC_BINS)]
    return dict(left_eye_openness=f'{left:.6f}',right_eye_openness=f'{right:.6f}',
                eye_openness_mean=f'{(left+right)/2:.6f}',blink_suspected=str(min(left,right)<BLINK_DIAGNOSTIC_RATIO).lower(),
                mouth_open_ratio=f'{mouth:.6f}',mouth_open_class=label)


def csv_bytes(rows, fields=None):
    fields=fields or list(rows[0])
    stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
    return ('\ufeff'+stream.getvalue()).encode('utf-8')


def distribution(rows):
    result=[]
    for metric in METRICS:
        values=[float(r[metric]) for r in rows if r.get(metric)!='' and r.get(metric) is not None]
        data=stats(values) if values else dict(count=0,mean='',std='',**{k:'' for k in ('min','p01','p05','p10','p25','p50','p75','p90','p95','p99','max')})
        result.append(dict(metric=metric,**data,missing_count=sum(r.get(metric) in ('', None) for r in rows),
                           not_applicable_count=sum(r.get('face_detected')=='false' for r in rows),
                           analysis_error_count=sum(r['face_gate_status']=='error' for r in rows)))
    return result


def summarize(rows):
    eligible=sum(r['face_eligible']=='true' for r in rows)
    return dict(frame_count=len(rows),eligible_count=eligible,eligible_ratio=round(eligible/len(rows),6),
                rejected_count=len(rows)-eligible,analysis_error_count=sum(r['face_gate_status']=='error' for r in rows),
                no_face_count=sum(r['face_detected']=='false' for r in rows),
                face_detected_count=sum(r['face_detected']=='true' for r in rows),
                single_face_count=sum(r['face_count']=='1' for r in rows),
                multiple_faces_count=sum(r['multiple_faces']=='true' for r in rows),
                facemesh_detected_count=sum(r.get('facemesh_detected')=='true' for r in rows),
                blink_suspected_count=sum(r.get('blink_suspected')=='true' for r in rows),
                mouth_open_count=sum(r.get('mouth_open_class')=='open' for r in rows),
                mouth_very_open_count=sum(r.get('mouth_open_class')=='very_open' for r in rows),
                beauty_fullbody_skipped_count=sum(r.get('beauty_filter_applicability')=='not_applicable_full_body' for r in rows))


def build_artifacts(rows, source_columns, generation, source_sha, arguments, partial=False):
    if not rows or len({r['filename'] for r in rows})!=len(rows):
        raise ValueError('Empty/duplicate audit universe')
    if not partial and len(rows)!=generation['frame_count']:
        raise ValueError('Incomplete production audit')
    # Keep the authoritative machine CSV and add Excel-compatible local links.
    # Root comes from the recorded STEP3 arguments, including CLI overrides.
    if arguments.get('images'):
        root = Path(arguments['images']).resolve()
        rows = [dict(row) for row in rows]
        for row in rows:
            relative = Path(row['filename'])
            target = (root / relative).resolve()
            if relative.is_absolute() or not target.is_relative_to(root):
                raise ValueError('Image link escapes the recorded STEP3 image directory')
            row['image_path'] = str(target)
            row['image_open'] = '=HYPERLINK("' + str(target).replace('"', '""') + '","画像を開く")'
    fields=list(source_columns)+sorted(set().union(*(set(r) for r in rows))-set(source_columns))
    dataset=csv_bytes(rows,fields)
    digest=hashlib.sha256(dataset).hexdigest()
    counts=summarize(rows)
    reason_names=sorted(set(reason for r in rows for reason in r['face_gate_reason'].split(';')) | set(('eligible','no_face','multiple_faces','global_blurry','face_blurry','face_too_small','low_visibility','hair_covered_face','one_eye_occluded','face_underexposed','face_backlit_underexposed','beauty_filter_detected','analysis_error','low_resolution_source')))
    reasons=[]
    for mode,names in [('overlapping_reason',reason_names),('exclusive_primary_category',sorted({r['face_gate_category'] for r in rows} | {'ELIGIBLE','REVIEW_UNKNOWN','REJECT_NO_FACE','REJECT_MULTIPLE_FACE','REJECT_LOW_RES','REJECT_BEAUTY_FILTER','REJECT_OCCLUSION','REJECT_BLUR','REJECT_SMALL_FACE'}))]:
        for name in names:
            selected=[r for r in rows if name in r['face_gate_reason'].split(';')] if mode=='overlapping_reason' else [r for r in rows if r['face_gate_category']==name]
            reasons.append(dict(count_type=mode,reason=name,frame_count=len(selected),percentage=round(100*len(selected)/len(rows),6),video_count=len({r['video_id'] for r in selected})))
    videos=[]
    for video in sorted({r['video_id'] for r in rows},key=video_key):
        group=[r for r in rows if r['video_id']==video]
        record=dict(video_id=video,**summarize(group))
        for reason in reason_names:
            record['reason_'+reason+'_count']=sum(reason in r['face_gate_reason'].split(';') for r in group)
        for metric in ('face_laplacian_score','face_tenengrad_score','face_laplacian_canonical_192','eye_sharpness','skin_texture_score','plasticity_ratio'):
            values=sorted(float(r[metric]) for r in group if r.get(metric))
            from statistics import median
            record['median_'+metric]=round(median(values),6) if values else ''
        videos.append(record)
    dist=distribution(rows)
    tail=max(1,math.ceil(len(rows)*.1)); order=sorted(rows,key=lambda r:int(r['quality_rank']))
    cross={}
    for name,group in [('global_top_10_percent',order[:tail]),('global_bottom_10_percent',order[-tail:])]:
        cross[name]=dict(summarize(group),face_blurry_count=sum('face_blurry' in r['face_gate_reason'].split(';') for r in group),beauty_filter_count=sum('beauty_filter_detected' in r['face_gate_reason'].split(';') for r in group))
    summary=dict(status='PARTIAL' if partial else 'FAIL' if counts['analysis_error_count'] else 'PASS',
                 input_generation=generation,step2_csv_sha256=source_sha,step3_csv_sha256=digest,
                 partial=partial,counts=counts,cross_analysis=cross,arguments={k:str(v) if isinstance(v,Path) else v for k,v in arguments.items()},
                 diagnostic_policy=dict(blink_ratio=BLINK_DIAGNOSTIC_RATIO,mouth_bins=MOUTH_DIAGNOSTIC_BINS,hard_gate=False),
                 full_row_preservation=not partial,source_columns=source_columns)
    canonical_policy = any(r.get('face_sharpness_metric') == 'face_laplacian_canonical_192' for r in rows)
    if canonical_policy:
        from common.step3_gate_policy import FLAGS
        summary['face_gate_architecture'] = dict(version='canonical192_review_v2',
            metric='face_laplacian_canonical_192',
            short_edges=sorted({r['face_sharpness_canonical_short_edge'] for r in rows}),
            thresholds=sorted({r['face_sharpness_gate_threshold'] for r in rows}),
            resize='aspect preserved; INTER_AREA shrink / INTER_CUBIC enlarge / IDENTITY copy',
            diagnostic_counts={f:sum(r.get(f)=='true' for r in rows) for f in FLAGS},
            diagnostic_state_counts=dict(Counter(r.get('diagnostic_state','UNKNOWN') for r in rows)),
            eye_presence_gate_counts=dict(Counter(r.get('eye_presence_gate_state','UNKNOWN') for r in rows)),
            review_diagnostic_configs=sorted({r.get('review_diagnostic_config_sha256','') for r in rows}),
            temporary_review_outputs='configured reports/passed and reports/borderline; disposable copies, never lineage/input',
            borderline='eligible AND ((EYE_DETAIL AND SKIN_PROCESSING) OR half-eye/blink OR exposure concern OR diagnostic measurement unavailable); no A/B/C')
    summary['review_counts'] = dict(
        official_eligible=sum(r['face_eligible']=='true' for r in rows),
        **{state:sum(r.get('diagnostic_state')==state for r in rows) for state in ('PASS','BORDERLINE','REJECT')},
        half_eye_suspected=sum(r.get('half_eye_suspected')=='true' for r in rows),
        overexposure_white_haze_suspected=sum(r.get('overexposure_white_haze_suspected')=='true' for r in rows),
        eye_presence_applicable=sum(r.get('eye_presence_gate_state')=='APPLICABLE' for r in rows),
        eye_presence_skipped_insufficient_scale=sum(r.get('eye_presence_gate_state')=='SKIPPED_INSUFFICIENT_SCALE' for r in rows))
    lines=['# STEP3 Face Quality Summary','',f"Status: {summary['status']}; rows: {len(rows)}; eligible: {counts['eligible_count']}; errors: {counts['analysis_error_count']}",'',
           'Regenerated solely from STEP3 CSV values. Source SHA256: '+digest,'',
           'All STEP2 values retained. Reasons overlap; primary categories are exclusive. Rejected includes error rows.',
           'Face percentiles use successful single-face rows (historical midrank formula). shot_type is provisional face scale, not STEP4 pose/composition.',
           'Geometric blink and mouth bins are provisional diagnostics, not validated blink/expression/speech labels and never rejection gates.',
           ('Native global/face sharpness, eye/skin/beauty/plasticity are diagnostic-only. Canonical192 is the face sharpness Hard Gate. Missing metrics are blank, not measured zero.' if canonical_policy else 'Historical architecture: beauty/filter and occlusion outputs are heuristic flags, not verified causes. FULL_BODY bypasses beauty rejection. Missing metrics are blank, not measured zero.'),'',
           '## Review diagnostics (not A/B/C)', '', '```json', json.dumps(summary['review_counts'],indent=2), '```', '',
           '## Detection and eligibility','', '```json',json.dumps(counts,indent=2),'```','',
           '## Reasons (overlap and exclusive categories)','', '| Type | Reason | Frames | % | Videos |','|---|---|---:|---:|---:|']
    lines += [f"| {r['count_type']} | {r['reason']} | {r['frame_count']} | {r['percentage']} | {r['video_count']} |" for r in reasons]
    if canonical_policy:
        lines += ['', '## Canonical face Gate audit', '',
                  'Native50 is superseded for Hard Gate use; native columns/percentiles remain historical-scale diagnostics. Canonical evaluates every detected single-face row directly, independent of eye sharpness. no_face/multiple_faces, visibility/FaceMesh, size/resolution, exposure/backlight, hair and per-eye presence formulas/cutoffs remain unchanged; eye-presence applicability now uses measured scale regardless of shot.',
                  'BORDERLINE is a separate review state: EYE_DETAIL plus SKIN_PROCESSING, or suspected half-eye/blink, or exposure concern. Native blur alone never causes BORDERLINE. These diagnostics never change eligibility or A/B/C. Eye-presence Hard Gate uses available per-eye evidence and configured upper-body minimum face dimension regardless of shot.',
                  '```json', json.dumps(summary['face_gate_architecture'],indent=2), '```']
    lines += ['', '## STEP2 × STEP3','', 'Top/bottom 10% use stored quality_rank with ceil(N × 0.10), ties already ordered by STEP2.', '```json',json.dumps(cross,indent=2),'```','', '## Video concentration','', '| Video | Frames | Eligible | Ratio | No face | Multiple | Errors |','|---|---:|---:|---:|---:|---:|---:|']
    lines += [f"| {r['video_id']} | {r['frame_count']} | {r['eligible_count']} | {r['eligible_ratio']} | {r['no_face_count']} | {r['multiple_faces_count']} | {r['analysis_error_count']} |" for r in videos]
    lines += ['', '## Distributions','', 'Population std, linear percentiles of stored values; missing includes N/A and errors (not additive categories).', '', '| Metric | Count | Missing | N/A (no face) | Errors | Min | P50 | P90 | Max |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    lines += [f"| {r['metric']} | {r['count']} | {r['missing_count']} | {r['not_applicable_count']} | {r['analysis_error_count']} | {r['min']} | {r.get('p50',r.get('P50',''))} | {r.get('p90',r.get('P90',''))} | {r['max']} |" for r in dist]
    lines += ['', '## Review examples','', 'Examples are audit references only; no selection or verified causal labels.','']
    for reason in reason_names+['blink_suspected','mouth_open','mouth_very_open']:
        group=[r for r in rows if reason in r['face_gate_reason'].split(';') or (reason=='blink_suspected' and r.get(reason)=='true') or (reason=='mouth_open' and r.get('mouth_open_class')=='open') or (reason=='mouth_very_open' and r.get('mouth_open_class')=='very_open')]
        lines.append('### '+reason);lines.append('')
        for r in group[:3]:
            lines.append(f"- `{r['filename']}`: global Lap={r.get('laplacian_score')}, face Lap={r.get('face_laplacian_score')}, eye={r.get('eye_sharpness')}, skin={r.get('skin_texture_score')}, plasticity={r.get('plasticity_ratio')}, openness={r.get('eye_openness_mean')}, mouth={r.get('mouth_open_ratio')}; {r['face_gate_reason']}")
        lines.append('')
    return {'dataset.csv':dataset,'step3_video_summary.csv':csv_bytes(videos),
            'step3_reason_summary.csv':csv_bytes(reasons),'step3_distribution_summary.csv':csv_bytes(dist),
            'step3_summary.json':(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode(),
            'STEP3_FACE_QUALITY_SUMMARY.md':('\n'.join(lines)+'\n').encode('utf-8')}


def publish(output, artifacts, failed=False, partial=False):
    """Stage all outputs; archive good reports and rollback ordinary publication errors."""
    output.parent.mkdir(parents=True,exist_ok=True)
    (output.parent/'step3_revision1_audit').mkdir(exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.step3-stage-',dir=output.parent))
    try:
        for name,data in artifacts.items(): (stage/name).write_bytes(data)
        if failed or partial:
            audit=output.parent/'step3_revision1_audit'/('failed' if failed else 'partial')
            audit.mkdir(parents=True,exist_ok=True)
            target=Path(tempfile.mkdtemp(prefix='run-',dir=audit))
            for name in artifacts: shutil.copy2(stage/name,target/name)
            if partial: os.replace(stage/'dataset.csv',output)
            return
        project=Path(__file__).resolve().parents[2]
        destinations={name:output if name=='dataset.csv' else project/'docs'/name if name.endswith('.md') else output.parent/name for name in artifacts}
        backup={p:p.read_bytes() if p.exists() else None for p in destinations.values()}
        if any(v is not None for v in backup.values()):
            archive=Path(tempfile.mkdtemp(prefix='previous-',dir=output.parent/'step3_revision1_audit')) if (output.parent/'step3_revision1_audit').exists() else None
            if archive:
                for p,data in backup.items():
                    if data is not None: (archive/p.name).write_bytes(data)
        changed=[]
        try:
            for name,p in destinations.items():
                p.parent.mkdir(parents=True,exist_ok=True)
                fd,tmp=tempfile.mkstemp(prefix='.step3-',dir=p.parent); os.close(fd)
                Path(tmp).write_bytes(artifacts[name])
                try: os.replace(tmp,p)
                finally:
                    if Path(tmp).exists():Path(tmp).unlink()
                changed.append(p)
        except Exception:
            for p in reversed(changed):
                if backup[p] is None:p.unlink(missing_ok=True)
                else:
                    fd,tmp=tempfile.mkstemp(prefix='.step3-rollback-',dir=p.parent);os.close(fd)
                    Path(tmp).write_bytes(backup[p]);os.replace(tmp,p)
            raise
    finally:
        shutil.rmtree(stage)
