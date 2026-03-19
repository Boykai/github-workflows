# Data Model: Find/Fix Bugs & Increase Test Coverage

**Feature Branch**: `050-fix-bugs-test-coverage`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This feature is primarily a quality-engineering effort — it does not introduce new data models or
API endpoints. Instead, it operates on the existing data models and produces quality-measurement
artifacts. The entities below represent the conceptual objects managed during execution, not new
database tables or API resources.

## Entities

### 1. Test Suite

A collection of test files targeting a specific codebase area.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Suite identifier | Unique within scope (e.g., `backend-unit`, `frontend-e2e`) |
| `scope` | enum | Test category | One of: `unit`, `integration`, `property`, `fuzz`, `chaos`, `concurrency`, `e2e`, `architecture` |
| `codebase` | enum | Target codebase | One of: `backend`, `frontend` |
| `test_count` | integer | Number of test files | ≥ 0 |
| `pass_rate` | float | Percentage of passing tests | 0.0–100.0 |
| `coverage_pct` | float | Code coverage percentage | 0.0–100.0 |
| `flaky_count` | integer | Number of flaky tests detected | ≥ 0 |

**Relationships**:
- A Test Suite *produces* one Coverage Report per run.
- A Test Suite *contains* zero or more Flaky Test Records.

---

### 2. Coverage Report

A measurement of code exercised by tests, produced per test run.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `suite_name` | string | Owning test suite | FK → Test Suite.name |
| `timestamp` | datetime | When the report was generated | ISO 8601 |
| `statement_pct` | float | Statement coverage | 0.0–100.0 |
| `branch_pct` | float | Branch coverage | 0.0–100.0 |
| `function_pct` | float | Function coverage | 0.0–100.0 |
| `line_pct` | float | Line coverage | 0.0–100.0 |
| `threshold` | float | Minimum required coverage | From config (fail_under / thresholds) |
| `passed` | boolean | Whether threshold was met | `true` if all metrics ≥ threshold |

**Relationships**:
- A Coverage Report *belongs to* one Test Suite.
- A Coverage Report *enforces* one CI Gate.

---

### 3. Mutation Report

A measurement of test effectiveness via code mutations.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `tool` | enum | Mutation testing tool | One of: `mutmut`, `stryker` |
| `shard` | string | Shard name (backend) or scope (frontend) | e.g., `auth-and-projects`, `hooks` |
| `total_mutants` | integer | Total mutations generated | ≥ 0 |
| `killed` | integer | Mutants detected by tests | 0 ≤ killed ≤ total_mutants |
| `survived` | integer | Mutants not detected | 0 ≤ survived ≤ total_mutants |
| `kill_rate` | float | killed / total_mutants × 100 | 0.0–100.0 |
| `timeout_mutants` | integer | Mutants that caused timeout | ≥ 0 |

**Relationships**:
- A Mutation Report *is produced by* one Test Suite.
- A Mutation Report *identifies* surviving mutants that need targeted assertions.

---

### 4. Flaky Test Record

A test identified as producing inconsistent results across multiple runs.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `test_id` | string | Fully qualified test name | e.g., `tests/unit/test_cache.py::test_clear` |
| `suite_name` | string | Owning test suite | FK → Test Suite.name |
| `failure_rate` | float | Percentage of runs that fail | 0.0–100.0 (exclusive of 0 and 100) |
| `root_cause` | enum | Category of flakiness | One of: `async_timing`, `shared_state`, `non_deterministic_order`, `time_dependent`, `external_dependency`, `unknown` |
| `quarantine_status` | enum | Current disposition | One of: `active`, `quarantined`, `fixed` |
| `fix_description` | string | How the flakiness was resolved | Nullable; required when status = `fixed` |

**Relationships**:
- A Flaky Test Record *belongs to* one Test Suite.
- A Flaky Test Record *transitions* through states: `active` → `quarantined` → `fixed`.

**State Transitions**:
```
active ──────→ quarantined ──────→ fixed
  │                                  ↑
  └──────────────────────────────────┘
         (direct fix without quarantine)
```

---

### 5. CI Gate

