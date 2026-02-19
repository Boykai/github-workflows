# Tasks: Update App Name to "Robot"

**Input**: Design documents from `/specs/007-update-app-name/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new tests are required. Existing E2E test assertions that reference the old name "Agent Projects" are updated as part of the implementation (FR-008). No TDD approach was requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: No project initialization is needed — this feature modifies existing files only. This phase is intentionally empty.

*(No tasks — all target files already exist in the repository.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking infrastructure changes are required. All changes are independent string replacements in existing files. This phase is intentionally empty.

*(No tasks — no shared infrastructure or blocking prerequisites for a display-name rename.)*

**Checkpoint**: No foundational work required — user story implementation can begin immediately.

---

## Phase 3: User Story 1 — App Name Displays as "Robot" in the Browser (Priority: P1) 🎯 MVP

**Goal**: The browser tab title displays "Robot" when the application is loaded, so users can identify the app among open tabs.

**Independent Test**: Open the application in a browser and verify the tab title reads "Robot". Bookmark the page and confirm the default bookmark name is "Robot".

### Implementation for User Story 1

- [x] T001 [US1] Update HTML page title from "Agent Projects" to "Robot" in frontend/index.html

**Checkpoint**: Browser tab now displays "Robot". US1 is independently verifiable.

---

## Phase 4: User Story 2 — App Name Displays as "Robot" in the Application UI (Priority: P1)

**Goal**: All visible headings, titles, and branding elements in the application UI display "Robot" instead of "Agent Projects".

**Independent Test**: Navigate through the application (login page and authenticated view) and visually confirm all `<h1>` headings read "Robot".

### Implementation for User Story 2

- [x] T002 [US2] Update login page header from "Agent Projects" to "Robot" in frontend/src/App.tsx (line 72)
- [x] T003 [US2] Update authenticated app header from "Agent Projects" to "Robot" in frontend/src/App.tsx (line 89)

**Checkpoint**: Both login and authenticated headers display "Robot". US2 is independently verifiable.

---

## Phase 5: User Story 3 — App Name Displays as "Robot" in Backend and Developer Surfaces (Priority: P2)

**Goal**: Backend startup logs, API documentation title, developer environment name, and project metadata all display "Robot".

**Independent Test**: Start the backend and check startup log messages for "Starting Robot API". Access `/api/docs` and verify the title reads "Robot API". Check devcontainer name, pyproject.toml description, and .env.example header.

### Implementation for User Story 3

- [x] T004 [US3] Update startup log message from "Starting Agent Projects API" to "Starting Robot API" in backend/src/main.py (line 75)
- [x] T005 [US3] Update shutdown log message from "Shutting down Agent Projects API" to "Shutting down Robot API" in backend/src/main.py (line 77)
- [x] T006 [US3] Update FastAPI title from "Agent Projects API" to "Robot API" in backend/src/main.py (line 85)
- [x] T007 [US3] Update FastAPI description from "REST API for Agent Projects" to "REST API for Robot" in backend/src/main.py (line 86)
- [x] T008 [P] [US3] Update devcontainer name from "Agent Projects" to "Robot" in .devcontainer/devcontainer.json (line 2)
- [x] T009 [P] [US3] Update setup script log message from "Agent Projects" to "Robot" in .devcontainer/post-create.sh (line 7)
- [x] T010 [P] [US3] Update environment config header from "Agent Projects" to "Robot" in .env.example (line 2)
- [x] T011 [P] [US3] Update project description from "FastAPI backend for Agent Projects" to "FastAPI backend for Robot" in backend/pyproject.toml (line 4)

**Checkpoint**: All backend and developer surfaces display "Robot". US3 is independently verifiable.

---

## Phase 6: User Story 4 — No References to Old App Name Remain (Priority: P2)

**Goal**: Zero references to "Agent Projects" remain in user-facing content, configuration files, documentation, or test assertions. The rebrand is complete and professional.

**Independent Test**: Run `grep -rn "Agent Projects" . --include="*.html" --include="*.tsx" --include="*.ts" --include="*.py" --include="*.json" --include="*.toml" --include="*.sh" --include="*.md" | grep -v "specs/" | grep -v "node_modules/" | grep -v ".git/"` and confirm zero results.

### Implementation for User Story 4

- [x] T012 [P] [US4] Update main README heading from "# Agent Projects" to "# Robot" in README.md (line 1)
- [x] T013 [US4] Update backend README heading from "# Agent Projects — Backend" to "# Robot — Backend" in backend/README.md (line 1)
- [x] T014 [US4] Update backend README body text from "Agent Projects" to "Robot" in backend/README.md (line 3)
- [x] T015 [US4] Update E2E auth test h1 assertion from "Agent Projects" to "Robot" in frontend/e2e/auth.spec.ts (line 12)
- [x] T016 [US4] Update E2E auth test h1 assertion from "Agent Projects" to "Robot" in frontend/e2e/auth.spec.ts (line 24)
- [x] T017 [US4] Update E2E auth test h1 assertion from "Agent Projects" to "Robot" in frontend/e2e/auth.spec.ts (line 38)
- [x] T018 [US4] Update E2E auth test page title assertion from /Agent Projects/i to /Robot/i in frontend/e2e/auth.spec.ts (line 62)
- [x] T019 [US4] Update E2E auth test h1 assertion from "Agent Projects" to "Robot" in frontend/e2e/auth.spec.ts (line 99)
- [x] T020 [US4] Update E2E ui test h1 assertion from "Agent Projects" to "Robot" in frontend/e2e/ui.spec.ts (line 43)
- [x] T021 [US4] Update E2E ui test h1 assertion from "Agent Projects" to "Robot" in frontend/e2e/ui.spec.ts (line 67)
- [x] T022 [P] [US4] Update E2E integration test h1 assertion from "Agent Projects" to "Robot" in frontend/e2e/integration.spec.ts (line 69)
- [x] T023 [US4] Run full codebase search to verify zero remaining "Agent Projects" references outside specs/

**Checkpoint**: No references to "Agent Projects" remain in user-facing content, configuration, or test assertions. US4 is independently verifiable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T024 Run quickstart.md validation checklist to confirm all FRs are satisfied
- [x] T025 Verify all E2E tests pass with the updated application name

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Empty — no project initialization required
- **Foundational (Phase 2)**: Empty — no blocking prerequisites for string replacements
- **User Story 1 (Phase 3)**: No dependencies — can start immediately
- **User Story 2 (Phase 4)**: No dependencies — can start immediately (parallel with US1)
- **User Story 3 (Phase 5)**: No dependencies — can start immediately (parallel with US1, US2)
- **User Story 4 (Phase 6)**: Depends on US1, US2, US3 completion (ensures all name changes are done before verifying zero old references)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent — modifies only `frontend/index.html`
- **User Story 2 (P1)**: Independent — modifies only `frontend/src/App.tsx`
- **User Story 3 (P2)**: Independent — modifies `backend/src/main.py`, `.devcontainer/`, `.env.example`, `backend/pyproject.toml`
- **User Story 4 (P2)**: Depends on US1 + US2 + US3 — verifies completeness and updates READMEs + E2E test assertions

### Within Each User Story

- US1 has a single task — no parallelism considerations
- US2 tasks modify the same file (`App.tsx`) — sequential within story
- US3: T004–T007 sequential (same file `main.py`); T008–T011 parallelizable (different files each)
- US4: tasks grouped by file — groups can run in parallel, tasks within same-file groups are sequential
- T023 (verification search) must run after all other US4 tasks are complete

### Parallel Opportunities

- US1 has a single task (T001) — no internal parallelism needed
- US2 tasks (T002–T003) modify the same file (`App.tsx`) — must be sequential
- US3 tasks T004–T007 modify the same file (`main.py`) — must be sequential; T008–T011 modify different files — can run in parallel with each other and with main.py changes
- US4 groups by file: T012 (README.md), T013–T014 (backend/README.md), T015–T019 (auth.spec.ts), T020–T021 (ui.spec.ts), T022 (integration.spec.ts) — groups can run in parallel
- US1, US2, and US3 can all execute in parallel with each other — they modify different files across stories
- All [P] tasks within US3 modify different files and can run simultaneously
- All [P] tasks within US4 modify different files and can run simultaneously

---

## Parallel Example: User Story 3

```bash
# Tasks T004-T007 modify the same file (main.py) and must run sequentially.
# Tasks T008-T011 each modify different files and can run in parallel with each other:
Task T008: "Update devcontainer name in .devcontainer/devcontainer.json"
Task T009: "Update setup script in .devcontainer/post-create.sh"
Task T010: "Update env header in .env.example"
Task T011: "Update pyproject description in backend/pyproject.toml"
```

---

## Parallel Example: User Story 4

```bash
# These groups modify different files and can run in parallel:
# Group 1 (README.md - single file):
Task T012: "Update README.md"
# Group 2 (backend/README.md - sequential, same file):
Task T013: "Update backend/README.md heading"
Task T014: "Update backend/README.md body"
# Group 3 (auth.spec.ts - sequential, same file):
Task T015-T019: "Update frontend/e2e/auth.spec.ts assertions"
# Group 4 (ui.spec.ts - sequential, same file):
Task T020-T021: "Update frontend/e2e/ui.spec.ts assertions"
# Group 5 (integration.spec.ts - single file):
Task T022: "Update frontend/e2e/integration.spec.ts assertion"

