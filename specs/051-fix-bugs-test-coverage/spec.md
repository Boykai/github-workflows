# Feature Specification: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature Branch**: `051-fix-bugs-test-coverage`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Find & Fix Bugs, Increase Test Coverage: finish static analysis sweep, raise backend coverage 75%→85%, frontend 51%→75%+, verify mutation kill rates, close final verification"  
**Targets Refined**: Original user request specified 85% backend / 75%+ frontend. Targets adjusted to 80% backend line coverage and 55%/50%/45% frontend statement/branch/function coverage based on feasibility analysis and incremental ratcheting strategy.  
**Predecessor**: `050-fix-bugs-test-coverage` (42% complete — all 4 critical bugs fixed, infrastructure established)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Complete Static Analysis Sweep and Resolve Remaining Violations (Priority: P1)

As a developer, I want all remaining lint errors, type-check failures, and test warnings resolved or triaged so that the codebase has a clean baseline before any new tests are written.

**Why this priority**: Static analysis violations mask real defects and cause false confidence. Finishing this sweep (started in spec 050, roughly 50% complete) ensures new tests are written against correct, type-safe code. Flaky tests must also be identified and quarantined so test results are deterministic and trustworthy.

**Independent Test**: Can be fully tested by running the full lint and type-check suites across both codebases and verifying zero unacknowledged violations. Flaky detection is verified by running each test suite 5 times and confirming consistent results.

**Acceptance Scenarios**:

1. **Given** the frontend codebase, **When** the lint tool is executed, **Then** zero unresolved violations remain (all findings are either fixed or documented as false-positive with justification).
2. **Given** the frontend codebase, **When** the type-check tool is executed in strict mode, **Then** zero type errors are reported.
3. **Given** the frontend test suite, **When** tests are run with verbose output, **Then** all warnings are cataloged and addressed.
4. **Given** the backend test suite, **When** tests are run 5 consecutive times, **Then** the same tests pass and fail each time (zero flaky tests).
5. **Given** the frontend test suite, **When** tests are run 5 consecutive times, **Then** the same tests pass and fail each time (zero flaky tests).
6. **Given** any test identified as flaky, **When** it is quarantined, **Then** its quarantine record includes the root cause category, a tracking reference, and a re-enablement condition.

---

### User Story 2 — Raise Backend Test Coverage to at Least 80% (Priority: P2)

As a developer, I want backend line coverage raised from 75% to at least 80% by adding integration tests for untested API routes, unit tests for orphan files, service edge-case tests, and property-based tests so that critical backend code paths are protected against regressions.

**Why this priority**: With static analysis clean (P1) and all known bugs already fixed (spec 050 Phase 3), expanding backend coverage is the highest-value next step. Targeting untested API routes and orphan files closes the biggest gaps. Property-based tests protect complex state logic where example-based tests are insufficient.

**Independent Test**: Can be fully tested by running the backend test suite with coverage enforcement at the 80% threshold and verifying it passes.

**Acceptance Scenarios**:

1. **Given** the auth callback, webhook dispatch, pipeline launch, and chat confirm API routes have no integration tests, **When** integration tests are added for each route, **Then** each route has tests covering valid input, invalid input, and authorization checks.
2. **Given** the dependency injection module and request ID middleware have no dedicated test files, **When** unit tests are added for each, **Then** both modules achieve at least 90% line coverage.
3. **Given** the recovery, state validation, and signal bridge service modules have edge-case gaps, **When** tests are added for retry scenarios, boundary state values, and error propagation paths, **Then** each module's branch coverage increases by at least 15 percentage points.
4. **Given** the pipeline state machine and markdown parser, **When** property-based tests are added, **Then** invariants hold across 100+ generated input scenarios per property.
5. **Given** mutation testing currently targets only service modules, **When** mutation targets are expanded to include API routes, middleware, and utility modules, **Then** each expanded target reports results and surviving mutants are documented.
6. **Given** the full backend test suite, **When** run with coverage threshold enforcement at 80%, **Then** the suite passes.

---

### User Story 3 — Raise Frontend Test Coverage to at Least 55%/50%/45% (Priority: P3)

