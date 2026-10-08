"""Bounded diagnostic comparison only; never updates production STEP4."""
import argparse
from collections import Counter
import csv
import html
import json
from pathlib import Path

import numpy as np
from common.config import load_config, resolve_config_path
from common.identity_v2 import decode, digest, iou
from common.pose_composition import POSE_BINS, settings_from, yaw_bin
from step5_dedup_v2 import preflight, source_path

ROOT = Path(__file__).resolve().parents[1]


def sample(rows, required, per_bin=5):
    by_id = {r['frame_id']: r for r in rows}
    if required not in by_id:
        raise ValueError('Required counterexample missing: ' + required)
    chosen = [by_id[required]]
    for bucket in POSE_BINS[:-1]:
        pool = sorted((r for r in rows if r['pose_bin'] == bucket),
                      key=lambda r: (int(r['global_rank']), r['frame_id']))
        count = sum(r['pose_bin'] == bucket for r in chosen)
        while count < per_bin:
            available = [r for r in pool if r not in chosen and not any(
                r['video_id'] and r['video_id'] == c['video_id'] and
                abs(int(r['temporal_index']) - int(c['temporal_index'])) <= 2
                for c in chosen)]
            if not available:
                break
            used = Counter(r['source_id'] for r in chosen)
            pick = min(available, key=lambda r: (used[r['source_id']], int(r['global_rank']), r['frame_id']))
            chosen.append(pick)
            count += 1
    if not 20 <= len(chosen) <= 30:
        raise ValueError('Insufficient diverse comparison samples: ' + str(len(chosen)))
    if any(not any(r['pose_bin'] == p for r in chosen) for p in POSE_BINS[:-1]):
        raise ValueError('Requested pose coverage unavailable')
    return chosen


