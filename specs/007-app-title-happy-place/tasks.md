# Tasks: Update App Title to "Happy Place"

**Input**: Design documents from `/specs/007-app-title-happy-place/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Not explicitly requested in feature specification. Existing E2E tests that assert the app title will be updated as part of the implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Identify and confirm all occurrences of the current app title before making changes

- [ ] T001 Run codebase-wide search for "Agent Projects" and confirm all occurrences to be replaced

---

## Phase 2: User Story 1 — Browser Tab Displays New Title (Priority: P1) 🎯 MVP

**Goal**: Update the browser tab to display "Happy Place" when users open the application

**Independent Test**: Open the application in a browser and verify the tab displays "Happy Place"

### Implementation for User Story 1

- [ ] T002 [US1] Update `<title>` tag from "Agent Projects" to "Happy Place" in frontend/index.html
- [ ] T003 [US1] Update E2E test title assertion from "Agent Projects" to "Happy Place" in frontend/e2e/auth.spec.ts (line 62)

**Checkpoint**: Browser tab shows "Happy Place". Title assertion in E2E tests updated.

---

## Phase 3: User Story 2 — Application Header Shows New Title (Priority: P1)

**Goal**: Update the in-app header/navbar to display "Happy Place" on both logged-in and logged-out views

**Independent Test**: Load the application and verify the header displays "Happy Place" on both logged-in and logged-out views

### Implementation for User Story 2

- [ ] T004 [P] [US2] Update logged-out `<h1>` header from "Agent Projects" to "Happy Place" in frontend/src/App.tsx (line 72)
- [ ] T005 [P] [US2] Update logged-in `<h1>` header from "Agent Projects" to "Happy Place" in frontend/src/App.tsx (line 89)
- [ ] T006 [P] [US2] Update E2E h1 assertion from "Agent Projects" to "Happy Place" in frontend/e2e/auth.spec.ts (lines 12, 24, 38, 99)
- [ ] T007 [P] [US2] Update E2E h1 assertion from "Agent Projects" to "Happy Place" in frontend/e2e/ui.spec.ts (lines 43, 67)
- [ ] T008 [P] [US2] Update E2E h1 assertion from "Agent Projects" to "Happy Place" in frontend/e2e/integration.spec.ts (line 69)

**Checkpoint**: Header shows "Happy Place" on all views. All E2E test assertions updated.

---

## Phase 4: User Story 3 — Consistent Branding Across All Touchpoints (Priority: P2)

**Goal**: Update all remaining occurrences of "Agent Projects" in metadata, configuration, documentation, backend, and developer tooling to "Happy Place"

**Independent Test**: Perform a full codebase search for "Agent Projects" and verify zero results remain

### Implementation for User Story 3

- [ ] T009 [P] [US3] Update FastAPI app title from "Agent Projects API" to "Happy Place API" in backend/src/main.py (line 85)
- [ ] T010 [P] [US3] Update FastAPI app description from "REST API for Agent Projects" to "REST API for Happy Place" in backend/src/main.py (line 86)
- [ ] T011 [P] [US3] Update startup log message from "Starting Agent Projects API" to "Starting Happy Place API" in backend/src/main.py (line 75)
- [ ] T012 [P] [US3] Update shutdown log message from "Shutting down Agent Projects API" to "Shutting down Happy Place API" in backend/src/main.py (line 77)
- [ ] T013 [P] [US3] Update project description from "FastAPI backend for Agent Projects" to "FastAPI backend for Happy Place" in backend/pyproject.toml (line 4)
- [ ] T014 [P] [US3] Update docstring from "Agent Projects" to "Happy Place" in backend/tests/test_api_e2e.py (line 2)
- [ ] T015 [P] [US3] Update devcontainer name from "Agent Projects" to "Happy Place" in .devcontainer/devcontainer.json (line 2)
- [ ] T016 [P] [US3] Update setup message from "Setting up Agent Projects development environment" to "Setting up Happy Place development environment" in .devcontainer/post-create.sh (line 7)
- [ ] T017 [P] [US3] Update environment config comment from "Agent Projects" to "Happy Place" in .env.example (line 2)
- [ ] T018 [P] [US3] Update heading from "# Agent Projects" to "# Happy Place" in README.md (line 1)
- [ ] T019 [P] [US3] Update heading from "# Agent Projects — Backend" to "# Happy Place — Backend" and description references in backend/README.md (lines 1, 3)
- [ ] T020 [P] [US3] Update doc comment from "Agent Projects API" to "Happy Place API" in frontend/src/types/index.ts (line 2)
- [ ] T021 [P] [US3] Update doc comment from "Agent Projects" to "Happy Place" in frontend/src/services/api.ts (line 2)

**Checkpoint**: All occurrences of "Agent Projects" replaced with "Happy Place". Codebase-wide search confirms zero remaining references.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [ ] T022 Run full codebase search to confirm zero remaining "Agent Projects" references
- [ ] T023 Run existing E2E test suite to verify all title-related assertions pass with "Happy Place"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: Depends on Phase 1 — MVP delivery target (browser tab)
- **US2 (Phase 3)**: Can run in parallel with Phase 2 (different files)
- **US3 (Phase 4)**: Can run in parallel with Phases 2 and 3 (different files)
- **Polish (Phase 5)**: Depends on all prior phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — standalone browser tab update
- **User Story 2 (P1)**: No dependencies on other stories — standalone header update
- **User Story 3 (P2)**: No dependencies on other stories — standalone metadata/config update

### Within Each User Story

- Frontend source changes before E2E test updates (to keep tests consistent with code)
- Backend changes are all independent of each other

### Parallel Opportunities

- All tasks marked [P] within a phase can run in parallel (they touch different files)
- All three user story phases (2, 3, 4) can run in parallel since they modify different files
- Within Phase 4 (US3), all 13 tasks can run in parallel — each modifies a different file

---

## Parallel Example: Phase 4 (User Story 3)

```bash
# All of these tasks modify different files and can run simultaneously:
T009: Update FastAPI title in backend/src/main.py
T013: Update description in backend/pyproject.toml
T014: Update docstring in backend/tests/test_api_e2e.py
T015: Update devcontainer name in .devcontainer/devcontainer.json
T016: Update setup message in .devcontainer/post-create.sh
T017: Update env config comment in .env.example
T018: Update heading in README.md
T019: Update heading and description in backend/README.md
T020: Update doc comment in frontend/src/types/index.ts
T021: Update doc comment in frontend/src/services/api.ts
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (confirm all occurrences)
2. Complete Phase 2: User Story 1 (browser tab title)
3. **STOP and VALIDATE**: Open app in browser, verify tab shows "Happy Place"
4. Deploy/demo if ready

### Incremental Delivery

1. Phase 1: Setup → Identify all occurrences
2. Phase 2: US1 → Browser tab shows "Happy Place" → **MVP!**
3. Phase 3: US2 → Header shows "Happy Place" → Consistent visible branding
4. Phase 4: US3 → All metadata, config, docs updated → Complete branding
5. Phase 5: Polish → Full verification, all E2E tests pass

### Parallel Team Strategy

With multiple developers:

1. All three user story phases can start simultaneously (different files)
   - Developer A: US1 (browser tab + title E2E)
   - Developer B: US2 (header + header E2E tests)
   - Developer C: US3 (metadata, config, docs, backend)
2. All changes are pure string replacements with no cross-dependencies

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- This is a purely cosmetic/branding change — no logic, schema, or API changes
- All tasks are simple string replacements: "Agent Projects" → "Happy Place"
- The old title "Agent Projects" appears ~25 times across 15 files
- Commit after each phase for clean history
- Stop at any checkpoint to validate independently
