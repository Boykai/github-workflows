# Research: Activity Log / Audit Trail

**Feature**: `054-activity-audit-trail` | **Date**: 2026-03-20
**Purpose**: Resolve all NEEDS CLARIFICATION items and document technology decisions.

## Research Tasks

### 1. Database Schema Design for Activity Events

**Question**: What schema design best fits a unified activity log in an existing SQLite database with aiosqlite?

**Decision**: Single denormalized `activity_events` table with composite indexes.

**Rationale**:
- The existing codebase uses SQLite with aiosqlite and direct SQL queries (no ORM). All tables follow a flat schema pattern with TEXT columns and explicit indexes (see `023_consolidated_schema.sql`).
- A single table avoids JOINs for the unified feed query — the primary access pattern is "all events for a project, ordered by time."
- SQLite handles single-writer workloads well; fire-and-forget inserts won't contend with reads since activity queries are simple index scans.
- The `detail` column stores a JSON blob as TEXT — SQLite's `json_extract()` can be used for optional querying, but the primary use is opaque storage rendered by the frontend.

**Alternatives considered**:
- **Per-entity history tables** (e.g., `pipeline_event_log`, `chore_event_log`): Rejected — requires complex UNION queries for the unified feed, more migrations, and violates DRY. The spec explicitly chose a unified table.
- **Event sourcing / append-only log with snapshots**: Rejected — overengineered for the scale (10K–100K events). Simple INSERT + SELECT with cursor pagination is sufficient.
- **Write-ahead log (WAL) journal mode**: Already enabled by default in the app's SQLite configuration. No change needed.

---

### 2. Cursor-Based Pagination for Append-Only Data

**Question**: How should cursor-based pagination work for a time-ordered, append-only activity feed?

**Decision**: Use `created_at` timestamp as the cursor value, encoded as base64 for opacity. For stable ordering on timestamp collisions, use `(created_at, id)` as the compound sort key.

**Rationale**:
- The existing `PaginatedResponse[T]` model and cursor encoding pattern (`_encode_cursor` / `_decode_cursor` in `services/pagination.py`) use base64-encoded opaque cursors. The activity feed should follow the same pattern.
- However, the existing `apply_pagination()` operates on in-memory lists. Activity data lives in the database, so pagination must happen at the SQL level: `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT ?`.
- Using `(created_at, id)` as the compound cursor guarantees stable ordering even when multiple events share the same timestamp (edge case identified in spec).
- The cursor value is a base64-encoded `timestamp|id` string, decoded server-side for the SQL query.

**Alternatives considered**:
- **Offset-based pagination**: Rejected — spec explicitly chose cursor-based. Offset pagination has known issues with concurrent inserts (duplicated/skipped rows).
- **Auto-increment integer cursor**: Rejected — the existing pattern uses string IDs (UUIDs). Adding an auto-increment column diverges from conventions.
- **In-memory pagination via `apply_pagination()`**: Rejected — requires loading all events into memory, which fails at 10K+ rows.

---

### 3. Fire-and-Forget Activity Logging Pattern

**Question**: How to implement non-blocking, failure-tolerant activity logging in an async FastAPI application?

**Decision**: A standalone async function `log_event()` that wraps the INSERT in a try/except and logs failures to the application logger. Called directly from route handlers and services — no background task queue.

**Rationale**:
- The spec requires that "activity logging failures must never break the primary operation" (FR-004, SC-007). A bare try/except with logging is the simplest pattern that satisfies this.
- FastAPI's `BackgroundTasks` could be used but adds unnecessary complexity — the INSERT is a sub-millisecond operation on SQLite with WAL mode. The overhead of scheduling a background task may exceed the INSERT itself.
- The function accepts a database connection and event data, executes the INSERT, and silently catches any exception. No retry logic — if the INSERT fails (e.g., disk full), the event is lost, which is acceptable per spec.
- The function is importable from `services/activity_logger.py` and called from any route handler or service that has a database connection.

**Alternatives considered**:
- **FastAPI BackgroundTasks**: Rejected — adds scheduling overhead for a sub-millisecond operation. Also complicates dependency injection (need to pass BackgroundTasks through the call chain).
- **asyncio.create_task()**: Rejected — creates a detached coroutine that may outlive the request lifecycle and complicates error handling.
- **Message queue (Redis, RabbitMQ)**: Rejected — massive overengineering for SQLite INSERT. No external dependencies exist in the current stack.
- **Middleware-based logging**: Rejected — activity events need domain context (entity type, action, summary) that middleware doesn't have.

---

### 4. Frontend Activity Feed Architecture

**Question**: How to build the Activity page with filtering and infinite scroll using existing frontend patterns?

**Decision**: Reuse `useInfiniteList` hook with a new `useActivityFeed` wrapper. Use `InfiniteScrollContainer` for scroll-based loading. Filter state managed locally in the `ActivityPage` component.

**Rationale**:
- The `useInfiniteList` hook already wraps TanStack Query's `useInfiniteQuery` with cursor-based pagination, page flattening, and reset logic. A thin `useActivityFeed` wrapper adds activity-specific query keys and filter parameters.
- The `InfiniteScrollContainer` component already implements intersection observer-based scroll detection. Reusing it avoids duplicating scroll logic.
- Filter state (selected event types) is component-local because it only affects the Activity page query. When filters change, the query key changes, triggering a fresh fetch — TanStack Query handles cache invalidation automatically.
- The 30s `staleTime` provides light polling without WebSocket complexity, per spec assumptions.

