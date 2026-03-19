# Feature Specification: Find/Fix Bugs & Increase Test Coverage

**Feature Branch**: `050-fix-bugs-test-coverage`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Plan: Find/Fix Bugs & Increase Test Coverage"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Fix Known Bugs Blocking Test Infrastructure (Priority: P1)

As a developer, I want all known bugs that block or degrade test infrastructure to be resolved so that existing and new tests produce trustworthy, deterministic results.

**Why this priority**: Broken infrastructure wastes all downstream effort. If mutation testing reports 0% kill rate due to a trampoline bug, or tests leak state through an uncleared cache, every subsequent coverage expansion is built on a false foundation. Fixing these bugs first is the highest-value action.

**Independent Test**: Can be fully tested by running the complete backend test suite and verifying zero warnings, zero flaky failures, and non-zero mutation kill rates.

**Acceptance Scenarios**:

1. **Given** the mutation testing tool is invoked on backend services, **When** it completes a full run, **Then** the kill rate is above 0% per shard (confirming the trampoline name-resolution bug is fixed).
2. **Given** unit and integration tests run in the same session, **When** one test modifies cached data, **Then** subsequent tests in other suites do not observe stale values (confirming cache leakage is fixed).
3. **Given** the integration test suite runs, **When** async service doubles are used, **Then** no deprecation or runtime warnings related to mock objects appear in the output.
4. **Given** a pipeline is being monitored by the copilot polling service, **When** a status transition occurs (e.g., "Queued" → "In Progress" → "Completed"), **Then** the transition is accepted and persisted without reverting to a previous state.

---

### User Story 2 — Discover and Triage Existing Defects via Static Analysis (Priority: P2)

As a developer, I want a systematic sweep of static analysis and test execution across backend and frontend codebases so that all latent type errors, lint violations, and test failures are surfaced before new tests are written.

**Why this priority**: Static analysis catches entire categories of defects (type mismatches, unreachable code, unused imports) cheaply and quickly. Running existing test suites exposes runtime failures. Together they produce a prioritized defect backlog. This must happen before expanding coverage to avoid writing tests against broken code.

**Independent Test**: Can be fully tested by running lint, type-check, and test suites against both codebases and verifying the error report is generated.

**Acceptance Scenarios**:

1. **Given** the backend codebase, **When** lint and type-check tools are executed, **Then** a report of all violations is produced and each finding is triaged as fix-now, fix-later, or false-positive.
2. **Given** the frontend codebase, **When** lint and type-check tools are executed, **Then** a report of all violations is produced and each finding is triaged.
3. **Given** the backend test suite, **When** all tests are executed, **Then** a machine-readable results file is produced listing pass, fail, and error counts.
4. **Given** the backend test suite has been run multiple times, **When** flaky test detection is performed across 5+ runs, **Then** genuinely flaky tests are identified and quarantined, and their root causes (async timing, shared state) are documented for fixing.

---

### User Story 3 — Expand Backend Test Coverage (Priority: P3)

As a developer, I want backend test coverage to increase from 75% to at least 80% (with a stretch goal of 85%+) by targeting high-risk, critical-path modules so that the most important code paths are protected against regressions.

**Why this priority**: Once bugs are fixed and infrastructure is sound (P1–P2), expanding coverage on the highest-risk modules delivers the most regression-prevention value per test written. Risk-first targeting (state machines, recovery logic, guard enforcement) protects critical business logic rather than easy-to-cover utility code.

**Independent Test**: Can be fully tested by running the backend test suite with coverage reporting and verifying the overall percentage meets the target threshold.

**Acceptance Scenarios**:

1. **Given** API routes have zero integration tests, **When** integration tests are added for auth flow, webhook dispatch, pipeline CRUD, and chat messages, **Then** each route responds correctly to valid and invalid inputs.
2. **Given** high-risk service modules (recovery logic, state validation, transitions, signal pipeline, guard enforcement) lack tests, **When** unit and property-based tests are added, **Then** each module's core behaviors and edge cases are covered.
3. **Given** mutation testing covers only service modules, **When** mutation targets are expanded to include API routes, middleware, and utilities, **Then** surviving mutants are identified and killed with targeted assertions.
4. **Given** DRY refactoring candidates exist in the codebase, **When** characterization tests are added for repo-resolution paths and error-response patterns, **Then** the current behavior is pinned by regression tests before any refactoring occurs.

---

### User Story 4 — Expand Frontend Test Coverage (Priority: P4)

As a developer, I want frontend test coverage to increase from 51% statements to at least 55% (with a stretch goal of 65%+) by covering untested components, branch paths, and adding E2E specs so that the user-facing application is protected against visual and functional regressions.

**Why this priority**: Frontend coverage lags behind backend. Targeting zero-coverage components (App.tsx), partial-coverage board components, and low branch coverage in hooks provides the highest marginal value. E2E specs validate end-to-end user flows that unit tests cannot.

