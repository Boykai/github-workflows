# Tasks: Phase 8 Feature Enhancements — Polling, UX, Board Projection, Concurrency, Collision Fix, Undo/Redo

**Input**: Design documents from `/specs/001-phase8-enhancements/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- Backend tests: `solune/backend/tests/unit/`
- Frontend tests: `solune/frontend/src/` (co-located with Vitest)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migrations, model extensions, and icon setup shared across multiple user stories

- [ ] T001 Create database migration for `pipeline_states` table extensions (`concurrent_group_id TEXT`, `is_isolated INTEGER DEFAULT 1`, `recovered_at TEXT`) in `solune/backend/src/migrations/` (next sequential migration file)
- [ ] T002 [P] Create database migration for `mcp_configurations` version column (`version INTEGER NOT NULL DEFAULT 1`) in `solune/backend/src/migrations/` (next sequential migration file)
- [ ] T003 [P] Create database migration for new `collision_events` table in `solune/backend/src/migrations/` (next sequential migration file, schema per data-model.md)
- [ ] T004 [P] Create database migration for new `recovery_log` table in `solune/backend/src/migrations/` (next sequential migration file, schema per data-model.md)
- [ ] T005 [P] Add new Lucide icons (Filter, Undo2, Redo2, Activity, Loader) to frontend barrel file in `solune/frontend/src/lib/icons.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model extensions and constants that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Add adaptive polling interval constants and tier configuration (`POLLING_TIER_HIGH`, `POLLING_TIER_MEDIUM`, `POLLING_TIER_LOW`, `POLLING_TIER_BACKOFF`, thresholds, and window size defaults) to `solune/backend/src/services/copilot_polling/state.py`
- [ ] T007 [P] Extend `PipelineState` dataclass with `execution_mode`, `concurrent_group_id`, `is_isolated`, and `recovered_at` fields in `solune/backend/src/services/workflow_orchestrator/models.py`
- [ ] T008 [P] Add `CollisionOperation` and `CollisionEvent` dataclass models to `solune/backend/src/models/mcp.py` (fields per data-model.md and collision-api.yaml contract)
- [ ] T009 [P] Add `RecoveryState` and `RecoveryReport` dataclasses to `solune/backend/src/services/copilot_polling/recovery.py` (fields per data-model.md and recovery-api.yaml contract)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Adaptive Polling (Priority: P1) 🎯 MVP

**Goal**: Polling frequency dynamically adapts to board activity — fast during active periods, slow during idle, with exponential backoff on failure and tab-visibility awareness.

**Independent Test**: Open a board, observe network tab — polling interval should shorten when items change and lengthen during idle periods. Background the tab and return — an immediate poll should fire.

### Implementation for User Story 1

- [ ] T010 [US1] Add activity tracking logic (sliding window `changes_detected` counter, activity score computation, tier transition logic) to the poll tick in `solune/backend/src/services/copilot_polling/polling_loop.py`
- [ ] T011 [P] [US1] Create `useAdaptivePolling` hook implementing `AdaptivePollingConfig`, `AdaptivePollingState`, and `UseAdaptivePollingReturn` interfaces in `solune/frontend/src/hooks/useAdaptivePolling.ts` (contract per polling-api.yaml)
- [ ] T012 [US1] Integrate `useAdaptivePolling` into `useProjectBoard` hook — pass dynamic `getRefetchInterval` to TanStack Query's `refetchInterval` option, wire `reportPollResult` and `reportPollFailure` callbacks in `solune/frontend/src/hooks/useProjectBoard.ts`
- [ ] T013 [US1] Add tab visibility handling (`document.visibilitychange` event listener) with immediate poll on tab focus and polling pause when hidden in `solune/frontend/src/hooks/useAdaptivePolling.ts`
- [ ] T014 [P] [US1] Extend `useBoardRefresh` hook to use adaptive polling state for refresh indicators (show activity tier badge or polling status) in `solune/frontend/src/hooks/useBoardRefresh.ts`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Board polling adapts to activity, backs off on errors, and pauses/resumes on tab visibility changes.

---

## Phase 4: User Story 2 — Concurrent Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Independent pipelines execute concurrently via `task_registry` when queue-mode is disabled, with fault isolation so one failure doesn't cancel siblings. Sequential behavior preserved when queue-mode is enabled.

