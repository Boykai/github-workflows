# Tasks: Solune UX Improvements

**Input**: Design documents from `/specs/051-solune-ux-improvements/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are expected per spec success criteria (SC-009). Test tasks are included where existing test infrastructure supports them.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. 11 user stories mapped from spec.md (US-1 through US-11), organized by priority (P1 → P4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` at repository root
- All changes are frontend-only — no backend modifications required

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the shared `useMediaQuery` hook that all responsive user stories depend on. No new dependencies — uses existing `matchMedia` browser API.

- [ ] T001 Create `useMediaQuery` hook with `matchMedia` wrapper, SSR safety, and `change` event listener in `solune/frontend/src/hooks/useMediaQuery.ts`
- [ ] T002 Add unit tests for `useMediaQuery` hook covering mount, resize, cleanup, and SSR fallback in `solune/frontend/src/hooks/useMediaQuery.test.ts`

**Checkpoint**: `useMediaQuery` hook is available and tested. All responsive user stories can now proceed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No additional foundational tasks required. The `useMediaQuery` hook from Phase 1 is the sole shared prerequisite for responsive stories (US-1 through US-4). Phases 3+ can begin immediately after Phase 1 completion.

**⚠️ CRITICAL**: Phase 1 must be complete before any responsive story (US-1 through US-4) can begin. Non-responsive stories (US-5 through US-11) have no Phase 1 dependency and can start independently.

---

## Phase 3: User Story 1 — Mobile Chat Experience (Priority: P1) 🎯 MVP

**Goal**: Transform `ChatPopup` into a full-screen bottom-sheet overlay on mobile viewports (< 768px), preserving all desktop functionality.

**Independent Test**: Open chat at 320px viewport → full-screen overlay covering entire viewport, no horizontal scroll, all chat controls (input, send, close) fully usable.

### Implementation for User Story 1

- [ ] T003 [US1] Import `useMediaQuery` and add mobile detection to `ChatPopup` component in `solune/frontend/src/components/chat/ChatPopup.tsx`
- [ ] T004 [US1] Conditionally render full-screen layout (`fixed inset-0 z-50`) when `isMobile` is true, disabling drag-to-resize in `solune/frontend/src/components/chat/ChatPopup.tsx`
- [ ] T005 [US1] Ensure smooth transition between floating popup and bottom-sheet when viewport crosses 768px while chat is open in `solune/frontend/src/components/chat/ChatPopup.tsx`
- [ ] T006 [US1] Update existing ChatPopup tests to cover mobile bottom-sheet rendering and viewport transition in `solune/frontend/src/components/chat/ChatPopup.test.tsx`

**Checkpoint**: Chat opens as full-screen bottom-sheet on mobile, floating popup on desktop. Transition is smooth across breakpoint. All existing tests pass.

---

## Phase 4: User Story 2 — Sidebar Auto-Collapse on Mobile (Priority: P1)

**Goal**: Auto-collapse sidebar on mobile (< 768px), render as overlay with backdrop when expanded on mobile, restore desktop preference when viewport crosses above 768px.

**Independent Test**: Load any page at 375px → sidebar collapsed (icon-only). Tap toggle → overlay with backdrop. Tap outside → collapses. Resize to ≥768px → restores user's desktop preference.

### Implementation for User Story 2

- [ ] T007 [US2] Add `useMediaQuery` to `AppLayout` and implement mobile auto-collapse logic with desktop preference memory in `solune/frontend/src/layout/AppLayout.tsx`
- [ ] T008 [US2] Add mobile overlay rendering with backdrop (`fixed inset-y-0 left-0 z-40`) and outside-click/nav-item dismiss behavior in `solune/frontend/src/layout/Sidebar.tsx`
- [ ] T009 [US2] Update existing Sidebar/AppLayout tests to cover mobile auto-collapse, overlay behavior, and viewport transition in `solune/frontend/src/layout/Sidebar.test.tsx`

