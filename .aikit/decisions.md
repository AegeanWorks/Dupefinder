# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

<!-- Entry format:
### ADR-NNN: <decision in one line>
- **Date**: YYYY-MM-DD
- **Status**: Accepted
- **Context**: <what forced the decision>
- **Decision**: <what was decided>
- **Consequences**: <what follows, including what it costs>
-->

### ADR-001: Read-only, size-first duplicate detection with SHA-256

- **Date**: 2026-10-29
- **Status**: Accepted
- **Context**: Duplicate files waste disk space, but automatic deletion risks data loss, and hashing every file is slow on large trees.
- **Decision**: Scan without modifying anything, group candidates by exact byte size, hash only same-size files with SHA-256, and count hard links once so the report never claims space that deleting a path would not reclaim.
- **Consequences**: Reports are safe and fast on mostly unique trees. Byte-identical files always share a size, so no duplicate is missed. Hard-linked paths are not listed as reclaimable copies.
