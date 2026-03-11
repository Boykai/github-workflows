# Tasks: Add Confirmation Step to Critical Actions

**Input**: Design documents from `/specs/035-confirm-critical-actions/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Tests are omitted per constitution principle IV (Test Optionality). Existing test coverage for `useConfirmation` and `ConfirmationDialog` is sufficient.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- All changes are frontend-only — no backend modifications required

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing confirmation infrastructure and project build

- [x] T001 Verify frontend project builds cleanly and existing confirmation tests pass by running `npm run type-check && npm run test` in `frontend/`
- [x] T002 Audit all current `useConfirmation` call sites across `frontend/src/` to document which critical actions already have confirmation prompts and which do not

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Harden the core confirmation infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Add `aria-live="assertive"` region wrapping the error display area in `frontend/src/components/ui/confirmation-dialog.tsx` so screen readers announce errors immediately
- [x] T004 [P] Add `aria-live="polite"` region wrapping the loading indicator text ("Processing…") in `frontend/src/components/ui/confirmation-dialog.tsx`
- [x] T005 [P] Add `aria-disabled="true"` attribute to confirm and cancel buttons during loading state in `frontend/src/components/ui/confirmation-dialog.tsx`
- [x] T006 Verify `useConfirmation` queuing robustness in `frontend/src/hooks/useConfirmation.tsx` — ensure queue items preserve their `resolve` reference across React re-renders and that unmounting resolves pending promises with `false`
- [x] T007 Verify that Escape key and backdrop click are blocked while `isLoading` is `true` in `frontend/src/hooks/useConfirmation.tsx`

**Checkpoint**: Core confirmation infrastructure is accessibility-hardened and queuing-robust — user story implementation can now begin

---

## Phase 3: User Story 1 — Confirmation Before Destructive Deletion (Priority: P1) 🎯 MVP

**Goal**: Ensure all destructive deletion actions display a confirmation prompt before executing, and canceling leaves the system unchanged

**Independent Test**: Trigger a delete action on any entity (agent, chore, pipeline, tool) and verify that a confirmation prompt appears before execution; cancel and verify the entity is unchanged

### Implementation for User Story 1

- [x] T008 [US1] Add `useConfirmation` import and wrap the `handleDelete` function in `frontend/src/pages/AgentsPipelinePage.tsx` with a confirmation prompt (title: "Delete Pipeline", variant: `danger`, confirmLabel: "Yes, Delete") before calling `pipelineConfig.deletePipeline()`
- [x] T009 [US1] Refactor tool deletion in `frontend/src/components/tools/ToolsPanel.tsx` — remove the ad-hoc custom modal JSX (fixed overlay `<div>` with inline "Cancel" / "Delete anyway" buttons), remove `deleteConfirmId` state variable, and remove `handleConfirmDelete` function
- [x] T010 [US1] Add `useConfirmation` hook to `frontend/src/components/tools/ToolsPanel.tsx` and implement the initial tool deletion confirmation (title: "Delete Tool", variant: `danger`, confirmLabel: "Yes, Delete") before calling `deleteTool({ confirm: false })`
- [x] T011 [US1] Implement the second-step confirmation in `frontend/src/components/tools/ToolsPanel.tsx` for tools with affected agents — show the agent list in the description, use title "Tool In Use", variant `danger`, confirmLabel "Delete Anyway", and `onConfirm` callback calling `deleteTool({ confirm: true })`
- [x] T012 [US1] Verify that canceling any confirmation prompt (agent, chore, pipeline, tool, repo MCP) leaves the application state completely unchanged — no mutations fired, no UI side effects

**Checkpoint**: All destructive deletion actions now require explicit confirmation. User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 — Clear and Contextual Confirmation Messaging (Priority: P1)

**Goal**: Ensure every confirmation prompt has a specific title naming the action, a body describing consequences, and an action-specific confirm button label

**Independent Test**: Trigger each type of critical action and verify the prompt title, body text, and button labels match the standardized messaging catalog in `specs/035-confirm-critical-actions/contracts/components.md`

### Implementation for User Story 2

- [x] T013 [US2] Audit and update the agent deletion confirmation message in `frontend/src/components/agents/AgentCard.tsx` to match the standardized pattern: title "Delete Agent", description including PR creation context and "cannot be undone", confirm label "Delete"
- [x] T014 [P] [US2] Audit and update the chore deletion confirmation message in `frontend/src/components/chores/ChoreCard.tsx` to match the standardized pattern: title "Delete Chore", description "Remove chore '{name}'? This cannot be undone.", confirm label "Delete"
- [x] T015 [P] [US2] Audit and update the repo MCP server deletion confirmation message in `frontend/src/components/tools/ToolsPanel.tsx` to match the standardized pattern: title "Delete Repository MCP", description "Remove MCP server '{name}' from the repository config files?", confirm label "Delete"
- [x] T016 [US2] Verify that the pipeline deletion confirmation (T008), tool deletion confirmations (T010, T011), and all other prompts use the exact messaging from the standardized catalog

**Checkpoint**: All confirmation prompts use clear, contextual, standardized messaging. User Story 2 is independently verifiable.

---

## Phase 5: User Story 3 — Accessible Confirmation Experience (Priority: P1)

**Goal**: Ensure all confirmation dialogs are fully keyboard-navigable, focus-trapped, screen-reader-compatible, and meet WCAG 2.1 AA

**Independent Test**: Trigger a confirmation prompt using only the keyboard and verify: Tab cycles between buttons (focus trapped), Escape dismisses the dialog, screen reader announces title and description, focus returns to the triggering element on dismiss

### Implementation for User Story 3

- [x] T017 [US3] Audit `frontend/src/components/board/CleanUpConfirmModal.tsx` — verify `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `aria-describedby` attributes are present on the modal container; add any missing attributes
- [x] T018 [US3] Verify focus trapping in `frontend/src/components/board/CleanUpConfirmModal.tsx` — ensure Tab/Shift+Tab cycles within the modal and does not escape to background content; add focus trap logic if missing
- [x] T019 [US3] Add focus restoration to `frontend/src/components/board/CleanUpConfirmModal.tsx` — on close, focus should return to the "Clean Up" button that triggered the modal
- [x] T020 [P] [US3] Audit `frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — verify `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby` attributes are present; add any missing attributes
- [x] T021 [P] [US3] Verify focus trapping in `frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — ensure Tab cycles between the three buttons (Save, Discard, Cancel) and does not escape
- [x] T022 [US3] Verify that the `ConfirmationDialog` accessibility enhancements from Phase 2 (T003–T005) work correctly with screen readers — error announcements, loading announcements, and button disabled states

