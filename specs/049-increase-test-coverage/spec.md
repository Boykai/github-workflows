# Feature Specification: Increase Test Coverage to Surface Unknown Bugs

**Feature Branch**: `049-increase-test-coverage`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Systematically raise backend coverage from 71% → 80% and frontend from ~50/45/42/51% → 60/55/52/60% using a phased approach: promote existing advanced tests to CI, fill high-ROI coverage gaps, add mutation-hardened tests, and introduce production-parity and time-controlled testing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — CI Runs All Existing Advanced Tests (Priority: P1)

As a developer, I want all existing advanced tests (property-based, fuzz, chaos, concurrency) to execute automatically in CI so that regressions in complex behaviors are caught before code merges.

**Why this priority**: Advanced tests already exist locally but are not wired into CI. Without this foundation, no coverage improvements can be verified continuously. This is the single highest-leverage change because it costs almost nothing (tests are written) and immediately expands defect detection.

**Independent Test**: Run a CI pipeline on a pull request and verify that backend property, fuzz, chaos, and concurrency test suites all execute and report results. Frontend fuzz tests must also appear in the CI test output.

**Acceptance Scenarios**:

1. **Given** a pull request is opened, **When** the CI pipeline runs, **Then** backend advanced test suites (property, fuzz, chaos, concurrency) execute within a 120-second timeout and report pass/fail results.
2. **Given** a pull request is opened, **When** the CI pipeline runs, **Then** frontend fuzz tests under `src/__tests__/fuzz/` execute as part of the frontend CI test run and report pass/fail results.
3. **Given** the advanced tests are newly wired into CI, **When** any of them fail, **Then** the failure is reported but does not block the merge (non-blocking initially).
4. **Given** mutation testing is scheduled, **When** the weekly schedule triggers, **Then** backend and frontend mutation tests run, and reports are uploaded as CI artifacts.
5. **Given** the flaky test detection job runs on schedule, **When** the backend suite executes 3 times, **Then** inconsistent results are flagged and the 20 slowest tests are reported.

---

### User Story 2 — Backend Coverage Reaches 80% (Priority: P1)

As a project maintainer, I want backend test coverage to reach at least 80% line coverage and 70% branch coverage so that high-risk untested modules are exercised and unknown bugs are surfaced before they reach production.

**Why this priority**: The backend currently sits at 71% coverage with 9 completely untested modules in business-critical areas (GitHub integration, Copilot polling, chores subsystem, API routes). These gaps represent the highest-risk areas for hidden defects.

**Independent Test**: Run the backend test suite with coverage reporting and verify the total line coverage meets or exceeds 80% and branch coverage meets or exceeds 70%.

**Acceptance Scenarios**:

1. **Given** the GitHub integration layer has no tests, **When** new tests are added for the agents module, **Then** tests verify request construction, error handling for rate-limit (429), timeout, and not-found (404) responses.
2. **Given** the Copilot polling subsystem is untested, **When** new tests are added for helpers and pipeline modules, **Then** tests verify rate-limit tier logic and adaptive polling interval calculations.
3. **Given** the chores subsystem is untested, **When** new tests are added for chat and template builder modules, **Then** tests verify message construction and template rendering.
4. **Given** API routes lack coverage, **When** new tests are added for agents, health, and webhook model endpoints, **Then** tests verify route responses, input validation, and error handling.
5. **Given** all Phase 2 tests pass, **When** the coverage threshold is updated, **Then** the minimum required coverage is raised to 76% and CI enforces it.
6. **Given** mutation testing runs against the backend, **When** results identify surviving mutants, **Then** targeted tests are written to kill at least 10 previously-surviving mutants (focusing on boundary conditions, boolean negations, and arithmetic mutations).
7. **Given** all backend coverage phases complete, **When** the final coverage threshold is set, **Then** the minimum required coverage is 80% lines and 70% branches and CI enforces it.

---

### User Story 3 — Frontend Coverage Reaches Target Thresholds (Priority: P1)

As a project maintainer, I want frontend test coverage to reach at least 60% statements, 55% branches, 52% functions, and 60% lines so that hooks, services, and components containing business logic are verified against regressions.

**Why this priority**: Frontend coverage is currently at approximately 50/45/42/51% (statements/branches/functions/lines). Hooks contain core business logic and schema validators are pure functions — both categories offer the highest return on testing investment with the least complexity.

**Independent Test**: Run the frontend test suite with coverage reporting and verify all four coverage metrics meet or exceed their respective targets.

**Acceptance Scenarios**:

1. **Given** 6 schema validation files are untested, **When** new tests are added, **Then** tests verify valid and invalid inputs for every schema with zero mocking and achieve 100% coverage on those files.
2. **Given** 24 hooks are untested, **When** new tests are added in priority order (P1 business-critical first, then P2 UI state, then P3 simple), **Then** tests use the render-hook pattern with mock API, asserting query keys, mutation calls, and error states.
3. **Given** Phase 3 tests pass, **When** coverage thresholds are updated, **Then** the minimums are raised to 53/48/45/54% (statements/branches/functions/lines) and CI enforces them.
4. **Given** 53 components are untested, **When** new tests are added for settings, board, pipeline, chat, chores, tools, and agent components, **Then** tests use the provider-wrapped rendering pattern and verify accessibility compliance.
5. **Given** all frontend coverage phases complete, **When** the final coverage thresholds are set, **Then** the minimums are 60/55/52/60% (statements/branches/functions/lines) and CI enforces them.
6. **Given** mutation testing runs against the frontend, **When** results identify surviving mutants, **Then** targeted tests are written to kill at least 10 previously-surviving mutants, strengthening assertions on return values, conditional branches, and error paths.

---

### User Story 4 — Production-Parity and Time-Controlled Tests Surface Hidden Bugs (Priority: P2)

As a developer, I want tests that run under production-like configuration and control time-dependent behavior so that bugs hidden by test-mode shortcuts or timing assumptions are surfaced before deployment.

**Why this priority**: Standard tests often run with relaxed security, disabled encryption, and mocked time — masking real-world failure modes. Production-parity and time-controlled tests are the most effective way to find bugs that only manifest in production but are lower priority than achieving baseline coverage first.

**Independent Test**: Run the production-parity test suite with production configuration flags enabled and verify at least one behavior difference from test mode is detected. Run time-controlled tests and verify all 15 temporal behaviors are exercised at exact boundaries.

**Acceptance Scenarios**:

1. **Given** tests normally run with test-mode configuration, **When** production-parity tests execute with encryption enabled, webhook secrets set, CSRF enabled, and testing flag disabled, **Then** the auth flow, webhook verification, and rate limiting are exercised under production conditions.
2. **Given** invalid environment variable combinations exist, **When** production-parity tests check for them, **Then** the system reports or rejects the invalid configurations.
3. **Given** 15+ temporal behaviors exist (session expiry, token refresh, rate-limit window resets, polling backoff, reconnection delays, cache TTL, debounce timers), **When** time-controlled tests freeze time at exact boundaries (±1 second), **Then** each behavior is verified to trigger correctly at its boundary.
4. **Given** the WebSocket connection lifecycle includes connect, receive, disconnect, and reconnect states, **When** a lifecycle test exercises the full sequence including polling fallback, **Then** data freshness is verified after reconnection.

---

### User Story 5 — Architecture Fitness Tests Prevent Regression (Priority: P2)

As a developer, I want automated architectural boundary tests so that import violations and contract mismatches are caught before they accumulate into structural debt.

**Why this priority**: Without structural guards, coverage gains erode over time as developers inadvertently introduce cross-layer imports or break API contracts. These tests are preventive and complement the coverage work but depend on having a solid test infrastructure first.

**Independent Test**: Run the architecture fitness test suite and verify that all import boundary rules pass and contract validation succeeds.

**Acceptance Scenarios**:

1. **Given** backend import boundaries are defined (services never imports API, API never imports stores, models never imports services), **When** architecture tests run, **Then** violations are detected and reported, with a known-violations allowlist for pre-existing exceptions.
2. **Given** frontend import boundaries are defined (pages never imports other pages, hooks never imports components, utils never imports hooks or components), **When** architecture tests run, **Then** violations are detected and reported.
3. **Given** mock API types are defined for testing, **When** contract validation runs, **Then** mock types are verified to align with the API schema on every CI run.

---

### User Story 6 — Flaky Tests Are Detected and Eliminated (Priority: P3)

As a developer, I want an automated flaky test detection system so that unreliable tests are identified and fixed, preventing false-positive CI failures that erode developer trust.

**Why this priority**: Flaky tests undermine the value of the entire test suite. While less urgent than adding missing coverage, eliminating flakiness is essential for maintaining long-term confidence in CI results.

**Independent Test**: Run the scheduled flaky detection job and verify it correctly identifies tests with inconsistent results across 3 runs and reports the 20 slowest tests.

**Acceptance Scenarios**:

1. **Given** the flaky detection job runs on schedule, **When** the backend suite executes 3 times, **Then** any test that produces different results across runs is flagged as flaky.
2. **Given** flaky tests are identified, **When** remediation is complete, **Then** subsequent flaky detection runs report zero flaky tests.
3. **Given** the detection job completes, **When** the slowest-test report is generated, **Then** the 20 slowest tests are listed with their execution times.

