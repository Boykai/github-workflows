# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher
**Date**: 2026-03-22
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Entities

### BugReportEntry

Represents a single identified issue discovered during the bug-bash audit. Each entry appears as one row in the final summary table. Tracks the full lifecycle from discovery through resolution or flagging.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sequence` | `integer` | Yes | Sequential number (1-based) in the summary table, ordered by discovery |
| `file` | `string` | Yes | Relative file path from repository root (e.g., `solune/backend/src/api/pipelines.py`) |
| `lines` | `string` | Yes | Line number or range where the issue exists (e.g., `42` or `42-45`) |
| `category` | `BugCategory` | Yes | One of the five priority-ordered bug categories |
| `description` | `string` | Yes | Clear, concise description of the bug and how the fix resolves it |
| `status` | `BugStatus` | Yes | Whether the bug was fixed or flagged for human review |

#### BugCategory (enum)

| Value | Priority | Description |
|-------|----------|-------------|
| `Security` | P1 | Auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation |
| `Runtime` | P1 | Unhandled exceptions, race conditions, null/None references, missing imports, type errors, resource leaks |
| `Logic` | P2 | Incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow |
| `Test Quality` | P2 | Untested code paths, tests that pass for wrong reason, mock leaks, tautological assertions |
| `Code Quality` | P3 | Dead code, unreachable branches, duplicated logic, hardcoded values, silent failures |

#### BugStatus (enum)

| Value | Indicator | Description |
|-------|-----------|-------------|
| `Fixed` | ✅ Fixed | Bug was resolved in source code, affected tests updated, at least one new regression test added, all tests passing |
| `Flagged` | ⚠️ Flagged (TODO) | Ambiguous issue left as `TODO(bug-bash)` comment for human review — no source code changed |

#### Validation Rules

- `file` must be a valid relative path to an existing file in the repository
- `lines` must reference actual line numbers in the file at the time of the fix
- `category` must be exactly one of the five defined categories
- `status` must be either `Fixed` or `Flagged`
- For `Fixed` status: a corresponding regression test must exist
- For `Flagged` status: a `TODO(bug-bash)` comment must exist at the specified file and line

---

### RegressionTest

Represents a test specifically added to validate a bug fix. Linked to its corresponding BugReportEntry. Designed to fail if the bug were reintroduced.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_file` | `string` | Yes | Path to the test file containing the regression test |
| `test_name` | `string` | Yes | Name of the test function or test case |
| `bug_entry` | `BugReportEntry` | Yes | The bug report entry this test validates |
| `assertion_type` | `string` | Yes | What the test asserts (e.g., "raises ValueError", "returns None", "does not leak mock") |

#### Validation Rules

- `test_file` must follow existing naming conventions (`test_*.py` for Python, `*.test.tsx` or `*.test.ts` for TypeScript)
- `test_name` must be descriptive and indicate what behavior is being validated
- The test must fail if the fix is reverted (i.e., it genuinely validates the fix)

---

### TodoBugBashComment

Represents an in-code annotation for an ambiguous issue that requires human decision. Placed at the exact location of the identified issue.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `string` | Yes | File path where the comment is placed |
| `line` | `integer` | Yes | Line number where the comment is placed |
| `description` | `string` | Yes | Clear description of the issue |
| `options` | `string[]` | Yes | Available resolution approaches |
| `rationale` | `string` | Yes | Why human decision is needed (not a clear-cut fix) |

#### Format

**Python**:
```python
# TODO(bug-bash): {description} | Options: {option1}, {option2} | Reason: {rationale}
```

**TypeScript**:
```typescript
// TODO(bug-bash): {description} | Options: {option1}, {option2} | Reason: {rationale}
```

#### Validation Rules

- Comment must start with `TODO(bug-bash):` prefix (machine-searchable)
- Must include at least two options (otherwise it's a clear fix, not ambiguous)
- Must include a rationale explaining why this needs human judgment
- No source code changes accompany a `TODO(bug-bash)` comment

---

### SummaryTable

The final deliverable listing all identified issues. One instance per bug-bash execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entries` | `BugReportEntry[]` | Yes | All identified issues, ordered by discovery sequence |
| `total_fixed` | `integer` | Yes | Count of entries with status `Fixed` |
| `total_flagged` | `integer` | Yes | Count of entries with status `Flagged` |
| `categories_covered` | `BugCategory[]` | Yes | Which categories had findings |

#### Validation Rules

- `entries` must include every identified issue — no omissions
- Files with no bugs must NOT appear in the table (FR-015)
- `total_fixed + total_flagged` must equal `len(entries)`
- Every `Fixed` entry must have a corresponding commit and regression test
- Every `Flagged` entry must have a corresponding `TODO(bug-bash)` comment in the codebase

---

## Relationships

```text
┌───────────────┐
│ SummaryTable  │──contains──▶ BugReportEntry[] (ordered by sequence)
└───────────────┘
        │
        ├── Fixed entries ──link to──▶ RegressionTest (1:1 minimum)
        │                              └── Lives in existing test file
        │
        └── Flagged entries ──link to──▶ TodoBugBashComment (1:1)
                                         └── Lives in source file at issue location
```

## State Transitions

### Bug Discovery & Resolution Flow

```text
File Audit
  │
  ├── Issue found
  │     │
  │     ├── Clear fix? ──Yes──▶ Fix source code
  │     │                        ├── Update affected tests
  │     │                        ├── Add regression test
  │     │                        ├── Verify all tests pass
  │     │                        └── Create BugReportEntry (status: Fixed)
  │     │
  │     └── Ambiguous? ──Yes──▶ Add TODO(bug-bash) comment
  │                              └── Create BugReportEntry (status: Flagged)
  │
  └── No issues ──▶ Skip file (FR-015)

After all files audited:
  │
  ├── Run full validation pipeline
  │     ├── pytest --timeout=60
  │     ├── ruff check src tests
  │     ├── pyright src
  │     ├── bandit -r src/
  │     ├── npm run test
  │     ├── npm run lint
  │     ├── npm run type-check
  │     └── npm run build
  │
  └── Generate SummaryTable from all BugReportEntries
```

### Category Priority Flow

```text
Phase 1: Security (P1) ──complete──▶ Phase 2: Runtime (P1)
                                       │
                                       ├──complete──▶ Phase 3: Logic (P2)
                                       │               │
                                       │               ├──complete──▶ Phase 4: Tests (P2)
                                       │               │               │
                                       │               │               └──complete──▶ Phase 5: Quality (P3)
                                       │               │                               │
                                       │               │                               └──complete──▶ Phase 6: Validation
```
