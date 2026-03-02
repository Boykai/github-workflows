# Tasks: Repository-Wide Codebase Cleanup (Backend + Frontend)

**Input**: Design documents from `/specs/016-codebase-cleanup/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Tests are NOT included — the specification does not request new tests. The cleanup itself is validated by ensuring all existing CI checks pass after each change.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories map to the five cleanup categories defined in the specification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`, `frontend/src/`
- **Infrastructure**: `docker-compose.yml`, `pyproject.toml`, `frontend/package.json`
- **Scripts**: `scripts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline CI health and inventory before any cleanup changes

- [ ] T001 Run full backend CI checks (ruff, pyright, pytest) and record baseline pass/fail state from repository root
- [ ] T002 [P] Run full frontend CI checks (eslint, tsc, vitest, vite build) and record baseline pass/fail state from frontend/
- [ ] T003 Audit dynamically-loaded code paths (string-based plugin loading in backend/src/services/github_projects/service.py, migration discovery in backend/src/migrations/__init__.py, agent discovery in backend/src/services/agent_creator.py) and document protected files that MUST NOT be removed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Identify all cleanup targets across the codebase that MUST be catalogued before any deletion or refactoring begins

**⚠️ CRITICAL**: No cleanup work should begin until the full inventory of targets is established to avoid breaking cross-references

- [ ] T004 Scan backend for unused imports, variables, and functions using ruff's F401/F811/F841 rules across backend/src/
- [ ] T005 [P] Scan frontend for unused imports, variables, exports, and components using eslint and tsc --noUnusedLocals across frontend/src/
- [ ] T006 [P] Scan for commented-out code blocks (excluding docstrings and documentation comments) across backend/src/ and frontend/src/
- [ ] T007 [P] Scan for stale TODO/FIXME/HACK comments tied to completed work across all source files
- [ ] T008 [P] Identify backwards-compatibility shims, legacy conditional branches (if old_format:, if legacy: patterns), and adapter code across backend/src/ and frontend/src/
- [ ] T009 [P] Identify near-duplicate functions, helpers, and overlapping type/model definitions across backend/src/ and frontend/src/
- [ ] T010 [P] Identify stale test files and test cases covering deleted functionality across backend/tests/ and frontend/src/

**Checkpoint**: Full cleanup inventory established — specific targets identified for each cleanup category

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all dead code paths, unused imports, unreferenced functions, orphaned components, commented-out logic blocks, and unused API route handlers so the codebase is easier to navigate and maintain.

**Independent Test**: Run all CI checks (ruff, pyright, pytest, eslint, tsc, vitest, vite build) after removal — all must pass with zero regressions.

### Backend Dead Code Removal

- [ ] T011 [P] [US1] Remove unused imports flagged by ruff (F401) across all files in backend/src/
- [ ] T012 [P] [US1] Remove unused variables flagged by ruff (F841) across all files in backend/src/
- [ ] T013 [P] [US1] Remove unused functions and methods that are defined but never imported or called in backend/src/services/, backend/src/api/, backend/src/models/
- [ ] T014 [P] [US1] Remove unused Pydantic model definitions that are defined but never referenced in backend/src/models/
- [ ] T015 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) in backend/src/
- [ ] T016 [US1] Remove unused API route handlers with no frontend callers or test coverage in backend/src/api/ (verify each handler against frontend/src/services/api.ts and backend/tests/)
- [ ] T017 [US1] Run backend CI checks (ruff, pyright, pytest) to verify all removals are safe

### Frontend Dead Code Removal

- [ ] T018 [P] [US1] Remove unused imports flagged by eslint across all files in frontend/src/
- [ ] T019 [P] [US1] Remove unused React components that are defined but never imported in frontend/src/components/
- [ ] T020 [P] [US1] Remove unused React hooks that are defined but never imported in frontend/src/hooks/
- [ ] T021 [P] [US1] Remove unused utility functions in frontend/src/utils/ and frontend/src/lib/utils.ts
- [ ] T022 [P] [US1] Remove unused TypeScript type definitions and interfaces in frontend/src/types/index.ts
- [ ] T023 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) in frontend/src/
- [ ] T024 [US1] Run frontend CI checks (eslint, tsc, vitest, vite build) to verify all removals are safe

**Checkpoint**: User Story 1 complete — all dead code removed, all CI checks pass

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims and Legacy Branches (Priority: P1)

**Goal**: Remove compatibility layers, polyfills, adapter code, and dead conditional branches supporting deprecated patterns so the codebase reflects only the current architecture.

**Independent Test**: Run full CI suite after removal and verify all checks pass. Verify no public API route paths or request/response shapes have changed.

### Backend Shim Removal

- [ ] T025 [P] [US2] Remove backwards-compatibility shims, adapter code, and migration-period aliases in backend/src/services/ and backend/src/api/
- [ ] T026 [P] [US2] Remove dead conditional branches (e.g., if old_format:, if legacy: patterns) in backend/src/
- [ ] T027 [US2] Update any callers of removed shims to use the current pattern directly in backend/src/
- [ ] T028 [US2] Run backend CI checks (ruff, pyright, pytest) to verify shim removal is safe

### Frontend Shim Removal

- [ ] T029 [P] [US2] Remove backwards-compatibility shims, polyfills, and adapter code in frontend/src/
- [ ] T030 [P] [US2] Remove dead conditional branches supporting deprecated patterns in frontend/src/
- [ ] T031 [US2] Update any callers of removed shims to use the current pattern directly in frontend/src/
- [ ] T032 [US2] Run frontend CI checks (eslint, tsc, vitest, vite build) to verify shim removal is safe
- [ ] T033 [US2] Verify no public API contracts (route paths, request/response shapes) have been altered by comparing backend/src/api/ route definitions before and after changes

**Checkpoint**: User Story 2 complete — all backwards-compatibility code removed, all CI checks pass, no API contract changes

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P2)

**Goal**: Merge near-duplicate functions, helpers, service methods, and type definitions into single implementations so future changes only need to be made in one place.

**Independent Test**: Run all CI checks after consolidation. Verify every caller of previously duplicated functions now uses the consolidated version.

### Backend Consolidation

- [ ] T034 [P] [US3] Consolidate near-duplicate helper functions and service methods into single implementations in backend/src/services/ and backend/src/utils.py
- [ ] T035 [P] [US3] Consolidate overlapping Pydantic model definitions into unified models in backend/src/models/
- [ ] T036 [US3] Update all callers to use consolidated implementations in backend/src/
- [ ] T037 [US3] Run backend CI checks (ruff, pyright, pytest) to verify consolidation is safe

### Frontend Consolidation

- [ ] T038 [P] [US3] Consolidate near-duplicate utility functions and helpers into single implementations in frontend/src/utils/ and frontend/src/lib/
- [ ] T039 [P] [US3] Consolidate overlapping TypeScript type definitions and interfaces in frontend/src/types/index.ts
- [ ] T040 [P] [US3] Consolidate duplicated API client logic in frontend/src/services/api.ts
- [ ] T041 [US3] Update all callers to use consolidated implementations in frontend/src/
- [ ] T042 [US3] Run frontend CI checks (eslint, tsc, vitest, vite build) to verify consolidation is safe

### Test Consolidation

- [ ] T043 [P] [US3] Refactor copy-pasted test patterns into shared helpers/factories in backend/tests/helpers/factories.py and backend/tests/helpers/mocks.py
- [ ] T044 [P] [US3] Refactor copy-pasted frontend test patterns into shared test utilities in frontend/src/test/test-utils.tsx
- [ ] T045 [US3] Run full test suite (pytest + vitest) to verify test refactoring preserves all coverage

**Checkpoint**: User Story 3 complete — all duplicated logic consolidated, all CI checks pass

---

## Phase 6: User Story 4 — Delete Stale and Irrelevant Tests (Priority: P2)

**Goal**: Remove test files and test cases that cover deleted functionality, over-mock internals, or test nonexistent code paths so the test suite accurately reflects current system behavior.

**Independent Test**: Run full test suite after removal and confirm all remaining tests pass. Verify no test covering active functionality is removed.

### Backend Stale Test Removal

- [ ] T046 [P] [US4] Remove test files covering deleted or refactored functionality in backend/tests/unit/
- [ ] T047 [P] [US4] Remove test cases that over-mock internals and no longer validate real behavior in backend/tests/unit/
- [ ] T048 [P] [US4] Remove tests for code paths that no longer exist in backend/tests/unit/ and backend/tests/integration/
- [ ] T049 [P] [US4] Clean up leftover test artifacts (e.g., MagicMock database files, stale fixtures) in backend/ workspace root and backend/tests/
- [ ] T050 [US4] Run backend tests (pytest) to verify remaining test suite passes

### Frontend Stale Test Removal

- [ ] T051 [P] [US4] Remove test files and test cases covering deleted or refactored frontend functionality in frontend/src/
- [ ] T052 [P] [US4] Remove tests that over-mock internals and no longer validate real behavior in frontend/src/
- [ ] T053 [US4] Run frontend tests (vitest) to verify remaining test suite passes

**Checkpoint**: User Story 4 complete — all stale tests removed, remaining test suite passes

---

## Phase 7: User Story 5 — General Hygiene and Dependency Cleanup (Priority: P3)

**Goal**: Remove orphaned configs, stale TODO/FIXME/HACK comments, unused dependencies, and unused infrastructure definitions so the project configuration accurately reflects what is actually in use.

**Independent Test**: Run all CI checks, confirm no build or runtime errors, and verify removed dependencies are truly unused.

### Stale Comments and Config Cleanup

- [ ] T054 [P] [US5] Remove stale TODO, FIXME, and HACK comments tied to completed work across backend/src/ and frontend/src/
- [ ] T055 [P] [US5] Remove orphaned migration files or configs referencing deleted features in backend/src/migrations/ (verify each migration is still needed by checking database schema dependencies)

### Dependency Cleanup

- [ ] T056 [P] [US5] Remove unused Python dependencies from backend/pyproject.toml (verify each dependency is not imported anywhere in backend/src/ or backend/tests/)
- [ ] T057 [P] [US5] Remove unused npm dependencies from frontend/package.json (verify each dependency is not imported anywhere in frontend/src/)
- [ ] T058 [US5] Run backend CI checks (ruff, pyright, pytest) after dependency removal to verify no missing imports
- [ ] T059 [US5] Run frontend CI checks (eslint, tsc, vitest, vite build) after dependency removal to verify no missing imports

### Infrastructure Cleanup

- [ ] T060 [P] [US5] Remove unused Docker Compose services or environment variables in docker-compose.yml
- [ ] T061 [P] [US5] Remove unused environment variable references in .env.example
- [ ] T062 [US5] Verify containerized environment functions correctly after infrastructure cleanup by reviewing docker-compose.yml for consistency

**Checkpoint**: User Story 5 complete — all hygiene items addressed, all CI checks pass

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all cleanup categories and PR documentation

- [ ] T063 [P] Verify no public API contracts have been altered by comparing all route paths and request/response shapes in backend/src/api/ against pre-cleanup state
- [ ] T064 [P] Verify no dynamically-loaded code was removed (check plugin loading in backend/src/services/github_projects/service.py, migration discovery in backend/src/migrations/__init__.py, agent discovery patterns)
- [ ] T065 Run full backend CI suite (ruff, pyright, pytest) for final validation
- [ ] T066 [P] Run full frontend CI suite (eslint, tsc, vitest, vite build) for final validation
- [ ] T067 Commit all changes using conventional commits (refactor: for consolidation, chore: for dead code and test removal)
- [ ] T068 Create categorized PR summary covering every change, organized by the five cleanup categories, explaining why each piece of code was identified as dead, stale, or duplicated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — Dead code removal
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — Can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion — Consolidation requires dead code to be removed first
- **User Story 4 (Phase 6)**: Depends on US1 and US3 — Stale test removal requires dead code and consolidation to be complete
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) — Can run in parallel with US1/US2
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Independent of US1
- **User Story 3 (P2)**: Should follow US1/US2 — Consolidation is easier after dead code is removed
- **User Story 4 (P2)**: Should follow US1/US3 — Stale tests are easier to identify after dead code and consolidation
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) — Independent of code-level cleanup

### Within Each User Story

- Backend cleanup before frontend cleanup (backend changes may expose frontend dead code)
- Scan/identify before remove/refactor
- Remove before consolidate
- Verify CI after each major removal batch

### Parallel Opportunities

- T001 and T002 (baseline CI checks) can run in parallel — different directories
- All Foundational scan tasks (T004–T010) marked [P] can run in parallel — independent scans
- US1 backend removal tasks (T011–T015) can run in parallel — different targets
- US1 frontend removal tasks (T018–T023) can run in parallel — different file categories
- US1 and US2 can run in parallel after Foundational — independent cleanup categories
- US5 can run in parallel with US1/US2 — independent hygiene concerns
- US3 backend (T034–T035) and frontend (T038–T040) consolidation tasks can run in parallel — different directories
- US4 backend (T046–T049) and frontend (T051–T052) test cleanup tasks can run in parallel — different test suites
- Polish verification tasks (T063–T066) can run in parallel — independent checks

---

## Parallel Example: Foundational Phase

```bash
# Launch all scan tasks in parallel (independent analysis):
Task: T004 "Scan backend for unused imports/variables/functions"
Task: T005 "Scan frontend for unused imports/variables/exports"
Task: T006 "Scan for commented-out code blocks"
Task: T007 "Scan for stale TODO/FIXME/HACK comments"
Task: T008 "Identify backwards-compatibility shims"
Task: T009 "Identify near-duplicate functions"
Task: T010 "Identify stale test files"
```

## Parallel Example: User Story 1 Backend

```bash
# Launch backend dead code removal tasks in parallel (different targets):
Task: T011 "Remove unused imports in backend/src/"
Task: T012 "Remove unused variables in backend/src/"
Task: T013 "Remove unused functions in backend/src/services/, api/, models/"
Task: T014 "Remove unused Pydantic models in backend/src/models/"
Task: T015 "Remove commented-out logic blocks in backend/src/"
```

## Parallel Example: User Story 1 Frontend

```bash
# Launch frontend dead code removal tasks in parallel (different file categories):
Task: T018 "Remove unused imports in frontend/src/"
Task: T019 "Remove unused React components in frontend/src/components/"
Task: T020 "Remove unused React hooks in frontend/src/hooks/"
Task: T021 "Remove unused utility functions in frontend/src/utils/"
Task: T022 "Remove unused TypeScript types in frontend/src/types/"
Task: T023 "Remove commented-out logic blocks in frontend/src/"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (baseline CI + dynamic loading audit)
2. Complete Phase 2: Foundational (full cleanup inventory)
3. Complete Phase 3: User Story 1 — Dead code removal (highest impact)
4. Complete Phase 4: User Story 2 — Shim removal (equally critical)
5. **STOP and VALIDATE**: Run full CI suite, verify no API contract changes
6. Commit with `chore:` prefix for dead code removal