**Alternatives considered**:
- **Custom `useInfiniteQuery` wrapper**: Rejected — `useInfiniteList` already does this. DRY principle.
- **Zustand/Redux for filter state**: Rejected — filter state is page-local and doesn't need global persistence.
- **WebSocket real-time updates**: Rejected per spec — deferred to follow-up. 30s polling is acceptable for v1.
- **Optimistic updates for activity feed**: Rejected — activity events are server-generated, not user-created. No optimistic pattern needed.

---

### 5. Notification Bell Integration

**Question**: How to wire the placeholder notification bell to real activity data?

**Decision**: Modify `useNotifications` to query the activity feed API for recent high-signal events (pipeline completions/failures, chore triggers, agent executions). Map activity events to the existing `Notification` type. Keep localStorage read tracking.

**Rationale**:
- The `useNotifications` hook already has the read tracking infrastructure (localStorage `solune-read-notifications`). It returns `Notification[]` with `id`, `type`, `title`, `timestamp`, `read`, `source` fields.
- Activity events map cleanly to notifications: `event.id` → `notification.id`, `event.summary` → `notification.title`, `event.created_at` → `notification.timestamp`, `event.event_type` → `notification.type` (mapped to 'agent' | 'chore' or extended).
- The notification bell queries the last 20 events filtered to high-signal types. This reuses the same API endpoint as the Activity page with a smaller limit and type filter.
- No new API endpoint needed — the activity feed endpoint with `event_type` filter serves both the Activity page and the notification bell.

**Alternatives considered**:
- **Separate notifications API**: Rejected — duplicates activity data. The activity feed with type filtering serves the notification use case.
- **Server-side read tracking**: Rejected — spec assumes localStorage (consistent with existing pattern). Cross-device sync is out of scope.
- **Push notifications (browser Notification API)**: Rejected — out of scope. Would require service worker registration and user permission.

---

### 6. Entity-Scoped History API Design

**Question**: How to query activity events for a specific entity?

**Decision**: Add a `GET /activity/{entity_type}/{entity_id}` endpoint that queries the `activity_events` table filtered by `entity_type` and `entity_id`, using the same pagination pattern as the main feed.

**Rationale**:
- The `(entity_type, entity_id)` composite index supports efficient lookups for entity-scoped queries.
- The endpoint returns the same `PaginatedResponse[ActivityEvent]` envelope as the main feed, so the frontend can reuse `useInfiniteList` with a different query function.
- Entity type is part of the URL path (not a query parameter) because it changes the semantic meaning of the resource — you're viewing "the history of pipeline X," not "all events filtered to pipeline X."

**Alternatives considered**:
- **Query parameter filter on main feed** (`GET /activity?entity_type=pipeline&entity_id=abc`): Rejected — semantically different resource. Entity history is a focused view, not a filtered feed.
- **Embedding history in entity GET endpoints** (e.g., `GET /pipelines/{id}` includes recent events): Rejected — violates single-responsibility. Entity endpoints return entity data; activity endpoints return activity data.

---

### 7. Migration Naming and Numbering

**Question**: What migration number and naming convention to use?

**Decision**: `032_activity_events.sql` — next sequential number after `031_queue_mode.sql`.

**Rationale**:
- Existing migrations use zero-padded three-digit sequential numbering: `023_consolidated_schema.sql` through `031_queue_mode.sql`.
- The database initialization code (`database.py`) runs migrations in order based on filename sorting.
- A single migration file creates the table and both indexes. No multi-file migration needed.

**Alternatives considered**:
- **Timestamp-based migration naming**: Rejected — not consistent with existing convention.
- **Multiple migration files** (one for table, one for indexes): Rejected — unnecessary complexity for a single table.

---

### 8. Activity Event Types and Actions Taxonomy

**Question**: What are the complete sets of event types and actions?

**Decision**: Use two orthogonal enums — `event_type` categorizes what happened, `action` categorizes the verb.

**Event types** (12 values):
- `pipeline_run` — Pipeline execution lifecycle
- `pipeline_stage` — Individual stage completion/failure
- `chore_trigger` — Chore trigger evaluation/execution
- `chore_crud` — Chore create/update/delete
- `agent_crud` — Agent create/update/delete
- `agent_execution` — Agent task execution
- `cleanup` — Cleanup operation lifecycle
- `app_crud` — App create/update/delete
- `tool_crud` — Tool create/update/delete
- `status_change` — Workflow status transition
- `webhook` — Inbound webhook event

**Entity types** (6 values):
- `pipeline`, `chore`, `agent`, `app`, `tool`, `issue`

**Actions** (9 values):
- `created`, `updated`, `deleted`, `triggered`, `started`, `completed`, `failed`, `cancelled`, `moved`

**Rationale**: These align directly with the spec's FR-022 through FR-027. The taxonomy is flat (no hierarchy) because the activity feed displays events uniformly. The frontend maps `event_type` to icons and filter chips.

---

## Summary of Resolved Items

| Item | Resolution |
|------|------------|
| Schema design | Single `activity_events` table with `(project_id, created_at DESC)` and `(entity_type, entity_id)` indexes |
| Cursor pagination | `(created_at, id)` compound cursor, base64-encoded, SQL-level pagination |
| Fire-and-forget logging | Async `log_event()` with try/except, no background task queue |
| Frontend architecture | Reuse `useInfiniteList` + `InfiniteScrollContainer`, component-local filter state |
| Notification bell | Query activity feed API with type filter, map to existing `Notification` type |
| Entity history | Separate `GET /activity/{entity_type}/{entity_id}` endpoint with same pagination |
| Migration naming | `032_activity_events.sql` (next sequential) |
| Event taxonomy | 11 event types × 9 actions, flat structure, mapped to icons/filters in frontend |
