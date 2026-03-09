# Quickstart: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09
**Branch**: `032-performance-review`

## Quick Reference

This feature optimizes backend API consumption and frontend board responsiveness through a phased, measurement-driven approach. No new dependencies or architectural changes — only refinements to existing patterns.

## Implementation Phases

### Phase 1 — Baseline and Guardrails (blocks all other work)

**Goal**: Capture quantitative before-state for all performance metrics.

| Task | Files | What to Measure |
|------|-------|-----------------|
| Backend idle baseline | `backend/src/api/board.py`, `backend/src/api/projects.py` | API calls over 5-min idle window |
| Backend warm-cache baseline | `backend/src/services/github_projects/service.py` | API calls: cold-cache vs warm-cache board refresh |
| Spec 022 gap audit | `backend/src/api/projects.py` (WebSocket subscription) | Is server-side hash change detection implemented? |
| Frontend render baseline | `frontend/src/pages/ProjectsPage.tsx`, board components | Rerender count per task update, board load time |
| Frontend network baseline | `frontend/src/hooks/useRealTimeSync.ts` | Fallback polling invalidation scope |

**Verification**: Document baselines in a measurement log before proceeding to Phase 2.

### Phase 2 — Backend API Consumption + Frontend Refresh Path (parallel)

**Backend tasks**:

| Task | File | Change |
|------|------|--------|
| WebSocket change detection | `backend/src/api/projects.py` | Hash task data before sending; skip if unchanged |
| Fallback polling scope | `frontend/src/hooks/useRealTimeSync.ts` | Ensure polling only invalidates tasks query, not board data |

**Frontend tasks**:

| Task | File | Change |
|------|------|--------|
| Decouple task updates from board query | `frontend/src/hooks/useRealTimeSync.ts` | Verify WS messages only invalidate tasks query |
| Coherent refresh policy | `frontend/src/hooks/useBoardRefresh.ts` | Confirm manual refresh is only cache-bypass path |

**Verification**: Re-measure idle API calls and confirm <50% of baseline.

### Phase 3 — Frontend Render Optimization + Verification (parallel)

**Render optimization tasks**:

| Task | File | Change |
|------|------|--------|
| Stabilize callback props | `frontend/src/pages/ProjectsPage.tsx` | Wrap callbacks in `useCallback`, memoize `getGroups` |
| Throttle popover listeners | `frontend/src/components/agents/AddAgentPopover.tsx` | RAF-gate scroll/resize handlers |

**Verification tasks**:

| Task | File | Change |
|------|------|--------|
| Backend regression tests | `backend/tests/unit/test_cache.py`, `test_api_board.py` | Extend for warm-cache behavior |
| Frontend regression tests | `frontend/src/hooks/useRealTimeSync.test.tsx`, `useBoardRefresh.test.tsx` | Extend for polling scope, refresh isolation |
| Manual E2E verification | N/A | Network/profile pass on representative board |

## Key Files Quick Reference

### Backend

| File | Role |
|------|------|
| `backend/src/api/board.py` | Board data endpoint, 300s cache, manual refresh bypass |
| `backend/src/api/projects.py` | WebSocket subscription, task endpoints |
| `backend/src/services/cache.py` | InMemoryCache, TTL helpers, cache key functions |
| `backend/src/services/github_projects/service.py` | Board fetching, sub-issue caching (600s TTL) |
| `backend/src/services/copilot_polling/polling_loop.py` | Adaptive polling with rate-limit awareness |
| `backend/src/utils.py` | Shared `resolve_repository()` 3-step fallback |

### Frontend

| File | Role |
|------|------|
| `frontend/src/hooks/useRealTimeSync.ts` | WebSocket + polling fallback, message invalidation |
| `frontend/src/hooks/useBoardRefresh.ts` | Manual/auto refresh, deduplication, page visibility |
| `frontend/src/hooks/useProjectBoard.ts` | Board data query, project selection |
| `frontend/src/components/board/BoardColumn.tsx` | React.memo column rendering |
| `frontend/src/components/board/IssueCard.tsx` | React.memo card with sub-issues |
| `frontend/src/pages/ProjectsPage.tsx` | Board page, derived state, callback props |
| `frontend/src/components/agents/AddAgentPopover.tsx` | Portal positioning with scroll/resize listeners |

## Success Criteria Summary

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Idle API calls | ≤50% of baseline over 5 min | Count outgoing calls with idle board |
| Warm-cache refresh | ≤50% of cold-cache API calls | Compare sub-issue fetch counts |
| Interaction response | <100ms on 50+ card board | Profile board interactions |
| Single-update rerender | Only affected card + parent column | React Profiler flamegraph |
| Refresh deduplication | ≤1 board refresh per 1s window | Simulate concurrent triggers |
| Existing tests | All pass | `pytest` (backend), `vitest run` (frontend) |

## Commands

```bash
# Backend
cd backend
pip install -e ".[dev]"          # Install with dev dependencies
ruff check src/ tests/           # Lint
pyright src/                     # Type check
pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py  # Targeted tests

# Frontend
cd frontend
npm install                      # Install dependencies
npm run lint                     # ESLint
npm run type-check               # TypeScript check
npm test                         # Vitest (all tests)
npm run build                    # Production build check
```

## Decisions Log

See [research.md](research.md) for full decision rationale. Key decisions:

1. **No new dependencies** in first pass — use existing React.memo, useMemo, useCallback, RAF patterns
2. **No virtualization** unless baseline measurements show large boards still regress
3. **Server-side hash detection** is the highest-value backend change
4. **Fallback polling scope fix** is the highest-value frontend change
5. **Repository resolution** already consolidated — no changes needed