**Checkpoint**: Sidebar auto-collapses on mobile, expands as overlay with backdrop, and collapses on outside click or nav selection. Desktop preference is preserved across breakpoint transitions.

---

## Phase 5: User Story 3 — Responsive Issue Detail Modal (Priority: P2)

**Goal**: Make `IssueDetailModal` full-screen on mobile (< 768px) with fixed header and scrollable content area.

**Independent Test**: Tap an issue card at 375px → modal fills viewport (100vw × ≥95vh), header stays fixed, description scrolls. Close button and Escape key work.

### Implementation for User Story 3

- [ ] T010 [US3] Import `useMediaQuery` and conditionally apply full-screen layout (`fixed inset-0`) with fixed header and scrollable body on mobile in `solune/frontend/src/components/board/IssueDetailModal.tsx`
- [ ] T011 [US3] Update existing IssueDetailModal tests to cover full-screen mobile rendering, fixed header, and close behavior in `solune/frontend/src/components/board/IssueDetailModal.test.tsx`

**Checkpoint**: Issue modal is full-screen with sticky header on mobile, centered dialog on desktop. No layout regressions.

---

## Phase 6: User Story 4 — Mobile-Friendly Board Toolbar (Priority: P2)

**Goal**: Adapt `BoardToolbar` to a compact layout (icon-only buttons or collapsible menu) on mobile viewports to prevent horizontal overflow.

**Independent Test**: View board toolbar at 375px → compact layout, no horizontal overflow, all filter/sort/group controls accessible, active filter indicator visible.

### Implementation for User Story 4

- [ ] T012 [US4] Import `useMediaQuery` and switch to icon-only buttons or collapsible overflow menu on mobile in `solune/frontend/src/components/board/BoardToolbar.tsx`
- [ ] T013 [US4] Add active filter indicator (badge count or highlighted icon) visible in mobile compact layout in `solune/frontend/src/components/board/BoardToolbar.tsx`
- [ ] T014 [US4] Update existing BoardToolbar tests to cover compact mobile layout and active filter indicator in `solune/frontend/src/components/board/BoardToolbar.test.tsx`

**Checkpoint**: Board toolbar fits within narrow viewports, all controls are accessible, and active filters are indicated. No horizontal overflow at 375px.

---

## Phase 7: User Story 5 — Skeleton Loaders for Catalog Pages (Priority: P2)

**Goal**: Replace generic spinners with skeleton placeholders matching each catalog page's layout during data loading. Uses existing `Skeleton` component with `shimmer` variant.

**Independent Test**: Throttle network to Slow 3G → navigate to each catalog page → skeleton rows/cards visible during load → smooth transition to content with zero layout shift.

### Implementation for User Story 5

- [ ] T015 [P] [US5] Add skeleton loader layout (6 list-row placeholders, shimmer variant) to `AgentsPage` loading state in `solune/frontend/src/pages/AgentsPage.tsx`
- [ ] T016 [P] [US5] Add skeleton loader layout (6 list-row placeholders, shimmer variant) to `ToolsPage` loading state in `solune/frontend/src/pages/ToolsPage.tsx`
- [ ] T017 [P] [US5] Add skeleton loader layout (4 list-row placeholders, shimmer variant) to `ChoresPage` loading state in `solune/frontend/src/pages/ChoresPage.tsx`
- [ ] T018 [P] [US5] Add skeleton loader layout (4 card-grid placeholders, shimmer variant) to `AppsPage` loading state in `solune/frontend/src/pages/AppsPage.tsx`
- [ ] T019 [P] [US5] Update existing page tests to verify skeleton placeholders render during loading state in `solune/frontend/src/pages/AgentsPage.test.tsx`, `ToolsPage.test.tsx`, `ChoresPage.test.tsx`, `AppsPage.test.tsx`

**Checkpoint**: All four catalog pages show skeleton placeholders during loading. Transition to content is smooth with zero layout shift. Existing tests pass.

---

## Phase 8: User Story 6 — Optimistic Updates for Drag-Drop and App Actions (Priority: P3)

