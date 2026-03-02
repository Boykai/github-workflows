# Tasks: Repository-Wide Codebase Cleanup Across Backend & Frontend

**Input**: Design documents from `/specs/016-codebase-cleanup/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Tests are NOT requested — no test tasks are included. Existing CI checks (`ruff`, `pyright`, `pytest`, `eslint`, `tsc`, `vitest`, `vite build`) serve as validation after each cleanup phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each user story maps to one of the five cleanup categories from the parent issue.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/helpers/`
- **Docker config**: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`
- **Dependency manifests**: `backend/pyproject.toml`, `frontend/package.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Validate baseline CI state and audit dynamic loading patterns to establish a do-not-remove list before any cleanup begins.

- [ ] T001 Run baseline backend CI checks (`ruff check src tests`, `ruff format --check src tests`, `pyright`, `pytest`) in `backend/` and record pass/fail state
- [ ] T002 Run baseline frontend CI checks (`eslint .`, `tsc --noEmit`, `vitest run`, `vite build`) in `frontend/` and record pass/fail state
- [ ] T003 Audit dynamic loading patterns in backend: document all string-based plugin loading (agent discovery regex in `backend/src/services/github_projects/service.py`), migration file glob (`backend/src/services/database.py`), and prompt file loading (`backend/src/prompts/`) to create a do-not-remove reference list
- [ ] T004 Audit dynamic loading patterns in frontend: document any lazy imports, dynamic `import()` calls, and route-based code splitting in `frontend/src/` to create a do-not-remove reference list

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Static analysis scans to identify all cleanup targets across both codebases. Results from these scans inform every subsequent user story phase.

**⚠️ CRITICAL**: No cleanup work should begin until these scans are complete and the do-not-remove list from Phase 1 is established.

- [ ] T005 Run `ruff check --select F401,F811,F841` on `backend/src/` and `backend/tests/` to identify unused imports and variables, cross-referencing against the do-not-remove list from T003
- [ ] T006 [P] Run TypeScript compiler unused analysis (`tsc --noUnusedLocals --noUnusedParameters --noEmit`) on `frontend/src/` to identify unused TypeScript imports, variables, and parameters
- [ ] T007 [P] Search for commented-out code blocks (multi-line `#`-prefixed blocks in Python, `//` and `/* */` blocks in TypeScript) across `backend/src/` and `frontend/src/`, excluding documentation comments and license headers
- [ ] T008 [P] Search for legacy/backwards-compatibility patterns (`old_format`, `legacy`, `deprecated`, `compat`, `shim`, `polyfill`, `adapter`, `migration_period`, `v1_`, `old_`) across `backend/src/` and `frontend/src/`
- [ ] T009 [P] Identify near-duplicate functions by scanning for functions with similar names and signatures across `backend/src/services/`, `backend/src/api/`, `frontend/src/services/`, and `frontend/src/hooks/`
- [ ] T010 Search for stale `TODO`, `FIXME`, and `HACK` comments across the entire repository, categorizing each as tied-to-completed-work (removable) or tied-to-ongoing-work (preserve)

**Checkpoint**: All cleanup targets identified — user story implementation can now begin

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all unused functions, methods, components, imports, variables, type definitions, Pydantic models, commented-out logic blocks, and unused API route handlers from both backend and frontend.

