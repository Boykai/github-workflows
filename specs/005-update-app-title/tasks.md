# Tasks: Update App Title to "Happy Place"

**Input**: Design documents from `/specs/005-update-app-title/`
**Prerequisites**: spec.md (user stories and requirements)

**Tests**: Not explicitly requested as new test tasks. Existing E2E test assertions referencing the old title will be updated as part of User Story 4 (residual cleanup).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current baseline and identify all occurrences of the old title

- [ ] T001 Verify current title "Agent Projects" appears in frontend/index.html, frontend/src/App.tsx, backend/src/main.py, and all E2E test files by running a codebase-wide search

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational blocking tasks required — this feature is a string replacement across existing files with no new infrastructure needed.

**Checkpoint**: Baseline verified — user story implementation can now begin.

---

## Phase 3: User Story 1 — Browser Tab Displays New Title (Priority: P1) 🎯 MVP

**Goal**: The browser tab displays "Happy Place" when the application is loaded.

**Independent Test**: Open the application in any browser and verify the tab reads "Happy Place".

### Implementation for User Story 1

- [ ] T002 [US1] Update `<title>` tag from "Agent Projects" to "Happy Place" in frontend/index.html

**Checkpoint**: Browser tab now displays "Happy Place". This is verifiable by loading the app and checking the tab title.

---

## Phase 4: User Story 2 — In-App Header Displays New Title (Priority: P1)

**Goal**: The header/navbar area displays "Happy Place" in both logged-out and logged-in views.

**Independent Test**: Load the application and visually confirm the header reads "Happy Place" in both views.

### Implementation for User Story 2

- [ ] T003 [US2] Update logged-out view `<h1>` from "Agent Projects" to "Happy Place" on line 72 of frontend/src/App.tsx
- [ ] T004 [US2] Update logged-in header `<h1>` from "Agent Projects" to "Happy Place" on line 89 of frontend/src/App.tsx

**Checkpoint**: Both logged-out and logged-in views display "Happy Place" in the header.

---

## Phase 5: User Story 3 — Metadata Reflects New Title (Priority: P2)

**Goal**: HTML metadata reflects "Happy Place" for search results, bookmarks, and social shares.

**Independent Test**: Inspect the page source and verify the `<title>` tag contains "Happy Place". No PWA manifest or OpenGraph meta tags currently exist.

### Implementation for User Story 3

- [ ] T005 [US3] Verify `<title>` tag already updated in frontend/index.html (completed by T002) — no additional metadata tags (og:title, manifest.json) exist to update

**Checkpoint**: All metadata reflects "Happy Place". No PWA manifest or OpenGraph tags exist in this project, so no additional changes are needed.

---

## Phase 6: User Story 4 — No Residual Old Title References (Priority: P2)

**Goal**: Zero instances of "Agent Projects" remain in user-facing source files.

**Independent Test**: Run `grep -r "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" --include="*.py" --include="*.toml" --include="*.json" --include="*.md" --include="*.sh"` and verify zero matches (excluding spec files).

### Implementation for User Story 4

#### Backend files

- [ ] T006 [P] [US4] Update FastAPI startup log message from "Agent Projects" to "Happy Place" on line 75 of backend/src/main.py
- [ ] T007 [P] [US4] Update FastAPI shutdown log message from "Agent Projects" to "Happy Place" on line 77 of backend/src/main.py
- [ ] T008 [P] [US4] Update FastAPI app `title` from "Agent Projects API" to "Happy Place API" on line 85 of backend/src/main.py
- [ ] T009 [P] [US4] Update FastAPI app `description` from "REST API for Agent Projects" to "REST API for Happy Place" on line 86 of backend/src/main.py
- [ ] T010 [P] [US4] Update project description from "FastAPI backend for Agent Projects" to "FastAPI backend for Happy Place" in backend/pyproject.toml line 4
- [ ] T011 [P] [US4] Update docstring comment from "Agent Projects" to "Happy Place" on line 2 of backend/tests/test_api_e2e.py

#### Frontend source files

- [ ] T012 [P] [US4] Update JSDoc comment from "Agent Projects" to "Happy Place" on line 2 of frontend/src/services/api.ts
- [ ] T013 [P] [US4] Update JSDoc comment from "Agent Projects" to "Happy Place" on line 2 of frontend/src/types/index.ts