**Independent Test**: Can be fully tested by running the frontend test suite with coverage reporting and the E2E suite, and verifying percentages meet targets.

**Acceptance Scenarios**:

1. **Given** App.tsx has 0% coverage, **When** tests are added for route rendering, auth guards, and error boundaries, **Then** App.tsx coverage rises above 70%.
2. **Given** board components have partial coverage, **When** interaction tests are added for column drag-drop, card rendering, and project switching, **Then** board component coverage increases by at least 10 percentage points.
3. **Given** hooks have 44% branch coverage, **When** tests are added for error states, loading states, empty data, and API failures, **Then** branch coverage rises above 50%.
4. **Given** the E2E suite has 10 specs, **When** 4 new specs are added (agent creation, pipeline monitoring, MCP tool configuration, error recovery), **Then** the E2E suite has at least 14 passing specs.

---

### User Story 5 — Harden CI Gates and Prevent Regression (Priority: P5)

As a developer, I want CI coverage thresholds ratcheted up, pre-commit hooks strengthened, and chaos/concurrency tests added so that quality improvements are locked in and cannot silently degrade over time.

**Why this priority**: Without enforcement, coverage gains erode. Ratcheting thresholds ensures every merge maintains or improves coverage. Stronger pre-commit hooks catch issues before they reach CI. Chaos and concurrency tests guard against the hardest-to-reproduce production failures.

**Independent Test**: Can be fully tested by attempting to merge code that lowers coverage below thresholds and verifying it is rejected.

**Acceptance Scenarios**:

1. **Given** backend coverage threshold is 75%, **When** the threshold is ratcheted to 80%, **Then** any future code change that drops coverage below 80% fails the CI gate.
2. **Given** frontend coverage thresholds are 50% statements / 44% branches / 41% functions, **When** thresholds are ratcheted to 55% / 50% / 45%, **Then** any future code change that drops below these thresholds fails the CI gate.
3. **Given** a developer modifies backend files, **When** they attempt to commit, **Then** pre-commit hooks automatically run lint and type-check on the changed files and block the commit if violations are found.
4. **Given** a developer modifies frontend files, **When** they attempt to commit, **Then** pre-commit hooks automatically run lint and type-check on the changed files and block the commit if violations are found.
5. **Given** the system handles concurrent operations, **When** chaos and concurrency tests are executed (concurrent state updates, connection pool exhaustion, reconnection under load), **Then** the system behaves correctly without data corruption or deadlocks.

---

### Edge Cases

- What happens when a test that was previously quarantined as flaky is fixed but the quarantine flag is not removed? The system must have a process to re-enable quarantined tests after fixes.
- How does the system handle mutation testing timing out on large modules? Sharding must distribute work evenly and handle shard failures gracefully.
- What happens when coverage thresholds are ratcheted but a critical hotfix must be merged with lower coverage? A documented override process must exist for emergency situations (e.g., a CI bypass label with mandatory post-merge coverage restoration).
- What happens when pre-commit hooks add significant delay to developer workflow? Hooks must run only on changed files, not the entire codebase, to keep commit times under 30 seconds.
- How does the system handle E2E test environment unavailability? E2E failures due to environment issues must be distinguishable from genuine test failures.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Static Analysis & Error Discovery**

- **FR-001**: The project MUST support running a full lint and type-check sweep across the backend codebase that surfaces type errors, unused imports, and unreachable code.
- **FR-002**: The project MUST support running a full lint and type-check sweep across the frontend codebase that surfaces type errors, lint violations, and unreachable code.
- **FR-003**: The project MUST support executing all existing backend test suites and producing a machine-readable results report with pass/fail/error counts.
- **FR-004**: The project MUST support executing all existing frontend test suites (unit and E2E) and producing verbose results.
- **FR-005**: The project MUST support flaky test detection by running backend tests across multiple iterations (5+) and reporting inconsistent results.
- **FR-006**: Genuinely flaky tests MUST be quarantined with documented root causes and a process for re-enabling them after fixes.

**Phase 2 — Fix Known Bugs**

- **FR-007**: The mutation testing trampoline MUST correctly resolve mutant names so that the kill rate reflects actual mutation survival, not a name-mismatch bug.
- **FR-008**: The test cache MUST be fully cleared between unit and integration test boundaries so that no cached state leaks across suites.
- **FR-009**: Integration tests MUST NOT produce async mock-related deprecation or runtime warnings.
- **FR-010**: The copilot polling pipeline MUST accept valid status transitions without reverting to previous states (fixing the "stuck in In Progress" bug).

**Phase 3 — Backend Coverage Expansion**