**Independent Test**: Run static analysis tools to confirm zero unused exports, imports, variables, and definitions exist, and verify all CI checks pass after removal.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Remove unused imports and variables identified by `ruff` (F401/F841) across all files in `backend/src/`
- [ ] T012 [P] [US1] Remove unused imports and variables identified by `ruff` (F401/F841) across all files in `backend/tests/`
- [ ] T013 [P] [US1] Remove unused TypeScript imports, variables, and type definitions across all files in `frontend/src/`
- [ ] T014 [P] [US1] Scan for defined-but-never-called Python functions and methods in `backend/src/services/` and `backend/src/api/` — remove those confirmed unused (not dynamically loaded, not referenced in tests)
- [ ] T015 [P] [US1] Scan for defined-but-never-imported React components in `frontend/src/components/` — remove those confirmed unused (not lazy-loaded, not referenced elsewhere)
- [ ] T016 [P] [US1] Scan for unused React hooks in `frontend/src/hooks/` — remove those with zero import references across `frontend/src/`
- [ ] T017 [P] [US1] Scan for unused utility functions in `frontend/src/utils/` and `frontend/src/lib/` — remove those with zero import references
- [ ] T018 [P] [US1] Remove unused Pydantic models in `backend/src/models/` — verify each model is referenced in at least one API route, service, or test before removing
- [ ] T019 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) identified in T007 across `backend/src/` and `frontend/src/`
- [ ] T020 [US1] Scan for unused API route handlers in `backend/src/api/` — identify handlers with no frontend callers (not referenced in `frontend/src/services/api.ts`) and no test coverage, then remove while preserving all public route paths
- [ ] T021 [US1] Run full backend CI checks (`ruff`, `pyright`, `pytest`) to verify no regressions from dead code removal
- [ ] T022 [US1] Run full frontend CI checks (`eslint`, `tsc`, `vitest`, `vite build`) to verify no regressions from dead code removal

**Checkpoint**: User Story 1 complete — all dead code and unused artifacts removed, CI green

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims and Legacy Code (Priority: P1)

**Goal**: Remove compatibility layers, polyfills, adapter code, migration-period aliases, and dead conditional branches following legacy patterns. The codebase reflects only current supported behavior.

**Independent Test**: Search for legacy patterns (`old_format`, `legacy`, `deprecated`, `compat`, `shim`) and confirm none remain, then verify all CI checks pass.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Remove backwards-compatibility shims and adapter code identified in T008 from `backend/src/` — remove compatibility layers, deprecated API shape adapters, and migration-period aliases
- [ ] T024 [P] [US2] Remove dead conditional branches following legacy patterns (e.g., `if old_format:`, `if legacy:`, `if deprecated:`) from `backend/src/` — simplify to retain only the current code path
- [ ] T025 [P] [US2] Remove backwards-compatibility shims and polyfills identified in T008 from `frontend/src/` — remove compatibility layers, deprecated shape adapters, and migration-period code
- [ ] T026 [P] [US2] Remove dead conditional branches following legacy patterns from `frontend/src/` — simplify to retain only the current code path
- [ ] T027 [US2] Verify no public API contracts (route paths, request/response shapes) were altered by shim removal — compare `backend/src/api/` route definitions before and after changes
- [ ] T028 [US2] Run full backend and frontend CI checks to verify no regressions from shim removal

**Checkpoint**: User Story 2 complete — all backwards-compatibility code removed, only current behavior remains, CI green

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P2)

**Goal**: Merge near-duplicate functions, helpers, and service methods into single implementations. Refactor copy-pasted test patterns using shared helpers/factories. Consolidate duplicated API client logic and overlapping model definitions.

**Independent Test**: Verify all consolidated functions' callers produce identical results before and after consolidation, with all CI checks passing.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Identify and consolidate near-duplicate Python functions and service methods in `backend/src/services/` — merge into single implementations and update all callers
- [ ] T030 [P] [US3] Identify and consolidate near-duplicate Python helper functions in `backend/src/api/` and `backend/src/utils.py` — merge into single implementations and update all callers
- [ ] T031 [P] [US3] Identify and consolidate overlapping Pydantic model definitions in `backend/src/models/` — merge near-identical models into canonical definitions and update all references
- [ ] T032 [P] [US3] Identify and consolidate duplicated API client logic in `frontend/src/services/api.ts` — merge near-duplicate fetch/mutation functions into shared service functions
- [ ] T033 [P] [US3] Identify and consolidate overlapping TypeScript type definitions in `frontend/src/types/index.ts` — merge near-identical types into canonical definitions and update all references
- [ ] T034 [P] [US3] Refactor copy-pasted test patterns in `backend/tests/unit/` — extract shared helpers into `backend/tests/helpers/factories.py` and `backend/tests/helpers/mocks.py`, update tests to use them
- [ ] T035 [US3] Run full backend and frontend CI checks to verify no regressions from consolidation