#### E2E test files

- [ ] T014 [P] [US4] Update all `toContainText('Agent Projects')` assertions to `toContainText('Happy Place')` in frontend/e2e/auth.spec.ts (lines 12, 24, 38, 62, 99)
- [ ] T015 [P] [US4] Update all `toContainText('Agent Projects')` assertions to `toContainText('Happy Place')` in frontend/e2e/ui.spec.ts (lines 43, 67)
- [ ] T016 [P] [US4] Update `toContainText('Agent Projects')` assertion to `toContainText('Happy Place')` in frontend/e2e/integration.spec.ts (line 69)

#### Configuration and documentation files

- [ ] T017 [P] [US4] Update devcontainer name from "Agent Projects" to "Happy Place" in .devcontainer/devcontainer.json line 2
- [ ] T018 [P] [US4] Update setup echo message from "Agent Projects" to "Happy Place" in .devcontainer/post-create.sh line 7
- [ ] T019 [P] [US4] Update environment config comment from "Agent Projects" to "Happy Place" in .env.example line 2
- [ ] T020 [P] [US4] Update heading from "# Agent Projects" to "# Happy Place" in README.md line 1
- [ ] T021 [P] [US4] Update heading and description from "Agent Projects" to "Happy Place" in backend/README.md lines 1 and 3

**Checkpoint**: Zero instances of "Agent Projects" remain outside of spec documentation files.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [ ] T022 Run codebase-wide search to confirm zero remaining "Agent Projects" references outside specs/
- [ ] T023 Verify all E2E test assertions reference "Happy Place" by reviewing frontend/e2e/*.spec.ts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify baseline first
- **Foundational (Phase 2)**: No blocking tasks for this feature
- **User Story 1 (Phase 3)**: Can start immediately after setup
- **User Story 2 (Phase 4)**: Can start immediately after setup, independent of US1
- **User Story 3 (Phase 5)**: Depends on US1 completion (title tag shared)
- **User Story 4 (Phase 6)**: Can start immediately after setup, independent of US1/US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — single file change
- **User Story 2 (P1)**: No dependencies on other stories — single file change
- **User Story 3 (P2)**: Shares `<title>` tag with US1 — verify after US1 completes
- **User Story 4 (P2)**: Independent of other stories — covers all remaining files

### Parallel Opportunities

- T002 (US1) and T003/T004 (US2) can run in parallel (different files)
- All US4 tasks (T006–T021) can run in parallel (all different files)
- US1, US2, and US4 can all proceed simultaneously

---

## Parallel Example: User Story 4

```bash
# All US4 tasks touch different files and can run simultaneously:
Task: T006 "Update startup log in backend/src/main.py"
Task: T010 "Update description in backend/pyproject.toml"
Task: T012 "Update comment in frontend/src/services/api.ts"
Task: T014 "Update assertions in frontend/e2e/auth.spec.ts"
Task: T015 "Update assertions in frontend/e2e/ui.spec.ts"
Task: T017 "Update name in .devcontainer/devcontainer.json"
Task: T020 "Update heading in README.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline
2. Complete Phase 3: Update browser tab title (1 file, 1 line)
3. **STOP and VALIDATE**: Open app, verify tab reads "Happy Place"
4. Deploy/demo if ready

### Incremental Delivery

1. Verify baseline → Baseline confirmed
2. Update browser tab title (US1) → Tab shows "Happy Place" (MVP!)
3. Update in-app headers (US2) → Headers show "Happy Place"
4. Verify metadata (US3) → Metadata confirmed
5. Remove all residual references (US4) → Zero old title references remain
6. Polish → Final verification complete

### Parallel Team Strategy

With multiple developers:

1. Setup verification together (Phase 1)
2. Once verified:
   - Developer A: US1 (browser tab) + US3 (metadata verification)
   - Developer B: US2 (in-app headers)
   - Developer C: US4 (all residual references across backend, tests, config, docs)
3. All stories complete independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This feature is a straightforward string replacement — no new files, models, or services needed
- The old title "Agent Projects" appears ~25 times across ~16 files
- Spec files (specs/005-update-app-title/) are excluded from residual cleanup — they document the old title for historical reference
- No PWA manifest (manifest.json) or OpenGraph meta tags exist in this project
- Commit after each task or logical group
