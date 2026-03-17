# Feature Specification: Increase Test Coverage & Surface Unknown Bugs

**Feature Branch**: `048-test-coverage-bugs`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Plan: Increase Test Coverage & Surface Unknown Bugs — grow backend line coverage from 69% to 80% and frontend statement/branch/function/line coverage from 46/41/38/47 to 60/55/52/60 through phased test writing targeting highest-ROI untested modules. Promote existing local-only advanced tests (property, fuzz, chaos, concurrency) into CI. Add time-controlled testing for 15+ temporal behaviors, production-parity tests for code paths only exercised outside TESTING=1, architecture fitness functions to prevent layer violations, expanded property/fuzz testing for new modules, and WebSocket/real-time state lifecycle tests."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Promote Existing Advanced Tests to CI (Priority: P1)

A developer opens a pull request. In addition to the standard unit test suite, CI now also runs the existing property-based, fuzz, chaos, and concurrency tests that previously only ran on developer machines. If any advanced test detects a regression — a race condition, a crash on random input, or a state invariant violation — the build fails before the code reaches production.

On the frontend, fuzz tests that exist but were excluded from CI discovery are now included. On a scheduled basis (weekly), mutation testing runs against both backend and frontend code, posting surviving-mutant reports as artifacts for developer review.

**Why this priority**: These tests already exist and have proven value locally. Promoting them to CI requires zero new test code — only CI configuration changes — and immediately catches bugs on every PR that were previously invisible.

**Independent Test**: Trigger a CI run on a branch that introduces a deliberate race condition or a crash-inducing input. Verify the advanced test suite catches it and fails the build.

**Acceptance Scenarios**:

1. **Given** backend property, fuzz, chaos, and concurrency tests exist locally, **When** a pull request is opened, **Then** CI runs these advanced tests as a separate job with a 120-second timeout per test and reports results alongside the standard test suite.
2. **Given** known-flaky concurrency tests are marked as expected failures, **When** CI runs the advanced test suite, **Then** expected-failure tests do not block the build but are still reported.
3. **Given** frontend fuzz tests exist in the test directory, **When** CI runs the frontend test suite, **Then** the fuzz tests are discovered and executed rather than silently excluded.
4. **Given** a weekly schedule triggers the mutation testing workflow, **When** mutation testing completes for backend and frontend, **Then** results are published as a downloadable artifact showing surviving mutants by file and line.

---

### User Story 2 — Backend Coverage Growth: GitHub Integration Layer (Priority: P2)

A developer working on the backend sees that the 9 untested GitHub integration modules (GraphQL client, issues, pull requests, branches, copilot, identities, repository, projects, board) are the single largest coverage gap. After writing tests for these modules — mocking the external API client, verifying request construction and response transformation, and covering error paths (rate limits, timeouts, 404/429 responses) — backend line coverage climbs from 69% to approximately 74%. The CI coverage threshold is then ratcheted up to match.

**Why this priority**: These modules have the highest line count of any untested area, use straightforward mock patterns already established in the codebase, and collectively represent the largest single coverage jump available.

**Independent Test**: Run the backend test suite with coverage reporting after adding tests for the GitHub integration layer. Verify that line coverage has increased to at least 74% and that the new tests pass consistently.

**Acceptance Scenarios**:

1. **Given** the GraphQL client module has no tests, **When** tests are added that mock the client and verify query variables, response transformation, rate-limit errors, and timeout handling, **Then** the module reaches at least 80% line coverage.
2. **Given** the issues, pull requests, and repository modules have no tests, **When** tests are added covering CRUD operations, status transitions, label operations, and 404/429 error responses, **Then** each module reaches at least 80% line coverage.
3. **Given** the smaller modules (branches, copilot, identities, projects, board) have no tests, **When** tests are added verifying API path and parameter correctness, **Then** each module reaches at least 70% line coverage.
4. **Given** all GitHub integration layer tests pass, **When** the CI coverage threshold is updated to 74%, **Then** CI continues to pass on the main branch.

---

### User Story 3 — Backend Coverage Growth: Polling, Services & API Routes (Priority: P3)

After the GitHub integration layer is covered, a developer tackles the next tier: 4 untested polling modules (containing rate-limit tier logic, adaptive interval math, and state predicates), 6+ untested services (message persistence, policy enforcement, label caching, integration points), and 4 untested API routes. These are tested using established patterns — in-memory database fixtures for services, test client fixtures for API routes. Backend coverage reaches approximately 78%, and the threshold ratchets up.

