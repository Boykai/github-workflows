# Tasks: Chores Page Type Header Toggle for Clean Up Deletion

**Input**: Design documents from `/specs/001-type-header-toggle/`
**Prerequisites**: spec.md (user stories US1–US4, requirements FR-001–FR-014)

**Tests**: Not explicitly requested in the feature specification. Tests are omitted per template rules.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `solune/frontend/src/`
- **Backend**: `solune/backend/src/`
- **Components**: `solune/frontend/src/components/board/`
- **Hooks**: `solune/frontend/src/hooks/`
- **Types**: `solune/frontend/src/types/`
- **Services**: `solune/frontend/src/services/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Define shared types and utility functions needed across all user stories

- [ ] T001 Add `ProtectedBranch` constant and `isProtectedBranch` utility function in solune/frontend/src/utils/branchProtection.ts
- [ ] T002 [P] Extend cleanup-related TypeScript interfaces to include selection state tracking (selected set, eligible items) in solune/frontend/src/types/cleanup.ts or existing type file used by CleanUpConfirmModal

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Refactor existing CleanUpConfirmModal selection logic from preserve/delete toggle pattern to a checkbox selection model that supports header-level bulk operations

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Refactor CleanUpConfirmModal state from `preserved`/`markedForDeletion` Sets to a unified `selectedForDeletion` Set with eligibility awareness in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T004 Create `useGroupSelection` custom hook encapsulating group-level selection logic (select all eligible, deselect all, compute header state) in solune/frontend/src/hooks/useGroupSelection.ts
- [ ] T005 [P] Extract `TypeGroupHeader` presentational component skeleton (checkbox + label + count) in solune/frontend/src/components/board/TypeGroupHeader.tsx

**Checkpoint**: Foundation ready — selection model refactored, group selection hook available, header component skeleton in place

---

## Phase 3: User Story 1 — Bulk-Select All Items by Type Header (Priority: P1) 🎯 MVP

**Goal**: Users can click a type header checkbox to select or deselect all eligible items under that type group in a single click

**Independent Test**: Open Chores page → trigger Clean Up → click "Branches" header checkbox → verify all eligible branches toggle selection. Click again → verify all deselect. Repeat for "Pull Requests" group.

### Implementation for User Story 1

- [ ] T006 [US1] Integrate `useGroupSelection` hook into CleanUpConfirmModal to manage per-group selection state for branches in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T007 [US1] Integrate `useGroupSelection` hook into CleanUpConfirmModal to manage per-group selection state for pull requests in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T008 [US1] Integrate `useGroupSelection` hook into CleanUpConfirmModal to manage per-group selection state for orphaned issues in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T009 [US1] Render `TypeGroupHeader` with functional checkbox for "Branches to Delete" section — clicking toggles all branch items in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T010 [US1] Render `TypeGroupHeader` with functional checkbox for "Pull Requests to Close" section — clicking toggles all PR items in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T011 [US1] Render `TypeGroupHeader` with functional checkbox for "Orphaned Issues to Delete" section — clicking toggles all issue items in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T012 [US1] Update `BranchRow` and `PrRow` sub-components to use checkbox selection model instead of shield toggle in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T013 [US1] Wire final deletion payload to derive from `selectedForDeletion` set, ensuring only checked eligible items are submitted in solune/frontend/src/components/board/CleanUpConfirmModal.tsx

**Checkpoint**: User Story 1 complete — type header checkboxes toggle all eligible items; individual items use checkbox selection; deletion payload reflects checked items only

---

## Phase 4: User Story 2 — 'main' Branch Protection During Bulk Toggle (Priority: P1)

**Goal**: The 'main' branch checkbox is permanently disabled and excluded from all bulk-select operations, ensuring it can never be queued for deletion

**Independent Test**: Open Chores page → trigger Clean Up → verify 'main' branch row shows a disabled, greyed-out checkbox → click "Branches" header checkbox → verify 'main' remains unselected → confirm deletion → verify 'main' is not included in API payload. Hover over 'main' row → verify tooltip/indicator appears.

### Implementation for User Story 2

- [ ] T014 [US2] Integrate `isProtectedBranch` check into `useGroupSelection` hook to exclude protected branches from eligible item sets in solune/frontend/src/hooks/useGroupSelection.ts
- [ ] T015 [US2] Render 'main' branch row with permanently disabled checkbox and distinct visual styling (greyed out, non-interactive) in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T016 [US2] Add tooltip or muted label on 'main' branch row explaining "Default branch cannot be deleted" in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T017 [US2] Ensure header checkbox state computation excludes protected branches (e.g., all-checked means all eligible non-protected items checked) in solune/frontend/src/hooks/useGroupSelection.ts
- [ ] T018 [US2] Add server-side validation to reject 'main' branch from cleanup deletion payload in solune/backend/src/api/cleanup.py or equivalent backend cleanup endpoint
- [ ] T019 [US2] Verify deletion payload assembly in CleanUpConfirmModal filters out protected branches before API submission in solune/frontend/src/components/board/CleanUpConfirmModal.tsx

**Checkpoint**: User Story 2 complete — 'main' branch permanently protected on both client and server; tooltip explains protection; header toggle skips 'main'

---

## Phase 5: User Story 3 — Indeterminate Header State for Partial Selections (Priority: P2)

**Goal**: The type header checkbox visually reflects whether all, some, or no eligible items are selected (checked / indeterminate / unchecked)

**Independent Test**: Open Chores page → trigger Clean Up → manually select 2 of 5 branches → verify header shows indeterminate (dash) state → select all remaining → verify header shows fully checked → deselect all → verify header shows unchecked. Click header while indeterminate → verify all eligible become selected.

### Implementation for User Story 3

- [ ] T020 [US3] Add indeterminate state computation to `useGroupSelection` hook (return `checked`, `indeterminate`, `unchecked` based on eligible selection ratio) in solune/frontend/src/hooks/useGroupSelection.ts
- [ ] T021 [US3] Apply HTML checkbox `indeterminate` property via ref on `TypeGroupHeader` component to render browser-native indeterminate visual in solune/frontend/src/components/board/TypeGroupHeader.tsx
- [ ] T022 [US3] Implement click-while-indeterminate behavior: clicking header in indeterminate state selects all eligible items (resolves to fully checked) in solune/frontend/src/hooks/useGroupSelection.ts
- [ ] T023 [US3] Handle edge case: when group contains only protected items, render header checkbox as disabled with no toggle in solune/frontend/src/components/board/TypeGroupHeader.tsx

**Checkpoint**: User Story 3 complete — header checkbox reflects three visual states; clicking indeterminate resolves to all-selected; protected-only groups show disabled header

---

## Phase 6: User Story 4 — Keyboard Accessibility for Header Toggles (Priority: P3)

**Goal**: Keyboard-only users can navigate to and operate type header checkboxes using Tab, Space, and Enter keys with proper screen reader announcements

**Independent Test**: Tab to "Branches" header checkbox → press Space → verify all eligible branches toggle → press Enter → verify toggle again. Use screen reader → verify indeterminate state announced as "mixed".

### Implementation for User Story 4

- [ ] T024 [US4] Ensure `TypeGroupHeader` checkbox is natively focusable and included in tab order (use semantic `<input type="checkbox">` or `role="checkbox"` with `tabIndex={0}`) in solune/frontend/src/components/board/TypeGroupHeader.tsx
- [ ] T025 [US4] Add `aria-checked` attribute with `"true"`, `"false"`, or `"mixed"` values matching header checkbox state in solune/frontend/src/components/board/TypeGroupHeader.tsx
- [ ] T026 [US4] Add `aria-disabled="true"` and `aria-label` to 'main' branch row checkbox explaining protection reason in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T027 [US4] Add `aria-label` to each `TypeGroupHeader` describing the group and count (e.g., "Select all 5 branches for deletion") in solune/frontend/src/components/board/TypeGroupHeader.tsx
- [ ] T028 [US4] Verify Space and Enter key events trigger toggle on `TypeGroupHeader` — native checkbox handles this, but confirm if using custom `role="checkbox"` pattern in solune/frontend/src/components/board/TypeGroupHeader.tsx

**Checkpoint**: User Story 4 complete — keyboard navigation works; ARIA attributes announce correct states; 'main' row announces disabled reason

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Add visual hover and focus styles to `TypeGroupHeader` for sufficient hit targets and interactive feedback in solune/frontend/src/components/board/TypeGroupHeader.tsx
- [ ] T030 [P] Handle edge case: empty type groups should not render header or should render disabled header in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T031 [P] Handle edge case: when no items are selected, ensure Clean Up confirm/execute button is disabled or shows appropriate prompt in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T032 Verify end-to-end flow: preflight → confirm modal with headers → individual + bulk selection → execute with correct payload in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T033 [P] Run existing lint, type-check, and test suites to confirm no regressions (npm run lint, npm run type-check, npm run test:coverage in solune/frontend)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — delivers core bulk-select value
- **User Story 2 (Phase 4)**: Depends on Foundational — can run in parallel with US1 but logically builds on header toggle
- **User Story 3 (Phase 5)**: Depends on US1 completion (needs working header checkbox to add indeterminate state)
- **User Story 4 (Phase 6)**: Depends on US3 completion (needs all visual states to apply ARIA attributes)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. **MVP scope.**
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Independent from US1 but both required for MVP safety
- **User Story 3 (P2)**: Depends on US1 completion — extends the header checkbox with indeterminate visual state
- **User Story 4 (P3)**: Depends on US3 completion — applies ARIA attributes to all three checkbox states

### Within Each User Story

- Hook/utility changes before component integration
- Component rendering before payload wiring
- Core implementation before edge cases

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T004 and T005 can run in parallel (different files)
- T006, T007, T008 share same file — must be sequential
- T009, T010, T011 share same file — must be sequential
- T014 and T015 can run in parallel (different files)
- T020 and T021 can run in parallel (different files)
- T024, T025, T027, T028 share TypeGroupHeader.tsx — must be sequential
- T029, T030, T031, T033 are marked [P] in Polish phase — can run in parallel

---

## Parallel Example: User Story 1

```bash
# Phase 2 parallelism:
Task T004: "Create useGroupSelection hook in solune/frontend/src/hooks/useGroupSelection.ts"
Task T005: "Extract TypeGroupHeader component in solune/frontend/src/components/board/TypeGroupHeader.tsx"