---

### Edge Cases

- What happens when a newly added test is itself flaky? The flaky detection system should catch it within one scheduled cycle, and the test should be quarantined until stabilized.
- What happens when production-parity tests reveal a behavior difference that is intentional (e.g., debug logging in test mode)? Document the intentional difference and exclude it from failure reporting.
- What happens when a coverage threshold increase causes a previously passing CI pipeline to fail? The ratchet is set 2% below actual achieved coverage to allow minor fluctuations without blocking development.
- What happens when mutation testing takes longer than the CI budget allows? Mutation testing runs on a weekly schedule (not per-PR) and is non-blocking, with results uploaded as artifacts only.
- What happens when an architecture test detects a pre-existing import violation? A known-violations allowlist permits documented exceptions while still catching new violations.
- What happens when the contract validation mock types drift from the live API schema? Contract validation runs on every CI build, catching drift immediately rather than allowing it to accumulate.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1: CI Foundation

- **FR-001**: CI MUST execute backend advanced test suites (property-based, fuzz, chaos, concurrency) on every pull request with a 120-second timeout per suite.
- **FR-002**: CI MUST execute frontend fuzz tests as part of the standard frontend test run on every pull request.
- **FR-003**: CI MUST run mutation testing (backend and frontend) on a weekly schedule, uploading results as downloadable artifacts.
- **FR-004**: CI MUST run a flaky test detection job on a schedule that executes the backend suite 3 times and flags tests with inconsistent results.
- **FR-005**: Advanced test suites MUST be non-blocking (allow-failure) initially and transition to blocking once baselines stabilize.

#### Phase 2: Backend Coverage Growth

- **FR-006**: Tests MUST exist for the GitHub integration layer covering request construction, rate-limit handling (429), timeout errors, and not-found (404) responses.
- **FR-007**: Tests MUST exist for the Copilot polling subsystem covering rate-limit tier logic and adaptive interval calculations.
- **FR-008**: Tests MUST exist for the chores subsystem covering chat message construction and template rendering.
- **FR-009**: Tests MUST exist for API routes covering agents, health, and webhook model endpoints with input validation and error handling.
- **FR-010**: The backend coverage threshold MUST be raised to 76% after Phase 2 completion.

#### Phase 3: Frontend Coverage Growth — Hooks & Services

- **FR-011**: Tests MUST exist for all schema validation files with 100% coverage, using pure input/output assertions with zero mocking.
- **FR-012**: Tests MUST exist for all 24 untested hooks, prioritized by business risk (P1 business-critical, P2 UI state, P3 simple), using render-hook patterns with mock API.
- **FR-013**: Frontend coverage thresholds MUST be raised to 53/48/45/54% (statements/branches/functions/lines) after Phase 3 completion.

#### Phase 4: Frontend Coverage Growth — Components

- **FR-014**: Tests MUST exist for settings components (14 untested), following existing test patterns.
- **FR-015**: Tests MUST exist for board components (11 untested), following existing test patterns.
- **FR-016**: Tests MUST exist for pipeline components (9 untested).
- **FR-017**: Tests MUST exist for remaining untested components (chat, chores, tools, agents — approximately 19 components), using provider-wrapped rendering with accessibility validation.
- **FR-018**: Frontend coverage thresholds MUST be raised to 60/55/52/60% (statements/branches/functions/lines) after Phase 4 completion.

#### Phase 5: Mutation-Hardened Tests

- **FR-019**: Backend mutation testing MUST identify the top 20 surviving mutants and targeted tests MUST be written to kill at least 10 of them, focusing on boundary conditions, boolean negations, and arithmetic mutations.
- **FR-020**: Frontend mutation testing MUST identify the top 20 surviving mutants and targeted tests MUST be written to kill at least 10 of them, strengthening assertions on return values, conditional branches, and error paths.

#### Phase 6: Production-Parity & Time-Controlled Tests

- **FR-021**: A production-parity test suite MUST run tests with production configuration (encryption enabled, webhook secrets set, CSRF enabled, testing flag disabled) and exercise auth flow, webhook verification, and rate limiting.
- **FR-022**: Time-controlled tests MUST verify at least 15 temporal behaviors at exact boundaries (±1 second), including session expiry, token refresh timing, rate-limit window resets, polling backoff, reconnection delays, cache TTL, and debounce timers.
- **FR-023**: A WebSocket lifecycle test MUST exercise the full connection lifecycle: connect → receive → disconnect → polling fallback → reconnect → data freshness verification.

