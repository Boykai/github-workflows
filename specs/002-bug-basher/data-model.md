# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: 002-bug-basher
**Date**: 2026-03-24
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Entities

### BugFinding

Represents a single bug or issue identified during the codebase review. Used to track findings across all five review categories and generate the summary report.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `integer` | Yes | Sequential finding number (1, 2, 3, ...) |
| `file` | `string` | Yes | Relative file path from repository root (e.g., `solune/backend/src/api/auth.py`) |
| `lines` | `string` | Yes | Line number or range (e.g., `42`, `42-45`) |
| `category` | `BugCategory` | Yes | One of: Security, Runtime, Logic, Test Quality, Code Quality |
| `description` | `string` | Yes | Clear, concise description of the bug and why it is a bug |
| `status` | `FixStatus` | Yes | Either "Fixed" or "Flagged (TODO)" |
| `commit` | `string \| null` | No | Commit hash of the fix (null for flagged items) |
| `regression_test` | `string \| null` | No | Test function name or file path for the regression test (null for flagged items) |

#### Validation Rules

- `number` must be unique and sequential starting from 1
- `file` must be a valid path relative to repository root
- `lines` must match pattern `\d+(-\d+)?`
- `description` must be non-empty
- If `status` is "Fixed", both `commit` and `regression_test` must be non-null
- If `status` is "Flagged (TODO)", `commit` and `regression_test` must be null

---

### BugCategory (enum)

Classification of the bug finding, matching the five review categories defined in the spec.

| Value | Priority | Description |
|-------|----------|-------------|
| `Security` | P1 | Auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation |
| `Runtime` | P2 | Unhandled exceptions, race conditions, null references, missing imports, type errors, resource leaks |
| `Logic` | P3 (within P2 phase) | Incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow |
| `Test Quality` | P3 | Untested paths, tests passing for wrong reason, mock leaks, dead assertions, missing edge cases |
| `Code Quality` | P4 | Dead code, unreachable branches, duplicated logic, hardcoded values, missing error messages, silent failures |

---

### FixStatus (enum)

Resolution status of a bug finding.

| Value | Symbol | Description |
|-------|--------|-------------|
| `Fixed` | ✅ | Bug was resolved, regression test added, all tests passing |
| `Flagged (TODO)` | ⚠️ | Ambiguous issue left as `TODO(bug-bash)` comment for human review |

---

### SummaryReport

The final output artifact listing all bug findings from the review.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `findings` | `BugFinding[]` | Yes | Ordered list of all bug findings |
| `total_fixed` | `integer` | Yes | Count of findings with status "Fixed" |
| `total_flagged` | `integer` | Yes | Count of findings with status "Flagged (TODO)" |
| `total_files_reviewed` | `integer` | Yes | Total files reviewed across the repository |
| `test_suite_status` | `string` | Yes | "PASS" or "FAIL" — final test suite status |

#### Validation Rules

- `total_fixed + total_flagged` must equal `len(findings)`
- `test_suite_status` must be "PASS" for the report to be considered complete
- Files with no bugs must NOT appear in the findings list (FR-012)

---

### TODOComment

Format for `TODO(bug-bash)` comments added to source code for ambiguous findings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `marker` | `string` | Yes | Always `TODO(bug-bash):` |
| `issue_description` | `string` | Yes | What the potential issue is |
| `options` | `string` | Yes | Available approaches to resolve |
| `reasoning` | `string` | Yes | Why this needs a human decision |

#### Format Example

```python
# TODO(bug-bash): Potential race condition in concurrent webhook processing.
# Options: (1) Add database-level locking, (2) Use queue-based processing.
# Needs human decision: Both options have performance trade-offs that depend
# on expected webhook volume.
```

---

## Relationships

```text
SummaryReport
    │
    └── contains ──▶ BugFinding[] (ordered by number)
                         │
                         ├── has ──▶ BugCategory (enum)
                         │
                         └── has ──▶ FixStatus (enum)
                                        │
                                        ├── Fixed ──▶ linked to commit + regression_test
                                        │
                                        └── Flagged ──▶ linked to TODOComment in source
```

## State Transitions

### Bug Finding Lifecycle

```text
File under review
    │
    ├─ Issue identified ──▶ Is it clear/obvious?
    │                          │
    │                          ├─ YES ──▶ Fix applied ──▶ Test added ──▶ Tests pass?
    │                          │                                            │
    │                          │                                            ├─ YES ──▶ BugFinding(status=Fixed)
    │                          │                                            │
    │                          │                                            └─ NO ──▶ Iterate on fix
    │                          │
    │                          └─ NO (ambiguous) ──▶ Add TODO(bug-bash) comment
    │                                                   │
    │                                                   └──▶ BugFinding(status=Flagged)
    │
    └─ No issue found ──▶ Skip file (not in report)
```

### Review Phase Flow

```text
Phase 1: Security (P1)
    │
    ├─ Fix all clear security bugs ──▶ Run test suite ──▶ All pass?
    │                                                        │
    │                                                        ├─ YES ──▶ Commit phase
    │                                                        └─ NO ──▶ Iterate
    │
    ▼
Phase 2: Runtime + Logic (P2)
    │
    ├─ Fix all clear runtime/logic bugs ──▶ Run test suite ──▶ All pass?
    │                                                             │
    │                                                             ├─ YES ──▶ Commit phase
    │                                                             └─ NO ──▶ Iterate
    │
    ▼
Phase 3: Test Quality (P3)
    │
    ├─ Fix test quality issues ──▶ Run test suite ──▶ All pass?
    │                                                    │
    │                                                    ├─ YES ──▶ Commit phase
    │                                                    └─ NO ──▶ Iterate
    │
    ▼
Phase 4: Code Quality (P4)
    │
    ├─ Fix code quality issues ──▶ Run linters + tests ──▶ All pass?
    │                                                          │
    │                                                          ├─ YES ──▶ Commit phase
    │                                                          └─ NO ──▶ Iterate
    │
    ▼
Phase 5: Summary Report (P5)
    │
    └─ Compile SummaryReport from all phases ──▶ Final validation ──▶ Done
```
