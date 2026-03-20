# Research: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature**: `052-fix-bugs-test-coverage`
**Date**: 2026-03-19

## Research Tasks

### R1: Backend Integration Test Pattern for API Routes

**Task**: Research the established integration test pattern for the Solune FastAPI backend.

**Decision**: Use `httpx.AsyncClient` with `ASGITransport` as established in the existing integration tests (e.g., `test_health_endpoint.py`). Mock services with `AsyncMock(spec=ServiceClass)`, patch module-level globals with `unittest.mock.patch()`, and assert response status codes + JSON structure.

**Rationale**: The project already has a proven integration test pattern with fixtures in `conftest.py` providing a fully-wired `client` fixture with dependency overrides. Deviating from this pattern would introduce inconsistency and require additional infrastructure. The `test_health_endpoint.py` pattern covers healthy/unhealthy/warn scenarios and serves as a direct template.

**Alternatives Considered**:
- **TestClient (Starlette sync)**: Rejected because the backend is fully async; `httpx.AsyncClient` with `ASGITransport` is the async-native approach already adopted.
- **pytest-httpx**: Rejected because it's designed for mocking outbound HTTP calls, not for testing the app itself.

---

### R2: Frontend Board Component Test Pattern with DndContext

**Task**: Research how to test board components that depend on `@dnd-kit` drag-and-drop contextn.

**Decision**: Wrap components in `DndContext` provider during test rendering. Use factory functions (e.g., `createColumn()`, `createBoardItem()`) for test data. Assert on rendered content, empty states, and interaction handlers using `@testing-library/react`.

**Rationale**: The existing `BoardColumn.test.tsx` establishes this pattern — it uses `vi.mock()` for external dependencies, factory functions for test data, and assertion patterns for both content rendering and a11y compliance. The `DndContext` wrapper is required because components access drag-and-drop context internally.

**Alternatives Considered**:
- **Shallow rendering**: Rejected because React Testing Library deliberately doesn't support shallow rendering; full rendering with provider wrappers is the recommended approach.
- **Mocking @dnd-kit entirely**: Rejected because it would miss integration bugs between components and the drag-drop system. Wrapping in `DndContext` is lightweight and mirrors production.

---

### R3: Frontend Hook Test Pattern with Branch Coverage

**Task**: Research how to achieve 5-branch-path coverage for React hooks.

**Decision**: Use `renderHook` from `@testing-library/react` with provider wrappers (`QueryClientProvider`, `RouterProvider`, `DndContext` where applicable). Test 5 branch paths per hook: success, error, loading, empty, and edge-case. Follow the pattern established in `useBoardControls.test.tsx` which uses factory functions and localStorage mocking.

**Rationale**: The existing hook tests demonstrate comprehensive branch coverage through explicit state management. `useBoardControls.test.tsx` tests localStorage persistence, filtering edge cases, and per-project state loading — all representing distinct branches. This pattern directly applies to untested hooks.

**Alternatives Considered**:
- **enzyme `shallow`**: Rejected; enzyme is deprecated and not compatible with React 19.
- **Direct function invocation**: Rejected; hooks must be called within a React rendering context; `renderHook` provides this correctly.

---

### R4: Property-Based Testing for Pipeline State Machine

**Task**: Research best practices for Hypothesis stateful testing of the pipeline state machine.

**Decision**: Use Hypothesis `RuleBasedStateMachine` with `@rule()` transitions and `@precondition()` guards, plus `@invariant()` checks. The existing `test_pipeline_state_machine.py` already implements this pattern with bounds checking, subset validation, and terminal state consistency invariants. Extend with ≥100 generated examples via `@settings(max_examples=100)`.

**Rationale**: The existing property test already uses the exact recommended pattern. New tests should add coverage for edge cases not yet covered: concurrent recovery attempts, crash-during-recovery state, and empty-state initialization. The Hypothesis stateful testing framework is purpose-built for state machine verification.

