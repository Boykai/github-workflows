# Data Model: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09
**Source**: [spec.md](spec.md) requirements + [research.md](research.md) findings

## Entity Overview

This feature does not introduce new persistent data entities. Instead, it refines the behavior of existing runtime entities (caches, refresh triggers, render state) to reduce waste and improve responsiveness. The data model below documents the entities relevant to optimization decisions.

## Entities

### 1. BoardData

**Description**: Full project board state — the expensive payload that drives all optimization decisions.

| Field | Type | Notes |
|-------|------|-------|
| project_id | string | Unique GitHub project node ID (e.g., `PVT_xxx`) |
| title | string | Project title |
| columns | Column[] | Status columns with ordered items |
| field_definitions | FieldDef[] | Status, Priority, Size, Estimate fields |
| item_count | int | Total items across all columns |

**Cache Behavior**:
- Backend cache key: project-specific
- Backend cache TTL: 300 seconds (aligned with frontend auto-refresh)
- Manual refresh (`refresh=true`): bypasses cache entirely
- Automatic refresh: serves from cache if TTL valid

**Relationships**: Contains → Column → BoardItem → SubIssue

---

### 2. SubIssueData

**Description**: Child issue details for board cards. Represents the largest volume of cacheable external API calls.

| Field | Type | Notes |
|-------|------|-------|
| cache_key | string | `sub_issues:{owner}/{repo}#{issue_number}` |
| issue_number | int | Parent issue number |
| owner | string | Repository owner |
| repo | string | Repository name |
| sub_issues | SubIssue[] | List of child issues with state, assignees, agent info |

**Cache Behavior**:
- Cache TTL: 600 seconds
- Cache hit: zero external API calls for this issue's sub-issues
- Cache miss: REST GET `/repos/{owner}/{repo}/issues/{issue_number}/sub_issues`
- Manual refresh: cache should be cleared for affected issues

**Validation Rules**:
- `per_page=50` limit on sub-issue fetch
- Empty list on API error (graceful degradation)

---

### 3. RefreshTrigger

**Description**: Any event that can initiate a board data update. Must be coordinated under a single policy.

| Trigger Type | Source | Invalidation Target | Cache Bypass |
|--------------|--------|---------------------|--------------|
| WebSocket message | Server push via `useRealTimeSync` | Tasks query only | No |
| Fallback polling | Interval timer in `useRealTimeSync` | Tasks query only | No |
| Auto-refresh | 5-min timer in `useBoardRefresh` | Board data query (via `invalidateQueries`) | No (uses backend cache) |
| Manual refresh | User action via `useBoardRefresh` | Board data + tasks queries | Yes (`refresh=true`) |

**State Transitions**:

```text
Idle → [WebSocket message] → Invalidate tasks → Idle
Idle → [Poll tick] → Invalidate tasks → Idle
Idle → [Auto-refresh timer] → Invalidate board (cached) → Idle
Idle → [Manual refresh] → Force-fetch board (bypass cache) → Idle
```

**Deduplication Rules**:
- Manual refresh: concurrent calls share the same promise (existing dedup in `useBoardRefresh`)
- TanStack Query: same query key requests are automatically deduped
- WebSocket `initial_data`: debounced to max once per 2-second window

---

### 4. PerformanceBaseline

**Description**: Documented snapshot of quantitative metrics for before/after comparison.

| Metric | Unit | Measurement Method |
|--------|------|--------------------|
| idle_api_call_count | calls/5min | Count outgoing API calls with board open, no interaction, 5-min window |
| board_endpoint_cost_cold | API calls | Count external API calls for a full board refresh with empty cache |
| board_endpoint_cost_warm | API calls | Count external API calls for a board refresh with warm sub-issue cache |
| ws_refresh_frequency | messages/min | Count WebSocket messages sent to idle client |
| polling_refresh_frequency | calls/min | Count fallback polling API calls when WS unavailable |
| board_render_time | ms | React Profiler measurement for initial board render |
| interaction_response_time | ms | Time from user action (click, drag) to visual response |
| rerender_count_per_update | count | Number of component rerenders triggered by a single task update |

**Validation Rules**:
- Baselines MUST be captured before any optimization code changes (FR-001, FR-002)
- After-measurements MUST use the same protocol as baselines (FR-014)
- No metric may regress beyond acceptable tolerance (SC-008)

---

### 5. WebSocketSubscription

**Description**: Server-side subscription state for connected clients.

| Field | Type | Notes |
|-------|------|-------|
| project_id | string | Subscribed project |
| client_id | string | Connected client identifier |
| last_data_hash | string | Hash of last-sent task data (for change detection) |
| connection_state | enum | connected, disconnected |

**Change Detection Logic** (optimization target):
1. On subscription update cycle: hash current task data
2. Compare with `last_data_hash`
3. If equal: skip sending message (no-op)
4. If different: send message, update `last_data_hash`

**State Transitions**:

```text
Disconnected → [Client connects] → Connected (last_data_hash = null)
Connected → [Data unchanged] → Connected (no message sent)
Connected → [Data changed] → Connected (message sent, hash updated)
Connected → [Client disconnects] → Disconnected (subscription cleaned up)
```

---

### 6. RenderOptimizationTarget

**Description**: Frontend components targeted for render optimization.

| Component | Current Pattern | Optimization |
|-----------|----------------|-------------|
| BoardColumn | `React.memo()` | Ensure parent passes stable props (callbacks, getGroups) |
| IssueCard | `React.memo()` | Ensure parent passes stable `onClick`, `availableAgents` |
| ProjectsPage | `useMemo` x3, `useCallback` x2 | Memoize `getGroups` callback if unstable |
| AddAgentPopover | Scroll/resize listeners | RAF-gate or throttle `updatePosition` |
| ChatPopup | RAF-gated drag | Already optimized — no changes needed |

## Relationship Diagram

```text
BoardData (300s cache)
├── Column[]
│   └── BoardItem[]
│       └── SubIssueData (600s cache, per-issue key)
│
RefreshTrigger ──→ invalidates ──→ TanStack Query Cache
│                                   ├── ['board', 'data', projectId]
│                                   └── ['board', 'projects']
│
WebSocketSubscription
├── change detection (hash comparison)
└── sends messages only on data change
│
PerformanceBaseline
├── before-state (captured pre-optimization)
└── after-state (captured post-optimization)
```
