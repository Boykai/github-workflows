# Research: Find/Fix Bugs & Increase Test Coverage

**Feature Branch**: `050-fix-bugs-test-coverage`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md)

## Research Tasks

### RT-001: Mutmut Trampoline Name-Resolution Bug

**Context**: The issue reports that `get_mutant_name()` strips a `src.` prefix but the trampoline
uses `orig.__module__` which retains it, causing 0% kill rate.

**Decision**: Patch the `run_mutmut_shard.py` script to normalize module paths before comparison.
Additionally, pin mutmut ≥3.2.0 (already done in `pyproject.toml`) and verify the trampoline
behavior with the installed version. If mutmut's internal trampoline is the root cause, set the
`PYTHONPATH` so that `src/` is not duplicated in module resolution.

**Rationale**: The shard script already manipulates `pyproject.toml` paths at runtime. Aligning
the `PYTHONPATH` or adding a `--paths-prefix` normalization is less invasive than forking mutmut.
The `src/` layout (flat namespace packages) causes `src.services.foo` vs `services.foo` mismatch.

**Alternatives considered**:
- Fork and patch mutmut's trampoline template — too much maintenance burden.
- Pin an older mutmut version — loses recent fixes and performance improvements.
- Use `cosmic-ray` instead of mutmut — large migration cost with no test compatibility.

---

### RT-002: Cache Leakage Between Test Boundaries

**Context**: A global in-memory cache (`cache.py`) is not cleared between unit and integration
test runs, causing stale state to leak across boundaries.

**Decision**: Verify that the existing `_clear_test_caches` autouse fixture in `conftest.py` covers
all cache entry points. If any cache singleton or module-level dict is missed, add it. Use
`pytest`'s `autouse=True` fixture with `function` scope so every test starts with a clean cache.

**Rationale**: Autouse fixtures at function scope are the standard pytest pattern for test
isolation. The existing fixture exists but may not cover all cache entry points (e.g., LRU caches,
module-level dicts, or class-level singletons).

**Alternatives considered**:
- Use `pytest-xdist` process isolation — overkill, slows down test suite.
- Patch `cache.py` to disable caching in test mode — leaky abstraction, fragile.
- Use `importlib.reload` — breaks other module references.

---

### RT-003: AsyncMock Warnings in Integration Tests

**Context**: `AsyncMock(spec=...)` produces deprecation/runtime warnings. The repo best practice
is to use plain async stub classes instead.

**Decision**: Replace all `AsyncMock(spec=SomeService)` patterns in integration test fixtures with
plain async stub classes that implement the same interface. This is already the documented repo
best practice.

**Rationale**: Plain async stub classes are more explicit, avoid mock framework warnings, and
produce clearer error messages when methods are called incorrectly. They also work better with
type checkers.

**Alternatives considered**:
- Suppress warnings with `pytest.mark.filterwarnings` — hides real issues.
- Upgrade to a newer mock library — unnecessary dependency.
- Use `unittest.mock.patch` with `new_callable` — still relies on mock framework.

---

### RT-004: Pipeline "Stuck in In Progress" Bug

**Context**: The copilot polling pipeline reverts status transitions instead of accepting them.
The state validation logic may be too strict or the transition ordering may be incorrect.

**Decision**: Review `state_validation.py` transition logic. Ensure the state machine accepts
forward transitions (e.g., Queued → In Progress → Completed) and only rejects invalid backward
transitions. Add explicit test cases for all valid transition sequences.

**Rationale**: State machine bugs are subtle. The fix should be in the validation logic, not in
skipping validation. Property-based tests (Hypothesis) can verify the state machine exhaustively.

**Alternatives considered**:
- Disable state validation — defeats the purpose of the guard.
- Use a state machine library (e.g., `transitions`) — adds dependency for a small state space.
- Log-and-continue instead of reject — hides bugs in production.

---

### RT-005: Backend Test Coverage Strategy (75% → 85%+)

**Context**: Backend coverage is at 75% with 121+ test files. Need to reach 80–85%+ by targeting
high-risk modules.

**Decision**: Prioritize test coverage by risk, not by ease:
1. **API route integration tests** — currently zero integration tests for routes. Use
   `httpx.AsyncClient` + `ASGITransport` pattern already established in existing integration tests.
2. **High-risk service modules** — `recovery.py`, `state_validation.py`, `transitions.py`,
   `signal_bridge.py`, `signal_delivery.py`, `guard_service.py`.
3. **Property-based tests** — Use Hypothesis for state machines and parsers.
4. **Characterization tests** — Pin DRY candidates before any refactoring.

**Rationale**: Risk-first targeting protects critical business logic. API routes are a major gap
(zero integration tests). Property-based testing catches edge cases that example-based tests miss.

**Alternatives considered**:
- Coverage-first (target lowest-coverage files) — wastes effort on low-risk utility code.
- Only unit tests — misses integration-level bugs in API routes.
- Skip characterization tests — risks breaking existing behavior during future refactoring.

