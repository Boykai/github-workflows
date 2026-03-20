# Tasks: Activity Log / Audit Trail

**Input**: Design documents from `/specs/054-activity-audit-trail/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/activity-api.yaml, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Tests are omitted. Run existing backend (ruff, pyright, pytest) and frontend (ESLint, tsc, vitest) suites for regression checks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration for the activity_events table

- [ ] T001 Create database migration with activity_events table and indexes in solune/backend/src/migrations/032_activity_events.sql

  > Table: `activity_events` with columns: `id TEXT PK`, `event_type TEXT NOT NULL`, `entity_type TEXT NOT NULL`, `entity_id TEXT NOT NULL`, `project_id TEXT NOT NULL`, `actor TEXT NOT NULL DEFAULT 'system'`, `action TEXT NOT NULL`, `summary TEXT NOT NULL`, `detail TEXT` (JSON blob), `created_at TEXT NOT NULL DEFAULT (datetime('now'))`.
  > Index: `idx_activity_project_time` on `(project_id, created_at DESC)` for feed queries.
  > Index: `idx_activity_entity` on `(entity_type, entity_id)` for entity-scoped history.
  > See data-model.md for full schema, quickstart.md § Step 1 for reference SQL.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend service + API and frontend types/client that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Create ActivityEvent and ActivityEventCreate Pydantic models in solune/backend/src/models/activity.py

  > `ActivityEvent`: response model with fields `id`, `event_type`, `entity_type`, `entity_id`, `project_id`, `actor`, `action`, `summary`, `detail: dict[str, Any] | None`, `created_at`.
  > `ActivityEventCreate`: internal model (no `id`, no `created_at`). Actor defaults to `"system"`.
  > See data-model.md § Backend Models for field definitions.

- [ ] T003 [P] Create fire-and-forget activity logger service in solune/backend/src/services/activity_logger.py

  > `async def log_event(db, *, event_type, entity_type, entity_id, project_id, actor, action, summary, detail=None)` — generates UUID, serializes detail as JSON, INSERTs row, commits. Wraps entire body in `try/except Exception` with `logger.exception()` — must NEVER raise.
  > See research.md § 3 for fire-and-forget pattern rationale. See quickstart.md § Step 3 for reference implementation.

- [ ] T004 Create activity feed API router with two GET endpoints in solune/backend/src/api/activity.py

  > `GET /activity` — query params: `project_id` (required), `limit` (default 50, max 100), `cursor` (optional, opaque base64 timestamp|id), `event_type` (optional, comma-separated filter). Returns `PaginatedResponse`-compatible envelope: `{ items, next_cursor, has_more, total_count }`. SQL-level cursor pagination using `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT ?`.
  > `GET /activity/{entity_type}/{entity_id}` — same pagination, filtered by entity_type + entity_id. Path validates entity_type against allowed values: pipeline, chore, agent, app, tool, issue.
  > See contracts/activity-api.yaml for full OpenAPI spec. See research.md § 2 for cursor encoding.

- [ ] T005 Register activity router in solune/backend/src/api/__init__.py

  > `from src.api.activity import router as activity_router` and `router.include_router(activity_router, prefix="/activity", tags=["activity"])`. Follow existing registration pattern (16 routers already registered).

- [ ] T006 [P] Add ActivityEvent TypeScript interface in solune/frontend/src/types/index.ts

  > ```typescript
  > export interface ActivityEvent {
  >   id: string;
  >   event_type: string;
  >   entity_type: string;
  >   entity_id: string;
  >   project_id: string;
  >   actor: string;
  >   action: string;
  >   summary: string;
  >   detail?: Record<string, unknown>;
  >   created_at: string;
  > }
  > ```
  > See data-model.md § Frontend Types.

- [ ] T007 Add activityApi.feed() and activityApi.entityHistory() methods in solune/frontend/src/services/api.ts

  > `activity.feed(projectId, { limit?, cursor?, event_type? })` → `GET /activity?project_id=...`
  > `activity.entityHistory(entityType, entityId, { limit?, cursor? })` → `GET /activity/{entityType}/{entityId}`
  > Both return `PaginatedResponse<ActivityEvent>`. Follow existing API client patterns (fetchApi wrapper).
  > See quickstart.md § Step 7 for reference implementation.

**Checkpoint**: Foundation ready — activity events can be logged and queried. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Unified Activity Feed (Priority: P1) 🎯 MVP

**Goal**: Users can see all significant events across their project in one chronological Activity page with human-readable summaries, type icons, relative timestamps, expand-to-detail, and empty state.

**Independent Test**: Perform several actions (run a pipeline, create a chore, delete an agent, trigger a webhook), navigate to the Activity page, verify all actions appear in reverse-chronological order with accurate summaries, icons, and timestamps. Click an event to expand detail. Verify empty state on a project with no events.

### Backend Instrumentation for User Story 1

- [ ] T008 [P] [US1] Add log_event() calls for pipeline run lifecycle in solune/backend/src/api/pipelines.py

  > Log on: run created (action: "started"), status transitions to completed/failed/cancelled. Include detail: `{ pipeline_name, run_id, status, duration_ms, stages_completed, stages_total }`. Use `event_type="pipeline_run"`, `entity_type="pipeline"`. Actor from session username.
  > See data-model.md § Pipeline Run Events for detail schema.

- [ ] T009 [P] [US1] Add log_event() calls for workflow transitions in solune/backend/src/services/workflow_orchestrator/orchestrator.py

  > Persist WorkflowTransition data via log_event() in addition to in-memory `_transitions` list. `event_type="status_change"`, `entity_type="issue"`, `action="moved"`. Detail: `{ from_status, to_status, triggered_by, issue_number }`.
  > See data-model.md § Workflow Status Change Events for detail schema.

- [ ] T010 [P] [US1] Add log_event() calls for chore triggers and CRUD in solune/backend/src/api/chores.py

  > Triggers: `event_type="chore_trigger"`, `action="triggered"`, detail: `{ chore_name, trigger_type, result_count }`.
  > CRUD: `event_type="chore_crud"`, `entity_type="chore"`, actions: created/updated/deleted, detail: `{ entity_name }`.
  > See data-model.md § Chore Trigger Events and CRUD Events.

- [ ] T011 [P] [US1] Add log_event() calls for agent CRUD in solune/backend/src/api/agents.py

  > `event_type="agent_crud"`, `entity_type="agent"`, actions: created/updated/deleted. Summary: `"Agent '{name}' {action}"`. Detail: `{ entity_name }`. One log_event() call per endpoint handler.

- [ ] T012 [P] [US1] Add log_event() calls for app CRUD and lifecycle in solune/backend/src/api/apps.py

  > `event_type="app_crud"`, `entity_type="app"`, actions: created/updated/deleted/started/completed. Summary: `"App '{name}' {action}"`. Detail: `{ entity_name }`. One log_event() call per endpoint handler.

- [ ] T013 [P] [US1] Add log_event() calls for tool CRUD in solune/backend/src/api/tools.py

  > `event_type="tool_crud"`, `entity_type="tool"`, actions: created/updated/deleted. Summary: `"Tool '{name}' {action}"`. Detail: `{ entity_name }`. One log_event() call per endpoint handler.

- [ ] T014 [P] [US1] Add log_event() calls for inbound webhook events in solune/backend/src/api/webhooks.py

  > `event_type="webhook"`, `entity_type="issue"`, `action` mapped from webhook action. Summary: `"Webhook: {type} {action} on {repo}"`. Detail: `{ webhook_type, action, sender, repository }`.
  > See data-model.md § Webhook Events for detail schema.

- [ ] T015 [P] [US1] Add log_event() calls for cleanup operations in solune/backend/src/api/cleanup.py

  > `event_type="cleanup"`, `entity_type="pipeline"` (or contextual), actions: started/completed. Detail: `{ branches_deleted, prs_closed, duration_ms }`. Reuse data from existing CleanupAuditLogRow.
  > See data-model.md § Cleanup Events for detail schema.

### Frontend Implementation for User Story 1

- [ ] T016 [US1] Create useActivityFeed hook in solune/frontend/src/hooks/useActivityFeed.ts

  > Wraps `useInfiniteList<ActivityEvent>` with activity-specific query key `['activity', projectId, eventTypeParam]`. Accepts `projectId: string` and optional `eventTypes?: string[]`. Passes `event_type` as comma-joined string to `api.activity.feed()`. Uses `staleTime: 30_000` (30s polling). `enabled: !!projectId`.
  > Returns `{ allItems, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, isError, totalCount }`.
  > See research.md § 4 and quickstart.md § Step 8 for design rationale and reference.

- [ ] T017 [US1] Create ActivityPage with event timeline, expand detail, icons, and empty state in solune/frontend/src/pages/ActivityPage.tsx

  > Timeline layout: each event as a compact row with type icon (use Lucide icons: `GitBranch` for pipeline, `ListChecks` for chore, `Bot` for agent, `Boxes` for app, `Wrench` for tool, `Webhook` for webhook, `Trash2` for cleanup, `ArrowRightLeft` for status_change), summary text, relative timestamp (e.g., "5 minutes ago"), and entity link.
  > Click event → expand inline to show detail JSON as key-value pairs.
  > Empty state: friendly message when no events exist (spec US1 scenario 4).
  > Uses `useActivityFeed(projectId)` hook. Uses `InfiniteScrollContainer` from `solune/frontend/src/components/common/InfiniteScrollContainer.tsx` for scroll-based loading.
  > Lazy-load via `lazyWithRetry` following existing pattern in App.tsx.

- [ ] T018 [US1] Add /activity route in solune/frontend/src/App.tsx

  > Add lazy import: `const ActivityPage = lazyWithRetry(() => import('./pages/ActivityPage'));`
  > Add route inside main layout routes: `<Route path="activity" element={<ActivityPage />} />`
  > Place between existing routes (after /apps or before /settings).

- [ ] T019 [P] [US1] Add Activity nav link with Clock icon to NAV_ROUTES in solune/frontend/src/constants.ts

  > Add `{ path: '/activity', label: 'Activity', icon: Clock }` to the `NAV_ROUTES` array. Import `Clock` from `lucide-react`. Place between existing nav items (after Apps, before Settings).
  > The Sidebar component (`solune/frontend/src/layout/Sidebar.tsx`) auto-renders all NAV_ROUTES entries.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The Activity page shows all system events with icons, summaries, timestamps, expand-to-detail, empty state, and basic infinite scroll.

---

## Phase 4: User Story 2 — Filtered Activity Feed (Priority: P1)

**Goal**: Users can filter the activity feed by event type using filter chips, narrowing the feed to only the events they care about.

**Independent Test**: Generate 50+ events across multiple types, use filter chips to select "Pipeline" only → verify only pipeline events shown. Select "Pipeline" + "Chore" → both types shown. Remove all filters → full feed restored.

### Implementation for User Story 2

- [ ] T020 [US2] Add event type filter chips UI to ActivityPage in solune/frontend/src/pages/ActivityPage.tsx

  > Filter bar at top of page with clickable chips for each event category: Pipeline, Chore, Agent, App, Tool, Webhook, Cleanup, Status Change. Use chip/badge styling consistent with existing UI (Tailwind classes). Multiple chips can be selected simultaneously. Visual indicator for active filters.
  > State: `selectedEventTypes: string[]` managed locally in ActivityPage. When changed, pass to `useActivityFeed(projectId, selectedEventTypes)`.
  > Clear-all button to reset filters. Filtered empty state: "No {type} events found" (distinct from generic empty state per spec edge case).

- [ ] T021 [US2] Ensure useActivityFeed passes event_type filter through to API in solune/frontend/src/hooks/useActivityFeed.ts

  > Verify that when `eventTypes` changes, the query key includes the new filter, triggering a fresh fetch. TanStack Query handles cache invalidation via query key change automatically.
  > Map UI category names to API event_type values: Pipeline → "pipeline_run,pipeline_stage", Chore → "chore_trigger,chore_crud", Agent → "agent_crud,agent_execution", App → "app_crud", Tool → "tool_crud", Webhook → "webhook", Cleanup → "cleanup", Status Change → "status_change".

**Checkpoint**: At this point, User Stories 1 AND 2 are both functional. The Activity page supports type-based filtering.

---

## Phase 5: User Story 3 — Paginated Activity Feed with Infinite Scroll (Priority: P1)

**Goal**: The activity feed loads efficiently using cursor-based pagination and infinite scroll, handling large event volumes without performance degradation.

**Independent Test**: Generate 100+ events, load Activity page → verify only first 50 appear. Scroll to bottom → next 50 load automatically. Continue scrolling → all events eventually load. Verify no duplicated or skipped events. Verify "end of activity" indicator when all events loaded.

### Implementation for User Story 3

- [ ] T022 [US3] Verify InfiniteScrollContainer integration and end-of-activity indicator in solune/frontend/src/pages/ActivityPage.tsx

  > Ensure ActivityPage wraps the event list in `InfiniteScrollContainer` with props: `hasNextPage`, `isFetchingNextPage`, `fetchNextPage`, `isError` from the `useActivityFeed` hook.
  > Add "end of activity" indicator when `hasNextPage === false` and events exist (e.g., "You've reached the end of the activity log" with a subtle divider). This is distinct from the empty state (no events at all).
  > Verify that the default page size is 50 events (passed as `limit` to useInfiniteList).

- [ ] T023 [US3] Verify cursor-based pagination consistency in solune/backend/src/api/activity.py

  > Ensure compound cursor `(created_at, id)` produces stable ordering when events share timestamps. Verify that `next_cursor` is base64-encoded `timestamp|id` string and decoded correctly. Confirm no duplicated or skipped events across pages by testing with concurrent inserts.
  > See research.md § 2 for cursor encoding design.

**Checkpoint**: All three P1 stories are now complete. The Activity page is fully functional with event timeline, filtering, and infinite scroll pagination.

---

## Phase 6: User Story 4 — Entity-Scoped Activity History (Priority: P2)

**Goal**: Users can view activity history for a specific entity (pipeline, chore, agent, app, tool) directly from that entity's detail view, showing only events related to that entity.

**Independent Test**: Perform multiple actions on a single pipeline (create, run 3 times with different outcomes), open the pipeline detail view → verify history section shows only events for that pipeline. Open a chore with no history → verify "no activity recorded" message.

### Implementation for User Story 4

- [ ] T024 [US4] Create useEntityHistory hook in solune/frontend/src/hooks/useEntityHistory.ts

  > Wraps `useInfiniteList<ActivityEvent>` with query key `['activity', 'entity', entityType, entityId]`. Calls `api.activity.entityHistory(entityType, entityId, { limit, cursor })`. `staleTime: 30_000`. `enabled: !!entityType && !!entityId`.
  > Returns same shape as `useActivityFeed` for consistent consumption.

- [ ] T025 [P] [US4] Add collapsible History section to pipeline detail view in solune/frontend/src/components/pipeline/PipelineBoard.tsx

  > Add a collapsible "History" panel/section (using a disclosure/accordion pattern) that calls `useEntityHistory('pipeline', pipelineId)` and renders a mini-timeline of events. Each event shows: action icon, summary, relative timestamp. Click to expand detail. Empty state when no history. The panel should not disrupt the existing pipeline editor layout.
  > Alternative location: solune/frontend/src/pages/AgentsPipelinePage.tsx if the panel is better placed at page level.

- [ ] T026 [P] [US4] Add collapsible History section to chore detail view in solune/frontend/src/components/chores/ChoreInlineEditor.tsx

  > Same pattern as T025 but with `useEntityHistory('chore', choreId)`. Collapsible "History" section showing chore-related events (triggers, CRUD operations).

- [ ] T027 [P] [US4] Add collapsible History section to agent detail view in solune/frontend/src/components/agents/AgentInlineEditor.tsx

  > Same pattern as T025 but with `useEntityHistory('agent', agentId)`. Collapsible "History" section showing agent-related events (CRUD, executions).

- [ ] T028 [P] [US4] Add collapsible History section to app detail view in solune/frontend/src/components/apps/AppDetailView.tsx

  > Same pattern as T025 but with `useEntityHistory('app', appId)`. Collapsible "History" section showing app-related events (CRUD, start/stop).

- [ ] T029 [P] [US4] Add collapsible History section to tool detail view in solune/frontend/src/components/agents/ToolsEditor.tsx

  > Same pattern as T025 but with `useEntityHistory('tool', toolId)`. Collapsible "History" section showing tool-related events (CRUD).

**Checkpoint**: At this point, User Story 4 is complete. Entity detail views show scoped activity history.

---

## Phase 7: User Story 5 — Notification Bell with Real Activity (Priority: P2)

**Goal**: The existing placeholder notification bell is wired to real activity data, showing high-signal events (pipeline completions/failures, chore triggers, agent executions) as notifications with unread tracking.

**Independent Test**: Trigger a pipeline failure and a chore execution, click the notification bell → both events appear as notifications with summaries and timestamps. Verify unread badge shows count. Mark as read → badge decreases. Click "View all" → navigates to /activity page.

### Implementation for User Story 5

- [ ] T030 [US5] Replace empty placeholder with real activity feed query in solune/frontend/src/hooks/useNotifications.ts

  > Query `api.activity.feed(projectId, { limit: 20, event_type: 'pipeline_run,chore_trigger,agent_execution' })` for recent high-signal events.
  > Map `ActivityEvent` → existing `Notification` type: `event.id` → `id`, `event.event_type` → `type` (map pipeline_run/agent_* to 'agent', chore_* to 'chore'), `event.summary` → `title`, `event.created_at` → `timestamp`, `readIds.has(event.id)` → `read`, `event.entity_type` → `source`.
  > Keep existing localStorage read tracking pattern (key: `'solune-read-notifications'`).
  > Use `staleTime: 30_000` consistent with activity feed polling.
  > See data-model.md § Notification mapping for field mapping reference.

- [ ] T031 [US5] Add "View all" link navigating to /activity in notification bell dropdown in solune/frontend/src/layout/NotificationBell.tsx

  > Add a "View all" link at the bottom of the notification dropdown that navigates to `/activity` using React Router's `useNavigate` or a `<Link>` component. Style consistently with existing dropdown footer patterns.

**Checkpoint**: At this point, User Story 5 is complete. The notification bell surfaces real high-signal events.

---

## Phase 8: User Story 6 — Pipeline Run History Panel (Priority: P3)

**Goal**: Users can view past pipeline runs with status badges, durations, and stage breakdowns directly from the pipeline editor view, without navigating to the Activity page.

**Independent Test**: Run a pipeline 3 times (one success, one failure, one cancelled), open the pipeline editor → verify a "Run History" tab shows all 3 runs with status badges, durations, and timestamps. Click a run → stage breakdown visible. Empty state for pipelines with no runs.

### Implementation for User Story 6

- [ ] T032 [US6] Add pipelinesApi.listRuns() and pipelinesApi.getRun() methods in solune/frontend/src/services/api.ts

  > `pipelinesApi.listRuns(projectId, pipelineId)` → `GET /{pipeline_id}/runs` (backend endpoints already exist).
  > `pipelinesApi.getRun(projectId, pipelineId, runId)` → `GET /{pipeline_id}/runs/{run_id}` (backend endpoint already exists).
  > Add corresponding TypeScript types for PipelineRun and PipelineStageState if not already present in types/index.ts.

- [ ] T033 [US6] Create PipelineRunHistory component in solune/frontend/src/components/pipeline/PipelineRunHistory.tsx

  > Displays a list of past runs with: status badge (completed=green, failed=red, cancelled=yellow), duration (formatted), timestamp (relative).
  > Click a run → expand to show stage-by-stage breakdown with individual stage statuses and durations.
  > Empty state: "No runs recorded yet" for pipelines with no history.
  > Uses a custom hook or direct `useQuery` to fetch run data via `pipelinesApi.listRuns()`.

- [ ] T034 [US6] Add "Run History" tab/panel to pipeline editor view in solune/frontend/src/pages/AgentsPipelinePage.tsx

  > Add a "Run History" tab or collapsible panel in the pipeline editor page that renders the `PipelineRunHistory` component. Pass the current `pipelineId` and `projectId` as props.
  > Integrate alongside existing pipeline editor components (PipelineBoard, PipelineToolbar, PipelineAnalytics).

**Checkpoint**: All user stories (US1–US6) are now complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Regression checks and performance validation across all stories

- [ ] T035 [P] Run backend validation (ruff check, pyright, pytest) to confirm no regressions in solune/backend/
- [ ] T036 [P] Run frontend validation (ESLint, tsc, vitest) to confirm no regressions in solune/frontend/
- [ ] T037 Verify activity feed query performance with EXPLAIN QUERY PLAN on indexed query against 10K rows
- [ ] T038 Run quickstart.md verification checklist end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration must exist) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — foundational models, service, API, types, and client must exist
- **User Story 2 (Phase 4)**: Depends on Phase 3 — Activity page must exist to add filters
- **User Story 3 (Phase 5)**: Depends on Phase 3 — Activity page must exist to add infinite scroll
- **User Story 4 (Phase 6)**: Depends on Phase 2 — only needs foundational API and types
- **User Story 5 (Phase 7)**: Depends on Phase 2 — only needs foundational API and types
- **User Story 6 (Phase 8)**: Depends on Phase 2 — uses existing backend endpoints, needs frontend API client
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (Activity page must exist to add filter chips)
- **User Story 3 (P1)**: Depends on US1 (Activity page must exist to verify scroll integration)
- **User Story 4 (P2)**: Can start after Phase 2 — independent of US1/US2/US3 (uses entity history API directly)
- **User Story 5 (P2)**: Can start after Phase 2 — independent of US1/US2/US3 (uses activity feed API directly)
- **User Story 6 (P3)**: Can start after Phase 2 — independent (uses existing backend pipeline run endpoints)

### Within Each User Story

- Backend instrumentation tasks (T008–T015) are all parallel — different files, no dependencies
- Frontend: Hook before Page, Page before Route
- Models/types before services/hooks
- Services before API endpoints

### Parallel Opportunities

- All Foundational tasks marked [P] can run in parallel (T003, T006 with T002/T004/T005/T007)
- All backend instrumentation tasks (T008–T015) can run in parallel — each modifies a different file
- US4 entity history panels (T025–T029) can all run in parallel — each modifies a different component
- US4, US5, US6 can all start in parallel after Phase 2 (independent of each other)

---

## Parallel Example: User Story 1

```bash
# Launch all backend instrumentation tasks in parallel (different files):
Task T008: "Add log_event() calls for pipeline runs in api/pipelines.py"
Task T009: "Add log_event() calls for workflow transitions in orchestrator.py"
Task T010: "Add log_event() calls for chore triggers/CRUD in api/chores.py"
Task T011: "Add log_event() calls for agent CRUD in api/agents.py"
Task T012: "Add log_event() calls for app CRUD in api/apps.py"
Task T013: "Add log_event() calls for tool CRUD in api/tools.py"
Task T014: "Add log_event() calls for webhook events in api/webhooks.py"
Task T015: "Add log_event() calls for cleanup operations in api/cleanup.py"
```

## Parallel Example: User Story 4

```bash
# Launch all entity history panel tasks in parallel (different components):
Task T025: "Add History section to PipelineBoard.tsx"
Task T026: "Add History section to ChoreInlineEditor.tsx"
Task T027: "Add History section to AgentInlineEditor.tsx"
Task T028: "Add History section to AppDetailView.tsx"
Task T029: "Add History section to ToolsEditor.tsx"
```

## Parallel Example: P2 Stories

```bash
# Launch all P2 stories in parallel after Phase 2 (independent of each other):
Phase 6: User Story 4 (Entity-Scoped History)
Phase 7: User Story 5 (Notification Bell)
Phase 8: User Story 6 (Pipeline Run History)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration)
2. Complete Phase 2: Foundational (models, service, API, types, client)
3. Complete Phase 3: User Story 1 (instrumentation + Activity page)
4. **STOP and VALIDATE**: Test User Story 1 independently — all events appear in the feed with correct summaries
5. Deploy/demo if ready — the Activity page is the core deliverable

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 → Test filtering → Deploy/Demo
4. Add User Story 3 → Test infinite scroll → Deploy/Demo
5. Add User Stories 4, 5, 6 (in parallel or sequential) → Test each → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend instrumentation)
   - Developer B: User Story 1 (frontend page) — after hook is ready
3. After US1:
   - Developer A: User Story 2 (filters) + User Story 3 (pagination)
   - Developer B: User Story 5 (notification bell)
   - Developer C: User Story 4 (entity history panels)
   - Developer D: User Story 6 (pipeline run history)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All file paths are relative to repository root
- Backend paths: `solune/backend/src/`
- Frontend paths: `solune/frontend/src/`
