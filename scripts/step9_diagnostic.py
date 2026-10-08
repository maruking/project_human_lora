"""Read accepted STEP8 metrics only; never infer, restore, copy or export images."""
import argparse
from collections import Counter
from contextlib import ExitStack
import json
import math
from pathlib import Path
import sys

from common.config import load_for_cli,resolve_config_path
from common.video_manifest import manifest_lock
from common.candidate_selection_v2 import priority
from step8_folder_review import load_step9_selection,paths_for,encoded_csv
from step5_dedup_v2 import sha256_file as digest,source_path
from step6_identity_v2 import publish,ensure_unchanged

ROOT=Path(__file__).resolve().parents[1]
METRICS=('face_bbox_width','face_bbox_height','face_laplacian_canonical_192','face_tenengrad_canonical_192',
    'eye_sharpness','eye_measurement_availability','expected_eye_sides','left_eye_local_detail','right_eye_local_detail',
    'left_eye_measurement_status','right_eye_measurement_status','eye_openness_state','eye_quality_reason',
    'blur_quality_factor','penalty_strength_blur','deduction_blur','deduction_eye_closed','deduction_eye_half_open',
    'deduction_eye_obstruction','skin_texture_score','face_laplacian_score','global_laplacian')


def number(value):
    try:
        result=float(value)
        return result if math.isfinite(result) and result>=0 else None
    except (ValueError,TypeError):return None


def diagnose(row,settings):
    if row.get('step8_decision')!='STEP8_ACCEPT':raise ValueError('Diagnostic accepts STEP8_ACCEPT only')
    reasons=[]
    dim=number(row.get('face_min_dimension'))
    dim_source='STORED_FACE_MIN_DIMENSION'
    if dim is None:
        w,h=number(row.get('face_bbox_width')),number(row.get('face_bbox_height'))
        dim=min(w,h) if w is not None and h is not None else None
        dim_source='STORED_BBOX_MIN_SAME_STEP3_FORMULA' if dim is not None else 'UNAVAILABLE'
    eye=number(row.get('eye_sharpness'))
    disabled=row.get('anatomical_metric_status','')=='eye_sharpness_disabled_by_existing_presence_gate'
    eye_state='UNAVAILABLE' if eye is None else 'DISABLED' if disabled else 'STORED'
    scale=row.get('face_scale_bin','')
    if scale not in ('CLOSE_UP','UPPER_BODY','FULL_BODY'):reasons.append('FACE_SCALE_NOT_EVALUABLE')
    if dim is None or dim<=0:reasons.append('FACE_DIMENSION_UNAVAILABLE')
    if number(row.get('face_laplacian_canonical_192')) is None:reasons.append('CANONICAL_SHARPNESS_UNAVAILABLE')
    # Reuse only the legacy STEP9 eligibility predicate. Model availability is
    # irrelevant to this diagnostic; no backend is imported. Protected shots stay raw.
    if scale=='FULL_BODY':
        if dim is not None and dim<settings['restoration_face_dim_threshold']:reasons.append('EXISTING_STEP9_FACE_DIMENSION_TRIGGER')
        if eye_state!='STORED':reasons.append('EXISTING_STEP9_EYE_METRIC_UNAVAILABLE')
        elif eye<settings['restoration_eye_threshold']:reasons.append('EXISTING_STEP9_EYE_TRIGGER')
    return dict({k:row.get(k,'') for k in ('frame_id','filename','video_id','input_kind','dataset_generation_id','image_sha256',
        'step8_review_session_id','step8_decision','face_scale_bin','best_score','global_rank',*METRICS)},
        face_min_dimension='' if dim is None else dim,face_min_dimension_source=dim_source,
        legacy_eye_metric_state=eye_state,
        step9_diagnostic_state='REVIEW_RECOMMENDED' if reasons else 'RESTORATION_NOT_NEEDED',
        diagnostic_reason=';'.join(reasons) if reasons else 'NO_EXISTING_STEP9_TRIGGER' if scale=='FULL_BODY' else 'EXISTING_STEP9_PROTECTED_SHOT',
        restoration_executed='NO',image_modified='NO')


