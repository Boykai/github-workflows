# Tasks: Perform Repository-Wide Codebase Cleanup to Reduce Technical Debt

**Input**: Design documents from `/specs/016-codebase-cleanup-debt/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Tests are NOT explicitly requested — this is a cleanup/refactoring task. All existing CI checks (ruff, pyright, pytest, eslint, tsc, vitest, vite build) must remain green after each change.

**Organization**: Tasks are grouped by user story (cleanup category) to enable independent implementation and validation of each category.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/`
- **Frontend tests**: co-located `*.test.ts` / `*.test.tsx` files
- **Infrastructure**: `docker-compose.yml`, `pyproject.toml`, `frontend/package.json`

---

## Phase 1: Setup (Analysis & Baseline)

**Purpose**: Establish a clean baseline, verify all CI checks pass before any cleanup begins, and document current codebase metrics for comparison

- [ ] T001 Run full backend CI checks (ruff check, ruff format --check, pyright, pytest) to establish passing baseline from backend/
- [ ] T002 Run full frontend CI checks (eslint, tsc --noEmit, vitest run, vite build) to establish passing baseline from frontend/
- [ ] T003 Audit dynamic code loading patterns — trace string-based plugin loading in backend/src/services/github_projects/service.py and migration discovery in backend/src/services/database.py to build a safe-to-ignore list of dynamically loaded modules

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Static analysis and tooling-assisted dead code detection that MUST complete before manual cleanup begins

**⚠️ CRITICAL**: No user story cleanup work should begin until the analysis in this phase is complete

- [ ] T004 Run ruff with unused-import and unused-variable rules across all Python files in backend/src/ to generate a list of unused imports and variables
- [ ] T005 [P] Run eslint with no-unused-vars and no-unused-imports rules across all TypeScript files in frontend/src/ to generate a list of unused imports and variables
- [ ] T006 [P] Scan for commented-out code blocks (excluding documentation comments and license headers) across backend/src/ and frontend/src/
- [ ] T007 [P] Search for backwards-compatibility patterns (if old_format, if legacy, compat, polyfill, shim, deprecated, adapter, alias) across backend/src/ and frontend/src/
- [ ] T008 [P] Search for stale TODO/FIXME/HACK comments across backend/src/, frontend/src/, and scripts/ and cross-reference with completed issues/PRs
- [ ] T009 [P] Identify duplicate or near-duplicate functions by comparing function signatures and bodies across backend/src/services/ and frontend/src/services/

**Checkpoint**: Full analysis complete — cleanup categories are documented with specific files and line numbers for each change

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all functions, methods, components, imports, variables, type definitions, and models that are defined but never imported or called, excluding dynamically loaded code. Remove commented-out logic blocks.

**Independent Test**: Run the full CI check suite (ruff, pyright, pytest, eslint, tsc, vitest, vite build) after each removal batch. All checks must pass.

### Implementation for User Story 1

#### Backend Dead Code Removal

