# Tasks: Confirmation Flow for Critical Actions

**Input**: Design documents from `/specs/001-confirmation-flow/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (api.md, components.md), quickstart.md

**Tests**: Explicitly requested in the feature specification acceptance criteria ("Unit and/or integration tests cover the confirmation logic") and confirmed in the Constitution Check (Principle IV). Test tasks are included.

**Organization**: Tasks grouped by user story (US1–US4) for independent implementation and testing. US1 and US2 are tightly coupled (the reusable component IS the confirmation prompt) — US2 is implemented as part of Setup/Foundational phases, and US1 retrofits the 4 existing call sites. US3 (accessibility) and US4 (state-changing submissions) build on the completed component.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- All changes are frontend-only — no backend modifications required
- New files: `frontend/src/components/ui/confirmation-dialog.tsx`, `frontend/src/hooks/useConfirmation.ts`
- Modified files: `frontend/src/App.tsx`, `frontend/src/components/agents/AgentCard.tsx`, `frontend/src/components/agents/AgentsPanel.tsx`, `frontend/src/components/chores/ChoreCard.tsx`, `frontend/src/pages/AgentsPipelinePage.tsx`

---

## Phase 1: Setup

**Purpose**: No new project setup required — this feature adds a reusable component to an existing frontend application. All infrastructure (React 19.2, Tailwind CSS v4, lucide-react, CVA) is already in place.

- [x] T001 Verify existing frontend build succeeds by running `cd frontend && npm run build` to establish a clean baseline before making changes
- [x] T002 Verify existing frontend tests pass by running `cd frontend && npx vitest run` to confirm no pre-existing test failures

**Checkpoint**: Baseline confirmed. Build and tests pass. Ready for implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the core reusable ConfirmationDialog component and useConfirmation hook that ALL user stories depend on. These are the building blocks — US1 needs them for retrofitting call sites, US2's acceptance criteria are satisfied by their existence, US3 adds accessibility features within them, and US4 uses the async onConfirm pattern they provide.

**⚠️ CRITICAL**: No user story work can begin until the component and hook exist.

- [x] T003 Create the `ConfirmationDialog` presentational component in frontend/src/components/ui/confirmation-dialog.tsx — implement the fixed overlay (`inset-0 z-[60]`) with semi-transparent backdrop (`bg-black/50`), centered inner container (`max-w-md rounded-2xl border shadow-xl`), variant-based styling (danger: red, warning: amber, info: blue) using a `VARIANT_CONFIG` map with `AlertTriangle` and `Info` icons from lucide-react, scrollable description area (`max-h-[60vh] overflow-y-auto`), button footer with Cancel (ghost) and Confirm (variant-colored) buttons, loading state with `Loader2` spinner, and inline error message display — accept props per the `ConfirmationDialogProps` interface defined in contracts/components.md
- [x] T004 Create the `useConfirmation` hook and `ConfirmationDialogProvider` context in frontend/src/hooks/useConfirmation.ts — implement the React Context with `confirm(options): Promise<boolean>` API, internal state management (isOpen, options, isLoading, error, resolve callback), queue management for single-dialog constraint (FR-016), support for optional async `onConfirm` callback with loading/error handling (FR-013, FR-014), focus capture (`document.activeElement`) on dialog open for later restoration, Escape key handling (dismiss as cancel, FR-012), backdrop click handling (dismiss as cancel, disabled during loading), and double-click prevention via immediate `isLoading` state + promise guard (R7)
- [x] T005 Add `ConfirmationDialogProvider` wrapper in frontend/src/App.tsx — import `ConfirmationDialogProvider` from `@/hooks/useConfirmation` and wrap the existing app content (inside `QueryClientProvider`, around `RouterProvider`) so `useConfirmation()` is available in all routed components

**Checkpoint**: Foundation ready. `useConfirmation()` is callable from any component. Dialog renders with correct styling when `confirm()` is called. Escape and backdrop dismiss work. Loading and error states display correctly. Ready for user story implementation.

---

## Phase 3: User Story 1 — Confirmation Prompt for Destructive Actions (Priority: P1) 🎯 MVP

**Goal**: Replace all 4 existing `window.confirm()` calls with the new `useConfirmation` hook so that every destructive action presents a styled, consistent confirmation dialog before executing. The destructive action is NOT executed until the user explicitly confirms.

**Independent Test**: Trigger any destructive action (e.g., click "Delete" on an agent card) → verify the styled confirmation dialog appears with a clear description of the consequences → click "Confirm" → verify the action executes → repeat but click "Cancel" → verify no side effects occur. Also test Escape key and backdrop click as cancel.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T006 [P] [US1] Write test for AgentCard delete confirmation flow in frontend/src/components/agents/__tests__/AgentCard.test.tsx — test that clicking the delete button opens the confirmation dialog (not `window.confirm`), confirming triggers `deleteMutation.mutate()`, and cancelling does not trigger the mutation
- [x] T007 [P] [US1] Write test for AgentsPanel clear pending confirmation flow in frontend/src/components/agents/__tests__/AgentsPanel.test.tsx — test that clicking the clear pending button opens the confirmation dialog with warning variant and "Clear Records" confirm label, confirming triggers `clearPendingMutation.mutate()`, and cancelling does not trigger the mutation
- [x] T008 [P] [US1] Write test for ChoreCard delete confirmation flow in frontend/src/components/chores/__tests__/ChoreCard.test.tsx — test that clicking the delete button opens the confirmation dialog with danger variant, confirming triggers `deleteMutation.mutate()`, and cancelling does not trigger the mutation
- [x] T009 [P] [US1] Write test for AgentsPipelinePage delete confirmation flow in frontend/src/pages/__tests__/AgentsPipelinePage.test.tsx — test that clicking the delete pipeline button opens the confirmation dialog with danger variant and "Delete Pipeline" confirm label, confirming triggers `pipelineConfig.deletePipeline()`, and cancelling does not trigger deletion

### Implementation for User Story 1

- [x] T010 [P] [US1] Replace `window.confirm()` in AgentCard delete handler in frontend/src/components/agents/AgentCard.tsx — import `useConfirmation`, make `handleDelete` async, call `await confirm({ title: 'Delete Agent', description: agent-specific message, variant: 'danger', confirmLabel: 'Delete' })`, and only call `deleteMutation.mutate(agent.id)` if confirmed
- [x] T011 [P] [US1] Replace `window.confirm()` in AgentsPanel clear pending handler in frontend/src/components/agents/AgentsPanel.tsx — import `useConfirmation`, make `handleClearPending` async, call `await confirm({ title: 'Clear Pending Records', description: pending-specific message, variant: 'warning', confirmLabel: 'Clear Records' })`, and only call `clearPendingMutation.mutate()` if confirmed
- [x] T012 [P] [US1] Replace `window.confirm()` in ChoreCard delete handler in frontend/src/components/chores/ChoreCard.tsx — import `useConfirmation`, make `handleDelete` async, call `await confirm({ title: 'Delete Chore', description: chore-specific message, variant: 'danger', confirmLabel: 'Delete' })`, and only call `deleteMutation.mutate(chore.id)` if confirmed
- [x] T013 [P] [US1] Replace `window.confirm()` in AgentsPipelinePage delete handler in frontend/src/pages/AgentsPipelinePage.tsx — import `useConfirmation`, make `handleDelete` async (update `useCallback` to async), call `await confirm({ title: 'Delete Pipeline', description: pipeline-specific message, variant: 'danger', confirmLabel: 'Delete Pipeline' })`, and only call `pipelineConfig.deletePipeline()` if confirmed, add `confirm` to `useCallback` dependency array

**Checkpoint**: All 4 destructive actions now show the styled confirmation dialog. Confirm executes the action, Cancel/Escape/backdrop click does not. Zero `window.confirm()` calls remain in the codebase. US1 tests pass. This is the MVP.

---

## Phase 4: User Story 2 — Reusable and Consistent Confirmation Component (Priority: P1)

**Goal**: Validate that the ConfirmationDialog component is truly reusable and consistent — invocable from any feature with customizable messaging, visually identical across all call sites, and the destructive action button is visually distinct from cancel.

**Independent Test**: Invoke the confirmation component from two or more different features (e.g., deleting an agent, removing a pipeline) and verify both instances use the same visual style, interaction pattern, and behavior. Verify the confirm button uses danger/warning color and cancel button uses ghost styling.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T014 [P] [US2] Write unit tests for ConfirmationDialog component in frontend/src/components/ui/__tests__/confirmation-dialog.test.tsx — test rendering with all three variants (danger, warning, info), verify correct icon (AlertTriangle for danger/warning, Info for info), verify confirm button color matches variant (red for danger, amber for warning, blue for info), verify cancel button uses ghost/outline styling distinct from confirm, verify custom title/description/confirmLabel/cancelLabel render correctly
- [x] T015 [P] [US2] Write unit tests for useConfirmation hook in frontend/src/hooks/__tests__/useConfirmation.test.tsx — test that `confirm()` opens the dialog and returns `Promise<boolean>`, test that confirming resolves with `true`, test that cancelling resolves with `false`, test that the hook throws when used outside `ConfirmationDialogProvider`, test that customizable options (title, description, variant, labels) are passed through to the dialog

### Implementation for User Story 2

- [x] T016 [US2] Verify visual consistency across all 4 retrofitted call sites — confirm that AgentCard (danger), AgentsPanel (warning), ChoreCard (danger), and AgentsPipelinePage (danger) all render with identical layout, typography, spacing, button placement, and animation patterns by running the app and visually inspecting each dialog

**Checkpoint**: ConfirmationDialog is verified reusable across 4 distinct features. All instances share identical visual layout and interaction patterns. Destructive action button is visually distinct (variant-colored) from cancel button (ghost). US2 tests pass.

---

## Phase 5: User Story 3 — Accessible Confirmation Flow (Priority: P2)

**Goal**: Ensure the confirmation dialog meets WCAG 2.1 AA accessibility standards — focus is trapped within the dialog, initial focus is on the cancel button (safe default), focus is restored to the triggering element on close, ARIA attributes are correct, and the entire flow is keyboard-navigable.

**Independent Test**: Navigate the entire confirmation flow using only the keyboard (Tab, Shift+Tab, Enter, Escape) → verify all elements are reachable, focus is trapped, and focus returns to the trigger on close. Inspect ARIA attributes (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`).

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T017 [P] [US3] Write accessibility tests for ConfirmationDialog in frontend/src/components/ui/__tests__/confirmation-dialog.test.tsx — test that `role="dialog"` and `aria-modal="true"` are set on the dialog container, test that `aria-labelledby` references the title element id (`confirmation-dialog-title`), test that `aria-describedby` references the description element id (`confirmation-dialog-description`), test that Escape key triggers `onCancel`
- [x] T018 [P] [US3] Write focus management tests for useConfirmation hook in frontend/src/hooks/__tests__/useConfirmation.test.tsx — test that focus moves to the cancel button when dialog opens (safe default per R3), test that focus is restored to the triggering element when dialog closes (confirm, cancel, or Escape), test that Tab key cycles focus only within dialog focusable elements (focus trapping)

