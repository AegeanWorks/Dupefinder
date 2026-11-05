"""Data reported for one set of byte-identical files."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DuplicateGroup:
    """Files with the same size and SHA-256 digest."""

    digest: str
    size: int
    paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        """Reject shapes that would make `wasted_bytes` or sorting lie."""
        if isinstance(self.digest, bool) or not isinstance(self.digest, str) or not self.digest:
            raise ValueError(f"digest must be a non-empty string, got {self.digest!r}")
        if isinstance(self.size, bool) or not isinstance(self.size, int) or self.size < 0:
            raise ValueError(f"size must be a non-negative integer, got {self.size!r}")
        if not isinstance(self.paths, tuple) or not self.paths:
            raise ValueError("paths must be a non-empty tuple of Path objects")
        for item in self.paths:
            if not isinstance(item, Path):
                raise ValueError(f"paths must contain only Path objects, got {item!r}")

    @property
    def wasted_bytes(self) -> int:
        """Space reclaimable by keeping one copy."""
        return self.size * (len(self.paths) - 1)
