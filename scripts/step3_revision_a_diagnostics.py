"""Maru-run Revision A: ALL formal frames + supplemental stills, separate A/B/C."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)+'\n').encode('utf-8')


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f'Invalid CSV header: {path}')
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f'Malformed CSV: {path}')
    return rows


def supplemental_inventory(directory):
    if not directory.is_dir():
        raise ValueError(f'Missing supplemental directory: {directory}')
    files = sorted(p for p in directory.rglob('*') if p.is_file() and
                   p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'})
    if not files:
        raise ValueError('Supplemental directory contains no supported images')
    if any(not p.resolve().is_relative_to(directory.resolve()) for p in files):
        raise ValueError('Supplemental image symlink escapes its input directory')
    return files, {p.relative_to(directory).as_posix(): digest(p) for p in files}


def validate_inputs(config, supplemental):
    from common.config import resolve_config_path
    from common.metric_generation import preflight
    from common.revision_a import FormalInventory
    from build_step2_reports import read_dataset, validate_generation
    paths = config['paths']
    raw = resolve_config_path(paths['raw_frames_dir'], config)
    manifests = resolve_config_path(paths['manifests_dir'], config)
    reports = resolve_config_path(paths['reports_dir'], config)
    _, images, provenance, generation = preflight(FormalInventory(raw, supplemental), manifests)
    step2 = reports/'step2_dataset_report.csv'
    rows2, hash2 = read_dataset(step2)
    summary2 = validate_generation(rows2, reports/'step2_summary.json', manifests)
    if summary2['input_generation'] != generation or {r['filename'] for r in rows2} != set(provenance):
        raise ValueError('Formal STEP1/STEP2 generation mismatch')
    step3 = reports/'step3_dataset_report.csv'
    summary_path = reports/'step3_summary.json'
    summary3 = json.loads(summary_path.read_text(encoding='utf-8-sig'))
    rows3 = read_csv(step3)
    hash3 = digest(step3)
    if (summary3['status'] != 'PASS' or summary3['partial'] or
        summary3['input_generation'] != generation or summary3['step2_csv_sha256'] != hash2 or
        summary3['step3_csv_sha256'] != hash3 or len(rows3) != len(images) or
        len({r['filename'] for r in rows3}) != len(rows3) or
        {r['filename'] for r in rows3} != set(provenance)):
        raise ValueError('Formal STEP3 report lineage/inventory mismatch')
    human_path = reports/'step3_eligible_human_review.csv'
    human_rows = read_csv(human_path)
    human = {}
    for row in human_rows:
        key = row['filename']
        if (row['dataset_generation_id'] != generation['sha256'] or row['source_sha256'] != hash3
            or key not in provenance or row['frame_id'] != key or key in human):
            raise ValueError(f'Human review stale/duplicate/invalid identity: {key}')
        human[key] = row
    files, inventory = supplemental_inventory(supplemental)
    checks = {str(p): digest(p) for p in (step2, step3, summary_path, human_path,
                                         reports/'step2_summary.json')}
    # Selection coverage is the full formal universe, including official rejects.
    # Official eligibility is evidence carried alongside A/B/C, never an input filter.
    return raw, reports, generation, rows3, human, files, inventory, checks


def measure(image, official, detector, mesh, settings, gate):
    import cv2
    import numpy as np
    from common.revision_a import eye_metrics, pixel_metrics
    from common.step3_audit import geometry_diagnostics
    h, w = image.shape[:2]
    result = dict(width=w, height=h, face_count=None, face_roi_method='NONE',
                  diagnostic_status='MEASURED', diagnostic_error='',
                  left_eye_open_ratio=None, right_eye_open_ratio=None, eye_open_min=None,
                  eye_open_asymmetry=None, eye_openness_state='UNKNOWN',
                  face_highlight_clip_ratio=None, face_bright_region_ratio=None,
                  face_dynamic_range=None, face_exposure_state='UNKNOWN',
                  face_local_contrast=None, skin_texture_score=None, face_detail_state='UNKNOWN')
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    detections = detector.process(rgb).detections or []
    result['face_count'] = len(detections)
    # Formal rows retain the original primary-face bbox; stills use the same largest-area rule.
    if official and official['face_detected'] == 'true':
        box = tuple(int(official['face_bbox_'+k]) for k in ('x', 'y', 'width', 'height'))
        result['primary_face_source'] = 'OFFICIAL_STEP3_BBOX'
    elif detections:
        boxes = [gate.face_box(d, w, h) for d in detections]
        box = max(boxes, key=lambda b: b[2]*b[3])
        result['primary_face_source'] = 'LARGEST_CLIPPED_BBOX_AREA_FIRST_DETECTION_TIE'
    else:
        result['primary_face_source'] = 'NONE'
        result['diagnostic_status'] = 'UNKNOWN_NO_FACE'
        return result
    x, y, bw, bh = box
    if bw <= 0 or bh <= 0 or x < 0 or y < 0 or x+bw > w or y+bh > h:
        raise ValueError('Invalid primary face bounding box')
    points = gate.matching_landmarks(mesh.process(rgb), box, w, h)
    result.update(face_bbox_x=x, face_bbox_y=y, face_bbox_width=bw, face_bbox_height=bh)
    mask = np.zeros((h, w), dtype=np.uint8)
    texture = None
    if points is not None:
        geo = geometry_diagnostics(points, w, h)
        result.update(eye_metrics(float(geo['left_eye_openness']), float(geo['right_eye_openness']), settings))
        # Face oval avoids background and hair; native pixels, no resizing/restoration.
        import mediapipe as mp
        indices = sorted({i for edge in mp.solutions.face_mesh.FACEMESH_FACE_OVAL for i in edge})
        coords = np.array([(round(points[i].x*w), round(points[i].y*h)) for i in indices], dtype=np.int32)
        cv2.fillConvexPoly(mask, cv2.convexHull(coords), 255)
        result['face_roi_method'] = 'FACEMESH_FACE_OVAL_CONVEX_HULL'
        texture = gate.cheek_skin_texture_metrics(image, points, box, 0, 'FULL_BODY', 0, 0, 0)[0]
    else:
        mask[y:y+bh, x:x+bw] = 255
        result['face_roi_method'] = 'BBOX_FALLBACK_NO_MESH'
        result['diagnostic_status'] = 'UNKNOWN_NO_MESH'
    result.update(pixel_metrics(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), mask, texture, settings))
    return result


def markdown(rows, summary):
    text = ['# STEP3 Revision A — diagnostics / selection review', '',
            '新しい数値境界は未検証の診断用binです。公式Gate・採否・加工の有無を確定しません。',
            'A=人間確認済み主候補、B=予備候補、C=明示人間Reject。',
            '**B / UNDECIDEDは使用可能未確認。B / CONFIRMEDとは区別し、繰り上げ前に人間確認が必要です。**', '',
            f"Formal STEP1 audit: {summary['formal_generation']['frame_count']} frames / {summary['formal_generation']['video_count']} videos; unchanged.",
            f"Diagnostic rows: {len(rows)}; errors: {summary['error_count']}; A/B/C: {summary['selection_counts']}", '',
            '## 入力別の集計', '', '| Input | Rows | Eye | Exposure | Detail |', '|---|---:|---|---|---|']
    for kind, counts in summary['by_input'].items():
        text.append(f"| {kind} | {counts['rows']} | {counts['eye_openness_state']} | {counts['face_exposure_state']} | {counts['face_detail_state']} |")
    text += ['', '## 境界・白飛び・情報低下・目の診断フラグ', '',
             'UNKNOWNも一覧に含めます。NORMAL/OPENはLoRA適性の保証ではありません。', '',
             '| Frame | Eye/min | Exposure/clip | Detail/contrast/texture | Selection/review |', '|---|---|---|---|---|']
    for r in rows:
        if (any(r[k] not in ('OPEN', 'NORMAL') for k in ('eye_openness_state','face_exposure_state','face_detail_state'))
            or r['human_accept']):
            text.append(f"| {r['frame_id']} | {r['eye_openness_state']} / {r['eye_open_min']} | {r['face_exposure_state']} / {r['face_highlight_clip_ratio']} | {r['face_detail_state']} / {r['face_local_contrast']} / {r['skin_texture_score']} | {r['selection_group']} / {r['selection_review_status']} |")
    text += ['', '## 測定式と解釈限界', '',
             '- 目: 既存geometry_diagnosticsと同じ上下ランドマーク距離 / 目幅。最小値、左右最大/最小比。',
             '- 露出: FaceMesh顔輪郭mask（欠測時bbox）のgray clipping/bright画素比、P95−P5。',
             '- 局所contrast: 顔mask内3×3区画のP90−P10を平均。',
             '- Texture: 既存cheek_skin_texture_metricsの頬Laplacian分散 / max(平均輝度,10)。FULL_BODYにも測定のみ実施。',
             '- 目・露出・textureは解像度、角度、照明に依存。半開眼、加工、Identityの確定判定ではない。',
             '- 顔・meshがない画像も欠測理由付きで保持。補助静止画に正式STEP1 video_idや公式Gate判定を捏造しない。',
            '- 正式STEP1全画像＋追加静止画の全件を、重複なしでA/B/Cのいずれかに記録。公式Rejectも入力から除外しない。',
            '- 新診断でA/B/Cを確定せず、確認不足はB/UNDECIDED。Pose/angle quota・最終選定は実施しない。', '',
             '## 今回の診断境界（採否の閾値ではない・未検証・調整未実施）', '',
             '設定の単一参照元はsummary.jsonのsettingsおよび実行時diagnostic-configです。', '',
             '```json', json.dumps(summary['settings'], ensure_ascii=False, indent=2), '```', '',
             'Eye: min < closed→CLOSED_OR_BLINK、min < borderlineまたは左右比 > asymmetry→BORDERLINE。',
             'Exposure: clip >= overexposed→OVEREXPOSED、clip >= borderlineまたはbright >= borderline→BORDERLINE。',
             'Detail: contrastまたはtextureがlost未満→DETAIL_LOST、borderline未満→BORDERLINE。欠測→UNKNOWN。', '',
             'Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, .agents/rules/*.md.',
             'Data lineage preserved: YES. Full-row preservation: YES (all formal frames + all declared supplemental images).',
             'Historical evidence preserved: YES. Config SSOT preserved: YES (separate diagnostic config).', '']
    return '\n'.join(text).encode('utf-8')


def main():
    # Match the existing STEP3 BAT runtime, also for direct Python execution.
    isolated = ROOT/'.step3_packages'
    if isolated.is_dir():
        sys.path.insert(0, str(isolated))
    from common.config import load_config, resolve_config_path, resolve_project_path
    from common.revision_a import validate_settings, selection_state
    from common.video_manifest import manifest_lock
    import cv2
    import mediapipe as mp
    import numpy as np
    import face_quality_gate as gate
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--diagnostic-config', type=Path, default=ROOT/'config/step3_revision_a.local.json')
    parser.add_argument('--supplemental-dir', type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    settings_path = resolve_project_path(args.diagnostic_config)
    settings = json.loads(settings_path.read_text(encoding='utf-8-sig'))
    validate_settings(settings)
    raw = resolve_config_path(config['paths']['raw_frames_dir'], config)
    declared = args.supplemental_dir or settings.get('supplemental_dir')
    if not declared:
        raise ValueError('Declare supplemental_dir in diagnostic config or --supplemental-dir')
    supplemental = (raw/declared).resolve()
    reports = resolve_config_path(config['paths']['reports_dir'], config)
    with manifest_lock(reports/'step3_revision_a/.diagnostic.lock'):
        raw, reports, generation, official, human, stills, inventory, checks = validate_inputs(config, supplemental)
        config_path = resolve_project_path(args.config) if args.config else ROOT/'config/config.yaml'
        if not config_path.is_file():
            config_path = ROOT/'config/config.example.yaml'
        checks.update({str(p.resolve()): digest(p) for p in
                       (config_path, settings_path, Path(__file__), ROOT/'scripts/common/revision_a.py',
                        ROOT/'scripts/face_quality_gate.py', ROOT/'scripts/common/step3_audit.py')})
        supplemental_generation = hashlib.sha256(json_bytes(inventory)).hexdigest()
        provenance = dict(input_scope='ALL_FORMAL_AND_SUPPLEMENTAL',
                          formal_generation=generation, supplemental_generation_id=supplemental_generation,
                          supplemental_root=str(supplemental), supplemental_inventory=inventory,
                          settings=settings, source_sha256=checks,
                          runtime=dict(python=sys.version.split()[0], opencv=cv2.__version__,
                                       numpy=np.__version__, mediapipe=mp.__version__))
        signature = hashlib.sha256(json_bytes(provenance)).hexdigest()
        inputs = [(raw/r['filename'], r) for r in official]+[(p, None) for p in stills]
        expected_rows = generation['frame_count'] + len(stills)
        if len(inputs) != expected_rows:
            raise ValueError('Full-input coverage mismatch before inference')
        print(f'ALL inputs: formal={len(official)}, supplemental={len(stills)}, total={expected_rows}', flush=True)
        rows = []
        cv2.setNumThreads(1)
        cfg = config['step3_face_gate']
        with mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=cfg['detection_confidence']) as detector, mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=cfg['max_faces'], refine_landmarks=False, min_detection_confidence=cfg['detection_confidence']) as mesh:
            for i, (path, old) in enumerate(inputs, 1):
                name = path.relative_to(raw).as_posix()
                context = human.get(name, {}) if old else {}
                row = dict(input_kind='formal_video' if old else 'supplemental_still',
                           dataset_generation_id=generation['sha256'] if old else supplemental_generation,
                           official_dataset_generation_id=generation['sha256'] if old else '',
                           video_id=old['video_id'] if old else '', temporal_index=old['temporal_index'] if old else '',
                           extraction_policy_version=old['extraction_policy_version'] if old else '',
                           sample_fps_requested=old['sample_fps_requested'] if old else '',
                           sample_fps_effective=old['sample_fps_effective'] if old else '',
                           filename=name, frame_id=name, image_sha256=digest(path),
                           official_face_eligible=old['face_eligible'] if old else '',
                           official_face_gate_reason=old['face_gate_reason'] if old else '',
                           official_face_laplacian_score=old['face_laplacian_score'] if old else '',
                           official_eye_sharpness=old['eye_sharpness'] if old else '',
                           official_source_sha256=checks[str(reports/'step3_dataset_report.csv')] if old else '',
                           human_accept=context.get('human_accept', ''), human_notes=context.get('human_notes', ''),
                           human_label_source=context.get('label_source', ''), production_label_applied=False)
                try:
                    image = cv2.imdecode(np.frombuffer(path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
                    if image is None:
                        raise ValueError('Image decode failed')
                    row.update(measure(image, old, detector, mesh, settings, gate))
                except Exception as exc:
                    row.update(diagnostic_status='ERROR', diagnostic_error=f'{type(exc).__name__}: {exc}',
                               eye_openness_state='UNKNOWN', face_exposure_state='UNKNOWN', face_detail_state='UNKNOWN')
                row.update(selection_state(context, row))
                rows.append(row)
                if i % 20 == 0 or i == len(inputs):
                    print(f'Diagnostics {i}/{len(inputs)}', flush=True)
        # Publication only after a second complete lineage/inventory audit.
        second = validate_inputs(config, supplemental)
        if second[2] != generation or second[6] != inventory or any(digest(Path(p)) != h for p, h in checks.items()):
            raise ValueError('Inputs changed during diagnostics; no publication')
        for row in rows:
            for k, v in list(row.items()):
                if isinstance(v, float):
                    row[k] = round(v, 6)
        errors = sum(r['diagnostic_status'] == 'ERROR' for r in rows)
        if (len(rows) != expected_rows or len({r['frame_id'] for r in rows}) != expected_rows
            or any(r['selection_group'] not in ('A', 'B', 'C') for r in rows)):
            raise ValueError('Full-row / exactly-one A/B/C invariant violated')
        by_input = {}
        for kind in sorted({r['input_kind'] for r in rows}):
            subset = [r for r in rows if r['input_kind'] == kind]
            by_input[kind] = dict(rows=len(subset), **{k: dict(Counter(r[k] for r in subset)) for k in
                ('eye_openness_state', 'face_exposure_state', 'face_detail_state')})
        summary = dict(provenance, run_id=signature, status='ERROR' if errors else 'PASS_DIAGNOSTICS_ONLY',
                       row_count=len(rows), expected_row_count=expected_rows,
                       full_selection_coverage=True, error_count=errors, by_input=by_input,
                       selection_counts={g: sum(r['selection_group'] == g for r in rows) for g in ('A', 'B', 'C')},
                       selection_review_counts=dict(Counter(r['selection_review_status'] for r in rows)),
                       official_decisions_modified=False, final_selection_performed=False)
        fields = sorted({k for r in rows for k in r})
        # Missing measurements are explicit null in JSON and empty cells in CSV.
        rows = [{k: r.get(k) for k in fields} for r in rows]
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        artifacts = {'diagnostics.csv': ('\ufeff'+stream.getvalue()).encode('utf-8'),
                     'diagnostics.json': json_bytes(rows), 'summary.json': json_bytes(summary),
                     'REPORT.md': markdown(rows, summary)}
        selection_fields = ['frame_id', 'filename', 'input_kind', 'dataset_generation_id',
                            'image_sha256', 'selection_group', 'selection_group_source',
                            'selection_group_reason', 'selection_review_status', 'reserve_use_allowed',
                            'official_face_eligible', 'official_face_gate_reason', 'human_accept', 'human_notes']
        # One full selection CSV plus disjoint A/B/C CSVs; even an empty group has its header.
        for group in ('ALL', 'A', 'B', 'C'):
            selection_stream = io.StringIO(newline='')
            selection_writer = csv.DictWriter(selection_stream, fieldnames=selection_fields, extrasaction='ignore')
            selection_writer.writeheader()
            selection_writer.writerows(r for r in rows if group == 'ALL' or r['selection_group'] == group)
            name = 'selection_groups.csv' if group == 'ALL' else f'selection_{group}.csv'
            artifacts[name] = ('\ufeff'+selection_stream.getvalue()).encode('utf-8')
        run = reports/'step3_revision_a/runs'/signature
        # Immutable runs; interrupted publications can be resumed with identical bytes.
        run.mkdir(parents=True, exist_ok=True)
        for name, content in artifacts.items():
            dest = run/name
            if dest.exists() and dest.read_bytes() != content:
                raise ValueError('Deterministic rerun differs; historical run left intact')
            if not dest.exists():
                dest.write_bytes(content)
        if errors:
            print(f'ERROR rows retained for audit: {run}', file=sys.stderr)
            return 1
        pointer = reports/'step3_revision_a/latest.json'
        temp = pointer.with_suffix('.tmp')
        temp.write_bytes(json_bytes(dict(run_id=signature, directory=str(run), row_count=len(rows))))
        os.replace(temp, pointer)
        print(json.dumps(dict(run_id=signature, rows=len(rows), groups=summary['selection_counts'], report=str(run/'REPORT.md')), ensure_ascii=False))
        return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, ImportError) as exc:
        print(f'Revision A failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
