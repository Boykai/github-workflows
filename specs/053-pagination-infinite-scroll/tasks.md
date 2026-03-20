# Tasks: Pagination & Infinite Scroll for All List Views

**Input**: Design documents from `/specs/053-pagination-infinite-scroll/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included where the plan explicitly calls for them (backend pagination utility tests). Frontend tests follow existing project patterns but are not the primary deliverable.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`

---

## Phase 1: Setup (Backend Pagination Foundation)

**Purpose**: Create the shared backend pagination model and utility that all endpoints depend on

- [ ] T001 Create `PaginatedResponse[T]` generic Pydantic model with `items`, `next_cursor`, `has_more`, `total_count` fields in solune/backend/src/models/pagination.py
- [ ] T002 Create `PaginationParams` Pydantic model with `limit` (1–100, default 25) and `cursor` (optional base64 string) validation in solune/backend/src/models/pagination.py
- [ ] T003 Implement `apply_pagination()` helper that accepts a list, `limit`, and `cursor`, decodes base64 cursor to find start position, slices the list, and returns a `PaginatedResponse` in solune/backend/src/services/pagination.py
- [ ] T004 Add unit tests for pagination utility covering empty list, list smaller than limit, list equal to limit, list larger than limit, cursor navigation, and invalid cursor handling in solune/backend/tests/unit/test_pagination.py

**⚠️ GATE**: All pagination utility tests pass (`pytest tests/unit/test_pagination.py`) before proceeding to Phase 2.

---

## Phase 2: Foundational (Frontend Shared Infrastructure)

**Purpose**: Create the shared frontend types, hooks, and components that ALL list view migrations depend on

**⚠️ CRITICAL**: No user story frontend work can begin until this phase is complete

- [ ] T005 Add `PaginatedResponse<T>` TypeScript interface with `items`, `next_cursor`, `has_more`, `total_count` fields to solune/frontend/src/types/index.ts
- [ ] T006 [P] Create `useInfiniteList<T>` hook wrapping `useInfiniteQuery` with shared defaults (`getNextPageParam` extracting `next_cursor`, `initialPageParam`, configurable `limit`/`staleTime`/`enabled`) in solune/frontend/src/hooks/useInfiniteList.ts
- [ ] T007 [P] Create `InfiniteScrollContainer` component using `IntersectionObserver` to detect sentinel element visibility, trigger `fetchNextPage`, show loading spinner during fetch, show error with retry button on failure, and render nothing when all pages loaded in solune/frontend/src/components/common/InfiniteScrollContainer.tsx
- [ ] T008 [P] Add paginated fetch helpers to API service (each list API module gets a paginated variant accepting `limit` and `cursor` params, returning `PaginatedResponse<T>`) in solune/frontend/src/services/api.ts

**Checkpoint**: Foundation ready — `npx tsc --noEmit` passes, `npx eslint` clean. User story implementation can now begin.

---

## Phase 3: User Story 1 — Paginated Project Board (Priority: P1) 🎯 MVP

**Goal**: Each board column loads at most 25 issues initially, with infinite scroll to load more items per column independently

**Independent Test**: Create a project with 200+ issues across multiple columns, load the board, verify only an initial batch appears per column with a mechanism to load additional items. Verify drag-and-drop works across paginated columns.

### Implementation for User Story 1

- [ ] T009 [US1] Add `column_limit` (int, default 25) and `column_cursors` (JSON-encoded map of `{ status_option_id: cursor }`) query params to board data endpoint, apply `apply_pagination()` per column independently, and add `next_cursor`/`has_more` fields to each `BoardColumn` in response in solune/backend/src/api/board.py
- [ ] T010 [US1] Update `useProjectBoard` hook to accept and pass `column_limit` and `column_cursors` params to the board data endpoint, and expose per-column `fetchNextPage` capability in solune/frontend/src/hooks/useProjectBoard.ts
- [ ] T011 [US1] Add `InfiniteScrollContainer` sentinel inside each `BoardColumn` to trigger per-column next-page fetches, ensuring items append below existing content without disrupting scroll position in solune/frontend/src/components/board/BoardColumn.tsx
- [ ] T012 [US1] Verify `@dnd-kit` drag-and-drop interactions work correctly with paginated board columns — dragged items move between columns regardless of which page batch they belong to, and column counts update accurately in solune/frontend/src/components/board/BoardColumn.tsx

