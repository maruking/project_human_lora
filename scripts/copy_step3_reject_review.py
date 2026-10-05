"""Copy existing successful STEP3 Reject results for human review; no inference."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from common.config import load_config, resolve_config_path
from common.step3_audit import validate_input
from common.step3_review import require_source, review_roots


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(config, dry_run=False):
    reports = review_roots(config)[0].parent
    raw = resolve_config_path(config['paths']['raw_frames_dir'], config).resolve()
    require_source(raw)
    manifests = resolve_config_path(config['paths']['manifests_dir'], config)
    report, summary_path = reports/'step3_dataset_report.csv', reports/'step3_summary.json'
    content, summary_content = report.read_bytes(), summary_path.read_bytes()
    csv_hash = hashlib.sha256(content).hexdigest()
    summary_hash = hashlib.sha256(summary_content).hexdigest()
    summary = json.loads(summary_content.decode('utf-8-sig'))
    if summary['status'] != 'PASS' or summary['partial'] or summary['step3_csv_sha256'] != csv_hash:
        raise ValueError('STEP3 must be a complete successful report with matching CSV hash')
    _, generation, step2_hash = validate_input(reports/'step2_dataset_report.csv', raw, manifests)
    if generation != summary['input_generation'] or step2_hash != summary['step2_csv_sha256']:
        raise ValueError('Current STEP1/2 and STEP3 lineage differ')
    rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
    if len(rows) != generation['frame_count'] or len({r['filename'] for r in rows}) != len(rows):
        raise ValueError('STEP3 row count or unique identities differ from formal generation')
    with (reports/'step2_dataset_report.csv').open(encoding='utf-8-sig',newline='') as f:
        step2_names = {r['filename'] for r in csv.DictReader(f)}
    if {r['filename'] for r in rows} != step2_names:
        raise ValueError('STEP3 identities differ from current formal STEP2 universe')
    counts = Counter(r['diagnostic_state'] for r in rows)
    if set(counts) - {'PASS','BORDERLINE','REJECT'}:
        raise ValueError('Unexpected review state')
    if any(counts[k] != summary['review_counts'][k] for k in ('PASS','BORDERLINE','REJECT')):
        raise ValueError('STEP3 review counts differ from summary')
    if any((r['face_eligible'] == 'false') != (r['diagnostic_state'] == 'REJECT') for r in rows):
        raise ValueError('Eligibility and Reject review state disagree')
    copies = []
    for row in rows:
        if row['diagnostic_state'] != 'REJECT':
            continue
        name = row['filename']
        relative = Path(name)
        source = (raw/relative).resolve()
        if '\\' in name or relative.is_absolute() or any(p in ('','.','..') for p in name.split('/')):
            raise ValueError('Unsafe relative source identity')
        require_source(source)
        if not source.is_relative_to(raw) or not source.is_file():
            raise ValueError('Reject source missing or outside current raw input')
        stat = source.stat()
        copies.append((source, relative, stat.st_size, stat.st_mtime_ns))
    total_bytes = sum(size for _,_,size,_ in copies)
    target = reports/'reject'
    receipt_path = reports/'step3_reject_review_receipt.json'
    print(f'STEP3 rows={len(rows)}; review={dict(counts)}; Reject copies={len(copies)}; bytes={total_bytes}; {target}', flush=True)
    if dry_run:
        return
    if target.exists() or target.is_symlink():
        # No deletion/overwrite of an existing review folder by this copy utility.
        raise FileExistsError(f'Reject review folder already exists; preserved unchanged: {target}')
    if shutil.disk_usage(reports).free < total_bytes:
        raise OSError('Insufficient free space for Reject review copies')
    stage = Path(tempfile.mkdtemp(prefix='.step3-review-stage-reject-', dir=reports))
    try:
        for i,(source, relative, size, mtime) in enumerate(copies,1):
            destination = stage/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
            after = source.stat()
            if after.st_size != size or after.st_mtime_ns != mtime or destination.stat().st_size != size:
                raise ValueError('Source changed or incomplete review copy')
            if i % 100 == 0 or i == len(copies):
                print(f'Copied {i}/{len(copies)}',flush=True)
        if digest(report) != csv_hash or digest(summary_path) != summary_hash:
            raise ValueError('STEP3 evidence changed while copying; not published')
        if target.exists() or target.is_symlink():
            raise FileExistsError('Reject destination appeared while copying; preserved unchanged')
        os.rename(stage,target)
        receipt = dict(status='REVIEW_COPIES_ONLY',copied_count=len(copies),copied_bytes=total_bytes,
                       dataset_generation_id=generation['sha256'],step3_csv_sha256=csv_hash,
                       source_root=str(raw),destination=str(target),selection_state_changed=False,
                       inference_executed=False,pipeline_input=False)
        receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'Published {len(copies)} Reject copies. Official reports and sources unchanged.',flush=True)
    finally:
        # Only this utility's owned staging; never source/other existing reports.
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--dry-run',action='store_true')
    args = parser.parse_args()
    run(load_config(args.config),args.dry_run)
