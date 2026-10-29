# Dupefinder

[![Built with AIKit](https://img.shields.io/badge/built%20with-AIKit-6f42c1)](https://github.com/AegeanWorks/AIKit)

Read-only duplicate file finder that groups byte-identical files by size and SHA-256 and reports reclaimable space.

## ⚡ 30-Second Cold-Start Quick Reference

- **Runtime Prerequisites**: Python 3.10 or newer; no third-party packages.
- **Canonical Regression Shield Gate**:
  ```bash
  python -m unittest discover
  ```

### 🛠️ AIKit Commands (run from the AIKit folder)
| Role | Command |
|---|---|
| Status, task and gates | `python aikit.py status dupefinder` |
| Phase 4: every gate | `python aikit.py check dupefinder` |
| Repair memory and map, then check | `python aikit.py fix dupefinder` |
| Resume an interrupted task | `python aikit.py resume dupefinder` |

## 🚀 Usage

Scan the current folder:

```bash
python -m dupefinder .
```

Scan a folder and ignore files smaller than 1 MiB:

```bash
python -m dupefinder ~/Downloads --min-size 1MiB
```

Scan only files between 10 MiB and 500 MiB:

```bash
python -m dupefinder ~/Downloads --min-size 10MiB --max-size 500MiB
```

Print a machine-readable report:

```bash
python -m dupefinder . --json
```

Export one CSV row per duplicate path:

```bash
python -m dupefinder . --csv > duplicates.csv
```

Skip logs and dependency folders:

```bash
python -m dupefinder . --exclude "*.log" --exclude node_modules
```

Keep shared rules in a file:

```bash
python -m dupefinder . --exclude-from .dupeignore
```

`.dupeignore`:

```text
# dependency and build output
node_modules
build/*
*.log
```

Write a review list of redundant copies, keeping the first path in each group:

```bash
python -m dupefinder . --redundant-list redundant.txt
```

The list contains one path per line and is created only if it does not already exist. It is not written when the scan is incomplete. `dupefinder` never deletes files; review the list before removing anything.

Keep the shortest path, the oldest copy, or the newest copy in each group:

```bash
python -m dupefinder . --redundant-list redundant.txt --keep shortest
python -m dupefinder . --redundant-list redundant.txt --keep oldest
python -m dupefinder . --redundant-list redundant.txt --keep newest
```

Limit the scan to two folder levels below the root:

```bash
python -m dupefinder . --max-depth 2
```

Check the version:

```bash
python -m dupefinder --version
```

Use it in CI, failing when copies exist:

```bash
python -m dupefinder . --fail-on-duplicates
```

`dupefinder` never deletes, moves, or rewrites a file. It groups candidates by exact size, hashes only same-size files with SHA-256, and counts hard links once. Inside scanned folders, entries whose names start with `.` are skipped unless `--include-hidden` is passed; a hidden path passed explicitly is still scanned. Symbolic links inside scanned folders are skipped.

`--min-size` and `--max-size` accept whole numbers with optional `B`, `K`/`KiB`, `M`/`MiB`, `G`/`GiB`, `T`/`TiB` or `P`/`PiB` suffixes. All suffixes are 1024-based, so `1K` means 1024 bytes.

`--exclude` is repeatable and case-sensitive. A pattern without `/` matches a file or folder name; a pattern with `/` matches the POSIX-style path relative to each root, and `*` also matches `/`. `--exclude-from FILE` reads one pattern per line, ignores blank lines and lines starting with `#`, and may be repeated. `--max-depth 1` includes files directly in each root but not subfolders; `--max-depth 0` scans only files passed explicitly. `--csv` emits the columns `sha256,size,count,wasted_bytes,path`.

`--redundant-list FILE` writes every path except the kept path in each group to a new file, one path per line. It refuses to overwrite an existing file, including a scanned file. `--keep` chooses the kept path: `first` (default, scan order), `shortest`, `oldest`, or `newest`. Ties fall back to the shortest path, then the lexicographic path, so results are deterministic. `oldest` and `newest` compare file modification times; if metadata cannot be read, the run exits `1` without writing a list. `--keep` requires `--redundant-list`.

| Exit code | Meaning |
|---|---|
| `0` | Scan completed without warnings; duplicates may or may not exist |
| `1` | `--fail-on-duplicates` was passed and duplicates were found, the scan was incomplete, or the redundant list could not be written |
| `2` | A path or exclude file does not exist, an output list already exists, or an argument is invalid |

A scan is incomplete when a folder or file cannot be read, or a root disappears while it is being scanned. Those errors are printed as `Warning:` lines on stderr, the partial report is still written to stdout, and the run exits `1` so CI cannot mistake a partial scan for a clean one.

## 🔍 How It Works

1. Walk each root without following symbolic links.
2. Group files by exact byte size, since byte-identical files always share a size.
3. Hash only the groups that contain more than one file, using streaming SHA-256.
4. Report each duplicate set, largest reclaimable space first.
5. Optionally write all but the kept path in each group to a new redundant list; `--keep` selects the first, shortest, oldest, or newest copy, and nothing is deleted.

Hard links share one inode, so they are counted once: deleting one name would not reclaim the space.

## 📦 What's Inside

```text
dupefinder/
├── .gitignore                <- transient AIKit state excluded
├── LICENSE                   <- Aegean License 1.1 (AL-1.1): free personal use
├── COMMERCIAL.md             <- Commercial licensing terms
├── LICENSES/                 <- REUSE license texts
├── REUSE.toml                <- Machine-readable SPDX metadata
├── README.md
├── pyproject.toml            <- Packaging and console-script metadata
├── dupefinder/
│   ├── __init__.py           <- Public exports
│   ├── __main__.py           <- `python -m dupefinder` entry point
│   ├── cli.py                <- Argument parsing and exit codes
│   ├── filters.py            <- Exclude globs and exclude-file loading
│   ├── hashing.py            <- Streaming SHA-256
│   ├── model.py              <- DuplicateGroup data
│   ├── report.py             <- Text, JSON and CSV rendering; redundant selection
│   └── scanner.py            <- Read-only walk and grouping
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_scanner.py
└── .aikit/                   <- this project's memory: record, ledger, decisions
```

## 📜 License

Free for personal use under the Aegean License 1.1 (AL-1.1); see [LICENSE](LICENSE). Any commercial use needs the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).
