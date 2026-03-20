# Data Model: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature Branch**: `051-fix-bugs-test-coverage`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This feature is a quality-engineering effort — it does not introduce new data models or API
endpoints. Instead, it operates on the existing data models and produces quality-measurement
artifacts. The entities below represent the conceptual objects managed during execution, not new
database tables or API resources.

## Entities

### 1. Test Suite

A collection of test files targeting a specific codebase area.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Suite identifier | Unique within scope (e.g., `backend-unit`, `frontend-vitest`) |
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
| `threshold` | float | Minimum required coverage | From config (`fail_under` / `thresholds`) |
| `passed` | boolean | Whether threshold was met | `true` if all metrics ≥ threshold |

**Relationships**:
- A Coverage Report *belongs to* one Test Suite.
- A Coverage Report *triggers* one or more CI Gate evaluations.

---

### 3. Mutation Report

A measurement of test effectiveness via code mutations, produced per shard execution.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `shard_name` | string | Mutation shard identifier | One of: `auth-and-projects`, `orchestration`, `app-and-data`, `agents-and-integrations`, `frontend` |
| `timestamp` | datetime | When the report was generated | ISO 8601 |
| `total_mutants` | integer | Total mutants generated | ≥ 0 |
| `killed` | integer | Mutants caught by tests | 0 ≤ killed ≤ total_mutants |
| `survived` | integer | Mutants not caught | 0 ≤ survived ≤ total_mutants |
| `timed_out` | integer | Mutants that exceeded timeout | 0 ≤ timed_out ≤ total_mutants |
| `kill_rate` | float | Percentage of mutants killed | 0.0–100.0 |
| `threshold` | float | Minimum required kill rate | Backend: 60%, Frontend: 80% high / 60% low |

**Relationships**:
- A Mutation Report *belongs to* one shard (backend) or the frontend suite.
- A Mutation Report *triggers* one CI Gate evaluation.

**Constraints**:
- `killed + survived + timed_out == total_mutants`
- Timed-out mutants are logged as warnings, not counted as survived.

---

### 4. Flaky Test Record

A test identified as producing inconsistent results across multiple runs.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `test_name` | string | Fully qualified test name | Unique |
| `suite_name` | string | Owning test suite | FK → Test Suite.name |
| `failure_rate` | float | Percentage of runs that failed | 0.0–100.0 (exclusive of 0 and 100) |
| `root_cause` | enum | Category of flakiness | One of: `async-timing`, `shared-state`, `environment`, `non-deterministic-ordering`, `time-dependent` |
| `quarantine_status` | enum | Current status | One of: `active`, `quarantined`, `fixed`, `removed` |
| `tracking_ref` | string | Link to issue or task | URL or task ID |
| `re_enable_condition` | string | When to re-test | Human-readable condition |

**Relationships**:
- A Flaky Test Record *belongs to* one Test Suite.
- A Flaky Test Record *updates* the CI Gate flaky-test threshold.

---

### 5. CI Gate

A quality enforcement checkpoint in the continuous integration pipeline.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `gate_name` | string | Gate identifier | Unique (e.g., `backend-coverage`, `frontend-mutation`) |
| `metric_type` | enum | What is measured | One of: `coverage`, `mutation`, `lint`, `type-check`, `flaky` |
| `threshold_value` | float | Minimum required value | ≥ 0.0 |
| `enforcement_action` | enum | What happens on failure | One of: `block-merge`, `warn`, `log` |
| `override_process` | string | Emergency bypass procedure | Non-empty for `block-merge` gates |
| `current_value` | float | Latest measured value | ≥ 0.0 |
| `status` | enum | Current gate state | One of: `passing`, `failing`, `not-evaluated` |

**Relationships**:
- A CI Gate *evaluates* one Coverage Report or Mutation Report.
- A CI Gate *blocks* or *warns* on merge requests.

## State Transitions

### Flaky Test Lifecycle

```text
[Detected] → [Quarantined] → [Root-Cause Analyzed] → [Fix Attempted] → [Re-tested]
                                                                            ↓
                                                                    [Fixed / Removed]
```

- **Detected**: Test produces inconsistent results across 5 runs.
- **Quarantined**: Test marked with `@pytest.mark.skip(reason="flaky: ...")` or equivalent.
- **Root-Cause Analyzed**: Category assigned (async-timing, shared-state, etc.).
- **Fix Attempted**: Code change deployed to address root cause.
- **Re-tested**: Run 5 times to verify consistency.
- **Fixed**: Test consistently passes, quarantine removed.
- **Removed**: Test deleted if the feature is deprecated or the test is fundamentally unreliable.

### Coverage Threshold Ratcheting

```text
[Baseline] → [Tests Written] → [Threshold Met Consistently] → [Config Updated] → [CI Enforcing]
```

- **Baseline**: Current coverage measured (backend 75%, frontend 51/44/41).
- **Tests Written**: New tests added per Phases B and C.
- **Threshold Met Consistently**: Coverage exceeds target across multiple CI runs.
- **Config Updated**: `pyproject.toml` and `vitest.config.ts` thresholds raised.
- **CI Enforcing**: Merges blocked if coverage drops below new thresholds.
- **One-directional**: Thresholds may only be raised, never lowered.
