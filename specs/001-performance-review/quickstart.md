# Quickstart: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-11

## Prerequisites

- Python 3.12+ with `uv` package manager
- Node.js 18+ with npm
- Git
- A GitHub token configured for the project (for live API testing)

## Repository Setup

```bash
# Clone and enter the repository
cd /path/to/github-workflows

# Backend setup
cd backend
uv sync --extra dev

# Frontend setup
cd ../frontend
npm install
```

## Running Existing Tests (Baseline Guardrails)

These commands verify that the current regression suite passes before any optimization work begins.

### Backend Tests

```bash
cd backend

# Run targeted unit tests that serve as regression guardrails
uv run --extra dev pytest tests/unit/test_cache.py -x -v
uv run --extra dev pytest tests/unit/test_api_board.py -x -v
uv run --extra dev pytest tests/unit/test_copilot_polling.py -x -v

# Run linting and type checking
uv run --extra dev ruff check src/
uv run --extra dev pyright src/
```

### Frontend Tests

```bash
cd frontend

# Run targeted hook tests that serve as regression guardrails
npx vitest run src/hooks/useRealTimeSync.test.tsx
npx vitest run src/hooks/useBoardRefresh.test.tsx

# Run linting and type checking
npm run lint
npm run type-check

# Run full test suite
npm run test

# Build check
npm run build
```

## Key Files to Understand

Before starting implementation, read these files in order:

### Backend (cache and refresh mechanics)

1. `backend/src/services/cache.py` — In-memory TTL cache with stale fallback. Understand `get()`, `set()`, `get_stale()`, and TTL configuration.
2. `backend/src/api/board.py` — Board endpoint: cache usage, manual refresh (`refresh=true`), sub-issue cache clearing.
3. `backend/src/api/projects.py` — WebSocket subscription endpoint, message types, task/board event broadcasting.
4. `backend/src/services/copilot_polling/polling_loop.py` — Polling hot path. Understand what triggers and what it costs.
5. `backend/src/utils.py` — Canonical shared helpers: `cached_fetch()` and repository resolution.

### Frontend (refresh and render paths)

1. `frontend/src/hooks/useRealTimeSync.ts` — WebSocket connection, fallback polling, message handling, query invalidation.
2. `frontend/src/hooks/useBoardRefresh.ts` — Auto-refresh timer (5 min), manual refresh, page visibility gating.
3. `frontend/src/hooks/useProjectBoard.ts` — Board query ownership, stale times, refetch configuration.
4. `frontend/src/pages/ProjectsPage.tsx` — Derived state computation (`useMemo` patterns), rate-limit context publishing.
5. `frontend/src/components/board/BoardColumn.tsx` — Memoized column component.
6. `frontend/src/components/board/IssueCard.tsx` — Memoized card component.
7. `frontend/src/components/chat/ChatPopup.tsx` — Drag listener (throttle candidate).
8. `frontend/src/components/agents/AddAgentPopover.tsx` — Positioning listener (throttle candidate).

## Development Workflow

### Phase 1: Baseline Capture

1. Run all guardrail tests (commands above) and record pass/fail counts.
2. Start the dev server and open a representative board.
3. Use browser DevTools Network tab to observe API calls during 10-minute idle observation.
4. Use React DevTools Profiler to capture render hot spots during board interactions.
5. Document results in a baseline capture record.

### Phase 2: Backend Changes

1. Add `data_hash` computation to board cache entries in `cache.py`.
2. Update WebSocket subscription in `projects.py` to compare `data_hash` before broadcasting `refresh`.
3. Verify with `test_cache.py` and `test_api_board.py`.

### Phase 2: Frontend Refresh Contract

1. Update `useRealTimeSync.ts` to handle `refresh` messages according to the refresh contract.
2. Add debounce logic for board reloads in `useBoardRefresh.ts`.
3. Verify with `useRealTimeSync.test.tsx` and `useBoardRefresh.test.tsx`.

### Phase 3: Frontend Render Optimization

1. Stabilize callback props with `useCallback` in parent components passing callbacks to memoized children.
2. Throttle drag listeners in `ChatPopup.tsx`.
3. Throttle positioning listeners in `AddAgentPopover.tsx`.
4. Profile before/after to confirm improvements.

### Phase 3: Verification

1. Re-run all guardrail tests — 0 new failures.
2. Repeat the baseline observation — compare against Phase 1 baseline.
3. Document results.

## Refresh Contract Reference

See [contracts/refresh-contract.md](./contracts/refresh-contract.md) for the full refresh policy governing all update paths.

## Relevant Spec References

- [spec.md](./spec.md) — Feature specification with user stories and acceptance criteria
- [research.md](./research.md) — Research findings and technology decisions
- [data-model.md](./data-model.md) — Entity definitions and relationships
