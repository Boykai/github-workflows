# Test Quality Review Contract

**Feature**: 042-bug-basher
**Date**: 2026-03-15
**Version**: 1.0
**Priority**: P4 — Reviewed after logic bugs

## Purpose

Defines the process for identifying and improving low-quality tests across the Solune codebase. This contract governs User Story 4 (Test Quality Improvement) and covers: tests that pass for the wrong reason, mock leaks, assertions that never fail, and missing edge case coverage.

## Input: File Scope

Test files to review in order:

1. **Backend test configuration**: `solune/backend/tests/conftest.py` — fixture quality, mock scoping
2. **Backend unit tests**: All files in `solune/backend/tests/unit/` — assertion quality, mock correctness
3. **Backend integration tests**: All files in `solune/backend/tests/integration/` — isolation, meaningful assertions
4. **Backend E2E tests**: `solune/backend/tests/test_api_e2e.py` — real behavior testing
5. **Backend test helpers**: All files in `solune/backend/tests/helpers/` — helper correctness
6. **Frontend test utilities**: `solune/frontend/src/test/setup.ts`, `solune/frontend/src/test/test-utils.tsx`, `solune/frontend/src/test/factories/`
7. **Frontend component tests**: All `*.test.tsx` files — assertion quality, cleanup
8. **Frontend hook tests**: All `*.test.ts` files in `solune/frontend/src/hooks/__tests__/`
9. **Frontend E2E tests**: `solune/frontend/e2e/` — test reliability

## Check Categories

### TQ1: Mock Leaks

**Pattern**: Mock objects (e.g., `MagicMock`, `Mock`, `vi.fn()`) leaking outside test scope into production code paths.

**Detection**:
- `MagicMock` used as a file path, database URI, or API URL
- `patch()` without `with` statement or decorator (unbounded patches)
- Mock return values that contain other mocks (nested mock leaks)
- Frontend mocks not cleaned up between tests (`vi.restoreAllMocks()` missing)

**Fix pattern**: Scope mocks with `with` statements or decorators; use explicit mock values instead of auto-generated `MagicMock`; ensure cleanup in `afterEach`.

**Regression test**: Verify that the production code path uses real values, not mock objects, by asserting the type or format of values used.

### TQ2: Assertions That Never Fail

**Pattern**: Test assertions that are tautologically true, test the wrong thing, or have no assertions at all.

**Detection**:
- `assert True`, `assert response is not None` (on non-nullable returns)
- `assert isinstance(result, dict)` without checking contents
- Tests with no `assert` statement at all
- `expect(element).toBeTruthy()` on elements that are always present
- Assertions on mock return values instead of actual behavior

**Fix pattern**: Replace with meaningful assertions that verify the intended behavior. Add value-level checks, not just type-level.

**Regression test**: Verify the updated assertion would fail if the intended behavior were broken (manual mutation check).

### TQ3: Tests That Pass for Wrong Reason

**Pattern**: Tests where the assertion matches the mock return value rather than testing real behavior.

**Detection**:
- Test sets up mock to return `X`, then asserts result is `X` — tests the mock, not the code
- Test patches the function under test itself
- Test uses `any()` or `ANY` matchers excessively, hiding real assertions
- Test mocks both the input and output of the function being tested

**Fix pattern**: Reduce mocking to only external dependencies; assert on the transformation or side effect the function performs, not on mock pass-through values.

**Regression test**: Introduce a bug in the code under test and verify the test catches it.

### TQ4: Missing Critical Coverage

**Pattern**: Critical code paths with no test coverage, especially error handling and edge cases.

**Detection**:
- Error handling branches with no corresponding test
- Security-critical functions without test coverage
- State transition logic without edge case tests
- Complex conditional logic tested only for the happy path

**Fix pattern**: Add tests for the uncovered paths, focusing on error cases and edge cases.

**Regression test**: The new test itself is the regression test — it must fail if the covered behavior changes.

### TQ5: Test Isolation Issues

**Pattern**: Tests that depend on execution order, share mutable state, or modify global configuration.

**Detection**:
- Tests that pass individually but fail in suite (or vice versa)
- Tests that modify module-level variables, class attributes, or singletons
- Tests that write to shared files without cleanup
- Frontend tests that don't render in isolation (rely on parent component state)

**Fix pattern**: Isolate state per test using fixtures, setup/teardown, or fresh instances.

**Regression test**: Run the test in isolation and in suite to verify consistent behavior.

## Output

For each finding, produce:
- A BugReportEntry with `category: test-quality`
- A test fix (directly in the test file)
- An explanation of why the original test was incorrect (in commit message)
- A commit with `fix(test-quality): <description>` message format

## Completion Criteria

- All test files reviewed for mock scoping and assertion quality
- No `MagicMock` objects leaking into production code paths
- No tautological or empty assertions remain
- Critical code paths have meaningful test coverage
- Test isolation verified — no order-dependent tests
