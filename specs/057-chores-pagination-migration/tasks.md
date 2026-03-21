# Tasks: ChoresPanel Pagination Migration

**Input**: Design documents from `/specs/057-chores-pagination-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests ARE explicitly requested — the spec requires pytest tests for backend filter combinations + cursor behavior and Vitest tests for frontend hook with filter params in query key.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed — all infrastructure exists. This phase ensures the existing codebase is ready for modification and establishes the filter parameter types.

- [ ] T001 Define `ChoresFilterParams` TypeScript interface in `solune/frontend/src/hooks/useChores.ts` for filter/sort parameter typing used by hook and API layer
- [ ] T002 Verify `ChoresGrid.tsx` already accepts pagination props (`hasNextPage`, `isFetchingNextPage`, `fetchNextPage`) and wraps content in `InfiniteScrollContainer` in `solune/frontend/src/components/chores/ChoresGrid.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend filtering and sorting must be functional before frontend can consume filtered paginated data. The API contract changes are a prerequisite for all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add `status`, `schedule_type`, `search`, `sort`, and `order` query parameters to the `list_chores` endpoint signature in `solune/backend/src/api/chores.py`
- [ ] T004 Implement status filtering logic — filter chore list by `status` param (`active`, `paused`) before `apply_pagination()` in `solune/backend/src/api/chores.py`
- [ ] T005 Implement schedule_type filtering logic — filter chore list by `schedule_type` param (`time`, `count`, `unscheduled` for null) before `apply_pagination()` in `solune/backend/src/api/chores.py`
- [ ] T006 Implement search filtering logic — case-insensitive substring match on `name` and `template_path` before `apply_pagination()` in `solune/backend/src/api/chores.py`
- [ ] T007 Implement sort logic — support `name`, `updated_at`, `created_at`, `attention` sort fields with `asc`/`desc` order before `apply_pagination()` in `solune/backend/src/api/chores.py`
- [ ] T008 [P] Update `choresApi.listPaginated()` to accept optional filter params (`status`, `scheduleType`, `search`, `sort`, `order`) and append them to query string using `URLSearchParams` in `solune/frontend/src/services/api.ts`
- [ ] T009 Update `useChoresListPaginated()` to accept optional `filters` parameter (using `ChoresFilterParams` interface), include filter values in `queryKey` array, and spread filters into `queryFn` API call in `solune/frontend/src/hooks/useChores.ts`

**Checkpoint**: Backend accepts filter/sort params and returns correctly filtered+sorted paginated results. Frontend API layer and hook can forward filter params to backend. User story integration can now begin.

---

## Phase 3: User Story 1 — Paginated Chores Loading (Priority: P1) 🎯 MVP

**Goal**: ChoresPanel loads chores incrementally using cursor-based infinite scroll — initial load shows 25 chores, scrolling loads more batches.

**Independent Test**: Create a project with 50+ chores, open ChoresPanel, verify only 25 load initially with scroll indicator, scroll to load next batch.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Add pytest test: `GET /chores/{project_id}?limit=25` returns first 25 chores with `has_more=true` and valid `next_cursor` when project has 50+ chores in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T011 [P] [US1] Add pytest test: `GET /chores/{project_id}?limit=25&cursor=<next_cursor>` returns next page of chores correctly in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T012 [P] [US1] Add pytest test: `GET /chores/{project_id}?limit=25` returns all chores with `has_more=false` when project has fewer than 25 chores in `solune/backend/tests/unit/api/test_chores.py`

### Implementation for User Story 1

- [ ] T013 [US1] Switch `ChoresPanel.tsx` from `useChoresList()` to `useChoresListPaginated()` — destructure `allItems`, `isLoading`, `hasNextPage`, `isFetchingNextPage`, `fetchNextPage` from the hook in `solune/frontend/src/components/chores/ChoresPanel.tsx`
- [ ] T014 [US1] Pass pagination props (`hasNextPage`, `isFetchingNextPage`, `fetchNextPage`) to `ChoresGrid` component in `solune/frontend/src/components/chores/ChoresPanel.tsx`

