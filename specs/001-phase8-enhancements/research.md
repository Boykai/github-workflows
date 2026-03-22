# Research: Phase 8 Feature Enhancements

**Feature**: `001-phase8-enhancements` | **Date**: 2026-03-22  
**Purpose**: Resolve technical unknowns and document design decisions for the Phase 8 Feature Enhancements.

## Research Tasks

### RT-001: Adaptive Polling Strategy

**Context**: The existing `copilot_polling` service uses a fixed polling loop with rate-limit-aware pausing. We need to add activity-based adaptive intervals.

**Decision**: Use a sliding-window activity score with configurable interval tiers.

**Rationale**: The current `polling_loop.py` already tracks `poll_count`, `last_poll_time`, and rate limit state. The adaptive layer can be built on top by:
1. Tracking a `changes_detected` counter over a rolling window (e.g., last 5 polls).
2. Computing an activity score: `score = changes_in_window / window_size`.
3. Mapping score to interval tiers: high activity (score > 0.6) → 3s, medium (0.2–0.6) → 10s, low (< 0.2) → 30s.
4. On tab re-focus (frontend `visibilitychange` event), immediately trigger a poll and reset to the medium tier.
5. On poll failure, apply exponential backoff (2^n × base_interval, capped at 60s) using the existing `tenacity` retry library pattern.

**Frontend integration**: TanStack Query's `refetchInterval` option accepts a function `(query) => number | false`. The adaptive hook (`useAdaptivePolling`) returns a dynamic interval function that the `useProjectBoard` hook passes to `refetchInterval`.

**Alternatives considered**:
- **WebSocket push**: Would eliminate polling entirely but requires significant infrastructure (WebSocket server, connection management, reconnection logic). The existing polling architecture is well-tested and the improvement from adaptive intervals provides sufficient freshness. WebSockets deferred to a future phase.
- **Server-Sent Events (SSE)**: Simpler than WebSockets but still requires backend event source infrastructure that doesn't exist. Adaptive polling is the lowest-risk approach.
- **Fixed exponential decay**: Simpler but doesn't respond to activity bursts. The sliding-window approach adapts in both directions.

---

### RT-002: Concurrent Pipeline Execution Patterns

**Context**: The `workflow_orchestrator` already supports `execution_mode: "sequential" | "parallel"` in `PipelineState`. The `pipeline_state_store` has per-project launch locks. We need to enable true concurrent dispatch while respecting queue-mode.

**Decision**: Use `asyncio.TaskGroup` (Python 3.11+) for concurrent pipeline dispatch, gated by queue-mode check.

**Rationale**:
1. The existing `get_project_launch_lock(project_id)` serializes queue-gate decisions. This lock remains the entry point.
2. Inside the lock, check `is_queue_mode_enabled(project_id)` (10s TTL cache in `settings_store`).
3. If queue mode is OFF, release the lock immediately and dispatch each independent pipeline as a separate `asyncio.Task` via `task_registry.task_registry` (per codebase convention — no raw `asyncio.create_task`).
4. If queue mode is ON, maintain existing sequential behavior (backward compatibility per FR-006).
5. Fault isolation (FR-005): Each pipeline task has its own `try/except` handler. One failure does not cancel siblings.
6. Independence determination: Pipelines targeting different entities (different issue numbers) are independent. Pipelines targeting the same issue are serialized within the per-issue pipeline state lock.

**Alternatives considered**:
- **Thread pool executor**: Python's GIL makes this less efficient for I/O-bound pipeline work. `asyncio` tasks are native to the existing codebase.
- **Celery/distributed queue**: Massive infrastructure overhead for a single-server SQLite-backed application. The existing `task_registry` pattern is sufficient.
- **No concurrency, just faster sequential**: Doesn't address the core problem of independent pipelines blocking each other.

---

### RT-003: Board Lazy Loading / Projection Strategy

**Context**: The frontend `useProjectBoard` hook fetches all board data at once. Large boards (500+ items) cause slow initial renders. The backend returns `BoardDataResponse` with all columns and items.

**Decision**: Implement frontend-only virtualized rendering with intersection observer-based lazy loading, plus an optional backend pagination endpoint.