- **FR-011**: Integration tests MUST exist for all primary API routes, including auth flow, webhook dispatch, pipeline CRUD, and chat message endpoints.
- **FR-012**: Unit tests MUST cover the following high-risk service modules: recovery logic, state validation, workflow transitions, signal pipeline, and guard enforcement.
- **FR-013**: Property-based tests MUST be used for state machines and parsers to verify invariants across a wide range of inputs.
- **FR-014**: Mutation testing targets MUST be expanded beyond service modules to include API routes, middleware, and utility modules.
- **FR-015**: Characterization tests MUST pin the current behavior of repo-resolution paths and error-response patterns before any DRY refactoring occurs.

**Phase 4 — Frontend Coverage Expansion**

- **FR-016**: Tests MUST cover the App.tsx component, including route rendering, auth guards, and error boundaries.
- **FR-017**: Interaction tests MUST cover board components, including column drag-drop, card rendering, and project switching.
- **FR-018**: Tests MUST cover conditional branch paths in hooks, including error states, loading states, empty data, and API failure scenarios.
- **FR-019**: The E2E test suite MUST include at least 4 additional specs covering agent creation, pipeline monitoring, MCP tool configuration, and error recovery flows.
- **FR-020**: Frontend mutation testing MUST be run, and surviving mutants in hooks and library modules MUST be killed with targeted assertions.

**Phase 5 — Hardening & CI Gates**

- **FR-021**: Backend coverage threshold MUST be ratcheted from 75% to 80% (never lowered).
- **FR-022**: Frontend coverage thresholds MUST be ratcheted to at least 55% statements, 50% branches, and 45% functions (never lowered).
- **FR-023**: Pre-commit hooks MUST run lint and type-check on changed backend files before allowing a commit.
- **FR-024**: Pre-commit hooks MUST run lint and type-check on changed frontend files before allowing a commit.
- **FR-025**: Chaos and concurrency tests MUST cover concurrent pipeline state updates, connection pool exhaustion, and reconnection under load.

### Key Entities

- **Test Suite**: A collection of test files targeting a specific codebase area (unit, integration, E2E, property-based, chaos). Attributes: scope, pass rate, coverage percentage, flaky test count.
- **Coverage Report**: A measurement of code exercised by tests. Attributes: statement coverage, branch coverage, function coverage, target threshold, pass/fail status.
- **Mutation Report**: A measurement of test effectiveness via code mutations. Attributes: total mutants, killed mutants, survived mutants, kill rate, shard assignment.
- **Flaky Test Record**: A test identified as producing inconsistent results. Attributes: test name, failure rate, root cause category, quarantine status, fix status.
- **CI Gate**: A quality enforcement checkpoint in the continuous integration pipeline. Attributes: metric type, threshold value, enforcement action (block/warn).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All known bugs (mutation trampoline, cache leakage, async mock warnings, pipeline stuck state) are resolved and verified by passing tests with zero related warnings.
- **SC-002**: Backend test coverage reaches at least 80% overall, verified by the coverage tool's threshold enforcement.
- **SC-003**: Frontend statement coverage reaches at least 55%, branch coverage at least 50%, and function coverage at least 45%, verified by the coverage tool's threshold enforcement.
- **SC-004**: Flaky test detection across 10 runs reports zero flaky tests.
- **SC-005**: Backend mutation testing achieves a kill rate above 60% per shard.
- **SC-006**: Frontend mutation testing score meets or exceeds the configured thresholds.
- **SC-007**: The E2E test suite contains at least 14 passing specs (up from 10).
- **SC-008**: All backend tests pass with zero async mock warnings.
- **SC-009**: Pre-commit hooks execute lint and type-check on changed files, completing in under 30 seconds for typical changesets.
- **SC-010**: Coverage thresholds are enforced in CI — any merge request that lowers coverage below the ratcheted thresholds is automatically rejected.

## Assumptions

- The existing test infrastructure (test runners, coverage tools, mutation tools) is already installed and configured in the project. This feature focuses on fixing, expanding, and hardening — not on initial tool setup.
- The "fix before expand" principle means Phase 2 (bug fixes) must be completed before Phase 3–4 (coverage expansion) to avoid building on broken infrastructure.
- Coverage percentage targets (80% backend, 55%/50%/45% frontend) represent ratcheted minimums. Actual coverage may exceed these targets.
- Threshold ratcheting is one-directional: thresholds may only be raised, never lowered, once the codebase consistently meets them in CI.
- DRY refactoring is explicitly out of scope. Characterization tests will pin current behavior, but refactoring will occur in a separate effort.
- Emergency hotfix merges that temporarily lower coverage require a documented override process with mandatory post-merge coverage restoration.
- Pre-commit hooks run only on changed files (not the full codebase) to maintain developer productivity.
- Property-based testing is used for state machines and parsers where exhaustive input enumeration is impractical.
- Chaos and concurrency tests target known risk areas (concurrent state updates, connection pool exhaustion, reconnection) rather than attempting exhaustive failure-mode coverage.
