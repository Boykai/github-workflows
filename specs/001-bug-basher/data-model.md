# Data Model: Bug Basher

**Feature**: 001-bug-basher | **Date**: 2026-03-24

## Overview

The Bug Basher feature is a code review and fix process — not a runtime feature. It does not introduce new data models, database tables, or persistent entities. Instead, it operates on and modifies existing source code and tests. The "entities" below describe the conceptual artifacts produced by the bug bash process.

## Entities

### Bug Report Entry

Represents a single identified bug in the summary report.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `number` | integer | Sequential bug number | Auto-incremented, starting at 1 |
| `file` | string | Relative file path from repo root | Must exist in repository |
| `lines` | string | Line number(s) affected | Single line (e.g., "42") or range (e.g., "42-45") |
| `category` | enum | Bug category | One of: Security, Runtime, Logic, Test Quality, Code Quality |
| `description` | string | Human-readable description of the bug | Clear, concise, actionable |
| `status` | enum | Resolution status | One of: "✅ Fixed", "⚠️ Flagged (TODO)" |

**Validation Rules**:
- `file` must be a valid path relative to repository root
- `category` must be one of the five defined categories
- `status` must be either "✅ Fixed" (with regression test) or "⚠️ Flagged (TODO)" (with inline comment)
- Fixed entries must have a corresponding regression test
- Flagged entries must have a corresponding `# TODO(bug-bash):` comment in source

### Regression Test

Represents a test added to validate a bug fix.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `test_file` | string | Path to test file containing the regression test | Must be in existing test directory structure |
| `test_name` | string | Name of the test function/case | Follows codebase naming convention |
| `bug_reference` | integer | Reference to Bug Report Entry number | Must match a "✅ Fixed" entry |
| `framework` | enum | Test framework used | "pytest" (backend) or "vitest" (frontend) |

**Validation Rules**:
- Each "✅ Fixed" Bug Report Entry must have ≥1 Regression Test
- Test must fail when the bug is re-introduced (validates the fix)
- Test must pass with the fix applied

### TODO Comment

Represents a structured inline code comment for ambiguous issues.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `file` | string | File containing the TODO comment | Must match Bug Report Entry file |
| `line` | integer | Line number of the comment | Must be at or near the relevant code |
| `description` | string | Brief description of the issue | Concise, specific |
| `options` | string | Available resolution options | At least 2 options |
| `rationale` | string | Why this needs human decision | Explains the trade-off |

**Validation Rules**:
- Format: `# TODO(bug-bash): <description>`
- Must include options and rationale as follow-up comment lines
- Each TODO must have a corresponding "⚠️ Flagged (TODO)" Bug Report Entry

## Relationships

```text
Bug Report Entry (1) ──── (0..*) Regression Test
    │                              (Fixed entries have ≥1 test)
    │
    └── (0..1) TODO Comment
              (Flagged entries have exactly 1 TODO)
```

## State Transitions

Bug Report Entry lifecycle:

```text
[Identified] ──→ [Analyzed] ──→ [Fixed] ──→ [Tested] ──→ ✅ Fixed
                      │
                      └──→ [Ambiguous] ──→ [Flagged] ──→ ⚠️ Flagged (TODO)
```

1. **Identified**: Bug found during file audit
2. **Analyzed**: Root cause understood, category assigned
3. **Fixed**: Source code fix applied (clear bugs only)
4. **Tested**: Regression test added and passing
5. **Ambiguous**: Trade-off or design decision required
6. **Flagged**: `# TODO(bug-bash):` comment added

## Output Format

The final summary report is a markdown table:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```
