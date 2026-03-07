# Tasks: Solune UI Redesign

**Input**: Design documents from `/specs/025-solune-ui-redesign/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: FR-026 requires existing unit tests to pass with updated fixtures. No new test creation requested. Test fixture updates are included in the Polish phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The 3 P1 stories share foundational infrastructure (routing + theme), extracted into Phase 2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for all source changes. `backend/` has NO changes.

---

## Phase 1: Setup

**Purpose**: Install dependencies and create directory structure

- [X] T001 Install react-router-dom v7 via `npm install react-router-dom` in frontend/package.json
- [X] T002 Create layout directory at frontend/src/layout/
- [X] T003 [P] Add NavRoute, SidebarState, RecentInteraction, and Notification types to frontend/src/types/index.ts
- [X] T004 [P] Add NAV_ROUTES array and PRIORITY_COLORS constant to frontend/src/constants.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Design system token swap, React Router setup, and layout shell — shared infrastructure for ALL user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Design System Infrastructure

- [X] T005 Replace title "Agent Projects" with "Solune" and swap Rye font URL to Plus Jakarta Sans in frontend/index.html
- [X] T006 Replace all `:root` light-mode HSL theme tokens with purple/violet palette in frontend/src/index.css
- [X] T007 Replace all `.dark` dark-mode HSL theme tokens with cool purple palette in frontend/src/index.css
- [X] T008 Replace `--font-display` from 'Rye' to 'Plus Jakarta Sans', replace `--shadow-warm-*` with neutral shadows, update `--radius` to 0.5rem in frontend/src/index.css
- [X] T009 Add priority color CSS custom properties (--priority-p0 through --priority-p3) to frontend/src/index.css
- [X] T010 Remove Rye font-family usage from h1/h2/h3 global styles, ensure Plus Jakarta Sans is applied in frontend/src/index.css

### Router Setup

- [X] T011 Rewrite frontend/src/App.tsx: remove all hash routing logic (getViewFromHash, changeView, hashchange listener), replace with BrowserRouter + Routes + Route config per contracts/routes.md
- [X] T012 Create AuthGate wrapper component that checks useAuth and redirects unauthenticated users to LoginPage, storing intended path in sessionStorage, in frontend/src/layout/AppLayout.tsx (or co-located)

### Layout Shell

- [X] T013 Create AppLayout component with Sidebar + TopBar + Outlet + ChatPopup rendering in frontend/src/layout/AppLayout.tsx
- [X] T014 Create useSidebarState hook with localStorage persistence in frontend/src/hooks/useSidebarState.ts
- [X] T015 [P] Create Sidebar component with Solune branding, nav links from NAV_ROUTES, collapse toggle, and project name slot in frontend/src/layout/Sidebar.tsx
- [X] T016 [P] Create TopBar component with breadcrumb slot, theme toggle, notification bell slot, and user avatar in frontend/src/layout/TopBar.tsx
- [X] T017 [P] Create Breadcrumb component deriving segments from useLocation().pathname and NAV_ROUTES in frontend/src/layout/Breadcrumb.tsx

### Page Stubs

- [X] T018 [P] Create AppPage stub (welcome page with heading) in frontend/src/pages/AppPage.tsx
- [X] T019 [P] Create LoginPage with Solune branding and GitHub auth button in frontend/src/pages/LoginPage.tsx
- [X] T020 [P] Create NotFoundPage with "Page Not Found" message in frontend/src/pages/NotFoundPage.tsx

**Checkpoint**: Foundation ready — app loads with Solune theme, 6 routes work, sidebar + topbar render, auth gate redirects. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Navigate the Solune App via Sidebar (Priority: P1) 🎯 MVP

**Goal**: Fully functional sidebar navigation with collapse state, active-state indicators, breadcrumbs, and browser history support across all 6 routes.

**Independent Test**: Log in → click each sidebar link → verify URL changes + correct page renders → collapse sidebar → refresh → verify collapsed state persists → use browser back/forward → verify no full reload.

### Implementation for User Story 1

- [X] T021 [US1] Add purple active-state indicator with left border accent to Sidebar nav links using NavLink from react-router-dom in frontend/src/layout/Sidebar.tsx
- [X] T022 [US1] Implement sidebar collapse/expand with CSS transition (icons-only when collapsed, main content expands) in frontend/src/layout/Sidebar.tsx
- [X] T023 [US1] Wire useSidebarState hook into AppLayout and pass isCollapsed + onToggle to Sidebar in frontend/src/layout/AppLayout.tsx
- [X] T024 [US1] Add theme toggle button wired to useAppTheme in TopBar in frontend/src/layout/TopBar.tsx
- [X] T025 [US1] Add user avatar display (from useAuth) to TopBar in frontend/src/layout/TopBar.tsx
- [X] T026 [US1] Verify all 6 routes render correct page stubs with proper URL paths (manual verification via dev server)

**Checkpoint**: User Story 1 complete — navigable 6-page app with collapsible sidebar, breadcrumbs, and browser history working.

---

## Phase 4: User Story 3 — Use the Solune Design System (Priority: P1)

**Goal**: Complete visual redesign — every UI element uses the Solune purple/violet palette, Plus Jakarta Sans typography, cool shadows, and 0.5rem radius. Light/dark mode both cohesive. No western theme remnants.

**Independent Test**: Load app → visually confirm purple/violet colors, modern sans-serif fonts, cool shadows → toggle dark mode → verify contrast and palette consistency → search codebase for "Rye", "warm", "CowboyAvatar" → zero hits.

### Implementation for User Story 3

- [X] T027 [P] [US3] Delete frontend/src/components/CowboyAvatar.tsx and remove all imports referencing it across the codebase
- [X] T028 [P] [US3] Remove any remaining references to "Agent Projects" in component text, page titles, or meta tags throughout frontend/src/
- [X] T029 [US3] Audit all Tailwind utility classes using warm color tokens (e.g., amber, brown, orange-warm) and replace with purple/violet/slate equivalents across frontend/src/components/
- [X] T030 [US3] Verify dark mode contrast meets WCAG AA by testing primary text, links, and interactive elements against dark backgrounds in frontend/src/index.css

**Checkpoint**: User Story 3 complete — Solune design system applied everywhere, no remnants of old theme.

---

## Phase 5: User Story 2 — View and Manage the Project Board (Priority: P1)

**Goal**: Projects page with enhanced Kanban board — priority color badges, description snippets, assignee names, label pills, page header with project title/visibility/progress, and toolbar with Filter/Sort (functional) and scaffolding for Add column/Add card/Group by.

**Independent Test**: Navigate to `/projects` → verify board loads with enhanced cards (priority badges, descriptions, date, labels) → drag card between columns → confirm real-time sync → click Filter/Sort (functional) → click "Add new column" (Coming soon tooltip).

### Implementation for User Story 2

- [ ] T031 [US2] Create ProjectsPage composing useProjectBoard, useBoardRefresh, useRealTimeSync, ProjectBoard, and IssueDetailModal (migrated from ProjectBoardPage) in frontend/src/pages/ProjectsPage.tsx
- [ ] T032 [US2] Add page header section to ProjectsPage with project title, visibility badge, collaborator avatars, and progress bar in frontend/src/pages/ProjectsPage.tsx
- [ ] T033 [US2] Add toolbar section to ProjectsPage with Filter and Sort by buttons wired to client-side filtering/sorting of board data in frontend/src/pages/ProjectsPage.tsx
- [ ] T034 [US2] Add Group by button with "Coming soon" tooltip to ProjectsPage toolbar in frontend/src/pages/ProjectsPage.tsx
- [ ] T035 [US2] Enhance IssueCard with filled priority badge using PRIORITY_COLORS mapping (P0=red, P1=orange, P2=blue, P3=green, default P2) in frontend/src/components/board/IssueCard.tsx
- [ ] T036 [US2] Add description snippet (truncate body to ~80 chars), assignee name beside avatar, date display, and pastel label pills to IssueCard in frontend/src/components/board/IssueCard.tsx
- [x] T037 [US2] Add "+" scaffolding button with "Coming soon" tooltip to BoardColumn header in frontend/src/components/board/BoardColumn.tsx
- [x] T038 [US2] Add "Add new column" scaffolding button with "Coming soon" tooltip after last column in ProjectBoard in frontend/src/components/board/ProjectBoard.tsx
- [x] T039 [US2] Update card and column styles to use 0.5rem radius, cool shadows, and Solune color tokens in frontend/src/components/board/IssueCard.tsx and frontend/src/components/board/BoardColumn.tsx

**Checkpoint**: User Story 2 complete — enhanced board with priority badges, description snippets, functional filters, and scaffolding buttons.

---

## Phase 6: User Story 4 — Access Chat from Any Page (Priority: P2)

**Goal**: ChatPopup rendered in AppLayout (global), accessible from every page, with chat history persisting across navigation and browser refreshes.

**Independent Test**: Navigate to `/projects` → open chat → send message → navigate to `/settings` → reopen chat → verify full history preserved → refresh browser → reopen chat → verify history still present.

### Implementation for User Story 4

- [x] T040 [US4] Lift ChatPopup rendering and useChat/useWorkflow hook instantiation from ProjectBoardPage into AppLayout in frontend/src/layout/AppLayout.tsx
- [x] T041 [US4] Remove ChatPopup rendering and related chat hook imports from ProjectBoardPage (now ProjectsPage) in frontend/src/pages/ProjectsPage.tsx
- [x] T042 [US4] Verify useChatHistory localStorage persistence works across route navigation and full page refresh (manual verification via dev server)

**Checkpoint**: User Story 4 complete — chat accessible and persistent from every page.

---

## Phase 7: User Story 5 — Manage Agents via Pipeline and Agents Pages (Priority: P2)

**Goal**: Two new pages — AgentsPipelinePage (pipeline visualization with agent status, configuration, activity feed) and AgentsPage (assignment map + agent catalog grid).

**Independent Test**: Navigate to `/pipeline` → verify columns displayed as pipeline stages with agent status indicators → assign agent to column → verify save. Navigate to `/agents` → verify assignment map and agent catalog grid → add new agent → verify it appears.

### Implementation for User Story 5

- [x] T043 [P] [US5] Create AgentsPipelinePage composing useProjectBoard (columns), useAgentConfig, useAvailableAgents, useWorkflow, AgentConfigRow, AddAgentPopover, AgentPresetSelector, and AgentSaveBar in frontend/src/pages/AgentsPipelinePage.tsx
- [x] T044 [P] [US5] Create AgentsPage composing useAvailableAgents, useAgentConfig, AgentsPanel (agent catalog grid), AgentCard, and AddAgentModal in frontend/src/pages/AgentsPage.tsx
- [x] T045 [US5] Add pipeline visualization section to AgentsPipelinePage showing board columns as pipeline stages with agent status indicators (running/idle/error) in frontend/src/pages/AgentsPipelinePage.tsx
- [x] T046 [US5] Add activity feed section to AgentsPipelinePage displaying recent agent workflow events from useWorkflow in frontend/src/pages/AgentsPipelinePage.tsx
- [x] T047 [US5] Add visual agent-to-column assignment map to AgentsPage showing which agents are assigned to which columns in frontend/src/pages/AgentsPage.tsx

**Checkpoint**: User Story 5 complete — pipeline operational view and agent catalog management both functional.

---

## Phase 8: User Story 6 — Manage Chores from a Dedicated Page (Priority: P2)

**Goal**: Dedicated Chores page with chore catalog (status, schedule, last/next run), chore creation modal, and cleanup utility section.

**Independent Test**: Navigate to `/chores` → verify chore catalog with metadata → click "Add Chore" → verify template browser modal → toggle pause/resume → verify state update → trigger cleanup → verify confirmation modal.

### Implementation for User Story 6

- [x] T048 [US6] Create ChoresPage composing useChoresList, ChoresPanel, AddChoreModal, ChoreChatFlow, and ChoreScheduleConfig in frontend/src/pages/ChoresPage.tsx
- [x] T049 [US6] Add cleanup section to ChoresPage composing CleanUpButton, CleanUpConfirmModal, CleanUpSummary, and CleanUpAuditHistory from board/ components in frontend/src/pages/ChoresPage.tsx
- [x] T050 [US6] Add rich metadata display (status badges, schedule, last run, next run) to chore entries in ChoresPage in frontend/src/pages/ChoresPage.tsx

**Checkpoint**: User Story 6 complete — chore management and cleanup fully consolidated on dedicated page.

---

## Phase 9: User Story 7 — Select and Switch Projects (Priority: P2)

**Goal**: Project selector in sidebar bottom — displays current project name, opens selector on click, switches project and refreshes board data.

**Independent Test**: Click project name in sidebar → verify project list loads → select different project → verify board data refreshes.

### Implementation for User Story 7

- [x] T051 [US7] Create ProjectSelector dropdown/modal component with project list from useProjects in frontend/src/layout/ProjectSelector.tsx
- [x] T052 [US7] Wire ProjectSelector into Sidebar bottom slot, showing selected project name and opening selector on click in frontend/src/layout/Sidebar.tsx
- [x] T053 [US7] Add empty state to ProjectSelector when no projects available with prompt to connect a GitHub project in frontend/src/layout/ProjectSelector.tsx

**Checkpoint**: User Story 7 complete — project switching works from sidebar on any page.

---

## Phase 10: User Story 8 — Unauthenticated Login Experience (Priority: P3)

**Goal**: Solune-branded login page (no layout shell) for unauthenticated users. Deep-link redirect after auth.

**Independent Test**: Visit any URL while unauthenticated → verify Solune-branded login page renders without sidebar/topbar → authenticate → verify redirect to original URL (or `/` if none).

### Implementation for User Story 8

- [x] T054 [US8] Style LoginPage with Solune branding (logo, purple/violet background, centered card with GitHub auth button) in frontend/src/pages/LoginPage.tsx
- [x] T055 [US8] Implement deep-link redirect: store pre-auth pathname in sessionStorage before redirect, read and navigate after auth in AuthGate in frontend/src/layout/AppLayout.tsx
- [x] T056 [US8] Add fallback to `/` when no stored redirect path exists in AuthGate in frontend/src/layout/AppLayout.tsx

**Checkpoint**: User Story 8 complete — branded login experience with deep-link redirect.

---

## Phase 11: User Story 9 — View Recent Interactions in Sidebar (Priority: P3)

**Goal**: "Recent Interactions" section in sidebar showing up to 8 recent parent issues from board data, sorted descending.

**Independent Test**: Load app with board data → verify sidebar shows "Recent Interactions" with up to 8 parent issues → click an entry → verify navigation to relevant context.

### Implementation for User Story 9

- [x] T057 [US9] Create useRecentParentIssues hook deriving recent parent issues from BoardDataResponse in frontend/src/hooks/useRecentParentIssues.ts
- [x] T058 [US9] Add "Recent Interactions" section to Sidebar rendering items from useRecentParentIssues (max 8, sorted descending) in frontend/src/layout/Sidebar.tsx
- [x] T059 [US9] Add click handler on recent interaction entries to navigate to relevant issue context in frontend/src/layout/Sidebar.tsx
- [x] T060 [US9] Add empty state ("No recent activity") when no recent parent issues exist in frontend/src/layout/Sidebar.tsx

**Checkpoint**: User Story 9 complete — recent interactions visible and clickable in sidebar.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Notification bell, test fixture updates, cleanup of old files, final validation

### Notification Bell (FR-022)

- [x] T061 Create useNotifications hook aggregating agent workflow events and chore completion events with read/unread tracking via localStorage in frontend/src/hooks/useNotifications.ts
- [x] T062 Create NotificationBell component with count badge and dropdown listing recent notifications in frontend/src/layout/NotificationBell.tsx
- [x] T063 Wire NotificationBell into TopBar and connect to useNotifications data in frontend/src/layout/TopBar.tsx

### Cleanup & Validation

- [x] T064 [P] Remove old ProjectBoardPage.tsx (replaced by ProjectsPage.tsx) from frontend/src/pages/ProjectBoardPage.tsx
- [x] T065 [P] Remove all remaining hash routing references and unused imports from any file in frontend/src/
- [x] T066 [P] Restyle SettingsPage to match Solune design tokens (update any warm-theme specific classes) in frontend/src/pages/SettingsPage.tsx
- [x] T067 Update test fixtures to reflect new component structure (AppLayout, Sidebar, route changes) in frontend/src/test/ and relevant test files
- [x] T068 Run full unit test suite (`npm run test` in frontend/) and fix any failures from component restructuring
- [x] T069 Verify app builds with zero compile errors (`npm run build` in frontend/)
- [x] T070 Run quickstart.md validation steps (load `/`, navigate to `/projects`, verify back/forward, direct URL access)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 Navigation (Phase 3)**: Depends on Foundational — delivers the navigable shell
- **US3 Design System (Phase 4)**: Depends on Foundational — can run in PARALLEL with US1
- **US2 Board (Phase 5)**: Depends on Foundational — can run in PARALLEL with US1/US3 (different files)
- **US4 Chat (Phase 6)**: Depends on US1 (AppLayout must exist for chat lifting)
- **US5 Agents (Phase 7)**: Depends on Foundational only — can run in PARALLEL with US1-US3
- **US6 Chores (Phase 8)**: Depends on Foundational only — can run in PARALLEL with US1-US3
- **US7 Project Selector (Phase 9)**: Depends on US1 (Sidebar must exist)
- **US8 Login (Phase 10)**: Depends on Foundational (AuthGate, LoginPage stub exist)
- **US9 Recent Interactions (Phase 11)**: Depends on US1 (Sidebar must exist)
- **Polish (Phase 12)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1) — Navigation**: Can start after Phase 2. No dependencies on other stories.
- **US3 (P1) — Design System**: Can start after Phase 2. No dependencies on other stories. **PARALLEL with US1**.
- **US2 (P1) — Board**: Can start after Phase 2. No dependencies on other stories. **PARALLEL with US1/US3** (touches different files — board/ components vs layout/).
- **US4 (P2) — Chat**: Depends on US1 (needs AppLayout). Independent of US2/US3/US5-US9.
- **US5 (P2) — Agents**: Can start after Phase 2. Independent of other stories.
- **US6 (P2) — Chores**: Can start after Phase 2. Independent of other stories.
- **US7 (P2) — Project Selector**: Depends on US1 (needs Sidebar). Independent of US2-US6.
- **US8 (P3) — Login**: Can start after Phase 2 (AuthGate exists). Independent of other stories.
- **US9 (P3) — Recent Interactions**: Depends on US1 (needs Sidebar). Independent of other stories.

### Within Each User Story

- Core structure before visual polish
- Layout components before page components
- Hooks before components that use them
- Story complete before moving to next priority

### Parallel Opportunities

- T003 + T004 (types and constants) can run in parallel
- T005–T010 (design system infra) are sequential within index.css but T005 (index.html) can parallel with T006–T010
- T015 + T016 + T017 (Sidebar, TopBar, Breadcrumb) can run in parallel
- T018 + T019 + T020 (page stubs) can run in parallel
- T027 + T028 (CowboyAvatar deletion + branding cleanup) can run in parallel
- T043 + T044 (AgentsPipelinePage + AgentsPage) can run in parallel
- T064 + T065 + T066 (cleanup tasks) can run in parallel
- **Across stories**: US1, US3, US2, US5, US6, US8 can all run in parallel after Phase 2

---

## Parallel Example: After Phase 2 Completion

```text
# These user stories can all start simultaneously (different files):

