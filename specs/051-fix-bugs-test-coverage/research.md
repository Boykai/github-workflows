# Research: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature Branch**: `051-fix-bugs-test-coverage`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md)
**Predecessor**: `050-fix-bugs-test-coverage` (RT-001 through RT-004 addressed bugs now fixed)

## Research Tasks

### RT-001: Frontend Static Analysis Triage Strategy

**Context**: The frontend lint sweep (started in spec 050, ~50% complete) needs to be finished.
ESLint violations must be triaged into fix-now, fix-later, or false-positive categories. TypeScript
strict mode must report zero errors.

**Decision**: Run `npx eslint . --max-warnings=0` and categorize all remaining violations.
Fix-now items include unused variables, missing return types, and unsafe type assertions. Fix-later
items include stylistic issues that don't affect correctness. Document false-positives with inline
`// eslint-disable-next-line` comments and justification.

**Rationale**: Finishing the sweep before writing new tests ensures new test code is written
against a clean, type-safe codebase. This prevents compounding violations in new test files.

**Alternatives considered**:
- Suppress all warnings globally — hides real issues, defeats the purpose.
- Address only new violations — leaves existing debt that confuses developers.
- Switch to Biome — large migration cost, no immediate benefit.

---

### RT-002: Flaky Test Detection Methodology (5-Run Strategy)

**Context**: Both test suites need flaky test detection. The backend has an existing
`scripts/detect_flaky.py` script. The frontend needs an equivalent approach.

**Decision**: Run each test suite 5 consecutive times, compare results across runs, and flag any
test that produces different outcomes. Backend uses the existing `detect_flaky.py --runs=5`.
Frontend uses `npm run test -- --reporter=verbose` run 5 times with output comparison. Root cause
categories: async timing, shared state, environment dependency, non-deterministic ordering.

**Rationale**: 5 runs provides reasonable statistical confidence while keeping execution time
manageable. The existing backend script is proven and reusable. Categorizing root causes guides
targeted fixes rather than blind quarantine.

**Alternatives considered**:
- `pytest-randomly` only — detects order-dependent but not timing issues.
- 10+ runs for higher confidence — diminishing returns, significantly longer execution.
- `pytest-repeat` — doesn't compare across runs for consistency.

---

### RT-003: API Route Integration Test Pattern

**Context**: Backend has zero integration tests for key API routes (auth callback, webhook dispatch,
pipeline launch, chat confirm). Need a consistent pattern for testing FastAPI routes.

**Decision**: Use `httpx.AsyncClient` + `ASGITransport` pattern already established in existing
integration tests. Each route test covers: valid input (200/201), invalid input (400/422),
authorization checks (401/403), and edge cases (empty payloads, duplicate requests). Test fixtures
provide authenticated client instances with mock service dependencies.

**Rationale**: The `httpx.AsyncClient` + `ASGITransport` pattern is already the project standard
for integration testing. It provides real HTTP semantics without requiring a running server.
Consistent patterns reduce cognitive overhead for test authors.

**Alternatives considered**:
- `TestClient` (sync) — doesn't support async endpoints natively.
- Full server startup with `uvicorn` — unnecessarily heavy, slow tests.
- `requests` + live server — requires server management, port conflicts.

---

### RT-004: Board Component Test Strategy

**Context**: 14 of 32 board components are untested. The top 5 priority targets are ProjectBoard,
BoardToolbar, CleanUpConfirmModal, AgentColumnCell, and BoardDragOverlay. Board components use
`@dnd-kit` for drag-and-drop functionality.

**Decision**: Use `@testing-library/react` with `DndContext` wrapper for drag-drop components.
Each component test covers: rendering with various props, user interactions (click, drag, hover),
conditional rendering (loading, error, empty states), and accessibility attributes. DndContext
provides the drag-and-drop context without requiring full application setup.

**Rationale**: `@testing-library/react` is already the project standard. Wrapping components in
`DndContext` mirrors real usage without needing the full board tree. Testing user interactions
matches the library's philosophy of testing behavior over implementation details.

**Alternatives considered**:
- Enzyme — deprecated, doesn't support React 19.
- Snapshot testing — brittle, low value for detecting real behavioral bugs.
- E2E only for board components — slow feedback, hard to isolate component behavior.

---

### RT-005: Hook Testing Strategy (Branch Coverage Focus)

**Context**: 3 hooks are untested (useBoardDragDrop, useConfirmation, useUnsavedPipelineGuard).
Overall hook branch coverage is at 44%, target is 50%+. Need to cover 5 key branch paths per hook.

