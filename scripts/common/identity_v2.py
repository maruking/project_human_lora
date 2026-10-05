"""Identity-only STEP6 semantics. No quality, pose, quota or review features."""
from pathlib import Path
import hashlib
import json
import os
import sys
import numpy as np
import cv2

VERSION = 'step6_identity_v2'
TARGET_ROLES = {'UNIQUE', 'REPRESENTATIVE'}
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
FIELDS = ('step6_version', 'step6_status', 'identity_backend', 'identity_model',
    'identity_embedding_dim', 'identity_similarity_centroid', 'identity_similarity_max',
    'identity_similarity_median', 'identity_similarity_min', 'identity_threshold',
    'best_reference_id', 'reference_count', 'candidate_face_detection_score',
    'candidate_face_count', 'candidate_multi_face_detected', 'candidate_face_bbox',
    'candidate_primary_face_iou', 'identity_state', 'identity_passed', 'identity_rank',
    'identity_warning', 'identity_error', 'cluster_identity_fallback_needed')


class AssociationAmbiguous(ValueError):
    pass


def normalized(vector):
    vector = np.asarray(vector, dtype=np.float64)
    if vector.ndim != 1 or not vector.size or not np.isfinite(vector).all():
        raise ValueError('Embedding is missing/nonfinite/not a vector')
    norm = float(np.linalg.norm(vector))
    if norm <= 0:
        raise ValueError('Zero embedding')
    return vector / norm


def centroid(bank):
    bank = np.stack([normalized(v) for v in bank])
    return normalized(bank.mean(axis=0))


def identity_state(center, maximum, threshold, ambiguous=False, warning=False):
    if center is None or maximum is None:
        return 'IDENTITY_NOT_EVALUABLE'
    if ambiguous or warning:
        return 'IDENTITY_REVIEW'
    if center >= threshold:
        return 'IDENTITY_PASS'
    return 'IDENTITY_REVIEW' if maximum >= threshold else 'IDENTITY_REJECT'


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(handle.read()).hexdigest()


def reference_inventory(directory):
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise ValueError('Reference directory missing: ' + str(directory))
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)
    items = [{'filename': p.name, 'sha256': digest(p)} for p in files]
    fingerprint = hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return files, fingerprint


def decode(path, expected_sha=None):
    raw = Path(path).read_bytes()
    if expected_sha and hashlib.sha256(raw).hexdigest() != expected_sha.lower():
        raise ValueError('Image SHA256 differs from audited generation')
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Image decode failed')
    return image


class InsightFaceBackend:
    """Same original-image detection + model alignment for references/candidates."""
    def __init__(self, model_name='buffalo_l', device='auto'):
        import insightface
        import onnxruntime as ort
        # cuDNN sublibraries require both DLL search directories and PATH on Windows.
        self.dll_handles = []
        if os.name == 'nt':
            bins = list((Path(sys.prefix)/'Lib/site-packages/nvidia').glob('*/bin'))
            self.dll_handles = [os.add_dll_directory(str(p)) for p in bins]
            os.environ['PATH'] = os.pathsep.join(map(str, bins)) + os.pathsep + os.environ['PATH']
        if device != 'cpu' and hasattr(ort, 'preload_dlls'):
            ort.preload_dlls(directory='')
        use_gpu = device != 'cpu' and 'CUDAExecutionProvider' in ort.get_available_providers()
        if device == 'cuda' and not use_gpu:
            raise ValueError('Requested CUDA provider unavailable')
        from insightface.app import FaceAnalysis
        # Never implicitly download model weights during a pipeline run.
        root = Path.home()/'.insightface'
        pack = root/'models'/model_name
        if not all((pack/p).is_file() for p in ('det_10g.onnx', 'w600k_r50.onnx')):
            raise ValueError('Required buffalo_l detection/recognition weights missing: ' + str(pack))
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        self.app = FaceAnalysis(name=model_name, root=str(root), allowed_modules=['detection', 'recognition'], providers=providers)
        self.app.prepare(ctx_id=0 if use_gpu else -1)
        if set(self.app.models) != {'detection', 'recognition'}:
            raise ValueError('Detection/recognition model missing')
        for model in self.app.models.values():
            model.session.disable_fallback()  # GPU errors must be visible, never silent CPU retry.
            if use_gpu and 'CUDAExecutionProvider' not in model.session.get_providers():
                raise ValueError('CUDA model initialization failed')
        self.metadata = dict(backend='insightface', model=model_name, insightface_version=insightface.__version__,
            onnxruntime_version=ort.__version__, device='cuda' if use_gpu else 'cpu',
            providers={k:v.session.get_providers() for k,v in self.app.models.items()},
            model_sha256={p.name:digest(p) for p in pack.glob('*.onnx')},
            preprocessing='InsightFace original-image detection, five-point alignment, recognition model defaults',
            detection_input_size=[640,640], detection_threshold=self.app.det_model.det_thresh)

    def faces(self, image):
        return [dict(bbox=f.bbox.tolist(), detection_score=float(f.det_score), embedding=f.embedding)
                for f in self.app.get(image)]


