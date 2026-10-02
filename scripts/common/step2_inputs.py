"""Explicit supplemental still input, separate from the formal STEP1 generation."""
import hashlib
import json
from pathlib import Path
from common.metric_generation import preflight
from common.metric_report import image_order
from common.video_manifest import sha256_file


class FormalSource:
    def __init__(self, root, supplemental):
        self.root = Path(root).resolve()
        self.supplemental = Path(supplemental).resolve()
        if self.root == self.supplemental or not self.supplemental.is_relative_to(self.root):
            raise ValueError('Supplemental directory must be a distinct subtree inside input')

    def __fspath__(self): return str(self.root)
    def __truediv__(self, name): return self.root/name
    def rglob(self, pattern):
        return (p for p in self.root.rglob(pattern) if not p.resolve().is_relative_to(self.supplemental))


def preflight_inputs(source, manifests, supplemental=None):
    view = FormalSource(source, supplemental) if supplemental is not None else source
    formal = preflight(view, manifests)
    if supplemental is None:
        return formal, [], None
    if not supplemental.is_dir():
        raise ValueError(f'Declared supplemental directory missing: {supplemental}')
    files = sorted((p for p in supplemental.rglob('*') if p.is_file() and
                    p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'}),key=lambda p:image_order(p,source))
    if not files:
        raise ValueError('Declared supplemental directory has no supported images')
    inventory = {}
    for p in files:
        if not p.resolve().is_relative_to(supplemental.resolve()):
            raise ValueError('Supplemental image escapes declared subtree')
        inventory[p.relative_to(source).as_posix()] = sha256_file(p)
    generation = dict(image_count=len(files), files=inventory,
                      sha256=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                      input_kind='SUPPLEMENTAL_STILL', directory=str(supplemental))
    return formal, files, generation
