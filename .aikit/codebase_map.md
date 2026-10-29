# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `11`
- **Total Classes**: `3`
- **Total Top-Level Functions**: `19`
- **Total Class Methods**: `60`
- **Total Source Lines**: `943`

---

## 📦 Modules & Exported Symbols

### [`dupefinder/__init__.py`](dupefinder/__init__.py)
> *Find byte-identical files without changing them.*

**Size**: `7` lines (`259` bytes)

---

### [`dupefinder/__main__.py`](dupefinder/__main__.py)
> *Run dupefinder with `python -m dupefinder`.*

**Size**: `6` lines (`140` bytes)

---

### [`dupefinder/cli.py`](dupefinder/cli.py)
> *Command-line entry point for dupefinder.*

**Size**: `177` lines (`8086` bytes)

**Functions:**
- `def _size(value)` - *Parse a byte size such as `500`, `10K` or `1MiB`; suffixes are 1024-based.*
- `def _non_negative_int(value)` - *Parse a whole number that cannot be negative.*
- `def build_parser()` - *The CLI grammar, kept separate so tests can inspect it.*
- `def _write_redundant_list(path, groups)` - *Write all but the first path per group to a new file; return an exit code.*
- `def main(argv)` - *Run one scan; returns the process exit code.*

---

### [`dupefinder/filters.py`](dupefinder/filters.py)
> *Case-sensitive glob filters applied while walking a scan root.*

**Size**: `31` lines (`1192` bytes)

**Functions:**
- `def load_patterns(path)` - *Read one exclude glob per line, ignoring blank lines and `#` comments.*
- `def normalize_patterns(patterns)` - *Turn user globs into POSIX-style patterns; backslashes become slashes.*
- `def is_excluded(relative, name, patterns)` - *Whether a file or folder matches one exclude pattern.*

---

### [`dupefinder/hashing.py`](dupefinder/hashing.py)
> *Streaming SHA-256 for candidate files.*

**Size**: `15` lines (`456` bytes)

**Functions:**
- `def hash_file(path, chunk_size)` - *Return the SHA-256 hex digest of `path`, reading it in bounded chunks.*

---

### [`dupefinder/model.py`](dupefinder/model.py)
> *Data reported for one set of byte-identical files.*

**Size**: `18` lines (`431` bytes)

**Classes:**
- `class DuplicateGroup` - *Files with the same size and SHA-256 digest.*
  - Property `.wasted_bytes` - *Space reclaimable by keeping one copy.*

---

### [`dupefinder/report.py`](dupefinder/report.py)
> *Text, JSON and CSV renderings of duplicate groups.*

**Size**: `79` lines (`2828` bytes)

**Functions:**
- `def format_size(size)` - *A compact binary-unit size such as `1.5 KiB`.*
- `def render_text(groups, roots)` - *A readable report: one block per duplicate set, then a summary.*
- `def render_json(groups, roots)` - *A stable JSON document for scripts.*
- `def render_csv(groups)` - *One CSV row per duplicate path, with a header, for spreadsheets and scripts.*
- `def redundant_paths(groups)` - *Every path except the first (kept) path in each group.*

---

### [`dupefinder/scanner.py`](dupefinder/scanner.py)
> *Read-only filesystem walk and duplicate grouping.*

**Size**: `114` lines (`4644` bytes)

**Functions:**
- `def scan_files(roots, *, include_hidden, exclude, max_depth, on_error)` - *Every regular, non-symlink file under `roots`, in stable order.*
- `def _walk(root, include_hidden, patterns, max_depth, on_error, found)` - *Append regular files under one directory, skipping hidden, excluded and symlinked entries.*
- `def _raise(error)` - *Default walk error handler: surface the failure instead of hiding it.*
- `def _report(error, on_error)` - *Send a recoverable per-file error to the caller, or re-raise when it has no handler.*
- `def find_duplicates(roots, *, min_size, max_size, include_hidden, exclude, max_depth, on_error)` - *Group byte-identical files between the size bounds; hard links count once.*

---

### [`tests/__init__.py`](tests/__init__.py)
> *Tests for dupefinder.*