### Implementation for User Story 3

- [x] T019 [US3] Implement focus trapping in the ConfirmationDialog component in frontend/src/components/ui/confirmation-dialog.tsx — add a `useEffect` that queries all focusable elements within the dialog (`button:not([disabled]), [tabindex]:not([tabindex="-1"])`) and intercepts Tab/Shift+Tab keydown events to cycle focus within the dialog boundaries, wrapping from last to first on Tab and from first to last on Shift+Tab
- [x] T020 [US3] Implement initial focus and focus restoration in frontend/src/hooks/useConfirmation.ts — on dialog open, set focus to the cancel button (not the destructive confirm button, per WAI-ARIA best practice in R3), on dialog close, restore focus to `previousFocusRef.current` which was captured as `document.activeElement` before the dialog opened
- [x] T021 [US3] Add ARIA attributes to the dialog container in frontend/src/components/ui/confirmation-dialog.tsx — set `role="dialog"`, `aria-modal="true"`, `aria-labelledby="confirmation-dialog-title"` referencing the title element, and `aria-describedby="confirmation-dialog-description"` referencing the description text element

**Checkpoint**: Dialog is fully keyboard-navigable. Focus trapping prevents Tab from reaching background elements. Focus returns to the trigger on close. ARIA attributes pass automated audit. US3 tests pass.

