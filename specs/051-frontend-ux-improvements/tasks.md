# Tasks: Solune Frontend UX Improvements

**Input**: Design documents from `/specs/051-frontend-ux-improvements/`
**Prerequisites**: spec.md (user stories with priorities P1–P6), plan from parent issue context
**Tests**: No automated test tasks included — tests were not explicitly requested in the feature specification. Each user story includes independent manual test criteria and acceptance scenarios in the spec.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` for frontend code
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install the only new dependency and prepare shared utilities

- [ ] T001 Install `sonner` toast library in `solune/frontend/package.json`
- [ ] T002 [P] Create Skeleton base primitive in `solune/frontend/src/components/ui/skeleton.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add `<Toaster />` provider to `solune/frontend/src/layout/AppLayout.tsx` and style toasts to match the celestial theme (custom `toastOptions` with celestial colors, border, and shadow)
- [ ] T004 [P] Create reusable `CopyButton` component in `solune/frontend/src/components/ui/copy-button.tsx` (clipboard write with "Copied!" feedback state, used by US2 code blocks and message copy)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Action Feedback via Toast Notifications (Priority: P1) 🎯 MVP

**Goal**: Every user-initiated mutation in the app surfaces a toast notification with the correct severity (success, error, warning, info), auto-dismisses, and stacks when multiple fire rapidly.

**Independent Test**: Trigger any mutation (save a setting, add an agent, delete a workflow) and verify a themed toast appears with correct severity, auto-dismisses within 5 seconds (success) or persists until dismissed (error), and stacks when multiple toasts fire rapidly.

### Implementation for User Story 1

