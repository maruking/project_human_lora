"""Separate VLM caption export. Never modify the baseline or selected sources."""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

FIELDS = ('shot', 'pose', 'clothing', 'hair_style', 'background', 'lighting', 'expression')
PROMPT = '''Inspect this image directly and describe only the visible woman's VARIABLE attributes.
Return ONLY one JSON object with these keys: shot, pose, clothing, hair_style,
background, lighting, expression. Each value is a short English string or null.
Use short self-contained phrases rather than disconnected words. shot describes
the visible framing extent, not the viewing direction. pose describes viewing
direction/body posture when clear. Clothing should combine garment type, color,
and clearly visible pattern/graphic/text-print in one natural phrase. Do not
transcribe logos or brand names. Do not invent a plain pattern when uncertain.
hair_style should be a phrase including the word hair and visible style/length.
Describe clothing type, color, and pattern ONLY when clearly visible. Describe
hairstyle, not facial identity. Omit uncertain/ambiguous/hidden attributes with null;
never guess. Do not choose from a fixed candidate list. Describe left/right profile
only if visually certain; otherwise omit the direction. Do not infer age, ethnicity,
identity, personality, location, material or brand. Do not describe intrinsic face
features (eye shape/color, nose, lips, face shape, skin, bone structure). No beauty
judgments, quality adjectives, young girl, trigger token, or extra commentary.
Expression may describe a smile or neutral expression without facial anatomy.'''
FORBIDDEN = re.compile(r'\b(character|young|girl|child|teen\w*|eyes?|eyebrows?|nose|lips?|face|facial|skin|cheeks?|jaw\w*|chin|forehead|freckles|ethnic\w*)\b', re.I)
UNCERTAIN = re.compile(r'\b(unknown|unclear|uncertain|possibly|probably|maybe|appears|seems|could|might|unsure|not visible|n/a)\b', re.I)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))


def verify_model(root):
    required = ('config.json', 'generation_config.json', 'chat_template.json',
                'tokenizer_config.json', 'tokenizer.json', 'preprocessor_config.json',
                'video_preprocessor_config.json', 'merges.txt', 'vocab.json',
                'model.safetensors.index.json')
    missing = [name for name in required if not (root / name).is_file()]
    if missing: raise ValueError('Missing model files: ' + ', '.join(missing))
    cfg = json.loads((root / 'config.json').read_text(encoding='utf-8'))
    if cfg.get('model_type') != 'qwen3_vl': raise ValueError('Expected approved Qwen3-VL model; no fallback')
    index = json.loads((root / 'model.safetensors.index.json').read_text())
    mapping = index['weight_map']; seen = {}; total = 0
    for filename in sorted(set(mapping.values())):
        if Path(filename).name != filename: raise ValueError('Unsafe shard filename')
        path = root / filename
        with path.open('rb') as f:
            header_size = struct.unpack('<Q', f.read(8))[0]
            if header_size > 100_000_000: raise ValueError('Invalid safetensors header')
            header = json.loads(f.read(header_size))
        payload_size = path.stat().st_size - 8 - header_size
        offsets = []
        for name, tensor in header.items():
            if name == '__metadata__': continue
            if name in seen or mapping.get(name) != filename: raise ValueError('Shard/index tensor mismatch: ' + name)
            start, end = tensor['data_offsets']
            if start < 0 or end < start or end > payload_size: raise ValueError('Incomplete shard: ' + filename)
            seen[name] = filename; total += end - start; offsets.append((start, end))
        offsets.sort()
        if not offsets or offsets[0][0] != 0 or offsets[-1][1] != payload_size:
            raise ValueError('Shard payload length mismatch: ' + filename)
        if any(a[1] != b[0] for a, b in zip(offsets, offsets[1:])):
            raise ValueError('Shard payload gap/overlap: ' + filename)
    if seen != mapping or total != index['metadata']['total_size']:
        raise ValueError('Model tensor universe/size differs from index')
    return {'shards': len(set(mapping.values())), 'tensors': len(seen), 'tensor_bytes': total,
            'index_sha256': digest(root / 'model.safetensors.index.json')}