**Why this priority**: The polling and service modules contain critical business logic (rate-limit enforcement, state validation, message persistence) that is currently exercised only in production. Testing these surfaces bugs in core system behavior.

**Independent Test**: Run the backend test suite after adding tests for polling, services, and API routes. Verify line coverage has reached at least 78%.

**Acceptance Scenarios**:

1. **Given** the polling internals (state management, pipeline processing, state validation, helper utilities) have no tests, **When** tests are added for rate-limit tier logic, adaptive interval calculations, and state predicates, **Then** each polling module reaches at least 80% line coverage.
2. **Given** high-value services (message persistence, policy enforcement, label caching) have no tests, **When** tests are added using in-memory database fixtures, **Then** each service module reaches at least 75% line coverage.
3. **Given** 4 API routes have no tests, **When** tests are added using the test client fixture pattern, **Then** each route module reaches at least 75% line coverage.
4. **Given** all new tests pass, **When** the CI coverage threshold is updated to 78%, **Then** CI continues to pass on the main branch.

---

### User Story 4 — Backend Coverage Growth: Branch Coverage & Edge Cases to 80% (Priority: P4)

A developer inspects the HTML coverage report to identify the top files with the most uncovered branches — typically error handlers, fallback paths, and production-only code paths. Edge-case tests are added that inject specific exceptions to hit `except` clauses, exercise early returns for empty/null inputs, and cover conditional branches. Backend line coverage reaches the 80% target, and the threshold ratchets to its final value.

**Why this priority**: After file-level coverage gaps are closed, branch coverage analysis reveals the remaining untested error-handling and fallback logic — the code most likely to contain latent bugs.

**Independent Test**: Run the backend test suite with branch coverage reporting. Verify line coverage has reached 80% and that the top 10 highest-uncovered-branch files have each improved by at least 15 percentage points.

**Acceptance Scenarios**:

1. **Given** the HTML coverage report identifies files with the most uncovered branches, **When** edge-case tests are added for the top 10 files, **Then** each file's branch coverage improves by at least 15 percentage points.
2. **Given** error handler branches are untested, **When** tests inject specific exceptions, **Then** the `except` clauses execute and their behavior is verified.
3. **Given** early-return paths for empty or null inputs are untested, **When** tests supply empty/null inputs, **Then** the early-return behavior is verified.
4. **Given** all edge-case tests pass, **When** the CI coverage threshold is updated to 80%, **Then** CI continues to pass on the main branch.

---

### User Story 5 — Frontend Coverage Growth: Services & Hooks (Priority: P5)

A developer targets the highest-ROI frontend modules: 6 schema validation files (pure validators with no UI dependencies), the API error-handling layer, and 24 untested hooks. Schema tests verify that valid data passes and invalid data fails. Hook tests use the established render-hook pattern with mock API and async assertions. Frontend coverage climbs from 46/41/38/47 to approximately 53/48/45/54.

**Why this priority**: Services and hooks are pure logic — they yield the most coverage per test written and avoid the complexity of UI component rendering. Schema validators are especially high-ROI as they require no mocking at all.

**Independent Test**: Run the frontend test suite with coverage reporting after adding tests for schemas, API error handling, and hooks. Verify that coverage metrics have reached at least 53/48/45/54.

**Acceptance Scenarios**:

1. **Given** 6 schema validation files have no tests, **When** tests are added verifying valid data passes, invalid data is rejected, and field rename detection works, **Then** each schema file has at least 90% coverage.
2. **Given** the API error-handling layer has no tests, **When** tests are added mocking fetch and verifying error normalization for each HTTP status and auth-expired listener flow, **Then** the API module reaches at least 80% coverage.
3. **Given** 24 hooks have no tests, **When** tests are added using the render-hook pattern, **Then** at least 20 of the 24 hooks have passing test suites.
4. **Given** all new tests pass, **When** frontend coverage thresholds are updated to 53/48/45/54, **Then** CI continues to pass on the main branch.

---

### User Story 6 — Frontend Coverage Growth: Components to 60% (Priority: P6)

A developer works through the remaining untested frontend components in order of complexity: settings components (form-heavy, interaction-focused), pipeline components (graph rendering, execution state), board components (toolbar, modals, project board), and then the remaining components across agents, tools, chores, chat, and layout. Each phase uses the established render-with-providers and user-event patterns. Frontend coverage reaches the 60/55/52/60 target.