**Independent Test**: Trigger two independent pipelines for the same project — both should start concurrently (check backend logs for overlapping timestamps). Enable queue-mode — pipelines should serialize.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `dispatch_pipelines()` function with queue-mode gate in `solune/backend/src/services/workflow_orchestrator/orchestrator.py` — check `is_queue_mode_enabled()`, dispatch concurrently via `task_registry` when off, sequentially when on
- [ ] T016 [P] [US2] Extend `pipeline_state_store.py` to read/write `concurrent_group_id`, `is_isolated`, and `execution_mode` fields in `solune/backend/src/services/pipeline_state_store.py`
- [ ] T017 [US2] Implement `execute_pipeline_concurrent()` with fault isolation (`try/except` per pipeline, failures do not propagate to siblings) in `solune/backend/src/services/copilot_polling/pipeline.py`
- [ ] T018 [US2] Extend `GET /api/v1/projects/{project_id}/pipelines` response to include `execution_mode`, `concurrent_group_id`, and `is_isolated` fields in `solune/backend/src/api/pipelines.py`
- [ ] T019 [P] [US2] Add `concurrent_group_id` generation (UUID) and group linking logic for sibling pipelines in `solune/backend/src/services/workflow_orchestrator/orchestrator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Concurrent pipelines execute in parallel with fault isolation.

---

## Phase 5: User Story 3 — Board Projection with Lazy Loading (Priority: P2)

**Goal**: Large boards (500+ items) render initial visible items within 2 seconds using intersection observer-based lazy loading. Full dataset remains in TanStack Query cache for client-side filtering.

**Independent Test**: Load a board with 500+ items — initial render should show only visible items (check DOM node count). Scroll down — additional items appear within 500ms per batch.

### Implementation for User Story 3

- [ ] T020 [US3] Create `useBoardProjection` hook implementing `BoardProjectionConfig`, `ColumnProjection`, and `UseBoardProjectionReturn` interfaces with intersection observer logic in `solune/frontend/src/hooks/useBoardProjection.ts` (contract per board-api.yaml)
- [ ] T021 [US3] Integrate `useBoardProjection` into `ProjectBoard.tsx` — pass projected items to columns, use `observerRef` for scroll-triggered loading in `solune/frontend/src/components/board/ProjectBoard.tsx`
- [ ] T022 [US3] Add intersection observer ref attachment and projected item rendering to `BoardColumn.tsx` — render only items within `renderedRange`, show placeholder for off-screen items in `solune/frontend/src/components/board/BoardColumn.tsx`
- [ ] T023 [P] [US3] Add scroll debouncing (150ms default) to intersection observer callbacks in `useBoardProjection` to handle rapid scrolling in `solune/frontend/src/hooks/useBoardProjection.ts`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. Large boards render fast with lazy loading.

---

## Phase 6: User Story 4 — Pipeline Config Filter in Board Toolbar (Priority: P2)

**Goal**: Board toolbar includes a pipeline config filter dropdown for client-side filtering by pipeline. Selecting a pipeline shows only associated items. Filter persists across polling updates.

**Independent Test**: Open a board with multiple pipelines — use the dropdown to select a specific pipeline — only matching items should appear. Select "All Pipelines" to restore all items.

### Implementation for User Story 4

- [ ] T024 [US4] Add `pipelineConfigId: string | null` field and `setPipelineConfigFilter` handler to `BoardFilterState` in `solune/frontend/src/hooks/useBoardControls.ts`
- [ ] T025 [US4] Implement client-side filtering logic — filter board items by `pipelineConfigId` when set (null = "All Pipelines") and derive `availablePipelineConfigs` from board data in `solune/frontend/src/hooks/useBoardControls.ts`
- [ ] T026 [US4] Add pipeline config filter dropdown UI (Radix UI `Select` component with "All Pipelines" default + pipeline config options with item counts) to `solune/frontend/src/components/board/BoardToolbar.tsx`

**Checkpoint**: At this point, User Stories 1–4 should all work independently. Pipeline filtering works client-side with no backend changes.

---

## Phase 7: User Story 5 — Label-Driven State Recovery (Priority: P2)

**Goal**: On startup, when internal pipeline state is unavailable or corrupted, the system reconstructs state from `solune:pipeline:*` labels on board items. Ambiguous items are flagged for manual review. Recovered items skip re-processing.

**Independent Test**: Clear the pipeline state database, restart the backend — check logs for a recovery report showing reconstructed states. Verify recovered items are not re-processed by the polling pipeline.

### Implementation for User Story 5

- [ ] T027 [US5] Extend `label_manager.py` with `batch_parse_pipeline_labels()` function for parsing all `solune:pipeline:*` labels on a list of items in `solune/backend/src/services/copilot_polling/label_manager.py`
- [ ] T028 [US5] Implement `recover_single_item_state()` function to reconstruct `RecoveryState` from parsed labels with confidence scoring and ambiguity detection in `solune/backend/src/services/copilot_polling/recovery.py`
- [ ] T029 [US5] Implement `recover_pipeline_states_from_labels()` function orchestrating full project-level recovery: list items, parse labels, reconstruct states, handle ambiguities, populate state store in `solune/backend/src/services/copilot_polling/recovery.py`
- [ ] T030 [US5] Add `recovered_at` timestamp handling to `pipeline_state_store.py` — set on recovered states, check in polling pipeline to skip re-processing in `solune/backend/src/services/pipeline_state_store.py`
- [ ] T031 [US5] Wire recovery into startup — call `recover_pipeline_states_from_labels()` when `init_pipeline_state_store()` detects empty or corrupt state, use `get_dispatcher()` for alerts in `solune/backend/src/services/pipeline_state_store.py`
- [ ] T032 [P] [US5] Add recovery event logging to `recovery_log` table (persist `RecoveryState` entries for auditability) in `solune/backend/src/services/copilot_polling/recovery.py`

**Checkpoint**: At this point, User Stories 1–5 should all work independently. The system self-heals from state loss using label-based recovery.

---

## Phase 8: User Story 6 — MCP Collision Resolution (Priority: P3)

**Goal**: Concurrent MCP operations targeting the same entity are detected via optimistic concurrency control (version field). Resolution follows user-priority > last-write-wins > manual-review strategy. All collisions are logged.

**Independent Test**: Trigger two concurrent MCP updates on the same entity — verify collision is detected, resolved with correct strategy, and logged to `collision_events` table.

### Implementation for User Story 6

- [ ] T033 [US6] Create `collision_resolver.py` service with `detect_collision()`, `resolve_collision()`, and `log_collision_event()` functions implementing resolution priority (user > automation, last-write-wins, manual review fallback) in `solune/backend/src/services/collision_resolver.py`
- [ ] T034 [US6] Add version field and optimistic concurrency check to `update_mcp_configuration()` in `solune/backend/src/services/mcp_store.py` — increment version on write, detect version mismatch, call `detect_collision()`
- [ ] T035 [US6] Add `expected_version` parameter to MCP update API endpoint and return collision summary in response when collision is detected in `solune/backend/src/api/mcp.py`
- [ ] T036 [P] [US6] Add collision event persistence to `collision_events` table (insert collision records, query for audit) in `solune/backend/src/services/collision_resolver.py`

**Checkpoint**: At this point, User Stories 1–6 should all work independently. Concurrent MCP operations are safe with deterministic collision resolution.

---

## Phase 9: User Story 7 — Undo/Redo for Destructive Actions (Priority: P3)

**Goal**: Session-scoped undo/redo for destructive board actions (archive, delete, label removal). Configurable time window (default 30s). Toast notifications with "Undo" button. Keyboard shortcuts Ctrl+Z / Ctrl+Shift+Z.

**Independent Test**: Archive a board item → click "Undo" toast → item is restored → press Ctrl+Shift+Z → item is archived again. Wait for undo window to expire → undo is no longer available.

### Implementation for User Story 7

- [ ] T037 [US7] Create `UndoRedoContext.tsx` with `UndoRedoProvider` component implementing `UndoRedoContextValue` interface — undo/redo stacks, pushAction, expiry timer, stack clearing on new action in `solune/frontend/src/context/UndoRedoContext.tsx`
- [ ] T038 [US7] Create `useUndoRedo` hook wrapping `UndoRedoContext` with convenience methods (`undo`, `redo`, `canUndo`, `canRedo`, `nextUndoDescription`, `nextRedoDescription`) in `solune/frontend/src/hooks/useUndoRedo.ts`
- [ ] T039 [US7] Wrap `ProjectBoardContent` with `UndoRedoProvider` and wire destructive actions (archive, delete, label removal) to call `pushAction` with state snapshots in `solune/frontend/src/components/board/ProjectBoardContent.tsx`
- [ ] T040 [US7] Add undo toast notification using `sonner` — display toast with "Undo" button and countdown timer on destructive actions in `solune/frontend/src/components/board/ProjectBoardContent.tsx`
- [ ] T041 [P] [US7] Add keyboard shortcut handler (Ctrl+Z for undo, Ctrl+Shift+Z for redo) as a global keydown listener inside `UndoRedoProvider` in `solune/frontend/src/context/UndoRedoContext.tsx`
- [ ] T042 [US7] Add undo window expiry logic — remove expired entries from undo stack, show "undo window expired" notification with recovery guidance in `solune/frontend/src/context/UndoRedoContext.tsx`

**Checkpoint**: All user stories (1–7) should now be independently functional. Users can undo/redo destructive actions with visual feedback.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories — documentation, validation, and integration hardening

- [ ] T043 [P] Update `solune/docs/` with documentation for adaptive polling configuration, concurrent pipeline behavior, and undo/redo usage
- [ ] T044 Code cleanup — ensure all new modules have consistent docstrings and follow existing code conventions across `solune/backend/src/` and `solune/frontend/src/`
- [ ] T045 [P] Performance validation — verify board initial render ≤2s for 500 items (SC-003), scroll batch load ≤500ms (FR-008), poll updates visible within 5s (SC-001)
- [ ] T046 [P] Run quickstart.md validation — execute all setup and verification steps from `specs/001-phase8-enhancements/quickstart.md`
- [ ] T047 Integration validation — verify polling + lazy loading + pipeline filter work together without regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–9)**: All depend on Foundational phase completion
  - Tier 1 stories (US-1, US-4) can start immediately after Foundational
  - Tier 2 stories (US-2, US-3, US-5) can start after Foundational (US-2 benefits from US-1 polling)
  - Tier 3 stories (US-6, US-7) can start after Foundational (US-6 benefits from US-2 concurrency)
  - All stories are independently implementable and testable
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Benefits from US-1 polling awareness but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) — Benefits from US-2 concurrency but independently testable
- **User Story 7 (P3)**: Can start after Foundational (Phase 2) — No dependencies on other stories

### Within Each User Story

- Models/constants before services
- Services before API endpoints
- Backend before frontend integration (where both exist)
- Core implementation before integration with other hooks
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks T002–T005 marked [P] can run in parallel with T001
- All Foundational tasks T007–T009 marked [P] can run in parallel with T006
- Once Foundational phase completes, all Tier 1 user stories (US-1, US-4) can start in parallel
- Within US-1: T011 and T014 can run in parallel (different files)
- Within US-2: T016 and T019 can run in parallel (different files)
- Within US-3: T023 can run in parallel with T020–T022
- Within US-7: T041 can run in parallel with T039–T040
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch parallelizable tasks for User Story 1 together:
Task: T011 "Create useAdaptivePolling hook in solune/frontend/src/hooks/useAdaptivePolling.ts"
Task: T014 "Extend useBoardRefresh for adaptive polling status in solune/frontend/src/hooks/useBoardRefresh.ts"

# Then sequential tasks:
Task: T010 "Add activity tracking to polling_loop.py" (backend, no frontend deps)
Task: T012 "Integrate adaptive polling into useProjectBoard.ts" (depends on T011)
Task: T013 "Add tab visibility handling" (extends T011)
```

