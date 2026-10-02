"""Stable video IDs and durable copy-based normalization (DEC-0007).

Sources are never renamed or overwritten. Persist intent before publishing copies
so a process interruption cannot change the numbering on the next run.
"""
from __future__ import annotations

from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile


MANIFEST_FIELDS = [
    "video_id", "subject_name", "index", "original_filename", "normalized_filename",
    "original_path", "normalized_path", "extension", "file_size", "sha256",
    "created_at", "normalization_status", "normalization_error",
]


class NormalizationError(ValueError):
    pass


class ManifestLocked(NormalizationError):
    pass


def validate_subject(subject: str) -> str:
    # A single portable path component; never silently sanitize an identity.
    if not subject or subject != subject.strip() or re.search(r'[<>:"/\\|?*\x00-\x1f]', subject):
        raise NormalizationError("subject_name must be a nonempty portable filename component")
    if subject in (".", "..") or subject.endswith((".", " ")):
        raise NormalizationError("subject_name cannot be '.', '..' or end in a dot/space")
    return subject


def video_id(subject: str, index: int) -> str:
    validate_subject(subject)
    if index < 1:
        raise NormalizationError("Video index must be positive")
    return f"{subject}_v{index:02d}"


def natural_key(path: Path) -> tuple:
    # A raw-name tie-breaker makes names differing only in case/zero padding stable.
    parts = re.split(r'(\d+)', path.name.casefold())
    return (tuple((1, int(p)) if p.isdigit() else (0, p) for p in parts), path.name)


def scan_videos(directory: Path, extensions: set[str]) -> tuple[list[Path], list[str]]:
    files = [p for p in directory.iterdir() if p.is_file()]
    extensions = {ext.lower() for ext in extensions}
    return (sorted((p for p in files if p.suffix.lower() in extensions), key=natural_key),
            sorted((p.name for p in files if p.suffix.lower() not in extensions), key=str.casefold))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = set(MANIFEST_FIELDS[:9]) - set(reader.fieldnames or [])
            if missing:
                raise NormalizationError(f"Manifest missing fields: {', '.join(sorted(missing))}")
            return list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise NormalizationError(f"Cannot read video manifest {path}: {exc}") from exc


def path_key(path: Path | str) -> str:
    # Casefold matches Windows path identity and makes manifests portable there.
    return str(Path(path).resolve()).casefold()