---

## Phase 6: User Story 4 — Confirmation for State-Changing Submissions (Priority: P2)

**Goal**: Extend the confirmation component to support state-changing submissions (e.g., bulk updates) by utilizing the async `onConfirm` callback pattern. When used, the dialog shows a loading state during the async operation, catches errors and displays them inline, and allows retry.

**Independent Test**: Trigger a confirmation with an async `onConfirm` callback → verify the dialog shows a loading spinner on the confirm button, both buttons are disabled during the operation → on success, dialog closes → on failure, error message is displayed inline and retry is available.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T022 [P] [US4] Write async confirmation tests in frontend/src/hooks/__tests__/useConfirmation.test.tsx — test that when `onConfirm` async callback is provided and user clicks confirm, the dialog shows loading state (`isLoading: true`), both buttons are disabled, and on success the promise resolves with `true` and dialog closes
- [x] T023 [P] [US4] Write error handling tests in frontend/src/hooks/__tests__/useConfirmation.test.tsx — test that when `onConfirm` async callback throws an error, the error message is displayed inline in the dialog, the confirm button re-enables for retry, and the user can retry (calling `onConfirm` again) or cancel

### Implementation for User Story 4

- [x] T024 [US4] Implement async `onConfirm` handling in the ConfirmationDialogProvider in frontend/src/hooks/useConfirmation.ts — when the user clicks confirm and `options.onConfirm` is defined, set `isLoading: true`, call `await options.onConfirm()`, on success resolve the promise with `true` and close the dialog, on failure catch the error, set `error: error.message`, set `isLoading: false` to re-enable the confirm button for retry
- [x] T025 [US4] Implement loading and error UI states in frontend/src/components/ui/confirmation-dialog.tsx — when `isLoading` is true, show `Loader2` spinner icon on the confirm button with "Processing..." text and disable both buttons; when `error` is non-null, display a red error banner above the button footer with the error message; disable backdrop click dismissal during loading state