def gallery(files, backend, threshold, min_count, max_count):
    records, bank = [], []
    seen = set()
    for path in files:
        record = dict(reference_id='ref_' + hashlib.sha256(path.name.encode()).hexdigest(), filename=path.name,
            image_sha256=digest(path), reference_status='INVALID', error='', face_count='', detected_face_bbox='',
            detection_score='', embedding_norm='', embedding_dim='', leave_one_out_centroid_similarity='',
            pairwise_similarities='', **backend.metadata)
        try:
            if record['image_sha256'] in seen:
                raise ValueError('Duplicate reference bytes are not independent anchors')
            seen.add(record['image_sha256'])
            faces = backend.faces(decode(path, record['image_sha256']))
            record['face_count'] = len(faces)
            if len(faces) != 1:
                raise ValueError('Reference requires exactly one detected face')
            face = faces[0]
            vector = normalized(face['embedding'])
            box = np.asarray(face['bbox'])
            if box.shape != (4,) or not np.isfinite(box).all() or box[2] <= box[0] or box[3] <= box[1]:
                raise ValueError('Invalid detected face bbox')
            record.update(reference_status='VALID', detected_face_bbox=json.dumps(face['bbox']),
                detection_score=face['detection_score'], embedding_norm=float(np.linalg.norm(face['embedding'])),
                embedding_dim=len(vector))
            bank.append((record['reference_id'], vector, record))
        except (ValueError, TypeError, OSError) as exc:
            record['error'] = str(exc)
        records.append(record)
    dimensions = {len(v) for _,v,_ in bank}
    if len(dimensions) > 1:
        raise ValueError('Reference embedding dimension mismatch')
    if len(bank) >= 2:
        for i, (_, vec, record) in enumerate(bank):
            others = [v for j,(_,v,_) in enumerate(bank) if j != i]
            try:
                loo = float(vec @ centroid(others))
                record['leave_one_out_centroid_similarity'] = loo
                record['pairwise_similarities'] = json.dumps({rid:float(vec@v) for rid,v,_ in bank}, sort_keys=True)
                if loo < threshold:
                    record['reference_status'] = 'REVIEW_OUTLIER'
            except ValueError as exc:
                record.update(reference_status='REVIEW_OUTLIER', error=str(exc))
    invalid = sum(r['reference_status'] == 'INVALID' for r in records)
    outliers = sum(r['reference_status'] == 'REVIEW_OUTLIER' for r in records)
    passed = min_count <= len(bank) <= max_count and len(files) <= max_count and not invalid and not outliers
    summary = dict(reference_audit_status='PASS' if passed else 'BLOCKED', total_references=len(files),
        valid_references=len(bank), invalid_references=invalid, reference_outliers=outliers,
        embedding_dim=next(iter(dimensions)) if len(dimensions)==1 else None,
        historical_identity_threshold=threshold, min_reference_count=min_count, max_reference_count=max_count,
        reference_confirmation='User places explicitly confirmed identity anchors in configured reference directory; not automatically selected',
        **backend.metadata)
    loos = [r['leave_one_out_centroid_similarity'] for r in records if isinstance(r['leave_one_out_centroid_similarity'], float)]
    summary['leave_one_out_distribution'] = distribution(loos)
    return records, summary, bank, centroid([v for _,v,_ in bank]) if passed else None