- [ ] T005 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/useSettingsForm.ts` — add success toast on save, error toast on failure
- [ ] T006 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/usePipelineConfig.ts` — add success/error toasts for pipeline save/update mutations
- [ ] T007 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/useAgentConfig.ts` — add success/error toasts for agent configuration mutations
- [ ] T008 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/useChores.ts` — add success/error toasts for chore create/update/delete mutations
- [ ] T009 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/useWorkflow.ts` — add success/error toasts for workflow mutations
- [ ] T010 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/useApps.ts` — add success/error toasts for app create/delete mutations
- [ ] T011 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/useAgents.ts` — add success/error toasts for agent add/remove mutations
- [ ] T012 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/useProjects.ts` — add success/error toasts for project mutations
- [ ] T013 [P] [US1] Wire toast notifications into `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — add success/error toasts for pipeline board mutations
- [ ] T014 [US1] Verify toast accessibility — screen reader announcements via `aria-live`, keyboard dismissal, max 3 visible toasts with oldest auto-dismissed

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — every mutation surfaces appropriate toast feedback

---

## Phase 4: User Story 2 — Chat Markdown and Code Block Rendering (Priority: P2)

**Goal**: AI chat messages render markdown with GFM support, code blocks have a copy button, and users can copy entire AI messages via a hover action. User messages remain plain text.

**Independent Test**: Send a chat message that triggers an AI response containing markdown with a fenced code block. Verify formatted text renders (bold, links, lists), the code block has a copy button that works, and a hover "Copy message" action appears on AI messages.

### Implementation for User Story 2

- [ ] T015 [US2] Create `MarkdownRenderer` component in `solune/frontend/src/components/chat/MarkdownRenderer.tsx` — wrap `react-markdown` with `remark-gfm`, custom renderers for code blocks (using `CopyButton` from T004), links (open in new tab), and styled containers matching the celestial theme
- [ ] T016 [US2] Update `solune/frontend/src/components/chat/MessageBubble.tsx` — render AI messages through `MarkdownRenderer`, keep user messages as plain text, add "Copy message" hover action using `CopyButton` that copies raw markdown content
- [ ] T017 [US2] Sanitize HTML in AI markdown responses — ensure raw HTML tags in markdown do not execute (configure `react-markdown` to disallow dangerous HTML)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 — Kanban Board Drag-and-Drop (Priority: P3)

**Goal**: Users can drag issue cards between board columns with optimistic UI updates, visual feedback (column highlighting, ghost card), and rollback on API error. Reference existing `AgentDragOverlay.tsx` pattern.

**Independent Test**: Drag an issue card from one column to a different column. Verify the card moves immediately (optimistic update), the backend API is called, the column highlights during drag, a ghost card overlay appears, and a success toast confirms the move. Simulate an API error and verify the card rolls back.

### Implementation for User Story 3

- [ ] T018 [US3] Create `useBoardDragDrop` hook in `solune/frontend/src/hooks/useBoardDragDrop.ts` — manage drag state, handle `onDragStart`/`onDragOver`/`onDragEnd` events, perform optimistic status update on drop, call backend API to update issue status, rollback on error with error toast, no-op when dropping on same column
- [ ] T019 [US3] Update `solune/frontend/src/components/board/ProjectBoard.tsx` — wrap board with `<DndContext>` and `<DragOverlay>` from `@dnd-kit/core`, wire `useBoardDragDrop` hook, render drag overlay following the `AgentDragOverlay.tsx` pattern in `solune/frontend/src/components/board/AgentDragOverlay.tsx`
- [ ] T020 [US3] Update `solune/frontend/src/components/board/IssueCard.tsx` — make card draggable using `useDraggable` from `@dnd-kit/core`, add drag handle, dim card when actively dragging, support keyboard drag activation (Enter/Space to activate, arrow keys to navigate, Enter to drop)
- [ ] T021 [US3] Update `solune/frontend/src/components/board/BoardColumn.tsx` — make column droppable using `useDroppable` from `@dnd-kit/core`, highlight column when a card is dragged over it (visual drop target indicator)
- [ ] T022 [US3] Create `BoardDragOverlay` component in `solune/frontend/src/components/board/BoardDragOverlay.tsx` — ghost card overlay that follows cursor during drag, styled to match celestial theme with reduced opacity

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 — Skeleton Loading States (Priority: P4)

**Goal**: Data-loading states show content-shaped skeleton placeholders instead of generic spinners, reducing perceived load time and eliminating layout shift. Keep `CelestialLoader` for route-level suspense only.

**Independent Test**: Throttle the network to slow loading. Navigate to the project board. Verify content-shaped skeletons appear instead of the spinner, and when data loads, content replaces skeletons without layout shift.

### Implementation for User Story 4

- [ ] T023 [P] [US4] Create `BoardColumnSkeleton` component in `solune/frontend/src/components/board/BoardColumnSkeleton.tsx` — skeleton matching `BoardColumn` dimensions with celestial-shimmer animation
- [ ] T024 [P] [US4] Create `IssueCardSkeleton` component in `solune/frontend/src/components/board/IssueCardSkeleton.tsx` — skeleton matching `IssueCard` dimensions with celestial-shimmer animation
- [ ] T025 [P] [US4] Create `AgentCardSkeleton` component in `solune/frontend/src/components/board/AgentCardSkeleton.tsx` — skeleton matching `AgentTile` dimensions with celestial-shimmer animation
- [ ] T026 [P] [US4] Create `ChatMessageSkeleton` component in `solune/frontend/src/components/chat/ChatMessageSkeleton.tsx` — skeleton matching `MessageBubble` dimensions with celestial-shimmer animation
- [ ] T027 [US4] Replace data-loading spinners with skeletons in `solune/frontend/src/components/board/ProjectBoardContent.tsx` — use `BoardColumnSkeleton` and `IssueCardSkeleton` instead of `CelestialLoader` for board data loading
- [ ] T028 [US4] Replace data-loading spinner with skeleton in `solune/frontend/src/components/chat/ChatInterface.tsx` — use `ChatMessageSkeleton` for chat history loading
- [ ] T029 [US4] Add accessible loading announcements to all skeleton components — `aria-busy="true"` on skeleton containers with `role="status"` and visually hidden "Loading" text for screen readers

**Checkpoint**: At this point, User Stories 1–4 should all work independently

---

## Phase 7: User Story 5 — Global Keyboard Shortcuts (Priority: P5)

**Goal**: Power users can navigate efficiently with keyboard shortcuts: `?` for help modal, `Ctrl+K` to focus chat, `1–5` for section navigation, `Escape` to close modals. Shortcut hints appear in tooltips.

**Independent Test**: Press `?` on any page (no input focused). Verify a shortcut help modal opens. Press `Ctrl+K` and verify the chat input receives focus (opening the chat panel if closed). Press `Escape` and verify the topmost modal closes.

### Implementation for User Story 5

- [ ] T030 [US5] Create `useGlobalShortcuts` hook in `solune/frontend/src/hooks/useGlobalShortcuts.ts` — listen on `document` keydown, implement `?` (shortcut help), `Ctrl+K`/`Cmd+K` (focus chat), `1–5` (section navigation), `Escape` (close modal), guard against firing when text input/textarea/contenteditable is focused (except `Escape` and `Ctrl+K`), suppress shortcuts when modals are open (except `Escape`)
- [ ] T031 [US5] Create `KeyboardShortcutModal` component in `solune/frontend/src/components/ui/keyboard-shortcut-modal.tsx` — accessible modal listing all available keyboard shortcuts, grouped by category (Navigation, Actions, Help), dismissible with `Escape`
- [ ] T032 [US5] Wire `useGlobalShortcuts` into `solune/frontend/src/layout/AppLayout.tsx` — activate global shortcuts at the layout level so they work on every page
- [ ] T033 [US5] Add shortcut hint tooltips to sidebar nav items in `solune/frontend/src/layout/AppLayout.tsx` — update tooltip content to include shortcut hint (e.g., "Board (2)")
- [ ] T034 [US5] Wire `Ctrl+K` to open chat panel and focus input — coordinate with chat panel open/close state in `solune/frontend/src/components/chat/ChatInterface.tsx`

**Checkpoint**: At this point, User Stories 1–5 should all work independently

---

## Phase 8: User Story 6 — Quick Wins (Priority: P6)

**Goal**: A collection of independent polish improvements: board filtering/sorting, onboarding tour progress, chat date separators, notification bell pulse, empty state enrichment, and `Ctrl+Enter` to send in chat.

**Independent Test**: Each sub-improvement tested independently — filter the board by a label; check tour shows "Step 2 of 9"; send messages across days and verify date separator; trigger unread notifications and verify bell animates; view empty board column for illustration; press `Ctrl+Enter` in chat.

### Implementation for User Story 6

- [ ] T035 [P] [US6] Add board filtering/sorting by assignee, label, and priority in `solune/frontend/src/components/board/BoardToolbar.tsx` and `solune/frontend/src/hooks/useBoardControls.ts` — add filter dropdowns to toolbar, update board hook to apply filters, show active filter state, add "Clear filters" action with friendly empty state when no issues match
- [ ] T036 [P] [US6] Add onboarding tour step progress indicator in `solune/frontend/src/components/onboarding/SpotlightTooltip.tsx` and `solune/frontend/src/components/onboarding/SpotlightTour.tsx` — display "Step X of N" in spotlight tooltip
- [ ] T037 [P] [US6] Add chat date separators in `solune/frontend/src/components/chat/ChatInterface.tsx` — insert a date separator label between messages from different calendar days
- [ ] T038 [P] [US6] Add notification bell pulse animation in `solune/frontend/src/layout/NotificationBell.tsx` — animate bell icon when unread count > 0 using CSS pulse animation
- [ ] T039 [P] [US6] Enrich empty board column states in `solune/frontend/src/components/board/ProjectBoardContent.tsx` and `solune/frontend/src/components/board/BoardColumn.tsx` — add celestial-themed illustration and suggested next step (e.g., "Create your first issue")
- [ ] T040 [P] [US6] Add `Ctrl+Enter` to send message in `solune/frontend/src/components/chat/ChatInterface.tsx` — listen for `Ctrl+Enter` keydown on the chat input and trigger send

**Checkpoint**: All user stories should now be independently functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Verify all toast notifications across the app — manually trigger every mutation type and confirm correct severity, auto-dismiss timing, stacking, and theme consistency
- [ ] T042 [P] Verify responsive behavior of all new components across 320px–1920px viewport range
- [ ] T043 Run accessibility audit on all new interactive elements — verify WCAG 2.1 AA compliance, screen reader announcements, keyboard navigation, and focus management
- [ ] T044 Performance review — ensure no unnecessary re-renders from drag-and-drop context, skeleton animations use GPU-accelerated properties, and toast notifications don't cause layout shifts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3–8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5 → P6)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Requires `sonner` from T001 and `<Toaster />` from T003.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Uses `CopyButton` from T004. Uses already-installed `react-markdown` and `remark-gfm`.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Integrates with US1 (toast on drag success/error) but is independently testable. Uses already-installed `@dnd-kit/core`.
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Uses `Skeleton` primitive from T002.
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) — No dependencies on other stories. May coordinate with chat panel state.
- **User Story 6 (P6)**: Can start after Foundational (Phase 2) — All sub-tasks are independent and can be cherry-picked in any order.

### Within Each User Story

- Models/primitives before services/hooks
- Hooks before components that consume them
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001, T002)
- All Foundational tasks marked [P] can run in parallel (T003, T004)
- Once Foundational phase completes, all user stories can start in parallel
- US1 tasks T005–T013 are all [P] — different hook files with no cross-dependencies
- US4 skeleton components T023–T026 are all [P] — different component files
- US6 tasks T035–T040 are all [P] — different component files with no cross-dependencies
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all toast integration tasks together (different hook files):
Task T005: "Wire toast into useSettingsForm.ts"
Task T006: "Wire toast into usePipelineConfig.ts"
Task T007: "Wire toast into useAgentConfig.ts"
Task T008: "Wire toast into useChores.ts"
Task T009: "Wire toast into useWorkflow.ts"
Task T010: "Wire toast into useApps.ts"
Task T011: "Wire toast into useAgents.ts"
Task T012: "Wire toast into useProjects.ts"
Task T013: "Wire toast into usePipelineBoardMutations.ts"
```

