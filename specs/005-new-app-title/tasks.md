# Tasks: Update App Title to "New App"

**Input**: Design documents from `/specs/005-new-app-title/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/file-changes.md, quickstart.md

**Tests**: Not explicitly requested in feature specification. Existing E2E test assertions must be updated to match new title (not new tests, but maintenance of existing ones). No new test tasks generated per Test Optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline state before making changes

- [x] T001 Verify current title occurrences by running `grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.json" --include="*.html" --include="*.md" --include="*.sh" --include="*.toml" | grep -v ".git/" | grep -v "node_modules/" | grep -v "specs/"` from repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational blocking tasks required — all changes are independent string literal replacements across isolated files with no shared infrastructure, data model, or API contract changes.

**Checkpoint**: No blocking prerequisites — user story implementation can begin immediately after setup verification.

---

## Phase 3: User Story 1 — Browser Tab Title Display (Priority: P1) 🎯 MVP

**Goal**: Update the HTML `<title>` tag so the browser tab displays "New App" instead of "Agent Projects"

**Independent Test**: Open the application in a browser and verify the browser tab displays "New App" as the page title.

### Implementation

- [x] T002 [US1] Replace `<title>Agent Projects</title>` with `<title>New App</title>` on line 7 of frontend/index.html
- [x] T003 [P] [US1] Replace `toHaveTitle(/Agent Projects/i)` with `toHaveTitle(/New App/i)` on line 62 of frontend/e2e/auth.spec.ts

**Checkpoint**: Browser tab displays "New App". Title assertion in auth E2E test updated.

---

## Phase 4: User Story 2 — Application Header Display (Priority: P2)

**Goal**: Update all `<h1>` header elements so the login page and authenticated application header display "New App"

**Independent Test**: Load the application (unauthenticated) — login page header displays "New App". Authenticate (login) — main application header displays "New App".

### Implementation

- [x] T004 [US2] Replace `<h1>Agent Projects</h1>` with `<h1>New App</h1>` on line 72 (login header) and line 89 (authenticated header) of frontend/src/App.tsx
- [x] T005 [P] [US2] Replace all `toContainText('Agent Projects')` heading assertions with `toContainText('New App')` on lines 12, 24, 38, 99 of frontend/e2e/auth.spec.ts
- [x] T006 [P] [US2] Replace `toContainText('Agent Projects')` heading assertions with `toContainText('New App')` on lines 43, 67 of frontend/e2e/ui.spec.ts
- [x] T007 [P] [US2] Replace `toContainText('Agent Projects')` heading assertion with `toContainText('New App')` on line 69 of frontend/e2e/integration.spec.ts

**Checkpoint**: Login page and authenticated headers display "New App". All heading-related E2E test assertions updated.

---

## Phase 5: User Story 3 — Complete Branding Consistency (Priority: P3)

**Goal**: Remove all remaining references to "Agent Projects" from backend metadata, configuration files, documentation, and code comments to ensure complete rebranding

**Independent Test**: Run `grep -rn "Agent Projects" --exclude-dir=specs --exclude-dir=node_modules --exclude-dir=.git` from repository root and verify zero matches remain (excluding internal package names).

### Implementation — Backend

- [x] T008 [P] [US3] Replace `"Starting Agent Projects API"` with `"Starting New App API"` on line 75 and `"Shutting down Agent Projects API"` with `"Shutting down New App API"` on line 77 of backend/src/main.py
- [x] T009 [US3] Replace `title="Agent Projects API"` with `title="New App API"` on line 85 and `description="REST API for Agent Projects"` with `description="REST API for New App"` on line 86 of backend/src/main.py (same file as T008, run sequentially)
- [x] T010 [P] [US3] Replace `description = "FastAPI backend for Agent Projects"` with `description = "FastAPI backend for New App"` on line 4 of backend/pyproject.toml
- [x] T011 [P] [US3] Replace `# Agent Projects — Backend` with `# New App — Backend` and `Agent Projects` with `New App` in body text of backend/README.md
- [x] T012 [P] [US3] Replace `Agent Projects Backend` with `New App Backend` in the file header comment on line 2 of backend/tests/test_api_e2e.py

### Implementation — Configuration

- [x] T013 [P] [US3] Replace `"name": "Agent Projects"` with `"name": "New App"` on line 2 of .devcontainer/devcontainer.json
- [x] T014 [P] [US3] Replace `Setting up Agent Projects development environment` with `Setting up New App development environment` on line 7 of .devcontainer/post-create.sh

### Implementation — Documentation & Comments

- [x] T015 [P] [US3] Replace `# Agent Projects` with `# New App` on line 1 of README.md
- [x] T016 [P] [US3] Replace `Agent Projects API` with `New App API` in the file header comment on line 2 of frontend/src/types/index.ts
- [x] T017 [P] [US3] Replace `Agent Projects` with `New App` in the file header comment on line 2 of frontend/src/services/api.ts