**Goal**: Add `onMutate`/`onError`/`onSettled` optimistic update pattern to board drag-drop and app start/stop mutations via TanStack Query. Visual feedback < 100ms, automatic rollback on server error with error toast.

**Independent Test**: Drag card with 2s network delay → card moves instantly. Fail server → card snaps back with error toast. Click Start with delay → instant "Starting" state. Fail → reverts with error toast.

### Implementation for User Story 6

- [ ] T020 [P] [US6] Implement optimistic update in board drag-drop mutation: snapshot board columns in `onMutate`, move card in cache, restore on `onError` with `toast.error`, invalidate on `onSettled` in `solune/frontend/src/hooks/useBoardDragDrop.ts`
- [ ] T021 [P] [US6] Implement optimistic update in app start/stop mutations: snapshot app status in `onMutate`, set to 'starting'/'stopping' in cache, restore on `onError` with `toast.error`, invalidate on `onSettled` in `solune/frontend/src/hooks/useApps.ts`
- [ ] T022 [US6] Update existing `useBoardDragDrop` and `useApps` tests to cover optimistic update, rollback on error, and cache invalidation in `solune/frontend/src/hooks/useBoardDragDrop.test.ts` and `solune/frontend/src/hooks/useApps.test.ts`

**Checkpoint**: Board drag-drop and app start/stop have instant visual feedback. Server errors trigger automatic rollback and error toasts. Existing mutation behavior is preserved on success.

---

## Phase 9: User Story 7 — Standardized Toast Notifications (Priority: P3)

**Goal**: Unify all mutation feedback to Sonner `toast.success()`/`toast.error()` pattern. Remove manual `successMessage`/`actionError` state from `AppsPage`. Ensure all mutation hooks (agents, tools, chores, apps) use consistent toast patterns.

**Independent Test**: Perform CRUD on agents, tools, chores, apps → each action produces a consistent toast notification. No inline success/error messages remain.

### Implementation for User Story 7

- [ ] T023 [US7] Remove `successMessage`/`actionError` state and ref-based timer from `AppsPage`, replace with toast calls from mutation hooks in `solune/frontend/src/pages/AppsPage.tsx`
- [ ] T024 [P] [US7] Ensure all mutation callbacks in `useApps` hook use `toast.success()`/`toast.error()` from Sonner for create/update/delete/start/stop feedback in `solune/frontend/src/hooks/useApps.ts`
- [ ] T025 [P] [US7] Verify and standardize toast notification pattern in `useAgents` hook (`onSuccess → toast.success`, `onError → toast.error`) in `solune/frontend/src/hooks/useAgents.ts`
- [ ] T026 [P] [US7] Verify and standardize toast notification pattern in `useTools` hook in `solune/frontend/src/hooks/useTools.ts`
- [ ] T027 [P] [US7] Verify and standardize toast notification pattern in `useChores` hook in `solune/frontend/src/hooks/useChores.ts`
- [ ] T028 [US7] Update existing tests to verify toast notification consistency across all mutation hooks in relevant test files

**Checkpoint**: All create/update/delete mutations across agents, tools, chores, and apps produce consistent Sonner toast notifications. No inline state-based feedback remains in `AppsPage`.

---

## Phase 10: User Story 8 — Actionable Empty States for Catalog Pages (Priority: P3)

**Goal**: Create a reusable `EmptyState` component and render it on catalog pages when a project is selected but the list is empty. Each empty state includes an icon, title, description, and CTA button.

**Independent Test**: Select a project with no agents → empty state with "Create your first agent" CTA displayed. Click CTA → create dialog opens.

### Implementation for User Story 8

