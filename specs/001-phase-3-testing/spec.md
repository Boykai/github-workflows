# Feature Specification: Phase 3 — Testing: Coverage, Mutation Enforcement, E2E, Property-Based & Keyboard Navigation

**Feature Branch**: `001-phase-3-testing`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Phase 3 — Testing: Coverage, Mutation Enforcement, E2E, Property-Based & Keyboard Navigation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Frontend Coverage Enforcement (Priority: P1)

As a developer, I want frontend Vitest coverage thresholds raised in two incremental phases so that untested hooks and high-LOC components are covered and regressions are caught before merge.

**Why this priority**: Frontend coverage is the highest-ROI improvement — approximately 2,200 new covered statements across ~20 untested hooks and 10 high-LOC components. Raising thresholds in CI prevents coverage from regressing after the work is done.

**Independent Test**: Can be fully tested by running `npm run test:coverage` and verifying the build fails when coverage drops below the configured thresholds. Delivers value by catching regressions in critical UI components (ProjectBoard, ChatInterface, AgentsPanel, ChoresPanel) and hooks.

**Acceptance Scenarios**:

1. **Given** the current frontend coverage thresholds are below 65/55/55/65 (statements/branches/functions/lines), **When** Phase 1 coverage work is merged, **Then** `npm run test:coverage` passes with thresholds set to 65/55/55/65.
2. **Given** Phase 1 coverage thresholds are enforced, **When** Phase 2 coverage work is merged, **Then** `npm run test:coverage` passes with thresholds set to 75/65/65/75.
3. **Given** the raised thresholds are in place, **When** a developer submits a PR that reduces coverage below the configured minimums, **Then** CI fails the coverage check and blocks merge.
4. **Given** ~20 untested hooks in `src/hooks/` exist, **When** hook tests are written using the TanStack Query wrapper + `createMockApi()` pattern, **Then** each hook has at least one test covering its primary behavior.
5. **Given** high-LOC components (ProjectBoard, ChatInterface, AgentsPanel, ChoresPanel, AddAgentModal, CleanUpConfirmModal, PipelineAnalytics, MarkdownRenderer, McpSettings, WorkflowSettings) are undertested, **When** component tests are written, **Then** each component has tests covering its primary render and interaction paths.

---

### User Story 2 - Backend Coverage Enforcement (Priority: P1)

As a developer, I want backend test suites extended to meet per-file coverage floors so that critical backend paths (board operations, pipeline orchestration, agent creation) are verified and regressions are caught before merge.

**Why this priority**: Backend modules handle critical business logic — board state management, pipeline orchestration, queue processing, and agent lifecycle. Missing coverage in these areas (116–246 untested statements per file) creates significant regression risk.

**Independent Test**: Can be tested by running per-module pytest coverage reports (e.g., `pytest --cov=src/api/board`, `pytest --cov=src/api/pipelines`) with per-file coverage assertions. Delivers value by ensuring critical paths like rate-limit recovery, token expiration handling, queue routing, and agent assignment are tested.

**Acceptance Scenarios**:

1. **Given** board.py has 116 missing statements, **When** test_api_board.py is extended with tests for column transforms, rate-limit recovery, token expiration, cache hash, and error branches, **Then** board.py coverage reports ≥ 80%.
2. **Given** pipelines.py has 108 missing statements, **When** tests are extended for queue mode routing (L388-406), position calculation, dequeue, and sub-issue errors, **Then** pipelines.py coverage reports ≥ 80%.
3. **Given** pipeline.py has 230 missing statements, **When** tests are extended for `_dequeue_next_pipeline()`, grace period logic, and BoundedDict races, **Then** pipeline.py coverage reports ≥ 85%.
4. **Given** agent_creator.py has 246 missing statements, **When** tests are extended for exception paths, config parsing, and tool assignment, **Then** agent_creator.py coverage reports ≥ 70%.

---

### User Story 3 - Full-Workflow Integration Test (Priority: P1)

As a developer, I want a full-workflow integration test that exercises the complete pipeline lifecycle (issue creation through cleanup and dequeue) so that cross-module interactions are verified end-to-end without requiring external services.

**Why this priority**: Individual unit tests can pass while cross-module interactions break. A full-workflow test verifying the entire lifecycle provides the highest confidence that the system works correctly as a whole. This depends on backend coverage work (User Story 2) landing first.

**Independent Test**: Can be tested by running `pytest tests/integration/test_full_workflow.py -v` and verifying the pipeline traverses all four statuses. Delivers value by catching integration bugs that unit tests miss.

**Acceptance Scenarios**:

1. **Given** a test environment using `httpx.ASGITransport` (following the `test_webhook_dispatch.py` pattern), **When** the full-workflow integration test runs, **Then** it successfully exercises: issue creation → project add → pipeline launch → agent assignment.
2. **Given** a pipeline is launched, **When** status transitions occur, **Then** the pipeline correctly moves through Backlog → Ready → In Progress → In Review.
3. **Given** a PR creation webhook fires, **When** the integration test processes it, **Then** the pipeline state updates correctly.
4. **Given** a PR merge webhook fires, **When** the integration test processes it, **Then** the cleanup trigger executes and the next pipeline is dequeued.

---

### User Story 4 - FIFO Queue Integration Tests (Priority: P2)

As a developer, I want FIFO queue integration tests verifying strict ordering across multiple pipelines so that queue behavior is validated with real interactions rather than mocked state.

**Why this priority**: Queue ordering is a critical correctness property. While unit tests verify individual queue operations, integration tests with 3+ pipelines ensure the FIFO invariant holds under realistic conditions.

**Independent Test**: Can be tested by running the extended `test_queue_mode.py` and verifying strict FIFO ordering across 3+ pipelines. Delivers value by catching queue ordering bugs that only manifest with multiple concurrent pipelines.

**Acceptance Scenarios**:

1. **Given** Pipeline A is launched and running, **When** Pipeline B is submitted, **Then** Pipeline B is queued (not started).
2. **Given** Pipeline A completes, **When** the dequeue logic runs, **Then** Pipeline B starts automatically.
3. **Given** Pipelines A, B, and C are submitted in order (A running, B and C queued), **When** A completes and then B completes, **Then** B starts before C, and C starts after B completes, preserving strict FIFO ordering.

---

### User Story 5 - Mutation Testing CI Enforcement (Priority: P2)

As a developer, I want mutation testing CI jobs to be blocking (not informational) so that code quality regressions are caught before merge and the mutation kill ratio is continuously enforced.

**Why this priority**: Mutation testing infrastructure already exists but runs as non-blocking. Making it blocking ensures that surviving mutants (indicating weak tests) are caught before merge. This is a configuration change with high impact and low effort.

**Independent Test**: Can be tested by verifying that CI mutation jobs fail when kill ratios drop below thresholds (frontend < 50%, backend < 60%). Delivers value by ensuring tests are meaningful and not just achieving coverage through trivial assertions.

**Acceptance Scenarios**:

1. **Given** `stryker.config.mjs` has `break` set to `null`, **When** the threshold is changed to 50, **Then** mutation testing exits with a non-zero code when the mutation score drops below 50%.
2. **Given** the Stryker job in `mutation-testing.yml` has `continue-on-error: true`, **When** `continue-on-error` is removed, **Then** the CI workflow fails when Stryker reports a score below the threshold.
3. **Given** mutmut backend shards have `continue-on-error: true`, **When** an aggregation step is added that checks kill ratio ≥ 60% and `continue-on-error` is removed, **Then** the CI workflow fails when the backend mutation kill ratio drops below 60%.
4. **Given** the mutation CI jobs are blocking, **When** a PR introduces code with surviving mutants below thresholds, **Then** the PR is blocked from merging.

---

### User Story 6 - Property-Based Queue Tests (Priority: P2)

As a developer, I want property-based tests exercising queue operations with random state combinations so that invariants (FIFO ordering, agent exclusivity, active pipeline limits) are verified across a wide range of inputs.

**Why this priority**: Property-based testing catches edge cases that manually-written tests miss. Queue operations have combinatorial state spaces where hand-crafted test cases cannot provide sufficient coverage.

**Independent Test**: Can be tested by running `pytest tests/property/ -v` and verifying queue rules pass across ≥ 200 Hypothesis examples. Delivers value by catching subtle queue ordering and concurrency bugs.

**Acceptance Scenarios**:

1. **Given** `test_pipeline_state_machine.py` contains a `RuleBasedStateMachine`, **When** queue-specific rules (`enqueue_pipeline`, `dequeue_pipeline`, `cancel_queued`) are added, **Then** the invariants are enforced: FIFO order is preserved, queued pipelines have no assigned agent, and active pipeline count per project never exceeds 1.
2. **Given** a new file `tests/property/test_blocking_queue.py` is created, **When** it exercises `count_active_pipelines_for_project()` and `get_queued_pipelines_for_project()` with random pipeline state combinations, **Then** all property assertions pass across ≥ 200 Hypothesis examples.
3. **Given** the state machine is extended with `should_skip_agent_trigger()` rules, **When** exclusivity within the grace period and stale reclaim at > 120 seconds are tested, **Then** the invariants hold across ≥ 200 Hypothesis examples.

