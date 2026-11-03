"""Behavior of the read-only scanner."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dupefinder.hashing import hash_file
from dupefinder.report import format_size
from dupefinder.scanner import find_duplicates, scan_files


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

    def test_max_size_filters_large_files(self):
        self.write("small-a.bin", b"x")
        self.write("small-b.bin", b"x")
        self.write("large-a.bin", b"x" * 10)
        self.write("large-b.bin", b"x" * 10)
        small = find_duplicates([self.root], max_size=1)
        self.assertEqual(len(small), 1)
        self.assertEqual(small[0].size, 1)
        both = find_duplicates([self.root], max_size=10)
        self.assertEqual([group.size for group in both], [10, 1])

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

    def test_scan_files_skips_symlinked_directory_root(self):
        link = self.root / "linkdir"
        link.mkdir()
        self.write("linkdir/a.txt", b"x")
        with mock.patch.object(Path, "exists", autospec=True) as exists, \
                mock.patch.object(Path, "is_symlink", autospec=True) as is_link, \
                mock.patch.object(Path, "is_file", autospec=True) as is_file:
            exists.side_effect = lambda self: True
            is_link.side_effect = lambda self: self == link
            is_file.side_effect = lambda self: False
            self.assertEqual(scan_files([link]), [])

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

    def test_exclude_skips_matching_files(self):
        self.write("keep-a.txt", b"same")
        self.write("keep-b.txt", b"same")
        self.write("skip-a.log", b"other")
        self.write("skip-b.log", b"other")
        groups = find_duplicates([self.root], exclude=["*.log"])
        self.assertEqual(len(groups), 1)
        self.assertTrue(all(path.suffix == ".txt" for path in groups[0].paths))

    def test_exclude_prunes_matching_folders(self):
        self.write("node_modules/a.txt", b"same")
        self.write("node_modules/b.txt", b"same")
        self.write("src/a.txt", b"same")
        self.write("src/b.txt", b"same")
        groups = find_duplicates([self.root], exclude=["node_modules"])
        self.assertEqual(len(groups), 1)
        self.assertTrue(all(path.relative_to(self.root).parts[0] != "node_modules"
                            for path in groups[0].paths))

    def test_exclude_matches_relative_paths(self):
        self.write("build/a.tmp", b"same")
        self.write("build/b.tmp", b"same")
        self.write("src/a.tmp", b"same")
        self.write("src/b.tmp", b"same")
        groups = find_duplicates([self.root], exclude=["build/*"])
        self.assertEqual(len(groups), 1)
        self.assertTrue(all(path.relative_to(self.root).parts[0] != "build"
                            for path in groups[0].paths))

    def test_exclude_can_skip_an_explicit_file(self):
        path = self.write("one.log", b"x")
        self.assertEqual(scan_files([path], exclude=["*.log"]), [])

    def test_exclude_normalizes_backslashes(self):
        self.write("build/a.tmp", b"same")
        self.write("build/b.tmp", b"same")
        self.write("src/a.tmp", b"same")
        self.write("src/b.tmp", b"same")
        groups = find_duplicates([self.root], exclude=["build\\*.tmp"])
        self.assertEqual(len(groups), 1)
        self.assertTrue(all(path.relative_to(self.root).parts[0] != "build"
                            for path in groups[0].paths))

    def test_max_depth_limits_recursion(self):
        self.write("root-a.txt", b"same")
        self.write("root-b.txt", b"same")
        self.write("sub/deep-a.txt", b"same")
        self.write("sub/deep-b.txt", b"same")
        shallow = find_duplicates([self.root], max_depth=1)
        self.assertEqual(len(shallow), 1)
        self.assertEqual(len(shallow[0].paths), 2)
        deep = find_duplicates([self.root], max_depth=2)
        self.assertEqual(len(deep[0].paths), 4)

    def test_max_depth_zero_skips_directory_files(self):
        self.write("a.txt", b"same")
        self.write("b.txt", b"same")
        self.assertEqual(find_duplicates([self.root], max_depth=0), [])

    def test_max_depth_zero_keeps_an_explicit_file(self):
        path = self.write("a.txt", b"x")
        self.assertEqual(scan_files([path], max_depth=0), [path])

    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1024), "1.0 KiB")
        self.assertEqual(format_size(1536), "1.5 KiB")

    def test_format_size_large_units(self):
        self.assertEqual(format_size(1024 ** 2), "1.0 MiB")
        self.assertEqual(format_size(1024 ** 4), "1.0 TiB")
        self.assertEqual(format_size(1024 ** 5), "1.0 PiB")
        self.assertEqual(format_size(1024 ** 6), "1.0 EiB")

    def test_format_size_rounding_carries_to_next_unit(self):
        self.assertEqual(format_size(1048575), "1.0 MiB")
        self.assertEqual(format_size(1073741823), "1.0 GiB")
        self.assertNotIn("1024.0", format_size(1048575))

    def test_hash_file_rejects_non_positive_chunk_size(self):
        path = self.write("a.bin", b"abc")
        for bad in (0, -1, -4096):
            with self.assertRaises(ValueError, msg=f"chunk_size={bad}"):
                hash_file(path, chunk_size=bad)

    def test_broken_symlink_root_is_skipped(self):
        link = self.root / "link.txt"
        with mock.patch.object(Path, "exists", autospec=True) as exists, \
                mock.patch.object(Path, "is_symlink", autospec=True) as is_link:
            exists.side_effect = lambda self: False if self == link else True
            is_link.side_effect = lambda self: True if self == link else False
            self.assertEqual(scan_files([link]), [])

    def test_scan_files_dedupes_overlapping_roots(self):
        first = self.write("a.txt", b"x")
        self.write("b.txt", b"x")
        self.assertEqual(
            sorted(map(str, scan_files([self.root, first]))),
            sorted(map(str, scan_files([self.root]))))

    def test_redundant_paths_validates_keep_even_when_empty(self):
        from dupefinder.report import redundant_paths
        with self.assertRaises(ValueError):
            redundant_paths([], keep="bogus")

    def test_redundant_paths_duplicate_entries(self):
        from pathlib import Path as _Path  # noqa: F401  (kept local for clarity)
        from dupefinder.model import DuplicateGroup
        from dupefinder.report import redundant_paths
        group = DuplicateGroup("d", 4, (_Path("a"), _Path("a")))
        self.assertEqual(redundant_paths([group], keep="first"), [_Path("a")])

    def test_redundant_singleton_oldest_does_not_stat(self):
        from dupefinder.model import DuplicateGroup
        from dupefinder.report import redundant_paths
        group = DuplicateGroup("d", 4, (self.root / "definitely-missing-xyz",))
        with mock.patch.object(Path, "stat", side_effect=AssertionError("must not stat")):
            self.assertEqual(redundant_paths([group], keep="oldest"), [])
            self.assertEqual(redundant_paths([group], keep="newest"), [])

    def test_render_text_preserves_trailing_space(self):
        from dupefinder.model import DuplicateGroup
        from dupefinder.report import render_text
        text = render_text(
            [DuplicateGroup("d", 1, (Path("/tmp/a "), Path("/tmp/b")))], [Path("/tmp")])
        self.assertIn("a ", text)
        self.assertNotIn("a\n", text.split("sha256")[1])