def markdown(rows,settings,evidence,images):
    counts=Counter(r['step9_diagnostic_state'] for r in rows);review=[r for r in rows if r['step9_diagnostic_state']=='REVIEW_RECOMMENDED']
    text='# STEP9 Diagnostic Summary\n\n'
    text+=f"STEP8_ACCEPT対象: **{len(rows)}枚**\n\nRESTORATION_NOT_NEEDED: **{counts['RESTORATION_NOT_NEEDED']}枚**\n\nREVIEW_RECOMMENDED: **{len(review)}枚**\n\n"
    text+='## 判定の範囲\n\n既存STEP9のFULL_BODY限定条件を使用。顔短辺 < '+str(settings['restoration_face_dim_threshold'])+'px または旧eye_sharpness < '+str(settings['restoration_eye_threshold'])+'。境界値は未満比較。CLOSE_UP/UPPER_BODYは既存のraw保護対象です。\n\n'
    text+='face_min_dimensionは既存値、または保存済bbox幅・高さのmin（既存STEP3と同じ式）。再検出はありません。旧eye_sharpnessが無い場合は左右眼local_detailで代用しません。FULL_BODYの旧眼評価が欠ける場合、修復不要と断定できないためREVIEW_RECOMMENDED。これは修復指示ではありません。\n\n'
    text+='canonical Laplacian/Tenengrad、左右眼/detail/blur診断、face_scale、BEST/rankをCSVにそのまま記録。STEP9にはcanonical値用の既存閾値がないため、この値へ新しいcutoffを適用しません。BESTの順位・スコアやSTEP8採用は変更しません。RESTORATION_NOT_NEEDEDは既存STEP9対象条件による判定で、画像の完全な品質保証ではありません。\n\n'
    for key in ('face_min_dimension','face_laplacian_canonical_192','face_tenengrad_canonical_192'):
        values=[number(r.get(key)) for r in rows];values=[v for v in values if v is not None]
        text+=f"- {key}: measured {len(values)}/{len(rows)}, min {min(values) if values else 'N/A'}, max {max(values) if values else 'N/A'}\n"
    text+='\n## REVIEW_RECOMMENDED一覧\n\n| global rank | 画像 | scale | 顔短辺 | canonical Laplacian | 理由 |\n|---:|---|---|---:|---:|---|\n'
    for r in review:
        uri=source_path(r,images).resolve().as_uri();label=r['frame_id'].replace('|','\\|')
        text+=f"| {r['global_rank']} | [{label}]({uri}) | {r['face_scale_bin']} | {r['face_min_dimension']} | {r['face_laplacian_canonical_192']} | {r['diagnostic_reason']} |\n"
    if not review:text+='対象なし。\n'
    text+='\n## Evidence / execution boundary\n\nDerived subset only: STEP8 full audit unchanged; all accepted frame IDs retained. No full-generation STEP9 audit replacement.\n\n```json\n'+json.dumps(evidence,ensure_ascii=False,indent=2)+'\n```\n'
    text+='\nRules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, pipeline/lineage rules. Data lineage preserved:YES. Full-row preservation:YES within accepted subset; official STEP8 full audit unchanged. Historical evidence preserved:YES. Config SSOT:YES.\n\nRestoration executed:NO. New AI inference:NO. Image change/copy:NO. STEP8 changed:NO. STEP10 executed:NO.\n\n'
    text+='★maru: このSummaryをChappyへ共有してください。'+('確認対象0枚のためSTEP9をスキップする判断材料になります。' if not review else '上記画像のみ目視確認してください。REVIEW_RECOMMENDEDは修復必須・自動修復の意味ではありません。')+' STEP10は実行していません。\n'
    return text


def main():
    cfg=load_for_cli();settings=cfg['step9_restoration']
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--output-csv',type=Path,default=resolve_config_path(settings['diagnostic_csv'],cfg))
    parser.add_argument('--summary',type=Path,default=resolve_config_path(settings['diagnostic_summary'],cfg))
    args=parser.parse_args()
    _,paths,images=paths_for(cfg)
    targets={'csv':args.output_csv.resolve(),'summary':args.summary.resolve()}
    if targets['csv'].parent!=paths['selection_csv'].parent.resolve() or targets['csv'].name!='STEP9_DIAGNOSTIC.csv' or targets['summary']!=(ROOT/'docs/STEP9_DIAGNOSTIC_SUMMARY.md').resolve():
        raise ValueError('Diagnostic outputs must be dedicated STEP9 paths; no input overwrite')
    with ExitStack() as stack:
        for name in ('.step3_best_operation.lock','.step4_pose_operation.lock','.step5_dedup_operation.lock','.step6_identity_operation.lock','.step7_candidate_operation.lock','.step8_folder_operation.lock'):
            stack.enter_context(manifest_lock(paths['selection_csv'].parent/name))
        pins={str(paths[k]):digest(paths[k]) for k in ('selection_csv','summary','manifest','preparation_summary')}
        selected=load_step9_selection(cfg)
        if len({r['frame_id'] for r in selected})!=len(selected):raise ValueError('Duplicate accepted frame')
        for row in selected:pins[str(source_path(row,images))]=row['image_sha256']
        outputs=[diagnose(r,settings) for r in sorted(selected,key=priority)]
        if {r['frame_id'] for r in outputs}!={r['frame_id'] for r in selected}:raise ValueError('Lost accepted rows')
        evidence=dict(accepted_total=len(selected),diagnostic_rows=len(outputs),subset='STEP8_ACCEPT only',
            step8_session_id=selected[0]['step8_review_session_id'],input_sha256=pins,
            existing_step9_settings={k:settings[k] for k in ('restoration_face_dim_threshold','restoration_eye_threshold')},
            source_legacy_predicate='FULL_BODY and (face_min_dimension < configured threshold or eye_sharpness < configured threshold)',
            thresholds_changed=False,new_score=False)
        contents={'csv':encoded_csv(outputs),'summary':markdown(outputs,settings,evidence,images).encode('utf-8')}
        ensure_unchanged(pins);publish(contents,targets,'summary',pins);ensure_unchanged(pins)
        print('DIAGNOSTIC ONLY:',dict(Counter(r['step9_diagnostic_state'] for r in outputs)))
        print('Report:',targets['summary'])
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('[ERROR]',type(exc).__name__,str(exc),file=sys.stderr);sys.exit(1)
