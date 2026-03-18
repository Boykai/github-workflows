# Quickstart: Performance Review

**Feature**: `051-performance-review`
**Date**: 2026-03-18

---

## Prerequisites

- Python 3.12+ with pip
- Node.js 22+ with npm
- Git
- Chrome/Chromium (for frontend profiling)

## Quick Verification Commands

### Backend — Run Targeted Tests

```bash
cd solune/backend
pip install -e ".[dev]"

# Cache behavior tests
pytest tests/unit/test_cache.py -v

# Board endpoint tests
pytest tests/unit/test_api_board.py -v

# Polling behavior tests
pytest tests/unit/test_copilot_polling.py -v

# All three together
pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v
```

### Backend — Lint and Type Check

```bash
cd solune/backend

# Linting
ruff check src/

# Type checking
pyright src/
```

### Frontend — Run Targeted Tests

```bash
cd solune/frontend
npm ci

# Real-time sync hook tests
npx vitest run src/hooks/useRealTimeSync.test.tsx

# Board refresh hook tests
npx vitest run src/hooks/useBoardRefresh.test.tsx

# Both together
npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx
```

### Frontend — Lint and Type Check

```bash
cd solune/frontend

# Linting
npx eslint src/

# Type checking
npx tsc --noEmit

# Build check
npm run build
```

### Frontend — Full Test Suite

```bash
cd solune/frontend
npm run test
```

## Baseline Capture Procedure

### Step 1: Backend Idle API Monitoring

```bash
cd solune/backend

# Start the backend with debug logging
LOG_LEVEL=DEBUG uvicorn src.main:app --host 0.0.0.0 --port 8000

# In another terminal, observe GitHub API calls in logs:
# Look for lines containing "api.github.com" or "GraphQL" or "REST"
# Count calls over a 5-minute idle period with a board open
```

### Step 2: Frontend Performance Profiling

1. Start the frontend dev server:
   ```bash
   cd solune/frontend
   npm run dev
   ```

2. Open Chrome DevTools → Performance tab
3. Navigate to a project board
4. Record a 10-second trace during:
   - Initial board load
   - Card drag interaction
   - Popover open/close
5. Note FPS, render cycle count, and network requests

### Step 3: Network Activity Inspection

1. Open Chrome DevTools → Network tab
2. Filter by Fetch/XHR
3. Navigate to a board and wait for it to stabilize
4. Leave the board idle for 5 minutes
5. Count the number of network requests during the idle period
6. Note which endpoints are called and how frequently

## Key Files to Monitor

### Backend (optimization targets)

| File | What to Watch |
|------|--------------|
| `solune/backend/src/api/projects.py` | WebSocket handler — 30s check cycle, hash comparison |
| `solune/backend/src/api/board.py` | Board data endpoint — cache TTL, sub-issue cache clearing |
| `solune/backend/src/services/cache.py` | Cache hits/misses — log output at DEBUG level |
| `solune/backend/src/services/copilot_polling/polling_loop.py` | Poll interval, idle backoff, rate-limit pauses |
| `solune/backend/src/services/github_projects/service.py` | Cycle cache, request coalescing, sub-issue fetches |
| `solune/backend/src/utils.py` | Repository resolution cache hits |
| `solune/backend/src/api/workflow.py` | Duplicate repo resolution (consolidation target) |

### Frontend (optimization targets)

| File | What to Watch |
|------|--------------|
| `solune/frontend/src/hooks/useRealTimeSync.ts` | Query invalidation scope — should not invalidate board data on task updates |
| `solune/frontend/src/hooks/useBoardRefresh.ts` | Debounce behavior, auto-refresh timer, manual refresh cache bypass |
| `solune/frontend/src/hooks/useProjectBoard.ts` | Query staleness config, refetch strategy |
| `solune/frontend/src/components/board/BoardColumn.tsx` | Memoization — should use React.memo |
| `solune/frontend/src/components/board/IssueCard.tsx` | Memoization — should use React.memo |
| `solune/frontend/src/pages/ProjectsPage.tsx` | Derived data — should use useMemo for sort/filter |
| `solune/frontend/src/components/chat/ChatPopup.tsx` | Resize handler — should use rAF throttling |

## Verification After Optimization

### Automated Checks

```bash
# Backend
cd solune/backend
ruff check src/
pyright src/
pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v

# Frontend
cd solune/frontend
npx eslint src/
npx tsc --noEmit
npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx
npm run build
```

### Manual End-to-End Check

1. Open a board with a WebSocket connection
2. Have a second session change a task status → verify the first session updates within 3 seconds without full board re-render
3. Disconnect WebSocket (disable network briefly) → verify fallback polling activates safely
4. Leave board idle for 5 minutes → verify ≤2 external API calls/minute
5. Click manual refresh → verify all data is fresh (sub-issue caches cleared)
6. Drag a card between columns → verify smooth animation (≥30 FPS)
