# Tasks: Update App Title to "Ready Set Go"

**Input**: Design documents from `/specs/007-app-title-ready-set-go/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/file-changes.md, quickstart.md

**Tests**: Not explicitly requested in feature specification. Existing E2E test assertions are updated as part of the title change (they assert on the old title "Agent Projects"). No new test tasks are generated per Test Optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current state and confirm no new dependencies are needed

- [ ] T001 Verify current title "Agent Projects" appears in all 15 expected files by running `grep -rn "Agent Projects"` excluding `specs/`, `.git/`, and `node_modules/`

> **Note**: This feature requires no new dependencies — it is a pure text replacement across existing files. No project initialization, package installs, or scaffolding needed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking prerequisites exist for this feature

> **Note**: This feature is a cosmetic branding change with no shared infrastructure, database migrations, or framework changes. All user stories can proceed immediately after Phase 1 verification.

**Checkpoint**: No blocking work needed — proceed directly to user story phases.

---

## Phase 3: User Story 1 — Browser Tab Displays Correct Title (Priority: P1) 🎯 MVP

**Goal**: Update the HTML `<title>` tag so the browser tab displays "Ready Set Go" and update the corresponding E2E test assertion.

**Independent Test**: Open the application in a browser and verify the tab title reads "Ready Set Go".

### Implementation

- [ ] T002 [US1] Update `<title>` tag from "Agent Projects" to "Ready Set Go" in frontend/index.html (line 7)
- [ ] T003 [US1] Update `toHaveTitle` regex assertion from `/Agent Projects/i` to `/Ready Set Go/i` in frontend/e2e/auth.spec.ts (line 62)

**Checkpoint**: Browser tab displays "Ready Set Go". E2E title assertion updated to expect new title.

---

## Phase 4: User Story 2 — Application Header Shows Correct Title (Priority: P1)

**Goal**: Update the `<h1>` heading text in both the unauthenticated and authenticated views and update all E2E test assertions that verify header content.

**Independent Test**: Navigate to any page within the application and verify the header displays "Ready Set Go".

### Implementation

- [ ] T004 [US2] Update both `<h1>` headers from "Agent Projects" to "Ready Set Go" in frontend/src/App.tsx (lines 72, 89)
- [ ] T005 [P] [US2] Update 4 `toContainText` assertions from "Agent Projects" to "Ready Set Go" in frontend/e2e/auth.spec.ts (lines 12, 24, 38, 99)
- [ ] T006 [P] [US2] Update 2 `toContainText` assertions from "Agent Projects" to "Ready Set Go" in frontend/e2e/ui.spec.ts (lines 43, 67)
- [ ] T007 [P] [US2] Update 1 `toContainText` assertion from "Agent Projects" to "Ready Set Go" in frontend/e2e/integration.spec.ts (line 69)

**Checkpoint**: Application header displays "Ready Set Go" on all views (login and dashboard). All E2E header assertions updated.

---

## Phase 5: User Story 3 — Backend and Configuration Consistency (Priority: P2)

**Goal**: Update all backend service metadata, configuration files, developer tooling, and documentation to reference "Ready Set Go" consistently.

**Independent Test**: Inspect backend service metadata, configuration files, developer environment names, and documentation to verify they all reference "Ready Set Go".

### Implementation — Backend

- [ ] T008 [P] [US3] Update FastAPI `title`, `description`, and 2 logger messages from "Agent Projects" to "Ready Set Go" in backend/src/main.py (lines 75, 77, 85, 86)
- [ ] T009 [P] [US3] Update project description from "Agent Projects" to "Ready Set Go" in backend/pyproject.toml (line 4)
- [ ] T010 [P] [US3] Update module docstring from "Agent Projects Backend" to "Ready Set Go Backend" in backend/tests/test_api_e2e.py (line 2)
- [ ] T011 [P] [US3] Update heading and description paragraph from "Agent Projects" to "Ready Set Go" in backend/README.md (lines 1, 3)

### Implementation — Configuration & Developer Environment

- [ ] T012 [P] [US3] Update container name from "Agent Projects" to "Ready Set Go" in .devcontainer/devcontainer.json (line 2)
- [ ] T013 [P] [US3] Update setup echo message from "Agent Projects" to "Ready Set Go" in .devcontainer/post-create.sh (line 7)
- [ ] T014 [P] [US3] Update header comment from "Agent Projects" to "Ready Set Go" in .env.example (line 2)

### Implementation — Documentation

- [ ] T015 [P] [US3] Update project heading from "Agent Projects" to "Ready Set Go" in README.md (line 1)

### Implementation — Frontend Docstrings

- [ ] T016 [P] [US3] Update module docstring from "Agent Projects" to "Ready Set Go" in frontend/src/services/api.ts (line 2)
- [ ] T017 [P] [US3] Update module docstring from "Agent Projects" to "Ready Set Go" in frontend/src/types/index.ts (line 2)

**Checkpoint**: All backend metadata, configuration files, developer environment references, and documentation display "Ready Set Go". Zero references to "Agent Projects" remain outside of `specs/`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that all references have been updated and no regressions exist

- [ ] T018 Run completeness verification: `grep -rn "Agent Projects"` excluding `specs/`, `.git/`, and `node_modules/` must return zero results
- [ ] T019 Run quickstart.md verification checklist from specs/007-app-title-ready-set-go/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: N/A — no blocking prerequisites for this feature
- **US1 (Phase 3)**: Can start after Phase 1 verification — no dependencies on other stories
- **US2 (Phase 4)**: Can start after Phase 1 verification — no dependencies on other stories
- **US3 (Phase 5)**: Can start after Phase 1 verification — no dependencies on other stories
- **Polish (Phase 6)**: Depends on all prior phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent — affects only `frontend/index.html` and one E2E assertion
- **User Story 2 (P1)**: Independent — affects only `frontend/src/App.tsx` and E2E header assertions
- **User Story 3 (P2)**: Independent — affects backend, config, docs, and frontend docstrings
- All three user stories modify different files with zero overlap and can be executed in any order or in parallel

### Within Each User Story

- Source file changes before corresponding E2E test assertion updates (logical order)
- All tasks within US3 are marked [P] — they modify different files with no dependencies

### Parallel Opportunities

- **All three user stories** (Phases 3, 4, 5) can run in parallel — they modify entirely different files
- **Within Phase 4**: T005, T006, T007 (E2E test files) can run in parallel with each other
- **Within Phase 5**: All tasks T008–T017 can run in parallel — each modifies a different file
- **Maximum parallelism**: Up to 10 tasks running simultaneously in Phase 5

---

## Parallel Example: Phase 5 (US3 — Backend & Config)

```
# All these tasks modify different files and can run simultaneously:
T008: Update FastAPI config in backend/src/main.py
T009: Update metadata in backend/pyproject.toml
T010: Update docstring in backend/tests/test_api_e2e.py
T011: Update docs in backend/README.md
T012: Update container name in .devcontainer/devcontainer.json
T013: Update echo in .devcontainer/post-create.sh
T014: Update comment in .env.example
T015: Update heading in README.md
T016: Update docstring in frontend/src/services/api.ts
T017: Update docstring in frontend/src/types/index.ts
```

---

## Implementation Strategy

### MVP First (Phase 1 + 3)

1. Complete Phase 1: Verify current state
2. Complete Phase 3: US1 — Browser tab shows "Ready Set Go"
3. **STOP and VALIDATE**: Open app in browser, verify tab title
4. Deploy/demo if ready — users see new title immediately

### Incremental Delivery

1. Phase 1 (Setup verification) → Confirm scope
2. Phase 3 (US1 — Browser Tab) → Tab title updated → **MVP!**
3. Phase 4 (US2 — App Header) → Header branding consistent
4. Phase 5 (US3 — Backend & Config) → Full consistency across codebase
5. Phase 6 (Polish) → Verified zero remaining old title references
6. Each phase adds consistency without breaking previous changes

### Parallel Team Strategy

With multiple developers:

1. Developer A: US1 (Phase 3) — browser tab + title E2E assertion
2. Developer B: US2 (Phase 4) — app headers + header E2E assertions
3. Developer C: US3 (Phase 5) — all backend, config, docs, and docstrings
4. All three can work simultaneously from the start — zero file conflicts

---

## Summary

- **Total tasks**: 19
- **User Story 1 (Browser Tab)**: 2 tasks (T002–T003)
- **User Story 2 (App Header)**: 4 tasks (T004–T007)
- **User Story 3 (Backend & Config)**: 10 tasks (T008–T017)
- **Setup + Polish**: 3 tasks (T001, T018–T019)
- **Parallel opportunities**: All 3 user stories can run in parallel; 10 tasks in US3 can run simultaneously
- **Suggested MVP scope**: User Story 1 only (2 tasks — browser tab title update)
- **Format validation**: ✅ All tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- This is a pure text-replacement feature — no logic changes, no new files, no new dependencies
- Exact casing "Ready Set Go" must be used in every replacement per FR-008
- After all replacements, `grep -rn "Agent Projects"` (excluding `specs/` and `.git/`) must return zero results
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
