# Data Model: Performance Review

**Feature**: 001-performance-review  
**Date**: 2026-03-26  
**Source**: [spec.md](./spec.md) Key Entities + [research.md](./research.md) findings

## Entities

### E-001: Board Data Cache

**Source**: FR-004, FR-005, FR-007 | Existing: `solune/backend/src/services/cache.py`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| cache_key | `str` | Format: `board_data:{project_id}` | Non-empty, matches `prefix:identifier` pattern |
| value | `T` (generic) | Cached board payload (columns, items, metadata) | JSON-serializable |
| expires_at | `datetime` | UTC timestamp when entry expires | Must be in the future at creation |
| ttl | `int` | Time-to-live in seconds (default: 300) | Positive integer |
| data_hash | `str \| None` | SHA256 of JSON-serialized value | 64-char hex string when present |
| etag | `str \| None` | HTTP ETag for conditional requests | Optional |
| last_modified | `str \| None` | HTTP Last-Modified header value | ISO 8601 when present |

**Relationships**:
- One board data cache entry per `project_id`
- Contains sub-issue references that link to Sub-Issue Cache entries
- Invalidated by: manual refresh (full delete), status update (full delete)
- Refreshed by: auto-refresh timer, WebSocket change detection (TTL refresh only if unchanged)

**State Transitions**:
```
[Empty] --set()--> [Warm] --expires--> [Expired/Stale]
[Warm] --delete()--> [Empty]
[Warm] --refresh_ttl()--> [Warm] (unchanged data, TTL reset)
[Warm] --set()--> [Warm] (changed data, new value + TTL)
[Expired/Stale] --get_stale()--> returns value (degraded mode)
[Expired/Stale] --set()--> [Warm]
```

---

### E-002: Sub-Issue Cache

**Source**: FR-005 | Existing: `solune/backend/src/services/cache.py` (key helper)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| cache_key | `str` | Format: `sub_issues:{owner}/{repo}#{issue_number}` | Non-empty, matches pattern |
| value | `list` | Cached sub-issue list for a parent issue | JSON-serializable list |
| expires_at | `datetime` | UTC timestamp when entry expires | Must be in the future at creation |
| ttl | `int` | Time-to-live in seconds (default: 300) | Positive integer |
| data_hash | `str \| None` | SHA256 of JSON-serialized sub-issue list | 64-char hex string when present |

**Relationships**:
- One sub-issue cache entry per parent issue (keyed by owner/repo/issue_number)
- Referenced by Board Data Cache (board items may expand sub-issues)
- Invalidated by: manual refresh only (`refresh=true`)
- Reused by: automatic refreshes, auto-refresh timer

**State Transitions**:
```
[Empty] --fetch+cache()--> [Warm]
[Warm] --manual_refresh()--> [Empty] (cleared on manual refresh)
[Warm] --auto_refresh()--> [Warm] (reused, not cleared)
[Warm] --expires--> [Expired/Stale]
```

---

### E-003: Refresh Event

**Source**: FR-008, FR-009, FR-010, FR-011 | Existing: `useRealTimeSync.ts`, `useBoardRefresh.ts`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| source | `RefreshSource` | Origin of the refresh trigger | One of: `websocket`, `polling_fallback`, `auto_refresh`, `manual_refresh` |
| scope | `RefreshScope` | Breadth of data to refresh | One of: `task_update`, `full_board` |
| project_id | `string` | Target project for this refresh | Non-empty string |
| dedupe_id | `string \| undefined` | Identifier for deduplication within debounce window | Optional |
| timestamp | `number` | When the event was created (epoch ms) | Positive number |
| bypass_cache | `boolean` | Whether to skip all caches | `true` only for `manual_refresh` source |

**Relationships**:
- Each Refresh Event targets one project's board data
- Deduplication groups events within a 2-second window
- Manual refresh events override all other concurrent events
- Refresh policy determines which backend cache behavior applies

**Refresh Policy Matrix** (see also: `contracts/refresh-policy.md`):

