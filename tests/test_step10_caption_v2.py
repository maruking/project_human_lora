import unittest
import json
import tempfile
import struct
from pathlib import Path
from step10_caption_v2 import finalize, FIELDS, verify_model


class CaptionV2Tests(unittest.TestCase):
    def raw(self, **kw):
        return json.dumps(dict.fromkeys(FIELDS, None) | kw)

    def test_free_observed_clothing_not_fixed_candidates(self):
        c, _, omitted = finalize(self.raw(clothing='blue and white striped dress', hair_style='long loose dark hair'), 'test_token')
        self.assertEqual(c, 'test_token. A woman is shown, wearing a blue and white striped dress, with long loose dark hair.')
        self.assertEqual(omitted, {})

    def test_face_intrinsic_uncertain_and_trigger_omitted(self):
        c, _, omitted = finalize(self.raw(clothing='possibly silk blouse', expression='almond eyes', hair_style='test_token hair'), 'test_token')
        self.assertEqual(c, 'test_token. A woman is shown.'); self.assertEqual(len(omitted), 3)

    def test_no_young_girl_or_character(self):
        c, _, _ = finalize(self.raw(expression='young girl', clothing='character costume'), 'test_token')
        self.assertEqual(c, 'test_token. A woman is shown.')

    def test_medium_sitting_clothing_natural_sentence_and_raw_preserved(self):
        raw = self.raw(shot='medium', pose='sitting', clothing='black one-piece swimsuit with a Mickey Mouse graphic')
        c, parsed, _ = finalize(raw, 'test_token')
        self.assertEqual(c, 'test_token. A woman is sitting in a medium shot, wearing a black one-piece swimsuit with a Mickey Mouse graphic.')
        self.assertEqual(parsed, json.loads(raw)); self.assertEqual(c.count('test_token'), 1)

    def test_unknown_framing_omitted_not_guessed(self):
        c, parsed, omitted = finalize(self.raw(shot='profile', pose='left profile'), 'test_token')
        self.assertEqual(c, 'test_token. A woman is shown in left profile.')
        self.assertEqual(parsed['shot'], 'profile'); self.assertIn('shot', omitted)

    def test_context_and_no_duplicated_article(self):
        c, _, _ = finalize(self.raw(shot='close-up', clothing='a blue dress', background='indoors', lighting='soft daylight', expression='neutral'), 'test_token')
        self.assertEqual(c, 'test_token. A woman is shown in a close-up shot, wearing a blue dress, with a neutral expression. The setting is indoors, with soft daylight.')

    def test_front_facing_and_white_background_grammar(self):
        c, _, _ = finalize(self.raw(shot='head and shoulders', pose='front-facing', background='white', lighting='even'), 'test_token')
        self.assertEqual(c, 'test_token. A woman is facing forward in a head-and-shoulders shot. The background is white, with even lighting.')

    def test_missing_keys_stop_no_fallback(self):
        with self.assertRaises(ValueError): finalize('{"caption":"a woman"}', 'test_token')

    def test_malformed_json_stop(self):
        with self.assertRaises(ValueError): finalize('not JSON', 'test_token')

    def model(self, root):
        names = ('config.json', 'generation_config.json', 'chat_template.json',
                 'tokenizer_config.json', 'tokenizer.json', 'preprocessor_config.json',
                 'video_preprocessor_config.json', 'merges.txt', 'vocab.json')
        for name in names: (root / name).write_text('{}')
        (root / 'config.json').write_text('{"model_type":"qwen3_vl"}')
        header = json.dumps({'weight': {'data_offsets': [0, 4]}}).encode()
        (root / 'shard.safetensors').write_bytes(struct.pack('<Q', len(header)) + header + b'1234')
        (root / 'model.safetensors.index.json').write_text(json.dumps({'metadata': {'total_size': 4}, 'weight_map': {'weight': 'shard.safetensors'}}))

    def test_complete_index_shard_loadable(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.model(root)
            self.assertEqual(verify_model(root)['tensors'], 1)

    def test_missing_tokenizer_stops(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.model(root); (root / 'tokenizer_config.json').unlink()
            with self.assertRaisesRegex(ValueError, 'Missing model'): verify_model(root)

    def test_truncated_shard_stops(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self.model(root); p = root / 'shard.safetensors'; p.write_bytes(p.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError, 'Incomplete shard'): verify_model(root)


if __name__ == '__main__': unittest.main()