**Checkpoint**: User Story 3 complete — duplicated logic consolidated, shared helpers in use, CI green

---

## Phase 6: User Story 4 — Delete Stale and Irrelevant Tests (Priority: P2)

**Goal**: Remove test files and cases covering deleted or refactored functionality. Remove tests that over-mock internals and no longer validate real behavior. Remove leftover test artifacts.

**Independent Test**: Run the full test suite and confirm all remaining tests pass, and verify no test references deleted functions, components, or code paths.

### Implementation for User Story 4

- [ ] T036 [P] [US4] Scan `backend/tests/unit/` for test files and test cases that reference functions, classes, or code paths deleted in earlier cleanup phases (US1, US2, US3) — remove those tests
- [ ] T037 [P] [US4] Scan `backend/tests/integration/` for test files and test cases referencing deleted functionality — remove those tests
- [ ] T038 [P] [US4] Scan frontend test files (`frontend/src/**/*.test.tsx`, `frontend/src/**/*.test.ts`) for test cases referencing deleted components, hooks, or utilities — remove those tests
- [ ] T039 [P] [US4] Identify tests in `backend/tests/unit/` that over-mock internals (e.g., excessive `MagicMock` usage that bypasses real behavior) and no longer validate actual application behavior — remove or flag for rewrite
- [ ] T040 [P] [US4] Search for and remove leftover test artifacts in the repository root and `backend/` root — e.g., stray `MagicMock` database files, `.db` files, temporary test outputs
- [ ] T041 [US4] Run full backend and frontend test suites to verify all remaining tests pass with no regressions

**Checkpoint**: User Story 4 complete — stale tests removed, test suite accurately reflects current codebase, CI green

---

## Phase 7: User Story 5 — General Hygiene and Dependency Cleanup (Priority: P3)

**Goal**: Remove orphaned configs, stale comments, unused dependencies, and unused Docker Compose services/variables. Project configuration accurately reflects the current application state.

**Independent Test**: Audit dependency manifests for unused packages, search for stale TODO/FIXME/HACK comments, and verify all CI checks and builds pass after removal.

### Implementation for User Story 5

- [ ] T042 [P] [US5] Remove stale `TODO`, `FIXME`, and `HACK` comments tied to completed work identified in T010 across `backend/src/` and `backend/tests/`
- [ ] T043 [P] [US5] Remove stale `TODO`, `FIXME`, and `HACK` comments tied to completed work identified in T010 across `frontend/src/`
- [ ] T044 [P] [US5] Audit `backend/pyproject.toml` dependencies — identify packages not imported anywhere in `backend/src/` or `backend/tests/` and remove them (validate with full build and test run)
- [ ] T045 [P] [US5] Audit `frontend/package.json` dependencies and devDependencies — identify packages not imported anywhere in `frontend/src/` or test/config files and remove them (validate with `npm install`, `vitest run`, `vite build`)
- [ ] T046 [P] [US5] Audit `backend/src/migrations/` for orphaned migration files referencing deleted features — remove only if confirmed not part of the active migration chain (do NOT break schema history)
- [ ] T047 [P] [US5] Audit `docker-compose.yml` for unused services, environment variables, or volume definitions referencing deleted features — remove unused entries
- [ ] T048 [P] [US5] Audit `.env.example` for environment variables no longer referenced in `backend/src/config.py` or `docker-compose.yml` — remove stale entries
- [ ] T049 [P] [US5] Scan `scripts/` for unused or stale script files referencing deleted features or workflows — remove those confirmed unused
- [ ] T050 [US5] Run full backend and frontend CI checks plus `docker-compose config` to verify no regressions from hygiene cleanup

