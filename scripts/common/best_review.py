"""Durable review history; source images are immutable and copies disposable."""
import json
import shutil
from pathlib import Path
from common.best_ranking import VERSION, choose_round
from common.video_manifest import sha256_file, write_json_atomic
from common.step3_review import require_source


HISTORY_NAME = 'step3_best_review_history_by_version.json'
LEGACY_NAME = 'step3_best_review_history.json'


def read_history(path):
    """Read versioned history; import legacy v1 in memory without rewriting it.

    rounds/records are active-version views, not serialized duplicate histories.
    The first explicit review publication persists the version-separated store.
    """
    path=Path(path)
    if path.exists():
        history=json.loads(path.read_text(encoding='utf-8-sig'))
        if history.get('version')!=2 or 'review_history' not in history:
            raise ValueError('Legacy history is read-only; use '+HISTORY_NAME)
    else:
        history=dict(version=2,review_history={})
        legacy=path.with_name(LEGACY_NAME)
        if legacy.exists():
            old=json.loads(legacy.read_text(encoding='utf-8-sig'))
            if old.get('version')!=1 or any(r.get('ranking_version')!='best_rank_v1' for r in old['records']):
                raise ValueError('Legacy history is not exclusively best_rank_v1; inspect before migration')
            history['review_history']['best_rank_v1']=old
            history['legacy_source']=dict(filename=LEGACY_NAME,sha256=sha256_file(legacy))
    source=history.get('legacy_source')
    if source:
        legacy=path.with_name(LEGACY_NAME)
        if not legacy.exists() or sha256_file(legacy)!=source['sha256']:
            raise ValueError('Historical v1 evidence changed or is missing; inspect before continuing')
    active=history['review_history'].setdefault(VERSION,dict(rounds=[],records=[]))
    if any(r.get('ranking_version')!=VERSION for r in active['records']):
        raise ValueError('Mixed ranking versions in active review history')
    history['rounds']=active['rounds'];history['records']=active['records']
    return history


def write_history(path,history):
    write_json_atomic(path,{k:v for k,v in history.items() if k not in ('rounds','records')})


def historical_reviews(history,row):
    """Return prior-version evidence only for the identical source/generation."""
    return [dict(ranking_version=version,review_round=r['review_round'],
                 frame_id=r['frame_id'],review_state=r['review_state'])
            for version,group in history['review_history'].items() if version!=VERSION
            for r in group['records']
            if all(r.get(k)==row.get(k) for k in ('frame_id','dataset_generation_id','image_sha256'))]


def validate_history_rows(rows,history):
    current={r['frame_id']:r for r in rows}
    for previous in history['records']:
        row=current.get(previous['frame_id'])
        if row is None or any(row.get(k)!=previous.get(k) for k in ('dataset_generation_id','image_sha256')):
            raise ValueError('Active review lineage differs from current ranking; explicit generation handling required')


