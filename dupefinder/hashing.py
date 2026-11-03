"""Streaming SHA-256 for candidate files."""

import hashlib
from pathlib import Path

CHUNK_SIZE = 64 * 1024


def hash_file(path: Path, chunk_size: int = CHUNK_SIZE) -> str:
    """Return the SHA-256 hex digest of `path`, reading it in bounded chunks."""
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError(f"chunk_size must be a positive integer, got {chunk_size!r}")
    digest = hashlib.sha256()
    with path.open(mode="rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
