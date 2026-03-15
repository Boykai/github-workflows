# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: `001-bug-basher` | **Date**: 2026-03-15 | **Plan**: [plan.md](plan.md)

## Entities

### BugReportEntry

Represents a single identified bug or issue found during the code review.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `number` | Integer | Sequential, starts at 1 | Unique identifier within the summary table |
| `file` | String | Valid file path relative to repo root | Path to the file containing the bug |
| `lines` | String | Format: `N` or `N-M` | Line number(s) where the bug is located |
| `category` | Enum | One of: Security, Runtime, Logic, Test Quality, Code Quality | Bug classification per priority order |
| `description` | String | Non-empty, human-readable | Clear description of what the bug is and why it matters |
| `status` | Enum | One of: `✅ Fixed`, `⚠️ Flagged (TODO)` | Resolution status |

**Validation Rules**:
- `number` must be unique and sequential across the entire summary table.
- `file` must reference an actual file in the repository.
- `category` must be exactly one of the five defined categories — bugs that span categories are classified under the highest-priority applicable category.
- `status` of `✅ Fixed` requires: source code fix committed, affected tests updated, at least one new regression test added, test suite passes.
- `status` of `⚠️ Flagged (TODO)` requires: `# TODO(bug-bash):` comment placed at the relevant code location describing the issue, options, and rationale for deferral.

---

### SummaryTable

The consolidated output artifact of the entire bug bash. Contains all BugReportEntry records.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `entries` | List[BugReportEntry] | Ordered by `number` | All bugs found during the review |
| `total_fixed` | Integer | Count of entries with status `✅ Fixed` | Total bugs directly resolved |
| `total_flagged` | Integer | Count of entries with status `⚠️ Flagged (TODO)` | Total ambiguous issues deferred |

**Validation Rules**:
- Files with no bugs found must NOT appear in the table (FR-015).
- `total_fixed + total_flagged` must equal `len(entries)`.
- The table is rendered as a markdown table with the exact column headers: `#`, `File`, `Line(s)`, `Category`, `Description`, `Status`.

---

### RegressionTest

Represents a test added to guard against a specific bug reintroduction.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `bug_number` | Integer | References BugReportEntry.number | The bug this test guards against |
| `test_file` | String | Valid test file path | Location of the new regression test |
| `test_name` | String | Follows project naming conventions | Name of the test function/method |
| `assertion` | String | Non-empty description | What the test asserts to catch the bug |

**Validation Rules**:
- Every BugReportEntry with status `✅ Fixed` must have at least one associated RegressionTest.
- The test must fail if the bug is reintroduced (i.e., it must not be vacuous).
- Backend tests follow pytest naming: `test_bug_NNN_<descriptive_name>` in `solune/backend/tests/unit/` or `solune/backend/tests/integration/`.
- Frontend tests follow Vitest naming: `describe/it` blocks in `*.test.ts` or `*.test.tsx` files.

---

### TODOFlag

Represents an ambiguous bug flagged for human review.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `bug_number` | Integer | References BugReportEntry.number | The bug this TODO references |
| `file` | String | Same as BugReportEntry.file | File where the comment is placed |
| `line` | Integer | Line number of the comment | Where the `# TODO(bug-bash):` comment is placed |
| `comment_text` | String | Non-empty | Full text of the TODO comment including issue description, options, and rationale |

**Validation Rules**:
- The comment must follow the exact format: `# TODO(bug-bash): <description>`.
- For multi-file bugs, the TODO is placed in the most relevant file with cross-references to other affected files.
- Every BugReportEntry with status `⚠️ Flagged (TODO)` must have exactly one associated TODOFlag.

## Relationships

```text
SummaryTable 1──* BugReportEntry
BugReportEntry (status=Fixed) 1──+ RegressionTest    (one-to-many, min 1)
BugReportEntry (status=Flagged) 1──1 TODOFlag         (one-to-one)
```

## State Transitions

### BugReportEntry Status

```text
[Discovered] ──(obvious fix)──→ [✅ Fixed]
[Discovered] ──(ambiguous/trade-off)──→ [⚠️ Flagged (TODO)]
```

There are no transitions between Fixed and Flagged. Once classified, a bug's status is final for the scope of this bug bash. A human reviewer may later decide to fix a Flagged item in a subsequent PR.

## Category Priority Order

The five categories form a strict priority ordering for triage:

```text
1. Security Vulnerabilities  (highest priority — addressed first)
2. Runtime Errors
3. Logic Bugs
4. Test Gaps & Test Quality
5. Code Quality Issues        (lowest priority — addressed last)
```

Per SC-009, no lower-priority fix may be committed while a known higher-priority issue remains unaddressed.
