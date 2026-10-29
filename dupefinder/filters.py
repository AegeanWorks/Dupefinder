"""Case-sensitive glob filters applied while walking a scan root."""

import fnmatch
from collections.abc import Sequence
from pathlib import Path


def load_patterns(path: Path) -> list[str]:
    """Read one exclude glob per line, ignoring blank lines and `#` comments."""
    patterns: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            patterns.append(text)
    return patterns


def normalize_patterns(patterns: Sequence[str]) -> tuple[str, ...]:
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
