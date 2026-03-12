# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: 037-bug-basher | **Date**: 2026-03-12

## Entities

### BugReportEntry

Represents a single discovered bug in the codebase. Each entry corresponds to one row in the final summary table.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `number` | `int` | Sequential identifier (1, 2, 3, ...) | Auto-incremented, unique |
| `file_path` | `str` | Relative path from repo root (e.g., `backend/src/services/database.py`) | Must be an existing file in the repository |
| `line_range` | `str` | Line number or range (e.g., `42` or `42-45`) | Must be valid line numbers within the file |
| `category` | `enum` | Bug category | One of: `Security`, `Runtime`, `Logic`, `Test Quality`, `Code Quality` |
| `description` | `str` | Clear description of the bug, including what is wrong and why it is a bug | Non-empty, human-readable |
| `status` | `enum` | Resolution status | One of: `✅ Fixed`, `⚠️ Flagged (TODO)` |
| `commit_ref` | `str \| None` | Git commit SHA or message reference for the fix | Required when status is `✅ Fixed`; `None` for flagged items |
| `regression_test` | `str \| None` | Path and name of the regression test added | Required when status is `✅ Fixed`; `None` for flagged items |

**State transitions**:
- `discovered` → `fixed`: Bug is obvious, fix is applied, regression test added, tests pass
- `discovered` → `flagged`: Bug is ambiguous or involves trade-offs, `TODO(bug-bash)` comment added
- `fixed` → `reverted`: Fix causes test failures, must iterate

### RegressionTest

Represents a test specifically added to guard against reintroduction of a fixed bug.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `test_file` | `str` | Path to the test file (e.g., `backend/tests/unit/test_database.py`) | Must follow existing naming convention |
| `test_name` | `str` | Full test function name (e.g., `test_sql_injection_in_query_param`) | Must be descriptive of the bug it guards |
| `bug_entry_number` | `int` | Reference to the BugReportEntry this test guards | Must match a valid BugReportEntry number |
| `framework` | `enum` | Testing framework used | One of: `pytest`, `vitest` |
| `validates` | `str` | Description of what this test specifically validates | Non-empty, describes the failure mode it catches |

### TodoBugBashComment

Represents an inline code comment marking an ambiguous issue for human review.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `file_path` | `str` | Path to the file containing the comment | Must be an existing file |
| `line_number` | `int` | Line number where the comment is placed | Must be valid |
| `issue_description` | `str` | What the potential bug or concern is | Non-empty |
| `options` | `list[str]` | Available resolution approaches | At least 2 options |
| `rationale` | `str` | Why this needs human decision rather than automated fix | Non-empty |
| `bug_entry_number` | `int` | Reference to the BugReportEntry | Must match a valid BugReportEntry |

**Comment format**:
```python
# TODO(bug-bash): {issue_description}
# Options: {option_1} | {option_2} | ...
# Needs human decision because: {rationale}
```

### SummaryTable

The consolidated output artifact listing all BugReportEntry records. Generated as a Markdown table in the final PR comment.

| Field | Type | Description |
|-------|------|-------------|
| `entries` | `list[BugReportEntry]` | All discovered bugs, ordered by number |
| `total_fixed` | `int` | Count of entries with status `✅ Fixed` |
| `total_flagged` | `int` | Count of entries with status `⚠️ Flagged (TODO)` |
| `files_reviewed` | `int` | Total number of files audited |
| `files_with_bugs` | `int` | Number of files where at least one bug was found |
| `files_clean` | `int` | Number of files with no bugs (omitted from table per FR-014) |

## Relationships

```text
SummaryTable ──contains──▶ BugReportEntry (1:N)
BugReportEntry ──guarded_by──▶ RegressionTest (1:1, when status = Fixed)
BugReportEntry ──documented_by──▶ TodoBugBashComment (1:1, when status = Flagged)
BugReportEntry ──references──▶ SourceFile (N:1, multiple bugs can be in one file)
RegressionTest ──located_in──▶ TestFile (N:1, multiple tests can be in one test file)
```

## Category Priority Mapping

| Priority | Category | Risk Level | Fix Approach |
|----------|----------|------------|--------------|
| P1 | Security | Critical | Immediate fix + regression test |
| P2 | Runtime | High | Fix + regression test |
| P3 | Logic | Medium | Fix + regression test |
| P4 | Test Quality | Low-Medium | Test improvement (may not need separate regression test) |
| P5 | Code Quality | Low | Cleanup or TODO flag |

## Output Format

The final summary table follows this exact format (per spec):

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```

- Files with no bugs are omitted entirely (FR-014)
- Entries are ordered by discovery sequence (number field)
- Each entry maps 1:1 to either a code fix + regression test OR a TODO comment
