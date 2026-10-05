"""Human folder interaction: copies only, immutable lineage and explicit decisions."""
from collections import Counter
import hashlib
import json
import re
import shutil
import statistics
import uuid
from pathlib import Path
from common.candidate_selection_v2 import POSES,SCALES,VERTICALS,priority
from step5_dedup_v2 import source_path,sha256_file as digest

VERSION='step8_folder_review_v2'
EXTRA=('step8_version','step8_review_candidate','step8_decision','step8_selection_status',
    'step8_review_session_id','review_filename','full_review_path','accept_review_path')


def validate_settings(settings):
    if settings['version']!=VERSION:raise ValueError('Wrong STEP8 version')
    values=[settings[k] for k in ('final_count_min','final_count_target','final_count_max')]
    if any(not isinstance(v,int) or isinstance(v,bool) or v<1 for v in values) or not values[0]<=values[1]<=values[2]:
        raise ValueError('Invalid final count guidance')
    for key,labels in (('pose_guidance',POSES),('scale_guidance',SCALES[:-1])):
        if set(settings[key])!=set(labels):raise ValueError('Guidance labels must match stored classification')
        for limits in settings[key].values():
            if len(limits)!=2 or any(not isinstance(v,int) or v<0 for v in limits) or limits[0]>limits[1]:
                raise ValueError('Invalid soft guidance range')


def pose_folder(pose,settings):
    low,high=settings['pose_guidance'][pose]
    return f'{POSES.index(pose)+1:02d}_{pose}__ACCEPT_{low}-{high}'


def no_links(path):
    """Reject symlinks/junctions before descending into user-controlled folders."""
    path=Path(path)
    pending=[path]
    while pending:
        current=pending.pop()
        if not current.exists() and not current.is_symlink():continue
        st=current.lstat()
        if current.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:
            raise ValueError('Review path contains a symlink/junction: '+str(current))
        if current.is_dir():pending.extend(current.iterdir())


def safe_root(root,images,project):
    root=Path(root);work=Path(project).resolve()/'work'
    if not root.resolve().is_relative_to(work) or root.resolve()==work or root.resolve().is_relative_to(images.resolve()) or images.resolve().is_relative_to(root.resolve()):
        raise ValueError('Review root must be an isolated derived work subdirectory')
    for p in [work,root.parent,root]:
        no_links(p) if p==root else check_ancestor(p)


