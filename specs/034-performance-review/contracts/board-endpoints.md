# Contract: Board Endpoint Performance

**Feature**: 034-performance-review
**Date**: 2026-03-11
**Traces to**: FR-001, FR-002, FR-004, FR-006, FR-010, FR-011, FR-012, SC-001, SC-005, SC-006

## Backend Board Endpoint Contract

### GET /api/board/{project_id}

**Cache behavior**:

- Default (no query params): Serve from cache if fresh (TTL 300s); fetch from GitHub API if expired.
- `refresh=true`: Clear board data cache + all sub-issue caches; fetch from GitHub API; cache results.

**Response contract**:

```text
200 OK
{
  "columns": [...],
  "metadata": {...},
  "cached": true|false,        // Whether response was served from cache
  "stale": true|false           // Whether response was served from stale fallback
}
```

**Rate-limit handling**:

- If GitHub API returns rate-limit error: serve stale cached data if available; return 503 if no stale data.
- Rate-limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`) are extracted and stored for polling loop decisions.

### Performance Targets

| Metric | Baseline (pre-optimization) | Target (post-optimization) | Measurement Method |
|--------|----------------------------|---------------------------|-------------------|
| Idle API calls (5 min) | TBD (measure) | ≥ 50% reduction (SC-001) | Count outbound GitHub API calls during idle board viewing |
| Warm-cache refresh API calls | TBD (measure) | ≥ 30% fewer than cold cache (SC-002) | Compare API call count with/without warm sub-issue caches |
| Board endpoint response time | TBD (measure) | No regression | Measure endpoint response time under warm and cold cache |

## WebSocket Subscription Contract

### SSE/WebSocket /api/projects/{project_id}/subscribe

**Change detection**:

- Server computes SHA256 hash of task payload on each 30s refresh cycle.
- If hash matches previous: no message sent (idle-safe).
- If hash differs: `task_update` or `refresh` message sent to connected clients.

**Idle behavior invariant** (SC-001):

- With no upstream data changes, the subscription MUST NOT send any messages to the client.
- The server-side refresh cycle (30s) MUST check the cache first and only call GitHub API if the cache is expired.
- Zero-change cycles MUST NOT increment the outbound API call counter.

## Frontend Rendering Contract

### Board Component Rerender Policy

| Component | Memo | Rerender Trigger | NOT a Rerender Trigger |
|-----------|------|------------------|----------------------|
| BoardColumn | `React.memo()` | Own column data changes | Sibling column changes, parent rerender |
| IssueCard | `React.memo()` | Own card data changes | Sibling card changes, parent rerender |
| ProjectsPage | N/A (root) | Any state change | N/A |

### Derived State Contract (FR-011)

| Derived Value | Computation | Memoization | Invalidation |
|---------------|-------------|-------------|--------------|
| transformedBoardData | Sort/filter board data | `useMemo` | Board data reference changes |
| assignedPipeline | Pipeline lookup | `useMemo` | Pipeline data reference changes |
| assignedStageMap | Stage aggregation | `useMemo` | Pipeline data reference changes |
| pipelineGridStyle | CSS grid computation | **NEEDS `useMemo`** | Grid config reference changes |

### Event Listener Contract (FR-012)

| Listener | Component | Current State | Target State |
|----------|-----------|---------------|-------------|
| mousemove/mouseup (resize) | ChatPopup | ✅ rAF-gated, active-only | No change needed |
| Modal toggle listeners | ProjectsPage | ⚠️ Re-registered on toggle | Stabilize with useCallback |
| Drag handlers | Board (dnd-kit) | Library-managed | Monitor, no change unless profiling shows issues |

### Measurement Contract (SC-005, SC-006)

| Metric | Target | Method |
|--------|--------|--------|
| Card drag rerender scope | Source + destination columns only (SC-006) | React DevTools Profiler |
| Board interaction responsiveness | No perceptible lag, 100+ cards (SC-005) | Manual profiling |
| Derived state recomputation | Zero recomputation when data unchanged (FR-011) | React DevTools render count |
| Event listener fire rate | ≤ 1 per rAF for mouse handlers (FR-012) | Performance timeline |

## Regression Test Coverage Contract (FR-013)

### Backend Tests to Extend

| Test File | Coverage Target | New/Extended |
|-----------|----------------|-------------|
| test_cache.py | Warm vs. cold sub-issue cache hit measurement | Extended |
| test_api_board.py | Idle board produces zero redundant API calls | Extended |
| test_copilot_polling.py | Polling does not trigger full board refresh | Extended |

### Frontend Tests to Extend

| Test File | Coverage Target | New/Extended |
|-----------|----------------|-------------|
| useRealTimeSync.test.tsx | Polling fallback invalidates only task queries | Extended |
| useBoardRefresh.test.tsx | Auto-refresh uses task-only scope, not full board | Extended |
