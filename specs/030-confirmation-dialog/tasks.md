# Tasks: Confirmation Dialog for Critical User Actions

**Input**: Design documents from `/specs/030-confirmation-dialog/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are omitted per Test Optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature is frontend-only — no backend changes required

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — no new dependencies, no new configuration; verify existing tooling

- [x] T001 Verify existing frontend dependencies (React 19.2, Tailwind CSS v4, lucide-react 0.577, class-variance-authority 0.7) are present in frontend/package.json
- [x] T002 [P] Verify existing UI primitives pattern in frontend/src/components/ui/ (button.tsx, card.tsx, input.tsx) to ensure new component follows conventions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core reusable component and hook that ALL user stories depend on — MUST be complete before any user story migration

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create ConfirmationDialog presentational component in frontend/src/components/ui/confirmation-dialog.tsx with ConfirmationDialogProps interface (isOpen, title, description, confirmLabel, cancelLabel, variant, onConfirm, onCancel)
- [x] T004 Implement three visual severity variants (danger, warning, info) in frontend/src/components/ui/confirmation-dialog.tsx using VARIANT_CONFIG map with AlertTriangle icon for danger/warning and Info icon for info from lucide-react
- [x] T005 Implement portal-based rendering via createPortal() in frontend/src/components/ui/confirmation-dialog.tsx with fixed-position overlay, semi-transparent backdrop (bg-black/50 backdrop-blur-sm), and centered dialog card
- [x] T006 Implement backdrop click-to-cancel and Escape key handler in frontend/src/components/ui/confirmation-dialog.tsx calling onCancel() for both interactions
- [x] T007 Add WCAG 2.1 AA accessibility attributes to frontend/src/components/ui/confirmation-dialog.tsx: role="alertdialog", aria-modal="true", aria-labelledby pointing to title h2 element, aria-describedby pointing to description p element
- [x] T008 Implement focus trap in frontend/src/components/ui/confirmation-dialog.tsx: Tab cycles between Cancel and Confirm buttons only, Shift+Tab reverses direction, focus moves to Cancel button on open
- [x] T009 Create ConfirmationContext, ConfirmationProvider, and useConfirmation hook in frontend/src/hooks/useConfirmation.tsx with Promise-based confirm() API returning Promise<boolean>
- [x] T010 Implement confirmation request queue in frontend/src/hooks/useConfirmation.tsx to prevent overlapping dialogs (FR-009): queue pending requests when dialog is already open, dequeue next on resolve
- [x] T011 Implement focus restoration in frontend/src/hooks/useConfirmation.tsx: capture document.activeElement before opening dialog, restore focus to trigger element after dialog closes
- [x] T012 Wrap application tree with ConfirmationProvider in frontend/src/App.tsx inside QueryClientProvider and wrapping all routes/providers

**Checkpoint**: Foundation ready — ConfirmationDialog renders correctly, useConfirmation() hook works, focus trap and accessibility attributes in place. User story migrations can now begin in parallel.

---

## Phase 3: User Story 1 — Confirmation Before Destructive Actions (Priority: P1) 🎯 MVP

**Goal**: Replace all `window.confirm()` calls on destructive delete actions with the new ConfirmationDialog, so users see a styled, accessible confirmation prompt before any deletion is executed.

**Independent Test**: Trigger any delete action (e.g., click "Delete" on an agent card) → styled confirmation dialog appears with danger variant → confirming executes the delete → cancelling aborts with no side effects.

### Implementation for User Story 1

- [x] T013 [P] [US1] Replace window.confirm() in handleDelete() in frontend/src/components/agents/AgentCard.tsx with useConfirmation() hook: variant 'danger', confirmLabel 'Remove', description includes agent name and PR consequence
- [x] T014 [P] [US1] Replace window.confirm() in handleDelete() in frontend/src/components/chores/ChoreCard.tsx with useConfirmation() hook: variant 'danger', confirmLabel 'Remove', description includes chore name and irreversibility warning
- [x] T015 [P] [US1] Replace window.confirm() in handleDelete() in frontend/src/pages/AgentsPipelinePage.tsx with useConfirmation() hook: variant 'danger', confirmLabel 'Delete', description warns action cannot be undone

**Checkpoint**: All destructive delete actions (3 call sites) now show the styled ConfirmationDialog with danger variant instead of browser-native confirm. Each dialog displays a clear description of what will be deleted and its consequences. Cancel aborts with no side effects.

---

## Phase 4: User Story 2 — Confirmation Before Irreversible Submissions (Priority: P1)

**Goal**: Replace the `window.confirm()` call for the bulk cleanup action (clearing pending agents) with the ConfirmationDialog, using a warning variant to communicate the scope of the bulk operation.

**Independent Test**: Click "Clear Pending" in the agents panel → styled confirmation dialog appears with warning variant → confirming clears the records → cancelling aborts with no side effects.

### Implementation for User Story 2

- [x] T016 [US2] Replace window.confirm() in handleClearPending() in frontend/src/components/agents/AgentsPanel.tsx with useConfirmation() hook: variant 'warning', confirmLabel 'Clear Records', description explains scope (stale SQLite rows only, no repository changes)

**Checkpoint**: The bulk cleanup action now shows a styled ConfirmationDialog with warning variant. User Story 2 is independently testable — triggering the clear pending action shows the dialog with appropriate messaging.

---

## Phase 5: User Story 3 — Reusable Confirmation Dialog Across the Application (Priority: P2)

**Goal**: Ensure the ConfirmationDialog component is truly reusable — verify it works across different contexts with different configurations (titles, descriptions, button labels, variants) while maintaining consistent look and feel.

**Independent Test**: Invoke the confirmation dialog from at least two different contexts (e.g., deleting an agent and clearing pending agents) and verify the dialog adapts its title, description, and button labels while maintaining consistent styling.

### Implementation for User Story 3

- [x] T017 [US3] Validate reusability by reviewing all 4 integration points (AgentCard.tsx, AgentsPanel.tsx, ChoreCard.tsx, AgentsPipelinePage.tsx) use the same useConfirmation() hook with different ConfirmationOptions and verify consistent dialog rendering
- [x] T018 [US3] Ensure ConfirmationDialog component in frontend/src/components/ui/confirmation-dialog.tsx handles edge cases: missing optional props default correctly (confirmLabel defaults to "Confirm", cancelLabel defaults to "Cancel", variant defaults to "info"), long description text overflows gracefully with scrollable content

**Checkpoint**: The reusable component is proven across 4 different call sites with 2 different variants (danger, warning), different labels, and different descriptions. Default props work correctly for edge cases.

---

## Phase 6: User Story 4 — Accessible Confirmation Dialog (Priority: P2)

**Goal**: Verify and finalize WCAG 2.1 AA compliance — focus trapping, keyboard navigation, screen reader announcements, and focus restoration all work correctly across all integration points.

**Independent Test**: Open the confirmation dialog using only keyboard navigation → verify screen reader announces dialog title and description → Tab cycles within dialog only → Escape closes and aborts → focus returns to the triggering element.

### Implementation for User Story 4

- [x] T019 [US4] Verify focus trap implementation in frontend/src/components/ui/confirmation-dialog.tsx works across all 4 call sites: Tab cycles between Cancel and Confirm buttons, Shift+Tab reverses, focus cannot escape to background content
- [x] T020 [US4] Verify focus restoration in frontend/src/hooks/useConfirmation.tsx: after dialog closes (confirm or cancel), focus returns to the button element that originally triggered the dialog across all 4 call sites
- [x] T021 [US4] Verify screen reader compatibility: role="alertdialog" causes announcement, aria-labelledby reads title text, aria-describedby reads description text, aria-modal="true" marks background as inert

**Checkpoint**: All WCAG 2.1 AA requirements verified — keyboard-only users and screen reader users can fully interact with the confirmation dialog.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all user stories

- [x] T022 Verify no regressions in existing custom dialogs (BulkModelUpdateDialog, CleanUpConfirmModal, ConfirmChoreModal, UnsavedChangesDialog) — they must continue to work unchanged
- [x] T023 [P] Verify single-dialog enforcement: rapidly trigger two destructive actions and confirm only one dialog appears at a time (queue behavior from T010)
- [x] T024 [P] Run TypeScript type check (npx tsc --noEmit) from frontend/ to confirm no type errors introduced
- [x] T025 [P] Run existing frontend test suite (npx vitest run) from frontend/ to confirm no test regressions
- [x] T026 Run quickstart.md verification checklist: dialog appears, cancel aborts, confirm executes, Escape cancels, backdrop cancels, severity variants display correctly, focus trap works, focus restoration works, screen reader attributes present, single dialog enforcement

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) completion
- **User Story 3 (Phase 5)**: Depends on User Stories 1 and 2 being complete (validates reusability across call sites)
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — accessibility is built into the component, but verification requires integration points from US1/US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories; can run in parallel with US1
- **User Story 3 (P2)**: Depends on US1 and US2 completion — validates reusability across multiple integration points
- **User Story 4 (P2)**: Can start verification after Foundational (Phase 2) — but full validation benefits from US1/US2 integration points being in place

### Within Each User Story

- Each `window.confirm()` replacement is a self-contained change in one file
- US1 tasks (T013, T014, T015) are all parallelizable — different files, no cross-dependencies
- US2 has a single task (T016) — independent file
- US3 and US4 are verification/validation phases

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- T003–T008 (dialog component tasks) are sequential within the file but T009–T011 (hook tasks) can begin in parallel once T003 is complete
- T013, T014, T015 (US1 migrations) can ALL run in parallel — each modifies a different file
- T016 (US2) can run in parallel with any US1 task
- T022, T023, T024, T025 (Polish) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all US1 migration tasks together (different files, no dependencies):
Task T013: "Replace window.confirm() in AgentCard.tsx"
Task T014: "Replace window.confirm() in ChoreCard.tsx"
Task T015: "Replace window.confirm() in AgentsPipelinePage.tsx"
```