## Parallel Example: User Story 2

```bash
# Launch parallelizable tasks for User Story 2 together:
Task: T016 "Extend pipeline_state_store.py for concurrent fields"
Task: T019 "Add concurrent_group_id generation to orchestrator.py"

# Then sequential tasks:
Task: T015 "Implement dispatch_pipelines() with queue-mode gate" (depends on T016)
Task: T017 "Implement execute_pipeline_concurrent() with fault isolation" (depends on T015)
Task: T018 "Extend pipelines API response" (depends on T017)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (database migrations, icons)
2. Complete Phase 2: Foundational (model extensions, constants)
3. Complete Phase 3: User Story 1 — Adaptive Polling
4. Complete Phase 4: User Story 2 — Concurrent Pipelines
5. **STOP and VALIDATE**: Test US-1 and US-2 independently
6. Deploy/demo if ready — users get adaptive polling and concurrent pipelines

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Adaptive Polling) → Test independently → Deploy/Demo (MVP Tier 1!)
3. Add User Story 4 (Pipeline Filter) → Test independently → Deploy/Demo (MVP Tier 1 complete!)
4. Add User Story 2 (Concurrent Pipelines) → Test independently → Deploy/Demo
5. Add User Story 3 (Board Projection) → Test independently → Deploy/Demo
6. Add User Story 5 (Label Recovery) → Test independently → Deploy/Demo (Tier 2 complete!)
7. Add User Story 6 (Collision Resolution) → Test independently → Deploy/Demo
8. Add User Story 7 (Undo/Redo) → Test independently → Deploy/Demo (Tier 3 complete!)
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Adaptive Polling) → then US-2 (Concurrent Pipelines)
   - Developer B: User Story 4 (Pipeline Filter) → then US-3 (Board Projection)
   - Developer C: User Story 5 (Label Recovery) → then US-6 (Collision Resolution)
   - Developer D: User Story 7 (Undo/Redo)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Use `task_registry.task_registry` for all fire-and-forget async tasks (codebase convention)
- Import Lucide icons from `@/lib/icons` barrel file only (ESLint enforced)
- Use `get_dispatcher()` for alert dispatch (avoid circular imports)
- Patch source module paths when mocking function-level imports in tests
- `is_queue_mode_enabled()` has 10s TTL cache — eventual consistency is intentional
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