- [ ] T029 [US8] Create reusable `EmptyState` component accepting `icon`, `title`, `description`, `actionLabel`, `onAction` props with celestial design tokens in `solune/frontend/src/components/common/EmptyState.tsx`
- [ ] T030 [P] [US8] Render `EmptyState` in `AgentsPage` when project is selected but agents list is empty, with agent-specific copy and create CTA in `solune/frontend/src/pages/AgentsPage.tsx`
- [ ] T031 [P] [US8] Render `EmptyState` in `ToolsPage` when project is selected but tools list is empty, with tool-specific copy and create CTA in `solune/frontend/src/pages/ToolsPage.tsx`
- [ ] T032 [P] [US8] Render `EmptyState` in `ChoresPage` when project is selected but chores list is empty, with chore-specific copy and create CTA in `solune/frontend/src/pages/ChoresPage.tsx`
- [ ] T033 [US8] Add unit tests for `EmptyState` component and update page tests to verify empty state rendering in `solune/frontend/src/components/common/EmptyState.test.tsx`

**Checkpoint**: All three catalog pages (Agents, Tools, Chores) show actionable empty states when list is empty. CTA buttons open the create dialog. EmptyState component is tested.

---

## Phase 11: User Story 9 — Text Search on Board and Catalog Pages (Priority: P4)

**Goal**: Add text search input to `BoardToolbar` and catalog pages. Client-side filtering with 150ms debounce. Case-insensitive substring match against title/name and description fields.

**Independent Test**: Type search term on board → only matching issues shown. Clear → all items restored. No matches → "No results found" message. Response within 300ms for ≤500 items.

### Implementation for User Story 9

- [ ] T034 [US9] Add search input field to `BoardToolbar` with local state and 150ms debounce, filtering issues by title/description in `solune/frontend/src/components/board/BoardToolbar.tsx`
- [ ] T035 [P] [US9] Add search input to `AgentsPage` with 150ms debounce, filtering agents by name/description in `solune/frontend/src/pages/AgentsPage.tsx`
- [ ] T036 [P] [US9] Add search input to `ToolsPage` with 150ms debounce, filtering tools by name/description in `solune/frontend/src/pages/ToolsPage.tsx`
- [ ] T037 [P] [US9] Add search input to `ChoresPage` with 150ms debounce, filtering chores by name/description in `solune/frontend/src/pages/ChoresPage.tsx`
- [ ] T038 [US9] Add "No results found" message display when search term matches zero items across board and catalog pages
- [ ] T039 [US9] Update existing BoardToolbar and catalog page tests to cover search filtering, clear behavior, and no-results state in relevant test files

**Checkpoint**: Board and catalog pages support text search. Search filters items instantly (within 300ms). Clearing search restores all items. Empty results show helpful message.

---

## Phase 12: User Story 10 — Extended Onboarding Tour (Priority: P4)

**Goal**: Add 4 new tour steps (Tools, Chores, Settings, Apps) to the existing `SpotlightTour`, extending from 9 to 13 steps. Update `TOTAL_STEPS` constant.

**Independent Test**: Trigger onboarding tour → all 13 steps display correctly, new steps highlight correct sidebar items. Skip and complete behaviors work correctly with updated total.

### Implementation for User Story 10

- [ ] T040 [P] [US10] Add 4 new `TOUR_STEPS` entries (Steps 10–13: Tools, Chores, Settings, Apps) with `targetSelector`, `title`, `description`, `icon`, and `placement` in `solune/frontend/src/components/onboarding/SpotlightTour.tsx`
- [ ] T041 [P] [US10] Update `TOTAL_STEPS` constant from `9` to `13` in `solune/frontend/src/hooks/useOnboarding.tsx`
- [ ] T042 [US10] Update existing onboarding tests to verify all 13 steps render correctly and tour completion works with updated total in `solune/frontend/src/hooks/useOnboarding.test.tsx` and `solune/frontend/src/components/onboarding/SpotlightTour.test.tsx`

**Checkpoint**: Onboarding tour walks through all 13 steps including new pages. Tour completion and skip behaviors work correctly with the extended step count.

---

## Phase 13: User Story 11 — Undo/Redo in Pipeline Builder (Priority: P4)

**Goal**: Implement undo/redo state snapshot stack in `usePipelineConfig`. Max 50 entries, Ctrl+Z/Ctrl+Shift+Z keyboard shortcuts, stack clears on pipeline load/discard/create. Each operation completes in < 200ms.

