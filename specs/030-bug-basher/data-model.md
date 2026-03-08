# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: `030-bug-basher` | **Date**: 2026-03-08

## Overview

This feature does not introduce new database entities or API models. It is a code review and bug fix effort. The "data model" for this feature describes the logical entities used to track and report findings during the review process.

## Entities

### Bug Report Entry

Represents a single identified issue in the codebase. Used in the summary table output.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | Integer | Sequential bug number | Auto-increment, starts at 1 |
| `file` | String | Relative file path from repo root | Must be a real file in the repository |
| `lines` | String | Line number or range | Format: `N` or `N-M` |
| `category` | Enum | Bug category | One of: Security, Runtime, Logic, Test Quality, Code Quality |
| `description` | String | Human-readable description of the bug | Non-empty, concise |
| `status` | Enum | Resolution status | One of: `✅ Fixed`, `⚠️ Flagged (TODO)` |

**Validation rules**:
- `file` must exist in the repository at the time of the report
- `lines` must reference valid line numbers in the file
- `category` must be one of the five defined categories
- `description` must explain what the bug is and why it matters
- `status` is `✅ Fixed` if the bug was resolved with a regression test, or `⚠️ Flagged (TODO)` if it was left as a `TODO(bug-bash):` comment

### Regression Test

Represents a new test added alongside a bug fix.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `test_file` | String | Path to the test file | Must be in `backend/tests/` or `frontend/src/` |
| `test_name` | String | Name of the test function/describe block | Must follow existing naming conventions |
| `bug_entry_id` | Integer | Reference to the Bug Report Entry | Must correspond to a `✅ Fixed` entry |
| `failure_mode` | String | What the test would detect if the bug regressed | Non-empty description |

### TODO Flag

Represents a structured code comment placed for ambiguous issues.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `file` | String | Path to the file containing the TODO | Must be a real file |
| `line` | Integer | Line number of the TODO comment | Must be accurate after all fixes |
| `comment_format` | String | Comment text | Must start with `# TODO(bug-bash):` or `// TODO(bug-bash):` |
| `issue_description` | String | What the issue is | Non-empty |
| `options` | String | Available resolution approaches | At least two options |
| `rationale` | String | Why human review is needed | Non-empty |

## Relationships

```text
Bug Report Entry (1) ←→ (1..N) Regression Test
  A fixed bug has one or more regression tests.
  A flagged bug has no regression test.

Bug Report Entry (1) ←→ (0..1) TODO Flag
  A flagged bug has exactly one TODO comment in source code.
  A fixed bug has no TODO comment.
```

## State Transitions

A Bug Report Entry follows this lifecycle:

```text
[Discovered] → [Analyzed] → [Fixed + Tested] → Status: ✅ Fixed
                           → [Flagged as TODO] → Status: ⚠️ Flagged (TODO)
```

- **Discovered**: Issue identified during file audit
- **Analyzed**: Category assigned, severity assessed, fix approach determined
- **Fixed + Tested**: Bug fixed in source, regression test added, full suite passing
- **Flagged as TODO**: `TODO(bug-bash):` comment added, included in summary as flagged

## No Schema Changes

This feature does **not** modify:
- Database tables or migrations
- Pydantic models in `backend/src/models/`
- TypeScript types in `frontend/src/`
- API request/response schemas

All changes are to implementation code (bug fixes) and test code (regression tests).
