# Feature Specification: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature Branch**: `052-fix-bugs-test-coverage`
**Created**: 2026-03-19
**Status**: Draft
**Input**: User description: "Systematically discover bugs via static analysis, mutation testing, and error-path auditing across the Solune monorepo (Python/FastAPI backend + React/TypeScript frontend), then increase test coverage to hardened thresholds (backend 75→80% lines, frontend 51→55% statements). Five phases: static sweep, backend coverage, frontend coverage, mutation verification, CI enforcement."

**Predecessor**: `050-fix-bugs-test-coverage` (42% complete — all 4 critical bugs fixed, infrastructure established) and `051-fix-bugs-test-coverage` (planning completed with 67 tasks defined across 5 user stories).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Complete Static Analysis Sweep (Priority: P1)

As a developer, I want all lint, type-check, and security violations resolved across the entire monorepo so that the codebase has zero static analysis warnings and all flaky tests are quarantined with documented root causes.

**Why this priority**: Static analysis violations mask real bugs and block reliable automated testing. Every subsequent phase depends on a clean, warning-free baseline. Flaky tests erode trust in the test suite, making it impossible to verify coverage improvements.

**Independent Test**: Run the full static analysis tool chain (linter, type-checker, security scanner) and the flaky test detection script. The feature delivers value when every tool exits cleanly and no tests produce intermittent results.

**Acceptance Scenarios**:

1. **Given** the frontend codebase has lint violations, **When** the developer runs the linter, **Then** it exits with zero violations and zero warnings.
2. **Given** the frontend has type errors under strict mode, **When** the developer runs the type-checker in strict mode, **Then** it exits with zero errors.
3. **Given** the backend codebase may have lint, type, or security issues, **When** the developer runs the linter, type-checker, and security scanner, **Then** all three tools exit with zero violations.
4. **Given** the test suites may contain flaky tests, **When** the developer runs the flaky detection process (5 iterations per suite), **Then** any confirmed flaky tests are quarantined with a documented root cause and a corresponding issue filed.
5. **Given** the test suites emit deprecation or library warnings, **When** the developer runs the test suites, **Then** zero deprecation warnings are emitted (specifically zero AsyncMock-related warnings).

---

### User Story 2 — Raise Backend Line Coverage to 80% (Priority: P2)

As a developer, I want backend line coverage increased from the current 75% threshold to 80% by adding integration tests for high-risk API routes, unit tests for orphan modules, edge-case tests for high-risk services, and property-based tests for complex state logic, so that regressions in critical paths are caught before deployment.

**Why this priority**: The backend contains the core business logic — authentication, webhook processing, pipeline orchestration, and signal delivery. Gaps in these areas represent the highest risk of production incidents. Coverage increase must be verified before mutation testing can meaningfully run.

**Independent Test**: Run the test suite with coverage enforcement at the 80% threshold. The feature delivers value when the coverage gate passes and the newly covered paths include all identified high-risk modules.

**Acceptance Scenarios**:

1. **Given** four high-risk API routes (auth callback, webhook dispatch, pipeline launch, chat confirm) lack integration tests, **When** the developer adds integration tests using the established client fixture pattern, **Then** each route has at least one happy-path and one error-path integration test.
2. **Given** orphan modules (dependency injection, request ID middleware) have no dedicated test files, **When** the developer adds unit tests, **Then** each module has a dedicated test file with tests covering its public interface.
3. **Given** high-risk services (recovery logic, state validation, signal bridge, guard service, signal delivery) have coverage gaps in error handling and edge cases, **When** the developer adds edge-case tests, **Then** each service's error/boundary paths are exercised.
4. **Given** complex state logic exists in the pipeline state machine and markdown parser, **When** the developer adds property-based tests with at least 100 generated examples, **Then** no invalid state transitions pass and parser roundtrips are verified.
5. **Given** mutation testing currently only targets the services directory, **When** the developer expands mutation targets to include API routes and middleware, **Then** the mutation shard configuration includes these new targets distributed across existing shards.
6. **Given** all new tests are added, **When** the developer runs coverage with the 80% threshold, **Then** the coverage gate passes.

---

### User Story 3 — Raise Frontend Coverage to 55/50/45 (Priority: P3)

As a developer, I want frontend statement, branch, and function coverage increased to 55%, 50%, and 45% respectively by adding component tests for untested board components, hook tests with branch coverage, utility tests, and service layer tests, so that UI regressions and logic errors are caught before release.

**Why this priority**: The frontend has the most visible coverage gaps — 14 of 32 board components lack tests, 3 hooks are untested, and only 1 service test file exists. These gaps mean UI regressions can ship undetected. This is lower priority than backend coverage because the backend carries more business-critical logic.

**Independent Test**: Run the frontend test suite with coverage enforcement at the new thresholds. The feature delivers value when the coverage gate passes and untested board components, hooks, and utilities all have test files.

**Acceptance Scenarios**:

1. **Given** five key board components (ProjectBoard, BoardToolbar, CleanUpConfirmModal, AgentColumnCell, BoardDragOverlay) lack tests, **When** the developer adds component tests with the required provider wrappers, **Then** each component has a test file exercising its primary render and interaction paths.
2. **Given** three hooks (useBoardDragDrop, useConfirmation, useUnsavedPipelineGuard) are untested, **When** the developer adds hook tests, **Then** each hook has tests covering at least 5 branch paths (success, error, loading, empty, edge-case).
3. **Given** four utility modules (lazyWithRetry, commands, formatAgentName, generateId) have gaps, **When** the developer adds utility tests, **Then** each module has a test file covering its public exports.
4. **Given** the services layer has only 1 test file, **When** the developer adds service tests covering error handling, retry logic, and response parsing, **Then** the services layer has meaningful test coverage beyond the API client.
5. **Given** all new tests are added, **When** the developer runs coverage with thresholds 55/50/45, **Then** the coverage gate passes.

---

### User Story 4 — Verify Mutation Kill Rates (Priority: P4)

As a developer, I want mutation testing executed across all backend shards and the frontend mutation suite, with surviving mutants triaged and killable survivors addressed, so that test quality is verified beyond line coverage metrics.

**Why this priority**: Line coverage alone does not guarantee test quality — a test that executes a line without asserting behavior provides false confidence. Mutation testing verifies that tests actually detect behavioral changes. This depends on coverage expansion (P2/P3) being complete.

**Independent Test**: Run all mutation testing shards and the frontend mutation suite. The feature delivers value when kill rates exceed 60% per shard and all killable survivors have targeted assertions.

**Acceptance Scenarios**:

1. **Given** four backend mutation shards exist (auth-and-projects, orchestration, app-and-data, agents-and-integrations), **When** the developer executes each shard, **Then** each shard reports results and completes within CI timeout.
2. **Given** the frontend mutation suite targets hooks and lib modules, **When** the developer executes the mutation suite, **Then** it reports results and completes within CI timeout.
3. **Given** mutation results show surviving mutants, **When** the developer triages each survivor, **Then** each is classified as killable, equivalent, or non-killable with documented justification.
4. **Given** killable mutant survivors are identified, **When** the developer writes targeted assertions, **Then** the kill rate improves and all killable survivors are addressed.

---

### User Story 5 — Enforce Thresholds and Harden CI (Priority: P5)

As a developer, I want coverage thresholds ratcheted upward in configuration, pre-commit hooks verified to complete quickly, an emergency override process documented, and final reports generated, so that quality gains are locked in and cannot regress.

**Why this priority**: Without CI enforcement, coverage gains erode over time as new code is added without tests. This is the final phase because it locks in the work from all previous stories. It must be the last step to avoid blocking development on thresholds that haven't been met yet.

**Independent Test**: Push a commit that intentionally lowers coverage and verify CI rejects it. Run pre-commit hooks and verify they complete within the time budget. The feature delivers value when ratcheted thresholds are enforced and the override process is documented.

**Acceptance Scenarios**:

1. **Given** backend coverage now meets 80%, **When** the developer updates the coverage threshold configuration to 80%, **Then** a commit that drops below 80% is rejected by CI.
2. **Given** frontend coverage now meets 55/50/45, **When** the developer updates the coverage threshold configuration, **Then** a commit that drops below the thresholds is rejected by CI.
3. **Given** pre-commit hooks may have grown slower with added checks, **When** the developer runs pre-commit on a set of changed files, **Then** execution completes in under 30 seconds.
4. **Given** hotfix situations may require bypassing coverage gates, **When** the developer follows the documented emergency override process, **Then** the bypass is logged and traceable for audit.
5. **Given** all phases are complete, **When** final reports are generated, **Then** coverage HTML reports and mutation reports are produced and stored.

---

### Edge Cases

