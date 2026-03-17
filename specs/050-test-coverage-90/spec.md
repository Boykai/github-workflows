# Feature Specification: Comprehensive Test Coverage to 90%+

**Feature Branch**: `050-test-coverage-90`
**Created**: 2026-03-17
**Status**: Draft
**Input**: User description: "Plan: Comprehensive Test Coverage to 90%+"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CI Coverage Ratchet Prevents Regression (Priority: P1)

As a developer, I want the CI pipeline to automatically prevent any pull request from reducing test coverage, so that existing test quality is preserved as the codebase evolves.

**Why this priority**: Without regression protection, any subsequent coverage improvements can be quietly eroded. This is the foundation that all other stories depend on — no coverage increase is safe without a ratchet to lock it in.

**Independent Test**: Can be fully tested by opening a PR that removes an existing test and verifying CI blocks the merge. Delivers immediate protection for current coverage levels.

**Acceptance Scenarios**:

1. **Given** a committed `.coverage-baseline.json` file with current coverage metrics, **When** a developer submits a PR that decreases any coverage metric below the baseline, **Then** the CI pipeline fails with a clear message identifying which metric decreased and by how much.
2. **Given** baseline thresholds of 75% for backend and current-minus-1% for frontend, **When** the CI pipeline runs on a PR that meets or exceeds all thresholds, **Then** the pipeline passes the coverage check step.
3. **Given** a developer has intentionally increased coverage, **When** they run the baseline update script, **Then** the `.coverage-baseline.json` is updated to reflect the new higher values and can be committed.
4. **Given** a PR that adds new code without tests, **When** the diff-cover step runs, **Then** it reports which changed lines lack test coverage without blocking the build.

---

### User Story 2 - Backend Coverage Reaches 90%+ (Priority: P1)

As a quality-focused team, we want backend line coverage to reach 90% or higher through systematic testing of services, API endpoints, and integration workflows, so that bugs in critical backend logic are caught before deployment.

**Why this priority**: The backend handles business logic, data integrity, and security. Raising coverage from 71% to 90%+ directly reduces production bugs in the most impactful part of the system.

**Independent Test**: Can be tested by running `pytest --cov=src` in the backend directory and verifying the coverage report shows ≥90% line coverage. Delivers confidence that all service-layer, API, and integration paths are exercised.

**Acceptance Scenarios**:

1. **Given** the backend test suite, **When** `pytest --cov=src` is run, **Then** line coverage is reported at 90% or higher.
2. **Given** an API endpoint, **When** its test file is reviewed, **Then** it includes parameterized tests covering success (200), authentication failure (401), authorization failure (403), not found (404), validation error (422), rate limiting (429), and server error (500) response codes.
3. **Given** a service module (e.g., `signal_bridge.py`, `github_commit_workflow.py`), **When** its test file is reviewed, **Then** all public functions have at least one test covering the happy path and one test covering an error path.
4. **Given** integration test scenarios for pipeline lifecycle, chat flow, and webhook processing, **When** they are executed, **Then** they validate end-to-end behavior using a mock database backed by real SQLite.

---

### User Story 3 - Frontend Coverage Reaches 90%+ (Priority: P1)

As a quality-focused team, we want frontend statement coverage to reach 90%+ and branch coverage to reach 85%+, so that UI bugs and interaction defects are caught before they reach users.

**Why this priority**: Frontend coverage starts at 49% statements and 44% branches — the largest gap. Raising this protects the most user-visible part of the application and catches regressions in hooks, components, and services.

**Independent Test**: Can be tested by running `npx vitest run --coverage` in the frontend directory and verifying the coverage report meets the target thresholds. Delivers confidence that user-facing functionality is well tested.

**Acceptance Scenarios**:

1. **Given** the frontend test suite, **When** `npx vitest run --coverage` is run, **Then** statement coverage is 90%+, branch coverage is 85%+, function coverage is 85%+, and line coverage is 90%+.
2. **Given** a hook test file (e.g., `useChat.test.tsx`), **When** reviewed, **Then** it includes tests for error states, loading states, empty/null edge cases, and cache invalidation.
3. **Given** an interactive component (e.g., `TopBar`, `Sidebar`, `ChatInterface`), **When** its test file is reviewed, **Then** it follows the render → interact → assert pattern and includes an accessibility validation check.
4. **Given** a schema test file, **When** reviewed, **Then** it includes negative tests for malformed payloads, missing required fields, and type coercion.

---

### User Story 4 - Mutation Testing Validates Test Quality (Priority: P2)

As a quality-focused team, we want mutation testing to verify that tests actually detect code changes, so that high coverage numbers reflect genuine defect-detection capability rather than superficial line execution.

**Why this priority**: Coverage percentage alone can be misleading. Mutation testing validates that tests are truly asserting behavior, not just executing code. This story turns coverage numbers into meaningful quality signals.