---

### User Story 7 - Keyboard Navigation E2E & Accessibility (Priority: P2)

As a developer, I want a dedicated keyboard navigation E2E suite and extended accessibility assertions so that keyboard-only users can navigate all primary pages and accessibility regressions are caught in CI.

**Why this priority**: Accessibility is a quality requirement that affects all users. Adding keyboard navigation tests and axe-core scans provides automated verification that the application remains accessible as it evolves. No visual/layout changes are required — this is purely test instrumentation.

**Independent Test**: Can be tested by running `npx playwright test keyboard-navigation.spec.ts` and verifying all keyboard navigation assertions pass. Delivers value by ensuring Tab order, Enter/Space activation, Escape closing, focus trapping, and initial focus are correct across all primary pages.

**Acceptance Scenarios**:

1. **Given** no dedicated keyboard navigation E2E suite exists, **When** `e2e/keyboard-navigation.spec.ts` is created, **Then** it covers all primary pages with assertions for Tab order, Enter/Space activation, Escape closing modals, focus trapping, and correct initial focus.
2. **Given** existing E2E specs (board-navigation, agent-creation, chat-interaction) lack focus assertions, **When** `expect(locator).toBeFocused()` assertions are added for Tab/Enter/Escape flows, **Then** keyboard navigation regressions are caught.
3. **Given** axe-core automated accessibility checks are present in only 3 specs, **When** axe-core scans are added to agent-creation, pipeline-monitoring, mcp-tool-config, chat-interaction, and keyboard-navigation specs, **Then** automated accessibility violations are caught across all primary pages.
4. **Given** cross-service Playwright E2E against a real backend is evaluated, **When** feasibility is assessed (docker-compose + DB + GitHub API mock + auth bypass), **Then** findings and recommendations are documented as future work if not feasible within this phase.

---

### Edge Cases

- What happens when frontend coverage thresholds are raised but existing tests fail? The threshold increase must be paired with sufficient new tests to meet the floor — CI must pass with the new thresholds before merging.
- What happens when a backend file already exceeds the coverage floor? No additional tests are required for that file; the floor simply ensures it does not regress.
- What happens when mutation testing times out (60-minute limit)? The existing timeout configuration is preserved; PR-level `--since` mode is explicitly deferred until weekly blocking runs are stable.
- What happens when property-based tests find a failing example? Hypothesis records the minimal failing case for reproduction. The test must be fixed or the invariant revised before merging.
- What happens when an axe-core scan finds accessibility violations in existing code? The violations must be triaged — critical violations block the PR, while informational violations are documented for future remediation.
- What happens when the full-workflow integration test flakes due to timing? The test should use deterministic state transitions (no real async waits) via `httpx.ASGITransport` to eliminate flakiness.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST raise frontend Vitest coverage thresholds in two incremental phases via separate PRs: Phase 1 to 65/55/55/65 (statements/branches/functions/lines) and Phase 2 to 75/65/65/75.
- **FR-002**: System MUST prioritize testing ~20 untested hooks in `src/hooks/` first (highest ROI), followed by high-LOC components: ProjectBoard, ChatInterface, AgentsPanel, ChoresPanel, AddAgentModal, CleanUpConfirmModal, PipelineAnalytics, MarkdownRenderer, McpSettings, WorkflowSettings.
- **FR-003**: System MUST extend backend test suites to meet per-file coverage floors: board.py ≥ 80%, pipelines.py ≥ 80%, pipeline.py ≥ 85%, agent_creator.py ≥ 70%.
- **FR-004**: System MUST implement a full-workflow integration test at `tests/integration/test_full_workflow.py` using `httpx.ASGITransport` covering: issue creation → project add → pipeline launch → agent assignment; status transitions Backlog → Ready → In Progress → In Review; PR creation webhook → pipeline state update; PR merge webhook → cleanup trigger → dequeue next pipeline.
- **FR-005**: System MUST extend `test_queue_mode.py` with FIFO queue integration covering: Pipeline A launches → Pipeline B queued → A completes → B dequeues, verified with 3+ pipelines to assert strict FIFO ordering.
- **FR-006**: System MUST make mutation testing CI jobs blocking: set `stryker.config.mjs` `break` from `null` to `50` and remove `continue-on-error` from the Stryker job in `mutation-testing.yml`; add an aggregation step to mutmut backend shards that fails the job if the kill ratio is below 60% and remove `continue-on-error` from those shards.
- **FR-007**: System MUST extend `RuleBasedStateMachine` in `test_pipeline_state_machine.py` with queue-specific rules: `enqueue_pipeline`, `dequeue_pipeline`, `cancel_queued`; enforcing invariants that FIFO order is preserved, queued pipelines have no assigned agent, and active pipeline count per project never exceeds 1.
- **FR-008**: System MUST add a new property test file `tests/property/test_blocking_queue.py` exercising `count_active_pipelines_for_project()` and `get_queued_pipelines_for_project()` with random pipeline state combinations, and extend the state machine with `should_skip_agent_trigger()` exclusivity within the grace period and stale reclaim at > 120 s, running across ≥ 200 Hypothesis examples.
- **FR-009**: System MUST create `e2e/keyboard-navigation.spec.ts` as a dedicated keyboard navigation suite covering all primary pages with assertions for Tab order, Enter/Space activation, Escape closing modals, focus trapping, and correct initial focus.
- **FR-010**: System MUST extend existing E2E specs (board-navigation, agent-creation, chat-interaction) with `expect(locator).toBeFocused()` assertions for Tab/Enter/Escape flows.
- **FR-011**: System MUST add axe-core automated accessibility checks to agent-creation, pipeline-monitoring, mcp-tool-config, chat-interaction, and keyboard-navigation specs.
- **FR-012**: System SHOULD evaluate cross-service Playwright E2E against a real backend (docker-compose + DB + GitHub API mock + auth bypass) and document findings as future work if not feasible within this phase.