**Checkpoint**: ChoresPanel loads 25 chores initially and scrolling loads more. No filters wired yet — default (unfiltered) paginated loading works.

---

## Phase 4: User Story 2 — Server-Side Filtering (Priority: P1)

**Goal**: Filter by status, schedule type, and search text — filters apply across ALL chores on the server, not just loaded pages.

**Independent Test**: Create 50+ chores with varying statuses, apply status filter, verify all matching chores are returned across all pages.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US2] Add pytest test: `GET /chores/{project_id}?limit=25&status=active` returns only active chores in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T016 [P] [US2] Add pytest test: `GET /chores/{project_id}?limit=25&schedule_type=time` returns only time-scheduled chores in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T017 [P] [US2] Add pytest test: `GET /chores/{project_id}?limit=25&schedule_type=unscheduled` returns only chores with null schedule_type in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T018 [P] [US2] Add pytest test: `GET /chores/{project_id}?limit=25&search=deploy` returns only chores matching search term in name or template_path in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T019 [P] [US2] Add pytest test: combined filters `status=active&schedule_type=time&search=deploy` returns intersection of all filter criteria in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T020 [P] [US2] Add pytest test: cursor pagination works correctly with active filters — second page respects same filters in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T021 [P] [US2] Add pytest test: `total_count` in paginated response reflects filtered count (not total chores) in `solune/backend/tests/unit/api/test_chores.py`

### Implementation for User Story 2

- [ ] T022 [US2] Pass filter state (`status`, `scheduleType`, `search`) from `ChoresPanel` component state as params to `useChoresListPaginated()` hook — map `statusFilter`, `scheduleFilter`, `deferredSearch` to hook filter params in `solune/frontend/src/components/chores/ChoresPanel.tsx`
- [ ] T023 [US2] Remove the client-side `filteredChores` `useMemo` block that previously applied status, schedule type, and search filters on the full chore list in `solune/frontend/src/components/chores/ChoresPanel.tsx`
- [ ] T024 [P] [US2] Add Vitest test: `useChoresListPaginated` includes filter params in query key — verify different filter values produce different query keys in `solune/frontend/tests/hooks/useChores.test.ts`
- [ ] T025 [P] [US2] Add Vitest test: `useChoresListPaginated` passes filter params to `choresApi.listPaginated()` call in `solune/frontend/tests/hooks/useChores.test.ts`

**Checkpoint**: Filtering by status, schedule type, and search works end-to-end — server returns only matching chores across all pages. Client-side filter logic is removed.

---

## Phase 5: User Story 3 — Server-Side Sorting (Priority: P2)

**Goal**: Sort chores by name, creation date, updated date, or attention score — sort applies globally on the server so paginated results are in correct global order.

**Independent Test**: Create 50+ chores, apply sort, verify first 25 are correctly ordered and subsequent pages continue the correct global sort order.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T026 [P] [US3] Add pytest test: `GET /chores/{project_id}?limit=25&sort=name&order=asc` returns chores sorted by name ascending in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T027 [P] [US3] Add pytest test: `GET /chores/{project_id}?limit=25&sort=updated_at&order=desc` returns chores sorted by updated_at descending in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T028 [P] [US3] Add pytest test: `GET /chores/{project_id}?limit=25&sort=attention&order=asc` returns chores sorted by attention score (0=active+no schedule, 1=has issue, 2=normal, 3=paused) in `solune/backend/tests/unit/api/test_chores.py`

### Implementation for User Story 3

- [ ] T029 [US3] Pass sort state (`sort`, `order`) from `ChoresPanel` component state as params to `useChoresListPaginated()` hook — map `sortMode` to hook sort params in `solune/frontend/src/components/chores/ChoresPanel.tsx`
- [ ] T030 [US3] Remove the client-side sort `useMemo` block that previously sorted the chore list on the client in `solune/frontend/src/components/chores/ChoresPanel.tsx`