**Checkpoint**: Board columns display at most 25 items, scroll to load more per column, drag-and-drop functions correctly. User Story 1 is independently testable.

---

## Phase 4: User Story 2 — Paginated Agents Catalog (Priority: P1)

**Goal**: Agents page loads at most 24 agent cards initially with infinite scroll to load more

**Independent Test**: Populate 100+ agents, navigate to the agents page, verify only a subset loads initially with seamless scroll-to-load-more behavior.

### Implementation for User Story 2

- [ ] T013 [P] [US2] Add optional `limit` (int, default 25) and `cursor` (str) query params to agents list endpoint, fetch full agent list, pass to `apply_pagination()`, and return `PaginatedResponse[Agent]` (backward-compatible when params omitted) in solune/backend/src/api/agents.py
- [ ] T014 [US2] Migrate `useAgentsList` from `useQuery` to `useInfiniteList`, update fetch function to pass `limit` and `cursor` params, and flatten pages into a single items array for consumers in solune/frontend/src/hooks/useAgents.ts
- [ ] T015 [US2] Integrate `InfiniteScrollContainer` into `AgentsPage` to wrap the agent card grid, connecting `hasNextPage`, `isFetchingNextPage`, `fetchNextPage`, and `isError` props from the migrated hook in solune/frontend/src/pages/AgentsPage.tsx

**Checkpoint**: Agents page displays at most 24 agent cards, scrolling loads more agents seamlessly. User Story 2 is independently testable.

---

## Phase 5: User Story 3 — Paginated Tools List (Priority: P2)

**Goal**: Tools page loads at most 24 tools initially with infinite scroll to load more

**Independent Test**: Add 60+ tools to a project and verify the tools page loads an initial batch with scroll-to-load-more.

### Implementation for User Story 3

- [ ] T016 [P] [US3] Add optional `limit` (int, default 25) and `cursor` (str) query params to tools list endpoint, paginate the `tools` array within `McpToolConfigListResponse` (keeping `presets` unpaginated in every response), and return `PaginatedResponse[McpToolConfig]` in solune/backend/src/api/tools.py
- [ ] T017 [US3] Migrate `useToolsList` from `useQuery` to `useInfiniteList`, update fetch function to pass `limit` and `cursor` params in solune/frontend/src/hooks/useTools.ts
- [ ] T018 [US3] Integrate `InfiniteScrollContainer` into `ToolsPage` to wrap the tools list, showing loading indicator during fetch and handling the filtered results pagination in solune/frontend/src/pages/ToolsPage.tsx

**Checkpoint**: Tools page displays at most 24 tools, scrolling loads more. Filtered results also paginate correctly. User Story 3 is independently testable.

---

## Phase 6: User Story 4 — Paginated Chores List (Priority: P2)

**Goal**: Chores page loads at most 24 chores initially with infinite scroll to load more

**Independent Test**: Create 50+ chores and verify the chores page loads in batches with scroll-to-load-more.

### Implementation for User Story 4

- [ ] T019 [P] [US4] Add optional `limit` (int, default 25) and `cursor` (str) query params to chores list endpoint, pass to `apply_pagination()`, and return `PaginatedResponse[Chore]` in solune/backend/src/api/chores.py
- [ ] T020 [US4] Migrate `useChoresList` from `useQuery` to `useInfiniteList`, update fetch function to pass `limit` and `cursor` params in solune/frontend/src/hooks/useChores.ts
- [ ] T021 [US4] Integrate `InfiniteScrollContainer` into `ChoresPage` to wrap the chores grid in solune/frontend/src/pages/ChoresPage.tsx

**Checkpoint**: Chores page displays at most 24 chores, scrolling loads more. User Story 4 is independently testable.

---

## Phase 7: User Story 5 — Paginated Apps Gallery (Priority: P2)

**Goal**: Apps page loads at most 24 app cards initially with infinite scroll to load more

**Independent Test**: Have 50+ apps and verify the apps page loads an initial batch with scroll-to-load-more.

### Implementation for User Story 5

