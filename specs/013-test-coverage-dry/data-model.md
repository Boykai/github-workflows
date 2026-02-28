# Data Model: Increase Meaningful Test Coverage, Fix Discovered Bugs, and Enforce DRY Best Practices

**Feature**: 013-test-coverage-dry | **Date**: 2026-02-28

> This feature does not introduce new application data entities. The "entities" below describe the conceptual artifacts produced and consumed during the test audit and improvement process.

## Entity: Test Audit Report

**Purpose**: Classification of every existing test, driving all subsequent cleanup work.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| test_file | string | Path to test file relative to repo root | Required, must exist |
| test_name | string | Fully qualified test name (class::method or describe > it) | Required |
| classification | enum | `meaningful` \| `redundant` \| `misaligned` | Required |
| rationale | string | Explanation for the classification | Required, non-empty |
| action | enum | `keep` \| `rewrite` \| `remove` | Required |
| mapped_feature | string | Documented application feature this test validates | Required for `meaningful` and `rewrite` |
| related_test | string | For `redundant` — the test that provides equivalent coverage | Required for `redundant` |

**Validation Rules**:
- Every existing test must have exactly one audit entry
- `misaligned` tests must have action `rewrite` or `remove`
- `redundant` tests must have action `remove` and a valid `related_test`
- `meaningful` tests must have action `keep`

---

## Entity: Shared Test Utility

**Purpose**: Reusable test infrastructure modules replacing duplicated logic.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| module_path | string | Path to shared utility module | Required |
| utility_type | enum | `factory` \| `fixture` \| `mock_builder` \| `assertion_helper` | Required |
| description | string | What the utility provides | Required |
| consumers | list[string] | Test files that import this utility | Must have ≥ 2 entries |

**Backend Shared Utilities** (`backend/tests/helpers/`):
- `factories.py` — Test data factories (make_user_session, make_project, make_task, etc.)
- `assertions.py` — Custom assertion helpers (assert_api_error, assert_json_structure)
- `mocks.py` — Pre-configured mock builders for common services

**Frontend Shared Utilities** (`frontend/src/test/`):
- `factories/` — Test data factories (createMockProject, createMockTask, createMockUser)
- `setup.ts` — Already exists: global mocks and polyfills
- `test-utils.tsx` — Already exists: renderWithProviders

---

## Entity: Regression Test

**Purpose**: Test written to reproduce and permanently guard against a discovered bug.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| test_name | string | Descriptive name referencing the bug | Required, must communicate the defect |
| test_file | string | Path to test file | Required, in same module as fix |
| bug_description | string | What the bug was | Required |
| fix_description | string | What the fix changed | Required |
| red_commit | string | Commit SHA where test was added (failing) | Tracked during implementation |
| green_commit | string | Commit SHA where fix was applied (passing) | Tracked during implementation |

**Validation Rules**:
- Regression test must fail before fix is applied (red)
- Regression test must pass after fix is applied (green)
- All other tests must continue to pass after fix

---

## Entity: Coverage Report

**Purpose**: Measurement of test coverage to verify improvement.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| scope | enum | `backend` \| `frontend` \| `overall` | Required |
| tool | string | Coverage tool used | `pytest-cov` or `vitest --coverage` |
| line_coverage_pct | float | Percentage of lines covered | 0–100 |
| branch_coverage_pct | float | Percentage of branches covered | 0–100, optional |
| uncovered_modules | list[string] | Modules with zero coverage | Informational |
| timestamp | datetime | When the report was generated | Required |

**Validation Rules**:
- Coverage must be measured before and after this feature work
- All documented critical flows must have non-zero coverage after completion

---

## Relationships

```
Test Audit Report 1──* Shared Test Utility  (audit identifies duplication → utilities extracted)
Test Audit Report 1──* Regression Test      (audit discovers bugs → regression tests written)
Coverage Report   1──1 Test Audit Report    (baseline before, measurement after)
```

## State Transitions

### Test Lifecycle
```
existing test → [audit] → classified (meaningful|redundant|misaligned)
  meaningful  → kept as-is (may receive AAA/naming improvements)
  redundant   → removed (related_test verified to cover same behavior)
  misaligned  → rewritten to test correct behavior OR removed with rationale
```

### Bug Fix Lifecycle
```
discovered → [write failing test] → red → [apply fix] → green → [verify all tests pass] → merged
```