As a developer, I want frontend statement coverage raised from 51% to at least 55%, branch coverage from 44% to at least 50%, and function coverage from ~41% to at least 45% by testing the largest untested component and hook files so that the user-facing application is protected against regressions.

**Why this priority**: Frontend coverage significantly lags behind backend. With ~23 untested files and board components representing the largest gap (14 of 32 files untested), systematic component and hook testing delivers the most value per test written.

**Independent Test**: Can be fully tested by running the frontend test suite with coverage reporting and verifying statement/branch/function percentages meet targets.

**Acceptance Scenarios**:

1. **Given** 14 of 32 board components are untested, **When** tests are added for the 5 highest-priority components (ProjectBoard, BoardToolbar, CleanUpConfirmModal, AgentColumnCell, BoardDragOverlay), **Then** each has tests covering rendering, user interactions, and key conditional branches.
2. **Given** 3 hooks are untested (useBoardDragDrop, useConfirmation, useUnsavedPipelineGuard), **When** tests are added for each hook, **Then** each hook has tests covering success paths, error states, loading states, and empty data scenarios.
3. **Given** the utility library modules (lazyWithRetry, commands directory, formatAgentName, generateId) lack tests, **When** tests are added, **Then** each module achieves at least 90% line coverage.
4. **Given** hooks currently have 44% branch coverage, **When** tests targeting error paths, loading states, empty data, and API failure scenarios are added, **Then** overall branch coverage rises to at least 50%.
5. **Given** the number of untested frontend files is approximately 23, **When** tests are systematically added, **Then** the number of files with zero coverage drops to approximately 5.
6. **Given** the full frontend test suite, **When** run with coverage thresholds at 55/50/45, **Then** the suite passes.

---

### User Story 4 — Verify Mutation Kill Rates Across All Shards (Priority: P4)

As a developer, I want mutation testing verified across all backend shards and the frontend, with kill rates exceeding defined thresholds, so that the test suite is proven to detect real code changes — not just execute lines.

**Why this priority**: Coverage alone does not prove test effectiveness. Mutation testing reveals tests that pass regardless of code changes. This depends on coverage expansion (P2–P3) being complete to have enough tests to kill mutants.

**Independent Test**: Can be fully tested by running all mutation testing shards and verifying each reports a kill rate above the threshold.

**Acceptance Scenarios**:

1. **Given** 4 backend mutation shards (auth-and-projects, orchestration, app-and-data, agents-and-integrations), **When** each shard is executed, **Then** every shard reports a kill rate above 60%.
2. **Given** the frontend mutation testing tool, **When** it is executed against the test suite, **Then** the mutation score meets or exceeds configured thresholds (80% high, 60% low).
3. **Given** surviving mutants are identified, **When** reviewed, **Then** each surviving mutant is either killed by a new targeted assertion or documented as equivalent/non-killable with justification.

---

### User Story 5 — Final Verification and CI Enforcement (Priority: P5)

As a developer, I want a final end-to-end verification pass confirming all targets are met, CI gates enforce the new thresholds, and the development workflow remains fast so that quality gains cannot silently regress.

**Why this priority**: This is the capstone that locks in all gains from P1–P4. Without enforcement, thresholds drift. This must happen last because it validates everything.

**Independent Test**: Can be fully tested by running the complete CI pipeline (test suites, coverage, mutation testing, pre-commit hooks) and verifying all gates pass.

**Acceptance Scenarios**:

1. **Given** the full backend test suite, **When** executed with the 80% coverage threshold, **Then** the suite passes with zero failures and meets the threshold.
2. **Given** the full frontend test suite, **When** executed with 55/50/45 statement/branch/function thresholds, **Then** the suite passes with zero failures and meets all thresholds.
3. **Given** the flaky test detection process, **When** both test suites are run 5 consecutive times, **Then** zero flaky tests are detected.
4. **Given** the backend integration test output, **When** scanned for deprecated mock usage warnings, **Then** zero AsyncMock deprecation warnings appear.
5. **Given** a developer runs the pre-commit hooks, **When** typical file changes are staged, **Then** hooks complete in under 30 seconds.
6. **Given** all phases are complete, **When** the task tracker is reviewed, **Then** all 90 tasks are marked complete and final coverage and mutation reports are generated.

---

### Edge Cases

