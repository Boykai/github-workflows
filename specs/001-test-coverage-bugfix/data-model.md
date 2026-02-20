# Data Model: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20
**Purpose**: Document the key entities, their relationships, and validation rules relevant to this testing effort.

## Overview

This feature is a testing infrastructure task. It does not introduce new data models or modify existing schemas. The entities below describe the conceptual artifacts produced and consumed during the coverage improvement process.

## Entities

### Coverage Report

A generated artifact representing the test coverage state of the codebase at a point in time.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| scope | enum | `frontend` or `backend` | Required; one of the two supported scopes |
| overall_percentage | float | Aggregate coverage across all measured files | 0.0–100.0 |
| line_coverage | float | Percentage of executed lines | 0.0–100.0 |
| branch_coverage | float | Percentage of executed branches | 0.0–100.0 |
| statement_coverage | float | Percentage of executed statements | 0.0–100.0 |
| per_file_details | list | Per-file coverage breakdown | Each entry has file path + line/branch/statement percentages |
| generated_at | datetime | When the report was produced | ISO 8601 timestamp |

**Relationships**: A Coverage Report is produced by running the test suite with coverage enabled. Two reports (baseline and final) are compared to measure progress.

### Test Case

An individual test that validates a specific behavior.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| name | string | Descriptive test name | Required; follows `describe > it/test` naming |
| file_path | string | Path to the test file | Must match `*.test.{ts,tsx}` (frontend) or `test_*.py` (backend) |
| module_under_test | string | The source file or module being tested | Must reference an existing source file |
| pattern | enum | `AAA` (Arrange-Act-Assert) | Required; all new tests must use AAA |
| is_isolated | boolean | No shared mutable state with other tests | Must be `true` |
| is_deterministic | boolean | Same result on every run | Must be `true` |

**Relationships**: Each Test Case targets one or more functions/components in a module. Multiple Test Cases can target the same module.

### Bug Report Entry

A documented record of a bug discovered during testing.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | string | Unique identifier (e.g., `BUG-001`) | Required; sequential |
| affected_module | string | File path of the buggy source code | Must reference an existing source file |
| description | string | What the incorrect behavior was | Required; non-empty |
| fix_description | string | How the bug was resolved | Required; non-empty |
| exposing_test | string | Test name or file that revealed the bug | Must reference a test case |
| commit_sha | string | Commit hash of the bug fix | Populated after fix is committed |

**Relationships**: Each Bug Report Entry is linked to exactly one exposing Test Case and one source module. The fix commit is separate from the test commit (per FR-008).

## State Transitions

### Coverage Improvement Lifecycle

```
[Baseline Measured] → [Tests Written] → [Coverage Measured] → [Target Met?]
                                                                   │
                                                         Yes ──────┤────── No
                                                          │                 │
                                                   [Document Results]  [Write More Tests]
                                                                         │
                                                                    (loop back)
```

### Bug Discovery Lifecycle

```
[Test Written] → [Test Fails (bug exposed)] → [Bug Documented] → [Bug Fixed] → [Test Passes]
```

## Existing Models (No Changes)

The following existing data models in the codebase are **not modified** by this feature. They are listed here for context since tests will exercise them:

- `backend/src/models/board.py` — Board, Column, BoardItem models
- `backend/src/models/chat.py` — ChatMessage, ChatSession models
- `backend/src/models/project.py` — Project, ProjectConfig models
- `backend/src/models/settings.py` — Settings models
- `backend/src/models/task.py` — Task models
- `backend/src/models/user.py` — User, AuthToken models
- `frontend/src/types/index.ts` — TypeScript type definitions for all frontend entities
