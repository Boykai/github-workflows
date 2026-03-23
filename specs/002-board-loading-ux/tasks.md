# Tasks: Board Loading UX — Skeleton, Stale-While-Revalidate, Refetch Indicator

**Input**: Design documents from `/specs/002-board-loading-ux/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification — test tasks are omitted per spec SC-008 (existing tests must pass, no new tests required).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` — all changes are within the existing frontend directory
- No backend changes are in scope for this feature

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed — feature modifies existing files within `solune/frontend/`. This phase verifies prerequisites and existing components.

- [ ] T001 Verify existing `BoardColumnSkeleton` component dimensions match `ProjectBoard.tsx` grid layout in `solune/frontend/src/components/board/BoardColumnSkeleton.tsx`
- [ ] T002 [P] Verify existing `IssueCardSkeleton` component renders correctly in `solune/frontend/src/components/board/IssueCardSkeleton.tsx`
- [ ] T003 [P] Verify `@tanstack/react-query` version supports `keepPreviousData` export (requires `^5.x`) in `solune/frontend/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hook changes that ALL user stories depend on — must complete before any rendering changes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Import `keepPreviousData` from `@tanstack/react-query` in `solune/frontend/src/hooks/useProjectBoard.ts`
- [ ] T005 Add `placeholderData: keepPreviousData` to the board data query options in `solune/frontend/src/hooks/useProjectBoard.ts`
- [ ] T006 Destructure `isPlaceholderData` from the board data query result in `solune/frontend/src/hooks/useProjectBoard.ts`
- [ ] T007 Add `isPlaceholderData` to the hook's return object and TypeScript return type interface in `solune/frontend/src/hooks/useProjectBoard.ts`

**Checkpoint**: Foundation ready — `useProjectBoard` hook now exposes `isPlaceholderData` and retains previous data during project switches. User story implementation can now begin.

---

## Phase 3: User Story 1 — Instant Board Display from Cache (Priority: P1) 🎯 MVP

**Goal**: Re-visiting a cached project board renders instantly from TanStack Query's cache (60s staleTime) with no loading spinner. Switching projects keeps the old board visible while the new one loads.

**Independent Test**: Navigate to a project board, navigate away, then navigate back — the board should render instantly from cache with no spinner or skeleton shown.

### Implementation for User Story 1

- [ ] T008 [US1] Confirm `staleTime` is set to 60s (`STALE_TIME_SHORT`) on the board data query to enable cache-based instant display in `solune/frontend/src/hooks/useProjectBoard.ts`
- [ ] T009 [US1] Update the board rendering condition in `ProjectsPage.tsx` to show board content immediately when `boardData` is available (even when `isPlaceholderData` is true) in `solune/frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional — re-visiting a cached project instantly shows the board without a spinner.

---

## Phase 4: User Story 2 — Skeleton Board on First Load (Priority: P2)

**Goal**: First-time board loads (no cached data) show a skeleton column layout matching the real board's CSS grid instead of the full-screen CelestialLoader spinner.

**Independent Test**: Clear browser cache or navigate to a never-visited project — skeleton columns appear immediately and transition to real board data when loaded.

### Implementation for User Story 2

- [ ] T010 [P] [US2] Create `BoardSkeleton` component in `solune/frontend/src/components/board/BoardSkeleton.tsx` — render a grid of 5 `BoardColumnSkeleton` columns matching `ProjectBoard.tsx` CSS grid layout (`gridTemplateColumns: repeat(5, minmax(min(16rem, 85vw), 1fr))`, `gap-5`), with `aria-busy="true"` and `role="region"` for accessibility
- [ ] T011 [US2] Import `BoardSkeleton` in `solune/frontend/src/pages/ProjectsPage.tsx`
- [ ] T012 [US2] Replace the `CelestialLoader` spinner block (~line 460) with `<BoardSkeleton />` when `boardLoading && !boardData` in `solune/frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: At this point, User Story 2 should be fully functional — first-time loads show skeleton columns instead of a spinner.

---

## Phase 5: User Story 3 — Background Refetch Indicator (Priority: P3)

**Goal**: Show a subtle "Updating…" indicator and dim the board to opacity-60 during background data refreshes. Show a toast notification on background refresh failures. Users can still interact with the board during refresh.

**Independent Test**: View a cached board, trigger a background refetch — the board dims with "Updating…" text, then restores to full opacity when fresh data arrives. Simulate a refetch failure — toast notification appears and board remains usable.

### Implementation for User Story 3

- [ ] T013 [US3] Wrap the board rendering block in an opacity transition container (`transition-opacity duration-300`) in `solune/frontend/src/pages/ProjectsPage.tsx` — apply `opacity-60` when `(isFetching && !boardLoading) || isPlaceholderData`, otherwise `opacity-100`
- [ ] T014 [US3] Add "Updating…" text indicator (positioned top-right of board area, `z-10`, muted foreground color) visible only during the stale/refreshing state in `solune/frontend/src/pages/ProjectsPage.tsx`
- [ ] T015 [US3] Add `useEffect` watching `boardError` and `boardData` — when `boardError && boardData` (background refresh failure), call `toast.error('Failed to refresh board')` using existing sonner pattern in `solune/frontend/src/pages/ProjectsPage.tsx`
- [ ] T016 [US3] Ensure initial load errors (`boardError && !boardData`) continue to show the existing full error state (no toast for initial failures) in `solune/frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: At this point, User Story 3 should be fully functional — background refreshes show a non-intrusive indicator and failures produce toast notifications.

