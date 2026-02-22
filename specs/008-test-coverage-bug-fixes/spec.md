# Feature Specification: Test Coverage & Bug Fixes

**Feature Branch**: `008-test-coverage-bug-fixes`  
**Created**: 2026-02-20  
**Status**: Draft  
**Input**: User description: "Update tests for 85% coverage. Resolve any discovered bugs/errors/issues. Keep it simple. Keep it DRY. Use best practices."

## Clarifications

### Session 2026-02-20

- Q: Should there be a per-file minimum coverage floor in addition to the 85% aggregate? → A: Yes — aggregate 85% + per-file minimum of 70%.
- Q: Should the no-network constraint apply to all tests or only new unit/component tests? → A: New unit/component tests only; existing integration/e2e tests are left as-is.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backend Test Coverage Reaches 85% (Priority: P1)

A developer runs the backend test suite and receives a coverage report showing at least 85% line coverage across all backend source modules. Currently, 5 of 12 service modules, 6 of 8 API route modules, all prompt modules, and core modules (`config.py`, `constants.py`, `exceptions.py`, `main.py`) lack test coverage. This story closes those gaps with unit tests that are simple, DRY, and follow pytest best practices.

**Why this priority**: Tests are the foundation for safely resolving bugs and making future changes. Without adequate coverage, bug fixes cannot be verified and regressions cannot be caught.

**Independent Test**: Run `pytest --cov=src --cov-report=term-missing` from the `backend/` directory and confirm the overall coverage percentage is ≥ 85%.

**Acceptance Scenarios**:

1. **Given** the backend test suite is run with coverage enabled, **When** coverage is calculated, **Then** overall line coverage is at least 85%.
2. **Given** a developer adds a new unit test file, **When** they follow the existing test patterns and shared fixtures, **Then** the test uses no more than 5 lines of setup boilerplate (DRY fixtures in `conftest.py`).
3. **Given** the backend test suite exists, **When** it is run, **Then** all tests pass without errors or warnings.

---

### User Story 2 - Frontend Test Coverage Reaches 85% (Priority: P2)

A developer runs the frontend test suite and receives a coverage report showing at least 85% line coverage. Currently, only 3 of 9 hooks have unit tests, zero components have tests, and the API service module is untested. This story adds Vitest unit/component tests using React Testing Library to close those gaps.

**Why this priority**: Frontend coverage is significantly lower than backend. However, backend tests are prioritized first because backend bugs have wider blast radius (data corruption, auth issues). Frontend tests are equally important for user-facing reliability.

**Independent Test**: Run `npm run test:coverage` from the `frontend/` directory and confirm the overall coverage percentage is ≥ 85%.

**Acceptance Scenarios**:

1. **Given** the frontend test suite is run with coverage enabled, **When** coverage is calculated, **Then** overall line coverage is at least 85%.
2. **Given** a developer writes a new component test, **When** they follow the existing test patterns and shared mocks in `test/setup.ts`, **Then** common mocks (WebSocket, API, router) are reusable without duplication.
3. **Given** the frontend test suite exists, **When** it is run, **Then** all tests pass without errors or warnings.

---

### User Story 3 - Bugs and Issues Discovered During Testing Are Resolved (Priority: P2)

While writing tests to reach 85% coverage, developers discover bugs, dead code, type errors, or incorrect behavior in the codebase. Each discovered issue is documented and fixed as part of this effort. Fixes are verified by the newly written tests.

**Why this priority**: Bug resolution is a direct byproduct of the coverage effort. Fixing bugs as they're found prevents technical debt accumulation and ensures the test suite validates correct behavior, not broken behavior.

**Independent Test**: Each bug fix has at least one corresponding test that fails before the fix and passes after.

**Acceptance Scenarios**:

1. **Given** a bug is discovered while writing tests, **When** the developer fixes it, **Then** there is at least one test that specifically validates the fix.
2. **Given** dead code or unreachable branches are found, **When** they are removed, **Then** no existing tests break and overall coverage improves.
3. **Given** type errors or incorrect error handling are found, **When** they are corrected, **Then** the corrections follow existing code conventions and patterns.

---

### User Story 4 - Coverage Thresholds Enforced in Configuration (Priority: P3)

Coverage thresholds are configured in both `pyproject.toml` (backend) and `vitest.config.ts` (frontend) so that the test suite fails if coverage drops below 85%. This prevents future regressions in test coverage.

**Why this priority**: Threshold enforcement is the long-term safeguard, but only meaningful once coverage actually reaches the target. It is a configuration change, not a testing effort.

**Independent Test**: Temporarily remove a test file and run the test suite. Confirm the suite fails due to the coverage threshold violation.

**Acceptance Scenarios**:

1. **Given** backend coverage configuration exists in `pyproject.toml`, **When** coverage drops below 85%, **Then** the test runner exits with a non-zero return code.
2. **Given** frontend coverage configuration exists in `vitest.config.ts`, **When** coverage drops below 85%, **Then** the test runner exits with a non-zero return code.

---

### User Story 5 - Shared Test Fixtures Are DRY and Reusable (Priority: P3)

Backend `conftest.py` is expanded with reusable fixtures for common test needs: mock HTTP client, mock database connections, mock GitHub API responses, and mock AI/agent services. Frontend `test/setup.ts` is expanded with shared mocks/utilities for the API service, router context, and theme provider. These shared utilities eliminate repetitive setup code across test files.

**Why this priority**: DRY test infrastructure is an enabler for Stories 1 and 2 but represents the scaffolding, not the coverage itself.

