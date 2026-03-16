# Feature Specification: Modernize Testing to Surface Unknown Bugs

**Feature Branch**: `046-modernize-testing`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Modernize Testing to Surface Unknown Bugs — introduce coverage enforcement, mutation testing, property-based testing, API contract validation, visual/accessibility regression, and security/dependency scanning to systematically discover issues that the existing test suite does not catch."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Coverage Enforcement Catches Blind Spots (Priority: P1)

A developer opens a pull request that touches backend or frontend code. The CI pipeline measures test coverage and compares it against the project's minimum threshold. If the change drops coverage below the threshold, the pipeline fails and points the developer to the uncovered lines.

**Why this priority**: Coverage enforcement is the foundation: it reveals which code paths have zero tests and establishes the ratchet that every subsequent technique builds on. Without baseline visibility, mutation testing and property tests cannot be targeted effectively.

**Independent Test**: Run the CI pipeline on a branch where a tested function's tests have been deliberately deleted. Verify that CI reports the coverage shortfall and rejects the build.

**Acceptance Scenarios**:

1. **Given** the backend coverage threshold is set 2 % below the current baseline, **When** a developer pushes a commit that reduces backend coverage below the threshold, **Then** the CI pipeline fails with a clear coverage report listing uncovered files and lines.
2. **Given** the frontend coverage threshold is configured, **When** a developer pushes a commit that maintains or improves coverage, **Then** the CI pipeline passes and the coverage summary is visible in the build log.
3. **Given** a new source file is added without any corresponding tests, **When** CI runs, **Then** the new file appears in the "uncovered" section of the coverage report.

---

### User Story 2 — Property-Based Tests Discover Edge-Case Bugs (Priority: P2)

A developer writes a property test for a backend model validator or a frontend utility function. The test framework generates thousands of random (but structured) inputs — unusual Unicode, empty strings, extreme numeric ranges, deeply nested objects — and checks that the function's stated invariant holds for all of them. Any violation surfaces as a reproducible, minimized failing case.

**Why this priority**: Property-based testing is the highest-ROI technique for finding *unknown* bugs. Tests that only use hand-picked examples often miss boundary conditions; property tests explore the input space far more broadly and are cheap to write once the invariant is identified.

**Independent Test**: Write a property test for a single utility function (e.g., `formatAgentName`) that asserts "the output is always a non-empty string when the input is a non-empty string." Run the test and confirm it either passes or surfaces a genuine edge-case failure.

**Acceptance Scenarios**:

1. **Given** a property test exists for a backend model serialization round-trip, **When** the test framework generates 1 000 random inputs, **Then** every input round-trips correctly or a minimized counterexample is reported.
2. **Given** a property test exists for a frontend utility function, **When** the test framework generates random strings, numbers, and special characters, **Then** the function either produces the correct result or a minimized counterexample is reported.
3. **Given** a property test for pipeline state transitions, **When** the framework generates random sequences of valid state transitions, **Then** the system never enters an invalid state.

---

### User Story 3 — Mutation Testing Identifies Weak Tests (Priority: P3)

On a scheduled (nightly or weekly) basis, the mutation testing tool modifies source code in small, systematic ways (e.g., flipping operators, removing return statements, swapping boolean values). The existing test suite then runs against each mutant. Surviving mutants — those not caught by any test — are listed in a report. A developer reviews the report and either strengthens the relevant tests or acknowledges the surviving mutant as a false positive.

**Why this priority**: Mutation testing audits test *quality* rather than quantity. It is computationally expensive and best run on a schedule rather than every PR, but the results reveal concrete blind spots that coverage alone cannot.

**Independent Test**: Run the mutation tool against a single, well-tested module. Verify the report lists surviving mutants with file, line, and mutation description.

**Acceptance Scenarios**:

1. **Given** the mutation tool is configured for backend `src/services/`, **When** a scheduled run completes, **Then** a report lists every surviving mutant with file path, line number, and mutation description.
2. **Given** the mutation tool is configured for frontend `src/hooks/` and `src/lib/`, **When** a scheduled run completes, **Then** a report lists surviving mutants for those directories.
3. **Given** a developer strengthens a test to kill a previously surviving mutant, **When** the mutation tool runs again, **Then** that mutant no longer appears in the surviving list.

