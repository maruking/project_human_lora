"""Exactly the buffalo_l CPU estimator used in the approved 25-image comparison."""
from pathlib import Path
import numpy as np
from .identity_v2 import decode, digest, iou


class BuffaloPose:
    def __init__(self):
        import insightface
        from insightface.model_zoo import get_model
        pack = Path.home()/'.insightface/models/buffalo_l'
        paths = [pack/'det_10g.onnx', pack/'1k3d68.onnx']
        if not all(p.is_file() for p in paths):
            raise ValueError('Existing buffalo_l detection/3D landmark required; no download permitted')
        self.detector, self.landmark = [get_model(str(p), providers=['CPUExecutionProvider']) for p in paths]
        if self.landmark.taskname != 'landmark_3d_68' or not self.landmark.require_pose:
            raise ValueError('buffalo_l does not expose required 3D pose')
        if self.landmark.mean_lmk is None:
            raise ValueError('Installed InsightFace bundled meanshape missing; no download permitted')
        self.detector.prepare(-1, input_size=(640,640), det_thresh=0.5)
        self.landmark.prepare(-1)
        self.metadata = dict(estimator='buffalo_l_1k3d68', device='CPUExecutionProvider',
            insightface_version=insightface.__version__, model_hashes={p.name:digest(p) for p in paths},
            detection_size=[640,640], detection_threshold=0.5,
            pose_order='pitch,yaw,roll; returned yaw,pitch,roll without sign inversion or normalization',
            association='Unique maximal positive IoU with persisted STEP3 primary bbox',
            preprocessing='Original image; InsightFace Landmark.get defaults; same as comparison')

    def measure(self, row, path):
        from insightface.app.common import Face
        image = decode(path, row['image_sha256'])
        boxes, keypoints = self.detector.detect(image, max_num=0, metric='default')
        result = dict(status='NO_FACE', face_count=len(boxes), association_iou='', yaw='', pitch='', roll='')
        if not len(boxes):
            return result
        x,y,w,h = map(float,row['face_bbox'].split(','))
        scores = [iou(b[:4],(x,y,x+w,y+h)) for b in boxes]
        best = max(scores)
        result['association_iou'] = best
        if best <= 0 or scores.count(best) != 1:
            result['status'] = 'PRIMARY_FACE_AMBIGUOUS'
            return result
        index = scores.index(best)
        face = Face(bbox=boxes[index,:4], det_score=boxes[index,4], kps=keypoints[index])
        self.landmark.get(image,face)
        pose = np.asarray(face.pose)
        if pose.shape != (3,) or not np.isfinite(pose).all():
            raise ValueError('buffalo_l pose missing/nonfinite')
        pitch,yaw,roll = map(float,pose)
        result.update(status='MEASURED',yaw=yaw,pitch=pitch,roll=roll)
        return result