**Rationale**:
1. **Frontend virtualization**: Use intersection observers to detect which `BoardColumn` items are in the viewport. Only render DOM nodes for visible items + a small buffer (e.g., ±10 items).
2. **Initial projection**: On first load, the backend returns all items but the frontend only mounts DOM for the initially visible set. This achieves the 2-second render target (FR-007) by reducing DOM node count.
3. **Scroll loading**: As users scroll, intersection observers trigger rendering of additional items. Since data is already in memory (TanStack Query cache), the 500ms target (FR-008) is easily achievable.
4. **Full dataset for filters**: Since all data is loaded into TanStack Query cache, filters and search (FR-009) operate on the complete dataset, not just the rendered projection.
5. **Cache strategy**: TanStack Query's existing `staleTime` configuration ensures previously loaded data is served from cache on return navigation (spec acceptance scenario 4).
6. **Backend pagination (optional Phase 2)**: For boards exceeding 1000+ items, a future backend endpoint could support cursor-based pagination. This is not required for the 500-item target.

**Alternatives considered**:
- **Backend-only pagination**: Would require significant API changes and breaks client-side filtering/search requirements (FR-009). The full dataset must be available on the client.
- **React-window/react-virtuoso**: Third-party virtualization libraries. The Kanban layout (horizontal columns with vertical card lists) doesn't map cleanly to these row-based virtualizers. Custom intersection observer approach is simpler and fits the existing `@dnd-kit` drag-drop setup.
- **Canvas-based rendering**: Extreme performance gains but incompatible with the existing React component tree and accessibility requirements.

---

### RT-004: Pipeline Config Filter in BoardToolbar

**Context**: `BoardToolbar.tsx` already supports filter (labels, assignees, milestones), sort, and group-by controls. We need to add a pipeline configuration filter dropdown.

**Decision**: Add a pipeline config filter as a new filter dimension in `BoardToolbar.tsx`, using the existing mutually-exclusive panel pattern.

**Rationale**:
1. `useBoardControls` already manages `BoardFilterState` with label/assignee/milestone filters. Add a `pipelineConfigId: string | null` field (null = "All Pipelines").
2. The board data response already includes pipeline configuration metadata per item (items have associated pipeline config references).
3. Client-side filtering: When `pipelineConfigId` is set, filter items in the existing board data by matching the pipeline config. No backend changes needed (FR-011).
4. Filter persistence across polls: The filter state lives in React state (useBoardControls), independent of data fetching. When polling delivers new data, the filter is re-applied (FR-012).
5. UI: A `Select` dropdown (Radix UI) with pipeline config names + "All Pipelines" default. Positioned alongside existing toolbar controls.

**Alternatives considered**:
- **Backend-side filtering**: Adds API complexity. Since all data is already on the client, client-side filtering is simpler and faster.
- **URL query parameter persistence**: Could persist filter across page reloads, but the spec says "per session" which React state handles. URL persistence can be added later.

---

### RT-005: Label-Driven State Recovery

**Context**: `recovery.py` (33.8KB) already implements self-healing recovery for stalled agent pipelines. `label_manager.py` provides `build_label_name()`, `parse_label()`, and `create_pipeline_label()`. Labels follow the pattern `solune:pipeline:{run_id}:stage:{stage_id}:{status}`.

**Decision**: Extend the existing recovery module to perform full state reconstruction from labels on startup when internal state is unavailable.

**Rationale**:
1. On startup, `init_pipeline_state_store(db)` loads states from SQLite. If the database is empty/corrupt (database.py already handles corruption detection), trigger label-based recovery.
2. Recovery flow: For each project → list all items → parse `solune:pipeline:*` labels → reconstruct `PipelineState` entries in the state store.
3. `_validate_and_reconcile_tracking_table()` in recovery.py already validates pipeline steps against GitHub ground truth. The new recovery extends this to handle the "no internal state at all" case.
4. Ambiguity handling (FR-015): If an item has labels from multiple pipeline runs or contradictory stages, log a warning via the existing alert dispatcher (`get_dispatcher()`) and mark the item with a `recovery:manual-review` flag.
5. Duplicate action prevention (FR-016): Set a `recovered_at` timestamp on reconstructed states. The polling pipeline checks this and skips re-processing for items recovered within the current startup cycle.

**Alternatives considered**:
- **Snapshot-based backup**: Periodically dump state to a backup file. More complex to implement and doesn't leverage the existing label infrastructure. Labels are already the source of truth per the existing recovery.py design.
- **External state store (Redis/Postgres)**: Architectural change beyond scope. SQLite + labels-as-backup is sufficient for the single-server deployment model.

---

### RT-006: MCP Collision Detection and Resolution

