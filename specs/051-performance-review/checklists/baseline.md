# Baseline Metrics Checklist: Performance Review

**Purpose**: Track pre-optimization and post-optimization performance baselines
**Created**: 2026-03-18
**Feature**: [spec.md](../spec.md)
**Metrics**: [baseline-metrics.md](../contracts/baseline-metrics.md)

## Pre-Optimization Baselines

> **NOTE**: These metrics require a running instance with representative data.
> They are captured manually via DevTools, backend logs, and profiling tools.

| # | Metric | Tool | Target | Pre-Optimization | Post-Optimization | Status |
|---|--------|------|--------|-------------------|-------------------|--------|
| BM-1 | Idle API Call Rate (calls/min) | Backend logs | ≤2/min | _Requires live instance_ | _TBD_ | ⏳ |
| BM-2 | Board Endpoint Cost — cold (calls) | Backend logs | Record | _Requires live instance_ | _TBD_ | ⏳ |
| BM-2 | Board Endpoint Cost — warm (calls) | Backend logs | 40% fewer sub-issue fetches | _Requires live instance_ | _TBD_ | ⏳ |
| BM-3 | Polling Cycle Cost (calls/cycle) | Backend logs | ≤1 call/cycle | _Requires live instance_ | _TBD_ | ⏳ |
| FM-1 | Board TTI — warm cache (ms) | Performance API | 30% faster | _Requires live instance_ | _TBD_ | ⏳ |
| FM-2 | Render Cycle Count | React Profiler | Reduction | _Requires live instance_ | _TBD_ | ⏳ |
| FM-3 | Drag FPS | DevTools Performance | ≥30 FPS | _Requires live instance_ | _TBD_ | ⏳ |
| FM-3 | Popover FPS | DevTools Performance | ≥30 FPS | _Requires live instance_ | _TBD_ | ⏳ |
| FM-3 | Scroll FPS | DevTools Performance | ≥30 FPS | _Requires live instance_ | _TBD_ | ⏳ |
| FM-4 | Network Request Count | DevTools Network | Reduction | _Requires live instance_ | _TBD_ | ⏳ |
| FM-5 | Real-Time Update Latency (s) | Manual timing | ≤3 seconds | _Requires live instance_ | _TBD_ | ⏳ |

## Implementation State Review (Spec 022 Cross-Reference)

### Backend — Already Implemented ✅

| Feature | Status | Evidence |
|---------|--------|----------|
| WebSocket hash-based change detection | ✅ Implemented | `projects.py:444-462` — `compute_data_hash()` comparison before sending refresh |
| Board cache 300s TTL | ✅ Implemented | `board.py:431` — `cache.set()` uses default 300s TTL from config |
| Sub-issue cache invalidation on manual refresh | ✅ Implemented | `board.py:376-385` — iterates board items, deletes sub-issue cache keys |
| Sub-issue cache preservation on auto refresh | ✅ Implemented | `board.py` non-refresh path skips cache.delete calls |
| Board data hash excludes rate_limit | ✅ Implemented | `board.py:429-431` — `exclude={"rate_limit"}` in model_dump |
| Stale data fallback on fetch failure | ✅ Implemented | `projects.py:393-400` — WebSocket falls back to stale cache on error |
| Stale revalidation counter (10 cycles) | ✅ Implemented | `projects.py:348-385` — counter with configurable limit |
| Rate-limit aware polling with adaptive backoff | ✅ Implemented | `polling_loop.py:438-484` — dynamic interval scaling |
| Shared resolve_repository in utils.py | ✅ Implemented | `utils.py:167-230` — 3-step fallback with caching |
| workflow.py uses shared resolve_repository | ✅ Implemented | `workflow.py:42` — imports from `src.utils` |

### Backend — New Optimizations (This PR) 🆕

| Feature | Status | Evidence |
|---------|--------|----------|
| Stale-revalidation hash comparison (T016) | ✅ Implemented | `projects.py:390-408` — `compute_data_hash` + `refresh_ttl` on match |
| SSE stale fallback on fetch failure (T046) | ✅ Implemented | `projects.py:538-543` — serves stale data instead of error event |

### Frontend — Already Implemented ✅

| Feature | Status | Evidence |
|---------|--------|----------|
| WebSocket invalidates only tasks query | ✅ Implemented | `useRealTimeSync.ts:65,75,87` — all handlers target tasks key |
| Board data managed by useBoardRefresh | ✅ Implemented | `useBoardRefresh.ts` — auto-refresh timer + manual refresh |
| No refetchInterval on board query | ✅ Implemented | `useProjectBoard.ts:66-68` — explicit comment + no refetchInterval |
| BoardColumn React.memo | ✅ Implemented | `BoardColumn.tsx:19` — `memo()` wrapper |
| IssueCard React.memo | ✅ Implemented | `IssueCard.tsx:109` — `memo()` wrapper |
| SubIssueRow React.memo | ✅ Implemented | `IssueCard.tsx:57` — `memo()` wrapper |
| ChatPopup RAF gating | ✅ Implemented | `ChatPopup.tsx:98-113` — requestAnimationFrame for drag resize |
| Page Visibility API pause/resume | ✅ Implemented | `useBoardRefresh.ts:178-200` — timer pauses on hidden |
| Debounce deduplication (2s window) | ✅ Implemented | `useBoardRefresh.ts:158-176` — `requestBoardReload()` |
| useMemo for derived data | ✅ Implemented | `ProjectsPage.tsx:116-146` — heroStats, assignedPipeline, etc. |
| useCallback for event handlers | ✅ Implemented | `ProjectsPage.tsx:113-114,198-204` — handleCardClick, etc. |

### Frontend — New Optimizations (This PR) 🆕

| Feature | Status | Evidence |
|---------|--------|----------|
| Fallback polling change detection (T044) | ✅ Implemented | `useRealTimeSync.ts:111-126` — ref comparison before invalidation |
| Polling skips unchanged data (T045) | ✅ Implemented | `useRealTimeSync.ts:116-119` — reference equality check |

## Notes

- Backend baseline metrics (BM-1 through BM-3) require a running backend instance with an active GitHub project. These cannot be automated in a CI environment.
- Frontend baseline metrics (FM-1 through FM-5) require a browser with DevTools or React Profiler. These are captured during manual testing.
- All automated verification (tests, linting, type checking) has been completed and passes.
- The majority of Spec 022 features were already implemented. This PR adds targeted improvements to stale-revalidation (backend) and polling change detection (frontend).
