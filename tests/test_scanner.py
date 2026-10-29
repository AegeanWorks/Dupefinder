"""Behavior of the read-only scanner."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from dupefinder.report import format_size
from dupefinder.scanner import find_duplicates, scan_files
from dupefinder.hashing import hash_file


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, relative: str, data: bytes) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_finds_identical_files_and_ignores_unique_ones(self):
        first = self.write("a/one.txt", b"same")
        second = self.write("b/two.txt", b"same")
        self.write("unique.txt", b"different")
        groups = find_duplicates([self.root])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].size, 4)
        self.assertEqual(groups[0].paths, (first, second))
        self.assertEqual(groups[0].wasted_bytes, 4)

    def test_same_size_different_content_is_not_a_duplicate(self):
        self.write("a.bin", b"abcd")
        self.write("b.bin", b"wxyz")
        self.assertEqual(find_duplicates([self.root]), [])

    def test_min_size_filters_small_files(self):
        self.write("a.txt", b"x")
        self.write("b.txt", b"x")
        self.assertEqual(find_duplicates([self.root], min_size=2), [])
        self.assertEqual(len(find_duplicates([self.root], min_size=1)), 1)

    def test_hidden_files_are_skipped_unless_requested(self):
        self.write(".hidden/a.txt", b"same")
        self.write(".hidden/b.txt", b"same")
        self.assertEqual(find_duplicates([self.root]), [])
        self.assertEqual(len(find_duplicates([self.root], include_hidden=True)), 1)

    def test_hidden_root_is_scanned_when_passed_explicitly(self):
        self.write(".hidden/a.txt", b"same")
        self.write(".hidden/b.txt", b"same")
        groups = find_duplicates([self.root / ".hidden"])
        self.assertEqual(len(groups), 1)

    def test_hard_links_are_counted_once(self):
        original = self.write("original.txt", b"same")
        link = self.root / "link.txt"
        try:
            link.hardlink_to(original)
        except (OSError, NotImplementedError):
            self.skipTest("hard links are unavailable here")
        self.write("copy.txt", b"same")
        groups = find_duplicates([self.root])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].paths), 2)
        self.assertEqual(groups[0].wasted_bytes, 4)

    def test_scan_files_returns_a_file_passed_directly(self):
        path = self.write("one.txt", b"x")
        self.assertEqual(scan_files([path]), [path])

    def test_scan_files_skips_symlinks(self):
        target = self.write("target.txt", b"x")
        link = self.root / "link.txt"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are unavailable here")
        self.assertEqual(scan_files([self.root]), [target])

    def test_missing_root_raises(self):
        with self.assertRaises(FileNotFoundError):
            scan_files([self.root / "missing"])

    def test_hash_file_matches_hashlib(self):
        path = self.write("data.bin", b"abc")
        self.assertEqual(hash_file(path), hashlib.sha256(b"abc").hexdigest())

    def test_largest_reclaimable_group_is_reported_first(self):
        self.write("small/a.txt", b"x")
        self.write("small/b.txt", b"x")
        self.write("large/a.txt", b"0123456789")
        self.write("large/b.txt", b"0123456789")
        groups = find_duplicates([self.root])
        self.assertEqual([group.size for group in groups], [10, 1])

    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1024), "1.0 KiB")
        self.assertEqual(format_size(1536), "1.5 KiB")
