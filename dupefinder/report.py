"""Text, JSON and CSV renderings of duplicate groups."""

import csv
import io
import json
from collections.abc import Sequence
from pathlib import Path

from dupefinder.model import DuplicateGroup


def format_size(size: int) -> str:
    """A compact binary-unit size such as `1.5 KiB`."""
    if size < 1024:
        return f"{size} B"
    amount = float(size)
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        amount /= 1024
        if amount < 1024:
            return f"{amount:.1f} {unit}"
    return f"{amount:.1f} PiB"


def render_text(groups: Sequence[DuplicateGroup], roots: Sequence[Path]) -> str:
    """A readable report: one block per duplicate set, then a summary."""
    if not groups:
        return f"No duplicate files found in {len(roots)} path(s)."
    copies = sum(len(group.paths) - 1 for group in groups)
    wasted = sum(group.wasted_bytes for group in groups)
    lines = [
        (f"Found {len(groups)} duplicate group(s), {copies} redundant file(s), "
         f"{format_size(wasted)} reclaimable."),
        "",
    ]
    for index, group in enumerate(groups, start=1):
        lines.append(
            f"{index}. {format_size(group.size)} each, {len(group.paths)} copies, "
            f"{format_size(group.wasted_bytes)} reclaimable"
        )
        lines.append(f"   sha256: {group.digest}")
        lines.extend(f"   {path}" for path in group.paths)
        lines.append("")
    return "\n".join(lines).rstrip()


def render_json(groups: Sequence[DuplicateGroup], roots: Sequence[Path]) -> str:
    """A stable JSON document for scripts."""
    payload = {
        "roots": [str(root) for root in roots],
        "groups": [
            {
                "sha256": group.digest,
                "size": group.size,
                "count": len(group.paths),
                "wasted_bytes": group.wasted_bytes,
                "paths": [str(path) for path in group.paths],
            }
            for group in groups
        ],
        "total_wasted_bytes": sum(group.wasted_bytes for group in groups),
    }
    return json.dumps(payload, indent=2)


def render_csv(groups: Sequence[DuplicateGroup]) -> str:
    """One CSV row per duplicate path, with a header, for spreadsheets and scripts."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["sha256", "size", "count", "wasted_bytes", "path"])
    for group in groups:
        for path in group.paths:
            writer.writerow([group.digest, group.size, len(group.paths),
                             group.wasted_bytes, str(path)])
    return buffer.getvalue().rstrip("\n")