**Checkpoint**: All dialogs (ConfirmationDialog, CleanUpConfirmModal, UnsavedChangesDialog) meet WCAG 2.1 AA accessibility requirements. User Story 3 is independently testable.

---

## Phase 6: User Story 4 — Protection Against Rapid or Duplicate Submissions (Priority: P2)

**Goal**: Prevent duplicate action execution when users rapidly click or double-click the confirm button; show loading state during async operations

**Independent Test**: Trigger a confirmation, click the confirm button rapidly multiple times, and verify the action executes only once with a loading indicator shown

### Implementation for User Story 4

- [x] T023 [US4] Verify that the `isLoading` state in `frontend/src/hooks/useConfirmation.tsx` correctly disables the confirm button and shows a loading spinner when `onConfirm` is an async operation
- [x] T024 [US4] Verify that cancel and Escape are blocked while `isLoading` is `true` in `frontend/src/hooks/useConfirmation.tsx` — the user must wait for the in-progress action to complete or fail before dismissing
- [x] T025 [P] [US4] Verify that boolean-result consumers (AgentCard, ChoreCard) have `isPending` mutation guards on their trigger buttons in `frontend/src/components/agents/AgentCard.tsx` and `frontend/src/components/chores/ChoreCard.tsx` to prevent double-click during the mutation window
- [x] T026 [US4] Verify that the tool deletion `onConfirm` callback (T011) properly shows loading state during the `deleteTool({ confirm: true })` API call in `frontend/src/components/tools/ToolsPanel.tsx`

