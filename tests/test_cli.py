"""Behavior of the command-line interface."""

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from dupefinder import __version__
from dupefinder.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, relative: str, data: bytes) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def run_main(self, *args: str) -> tuple:
        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(list(args))
        return code, output.getvalue(), errors.getvalue()

    def test_json_report_lists_duplicate_groups(self):
        self.write("a.txt", b"same")
        self.write("b.txt", b"same")
        code, output, _ = self.run_main("--json", str(self.root))
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(report["total_wasted_bytes"], 4)
        self.assertEqual(len(report["groups"]), 1)
        self.assertEqual(report["groups"][0]["count"], 2)

    def test_human_report_summarizes_reclaimable_space(self):
        first = self.write("a.txt", b"same")
        second = self.write("b.txt", b"same")
        code, output, _ = self.run_main(str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("4 B reclaimable", output)
        self.assertIn(str(first), output)
        self.assertIn(str(second), output)

    def test_no_duplicates_message(self):
        self.write("only.txt", b"unique")
        code, output, _ = self.run_main(str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("No duplicate files found", output)

    def test_missing_path_exits_2(self):
        code, _, errors = self.run_main(str(self.root / "missing"))
        self.assertEqual(code, 2)
        self.assertIn("Error: path not found", errors)

    def test_fail_on_duplicates_exits_1(self):
        self.write("a.txt", b"same")
        self.write("b.txt", b"same")
        code, _, _ = self.run_main("--fail-on-duplicates", str(self.root))
        self.assertEqual(code, 1)

    def test_fail_on_duplicates_without_duplicates_exits_0(self):
        self.write("only.txt", b"unique")
        code, _, _ = self.run_main("--fail-on-duplicates", str(self.root))
        self.assertEqual(code, 0)

    def test_min_size_filters_small_files(self):
        self.write("a.txt", b"x")
        self.write("b.txt", b"x")
        code, output, _ = self.run_main("--min-size", "2", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("No duplicate files found", output)

    def test_invalid_min_size_exits_2(self):
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
            main(["--min-size", "-1", str(self.root)])
        self.assertEqual(caught.exception.code, 2)

    def test_invalid_max_depth_exits_2(self):
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
            main(["--max-depth", "-1", str(self.root)])
        self.assertEqual(caught.exception.code, 2)

    def test_csv_report_has_a_header_and_one_row_per_path(self):
        self.write("a.txt", b"same")
        self.write("b.txt", b"same")
        code, output, _ = self.run_main("--csv", str(self.root))
        rows = list(csv.reader(io.StringIO(output)))
        self.assertEqual(code, 0)
        self.assertEqual(rows[0], ["sha256", "size", "count", "wasted_bytes", "path"])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1][1], "4")
        self.assertEqual(rows[1][2], "2")
        self.assertEqual(rows[1][3], "4")

    def test_exclude_flag_filters_files(self):
        keep = self.write("keep.txt", b"same")
        self.write("other.txt", b"same")
        skip = self.write("skip.log", b"other")
        self.write("also.log", b"other")
        code, output, _ = self.run_main("--exclude", "*.log", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn(str(keep), output)
        self.assertNotIn(str(skip), output)

    def test_exclude_can_be_repeated(self):
        keep = self.write("keep.txt", b"same")
        self.write("other.txt", b"same")
        skip_log = self.write("skip.log", b"other")
        self.write("also.log", b"other")
        skip_tmp = self.write("skip.tmp", b"third")
        self.write("also.tmp", b"third")
        code, output, _ = self.run_main(
            "--exclude", "*.log", "--exclude", "*.tmp", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn(str(keep), output)
        self.assertNotIn(str(skip_log), output)
        self.assertNotIn(str(skip_tmp), output)

    def test_max_depth_flag_limits_scan(self):
        self.write("a.txt", b"same")
        self.write("b.txt", b"same")
        self.write("sub/c.txt", b"same")
        self.write("sub/d.txt", b"same")
        code, output, _ = self.run_main("--max-depth", "1", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("2 copies", output)
        self.assertNotIn(str(self.root / "sub"), output)

    def test_min_size_accepts_binary_suffixes(self):
        self.write("big-a.bin", b"x" * 1024)
        self.write("big-b.bin", b"x" * 1024)
        self.write("small-a.bin", b"x" * 10)
        self.write("small-b.bin", b"x" * 10)
        code, output, _ = self.run_main("--json", "--min-size", "1KiB", str(self.root))
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual([group["size"] for group in report["groups"]], [1024])

    def test_max_size_filters_large_files(self):
        self.write("big-a.bin", b"x" * 1024)
        self.write("big-b.bin", b"x" * 1024)
        self.write("small-a.bin", b"x" * 10)
        self.write("small-b.bin", b"x" * 10)
        code, output, _ = self.run_main("--json", "--max-size", "10", str(self.root))
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual([group["size"] for group in report["groups"]], [10])

    def test_invalid_size_unit_exits_2(self):
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
            main(["--min-size", "1XB", str(self.root)])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("unknown size unit", errors.getvalue())

    def test_max_size_below_min_size_exits_2(self):
        code, _, errors = self.run_main(
            "--min-size", "2K", "--max-size", "1K", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("--max-size must be greater than or equal to --min-size", errors)

    def test_exclude_from_reads_patterns_and_ignores_comments(self):
        keep = self.write("keep.txt", b"same")
        self.write("other.txt", b"same")
        skip_log = self.write("skip.log", b"other")
        self.write("also.log", b"other")
        skip_dir = self.write("node_modules/skip.txt", b"third")
        self.write("node_modules/also.txt", b"third")
        rules = self.root / "excludes.txt"
        rules.write_text("# generated\n\n*.log\nnode_modules\n", encoding="utf-8")
        code, output, _ = self.run_main("--exclude-from", str(rules), str(self.root))
        self.assertEqual(code, 0)
        self.assertIn(str(keep), output)
        self.assertNotIn(str(skip_log), output)
        self.assertNotIn(str(skip_dir), output)

    def test_exclude_from_can_be_repeated(self):
        keep = self.write("keep.txt", b"same")
        self.write("other.txt", b"same")
        skip_log = self.write("skip.log", b"other")
        self.write("also.log", b"other")
        skip_tmp = self.write("skip.tmp", b"third")
        self.write("also.tmp", b"third")
        first = self.root / "first.rules"
        second = self.root / "second.rules"
        first.write_text("*.log\n", encoding="utf-8")
        second.write_text("*.tmp\n", encoding="utf-8")
        code, output, _ = self.run_main(
            "--exclude-from", str(first), "--exclude-from", str(second), str(self.root))
        self.assertEqual(code, 0)
        self.assertIn(str(keep), output)
        self.assertNotIn(str(skip_log), output)
        self.assertNotIn(str(skip_tmp), output)

    def test_missing_exclude_file_exits_2(self):
        code, _, errors = self.run_main(
            "--exclude-from", str(self.root / "missing.rules"), str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("cannot read exclude file", errors)

    def test_non_utf8_exclude_file_exits_2(self):
        rules = self.root / "bad.rules"
        rules.write_bytes(b"\xff\xfe\n")
        code, _, errors = self.run_main("--exclude-from", str(rules), str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("cannot read exclude file", errors)

    def test_redundant_list_writes_all_but_first_path(self):
        first = self.write("a.txt", b"same")
        second = self.write("b.txt", b"same")
        third = self.write("c.txt", b"same")
        output = self.root / "redundant.txt"
        code, _, _ = self.run_main("--redundant-list", str(output), str(self.root))
        self.assertEqual(code, 0)
        self.assertEqual(output.read_text(encoding="utf-8").splitlines(),
                         [str(second), str(third)])
        self.assertNotIn(str(first), output.read_text(encoding="utf-8"))

    def test_redundant_list_refuses_to_overwrite_a_scanned_file(self):
        first = self.write("a.txt", b"same")
        self.write("b.txt", b"same")
        code, _, errors = self.run_main("--redundant-list", str(first), str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("already exists", errors)
        self.assertEqual(first.read_bytes(), b"same")

    def test_redundant_list_is_empty_without_duplicates(self):
        self.write("only.txt", b"unique")
        output = self.root / "redundant.txt"
        code, _, _ = self.run_main("--redundant-list", str(output), str(self.root))
        self.assertEqual(code, 0)
        self.assertEqual(output.read_text(encoding="utf-8"), "")

    def test_redundant_list_write_failure_exits_1(self):
        self.write("a.txt", b"same")
        self.write("b.txt", b"same")
        output = self.root / "missing" / "redundant.txt"
        code, _, errors = self.run_main("--redundant-list", str(output), str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("cannot write redundant list", errors)

    def test_incomplete_scan_does_not_write_redundant_list(self):
        def fake_scan(roots, **kwargs):
            kwargs["on_error"](PermissionError("denied"))
            return []

        output = self.root / "redundant.txt"
        with mock.patch("dupefinder.cli.find_duplicates", side_effect=fake_scan):
            code, _, errors = self.run_main("--redundant-list", str(output), str(self.root))
        self.assertEqual(code, 1)
        self.assertFalse(output.exists())
        self.assertIn("refusing to write redundant list", errors)

    def test_csv_and_json_are_mutually_exclusive(self):
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
            main(["--json", "--csv", str(self.root)])
        self.assertEqual(caught.exception.code, 2)

    def test_version_prints_the_package_version(self):
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as caught:
            main(["--version"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn("dupefinder 0.4.0", output.getvalue())

    def test_version_matches_pyproject(self):
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        self.assertIn(f'version = "{__version__}"',
                      pyproject.read_text(encoding="utf-8"))

    def test_include_hidden_flag_scans_dot_directories(self):
        self.write(".hidden/a.txt", b"same")
        self.write(".hidden/b.txt", b"same")
        code, output, _ = self.run_main(str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("No duplicate files found", output)
        code, output, _ = self.run_main("--include-hidden", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("2 copies", output)

    def test_csv_quotes_paths_with_commas(self):
        self.write("a,one.txt", b"same")
        self.write("b,two.txt", b"same")
        code, output, _ = self.run_main("--csv", str(self.root))
        rows = list(csv.reader(io.StringIO(output)))
        self.assertEqual(code, 0)
        self.assertEqual(len(rows), 3)
        self.assertTrue(rows[1][4].endswith("a,one.txt"))

    def test_incomplete_scan_exits_1(self):
        def fake_scan(roots, **kwargs):
            kwargs["on_error"](PermissionError("denied"))
            return []

        with mock.patch("dupefinder.cli.find_duplicates", side_effect=fake_scan):
            code, _, errors = self.run_main(str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("Warning: denied", errors)

    def test_scan_failure_exits_1(self):
        with mock.patch("dupefinder.cli.find_duplicates",
                        side_effect=FileNotFoundError("gone")):
            code, _, errors = self.run_main(str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("Error: scan failed: gone", errors)