**Checkpoint**: All references to "Agent Projects" removed from backend, configuration, documentation, and comments. Codebase search returns zero matches (excluding internal package identifiers).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and validation across all user stories

- [x] T018 Run post-change verification search: `grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.json" --include="*.html" --include="*.md" --include="*.sh" --include="*.toml" | grep -v ".git/" | grep -v "node_modules/" | grep -v "specs/"` — confirm zero unexpected matches remain (same command as T001, now expecting 0 results instead of ~20)
- [x] T019 Run quickstart.md validation checklist from specs/005-new-app-title/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Skipped — no blocking prerequisites for string replacements
- **US1 (Phase 3)**: No dependencies — can start immediately after setup
- **US2 (Phase 4)**: No dependencies on US1 — can start in parallel
- **US3 (Phase 5)**: No dependencies on US1 or US2 — can start in parallel
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent — modifies only frontend/index.html and one E2E assertion
- **User Story 2 (P2)**: Independent — modifies only frontend/src/App.tsx and heading E2E assertions
- **User Story 3 (P3)**: Independent — modifies backend, config, docs, and comment files only
- All three user stories touch different files and can be implemented in parallel

### Within Each User Story

- Source file changes before (or in parallel with) E2E test assertion updates
- All tasks within a story marked [P] can run in parallel (different files)

### Parallel Opportunities

- **All user stories can run in parallel** — each touches completely different files
- Within Phase 5 (US3): All tasks T008–T017 are parallel (different files, no dependencies)
- Within Phase 4 (US2): T005, T006, T007 are parallel (different E2E test files)
- T003 (US1) can run in parallel with T002 (US1) — different files

---

## Parallel Example: All User Stories

```
# All three user stories can execute simultaneously:

# US1 (Phase 3):
T002: Replace title in frontend/index.html
T003: Update title assertion in frontend/e2e/auth.spec.ts

# US2 (Phase 4):
T004: Replace headers in frontend/src/App.tsx
T005: Update heading assertions in frontend/e2e/auth.spec.ts
T006: Update heading assertions in frontend/e2e/ui.spec.ts
T007: Update heading assertion in frontend/e2e/integration.spec.ts

# US3 (Phase 5) — all parallel:
T008-T009: Backend main.py updates
T010: Backend pyproject.toml update
T011: Backend README.md update
T012: Backend test comment update
T013-T014: Devcontainer config updates
T015: Root README.md update
T016-T017: Frontend file comment updates
```

## Parallel Example: Phase 5 (US3)

```
# All tasks in Phase 5 can run simultaneously (different files):
T008: backend/src/main.py (log messages)
T009: backend/src/main.py (FastAPI metadata) — same file as T008, run sequentially after T008
T010: backend/pyproject.toml
T011: backend/README.md
T012: backend/tests/test_api_e2e.py
T013: .devcontainer/devcontainer.json
T014: .devcontainer/post-create.sh
T015: README.md
T016: frontend/src/types/index.ts
T017: frontend/src/services/api.ts
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline
2. Complete Phase 3: User Story 1 (browser tab title)
3. **STOP and VALIDATE**: Open browser → tab shows "New App"
4. Deploy/demo if ready — minimal viable branding update

### Incremental Delivery

1. Verify baseline → Confirm all "Agent Projects" occurrences found
2. Add User Story 1 → Browser tab shows "New App" → **MVP!**
3. Add User Story 2 → Application headers show "New App" → Complete user-facing update
4. Add User Story 3 → All backend, config, docs, and comments updated → Full branding consistency
5. Polish → Final verification search confirms zero old references remain
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. All developers start simultaneously after baseline verification
   - Developer A: User Story 1 (frontend/index.html + title E2E assertion)
   - Developer B: User Story 2 (frontend/src/App.tsx + heading E2E assertions)
   - Developer C: User Story 3 (backend + config + docs + comments)
2. Stories complete and integrate independently — no merge conflicts expected (different files)

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 19 |
| US1 tasks | 2 (T002–T003) |
| US2 tasks | 4 (T004–T007) |
| US3 tasks | 10 (T008–T017) |
| Setup tasks | 1 (T001) |
| Polish tasks | 2 (T018–T019) |
| Parallel opportunities | All user stories parallel; all US3 tasks parallel (except T008+T009 same file) |
| Files modified | 14 |
| Suggested MVP | User Story 1 only (1 file: frontend/index.html + 1 E2E assertion update) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- No new dependencies, no new tests, no architectural changes — purely string replacements
- Internal package names (`agent-projects-frontend`, `agent-projects-backend`) are intentionally NOT changed per research.md decision
- Commit after each phase or logical group
- Stop at any checkpoint to validate the increment independently
