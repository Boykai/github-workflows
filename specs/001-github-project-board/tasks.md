# Tasks: Real-Time GitHub Project Board

**Input**: Design documents from `/specs/001-github-project-board/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/board-api.yaml ✅

**Tests**: Not explicitly requested in specification. Including basic tests for new API endpoints.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths included

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create base project structure for board feature

- [x] T001 Create board components directory at frontend/src/components/board/
- [x] T002 Create pages directory at frontend/src/pages/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend models, types, and API router that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create board Pydantic models in backend/src/models/board.py (BoardProject, StatusField, StatusOption, StatusColor, BoardItem, BoardColumn, BoardDataResponse per data-model.md)
- [x] T004 [P] Extend frontend TypeScript types in frontend/src/types/index.ts (add BoardProject, StatusOption, StatusColor, BoardItem, BoardColumn, LinkedPR, PRState interfaces)
- [x] T005 Add GraphQL query for project items with custom fields (Priority, Size, Estimate) in backend/src/services/github_projects.py
- [x] T006 Add GraphQL query for linked PRs via timeline events in backend/src/services/github_projects.py
- [x] T007 Create board API router in backend/src/api/board.py with route registration in backend/src/main.py
- [x] T008 Implement GET /api/v1/board/projects endpoint in backend/src/api/board.py (list projects with status field config)
- [x] T009 Implement GET /api/v1/board/projects/{project_id} endpoint in backend/src/api/board.py (board data with columns and items)

**Checkpoint**: Foundation ready - backend API functional, types defined

---

## Phase 3: User Story 1 - View Project Board with Live Data (Priority: P1) 🎯 MVP

**Goal**: Navigate to /project-board, select a project, view Kanban board with columns and issue cards showing all metadata

**Independent Test**: Navigate to /project-board, select project from dropdown, verify columns display with cards showing title, repo, assignees, priority, size, estimate, linked PRs

### Implementation for User Story 1

- [x] T010 [P] [US1] Create useProjectBoard hook in frontend/src/hooks/useProjectBoard.ts (fetch projects list, fetch board data, manage selected project state)
- [x] T011 [P] [US1] Create ProjectBoardPage component in frontend/src/pages/ProjectBoardPage.tsx (page layout with project selector dropdown)
- [x] T012 [US1] Create ProjectBoard component in frontend/src/components/board/ProjectBoard.tsx (horizontal columns container)
- [x] T013 [US1] Create BoardColumn component in frontend/src/components/board/BoardColumn.tsx (column header with status dot, name, count, estimate total, description; scrollable card list)
- [x] T014 [US1] Create IssueCard component in frontend/src/components/board/IssueCard.tsx (repo name, issue number, title, assignee avatars, priority/size/estimate badges, linked PR badge)
- [x] T015 [US1] Add /project-board route to frontend/src/App.tsx with React Router or conditional rendering
- [x] T016 [US1] Add "Project Board" navigation link to header navigation in frontend/src/App.tsx
- [x] T017 [US1] Add board CSS styles following existing Tailwind patterns in frontend/src/App.css or component-level styles
- [x] T018 [US1] Implement empty states (no projects available, project has no items, column is empty)
- [x] T019 [US1] Implement loading state during initial board fetch
- [x] T020 [US1] Implement error state with retry option when API fails

**Checkpoint**: User Story 1 complete - board displays with all metadata, navigation works

---

## Phase 4: User Story 2 - View Issue Details in Modal (Priority: P2)

**Goal**: Click issue card to open detail modal with expanded information and GitHub link

**Independent Test**: Click any issue card, verify modal opens with full details, click "Open in GitHub" to verify new tab opens

### Implementation for User Story 2

- [x] T021 [US2] Create IssueDetailModal component in frontend/src/components/board/IssueDetailModal.tsx (full title, body/description, all custom fields, assignees list, linked PRs with status)
- [x] T022 [US2] Add modal state management to ProjectBoardPage (selectedItem, isModalOpen)
- [x] T023 [US2] Wire IssueCard onClick to open modal with item data
- [x] T024 [US2] Implement "Open in GitHub" link that opens issue URL in new tab (target="_blank" rel="noopener")
- [x] T025 [US2] Implement modal dismiss via click outside, Escape key, and close button
- [x] T026 [US2] Style modal following existing app design patterns

**Checkpoint**: User Story 2 complete - detail modal fully functional

---

## Phase 5: User Story 3 - Auto-Refresh Board Data (Priority: P3)

**Goal**: Board data auto-refreshes every 15 seconds with subtle loading indicator

**Independent Test**: View board for 15+ seconds, make change in GitHub, verify board updates on next poll

### Implementation for User Story 3

- [x] T027 [US3] Add refetchInterval: 15000 to useProjectBoard hook's React Query configuration
- [x] T028 [US3] Add isFetching state tracking to show subtle refresh indicator
- [x] T029 [US3] Create refresh indicator UI (small spinner or pulse animation in header) that doesn't disrupt board view
- [x] T030 [US3] Ensure error during refresh retains previous data (staleWhileRevalidate pattern)
- [x] T031 [US3] Add "last updated" timestamp display similar to existing sync status in ProjectSidebar

**Checkpoint**: User Story 3 complete - auto-refresh working with proper UX

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, edge cases, and quality improvements

- [x] T032 [P] Handle edge case: issue with no assignees (hide avatar area or show placeholder)
- [x] T033 [P] Handle edge case: missing custom fields (show "—" or hide badge)
- [x] T034 [P] Handle edge case: column with 50+ items (ensure scroll works smoothly)
- [x] T035 [P] Handle edge case: authentication token expiry (show re-auth message)
- [x] T036 Add color mapping utility for StatusColor enum to Tailwind CSS classes
- [x] T037 Unit test for board API endpoints in backend/tests/unit/test_board.py

**Checkpoint**: Feature complete and polished

---

## Dependencies Graph

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Phase 3 (US1)    Phase 4 (US2)     Phase 5 (US3)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
                Phase 6 (Polish)
```

**Notes**:
- US1, US2, US3 can be implemented in parallel after Phase 2
- US2 (modal) requires US1 (cards) for integration
- US3 (auto-refresh) can be added to US1 independently
- Phase 6 tasks are all parallelizable

---

## Parallel Execution Examples

**Maximum parallelism after Phase 2**:
- T010 + T011 (hook + page) in parallel
- T012 + T013 + T014 (board components) after T010/T011
- T021 (modal) can start once T014 (card) is done
- T027-T031 (auto-refresh) can start once T010 is done

**Suggested execution order for single developer**:
1. T001-T002 (setup)
2. T003-T009 (backend foundation)
3. T010-T020 (US1 complete)
4. T021-T026 (US2 complete)
5. T027-T031 (US3 complete)
6. T032-T037 (polish)

---

## Implementation Strategy

**MVP Scope**: Complete Phase 1, 2, and 3 (User Story 1) for minimum viable feature

**Incremental Delivery**:
1. **MVP**: Board displays with project selection and all card metadata
2. **+US2**: Add detail modal for deeper issue inspection
3. **+US3**: Add auto-refresh for real-time updates
4. **+Polish**: Handle all edge cases and add tests
