# Quickstart: Performance Review

**Feature Branch**: `034-performance-review`
**Date**: 2026-03-11
**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

## Overview

This guide provides the implementation quickstart for Spec 034 — a balanced first-pass performance optimization across backend and frontend. The work is structured in four phases with explicit dependencies.

## Phase Dependency Graph

```text
Phase 1: Baseline & Spec 022 Audit
  ├── 1A: Backend baseline measurement
  ├── 1B: Frontend baseline measurement
  └── 1C: Spec 022 gap analysis
        │
        ▼
Phase 2: Backend + Frontend Refresh Fixes (parallel)
  ├── 2A: Backend API consumption fixes ──────► depends on 1A, 1C
  └── 2B: Frontend refresh-path fixes ────────► depends on 1B, 1C
        │
        ▼
Phase 3: Frontend Render Optimization + Verification (parallel)
  ├── 3A: Frontend render optimization ───────► depends on 2B
  └── 3B: Verification & regression coverage ─► depends on 2A, 2B, 3A
        │
        ▼
Phase 4: Optional Second-Wave (deferred)
  └── Only if Phase 3 measurements fail targets
```

## Implementation Sequence

### Phase 1A — Backend Baseline Measurement

**Goal**: Capture current backend performance numbers before any code changes.

**Steps**:

1. Add lightweight instrumentation to measure:
   - Outbound GitHub API call count during 5 minutes of idle board viewing
   - Board endpoint response time (warm cache vs. cold cache)
   - WebSocket subscription message count during idle period
   - Polling cycle GitHub API call count
2. Run measurements against a representative project (50–100 tasks, 4–6 columns)
3. Document results as the backend baseline in test comments or a baseline document

**Key files**:

- `backend/src/api/board.py` — board endpoint to instrument
- `backend/src/api/projects.py` — WebSocket subscription to instrument
- `backend/src/services/copilot_polling/polling_loop.py` — polling loop to instrument
- `backend/tests/unit/test_api_board.py` — extend with baseline assertions

**Verification**: Baseline numbers are documented and reproducible.

---

### Phase 1B — Frontend Baseline Measurement

**Goal**: Capture current frontend performance numbers.

**Steps**:

1. Profile board load and interaction using React DevTools Profiler:
   - Component render counts on initial load
   - Render duration per component
   - Rerender scope during card drag operations
   - Event listener fire rates during interactions
2. Inspect network activity:
   - WebSocket message handling and query invalidation
   - Fallback polling behavior and invalidation scope
   - Board data query refetch patterns
3. Document results as the frontend baseline

**Key files**:

- `frontend/src/hooks/useRealTimeSync.ts` — WebSocket/polling behavior
- `frontend/src/hooks/useBoardRefresh.ts` — auto-refresh policy
- `frontend/src/pages/ProjectsPage.tsx` — derived state computation
- `frontend/src/components/board/BoardColumn.tsx` — column rendering
- `frontend/src/components/board/IssueCard.tsx` — card rendering

**Verification**: Baseline render counts and network patterns are documented.

---

### Phase 1C — Spec 022 Gap Analysis

**Goal**: Confirm which Spec 022 items are fully implemented and identify remaining gaps.

**Steps**:

1. Verify WebSocket change detection (SHA256 hash comparison) is working correctly
2. Verify board cache TTL alignment (300s) is consistent across all entry points
3. Verify sub-issue cache invalidation on manual refresh clears all related entries
4. Verify stale fallback is only used during rate-limit conditions
5. Document any gaps found

**Key files**:

- `backend/src/api/board.py` — cache TTL and stale fallback
- `backend/src/api/projects.py` — WebSocket change detection
- `backend/src/services/cache.py` — TTL configuration

**Verification**: Gap analysis document with pass/fail per Spec 022 criterion.

---

### Phase 2A — Backend API Consumption Fixes

**Goal**: Reduce unnecessary GitHub API calls during idle board viewing and polling.

**Depends on**: Phase 1A (baseline), Phase 1C (gap analysis)

**Steps**:

1. Ensure WebSocket subscription refresh (30s cycle) checks cache before calling GitHub API
2. Verify sub-issue caches are reused during non-manual board refreshes
3. Ensure fallback polling does not trigger expensive full board data refreshes
4. Consolidate any duplicate repository resolution paths (workflow.py → utils.py)
5. Measure improvement against Phase 1A baseline

**Key files**:

- `backend/src/api/projects.py` — WebSocket refresh logic
- `backend/src/api/board.py` — sub-issue cache reuse
- `backend/src/services/copilot_polling/polling_loop.py` — polling behavior
- `backend/src/api/workflow.py` — duplicate repo resolution
- `backend/src/utils.py` — canonical repo resolution

**Verification**: SC-001 (≥ 50% idle API reduction), SC-002 (≥ 30% warm cache improvement).

---

### Phase 2B — Frontend Refresh-Path Fixes

**Goal**: Ensure lightweight updates stay decoupled from expensive board queries.

**Depends on**: Phase 1B (baseline), Phase 1C (gap analysis)

**Steps**:

1. Verify polling fallback invalidates only task queries, not board data queries
2. Ensure auto-refresh follows the same lightweight policy as WebSocket updates
3. Make the auto-refresh/polling interaction explicit (prevent competing invalidation)
4. Verify manual refresh still bypasses all caches and triggers full board reload
5. Measure improvement against Phase 1B baseline

**Key files**:

- `frontend/src/hooks/useRealTimeSync.ts` — polling fallback invalidation scope
- `frontend/src/hooks/useBoardRefresh.ts` — auto-refresh policy
- `frontend/src/hooks/useProjectBoard.ts` — query configuration