A quality enforcement checkpoint in the continuous integration pipeline.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Gate identifier | e.g., `backend-coverage`, `frontend-statements` |
| `metric_type` | enum | What is measured | One of: `statement_coverage`, `branch_coverage`, `function_coverage`, `line_coverage`, `mutation_kill_rate`, `test_pass_rate` |
| `threshold` | float | Minimum acceptable value | > 0.0 |
| `enforcement` | enum | What happens on failure | One of: `block` (fail CI), `warn` (advisory) |
| `ratchet_direction` | enum | How thresholds may change | Always `up` (never lower) |

**Relationships**:
- A CI Gate *is evaluated by* Coverage Reports and Mutation Reports.
- A CI Gate *blocks or warns* merge requests.

**Current Thresholds**:

| Gate | Current | Target | Config Location |
|------|---------|--------|-----------------|
| Backend coverage (`fail_under`) | 75% | 80% | `backend/pyproject.toml` `[tool.coverage.report]` |
| Frontend statements | 50% | 55% | `frontend/vitest.config.ts` thresholds |
| Frontend branches | 44% | 50% | `frontend/vitest.config.ts` thresholds |
| Frontend functions | 41% | 45% | `frontend/vitest.config.ts` thresholds |
| Frontend lines | 50% | 55% | `frontend/vitest.config.ts` thresholds |
| Stryker mutation (high) | 80% | 80% | `frontend/stryker.config.mjs` |
| Stryker mutation (low) | 60% | 60% | `frontend/stryker.config.mjs` |

---

### 6. Bug Fix Record

Tracks the known bugs that must be fixed in Phase 2.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | Bug identifier | e.g., `BUG-001` |
| `title` | string | Short description | Required |
| `severity` | enum | Impact level | One of: `critical`, `high`, `medium`, `low` |
| `affected_files` | list[string] | Files that need modification | ≥ 1 file |
| `root_cause` | string | Technical root cause | Required |
| `fix_approach` | string | How to resolve | Required |
| `verification` | string | How to confirm the fix | Required |
| `status` | enum | Current state | One of: `identified`, `in_progress`, `fixed`, `verified` |

**Known Bugs**:

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| BUG-001 | Mutmut trampoline name mismatch | Critical | identified |
| BUG-002 | Cache leakage between test suites | High | identified |
| BUG-003 | AsyncMock warnings in integration tests | Medium | identified |
| BUG-004 | Pipeline stuck in "In Progress" | High | identified |

## Entity Relationship Diagram

```
┌──────────────┐     produces      ┌─────────────────┐
│  Test Suite  │──────────────────→│ Coverage Report  │
│              │                   │                  │
│  name        │     contains      │  statement_pct   │
│  scope       │──────────┐       │  branch_pct      │
│  codebase    │          │       │  threshold       │
│  test_count  │          │       │  passed          │
│  pass_rate   │          ▼       └────────┬─────────┘
│  coverage_pct│   ┌──────────────┐       │ enforces
│  flaky_count │   │ Flaky Test   │       ▼
└──────┬───────┘   │   Record     │ ┌──────────┐
       │           │              │ │ CI Gate  │
       │ produces  │  test_id     │ │          │
       │           │  failure_rate│ │  name    │
       ▼           │  root_cause  │ │  metric  │
┌──────────────┐   │  quarantine  │ │  threshold│
│  Mutation    │   │  status      │ │  enforce │
│   Report     │   └──────────────┘ └──────────┘
│              │
│  tool        │   ┌──────────────┐
│  shard       │   │ Bug Fix      │
│  kill_rate   │   │   Record     │
│  total       │   │              │
│  killed      │   │  id          │
│  survived    │   │  severity    │
└──────────────┘   │  status      │
                   └──────────────┘
```

## Validation Rules

1. **Coverage thresholds are monotonically increasing**: A threshold value MUST NOT be set lower
   than its current value. This is enforced by code review and CI configuration checks.
2. **Flaky test quarantine requires root cause**: A test MUST NOT be quarantined without documenting
   the root cause category. This prevents "quarantine and forget" anti-patterns.
3. **Bug fix verification is mandatory**: A Bug Fix Record MUST NOT transition to `fixed` without
   a verification command that can be run to confirm the fix.
4. **Mutation kill rate floors**: Backend mutation kill rate per shard MUST be >60%. Frontend
   Stryker score MUST meet configured thresholds (high: 80%, low: 60%).
5. **Test isolation**: Every test MUST start with clean state. No test may depend on the execution
   order or side effects of another test.
