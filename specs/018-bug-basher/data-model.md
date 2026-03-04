# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: `018-bug-basher` | **Date**: 2026-03-04

## Entities

### Bug Report Entry (process artifact — summary table row)

Represents a single identified issue found during the bug bash review. This is a documentation entity, not a runtime data model — it exists as a row in the final summary table.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `number` | int | sequential, starting at 1 | Row number in the summary table |
| `file` | string | relative path from repo root | File where the bug was found (e.g., `backend/src/api/chat.py`) |
| `lines` | string | line number or range | Affected line(s) (e.g., `42-45` or `100`) |
| `category` | BugCategory | required | One of the five audit categories |
| `description` | string | required, human-readable | What the bug is and why it matters |
| `status` | ResolutionStatus | required | Whether the bug was fixed or flagged |

### BugCategory (enum)

Priority-ordered classification of bugs found during the review.

| Value | Priority | Description |
|-------|----------|-------------|
| `Security` | P1 | Auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation |
| `Runtime` | P2 | Unhandled exceptions, race conditions, null references, missing imports, type errors, resource leaks |
| `Logic` | P3 | Incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow |
| `Test Quality` | P4 | Untested code paths, tests passing for wrong reason, mock leaks, assertions that never fail |
| `Code Quality` | P5 | Dead code, unreachable branches, duplicated logic, hardcoded values, silent failures |

### ResolutionStatus (enum)

| Value | Symbol | Description |
|-------|--------|-------------|
| `Fixed` | ✅ | Bug was resolved, tests added, all passing |
| `Flagged` | ⚠️ | Ambiguous issue left as `# TODO(bug-bash):` comment for human review |

### TODO Flag (code artifact — structured comment)

A structured comment placed directly in source code for ambiguous issues that require human judgment.

| Field | Type | Description |
|-------|------|-------------|
| `marker` | literal | Always `# TODO(bug-bash):` (Python) or `// TODO(bug-bash):` (TypeScript) |
| `description` | string | What the issue is |
| `options` | string | Available resolution approaches |
| `rationale` | string | Why this needs a human decision |

**Format example (Python)**:
```python
# TODO(bug-bash): <description>
# Options: <option A> vs <option B>
# Rationale: <why this is ambiguous>
```

**Format example (TypeScript)**:
```typescript
// TODO(bug-bash): <description>
// Options: <option A> vs <option B>
// Rationale: <why this is ambiguous>
```

### Regression Test (code artifact — test function)

A test function specifically written to validate a bug fix. Linked to a specific Bug Report Entry.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Descriptive test function name indicating what bug is covered |
| `location` | string | File path where the test is added |
| `bug_ref` | int | References the Bug Report Entry number |
| `assertion` | string | What the test verifies (should fail if bug is reintroduced) |

### Commit Message (process artifact)

Structured commit message for each bug fix.

| Field | Type | Description |
|-------|------|-------------|
| `type` | literal | Always `fix` |
| `scope` | BugCategory | Lowercase category name (e.g., `security`, `runtime`, `logic`) |
| `subject` | string | What was fixed |
| `body` | string | Why it's a bug and how the fix resolves it |

**Format**: `fix(<scope>): <subject>`

## Relationships

```text
Bug Report Entry ──── 1:1 ──── Regression Test (for Fixed status)
      │
      │ file + lines
      ▼
  Source Code Location ──── 0..1 ──── TODO Flag (for Flagged status)
      │
      │ commit
      ▼
  Commit Message (for Fixed status only)
```

## State Transitions

```text
                    ┌─────────────────┐
   Reviewer finds   │   Identified    │
   potential issue   │  (under review) │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              Clear bug          Ambiguous
                    │                 │
                    ▼                 ▼
             ┌────────────┐   ┌─────────────┐
             │   Fixed    │   │   Flagged    │
             │ ✅ status  │   │ ⚠️ status   │
             └─────┬──────┘   └──────┬──────┘
                   │                  │
                   ▼                  ▼
            Regression test    TODO comment
            added + passing    added in source
                   │
                   ▼
            Commit with
            structured message
```

## Validation Rules

- **File path**: Must be a valid relative path from the repository root to an existing file
- **Line numbers**: Must reference actual lines in the file at the time of review
- **Category**: Must be one of the five defined categories — no custom categories
- **Description**: Must explain both what the bug is and why it is a bug
- **TODO format**: Must start with `# TODO(bug-bash):` (Python) or `// TODO(bug-bash):` (TypeScript)
- **Regression test**: Must fail when the fix is reverted (verified by the reviewer)
- **Commit message**: Must include what, why, and how — no one-word descriptions
- **Summary table**: Must include every finding — no omissions. Files with no bugs are excluded (FR-016)