**Checkpoint**: Async confirmation flow works end-to-end. Loading spinner shows during async operations. Error messages display inline with retry capability. Backdrop dismissal is blocked during loading. US4 tests pass.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and regression testing across all user stories.

- [x] T026 Run full frontend build to verify no TypeScript errors: `cd frontend && npm run build`
- [x] T027 Run full frontend test suite to verify all tests pass (existing + new): `cd frontend && npx vitest run`
- [x] T028 [P] Verify zero `window.confirm()` calls remain in the frontend codebase by searching for `window.confirm` across all frontend source files
- [x] T029 [P] Verify the confirmation dialog queue behavior works correctly — open a confirmation dialog, trigger another critical action, verify the second dialog appears after the first resolves (FR-016)
- [x] T030 [P] Verify double-click prevention — rapidly click the confirm button and verify the action executes only once (FR-013, edge case from spec)
- [x] T031 Run quickstart.md verification checklist: all 4 destructive actions show styled dialog, Escape/backdrop dismiss, focus trap works, ARIA attributes present, loading/error states display, queue processes correctly, visual consistency across all call sites

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — baseline build/test verification
- **Foundational (Phase 2)**: Depends on Setup — creates the core component and hook that BLOCK all user stories
- **US1 (Phase 3)**: Depends on Foundational — retrofits 4 call sites using the component/hook
- **US2 (Phase 4)**: Depends on Foundational — tests the component's reusability and visual consistency (implementation is largely done in Foundational + US1)
- **US3 (Phase 5)**: Depends on Foundational — adds accessibility features to the existing component/hook
- **US4 (Phase 6)**: Depends on Foundational — adds async loading/error handling to the existing component/hook
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2) — can start immediately after component/hook exist
- **US2 (P1)**: Depends on Foundational (Phase 2) + benefits from US1 (tests verify consistency across retrofitted call sites). Can run in parallel with US1 for test writing, but visual verification requires US1 completion.
- **US3 (P2)**: Depends on Foundational (Phase 2) — accessibility features are added to existing component. Can run in parallel with US1 and US4.
- **US4 (P2)**: Depends on Foundational (Phase 2) — async handling is added to existing hook. Can run in parallel with US1 and US3.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Component changes before hook changes (presentational before state management)
- Core implementation before integration/verification
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks (T003, T004, T005) are sequential — T003 (component) before T004 (hook imports component), T005 (provider wraps app) after T004
- US1 tests (T006, T007, T008, T009) can all run in parallel — different test files
- US1 implementation (T010, T011, T012, T013) can all run in parallel — different source files
- US2 tests (T014, T015) can run in parallel — different test files
- US3 tests (T017, T018) can run in parallel — different test files
- US4 tests (T022, T023) can run in parallel — different test files
- US1, US3, and US4 can be worked on in parallel by different team members after Foundational phase completes
- Polish tasks T028, T029, T030 can all run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (write before implementation):
Task: "Test AgentCard delete confirmation in frontend/src/components/agents/__tests__/AgentCard.test.tsx"
Task: "Test AgentsPanel clear pending confirmation in frontend/src/components/agents/__tests__/AgentsPanel.test.tsx"
Task: "Test ChoreCard delete confirmation in frontend/src/components/chores/__tests__/ChoreCard.test.tsx"
Task: "Test AgentsPipelinePage delete confirmation in frontend/src/pages/__tests__/AgentsPipelinePage.test.tsx"