## Parallel Example: Foundational Phase

```bash
# Component and hook can be developed in parallel:
# Stream 1 (component): T003 → T004 → T005 → T006 → T007 → T008
# Stream 2 (hook): T009 → T010 → T011
# T012 (App.tsx wrapping) depends on both streams completing
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify dependencies)
2. Complete Phase 2: Foundational (build ConfirmationDialog + useConfirmation hook)
3. Complete Phase 3: User Story 1 (replace 3 destructive delete confirmations)
4. **STOP and VALIDATE**: Test all 3 delete actions independently — styled dialog appears, confirm executes, cancel aborts
5. Deploy/demo if ready — users are already protected from accidental deletions

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (delete actions) → Test independently → Deploy (MVP! 🎯)
3. Add User Story 2 (bulk clear action) → Test independently → Deploy
4. Add User Story 3 (reusability validation) → Verify consistency → Deploy
5. Add User Story 4 (accessibility verification) → Run a11y audit → Deploy
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T013, T014, T015 — all parallelizable)
   - Developer B: User Story 2 (T016)
3. After US1 + US2: Developer A validates US3, Developer B validates US4
4. Both run Polish tasks in parallel

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 26 |
| **Phase 1 (Setup)** | 2 tasks |
| **Phase 2 (Foundational)** | 10 tasks |
| **Phase 3 (US1 — Destructive Actions)** | 3 tasks |
| **Phase 4 (US2 — Irreversible Submissions)** | 1 task |
| **Phase 5 (US3 — Reusability)** | 2 tasks |
| **Phase 6 (US4 — Accessibility)** | 3 tasks |
| **Phase 7 (Polish)** | 5 tasks |
| **Parallel opportunities** | 10 tasks marked [P] across phases |
| **New files** | 2 (confirmation-dialog.tsx, useConfirmation.ts) |
| **Modified files** | 5 (App.tsx, AgentCard.tsx, AgentsPanel.tsx, ChoreCard.tsx, AgentsPipelinePage.tsx) |
| **Suggested MVP scope** | Phase 1 + Phase 2 + Phase 3 (User Story 1 — 15 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No tests generated — tests not explicitly requested in spec (Test Optionality principle)
- No backend changes — this feature is entirely frontend
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