### Exclusions

- **health.py** error paths are explicitly excluded from coverage targets (intentionally non-raising by design).
- **WebSocket handlers** are explicitly excluded from coverage targets.
- **Error-returning webhooks** are explicitly excluded from coverage targets (intentionally non-raising by design).
- **PR-level `--since` mode** for mutation testing is deferred until weekly blocking runs are stable.

### Dependencies & Ordering

- Frontend coverage (FR-001, FR-002) and backend coverage (FR-003) can be executed in parallel.
- Full-workflow integration test (FR-004) depends on backend coverage work (FR-003) landing first.
- Mutation enforcement (FR-006), property tests (FR-007, FR-008), and keyboard E2E (FR-009, FR-010, FR-011) are all independent of coverage work and can be executed in parallel.
- FIFO queue integration (FR-005) can be developed alongside backend coverage but should be verified after backend coverage tests stabilize.

### Assumptions

- The existing test infrastructure (Vitest, pytest, Playwright, Hypothesis, Stryker, mutmut) is already installed and configured — no new tooling installation is required.
- Frontend hook tests follow the established TanStack Query wrapper + `createMockApi()` pattern.
- Backend integration tests follow the established `httpx.ASGITransport` pattern from `test_webhook_dispatch.py`.
- Property tests follow the established Hypothesis `RuleBasedStateMachine` pattern.
- The 60-minute timeout for full Stryker/mutmut runs is an existing constraint that will be preserved.
- Coverage threshold increases will be delivered via separate PRs (Phase 1 and Phase 2) to reduce risk of CI breakage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Frontend test coverage meets or exceeds 75/65/65/75 (statements/branches/functions/lines) as verified by `npm run test:coverage`.
- **SC-002**: Backend per-file coverage meets or exceeds the defined floors — board.py ≥ 80%, pipelines.py ≥ 80%, pipeline.py ≥ 85%, agent_creator.py ≥ 70% — as verified by per-module pytest coverage reports.
- **SC-003**: The full-workflow integration test at `tests/integration/test_full_workflow.py` passes, with a pipeline traversing all four statuses (Backlog → Ready → In Progress → In Review) end-to-end.
- **SC-004**: FIFO queue ordering is verified across 3+ pipelines in `test_queue_mode.py`, with strict ordering assertions passing.
- **SC-005**: Mutation testing CI jobs are blocking — mutation testing exits non-zero when the frontend mutation score drops below 50%, and mutmut backend shards fail when the kill ratio drops below 60%.
- **SC-006**: Property-based tests pass across ≥ 200 Hypothesis examples, with all queue invariants (FIFO order, no agent on queued pipelines, single active pipeline per project) enforced.
- **SC-007**: Keyboard navigation E2E suite (`keyboard-navigation.spec.ts`) passes for all primary pages, verifying Tab order, Enter/Space activation, Escape closing, focus trapping, and initial focus.
- **SC-008**: axe-core accessibility scans are present in at least 8 Playwright specs (up from 3), covering agent-creation, pipeline-monitoring, mcp-tool-config, chat-interaction, and keyboard-navigation.
- **SC-009**: All CI checks (coverage, mutation, property tests, E2E) pass in the CI pipeline without `continue-on-error` flags masking failures.