# Launch all implementation tasks for User Story 1 together:
Task: "Replace window.confirm() in AgentCard.tsx"
Task: "Replace window.confirm() in AgentsPanel.tsx"
Task: "Replace window.confirm() in ChoreCard.tsx"
Task: "Replace window.confirm() in AgentsPipelinePage.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline build and tests
2. Complete Phase 2: Create ConfirmationDialog component + useConfirmation hook + add Provider to App.tsx
3. Complete Phase 3: Retrofit all 4 `window.confirm()` call sites
4. **STOP and VALIDATE**: Each destructive action shows the styled confirmation dialog. Confirm executes, Cancel does not.
5. Deploy/demo if ready — core value (preventing accidental destructive actions) is delivered

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready (component, hook, provider exist)
2. Add US1 (Phase 3) → All destructive actions use new dialog → **MVP!** Users are protected from accidental actions
3. Add US2 (Phase 4) → Reusability verified, visual consistency confirmed across all features
4. Add US3 (Phase 5) → Full WCAG 2.1 AA compliance → Accessibility audit passes
5. Add US4 (Phase 6) → Async loading/error support → Ready for bulk operations and complex confirmations
6. Phase 7 → Polish, regression testing, quickstart validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (retrofit call sites)
   - Developer B: User Story 3 (accessibility features)
   - Developer C: User Story 4 (async loading/error)
3. Developer A completes US1 → Developer D starts US2 (visual verification)
4. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 31 |
| **Setup Tasks** | 2 (T001–T002) |
| **Foundational Tasks** | 3 (T003–T005) |
| **US1 Tasks** | 8 (T006–T013: 4 tests + 4 implementation) |
| **US2 Tasks** | 3 (T014–T016: 2 tests + 1 verification) |
| **US3 Tasks** | 5 (T017–T021: 2 tests + 3 implementation) |
| **US4 Tasks** | 4 (T022–T025: 2 tests + 2 implementation) |
| **Polish Tasks** | 6 (T026–T031) |
| **Parallel Opportunities** | 8 groups (US1 tests, US1 impl, US2 tests, US3 tests, US4 tests, US1/US3/US4 in parallel, Polish T028/T029/T030 in parallel, T006/T007/T008/T009 in parallel) |
| **New Files** | 2 (confirmation-dialog.tsx, useConfirmation.ts) |
| **Modified Files** | 5 (App.tsx, AgentCard.tsx, AgentsPanel.tsx, ChoreCard.tsx, AgentsPipelinePage.tsx) |
| **New Test Files** | Up to 6 (component tests, hook tests, call site tests) |
| **MVP Scope** | Phases 1–3 (US1 only, tasks T001–T013) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 is the core user-facing value (preventing accidental destructive actions) and constitutes the MVP
- US2 is largely satisfied by the Foundational phase (reusable component) + US1 (consistent usage) — Phase 4 adds verification and tests
- US3 accessibility features (focus trapping, ARIA attributes, focus restoration) can be partially implemented in Phase 2 and refined in Phase 5 — the task structure assumes Phase 5 adds/verifies them
- US4 async loading/error pattern is available via the `onConfirm` option defined in Phase 2 — Phase 6 adds/verifies the implementation and UI states
- All changes are frontend-only — zero backend modifications required
- No new dependencies — uses existing lucide-react, Tailwind CSS, and React Context patterns
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
