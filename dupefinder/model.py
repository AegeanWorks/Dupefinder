"""Data reported for one set of byte-identical files."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DuplicateGroup:
    """Files with the same size and SHA-256 digest."""

    digest: str
    size: int
    paths: tuple[Path, ...]

    @property
    def wasted_bytes(self) -> int:
        """Space reclaimable by keeping one copy."""
        return self.size * (len(self.paths) - 1)