**Checkpoint**: Sorting works end-to-end — server returns correctly sorted paginated results. Client-side sort logic is removed.

---

## Phase 6: User Story 4 — Filter and Sort State Reset on Change (Priority: P2)

**Goal**: Changing any filter or sort parameter resets pagination to page 1 and fetches fresh results — no stale data from previous criteria visible.

**Independent Test**: Load chores with a filter, scroll to page 3, change the filter, verify list resets to page 1 with fresh results.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T031 [P] [US4] Add Vitest test: changing a filter value in `useChoresListPaginated` produces a new query key, causing TanStack Query to discard old pages and refetch from page 1 in `solune/frontend/tests/hooks/useChores.test.ts`

### Implementation for User Story 4

- [ ] T032 [US4] Verify that filter/sort params are included in `queryKey` of `useChoresListPaginated` so TanStack Query automatically resets on param changes — confirm no manual `resetPagination()` or `useEffect` is needed in `solune/frontend/src/hooks/useChores.ts`
- [ ] T033 [US4] Verify `useDeferredValue` for search text is preserved in `ChoresPanel.tsx` — the deferred value becomes a filter param passed to the hook, naturally debouncing API calls in `solune/frontend/src/components/chores/ChoresPanel.tsx`

**Checkpoint**: Changing filters/sort resets pagination automatically. Search is debounced via `useDeferredValue`. No manual reset logic needed.

---

## Phase 7: User Story 5 — Cleanup of Non-Paginated Code Paths (Priority: P3)

**Goal**: Remove unused non-paginated chore fetching code to maintain a single, consistent approach to loading chores.

**Independent Test**: Search codebase for `useChoresList` (non-paginated) and `choresApi.list` — verify they are not imported or called anywhere.

### Implementation for User Story 5

- [ ] T034 [US5] Search codebase for all imports and usages of `useChoresList` (non-paginated variant) across all `.ts` and `.tsx` files to determine if it is used outside `ChoresPanel.tsx`
- [ ] T035 [US5] Search codebase for all imports and usages of `choresApi.list` (non-paginated variant) across all `.ts` and `.tsx` files to determine if it is used outside direct callers
- [ ] T036 [US5] If `useChoresList` is not used elsewhere: remove the `useChoresList` function from `solune/frontend/src/hooks/useChores.ts`
- [ ] T037 [US5] If `choresApi.list` is not used elsewhere: remove the `list` function from `choresApi` in `solune/frontend/src/services/api.ts`
- [ ] T038 [US5] If either function IS used elsewhere: add deprecation JSDoc comment (`@deprecated Use useChoresListPaginated / choresApi.listPaginated instead`) to the retained functions
- [ ] T039 [US5] Remove any unused imports that resulted from removing non-paginated functions in affected files

**Checkpoint**: Codebase has a single approach to loading chores. No dead code or duplicate code paths remain (unless explicitly retained with deprecation notice).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T040 [P] Run full pytest test suite for chores API to verify no regressions in `solune/backend/tests/unit/api/test_chores.py`
- [ ] T041 [P] Run full Vitest test suite for chores hooks to verify no regressions in `solune/frontend/tests/hooks/useChores.test.ts`
- [ ] T042 Verify edge case: zero-result filter shows appropriate empty state message (not loading spinner) in `solune/frontend/src/components/chores/ChoresPanel.tsx`
- [ ] T043 Verify edge case: rapid filter toggling does not cause errors, duplicate results, or race conditions
- [ ] T044 Run quickstart.md verification checklist against the implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
  - T003–T007 (backend) and T008–T009 (frontend) can run in parallel
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) — builds on the hook swap in ChoresPanel
- **User Story 3 (Phase 5)**: Depends on User Story 2 (Phase 4) — builds on the filter param wiring
- **User Story 4 (Phase 6)**: Depends on User Story 3 (Phase 5) — verifies reset behavior across all params
- **User Story 5 (Phase 7)**: Depends on User Stories 1–4 — cleanup only after paginated path is fully wired
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — swaps the hook, enables basic pagination
- **User Story 2 (P1)**: Depends on US1 — adds filter param wiring to the already-swapped hook
- **User Story 3 (P2)**: Depends on US2 — adds sort param wiring alongside filters
- **User Story 4 (P2)**: Depends on US3 — validates reset behavior for all param types
- **User Story 5 (P3)**: Depends on US1–US4 — cleanup of old code paths

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend changes before frontend integration
- Hook/API changes before component changes
- Core implementation before cleanup