#### Phase 7: Architecture Fitness & Structural Guards

- **FR-024**: Backend architecture tests MUST verify import boundaries: services never imports API, API never imports stores directly, models never imports services. A known-violations allowlist MUST be supported.
- **FR-025**: Frontend architecture tests MUST verify import boundaries: pages never imports other pages, hooks never imports components, utils never imports hooks or components.
- **FR-026**: Contract validation MUST verify that test mock types align with the API schema on every CI run.

#### Cross-Cutting Requirements

- **FR-027**: Coverage thresholds MUST increase monotonically (ratchet pattern) — thresholds never decrease once raised.
- **FR-028**: All pre-existing tests MUST continue to pass after each phase (no regressions).
- **FR-029**: CI execution time MUST not increase by more than 90 seconds for backend or 60 seconds for frontend across all phases.

### Key Entities

- **Test Suite**: A collection of test files grouped by testing strategy (unit, property-based, fuzz, chaos, concurrency, mutation). Attributes: suite type, execution timeout, blocking/non-blocking status.
- **Coverage Threshold**: A minimum coverage percentage enforced by CI. Attributes: metric type (statements, branches, functions, lines), target percentage, enforcement phase.
- **Mutation Report**: Results from mutation testing showing surviving and killed mutants. Attributes: total mutants, killed count, surviving count, survival rate, top survivors list.
- **Architecture Rule**: An import boundary constraint between code layers. Attributes: source layer, forbidden target layer, known-violations allowlist.
- **Flaky Test Record**: A test identified as producing inconsistent results. Attributes: test name, file path, failure rate across runs, remediation status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Backend test coverage reaches at least 80% line coverage and 70% branch coverage as reported by the coverage tool.
- **SC-002**: Frontend test coverage reaches at least 60% statements, 55% branches, 52% functions, and 60% lines as reported by the coverage tool.
- **SC-003**: At least 10 previously-surviving mutants are killed per mutation-hardening phase (backend and frontend each).
- **SC-004**: CI logs confirm that property-based, fuzz, chaos, and concurrency test suites execute on every pull request.
- **SC-005**: Production-parity tests surface at least 1 behavior difference between test mode and production configuration.
- **SC-006**: Time-controlled tests cover all 15 identified temporal behaviors at exact boundary conditions.
- **SC-007**: Architecture fitness tests catch import violations and contract validation completes successfully (exit code 0) on every CI run.
- **SC-008**: Flaky test detection reports zero flaky tests after remediation is complete.
- **SC-009**: All pre-existing tests continue to pass with no regressions after each phase.
- **SC-010**: Total CI execution time increase stays within budget (backend +90 seconds maximum, frontend +60 seconds maximum across all phases).

## Assumptions

- The existing advanced test suites (property, fuzz, chaos, concurrency) are functional and pass locally; they only need CI wiring.
- The existing test patterns and helpers (factories, mock API, provider wrappers, accessibility helpers) are sufficient for new tests without requiring new test infrastructure.
- The 9 untested backend modules and 24 untested frontend hooks are stable enough to test without requiring refactoring first.
- Coverage thresholds are set 2% below actual achieved coverage to absorb minor fluctuations from code churn.
- Mutation testing is too slow for per-PR execution and will run on a weekly schedule as a quality signal.
- The known-violations allowlist for architecture tests will be populated with pre-existing violations at the time of implementation and reviewed periodically for removal.
- CI parallelization strategies can be employed if the CI budget is exceeded.

## Dependencies

- **God class decomposition (spec 033 Phase 4)**: The 5,338-line `GitHubAPIService` is the single biggest testing obstacle. Backend Phase 2 tests will be more maintainable after the class is split. Interleaving this decomposition with coverage work is recommended.
- **Existing test infrastructure**: All new tests depend on existing fixtures, factories, mock API factories, and rendering helpers being functional and up to date.
- **CI workflow configuration**: Phases 1, 3–4, and 7 require modifications to CI workflow definitions.

## Scope Boundaries

### In Scope

- Unit and integration test additions for backend and frontend
- CI pipeline changes for advanced test suites, mutation testing, and flaky detection
- Coverage threshold ratcheting
- Architecture fitness tests (import boundaries, contract validation)
- Production-parity and time-controlled test suites

### Out of Scope

- End-to-end (E2E) / Playwright test expansion — excluded to keep CI fast; follow-up effort
- Refactoring untested modules to improve testability (tests should be written against current interfaces)
- Performance benchmarking beyond the CI budget constraints
- Visual regression testing