def natural_caption(attributes, trigger):
    """Grammar normalization only; never introduce an unobserved image attribute."""
    shot = attributes.get('shot', '')
    aliases = {'medium': 'medium shot', 'medium shot': 'medium shot',
        'upper body': 'upper-body shot', 'upper-body': 'upper-body shot',
        'full body': 'full-body shot', 'full-body': 'full-body shot',
        'close up': 'close-up shot', 'close-up': 'close-up shot',
        'closeup': 'close-up shot', 'wide': 'wide shot',
        'head and shoulders': 'head-and-shoulders shot',
        'head-and-shoulders': 'head-and-shoulders shot'}
    shot = aliases.get(shot.lower(), shot)
    pose = attributes.get('pose', '')
    pose = {'front-facing': 'facing forward', 'front facing': 'facing forward',
            'front view': 'facing forward', 'frontal': 'facing forward',
            'facing front': 'facing forward'}.get(pose.lower(), pose)
    if re.match(r'^(sitting|standing|walking|lying|seated|leaning|facing|looking|turned)\b', pose, re.I):
        sentence = 'A woman is ' + pose
    elif pose:
        pose = re.sub(r'\bside view\b', 'profile', pose, flags=re.I)
        sentence = 'A woman is shown ' + (pose if re.match(r'^(in|from|with|at)\b', pose, re.I) else 'in ' + pose)
    else:
        sentence = 'A woman is shown'
    if shot: sentence += ' in a ' + re.sub(r'^(?:a|an)\s+', '', shot, flags=re.I)
    clothing = attributes.get('clothing', '')
    if clothing:
        clothing = re.sub(r'^(?:wearing|dressed in)\s+', '', clothing, flags=re.I)
        article = '' if re.match(r'^(a|an|the|some|her)\b', clothing, re.I) else 'a '
        if re.search(r'\b(pants|jeans|shorts|trousers|clothes|clothing)\b', clothing, re.I): article = ''
        sentence += ', wearing ' + article + clothing
    extras = []
    if attributes.get('hair_style'): extras.append(attributes['hair_style'])
    if attributes.get('expression'):
        expression = attributes['expression']
        if 'expression' not in expression.lower() and not re.match(r'^(?:a |an )?smil', expression, re.I): expression += ' expression'
        extras.append(('' if expression.lower().startswith(('a ', 'an ')) else 'a ') + expression)
    if extras: sentence += ', with ' + ' and '.join(extras)
    sentence = trigger + '. ' + sentence.rstrip('. ') + '.'
    background = attributes.get('background', '')
    lighting = attributes.get('lighting', '')
    if background:
        if re.match(r'^(indoors?|outdoors?)\b', background, re.I):
            context = 'The setting is ' + re.sub(r'^indoor\b', 'indoors', re.sub(r'^outdoor\b', 'outdoors', background, flags=re.I), flags=re.I)
        else: context = 'The background is ' + background
        if lighting: context += ', with ' + lighting + ('' if re.search(r'\b(light|lighting|sunlight|daylight)\b', lighting, re.I) else ' lighting')
        sentence += ' ' + context + '.'
    elif lighting: sentence += ' The lighting is ' + lighting + '.'
    return sentence


def finalize(raw, trigger):
    text = raw.strip()
    if text.startswith('```'): text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
    data = json.loads(text)
    if not isinstance(data, dict) or set(data) != set(FIELDS): raise ValueError('VLM must return exactly the seven attribute keys')
    accepted = {}; omitted = {}
    for key in FIELDS:
        value = data[key]
        if value is None: continue
        if not isinstance(value, str): raise ValueError('Non-string VLM attribute: ' + key)
        value = ' '.join(value.split()).strip(' ,.;')
        if not value: continue
        if trigger.lower() in value.lower() or FORBIDDEN.search(value):
            omitted[key] = 'PROHIBITED_CONTENT'; continue
        if UNCERTAIN.search(value): omitted[key] = 'UNCERTAIN_CONTENT'; continue
        if len(value) > 250: raise ValueError('Overlong VLM attribute: ' + key)
        if key == 'shot' and not re.search(r'\b(shot|medium|close|closeup|upper|full|wide|portrait|shoulders)\b', value, re.I):
            omitted[key] = 'NOT_A_CLEAR_FRAMING_ATTRIBUTE'; continue
        if value.lower() not in {v.lower() for v in accepted.values()}: accepted[key] = value
    caption = natural_caption(accepted, trigger)
    if caption.count(trigger) != 1 or FORBIDDEN.search(caption): raise ValueError('Invalid final caption')
    return caption, data, omitted


