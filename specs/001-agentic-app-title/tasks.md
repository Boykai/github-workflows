# Tasks: Replace App Title with 'agentic'

**Input**: Design documents from `/specs/001-agentic-app-title/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Existing E2E test assertions must be updated to reflect the new title string.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 — Consistent App Branding (Priority: P1) 🎯 MVP

**Goal**: Replace all user-facing instances of the app title with 'agentic' so the browser tab, login page header, and authenticated header display the correct branding.

**Independent Test**: Open the application in a browser — verify the browser tab reads 'agentic', the login page heading displays 'agentic', and the authenticated page heading displays 'agentic'.

### Implementation for User Story 1

- [ ] T001 [P] [US1] Replace page title text from 'Agent Projects' to 'agentic' in frontend/index.html (line 7, `<title>` element)
- [ ] T002 [P] [US1] Replace login page header text from 'Agent Projects' to 'agentic' in frontend/src/App.tsx (line 72, `<h1>` element)
- [ ] T003 [P] [US1] Replace authenticated header text from 'Agent Projects' to 'agentic' in frontend/src/App.tsx (line 89, `<h1>` element)
- [ ] T004 [P] [US1] Update heading assertions from 'Agent Projects' to 'agentic' in frontend/e2e/auth.spec.ts (lines 12, 24, 38, 99)
- [ ] T005 [P] [US1] Update title regex assertion from /Agent Projects/i to /agentic/i in frontend/e2e/auth.spec.ts (line 62)
- [ ] T006 [P] [US1] Update heading assertions from 'Agent Projects' to 'agentic' in frontend/e2e/ui.spec.ts (lines 43, 67)
- [ ] T007 [P] [US1] Update heading assertion from 'Agent Projects' to 'agentic' in frontend/e2e/integration.spec.ts (line 69)

**Checkpoint**: Browser tab, login header, and authenticated header all display 'agentic'. All E2E test assertions match the new title.

---

## Phase 2: User Story 2 — Updated Developer & Configuration References (Priority: P2)

**Goal**: Update all developer-facing references — backend metadata, devcontainer config, setup scripts, pyproject.toml, and README files — to reflect the 'agentic' branding.

**Independent Test**: Review backend FastAPI Swagger UI title, devcontainer setup output, pyproject.toml metadata, and README headers for correct 'agentic' references.

### Implementation for User Story 2

- [ ] T008 [P] [US2] Replace startup log message from 'Starting Agent Projects API' to 'Starting agentic API' in backend/src/main.py (line 75)
- [ ] T009 [P] [US2] Replace shutdown log message from 'Shutting down Agent Projects API' to 'Shutting down agentic API' in backend/src/main.py (line 77)
- [ ] T010 [P] [US2] Replace FastAPI title from 'Agent Projects API' to 'agentic API' in backend/src/main.py (line 85)
- [ ] T011 [P] [US2] Replace FastAPI description from 'REST API for Agent Projects' to 'REST API for agentic' in backend/src/main.py (line 86)
- [ ] T012 [P] [US2] Replace devcontainer name from 'Agent Projects' to 'agentic' in .devcontainer/devcontainer.json (line 2)
- [ ] T013 [P] [US2] Replace setup message from 'Setting up Agent Projects development environment...' to 'Setting up agentic development environment...' in .devcontainer/post-create.sh (line 7)
- [ ] T014 [P] [US2] Replace project name from 'agent-projects-backend' to 'agentic-backend' in backend/pyproject.toml (line 2)
- [ ] T015 [P] [US2] Replace project description from 'FastAPI backend for Agent Projects' to 'FastAPI backend for agentic' in backend/pyproject.toml (line 4)
- [ ] T016 [P] [US2] Replace root README header from '# Agent Projects' to '# agentic' in README.md (line 1)
- [ ] T017 [P] [US2] Replace backend README header from '# Agent Projects — Backend' to '# agentic — Backend' in backend/README.md (line 1)

**Checkpoint**: Backend metadata, devcontainer config, pyproject.toml, and all READMEs reference 'agentic'. No lingering 'Agent Projects' references in developer-facing files.

---

## Phase 3: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that no old title references remain

- [ ] T018 Run `grep -rn "Agent Projects" frontend/ backend/ .devcontainer/ README.md` to verify zero remaining references to the old title in source files
- [ ] T019 Run quickstart.md validation checklist to confirm all FR and SC items pass

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: User Story 1 (T001-T007, all parallel — different files or independent lines)
    ↓ (no hard dependency, but logical order)
Phase 2: User Story 2 (T008-T017, all parallel — different files or independent lines)
    ↓
Phase 3: Polish (T018-T019, sequential — verification after all changes)
```

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — can start immediately. All tasks modify different files or independent lines within the same file.
- **User Story 2 (P2)**: No dependency on US1 — can start in parallel. All tasks modify different files or independent lines.
- **Polish**: Depends on both US1 and US2 completion.

### Parallel Opportunities

- **Within US1**: T001, T002/T003 (same file but different lines), T004/T005 (same file but different lines), T006, T007 — all can run in parallel
- **Within US2**: All T008-T017 can run in parallel (different files or independent lines within same file)
- **Across stories**: US1 and US2 can be implemented in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# All US1 tasks can run in parallel (different files):
Task: T001 — Replace title in frontend/index.html
Task: T002 — Replace login header in frontend/src/App.tsx
Task: T003 — Replace auth header in frontend/src/App.tsx
Task: T004 — Update auth E2E heading assertions in frontend/e2e/auth.spec.ts
Task: T005 — Update auth E2E title assertion in frontend/e2e/auth.spec.ts
Task: T006 — Update UI E2E assertions in frontend/e2e/ui.spec.ts
Task: T007 — Update integration E2E assertion in frontend/e2e/integration.spec.ts
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: User Story 1 (T001-T007)
2. **STOP and VALIDATE**: Open app in browser, verify title in tab, login header, and authenticated header
3. Deploy/demo if ready — user-facing branding is complete

### Incremental Delivery

1. Complete User Story 1 → Test independently → Deploy (MVP!)
2. Complete User Story 2 → Test independently → Deploy (full branding alignment)
3. Run Polish phase to confirm zero old references remain

### Parallel Team Strategy

With multiple developers:

1. Developer A: User Story 1 (T001-T007)
2. Developer B: User Story 2 (T008-T017)
3. Both complete in parallel, then run Polish phase together

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| US1 — App Branding | T001-T007 | index.html, App.tsx, auth.spec.ts, ui.spec.ts, integration.spec.ts |
| US2 — Dev & Config | T008-T017 | main.py, devcontainer.json, post-create.sh, pyproject.toml, README.md, backend/README.md |
| Polish | T018-T019 | (verification only) |

**Total Tasks**: 19
**Tasks per User Story**: US1 = 7, US2 = 10, Polish = 2
**Parallel Opportunities**: All tasks within each user story can run in parallel; both user stories can run in parallel
**Independent Test Criteria**: US1 — visual browser inspection; US2 — file/config review
**Suggested MVP Scope**: User Story 1 (T001-T007) — delivers immediate visible branding
**Format Validation**: ✅ All tasks follow checklist format (checkbox, ID, labels, file paths)