**Independent Test**: Make pipeline changes → Ctrl+Z undoes each change in reverse order → Ctrl+Shift+Z redoes. New change after undo clears redo stack. Load/discard pipeline → stacks cleared. 50+ actions → oldest dropped silently.

### Implementation for User Story 11

- [ ] T043 [US11] Implement undo/redo wrapper around existing `pipelineReducer` with `undoStack` (max 50), `redoStack`, and fork behavior in `solune/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T044 [US11] Register Ctrl+Z (Cmd+Z) and Ctrl+Shift+Z (Cmd+Shift+Z) keyboard event listeners for undo/redo actions in `solune/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T045 [US11] Clear both undo/redo stacks on pipeline load, discard, and create operations in `solune/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T046 [US11] Export `canUndo` and `canRedo` boolean flags for UI controls (disabled state) in `solune/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T047 [US11] Update existing pipeline config tests to cover undo, redo, stack overflow (50+ entries), fork behavior, and stack clearing in `solune/frontend/src/hooks/usePipelineConfig.test.ts`

**Checkpoint**: Pipeline builder supports undo/redo with Ctrl+Z/Ctrl+Shift+Z. Stack depth is capped at 50. Stacks clear on load/discard/create. All existing pipeline tests pass.

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cross-cutting improvements that affect multiple user stories.

- [ ] T048 [P] Run full unit test suite (`npx vitest run`) and fix any regressions across all modified files
- [ ] T049 [P] Run TypeScript type check (`npx tsc --noEmit`) and fix any type errors
- [ ] T050 [P] Run ESLint (`npx eslint .`) and fix any lint violations in modified files
- [ ] T051 Run production build (`npm run build`) and verify successful completion
- [ ] T052 Manual responsive testing at 320px, 375px, 768px, 1024px viewports for all modified components
- [ ] T053 Verify all mobile transitions are smooth when resizing across the 768px breakpoint
- [ ] T054 Run quickstart.md verification checklist to confirm all implementation steps are complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: N/A — no foundational tasks beyond Phase 1
- **User Stories 1–4 (Phases 3–6)**: Depend on Phase 1 completion (`useMediaQuery` hook)
- **User Stories 5–11 (Phases 7–13)**: No Phase 1 dependency — can start independently in parallel
- **Polish (Phase 14)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US-1 (P1)**: Depends on Phase 1 (useMediaQuery). No dependencies on other stories.
- **US-2 (P1)**: Depends on Phase 1 (useMediaQuery). No dependencies on other stories.
- **US-3 (P2)**: Depends on Phase 1 (useMediaQuery). No dependencies on other stories.
- **US-4 (P2)**: Depends on Phase 1 (useMediaQuery). No dependencies on other stories.
- **US-5 (P2)**: No dependencies on Phase 1 or other stories. Uses existing `Skeleton` component.
- **US-6 (P3)**: No dependencies on other stories. Uses existing TanStack Query patterns.
- **US-7 (P3)**: No dependencies on other stories. Uses existing Sonner library.
- **US-8 (P3)**: No dependencies on other stories. Creates new `EmptyState` component.
- **US-9 (P4)**: Shares file with US-4 (`BoardToolbar.tsx`). If working in parallel, coordinate changes. Otherwise, US-4 should complete first.
- **US-10 (P4)**: No dependencies on other stories.
- **US-11 (P4)**: No dependencies on other stories.

### Within Each User Story

- Models/hooks before components (where applicable)
- Core implementation before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

**Independent story groups** (no file conflicts):
- **Group A** (Responsive — requires Phase 1): US-1, US-2, US-3 can run in parallel (different files)
- **Group B** (Performance): US-5 tasks (T015–T018) can all run in parallel (different pages)
- **Group C** (Consistency): US-7 tasks (T024–T027) can all run in parallel (different hooks)
- **Group D** (Empty states): US-8 tasks (T030–T032) can all run in parallel (different pages)
- **Group E** (Search): US-9 tasks (T035–T037) can all run in parallel (different pages)
- **Group F** (Independent): US-6, US-10, US-11 can all run in parallel (no shared files)