**Checkpoint**: All confirmation flows prevent duplicate submissions and show appropriate loading states. User Story 4 is independently testable.

---

## Phase 7: User Story 5 — Unsaved Changes Warning Before Navigation (Priority: P2)

**Goal**: Warn users about unsaved changes when they attempt to navigate away from an editor with modifications

**Independent Test**: Make edits to a pipeline configuration, attempt to navigate away, and verify the warning prompt appears with save/discard/cancel options

### Implementation for User Story 5

- [x] T027 [US5] Verify that `useUnsavedChanges` hook in `frontend/src/hooks/useUnsavedChanges.ts` correctly triggers `beforeunload` for browser close/refresh and `useBlocker` for SPA navigation when `isDirty` is `true`
- [x] T028 [US5] Verify that `UnsavedChangesDialog` in `frontend/src/components/pipeline/UnsavedChangesDialog.tsx` offers three options (Save, Discard, Cancel) and each option behaves correctly: Save → saves and navigates, Discard → discards and navigates, Cancel → stays on page
- [x] T029 [US5] Verify that the accessibility enhancements from T020–T021 apply to the unsaved changes flow — dialog is accessible, focus-trapped, and keyboard-navigable

**Checkpoint**: Unsaved changes warning is functional and accessible. User Story 5 is independently testable.

---

## Phase 8: User Story 6 — Repository Cleanup Confirmation with Impact Summary (Priority: P3)

**Goal**: Ensure repository cleanup operations display a detailed impact summary before execution

**Independent Test**: Initiate a repository cleanup, verify the preflight check runs, and confirm the impact summary (branches, PRs, orphaned issues) is displayed before execution

### Implementation for User Story 6

- [x] T030 [US6] Verify that `CleanUpConfirmModal` in `frontend/src/components/board/CleanUpConfirmModal.tsx` correctly displays categorized impact data (branches to delete, PRs to close, orphaned issues) from the preflight response
- [x] T031 [US6] Verify that canceling the cleanup confirmation in `frontend/src/components/board/CleanUpConfirmModal.tsx` leaves the repository unchanged — no cleanup actions are performed
- [x] T032 [US6] Verify that the accessibility enhancements from T017–T019 apply to the cleanup flow — modal is accessible, focus-trapped, and focus returns to trigger on close

**Checkpoint**: Repository cleanup confirmation with impact summary is functional and accessible. User Story 6 is independently testable.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and consistency checks across all user stories

- [x] T033 Run `npm run type-check` in `frontend/` to verify all TypeScript changes compile without errors
- [x] T034 [P] Run `npm run lint` in `frontend/` to verify all changes pass ESLint rules
- [x] T035 [P] Run `npm run test` in `frontend/` to verify all existing tests still pass with the changes
- [x] T036 Perform a cross-cutting visual consistency audit — verify all confirmation dialogs use the same layout, typography, button placement, and interaction patterns across the application
- [x] T037 Run the quickstart.md manual verification checklist from `specs/035-confirm-critical-actions/quickstart.md` to validate all critical actions end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — No dependencies on other stories
- **US2 (Phase 4)**: Depends on US1 (Phase 3) — Needs confirmation prompts to exist before auditing their messages
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — Can run in parallel with US1/US2 but benefits from their implementation
- **US4 (Phase 6)**: Depends on Foundational (Phase 2) and US1 (Phase 3) — Needs confirmation prompts to exist to verify loading behavior
- **US5 (Phase 7)**: Depends on US3 (Phase 5) — Needs accessibility enhancements to be in place
- **US6 (Phase 8)**: Depends on US3 (Phase 5) — Needs accessibility enhancements to be in place
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. **MVP scope.**
- **User Story 2 (P1)**: Depends on US1 — Needs the new confirmation prompts (pipeline, tool) to exist for messaging audit
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — Independent of US1/US2 but benefits from their implementation
- **User Story 4 (P2)**: Depends on US1 — Needs the new `onConfirm` patterns (tool deletion) to verify loading behavior
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories; mostly verification
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) — Independent of other stories; mostly verification