# Groups 1-5 can all run in parallel (different files).
# T023 (verification) runs last after all changes are complete.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001: Update browser tab title in `frontend/index.html`
2. **STOP and VALIDATE**: Open app in browser, verify tab reads "Robot"
3. Deploy/demo if ready — users immediately see "Robot" in their browser tab

### Incremental Delivery

1. Add User Story 1 (T001) → Browser tab displays "Robot" → MVP!
2. Add User Story 2 (T002–T003) → App UI headers display "Robot"
3. Add User Story 3 (T004–T011) → Backend/developer surfaces display "Robot"
4. Add User Story 4 (T012–T023) → All old references eliminated, tests updated
5. Polish (T024–T025) → Full validation and E2E test confirmation

### Parallel Team Strategy

With multiple developers:

1. **Developer A**: User Story 1 + User Story 2 (frontend changes — `index.html`, `App.tsx`)
2. **Developer B**: User Story 3 (backend + config changes — `main.py`, `.devcontainer/`, `.env.example`, `pyproject.toml`)
3. **Developer C**: User Story 4 (documentation + E2E tests — `README.md`, `backend/README.md`, `e2e/*.spec.ts`)
4. All three developers can work simultaneously — zero file conflicts between stories

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 25 |
| **User Story 1 tasks** | 1 (T001) |
| **User Story 2 tasks** | 2 (T002–T003) |
| **User Story 3 tasks** | 8 (T004–T011) |
| **User Story 4 tasks** | 12 (T012–T023) |
| **Polish tasks** | 2 (T024–T025) |
| **Parallel opportunities** | US1/US2/US3 can run in parallel across stories; T008–T011 parallel within US3; file-groups parallel within US4 |
| **Suggested MVP scope** | User Story 1 only (T001) |
| **Estimated time** | 10–15 minutes total |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new test infrastructure is required — only existing E2E assertion updates (FR-008)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Spec docs in `specs/007-update-app-name/` are excluded from "Agent Projects" search verification (they document the old name intentionally)