Stream A (Layout):  US1 → T021-T026 (Sidebar nav, collapse, TopBar wiring)
Stream B (Theme):   US3 → T027-T030 (Delete CowboyAvatar, audit warm classes)
Stream C (Board):   US2 → T031-T039 (ProjectsPage, IssueCard, BoardColumn enhancements)
Stream D (Agents):  US5 → T043-T047 (AgentsPipelinePage, AgentsPage)
Stream E (Chores):  US6 → T048-T050 (ChoresPage)
Stream F (Login):   US8 → T054-T056 (LoginPage styling, deep-link redirect)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 3 + 2)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T020)
3. Complete Phase 3: US1 — Navigation (T021–T026)
4. Complete Phase 4: US3 — Design System (T027–T030)
5. Complete Phase 5: US2 — Board (T031–T039)
6. **STOP and VALIDATE**: App is navigable, themed, board works — this is the MVP

### Incremental Delivery

1. Setup + Foundational → Shell renders with Solune theme
2. Add US1 → Navigable 6-page app → Demo!
3. Add US3 → Full visual redesign → Demo!
4. Add US2 → Enhanced board → Demo (MVP!)
5. Add US4 → Global chat → Demo
6. Add US5 + US6 → Agent + Chore pages → Demo
7. Add US7 + US8 + US9 → Project selector, login, recent → Demo
8. Polish → Tests pass, zero errors → Ship!

### Parallel Team Strategy

With multiple developers after Phase 2:

- Developer A: US1 (navigation) → US4 (chat, depends on layout) → US7 (project selector)
- Developer B: US2 (board enhancements) → US9 (recent interactions)
- Developer C: US3 (theme cleanup) → US5 (agents pages) → US6 (chores page) → US8 (login)

---

## Notes

- [P] tasks = different files, no dependencies on other in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new tests are created — FR-026 only requires existing tests to pass with updated fixtures (Phase 12)
- All existing hooks are preserved without modification — pages compose them
- Components are migrated by import/composition, not duplicated (per research R8)