**Why this priority**: Component tests require more setup than service/hook tests but are necessary to reach the coverage target. Working from simpler (settings forms) to more complex (graph rendering, chat interface) manages risk.

**Independent Test**: Run the frontend test suite with coverage reporting after each component batch. Verify progressive coverage improvement toward 60/55/52/60.

**Acceptance Scenarios**:

1. **Given** 14 settings components have no tests, **When** tests are added covering render, interaction, and error states, **Then** the settings component directory reaches at least 70% coverage.
2. **Given** 8 pipeline components and 12 board components have no tests, **When** tests are added for rendering correctness and key interactions, **Then** frontend coverage reaches at least 58/53/50/59.
3. **Given** remaining untested components (agents, tools, chores, chat, layout, apps, help, onboarding), **When** tests are added, **Then** frontend coverage reaches the 60/55/52/60 target.
4. **Given** all new tests pass, **When** frontend coverage thresholds are updated to 60/55/52/60, **Then** CI continues to pass on the main branch.

---

### User Story 7 — Production-Parity Testing (Priority: P7)

A developer discovers that the entire test suite runs with testing mode enabled and debug mode active, meaning production code paths — encryption enforcement, CSRF protection, rate limiting, admin validation, webhook secret verification — have never been exercised by any test. Production-mode integration tests are added that run with production-like configuration, exercising the authentication flow, webhook verification, CSRF checks, and rate limiting. Configuration matrix tests verify that invalid environment variable combinations (e.g., production mode with missing encryption key) cause the expected startup failures.

**Why this priority**: Code that only runs in production is the highest-risk category of untested code. A bug in encryption enforcement, CSRF protection, or rate limiting could be a security vulnerability that has existed undetected.

**Independent Test**: Run the production-mode integration test suite with the production-like configuration fixture. Verify that all production code paths are exercised and that invalid configurations produce the correct errors.

**Acceptance Scenarios**:

1. **Given** a production-like test configuration (testing mode disabled, debug mode off, encryption key set, webhook secret set), **When** the auth flow is tested, **Then** the production authentication code path executes and behaves correctly.
2. **Given** a production-like test configuration, **When** a webhook request is sent without the correct signature, **Then** the request is rejected by the production webhook verification logic.
3. **Given** a production-like test configuration, **When** CSRF protection and rate limiting are tested, **Then** both mechanisms enforce their rules correctly.
4. **Given** an invalid environment variable combination (production mode without encryption key), **When** the application starts, **Then** a clear configuration error is raised before any request is served.

---

### User Story 8 — Time-Controlled Testing (Priority: P8)

A developer identifies 15+ time-dependent behaviors across backend and frontend that have no time-controlled tests: session expiry boundaries, token refresh buffers, rate-limit reset windows, adaptive polling intervals, backoff formulas, reconnection delays, and debounce timers. Using time-freezing utilities, tests verify boundary behavior at exact time thresholds (e.g., one second before vs. one second after expiry) and verify that temporal sequences (backoff doubling, interval caps, debounce windows) work correctly.

**Why this priority**: Temporal boundary bugs are notoriously difficult to catch without time-controlled testing. A session that expires one second too early or a backoff that fails to cap causes production issues that are nearly impossible to reproduce.

**Independent Test**: Run the time-controlled test suite. Verify that each temporal behavior is tested at its exact boundary and that at least one previously unknown boundary bug is surfaced.

**Acceptance Scenarios**:

1. **Given** session expiry has a defined threshold, **When** time is frozen to one second before expiry, **Then** the session is still valid; **When** time advances to one second after expiry, **Then** the session is expired.
2. **Given** adaptive polling has a doubling interval on idle cycles with a maximum cap, **When** time is manipulated to simulate successive idle cycles, **Then** the interval doubles correctly and does not exceed the cap.
3. **Given** the frontend has a reconnection backoff sequence (1s, 2s, 4s... capped at 30s), **When** reconnection events are simulated with fake timers, **Then** each delay matches the expected backoff value and the cap is respected.
4. **Given** a debounced reconnection mechanism limits events to one per 2000ms, **When** 5 rapid reconnection events fire within 2000ms, **Then** only one cache invalidation occurs.

---

### User Story 9 — Architecture Fitness Functions (Priority: P9)

