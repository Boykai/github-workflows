# Contract: Bug Bash Summary Table

**Feature**: `031-bug-basher` | **Date**: 2026-03-08

## Output Format

The bug bash produces a single summary table as its primary output artifact. This table is included in the final PR comment/description.

### Table Schema

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```

### Column Definitions

| Column | Type | Format | Required |
|--------|------|--------|----------|
| `#` | Integer | Sequential, starting at 1 | Yes |
| `File` | String | Relative path from repo root, in backticks | Yes |
| `Line(s)` | String | Single line `N` or range `N-M` | Yes |
| `Category` | Enum | One of: `Security`, `Runtime`, `Logic`, `Test Quality`, `Code Quality` | Yes |
| `Description` | String | Concise bug description | Yes |
| `Status` | Enum | `✅ Fixed` or `⚠️ Flagged (TODO)` | Yes |

### Ordering Rules

1. Entries are grouped by category in priority order: Security → Runtime → Logic → Test Quality → Code Quality
2. Within each category, entries are ordered by file path (alphabetical)
3. Within each file, entries are ordered by line number (ascending)

### Status Definitions

- **✅ Fixed**: Bug was resolved in source code, affected tests updated, at least one new regression test added, full test suite passing
- **⚠️ Flagged (TODO)**: Ambiguous issue left as `TODO(bug-bash):` comment in source code for human review; no code change made

### Exclusions

- Files with no bugs found are **not** included in the table
- Pre-existing `TODO` comments (not created by this bug bash) are **not** included
- Code style preferences (formatting, naming) that are not bugs are **not** included

### Commit Message Format

Each bug fix commit follows this format:

```text
fix(<category>): <short description>

Bug: <what the bug was>
Why: <why it's a bug>
Fix: <how the fix resolves it>
```

Where `<category>` is one of: `security`, `runtime`, `logic`, `test-quality`, `code-quality`.

### Validation Contract

Before the summary table is finalized:

1. `pytest` passes with zero failures (including all new regression tests)
2. `ruff check` passes with zero errors (backend)
3. `ESLint` passes with zero errors (frontend)
4. `tsc --noEmit` passes with zero errors (frontend)
5. `vitest run` passes with zero failures (frontend)
6. Every `✅ Fixed` entry has a corresponding regression test
7. Every `⚠️ Flagged (TODO)` entry has a corresponding `TODO(bug-bash):` comment in source
