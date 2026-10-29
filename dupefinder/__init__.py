"""Find byte-identical files without changing them."""

from dupefinder.model import DuplicateGroup
from dupefinder.scanner import find_duplicates, scan_files

__all__ = ["DuplicateGroup", "find_duplicates", "scan_files"]