---

### User Story 4 — API Contract Validation Detects Frontend-Backend Drift (Priority: P4)

The backend auto-generates its API specification. A CI step exports the specification and validates that the frontend's mock data factories and type definitions conform to the response shapes defined in the specification. If the backend changes a response field and the frontend mocks are not updated, the CI step fails.

**Why this priority**: Contract drift is a silent failure mode — backend changes can ship while frontend tests continue to pass against stale mocks. This check closes that gap with a lightweight validation step.

**Independent Test**: Rename a field in a backend response model. Run the contract-validation CI step. Verify it reports the mismatch between the specification and the frontend mocks.

**Acceptance Scenarios**:

1. **Given** the backend specification and the frontend mocks are in sync, **When** CI runs the contract-validation step, **Then** it passes.
2. **Given** a backend response field has been renamed, **When** CI runs the contract-validation step, **Then** it fails with a clear message identifying the mismatched field and the affected mock file.

---

### User Story 5 — Visual & Accessibility Regression Prevention (Priority: P5)

Existing end-to-end test flows capture baseline screenshots and run accessibility audits. When a developer changes styles or markup, CI compares new screenshots against baselines and re-runs the accessibility audit. Unintended visual differences or new accessibility violations cause the build to fail.

**Why this priority**: Visual regressions and accessibility violations are hard to catch in code review alone. Automated screenshot comparison and audit tooling catch them consistently.