def distribution(values):
    if not values:
        return dict(count=0, min=None, P05=None, P10=None, median=None, P90=None, max=None)
    return dict(count=len(values), **dict(zip(('min','P05','P10','median','P90','max'),
        map(float,np.percentile(values,[0,5,10,50,90,100])))))


def iou(a, b):
    ax, ay, ar, ab = a
    bx, by, br, bb = b
    intersection = max(0, min(ar,br)-max(ax,bx))*max(0, min(ab,bb)-max(ay,by))
    union = (ar-ax)*(ab-ay)+(br-bx)*(bb-by)-intersection
    return intersection/union if union > 0 else 0


def associate(faces, row):
    if not faces:
        return None, None
    if len(faces) == 1:
        return faces[0], None
    x,y,w,h = map(float,row['face_bbox'].split(','))
    scores = [iou(f['bbox'], (x,y,x+w,y+h)) for f in faces]
    best = max(scores)
    if best <= 0 or scores.count(best) != 1:
        raise AssociationAmbiguous('No unique overlapping face for persisted primary bbox: ' + row['frame_id'])
    return faces[scores.index(best)], best


def evaluate(row, faces, bank, center, threshold, metadata):
    out = dict(row, **{k:'' for k in FIELDS})
    out.update(step6_version=VERSION, step6_status='MEASURED', identity_backend='insightface',
        identity_model=metadata['model'], identity_threshold=threshold, reference_count=len(bank),
        identity_passed='false', cluster_identity_fallback_needed='false')
    role = row['dedup_role']
    if role not in TARGET_ROLES:
        out.update(step6_status='NOT_APPLICABLE', identity_state='NOT_APPLICABLE_DUPLICATE_MEMBER' if role == 'DUPLICATE_MEMBER'
                   else ('UPSTREAM_ERROR' if role == 'ERROR' else 'NOT_APPLICABLE_UPSTREAM'))
        out['identity_passed'] = ''
        return out
    out.update(candidate_face_count=len(faces), candidate_multi_face_detected=str(len(faces)>1).lower())
    face, overlap = associate(faces, row)
    out['identity_state'] = 'IDENTITY_NOT_EVALUABLE'
    if face is None:
        out['identity_warning'] = 'NO_CANDIDATE_FACE'
    else:
        out.update(candidate_face_detection_score=face['detection_score'], candidate_face_bbox=json.dumps(face['bbox']),
            candidate_primary_face_iou=overlap if overlap is not None else '')
        try:
            vector = normalized(face['embedding'])
            if len(vector) != len(center):
                raise ValueError('Candidate embedding dimension differs from gallery')
            sims = [float(vector@v) for _,v,_ in bank]
            maximum = max(sims)
            similarity = float(vector@center)
            out.update(identity_embedding_dim=len(vector), identity_similarity_centroid=similarity,
                identity_similarity_max=maximum, identity_similarity_median=float(np.median(sims)),
                identity_similarity_min=min(sims), best_reference_id=bank[sims.index(maximum)][0],
                identity_state=identity_state(similarity, maximum, threshold, len(faces)>1))
            if len(faces)>1:
                out['identity_warning'] = 'MULTIPLE_CANDIDATE_FACES_PRIMARY_ASSOCIATED_BY_MAX_IOU'
        except (ValueError, TypeError) as exc:
            out['identity_warning'] = 'INVALID_CANDIDATE_EMBEDDING: ' + str(exc)
    out['identity_passed'] = str(out['identity_state']=='IDENTITY_PASS').lower()
    if role == 'REPRESENTATIVE' and out['identity_state'] in ('IDENTITY_REJECT','IDENTITY_NOT_EVALUABLE'):
        out['cluster_identity_fallback_needed'] = 'true'
    return out