**Checkpoint**: User Story 5 complete — project configuration is clean and accurate, CI green

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all cleanup categories and PR documentation.

- [ ] T051 Run full backend CI suite: `cd backend && ruff check src tests && ruff format --check src tests && pyright && pytest -v`
- [ ] T052 Run full frontend CI suite: `cd frontend && npm run lint && npm run type-check && npm test && npm run build`
- [ ] T053 Verify no public API contracts were altered — compare all route definitions in `backend/src/api/` before and after cleanup to confirm identical paths and response shapes
- [ ] T054 Verify no dynamically-loaded code was incorrectly removed — re-run dynamic loading audit from T003/T004 and confirm all referenced modules still exist
- [ ] T055 Compile categorized PR summary covering every change organized by the five cleanup categories (backwards-compatibility shims, dead code, duplicated logic, stale tests, general hygiene) with explanation for each removal
- [ ] T056 Document total lines of dead or duplicated code removed in the PR summary
- [ ] T057 Commit all changes using conventional commit format: `refactor:` for consolidation (US3) and `chore:` for dead code removal (US1, US2), stale test deletion (US4), and hygiene cleanup (US5)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T003/T004 do-not-remove list) — BLOCKS all cleanup work
- **User Story 1 (Phase 3)**: Depends on Foundational phase — uses scan results from T005–T007
- **User Story 2 (Phase 4)**: Depends on Foundational phase — uses scan results from T008. Can run in parallel with US1 (different targets)
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion — consolidation is safer after dead code and shims are removed
- **User Story 4 (Phase 6)**: Depends on US1, US2, and US3 — stale tests are identified by what was deleted/refactored in those phases
- **User Story 5 (Phase 7)**: Depends on Foundational phase — can run in parallel with US1/US2 for non-overlapping tasks (T042–T049)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories, can run in parallel with US1
- **US3 (P2)**: Should start after US1 and US2 — consolidation is safer once dead code and shims are removed
- **US4 (P2)**: Should start after US1, US2, and US3 — stale tests are identified by deletions in prior phases
- **US5 (P3)**: Partially parallelizable with US1/US2 (comments, dependencies, configs touch different files) but dependency removal should wait until code cleanup is complete

### Within Each User Story

- Scan/identify before remove
- Backend and frontend removals can run in parallel (different directories)
- CI validation after each story's removals
- Commit after each logical group using conventional commit format

### Parallel Opportunities

- T005, T006, T007, T008, T009, T010 (Foundational scans) — all scan different targets, fully parallel
- T011–T020 (US1 implementation) — all [P] tasks target different files/directories, parallel within story
- T023–T026 (US2 implementation) — backend and frontend removals are parallel
- T029–T034 (US3 implementation) — all target different directories, parallel within story
- T036–T040 (US4 implementation) — all target different test directories, parallel within story
- T042–T049 (US5 implementation) — all target different files/directories, parallel within story
- US1 and US2 can run in parallel (dead code vs. shims — different removal targets)
- US5 partial tasks (comments, configs) can run in parallel with US1/US2

---

## Parallel Example: Foundational Scans

```bash
# All scans can run simultaneously (different targets):
Task T005: "Run ruff unused import/variable scan on backend/"
Task T006: "Run TypeScript unused analysis on frontend/"
Task T007: "Search for commented-out code blocks across both codebases"
Task T008: "Search for legacy/backwards-compatibility patterns"
Task T009: "Identify near-duplicate functions across services"
Task T010: "Search for stale TODO/FIXME/HACK comments"
```

## Parallel Example: User Story 1 (Dead Code Removal)

```bash
# Backend and frontend removals can run simultaneously:
Task T011: "Remove unused imports/variables in backend/src/"
Task T013: "Remove unused imports/variables in frontend/src/"

# Component-level scans can run in parallel:
Task T014: "Scan for unused functions in backend/src/services/"
Task T015: "Scan for unused components in frontend/src/components/"
Task T016: "Scan for unused hooks in frontend/src/hooks/"
Task T017: "Scan for unused utilities in frontend/src/utils/"
Task T018: "Scan for unused Pydantic models in backend/src/models/"
```

