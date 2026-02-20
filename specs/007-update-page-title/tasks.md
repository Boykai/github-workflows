# Tasks: Update Page Title to "Front"

**Input**: Design documents from `/specs/007-update-page-title/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new tests required. Existing E2E test assertions are updated as maintenance to prevent regressions (Constitution Principle IV — Test Optionality).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline and confirm current title state before making changes

- [x] T001 Verify current title is "Agent Projects" in frontend/index.html, frontend/src/App.tsx, and frontend/e2e/ test files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational infrastructure changes needed — this feature modifies static string literals only

**⚠️ NOTE**: This phase is intentionally empty. No new dependencies, database changes, or framework modifications are required. All changes are isolated string replacements in existing files.

**Checkpoint**: No blocking prerequisites — user story implementation can begin immediately after baseline verification (T001)

---

## Phase 3: User Story 1 — Page Title Displays "Front" (Priority: P1) 🎯 MVP

**Goal**: Update the browser tab title and application headers to display "Front" instead of "Agent Projects"

**Independent Test**: Load the application in a browser, verify the browser tab displays "Front" and the main heading on both login and authenticated views displays "Front"

### Implementation for User Story 1

- [x] T002 [P] [US1] Update HTML page title from "Agent Projects" to "Front" in frontend/index.html (line 7)
- [x] T003 [P] [US1] Update login page header from "Agent Projects" to "Front" in frontend/src/App.tsx (line 72)
- [x] T004 [P] [US1] Update authenticated header from "Agent Projects" to "Front" in frontend/src/App.tsx (line 89)

**Checkpoint**: Browser tab and both application headers now display "Front". User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — No Residual References to Old Title (Priority: P2)

**Goal**: Ensure no remnants of the previous title "Agent Projects" remain in user-facing code or E2E test assertions

**Independent Test**: Search the rendered UI and frontend codebase for any occurrence of "Agent Projects" and confirm zero matches in user-facing files

### Implementation for User Story 2

- [x] T005 [P] [US2] Update title assertion on line 12 of frontend/e2e/auth.spec.ts from "Agent Projects" to "Front"
- [x] T006 [P] [US2] Update title assertion on line 24 of frontend/e2e/auth.spec.ts from "Agent Projects" to "Front"
- [x] T007 [P] [US2] Update title assertion on line 38 of frontend/e2e/auth.spec.ts from "Agent Projects" to "Front"
- [x] T008 [P] [US2] Update title regex assertion on line 62 of frontend/e2e/auth.spec.ts from /Agent Projects/i to /Front/i
- [x] T009 [P] [US2] Update title assertion on line 99 of frontend/e2e/auth.spec.ts from "Agent Projects" to "Front"
- [x] T010 [P] [US2] Update title assertion on line 43 of frontend/e2e/ui.spec.ts from "Agent Projects" to "Front"
- [x] T011 [P] [US2] Update title assertion on line 67 of frontend/e2e/ui.spec.ts from "Agent Projects" to "Front"
- [x] T012 [P] [US2] Update title assertion on line 69 of frontend/e2e/integration.spec.ts from "Agent Projects" to "Front"

**Checkpoint**: Zero occurrences of "Agent Projects" remain in user-facing frontend code and E2E tests.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T013 Run grep search for "Agent Projects" across frontend/index.html, frontend/src/App.tsx, and frontend/e2e/ to confirm zero matches
- [x] T014 Run quickstart.md validation steps to confirm browser tab and headers display "Front"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Empty — no blocking prerequisites
- **User Story 1 (Phase 3)**: Depends on Setup (T001) — can start after baseline verification
- **User Story 2 (Phase 4)**: Can start after Setup (T001) — independent of User Story 1
- **Polish (Phase 5)**: Depends on all user stories being complete (T002–T012)

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — implements the title change in source files
- **User Story 2 (P2)**: No dependencies on User Story 1 — updates E2E test assertions independently

### Within Each User Story

- **User Story 1**: All 3 tasks (T002, T003, T004) can run in parallel (different files or non-overlapping lines in same file)
- **User Story 2**: All 8 tasks (T005–T012) can run in parallel (different files or non-overlapping lines)

### Parallel Opportunities

- T002, T003, T004 can all run in parallel (T002 modifies index.html; T003 and T004 modify different lines in App.tsx)
- T005–T012 can all run in parallel (modifications span 3 different E2E test files with non-overlapping lines)
- User Story 1 and User Story 2 can proceed in parallel (no cross-dependencies)

---

## Parallel Example: User Story 1

```bash
# Launch all source file updates for User Story 1 together:
Task: "Update HTML page title in frontend/index.html (line 7)"
Task: "Update login page header in frontend/src/App.tsx (line 72)"
Task: "Update authenticated header in frontend/src/App.tsx (line 89)"
```

## Parallel Example: User Story 2

```bash
# Launch all E2E test assertion updates for User Story 2 together:
Task: "Update auth.spec.ts assertions (lines 12, 24, 38, 62, 99)"
Task: "Update ui.spec.ts assertions (lines 43, 67)"
Task: "Update integration.spec.ts assertion (line 69)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline (T001)
2. Complete Phase 3: User Story 1 (T002–T004)
3. **STOP and VALIDATE**: Load app in browser, confirm "Front" appears in tab and headers
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup (T001) → Baseline verified
2. Add User Story 1 (T002–T004) → Test independently → Browser shows "Front" (MVP!)
3. Add User Story 2 (T005–T012) → Test independently → E2E tests pass with new title
4. Polish (T013–T014) → Final grep verification and quickstart validation

### Parallel Team Strategy

With multiple developers:

1. Team verifies baseline together (T001)
2. Once baseline is confirmed:
   - Developer A: User Story 1 (T002–T004) — source file changes
   - Developer B: User Story 2 (T005–T012) — E2E test assertion updates
3. Both stories complete and validate independently

---

## Notes

- [P] tasks = different files or non-overlapping lines, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new tests are created — only existing E2E assertions are updated (maintenance)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 14 (1 setup, 3 US1, 8 US2, 2 polish)