**Independent Test**: Can be tested by running `mutmut run` for backend and `npx stryker run` for frontend and verifying mutation scores meet targets. Delivers assurance that tests have real defect-detection power.

**Acceptance Scenarios**:

1. **Given** the backend mutation testing configuration, **When** `mutmut run` is executed across all configured shards, **Then** each shard achieves a mutation score of 75% or higher.
2. **Given** the frontend Stryker configuration, **When** `npx stryker run` is executed, **Then** the mutation score is 60% or higher and the build fails if it drops below this threshold.
3. **Given** mutation testing is expanded to cover `src/api/`, `src/middleware/`, and `src/models/` (backend) and `src/services/**`, `src/utils/**` (frontend), **When** a surviving mutant is identified, **Then** it is logged as a test gap for follow-up.

---

### User Story 5 - Property-Based and Fuzz Testing Catches Edge Cases (Priority: P2)

As a quality-focused team, we want property-based and fuzz testing to discover edge cases that manual test authoring misses, so that the system is resilient to unexpected inputs and state transitions.

**Why this priority**: Property-based and fuzz tests catch classes of bugs that example-based tests miss — boundary conditions, malformed inputs, and invalid state transitions. These are often the bugs that cause production incidents.

**Independent Test**: Can be tested by running the property test suites and verifying they pass without failures. Delivers resilience against unexpected inputs and invariant violations.

**Acceptance Scenarios**:

1. **Given** a backend Hypothesis test for Pydantic model round-trip, **When** executed with 100+ generated examples, **Then** serialize → deserialize → equals holds for all cases.
2. **Given** a backend Hypothesis test for state machine transitions, **When** executed, **Then** no invalid state transition is possible from any reachable state.
3. **Given** a frontend fast-check test for URL construction, **When** executed with generated inputs, **Then** all produced URLs are valid and well-formed.
4. **Given** a fuzz test for webhook payloads, **When** run with malformed and adversarial inputs, **Then** the system rejects invalid payloads gracefully without crashing or exposing internal errors.

---

### User Story 6 - E2E and Visual Regression Testing Protects User Experience (Priority: P2)

As a quality-focused team, we want end-to-end tests and visual regression snapshots to validate complete user workflows and visual consistency, so that the application behaves correctly and looks right from the user's perspective.

**Why this priority**: E2E and visual tests are the final safety net — they validate what users actually see and do. Adding 10 new spec files and 42+ visual snapshots significantly expands this safety net.

**Independent Test**: Can be tested by running `npx playwright test` and verifying all specs pass and visual snapshots match. Delivers confidence that complete user workflows function correctly.

**Acceptance Scenarios**:

1. **Given** the Playwright test suite, **When** `npx playwright test` is run, **Then** all specs pass (68+ tests total).
2. **Given** a page in the application, **When** its visual regression test runs at 3 viewport sizes in both light and dark mode, **Then** screenshots match the stored baselines.
3. **Given** 2+ consecutive weeks of zero flaky E2E failures, **When** the CI configuration is reviewed, **Then** E2E tests are blocking (no `continue-on-error: true`).

---

### User Story 7 - Contract and Integration Testing Validates System Boundaries (Priority: P3)

As a quality-focused team, we want contract testing and expanded integration tests to validate API schema compliance and cross-system interactions, so that breaking changes at system boundaries are caught early.

**Why this priority**: Contract and integration tests protect the interfaces between frontend and backend and between the system and external services. These are less urgent than unit/component coverage but critical for long-term stability.

**Independent Test**: Can be tested by running `bash solune/scripts/validate-contracts.sh` and verifying it passes with schema validation. Delivers assurance that API contracts are honored.

**Acceptance Scenarios**:

1. **Given** the `openapi.json` schema, **When** schemathesis runs auto-generated test cases, **Then** all API responses conform to the schema.
2. **Given** integration tests for database migrations, WebSocket lifecycle, and rate limiting, **When** executed, **Then** they validate correct cross-component behavior.
3. **Given** the contract validation script, **When** run with response body validation enabled, **Then** it verifies response bodies match the documented schema.

---

### User Story 8 - Flaky Test Management Keeps the Suite Reliable (Priority: P3)

As a developer, I want a systematic process for detecting, quarantining, and resolving flaky tests, so that the test suite remains trustworthy and CI failures always indicate real problems.

**Why this priority**: Flaky tests erode trust in the test suite. A quarantine system lets coverage grow without being blocked by intermittent failures, while ensuring flaky tests are tracked and eventually fixed.

**Independent Test**: Can be tested by running the nightly flaky test detection script and verifying that identified flaky tests are marked and tracked. Delivers a reliable CI pipeline where failures are actionable.

**Acceptance Scenarios**:

1. **Given** the nightly flaky test detection job, **When** it identifies a test that fails intermittently, **Then** the test is marked with `@pytest.mark.flaky` (backend) or `test.fixme()` (frontend) and tracked for resolution.
2. **Given** a quarantined flaky test, **When** it has been quarantined for more than 30 days, **Then** it is either fixed or removed, maintaining a maximum of 5 quarantined tests at any time.
3. **Given** the CI pipeline, **When** a quarantined test fails, **Then** it does not block the build while it remains quarantined.

---

### Edge Cases

- What happens when a new module is added with zero tests? The diff-cover check warns about untested new code, and the developer must either add tests or justify the omission.
- What happens when a legitimate code change reduces coverage percentage (e.g., removing dead code that was tested)? The developer runs the baseline update script with justification in the PR description after review approval.
- What happens when mutation testing identifies a surviving mutant in generated or boilerplate code? The team documents a `pragma: no mutate` exemption with justification, limited to `__main__` guards, `TYPE_CHECKING` blocks, and platform-specific code.
- What happens when a visual regression snapshot changes due to an intentional design update? The developer updates the baseline snapshots and includes before/after comparisons in the PR.
- What happens when E2E tests become flaky during the stabilization period? The flaky test quarantine process kicks in, the 2-week stability clock resets, and E2E tests remain non-blocking until stability is achieved.
- What happens when third-party dependency updates cause test failures? Dependency update PRs are tested through the full CI pipeline including contract tests, and failures are resolved before merging.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a `.coverage-baseline.json` file that records current coverage metrics for both backend and frontend.
- **FR-002**: CI pipeline MUST compare every PR's coverage metrics against the baseline and fail if any metric decreases.
- **FR-003**: System MUST provide a `solune/scripts/update-coverage-baseline.sh` script that updates the baseline after intentional coverage increases.
- **FR-004**: CI pipeline MUST run diff-coverage on every PR and report which changed lines lack test coverage.
- **FR-005**: Backend coverage threshold MUST be raised incrementally: 71% → 75% → 85% → 90%.
- **FR-006**: Frontend coverage thresholds MUST be raised incrementally from current values to final targets of 90% statements, 85% branches, 85% functions, and 90% lines.
- **FR-007**: System MUST include dedicated test files for all currently uncovered backend service modules, including `github_commit_workflow.py`, `signal_bridge.py`, `signal_chat.py`, and `signal_delivery.py`.
- **FR-008**: Every backend API endpoint MUST have parameterized tests covering status codes: 200, 401, 403, 404, 422, 429, and 500.
- **FR-009**: Integration tests MUST validate pipeline lifecycle, chat flow, and webhook processing using a mock database with real SQLite.
- **FR-010**: All 44 frontend hook test files MUST include tests for error states, loading states, empty/null edge cases, and cache invalidation.
- **FR-011**: System MUST include tests for approximately 30 currently untested frontend components, following the render → interact → assert pattern with accessibility validation.
- **FR-012**: Frontend schema tests MUST include negative tests for malformed payloads, missing required fields, and type coercion.
- **FR-013**: Backend mutation testing scope MUST expand to cover `src/api/`, `src/middleware/`, and `src/models/` in addition to `src/services/`.
- **FR-014**: Frontend Stryker mutation testing scope MUST expand to cover `src/services/**` and `src/utils/**` in addition to current targets.
- **FR-015**: Backend mutation testing MUST achieve a mutation score of 75% or higher per shard.
- **FR-016**: Frontend mutation testing MUST achieve a mutation score of 60% or higher, enforced as a blocking threshold.
- **FR-017**: Backend MUST include Hypothesis property-based tests for GraphQL query invariants, state machine transitions, Pydantic model round-trips, encryption round-trips, and pipeline config validation.
- **FR-018**: Frontend MUST include fast-check property-based tests for URL construction invariants, pipeline reducer state machine invariants, Zod schema round-trips, and pipeline migration idempotency.
- **FR-019**: Backend MUST include fuzz tests for webhook payloads, chat message injection, and file upload path traversal.
- **FR-020**: Frontend MUST include fuzz tests for paste events, deeply nested JSON, and emoji sequences.
- **FR-021**: System MUST include 10 additional Playwright E2E spec files covering pipeline builder, agent management, apps page, chores workflow, projects page, tools page, help page, keyboard navigation, dark mode, and error recovery.
- **FR-022**: Visual regression tests MUST capture screenshots for every page at 3 viewport sizes in both light and dark modes (approximately 42 new snapshots).
- **FR-023**: E2E tests MUST become blocking in CI after 2+ consecutive weeks of zero flaky failures.
- **FR-024**: System MUST integrate schemathesis to auto-generate API test cases from `openapi.json` and run them in CI.
- **FR-025**: Integration tests MUST cover database migration correctness, WebSocket lifecycle, rate limiting end-to-end, guard config validation, and chore scheduling cycle.
- **FR-026**: Contract validation script MUST be enhanced with response body validation.
- **FR-027**: System MUST implement a nightly flaky test detection job using `detect_flaky.py`.
- **FR-028**: Quarantined flaky tests MUST be capped at a maximum of 5 at any time.
- **FR-029**: Final backend coverage threshold MUST be locked at `fail_under: 90`.
- **FR-030**: Final frontend coverage thresholds MUST be locked at `{ statements: 90, branches: 85, functions: 85, lines: 90 }`.
- **FR-031**: PR template MUST include a checklist item confirming that new code includes appropriate test coverage.
- **FR-032**: A monthly per-file audit script MUST be available to identify files with coverage below the team threshold.
- **FR-033**: `pragma: no cover` MUST be limited to `__main__` guards, `TYPE_CHECKING` blocks, and platform-specific code, with justification required in the PR.