**Context**: `mcp_store.py` manages MCP configuration CRUD. The spec requires collision detection when concurrent MCP operations target the same entity. The current MCP implementation is simple CRUD with no concurrency awareness.

**Decision**: Implement optimistic concurrency control with version vectors and a last-write-wins + user-priority resolution strategy.

**Rationale**:
1. Add a `version` field to MCP entities. Each mutation increments the version.
2. Operations include their expected version. If the current version doesn't match, a collision is detected.
3. Resolution strategy (FR-017, FR-018):
   - If both operations are automated: last-write-wins based on timestamp.
   - If one is user-initiated and one is automated: user-initiated wins (FR-018).
   - If both are user-initiated: last-write-wins with conflict notification.
   - If contradictory (FR-020): mark for manual review, notify via toast.
4. Logging (FR-019): All collision events are logged with both operations, resolution outcome, and target entity details.
5. Frontend notification: On collision resolution, the backend returns a collision summary in the response. The frontend displays a toast notification via `sonner`.

**Alternatives considered**:
- **Pessimistic locking**: Locks entities before modification. Simpler but degrades performance under load and doesn't scale to concurrent pipeline execution.
- **CRDTs (Conflict-free Replicated Data Types)**: Over-engineered for this use case. Entity mutations are discrete CRUD operations, not continuous state merges.
- **Manual conflict resolution UI**: Too complex for MVP. Automated resolution with manual fallback (FR-020) is the right balance.

---

### RT-007: Undo/Redo for Destructive Actions

**Context**: No existing undo/redo infrastructure exists in the codebase. The spec requires session-scoped undo/redo for destructive actions (archive, delete, label removal) with a configurable time window (default 30s).

**Decision**: Implement a React Context-based undo/redo stack on the frontend with backend soft-delete support.

**Rationale**:
1. **Frontend undo stack**: A React context (`UndoRedoContext`) maintains two stacks: `undoStack` and `redoStack`. Each entry is an `ActionHistoryEntry` containing the action type, affected entity, previous state snapshot, new state, and timestamp.
2. **Soft delete**: Destructive backend operations (archive, delete) mark items as "pending deletion" rather than immediately deleting. After the undo window expires (30s default), a background cleanup finalizes the deletion.
3. **Undo operation**: Reverses the most recent action by restoring the previous state snapshot via the appropriate API call. Moves the entry from `undoStack` to `redoStack`.
4. **Redo operation**: Re-applies the action from the `redoStack`. Moves the entry back to `undoStack`.
5. **Stack clearing** (FR-024): A new non-undo action clears the `redoStack`.
6. **Window expiry** (FR-025): Each entry has a TTL. Expired entries are removed from the stack and the user is notified.
7. **UI**: Toast notification with "Undo" button (using `sonner`). Keyboard shortcut Ctrl+Z / Ctrl+Shift+Z for undo/redo.
8. **Server divergence warning**: If polling delivers data that conflicts with an undo operation (the server state has changed since the action), the undo shows a warning toast.

**Alternatives considered**:
- **Backend event sourcing**: Store all mutations as events and replay for undo. Architecturally elegant but massive implementation effort for a feature that only needs session-scoped undo.
- **Database transaction rollback**: SQLite doesn't support long-lived transactions across requests. Soft delete is simpler and compatible with the existing async persistence model.
- **localStorage persistence**: Could persist undo stack across page reloads, but the spec says "current session" which React state handles.

---

## Best Practices Integration

### Python / FastAPI

- Use `task_registry.task_registry` for all fire-and-forget async tasks (no raw `asyncio.create_task` per codebase convention).
- Use `get_dispatcher()` for alert/notification dispatch to avoid circular imports with `src.main`.
- Use `get_project_launch_lock(project_id)` for per-project serialization of queue-gate decisions.
- Patch source module paths in tests when mocking function-level imports (e.g., `src.services.settings_store.is_queue_mode_enabled`).

### React / TypeScript

- Import all Lucide icons from `@/lib/icons` barrel file (ESLint enforced).
- Use TanStack Query for all server-state management (polling, caching, mutations).
- Use `getErrorHint(error)` from `@/utils/errorHints` for structured error display.
- Use `sonner` for toast notifications (existing pattern).

### Concurrency / State

- Sync `set_pipeline_state()` for L1 cache updates with async SQLite persistence.
- `is_queue_mode_enabled()` has 10s TTL cache — eventual consistency is intentional.
- `_store_lock` protects all pipeline state store mutations.
