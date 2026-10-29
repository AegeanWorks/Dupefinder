"""Find byte-identical files without changing them."""

from dupefinder.model import DuplicateGroup
from dupefinder.scanner import find_duplicates, scan_files

__version__ = "0.3.0"
__all__ = ["DuplicateGroup", "__version__", "find_duplicates", "scan_files"]