### Incremental Delivery

1. Complete Setup + Foundational → Inventory ready
2. Add User Story 1 → Dead code removed → Validate CI (MVP!)
3. Add User Story 2 → Shims removed → Validate CI
4. Add User Story 3 → Duplicates consolidated → Validate CI
5. Add User Story 4 → Stale tests removed → Validate CI
6. Add User Story 5 → Hygiene completed → Validate CI
7. Polish → Final validation + PR summary → Release
8. Each story adds cleanup value without breaking previous work

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (inventory phase)
2. Once Foundational is done:
   - Developer A: User Story 1 (dead code) + User Story 3 (consolidation)
   - Developer B: User Story 2 (shims) + User Story 4 (stale tests)
   - Developer C: User Story 5 (hygiene)
3. Stories complete independently and are committed separately

---

## Summary

- **Total tasks**: 68
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 7 tasks
- **Phase 3 (US1 — Dead Code Removal)**: 14 tasks
- **Phase 4 (US2 — Shim Removal)**: 9 tasks
- **Phase 5 (US3 — Logic Consolidation)**: 12 tasks
- **Phase 6 (US4 — Stale Test Deletion)**: 8 tasks
- **Phase 7 (US5 — General Hygiene)**: 9 tasks
- **Phase 8 (Polish)**: 6 tasks
- **Parallel opportunities**: 9 identified (Setup, Foundational, US1 backend, US1 frontend, US1/US2, US3 backend/frontend, US4 backend/frontend, US5, Polish)
- **Independent test criteria**: Each user story validated by running full CI suite after completion
- **Suggested MVP scope**: User Stories 1 + 2 (Dead Code + Shims — Phases 1–4, 33 tasks)
- **Format validation**: ✅ All 68 tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group using conventional commits
- Use `chore:` prefix for dead code and test removal commits
- Use `refactor:` prefix for consolidation and restructuring commits
- Stop at any checkpoint to validate story independently
- ⚠️ Do NOT remove code loaded via string-based plugin loading or migration discovery without first confirming it is truly unused
- Backend follows Python 3.12 / FastAPI / Pydantic v2 / aiosqlite patterns
- Frontend follows TypeScript 5.4 / React 18 / Vite 5.4 / TanStack Query v5 / Tailwind CSS 3.4 / Shadcn UI patterns
- No new test tasks included (cleanup is validated by existing CI checks passing)
- Public API contracts (route paths, request/response shapes) MUST remain unchanged