def plan_normalization(videos: list[Path], rows: list[dict], subject: str,
                       normalized_dir: Path, frames_dir: Path) -> list[dict]:
    """Read-only plan, retaining all IDs, including missing sources and gaps."""
    validate_subject(subject)
    normalized_dir = normalized_dir.resolve()
    records = []
    by_source = {}
    by_target = {}
    used_indices = set()
    for old in rows:
        row = dict(old)
        try:
            index = int(row['index'])
            identifier = video_id(subject, index)
            filename = identifier + row['extension'].lower()
            size = int(row['file_size'])
        except (KeyError, TypeError, ValueError) as exc:
            raise NormalizationError(f"Invalid manifest row: {old}") from exc
        if not re.fullmatch(r'\.[A-Za-z0-9]+', row['extension']):
            raise NormalizationError(f"Invalid manifest extension: {identifier}")
        if row['subject_name'] != subject or row['video_id'] != identifier:
            raise NormalizationError("Manifest subject/ID differs; use a separate manifest for another subject")
        if row['normalized_filename'] != filename or Path(row['normalized_path']).resolve() != normalized_dir / filename:
            raise NormalizationError(f"Manifest normalized path differs from configured directory: {identifier}")
        if index in used_indices or path_key(row['original_path']) in by_source:
            raise NormalizationError(f"Duplicate ID/source in manifest: {identifier}")
        if size < 1 or Path(row['original_path']).name != row['original_filename']:
            raise NormalizationError(f"Invalid original filename/size in manifest: {identifier}")
        row.update(index=index, file_size=size, _existing=True, _present=False)
        row['_frame_directory'] = str(frames_dir / identifier)
        records.append(row)
        used_indices.add(index)
        by_source[path_key(row['original_path'])] = row
        by_target[path_key(row['normalized_path'])] = row

    pending = []
    # Reserve already-normalized source IDs before assigning original filenames.
    naming = re.compile(rf'^{re.escape(subject)}_v([0-9]{{2,}})$', re.IGNORECASE)
    for source in sorted(videos, key=natural_key):
        known = by_source.get(path_key(source)) or by_target.get(path_key(source))
        if known:
            if known['_present']:
                raise NormalizationError(f"Both original and normalized input refer to {known['video_id']}; choose one source directory")
            known.update(_source=str(source.resolve()), _present=True)
            continue
        match = naming.fullmatch(source.stem)
        index = int(match.group(1)) if match else None
        if index is not None:
            if index < 1 or index in used_indices:
                raise NormalizationError(f"Already-normalized ID collision: {source.name}")
            used_indices.add(index)
        pending.append((source, index))

    next_index = max(used_indices, default=0)
    for source, index in pending:
        if index is None:
            next_index += 1
            index = next_index
        identifier = video_id(subject, index)
        extension = source.suffix.lower()
        normalized = normalized_dir / (identifier + extension)
        if normalized.exists() and not source.samefile(normalized):
            raise NormalizationError(f"Destination collision (never overwritten): {normalized}")
        frame_directory = frames_dir / identifier
        if frame_directory.exists() and (not frame_directory.is_dir() or
                any(p.name != '.gitkeep' for p in frame_directory.iterdir())):
            raise NormalizationError(f"Untracked frame directory (never adopted or overwritten): {frame_directory}")
        row = dict(video_id=identifier, subject_name=subject, index=index,
                   original_filename=source.name, normalized_filename=normalized.name,
                   original_path=str(source.resolve()), normalized_path=str(normalized),
                   extension=extension, file_size=source.stat().st_size,
                   sha256='', created_at=datetime.now(timezone.utc).isoformat(),
                   normalization_status='PLANNED', normalization_error='',
                   _source=str(source.resolve()), _present=True, _existing=False,
                   _frame_directory=str(frames_dir / identifier))
        records.append(row)

    for row in records:
        frame_directory = Path(row['_frame_directory'])
        if not frame_directory.resolve().is_relative_to(frames_dir.resolve()):
            raise NormalizationError(f"Frame directory escapes configured output root: {frame_directory}")
        if not row['_present']:
            row['_source'] = row['original_path']
            row['_plan'] = 'SOURCE_MISSING'
            continue
        source = Path(row['_source'])
        if source.stat().st_size < 1:
            raise NormalizationError(f"Empty video source: {source}")
        digest = sha256_file(source)
        if row.get('sha256') and digest != row['sha256']:
            raise NormalizationError(f"Source contents changed for {row['video_id']}; preserve mapping and investigate")
        if row['_existing'] and source.stat().st_size != int(row['file_size']):
            raise NormalizationError(f"Source size changed for {row['video_id']}")
        row['sha256'] = digest
        destination = Path(row['normalized_path'])
        if destination.exists():
            original = Path(row['original_path'])
            if path_key(original) != path_key(destination) and original.is_file() and original.samefile(destination):
                raise NormalizationError(f"Working video shares source data (link), expected a standalone copy: {destination}")
            if not destination.is_file() or sha256_file(destination) != digest:
                raise NormalizationError(f"Destination collision/incomplete copy: {destination}; never overwritten")
            row['_plan'] = 'ALREADY_NORMALIZED'
        else:
            row['_plan'] = 'COPY'
    return sorted(records, key=lambda r: int(r['index']))


def write_csv_atomic(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8-sig', newline='',
                                         dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def materialize_copy(row: dict) -> str:
    """Publish a complete standalone copy; no replacement of existing targets."""
    source, destination = Path(row['_source']), Path(row['normalized_path'])
    if row['_plan'] == 'SOURCE_MISSING':
        raise NormalizationError(f"Source missing for {row['video_id']}: {source}")
    if destination.exists():
        if (row['_existing'] or row['_plan'] == 'ALREADY_NORMALIZED') and sha256_file(destination) == row['sha256']:
            return 'ALREADY_NORMALIZED'
        raise NormalizationError(f"Destination collision: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with source.open('rb') as input_handle, tempfile.NamedTemporaryFile('wb', dir=destination.parent,
                     prefix=f'.{row["video_id"]}.copy-', delete=False) as handle:
            temporary = Path(handle.name)
            shutil.copyfileobj(input_handle, handle, length=1024 * 1024)
            handle.flush()
            os.fsync(handle.fileno())
        if sha256_file(temporary) != row['sha256']:
            raise NormalizationError(f"Source changed during copy: {source}")
        # This links only the private temporary copy to its final name, never the
        # original source. link() is exclusive on both Windows and POSIX.
        try:
            os.link(temporary, destination)
        except FileExistsError:
            raise NormalizationError(f"Destination appeared during copy: {destination}")
        except OSError:
            if os.name != 'nt':
                raise
            # Windows rename refuses an existing destination (unlike POSIX).
            os.rename(temporary, destination)
        return 'COPIED'
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


@contextmanager
def manifest_lock(path: Path):
    """OS advisory lock is released on process exit, including interruptions.

    A persistent lock file is normal; its mere presence never prevents a rerun.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ManifestLocked(f"Another Step1 process owns manifest lock: {path}") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
