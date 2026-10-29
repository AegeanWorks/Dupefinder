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
python -m dupefinder ~/Downloads --min-size 1048576
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

`dupefinder` never deletes, moves, or rewrites a file. It groups candidates by exact size, hashes only same-size files with SHA-256, and counts hard links once. Hidden files and folders are skipped unless `--include-hidden` is passed; symbolic links are skipped.

`--exclude` is repeatable and case-sensitive. A pattern without `/` matches a file or folder name; a pattern with `/` matches the POSIX-style path relative to each root, and `*` also matches `/`. `--max-depth 1` includes files directly in each root but not subfolders. `--csv` emits the columns `sha256,size,count,wasted_bytes,path`.

| Exit code | Meaning |
|---|---|
| `0` | Scan completed; duplicates may or may not exist |
| `1` | `--fail-on-duplicates` was passed and duplicates were found |
| `2` | A path does not exist, or an argument is invalid |

## 🔍 How It Works

1. Walk each root without following symbolic links.
2. Group files by exact byte size, since byte-identical files always share a size.
3. Hash only the groups that contain more than one file, using streaming SHA-256.
4. Report each duplicate set, largest reclaimable space first.

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
│   ├── filters.py            <- Exclude glob matching
│   ├── hashing.py            <- Streaming SHA-256
│   ├── model.py              <- DuplicateGroup data
│   ├── report.py             <- Text, JSON and CSV rendering
│   └── scanner.py            <- Read-only walk and grouping
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_scanner.py
└── .aikit/                   <- this project's memory: record, ledger, decisions
```

## 📜 License

Free for personal use under the Aegean License 1.1 (AL-1.1); see [LICENSE](LICENSE). Any commercial use needs the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).