- What happens when a quarantined flaky test is fixed but the quarantine marker is not removed? A weekly review process must exist to re-run quarantined tests and remove markers for tests that now pass consistently.
- What happens when mutation testing times out on a large module? Shards must have configurable timeouts, and timeout events must be logged as warnings rather than treated as surviving mutants.
- What happens when a critical hotfix must be merged with coverage below the enforced threshold? A documented emergency bypass process must exist, requiring mandatory follow-up to restore coverage within a defined timeframe.
- What happens when coverage thresholds are met overall but individual critical files have poor coverage? Per-file minimum coverage should be monitored for high-risk files identified during analysis.
- What happens when pre-commit hooks add significant delay to developer workflow? Hooks must run only on changed files, not the entire codebase, to keep commit times under 30 seconds.
- How does the system handle E2E test environment unavailability? E2E failures due to environment issues must be distinguishable from genuine test failures.

## Requirements *(mandatory)*

### Functional Requirements

**Phase A — Static Analysis Completion**

- **FR-001**: The project MUST produce a complete lint violation report for the frontend codebase with every finding triaged as fix-now, fix-later, or false-positive.
- **FR-002**: The project MUST produce a clean type-check result for the frontend codebase in strict mode with zero unresolved type errors.
- **FR-003**: The project MUST execute flaky test detection by running backend and frontend test suites 5 times each, comparing results, and flagging inconsistencies.
- **FR-004**: All confirmed flaky tests MUST be quarantined with a documented root cause category, tracking reference, and re-enablement condition.
- **FR-005**: All findings triaged as fix-now MUST be resolved before proceeding to coverage expansion phases.

**Phase B — Backend Coverage Expansion (75% → 80%)**

- **FR-006**: Integration tests MUST exist for the auth callback, webhook dispatch, pipeline launch, and chat confirm API routes, covering valid input, invalid input, and authorization scenarios.
- **FR-007**: Dedicated unit tests MUST exist for the dependency injection module and the request ID middleware, each achieving at least 90% line coverage.
- **FR-008**: Edge-case tests MUST be added for recovery logic (retry scenarios), state validation (boundary values), and signal bridge (error propagation paths).
- **FR-009**: Property-based tests MUST verify pipeline state machine transition invariants and markdown parser roundtrip consistency across a minimum of 100 generated inputs per property.
- **FR-010**: Mutation testing targets MUST be expanded to include API routes, middleware, and utility modules in addition to the existing service module targets.
- **FR-011**: The backend coverage report MUST show at least 80% line coverage. Backend branch coverage SHOULD target at least 75% as a stretch goal (not a blocking gate).

**Phase C — Frontend Coverage Expansion (51% → 55%+)**

- **FR-012**: Tests MUST exist for the 5 highest-priority untested board components: ProjectBoard, BoardToolbar, CleanUpConfirmModal, AgentColumnCell, and BoardDragOverlay.
- **FR-013**: Tests MUST exist for the 3 untested hooks: useBoardDragDrop, useConfirmation, and useUnsavedPipelineGuard, covering success, error, loading, and empty data paths.
- **FR-014**: Tests MUST exist for utility library modules: lazyWithRetry, the commands directory, formatAgentName, and generateId, each achieving at least 90% line coverage.
- **FR-015**: Hook tests MUST cover conditional branch paths including error states, loading states, empty data, and API failure scenarios.
- **FR-016**: The number of frontend files with 0% statement coverage MUST be reduced to no more than 7 (from the current baseline of ~23).
- **FR-017**: The frontend coverage report MUST show at least 55% statement coverage, 50% branch coverage, and 45% function coverage.

**Phase D — Mutation Verification**

- **FR-018**: All 4 backend mutation shards MUST be executed and each MUST report a kill rate above 60%.
- **FR-019**: Frontend mutation testing MUST be executed and MUST meet or exceed configured thresholds (80% high, 60% low).
- **FR-020**: Surviving mutants MUST be reviewed and either killed with targeted assertions or documented as equivalent/non-killable with justification.

**Phase E — Final Verification and CI Enforcement**

