"""Command-line entry point for dupefinder."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from dupefinder.report import render_json, render_text
from dupefinder.scanner import find_duplicates


def _non_negative(value: str) -> int:
    """Parse a byte count that cannot be negative."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"expected a whole number of bytes, got '{value}'") from error
    if number < 0:
        raise argparse.ArgumentTypeError("byte count cannot be negative")
    return number


def build_parser() -> argparse.ArgumentParser:
    """The CLI grammar, kept separate so tests can inspect it."""
    parser = argparse.ArgumentParser(
        prog="dupefinder",
        description="Find byte-identical files without changing them.",
    )
    parser.add_argument("paths", nargs="*", metavar="PATH",
                        help="files or folders to scan (default: current folder)")
    parser.add_argument("--min-size", type=_non_negative, default=1, metavar="BYTES",
                        help="ignore files smaller than BYTES (default: 1)")
    parser.add_argument("--include-hidden", action="store_true",
                        help="scan hidden files and folders")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--fail-on-duplicates", action="store_true",
                        help="exit 1 when duplicates are found")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
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
    warnings: List[str] = []
    groups = find_duplicates(
        roots,
        min_size=args.min_size,
        include_hidden=args.include_hidden,
        on_error=lambda error: warnings.append(str(error)),
    )
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(render_json(groups, roots) if args.json else render_text(groups, roots))
    if args.fail_on_duplicates and groups:
        return 1
    return 0
