# Data Model: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Overview

This feature does not introduce new persistent data models or database schema changes. It focuses on expanding the test suite and fixing discovered bugs. The entities below describe the conceptual artifacts produced during the testing workflow, not database tables.

## Entities

### Coverage Report

A generated artifact showing per-file and aggregate coverage metrics.

| Field | Type | Description |
|-------|------|-------------|
| tool | string | Coverage tool used (e.g., "vitest/coverage-v8", "pytest-cov") |
| layer | enum | "frontend" or "backend" |
| timestamp | datetime | When the report was generated |
| overall_percentage | float | Aggregate coverage percentage across all files |
| metrics | object | Breakdown by category: lines, branches, statements, functions |
| per_file | array | List of file-level coverage entries |

**Per-file entry:**

| Field | Type | Description |
|-------|------|-------------|
| file_path | string | Relative path from project root |
| lines | float | Line coverage percentage |
| branches | float | Branch coverage percentage |
| statements | float | Statement coverage percentage |
| functions | float | Function coverage percentage |
| uncovered_lines | array[int] | Line numbers not covered by tests |

**Validation rules:**
- `overall_percentage` must be ≥ 0 and ≤ 100
- `file_path` must be a valid relative path within the project

---

### Test Case

An individual test that validates a specific behavior.

| Field | Type | Description |
|-------|------|-------------|
| file_path | string | Path to the test file |
| test_name | string | Full test identifier (describe block + test name) |
| structure | enum | "AAA" (Arrange-Act-Assert) — required pattern |
| isolation | boolean | True if test has no shared mutable state |
| deterministic | boolean | True if test produces same result on every run |
| category | enum | "unit", "integration", "edge-case" |
| target_module | string | Source file being tested |

**Validation rules:**
- `structure` must always be "AAA"
- `isolation` and `deterministic` must both be `true`
- `test_name` must be descriptive of the behavior being verified

---

### Bug Report Entry

A documented record of a bug discovered during testing.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier (e.g., "BUG-001") |
| affected_module | string | File path of the buggy code |
| description | string | Description of the incorrect behavior |
| root_cause | string | Technical explanation of why it happened |
| fix_description | string | Description of the applied fix |
| test_reference | string | Test case that exposed the bug |
| severity | enum | "critical", "major", "minor" |

**Validation rules:**
- Every bug must have at least one `test_reference`
- `fix_description` must be non-empty (all bugs must be resolved)

## Relationships

```text
Coverage Report 1──* Per-file Entry
Test Case *──1 Target Module (source file)
Bug Report Entry *──1 Test Case (that exposed it)
Bug Report Entry *──1 Affected Module (source file)
```

## State Transitions

### Coverage Improvement Workflow

```text
[Baseline] → [Gap Analysis] → [Test Writing] → [Coverage Measurement] → [Target Met?]
     │                                                                        │
     │                                    ┌──── NO: More tests needed ────────┘
     │                                    │
     └────────────────────────────────────┘     YES: → [Documentation] → [Complete]
```

### Bug Discovery Workflow

```text
[Test Fails] → [Bug Identified] → [Root Cause Analysis] → [Fix Applied] → [Test Passes] → [Regression Check]
```