A developer adds automated tests that enforce the project's intended layer boundaries. On the backend, import-direction tests parse source files and assert that service modules never import from API modules, API modules never bypass services to access stores directly, and model modules never import from services or API. On the frontend, similar tests assert that pages don't import other pages, hooks don't import UI components, and utilities don't import hooks. Known existing violations are captured in an allowlist that shrinks over time.

**Why this priority**: Known layer violations already exist, and without automated enforcement, new violations accumulate with every feature. Fitness functions prevent architectural erosion permanently.

**Independent Test**: Introduce a deliberate layer violation (e.g., a service importing from an API module). Run the architecture test. Verify it catches the violation. Remove the deliberate violation.

**Acceptance Scenarios**:

1. **Given** backend import-direction tests are configured, **When** a service module imports from an API module, **Then** the test fails identifying the violating import.
2. **Given** a known-violations allowlist exists, **When** all allowed violations are present, **Then** the test passes; **When** a new violation is introduced outside the allowlist, **Then** the test fails.
3. **Given** frontend dependency-direction tests are configured, **When** a page imports another page or a hook imports a UI component, **Then** the test fails identifying the violating import.

---

### User Story 10 — Expanded Property & Fuzz Testing (Priority: P10)

A developer expands property-based and fuzz testing to modules not yet covered. Property tests for the rate-limit tier system verify that random `remaining` values always select the correct tier, with special attention to boundary values. Property tests for prompt generators verify that random inputs (Unicode, empty strings, extreme lengths) always produce well-formed prompts without crashes. Fuzz tests for webhook payloads are expanded to cover additional event types. Frontend property tests cover untested utility functions.

**Why this priority**: The existing property and fuzz tests have proven their value. Expanding them to new modules with rich property opportunities (rate-limit tiers, prompt generation, webhook parsing) systematically explores edge cases that manual testing misses.

**Independent Test**: Run the expanded property and fuzz test suites. Verify they explore the input space broadly and that any invariant violation or crash is a confirmed, reproducible bug.

**Acceptance Scenarios**:

1. **Given** property tests for the rate-limit tier system, **When** random `remaining` values are generated including boundary values (50/51, 100/101, 200/201), **Then** the correct tier is always selected.
2. **Given** property tests for prompt generators, **When** random inputs including Unicode, empty strings, and extreme lengths are generated, **Then** prompts always contain required sections and never crash.
3. **Given** expanded fuzz tests for webhook payloads, **When** payloads for additional event types are fuzzed, **Then** no unhandled exceptions occur for any well-formed-but-unexpected payload.
4. **Given** frontend property tests for untested utility functions, **When** random inputs are generated, **Then** outputs satisfy their stated invariants (no crashes, consistent formatting).

---

### User Story 11 — WebSocket & Real-Time State Testing (Priority: P11)

A developer adds end-to-end tests for the WebSocket lifecycle: connect, receive data, kill the connection, verify the system falls back to polling, reconnect, and verify data is current. A separate test verifies the reconnection debounce mechanism — sending rapid reconnect events and asserting only one cache invalidation fires within the debounce window.

**Why this priority**: The WebSocket lifecycle involves complex state transitions (connected → disconnected → polling fallback → reconnected) that are a common source of stale-data bugs. These tests catch data-freshness issues that are invisible to unit tests.

**Independent Test**: Run the WebSocket lifecycle end-to-end test. Verify the full connect → disconnect → fallback → reconnect → data-current flow completes successfully.

**Acceptance Scenarios**:

1. **Given** a WebSocket connection is established and receiving data, **When** the WebSocket is killed, **Then** the system falls back to polling within the configured fallback interval.
2. **Given** the system is in polling fallback mode, **When** the WebSocket reconnects, **Then** the system returns to WebSocket mode and data is current (not stale from the polling period).
3. **Given** 5 rapid reconnect events fire within the debounce window, **When** the debounce mechanism processes them, **Then** only one cache invalidation occurs.

---

### Edge Cases

- What happens when the CI coverage threshold is set but a new phase's tests haven't merged yet — does the ratchet cause a temporary CI failure on unrelated PRs?
- How does the system handle a production-mode test that triggers rate limiting against the test itself — does the test infrastructure account for its own rate-limit consumption?
- What happens when a time-controlled test freezes time in a way that conflicts with async event loops or timers used by the test framework itself?
- What happens when an architecture fitness test encounters a circular import that is technically a layer violation but is required for the runtime import system to work?
- How does mutation testing handle files that are intentionally unreachable in test mode (production-only code paths) — are surviving mutants in those files false positives?
- What happens when a WebSocket end-to-end test runs in CI where real WebSocket connections may be restricted or firewalled?
- How are coverage thresholds coordinated when multiple phases are being developed in parallel on separate branches?

