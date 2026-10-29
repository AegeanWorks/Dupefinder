"""Case-sensitive glob filters applied while walking a scan root."""

import fnmatch
from pathlib import Path
from typing import Sequence, Tuple


def normalize_patterns(patterns: Sequence[str]) -> Tuple[str, ...]:
    """Turn user globs into POSIX-style patterns; backslashes become slashes."""
    return tuple(pattern.replace("\\", "/") for pattern in patterns)


def is_excluded(relative: Path, name: str, patterns: Sequence[str]) -> bool:
    """Whether a file or folder matches one exclude pattern.

    A pattern containing `/` matches the POSIX-style path relative to the scan root; a bare
    pattern matches the entry's name. Matching is case-sensitive on every platform.
    """
    text = relative.as_posix()
    return any(fnmatch.fnmatchcase(text if "/" in pattern else name, pattern)
               for pattern in patterns)