| Source | Scope | Bypasses Cache | Deduplicatable |
|--------|-------|----------------|----------------|
| `websocket` (task_update) | `task_update` | No | Yes (2s window) |
| `websocket` (refresh) | `full_board` | No | Yes (2s window) |
| `polling_fallback` | `task_update` | No | Yes (2s window) |
| `auto_refresh` | `full_board` | No | Yes (2s window) |
| `manual_refresh` | `full_board` | Yes | No (always executes) |

---

### E-004: Performance Baseline

**Source**: FR-001, FR-002, SC-001 through SC-008

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| metric_name | `str` | Human-readable metric identifier | Non-empty, unique within a baseline set |
| category | `str` | Grouping: `backend_api`, `backend_cache`, `frontend_render`, `frontend_network` | One of the defined categories |
| measured_value | `number` | Numeric measurement result | Non-negative |
| unit | `str` | Measurement unit | e.g., `calls`, `ms`, `count`, `bytes` |
| conditions | `str` | Description of measurement conditions | Non-empty |
| timestamp | `datetime` | When the measurement was captured | ISO 8601 |
| board_size | `str` | Board dimensions during measurement | e.g., `5 columns, 25 cards` |

**Relationships**:
- Baseline set captured before optimization (Phase 1)
- Post-optimization set captured after changes (Phase 3 verification)
- SC-001 compares idle API call counts between baseline and post sets
- SC-004 compares rerender counts between baseline and post sets

**Baseline Metrics Catalog**:

| Metric | Category | Unit | Measurement Method |
|--------|----------|------|--------------------|
| Idle API calls (5 min) | backend_api | calls | Count outbound GitHub API requests during idle board viewing |
| Board cold-cache request cost | backend_api | calls | Count GitHub API calls for a board endpoint request with empty cache |
| Board warm-cache request cost | backend_api | calls | Count GitHub API calls for a board endpoint request with warm cache (expect 0) |
| WebSocket idle refresh events (5 min) | backend_api | count | Count `refresh` messages sent when no upstream data changes |
| Board initial render time | frontend_render | ms | Performance.mark/measure from mount to paint |
| Component mount count (initial load) | frontend_render | count | React DevTools profiler or test instrumentation |
| Single-card-update rerender count | frontend_render | count | React DevTools profiler: components rerendered on one card status change |
| Drag interaction event fires/sec | frontend_render | count/s | Event listener fire rate during drag operation |
| Network requests on WS task_update | frontend_network | count | Network inspector: requests triggered by a single WebSocket task update |
| Network requests on polling fallback cycle | frontend_network | count | Network inspector: requests triggered by one polling fallback interval |

---

## Relationships Diagram

```
┌─────────────────────┐     contains refs to     ┌──────────────────────┐
│   Board Data Cache   │ ───────────────────────► │   Sub-Issue Cache    │
│   (E-001)           │                           │   (E-002)           │
│                     │                           │                     │
│ key: board_data:PID │                           │ key: sub_issues:    │
│ ttl: 300s           │                           │   owner/repo#num    │
│ hash: SHA256        │                           │ ttl: 300s           │
└─────────┬───────────┘                           └──────────┬──────────┘
          │                                                  │
          │ invalidated/refreshed by                         │ cleared only by
          │                                                  │ manual refresh
          ▼                                                  ▼
┌─────────────────────┐                           ┌──────────────────────┐
│   Refresh Event      │                           │   Manual Refresh     │
│   (E-003)           │                           │   (source=manual)    │
│                     │                           │   bypass_cache=true  │
│ source: ws/poll/    │                           └──────────────────────┘
│   auto/manual       │
│ scope: task/board   │
│ dedup: 2s window    │
└─────────┬───────────┘
          │
          │ measured against
          ▼
┌─────────────────────┐
│ Performance Baseline │
│   (E-004)           │
│                     │
│ before vs. after    │
│ SC-001: ≥50% fewer  │
│   idle API calls    │
└─────────────────────┘
```
