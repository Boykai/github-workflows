# Tasks: Update App Title to "Hello World"

**Input**: Design documents from `/specs/005-hello-world-title/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new tests are required. Existing E2E test assertions will be updated to match the new title as part of User Story 3 (branding consistency).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Root configuration files: `.devcontainer/`, `.env.example`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current state and confirm all title reference locations before making changes

- [x] T001 Verify current title references by running `grep -r "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" --include="*.json" --include="*.py" --include="*.toml" --include="*.md" --include="*.example" .` from repository root
- [x] T002 Confirm frontend dev server runs successfully with `npm run dev` in frontend/

**Checkpoint**: Current state verified — ready to begin title replacement

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational blocking prerequisites exist for this feature

All changes are independent text replacements within existing files. No new infrastructure, schemas, or shared components are required. User story implementation can begin immediately after Phase 1 verification.

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Browser Tab Title Display (Priority: P1) 🎯 MVP

**Goal**: Update the HTML `<title>` tag so the browser tab displays "Hello World" when the application is loaded

**Independent Test**: Open the application in a browser and verify the browser tab displays "Hello World" as the page title

### Implementation for User Story 1

- [x] T003 [US1] Update `<title>` tag from "Agent Projects" to "Hello World" in frontend/index.html

**Checkpoint**: At this point, the browser tab should display "Hello World" — User Story 1 is complete and independently testable

---

## Phase 4: User Story 2 — Application Header Display (Priority: P2)

**Goal**: Update the React `<h1>` header elements so the in-app header displays "Hello World" on the login page and main application view

**Independent Test**: Navigate through the application and verify that "Hello World" appears consistently in the header on the login page and after login

### Implementation for User Story 2

- [x] T004 [P] [US2] Update first `<h1>Agent Projects</h1>` to `<h1>Hello World</h1>` (login page header) in frontend/src/App.tsx
- [x] T005 [P] [US2] Update second `<h1>Agent Projects</h1>` to `<h1>Hello World</h1>` (app header) in frontend/src/App.tsx

**Checkpoint**: At this point, both the browser tab and in-app headers should display "Hello World" — User Stories 1 AND 2 are complete

---

## Phase 5: User Story 3 — Complete Branding Consistency (Priority: P3)

**Goal**: Remove or replace all remaining references to "Agent Projects" across backend metadata, test assertions, configuration files, and documentation so no stale title references exist

**Independent Test**: Run a global search for "Agent Projects" and verify zero matches outside of the `specs/` directory (which documents the old title for historical context)

### Implementation for User Story 3

**Backend metadata:**

- [x] T006 [P] [US3] Update FastAPI app `title` from "Agent Projects API" to "Hello World API" in backend/src/main.py
- [x] T007 [P] [US3] Update FastAPI app `description` from "REST API for Agent Projects" to "REST API for Hello World" in backend/src/main.py
- [x] T008 [P] [US3] Update startup log message from "Starting Agent Projects API" to "Starting Hello World API" in backend/src/main.py
- [x] T009 [P] [US3] Update shutdown log message from "Shutting down Agent Projects API" to "Shutting down Hello World API" in backend/src/main.py
- [x] T010 [P] [US3] Update package description from "FastAPI backend for Agent Projects" to "FastAPI backend for Hello World" in backend/pyproject.toml
- [x] T011 [P] [US3] Update headings and descriptions from "Agent Projects" to "Hello World" in backend/README.md

**E2E test assertions:**

- [x] T012 [P] [US3] Update all "Agent Projects" assertions to "Hello World" in frontend/e2e/auth.spec.ts
- [x] T013 [P] [US3] Update all "Agent Projects" assertions to "Hello World" in frontend/e2e/ui.spec.ts
- [x] T014 [P] [US3] Update "Agent Projects" assertion to "Hello World" in frontend/e2e/integration.spec.ts

**Configuration and documentation:**

- [x] T015 [P] [US3] Update container name from "Agent Projects" to "Hello World" in .devcontainer/devcontainer.json
- [x] T016 [P] [US3] Update header comment from "Agent Projects" to "Hello World" in .env.example
- [x] T017 [P] [US3] Update JSDoc comment from "Agent Projects" to "Hello World" in frontend/src/types/index.ts
- [x] T018 [P] [US3] Update JSDoc comment from "Agent Projects" to "Hello World" in frontend/src/services/api.ts

**Checkpoint**: All user stories should now be independently functional — zero references to "Agent Projects" remain outside `specs/`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that all changes are consistent and complete

- [x] T019 Run global search `grep -r "Agent Projects"` to verify no references remain outside specs/ directory
- [x] T020 Run quickstart.md validation steps to confirm end-to-end correctness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: No work required — passes through immediately
- **User Story 1 (Phase 3)**: Can start after Phase 1 verification
- **User Story 2 (Phase 4)**: Can start after Phase 1 — independent of US1
- **User Story 3 (Phase 5)**: Can start after Phase 1 — independent of US1 and US2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — single file change (`frontend/index.html`)
- **User Story 2 (P2)**: No dependencies on other stories — single file change (`frontend/src/App.tsx`)
- **User Story 3 (P3)**: No dependencies on other stories — affects 9 independent files across backend, tests, and config

### Within Each User Story

- All tasks within US3 are marked [P] because they modify different files with no interdependencies
- US1 and US2 tasks can also run in parallel with each other (different files)

### Parallel Opportunities

- T003, T004, T005 can all run in parallel (different files, no dependencies)
- All US3 tasks (T006–T018) can run in parallel (each modifies a different file)
- In practice, all 16 implementation tasks (T003–T018) could run simultaneously since every task modifies a different file or a different location in the same file

---

## Parallel Example: User Story 3

```bash
# All US3 tasks can launch in parallel (each modifies a separate file):
Task: "T006 Update FastAPI app title in backend/src/main.py"
Task: "T010 Update package description in backend/pyproject.toml"
Task: "T011 Update headings in backend/README.md"
Task: "T012 Update assertions in frontend/e2e/auth.spec.ts"
Task: "T013 Update assertions in frontend/e2e/ui.spec.ts"
Task: "T014 Update assertion in frontend/e2e/integration.spec.ts"
Task: "T015 Update container name in .devcontainer/devcontainer.json"
Task: "T016 Update header comment in .env.example"
Task: "T017 Update JSDoc in frontend/src/types/index.ts"
Task: "T018 Update JSDoc in frontend/src/services/api.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify current state
2. Complete Phase 3: User Story 1 (single file: `frontend/index.html`)
3. **STOP and VALIDATE**: Browser tab displays "Hello World"
4. Deploy/demo if ready — MVP delivered

