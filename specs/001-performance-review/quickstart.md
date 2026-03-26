# Quickstart: Performance Review

**Feature**: 001-performance-review  
**Date**: 2026-03-26

## Prerequisites

- Python ≥3.12 with pip
- Node.js (for frontend)
- Git

## Repository Structure

```
solune/
├── backend/          # FastAPI backend (Python)
│   ├── src/          # Source code
│   └── tests/        # pytest test suite
└── frontend/         # React 19 frontend (TypeScript)
    ├── src/          # Source code
    └── ...
```

## Backend Setup

```bash
cd solune/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run Backend Tests (targeted)

```bash
# Cache behavior tests
pytest tests/unit/test_cache.py -v --timeout=30

# Board endpoint tests
pytest tests/unit/test_api_board.py -v --timeout=30

# Polling behavior tests
pytest tests/unit/test_copilot_polling.py -v --timeout=30

# All targeted tests together
pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --timeout=30
```

### Run Backend Lint/Type Checks

```bash
ruff check src tests
ruff format --check src tests
pyright src
```

### Full Backend CI Validation

```bash
pip-audit . --skip-editable --ignore-vuln CVE-2026-4539
ruff check src tests
ruff format --check src tests
bandit -r src/ -ll -ii --skip B104,B608
pyright src
pytest --cov=src --cov-report=term-missing --ignore=tests/property --ignore=tests/fuzz --ignore=tests/chaos --ignore=tests/concurrency
```

## Frontend Setup

```bash
cd solune/frontend
npm install
```

### Run Frontend Tests (targeted)

```bash
# Real-time sync hook tests
npx vitest run src/hooks/useRealTimeSync.test.tsx

# Board refresh hook tests
npx vitest run src/hooks/useBoardRefresh.test.tsx

# All hook tests
npx vitest run src/hooks/
```

### Run Frontend Lint/Type Checks

```bash
npm run lint
npm run type-check
```

### Full Frontend CI Validation

```bash
npm audit --audit-level=high
npm run lint
npm run type-check
npm run test
npm run build
```

## Key Files for This Feature

### Backend — Cache & API

| File | Purpose | What to Look For |
|------|---------|-----------------|
| `src/services/cache.py` | InMemoryCache, CacheEntry, `cached_fetch()` | TTL values, hash comparison logic, stale fallback |
| `src/api/board.py` | Board data endpoints, cache invalidation | `refresh=true` handling, cache key deletion |
| `src/api/projects.py` | WebSocket subscription, change detection | Hash comparison, `refresh` message suppression |
| `src/services/copilot_polling/polling_loop.py` | Polling loop, rate-limit thresholds | Step skipping, board cache interaction |
| `src/services/github_projects/service.py` | Board/project fetching | Sub-issue fetching, caching patterns |
| `src/utils.py` | `resolve_repository()`, BoundedDict/Set | Token-scoped cache, fallback chain |

### Frontend — Hooks & Components

| File | Purpose | What to Look For |
|------|---------|-----------------|
| `src/hooks/useRealTimeSync.ts` | WebSocket + polling fallback | Query invalidation keys, fallback behavior |
| `src/hooks/useBoardRefresh.ts` | Auto-refresh timer, manual refresh | WebSocket suppression, debounce window |
| `src/hooks/useProjectBoard.ts` | Board data query, adaptive polling | `staleTime`, `refetchInterval`, change detection |
| `src/components/board/BoardColumn.tsx` | Column rendering | Memoization, drag-drop |
| `src/components/board/IssueCard.tsx` | Card rendering | Rerender frequency, prop stability |
| `src/pages/ProjectsPage.tsx` | Board page orchestrator | Derived data computation, sorting/grouping |
| `src/components/chat/ChatPopup.tsx` | Chat drag/resize | Event listener frequency |
| `src/components/board/AddAgentPopover.tsx` | Agent popover | Confirm positioning remains Radix-managed and no custom listeners were added |

### Test Files

| File | Covers |
|------|--------|
| `tests/unit/test_cache.py` | CacheEntry lifecycle, TTL, hash comparison, `cached_fetch()` |
| `tests/unit/test_api_board.py` | Board endpoints, cache invalidation, error handling |
| `tests/unit/test_copilot_polling.py` | Polling steps, rate-limit handling |
| `src/hooks/useRealTimeSync.test.tsx` | WebSocket lifecycle, message handling, query invalidation |
| `src/hooks/useBoardRefresh.test.tsx` | Refresh timer, debounce, visibility API, manual refresh |

## Measurement Approach

### Backend Baseline

1. Start the backend server locally
2. Open a board and leave it idle for 5 minutes
3. Count outbound GitHub API calls (use logging or network proxy)
4. Record: idle call count, warm-cache request cost (expect 0 API calls), WebSocket idle refresh count

### Frontend Baseline

1. Open React DevTools Profiler
2. Load a representative board (5+ columns, 20+ cards)
3. Record: initial render time, component mount count
4. Trigger a single card status change via WebSocket
5. Record: rerender count, network requests triggered
6. Perform drag interaction
7. Record: event listener fire rate

### Post-Optimization Comparison

Compare all metrics against baseline. Success criteria:
- SC-001: ≥50% fewer idle API calls
- SC-002: Zero API calls on warm-cache board request
- SC-003: Single-task update → no full board reload
- SC-004: Measurable rerender reduction during interactions