- **FR-021**: Coverage thresholds MUST be enforced in CI configuration at 80% backend line coverage and 55/50/45 frontend statement/branch/function coverage.
- **FR-022**: Pre-commit hooks MUST complete lint and type-check on changed files in under 30 seconds for typical changesets.
- **FR-023**: A documented emergency hotfix override process MUST exist for CI bypass scenarios, including mandatory post-merge coverage restoration.
- **FR-024**: Final verification MUST confirm zero flaky tests, zero deprecated mock warnings, and all coverage and mutation thresholds met.
- **FR-025**: All tasks in this spec's task tracker (tasks.md) MUST be marked complete with final coverage and mutation reports generated.

### Key Entities

- **Test Suite**: A collection of test files targeting a specific codebase area (unit, integration, E2E, property-based). Attributes: scope, pass rate, coverage percentage, flaky test count.
- **Coverage Report**: A measurement of code exercised by tests. Attributes: statement coverage, branch coverage, function coverage, line coverage, target threshold, pass/fail status.
- **Mutation Report**: A measurement of test effectiveness via code mutations. Attributes: total mutants, killed mutants, survived mutants, timed-out mutants, kill rate, shard assignment.
- **Flaky Test Record**: A test identified as producing inconsistent results. Attributes: test name, failure rate across runs, root cause category (async timing, shared state, environment), quarantine status, tracking reference, re-enablement condition.
- **CI Gate**: A quality enforcement checkpoint in the continuous integration pipeline. Attributes: metric type (coverage, mutation, lint), threshold value, enforcement action (block merge), override process.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Frontend lint sweep produces zero unresolved violations (all fixed or documented as false-positive).
- **SC-002**: Frontend type-check in strict mode reports zero errors.
- **SC-003**: Flaky test detection across 5 consecutive runs of each test suite reports zero flaky tests.
- **SC-004**: Backend line coverage reaches at least 80%, verified by the coverage tool's threshold enforcement.
- **SC-005**: Backend branch coverage reaches at least 75% (target goal — not a blocking gate; tracked for visibility).
- **SC-006**: Frontend statement coverage reaches at least 55%, verified by the coverage tool's threshold enforcement.
- **SC-007**: Frontend branch coverage reaches at least 50%, verified by the coverage tool's threshold enforcement.
- **SC-008**: Frontend function coverage reaches at least 45%, verified by the coverage tool's threshold enforcement.
- **SC-009**: Pre-commit hooks complete in under 30 seconds for typical changesets.
- **SC-010**: Backend mutation kill rate exceeds 60% on every shard (4 shards total).
- **SC-011**: Frontend mutation score meets configured thresholds (80% high, 60% low).
- **SC-012**: Zero AsyncMock deprecation warnings appear in integration test output.
- **SC-013**: Number of frontend files with 0% statement coverage drops to no more than 7.
- **SC-014**: All coverage and mutation thresholds are enforced in CI — any merge request that lowers metrics below thresholds is automatically rejected.
- **SC-015**: All tasks in this spec's task tracker (tasks.md) are marked complete.

## Assumptions

- Spec 050 completed Phase 1 (static analysis ~50% done) and Phase 3 (all 4 critical bugs fixed: mutation trampoline, cache leakage, async mock warnings, pipeline stuck state). This spec resumes from that baseline.
- The existing test infrastructure (test runners, coverage tools, mutation tools, CI pipeline) is already installed and configured. This spec expands and hardens, not installs.
- Coverage targets (80% backend, 55%/50%/45% frontend) match the thresholds already ratcheted in configuration files — the task is writing tests to meet them.
- Threshold ratcheting is one-directional: thresholds may only be raised, never lowered, once the codebase consistently meets them.
- DRY refactoring is explicitly out of scope. Characterization tests pin current behavior; refactoring happens in a separate effort.
- The 14 untested board components and 3 untested hooks represent the highest-value frontend testing targets due to their user-facing criticality and coverage gap size.
- Property-based testing is appropriate for state machines and parsers where exhaustive input enumeration is impractical.
- Pre-commit hooks run only on changed files (not the full codebase) to maintain developer productivity.
- Emergency hotfix overrides are rare exceptions requiring documented justification and mandatory follow-up.
- A 5th mutation shard (api-and-middleware) may be needed to avoid overloading the existing 4 shards when expanding mutation targets.