## Parallel Example: User Story 4

```bash
# Launch all skeleton components together (different component files):
Task T023: "Create BoardColumnSkeleton.tsx"
Task T024: "Create IssueCardSkeleton.tsx"
Task T025: "Create AgentCardSkeleton.tsx"
Task T026: "Create ChatMessageSkeleton.tsx"
```

## Parallel Example: User Story 6

```bash
# Launch all quick wins together (independent improvements):
Task T035: "Board filtering/sorting"
Task T036: "Tour progress indicator"
Task T037: "Chat date separators"
Task T038: "Notification bell pulse"
Task T039: "Empty state enrichment"
Task T040: "Ctrl+Enter to send"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (install `sonner`, create `Skeleton` primitive)
2. Complete Phase 2: Foundational (`<Toaster />` provider, `CopyButton`)
3. Complete Phase 3: User Story 1 — Toast Notifications
4. **STOP and VALIDATE**: Trigger every mutation type and confirm toasts appear correctly
5. Deploy/demo if ready — every mutation now provides visual feedback

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Toast Notifications) → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 (Chat Markdown) → Test independently → Deploy/Demo
4. Add User Story 3 (Kanban DnD) → Test independently → Deploy/Demo
5. Add User Story 4 (Skeleton States) → Test independently → Deploy/Demo
6. Add User Story 5 (Keyboard Shortcuts) → Test independently → Deploy/Demo
7. Add User Story 6 (Quick Wins) → Cherry-pick items → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Toast Notifications) — 10 tasks
   - Developer B: User Story 2 (Chat Markdown) — 3 tasks
   - Developer C: User Story 3 (Kanban DnD) — 5 tasks
3. After first wave completes:
   - Developer A: User Story 4 (Skeleton States) — 7 tasks
   - Developer B: User Story 5 (Keyboard Shortcuts) — 5 tasks
   - Developer C: User Story 6 (Quick Wins) — 6 tasks, all [P]
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Only new dependency: `sonner` (Phase 1) — `react-markdown`, `remark-gfm`, and `@dnd-kit` are already installed
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
