"""Regenerate STEP3 human reports from authoritative CSV, without inference/image IO."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from common.config import load_for_cli, resolve_config_path, resolve_project_path, get_section
from common.step3_audit import build_artifacts, publish


def rebuild(report, summary_path, step2):
    summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
    data=report.read_bytes()
    if summary['status']!='PASS' or summary['partial'] or hashlib.sha256(data).hexdigest()!=summary['step3_csv_sha256']:
        raise ValueError('Authoritative STEP3 CSV/summary mismatch')
    with report.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    with step2.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; source=list(reader)
    if hashlib.sha256(step2.read_bytes()).hexdigest()!=summary['step2_csv_sha256'] or len(source)!=len(rows):
        raise ValueError('Source STEP2 CSV differs')
    indexed={r['filename']:r for r in source}
    if len(indexed)!=len(source) or {r['filename'] for r in rows}!=set(indexed):
        raise ValueError('Frame identities differ')
    for r in rows:
        if any(r[k]!=indexed[r['filename']][k] for k in fields):
            raise ValueError('STEP2 values differ in STEP3')
    return build_artifacts(rows,fields,summary['input_generation'],summary['step2_csv_sha256'],summary['arguments'])


def main():
    config=load_for_cli(); settings=get_section(config,'step3_face_gate')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,default=resolve_config_path(settings.get('output','@reports/step3_dataset_report.csv'),config))
    parser.add_argument('--config',type=Path)
    args=parser.parse_args(); report=args.report.resolve()
    step2=resolve_config_path(settings.get('report','@reports/step2_dataset_report.csv'),config)
    artifacts=rebuild(report,report.with_name('step3_summary.json'),step2)
    publish(report,artifacts)
    print('STEP3 reports regenerated from CSV; no images decoded')
    return 0


if __name__=='__main__': raise SystemExit(main())
