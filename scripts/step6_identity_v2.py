"""Versioned full-row identity audit. Legacy DINO runtime stays unchanged."""
import argparse
from collections import Counter
from contextlib import ExitStack
import csv
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from common.config import load_for_cli, get_section, configure_parser, resolve_config_path
from common.identity_v2 import (VERSION, TARGET_ROLES, FIELDS, InsightFaceBackend, reference_inventory,
    gallery, evaluate, decode, digest, distribution, AssociationAmbiguous)
from common.video_manifest import manifest_lock, write_csv_atomic, write_json_atomic
from common.pose_composition import geometry
from common.dedup_v2 import FIELDS as STEP5_FIELDS
from step5_dedup_v2 import read_csv, source_path, preflight as upstream_preflight, document, table, esc, link

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = dict(report='@reports/step5_dataset_report.csv', step5_summary='@reports/step5_dedup_summary.json',
    output_csv='@reports/step6_dataset_report.csv', summary='@reports/step6_identity_summary.json',
    markdown='docs/STEP6_IDENTITY_SUMMARY.md', review_html='docs/STEP6_IDENTITY_REVIEW.html',
    reference_csv='@reports/step6_reference_audit.csv', reference_summary='@reports/step6_reference_summary.json',
    reference_markdown='docs/STEP6_REFERENCE_AUDIT.md', reference_html='docs/STEP6_REFERENCE_REVIEW.html')
REF_KEYS = ('reference_csv','reference_markdown','reference_html','reference_summary')
FINAL_KEYS = ('output_csv','markdown','review_html','summary')


def preflight(report, summary_path, config, images):
    columns, rows = read_csv(report)
    required = {'step5_version','dedup_role','representative_frame_id','dedup_cluster_id','cluster_size',
        'frame_id','image_sha256','dataset_generation_id','filename','face_bbox','relative_path'}
    if required-set(columns):
        raise ValueError('Required STEP5 columns missing: ' + ','.join(sorted(required-set(columns))))
    if set(FIELDS) & set(columns):
        raise ValueError('STEP5 input contains STEP6 fields; wrong input generation')
    summary = json.loads(summary_path.read_text(encoding='utf-8-sig'))
    if summary.get('step5_version') != 'step5_dedup_v2' or summary.get('publication_status') != 'COMPLETE':
        raise ValueError('STEP5 must be step5_dedup_v2 / COMPLETE')
    if summary.get('total_rows') != len(rows) or summary.get('artifact_sha256',{}).get('output_csv') != digest(report):
        raise ValueError('STEP5 report differs from authoritative summary')
    settings = get_section(config,'step5_dedup')
    upstream_paths = [resolve_config_path(settings[k], config) for k in
        ('report','step4_summary','step3_report','step3_summary')]
    _, original = upstream_preflight(*upstream_paths, images)
    expected = {r['frame_id']:r for r in original}
    if len({r['frame_id'] for r in rows}) != len(rows) or set(expected) != {r['frame_id'] for r in rows}:
        raise ValueError('STEP5 IDs/count do not match current STEP3/4 universe')
    for path in upstream_paths:
        if summary.get('input_hashes',{}).get(str(path)) != digest(path):
            raise ValueError('STEP5 upstream generation changed: ' + str(path))
    clusters = {}
    roles = Counter(r['dedup_role'] for r in rows)
    if dict(roles) != summary.get('roles'):
        raise ValueError('STEP5 role counts mismatch')
    for row in rows:
        frame = row['frame_id']
        if row['step5_version'] != 'step5_dedup_v2':
            raise ValueError('Mixed STEP5 versions')
        for key, value in expected[frame].items():
            if key not in STEP5_FIELDS and row.get(key) != value:
                raise ValueError('STEP5 changed inherited lineage/measurement: ' + frame + '/' + key)
        role = row['dedup_role']
        if role not in TARGET_ROLES | {'DUPLICATE_MEMBER','NOT_APPLICABLE_STEP3_FATAL','ERROR'}:
            raise ValueError('Unknown STEP5 dedup role: ' + role)
        if not source_path(row, images).is_file():
            raise ValueError('Source missing: ' + frame)
        if role in TARGET_ROLES and geometry(row) is None:
            raise ValueError('Persisted primary bbox unavailable: ' + frame)
        if role in TARGET_ROLES | {'DUPLICATE_MEMBER'}:
            if not row['dedup_cluster_id'] or not row['representative_frame_id']:
                raise ValueError('Cluster lineage missing: ' + frame)
            clusters.setdefault(row['dedup_cluster_id'],[]).append(row)
        elif row['representative_frame_id']:
            raise ValueError('Not-applicable row has representative')
    for members in clusters.values():
        reps = [r for r in members if r['dedup_role'] in TARGET_ROLES]
        if len(reps) != 1 or any(r['representative_frame_id'] != reps[0]['frame_id'] or int(r['cluster_size']) != len(members) for r in members):
            raise ValueError('Inconsistent representative membership')
        if (len(members)==1) != (reps[0]['dedup_role']=='UNIQUE'):
            raise ValueError('Singleton/multi-member role inconsistent')
    return rows, {str(p):digest(p) for p in [report,summary_path,*upstream_paths]}


