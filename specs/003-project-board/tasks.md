# Tasks: Standalone Project Board Page

**Input**: Design documents from `/specs/003-project-board/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: OPTIONAL - not explicitly requested in feature specification. Manual verification via browser sufficient per constitution check.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Includes exact file paths based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new directories and files required for the project board feature

- [x] T001 Create project board component directory at `frontend/src/components/project-board/`
- [x] T002 [P] Create backend Pydantic models file at `backend/src/models/project_board.py` with BoardAssignee, LinkedPullRequest, BoardIssueCard, BoardStatusColumn, BoardStatusColumnSummary, BoardProject, BoardProjectListResponse, BoardDataResponse, LinkedPRsRequest, LinkedPRsResponse models per contracts/api-contracts.md Contract 2
- [x] T003 [P] Create backend API router file at `backend/src/api/project_board.py` with router skeleton

**Checkpoint**: File structure ready — proceed to foundational infrastructure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extend GitHub Projects service with `get_board_data(access_token, project_id)` method and `GET_BOARD_DATA_QUERY` GraphQL query in `backend/src/services/github_projects.py` — query fetches project items with fieldValues (Status, Priority, Size, Estimate), assignees with avatarUrl, and repository info per research.md Decision 2
- [x] T005 Extend GitHub Projects service with `get_linked_prs(access_token, content_ids)` method and `GET_LINKED_PRS_QUERY` GraphQL query in `backend/src/services/github_projects.py` — batched query using aliases on Issue.timelineItems for CrossReferencedEvent per research.md Decision 3
- [x] T006 Implement three FastAPI endpoints in `backend/src/api/project_board.py`: GET /projects (list projects reusing existing service), GET /{project_id}/board (board data grouped by status), POST /linked-prs (batch linked PRs) per contracts/api-contracts.md Contract 1
- [x] T007 Register project board router in `backend/src/api/__init__.py` with prefix `/project-board` and tags `["project-board"]` per contracts/api-contracts.md Contract 6.1
- [x] T008 [P] Add project board TypeScript types to `frontend/src/types/index.ts`: BoardAssignee, LinkedPullRequest, BoardIssueCard, BoardStatusColumn, BoardProject, BoardProjectListResponse, BoardDataResponse, LinkedPRsRequest, LinkedPRsResponse interfaces per contracts/api-contracts.md Contract 3
- [x] T009 [P] Add `projectBoardApi` object to `frontend/src/services/api.ts` with listProjects(), getBoardData(projectId), and getLinkedPRs(contentIds) methods per contracts/api-contracts.md Contract 4
- [x] T010 Create `useProjectBoard` custom hook in `frontend/src/hooks/useProjectBoard.ts` with useQuery for project list (key: `['board-projects']`), useQuery for board data (key: `['board-data', projectId]`), state for selectedProjectId/isModalOpen/selectedCard, and functions for selectProject/openModal/closeModal per research.md Decision 5

**Checkpoint**: Foundation ready — backend endpoints operational, frontend data layer wired, user story implementation can now begin

---

## Phase 3: User Story 1 — View Project Board (Priority: P1) 🎯 MVP

**Goal**: Users can navigate to /project-board, select a GitHub Project from a dropdown, and view a Kanban-style board with status columns and issue cards displaying repo name, assignee avatars, linked PR badges, and priority/estimate/size badges

**Independent Test**: Navigate to /project-board via sidebar, select a project from the dropdown, verify columns render with colored status dots, names, item counts, aggregate estimates, and issue cards display all required data fields

### Implementation for User Story 1

- [x] T011 [P] [US1] Create `ProjectBoardPage` component in `frontend/src/components/project-board/ProjectBoardPage.tsx` — main page with project dropdown selector, board grid layout, uses `useProjectBoard` hook, renders BoardColumn for each status column per contracts/api-contracts.md Contract 5.1
- [x] T012 [P] [US1] Create `BoardColumn` component in `frontend/src/components/project-board/BoardColumn.tsx` — renders colored status dot, column name, item count, aggregate total_estimate in header, scrollable list of BoardIssueCard components, accepts onCardClick callback per contracts/api-contracts.md Contract 5.2
- [x] T013 [P] [US1] Create `BoardIssueCard` component in `frontend/src/components/project-board/BoardIssueCard.tsx` — renders repo_name/issue_number, title, up to 3 assignee avatars with +N overflow, linked PR badge (count with state color), priority/size/estimate badges with color coding, clickable per contracts/api-contracts.md Contract 5.3
- [x] T014 [US1] Add state-based routing in `frontend/src/App.tsx` — add `currentPage` state (`'chat' | 'project-board'`), conditionally render ProjectBoardPage when `currentPage === 'project-board'`, pass onNavigate callback to sidebar per contracts/api-contracts.md Contract 6.2 and research.md Decision 4
- [x] T015 [US1] Add navigation link to project board in `frontend/src/components/sidebar/ProjectSidebar.tsx` — add onNavigateToBoard prop, render "Project Board" button/link that calls `onNavigate('project-board')` per contracts/api-contracts.md Contract 6.3
- [x] T016 [US1] Add board-specific CSS styles to `frontend/src/App.css` — add `.project-board-page`, `.board-project-selector`, `.board-container` (horizontal scroll), `.board-column`, `.board-column-header`, `.board-issue-card` (hover effects), `.board-card-badges` (priority/size/estimate colors), `.board-assignee-avatars`, `.board-pr-badge`, and status dot color classes (`.status-dot--GREEN`, `.status-dot--YELLOW`, `.status-dot--RED`, `.status-dot--BLUE`, `.status-dot--PURPLE`, `.status-dot--PINK`, `.status-dot--ORANGE`, `.status-dot--GRAY`) using existing CSS custom properties per research.md Decision 8 and Decision 9

**Checkpoint**: User Story 1 complete — user can navigate to /project-board, select a project, and see the full Kanban board with all issue card data fields

---

## Phase 4: User Story 2 — View Issue Details (Priority: P2)

**Goal**: Users can click any issue card to open a detail modal with expanded issue information and a link to open the issue on github.com in a new tab

**Independent Test**: Click any issue card on a loaded board, verify modal opens with full title, body summary, assignees, linked PRs, priority/estimate/size/status badges, verify "Open on GitHub" link opens in new tab, verify modal closes on click-outside/Escape/close button

### Implementation for User Story 2

- [x] T017 [US2] Create `IssueDetailModal` component in `frontend/src/components/project-board/IssueDetailModal.tsx` — modal overlay with centered content, displays full issue details (title, body, status, priority, size, estimate), lists assignees with avatars and usernames, lists linked PRs with state badges, "Open on GitHub" link with `target="_blank" rel="noopener noreferrer"`, closes on click-outside/Escape key/close button, renders nothing when isOpen is false per contracts/api-contracts.md Contract 5.4
- [x] T018 [US2] Integrate IssueDetailModal into ProjectBoardPage in `frontend/src/components/project-board/ProjectBoardPage.tsx` — wire selectedCard and isModalOpen state from useProjectBoard hook, pass openModal callback to BoardColumn/BoardIssueCard, pass closeModal callback to IssueDetailModal
- [x] T019 [US2] Add modal CSS styles to `frontend/src/App.css` — add `.issue-detail-modal-overlay` (fixed positioning, backdrop), `.issue-detail-modal-content` (centered card, scrollable), `.modal-assignee-list`, `.modal-pr-list`, `.modal-github-link`, `.modal-close-button` using existing CSS custom properties

**Checkpoint**: User Story 2 complete — clicking any issue card opens a detail modal with full information and a working GitHub link

---

## Phase 5: User Story 3 — Auto-Refresh Board Data (Priority: P3)

**Goal**: The board automatically refreshes every 15 seconds with a subtle loading indicator, pauses when the detail modal is open, and shows error notifications on refresh failure

**Independent Test**: Load a board, wait 15 seconds, verify data refreshes with subtle indicator, open modal and verify refresh pauses, close modal and verify refresh resumes, simulate network error and verify error notification with retry option

### Implementation for User Story 3

- [x] T020 [US3] Add 15-second auto-refresh to `useProjectBoard` hook in `frontend/src/hooks/useProjectBoard.ts` — set `refetchInterval: isModalOpen ? false : 15000` on board data useQuery, set `staleTime: 10000` for stale-while-revalidate behavior per research.md Decision 5
- [x] T021 [US3] Add subtle refresh indicator to `ProjectBoardPage` in `frontend/src/components/project-board/ProjectBoardPage.tsx` — show "Refreshing..." indicator using `isFetching` state from useQuery without disrupting current view or scroll position
- [x] T022 [US3] Add auto-refresh error notification to `ProjectBoardPage` in `frontend/src/components/project-board/ProjectBoardPage.tsx` — display error toast/banner when background refresh fails with retry button using `refetch()`, retain last successfully loaded data on failure
- [x] T023 [US3] Add refresh indicator CSS styles to `frontend/src/App.css` — add `.board-refresh-indicator` (subtle top-bar or corner indicator), `.board-refresh-error` (error notification banner with retry button)

**Checkpoint**: User Story 3 complete — board auto-refreshes every 15 seconds, pauses during modal, handles refresh errors gracefully

---

## Phase 6: User Story 4 — Loading and Error States (Priority: P4)

**Goal**: Users see clear loading indicators during data fetches and helpful error messages with retry options when things go wrong

**Independent Test**: Navigate to /project-board and verify loading indicator while project list loads, select a project and verify loading skeleton while board data loads, simulate API failure and verify error message with retry button, simulate invalid auth and verify re-authenticate prompt

### Implementation for User Story 4

- [x] T024 [US4] Add initial loading states to `ProjectBoardPage` in `frontend/src/components/project-board/ProjectBoardPage.tsx` — show loading spinner/skeleton while project list is loading (`isLoading` from projects query), show board loading skeleton while board data is loading (`isLoading` from board query) per research.md Decision 10
- [x] T025 [US4] Add error states to `ProjectBoardPage` in `frontend/src/components/project-board/ProjectBoardPage.tsx` — show error message with retry button when initial data fetch fails (`isError` + `error` from queries), show re-authenticate prompt when 401 error is returned
- [x] T026 [US4] Add empty state to `ProjectBoardPage` in `frontend/src/components/project-board/ProjectBoardPage.tsx` — show "No projects available" message when user has no GitHub Projects, show "No status columns" message when selected project has no status fields configured
- [x] T027 [US4] Add loading and error state CSS styles to `frontend/src/App.css` — add `.board-loading-skeleton`, `.board-loading-spinner`, `.board-error-state` (error message + retry button), `.board-empty-state` (informational message) using existing CSS custom properties

**Checkpoint**: User Story 4 complete — all loading, error, and empty states display correctly

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028 [P] Handle edge case of issues with missing optional fields (no assignees, no linked PRs, no priority/size/estimate) in `frontend/src/components/project-board/BoardIssueCard.tsx` — verify card renders gracefully without blank spaces or broken layout
- [x] T029 [P] Handle edge case of large project dropdown (50+ projects) in `frontend/src/components/project-board/ProjectBoardPage.tsx` — ensure dropdown supports scrolling and remains performant
- [x] T030 [P] Handle edge case of large column (100+ issues) in `frontend/src/components/project-board/BoardColumn.tsx` — ensure column supports scrolling and board remains responsive
- [x] T031 Handle network connectivity loss in `frontend/src/components/project-board/ProjectBoardPage.tsx` — retain last successfully loaded data and display connectivity warning
- [x] T032 Verify dark mode support for all board components in `frontend/src/App.css` — ensure all `.project-board-*` classes use CSS custom properties for theming per research.md Decision 8
- [x] T033 Run `npm run build` in `frontend/` and `python -m py_compile backend/src/api/project_board.py` to verify no build errors
- [x] T034 Manual verification: start backend + frontend dev servers and walk through all user scenarios per quickstart.md Step 11

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion — BLOCKS US2 (modal needs cards to click)
- **User Story 2 (Phase 4)**: Depends on US1 (needs rendered board with clickable cards)
- **User Story 3 (Phase 5)**: Depends on Foundational completion — can start in parallel with US1
- **User Story 4 (Phase 6)**: Depends on Foundational completion — can start in parallel with US1
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 — needs rendered board with clickable issue cards
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — auto-refresh logic is independent of card rendering (hook-level change)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — loading/error states are independent of card rendering

### Within Each User Story

- Components before integration
- Parent components before child components (where applicable)
- CSS styles alongside or after component creation
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 can run in parallel (different files in Phase 1)
- T008 and T009 can run in parallel (different frontend files in Phase 2)
- T011, T012, and T013 can run in parallel (different component files in Phase 3)
- T028, T029, and T030 can run in parallel (different component files in Phase 7)
- US3 and US4 can start in parallel after Foundational phase (hook-level and state-level changes)

---

## Parallel Example: User Story 1

```bash
# Launch all component files for User Story 1 together:
Task T011: "Create ProjectBoardPage component in frontend/src/components/project-board/ProjectBoardPage.tsx"
Task T012: "Create BoardColumn component in frontend/src/components/project-board/BoardColumn.tsx"
Task T013: "Create BoardIssueCard component in frontend/src/components/project-board/BoardIssueCard.tsx"