### Key Entities

- **Coverage Baseline**: A JSON document recording current coverage metrics (line, branch, statement, function percentages) for both backend and frontend. Serves as the source of truth for the ratchet mechanism.
- **Coverage Threshold**: Configured minimum coverage levels that the CI pipeline enforces. These increase through phases (75 → 85 → 90 for backend; incremental for frontend).
- **Quarantined Test**: A test identified as flaky by the detection system, marked for tracking and resolution. Has a maximum age of 30 days and a system-wide cap of 5.
- **Mutation Score**: The percentage of code mutations that are detected (killed) by the test suite. Measures test quality beyond simple coverage.
- **Visual Snapshot Baseline**: Stored screenshots at defined viewport sizes and color modes, used as reference for detecting unintended visual changes.
- **Contract Schema**: The `openapi.json` specification that defines expected API behavior, used by schemathesis for automated test generation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Backend test suite achieves 90%+ line coverage as reported by `pytest --cov=src`.
- **SC-002**: Frontend test suite achieves 90%+ statement coverage and 85%+ branch coverage as reported by `npx vitest run --coverage`.
- **SC-003**: All Playwright E2E specs pass (68+ tests) as reported by `npx playwright test`.
- **SC-004**: Backend mutation score reaches 75%+ per shard as reported by `mutmut run`.
- **SC-005**: Frontend mutation score reaches 60%+ as reported by `npx stryker run`.
- **SC-006**: Contract validation passes with schemathesis as reported by `bash solune/scripts/validate-contracts.sh`.
- **SC-007**: A PR that removes an existing test causes CI to fail due to ratchet enforcement.
- **SC-008**: A PR with untested new code receives a diff-coverage warning identifying the uncovered lines.
- **SC-009**: Coverage thresholds can never decrease — any attempt to lower a threshold in configuration is caught by code review process and ratchet enforcement.
- **SC-010**: Maximum of 5 flaky tests are quarantined at any point in time, with all quarantined tests resolved or removed within 30 days.
- **SC-011**: Every interactive frontend component test includes at least one accessibility validation check.
- **SC-012**: Every backend API endpoint test file covers at minimum 6 of the 7 standard HTTP status code scenarios (200, 401, 403, 404, 422, 429, 500).

## Assumptions

- Current backend line coverage is approximately 71%.
- Current frontend statement coverage is approximately 49% and branch coverage is approximately 44%.
- The project uses pytest with pytest-cov for backend coverage, Vitest with coverage plugin for frontend coverage, and Playwright for E2E testing.
- The project uses mutmut for backend mutation testing and Stryker for frontend mutation testing.
- The project has an existing CI pipeline in `.github/workflows/ci.yml` that can be extended with additional steps.
- An `openapi.json` schema exists or can be generated for the backend API.
- The `detect_flaky.py` script exists or will be created as part of implementation.
- The Hypothesis library (backend) and fast-check library (frontend) are available or can be added as development dependencies.
- Phases 2–7 can execute in parallel after Phase 1 is complete, with Phase 8 as the final lock-down.
- The `pragma: no cover` budget is strictly limited and requires PR-level justification.

## Dependencies

- **Phase 1** (CI Ratchet) must complete before any other phase, as it provides the regression protection that all subsequent phases rely on.
- **Phase 4** (Mutation Testing Expansion) depends on Phases 2 and 3 to ensure sufficient test coverage exists before measuring mutation scores.
- **Phase 8** (Coverage Ceiling & Maintenance) depends on all prior phases to reach final threshold targets.
- Phases 2–3, 5–7 can execute in parallel after Phase 1 completes.

## Out of Scope

- Rewriting existing tests that currently pass and provide value, unless they are flaky.
- Changing production code solely to improve testability (unless the change also improves code quality).
- Achieving 100% coverage — the target is 90%+ with justified exemptions for unreachable code.
- Performance testing or load testing beyond what is needed for rate-limiting integration tests.
- Testing third-party libraries or framework internals.