def materialize(rows, source_root, review_root, history_path, round_number, settings):
    if round_number not in (1,2,3):raise ValueError('Review round must be 1, 2 or 3')
    source_root=Path(source_root).resolve();review_root=Path(review_root).resolve()
    history_path=Path(history_path).resolve()
    if review_root.is_relative_to(source_root) or source_root.is_relative_to(review_root):
        raise ValueError('Review/source directories overlap')
    if history_path.is_relative_to(review_root):raise ValueError('History must be outside disposable review folders')
    history=read_history(history_path)
    validate_history_rows(rows,history)
    if any(r.get('ranking_version')!=VERSION for r in rows):
        raise ValueError(f'New review extraction requires {VERSION}; historical rounds stay unchanged')
    previous=next((r for r in history['rounds'] if r['review_round']==round_number),None)
    if previous:
        if previous['publication_status']!='COMPLETE':
            raise ValueError('Interrupted review publication; reserved history retained. Inspect before recovery')
        return history # Never recreate deleted copies or reshow a completed round.
    if round_number>1 and not any(r['review_round']==round_number-1 and r['publication_status']=='COMPLETE' for r in history['rounds']):
        raise ValueError('Previous review round has not been published')
    target=review_root/VERSION/f'round_{round_number:02d}'
    if target.exists():raise ValueError('Unregistered review folder exists; preserve it and resolve history before retrying')
    selected,info=choose_round(rows,history['records'],settings.get('review_size',45),settings.get('max_per_video',4),settings.get('min_supplemental',10),round_number=round_number)
    # Reserve history first. A crash may leave missing copies, but can never reshow IDs.
    records=[]
    for i,row in enumerate(selected,1):
        relative=Path(row['filename'])
        source=(source_root/relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or not source.is_relative_to(source_root):
            raise ValueError('Unsafe review source path')
        require_source(source)
        if sha256_file(source)!=row['image_sha256']:raise ValueError('Review source checksum changed')
        records.append(dict(row,review_round=round_number,review_round_rank=i,shown_to_maru=True,
                            review_state='PENDING',review_reason='',copy_status='RESERVED',
                            copy_relative=relative.as_posix()))
    history['records'].extend(records)
    history['rounds'].append(dict(review_round=round_number,**info,publication_status='RESERVED'))
    history_path.parent.mkdir(parents=True,exist_ok=True)
    write_history(history_path,history)
    (target/'candidates').mkdir(parents=True)
    (target/'review_reject').mkdir()
    for record in records:
        relative=Path(record['copy_relative']);source=source_root/relative
        dest=target/'candidates'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
        if sha256_file(dest)!=record['image_sha256']:raise ValueError('Review copy checksum differs')
        record['copy_status']='PRESENT'
    history['rounds'][-1]['publication_status']='COMPLETE'
    write_history(history_path,history)
    return history


def feedback(review_root,history_path):
    history=read_history(history_path);rejected=[]
    if not history['rounds']:raise ValueError(f'No {VERSION} review round; start {VERSION} Round 1 first')
    removals=[]
    for row in history['records']:
        relative=Path(row['copy_relative'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe history path')
        folder=review_root/VERSION/f"round_{row['review_round']:02d}"
        candidates=folder/'candidates'/relative;reject=folder/'review_reject'/relative
        existing=[p for p in (candidates,reject) if p.exists()]
        for p in existing:
            if not p.resolve().is_relative_to(review_root.resolve()):raise ValueError('Review copy escapes review root')
            if sha256_file(p)!=row['image_sha256']:raise ValueError('Review feedback image checksum changed')
        row['copy_status']='PRESENT' if existing else 'MISSING'
        if reject.exists():row['review_state']='REVIEW_REJECT'
        # Absence, deletion or staying in candidates never implies acceptance.
        if row['review_state']=='REVIEW_REJECT':
            # Reconcile disposable ACTIVE-version copies only. Both copies were
            # hash-checked above. If a saved Reject was moved back to candidates,
            # restore its visible Reject location without changing the decision.
            if not reject.exists() and candidates.exists():
                reject.parent.mkdir(parents=True,exist_ok=True)
                candidates.replace(reject)
            elif reject.exists() and candidates.exists():
                removals.append(candidates)
            out=dict(row)
            contributions=sorted(((k,float(v)) for k,v in row.items() if k.startswith('contribution_')),key=lambda p:-p[1])
            deductions=sorted(((k,float(v)) for k,v in row.items() if k.startswith('deduction_')),key=lambda p:-p[1])
            out['why_ranked_high']=';'.join(f'{k}={v:.4f}' for k,v in contributions[:3])
            out['potential_ranking_failure']='Hypothesis only: inspect '+ ';'.join(f'{k}={v:.4f}' for k,v in deductions[:3])+'; relative metrics may miss visible defects'
            rejected.append(out)
    write_history(history_path,history)
    # Persist the existing rejection first. A crash leaves a harmless duplicate
    # that the next feedback reconciles, never a lost Human decision/source image.
    for duplicate in removals:
        duplicate.unlink()
    return history,rejected