**Alternatives Considered**:
- **Manual enumeration of transitions**: Rejected because the state space is too large for manual enumeration; property-based testing explores the space more efficiently.
- **Model-based testing with separate spec**: Rejected as over-engineering; the `@rule() + @precondition() + @invariant()` pattern is sufficient.

---

### R5: Flaky Test Detection and Quarantine Process

**Task**: Research the flaky detection mechanism and quarantine workflow.

**Decision**: Use the existing `detect_flaky.py` script which parses JUnit XML results from multiple test runs and identifies tests with mixed pass/fail outcomes. Run 5 iterations per suite. Quarantine with `@pytest.mark.skip(reason="flaky: <root-cause>")` for backend and `it.skip("flaky: <root-cause>")` for frontend. File a GitHub issue per flaky test with the root cause.

**Rationale**: 5 runs balances statistical confidence with CI execution time. Google's Testing Blog recommends ≥3 runs for flaky detection; 5 provides additional confidence. The JUnit XML diff approach is well-tested in the existing script.

**Alternatives Considered**:
- **pytest-rerunfailures**: Rejected because it masks flakiness rather than detecting it. Our goal is to find and quarantine flaky tests, not automatically retry them.
- **10+ runs**: Rejected because the marginal detection improvement doesn't justify the additional CI time.

---

### R6: Mutation Testing Shard Expansion Strategy

**Task**: Research how to expand mutation testing targets to include API routes and middleware.

**Decision**: The existing shard configuration already includes a 5th shard `api-and-middleware` targeting `src/api/`, `src/middleware/`, and `src/utils.py`. No shard reconfiguration is needed — the expansion was already planned. Verify that this shard executes correctly and completes within CI timeout.

**Rationale**: The `run_mutmut_shard.py` script already defines 5 shards with the api-and-middleware shard in place. The module-affinity distribution is already correct — API routes are grouped with middleware because they share testing infrastructure (the `client` fixture).

**Alternatives Considered**:
- **Distributing API routes across existing 4 shards**: Rejected because it would unbalance shard sizes and API routes share more test infrastructure with middleware than with services.
- **Creating separate shards per API module**: Rejected because 19 separate shards would create excessive CI overhead.

---

### R7: Coverage Threshold Ratcheting Strategy

**Task**: Research the safest approach to ratchet coverage thresholds upward.

**Decision**: Ratchet as the final step (Phase E) only after all tests pass and coverage is verified. Update `fail_under = 80` in `pyproject.toml` `[tool.coverage.report]` and update thresholds in `vitest.config.ts` to `statements: 55, branches: 50, functions: 45, lines: 55`. Thresholds only ratchet upward, never down.

**Rationale**: Ratcheting before verification would block development on unmet thresholds. By ratcheting last, we ensure the codebase already meets the new thresholds before enforcing them. The one-directional ratchet prevents regression.

**Alternatives Considered**:
- **Ratchet incrementally per phase**: Rejected because it adds CI friction during the implementation phase and could block parallel development.
- **Use a separate CI job for threshold enforcement**: Rejected because it duplicates test execution; the existing coverage tool supports `fail_under` natively.

---

### R8: Emergency Hotfix Override Process

**Task**: Research how to safely bypass coverage gates for emergency hotfixes.

**Decision**: Document a `SKIP_COVERAGE=1` environment variable bypass in the pre-commit hook and CI configuration. The bypass must be logged and traceable. Include an expiration mechanism: a post-merge CI check that fails if the override flag persists in the commit history beyond one merge.

**Rationale**: Production emergencies sometimes require shipping fixes without full test coverage. The key is ensuring the bypass is auditable and temporary. An expiration mechanism prevents the override from becoming permanent.

**Alternatives Considered**:
- **No override mechanism**: Rejected because it would force developers to write tests during production outages, potentially extending the outage.
- **Admin-only override with approval**: Rejected as over-engineered for a small team; the audit trail provides accountability without approval bottlenecks.
