# Tasks: Chores Page Type Header Toggle for Clean Up Deletion

**Input**: Design documents from `/specs/001-type-header-toggle/`
**Prerequisites**: spec.md (user stories with priorities P1–P3), existing codebase analysis

**Tests**: Tests are included — the existing test file `CleanUpConfirmModal.test.tsx` must be extended to cover the new toggle behavior, and new utility tests should be added for the selection logic hook.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `solune/frontend/src/`
- **Backend**: `solune/backend/src/`
- **Tests**: Colocated with implementation (e.g., `Component.test.tsx` alongside `Component.tsx`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the shared selection state hook and utility types needed by all user stories

- [ ] T001 Create custom hook `useGroupSelection` for managing grouped item selection state in `solune/frontend/src/hooks/useGroupSelection.ts` — accepts items grouped by type key, tracks selected Set per group, exposes `toggleItem`, `toggleGroup`, `isSelected`, `getGroupState` (returns 'all' | 'some' | 'none'), and `selectedItems`. Protected item keys must be accepted as a config parameter so they are permanently excluded from all selection operations.
- [ ] T002 [P] Add `PROTECTED_BRANCHES` constant (containing `'main'`) in `solune/frontend/src/constants/cleanup.ts` — single source of truth for branch names that can never be deleted. Export a helper `isProtectedBranch(name: string): boolean`.
- [ ] T003 [P] Add `GroupHeaderCheckbox` presentational component in `solune/frontend/src/components/board/GroupHeaderCheckbox.tsx` — renders a checkbox-style header row with three visual states (unchecked, indeterminate, checked), accepts `label`, `count`, `state` ('all' | 'some' | 'none'), `disabled`, `onToggle`, and an icon slot. Uses controlled `indeterminate` property on the underlying `<input type="checkbox">` via a ref. Applies ARIA attribute `aria-checked="mixed"` when indeterminate.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Unit tests for the new shared hook and component — MUST pass before user story work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create unit tests for `useGroupSelection` hook in `solune/frontend/src/hooks/useGroupSelection.test.ts` — test `toggleItem` adds/removes from selection, `toggleGroup` selects all eligible / deselects all, `getGroupState` returns correct state for none/some/all selected, protected items are never included in selection even when `toggleGroup` is called, and `selectedItems` returns only eligible selected items.
- [ ] T005 [P] Create unit tests for `GroupHeaderCheckbox` component in `solune/frontend/src/components/board/GroupHeaderCheckbox.test.tsx` — test renders label and count, renders unchecked/indeterminate/checked states correctly, calls `onToggle` on click, renders disabled state when `disabled=true`, and sets `aria-checked="mixed"` for indeterminate state.
- [ ] T006 [P] Create unit tests for `isProtectedBranch` helper in `solune/frontend/src/constants/cleanup.test.ts` — test returns `true` for `'main'`, returns `false` for other branch names like `'feature/foo'`, `'develop'`, `'master'`.

**Checkpoint**: Foundation ready — shared hook, component, and constants are tested and ready for integration

---

## Phase 3: User Story 1 — Bulk-Select All Items by Type Header (Priority: P1) 🎯 MVP

**Goal**: Users can click a type header checkbox to select/deselect all eligible items in that group with a single click

**Independent Test**: Open Chores page → trigger Clean Up → click "Branches" header checkbox → verify all eligible branches toggle their selection state. Click again → verify all deselect.

### Implementation for User Story 1

- [ ] T007 [US1] Refactor `CleanUpConfirmModal` state management in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — replace the existing `preserved` and `markedForDeletion` `Set<string>` state with the `useGroupSelection` hook. Initialize groups: `'branches_delete'` (from `data.branches_to_delete`), `'prs_delete'` (from `data.prs_to_close`), `'issues_delete'` (from `data.orphaned_issues`), `'branches_preserve'` (from `data.branches_to_preserve`), `'prs_preserve'` (from `data.prs_to_preserve`). All items start selected-for-their-default-action (items in "to delete" groups default to selected/will-delete, items in "to preserve" groups default to unselected/preserved). Maintain backward-compatible `onConfirm` payload shape.
- [ ] T008 [US1] Add `GroupHeaderCheckbox` to "Branches to Delete" section header in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — replace the static `<h3>` with a clickable header row using `GroupHeaderCheckbox`. Wire `onToggle` to `toggleGroup('branches_delete')`. Derive `state` from `getGroupState('branches_delete')`. Display branch count and `GitBranch` icon.
- [ ] T009 [P] [US1] Add `GroupHeaderCheckbox` to "Pull Requests to Close" section header in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — same pattern as T008 but for `'prs_delete'` group with `GitPullRequest` icon and PR count.
- [ ] T010 [P] [US1] Add `GroupHeaderCheckbox` to "Orphaned Issues to Delete" section header in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — same pattern as T008 but for `'issues_delete'` group with `Trash2` icon and issue count.
- [ ] T011 [P] [US1] Add `GroupHeaderCheckbox` to "Branches to Preserve" section header in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — wire `onToggle` to `toggleGroup('branches_preserve')`. When toggled on, items move to the "will delete" state; when toggled off, items return to preserved. Display `Shield` icon.
- [ ] T012 [P] [US1] Add `GroupHeaderCheckbox` to "Pull Requests to Preserve" section header in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — same pattern as T011 but for `'prs_preserve'` group with `Shield` icon.
- [ ] T013 [US1] Update existing tests in `solune/frontend/src/components/board/CleanUpConfirmModal.test.tsx` — add tests for: clicking "Branches to Delete" header selects/deselects all branches, clicking "Pull Requests to Close" header selects/deselects all PRs, header checkbox reflects correct state after individual item toggles, confirm payload correctly reflects bulk-toggled selections.
- [ ] T014 [US1] Wire individual item `ToggleButton` clicks in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` to use `toggleItem` from the `useGroupSelection` hook, replacing the old `togglePreserve` / `toggleMarkForDeletion` calls. Ensure the header checkbox state updates reactively when individual items are toggled.

**Checkpoint**: At this point, users can bulk-select/deselect entire type groups. MVP is functional.

---

## Phase 4: User Story 2 — 'main' Branch Protection During Bulk Toggle (Priority: P1)

**Goal**: The 'main' branch is permanently protected — its checkbox is disabled, it is excluded from all bulk-toggle operations, and it is never included in the deletion payload

**Independent Test**: Open Clean Up → verify 'main' branch row has a disabled, greyed-out checkbox → click "Branches" header toggle → verify 'main' remains unselected → confirm cleanup → verify payload does not contain 'main'.

### Implementation for User Story 2

- [ ] T015 [US2] Pass `'main'` as a protected item key to the `useGroupSelection` hook in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — use the `PROTECTED_BRANCHES` constant from `solune/frontend/src/constants/cleanup.ts`. The hook must skip protected keys in `toggleGroup` and reject them in `toggleItem`.
- [ ] T016 [US2] Update `BranchRow` component in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` to accept an `isProtected` prop — when `true`, render the `ToggleButton` in a disabled state (greyed out, `pointer-events-none`, `opacity-50`), add `aria-disabled="true"` to the row, and display a lock icon (`Lock` from lucide-react) with tooltip text "Protected branch — cannot be deleted".
- [ ] T017 [US2] In the "Branches to Delete" and "Branches to Preserve" list rendering in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx`, detect if each branch is protected using `isProtectedBranch(branch.name)` and pass `isProtected={true}` to `BranchRow`. Ensure the `onToggle` callback is a no-op for protected branches.
- [ ] T018 [US2] Add validation guard in `handleConfirm` in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — filter out any protected branch names from the `branches_to_delete` array before calling `onConfirm`, as a defense-in-depth measure.
- [ ] T019 [US2] Add tests in `solune/frontend/src/components/board/CleanUpConfirmModal.test.tsx` — test that: 'main' branch row renders with disabled toggle button, clicking 'main' toggle does not change its state, clicking "Branches" header toggle does not select 'main', confirm payload never includes 'main' even if data contains it in `branches_to_delete`, tooltip/label on 'main' row indicates it is protected.

**Checkpoint**: At this point, 'main' branch is fully protected on the frontend. Combined with existing server-side validation in `solune/backend/src/api/cleanup.py` (line 65–75), defense-in-depth is achieved.

---

## Phase 5: User Story 3 — Indeterminate Header State for Partial Selections (Priority: P2)

**Goal**: Type header checkboxes visually reflect whether all, some, or no items are selected — including the indeterminate (dash/minus) state for partial selections

**Independent Test**: Manually select 2 of 5 branches → verify header shows indeterminate state → select remaining 3 → verify header shows fully checked → deselect all → verify header shows unchecked.

### Implementation for User Story 3

- [ ] T020 [US3] Implement indeterminate checkbox rendering in `GroupHeaderCheckbox` component in `solune/frontend/src/components/board/GroupHeaderCheckbox.tsx` — use a `useRef` + `useEffect` to set the native `indeterminate` property on the `<input>` element when `state === 'some'`. Set `checked={state === 'all'}` on the input. Ensure visual styling distinguishes all three states (unchecked: empty box, indeterminate: dash/minus icon, checked: checkmark).
- [ ] T021 [US3] Ensure `getGroupState` in `useGroupSelection` hook correctly handles edge cases in `solune/frontend/src/hooks/useGroupSelection.ts`: returns `'all'` when all eligible items are selected (excluding protected), returns `'none'` when zero items are selected, returns `'some'` for any partial selection. When a group has zero eligible items, return `'none'` (header should be disabled).
- [ ] T022 [US3] Implement click behavior for indeterminate state in `useGroupSelection` in `solune/frontend/src/hooks/useGroupSelection.ts` — when `getGroupState` returns `'some'` and `toggleGroup` is called, select all remaining eligible unselected items (resolve partial → fully selected), matching the spec requirement FR-012.
- [ ] T023 [US3] Handle edge case where group contains only protected items in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — when a "Branches" group has only 'main' and no other branches, render `GroupHeaderCheckbox` with `disabled={true}` and `state='none'` since there are no eligible items to toggle.
- [ ] T024 [US3] Add tests in `solune/frontend/src/components/board/CleanUpConfirmModal.test.tsx` — test that: header shows unchecked when no items selected, header shows indeterminate when subset selected, header shows fully checked when all eligible selected, clicking indeterminate header selects all remaining eligible items, header shows checked when 'main' is the only unselected item (since all eligible items are selected).

**Checkpoint**: All three visual states for header checkboxes are functional and tested

---

## Phase 6: User Story 4 — Keyboard Accessibility for Header Toggles (Priority: P3)

**Goal**: Keyboard-only users can navigate to and operate type header checkboxes using Tab, Space, and Enter keys, with proper ARIA attributes for screen readers

**Independent Test**: Tab through the modal → verify header checkboxes receive focus → press Space → verify toggle fires → press Enter → verify toggle fires → check screen reader announcements for all three states.

### Implementation for User Story 4

- [ ] T025 [US4] Ensure `GroupHeaderCheckbox` in `solune/frontend/src/components/board/GroupHeaderCheckbox.tsx` uses a native `<input type="checkbox">` wrapped in a `<label>` — this provides built-in Space key toggling and focus management. Add `role="checkbox"` and `aria-checked` attribute: `"true"` when checked, `"false"` when unchecked, `"mixed"` when indeterminate. Add `aria-label` with descriptive text (e.g., "Select all branches for deletion").
- [ ] T026 [US4] Add Enter key handler to `GroupHeaderCheckbox` in `solune/frontend/src/components/board/GroupHeaderCheckbox.tsx` — native checkboxes respond to Space but not Enter by default. Add an `onKeyDown` handler that calls `onToggle` when Enter is pressed, matching the spec requirement for both Space and Enter support.
- [ ] T027 [US4] Add `aria-disabled="true"` to the 'main' branch row in `BranchRow` in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — ensure screen readers announce the row as disabled. The toggle button inside must also have `tabIndex={-1}` to remove it from the tab order when protected.
- [ ] T028 [US4] Ensure focus ring styling on `GroupHeaderCheckbox` in `solune/frontend/src/components/board/GroupHeaderCheckbox.tsx` — add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` classes (consistent with existing Tailwind patterns in the codebase) so keyboard users can see which header is focused.
- [ ] T029 [US4] Add accessibility tests in `solune/frontend/src/components/board/CleanUpConfirmModal.test.tsx` — test that: header checkboxes are focusable via Tab, Space key toggles header selection, Enter key toggles header selection, `aria-checked` reflects correct state (`true`/`false`/`mixed`), 'main' branch toggle has `aria-disabled="true"` and is not in the tab order.

**Checkpoint**: Full keyboard accessibility and ARIA compliance achieved

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, edge cases, and code quality improvements

- [ ] T030 [P] Style refinements for `GroupHeaderCheckbox` in `solune/frontend/src/components/board/GroupHeaderCheckbox.tsx` — add hover state (`hover:bg-primary/10`), sufficient hit target (minimum 44×44px touch area via padding), and visual consistency with existing section headers in the modal. Ensure the checkbox area is visually distinct from the label text.
- [ ] T031 [P] Handle empty group edge case in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — when a type group has zero items, either don't render the section (existing behavior) or render the header in a disabled state. Verify the "No stale items" message still displays when all groups are empty.
- [ ] T032 Verify backward compatibility in `solune/frontend/src/components/board/CleanUpConfirmModal.tsx` — ensure the `onConfirm` payload shape (`CleanupConfirmPayload`) is identical to the previous implementation so `CleanUpButton.tsx` and `useCleanup.ts` require no changes. Run the full existing test suite for `CleanUpConfirmModal.test.tsx` to confirm no regressions.
- [ ] T033 [P] Verify server-side 'main' branch protection in `solune/backend/src/api/cleanup.py` — confirm the existing rejection logic (lines 65–75) remains intact and correctly returns a 400 error if 'main' is included in the deletion request. No code changes expected — this is a verification task.
- [ ] T034 Run full frontend lint, type-check, and test suite from `solune/frontend/` — execute `npm run lint`, `npm run type-check`, and `npm run test:coverage` to ensure zero regressions across the entire frontend.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — core toggle functionality
- **User Story 2 (Phase 4)**: Depends on Phase 2 — can run in parallel with Phase 3 but integrates with it
- **User Story 3 (Phase 5)**: Depends on Phase 3 (needs the header checkboxes to exist)
- **User Story 4 (Phase 6)**: Depends on Phase 3 and Phase 5 (needs header checkboxes with all three states)
- **Polish (Phase 7)**: Depends on all user story phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — integrates with US1's header but can be developed in parallel since both modify `CleanUpConfirmModal.tsx`
- **User Story 3 (P2)**: Depends on US1 (needs header checkboxes to exist for indeterminate state rendering)
- **User Story 4 (P3)**: Depends on US1 and US3 (needs header checkboxes with all visual states for ARIA attributes)

### Within Each User Story

- Models/utilities before components
- Components before integration
- Integration before tests (tests validate the integration)
- Core implementation before edge cases

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, no dependencies)
- T004, T005, T006 can all run in parallel (test different modules)
- T009, T010, T011, T012 can run in parallel (modify different sections of the same file, but are independent header additions)
- T025 through T029 are mostly sequential within US4 but T025/T026 can run together

