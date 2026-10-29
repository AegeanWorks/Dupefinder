"""Behavior of the command-line interface."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

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
