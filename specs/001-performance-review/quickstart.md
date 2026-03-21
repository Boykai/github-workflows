# Quickstart: Performance Review

**Feature Branch**: `001-performance-review`  
**Date**: 2026-03-21

## Prerequisites

- Python ≥ 3.12 (backend targets 3.13 in tooling)
- Node.js ≥ 18 (frontend)
- Git
- Access to the repository at `solune/`

## Setup

### Backend

```bash
cd solune/backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd solune/frontend
npm ci
```

## Running Tests (Baseline Verification)

### Backend — Targeted Test Suites

```bash
cd solune/backend

# Cache behavior tests
python -m pytest tests/unit/test_cache.py -x -q --timeout=30

# Board endpoint tests
python -m pytest tests/unit/test_api_board.py -x -q --timeout=30

# Polling behavior tests
python -m pytest tests/unit/test_copilot_polling.py -x -q --timeout=30

# Full unit suite
python -m pytest tests/unit/ -x -q --timeout=30
```

### Backend — Linting and Type Checking

```bash
cd solune/backend

# Ruff linter
ruff check src/

# Pyright type checker
python -m pyright src/
```

### Frontend — Targeted Test Suites

```bash
cd solune/frontend

# Real-time sync hook tests
npx vitest run src/hooks/useRealTimeSync.test.tsx

# Board refresh hook tests
npx vitest run src/hooks/useBoardRefresh.test.tsx

# Full test suite
npx vitest run
```

### Frontend — Linting, Type Checking, and Build

```bash
cd solune/frontend

# ESLint
npx eslint .

# TypeScript type checking
npx tsc --noEmit

# Production build
npx vite build
```

## Key Files to Modify

### Backend (Performance Optimization)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `solune/backend/src/api/projects.py` | WebSocket subscription + change detection | `send_tasks()`, WebSocket endpoint |
| `solune/backend/src/api/board.py` | Board cache, manual refresh, sub-issue invalidation | `get_board_data()` endpoint |
| `solune/backend/src/services/copilot_polling/polling_loop.py` | Polling hot path + rate-limit gating | `_poll_loop()`, `_pause_if_rate_limited()` |
| `solune/backend/src/services/cache.py` | Cache service, TTLs, hash computation | `InMemoryCache`, `compute_data_hash()` |

### Frontend (Performance Optimization)

| File | Purpose | Key Hooks/Components |
|------|---------|---------------------|
| `solune/frontend/src/hooks/useRealTimeSync.ts` | WebSocket + fallback polling | `useRealTimeSync()` |
| `solune/frontend/src/hooks/useBoardRefresh.ts` | Auto-refresh + manual refresh | `useBoardRefresh()` |
| `solune/frontend/src/hooks/useProjectBoard.ts` | Board query ownership | `useProjectBoard()` |
| `solune/frontend/src/components/board/BoardColumn.tsx` | Column rendering | `BoardColumn` (memo'd) |
| `solune/frontend/src/components/board/IssueCard.tsx` | Card rendering | `IssueCard` (memo'd) |
| `solune/frontend/src/pages/ProjectsPage.tsx` | Page-level derived state | `ProjectsPage` |
| `solune/frontend/src/components/chat/ChatPopup.tsx` | Drag resize handlers | `ChatPopup` |

### Test Files to Extend

| File | Coverage Area |
|------|---------------|
| `solune/backend/tests/unit/test_cache.py` | Cache TTL, hash-based change detection |
| `solune/backend/tests/unit/test_api_board.py` | Board cache bypass, sub-issue invalidation |
| `solune/backend/tests/unit/test_copilot_polling.py` | Polling rate-limit behavior |
| `solune/frontend/src/hooks/useRealTimeSync.test.tsx` | WebSocket fallback, query invalidation scope |
| `solune/frontend/src/hooks/useBoardRefresh.test.tsx` | Timer suppression, manual priority |

## Verification Workflow

### Phase 1: Capture Baselines (Before Code Changes)

1. **Backend idle API count**: Open a board, run for 10 minutes, count outbound GitHub requests.
2. **Frontend render profile**: Load a board with 50+ cards, profile initial render time and re-render counts.
3. **Network activity**: Inspect WebSocket messages, fallback polling frequency, and board query invalidation triggers.

### Phase 2: Apply Optimizations

1. Backend: Verify and extend change-detection-based refresh suppression.
2. Frontend: Verify refresh path decoupling, add event listener throttling.
3. Both: Add regression tests for changed behaviors.

### Phase 3: Validate Against Baselines

1. Re-run backend idle API count → confirm ≥ 50% reduction (SC-001).
2. Re-run frontend render profile → confirm no regression, ideally ≥ 20% improvement (SC-002).
3. Run all tests → confirm no regressions (SC-006).
4. Manual end-to-end check → confirm responsive interactions (SC-008).