**Independent Test**: Intentionally change a CSS property (e.g., increase a button's margin). Run the visual-regression test. Verify it fails with a screenshot diff highlighting the change.

**Acceptance Scenarios**:

1. **Given** baseline screenshots exist for key pages, **When** a developer changes a CSS property that affects layout, **Then** the visual-regression test fails with a diff image showing the change.
2. **Given** the accessibility audit runs on all component tests, **When** a developer adds a form input without a label, **Then** the audit fails identifying the specific accessibility violation.
3. **Given** end-to-end tests run against both the primary browser and an additional browser engine, **When** a rendering bug exists only in the secondary engine, **Then** the test suite catches it.

---

### User Story 6 — Security & Dependency Scanning Catches Known Vulnerabilities (Priority: P6)

CI runs dependency audit tools and security linters on every pull request. If a dependency has a known vulnerability or the source code contains a flagged security anti-pattern (e.g., hardcoded secrets, unsafe regex), the build fails with an actionable finding.

**Why this priority**: Known-vulnerability scanning is a low-effort, high-value gate. Flagging issues early prevents shipping code with published CVEs or common security anti-patterns.

**Independent Test**: Temporarily pin a dependency to a version with a known CVE. Run the audit step. Verify it reports the vulnerability.

**Acceptance Scenarios**:

1. **Given** all dependencies are free of known CVEs, **When** CI runs the dependency audit, **Then** the step passes.
2. **Given** a backend dependency has a known CVE, **When** CI runs the backend dependency audit, **Then** it fails and lists the affected package, CVE identifier, and recommended fix version.
3. **Given** the security linter is configured for the backend, **When** a developer pushes code containing a hardcoded secret pattern, **Then** the linter fails and identifies the file and line.
4. **Given** the security linter is configured for the frontend, **When** a developer pushes code using `eval()`, **Then** the linter fails and identifies the violation.

---

### Edge Cases

- What happens when coverage tools encounter dynamically generated code or code behind feature flags that is unreachable in the test environment? (Expected: the coverage report still generates; unreachable code may be excluded via configuration.)
- What happens when the mutation testing tool encounters an infinite loop in a mutant? (Expected: a per-mutant timeout kills the run and the mutant is reported as "timed out," not silently skipped.)
- What happens when the API specification changes its format version? (Expected: the contract-validation step fails clearly rather than silently accepting a mismatched format.)
- What happens when a screenshot baseline does not exist for a new page? (Expected: the first run generates the baseline; subsequent runs compare against it.)
- What happens when a dependency audit tool is unavailable or its database is unreachable? (Expected: the CI step fails with a clear error indicating the tool failure, rather than passing silently.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CI MUST measure backend test coverage on every pull request and fail the build if coverage drops below the configured threshold.
- **FR-002**: CI MUST measure frontend test coverage on every pull request and fail the build if coverage drops below the configured threshold.
- **FR-003**: Coverage thresholds MUST follow a ratchet pattern — set initially at 2 % below the measured baseline, and only increased over time.
- **FR-004**: The project MUST include property-based tests for backend model validation, serialization round-trips, and state-transition sequences.
- **FR-005**: The project MUST include property-based tests for frontend utility functions that handle user-facing data transformations.
- **FR-006**: A mutation testing tool MUST be configured for the backend, targeting `src/services/` as the initial scope.
- **FR-007**: A mutation testing tool MUST be configured for the frontend, targeting `src/hooks/` and `src/lib/` as the initial scope.
- **FR-008**: Mutation testing MUST run on a schedule (nightly or weekly), not on every pull request.
- **FR-009**: CI MUST export the backend API specification and validate that frontend mock data factories conform to the specification's response shapes.
- **FR-010**: End-to-end tests MUST include screenshot comparison against stored baselines, failing when visual differences exceed a configured tolerance.
- **FR-011**: Component-level tests MUST include accessibility audits, failing when violations are detected.
- **FR-012**: End-to-end tests MUST run against at least two browser engines (the primary engine plus one additional engine).
- **FR-013**: CI MUST run a backend dependency audit on every pull request, failing if known CVEs are found.
- **FR-014**: CI MUST run a frontend dependency audit on every pull request, failing if known CVEs are found.
- **FR-015**: CI MUST run a backend security linter on every pull request, failing on flagged anti-patterns.
- **FR-016**: CI MUST run a frontend security linter on every pull request, failing on flagged anti-patterns.
- **FR-017**: Coverage reports, mutation reports, and security findings MUST be surfaced in CI build logs with sufficient detail for a developer to locate and address the issue (file, line, description).
- **FR-018**: Untested pages and component directories MUST be prioritized for new test coverage: the project currently has 7 of 11 pages untested and entire component directories (`agents/`, `apps/`, `help/`, `onboarding/`, `pipeline/`) plus `src/services/api.ts` without direct tests.

## Assumptions

- The backend uses a framework that auto-generates an API specification (OpenAPI) from route definitions; no manual spec authoring is required.
- The existing CI infrastructure supports adding new pipeline steps without architectural changes.
- Mutation testing overhead is acceptable when run on a nightly or weekly schedule, not gating individual PRs.
- Property-based tests will be co-located alongside existing unit tests in the same test directories, following the project's current conventions.
- Baseline screenshots for visual regression will be committed to the repository and reviewed in PRs when intentional visual changes are made.
- The "ratchet" coverage thresholds will be maintained manually by periodically increasing the configured minimum after test improvements land.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Backend test coverage baseline is measured and a threshold is enforced in CI — any PR that drops coverage below the threshold is rejected.
- **SC-002**: Frontend test coverage baseline is measured and a threshold is enforced in CI — any PR that drops coverage below the threshold is rejected.
- **SC-003**: At least 10 property-based tests exist across backend and frontend, covering model validation, serialization round-trips, and utility functions.
- **SC-004**: Mutation testing reports are generated on schedule for the targeted modules; the initial run identifies surviving mutants that represent concrete test-quality improvements.
- **SC-005**: Contract validation catches at least one intentionally introduced API drift (verified during implementation) and prevents it from merging.
- **SC-006**: Visual-regression tests detect an intentionally introduced CSS change (verified during implementation) and prevent it from merging.
- **SC-007**: Accessibility audits run on all component tests; at least one intentionally introduced accessibility violation is caught during verification.
- **SC-008**: End-to-end tests pass on both the primary and secondary browser engines.
- **SC-009**: Dependency audits and security linters run on every PR with no false-negative gaps — a deliberately introduced known-CVE dependency or security anti-pattern is caught during verification.
- **SC-010**: The 7 currently untested pages and the zero-coverage component directories have at least smoke-level test coverage.