def worker(job_path):
    # Separate GPU interpreter; main orchestration uses the existing config runtime.
    import torch
    from PIL import Image
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    job = json.loads(Path(job_path).read_text(encoding='utf-8'))
    if not torch.cuda.is_available(): raise ValueError('CUDA unavailable; no fallback')
    processor = AutoProcessor.from_pretrained(job['model_dir'], local_files_only=True,
        min_pixels=256 * 32 * 32, max_pixels=job['max_pixels'])
    model = Qwen3VLForConditionalGeneration.from_pretrained(job['model_dir'],
        local_files_only=True, dtype=torch.bfloat16, device_map='cuda:0', attn_implementation='sdpa')
    model.eval()
    with Path(job['raw_path']).open('x', encoding='utf-8') as out:
        for i, entry in enumerate(job['entries'], 1):
            with Image.open(entry['v1_path']) as image:
                messages = [{'role': 'user', 'content': [{'type': 'image', 'image': image.convert('RGB')},
                            {'type': 'text', 'text': PROMPT}]}]
                inputs = processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                    return_dict=True, return_tensors='pt').to(model.device)
            with torch.inference_mode():
                output = model.generate(**inputs, do_sample=False, max_new_tokens=job['max_new_tokens'])
            generated = output[0, inputs['input_ids'].shape[1]:]
            raw = processor.decode(generated, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            eos = model.generation_config.eos_token_id
            truncated = int(generated[-1]) not in ([eos] if isinstance(eos, int) else (eos or []))
            out.write(json.dumps({'frame_id': entry['frame_id'], 'raw_vlm_output': raw, 'truncated': truncated}, ensure_ascii=False) + '\n'); out.flush()
            print(f'VLM [{i}/{len(job["entries"])}] {entry["final_filename"]}', flush=True)


def main():
    from common.config import load_config, get_section, resolve_config_path, resolve_project_path, PROJECT_ROOT, print_training_target
    from common.packaging_input import load_inputs
    from step6_identity_v2 import ensure_unchanged
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--preflight-only', action='store_true')
    mode.add_argument('--smoke-test', action='store_true', help='One image only, no production export')
    mode.add_argument('--format-smoke', action='store_true', help='Format first three stored VLM results, no inference/export')
    mode.add_argument('--reformat-existing', action='store_true', help='Reformat existing V2 raw JSON without VLM rerun; archive old V2')
    args = parser.parse_args(); cfg = load_config(args.config); settings = get_section(cfg, 'step10_caption_v2')
    print_training_target(cfg)
    trigger = get_section(cfg, 'project')['trigger_word']
    if not trigger or FORBIDDEN.search(trigger): raise ValueError('Use a unique non-generic configured trigger')
    model_dir = resolve_project_path(settings['model_dir']); python = resolve_project_path(settings['python_executable'])
    if not python.is_file(): raise ValueError('Configured VLM Python interpreter not found')
    model_info = verify_model(model_dir)
    old_root = resolve_project_path(get_section(cfg, 'paths')['output_dataset_dir'])
    report = resolve_config_path(get_section(cfg, 'step10_packaging')['output_csv'], cfg)
    selected, pins = load_inputs(cfg, resolve_config_path(get_section(cfg, 'step10_packaging')['step9_report'], cfg),
        resolve_project_path(get_section(cfg, 'paths')['restored_dir']))
    baseline = rows(report); pins[str(report)] = digest(report)
    if len(baseline) != len(selected) or [r['frame_id'] for r in baseline] != [r['frame_id'] for r in selected]:
        raise ValueError('V1 audit identity/order differs from current STEP8_ACCEPT')
    if {r['final_filename'] for r in baseline} != {p.name for p in old_root.glob('*.png')}:
        raise ValueError('Baseline image inventory differs from audit')
    if {Path(r['final_filename']).stem for r in baseline} != {p.stem for p in old_root.glob('*.txt')}:
        raise ValueError('Baseline paired caption inventory mismatch')
    for entry, original in zip(baseline, selected):
        for key in ('image_sha256', 'dataset_generation_id', 'step8_review_session_id'):
            if entry[key] != original[key]: raise ValueError('Stale baseline lineage: ' + key)
        if Path(entry['final_filename']).name != entry['final_filename']: raise ValueError('Unsafe baseline filename')
        path = old_root / entry['final_filename']; entry['v1_path'] = str(path); entry['v1_image_sha256'] = digest(path)
    pins.update({str(p): digest(p) for p in old_root.iterdir() if p.is_file()})
    dest = resolve_project_path(settings['output_dir']); audit = resolve_config_path(settings['output_csv'], cfg)
    review = resolve_project_path(settings['review_html'])
    if dest == old_root or dest.is_relative_to(old_root) or old_root.is_relative_to(dest): raise ValueError('V2 must be separate from baseline')
    if audit == report or any(str(p) in pins for p in (audit, review)): raise ValueError('Output would overwrite input evidence')
    if args.preflight_only:
        print(f'PREFLIGHT PASS: {len(baseline)} selected images, {model_info}; no inference/export'); return
    stored = None
    if args.format_smoke or args.reformat_existing:
        stored = rows(audit)
        if len(stored) != len(baseline) or [r['frame_id'] for r in stored] != [r['frame_id'] for r in baseline]:
            raise ValueError('Existing V2 identity/order mismatch')
        for r, b in zip(stored, baseline):
            if any(r[k] != b[k] for k in ('final_filename', 'image_sha256', 'dataset_generation_id', 'step8_review_session_id')):
                raise ValueError('Existing V2 lineage mismatch')
            if r['v1_image_sha256'] != b['v1_image_sha256'] or digest(dest / r['final_filename']) != b['v1_image_sha256']:
                raise ValueError('Existing V2 image hash mismatch')
            if r['model_id'] != settings['model_id'] or r['model_index_sha256'] != model_info['index_sha256']:
                raise ValueError('Existing V2 model provenance differs')
        pins.update({str(p): digest(p) for p in dest.iterdir() if p.is_file()})
        pins[str(audit)] = digest(audit); pins[str(review)] = digest(review)
    if not (args.smoke_test or args.format_smoke or args.reformat_existing) and any(p.exists() for p in (dest, audit, review)):
        raise ValueError('V2 output already exists; preserve it and choose separate paths before rerun')
    stage = Path(tempfile.mkdtemp(prefix='.caption_v2_stage_', dir=PROJECT_ROOT / 'work'))
    job = dict(model_dir=str(model_dir), entries=baseline[:3] if args.format_smoke else baseline[:1] if args.smoke_test else baseline,
               raw_path=str(stage / 'raw_vlm.jsonl'), max_pixels=settings['max_pixels'], max_new_tokens=settings['max_new_tokens'])
    job_path = stage / 'job.json'; job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
    (stage / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
    if stored is None:
        subprocess.run([str(python), '-u', str(Path(__file__).resolve()), '--worker', str(job_path)], check=True)
        raw_rows = [json.loads(line) for line in Path(job['raw_path']).read_text(encoding='utf-8').splitlines()]
    else:
        raw_rows = [dict(frame_id=r['frame_id'], raw_vlm_output=r['raw_vlm_output'], truncated=r['truncated'].lower() == 'true') for r in stored[:len(job['entries'])]]
    if len(raw_rows) != len(job['entries']): raise ValueError('Incomplete VLM results; stage preserved')
    results = []
    for entry, raw in zip(job['entries'], raw_rows):
        if raw['frame_id'] != entry['frame_id'] or raw['truncated']: raise ValueError('Mismatched/truncated VLM result; STOP')
        caption, attributes, omitted = finalize(raw['raw_vlm_output'], trigger)
        results.append(dict(entry, **raw, final_caption=caption, vlm_attributes=json.dumps(attributes, ensure_ascii=False),
            omitted_attributes=json.dumps(omitted, ensure_ascii=False), model_id=settings['model_id'], model_dir=str(model_dir),
            model_index_sha256=model_info['index_sha256'], prompt_sha256=hashlib.sha256(PROMPT.encode()).hexdigest(),
            generation_settings=json.dumps({'do_sample': False, 'dtype': 'bf16', 'max_pixels': job['max_pixels'], 'max_new_tokens': job['max_new_tokens']}),
            review_state='PENDING_HUMAN_REVIEW'))
        results[-1]['caption_format'] = 'natural_sentence_v1'
        if stored is not None:
            for key in ('model_id', 'model_dir', 'model_index_sha256', 'prompt_sha256', 'generation_settings', 'vlm_attributes'):
                results[-1][key] = stored[len(results)-1][key]
    ensure_unchanged(pins)
    if args.smoke_test or args.format_smoke:
        path = stage / 'smoke_result.json'; path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        cards = ''.join(f'<article><h2>{html.escape(r["frame_id"])}</h2><img src="{Path(r["v1_path"]).as_uri()}"><p>{html.escape(r["final_caption"])}</p><pre>{html.escape(r["raw_vlm_output"])}</pre></article>' for r in results)
        preview = stage / 'smoke_review.html'
        preview.write_text('<!doctype html><meta charset="utf-8"><style>body{font:18px sans-serif;margin:24px}img{max-height:650px;max-width:100%}pre{white-space:pre-wrap}article{margin-bottom:40px}</style><h1>Caption V2 natural format — smoke only</h1>' + cards, encoding='utf-8')
        print(f'SMOKE PASS: {len(results)} images, production export:NO. Result: {path}; Review: {preview}'); return
    staged_dataset = stage / 'dataset'; staged_dataset.mkdir()
    for r in results:
        output = staged_dataset / r['final_filename']; shutil.copyfile(r['v1_path'], output)
        if digest(output) != r['v1_image_sha256']: raise ValueError('V1/V2 image SHA256 mismatch')
        output.with_suffix('.txt').write_text(r['final_caption'], encoding='utf-8')
    staged_csv = stage / 'audit.csv'
    with staged_csv.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    cards = []
    for i, r in enumerate(results, 1):
        link = (dest / r['final_filename']).as_uri()
        cards.append(f'<article><h2>{i:02d} · {html.escape(r["frame_id"])}</h2><a href="{link}"><img src="{link}" loading="lazy"></a>'
            f'<p><strong>V2:</strong> {html.escape(r["final_caption"])}</p><p><strong>V1:</strong> {html.escape(r["flux_caption"])}</p>'
            f'<details><summary>VLM raw / omitted attributes</summary><pre>{html.escape(r["raw_vlm_output"])}</pre>'
            f'<pre>{html.escape(r["omitted_attributes"])}</pre></details></article>')
    staged_html = stage / 'review.html'
    staged_html.write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>STEP10 Caption V2 Review</title>'
        '<style>body{font:16px sans-serif;margin:24px;background:#eef2f6}article{background:white;padding:20px;margin:20px 0;border-radius:12px}img{max-width:100%;max-height:800px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
        f'<h1>STEP10 Caption V2 · {len(results)} images</h1><p>Qwen3-VLによる仮caption。服装・髪型・pose等を目視確認してください。Human Review完了まで再学習しません。画像SHA256はv1と全件一致。</p>' + ''.join(cards) + '</html>', encoding='utf-8')
    ensure_unchanged(pins)
    for p in (dest.parent, audit.parent, review.parent): p.mkdir(parents=True, exist_ok=True)
    # Validated staging publication. Three paths are not a single atomic transaction.
    if args.reformat_existing:
        backup = Path(tempfile.mkdtemp(prefix='caption_v2_before_natural_', dir=PROJECT_ROOT / 'output' / 'bkup'))
        if not dest.is_relative_to(PROJECT_ROOT / 'output'): raise ValueError('Refuse to archive export outside project output')
        dest.rename(backup / 'dataset_flux_caption_v2'); audit.rename(backup / audit.name); review.rename(backup / review.name)
        print(f'Previous V2 preserved: {backup}')
    elif any(p.exists() for p in (dest, audit, review)): raise ValueError('Output appeared during inference; STOP')
    staged_dataset.rename(dest); os.replace(staged_csv, audit); os.replace(staged_html, review)
    print(f'COMPLETE: {len(results)} images/captions; SHA256 match:{len(results)}; trigger once; no character/empty captions. Review: {review}')


if __name__ == '__main__':
    try:
        if len(sys.argv) == 3 and sys.argv[1] == '--worker': worker(sys.argv[2])
        else: main()
    except Exception as exc:
        print(f'[ERROR] Caption V2 STOP: {exc}', file=sys.stderr); sys.exit(1)
