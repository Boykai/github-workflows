# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-26 | **Phase**: 1 (Design & Contracts)

## Entities

### Bug Report Entry

Represents a single identified bug in the codebase.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `number` | integer | Sequential bug identifier | Auto-increment, starts at 1 |
| `file` | string | Relative file path from repo root | Must be a valid file in the repository |
| `lines` | string | Line number(s) affected | Single line (e.g., `42`) or range (e.g., `42-45`) |
| `category` | BugCategory | Classification of the bug | One of the 5 defined categories |
| `description` | string | Human-readable description of the bug | Clear, concise explanation of what's wrong |
| `status` | ResolutionStatus | Current resolution state | `Fixed` or `Flagged` |
| `commit_sha` | string (optional) | Git commit SHA of the fix | Present only for `Fixed` status |
| `regression_test` | string (optional) | Path to the regression test file/function | Present only for `Fixed` status |
| `todo_comment` | string (optional) | Content of the TODO(bug-bash) comment | Present only for `Flagged` status |

**Validation Rules**:
- `file` must reference an existing file at the time of review
- `lines` must be valid line numbers within the file
- `Fixed` entries must have both `commit_sha` and `regression_test`
- `Flagged` entries must have `todo_comment` with issue description, options, and rationale

---

### Bug Category (Enum)

Priority-ordered classification of bugs. Review order follows priority (1 = highest).

| Value | Priority | Label | Scope |
|-------|----------|-------|-------|
| `security` | 1 | Security Vulnerabilities | Auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation |
| `runtime` | 2 | Runtime Errors | Unhandled exceptions, race conditions, null references, missing imports, type errors, resource leaks |
| `logic` | 3 | Logic Bugs | Incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow |
| `test_quality` | 4 | Test Gaps & Quality | Untested paths, tests passing for wrong reasons, mock leaks, assertions that never fail, missing edge cases |
| `code_quality` | 5 | Code Quality Issues | Dead code, unreachable branches, duplicated logic, hardcoded values, silent failures |

**State Transitions**: Categories are processed sequentially (1 → 2 → 3 → 4 → 5). All bugs within a category are resolved before moving to the next category.

---

### Resolution Status (Enum)

| Value | Symbol | Description | Required Fields |
|-------|--------|-------------|-----------------|
| `Fixed` | ✅ | Bug was resolved, tests added, all passing | `commit_sha`, `regression_test` |
| `Flagged` | ⚠️ | Ambiguous issue left as TODO for human review | `todo_comment` |

**Transition Rules**:
- A bug starts as identified (no status)
- If the fix is clear and safe → transition to `Fixed`
- If the fix is ambiguous, requires API changes, or involves trade-offs → transition to `Flagged`
- A `Flagged` bug cannot become `Fixed` within this bug bash (requires human decision)

---

### Summary Table

The final output artifact aggregating all Bug Report Entries.

| Field | Type | Description |
|-------|------|-------------|
| `entries` | list[BugReportEntry] | All identified bugs, ordered by `number` |
| `total_fixed` | integer | Count of entries with `Fixed` status |
| `total_flagged` | integer | Count of entries with `Flagged` status |
| `categories_reviewed` | list[BugCategory] | Categories that were fully reviewed |

**Validation Rules**:
- Every identified bug must appear in the table (FR-010, SC-006)
- Files with no bugs are omitted (FR-011)
- Table is ordered by sequential `number`, not by category or file
- `categories_reviewed` should include all 5 categories when review is complete (SC-001)

---

### TODO Flag (Structured Comment)

A standardized comment format for ambiguous issues.

```python
# TODO(bug-bash): <brief description>
# Options: <option A> | <option B> | ...
# Rationale: <why this needs human decision>
```

**Validation Rules**:
- Must use exact prefix `# TODO(bug-bash):` (or `// TODO(bug-bash):` for TypeScript)
- Must include at least two options
- Must include rationale explaining why automated fix was not applied
- Must appear at the exact line(s) where the issue exists

## Relationships

```
Summary Table 1──* Bug Report Entry
Bug Report Entry *──1 Bug Category
Bug Report Entry *──1 Resolution Status
Bug Report Entry 0..1──1 TODO Flag  (only when status = Flagged)
```

## Notes

- This data model is conceptual — it describes the structure of the output artifacts (summary table, TODO comments), not a database schema or API model.
- The Bug Report Entry fields map directly to columns in the summary table specified in the issue requirements.
- No new code entities, database tables, or API models are created as part of this feature.
