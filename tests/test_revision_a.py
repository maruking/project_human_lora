import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from common.revision_a import FormalInventory, eye_metrics, pixel_metrics, selection_state, validate_settings
from step3_revision_a_diagnostics import supplemental_inventory


class RevisionATests(unittest.TestCase):
    def setUp(self):
        self.settings = json.loads((ROOT/'config/step3_revision_a.example.json').read_text())

    def test_closed_borderline_open_and_missing(self):
        for left, right, expected in ((0,0,'CLOSED_OR_BLINK'),(.09,.3,'CLOSED_OR_BLINK'),
                                      (.25,.3,'BORDERLINE'),(.4,.4,'OPEN'),
                                      (.35,.9,'BORDERLINE'),(None,.4,'UNKNOWN')):
            self.assertEqual(eye_metrics(left,right,self.settings)['eye_openness_state'], expected)

    def test_clipped_flat_and_informative_pixels(self):
        mask = np.ones((30,30),dtype=np.uint8)
        flat = pixel_metrics(np.full((30,30),255,dtype=np.uint8),mask,0,self.settings)
        self.assertEqual(flat['face_highlight_clip_ratio'],1)
        self.assertEqual(flat['face_exposure_state'],'OVEREXPOSED')
        self.assertEqual(flat['face_dynamic_range'],0)
        self.assertEqual(flat['face_detail_state'],'DETAIL_LOST')
        gray = np.tile(np.array([50,150]*15,dtype=np.uint8),(30,1))
        clear = pixel_metrics(gray,mask,.5,self.settings)
        self.assertEqual(clear['face_exposure_state'],'NORMAL')
        self.assertEqual(clear['face_detail_state'],'NORMAL')
        self.assertEqual(clear['face_local_contrast'],100)
        self.assertEqual(pixel_metrics(gray,mask,None,self.settings)['face_detail_state'],'UNKNOWN')
        with self.assertRaises(ValueError):
            pixel_metrics(gray,mask*0,.5,self.settings)

    def test_diagnostics_never_finalize_selection(self):
        for state in ('NORMAL','OVEREXPOSED','DETAIL_LOST','UNKNOWN'):
            diagnostics=dict(eye_openness_state='OPEN',face_exposure_state=state,face_detail_state=state)
            result=selection_state(None,diagnostics)
            self.assertEqual(result['selection_group'],'B')
            self.assertEqual(result['selection_review_status'],'UNDECIDED')
            self.assertFalse(result['reserve_use_allowed'])
            reject=selection_state(dict(human_accept='REJECT',selection_group='A',selection_group_source='HUMAN_CONFIRMED'),diagnostics)
            self.assertEqual(reject['selection_group'],'C')

    def test_confirmed_reserve_retained_and_generic_accept_not_clean(self):
        b=selection_state(dict(selection_group='B',selection_group_source='HUMAN_CONFIRMED'),{})
        self.assertEqual(b['selection_group'],'B'); self.assertTrue(b['reserve_use_allowed'])
        a=selection_state(dict(selection_group='A',selection_group_source='HUMAN_CONFIRMED'),{})
        self.assertEqual(a['selection_group'],'A')
        self.assertEqual(selection_state(dict(human_accept='ACCEPT'),{})['selection_group'],'B')

    def test_explicit_formal_inventory_exclusion_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); still=root/'stills'; still.mkdir()
            (still/'still.png').write_bytes(b'1')
            (root/'formal.png').write_bytes(b'2')
            (root/'unexpected.png').write_bytes(b'3')
            view=FormalInventory(root,still)
            names={p.relative_to(view).as_posix() for p in view.rglob('*') if p.is_file()}
            self.assertEqual(names,{'formal.png','unexpected.png'})
            self.assertEqual(view/'formal.png',root/'formal.png')
            files, hashes=supplemental_inventory(still)
            self.assertEqual(len(files),1); self.assertIn('still.png',hashes)
            with self.assertRaises(ValueError): FormalInventory(root,root)
            with self.assertRaises(ValueError): FormalInventory(root,root.parent)

    def test_missing_empty_and_invalid_settings_stop(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): supplemental_inventory(Path(d)/'missing')
            with self.assertRaises(ValueError): supplemental_inventory(Path(d))
        validate_settings(self.settings)
        for key,value in (('clip_pixel_min',256),('eye_closed_max',float('nan')),('clip_overexposed',2)):
            bad=dict(self.settings); bad[key]=value
            with self.assertRaises(ValueError): validate_settings(bad)


if __name__ == '__main__':
    unittest.main()