- What happens when a flaky test is detected only on the 5th run out of 5? It is still quarantined; a single intermittent failure is sufficient for quarantine with documented root cause.
- What happens when coverage improvement in one module causes a regression in another module's tests? All existing tests must continue to pass; no coverage improvement justifies breaking existing behavior.
- What happens when a mutation shard exceeds CI timeout? The shard is split further (by sub-module) or its max-children parameter is reduced to run fewer mutations per CI job.
- What happens when a surviving mutant is in dead code? It is classified as equivalent/non-killable with justification documented, and the dead code is flagged for removal in a future cleanup effort.
- What happens when the emergency hotfix override is used but never reverted? The override must include an expiration mechanism or post-merge check that fails if the override flag persists beyond one merge.
- What happens when property-based tests discover a real bug via a generated input? The bug is fixed immediately and a deterministic regression test is added using the failing input as a concrete test case.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The linter MUST report zero violations across the entire frontend codebase.
- **FR-002**: The type-checker MUST report zero errors in strict mode across the entire frontend codebase.
- **FR-003**: The linter MUST report zero violations across the entire backend codebase.
- **FR-004**: The type-checker MUST report zero errors across the entire backend codebase.
- **FR-005**: The security scanner MUST report zero issues across the backend codebase (with documented exception suppressions only for false positives).
- **FR-006**: The flaky test detection process MUST execute at least 5 iterations per test suite.
- **FR-007**: Every confirmed flaky test MUST be quarantined with a skip marker and documented root cause.
- **FR-008**: Every confirmed flaky test MUST have a corresponding tracked issue.
- **FR-009**: The test suites MUST emit zero AsyncMock deprecation warnings.
- **FR-010**: Integration tests MUST exist for 4 high-risk backend API routes: auth callback, webhook dispatch, pipeline launch, chat confirm.
- **FR-011**: Unit tests MUST exist for the dependency injection module and the request ID middleware.
- **FR-012**: Edge-case tests MUST exist for recovery logic (crash mid-recovery, empty state, concurrent recovery attempts).
- **FR-013**: Edge-case tests MUST exist for state validation (boundary transitions, invalid state combinations).
- **FR-014**: Edge-case tests MUST exist for signal bridge (error propagation, timeout handling, message loss).
- **FR-015**: Edge-case tests MUST exist for guard service (permission boundaries) and signal delivery (retry/failure paths).
- **FR-016**: Property-based tests MUST exist for the pipeline state machine with at least 100 generated examples.
- **FR-017**: Property-based tests MUST exist for the markdown parser with roundtrip verification.
- **FR-018**: Mutation testing targets MUST include backend API routes and middleware in addition to services.
- **FR-019**: Component tests MUST exist for 5 board components: ProjectBoard, BoardToolbar, CleanUpConfirmModal, AgentColumnCell, BoardDragOverlay.
- **FR-020**: Hook tests MUST exist for 3 hooks: useBoardDragDrop, useConfirmation, useUnsavedPipelineGuard — each with at least 5 branch paths tested.
- **FR-021**: Utility tests MUST exist for lazyWithRetry, commands directory, formatAgentName, and generateId.
- **FR-022**: Service layer tests MUST cover error handling, retry logic, and response parsing beyond the existing API client test.
- **FR-023**: All mutation testing shards MUST be executed and results documented.
- **FR-024**: Coverage thresholds MUST be ratcheted upward in configuration files after verification.
- **FR-025**: Pre-commit hooks MUST complete in under 30 seconds on a set of changed files.
- **FR-026**: An emergency hotfix override process MUST be documented with audit trail requirements.
- **FR-027**: Final coverage and mutation reports MUST be generated and stored.

### Key Entities

- **Test Suite**: A collection of test files organized by type (unit, integration, property, fuzz, chaos, concurrency, E2E) with associated configuration for execution and coverage reporting.
- **Coverage Threshold**: A minimum percentage (line, statement, branch, or function) enforced by configuration. Thresholds ratchet upward only.
- **Mutation Shard**: A partitioned subset of source modules targeted for mutation testing, executed independently to parallelize CI workload.
- **Flaky Test**: A test that produces inconsistent pass/fail results across identical runs. Characterized by root cause and quarantined until fixed.
- **Surviving Mutant**: A code mutation that no test detects. Classified as killable (test gap), equivalent (mutation doesn't change behavior), or non-killable (impractical to test).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All static analysis tools (linter, type-checker, security scanner) exit with zero violations across both frontend and backend.
- **SC-002**: Backend line coverage meets or exceeds 80% as verified by the coverage tool with fail-under enforcement.
- **SC-003**: Frontend statement coverage meets or exceeds 55%, branch coverage meets or exceeds 50%, and function coverage meets or exceeds 45%.
- **SC-004**: Zero confirmed flaky tests remain in the active test suite (all are quarantined with root cause and tracked issues).
- **SC-005**: Zero AsyncMock deprecation warnings are emitted during test execution.
- **SC-006**: Mutation kill rate exceeds 60% in each backend shard and the frontend mutation suite.
- **SC-007**: All killable surviving mutants have targeted assertions written to address them.
- **SC-008**: Coverage thresholds are enforced in CI — a commit that lowers coverage is rejected.
- **SC-009**: Pre-commit hooks complete in under 30 seconds on changed files.
- **SC-010**: An emergency hotfix override process is documented and includes audit trail requirements.
- **SC-011**: Final coverage and mutation reports are generated and accessible.

## Assumptions

- Phase 1 (050) bug fixes remain stable and do not regress during this effort.
- The existing test infrastructure (fixtures, factories, CI pipeline) does not require modification beyond configuration changes.
- DRY refactoring is explicitly deferred — this effort writes characterization tests that document current behavior without restructuring code.
- The 5-run flaky detection threshold balances statistical confidence with CI execution time.
- Property-based tests with 100+ examples provide adequate state space coverage without impractical runtime.
- Mutation testing shard structure (4 backend shards + 1 frontend suite) remains sufficient after target expansion.
- Coverage improvements are additive — no existing tests are removed or modified to meet thresholds.
