# Tasks: Update App Title to 'One More'

**Input**: Design documents from `/specs/007-update-app-title/`
**Prerequisites**: spec.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Existing E2E tests referencing the app title will need assertion updates.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup required — this is a string replacement task with no new dependencies, configuration, or project structure changes.

*(No tasks in this phase)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking tasks — all title changes are independent string replacements in existing files.

*(No tasks in this phase)*

---

## Phase 3: User Story 1 - Browser Tab Title Display (Priority: P1) 🎯 MVP

**Goal**: Update the HTML document title so the browser tab displays "One More"

**Independent Test**: Open the application in a browser and verify the browser tab displays "One More" as the page title.

### Implementation for User Story 1

- [ ] T001 [US1] Update `<title>` tag from "Agent Projects" to "One More" in frontend/index.html
- [ ] T002 [P] [US1] Update page title assertion in E2E test from "Agent Projects" to "One More" in frontend/e2e/auth.spec.ts

**Checkpoint**: Browser tab should now display "One More" when the application is opened.

---

## Phase 4: User Story 2 - Application Header Display (Priority: P2)

**Goal**: Update the application header text so "One More" is displayed in the main UI header on both the login page and the authenticated view.

**Independent Test**: Open the application, verify the login page header shows "One More", then sign in and verify the authenticated header also shows "One More".

### Implementation for User Story 2

- [ ] T003 [P] [US2] Update login page `<h1>` text from "Agent Projects" to "One More" in frontend/src/App.tsx (line ~72)
- [ ] T004 [P] [US2] Update authenticated header `<h1>` text from "Agent Projects" to "One More" in frontend/src/App.tsx (line ~89)
- [ ] T005 [P] [US2] Update header text assertions in E2E tests from "Agent Projects" to "One More" in frontend/e2e/auth.spec.ts
- [ ] T006 [P] [US2] Update header text assertions in E2E tests from "Agent Projects" to "One More" in frontend/e2e/ui.spec.ts
- [ ] T007 [P] [US2] Update header text assertion in E2E test from "Agent Projects" to "One More" in frontend/e2e/integration.spec.ts

**Checkpoint**: Both login page and authenticated header should display "One More".

---

## Phase 5: User Story 3 - Complete Branding Consistency (Priority: P3)

**Goal**: Ensure no references to the old title "Agent Projects" remain anywhere in the application codebase, including backend, configuration, and documentation.

**Independent Test**: Search the entire codebase for "Agent Projects" and verify zero results in user-facing or configuration files.

### Implementation for User Story 3

- [ ] T008 [P] [US3] Update FastAPI app title and description from "Agent Projects" to "One More" in backend/src/main.py
- [ ] T009 [P] [US3] Update startup/shutdown log messages from "Agent Projects" to "One More" in backend/src/main.py
- [ ] T010 [P] [US3] Update project description from "Agent Projects" to "One More" in backend/pyproject.toml
- [ ] T011 [P] [US3] Update devcontainer name from "Agent Projects" to "One More" in .devcontainer/devcontainer.json
- [ ] T012 [P] [US3] Update setup script echo message from "Agent Projects" to "One More" in .devcontainer/post-create.sh
- [ ] T013 [P] [US3] Update environment config comment from "Agent Projects" to "One More" in .env.example
- [ ] T014 [P] [US3] Update heading from "Agent Projects" to "One More" in README.md
- [ ] T015 [P] [US3] Update heading and description references from "Agent Projects" to "One More" in backend/README.md
- [ ] T016 [P] [US3] Update JSDoc comment from "Agent Projects" to "One More" in frontend/src/services/api.ts
- [ ] T017 [P] [US3] Update JSDoc comment from "Agent Projects" to "One More" in frontend/src/types/index.ts
- [ ] T018 [P] [US3] Update docstring from "Agent Projects" to "One More" in backend/tests/test_api_e2e.py

**Checkpoint**: A codebase-wide search for "Agent Projects" should return zero results outside of spec/documentation files.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T019 Run full codebase search to confirm no remaining "Agent Projects" references in source files
- [ ] T020 Visually verify browser tab title, login header, and authenticated header display "One More"

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 3: US1 - Browser Tab (T001-T002)
Phase 4: US2 - Header Display (T003-T007)    ← can run in parallel with Phase 3
Phase 5: US3 - Branding Consistency (T008-T018)    ← can run in parallel with Phases 3-4
Phase 6: Polish (T019-T020)    ← depends on all previous phases
```

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — can start immediately
- **User Story 2 (P2)**: No dependencies on US1 — can start in parallel
- **User Story 3 (P3)**: No dependencies on US1/US2 — can start in parallel

### Parallel Opportunities

- All user stories are fully independent and can be implemented in parallel
- Within US3, all tasks (T008-T018) modify different files and can run in parallel
- Within US2, tasks T003-T007 modify different files (except T003+T004 both in App.tsx) and most can run in parallel

---

## Parallel Example: User Story 3

```bash
# All US3 tasks modify different files and can run simultaneously:
Task: "Update FastAPI config in backend/src/main.py"
Task: "Update pyproject.toml in backend/pyproject.toml"
Task: "Update devcontainer in .devcontainer/devcontainer.json"
Task: "Update README in README.md"
Task: "Update backend README in backend/README.md"
Task: "Update .env.example"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3: Update browser tab title (T001-T002)
2. **STOP and VALIDATE**: Open app in browser, verify tab shows "One More"
3. Deploy/demo if ready

### Incremental Delivery

1. User Story 1 → Browser tab shows "One More" (MVP!)
2. User Story 2 → Headers show "One More" → Deploy/Demo
3. User Story 3 → All references updated → Deploy/Demo (complete rebranding)

### Parallel Team Strategy

With multiple developers:

1. Developer A: User Story 1 (browser tab)
2. Developer B: User Story 2 (headers)
3. Developer C: User Story 3 (consistency sweep)
4. All stories complete independently — no coordination needed

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| US1 - Browser Tab | T001-T002 | index.html, auth.spec.ts |
| US2 - Header | T003-T007 | App.tsx, auth.spec.ts, ui.spec.ts, integration.spec.ts |
| US3 - Consistency | T008-T018 | main.py, pyproject.toml, devcontainer.json, post-create.sh, .env.example, README.md, backend/README.md, api.ts, index.ts, test_api_e2e.py |
| Polish | T019-T020 | N/A (validation only) |

**Total Tasks**: 20
**Tasks per User Story**: US1: 2, US2: 5, US3: 11, Polish: 2
**Parallel Opportunities**: All 3 user stories can run in parallel; 11 of 18 implementation tasks are parallelizable
**Suggested MVP Scope**: User Story 1 only (T001-T002) — browser tab title update

## Notes

- All tasks are simple string replacements from "Agent Projects" to "One More"
- No architectural changes, new dependencies, or data model updates required
- E2E test updates (T002, T005-T007) ensure existing test assertions match the new title
- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