# After components are created, wire integration sequentially:
Task T014: "Add state-based routing in frontend/src/App.tsx"
Task T015: "Add navigation link in frontend/src/components/sidebar/ProjectSidebar.tsx"
Task T016: "Add board CSS styles to frontend/src/App.css"
```

---

## Parallel Example: Foundational Phase

```bash
# Launch frontend foundational tasks together:
Task T008: "Add TypeScript types to frontend/src/types/index.ts"
Task T009: "Add projectBoardApi to frontend/src/services/api.ts"

# Backend tasks run sequentially (service methods depend on each other):
Task T004: "Extend service with get_board_data method"
Task T005: "Extend service with get_linked_prs method"
Task T006: "Implement FastAPI endpoints"
Task T007: "Register router"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T010)
3. Complete Phase 3: User Story 1 (T011–T016)
4. **STOP and VALIDATE**: Navigate to /project-board, select a project, verify Kanban board renders with all data fields
5. Deploy/demo if ready — board is viewable

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Users can view the board)
3. Add User Story 2 → Test independently → Deploy/Demo (Users can see issue details)
4. Add User Story 3 → Test independently → Deploy/Demo (Board auto-refreshes)
5. Add User Story 4 → Test independently → Deploy/Demo (Polish with loading/error states)
6. Complete Polish → Final validation

### Single Developer Strategy

Recommended execution order for a single developer:

1. Phase 1: Setup (T001–T003) — ~15 min
2. Phase 2: Foundational (T004–T010) — ~2 hours
3. Phase 3: User Story 1 (T011–T016) — ~1.5 hours
4. Phase 4: User Story 2 (T017–T019) — ~45 min
5. Phase 5: User Story 3 (T020–T023) — ~30 min
6. Phase 6: User Story 4 (T024–T027) — ~30 min
7. Phase 7: Polish (T028–T034) — ~30 min

**Total estimated time**: ~6 hours

---

## Notes

- [P] tasks = different files, no dependencies on each other
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No test tasks included — spec does not explicitly request tests; manual verification per quickstart.md is sufficient
- All CSS uses existing custom properties for light/dark mode theming
- Backend endpoints reuse existing session authentication (`get_session_dep`) and caching infrastructure
- Frontend uses `@tanstack/react-query` for all data fetching and auto-refresh