def check_ancestor(path):
    for p in [path,*path.parents]:
        if p.exists() and (p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('Unsafe linked ancestor')


def manifest_rows(candidates,settings,root):
    if len({r['frame_id'] for r in candidates})!=len(candidates):raise ValueError('Duplicate candidate frame')
    result=[];names=set()
    for row in sorted(candidates,key=priority):
        if row['pose_bin'] not in POSES or row['vertical_pose'] not in VERTICALS or row['face_scale_bin'] not in SCALES:
            raise ValueError('Invalid stored pose/scale label')
        original=Path(row['filename']).name
        original=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',original)
        prefix=f"R{int(row['global_rank']):04d}_B{float(row['best_score']):05.1f}_{row['vertical_pose']}_{row['face_scale_bin']}__"
        name=prefix+original
        if len(name)>230 or name.casefold() in names:
            original=Path(original)
            suffix='__F'+hashlib.sha256(row['frame_id'].encode()).hexdigest()[:16]+original.suffix
            name=prefix+original.stem[:max(1,230-len(prefix)-len(suffix))]+suffix
        if name.casefold() in names:raise ValueError('Ambiguous review filename')
        names.add(name.casefold());directory=root/pose_folder(row['pose_bin'],settings)
        result.append(dict(row,review_filename=name,step7_selection_reason=row['selection_reason'],
            full_review_path=str(directory/'FULL'/name),accept_review_path=str(directory/'ACCEPT'/name)))
    return result


def check_existing(root,settings,reset=False):
    if not root.exists():return
    no_links(root)
    expected={pose_folder(p,settings) for p in POSES}|{'.step8_review_session.json'}
    if {p.name for p in root.iterdir()}-expected:raise ValueError('Unknown review root entries; preserve and inspect before rebuild')
    for folder in root.iterdir():
        if not folder.is_dir():continue
        if {p.name for p in folder.iterdir()}-{'FULL','ACCEPT'}:raise ValueError('Unknown pose folder entries')
        accept=folder/'ACCEPT'
        if accept.exists() and any(accept.iterdir()) and not reset:
            raise ValueError('ACCEPT is non-empty. STOP; explicit --reset-review archives all choices before rebuild')


def stage_review(candidates,settings,root,images,project,hashes,reset=False):
    validate_settings(settings);safe_root(root,images,project);check_existing(root,settings,reset)
    records=manifest_rows(candidates,settings,root)
    root.parent.mkdir(parents=True,exist_ok=True)
    stage=root.parent/('.step8_stage_'+uuid.uuid4().hex);stage.mkdir()
    session=uuid.uuid4().hex
    try:
        for pose in POSES:
            for kind in ('FULL','ACCEPT'):(stage/pose_folder(pose,settings)/kind).mkdir(parents=True)
        for row in records:
            source=source_path(row,images)
            if digest(source)!=row['image_sha256']:raise ValueError('Source image hash changed: '+row['frame_id'])
            hashes[str(source)]=row['image_sha256']
            destination=stage/pose_folder(row['pose_bin'],settings)/'FULL'/row['review_filename']
            shutil.copy2(source,destination)
            if digest(destination)!=row['image_sha256']:raise ValueError('Review copy hash mismatch')
        (stage/'.step8_review_session.json').write_text(json.dumps(dict(version=VERSION,session_id=session)),encoding='utf-8')
    except Exception:
        # Stage contains only this invocation's derived copies, never ACCEPT work.
        if stage.resolve().parent!=root.parent.resolve() or not stage.name.startswith('.step8_stage_'):
            raise ValueError('Unsafe stage cleanup target')
        no_links(stage)
        shutil.rmtree(stage);raise
    return records,stage,session


def install_review(stage,root,settings,reset=False):
    check_existing(root,settings,reset)
    archive=None
    if root.exists():
        directory=root.parent/'bkup';check_ancestor(directory);directory.mkdir(exist_ok=True)
        archive=directory/(VERSION+'_'+uuid.uuid4().hex)
        if not archive.resolve().is_relative_to(root.parent.resolve()):raise ValueError('Unsafe archive target')
        root.replace(archive)
    try:stage.replace(root)
    except OSError:
        if archive:archive.replace(root)
        raise
    return archive


def accepted_ids(records,root,settings,rejected=()):
    no_links(root)
    check_existing(root,settings,reset=True)
    by_name={r['review_filename']:r for r in records};ids=set();paths={}
    if len(by_name)!=len(records):raise ValueError('Review filename ambiguity')
    expected_full={Path(r['full_review_path']).resolve() for r in records}
    actual_full=set()
    for pose in POSES:
        directory=root/pose_folder(pose,settings)
        if not (directory/'FULL').is_dir() or not (directory/'ACCEPT').is_dir():raise ValueError('Review folder missing; prepare first')
        for p in (directory/'FULL').iterdir():
            if not p.is_file():raise ValueError('Nested/unknown FULL entry')
            actual_full.add(p.resolve())
        for p in (directory/'ACCEPT').iterdir():
            if not p.is_file():raise ValueError('Nested/unknown ACCEPT entry')
            row=by_name.get(p.name)
            if row is None:raise ValueError('Unknown ACCEPT file: '+p.name)
            if row['frame_id'] in ids:raise ValueError('Same frame accepted twice')
            if p.resolve()!=Path(row['accept_review_path']).resolve():raise ValueError('Accepted file in wrong pose folder')
            if row['frame_id'] in set(rejected):raise ValueError('Current-version Human Reject cannot be finalized')
            if digest(p)!=row['image_sha256']:raise ValueError('ACCEPT copy has been edited/replaced')
            ids.add(row['frame_id']);paths[str(p)]=row['image_sha256']
    if actual_full!=expected_full:raise ValueError('FULL must retain every candidate exactly once')
    for row in records:
        p=Path(row['full_review_path'])
        if digest(p)!=row['image_sha256']:raise ValueError('FULL copy changed')
        paths[str(p)]=row['image_sha256']
    return ids,paths


def selection_rows(full,records,accepted,settings,session):
    mapping={r['frame_id']:r for r in records};accepted=set(accepted)
    if accepted-set(mapping):raise ValueError('Accept set outside manifest')
    count=len(accepted)
    status='NEED_MORE_SELECTION' if count<settings['final_count_min'] else 'TOO_MANY_SELECTED' if count>settings['final_count_max'] else 'VALID'
    selected=[r for r in records if r['frame_id'] in accepted]
    outputs=[]
    for row in full:
        if set(row)&set(EXTRA):raise ValueError('Upstream already contains STEP8 decisions')
        record=mapping.get(row['frame_id'])
        outputs.append(dict(row,step8_version=VERSION,step8_review_candidate=str(record is not None).lower(),
            step8_decision='STEP8_ACCEPT' if row['frame_id'] in accepted else 'STEP8_NOT_SELECTED' if record else 'NOT_APPLICABLE_NOT_IN_REVIEW_POOL',
            step8_selection_status=status,step8_review_session_id=session,**{key:record[key] if record else '' for key in ('review_filename','full_review_path','accept_review_path')}))
    warnings=[]
    distributions={field:dict(Counter(r[field] for r in selected)) for field in ('pose_bin','vertical_pose','face_scale_bin','identity_state')}
    pose=[]
    for label,limits in settings['pose_guidance'].items():
        actual=distributions['pose_bin'].get(label,0)
        pose.append(dict(pose_bin=label,folder=pose_folder(label,settings),recommended_min=limits[0],recommended_max=limits[1],actual_accept_count=actual))
        if not limits[0]<=actual<=limits[1]:warnings.append(dict(reason='POSE_GUIDANCE_WARNING',label=label,actual=actual,recommended=limits))
    for label,limits in settings['scale_guidance'].items():
        actual=distributions['face_scale_bin'].get(label,0)
        if not limits[0]<=actual<=limits[1]:warnings.append(dict(reason='SCALE_GUIDANCE_WARNING',label=label,actual=actual,recommended=limits))
    for label,minimum in settings['vertical_guidance'].items():
        actual=distributions['vertical_pose'].get(label,0)
        if actual<minimum:warnings.append(dict(reason='VERTICAL_GUIDANCE_WARNING',label=label,actual=actual,recommended_min=minimum))
    videos=Counter(r['video_id'] for r in selected if r['input_kind']=='formal_video')
    scores=[float(r['best_score']) for r in selected];ranks=[int(r['global_rank']) for r in selected]
    return outputs,dict(step8_version=VERSION,publication_status='COMPLETE',selection_status=status,finalization_allowed=status=='VALID',
        full_upstream_rows=len(full),review_candidate_count=len(records),accepted_total=count,not_selected_total=len(records)-count,
        final_count_min=settings['final_count_min'],final_count_target=settings['final_count_target'],final_count_max=settings['final_count_max'],
        pose_guidance=pose,distributions=distributions,guidance_warnings=warnings,
        source_summary=dict(video_count=len(videos),supplemental_still_count=sum(r['input_kind']=='supplemental_still' for r in selected),max_selected_from_one_video=max(videos.values(),default=0),video_distribution=dict(videos)),
        quality=dict(best_min=min(scores) if scores else None,best_median=statistics.median(scores) if scores else None,best_max=max(scores) if scores else None,global_rank_min=min(ranks) if ranks else None,global_rank_max=max(ranks) if ranks else None),
        identity_diagnostic_only=True,step9_decision_filter='STEP8_ACCEPT',session_id=session)
