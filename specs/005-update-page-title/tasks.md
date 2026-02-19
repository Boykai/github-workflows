# Tasks: Update Page Title to "Objects"

**Input**: Design documents from `/specs/005-update-page-title/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/file-changes.md, quickstart.md

**Tests**: Not explicitly requested in feature specification. Existing E2E test assertions will be updated as part of the title change (FR-006), but no new tests are added per Test Optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current state and confirm baseline before making changes

- [ ] T001 Verify all occurrences of "Agent Projects" in the codebase by running `grep -rn "Agent Projects" . --include="*.html" --include="*.tsx" --include="*.ts" --include="*.py" --include="*.toml" --include="*.json" --include="*.md" --include="*.sh" --include="*.env*" | grep -v node_modules | grep -v .git/ | grep -v specs/`

---

## Phase 2: User Story 1 — See Updated Page Title (Priority: P1) 🎯 MVP

**Goal**: The browser tab title and main page headers display "Objects" instead of "Agent Projects" in both unauthenticated and authenticated views.

**Independent Test**: Open the application in a browser and verify (1) the browser tab title reads "Objects", (2) the login page header reads "Objects", and (3) the authenticated page header reads "Objects".

### Implementation for User Story 1

- [ ] T002 [US1] Replace `<title>Agent Projects</title>` with `<title>Objects</title>` in frontend/index.html
- [ ] T003 [P] [US1] Replace login page `<h1>Agent Projects</h1>` with `<h1>Objects</h1>` on line 72 of frontend/src/App.tsx
- [ ] T004 [P] [US1] Replace authenticated header `<h1>Agent Projects</h1>` with `<h1>Objects</h1>` on line 89 of frontend/src/App.tsx

**Checkpoint**: Browser tab and both page headers display "Objects". User Story 1 is fully functional and testable independently.

---

## Phase 3: User Story 2 — Consistent Title Across All UI Elements (Priority: P1)

**Goal**: Every location where "Agent Projects" previously appeared now consistently reads "Objects" — backend API metadata, log messages, E2E test assertions, configuration files, and documentation.

**Independent Test**: Search the entire codebase for "Agent Projects" (excluding specs/) and verify zero matches remain. Confirm FastAPI OpenAPI docs show "Objects API", log messages reference "Objects API", and all E2E test assertions expect "Objects".

### Backend Implementation

- [ ] T005 [P] [US2] Replace startup log `"Starting Agent Projects API"` with `"Starting Objects API"` on line 75 of backend/src/main.py
- [ ] T006 [P] [US2] Replace shutdown log `"Shutting down Agent Projects API"` with `"Shutting down Objects API"` on line 77 of backend/src/main.py
- [ ] T007 [P] [US2] Replace FastAPI title `"Agent Projects API"` with `"Objects API"` on line 85 of backend/src/main.py
- [ ] T008 [P] [US2] Replace FastAPI description `"REST API for Agent Projects"` with `"REST API for Objects"` on line 86 of backend/src/main.py

### E2E Test Assertion Updates

- [ ] T009 [P] [US2] Update 5 test assertions from "Agent Projects" to "Objects" in frontend/e2e/auth.spec.ts (lines 12, 24, 38, 62, 99)
- [ ] T010 [P] [US2] Update 2 test assertions from "Agent Projects" to "Objects" in frontend/e2e/ui.spec.ts (lines 43, 67)
- [ ] T011 [P] [US2] Update 1 test assertion from "Agent Projects" to "Objects" in frontend/e2e/integration.spec.ts (line 69)

### Configuration Files

- [ ] T012 [P] [US2] Replace dev container name `"Agent Projects"` with `"Objects"` in .devcontainer/devcontainer.json
- [ ] T013 [P] [US2] Replace echo message `"Agent Projects"` with `"Objects"` in .devcontainer/post-create.sh
- [ ] T014 [P] [US2] Replace comment header `"Agent Projects"` with `"Objects"` in .env.example
- [ ] T015 [P] [US2] Replace package name `"agent-projects-frontend"` with `"objects-frontend"` in frontend/package.json

### Documentation

- [ ] T016 [P] [US2] Replace heading `"# Agent Projects"` with `"# Objects"` in README.md
- [ ] T017 [P] [US2] Replace heading and description references from "Agent Projects" to "Objects" in backend/README.md
- [ ] T018 [P] [US2] Replace project description from `"FastAPI backend for Agent Projects"` to `"FastAPI backend for Objects"` in backend/pyproject.toml

### JSDoc and Docstrings

- [ ] T019 [P] [US2] Replace JSDoc comment from `"Agent Projects"` to `"Objects"` in frontend/src/services/api.ts
- [ ] T020 [P] [US2] Replace JSDoc comment from `"Agent Projects"` to `"Objects"` in frontend/src/types/index.ts
- [ ] T021 [P] [US2] Replace module docstring from `"Agent Projects"` to `"Objects"` in backend/tests/test_api_e2e.py

**Checkpoint**: All references to "Agent Projects" replaced with "Objects" across the entire codebase (excluding specs/ directory). User Story 2 is complete.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and validation across all changes

- [ ] T022 Verify zero remaining references to "Agent Projects" outside specs/ by running `grep -rn "Agent Projects" . --include="*.html" --include="*.tsx" --include="*.ts" --include="*.py" --include="*.toml" --include="*.json" --include="*.md" --include="*.sh" --include="*.env*" | grep -v node_modules | grep -v .git/ | grep -v specs/`
- [ ] T023 Run quickstart.md validation checklist from specs/005-update-page-title/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: Depends on Setup — MVP delivery target
- **US2 (Phase 3)**: Depends on Setup — can run in parallel with Phase 2 (different files)
- **Polish (Phase 4)**: Depends on all prior phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — no dependencies on other stories
- **User Story 2 (P1)**: Can start after Setup (Phase 1) — independent of US1 (all different files)

### Within Each Phase

- Phase 2 tasks T003 and T004 modify the same file (App.tsx) — apply sequentially to avoid conflicts
- Phase 3 tasks are all [P] — different files, no dependencies, maximum parallelism

### Parallel Opportunities

- All Phase 3 tasks (T005–T021) touch different files and can ALL run in parallel
- Phase 2 (T002) and Phase 3 (T005–T021) can run in parallel since they modify different files
- T003 and T004 modify the same file (App.tsx) — run sequentially within the file

---

## Parallel Example: Phase 2 + Phase 3

```
# Phase 2 (US1) — frontend user-facing:
T002: Replace title in frontend/index.html
T003: Replace login header in frontend/src/App.tsx
T004: Replace authenticated header in frontend/src/App.tsx (after T003, same file)