## Parallel Example: User Story 3 (Consolidation)

```bash
# Backend and frontend consolidations can run simultaneously:
Task T029: "Consolidate duplicate service methods in backend/src/services/"
Task T032: "Consolidate duplicate API client logic in frontend/src/services/api.ts"
Task T033: "Consolidate overlapping types in frontend/src/types/index.ts"
Task T034: "Refactor copy-pasted test patterns in backend/tests/unit/"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (baseline validation + dynamic loading audit)
2. Complete Phase 2: Foundational (static analysis scans)
3. Complete Phase 3: User Story 1 — Remove dead code and unused artifacts
4. Complete Phase 4: User Story 2 — Remove backwards-compatibility shims
5. **STOP and VALIDATE**: All CI checks pass, no public API contracts altered
6. Deploy/demo if ready — highest-impact cleanup delivered

### Incremental Delivery

1. Complete Setup + Foundational → All cleanup targets identified
2. Add User Story 1 → Dead code removed → CI green (MVP!)
3. Add User Story 2 → Legacy shims removed → CI green
4. Add User Story 3 → Duplicated logic consolidated → CI green
5. Add User Story 4 → Stale tests deleted → CI green
6. Add User Story 5 → General hygiene complete → CI green
7. Polish → PR summary documented, final validation → Done
8. Each story adds value without breaking previous cleanup work

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (dead code — backend focus)
   - Developer B: User Story 1 (dead code — frontend focus) + User Story 2 (shims)
   - Developer C: User Story 5 partial (comments, configs — non-overlapping with code removal)
3. After US1 + US2 merge:
   - Developer A: User Story 3 (consolidation)
   - Developer B: User Story 4 (stale tests)
   - Developer C: User Story 5 remaining (dependency removal)
4. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 57 (T001–T057) |
| **Phase 1 (Setup)** | 4 tasks (T001–T004) |
| **Phase 2 (Foundational)** | 6 tasks (T005–T010) |
| **Phase 3 (US1 — Dead Code)** | 12 tasks (T011–T022) |
| **Phase 4 (US2 — Shims)** | 6 tasks (T023–T028) |
| **Phase 5 (US3 — Consolidation)** | 7 tasks (T029–T035) |
| **Phase 6 (US4 — Stale Tests)** | 6 tasks (T036–T041) |
| **Phase 7 (US5 — Hygiene)** | 9 tasks (T042–T050) |
| **Phase 8 (Polish)** | 7 tasks (T051–T057) |
| **Parallel opportunities** | 7 groups identified |
| **Independent test criteria** | Each user story has clear independent verification |
| **Suggested MVP scope** | US1 + US2 (P1 — Dead code + shims, Phases 1–4, 28 tasks) |
| **Format validation** | ✅ All 57 tasks follow checklist format (checkbox, ID, labels, file paths) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Dynamic loading caution**: Always cross-reference removals against the do-not-remove list (T003/T004) before deleting any code
- **Public API protection**: No route paths or request/response shapes in `backend/src/api/` may be altered
- **Commit convention**: `refactor:` for consolidation (US3), `chore:` for dead code (US1, US2), stale tests (US4), hygiene (US5)
- **Migration chain safety**: Migration files in `backend/src/migrations/` must not be removed if part of active schema history
- No test tasks included — existing CI checks serve as validation
- Reuses existing test helpers in `backend/tests/helpers/` (factories.py, mocks.py) for consolidation work
- Backend follows Python 3.12 / FastAPI / Pydantic v2 / aiosqlite conventions
- Frontend follows TypeScript 5.4 / React 18 / Vite 5.4 / TanStack Query v5 / Tailwind CSS 3.4 conventions
