# Data Model: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Key Entities

This feature does not introduce new data models or modify existing schemas. The entities below describe the conceptual artifacts produced and consumed by the testing workflow.

### Coverage Report

A generated artifact showing per-file and aggregate coverage metrics.

| Field | Type | Description |
|-------|------|-------------|
| `overall_percentage` | float | Aggregate coverage across all measured files (target: ≥85%) |
| `lines_covered` | integer | Total number of source lines executed by tests |
| `lines_total` | integer | Total number of measurable source lines |
| `branches_covered` | integer | Total number of code branches executed by tests |
| `branches_total` | integer | Total number of measurable code branches |
| `per_file_metrics` | list | Array of per-file coverage breakdowns |
| `tool` | string | Coverage tool used (e.g., "@vitest/coverage-v8", "pytest-cov") |
| `timestamp` | datetime | When the report was generated |

**Validation**: `overall_percentage` must be ≥ 85.0 to meet the acceptance criteria.

### Test Case

An individual test that validates a specific behavior.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Descriptive test name (e.g., "returns user data when authenticated") |
| `module_under_test` | string | The source module being tested |
| `test_file` | string | Path to the test file |
| `pattern` | enum | Always "AAA" (Arrange-Act-Assert) per FR-003 |
| `isolation` | boolean | Must be `true` — no shared mutable state (FR-004) |
| `deterministic` | boolean | Must be `true` — same result on every run (FR-005) |

**Validation**: Tests must not depend on execution order or side effects from other tests.

### Bug Report Entry

A documented record of a bug discovered during testing.

| Field | Type | Description |
|-------|------|-------------|
| `affected_module` | string | Source file or module where the bug was found |
| `description` | string | What the incorrect behavior was |
| `root_cause` | string | Why the bug existed |
| `fix_description` | string | What was changed to resolve it |
| `test_reference` | string | Test(s) that expose and verify the fix |
| `commit_sha` | string | Git commit containing the fix |

## Relationships

```text
Coverage Report 1──* Per-File Metric
Test Case *──1 Module Under Test
Bug Report Entry 1──* Test Case (tests that verify the fix)
```

## State Transitions

No state machines are introduced by this feature. Coverage reports are generated as immutable snapshots (baseline → final comparison).