---

## Phase 6: User Story 4 — Project Switching with Stale Data Visibility (Priority: P2)

**Goal**: When switching from Project A to Project B, Project A's board remains visible (dimmed with "Updating…") until Project B's data loads. No blank screen or spinner between project switches.

**Independent Test**: Open Project A's board, then switch to Project B via navigation — Project A's board should remain visible with dimming until Project B renders.

### Implementation for User Story 4

- [ ] T017 [US4] Verify that `keepPreviousData` in `useProjectBoard.ts` retains Project A's `boardData` while Project B loads (enabled by T005) — confirm `isPlaceholderData` is `true` during the transition in `solune/frontend/src/hooks/useProjectBoard.ts`
- [ ] T018 [US4] Verify that the opacity/indicator logic from US3 (T013–T014) correctly handles the `isPlaceholderData === true` case during project switching — Project A's board should be dimmed with "Updating…" in `solune/frontend/src/pages/ProjectsPage.tsx`
- [ ] T019 [US4] Verify that when Project B's data arrives, the board replaces Project A's content at full opacity with the CSS transition in `solune/frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: At this point, all user stories should be independently functional — project switching never shows a blank screen.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cross-cutting quality checks

- [ ] T020 Run `npm run lint` from `solune/frontend/` — verify no linting errors introduced
- [ ] T021 [P] Run `npx tsc --noEmit` from `solune/frontend/` — verify no TypeScript errors introduced
- [ ] T022 [P] Run `npm run test` from `solune/frontend/` — verify all existing tests pass (SC-008)
- [ ] T023 Run `npm run build` from `solune/frontend/` — verify production build succeeds
- [ ] T024 Verify accessibility: `BoardSkeleton` has `aria-busy="true"` and `role="region"` attributes, skeleton columns have `role="status"`
- [ ] T025 Verify that rapid project switching (A → B → C) only renders the final project's board — intermediate requests should be cancelled by TanStack Query's automatic query cancellation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verification of existing components
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (hook changes needed by all rendering work)
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — can start immediately after
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — can run in parallel with US1 and US2
- **User Story 4 (Phase 6)**: Depends on US1 (T005/T009) and US3 (T013/T014) — verification phase for project switching behavior
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — independent of US1 (different rendering branch: `boardLoading && !boardData` vs. `boardData`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — independent of US1 and US2 (different rendering branch: `isFetching && boardData`)
- **User Story 4 (P2)**: Depends on US1 + US3 — verifies the combined behavior of `keepPreviousData` + opacity indicator during project switching

### Within Each User Story

- Models/hook changes before rendering changes
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002, T003 can all run in parallel (Setup verification)
- T010 (`BoardSkeleton.tsx` creation) can run in parallel with T008–T009 (US1 changes) since they modify different files
- T013–T016 (US3 indicator/toast) can run in parallel with T010–T012 (US2 skeleton) since US3 modifies a different rendering branch in `ProjectsPage.tsx`
- T020, T021, T022 (lint, typecheck, test) can run in parallel

---

## Parallel Example: User Story 2 + User Story 3

```bash
# These can run in parallel since they modify different files/sections:

# User Story 2 (skeleton component — new file):
Task: "Create BoardSkeleton component in solune/frontend/src/components/board/BoardSkeleton.tsx"

# User Story 3 (refetch indicator — different section of ProjectsPage.tsx):
Task: "Add opacity transition container for board rendering in solune/frontend/src/pages/ProjectsPage.tsx"
Task: "Add 'Updating…' text indicator in solune/frontend/src/pages/ProjectsPage.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing components)
2. Complete Phase 2: Foundational (`keepPreviousData` + `isPlaceholderData` in hook)
3. Complete Phase 3: User Story 1 (instant cache display)
4. **STOP and VALIDATE**: Re-visit a cached project — board should render instantly
5. This alone eliminates the spinner for the most common case (returning to a board)

### Incremental Delivery

1. Complete Setup + Foundational → Hook ready with stale-while-revalidate
2. Add User Story 1 → Instant cache display → Validate independently (MVP!)
3. Add User Story 2 → Skeleton on first load → Validate independently
4. Add User Story 3 → Background refetch indicator → Validate independently
5. Add User Story 4 → Project switching verification → Validate independently
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (hook validation + rendering condition)
   - Developer B: User Story 2 (BoardSkeleton component + ProjectsPage integration)
   - Developer C: User Story 3 (opacity/indicator + toast logic)
3. User Story 4 integrates after US1 + US3 are complete

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 25 |
| **User Story 1 tasks** | 2 (T008–T009) |
| **User Story 2 tasks** | 3 (T010–T012) |
| **User Story 3 tasks** | 4 (T013–T016) |
| **User Story 4 tasks** | 3 (T017–T019) |
| **Setup tasks** | 3 (T001–T003) |
| **Foundational tasks** | 4 (T004–T007) |
| **Polish tasks** | 6 (T020–T025) |
| **Parallel opportunities** | 7 (T001–T003, T010∥T008–T009, T013–T016∥T010–T012, T020–T022) |
| **Files modified** | 2 (`useProjectBoard.ts`, `ProjectsPage.tsx`) |
| **Files created** | 1 (`BoardSkeleton.tsx`) |
| **Suggested MVP scope** | User Story 1 (Phases 1–3: 9 tasks) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All changes are frontend-only — no backend modifications
- Existing `BoardColumnSkeleton` and `IssueCardSkeleton` are reused as-is
- SC-008: All existing tests must pass — no test modifications needed
