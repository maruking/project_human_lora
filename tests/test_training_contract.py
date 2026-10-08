import copy
import io
from contextlib import redirect_stdout
import unittest
from common.config import load_config, validate_config, ConfigError, print_training_target


class TrainingContractTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config('config/config.example.yaml')

    def test_current_contract_and_display(self):
        training = self.config['training']
        self.assertEqual(training['base_model']['name_or_path'], 'black-forest-labs/FLUX.2-klein-base-9B')
        self.assertEqual(training['base_model']['arch'], 'flux2_klein_9b')
        self.assertEqual(training['dataset']['caption_format'], 'natural_language')
        with redirect_stdout(io.StringIO()) as log: print_training_target(self.config)
        for label in ('TRAINING TARGET', 'Base Model:', 'Adapter:', 'Trigger:', 'Dataset:', 'Caption Version:'):
            self.assertIn(label, log.getvalue())
        self.assertNotIn('FLUX.1', log.getvalue())

    def test_trigger_mismatch_stops_validation(self):
        self.config['training']['trigger_word'] = 'different_token'
        with self.assertRaisesRegex(ConfigError, 'project.trigger_word must equal training.trigger_word'):
            validate_config(self.config)

    def test_missing_contract_no_legacy_step10_default(self):
        del self.config['training']
        validate_config(self.config)  # Partial legacy configs remain readable for other steps.
        with self.assertRaisesRegex(ConfigError, 'explicit training section'):
            print_training_target(self.config)

    def test_invalid_rank_rejected(self):
        self.config['training']['lora']['rank'] = 0
        with self.assertRaises(ConfigError): validate_config(self.config)

    def test_incomplete_training_contract_rejected(self):
        del self.config['training']['dataset']['caption_version']
        with self.assertRaises(ConfigError): validate_config(self.config)


if __name__ == '__main__': unittest.main()
