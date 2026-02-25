# Tasks: Update Title Text to "Tim is Awesome"

**Input**: Design documents from `/specs/011-update-title-text/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new tests requested. Existing test files referencing the old title must be updated per FR-005.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Configuration: `.devcontainer/`, `backend/pyproject.toml`
- Tests: `frontend/e2e/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify target files exist and no structural changes are needed

- [ ] T001 Verify all target files exist and contain "Agent Projects" string before modification

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking prerequisites are required for this feature

*This phase is intentionally empty. The title text change is a direct string replacement with no infrastructure dependencies. Proceed directly to user story implementation.*

**Checkpoint**: No foundational work needed — user story implementation can begin immediately after Setup

---

## Phase 3: User Story 1 - Title Displays Updated Text (Priority: P1) 🎯 MVP

**Goal**: Replace all instances of "Agent Projects" with "Tim is Awesome" across frontend, backend, and configuration files so the updated title is displayed consistently everywhere

**Independent Test**: Open the application in a browser — the browser tab should display "Tim is Awesome", login page heading should read "Tim is Awesome", main app header should read "Tim is Awesome", settings page should reference "Tim is Awesome", and API docs at `/docs` should show "Tim is Awesome API"

### Implementation for User Story 1

- [ ] T002 [P] [US1] Update browser tab title from "Agent Projects" to "Tim is Awesome" in frontend/index.html
- [ ] T003 [P] [US1] Update both `<h1>` headings from "Agent Projects" to "Tim is Awesome" in frontend/src/App.tsx
- [ ] T004 [P] [US1] Update settings description text from "Agent Projects" to "Tim is Awesome" in frontend/src/pages/SettingsPage.tsx
- [ ] T005 [P] [US1] Update FastAPI title from "Agent Projects API" to "Tim is Awesome API" in backend/src/main.py
- [ ] T006 [P] [US1] Update FastAPI description from "REST API for Agent Projects" to "REST API for Tim is Awesome" in backend/src/main.py
- [ ] T007 [P] [US1] Update startup log message from "Starting Agent Projects API" to "Starting Tim is Awesome API" in backend/src/main.py
- [ ] T008 [P] [US1] Update shutdown log message from "Shutting down Agent Projects API" to "Shutting down Tim is Awesome API" in backend/src/main.py
- [ ] T009 [P] [US1] Update package description from "FastAPI backend for Agent Projects" to "FastAPI backend for Tim is Awesome" in backend/pyproject.toml
- [ ] T010 [P] [US1] Update dev container name from "Agent Projects" to "Tim is Awesome" in .devcontainer/devcontainer.json

**Checkpoint**: At this point, User Story 1 should be fully functional — all user-facing and developer-facing title references display "Tim is Awesome"

---

## Phase 4: User Story 2 - No Unintended Side Effects (Priority: P1)

**Goal**: Update all existing test assertions that reference "Agent Projects" to reference "Tim is Awesome" so the test suite passes without regressions

**Independent Test**: Run `cd frontend && npx playwright test` — all E2E tests should pass with zero failures. No non-title text or UI elements should be affected.

### Implementation for User Story 2

- [ ] T011 [P] [US2] Update title assertions from "Agent Projects" to "Tim is Awesome" in frontend/e2e/auth.spec.ts
- [ ] T012 [P] [US2] Update title assertions from "Agent Projects" to "Tim is Awesome" in frontend/e2e/ui.spec.ts
- [ ] T013 [P] [US2] Update title assertions from "Agent Projects" to "Tim is Awesome" in frontend/e2e/integration.spec.ts

**Checkpoint**: All existing tests pass with updated title references — zero regressions confirmed

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all modified files

- [ ] T014 Run full-text search for any remaining "Agent Projects" references in the repository
- [ ] T015 Run quickstart.md validation to confirm all verification steps pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Skipped — no blocking prerequisites for this feature
- **User Story 1 (Phase 3)**: Depends on Setup (Phase 1) verification only
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (test assertions must match source changes)
- **Polish (Phase 5)**: Depends on both User Stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start immediately after Setup — no dependencies on other stories
- **User Story 2 (P1)**: Depends on User Story 1 — test assertions must reference the new title that was set in US1

### Within Each User Story

- All tasks within US1 are marked [P] and can run in parallel (different files, no cross-file dependencies)
- All tasks within US2 are marked [P] and can run in parallel (different test files)
- US2 must wait for US1 to complete (test assertions must match updated source files)

### Parallel Opportunities

- T002–T010 (all US1 implementation tasks) can run in parallel — each modifies a different file
- T011–T013 (all US2 test update tasks) can run in parallel — each modifies a different test file

---

## Parallel Example: User Story 1

```bash
# Launch all source file updates for User Story 1 together:
Task: "Update browser tab title in frontend/index.html"
Task: "Update h1 headings in frontend/src/App.tsx"
Task: "Update settings description in frontend/src/pages/SettingsPage.tsx"
Task: "Update FastAPI metadata and logs in backend/src/main.py"
Task: "Update package description in backend/pyproject.toml"
Task: "Update dev container name in .devcontainer/devcontainer.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify files exist)
2. Phase 2: Skipped (no foundational work)
3. Complete Phase 3: User Story 1 (all source file changes)
4. **STOP and VALIDATE**: Open the app — verify "Tim is Awesome" appears in browser tab, login heading, app header, settings page, and API docs
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup → Verified
2. Add User Story 1 → All title references updated → Visually verify (MVP!)
3. Add User Story 2 → All test assertions updated → Run test suite to confirm zero regressions
4. Polish → Full-text search for any missed references → Final validation

---

## Summary

- **Total tasks**: 15
- **User Story 1 tasks**: 9 (T002–T010) — source file modifications
- **User Story 2 tasks**: 3 (T011–T013) — test file updates
- **Setup tasks**: 1 (T001)
- **Polish tasks**: 2 (T014–T015)
- **Parallel opportunities**: All 9 US1 tasks can run in parallel; all 3 US2 tasks can run in parallel
- **Independent test criteria**: US1 — visually verify title in browser; US2 — run E2E test suite
- **Suggested MVP scope**: User Story 1 only (all source file changes)
- **Format validation**: ✅ All tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