---

### RT-006: Frontend Test Coverage Strategy (51% → 65%+)

**Context**: Frontend coverage is at 51% statements, 44% branches, 41% functions. E2E suite has
10 specs (Playwright).

**Decision**: Prioritize:
1. **App.tsx** — 0% coverage, 39 untested statements. Use `MemoryRouter` for route testing.
2. **Board components** — partial coverage. Add interaction tests for drag-drop, rendering.
3. **Hooks branch coverage** — 44% → 55%+. Focus on error/loading/empty states.
4. **E2E expansion** — 10 → 14 specs. Add agent creation, pipeline monitoring, MCP config, error
   recovery.

**Rationale**: App.tsx at 0% is the single biggest coverage gap. Board components are high-value
user interactions. Hooks have the lowest branch coverage. E2E specs validate end-to-end flows.

**Alternatives considered**:
- Snapshot testing for components — brittle, low value for detecting real bugs.
- Visual regression testing (e.g., Percy) — infrastructure cost, overkill for this phase.
- Only E2E tests — slow feedback loop, hard to debug failures.

---

### RT-007: Mutation Testing Expansion

**Context**: Backend mutmut covers only `src/services/`. Frontend Stryker covers `hooks/` and
`lib/`. Both need expansion.

**Decision**:
- **Backend**: Expand `paths_to_mutate` to include `src/api/`, `src/middleware/`, `src/utils.py`.
  Run sharded via the existing `run_mutmut_shard.py` script after adding new shards.
- **Frontend**: Keep current Stryker scope (`hooks/`, `lib/`) but add targeted assertions to kill
  surviving mutants. Consider adding `components/` in a future phase.

**Rationale**: Gradual expansion (services → API → middleware) avoids overwhelming the team with
mutant volume. The shard script already handles parallel execution.

**Alternatives considered**:
- Mutate everything at once — too many mutants, CI timeout risk.
- Different mutation tool (e.g., cosmic-ray for backend) — migration cost.
- Skip mutation testing — loses the strongest test quality signal.

---

### RT-008: CI Hardening Strategy

**Context**: Coverage thresholds need ratcheting. Pre-commit hooks need strengthening. Chaos and
concurrency tests need expansion.

**Decision**:
- **Ratchet thresholds** only after consistently meeting them in CI.
  Backend: 75 → 80. Frontend: 50/44/41 → 55/50/45.
- **Pre-commit hooks**: The existing `scripts/pre-commit` already runs ruff + pyright (backend) and
  eslint + tsc (frontend) on changed files. Verify it covers all entry points.
- **Chaos/concurrency tests**: Add targeted scenarios for concurrent state updates, DB pool
  exhaustion, WebSocket reconnection. Use existing `tests/chaos/` and `tests/concurrency/`
  directories.

**Rationale**: Ratcheting prevents regression. Pre-commit hooks catch issues before CI. Chaos tests
guard against hard-to-reproduce production failures. All three reinforce each other.

**Alternatives considered**:
- Aggressive threshold jumps (75 → 90) — blocks hotfixes, demoralizes team.
- External quality gates (SonarQube) — adds infrastructure, duplicates existing tooling.
- Remove pre-commit hooks in favor of CI-only checks — slower feedback loop.

---

### RT-009: Flaky Test Detection Strategy

**Context**: Backend has a `scripts/detect_flaky.py` script. Need to run across 5+ iterations and
quarantine genuinely flaky tests.

**Decision**: Use the existing `detect_flaky.py` script with `--runs=10` for thorough detection.
Root causes are typically: async timing (missing `await`), shared state (un-cleared globals),
non-deterministic ordering (set iteration), and time-dependent assertions.

**Rationale**: 10 runs provides statistical confidence. Root cause categorization guides fixes.
Quarantining (via `@pytest.mark.skip(reason="flaky: ...")`) prevents false CI failures while
fixes are developed.

**Alternatives considered**:
- `pytest-randomly` only — detects order-dependent tests but not timing issues.
- `pytest-repeat` only — doesn't compare across runs for consistency.
- Delete flaky tests — loses coverage, hides real bugs.

## Summary of Decisions

| # | Topic | Decision | Risk |
|---|-------|----------|------|
| RT-001 | Mutmut trampoline | Normalize PYTHONPATH in shard script | Low |
| RT-002 | Cache leakage | Verify/extend autouse fixture | Low |
| RT-003 | AsyncMock warnings | Replace with plain async stubs | Low |
| RT-004 | Pipeline stuck state | Fix state validation transitions | Medium |
| RT-005 | Backend coverage | Risk-first targeting, API routes first | Low |
| RT-006 | Frontend coverage | App.tsx first, then hooks branches | Low |
| RT-007 | Mutation expansion | Gradual: services → API → middleware | Low |
| RT-008 | CI hardening | Ratchet after meeting thresholds consistently | Low |
| RT-009 | Flaky tests | 10-run detection, quarantine + fix | Low |
