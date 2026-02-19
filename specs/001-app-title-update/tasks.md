# Tasks: App Title Update to 'GitHub Workflows'

**Input**: Design documents from `/specs/001-app-title-update/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/file-changes.md ✅, quickstart.md ✅

**Tests**: Not explicitly requested in specification. E2E test updates included only if existing assertions fail.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths included

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline and confirm current title state

- [ ] T001 Verify current app title strings by searching for existing title text in frontend/index.html and frontend/src/App.tsx

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational infrastructure required — changes are isolated string replacements in existing files

**⚠️ NOTE**: This feature requires no new dependencies, directories, or shared infrastructure. Phase 2 is intentionally empty per plan.md (direct string replacement approach).

**Checkpoint**: Foundation ready — no blocking prerequisites needed, user story implementation can begin

---

## Phase 3: User Story 1 - Browser Tab Title Display (Priority: P1) 🎯 MVP

**Goal**: Display "GitHub Workflows" in the browser tab so users can identify the application among open tabs

**Independent Test**: Open the application URL in a browser and verify the browser tab displays "GitHub Workflows" as the page title

### Implementation for User Story 1

- [ ] T002 [US1] Replace title text in `<title>` element on line 7 of frontend/index.html from current value to "GitHub Workflows"

**Checkpoint**: Browser tab displays "GitHub Workflows" — User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - Application Header Display (Priority: P2)

**Goal**: Display "GitHub Workflows" in the main application headers (login page and authenticated view) for consistent branding

**Independent Test**: Navigate through the application and verify "GitHub Workflows" appears in the header on both the login page and the authenticated view

### Implementation for User Story 2

- [ ] T003 [P] [US2] Replace login page header text in `<h1>` element in frontend/src/App.tsx from current value to "GitHub Workflows"
- [ ] T004 [P] [US2] Replace authenticated view header text in `<h1>` element in frontend/src/App.tsx from current value to "GitHub Workflows"

**Checkpoint**: Both login and authenticated headers display "GitHub Workflows" — User Story 2 is fully functional and independently testable

---

## Phase 5: User Story 3 - Complete Branding Consistency (Priority: P3)

**Goal**: Ensure no references to the old application title remain in user-facing areas

**Independent Test**: Perform a codebase search for the old title text and verify zero matches in frontend user-facing code

### Implementation for User Story 3

- [ ] T005 [US3] Search entire frontend/ directory for old title string references and verify zero matches remain
- [ ] T006 [US3] Run existing E2E test suite (frontend/e2e/auth.spec.ts) and update title assertions only if tests fail due to old title references

**Checkpoint**: No old title references remain — complete branding consistency achieved

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and manual validation

- [ ] T007 [P] Verify browser tab title by opening the application in a browser
- [ ] T008 [P] Verify login page header displays "GitHub Workflows" by loading the unauthenticated view
- [ ] T009 [P] Verify authenticated header displays "GitHub Workflows" after logging in
- [ ] T010 Run quickstart.md validation checklist to confirm all acceptance criteria pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Empty — no blocking prerequisites
- **User Story 1 (Phase 3)**: Can start after Setup (Phase 1)
- **User Story 2 (Phase 4)**: Can start after Setup (Phase 1) — independent of US1
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion (searches for remaining old references)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent — modifies frontend/index.html only
- **User Story 2 (P2)**: Independent — modifies frontend/src/App.tsx only
- **User Story 3 (P3)**: Depends on US1 + US2 — verifies completeness of changes made in both

### Within Each User Story

- US1: Single task (one file, one replacement)
- US2: Two parallel tasks (same file, different locations)
- US3: Sequential (search first, then fix if needed)

### Parallel Opportunities

- T003 + T004 can run in parallel (different `<h1>` elements in App.tsx)
- T002 (index.html) can run in parallel with T003/T004 (App.tsx) — different files
- T007 + T008 + T009 (verification tasks) can run in parallel
- US1 and US2 can be implemented simultaneously by different developers

---

## Parallel Example: User Stories 1 & 2

```bash
# US1 and US2 can execute simultaneously (different files):
Task: "T002 [US1] Replace title in frontend/index.html"
Task: "T003 [US2] Replace login header in frontend/src/App.tsx"
Task: "T004 [US2] Replace authenticated header in frontend/src/App.tsx"

# All verification tasks in parallel:
Task: "T007 Verify browser tab title"
Task: "T008 Verify login page header"
Task: "T009 Verify authenticated header"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 3: User Story 1 (browser tab title)
3. **STOP and VALIDATE**: Open app in browser, confirm tab shows "GitHub Workflows"
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup → Baseline confirmed
2. Add User Story 1 → Browser tab updated → Test independently (MVP!)
3. Add User Story 2 → Application headers updated → Test independently
4. Add User Story 3 → Old references removed → Test independently
5. Polish → Full verification complete
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Developer A: User Story 1 (frontend/index.html)
2. Developer B: User Story 2 (frontend/src/App.tsx)
3. Both complete → Developer A or B: User Story 3 (verification)
4. Stories complete and integrate independently (no merge conflicts — different files)

---

## Notes

- [P] tasks = different files or locations, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new tests required per spec — manual verification sufficient (Constitution Principle IV: Test Optionality)
- E2E test updates in T006 are conditional — only if existing tests fail
- Total implementation estimated at 5-10 minutes per quickstart.md