- [ ] T022 [P] [US5] Add optional `limit` (int, default 25) and `cursor` (str) query params to apps list endpoint, pass to `apply_pagination()`, and return `PaginatedResponse[App]` in solune/backend/src/api/apps.py
- [ ] T023 [US5] Migrate `useApps` from `useQuery` to `useInfiniteList`, update fetch function to pass `limit` and `cursor` params in solune/frontend/src/hooks/useApps.ts
- [ ] T024 [US5] Integrate `InfiniteScrollContainer` into `AppsPage` to wrap the apps card grid, handling filtered-by-status pagination in solune/frontend/src/pages/AppsPage.tsx

**Checkpoint**: Apps page displays at most 24 app cards, scrolling loads more. Filtered results also paginate. User Story 5 is independently testable.

---

## Phase 8: User Story 6 — Paginated Saved Pipelines List (Priority: P3)

**Goal**: Saved pipelines list loads at most 20 pipelines initially with infinite scroll to load more

**Independent Test**: Create 30+ saved pipelines and verify the list loads in batches with scroll-to-load-more.

### Implementation for User Story 6

- [ ] T025 [P] [US6] Add optional `limit` (int, default 20) and `cursor` (str) query params to pipelines list endpoint, pass to `apply_pagination()`, and return `PaginatedResponse[PipelineConfig]` in solune/backend/src/api/pipelines.py
- [ ] T026 [US6] Migrate pipeline listing to `useInfiniteList` in solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T027 [US6] Integrate `InfiniteScrollContainer` into saved pipelines list section in solune/frontend/src/pages/ProjectsPage.tsx

**Checkpoint**: Saved pipelines list displays at most 20 items, scrolling loads more. Deletion while paginated updates correctly. User Story 6 is independently testable.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, resilience, and quality improvements that affect multiple user stories