**Decision**: Use `renderHook` from `@testing-library/react` to test hooks in isolation. Each hook
test covers 5 branch paths: success path, error state, loading state, empty data, and API failure.
For hooks that depend on context providers (e.g., QueryClient, Router), wrap in appropriate
providers. Use `waitFor` for async state changes.

**Rationale**: `renderHook` isolates hook logic from component rendering, making branch coverage
direct and measurable. The 5 branch paths cover the most common conditional patterns in React
hooks. Provider wrappers are necessary for hooks using context APIs.

**Alternatives considered**:
- Test hooks only through component tests — harder to achieve targeted branch coverage.
- Mock all hook dependencies — over-mocking reduces test value.
- Use `enzyme` shallow rendering — deprecated, incompatible with React 19.

---

### RT-006: Property-Based Testing (Hypothesis) Expansion

**Context**: Property-based tests need to verify pipeline state machine transition invariants and
markdown parser roundtrip consistency. Existing property tests exist in `tests/property/`.

**Decision**: Use Hypothesis with `@given` strategies to generate 100+ input scenarios per property.
For the pipeline state machine: verify that all valid transition sequences produce valid end states,
that no invalid transition escapes validation, and that idempotent operations are truly idempotent.
For the markdown parser: verify roundtrip consistency (parse → serialize → parse yields same AST).

**Rationale**: Property-based testing excels at finding edge cases in state machines and parsers
where exhaustive input enumeration is impractical. 100+ examples provides a reasonable balance
between coverage and execution time. Hypothesis's shrinking capability helps identify minimal
failing cases.

**Alternatives considered**:
- Exhaustive enumeration — impractical for large state spaces.
- Manual edge cases only — misses non-obvious combinations.
- QuickCheck-style (different library) — Hypothesis is already installed and proven.

---

### RT-007: Mutation Testing Expansion Strategy

**Context**: Backend mutmut currently covers only `src/services/`. Need to expand to API routes,
middleware, and utilities. Existing 4 shards: auth-and-projects, orchestration, app-and-data,
agents-and-integrations.

**Decision**: Distribute new mutation targets across the existing 4 shards by module affinity:
- auth-and-projects: add `src/api/auth.py`, `src/api/projects.py`
- orchestration: add `src/api/pipeline.py`, `src/middleware/`
- app-and-data: add `src/api/chat.py`, `src/utils.py`
- agents-and-integrations: add `src/api/webhooks.py`, `src/dependencies.py`

**Rationale**: Distributing by affinity keeps shard execution times balanced and groups related
code together. Using existing shards avoids adding a 5th shard with its own CI overhead. The
affinity mapping matches the existing test directory structure.

**Alternatives considered**:
- Create new shard (api-and-middleware) — CI timeout risk, maintenance overhead.
- Mutate everything in one run — too slow, exceeds CI timeout.
- Random distribution — loses test-code affinity, harder to debug failures.

---

### RT-008: Threshold Ratcheting Strategy

**Context**: Coverage thresholds need to be permanently raised once consistently met. Backend:
75 → 80 line coverage. Frontend: 50/44/41 → 55/50/45 statement/branch/function.

**Decision**: Ratchet thresholds as the final step (Phase E), only after all coverage expansion
is complete and verified. Update `pyproject.toml` `fail_under` for backend and `vitest.config.ts`
`thresholds` for frontend. Thresholds are one-directional — they may only be raised, never lowered.

**Rationale**: Ratcheting last ensures the codebase consistently meets thresholds before enforcement.
Premature ratcheting blocks development. One-directional policy prevents quality regression.

**Alternatives considered**:
- Ratchet immediately (optimistic) — blocks hotfixes if tests aren't ready.
- Gradual ratcheting (75 → 77 → 80) — unnecessary complexity for a 5-point increase.
- No enforcement (advisory only) — allows silent regression.

## Summary of Decisions

| # | Topic | Decision | Risk |
|---|-------|----------|------|
| RT-001 | Frontend static analysis | Finish sweep, triage fix-now/fix-later/false-positive | Low — established workflow |
| RT-002 | Flaky detection | 5-run methodology, categorize root causes | Low — existing script |
| RT-003 | API route tests | httpx.AsyncClient + ASGITransport pattern | Low — established pattern |
| RT-004 | Board component tests | @testing-library/react + DndContext wrapper | Low — standard approach |
| RT-005 | Hook testing | renderHook with 5 branch paths per hook | Low — standard approach |
| RT-006 | Property-based tests | Hypothesis 100+ examples, state machine + parser | Medium — complex properties |
| RT-007 | Mutation expansion | Distribute across 4 existing shards by module affinity | Medium — shard balance |
| RT-008 | Threshold ratcheting | Ratchet as final step, one-directional only | Low — well-understood pattern |