## Requirements *(mandatory)*

### Functional Requirements

**Coverage Growth — Backend**

- **FR-001**: Test suite MUST include tests for all 9 GitHub integration modules (GraphQL client, issues, pull requests, branches, copilot, identities, repository, projects, board), covering request construction, response transformation, and error handling for rate-limit, timeout, 404, and 429 responses.
- **FR-002**: Test suite MUST include tests for 4 polling modules covering rate-limit tier logic, adaptive interval calculations, and state predicates.
- **FR-003**: Test suite MUST include tests for untested services (message persistence, policy enforcement, label caching, integration points) using in-memory database fixtures.
- **FR-004**: Test suite MUST include tests for all untested API routes using the established test client fixture pattern.
- **FR-005**: Test suite MUST include edge-case tests targeting the top 10 files with the most uncovered branches, covering error handlers, fallback paths, and early-return conditions.
- **FR-006**: Backend CI coverage threshold MUST be ratcheted upward at each phase: 74% after GitHub integration, 78% after polling/services/routes, 80% after edge cases.

**Coverage Growth — Frontend**

- **FR-007**: Test suite MUST include tests for all schema validation files verifying valid input acceptance, invalid input rejection, and field rename detection.
- **FR-008**: Test suite MUST include tests for the API error-handling layer covering error normalization for each HTTP status and authentication expiry flow.
- **FR-009**: Test suite MUST include tests for at least 20 of the 24 untested hooks using the established render-hook pattern.
- **FR-010**: Test suite MUST include tests for untested components across settings, pipeline, board, agents, tools, chores, chat, and layout directories.
- **FR-011**: Frontend CI coverage thresholds MUST be ratcheted upward at each phase: 53/48/45/54 after services and hooks, 58/53/50/59 after settings/pipeline/board, 60/55/52/60 after remaining components.

**CI Quality Gates**

- **FR-012**: CI MUST run backend property-based, fuzz, chaos, and concurrency tests as a separate job on every pull request, with a per-test timeout of 120 seconds.
- **FR-013**: CI MUST include frontend fuzz tests in the standard test discovery and execution.
- **FR-014**: CI MUST include a scheduled mutation testing workflow (weekly) for both backend and frontend, publishing results as downloadable artifacts.
- **FR-015**: Known expected-failure tests (e.g., known race conditions) MUST NOT block the CI build but MUST still be reported in test results.

**Production-Parity Testing**

- **FR-016**: Test suite MUST include integration tests that run with production-like configuration (testing mode disabled, debug mode off, encryption enabled, webhook secrets set).
- **FR-017**: Production-mode tests MUST exercise the authentication flow, webhook signature verification, CSRF protection, and rate limiting under production configuration.
- **FR-018**: Test suite MUST include configuration matrix tests verifying that every invalid environment variable combination produces the correct startup error and that every valid combination allows successful startup.

**Time-Controlled Testing**

- **FR-019**: Test suite MUST include time-controlled tests for backend temporal behaviors: session expiry boundaries, rate-limit reset windows, token refresh buffer, adaptive polling interval (doubling, reset, cap), assignment grace period, and recovery cooldown.
- **FR-020**: Test suite MUST include time-controlled tests for frontend temporal behaviors: WebSocket reconnection backoff sequence with cap, polling fallback interval, auto-refresh timer reset, chunk reload loop prevention, and debounced reconnection.
- **FR-021**: All time-controlled tests MUST verify behavior at exact boundaries (one unit before and one unit after the threshold).

**Architecture Fitness Functions**

- **FR-022**: Test suite MUST include backend import-direction tests asserting: services never import from API modules, API modules never import from store modules directly, and model modules never import from services or API.
- **FR-023**: Test suite MUST include frontend dependency-direction tests asserting: pages never import other pages, hooks never import UI components, and utilities never import hooks.
- **FR-024**: Architecture tests MUST support a known-violations allowlist that permits existing violations while preventing new ones.

**Property & Fuzz Testing Expansion**

