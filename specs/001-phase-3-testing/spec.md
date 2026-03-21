# Feature Specification: Phase 3 — Testing

**Feature Branch**: `001-phase-3-testing`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Phase 3: Testing — Raise frontend coverage thresholds, backend coverage for critical paths, end-to-end integration tests, mutation testing in CI, and property-based tests for state machines"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Raise Frontend Coverage Thresholds (Priority: P1)

As a development team, we need frontend test coverage thresholds raised from the current 50% statements / 44% branches / 41% functions to 75%+ across all three metrics so that code changes are validated against a meaningful safety net before merging.

**Why this priority**: The current thresholds are well below industry standard (typically 70–80%). Low thresholds allow large swaths of untested code to ship, increasing the likelihood of regressions reaching production. Raising thresholds provides the highest immediate risk-reduction value.

**Independent Test**: Can be fully tested by running the frontend test suite with coverage enforcement (`npm run test:coverage`) and verifying all three metrics meet or exceed 75%. Delivers value by catching regressions that currently slip through.

**Acceptance Scenarios**:

1. **Given** the frontend test suite runs with coverage enabled, **When** a developer triggers `npm run test:coverage`, **Then** the suite passes only if statement coverage ≥ 75%, branch coverage ≥ 75%, and function coverage ≥ 75%.
2. **Given** a pull request introduces new frontend code without corresponding tests, **When** CI runs, **Then** the build fails if any coverage metric drops below the 75% threshold.
3. **Given** the current test suite, **When** coverage is measured before any new tests are written, **Then** the team can identify which modules need additional tests to meet the new thresholds.

---

### User Story 2 — Backend Coverage for Critical Paths (Priority: P1)

As a development team, we need targeted test coverage improvements for the backend orchestration modules — specifically `board.py` (currently ~47% coverage), `pipelines.py` (currently ~64%), and `polling/pipeline.py` (currently ~72%) — so that the most complex and critical code paths are adequately protected.

**Why this priority**: These three modules form the core orchestration logic. With approximately 300+ untested statements across them, regressions in pipeline transitions, board state management, and polling behavior can cause silent failures that are difficult to diagnose. Jointly P1 with frontend coverage because backend orchestration failures are more severe than UI bugs.

**Independent Test**: Can be fully tested by running `pytest --cov=src --cov-report=term-missing` and verifying that coverage for `board.py`, `pipelines.py`, and `polling/pipeline.py` each reaches 80%+. Delivers value by ensuring the most critical backend code is exercised.

**Acceptance Scenarios**:

1. **Given** the backend test suite runs with coverage enabled, **When** coverage is reported per-file, **Then** `board.py` achieves ≥ 80% line coverage.
2. **Given** the backend test suite runs with coverage enabled, **When** coverage is reported per-file, **Then** `pipelines.py` achieves ≥ 80% line coverage.
3. **Given** the backend test suite runs with coverage enabled, **When** coverage is reported per-file, **Then** `polling/pipeline.py` achieves ≥ 80% line coverage.
4. **Given** a developer modifies orchestration logic in any of these three modules, **When** CI runs, **Then** the build fails if per-file coverage for the modified module drops below 80%.

---

### User Story 3 — End-to-End Integration Tests (Priority: P2)

As a development team, we need end-to-end integration tests that exercise the full workflow — issue creation → agent assignment → pull request creation → code review → merge → cleanup — so that we can verify the entire multi-service pipeline works correctly as a whole.

**Why this priority**: Currently no multi-service integration tests exist. Individual unit and integration tests verify components in isolation, but the complete workflow from issue to cleanup has never been tested end-to-end. This is P2 because it depends on adequate unit-level coverage (P1) to be meaningful and because E2E tests are slower and more brittle than unit tests.

**Independent Test**: Can be fully tested by triggering the E2E test suite in a test environment and verifying each stage of the workflow completes successfully. Delivers value by catching integration failures between services.

**Acceptance Scenarios**:

1. **Given** a test environment with all services running, **When** the E2E test suite creates a new issue, **Then** the system assigns an agent to the issue within the expected time window.
2. **Given** an agent has been assigned to an issue, **When** the agent produces a pull request, **Then** the PR is created against the correct branch and contains the expected changes.
3. **Given** a pull request exists, **When** the review process completes and the PR is merged, **Then** the system performs cleanup (branch deletion, issue status update) automatically.
4. **Given** any stage of the workflow fails, **When** the E2E test detects the failure, **Then** it reports which stage failed with sufficient diagnostic information for debugging.

