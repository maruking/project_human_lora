"""Lightweight configuration and parser tests; no AI imports or downloads."""
import argparse
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common.config import (ConfigError, load_config, validate_config, get_section,
                           configure_parser, configure_constants, resolve_project_path,
                           resolve_config_path)

MODULES = ['extract_frames', 'score_blur', 'face_quality_gate', 'classify_face_pose',
           'face_deduplication', 'evaluate_identity', 'score_lora_candidates',
           'prepare_human_review', 'selective_restoration', 'package_flux_dataset']
SECTIONS = ['step1_extract', 'step2_blur', 'step3_face_gate', 'step4_pose', 'step5_dedup',
            'step6_identity', 'step7_selection', 'step8_review', 'step9_restoration', 'step10_packaging']


def script_parser(module, config):
    """Execute the real argument declarations without importing inference modules."""
    tree = ast.parse((ROOT / 'scripts' / (module + '.py')).read_text(encoding='utf-8'))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    nodes = []
    started = False
    namespace = dict(argparse=argparse, Path=Path, configure_parser=configure_parser,
                     get_section=get_section, config=config)
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try: namespace[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError): pass
    for node in ast.walk(main):
        if isinstance(node, ast.Name) and node.id.startswith('default_'):
            namespace[node.id] = ROOT / 'internal-fallback' / node.id
    for node in main.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'parser':
            started = True
        if started:
            if isinstance(node, ast.Assign) and node.targets[0].id == 'args': break
            nodes.append(node)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<parser declarations>', 'exec'), namespace)
    return namespace['parser']


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / 'config/config.example.yaml')

    def test_example_schema(self):
        validate_config(self.config)

    def test_missing_local_fallback_and_local_precedence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'config').mkdir()
            for name in ('config.example.yaml', 'config.schema.json'):
                (root / 'config' / name).write_bytes((ROOT / 'config' / name).read_bytes())
            self.assertEqual(load_config(project_root=root), self.config)
            (root / 'config/config.yaml').write_text('step7_selection:\n  candidate_pool_size: 11\n', encoding='utf-8')
            local = load_config(project_root=root)
            self.assertEqual(local['step7_selection']['candidate_pool_size'], 11)
            self.assertNotIn('step3_face_gate', local)

    def test_invalid_yaml_and_explicit_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.yaml'
            path.write_text('step7_selection: [broken', encoding='utf-8')
            with self.assertRaisesRegex(ConfigError, 'Cannot load YAML'): load_config(path)
            with self.assertRaisesRegex(ConfigError, 'Cannot load YAML'): load_config(path.with_name('missing.yaml'))
            path.write_text('- not\n- mapping', encoding='utf-8')
            with self.assertRaisesRegex(ConfigError, 'mapping'): load_config(path)

    def test_invalid_values(self):
        for section, key, value in [('step7_selection', 'candidate_pool_size', 0),
                                    ('step6_identity', 'device', 'gpu'),
                                    ('step9_restoration', 'fidelity_weight', 1.2),
                                    ('step3_face_gate', 'skip_beauty_filter', 'false'),
                                    ('step1_extract', 'supported_extensions', []),
                                    ('step7_selection', 'shot_min', {'CLOSE_UP': 10})]:
            with self.subTest(key=key):
                config = copy.deepcopy(self.config)
                config[section][key] = value
                with self.assertRaisesRegex(ConfigError, key): validate_config(config)

    def test_paths_and_unicode(self):
        self.assertEqual(resolve_project_path('work\\日本語'), ROOT / 'work/日本語')
        self.assertEqual(resolve_project_path(ROOT), ROOT)
        for value in ('../outside', 'C:relative'):
            with self.assertRaises(ConfigError): resolve_project_path(value)
        self.assertEqual(resolve_config_path('@reports/a.csv', self.config), ROOT / 'output/reports/a.csv')
        with self.assertRaises(ConfigError): resolve_config_path('@reports/../../escape', self.config)

    def test_every_real_cli_default_and_override(self):
        frozen = json.loads((ROOT / 'tests/pre_ssot_defaults.json').read_text())
        for module, section in zip(MODULES, SECTIONS):
            with self.subTest(module=module):
                parser = script_parser(module, self.config)
                args = parser.parse_args([])
                for key, value in frozen[section]['cli'].items():
                    if section == 'step1_extract' and key in ('num_frames', 'trim_start', 'trim_end'): continue  # DEC-0009 authorized sampling revision
                    self.assertEqual(getattr(args, key), value, (module, key))
                for action in parser._actions:
                    if action.type is resolve_project_path:
                        self.assertIsInstance(getattr(args, action.dest), (Path, type(None)))
                fallback = script_parser(module, {}).parse_args([])
                for key, value in frozen[section]['cli'].items():
                    if section == 'step1_extract' and key in ('num_frames', 'trim_start', 'trim_end'): continue  # DEC-0009 authorized sampling revision
                    self.assertEqual(getattr(fallback, key), value, (module, key))
        self.assertEqual(script_parser('score_lora_candidates', self.config).parse_args(['--target-count', '10']).target_count, 10)
        self.assertFalse(script_parser('extract_frames', self.config).parse_args(['--flat']).subfolders)
        custom = copy.deepcopy(self.config)
        custom['step5_dedup']['limit'] = 99
        self.assertEqual(script_parser('face_deduplication', custom).parse_args(['--limit', '0']).limit, 0)
        custom['paths']['reports_dir'] = 'work/custom_reports'
        self.assertEqual(script_parser('score_blur', custom).parse_args([]).report, ROOT / 'work/custom_reports/step2_dataset_report.csv')
        self.assertEqual(script_parser('score_blur', custom).parse_args(['--report', 'work/override.csv']).report, ROOT / 'work/override.csv')
        custom['step7_selection']['candidate_pool_size'] = 12
        self.assertEqual(script_parser('score_lora_candidates', custom).parse_args([]).target_count, 12)
        custom['project']['subject_name'] = 'example'
        self.assertEqual(script_parser('extract_frames', custom).parse_args([]).subject_name, 'example')
        self.assertEqual(script_parser('extract_frames', custom).parse_args(['--subject-name', 'override']).subject_name, 'override')

    def test_pre_ssot_constants_preserved(self):
        frozen = json.loads((ROOT / 'tests/pre_ssot_defaults.json').read_text())
        for section, entry in frozen.items():
            namespace = copy.deepcopy(entry['constants'])
            configure_constants(namespace, self.config, section, list(namespace))
            self.assertEqual(namespace, entry['constants'], section)

    def test_model_and_restoration_defaults(self):
        self.assertEqual(self.config['step6_identity']['model_name'], 'facebook/dino-vitb16')
        self.assertEqual(self.config['step9_restoration']['restoration_face_dim_threshold'], 190.0)
        self.assertEqual(self.config['step10_packaging']['dimension_alignment'], 16)


if __name__ == '__main__':
    unittest.main()