- **FR-025**: Test suite MUST include property tests for the rate-limit tier system verifying correct tier selection for random `remaining` values, with boundary coverage at tier thresholds.
- **FR-026**: Test suite MUST include property tests for prompt generators verifying that random inputs (Unicode, empty strings, extreme lengths) always produce well-formed output.
- **FR-027**: Test suite MUST include expanded fuzz tests for webhook payload parsing covering additional event types beyond the current scope.
- **FR-028**: Test suite MUST include frontend property tests for untested utility functions verifying output invariants across random inputs.

**WebSocket & Real-Time Testing**

- **FR-029**: Test suite MUST include an end-to-end test covering the WebSocket lifecycle: connect, receive data, connection loss, polling fallback, reconnect, and data-freshness verification.
- **FR-030**: Test suite MUST include a test verifying the reconnection debounce mechanism enforces the configured debounce window.

### Key Entities

- **Coverage Threshold**: A per-metric minimum (line, branch, function, statement) enforced by CI. Ratchets upward as phases complete — never lowered.
- **Advanced Test Suite**: The collection of property-based, fuzz, chaos, and concurrency tests that explore input spaces and timing beyond what manual example-based tests cover.
- **Production Configuration**: The set of environment variables and flags that activate production-only code paths (encryption, CSRF, rate limiting, webhook verification) — distinct from the test configuration used by default.
- **Architecture Rule**: A directional import constraint defining which layers may depend on which other layers. Violations are either in the known-violations allowlist or are test failures.
- **Coverage Phase**: A discrete unit of test-writing work targeting a specific set of modules, with a defined coverage target and a corresponding CI threshold ratchet.

## Assumptions

- The existing foundational test infrastructure from features 046 and 047 (coverage enforcement, property-based testing, fuzz testing, mutation testing configuration, chaos/concurrency tests) is already merged and available on the main branch.
- Existing test templates and fixtures (mock GitHub client, in-memory database, test client, render-hook pattern) are reusable without modification for the new test files.
- The CI platform supports running separate test jobs in parallel and publishing artifacts from scheduled workflows.
- Coverage measurements are deterministic — running the same test suite twice produces the same coverage numbers, enabling reliable threshold enforcement.
- The production-mode test configuration uses synthetic secrets (generated Fernet keys, test webhook secrets) and does not connect to any real external service.
- Architecture fitness tests use static analysis (import parsing) and do not require running the application.
- The WebSocket end-to-end tests use the existing end-to-end test infrastructure and can simulate connection lifecycle events within the test environment.
- Coverage thresholds are ratcheted only after a phase fully merges to the main branch — in-progress phases do not affect unrelated PRs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Backend line coverage reaches 80%, verified by CI coverage reporting, up from the current 69%.
- **SC-002**: Frontend coverage reaches 60% statement, 55% branch, 52% function, and 60% line, verified by CI coverage reporting, up from the current 46/41/38/47.
- **SC-003**: CI coverage thresholds are ratcheted at each phase boundary — no phase merges without its corresponding threshold increase.
- **SC-004**: Backend advanced tests (property, fuzz, chaos, concurrency) run on every pull request in CI and catch at least one regression during the implementation period.
- **SC-005**: Frontend fuzz tests are discovered and executed in CI on every pull request.
- **SC-006**: Weekly mutation testing runs complete for both backend and frontend, and the first run identifies at least 10 surviving mutants representing concrete test improvements.
- **SC-007**: Production-mode integration tests exercise at least 4 production-only code paths (authentication, webhook verification, CSRF, rate limiting) and find at least one code path that behaves differently than expected.
- **SC-008**: Time-controlled tests cover all 15+ identified temporal behaviors at exact boundaries and surface at least one previously unknown boundary bug.
- **SC-009**: Architecture fitness tests enforce layer boundaries — a deliberately introduced violation is caught, and the known-violations allowlist shrinks by at least 2 entries during the implementation period.
- **SC-010**: Property and fuzz test expansion covers at least 3 new modules (rate-limit tiers, prompt generators, additional webhook event types) and discovers at least one new edge-case bug.
- **SC-011**: WebSocket lifecycle end-to-end test passes reliably in CI and verifies data freshness after reconnection.
- **SC-012**: All new tests run within the existing CI time budget — total backend test suite execution increases by no more than 90 seconds and total frontend test suite execution increases by no more than 60 seconds.
- **SC-013**: Zero untested source files remain in the GitHub integration layer (9 modules) and polling subsystem (4 modules) after their respective phases complete.
