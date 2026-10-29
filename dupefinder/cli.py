"""Command-line entry point for dupefinder."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from dupefinder import __version__
from dupefinder.report import render_csv, render_json, render_text
from dupefinder.scanner import find_duplicates


def _non_negative_int(value: str) -> int:
    """Parse a whole number that cannot be negative."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"expected a non-negative whole number, got '{value}'") from error
    if number < 0:
        raise argparse.ArgumentTypeError("value cannot be negative")
    return number


def build_parser() -> argparse.ArgumentParser:
    """The CLI grammar, kept separate so tests can inspect it."""
    parser = argparse.ArgumentParser(
        prog="dupefinder",
        description="Find byte-identical files without changing them.",
    )
    parser.add_argument("paths", nargs="*", metavar="PATH",
                        help="files or folders to scan (default: current folder)")
    parser.add_argument("--min-size", type=_non_negative_int, default=1, metavar="BYTES",
                        help="ignore files smaller than BYTES (default: 1)")
    parser.add_argument("--max-depth", type=_non_negative_int, default=None, metavar="N",
                        help="scan at most N folder levels below each root")
    parser.add_argument("--exclude", action="append", metavar="GLOB",
                        help="skip files or folders matching GLOB; repeatable, case-sensitive")
    parser.add_argument("--include-hidden", action="store_true",
                        help="scan dot-prefixed hidden files and folders")
    formats = parser.add_mutually_exclusive_group()
    formats.add_argument("--json", action="store_true", help="print machine-readable JSON")
    formats.add_argument("--csv", action="store_true",
                         help="print one CSV row per duplicate path")
    parser.add_argument("--fail-on-duplicates", action="store_true",
                        help="exit 1 when duplicates are found")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one scan; returns the process exit code."""
    args = build_parser().parse_args(argv)
    roots = [Path(item) for item in (args.paths or ["."])]
    missing = [str(path) for path in roots if not path.exists()]
    if missing:
        print(f"Error: path not found: {', '.join(missing)}", file=sys.stderr)
        print("Why: dupefinder scans existing files and folders only.", file=sys.stderr)
        print("Fix: pass an existing file or folder, e.g. `python -m dupefinder .`.",
              file=sys.stderr)
        return 2
    warnings: list[str] = []
    try:
        groups = find_duplicates(
            roots,
            min_size=args.min_size,
            include_hidden=args.include_hidden,
            exclude=args.exclude or (),
            max_depth=args.max_depth,
            on_error=lambda error: warnings.append(str(error)),
        )
    except OSError as error:
        print(f"Error: scan failed: {error}", file=sys.stderr)
        print("Why: a root may have moved or become unreadable during the scan.",
              file=sys.stderr)
        print("Fix: rerun the scan; if it repeats, check the path and its permissions.",
              file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    if args.csv:
        print(render_csv(groups))
    elif args.json:
        print(render_json(groups, roots))
    else:
        print(render_text(groups, roots))
    # An incomplete scan must not report success: an unreadable folder can hide the only
    # copy of a duplicate, so warnings fail the run just as --fail-on-duplicates does.
    if warnings or (args.fail_on_duplicates and groups):
        return 1
    return 0