---

## Parallel Example: Phase 1 (Setup)

```bash
# T002 and T003 can run in parallel — different files:
Task: "Create PROTECTED_BRANCHES constant in solune/frontend/src/constants/cleanup.ts"
Task: "Create GroupHeaderCheckbox component in solune/frontend/src/components/board/GroupHeaderCheckbox.tsx"
```

## Parallel Example: Phase 2 (Foundational)

```bash
# All three test files can be written in parallel:
Task: "Unit tests for useGroupSelection in solune/frontend/src/hooks/useGroupSelection.test.ts"
Task: "Unit tests for GroupHeaderCheckbox in solune/frontend/src/components/board/GroupHeaderCheckbox.test.tsx"
Task: "Unit tests for isProtectedBranch in solune/frontend/src/constants/cleanup.test.ts"
```

## Parallel Example: Phase 3 (User Story 1)

```bash
# After T008 completes, the remaining header additions can be done in parallel:
Task: "Add GroupHeaderCheckbox to PRs to Close section"
Task: "Add GroupHeaderCheckbox to Orphaned Issues section"
Task: "Add GroupHeaderCheckbox to Branches to Preserve section"
Task: "Add GroupHeaderCheckbox to PRs to Preserve section"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — create hook, constants, and component
2. Complete Phase 2: Foundational — run tests, ensure all pass
3. Complete Phase 3: User Story 1 — header toggle for all type groups
4. **STOP and VALIDATE**: Test bulk-select/deselect, confirm payload is correct
5. Deploy/demo if ready — core value delivered

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → 'main' branch now protected
4. Add User Story 3 → Test independently → Indeterminate states working
5. Add User Story 4 → Test independently → Keyboard accessibility complete
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (bulk toggle) + User Story 3 (indeterminate)
   - Developer B: User Story 2 ('main' protection) + User Story 4 (accessibility)
3. Stories integrate cleanly since US1/US3 focus on selection logic and US2/US4 focus on protection + a11y

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- The existing `CleanUpConfirmModal.test.tsx` has 5 passing tests that must not regress
- Backend already protects 'main' branch server-side — frontend protection is defense-in-depth
- The `useGroupSelection` hook encapsulates all selection logic, keeping the modal component focused on rendering
- All header checkbox states are derived from child selection state (FR-009) — no independent header state stored
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
