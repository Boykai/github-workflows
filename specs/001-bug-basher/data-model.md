# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-22

> This feature does not introduce new persistent data models. It is a code quality audit that modifies existing source code and tests in-place. The data model below describes the conceptual entities used during the review process and in the output summary report.

## Entities

### Bug Finding

Represents a single discovered issue during the codebase review.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `number` | integer | Sequential finding identifier | Auto-increment, starts at 1 |
| `file_path` | string | Relative path to the file containing the bug | Must be a valid file in the repository |
| `line_numbers` | string | Line number(s) affected (e.g., "42" or "42-45") | Non-empty |
| `category` | enum | Bug category classification | One of: Security, Runtime, Logic, Test Quality, Code Quality |
| `description` | string | Human-readable description of the bug | Non-empty, concise |
| `status` | enum | Resolution status | One of: ✅ Fixed, ⚠️ Flagged (TODO) |
| `commit_sha` | string | Git commit hash of the fix (if Fixed) | Valid SHA or empty (if Flagged) |

**Validation rules**:
- `category` must be one of the five defined categories
- `status` must be either Fixed (with commit) or Flagged (with TODO comment)
- `file_path` must reference an existing file at the time of the finding

### Regression Test

Represents a new test added to validate a bug fix.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `test_file` | string | Path to the test file | Must follow existing test directory conventions |
| `test_name` | string | Name of the test function/method | Must be descriptive of the bug being tested |
| `finding_number` | integer | References the Bug Finding this test validates | Must match a Finding with status ✅ Fixed |
| `framework` | enum | Testing framework used | One of: pytest, vitest |

**Validation rules**:
- Each Fixed finding must have at least one Regression Test (FR-003)
- Test must fail on original code and pass on fixed code (SC-002)

### TODO Comment

Represents an inline code comment for ambiguous issues.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `file_path` | string | Path to the file containing the comment | Must be a valid file |
| `line_number` | integer | Line where the comment is placed | Positive integer |
| `issue_description` | string | Description of the ambiguous issue | Non-empty |
| `options` | string | Available resolution options | Non-empty |
| `rationale` | string | Why this needs human decision | Non-empty |

**Format**: `# TODO(bug-bash): <issue_description>. Options: <options>. Deferred because: <rationale>`

### Summary Report

Aggregates all findings into a structured output table.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `findings` | array[Bug Finding] | All discovered issues | Ordered by finding number |
| `total_fixed` | integer | Count of ✅ Fixed findings | >= 0 |
| `total_flagged` | integer | Count of ⚠️ Flagged findings | >= 0 |
| `categories_reviewed` | array[string] | Bug categories audited | Must include all 5 categories |
| `files_reviewed` | integer | Total files audited | Must equal total repository file count (SC-001) |

## Relationships

```text
Summary Report
 └── contains 1..* Bug Finding
      ├── has 1..* Regression Test (if status = Fixed)
      └── has 1 TODO Comment (if status = Flagged)
```

## State Transitions

### Bug Finding Lifecycle

```text
[Discovered] → [Classified]
                   ├── (obvious bug) → [Fix Applied] → [Test Added] → [Validated] → ✅ Fixed
                   └── (ambiguous)   → [TODO Added] → ⚠️ Flagged
```

- **Discovered**: Issue identified during file review
- **Classified**: Determined as obvious fix or ambiguous trade-off
- **Fix Applied**: Source code change made (minimal, focused)
- **Test Added**: Regression test created
- **Validated**: Full test suite passes with the fix
- **TODO Added**: `TODO(bug-bash)` comment placed in code

No backward transitions — once a finding is Fixed or Flagged, it remains in that state.
