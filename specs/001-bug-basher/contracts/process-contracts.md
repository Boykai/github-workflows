# Bug Basher Contracts

**Feature**: 001-bug-basher | **Date**: 2026-03-24

## Overview

The Bug Basher feature is a code review and fix process — it does not introduce new API endpoints, services, or runtime contracts. This document defines the **process contracts** (input/output specifications) that govern the bug bash workflow.

## Process Contracts

### Contract 1: Bug Fix

**Input**: Identified bug in source code
**Output**: Fixed source code + regression test

**Pre-conditions**:
- Bug is clearly identified with file path and line numbers
- Bug falls into one of the five categories (Security, Runtime, Logic, Test Quality, Code Quality)
- Bug is unambiguous (clear fix exists)

**Post-conditions**:
- Source code is modified to fix the bug
- At least one regression test is added that:
  - Would have failed before the fix
  - Passes after the fix
- All existing tests still pass
- All linting checks still pass
- Commit message explains: what, why, and how

**Error conditions**:
- If fix breaks existing tests → iterate until green
- If fix requires API change → flag as TODO instead
- If fix requires new dependency → flag as TODO instead

### Contract 2: Ambiguity Flag

**Input**: Identified issue with trade-offs or ambiguity
**Output**: `# TODO(bug-bash):` comment in source + summary entry

**Pre-conditions**:
- Issue is identified but resolution is ambiguous
- Multiple valid approaches exist, or fix would violate constraints

**Post-conditions**:
- `# TODO(bug-bash):` comment added at the relevant code location
- Comment includes: description, options (≥2), and rationale
- Summary report entry with status "⚠️ Flagged (TODO)"
- No source code changes beyond the comment

### Contract 3: Summary Report

**Input**: All bug fixes and flagged issues
**Output**: Markdown table summary

**Format**:
```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
```

**Pre-conditions**:
- All files have been audited
- All fixes have been applied and validated
- All ambiguous issues have been flagged

**Post-conditions**:
- Every identified bug appears in the table
- Files with no bugs are omitted
- Status is either "✅ Fixed" or "⚠️ Flagged (TODO)"
- Table is ordered by category priority (Security first)

### Contract 4: Validation Gate

**Input**: Complete set of fixes
**Output**: Pass/fail for each validation check

**Backend validation**:
```
ruff check src/ tests/          → MUST pass
ruff format --check src/ tests/ → MUST pass
pyright src/                    → MUST pass
pytest -q --tb=short            → MUST pass (including new regression tests)
```

**Frontend validation**:
```
npm run lint                    → MUST pass
npm run type-check              → MUST pass
npm run test                    → MUST pass (including new regression tests)
npm run build                   → MUST pass
```

**All gates must pass before the bug bash is considered complete.**
