# Quickstart: Add Manual Refresh Button & Auto-Refresh to Project Board with GitHub API Rate Limit Optimization

**Feature**: 014-board-refresh-ratelimit | **Date**: 2026-02-28

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm (ships with Node.js)

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd frontend
npm ci
```

## Running the Application

### Backend Server

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### Frontend Dev Server

```bash
cd frontend
npm run dev
```

The project board is accessible at `http://localhost:5173` (or the port shown by Vite).

## Running Tests

### Backend Tests

```bash
# Run all backend tests
cd backend
pytest

# Run board-specific tests
pytest tests/unit/test_api_board.py

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

### Frontend Unit Tests

```bash
# Run all frontend unit tests
cd frontend
npm test

# Run board-related hook tests
npx vitest run src/hooks/useProjectBoard.test.ts
npx vitest run src/hooks/useRealTimeSync.test.tsx

# Run in watch mode
npm run test:watch
```

## Linting and Type Checking

### Backend

```bash
cd backend
ruff check src tests
ruff format --check src tests
```

### Frontend

```bash
cd frontend
npm run lint
npm run type-check
npm run build
```

## Key Files for This Feature

### Backend

| Path | Description |
|------|-------------|
| `backend/src/api/board.py` | Board API endpoints — add rate limit info to responses |
| `backend/src/services/cache.py` | In-memory cache — add ETag support |
| `backend/src/services/github_projects/service.py` | GitHub API client — extract rate limit headers |
| `backend/src/services/github_projects/graphql.py` | GraphQL queries (unchanged) |
| `backend/src/models/board.py` | Board models — add RateLimitInfo model |

### Frontend

| Path | Description |
|------|-------------|
| `frontend/src/hooks/useBoardRefresh.ts` | NEW: Refresh orchestration hook (timer, visibility, dedup) |
| `frontend/src/hooks/useProjectBoard.ts` | MODIFY: Integrate with useBoardRefresh |
| `frontend/src/hooks/useRealTimeSync.ts` | MODIFY: Coordinate with refresh timer |
| `frontend/src/components/board/RefreshButton.tsx` | NEW: Manual refresh button with tooltip |
| `frontend/src/pages/ProjectBoardPage.tsx` | MODIFY: Add RefreshButton, rate limit warning |
| `frontend/src/services/api.ts` | MODIFY: Parse rate limit info from responses |
| `frontend/src/constants.ts` | MODIFY: Add AUTO_REFRESH_INTERVAL_MS |
| `frontend/src/types/index.ts` | MODIFY: Add RateLimitInfo type |

## Feature Testing Workflow

### Manual Testing

1. **Manual Refresh Button**: Open the project board, click the refresh button, verify data reloads with a spinner animation.
2. **Tooltip**: Hover over the refresh button, verify tooltip "Auto-refreshes every 5 minutes" appears.
3. **Auto-Refresh**: Open the project board, wait 5+ minutes, verify data refreshes automatically.
4. **Tab Visibility**: Open the board, switch to another tab for 6+ minutes, switch back — verify immediate refresh occurs.
5. **Rapid Clicks**: Click the refresh button 5 times quickly — verify only 1 API call is made (check Network tab).
6. **Rate Limit Warning**: Simulate a 429 response — verify a yellow warning banner appears with reset time.

### Simulating Rate Limit Errors

To test rate limit handling without exhausting your actual limit:

```bash
# In backend, temporarily modify board.py to return a mock rate limit response
# Or use browser DevTools to intercept and modify the response
```

## Architecture Overview

```
User clicks refresh → useBoardRefresh.refresh()
                      ├── Guards against concurrent refresh (isRefreshing check)
                      ├── Invalidates TanStack Query cache
                      ├── Resets 5-minute auto-refresh timer
                      └── TanStack Query refetches board data
                          ├── Frontend: boardApi.getBoardData(id, refresh=true)
                          ├── Backend: board.py → github_projects_service.get_board_data()
                          ├── Backend: _graphql() → GitHub GraphQL API
                          ├── Backend: Extract rate limit headers from response
                          └── Backend: Return BoardDataResponse with rate_limit field

Auto-refresh timer (5 min) → same flow as manual refresh
Page Visibility API → pause timer when hidden, resume on visible
WebSocket message → TanStack Query invalidation (existing flow, resets timer)
```