# Phase 3 (US1) — sequential within CleanUpConfirmModal.tsx:
Task T006-T008: Integrate useGroupSelection per group type
Task T009-T011: Render TypeGroupHeader per group section
Task T012: Update BranchRow and PrRow sub-components
Task T013: Wire deletion payload
```

---

## Parallel Example: User Story 2

```bash
# These can be worked in parallel (different files):
Task T014: "Integrate isProtectedBranch into useGroupSelection hook"
Task T015: "Render 'main' branch with disabled checkbox in CleanUpConfirmModal"
Task T018: "Add server-side validation in cleanup backend endpoint"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup — define branch protection utility and extended types
2. Complete Phase 2: Foundational — refactor selection model, create hook and header component
3. Complete Phase 3: User Story 1 — header toggle bulk-select for all groups
4. Complete Phase 4: User Story 2 — 'main' branch protection on client + server
5. **STOP and VALIDATE**: Test bulk selection + main protection independently
6. Deploy/demo if ready — core value + safety delivered

### Incremental Delivery

1. Setup + Foundational → Selection model refactored, ready for features
2. Add User Story 1 → Bulk select works → Deploy/Demo (**MVP core**)
3. Add User Story 2 → 'main' branch protected → Deploy/Demo (**MVP safe**)
4. Add User Story 3 → Indeterminate state → Deploy/Demo (UX polish)
5. Add User Story 4 → Keyboard accessibility → Deploy/Demo (a11y compliance)
6. Polish phase → Edge cases, hover states, regressions checked

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (header toggle)
   - Developer B: User Story 2 (branch protection — separate files: hook, backend)
3. After US1 complete:
   - Developer A: User Story 3 (indeterminate state)
4. After US3 complete:
   - Developer A: User Story 4 (accessibility)
5. Polish phase: All developers in parallel on different files

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The spec does not request test tasks — add them only if explicitly required during implementation
- `CleanUpConfirmModal.tsx` is the primary file modified — coordinate sequential edits within the same file
- Backend validation (T018) is the only server-side task; all other tasks are frontend