- [ ] T028 [P] Add debounce/dedup protection to `InfiniteScrollContainer` to prevent duplicate page requests on rapid scroll (leveraging IntersectionObserver's built-in debounce and adding guard for `isFetchingNextPage`) in solune/frontend/src/components/common/InfiniteScrollContainer.tsx
- [ ] T029 [P] Add retry UI for failed page loads — error state with retry button, preserving already-loaded data — in solune/frontend/src/components/common/InfiniteScrollContainer.tsx
- [ ] T030 Add filter/sort reset helper to `useInfiniteList` that calls `queryClient.resetQueries()` when filter or sort params change, resetting pagination to the first page in solune/frontend/src/hooks/useInfiniteList.ts
- [ ] T031 [P] Integrate filter/sort reset into paginated page components — call reset on filter/sort change in solune/frontend/src/pages/AgentsPage.tsx, solune/frontend/src/pages/ToolsPage.tsx, solune/frontend/src/pages/ChoresPage.tsx, and solune/frontend/src/pages/AppsPage.tsx
- [ ] T032 [P] Add query invalidation on create/delete mutations to re-fetch paginated data correctly in solune/frontend/src/hooks/useAgents.ts, solune/frontend/src/hooks/useTools.ts, solune/frontend/src/hooks/useChores.ts, solune/frontend/src/hooks/useApps.ts, and solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T033 Add scroll position preservation using `useRef`/`scrollTo` pattern in `InfiniteScrollContainer` to restore scroll offset when returning from detail views in solune/frontend/src/components/common/InfiniteScrollContainer.tsx
- [ ] T034 Run quickstart.md final verification suite — full backend tests, frontend tests, type-check, lint, and manual performance verification per specs/053-pagination-infinite-scroll/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Frontend types (T005) have no backend dependency; hooks/components (T006–T008) depend on T005. Phase 2 can start in parallel with Phase 1.
- **User Stories (Phases 3–8)**: Backend tasks within each story depend on Phase 1 completion. Frontend tasks depend on both Phase 1 (backend) and Phase 2 (frontend foundation).
- **Polish (Phase 9)**: Depends on all desired user story phases being complete

### User Story Dependencies

- **User Story 1 — Board (P1)**: Depends on Phase 1 + Phase 2. No dependencies on other stories. **MVP target.**
- **User Story 2 — Agents (P1)**: Depends on Phase 1 + Phase 2. No dependencies on other stories. Can run in parallel with US1.
- **User Story 3 — Tools (P2)**: Depends on Phase 1 + Phase 2. No dependencies on other stories. Can run in parallel with US1/US2.
- **User Story 4 — Chores (P2)**: Depends on Phase 1 + Phase 2. No dependencies on other stories. Can run in parallel with US1/US2/US3.
- **User Story 5 — Apps (P2)**: Depends on Phase 1 + Phase 2. No dependencies on other stories. Can run in parallel with US1–US4.
- **User Story 6 — Pipelines (P3)**: Depends on Phase 1 + Phase 2. No dependencies on other stories. Can run in parallel with US1–US5.

### Within Each User Story

- Backend endpoint modification first (needs `apply_pagination()` from Phase 1)
- Frontend hook migration second (needs `useInfiniteList` from Phase 2 + backend endpoint)
- Frontend page integration third (needs migrated hook)
- Story complete and independently testable before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 → T002 → T003 (sequential — model before helper before tests)
- **Phase 2**: T005 first, then T006/T007/T008 in parallel
- **Across stories**: All backend endpoint tasks (T009, T013, T016, T019, T022, T025) are independent once Phase 1 is done — can run in parallel
- **Across stories**: All frontend migrations are independent once Phase 2 + their backend task is done
- **Phase 9**: T028/T029 can run in parallel; T030/T031 can run in parallel

---

## Parallel Example: User Story 2 (Agents)

```text
# After Phase 1 + Phase 2 complete:

# Backend (can run in parallel with other story backends):
Task T013: Add pagination params to agents endpoint in solune/backend/src/api/agents.py

# Frontend (after T013 completes):
Task T014: Migrate useAgentsList to useInfiniteList in solune/frontend/src/hooks/useAgents.ts
Task T015: Integrate InfiniteScrollContainer in solune/frontend/src/pages/AgentsPage.tsx
```

## Parallel Example: All Backend Endpoints (after Phase 1)

```text
# All of these can run simultaneously — different files, no dependencies:
Task T009: Board endpoint pagination in solune/backend/src/api/board.py
Task T013: Agents endpoint pagination in solune/backend/src/api/agents.py
Task T016: Tools endpoint pagination in solune/backend/src/api/tools.py
Task T019: Chores endpoint pagination in solune/backend/src/api/chores.py
Task T022: Apps endpoint pagination in solune/backend/src/api/apps.py
Task T025: Pipelines endpoint pagination in solune/backend/src/api/pipelines.py
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 — both P1)

1. Complete Phase 1: Backend Pagination Foundation
2. Complete Phase 2: Frontend Shared Infrastructure
3. Complete Phase 3: User Story 1 — Paginated Project Board
4. Complete Phase 4: User Story 2 — Paginated Agents Catalog
5. **STOP and VALIDATE**: Test both P1 stories independently
6. Deploy/demo the two highest-impact views

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready
2. Add User Story 1 (Board) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Agents) → Test independently → Deploy/Demo
4. Add User Story 3 (Tools) → Test independently → Deploy/Demo
5. Add User Story 4 (Chores) → Test independently → Deploy/Demo
6. Add User Story 5 (Apps) → Test independently → Deploy/Demo
7. Add User Story 6 (Pipelines) → Test independently → Deploy/Demo
8. Phase 9: Polish & Cross-Cutting → Final verification
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + Phase 2 together (foundation)
2. Once foundation is done:
   - Developer A: User Story 1 (Board — P1) + User Story 3 (Tools — P2)
   - Developer B: User Story 2 (Agents — P1) + User Story 4 (Chores — P2)
   - Developer C: User Story 5 (Apps — P2) + User Story 6 (Pipelines — P3)
3. All backend endpoint tasks (T009, T013, T016, T019, T022, T025) can run simultaneously
4. Stories complete and integrate independently
5. Phase 9 polish after all stories merge

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Backend endpoints default to returning full list when pagination params omitted (backward-compatible)
- `IntersectionObserver` handles scroll debouncing natively — Phase 9 adds additional guards
- Cursor-based pagination prevents duplicate/skipped items across page boundaries (RT-001)
- TanStack Query cache preserves loaded pages across SPA navigation (RT-006)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
