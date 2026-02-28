# Research: Increase Meaningful Test Coverage, Fix Discovered Bugs, and Enforce DRY Best Practices

**Feature**: 013-test-coverage-dry | **Date**: 2026-02-28

## Research Task 1: Current Backend Test Coverage and Gaps

### Decision
The backend has **39 test files** (33 unit, 3 integration, 1 E2E, plus conftest.py and __init__.py) covering most API endpoints and services. However, significant gaps exist for Signal integration services, the workflow orchestrator sub-modules, and copilot polling sub-modules.

### Rationale
Analysis of `backend/src/` versus `backend/tests/` reveals:
- **Well-covered**: API endpoints (auth, board, chat, projects, settings, tasks, webhooks, workflow), database, models, config, websocket, session/settings stores, github_auth, github_projects, ai_agent, completion_providers, copilot_polling (large 157KB file), workflow_orchestrator (large 107KB file)
- **Gaps identified**: Signal services (signal_chat.py, signal_delivery.py, signal_bridge.py — no dedicated unit tests), encryption service (partial — only test_token_encryption.py at 3KB), middleware module (no tests), cache service (test_cache.py exists but small at 5KB)
- **Observation**: Two test files are extremely large (test_copilot_polling.py at 157KB, test_github_projects.py at 124KB, test_workflow_orchestrator.py at 107KB) — these may contain duplicated setup logic that should be extracted

### Alternatives Considered
- Line-by-line coverage measurement via `pytest-cov` — deferred to implementation phase since running tests requires application dependencies
- Manual code-to-test mapping spreadsheet — too tedious, the file listing comparison is sufficient for planning

---

## Research Task 2: Current Frontend Test Coverage and Gaps

### Decision
The frontend has **only 3 unit test files** testing 3 of 13 hooks. No unit tests exist for any of the 25+ components, 2 pages, or the API service module. The 3 E2E tests (auth, integration, ui) provide some high-level coverage but do not substitute for unit tests.

### Rationale
- **Covered hooks**: useAuth, useProjects, useRealTimeSync (3 of 13)
- **Uncovered hooks**: useChat, useWorkflow, useProjectBoard, useSettings, useSettingsForm, useAgentConfig, useAppTheme, and others
- **Uncovered components**: All board components (11 files), all chat components (6 files), all settings components (8 files), auth/LoginButton, common/ErrorBoundary, UI components
- **Uncovered services**: api.ts (the central API client)
- **Uncovered pages**: ProjectBoardPage, SettingsPage
- **Test infrastructure**: Good foundation exists (setup.ts with mock factories, test-utils.tsx with renderWithProviders) but is underutilized

### Alternatives Considered
- E2E-only testing strategy — rejected because E2E tests are slow, hard to debug, and don't provide isolation; unit tests are needed for hooks and components
- Snapshot testing for components — rejected per spec requirement to test real behavior, not implementation details

---

## Research Task 3: Backend CI Pipeline Re-enablement

### Decision
Re-enable the `pytest --cov=src --cov-report=term-missing` step in `.github/workflows/ci.yml` by uncommenting lines 44-45 in the backend job. This is a documented requirement (FR-017, SC-008).

### Rationale
The CI file currently has:
```yaml
#- name: Run tests
#  run: pytest --cov=src --cov-report=term-missing
```
This was intentionally commented out (per spec assumptions). Re-enabling requires ensuring all existing backend tests pass first. The implementation must:
1. Run the full backend test suite locally to identify any currently-broken tests
2. Fix broken tests or remove with documented rationale
3. Uncomment the CI step
4. Verify CI passes

### Alternatives Considered
- Adding a separate test workflow — rejected for simplicity; the existing ci.yml already has the infrastructure
- Running only a subset of tests in CI — rejected per requirement SC-007 that the full suite must pass

---

## Research Task 4: DRY Best Practices for pytest Test Suites

### Decision
Extract shared test logic into a `backend/tests/helpers/` module containing factories, assertion helpers, and reusable mock builders. Use pytest fixtures (in conftest.py) for DI and setup, and factory functions for test data creation.