# Phase 3 (US2) — all parallel with Phase 2 and each other:
T005: Update startup log in backend/src/main.py
T006: Update shutdown log in backend/src/main.py (after T005, same file)
T007: Update FastAPI title in backend/src/main.py (after T006, same file)
T008: Update FastAPI description in backend/src/main.py (after T007, same file)
T009: Update auth.spec.ts assertions
T010: Update ui.spec.ts assertions
T011: Update integration.spec.ts assertions
T012: Update devcontainer.json
T013: Update post-create.sh
T014: Update .env.example
T015: Update frontend/package.json
T016: Update README.md
T017: Update backend/README.md
T018: Update backend/pyproject.toml
T019: Update frontend/src/services/api.ts
T020: Update frontend/src/types/index.ts
T021: Update backend/tests/test_api_e2e.py
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (verify current state)
2. Complete Phase 2: User Story 1 (browser tab + headers)
3. **STOP and VALIDATE**: Browser tab displays "Objects", login and authenticated headers display "Objects"
4. Deploy/demo if ready — users see the updated title immediately

### Incremental Delivery

1. Setup → Baseline verified
2. Add US1 → Browser tab and headers updated → **MVP!**
3. Add US2 → Backend, tests, config, docs all consistent → Feature complete
4. Polish → Zero old references confirmed → Production-ready

### Parallel Team Strategy

With multiple developers:

1. Complete Setup (Phase 1) together
2. Once Setup is verified:
   - Developer A: User Story 1 (3 file changes)
   - Developer B: User Story 2 (17 file changes — all independent)
3. Both stories complete and validate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- All changes are string literal replacements — no logic, no architecture, no new dependencies
- T005–T008 modify the same file (backend/src/main.py) — apply sequentially within the file but in parallel with other files
- Commit after each phase for clean rollback points
- Stop at any checkpoint to validate the increment independently
- Specs directory (`specs/005-update-page-title/`) references to "Agent Projects" are intentional historical context and should NOT be modified