**File conflict zones** (serialize these):
- `BoardToolbar.tsx`: US-4 (T012–T013) then US-9 (T034) — same file, different concerns
- `AgentsPage.tsx`, `ToolsPage.tsx`, `ChoresPage.tsx`: US-5, US-8, US-9 touch the same files — implement in story order or coordinate changes
- `useApps.ts`: US-6 (T021) and US-7 (T024) — same file, different mutation lifecycle stages
- `AppsPage.tsx`: US-5 (T018) and US-7 (T023) — same file, different concerns

---

## Parallel Example: User Story 5

```bash
# Launch all skeleton loader tasks in parallel (different files, no dependencies):
Task T015: "Add skeleton loaders to AgentsPage in solune/frontend/src/pages/AgentsPage.tsx"
Task T016: "Add skeleton loaders to ToolsPage in solune/frontend/src/pages/ToolsPage.tsx"
Task T017: "Add skeleton loaders to ChoresPage in solune/frontend/src/pages/ChoresPage.tsx"
Task T018: "Add skeleton loaders to AppsPage in solune/frontend/src/pages/AppsPage.tsx"
```

## Parallel Example: User Story 7

```bash
# Launch all toast standardization tasks in parallel (different hooks):
Task T025: "Standardize toasts in useAgents in solune/frontend/src/hooks/useAgents.ts"
Task T026: "Standardize toasts in useTools in solune/frontend/src/hooks/useTools.ts"
Task T027: "Standardize toasts in useChores in solune/frontend/src/hooks/useChores.ts"
```

## Parallel Example: Cross-Story Independence

```bash
# These story groups can proceed in parallel (no shared files):
# Developer A: US-1 (ChatPopup responsive)
# Developer B: US-5 (Skeleton loaders)
# Developer C: US-11 (Pipeline undo/redo)
# Developer D: US-10 (Onboarding tour extension)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (`useMediaQuery` hook)
2. Complete Phase 3: US-1 — Mobile Chat Experience
3. Complete Phase 4: US-2 — Sidebar Auto-Collapse
4. **STOP and VALIDATE**: Test mobile responsiveness independently at 320px, 375px viewports
5. Deploy/demo if ready — core mobile experience is functional

### Incremental Delivery

1. Complete Phase 1 → `useMediaQuery` hook ready
2. Add US-1 + US-2 (P1) → Test independently → Deploy/Demo (**MVP!** — mobile usable)
3. Add US-3 + US-4 (P2) → Test independently → Deploy/Demo (full mobile responsive)
4. Add US-5 (P2) → Test independently → Deploy/Demo (perceived performance)
5. Add US-6 + US-7 + US-8 (P3) → Test independently → Deploy/Demo (interaction polish)
6. Add US-9 + US-10 + US-11 (P4) → Test independently → Deploy/Demo (discoverability)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. All developers: Complete Phase 1 (Setup) together
2. Once Phase 1 is done:
   - **Developer A**: US-1 (ChatPopup) → US-3 (IssueDetailModal)
   - **Developer B**: US-2 (Sidebar) → US-4 (BoardToolbar)
   - **Developer C**: US-5 (Skeletons) → US-6 (Optimistic updates)
   - **Developer D**: US-7 (Toasts) → US-8 (Empty states)
3. After P1–P3 stories complete:
   - **Developer A**: US-9 (Search)
   - **Developer B**: US-10 (Onboarding tour)
   - **Developer C**: US-11 (Undo/redo)
4. Stories complete and integrate independently — serialize only on shared files

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- All changes are frontend-only (no backend API changes needed)
- Single breakpoint (768px) for all responsive behaviors
- No new dependencies — uses existing libraries (Sonner, @dnd-kit, TanStack Query, Tailwind, Skeleton)
- Two new files: `useMediaQuery.ts` (shared hook) and `EmptyState.tsx` (shared component)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
