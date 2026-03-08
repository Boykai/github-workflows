# Tasks: Fix Screen Scrolling Getting Stuck Intermittently

**Input**: Design documents from `/specs/030-fix-scroll-stuck/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/components.md, quickstart.md

**Tests**: Unit tests for the `useScrollLock` hook are included per plan.md constitution check recommendation (IV. Test Optionality with Clarity). No other tests explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- All changes are frontend-only. No backend modifications needed.

## Phase 1: Setup

**Purpose**: Document the root cause and prepare the working branch

- [ ] T001 Document root cause analysis of scroll freeze (modal scroll-lock race condition per R1) in the PR description and specs/030-fix-scroll-stuck/plan.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the centralized scroll-lock hook that ALL user story implementations depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Create useScrollLock hook with module-level reference-counting in frontend/src/hooks/useScrollLock.ts
- [ ] T003 [P] Create unit tests for useScrollLock reference-counting logic in `frontend/src/hooks/__tests__/useScrollLock.test.ts`

**Checkpoint**: Foundation ready — `useScrollLock` hook available for all modal component updates

---

## Phase 3: User Story 1 — Reliable Vertical Scrolling on All Pages (Priority: P1) 🎯 MVP

**Goal**: Eliminate the modal scroll-lock race condition by replacing all 4 "always-on" modal components that unconditionally reset `document.body.style.overflow = ''` on close with the centralized `useScrollLock(true)` hook and separating keydown handlers into their own `useEffect`

**Independent Test**: Open any scrollable page, open a modal, close it, verify scroll works. Open two modals in sequence, close them in any order, verify scroll restores correctly after the last modal closes.

### Implementation for User Story 1

- [ ] T004 [P] [US1] Replace manual scroll lock with useScrollLock(true) and separate keydown listener into its own useEffect in frontend/src/components/board/IssueDetailModal.tsx
- [ ] T005 [P] [US1] Replace manual scroll lock with useScrollLock(true) and separate keydown listener into its own useEffect in frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T006 [P] [US1] Replace manual scroll lock with useScrollLock(true) and separate keydown listener into its own useEffect in frontend/src/components/board/CleanUpSummary.tsx
- [ ] T007 [P] [US1] Replace manual scroll lock with useScrollLock(true) and separate keydown listener into its own useEffect in frontend/src/components/board/CleanUpAuditHistory.tsx

**Checkpoint**: At this point, the 4 worst-offending modals (those that unconditionally reset overflow to `''`) are fixed. Scrolling should no longer freeze after closing these modals. User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Consistent Scrolling Across Browsers and Devices (Priority: P1)

**Goal**: Improve scroll performance across all browsers by adding `passive: true` to capture-phase scroll event listeners used for popover repositioning. Passive listeners tell the browser the handler will not call `preventDefault()`, allowing the browser to scroll immediately without waiting for the handler to complete.

**Independent Test**: Open each component with a scroll listener (notification bell, agent popover, model selector, stage card), scroll the page, and verify the popover repositions correctly without scroll lag across Chrome, Firefox, and Safari.

### Implementation for User Story 2

- [ ] T008 [P] [US2] Update scroll addEventListener to { capture: true, passive: true } and removeEventListener to { capture: true } in frontend/src/layout/NotificationBell.tsx
- [ ] T009 [P] [US2] Update scroll addEventListener to { capture: true, passive: true } and removeEventListener to { capture: true } in frontend/src/components/board/AddAgentPopover.tsx
- [ ] T010 [P] [US2] Update scroll addEventListener to { capture: true, passive: true } and removeEventListener to { capture: true } in frontend/src/components/pipeline/ModelSelector.tsx
- [ ] T011 [P] [US2] Update scroll addEventListener to { capture: true, passive: true } and removeEventListener to { capture: true } in frontend/src/components/pipeline/StageCard.tsx

**Checkpoint**: All scroll event listeners now use passive mode. Browser can optimize scroll input processing. Popover repositioning still works correctly. User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 — Scroll Stability During View and State Transitions (Priority: P2)

**Goal**: Ensure scroll behavior is correctly maintained through conditional modal transitions by replacing the 2 remaining "conditional" modal scroll-lock implementations (gated by `isOpen` / `showCopyDialog`) with `useScrollLock`. These components already stored `previousOverflow` but still suffered from nesting issues when multiple conditional modals overlapped.

**Independent Test**: Open the AgentIconPickerModal, close it, verify scroll works. Open the PipelineToolbar copy dialog, press Escape, verify scroll works. Open a board modal (US1) then open the icon picker (US3), close the icon picker first — verify scroll remains locked for the board modal.

### Implementation for User Story 3

- [ ] T012 [P] [US3] Replace manual scroll lock with useScrollLock(isOpen) in frontend/src/components/agents/AgentIconPickerModal.tsx
- [ ] T013 [P] [US3] Replace manual scroll lock with useScrollLock(showCopyDialog) and separate keydown listener into its own useEffect in frontend/src/components/pipeline/PipelineToolbar.tsx

**Checkpoint**: All 6 modal components now use the centralized useScrollLock hook. The modal scroll-lock race condition is fully eliminated. Scroll stability during transitions is guaranteed by reference counting.

---

## Phase 6: User Story 4 — No Regressions to Scroll-Dependent UI Components (Priority: P2)

**Goal**: Validate that all scroll-dependent UI components continue to function correctly after the scroll-lock and passive listener changes. Add defensive guards to prevent edge-case regressions.

**Independent Test**: Exercise each scroll-dependent component individually — scroll within dropdown menus, scroll through lists, drag items in drag-and-drop areas, trigger infinite scroll — and verify correct behavior.

### Implementation for User Story 4

- [ ] T014 [US4] Add defensive lockCount floor guard (prevent negative values) to useScrollLock cleanup in frontend/src/hooks/useScrollLock.ts
- [ ] T015 [US4] Run full Vitest test suite and verify zero regressions across all modified components in frontend/

**Checkpoint**: All scroll-dependent components verified. No regressions introduced. The full acceptance criteria from the parent issue are met.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final validation, and cleanup

- [ ] T016 [P] Add JSDoc documentation to useScrollLock hook explaining reference-counting behavior and usage in frontend/src/hooks/useScrollLock.ts
- [ ] T017 Run quickstart.md validation checklist to verify all implementation steps in specs/030-fix-scroll-stuck/quickstart.md
- [ ] T018 Final cross-browser verification (Chrome, Firefox, Safari desktop + mobile touch) per SC-002

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase (T002 — useScrollLock hook)
- **User Story 2 (Phase 4)**: Depends on Setup only — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational phase (T002 — useScrollLock hook) — can run in parallel with US1
- **User Story 4 (Phase 6)**: Depends on US1, US2, and US3 completion (validates all changes)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Setup (Phase 1) — Independent of other stories (passive listeners are unrelated to useScrollLock)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Can run in parallel with US1 (different files)
- **User Story 4 (P2)**: Depends on US1 + US2 + US3 — Validates all changes together

### Within Each User Story

- Models/hooks before component changes
- All [P] tasks within a story can run in parallel (they modify different files)
- Story complete before moving to validation (US4)

### Parallel Opportunities

- **US1 + US2 + US3 can all proceed in parallel** after Foundational phase completes (all modify different files)
- Within US1: T004, T005, T006, T007 are all [P] — different files, no dependencies
- Within US2: T008, T009, T010, T011 are all [P] — different files, no dependencies
- Within US3: T012 is [P] (different file from T013)
- T003 (tests) can run in parallel with any US1/US2/US3 task

---

## Parallel Example: User Story 1

```text
# After Foundational (T002) completes, launch all US1 tasks together:
Task T004: "Replace manual scroll lock in IssueDetailModal.tsx"
Task T005: "Replace manual scroll lock in CleanUpConfirmModal.tsx"
Task T006: "Replace manual scroll lock in CleanUpSummary.tsx"
Task T007: "Replace manual scroll lock in CleanUpAuditHistory.tsx"
# All modify different files — safe to parallelize
```

## Parallel Example: All User Stories

```text
# After Foundational (T002 + T003) completes, launch all stories in parallel:
# Developer A: US1 (T004-T007) — board modal components
# Developer B: US2 (T008-T011) — passive scroll listeners
# Developer C: US3 (T012-T013) — conditional modal components
# All modify different files — safe to parallelize
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002, T003) — CRITICAL: blocks US1 and US3
3. Complete Phase 3: User Story 1 (T004–T007)
4. **STOP and VALIDATE**: Test scroll behavior after opening/closing modals on the board page
5. Deploy/demo if ready — the core scroll freeze is fixed

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T004–T007) → Test scroll on board page → **MVP delivered!**
3. Add User Story 2 (T008–T011) → Test scroll performance across browsers
4. Add User Story 3 (T012–T013) → Test conditional modal transitions
5. Add User Story 4 (T014–T015) → Run full test suite, verify zero regressions
6. Polish (T016–T018) → Documentation, final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T004–T007) — board modal components
   - Developer B: User Story 2 (T008–T011) — passive scroll listeners
   - Developer C: User Story 3 (T012–T013) — conditional modal components
3. Stories complete and integrate independently
4. All developers: User Story 4 (T014–T015) — regression validation
5. Polish phase (T016–T018)

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after Foundational phase
- This is a frontend-only bug fix — 0 backend changes, 0 new dependencies
- 1 new file created: `frontend/src/hooks/useScrollLock.ts`
- 10 existing files modified (6 modal components + 4 scroll listener components)
- Root cause: Modal scroll-lock race condition (R1) — 6 components independently manipulating `document.body.style.overflow`
- Fix: Centralized `useScrollLock` hook with module-level reference-counting (R2)
- Performance improvement: Passive scroll listeners for capture-phase handlers (R3)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
