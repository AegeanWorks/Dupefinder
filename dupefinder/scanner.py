"""Read-only filesystem walk and duplicate grouping."""

import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from dupefinder.hashing import hash_file
from dupefinder.model import DuplicateGroup

ErrorHandler = Callable[[OSError], None]


def scan_files(roots: Sequence[Path], *, include_hidden: bool = False,
               on_error: Optional[ErrorHandler] = None) -> List[Path]:
    """Every regular, non-symlink file under `roots`, in stable order."""
    found: List[Path] = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            raise FileNotFoundError(f"path does not exist: {root}")
        if root.is_file():
            if not root.is_symlink():
                found.append(root)
            continue
        _walk(root, include_hidden, on_error or _raise, found)
    return found


def _walk(root: Path, include_hidden: bool, on_error: ErrorHandler, found: List[Path]) -> None:
    """Append regular files under one directory, skipping hidden and symlinked entries."""
    for dirpath, dirnames, filenames in os.walk(root, onerror=on_error, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames
            if (include_hidden or not name.startswith("."))
            and not (current / name).is_symlink()
        )
        for name in sorted(filenames):
            if not include_hidden and name.startswith("."):
                continue
            path = current / name
            if not path.is_symlink():
                found.append(path)


def _raise(error: OSError) -> None:
    """Default walk error handler: surface the failure instead of hiding it."""
    raise error


def _report(error: OSError, on_error: Optional[ErrorHandler]) -> None:
    """Send a recoverable per-file error to the caller, or re-raise when it has no handler."""
    if on_error is None:
        raise error
    on_error(error)


def find_duplicates(roots: Sequence[Path], *, min_size: int = 1,
                    include_hidden: bool = False,
                    on_error: Optional[ErrorHandler] = None) -> List[DuplicateGroup]:
    """Group byte-identical files by size then SHA-256; hard links count once."""
    by_size: Dict[int, List[Path]] = {}
    seen_inodes: Set[Tuple[int, int]] = set()
    for path in scan_files(roots, include_hidden=include_hidden, on_error=on_error):
        try:
            info = path.stat()
        except OSError as error:
            _report(error, on_error)
            continue
        if info.st_size < min_size:
            continue
        if info.st_ino:
            key = (info.st_dev, info.st_ino)
            if key in seen_inodes:
                continue
            seen_inodes.add(key)
        by_size.setdefault(info.st_size, []).append(path)
    groups: List[DuplicateGroup] = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_digest: Dict[str, List[Path]] = {}
        for path in paths:
            try:
                digest = hash_file(path)
            except OSError as error:
                _report(error, on_error)
                continue
            by_digest.setdefault(digest, []).append(path)
        for digest, same in by_digest.items():
            if len(same) > 1:
                groups.append(DuplicateGroup(digest, size, tuple(sorted(same, key=str))))
    groups.sort(key=lambda group: (-group.wasted_bytes, -group.size, str(group.paths[0])))
    return groups
