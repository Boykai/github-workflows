# Contract: Bug Report Schema

**Feature**: `001-bug-basher` | **Date**: 2026-03-15 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the output formats for the bug bash review process. Since this feature is a code review workflow (not an API feature), the "contracts" are the structured output artifacts that the review produces. There are no REST/GraphQL endpoints to define — instead, the contracts specify the markdown table schema and code comment format that constitute the review's deliverables.

## Summary Table Contract

### Format

The summary table MUST be a markdown table with the following exact structure:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```

### Column Specifications

| Column | Type | Format | Required | Description |
|--------|------|--------|----------|-------------|
| `#` | Integer | Sequential starting at 1 | Yes | Unique bug identifier |
| `File` | String | Backtick-wrapped relative path | Yes | File path from repository root |
| `Line(s)` | String | `N` or `N-M` | Yes | Affected line number(s) |
| `Category` | Enum | Exact match required | Yes | One of: `Security`, `Runtime`, `Logic`, `Test Quality`, `Code Quality` |
| `Description` | String | Plain text, single line | Yes | Human-readable bug description |
| `Status` | Enum | Exact match required | Yes | One of: `✅ Fixed`, `⚠️ Flagged (TODO)` |

### Ordering Rules

1. Entries are ordered by `#` (sequential).
2. Within the table, entries from the same file SHOULD be grouped together.
3. Within a file group, entries SHOULD be ordered by line number.

### Exclusion Rules

- Files with no bugs found MUST NOT appear in the table (FR-015).
- The table MUST NOT include configuration files, generated files, or files outside the repository.

---

## TODO Comment Contract

### Format

```python
# TODO(bug-bash): <description>
```

### Content Requirements

Each TODO comment MUST include:

1. **Issue description**: What the bug or concern is.
2. **Options**: What the possible fixes or approaches are.
3. **Rationale for deferral**: Why this needs human review instead of a direct fix.

### Example

```python
# TODO(bug-bash): This endpoint accepts unbounded input for the `limit` parameter.
# Options: (a) Cap at 1000 with a constant, (b) Make configurable via settings,
# (c) Remove the parameter and paginate server-side.
# Deferred because: Changing pagination behavior would alter the public API contract.
```

### Multi-File References

For bugs spanning multiple files, the primary TODO is placed in the most relevant file. Cross-references use the format:

```python
# TODO(bug-bash): Related issue in `path/to/other/file.py:42` — see primary TODO there.
```

---

## Commit Message Contract

### Format

```text
fix(<category>): <short description>

<detailed explanation>

Bug: <what the bug was>
Impact: <why it matters>
Fix: <how the fix resolves it>
```

### Category Tags

| Tag | Maps to |
|-----|---------|
| `security` | Security Vulnerabilities |
| `runtime` | Runtime Errors |
| `logic` | Logic Bugs |
| `test-quality` | Test Gaps & Test Quality |
| `code-quality` | Code Quality Issues |

### Example

```text
fix(security): Remove hardcoded API key from config module

Bug: The SIGNAL_API_KEY was hardcoded as a default value in config.py,
exposing it in version control.
Impact: Any user with repo access could extract the key and impersonate
the application's Signal integration.
Fix: Changed the default to an empty string and added validation that
the key must be set via environment variable.
```

---

## Regression Test Contract

### Naming Convention

**Backend (Python/pytest)**:
```python
def test_bug_NNN_<descriptive_name>():
    """Regression test for bug #NNN: <short description>."""
```

**Frontend (TypeScript/Vitest)**:
```typescript
it('bug #NNN: <descriptive_name>', () => {
  // ...
});
```

### Requirements

1. Each regression test MUST fail if the corresponding bug is reintroduced.
2. Each regression test MUST include a docstring/comment referencing the bug number.
3. Backend regression tests are placed in `solune/backend/tests/unit/` unless they require external services (then `tests/integration/`).
4. Frontend regression tests are co-located with existing test files or in new `*.test.ts(x)` files alongside the source.