### Incremental Delivery

1. Verify current state → Phase 1 complete
2. Update browser tab title (US1) → Test independently → MVP!
3. Update app headers (US2) → Test independently → Enhanced branding
4. Update all remaining references (US3) → Verify zero old references → Full consistency
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Phase 1: Single developer verifies current state
2. Once verified:
   - Developer A: User Story 1 (frontend/index.html)
   - Developer B: User Story 2 (frontend/src/App.tsx)
   - Developer C: User Story 3 (all remaining files — can further split among sub-tasks)
3. All stories complete independently and can be merged in any order

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 20 |
| **Setup tasks** | 2 (T001–T002) |
| **User Story 1 tasks** | 1 (T003) |
| **User Story 2 tasks** | 2 (T004–T005) |
| **User Story 3 tasks** | 13 (T006–T018) |
| **Polish tasks** | 2 (T019–T020) |
| **Parallelizable tasks** | 15 of 16 implementation tasks (all [P] marked) |
| **Files modified** | ~14 files |
| **Suggested MVP scope** | User Story 1 only (Phase 3 — single file change) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new tests required — existing E2E tests updated for new assertions
- Tests are NOT explicitly requested in the feature specification
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The `specs/` directory will still contain references to "Agent Projects" for historical context — this is expected and correct