### Within Each User Story

- Models/infrastructure before consumer changes
- Core implementation before integration/verification
- Story complete before moving to next priority

### Parallel Opportunities

- T003, T004, T005 in Phase 2 can run in parallel (different ARIA enhancements in same file, non-overlapping sections)
- T013, T014, T015 in Phase 4 can run in parallel (different files)
- T017–T019 and T020–T021 in Phase 5 can run in parallel (different component files)
- T033, T034, T035 in Phase 9 can run in parallel (independent verification commands)
- US3 and US5 can proceed in parallel with US1/US2 if team capacity allows

---

## Parallel Example: User Story 1

```bash
# These tasks modify different files and can run in parallel:
# (None in US1 — tasks are sequential due to ToolsPanel dependencies)

# Sequential order required:
# T009: Remove ad-hoc modal from ToolsPanel.tsx
# T010: Add initial tool deletion confirmation in ToolsPanel.tsx (same file as T009)
# T011: Add second-step tool confirmation in ToolsPanel.tsx (same file as T010)
# T008: Add pipeline deletion confirmation in AgentsPipelinePage.tsx (independent file, can run in parallel with T009-T011)
```

## Parallel Example: User Story 3

```bash
# These tasks modify different files and can run in parallel:
Task: "Audit CleanUpConfirmModal ARIA attributes in frontend/src/components/board/CleanUpConfirmModal.tsx"
Task: "Audit UnsavedChangesDialog ARIA attributes in frontend/src/components/pipeline/UnsavedChangesDialog.tsx"

# T017-T019 (CleanUpConfirmModal) can run in parallel with T020-T021 (UnsavedChangesDialog)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify builds and tests pass)
2. Complete Phase 2: Foundational (accessibility hardening of ConfirmationDialog)
3. Complete Phase 3: User Story 1 (pipeline + tool deletion confirmations)
4. **STOP and VALIDATE**: Test all deletion actions independently — every delete requires confirmation
5. Deploy/demo if ready — the most critical safety gap (pipeline deletion) is now closed

### Incremental Delivery

1. Complete Setup + Foundational → Core infrastructure hardened
2. Add User Story 1 → All deletions confirmed → Deploy/Demo (**MVP!**)
3. Add User Story 2 → All messages standardized → Deploy/Demo
4. Add User Story 3 → All dialogs accessible → Deploy/Demo
5. Add User Story 4 → Rapid submission protection verified → Deploy/Demo
6. Add User Story 5 → Unsaved changes flow verified → Deploy/Demo
7. Add User Story 6 → Cleanup confirmation verified → Deploy/Demo
8. Each story adds safety value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + User Story 2 (confirmation implementation + messaging)
   - Developer B: User Story 3 (accessibility hardening across all dialogs)
   - Developer C: User Story 5 + User Story 6 (verification of existing flows)
3. User Story 4 follows after US1 is complete (needs new confirmations to verify)
4. Stories integrate independently — each adds a layer of safety

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 37 |
| **Phase 1 (Setup)** | 2 tasks |
| **Phase 2 (Foundational)** | 5 tasks |
| **US1 (Destructive Deletion)** | 5 tasks |
| **US2 (Contextual Messaging)** | 4 tasks |
| **US3 (Accessible Experience)** | 6 tasks |
| **US4 (Rapid Submissions)** | 4 tasks |
| **US5 (Unsaved Changes)** | 3 tasks |
| **US6 (Cleanup Confirmation)** | 3 tasks |
| **Phase 9 (Polish)** | 5 tasks |
| **Parallel opportunities** | 9 tasks marked [P] |
| **MVP scope** | Phase 1 + Phase 2 + Phase 3 (12 tasks) |
| **Files modified** | ~6 frontend files (0 new files) |
| **Estimated lines changed** | ~200–400 |

## Notes

- [P] tasks = different files or non-overlapping sections, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No tests generated — not requested in spec; existing test coverage is sufficient
- All changes are frontend-only — no backend modifications required
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