---

### User Story 4 — Mutation Testing Enforcement in CI (Priority: P2)

As a development team, we need mutation testing results to be enforced in CI with defined thresholds so that we can detect weak tests that pass despite meaningful code changes, ensuring our test suite genuinely validates behavior rather than merely executing code.

**Why this priority**: Mutation testing tools (mutmut for backend, Stryker for frontend) are already installed and configured but run as non-blocking informational checks. Without enforcement, teams ignore mutation results. This is P2 because it provides the most value after baseline coverage (P1) is established.

**Independent Test**: Can be fully tested by running mutation testing in CI and verifying the build fails when the mutation score drops below the defined threshold. Delivers value by ensuring test suite quality, not just quantity.

**Acceptance Scenarios**:

1. **Given** the backend mutation testing workflow runs, **When** the overall mutation score is below the minimum threshold, **Then** the CI job fails and blocks the PR.
2. **Given** the frontend mutation testing workflow runs, **When** the mutation score is below the minimum threshold, **Then** the CI job fails and blocks the PR.
3. **Given** a developer introduces a code change that lowers the mutation score below the threshold, **When** CI runs, **Then** the developer receives a clear report indicating which surviving mutants need additional tests.
4. **Given** mutation testing passes, **When** CI reports the results, **Then** a summary of the mutation score and surviving mutant count is visible in the CI output.

---

### User Story 5 — Property-Based Tests for State Machines (Priority: P3)

As a development team, we need property-based tests using Hypothesis (backend) and fast-check (frontend) for pipeline state transitions and the blocking queue so that we can discover subtle edge cases in state machine logic that conventional example-based tests miss.

**Why this priority**: State machines have subtle edge cases around transition ordering, concurrent state changes, and boundary conditions that are difficult to enumerate manually. Property-based testing generates hundreds of randomized scenarios to find these issues. This is P3 because it is an advanced testing technique that builds on top of basic coverage (P1) and mutation testing (P2).

**Independent Test**: Can be fully tested by running property-based test suites and verifying they pass with a CI-appropriate number of examples. Delivers value by finding edge cases in pipeline transitions and blocking queue behavior.

**Acceptance Scenarios**:

1. **Given** the backend property-based test suite runs, **When** Hypothesis generates randomized sequences of pipeline state transitions, **Then** all state invariants hold (no invalid transitions, no orphaned states, no deadlocks).
2. **Given** the frontend property-based test suite runs, **When** fast-check generates randomized inputs for state-dependent components, **Then** all component invariants hold.
3. **Given** a property-based test discovers a failing case, **When** the test report is generated, **Then** it includes a minimal reproducing example that can be used to write a regression test.
4. **Given** property-based tests run in CI, **When** the Hypothesis CI profile is active, **Then** tests use a sufficient number of examples (higher than default) to balance thoroughness with execution time.

---

### Edge Cases