def ranked_sample(rows, config):
    guidance = config['step8_folder_review']
    # Diagnostic allocation chosen by the user; not a production selection policy.
    counts = dict(zip(POSE_BINS[:-1], (16, 10, 10, 2, 2)))
    if sum(counts.values()) != guidance['final_count_target']:
        raise ValueError('Comparison allocation differs from configured target')
    chosen = []
    for bucket, count in counts.items():
        low, high = guidance['pose_guidance'][bucket]
        if not low <= count <= high:
            raise ValueError('Comparison allocation outside existing pose guidance')
        pool = sorted((r for r in rows if r['pose_bin'] == bucket and
                       r['ranking_eligible'].lower() == 'true'),
                      key=lambda r: (int(r['global_rank']), r['frame_id']))
        if len(pool) < count:
            raise ValueError('Insufficient samples for ' + bucket)
        chosen.extend(pool[:count])
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--required-frame')
    parser.add_argument('--ranked-lora-comparison', action='store_true',
                        help='40 diagnostic samples: stored-pose top global ranks, 16/10/10/2/2')
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    settings = config['step5_dedup']
    inputs = [resolve_config_path(settings[k], config) for k in
              ('report', 'step4_summary', 'step3_report', 'step3_summary')]
    images = resolve_config_path(config['paths']['raw_frames_dir'], config)
    _, rows = preflight(*inputs, images)  # read-only upstream integrity check
    if not args.ranked_lora_comparison and not args.required_frame:
        parser.error('--required-frame is necessary for the original comparison mode')
    chosen = ranked_sample(rows, config) if args.ranked_lora_comparison else sample(rows, args.required_frame)
    suffix = '_rank40' if args.ranked_lora_comparison else ''
    csv_path = ROOT/f'output/reports/step4_pose_estimator_comparison{suffix}.csv'
    html_path = ROOT/f'docs/STEP4_POSE_ESTIMATOR_COMPARISON{suffix.upper()}.html'
    if csv_path.exists() or html_path.exists():
        raise ValueError('Comparison already exists; preserve evidence before another run')
    protected = list((ROOT/'output/reports').glob('*')) + list((ROOT/'config').glob('*'))
    protected = [p for p in protected if p.is_file()] + list((ROOT/'scripts').rglob('*.py'))
    before = {p: digest(p) for p in protected}
    paths = {r['frame_id']: source_path(r, images) for r in chosen}
    for row in chosen:
        if digest(paths[row['frame_id']]) != row['image_sha256']:
            raise ValueError('Sample source hash mismatch: ' + row['frame_id'])
    # Explicit existing paths bypass all model-pack downloading and unrelated models.
    pack = Path.home()/'.insightface/models/buffalo_l'
    weights = [pack/'det_10g.onnx', pack/'1k3d68.onnx']
    if not all(p.is_file() for p in weights):
        raise ValueError('Installed buffalo_l detection/3D landmark unavailable; STOP')
    import insightface
    from insightface.model_zoo import get_model
    from insightface.app.common import Face
    detector, landmark = [get_model(str(p), providers=['CPUExecutionProvider']) for p in weights]
    if landmark.taskname != 'landmark_3d_68' or not landmark.require_pose:
        raise ValueError('Installed buffalo_l does not expose pose; STOP')
    detector.prepare(-1, input_size=(640, 640), det_thresh=0.5)
    landmark.prepare(-1)
    output = []
    for row in chosen:
        record = {k: row[k] for k in ('frame_id','filename','video_id','dataset_generation_id','image_sha256',
                                     'global_rank','best_score','review_state','fatal_reject_reason')}
        record.update({f'current_{k}': row[k] for k in ('yaw','pitch','roll','pose_bin')})
        record.update(alternative_yaw='', alternative_pitch='', alternative_roll='',
                      alternative_pose_bin='NOT_EVALUABLE', estimator_status='', association_iou='',
                      detected_face_count=0, current_pose_status=row['pose_status'])
        image = decode(paths[row['frame_id']], row['image_sha256'])
        boxes, keypoints = detector.detect(image, max_num=0, metric='default')
        record['detected_face_count'] = len(boxes)
        if not len(boxes):
            record['estimator_status'] = 'ALTERNATIVE_NO_FACE'
        else:
            x,y,w,h = map(float, row['face_bbox'].split(','))
            overlaps = [iou(b[:4], (x,y,x+w,y+h)) for b in boxes]
            best = max(overlaps)
            record['association_iou'] = best
            if best <= 0 or overlaps.count(best) != 1:
                record['estimator_status'] = 'ALTERNATIVE_PRIMARY_FACE_AMBIGUOUS'
            else:
                index = overlaps.index(best)
                face = Face(bbox=boxes[index,:4], det_score=boxes[index,4], kps=keypoints[index])
                landmark.get(image, face)
                pose = np.asarray(face.pose)
                if pose.shape != (3,) or not np.isfinite(pose).all():
                    raise ValueError('buffalo_l pose unavailable/nonfinite; STOP')
                pitch,yaw,roll = map(float, pose)
                record.update(alternative_yaw=yaw, alternative_pitch=pitch, alternative_roll=roll,
                              alternative_pose_bin=yaw_bin(yaw, settings_from(config)),
                              estimator_status='MEASURED_SIGN_CONVENTION_UNVALIDATED')
        output.append(record)
        print(row['frame_id'], record['estimator_status'], flush=True)
    if not any(r['alternative_yaw'] != '' for r in output):
        raise ValueError('No buffalo_l pose obtained; STOP')
    assert all(digest(p) == sha for p,sha in before.items()), 'Protected artifact changed'
    assert all(digest(paths[r['frame_id']]) == r['image_sha256'] for r in chosen)
    provenance = dict(sample_count=len(output), universe_count=len(rows),
        sampling=('Stored STEP4 bins, strict global_rank ascending within each bin; 16/10/10/2/2. '
                  'No source/diversity/duplicate filters: estimator comparison, not approved LoRA selection.'
                  if args.ranked_lora_comparison else
                  'Five per stored pose bin; mandatory counterexample, source diversity, temporal spacing >2'),
        current='Authoritative stored STEP4 angles: STEP3 MediaPipe six-point solvePnP; not rerun',
        alternative='Installed buffalo_l 1k3d68: 68-point 3D affine fit to bundled meanshape; raw pitch,yaw,roll in degrees',
        device='CPUExecutionProvider', insightface_version=insightface.__version__,
        model_hashes={p.name:digest(p) for p in weights}, input_hashes={str(p):digest(p) for p in inputs},
        bin_thresholds=settings_from(config), current_bin_counts=dict(Counter(r['current_pose_bin'] for r in output)),
        statuses=dict(Counter(r['estimator_status'] for r in output)),
        rules_checked=['AGENTS.md','.agents/AGENTS.md','PROJECT.md','lora_pipeline_rules.md','data_lineage_rules.md'],
        lineage_preserved=True, full_row_preservation='N/A diagnostic subset only; authoritative universe untouched',
        historical_evidence_preserved=True, config_ssot_preserved=True,
        documentation='Checked; no production Knowledge/Decision change warranted by an unvalidated comparison')
    esc = lambda v: html.escape(str(v), quote=True)
    body = '<!doctype html><html lang="ja"><meta charset="utf-8"><title>STEP4 pose estimator comparison</title><style>body{font-family:system-ui;margin:24px;background:#eef2f6}article{background:white;padding:20px;margin:20px 0;border-radius:10px}img{max-width:100%;max-height:650px}table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:10px}pre{white-space:pre-wrap}</style>'
    body += '<h1>STEP4 顔向き推定方式の比較（診断のみ）</h1><p>画像を見て、どちらの推定が実際の顔向きに合うか確認してください。旧値は正式reportの保存値です。代替値はbuffalo_lの生の角度です。左右の符号・pitch/rollの座標規約は未校正で、同じ符号が同じ見た目を表す保証はありません。代替pose_binは現行設定（正yaw=RIGHT、負yaw=LEFT）を機械的に適用した仮表示です。値の一致だけでは精度を判断できません。画像は左右反転していません。閾値・正式判定は変更していません。</p>'
    body += '<p>3Q = THREE_QUARTER。既存のbinで標本化したため、実際の顔向きの網羅はHuman Reviewで確認してください。</p>'
    if args.ranked_lora_comparison:
        body += '<p>40枚比較：現行分類の正面16、左右3Q各10、左右PROFILE各2。各分類のglobal rank上位から厳密に抽出しています。重複排除・動画上限・Human Reject除外は適用していません。Human Rejectも比較証拠として表示し、採用候補へ復活させる処理はありません。LoRA適性・最終採用は未確定です。</p><p><a href="STEP4_POSE_ESTIMATOR_COMPARISON.html">前回25枚比較と既知の失敗例を見る</a></p>'
    last_bucket = None
    for index, record in enumerate(output,1):
        if args.ranked_lora_comparison and last_bucket != record['current_pose_bin']:
            last_bucket = record['current_pose_bin']
            body += '<h2>'+esc(last_bucket)+'</h2>'
        uri = paths[record['frame_id']].as_uri()
        body += f'<article><h2>{index:02d} · {esc(record["frame_id"])}</h2><p>global rank: {esc(record["global_rank"])} / BEST: {esc(record["best_score"])} / Human state: {esc(record["review_state"])}</p><a href="{esc(uri)}" target="_blank"><img loading="lazy" src="{esc(uri)}"></a><table><tr><th>方式</th><th>yaw °</th><th>pitch °</th><th>roll °</th><th>pose_bin</th></tr>'
        for prefix,label in [('current','現行：FaceMesh 6点 + solvePnP（保存値）'),('alternative','代替：buffalo_l 68点3D（生値）')]:
            body += '<tr><td>'+label+'</td>'+''.join('<td>'+esc(record[prefix+'_'+key])+'</td>' for key in ('yaw','pitch','roll','pose_bin'))+'</tr>'
        body += f'</table><p>Status: {esc(record["estimator_status"])} / primary bbox IoU: {esc(record["association_iou"])} / faces: {record["detected_face_count"]}</p><p>Human Review：現行が合う / 代替が合う / 両方合う / 両方違う / 判断不能（結果はChappyへ共有）</p></article>'
    body += '<h2>監査・再現情報</h2><pre>'+esc(json.dumps(provenance,ensure_ascii=False,indent=2))+'</pre><p>Reference: <a href="https://github.com/deepinsight/insightface/blob/master/python-package/insightface/model_zoo/landmark.py">InsightFace official landmark implementation</a>. Local installed implementation inspected; no downloads/installations. Full production executed: NO. STEP3/4 official and STEP5+: unchanged.</p></html>'
    with csv_path.open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader(); writer.writerows(output)
    html_path.write_text(body, encoding='utf-8')
    print(json.dumps(provenance,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