**Verification**: SC-003 (task updates < 2s without full reload), SC-004 (zero full board refreshes from idle polling).

---

### Phase 3A — Frontend Render Optimization

**Goal**: Reduce unnecessary rerenders and derived-state recomputation.

**Depends on**: Phase 2B (refresh-path fixes)

**Steps**:

1. Memoize `pipelineGridStyle` in ProjectsPage with `useMemo`
2. Stabilize event listener registrations with `useCallback` in ProjectsPage
3. Review inline object creation in `useEffect` dependency arrays
4. Verify BoardColumn and IssueCard memo boundaries are effective under profiling
5. Measure improvement against Phase 1B baseline

**Key files**:

- `frontend/src/pages/ProjectsPage.tsx` — derived state and listener optimization
- `frontend/src/components/board/BoardColumn.tsx` — memo verification
- `frontend/src/components/board/IssueCard.tsx` — memo verification

**Verification**: SC-005 (responsive with 100+ cards), SC-006 (drag rerenders source + destination only).

---

### Phase 3B — Verification and Regression Coverage

**Goal**: Extend test coverage and validate all improvements.

**Depends on**: Phase 2A, Phase 2B, Phase 3A

**Steps**:

1. Extend `test_cache.py` with warm vs. cold sub-issue cache comparison tests
2. Extend `test_api_board.py` with idle-board zero-redundant-refresh assertions
3. Extend `test_copilot_polling.py` with polling-does-not-trigger-full-refresh tests
4. Extend `useRealTimeSync.test.tsx` with polling-fallback-task-only-invalidation tests
5. Extend `useBoardRefresh.test.tsx` with auto-refresh-uses-task-only-scope tests
6. Run full backend test suite: `uv run --extra dev pytest tests/unit/ -x`
7. Run full frontend test suite: `npm run test`
8. Perform manual network/profile verification pass

**Key files**:

- All test files listed above
- `backend/pyproject.toml` — test configuration
- `frontend/package.json` — test configuration

**Verification**: SC-007 (all tests pass), SC-008 (manual verification matches automated), SC-009 (no behavior regressions).

---

### Phase 4 — Optional Second-Wave (Deferred)

**Goal**: Structural improvements if first-pass measurements fail targets.

**Only proceed if**: Phase 3B measurements show material gaps against success criteria.

**Potential items** (not implemented in first pass):

- Board virtualization for large boards (react-window or react-virtuoso)
- Service decomposition of GitHub project fetching/polling pipeline
- ETag-based conditional requests to GitHub REST API
- Bounded cache policies beyond TTL-based approach
- Request budget instrumentation and render timing dashboards

## Build and Test Commands

### Backend

```bash
cd backend
uv run --extra dev ruff check src/          # Lint
uv run --extra dev pyright                   # Type check
uv run --extra dev pytest tests/unit/ -x     # Unit tests (full suite)
```

#### Performance-targeted backend tests

```bash
# Cache behavior regression
uv run --extra dev pytest tests/unit/test_cache.py -x -v

# Board endpoint cache and refresh behavior
uv run --extra dev pytest tests/unit/test_api_board.py -x -v

# Polling rate-limit and idle behavior
uv run --extra dev pytest tests/unit/test_copilot_polling.py -x -v
```

### Frontend

```bash
cd frontend
npm run lint                                  # ESLint
npm run type-check                            # TypeScript check
npm run test                                  # Vitest (full suite)
npm run build                                 # Production build
```

#### Performance-targeted frontend tests

```bash
# Real-time sync and polling fallback invalidation scope
npx vitest run src/hooks/useRealTimeSync.test.tsx --reporter=verbose

# Board refresh policy (auto-refresh vs manual)
npx vitest run src/hooks/useBoardRefresh.test.tsx --reporter=verbose

# Query-key helper contracts
npx vitest run src/hooks/useProjectBoard.test.tsx --reporter=verbose

# Board component memo boundary verification
npx vitest run src/components/board/BoardColumn.test.tsx src/components/board/IssueCard.test.tsx --reporter=verbose
```

### Documentation

```bash
npx -y markdownlint-cli@0.48.0 specs/034-performance-review/*.md --config .markdownlint.json
```

## Measurement Workflow

### Representative Board Assumptions

- **Board size**: 50–100 tasks across 4–6 columns
- **Idle observation window**: 5 minutes with no user interaction
- **WebSocket status**: Connected (primary) or polling fallback (secondary)
- **Cache state**: Warm (entries populated from previous load)

### Backend Baseline Measurement Steps

1. Open a board with a representative project (50–100 tasks)
2. Monitor network activity for outbound GitHub API calls over 5 minutes idle
3. Record: idle API call count, board endpoint response time (warm vs cold cache)
4. Record: WebSocket message count during idle period
5. Record: polling cycle API call count (if fallback polling active)

### Frontend Baseline Measurement Steps

1. Open React DevTools Profiler
2. Load the project board and record initial render counts per component
3. Perform a card drag and record rerender scope (which columns/cards rerender)
4. Open a popover and record event listener fire rate
5. Inspect Network tab for: WebSocket messages, polling requests, board query invalidations

### Backend Regression Suite Commands

```bash
cd backend
uv run --extra dev pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -x -v
```

Expected: All tests pass, including new warm-vs-cold cache tests and board cache performance tests.

### Frontend Regression Suite Commands

```bash
cd frontend
npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx src/hooks/useProjectBoard.test.tsx src/components/board/BoardColumn.test.tsx src/components/board/IssueCard.test.tsx --reporter=verbose
```

Expected: All tests pass, including new polling fallback scope tests, auto-refresh scope tests, query-key contract tests, and memo boundary tests.