- What happens when coverage thresholds are raised but existing tests are flaky? Flaky tests must be identified and stabilized before thresholds are enforced.
- How does the system handle E2E test timeouts when external services (GitHub API) are slow or rate-limited? Tests must use appropriate timeouts and retry logic with clear timeout failure messages.
- What happens when mutation testing produces equivalent mutants (code changes that don't affect behavior)? These should be documented and excluded from the mutation score calculation where the tooling supports it.
- How are property-based test failures handled when they produce non-deterministic results? Hypothesis and fast-check both support seed-based reproducibility; CI must log the failing seed for reproduction.
- What happens when new code is added that is inherently difficult to test (e.g., third-party API integrations)? Coverage exclusion markers (`pragma: no cover`, `istanbul ignore`) should be used sparingly and require justification in code review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The frontend CI pipeline MUST enforce coverage thresholds of ≥ 75% for statements, branches, and functions, failing the build when any metric falls below the threshold.
- **FR-002**: The backend CI pipeline MUST enforce per-file coverage thresholds of ≥ 80% for `board.py`, `pipelines.py`, and `polling/pipeline.py`, failing the build when any file falls below.
- **FR-003**: The backend CI pipeline MUST maintain its existing overall coverage threshold of 75% (fail_under in pytest-cov configuration).
- **FR-004**: An E2E integration test suite MUST exist that exercises the complete workflow: issue creation → agent assignment → pull request creation → review → merge → cleanup.
- **FR-005**: The E2E test suite MUST report which workflow stage failed when a test fails, including diagnostic information sufficient for debugging.
- **FR-006**: Backend mutation testing (mutmut) MUST be configured as a blocking CI check with a defined minimum mutation score threshold.
- **FR-007**: Frontend mutation testing (Stryker) MUST be configured as a blocking CI check with a defined minimum mutation score threshold.
- **FR-008**: Mutation testing CI jobs MUST produce a human-readable summary of results including mutation score percentage and count of surviving mutants.
- **FR-009**: Property-based tests using Hypothesis MUST exist for backend pipeline state transitions covering all valid transition sequences and verifying state invariants.
- **FR-010**: Property-based tests using Hypothesis MUST exist for the backend blocking queue covering concurrent enqueue/dequeue operations and capacity constraints.
- **FR-011**: Property-based tests using fast-check MUST exist for frontend state-dependent logic covering state transition invariants.
- **FR-012**: Property-based tests MUST run in CI with a dedicated profile that uses a higher example count than the default for thorough testing.
- **FR-013**: All new tests MUST follow the existing project test organization structure (unit tests in `tests/unit/`, property tests in `tests/property/`, integration tests in `tests/integration/`).

### Key Entities

- **Coverage Report**: Represents a per-file and aggregate coverage measurement for a test suite run. Key attributes: file path, statement coverage percentage, branch coverage percentage, function coverage percentage, uncovered line numbers.
- **Mutation Report**: Represents the results of mutation testing for a codebase section. Key attributes: total mutants generated, mutants killed, mutants survived, mutation score percentage, list of surviving mutant locations.
- **E2E Workflow Run**: Represents a single execution of the full end-to-end workflow test. Key attributes: workflow stages completed, stage durations, pass/fail status per stage, diagnostic output for failures.
- **State Invariant**: Represents a property that must hold true across all valid state transitions. Key attributes: invariant description, applicable states, violation conditions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Frontend test coverage meets or exceeds 75% for statements, branches, and functions (up from 50% / 44% / 41%).
- **SC-002**: Backend coverage for `board.py` reaches ≥ 80% (up from ~47%).
- **SC-003**: Backend coverage for `pipelines.py` reaches ≥ 80% (up from ~64%).
- **SC-004**: Backend coverage for `polling/pipeline.py` reaches ≥ 80% (up from ~72%).
- **SC-005**: At least one E2E integration test exercises the full issue → assign → PR → review → merge → cleanup workflow and passes consistently (≥ 95% pass rate over 20 consecutive runs).
- **SC-006**: Backend mutation testing runs as a blocking CI check with a minimum mutation score of 60%.
- **SC-007**: Frontend mutation testing runs as a blocking CI check with a minimum mutation score of 60%.
- **SC-008**: Property-based tests cover all valid pipeline state transitions (every transition in the state machine is exercised by at least one property test).
- **SC-009**: Property-based tests for the blocking queue verify capacity constraints, ordering guarantees, and concurrent access safety.
- **SC-010**: All CI checks related to testing complete within the existing CI time budget (no more than 25% increase in total CI duration).

### Assumptions

- The current test infrastructure (Vitest, pytest, Stryker, mutmut, Hypothesis, fast-check, Playwright) remains the standard tooling. No new testing frameworks need to be introduced.
- The 75% frontend coverage target is achievable by adding tests to existing untested modules without requiring architectural changes.
- The 80% per-file backend coverage target for the three critical modules is achievable by adding tests that exercise existing code paths, not by reducing module complexity.
- Mutation testing thresholds of 60% are a reasonable starting point and can be raised incrementally as the test suite matures.
- E2E tests will run against a test environment that mocks or stubs external service dependencies (GitHub API) where necessary to ensure deterministic and timely execution.
- The existing CI infrastructure supports the additional test execution without requiring new compute resources or significantly increased CI costs.

### Scope Boundaries

**In Scope**:
- Raising frontend coverage thresholds and writing tests to meet them
- Writing targeted tests for `board.py`, `pipelines.py`, and `polling/pipeline.py`
- Creating E2E integration tests for the full workflow
- Configuring mutation testing as blocking CI checks with thresholds
- Writing property-based tests for state machines and blocking queue
- Updating CI workflow configurations

**Out of Scope**:
- Refactoring existing code to improve testability (unless directly required to write a specific test)
- Introducing new testing frameworks or replacing existing ones
- Performance testing or load testing
- Security testing (covered by existing bandit/audit tools)
- UI visual regression testing
- Test infrastructure for services outside the Solune application