### Parallel Opportunities

- **Phase 2**: Backend tasks (T003–T007) and frontend tasks (T008–T009) can run in parallel — different files, no dependencies
- **Phase 3**: All pytest tests (T010–T012) can run in parallel
- **Phase 4**: All pytest tests (T015–T021) can run in parallel; Vitest tests (T024–T025) can run in parallel with backend tests
- **Phase 5**: All pytest tests (T026–T028) can run in parallel
- **Phase 7**: Codebase searches (T034–T035) can run in parallel
- **Phase 8**: Full test suite runs (T040–T041) can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Backend and frontend foundational work can proceed in parallel:

# Thread A — Backend (solune/backend/src/api/chores.py):
Task T003: Add filter/sort query parameters to endpoint signature
Task T004: Implement status filtering logic
Task T005: Implement schedule_type filtering logic
Task T006: Implement search filtering logic
Task T007: Implement sort logic

# Thread B — Frontend (solune/frontend/src/):
Task T008: Update choresApi.listPaginated() in api.ts
Task T009: Update useChoresListPaginated() in useChores.ts
```

## Parallel Example: Phase 4 Tests (User Story 2)

```bash
# All filter tests can be written in parallel (same test file, non-overlapping test functions):
Task T015: pytest test for status=active filter
Task T016: pytest test for schedule_type=time filter
Task T017: pytest test for schedule_type=unscheduled filter
Task T018: pytest test for search=deploy filter
Task T019: pytest test for combined filters
Task T020: pytest test for cursor pagination with filters
Task T021: pytest test for total_count with filters

# Frontend tests in parallel with backend tests (different files):
Task T024: Vitest test for filter params in query key
Task T025: Vitest test for filter params passed to API call
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (verify existing infrastructure)
2. Complete Phase 2: Foundational (backend filters + frontend API/hook updates)
3. Complete Phase 3: User Story 1 — Basic paginated loading works
4. Complete Phase 4: User Story 2 — Server-side filtering works
5. **STOP and VALIDATE**: ChoresPanel loads paginated, filtered data from server
6. Deploy/demo if ready — this covers the critical behavioral change

### Incremental Delivery

1. Complete Setup + Foundational → Backend API ready, frontend hook ready
2. Add User Story 1 → Paginated loading works → Test independently (MVP foundation)
3. Add User Story 2 → Filtering works server-side → Test independently (MVP complete!)
4. Add User Story 3 → Sorting works server-side → Test independently
5. Add User Story 4 → Reset behavior verified → Test independently
6. Add User Story 5 → Dead code removed → Codebase clean
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With two developers:

1. Both review Setup together (Phase 1)
2. Once Setup is verified:
   - Developer A: Backend foundational (T003–T007) + backend tests (T010–T012, T015–T021, T026–T028)
   - Developer B: Frontend foundational (T008–T009) + frontend integration (T013–T014, T022–T025)
3. Sync after Phase 4 for Phase 5–8

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new source files are created — all tasks modify existing files
- Default page size is 25, consistent with all other paginated hooks
- `useDeferredValue` for search debouncing is preserved (not replaced)
- `resetPagination()` is NOT needed — TanStack Query's queryKey reactivity handles resets automatically
- Reference implementations: AgentsPanel.tsx, ActivityPage.tsx, ToolsPanel.tsx
