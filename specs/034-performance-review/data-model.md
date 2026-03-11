# Data Model: Performance Review

**Feature Branch**: `034-performance-review`
**Date**: 2026-03-11
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Entities

### Board Data

The full project board state. This is the most expensive resource to fetch and the primary target for cache optimization.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| project_id | string | Unique project identifier | Required, non-empty |
| columns | Column[] | Ordered list of board columns | Required, ≥ 0 items |
| metadata | object | Project-level metadata (name, description) | Required |
| fetched_at | ISO 8601 timestamp | When the data was last fetched from GitHub | Required |
| cache_ttl | integer (seconds) | Time-to-live for this cache entry | Default: 300 |
| is_stale | boolean | Whether this data was served from stale fallback | Default: false |

**Cache key**: `board_data:{project_id}`
**TTL**: 300 seconds (5 minutes)
**Stale fallback**: Yes — served when GitHub API is rate-limited

**Relationships**:

- Contains → Column (1:N)
- Cached by → Cache Service
- Refreshed by → Refresh Event

---

### Column

A board column representing a status group or category.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | string | Column identifier | Required |
| name | string | Display name | Required |
| cards | IssueCard[] | Ordered list of issue cards | ≥ 0 items |
| position | integer | Column sort order | ≥ 0 |

**Relationships**:

- Contained by → Board Data (N:1)
- Contains → IssueCard (1:N)

**Rendering note**: Wrapped in `React.memo()` — only rerenders when its own props change.

---

### IssueCard (Task)

A single task/issue card displayed on the board. The lightweight unit that should be updatable without a full board reload.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | string | Issue/task identifier | Required |
| title | string | Issue title | Required |
| status | string | Current status (maps to column) | Required |
| assignee | string \| null | Assigned user | Optional |
| labels | string[] | Applied labels | ≥ 0 items |
| updated_at | ISO 8601 timestamp | Last modification time | Required |
| has_sub_issues | boolean | Whether this card has child issues | Default: false |

**Relationships**:

- Contained by → Column (N:1)
- Has children → Sub-Issue Data (1:N, optional)

**Rendering note**: Wrapped in `React.memo()` — only rerenders when its own props change.

---

### Sub-Issue Data

Child issue details fetched as part of board data. Independently cacheable to reduce redundant GitHub API calls.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| owner | string | Repository owner | Required |
| repo | string | Repository name | Required |
| issue_number | integer | Parent issue number | Required, > 0 |
| sub_issues | object[] | List of child issue details | ≥ 0 items |
| fetched_at | ISO 8601 timestamp | When sub-issues were last fetched | Required |

**Cache key**: `SUB_ISSUES:{owner}/{repo}#{issue_number}`
**TTL**: 300 seconds (5 minutes)
**Invalidation**: Cleared on manual refresh; otherwise expires via TTL

**Relationships**:

- Child of → IssueCard (N:1)
- Cached by → Cache Service

---

### Refresh Event

An event that triggers data fetching. The key entity for the unified refresh policy.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| source | enum | Origin of the refresh | Required; one of: `websocket`, `polling`, `auto_refresh`, `manual` |
| scope | enum | What data to refresh | Required; one of: `task_only`, `full_board` |
| force | boolean | Whether to bypass caches | Default: false |
| timestamp | ISO 8601 timestamp | When the event occurred | Required |
| deduplicated | boolean | Whether this event was merged with a concurrent event | Default: false |

**State transitions** (Refresh Policy):

```text
             ┌──────────────────────────────────────┐
             │        Refresh Event Received         │
             └──────────────┬───────────────────────┘
                            │
                    ┌───────▼───────┐
                    │ Check source  │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
     ┌──────▼──────┐ ┌─────▼─────┐ ┌───────▼──────┐
     │  websocket  │ │  polling   │ │   manual     │
     │ task_update │ │  fallback  │ │   refresh    │
     └──────┬──────┘ └─────┬─────┘ └───────┬──────┘
            │               │               │
            ▼               ▼               ▼
     scope: task_only  scope: task_only  scope: full_board
     force: false      force: false      force: true
            │               │               │
            ▼               ▼               ▼
     Invalidate task   Invalidate task   Clear all caches
     queries only      queries only      + full board refetch
            │               │               │
            └───────────────┼───────────────┘
                            │
                    ┌───────▼───────┐
                    │  Dedup check  │
                    │ (concurrent?) │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  Execute or   │
                    │  merge event  │
                    └───────────────┘
```

**auto_refresh** follows the same path as `polling` (scope: task_only, force: false).

---

### Performance Baseline

A documented set of measurements taken before optimization. Reference point for validating improvements.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| measurement_id | string | Unique identifier for this baseline run | Required |
| category | enum | Backend or frontend measurement | Required; one of: `backend`, `frontend` |
| metric_name | string | What is being measured | Required |
| value | number | Measured value | Required |
| unit | string | Unit of measurement | Required |
| conditions | string | Test conditions (board size, idle duration, etc.) | Required |
| measured_at | ISO 8601 timestamp | When measurement was taken | Required |

**Example baselines**:

| Metric | Category | Unit | Conditions |
|--------|----------|------|------------|
| idle_api_calls_5min | backend | count | Open board, no data changes, 5 min window |
| board_endpoint_response_ms | backend | milliseconds | Representative board (50–100 tasks) |
| board_endpoint_github_calls | backend | count | Cold cache vs. warm cache |
| ws_messages_idle_5min | backend | count | WebSocket connected, no changes |
| polling_data_fetches_5min | backend | count | Fallback polling active, no changes |
| board_render_count | frontend | count | Initial load + 1 interaction |
| board_render_duration_ms | frontend | milliseconds | Initial load of representative board |
| hot_component_rerenders | frontend | count | Single card drag operation |

---

## Validation Rules

1. **Cache TTL consistency**: Board data and sub-issue caches MUST use the same TTL (300s) to prevent inconsistent staleness.
2. **Refresh scope enforcement**: WebSocket and polling events MUST NOT set `scope: full_board` unless the source is `manual`.
3. **Deduplication**: Concurrent refresh events from different sources MUST be deduplicated — only one refresh executes.
4. **Stale fallback safety**: Stale data MUST only be served when the GitHub API is rate-limited, never during normal operation.
5. **Manual refresh override**: Manual refresh MUST always bypass all caches regardless of TTL state or concurrent operations.

## State Machines

### WebSocket Connection State

```text
disconnected ──► connecting ──► connected
     ▲                              │
     │                              ▼ (on error/close)
     └──────── polling ◄────────────┘
                  │
                  ▼ (on reconnect)
              connecting
```

- **disconnected**: Initial state or after all retry attempts exhausted
- **connecting**: WebSocket handshake in progress (10s timeout)
- **connected**: Active WebSocket receiving messages
- **polling**: Fallback HTTP polling (30s interval) with exponential backoff reconnect attempts (base 1s, max 30s, jitter)

### Cache Entry Lifecycle

```text
[empty] ──set()──► [fresh] ──TTL expires──► [stale] ──clear_expired()──► [empty]
                      │                        │
                      │ delete()               │ get_stale() (rate-limited)
                      ▼                        ▼
                   [empty]              [served + logged]
```
