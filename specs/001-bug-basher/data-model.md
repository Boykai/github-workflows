# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-04

## Entities

### BugReportEntry

Represents a single identified bug in the codebase audit.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| number | integer | Sequential identifier (1-based) | Must be unique, auto-incremented |
| file_path | string | Relative path from repository root | Must be a valid file in the repository |
| line_numbers | string | Line number or range (e.g., "42" or "42-45") | Must reference valid lines in the file |
| category | enum | Bug category from priority list | One of: Security, Runtime, Logic, Test Quality, Code Quality |
| description | string | Clear description of the bug | Non-empty; must explain what, why, and impact |
| status | enum | Resolution status | One of: "✅ Fixed", "⚠️ Flagged (TODO)" |

**Relationships**:
- Each BugReportEntry with status "✅ Fixed" has exactly one BugFix.
- Each BugReportEntry with status "⚠️ Flagged (TODO)" has exactly one TODOFlag.

---

### BugFix

Represents a source code change that resolves an identified bug.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| bug_number | integer | Reference to BugReportEntry.number | Must reference a valid entry with "✅ Fixed" status |
| source_change | diff | The minimal code change applied | Must change only the lines necessary to fix the bug |
| updated_tests | list[string] | Paths to existing tests modified by the fix | May be empty if no existing tests are affected |
| regression_test | string | Path to the new regression test | Must be non-empty; at least one per fix (FR-004) |
| commit_message | string | Descriptive commit message | Must explain: what, why, how (FR-005) |

**Validation Rules**:
- `source_change` must not alter public API surface (FR-010)
- `source_change` must not add new dependencies (FR-011)
- `source_change` must preserve existing code style (FR-012)
- `source_change` must be minimal and focused (FR-013)
- `regression_test` must fail if the bug reoccurs (SC-008)

---

### TODOFlag

Represents an ambiguous issue deferred for human review.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| bug_number | integer | Reference to BugReportEntry.number | Must reference a valid entry with "⚠️ Flagged (TODO)" status |
| comment_text | string | The `TODO(bug-bash)` comment added to source | Must include: issue description, options, rationale for deferring |
| file_path | string | File where the comment was added | Must match the BugReportEntry.file_path |
| line_number | integer | Line where the comment was inserted | Must be at or near the relevant code location |

**Validation Rules**:
- Comment format: `# TODO(bug-bash): <description>` (Python) or `// TODO(bug-bash): <description>` (TypeScript)
- Must describe the issue, the options considered, and why human decision is needed (FR-006)

---

### SummaryTable

The consolidated output artifact listing all BugReportEntries.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| entries | list[BugReportEntry] | All bugs found during the audit | Ordered by sequential number |
| total_fixed | integer | Count of entries with "✅ Fixed" status | Derived from entries |
| total_flagged | integer | Count of entries with "⚠️ Flagged (TODO)" status | Derived from entries |

**Validation Rules**:
- Must not include files with no bugs (FR-015)
- Must include every bug found (SC-007)
- Table format matches spec output template

---

## State Transitions

### BugReportEntry Lifecycle

```
[Identified] → [Assessed]
                  ├─→ (obvious fix) → [Fixed] → [Tested] → [Committed] → ✅ Fixed
                  └─→ (ambiguous)  → [Flagged] → [TODO Added] → ⚠️ Flagged (TODO)
```

**Transition Rules**:
1. **Identified → Assessed**: Bug is found during file audit; category is assigned
2. **Assessed → Fixed**: Bug is obvious; code change applied (must be minimal)
3. **Fixed → Tested**: Regression test added and passing; existing tests updated if affected
4. **Tested → Committed**: Full test suite passes; linting passes; commit message written
5. **Assessed → Flagged**: Bug is ambiguous, requires API change, or requires new dependency
6. **Flagged → TODO Added**: `TODO(bug-bash)` comment added to source code at relevant location

---

## Category Priority Enum

```
1. Security        — auth bypasses, injection, exposed secrets, insecure defaults, input validation
2. Runtime         — unhandled exceptions, race conditions, null refs, missing imports, type errors, leaks
3. Logic           — state transitions, wrong API calls, off-by-one, data inconsistencies, control flow
4. Test Quality    — untested paths, wrong-reason passes, mock leaks, never-fail assertions, missing edge cases
5. Code Quality    — dead code, unreachable branches, duplication, hardcoded values, silent failures
```
