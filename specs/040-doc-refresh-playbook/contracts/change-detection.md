# Change Detection Contract

**Feature**: 040-doc-refresh-playbook
**Date**: 2026-03-14
**Version**: 1.0

## Purpose

Defines the three-source change detection process that produces the Change Manifest. This contract governs Phase 1 (Detect Changes) of the refresh playbook and ensures comprehensive coverage of all user-visible changes.

## Input: Refresh Baseline

The process begins by reading `docs/.last-refresh`:

```json
{
  "date": "2026-03-01T10:00:00Z",
  "sha": "abc1234def5678...",
  "documents_updated": ["docs/api-reference.md", "README.md"],
  "documents_skipped": ["docs/signal-integration.md"],
  "broken_links_found": 0,
  "manual_followups": []
}
```

**Fallback behavior** (FR-020): If the file is missing or malformed:
1. Attempt to find the most recent `docs-refresh-*` git tag
2. If no tag exists, use `--since="2 weeks ago"` for date-based operations and `HEAD~100` for SHA-based operations
3. Log a warning: "No valid baseline found; using default 2-week window"

## Source 1: CHANGELOG Delta

**Command**: Read `CHANGELOG.md` from the current HEAD.

**Parsing rules**:
1. Scan for date-section headers matching `## YYYY-MM-DD` or `## [Unreleased]`
2. Include all entries from sections dated after the baseline date AND the `[Unreleased]` section
3. Within each section, extract items grouped under `### Added`, `### Changed`, `### Removed`, `### Fixed`
4. Each bullet item (`- `) becomes a ManifestItem with `source: "CHANGELOG"`

**Output format** (per item):
```
- description: <bullet text>
  source: CHANGELOG
  source_detail: "## YYYY-MM-DD > ### Added"
  domain: <inferred from content>
  category: <mapped from CHANGELOG section>
```

**Category mapping**:
| CHANGELOG Section | Manifest Category |
|---|---|
| `### Added` | New features |
| `### Changed` | Changed behavior |
| `### Removed` | Removed functionality |
| `### Fixed` | Changed behavior (unless fix removes a workaround → Removed functionality) |

## Source 2: Spec Directory Scan

**Command**: Find spec directories modified since the baseline date.

```bash
find specs/ -mindepth 1 -maxdepth 1 -type d -newer docs/.last-refresh
```

**Fallback** (no baseline file): Use `find specs/ -mindepth 1 -maxdepth 1 -type d -newermt "2 weeks ago"`

**Processing**:
1. For each modified directory, read `spec.md` (if it exists)
2. Extract the feature title (first `# ` heading) and the first paragraph as the summary
3. Create a ManifestItem with `source: "specs"` and `source_detail: "specs/<dir>/spec.md"`

**Deduplication**: If a spec's feature is already represented by a CHANGELOG entry, mark the spec entry as `(confirming CHANGELOG)` rather than creating a duplicate.

## Source 3: Code Diff Analysis

**Commands**:
```bash
# Structural changes (added/deleted/renamed files)
git diff --stat <baseline-sha>..HEAD

# Commit volume and frequency
git log --oneline --since="<baseline-date>"

# Detailed file-level changes
git diff --name-status <baseline-sha>..HEAD
```

**Processing rules**:
1. **New files** (`A` status in `--name-status`): Flag files in monitored directories
2. **Deleted files** (`D` status): Flag as potential removed functionality
3. **Renamed files** (`R` status): Flag as potential changed behavior
4. **High-churn files** (>5 commits or >100 lines changed): Flag for review

**Monitored directories** (high-documentation-impact):
| Directory | Documentation Impact |
|---|---|
| `backend/src/api/` | `docs/api-reference.md` |
| `backend/src/services/` | `docs/architecture.md`, `docs/agent-pipeline.md` |
| `backend/src/config.py` | `docs/configuration.md` |
| `backend/src/migrations/` | `docs/architecture.md` |
| `frontend/src/pages/` | README (UX flow), `docs/project-structure.md` |
| `frontend/src/components/` | `docs/project-structure.md` |
| `docker-compose.yml` | `docs/architecture.md`, `docs/setup.md` |
| `pyproject.toml` | `docs/setup.md`, `docs/testing.md` |
| `package.json` | `docs/setup.md`, `docs/testing.md` |

**Deduplication**: If a code change is already captured by CHANGELOG or spec entries, mark it as `(confirming CHANGELOG/spec)`.

## Output: Change Manifest

The final Change Manifest merges all three sources into the five-category structure defined in FR-005. The document includes:

1. **Header**: Refresh window (date range, SHA range), sources analyzed
2. **Categories**: Five sections, each containing ManifestItems
3. **Footer**: Summary counts per category, deduplication notes, uncategorized items (if any)

**Completeness check**: The manifest should be cross-referenced against `git log --oneline` for the period. Every user-visible commit should map to at least one manifest item (SC-002).