- [ ] T010 [P] [US1] Remove unused imports and variables identified by ruff in backend/src/api/*.py (auth.py, board.py, chat.py, cleanup.py, health.py, housekeeping.py, mcp.py, projects.py, settings.py, signal.py, tasks.py, webhooks.py, workflow.py)
- [ ] T011 [P] [US1] Remove unused imports and variables identified by ruff in backend/src/services/*.py (agent_creator.py, agent_tracking.py, ai_agent.py, cache.py, cleanup_service.py, completion_providers.py, database.py, encryption.py, github_auth.py, mcp_store.py, model_fetcher.py, session_store.py, settings_store.py, signal_bridge.py, signal_chat.py, signal_delivery.py, websocket.py)
- [ ] T012 [P] [US1] Remove unused imports and variables in backend/src/models/*.py (agent.py, agent_creator.py, board.py, chat.py, cleanup.py, housekeeping.py, mcp.py, project.py, recommendation.py, settings.py, signal.py, task.py, user.py, workflow.py)
- [ ] T013 [P] [US1] Remove unused functions and methods in backend/src/services/ that are defined but never called by any module (cross-reference with backend/src/api/ call sites and backend/tests/ usage)
- [ ] T014 [P] [US1] Remove unused Pydantic model definitions in backend/src/models/ that are not referenced by any API endpoint, service, or test
- [ ] T015 [P] [US1] Remove commented-out code blocks (not documentation comments) in backend/src/services/github_projects/service.py and other backend/src/ files
- [ ] T016 [P] [US1] Remove unused API route handlers in backend/src/api/ that have no frontend callers in frontend/src/services/api.ts and no test coverage in backend/tests/
- [ ] T017 [US1] Run backend CI checks (ruff check, pyright, pytest) to verify no regressions after backend dead code removal

#### Frontend Dead Code Removal

- [ ] T018 [P] [US1] Remove unused imports and variables identified by eslint across all TypeScript files in frontend/src/components/**/*.tsx
- [ ] T019 [P] [US1] Remove unused imports and variables identified by eslint across frontend/src/hooks/*.ts, frontend/src/services/api.ts, frontend/src/utils/*.ts, and frontend/src/types/index.ts
- [ ] T020 [P] [US1] Remove React components in frontend/src/components/ that are defined but never imported by any other file (check all import statements across frontend/src/)
- [ ] T021 [P] [US1] Remove unused React hooks in frontend/src/hooks/ that are not imported by any component or other hook
- [ ] T022 [P] [US1] Remove unused utility functions in frontend/src/utils/ that are not imported by any component, hook, or service
- [ ] T023 [P] [US1] Remove unused TypeScript type definitions and interfaces in frontend/src/types/index.ts that are not referenced anywhere in frontend/src/
- [ ] T024 [P] [US1] Remove commented-out code blocks (not documentation comments) across frontend/src/components/, frontend/src/hooks/, and frontend/src/services/
- [ ] T025 [US1] Run frontend CI checks (eslint, tsc --noEmit, vitest run, vite build) to verify no regressions after frontend dead code removal

**Checkpoint**: User Story 1 complete — all dead code, unused artifacts, and commented-out blocks removed from both backend and frontend. CI green.

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims (Priority: P1)

**Goal**: Remove compatibility layers, polyfills, adapter code supporting deprecated API shapes, migration-period aliases, and dead conditional branches (e.g., `if old_format:` / `if legacy:` patterns).

**Independent Test**: Run the full CI check suite after removing each shim. All checks must pass.

### Implementation for User Story 2

- [ ] T026 [P] [US2] Remove backwards-compatibility conditional branches (if old_format, if legacy, compat patterns) in backend/src/services/github_projects/service.py
- [ ] T027 [P] [US2] Remove backwards-compatibility conditional branches and adapter code in backend/src/services/*.py (agent_creator.py, ai_agent.py, cleanup_service.py, and other service files)
- [ ] T028 [P] [US2] Remove deprecated API shape adapters and migration-period aliases in backend/src/api/*.py
- [ ] T029 [P] [US2] Remove backwards-compatibility shims and polyfills in backend/src/models/*.py (deprecated field aliases, old model shapes, compatibility wrappers)
- [ ] T030 [P] [US2] Remove frontend compatibility layers, polyfills, and legacy conditional branches in frontend/src/components/**/*.tsx and frontend/src/hooks/*.ts
- [ ] T031 [P] [US2] Remove deprecated adapter code and migration-period aliases in frontend/src/services/api.ts and frontend/src/types/index.ts
- [ ] T032 [US2] Run full CI checks (backend + frontend) to verify no regressions after shim removal

**Checkpoint**: User Story 2 complete — all backwards-compatibility shims, polyfills, and legacy conditional branches removed. CI green.

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P2)

**Goal**: Merge near-duplicate functions, helpers, service methods, Pydantic models, and TypeScript types into single canonical implementations. Update all call sites. Refactor copy-pasted test patterns into shared helpers/factories.

**Independent Test**: Run the full CI check suite after each consolidation. Verify all checks pass and no behavior changes.

### Implementation for User Story 3

#### Backend Consolidation

- [ ] T033 [P] [US3] Consolidate duplicate or near-duplicate helper functions and service methods in backend/src/services/ into single canonical implementations
- [ ] T034 [P] [US3] Consolidate overlapping Pydantic model definitions in backend/src/models/ — merge models with substantially similar fields into single definitions with appropriate field unions
- [ ] T035 [P] [US3] Refactor copy-pasted test setup patterns in backend/tests/ into shared test helpers or factories in backend/tests/helpers/
- [ ] T036 [US3] Run backend CI checks (ruff check, pyright, pytest) to verify no regressions after backend consolidation

#### Frontend Consolidation

- [ ] T037 [P] [US3] Consolidate duplicate or near-duplicate utility functions and service methods in frontend/src/services/api.ts and frontend/src/utils/
- [ ] T038 [P] [US3] Consolidate overlapping TypeScript type definitions and interfaces in frontend/src/types/index.ts — merge types with substantially similar shapes
- [ ] T039 [P] [US3] Consolidate duplicated API client logic in frontend/src/services/api.ts — extract shared request patterns into reusable helpers
- [ ] T040 [P] [US3] Refactor copy-pasted test setup patterns across frontend/src/components/**/*.test.tsx and frontend/src/hooks/*.test.ts into shared test factories in frontend/src/test/factories/
- [ ] T041 [US3] Run frontend CI checks (eslint, tsc --noEmit, vitest run, vite build) to verify no regressions after frontend consolidation

**Checkpoint**: User Story 3 complete — duplicated logic consolidated across backend and frontend. All call sites updated. CI green.

---

## Phase 6: User Story 4 — Delete Stale and Irrelevant Tests (Priority: P2)

**Goal**: Remove test files and test cases covering deleted or refactored functionality, over-mocked tests that no longer validate real behavior, tests for non-existent code paths, and leftover test artifacts.

**Independent Test**: Run the full test suite after each removal. Verify all remaining tests pass and no active functionality loses coverage.

### Implementation for User Story 4

#### Backend Stale Test Removal

- [ ] T042 [P] [US4] Remove backend test files in backend/tests/unit/ that test deleted or refactored functionality (cross-reference test imports against current backend/src/ exports)
- [ ] T043 [P] [US4] Remove backend test cases in backend/tests/integration/ that over-mock internals and no longer validate real behavior
- [ ] T044 [P] [US4] Remove backend test cases that test code paths removed during US1 and US2 cleanup in backend/tests/
- [ ] T045 [P] [US4] Remove leftover test artifacts (e.g., MagicMock database files, temporary test databases) from the backend/ workspace root and backend/tests/

#### Frontend Stale Test Removal

- [ ] T046 [P] [US4] Remove frontend test files (*.test.ts, *.test.tsx) that test components, hooks, or utilities removed during US1 and US2 cleanup in frontend/src/
- [ ] T047 [P] [US4] Remove frontend test cases that over-mock internals and no longer validate real behavior across frontend/src/components/**/*.test.tsx and frontend/src/hooks/*.test.ts
- [ ] T048 [US4] Run full test suites (pytest for backend, vitest run for frontend) to verify all remaining tests pass after stale test removal

**Checkpoint**: User Story 4 complete — all stale tests and test artifacts removed. Test suite signal-to-noise ratio improved. CI green.

---

## Phase 7: User Story 5 — Perform General Hygiene Cleanup (Priority: P3)

**Goal**: Remove orphaned configuration/migration files, clean up stale TODO/FIXME/HACK comments tied to completed work, remove unused dependencies, and remove unused Docker Compose services or environment variables.

**Independent Test**: Run the full CI check suite and Docker Compose build after each change. Verify no active features are affected.

### Implementation for User Story 5

- [ ] T049 [P] [US5] Remove stale TODO/FIXME/HACK comments tied to completed work across backend/src/, frontend/src/, and scripts/ (cross-referenced with completed issues/PRs in Phase 2 analysis)
- [ ] T050 [P] [US5] Remove unused Python dependencies from backend/pyproject.toml — verify by running pip install and full backend test suite
- [ ] T051 [P] [US5] Remove unused JavaScript/TypeScript dependencies from frontend/package.json — verify by running npm install and full frontend build + test suite
- [ ] T052 [P] [US5] Remove orphaned migration files or configuration files in backend/src/migrations/ that reference deleted features (confirm not loaded by migration discovery in backend/src/services/database.py)
- [ ] T053 [P] [US5] Remove unused Docker Compose services or environment variables in docker-compose.yml and .env.example
- [ ] T054 [P] [US5] Remove orphaned configuration files in .vscode/, .devcontainer/, or scripts/ that reference deleted features or deprecated tooling
- [ ] T055 [US5] Run full CI checks (backend + frontend) and verify Docker Compose services start correctly after hygiene cleanup

**Checkpoint**: User Story 5 complete — all general hygiene items addressed. Stale comments, unused dependencies, and orphaned configs removed. CI green.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, categorized summary, and cross-cutting verification across all cleanup categories

- [ ] T056 [P] Verify no public API contracts were altered — diff all route paths, request shapes, and response shapes in backend/src/api/*.py against pre-cleanup baseline
- [ ] T057 [P] Verify no dynamically loaded code was removed — re-trace plugin loading in backend/src/services/github_projects/service.py and migration discovery in backend/src/services/database.py against the safe-to-ignore list from T003
- [ ] T058 [P] Run full backend CI suite (ruff check, ruff format --check, pyright, pytest) as final validation from backend/
- [ ] T059 [P] Run full frontend CI suite (eslint, tsc --noEmit, vitest run, vite build) as final validation from frontend/
- [ ] T060 Compile categorized PR summary covering every change made across all five cleanup categories with rationale for each removal or consolidation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — analysis uses baseline CI results — BLOCKS all user stories
- **US1 - Dead Code (Phase 3)**: Depends on Foundational (Phase 2) — uses analysis results
- **US2 - Shims (Phase 4)**: Depends on Foundational (Phase 2) — uses analysis results. Can run in parallel with US1 if changes target different files
- **US3 - Consolidation (Phase 5)**: Depends on US1 and US2 completion — consolidation should happen after dead code and shims are removed to avoid consolidating code that will be deleted
- **US4 - Stale Tests (Phase 6)**: Depends on US1 and US2 completion — test cleanup must account for code removed in those phases
- **US5 - Hygiene (Phase 7)**: Depends on US1 and US2 completion — dependency audit requires knowing which code was removed
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories — **MVP**
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — can run in parallel with US1 if targeting different files
- **User Story 3 (P2)**: Should start after US1 and US2 — avoid consolidating code that will be deleted
- **User Story 4 (P2)**: Should start after US1 and US2 — stale tests may reference removed code
- **User Story 5 (P3)**: Should start after US1 and US2 — dependency analysis depends on final code state

### Within Each User Story

- Backend changes before frontend changes (within same story)
- Analysis before removal
- Removal before CI verification
- CI verification confirms no regressions before moving to next story

### Parallel Opportunities

- T004 and T005 (Phase 2) can run in parallel — different toolchains (ruff vs eslint)
- T006, T007, T008, T009 (Phase 2) can all run in parallel — independent analysis tasks
- T010–T016 (Phase 3, backend) can all run in parallel — independent backend file groups
- T018–T024 (Phase 3, frontend) can all run in parallel — independent frontend file groups
- T026–T031 (Phase 4) can all run in parallel — independent file groups
- T033–T035 (Phase 5, backend) can run in parallel — different target areas
- T037–T040 (Phase 5, frontend) can run in parallel — different target areas
- T042–T047 (Phase 6) can all run in parallel — independent test file groups
- T049–T054 (Phase 7) can all run in parallel — independent hygiene areas
- T056–T059 (Phase 8) can all run in parallel — independent validation checks

---

## Parallel Example: Phase 2 Analysis

```bash
# Launch all analysis tasks in parallel (independent toolchains):
Task T004: "Run ruff unused-import/variable analysis on backend/src/"
Task T005: "Run eslint unused-import/variable analysis on frontend/src/"
Task T006: "Scan for commented-out code blocks across backend/src/ and frontend/src/"
Task T007: "Search for backwards-compatibility patterns across backend/src/ and frontend/src/"
Task T008: "Search for stale TODO/FIXME/HACK comments"
Task T009: "Identify duplicate functions across services"
```

## Parallel Example: User Story 1 (Backend)

```bash
# Launch all backend dead code removal tasks in parallel (different file groups):
Task T010: "Remove unused imports/variables in backend/src/api/*.py"
Task T011: "Remove unused imports/variables in backend/src/services/*.py"
Task T012: "Remove unused imports/variables in backend/src/models/*.py"
Task T013: "Remove unused functions/methods in backend/src/services/"
Task T014: "Remove unused Pydantic models in backend/src/models/"
Task T015: "Remove commented-out code in backend/src/"
Task T016: "Remove unused API route handlers in backend/src/api/"
```

## Parallel Example: User Story 1 (Frontend)

```bash
# Launch all frontend dead code removal tasks in parallel (different file groups):
Task T018: "Remove unused imports/variables in frontend/src/components/"
Task T019: "Remove unused imports/variables in frontend/src/hooks/, services/, utils/, types/"
Task T020: "Remove unused React components in frontend/src/components/"
Task T021: "Remove unused React hooks in frontend/src/hooks/"
Task T022: "Remove unused utility functions in frontend/src/utils/"
Task T023: "Remove unused TypeScript types in frontend/src/types/index.ts"
Task T024: "Remove commented-out code in frontend/src/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify baseline CI, audit dynamic loading)
2. Complete Phase 2: Foundational (run all analysis)
3. Complete Phase 3: User Story 1 — Dead Code Removal
4. **STOP and VALIDATE**: Run full CI suite, verify no API contract changes
5. Commit with `chore: remove dead code and unused artifacts`

### Incremental Delivery

1. Complete Setup + Foundational → Analysis complete
2. Add User Story 1 (Dead Code) → CI green → Commit (MVP!)
3. Add User Story 2 (Shims) → CI green → Commit
4. Add User Story 3 (Consolidation) → CI green → Commit
5. Add User Story 4 (Stale Tests) → CI green → Commit
6. Add User Story 5 (Hygiene) → CI green → Commit
7. Polish → Final validation + PR summary → Commit
8. Each commit uses conventional format: `chore:` for removals, `refactor:` for consolidations

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational analysis together
2. Once analysis is done:
   - Developer A: User Story 1 backend (T010–T017) + User Story 2 backend (T026–T029)
   - Developer B: User Story 1 frontend (T018–T025) + User Story 2 frontend (T030–T031)
3. After US1 + US2 merge:
   - Developer A: User Story 3 backend (T033–T036) + User Story 4 backend (T042–T045)
   - Developer B: User Story 3 frontend (T037–T041) + User Story 4 frontend (T046–T047)
   - Developer C: User Story 5 all (T049–T055)
4. Team completes Polish together

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 60 |
| **Phase 1 (Setup)** | 3 tasks |
| **Phase 2 (Foundational)** | 6 tasks |
| **Phase 3 (US1 — Dead Code, P1)** | 16 tasks |
| **Phase 4 (US2 — Shims, P1)** | 7 tasks |
| **Phase 5 (US3 — Consolidation, P2)** | 9 tasks |
| **Phase 6 (US4 — Stale Tests, P2)** | 7 tasks |
| **Phase 7 (US5 — Hygiene, P3)** | 7 tasks |
| **Phase 8 (Polish)** | 5 tasks |
| **Parallel opportunities** | 48 tasks marked [P] across all phases |
| **Independent test criteria** | Each story validated by full CI suite (ruff, pyright, pytest, eslint, tsc, vitest, vite build) |
| **Suggested MVP scope** | Phase 1 + 2 + 3 (User Story 1: Dead Code Removal — 25 tasks) |
| **Format validation** | ✅ All 60 tasks follow checklist format (checkbox, ID, labels, file paths) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story (cleanup category) for traceability
- Each user story should be independently completable and testable via CI suite
- Commit after each user story or logical group using conventional commits
- `chore:` prefix for dead code removal and test deletion (US1, US2, US4)
- `refactor:` prefix for consolidation changes (US3)
- `chore:` prefix for hygiene cleanup (US5)
- No public API contracts (route paths, request/response shapes) may be altered
- Dynamic loading patterns (plugin loaders, migration discovery) must be preserved
- Backend follows Python 3.12 / FastAPI / Pydantic v2 / aiosqlite patterns
- Frontend follows TypeScript 5.4 / React 18 / Vite 5.4 / TanStack Query v5 / Tailwind CSS 3.4 patterns
- Stop at any checkpoint to validate story independently before proceeding