**Size**: `1` lines (`28` bytes)

---

### [`tests/test_cli.py`](tests/test_cli.py)
> *Behavior of the command-line interface.*

**Size**: `318` lines (`13674` bytes)

**Classes:**
- `class CliTests`
  - Method `.setUp()`
  - Method `.write(relative, data)`
  - Method `.run_main(*args)`
  - Method `.test_json_report_lists_duplicate_groups()`
  - Method `.test_human_report_summarizes_reclaimable_space()`
  - Method `.test_no_duplicates_message()`
  - Method `.test_missing_path_exits_2()`
  - Method `.test_fail_on_duplicates_exits_1()`
  - Method `.test_fail_on_duplicates_without_duplicates_exits_0()`
  - Method `.test_min_size_filters_small_files()`
  - Method `.test_invalid_min_size_exits_2()`
  - Method `.test_invalid_max_depth_exits_2()`
  - Method `.test_csv_report_has_a_header_and_one_row_per_path()`
  - Method `.test_exclude_flag_filters_files()`
  - Method `.test_exclude_can_be_repeated()`
  - Method `.test_max_depth_flag_limits_scan()`
  - Method `.test_min_size_accepts_binary_suffixes()`
  - Method `.test_max_size_filters_large_files()`
  - Method `.test_invalid_size_unit_exits_2()`
  - Method `.test_max_size_below_min_size_exits_2()`
  - Method `.test_exclude_from_reads_patterns_and_ignores_comments()`
  - Method `.test_exclude_from_can_be_repeated()`
  - Method `.test_missing_exclude_file_exits_2()`
  - Method `.test_non_utf8_exclude_file_exits_2()`
  - Method `.test_redundant_list_writes_all_but_first_path()`
  - Method `.test_redundant_list_refuses_to_overwrite_a_scanned_file()`
  - Method `.test_redundant_list_is_empty_without_duplicates()`
  - Method `.test_redundant_list_write_failure_exits_1()`
  - Method `.test_incomplete_scan_does_not_write_redundant_list()`
  - Method `.test_csv_and_json_are_mutually_exclusive()`
  - Method `.test_version_prints_the_package_version()`
  - Method `.test_version_matches_pyproject()`
  - Method `.test_include_hidden_flag_scans_dot_directories()`
  - Method `.test_csv_quotes_paths_with_commas()`
  - Method `.test_incomplete_scan_exits_1()`
  - Method `.test_scan_failure_exits_1()`

---

### [`tests/test_scanner.py`](tests/test_scanner.py)
> *Behavior of the read-only scanner.*

**Size**: `177` lines (`7350` bytes)

**Classes:**
- `class ScannerTests`
  - Method `.setUp()`
  - Method `.write(relative, data)`
  - Method `.test_finds_identical_files_and_ignores_unique_ones()`
  - Method `.test_same_size_different_content_is_not_a_duplicate()`
  - Method `.test_min_size_filters_small_files()`
  - Method `.test_max_size_filters_large_files()`
  - Method `.test_hidden_files_are_skipped_unless_requested()`
  - Method `.test_hidden_root_is_scanned_when_passed_explicitly()`
  - Method `.test_hard_links_are_counted_once()`
  - Method `.test_scan_files_returns_a_file_passed_directly()`
  - Method `.test_scan_files_skips_symlinks()`
  - Method `.test_missing_root_raises()`
  - Method `.test_hash_file_matches_hashlib()`
  - Method `.test_largest_reclaimable_group_is_reported_first()`
  - Method `.test_exclude_skips_matching_files()`
  - Method `.test_exclude_prunes_matching_folders()`
  - Method `.test_exclude_matches_relative_paths()`
  - Method `.test_exclude_can_skip_an_explicit_file()`
  - Method `.test_exclude_normalizes_backslashes()`
  - Method `.test_max_depth_limits_recursion()`
  - Method `.test_max_depth_zero_skips_directory_files()`
  - Method `.test_max_depth_zero_keeps_an_explicit_file()`
  - Method `.test_format_size()`

---