def ensure_unchanged(hashes):
    for name, value in hashes.items():
        if digest(Path(name)) != value:
            raise ValueError('Input evidence changed during STEP6: ' + name)


def safe_targets(targets, inputs, images, reference):
    if len({p.resolve() for p in [*targets.values(),*inputs]}) != len(targets)+len(inputs):
        raise ValueError('STEP6 input/output paths must be distinct')
    for path in targets.values():
        if not path.resolve().is_relative_to(ROOT) or any(path.resolve().is_relative_to(p.resolve()) for p in
            [images,reference,*(ROOT/k for k in ('input','work','scripts','bat','config','knowledge','tests','.agents','history'))]):
            raise ValueError('Unsafe STEP6 output destination: ' + str(path))
        if not path.name.lower().startswith('step6_'):
            raise ValueError('STEP6 output name must start step6_: ' + str(path))


def publish(contents, targets, marker, hashes):
    """Archive existing evidence, atomic individual files, summary last; caught-error rollback.

    A process crash is not a multi-file transaction; summary artifact hashes detect it.
    """
    ensure_unchanged(hashes)
    backups, changed = {}, []
    existing = {k:p for k,p in targets.items() if p.exists()}
    if existing:
        archive = targets[marker].parent/'bkup'/(VERSION+'_'+uuid.uuid4().hex)
        archive.mkdir(parents=True)
        for key, path in existing.items():
            backup = archive/(key+path.suffix)
            shutil.copy2(path,backup)
            if digest(path) != digest(backup):
                raise ValueError('Archive verification failed')
            backups[key] = backup
        write_json_atomic(archive/'MANIFEST.json', {k:dict(original=str(existing[k]),backup=str(v),sha256=digest(v)) for k,v in backups.items()})
    try:
        for key in [k for k in contents if k != marker]+[marker]:
            path = targets[key]
            path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(contents[key])
            try:
                os.replace(temporary,path)
                changed.append(key)
            finally:
                temporary.unlink(missing_ok=True)
    except OSError:
        for key in reversed(changed):
            path = targets[key]
            if key in backups:
                with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as handle:
                    restore = Path(handle.name)
                    handle.write(backups[key].read_bytes())
                os.replace(restore,path)
            else:
                path.unlink(missing_ok=True)
        raise