### Rationale
Best practices for DRY pytest test suites:
- **Fixture hierarchy**: Root `conftest.py` for shared fixtures, directory-level `conftest.py` for scoped fixtures
- **Factory pattern**: Functions like `make_user_session(**overrides)` that return test objects with sensible defaults
- **Assertion helpers**: Custom assertion functions for common patterns (e.g., `assert_api_error(response, status, message)`)
- **Mock builders**: Functions that create pre-configured mocks for commonly-mocked services
- The existing `conftest.py` already has good fixtures but some tests duplicate setup (e.g., `_make_session()` in test_api_auth.py duplicates logic from conftest's `mock_session`)

### Alternatives Considered
- Using pytest plugins — over-engineered for this scope; simple modules and fixtures are sufficient
- Using pytest-factoryboy — adds a dependency; simple factory functions achieve the same goal with less overhead

---

## Research Task 5: DRY Best Practices for Vitest/React Testing Library Test Suites

### Decision
Extend the existing `frontend/src/test/` directory with additional factories for test data and component render helpers. Create hook-testing patterns that can be reused across all 13 hooks.

### Rationale
Best practices for DRY Vitest + React Testing Library:
- **Render helpers**: The existing `renderWithProviders()` is a good start; extend with component-specific wrappers if needed
- **Mock API factory**: The existing `createMockApi()` in setup.ts is excellent; ensure all new tests use it consistently
- **Hook test pattern**: Create a reusable pattern for testing hooks with QueryClient wrapper — the current 3 hook tests already follow a consistent pattern that can be templated
- **Test data factories**: Functions like `createMockProject()`, `createMockTask()` that return typed test objects

### Alternatives Considered
- MSW (Mock Service Worker) for API mocking — adds a dependency; the existing `vi.mock()` + `createMockApi()` approach is working well
- Storybook for component testing — out of scope; this feature focuses on unit tests

---

## Research Task 6: Test Organization and Naming Conventions

### Decision
Backend tests should maintain the existing `tests/unit/test_<module>.py` pattern that mirrors `src/<module>.py`. Frontend tests should use co-located `*.test.tsx` files next to the source files they test (hooks already follow this pattern).

### Rationale
- **Backend**: Already well-organized — `tests/unit/test_api_auth.py` tests `src/api/auth.py`. Integration tests in `tests/integration/` are separate. This pattern should be preserved and extended to cover missing modules.
- **Frontend**: The 3 existing hook tests are co-located with their hooks in `src/hooks/`. Component tests should follow the same pattern: `src/components/board/BoardColumn.test.tsx` for `src/components/board/BoardColumn.tsx`.
- **Naming**: Backend uses class-based tests with descriptive method names (`test_returns_user_info`). Frontend uses `describe`/`it` blocks. Both conventions are clear and should be preserved.

### Alternatives Considered
- Moving all frontend tests to a separate `tests/` directory — rejected because co-location is the React/Vitest community standard and already established in this project
- Flat test directory structure — rejected because the mirrored structure makes it obvious when a module lacks tests

---

## Research Task 7: Handling Large Test Files

### Decision
Break up excessively large test files (>50KB) into focused sub-files during the DRY refactoring phase. Extract shared setup into the helpers module.

### Rationale
Three backend test files are abnormally large:
- `test_copilot_polling.py` (157KB) — likely contains many test classes with duplicated setup
- `test_github_projects.py` (124KB) — similar pattern
- `test_workflow_orchestrator.py` (107KB) — similar pattern

These files likely violate DRY principles by repeating mock setup and test data creation. Splitting them into focused files (e.g., `test_copilot_polling_run_creation.py`, `test_copilot_polling_status_check.py`) and extracting shared setup to helpers will:
- Improve maintainability and readability
- Reduce duplication
- Make it easier to run targeted test subsets

### Alternatives Considered
- Leaving large files as-is — rejected per FR-008/FR-009 (DRY requirements) and FR-016 (organization)
- Using pytest markers to organize within a single file — insufficient; the files are too large for effective navigation

---

## Research Task 8: Regression Testing Strategy for Bug Fixes

### Decision
Follow red-green-refactor for each discovered bug: write a failing test that reproduces the bug, apply the minimal fix, confirm the test passes, then refactor if needed.

### Rationale
The spec explicitly requires (FR-006, FR-007):
1. Write failing regression test FIRST (demonstrates the bug)
2. Apply the minimal code fix
3. Confirm regression test passes AND all existing tests still pass
4. Refactor if needed

Regression tests should be placed alongside the relevant module's tests (not in a separate regression directory) to maintain the mirrored structure. Each regression test should have a descriptive name that references the bug (e.g., `test_login_does_not_crash_on_expired_token`).

### Alternatives Considered
- Separate `tests/regression/` directory — rejected because it fragments the test structure and makes it harder to see coverage for a specific module
- Bug tracking in a separate document — regression tests themselves serve as living documentation of bugs found and fixed
