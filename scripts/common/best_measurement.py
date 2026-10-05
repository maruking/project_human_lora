"""Measurement-only reuse of STEP3 kernels. Legacy apply_gate is never called."""
import math
import cv2
import numpy as np
from common.best_pose import estimate_head_pose
from common.revision_a import face_mask, pixel_metrics, eye_metrics, load_review_settings
from common.step3_audit import geometry_diagnostics
from common.best_ranking import METRICS


def measure_rows(rows, root, settings, gate):
    diagnostic_settings, diagnostic_path, diagnostic_hash=load_review_settings(settings.get('diagnostic_config'))
    confidence=settings.get('detection_confidence',.5)
    if not gate.mp or not hasattr(gate.mp,'solutions'):
        raise RuntimeError('MediaPipe solutions unavailable; use requirements-step3.txt / .step3_packages')
    with gate.mp.solutions.face_detection.FaceDetection(model_selection=1,min_detection_confidence=confidence) as detector, \
         gate.mp.solutions.face_mesh.FaceMesh(static_image_mode=True,max_num_faces=gate.MAX_FACES,
                                            refine_landmarks=False,min_detection_confidence=confidence) as mesh:
        for i,row in enumerate(rows,1):
            # A fresh measurement never carries old face diagnostics forward.
            row.update({k:'' for k in METRICS})
            row.update(analysis_status='MEASURED',analysis_error='',measurement_warnings='',
                       face_detected='false',face_count=0,confirmed_face_count=0,
                       face_evaluability='NOT_EVALUABLE',crop_geometry_status='UNKNOWN',
                       detector_status='SINGLE_MEDIAPIPE_CONFIDENCE_AND_VALID_BBOX',
                       detector_disagreement='NOT_MEASURED_SINGLE_DETECTOR',
                       measurement_version='best_native_core192_v1',diagnostic_config_sha256=diagnostic_hash,
                       eye_measurement_availability='UNAVAILABLE',pose_status='UNAVAILABLE',
                       face_bbox='',yaw='',pitch='',roll='',left_eye_openness='',right_eye_openness='',
                       native_face_laplacian='',native_face_tenengrad='',
                       native_global_laplacian=row.get('laplacian_score',''),skin_texture_score='',plasticity_ratio='')
            print(f'[{i}/{len(rows)}] {row["filename"]}',flush=True)
            warnings=[]
            try:
                source,_=gate.image_path(root,row['filename'])
                image=cv2.imdecode(np.fromfile(source,dtype=np.uint8),cv2.IMREAD_COLOR)
                if image is None:raise ValueError('Image decode failed')
                h,w=image.shape[:2];rgb=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
                detections=detector.process(rgb).detections or []
                valid=[]
                for d in detections:
                    box=gate.face_box(d,w,h)
                    if d.score and float(d.score[0])>=confidence and min(box[2:])>0:valid.append((d,box))
                row.update(raw_detector_face_count=len(detections),face_count=len(valid),confirmed_face_count=len(valid),
                           face_detected=str(bool(valid)).lower())
                if not valid:continue
                detection,box=max(valid,key=lambda item:item[1][2]*item[1][3])
                x,y,bw,bh=box
                core=gate.crop_face_core(image,box)
                if core.size==0 or min(core.shape[:2])<3:
                    row['crop_geometry_status']='INVALID';continue
                row.update(crop_geometry_status='VALID',face_evaluability='MEASURED',face_bbox=','.join(map(str,box)),
                           face_short_edge_px=min(bw,bh),face_area_ratio=bw*bh/(h*w),width=w,height=h,
                           frame_edge_contact=str(x==0 or y==0 or x+bw==w or y+bh==h).lower())
                native_lap,native_ten=gate.sharpness(core)
                canonical,method=gate.canonical_face_copy(core,settings.get('canonical_short_edge',192))
                lap,ten=gate.sharpness(canonical)
                row.update(face_laplacian_canonical_192=lap,face_tenengrad_canonical_192=ten,
                           native_face_laplacian=native_lap,native_face_tenengrad=native_ten,
                           native_global_laplacian=row.get('laplacian_score',''),canonical_resize_method=method,
                           face_bbox_x=x,face_bbox_y=y,face_bbox_width=bw,face_bbox_height=bh)
                # Mesh failure is measurement uncertainty, not a new quality rejection.
                try:points=gate.matching_landmarks(mesh.process(rgb),box,w,h)
                except Exception as exc:points=None;warnings.append('landmark:'+str(exc))
                row['landmark_status']='MEASURED' if points else 'UNAVAILABLE_BBOX_FALLBACK'
                if points:
                    try:
                        row.update(geometry_diagnostics(points,w,h))
                        row.update(eye_metrics(float(row['left_eye_openness']),float(row['right_eye_openness']),diagnostic_settings))
                        left,right,legacy_valid=gate.eye_presence_metrics(image,points,w,h)
                        row.update(left_eye_presence=left,right_eye_presence=right,legacy_eye_presence_valid=str(legacy_valid).lower())
                        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
                        available=[]
                        for name,a,b,fx,fy in (('left_eye',33,133,1.5,1.2),('right_eye',263,362,1.5,1.2),('mouth',61,291,1.4,.8)):
                            span=math.hypot((points[a].x-points[b].x)*w,(points[a].y-points[b].y)*h)
                            cx=(points[a].x+points[b].x)*w/2;cy=(points[a].y+points[b].y)*h/2
                            # No artificial minimum patch size: degeneracy stays unavailable.
                            if span<=0 or not(0<=cx<w and 0<=cy<h):
                                row[name+'_local_detail']='';row[name+'_roi_status']='UNAVAILABLE';continue
                            patch=gate.extract_patch(gray,(cx,cy),(span*fx,span*fy))
                            if patch.size==0 or min(patch.shape)<3:
                                row[name+'_local_detail']='';row[name+'_roi_status']='UNAVAILABLE';continue
                            row[name+'_local_detail']=gate.patch_normalized_tenengrad(patch)
                            row[name+'_roi_width']=patch.shape[1];row[name+'_roi_height']=patch.shape[0]
                            row[name+'_roi_status']='MEASURED';available.append(name)
                        row['eye_measurement_availability']='MEASURED' if all(k in available for k in ('left_eye','right_eye')) else 'PARTIAL'
                    except Exception as exc:warnings.append('eye_detail:'+str(exc))
                    try:
                        pose=estimate_head_pose(points,w,h)
                        if pose is not None and all(math.isfinite(v) for v in pose):
                            row.update(zip(('yaw','pitch','roll'),pose));row['pose_status']='MEASURED'
                    except Exception as exc:warnings.append('pose:'+str(exc))
                try:
                    visible,level,signals,_=gate.visibility(detection,points,box,image)
                    # Missing mesh is not a measured visibility zero.
                    row['face_visibility_score']=visible if points else ''
                    row['face_visibility_signals']=signals
                except Exception as exc:warnings.append('visibility:'+str(exc))
                try:
                    oval={i for edge in gate.mp.solutions.face_mesh.FACEMESH_FACE_OVAL for i in edge} if points else ()
                    mask,method=face_mask(points,box,h,w,oval)
                    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
                    if not np.any(mask):raise ValueError('Empty exposure mask')
                    exposure=pixel_metrics(gray,mask,None,diagnostic_settings)
                    pixels=gray[mask>0]
                    row.update(face_brightness_mean=float(pixels.mean()),highlight_clip_ratio=exposure['face_highlight_clip_ratio'],
                               face_shadow_ratio=float(np.mean(pixels<settings.get('shadow_pixel_max',40))),
                               dynamic_range_p95_p5=exposure['face_dynamic_range'],local_face_contrast=exposure['face_local_contrast'],
                               exposure_roi_method=method,exposure_diagnostic_state=exposure['face_exposure_state'])
                except Exception as exc:warnings.append('exposure:'+str(exc))
                if points:
                    try:
                        eye_values=[row[k] for k in ('left_eye_local_detail','right_eye_local_detail') if row.get(k) not in (None,'')]
                        texture,plasticity,_=gate.cheek_skin_texture_metrics(image,points,box,sum(eye_values)/len(eye_values) if eye_values else 0,'FULL_BODY',0,0,0)
                        row['skin_texture_score']=texture
                        row['plasticity_ratio']=plasticity if eye_values else ''
                    except Exception as exc:warnings.append('skin:'+str(exc))
                row['measurement_warnings']=';'.join(warnings)
            except Exception as exc:
                row.update(analysis_status='ERROR',analysis_error=type(exc).__name__+': '+str(exc))
    return rows