def encoded_artifacts(rows, summary, targets, csv_key, markdown_key, html_key, summary_key, body):
    import hashlib
    import io
    buffer = io.StringIO(newline='')
    columns = list(dict.fromkeys(k for row in rows for k in row))
    writer = csv.DictWriter(buffer,fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    contents = {csv_key:buffer.getvalue().encode('utf-8-sig'), html_key:body.encode('utf-8')}
    text = '# '+('STEP6 Reference Audit' if csv_key=='reference_csv' else 'STEP6 Identity Summary')+'\n\n'
    text += 'Identity-only audit. Historical threshold is not a measured FAR/FRR guarantee. No quality ranking, quotas or final training selection.\n\n'
    text += 'identity_state is authoritative. identity_passed is a compatibility field only. Duplicate members are not identity rejects.\n\n'
    text += '[Source-linked review]('+link(targets[html_key],targets[markdown_key])+')\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n'
    contents[markdown_key] = text.encode('utf-8')
    summary['artifact_sha256'] = {k:hashlib.sha256(v).hexdigest() for k,v in contents.items()}
    contents[summary_key] = json.dumps(summary,ensure_ascii=False,indent=2).encode('utf-8')
    return contents


def reference_html(records, summary, reference, page):
    body = '<p>★maruが本人と確認して配置した参照画像の監査です。候補の順位・画質評価は参照選択に使いません。</p>'
    body += '<p>Reference status: '+esc(summary['reference_audit_status'])+' / historical threshold: '+esc(summary['historical_identity_threshold'])+'</p><div class="grid">'
    for record in records:
        source = link(reference/record['filename'],page)
        body += '<article class="card"><a href="'+esc(source)+'" target="_blank"><img src="'+esc(source)+'"></a>'
        body += table(('項目','値'),[(k,record.get(k)) for k in ('reference_id','filename','image_sha256','reference_status','face_count','detected_face_bbox','detection_score','embedding_norm','embedding_dim','leave_one_out_centroid_similarity','pairwise_similarities','error')])+'</article>'
    return document('STEP6 reference gallery review',body+'</div>')


def review_html(rows, images, page):
    body = '<p>STEP6 Human Reviewは本人判定の校正だけを確認します。画像の鮮明さ、Poseの多様性、重複の正しさ、最終LoRA選定は評価しません。</p>'
    for state in ('IDENTITY_REJECT','IDENTITY_REVIEW','IDENTITY_NOT_EVALUABLE','LOWEST_PASS_BOUNDARY_EXAMPLES'):
        if state.startswith('LOWEST'):
            members = sorted((r for r in rows if r['identity_state']=='IDENTITY_PASS'),key=lambda r:(r['identity_similarity_centroid'],r['frame_id']))[:20]
        else:
            members = [r for r in rows if r['identity_state']==state]
        body += '<h2>'+state+' ('+str(len(members))+')</h2><div class="grid">'
        for row in members:
            source = link(source_path(row,images),page)
            body += '<article class="card"><a href="'+esc(source)+'" target="_blank"><img loading="lazy" src="'+esc(source)+'"></a>'
            keys = ('frame_id','video_id','source_id','dedup_role','best_score','global_rank','pose_bin','face_scale_bin',
                'identity_similarity_centroid','identity_similarity_max','identity_similarity_median','identity_threshold',
                'best_reference_id','identity_state','identity_warning','identity_error','cluster_identity_fallback_needed')
            body += table(('項目','値'),[(k,row.get(k)) for k in keys])+'</article>'
        body += '</div>'
    return document('STEP6 Identity Review',body)


def annotate(rows, images, backend, bank, center, threshold, limit=0):
    outputs, errors, measured = [], [], 0
    for row in rows:
        out = evaluate(row,[],bank,center,threshold,backend.metadata)
        if row['dedup_role'] in TARGET_ROLES:
            if limit and measured >= limit:
                out.update(step6_status='PARTIAL_NOT_EVALUATED',identity_warning='PARTIAL_LIMIT_NOT_EVALUATED',cluster_identity_fallback_needed='false')
            else:
                measured += 1
                try:
                    image = decode(source_path(row,images),row['image_sha256'])
                    if image.shape[:2] != (int(row['height']),int(row['width'])):
                        raise ValueError('Source dimensions differ from persisted primary bbox domain')
                    out = evaluate(row,backend.faces(image),bank,center,threshold,backend.metadata)
                except Exception as exc:
                    out.update(step6_status='ERROR',identity_state='IDENTITY_NOT_EVALUABLE',identity_error=str(exc),
                        identity_warning='MEASUREMENT_ERROR',identity_passed='false')
                    errors.append(row['frame_id']+': '+str(exc))
                    if isinstance(exc, (AssociationAmbiguous, RuntimeError)):
                        errors.append('STOP: ambiguous face association or identity runtime failure')
                        outputs.append(out)
                        for pending in rows[len(outputs):]:
                            item = evaluate(pending,[],bank,center,threshold,backend.metadata)
                            if pending['dedup_role'] in TARGET_ROLES:
                                item.update(step6_status='ABORTED_NOT_EVALUATED',identity_warning='IDENTITY_PROCESSING_ABORT',cluster_identity_fallback_needed='false')
                            outputs.append(item)
                        break
                if measured % 50 == 0:
                    print('Identity targets measured:',measured,flush=True)
        outputs.append(out)
    ranked = sorted((r for r in outputs if r['identity_similarity_centroid'] != ''),
        key=lambda r:(-r['identity_similarity_centroid'],-r['identity_similarity_max'],r['frame_id']))
    for rank,row in enumerate(ranked,1):
        row['identity_rank'] = rank
    if len(outputs)!=len(rows) or any(any(out[k]!=v for k,v in original.items()) for out,original in zip(outputs,rows)):
        raise ValueError('STEP6 failed full-row/inherited-column preservation')
    return outputs, errors


def main():
    config = load_for_cli()
    section = get_section(config,'step6_identity')
    parser = argparse.ArgumentParser(description='STEP6 InsightFace v2: explicit reference preflight, full-row identity audit')
    parser.add_argument('--config',type=Path)
    parser.add_argument('--reference-preflight-only',action='store_true')
    parser.add_argument('--preflight-only',action='store_true',help='Validate upstream metadata only, no model/image inference')
    parser.add_argument('--images',type=Path,default=resolve_config_path(config['paths']['raw_frames_dir'],config))
    parser.add_argument('--reference',type=Path,default=resolve_config_path(config['paths']['reference_face_dir'],config))
    for key,value in DEFAULT_PATHS.items():
        parser.add_argument('--'+key.replace('_','-'),type=Path,default=resolve_config_path(value,config))
    parser.add_argument('--device',choices=('auto','cpu','cuda'),default='auto')
    parser.add_argument('--limit',type=int,default=0)
    configure_parser(parser,config,'step6_identity',paths={'images':'raw_frames_dir','reference':'reference_face_dir'})
    args = parser.parse_args()
    if section.get('version') != VERSION or section.get('backend')!='insightface' or section.get('model_name')!='buffalo_l':
        raise ValueError('Explicit STEP6 v2 / insightface / buffalo_l config required')
    threshold = section['identity_threshold']
    if threshold != 0.55 or section['min_reference_count'] != 3 or section['max_reference_count'] != 20 or args.limit < 0:
        raise ValueError('Frozen STEP6 policy must use historical threshold0.55, minimum3, maximum20')
    targets = {k:getattr(args,k) for k in (*REF_KEYS,*FINAL_KEYS)}
    safe_targets(targets,[args.report,args.step5_summary],args.images,args.reference)
    # Reference source must not be a report/review/working candidate directory.
    if any(args.reference.resolve().is_relative_to((ROOT/k).resolve()) for k in ('docs','output','work')) or args.images.resolve()==args.reference.resolve():
        raise ValueError('Reference gallery must be explicit confirmed anchors, not a derived report/review directory')
    print(VERSION,'\nSTEP5 input:',args.report,'\nReference:',args.reference,'\nOutput:',args.output_csv,flush=True)
    with ExitStack() as stack:
        for path in (args.report.parent/'.step5_dedup_operation.lock',args.output_csv.parent/'.step6_identity_operation.lock',
            args.report.parent/'.step4_pose_operation.lock',args.report.parent/'.step3_best_operation.lock'):
            stack.enter_context(manifest_lock(path))
        rows, hashes = preflight(args.report,args.step5_summary,config,args.images)
        if args.preflight_only:
            print('UPSTREAM PREFLIGHT PASS; rows:',len(rows),'targets:',sum(r['dedup_role'] in TARGET_ROLES for r in rows))
            return 0
        files, fingerprint = reference_inventory(args.reference)
        backend = InsightFaceBackend(section['model_name'],args.device)
        records, ref_summary, bank, center = gallery(files,backend,threshold,section['min_reference_count'],section['max_reference_count'])
        ref_summary.update(step6_version=VERSION,reference_directory_sha256=fingerprint)
        reference_hashes = {str(p):digest(p) for p in files}
        if args.reference_preflight_only:
            body = reference_html(records,ref_summary,args.reference,targets['reference_html'])
            contents = encoded_artifacts(records,ref_summary,targets,'reference_csv','reference_markdown','reference_html','reference_summary',body)
            if reference_inventory(args.reference)[1] != fingerprint:
                raise ValueError('Reference inventory changed during preflight')
            publish(contents,{k:targets[k] for k in REF_KEYS},'reference_summary',{**hashes,**reference_hashes})
            print('REFERENCE PREFLIGHT:',ref_summary['reference_audit_status'],ref_summary['leave_one_out_distribution'])
            return 0 if center is not None else 1
        if center is None:
            raise ValueError('Reference preflight blocked: run --reference-preflight-only and review/fix anchors')
        approved = json.loads(args.reference_summary.read_text(encoding='utf-8-sig'))
        for key in ('reference_audit_status','reference_directory_sha256','model_sha256','historical_identity_threshold','insightface_version','onnxruntime_version'):
            if approved.get(key) != ref_summary.get(key):
                raise ValueError('Reference audit missing/stale/not PASS: ' + key + '; run reference preflight first')
        for key in ('reference_csv','reference_markdown','reference_html'):
            if approved.get('artifact_sha256',{}).get(key) != digest(targets[key]):
                raise ValueError('Reference audit artifact changed: '+key)
        hashes.update({str(targets[k]):digest(targets[k]) for k in REF_KEYS})
        hashes.update(reference_hashes)
        # Verify bytes of every target BEFORE candidate inference begins.
        for row in rows:
            if digest(source_path(row,args.images)) != row['image_sha256'].lower():
                raise ValueError('Source hash invalid: '+row['frame_id'])
        outputs, errors = annotate(rows,args.images,backend,bank,center,threshold,args.limit)
        final_targets = {k:targets[k] for k in FINAL_KEYS}
        partial = args.limit > 0
        if partial or errors:
            audit = args.output_csv.parent/'audit'/(VERSION+'_'+uuid.uuid4().hex)
            final_targets = {k:audit/p.name for k,p in final_targets.items()}
        summary = dict(step6_version=VERSION,publication_status='FAILED' if errors else ('PARTIAL' if partial else 'COMPLETE'),
            total_rows=len(outputs), input_roles=dict(Counter(r['dedup_role'] for r in rows)),
            candidate_target_count=sum(r['dedup_role'] in TARGET_ROLES for r in rows),
            states=dict(Counter(r['identity_state'] for r in outputs)), reference=ref_summary,
            historical_identity_threshold=threshold,input_hashes=hashes,errors=errors,
            dataset_generations_by_kind={kind:sorted({r['dataset_generation_id'] for r in rows if r['input_kind']==kind}) for kind in sorted({r['input_kind'] for r in rows})},
            outputs={k:str(p) for k,p in final_targets.items()}, **backend.metadata)
        measured = [r for r in outputs if r['identity_similarity_centroid'] != '']
        summary['similarity_distribution'] = distribution([r['identity_similarity_centroid'] for r in measured])
        summary['similarity_by_context'] = {key:{str(value):distribution([r['identity_similarity_centroid'] for r in measured if r.get(key)==value]) for value in sorted({r.get(key,'') for r in measured})} for key in ('pose_bin','face_scale_bin','input_kind')}
        summary['cluster_fallback_needed_count'] = sum(r['cluster_identity_fallback_needed']=='true' for r in outputs)
        summary['interpretation'] = 'Identity calibration only; no quality/quotas/final selection; identity_state authoritative; no measured current FAR/FRR claim'
        if reference_inventory(args.reference)[1] != fingerprint:
            raise ValueError('Reference inventory changed during candidate run')
        body = review_html(outputs,args.images,final_targets['review_html'])
        contents = encoded_artifacts(outputs,summary,final_targets,'output_csv','markdown','review_html','summary',body)
        publish(contents,final_targets,'summary',hashes)
        print(summary['publication_status'],summary['states'],'\nSummary:',final_targets['markdown'])
        return 1 if errors else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('[ERROR]',type(exc).__name__,str(exc),file=sys.stderr)
        sys.exit(1)
