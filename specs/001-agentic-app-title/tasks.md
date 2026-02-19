# Tasks: Replace App Title with 'agentic'

**Input**: Design documents from `/specs/001-agentic-app-title/`
**Prerequisites**: spec.md (required)

**Tests**: Not explicitly requested in feature specification. Test tasks are omitted per Test Optionality principle. Existing E2E test assertions are updated as part of the title change (FR-004).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup tasks required — this feature is a text-only replacement with no new dependencies, frameworks, or project structure changes.

*(No tasks in this phase)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational tasks required — no shared infrastructure, schemas, or blocking prerequisites are needed for a text replacement.

*(No tasks in this phase)*

---

## Phase 3: User Story 1 — Consistent App Branding (Priority: P1) 🎯 MVP

**Goal**: Display the exact string 'agentic' (all lowercase) consistently in the browser tab title, login page heading, and main application header.

**Independent Test**: Open the application in a browser → verify the browser tab reads 'agentic' → navigate to login page and verify heading reads 'agentic' → log in and verify the main header reads 'agentic'.

### Implementation for User Story 1

- [ ] T001 [P] [US1] Replace app title text with 'agentic' in the HTML title tag in frontend/index.html
- [ ] T002 [P] [US1] Replace app title text with 'agentic' in the login page h1 heading in frontend/src/App.tsx
- [ ] T003 [US1] Replace app title text with 'agentic' in the main application h1 heading in frontend/src/App.tsx
- [ ] T004 [P] [US1] Update E2E test assertions to expect 'agentic' in page title checks in frontend/e2e/auth.spec.ts
- [ ] T005 [P] [US1] Update E2E test assertions to expect 'agentic' in heading checks in frontend/e2e/ui.spec.ts
- [ ] T006 [P] [US1] Update E2E test assertions to expect 'agentic' in heading checks in frontend/e2e/integration.spec.ts

**Checkpoint**: At this point, User Story 1 should be fully functional — all user-facing surfaces display 'agentic' and E2E tests validate the new branding.

---

## Phase 4: User Story 2 — Updated Developer & Configuration References (Priority: P2)

**Goal**: Update all developer-facing references — development environment names, setup scripts, backend metadata, and documentation — to reflect the 'agentic' branding.

**Independent Test**: Review README files for 'agentic' references → inspect devcontainer configuration for correct name → check backend service metadata (FastAPI title/description) → run setup script and verify messaging references 'agentic'.

### Implementation for User Story 2

- [ ] T007 [P] [US2] Replace app name with 'agentic' in the devcontainer name field in .devcontainer/devcontainer.json
- [ ] T008 [P] [US2] Replace app name with 'agentic' in setup messaging in .devcontainer/post-create.sh
- [ ] T009 [P] [US2] Replace app title with 'agentic' in FastAPI title, description, and logger messages in backend/src/main.py
- [ ] T010 [P] [US2] Replace app name with 'agentic' in the project description in backend/pyproject.toml
- [ ] T011 [P] [US2] Replace app name with 'agentic' in project documentation in README.md
- [ ] T012 [P] [US2] Replace app name with 'agentic' in backend documentation in backend/README.md

**Checkpoint**: At this point, User Story 2 should be complete — all developer-facing references are updated and consistent.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that no stale title references remain anywhere in the codebase.

- [ ] T013 Search entire codebase for any remaining references to the old app title and replace with 'agentic'
- [ ] T014 Verify no styling, layout, or visual changes occurred — confirm text-only replacement per FR-008

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks — skip
- **Foundational (Phase 2)**: No tasks — skip
- **User Story 1 (Phase 3)**: No dependencies — can start immediately
- **User Story 2 (Phase 4)**: No dependencies on Phase 3 — can start in parallel
- **Polish (Phase 5)**: Depends on Phase 3 and Phase 4 completion

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — can start immediately
- **User Story 2 (P2)**: No dependencies on US1 — can start in parallel

### Within Each User Story

- All tasks within US1 that modify different files can run in parallel
- All tasks within US2 that modify different files can run in parallel
- T002 and T003 both modify frontend/src/App.tsx — execute sequentially

### Parallel Opportunities

- US1 and US2 can be worked on entirely in parallel (no shared files between stories)
- Within US1: T001, T004, T005, T006 can all run in parallel (different files)
- Within US1: T002 and T003 are sequential (same file: frontend/src/App.tsx)
- Within US2: All tasks (T007–T012) can run in parallel (all different files)

---

## Parallel Example: User Story 1

```
# These can all run in parallel (different files):
T001: Replace title in frontend/index.html
T004: Update assertions in frontend/e2e/auth.spec.ts
T005: Update assertions in frontend/e2e/ui.spec.ts
T006: Update assertions in frontend/e2e/integration.spec.ts

# These must be sequential (same file: frontend/src/App.tsx):
T002: Replace login page h1 heading
T003: Replace main application h1 heading
```

## Parallel Example: User Story 2

```
# All can run in parallel (every task targets a different file):
T007: Update .devcontainer/devcontainer.json
T008: Update .devcontainer/post-create.sh
T009: Update backend/src/main.py
T010: Update backend/pyproject.toml
T011: Update README.md
T012: Update backend/README.md
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3: User Story 1 (frontend title, headings, E2E tests)
2. **STOP and VALIDATE**: Open app in browser, verify 'agentic' in tab, login heading, and main heading
3. Run E2E tests to confirm all assertions pass
4. Deploy/demo if ready — user-facing branding is correct

### Incremental Delivery

1. Complete US1 → All user-facing surfaces show 'agentic' → **MVP!**
2. Complete US2 → Developer references updated → Full delivery
3. Complete Polish → Final codebase sweep → Production-ready

### Parallel Team Strategy

With multiple developers:

1. Developer A: User Story 1 (all frontend changes)
2. Developer B: User Story 2 (all config/docs changes)
3. Stories complete independently — no merge conflicts expected

---

## Summary

| Metric | Value |
|---|---|
| Total tasks | 14 |
| US1 tasks | 6 |
| US2 tasks | 6 |
| Polish tasks | 2 |
| Parallel opportunities | US1 and US2 fully parallel; within each story most tasks parallel |
| MVP scope | User Story 1 (6 tasks) |

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- This is a text-only replacement — no new files, components, or logic
- Typography and styling remain unchanged per FR-008
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
