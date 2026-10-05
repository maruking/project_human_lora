"""Disposable STEP3 review copies; never evidence or pipeline input."""
from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import tempfile


REGISTERED_ROOTS = set()


def review_roots(config):
    from common.config import get_section, resolve_config_path
    reports = resolve_config_path(get_section(config, 'paths').get('reports_dir', 'output/reports'), config)
    roots = tuple((reports / name).resolve() for name in ('passed', 'borderline', 'reject'))
    REGISTERED_ROOTS.update(roots)
    REGISTERED_ROOTS.add((reports/'step3_best_review').resolve())
    folder_review=get_section(config,'step8_folder_review')
    if folder_review.get('review_root'):
        REGISTERED_ROOTS.add(resolve_config_path(folder_review['review_root'],config).resolve())
    return roots


def is_review_copy(path, roots=()):
    path = Path(path).resolve()
    # Conventional layout also protects portable test/projects and generic scans.
    conventional = any((p.name.lower() in ('passed', 'borderline', 'reject') and
                        p.parent.name.lower() == 'reports') or
                       p.name.lower() == 'step3_best_review' or
                       p.name.lower() == 'step8_review' or
                       p.name.startswith(('.step8_stage_','step8_folder_review_v2_')) or
                       p.name.startswith('.step3-review-stage-') for p in (path, *path.parents))
    return conventional or any(path == root or path.is_relative_to(root) for root in (*roots, *REGISTERED_ROOTS))


def require_source(path, roots=()):
    if is_review_copy(path, roots):
        raise ValueError('Temporary STEP3 review copies cannot be pipeline inputs')
    return path


@contextmanager
def successful_review(rows, paths, reports, source_root):
    """Stage both groups, swap with rollback around official report publication.

    Only called for a complete successful analysis. Owned staging/backup files
    are removed on exit; pre-existing data outside the two destinations is untouched.
    Ordinary exceptions roll back both groups. Process termination/power loss is
    not a cross-directory atomic transaction; the owned stage retains recovery data.
    """
    reports, source_root = Path(reports).resolve(), Path(source_root).resolve()
    targets = [reports / name for name in ('passed', 'borderline')]
    if any(t == source_root or t.is_relative_to(source_root) or
           source_root.is_relative_to(t) for t in targets):
        raise ValueError('Review outputs overlap source input')
    for t in targets:
        if t.is_symlink() or (t.exists() and (not t.is_dir() or t.resolve() != t)):
            raise ValueError('Unsafe review directory (link/junction/file)')
    reports.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.step3-review-stage-', dir=reports))
    moved, installed = [], []
    cleanup = True
    try:
        for t in targets:
            (stage / ('new-' + t.name)).mkdir()
        seen = set()
        for i, row in enumerate(rows):
            state = row.get('diagnostic_state')
            if state not in ('PASS', 'BORDERLINE'):
                continue
            if row.get('face_eligible') != 'true' or i not in paths:
                raise ValueError('Review row lacks eligible current-generation source')
            source, relative = paths[i]
            source, relative = Path(source).resolve(), Path(relative)
            if (relative.is_absolute() or '..' in relative.parts or relative in seen or
                not source.is_relative_to(source_root) or source != (source_root / relative).resolve()):
                raise ValueError('Unsafe/duplicate review source identity')
            require_source(source)
            seen.add(relative)
            dest = stage / ('new-passed' if state == 'PASS' else 'new-borderline') / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        for t in targets:
            if t.exists():
                os.replace(t, stage / ('old-' + t.name))
                moved.append(t)
            os.replace(stage / ('new-' + t.name), t)
            installed.append(t)
        yield
    except BaseException:
        cleanup = False
        for t in reversed(installed):
            shutil.rmtree(t)
        for t in reversed(moved):
            os.replace(stage / ('old-' + t.name), t)
        cleanup = True
        raise
    finally:
        if cleanup:
            shutil.rmtree(stage)