**Independent Test**: Verify that at least 3 different test files import and use the same shared fixtures/mocks without duplicating mock setup code.

**Acceptance Scenarios**:

1. **Given** a new backend test needs a mock database connection, **When** the developer writes the test, **Then** they import a shared fixture from `conftest.py` rather than creating ad-hoc mocks.
2. **Given** a new frontend component test needs a mocked API service, **When** the developer writes the test, **Then** they import a shared mock from `test/setup.ts` or a test utility file.

---

### Edge Cases

- What happens when a source module has no testable logic (e.g., pure re-exports, type definitions)? Exclude from coverage requirements via configuration.
- How does the test suite handle modules that depend on external services (GitHub API, AI services)? All external dependencies are mocked; no tests require network access.
- What happens when a bug fix changes a public API signature? Existing tests that depend on the old signature are updated alongside the fix.
- How are async code paths tested? Using `pytest-asyncio` (backend) and async Vitest patterns (frontend) consistently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Backend test suite MUST achieve at least 85% overall line coverage as reported by `pytest-cov`, with no individual source file falling below 70% line coverage.
- **FR-002**: Frontend test suite MUST achieve at least 85% overall line coverage as reported by `@vitest/coverage-v8`, with no individual source file falling below 70% line coverage.
- **FR-003**: All currently untested backend service modules (`agent_tracking`, `completion_providers`, `database`, `session_store`, `settings_store`) MUST have corresponding unit test files.
- **FR-004**: All currently untested backend API route modules (`auth`, `chat`, `projects`, `settings`, `tasks`, `workflow`) MUST have corresponding unit test files.
- **FR-005**: Backend prompt modules (`issue_generation`, `task_generation`) MUST have unit tests validating prompt construction and output structure.
- **FR-006**: All currently untested frontend hooks (`useAgentConfig`, `useAppTheme`, `useChat`, `useProjectBoard`, `useSettings`, `useWorkflow`) MUST have corresponding unit test files.
- **FR-007**: High-value frontend components (at minimum: `LoginButton`, `ProjectBoard`, `IssueCard`, `ChatInterface`, `MessageBubble`, `ErrorDisplay`, `GlobalSettings`, `ProjectSidebar`) MUST have unit or component tests.
- **FR-008**: Frontend API service module (`api.ts`) MUST have unit tests covering all exported functions.
- **FR-009**: Backend `pyproject.toml` MUST include coverage configuration with `fail_under = 85`.
- **FR-010**: Frontend `vitest.config.ts` MUST include a coverage configuration block with threshold set to 85%.
- **FR-011**: Backend `conftest.py` MUST provide shared fixtures for: mock HTTP test client, mock database, mock GitHub API, and mock AI/agent services.
- **FR-012**: Frontend test setup MUST provide shared mocks/utilities for: API service, router context, and theme context.
- **FR-013**: Any bugs, dead code, or incorrect behavior discovered during test writing MUST be fixed, with at least one test validating each fix.
- **FR-014**: All test files MUST follow existing naming conventions (`test_*.py` for backend, `*.test.tsx` / `*.test.ts` for frontend).
- **FR-015**: All **new** unit and component tests MUST run without network access; external dependencies MUST be mocked. Existing integration and e2e tests are out of scope for this constraint.
- **FR-016**: All existing tests MUST continue to pass after changes are made.

### Key Entities

- **Test Suite**: Collection of test files organized by category (unit, integration, e2e) and layer (backend, frontend).
- **Coverage Report**: Output of coverage tools showing per-file and overall line coverage percentages, uncovered lines, and threshold pass/fail status.
- **Test Fixture / Mock**: Reusable test setup code that provides commonly needed dependencies (database connections, API clients, authentication contexts) without duplication.
- **Bug Fix**: A code change that corrects incorrect behavior discovered during test writing, accompanied by a validating test.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Backend test suite reports ≥ 85% overall line coverage and every source file ≥ 70% line coverage when run with coverage enabled.
- **SC-002**: Frontend test suite reports ≥ 85% overall line coverage and every source file ≥ 70% line coverage when run with coverage enabled.
- **SC-003**: All tests (backend and frontend) pass on a clean run with zero failures and zero errors.
- **SC-004**: At least 80% of test files use shared fixtures or mocks rather than inline ad-hoc mocking (DRY principle).
- **SC-005**: Coverage threshold enforcement is active — removing any single test file causes the test suite to fail due to coverage drop.
- **SC-006**: Every bug fix made during this effort has at least one test that would fail if the fix were reverted.
- **SC-007**: No **new** unit or component test requires network access or external service availability to pass. Existing integration/e2e tests are unchanged.

## Assumptions

- The 85% coverage target refers to **line coverage** (not branch or function coverage), as this is the most commonly used metric and the default for both coverage tools.
- Coverage is measured **per stack** (backend and frontend independently), not as a combined metric.
- E2E tests (Playwright for frontend, `test_api_e2e.py` for backend) are **not** the primary vehicle for reaching 85%. The target is met primarily through unit and component tests, which are faster, more reliable, and more maintainable.
- Files that contain only re-exports, type definitions, or configuration constants may be excluded from coverage calculation via tool configuration (`omit` patterns) if they contain no testable logic.
- The existing test frameworks (pytest + pytest-asyncio for backend, Vitest + React Testing Library for frontend) are retained. No new testing frameworks are introduced.
- "Best practices" means: arrange-act-assert pattern, descriptive test names, one assertion concept per test, mocking at boundaries (not internal implementation), and test isolation (no shared mutable state between tests).
