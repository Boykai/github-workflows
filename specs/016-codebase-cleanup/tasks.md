# Tasks: Perform Repository-Wide Codebase Cleanup Across Backend & Frontend

**Input**: Design documents from `/specs/016-codebase-cleanup/`
**Prerequisites**: spec.md (required for user stories), parent issue context (tech stack, CI requirements, commit conventions)

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification. This cleanup removes dead code and consolidates logic; it does not add new functionality requiring new tests.

**Organization**: Tasks are grouped by cleanup category (mapped to user stories) to enable independent implementation and CI validation of each category.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/`
- **Frontend tests**: Co-located `*.test.tsx` / `*.test.ts` files alongside source
- **Config**: `backend/pyproject.toml`, `frontend/package.json`, `docker-compose.yml`

---

## Phase 1: Setup (Baseline & Safety Gates)

**Purpose**: Establish a clean CI baseline, snapshot current state, and identify dynamically loaded code paths that must not be removed

- [ ] T001 Run full backend CI checks (`ruff check`, `pyright`, `pytest`) and record baseline pass/fail state from the backend/ directory
- [ ] T002 [P] Run full frontend CI checks (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) and record baseline pass/fail state from the frontend/ directory
- [ ] T003 [P] Identify and document all dynamically loaded code paths — scan for string-based plugin loading in backend/src/services/github_projects/service.py (agent discovery regex), migration file discovery in backend/src/migrations/, and any dynamic imports in frontend/src/ — to create a protected-code list that must not be removed

---

## Phase 2: Foundational (Analysis & Protected-Code Mapping)

**Purpose**: Run static analysis tools to catalog all candidates for removal or consolidation — MUST be complete before any cleanup changes

**⚠️ CRITICAL**: No cleanup work can begin until analysis is complete and the protected-code list is established

- [ ] T004 Run `ruff check --select F401,F811,F841` on backend/src/ to generate a report of all unused imports (F401), redefined unused variables (F811), and unused local variables (F841)
- [ ] T005 [P] Run `eslint` with unused-vars rules on frontend/src/ to generate a report of all unused imports, variables, and type definitions
- [ ] T006 [P] Search backend/src/ for backwards-compatibility patterns: grep for `if.*old_format`, `if.*legacy`, `if.*deprecated`, `if.*compat`, migration-period aliases, and adapter/shim function names — catalog all candidates
- [ ] T007 [P] Search frontend/src/ for backwards-compatibility patterns: grep for polyfills, adapter code, conditional feature-flag branches guarding old behavior, and deprecated API shape handlers — catalog all candidates
- [ ] T008 [P] Identify near-duplicate functions by comparing function signatures and bodies across backend/src/services/, backend/src/api/, backend/src/models/ — catalog consolidation candidates
- [ ] T009 [P] Identify near-duplicate TypeScript types and duplicated API client logic across frontend/src/types/index.ts, frontend/src/services/api.ts, frontend/src/hooks/, and frontend/src/components/ — catalog consolidation candidates
- [ ] T010 [P] Scan for stale TODO/FIXME/HACK comments across backend/ and frontend/ — cross-reference with completed work to identify removal candidates
- [ ] T011 [P] Cross-reference backend/pyproject.toml dependencies against actual imports in backend/src/ to identify unused packages
- [ ] T012 [P] Cross-reference frontend/package.json dependencies against actual imports in frontend/src/ to identify unused packages

**Checkpoint**: Analysis complete — all candidates cataloged, protected-code list established, ready to begin cleanup

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all dead code paths — unused functions, methods, React components, imports, variables, type definitions, Pydantic models, route handlers with no callers, unused hooks, utility functions, and commented-out logic blocks across the entire codebase

**Independent Test**: Run `ruff check`, `pyright`, `pytest` (backend) and `eslint`, `tsc --noEmit`, `vitest run`, `vite build` (frontend) after all removals — all must pass with zero regressions. Every deleted symbol must have zero references in the codebase.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Auto-fix unused imports in backend/src/ by running `ruff check --select F401 --fix backend/src/` — verify no dynamically loaded imports are removed by cross-referencing the protected-code list from T003
- [ ] T014 [P] [US1] Remove unused local variables and redefined-unused variables in backend/src/ by running `ruff check --select F811,F841 --fix backend/src/`
- [ ] T015 [P] [US1] Auto-fix unused imports and variables in frontend/src/ by running `eslint --fix frontend/src/` for unused-vars rules — verify no dynamically loaded imports are removed
- [ ] T016 [US1] Remove unused functions and methods in backend/src/services/ — search for functions defined but never called or imported anywhere in backend/src/ or backend/tests/, excluding dynamically loaded code from T003
- [ ] T017 [P] [US1] Remove unused functions and methods in backend/src/api/ — search for helper functions and internal methods that are defined but never referenced outside their own file
- [ ] T018 [P] [US1] Remove unused Pydantic models in backend/src/models/ — search across all model files (agent.py, agent_creator.py, board.py, chat.py, cleanup.py, housekeeping.py, mcp.py, project.py, recommendation.py, settings.py, signal.py, task.py, user.py, workflow.py) for models never imported or used in API routes, services, or tests
- [ ] T019 [P] [US1] Remove unused API route handlers in backend/src/api/ — identify route handlers with no frontend callers (cross-reference frontend/src/services/api.ts) and no test coverage (cross-reference backend/tests/), ensuring no public API contracts (route paths, request/response shapes) used by the frontend are altered
- [ ] T020 [P] [US1] Remove unused React components in frontend/src/components/ — search for component files or exports never imported in any page, component, or hook file
- [ ] T021 [P] [US1] Remove unused custom hooks in frontend/src/hooks/ — search for hooks never imported or called anywhere in frontend/src/
- [ ] T022 [P] [US1] Remove unused utility functions in frontend/src/utils/formatTime.ts, frontend/src/utils/generateId.ts, and frontend/src/lib/utils.ts — verify each export has at least one consumer
- [ ] T023 [P] [US1] Remove unused TypeScript type definitions and interfaces in frontend/src/types/index.ts — verify each exported type has at least one consumer across frontend/src/
- [ ] T024 [US1] Remove commented-out logic blocks (excluding documentation comments) across backend/src/ — scan all .py files for multi-line commented-out code blocks
- [ ] T025 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) across frontend/src/ — scan all .ts and .tsx files for multi-line commented-out code blocks
- [ ] T026 [US1] Run full backend CI (`ruff check`, `pyright`, `pytest`) to verify all US1 removals pass — fix any regressions introduced by dead code removal
- [ ] T027 [US1] Run full frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) to verify all US1 removals pass — fix any regressions introduced by dead code removal
- [ ] T028 [US1] Commit all US1 changes using `chore: remove dead code and unused artifacts` commit message

**Checkpoint**: User Story 1 complete — all dead code removed, CI green, every remaining symbol is actively referenced

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims and Legacy Branches (Priority: P1)

**Goal**: Remove all backwards-compatibility shims, polyfills, adapter code supporting deprecated API shapes, migration-period aliases, and dead conditional branches (e.g., `if old_format:`, `if legacy:` patterns) across the codebase

**Independent Test**: Run all CI checks after removing shims — any test or runtime path that depended on a removed shim will surface as a failure. All CI checks must pass.

### Implementation for User Story 2

- [ ] T029 [P] [US2] Remove dead conditional branches guarding legacy code paths in backend/src/ — search for `if old_format`, `if legacy`, `if deprecated`, `if compat` patterns, retain only the active code path
- [ ] T030 [P] [US2] Remove compatibility layers and adapter functions in backend/src/services/ — identify functions that exist solely to translate between deprecated and current API shapes, replace callers with direct usage of current shapes
- [ ] T031 [P] [US2] Remove migration-period aliases in backend/src/models/ — search for re-exports, alias assignments, or deprecated model names that map to current names, update all callers to use current names directly
- [ ] T032 [P] [US2] Remove backwards-compatibility shims and polyfills in frontend/src/ — search for adapter code, conditional feature-flag branches guarding old behavior, deprecated API shape handlers, and old format converters
- [ ] T033 [P] [US2] Remove migration-period aliases in frontend/src/types/index.ts and frontend/src/services/api.ts — search for type aliases or re-exports mapping deprecated names to current names, update all consumers
- [ ] T034 [US2] Run full backend CI (`ruff check`, `pyright`, `pytest`) to verify all US2 removals pass
- [ ] T035 [US2] Run full frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) to verify all US2 removals pass
- [ ] T036 [US2] Commit all US2 changes using `chore: remove backwards-compatibility shims and legacy branches` commit message

**Checkpoint**: User Story 2 complete — all shims and legacy branches removed, only current-version code paths remain, CI green

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P2)

**Goal**: Merge near-duplicate functions, helpers, service methods, API client logic, Pydantic models, and TypeScript types into single canonical implementations. Refactor copy-pasted test patterns to use shared helpers/factories.

**Independent Test**: Run all CI checks after consolidation — each merge must preserve existing behavior (no test should change its expected outcome). All CI checks must pass.

### Implementation for User Story 3

- [ ] T037 [P] [US3] Consolidate near-duplicate helper functions in backend/src/services/ — identify functions with overlapping logic across service files (cleanup_service.py, github_projects/service.py, housekeeping/service.py, workflow_orchestrator/orchestrator.py, copilot_polling/helpers.py), merge into shared utility functions in backend/src/utils.py or a new backend/src/services/shared.py
- [ ] T038 [P] [US3] Consolidate overlapping Pydantic model definitions in backend/src/models/ — identify models with duplicate or near-duplicate field sets across model files, merge into canonical definitions and update all importers
- [ ] T039 [P] [US3] Refactor copy-pasted test patterns in backend/tests/unit/ — identify repeated setup/teardown patterns and extract into shared helpers in backend/tests/helpers/factories.py and backend/tests/helpers/mocks.py
- [ ] T040 [P] [US3] Consolidate duplicated API client logic in frontend/src/services/api.ts — identify repeated request patterns (error handling, auth header injection, response parsing) and extract into shared helper functions within the same file
- [ ] T041 [P] [US3] Consolidate overlapping TypeScript type declarations in frontend/src/types/index.ts — identify types with duplicate or near-duplicate shapes, merge into canonical type definitions and update all consumers
- [ ] T042 [P] [US3] Consolidate near-duplicate component logic in frontend/src/components/ — identify repeated UI patterns, conditional rendering logic, or hook usage across components and extract into shared components or custom hooks
- [ ] T043 [US3] Run full backend CI (`ruff check`, `pyright`, `pytest`) to verify all US3 consolidations preserve existing behavior
- [ ] T044 [US3] Run full frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) to verify all US3 consolidations preserve existing behavior
- [ ] T045 [US3] Commit all US3 changes using `refactor: consolidate duplicated logic across backend and frontend` commit message

**Checkpoint**: User Story 3 complete — each piece of logic exists in exactly one place, CI green, all behavior preserved

---

## Phase 6: User Story 4 — Delete Stale and Irrelevant Tests (Priority: P2)

**Goal**: Remove test files and cases covering deleted or refactored functionality, tests that over-mock internals and no longer validate real behavior, tests for code paths that no longer exist, and leftover test artifacts

**Independent Test**: Run the full test suite after removals — all remaining tests must pass. Removed tests must reference code paths or functionality confirmed to no longer exist.

### Implementation for User Story 4

- [ ] T046 [P] [US4] Remove stale backend unit test files in backend/tests/unit/ — identify test files that import or reference functions, classes, or modules that no longer exist in backend/src/
- [ ] T047 [P] [US4] Remove stale backend unit test cases within files in backend/tests/unit/ — identify individual test methods that reference code paths removed in US1 or US2, remove only the stale methods (not entire files if other tests are valid)
- [ ] T048 [P] [US4] Remove tests that over-mock internals in backend/tests/unit/ — identify tests where MagicMock/patch usage is so extensive that the test no longer exercises any real code path, verify the tested functionality still exists, remove if the test provides no real validation
- [ ] T049 [P] [US4] Remove stale integration test files or cases in backend/tests/integration/ — identify tests referencing deleted functionality
- [ ] T050 [P] [US4] Clean up leftover test artifacts in backend/ workspace root — search for mock database files (e.g., MagicMock SQLite files, *.db files in backend/), temporary test output files, or other artifacts not cleaned up by test teardown
- [ ] T051 [P] [US4] Remove stale frontend test files — identify co-located test files (*.test.tsx, *.test.ts) in frontend/src/ that test components, hooks, or utilities removed in US1 or US2
- [ ] T052 [P] [US4] Remove stale frontend test cases within files — identify individual test cases in remaining frontend test files that reference removed functionality, remove only the stale cases
- [ ] T053 [US4] Run full backend CI (`ruff check`, `pyright`, `pytest`) to verify all remaining tests pass after US4 removals
- [ ] T054 [US4] Run full frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) to verify all remaining tests pass after US4 removals
- [ ] T055 [US4] Commit all US4 changes using `chore: delete stale and irrelevant tests and test artifacts` commit message

**Checkpoint**: User Story 4 complete — every remaining test validates current, real behavior, no leftover artifacts, CI green

---

## Phase 7: User Story 5 — General Hygiene and Dependency Cleanup (Priority: P3)

**Goal**: Remove orphaned configs, stale TODO/FIXME/HACK comments tied to completed work, unused dependencies, and unused Docker Compose services or environment variables

**Independent Test**: Run all CI checks and verify no removed configuration causes build, test, or runtime failures. Stale comments verified by confirming referenced work is complete.

### Implementation for User Story 5

- [ ] T056 [P] [US5] Remove stale TODO/FIXME/HACK comments in backend/src/ — cross-reference each comment with completed work items, merged PRs, or resolved issues; remove only comments where the referenced work is confirmed complete; update partially-complete comments to reflect current state
- [ ] T057 [P] [US5] Remove stale TODO/FIXME/HACK comments in frontend/src/ — apply the same cross-referencing approach as T056
- [ ] T058 [P] [US5] Remove unused Python dependencies from backend/pyproject.toml — cross-reference each dependency in the `[project.dependencies]` and `[project.optional-dependencies]` sections against actual import statements in backend/src/ and backend/tests/; remove packages with zero imports; run `pip install` and `pytest` to verify no transitive dependency breakage
- [ ] T059 [P] [US5] Remove unused JavaScript/TypeScript dependencies from frontend/package.json — cross-reference each package in `dependencies` and `devDependencies` against actual import statements in frontend/src/ and frontend/e2e/; remove packages with zero imports; run `npm install` and `npm run build` to verify no breakage
- [ ] T060 [P] [US5] Clean up Docker Compose configuration in docker-compose.yml — identify unused services, orphaned environment variables referencing deleted features, and unnecessary volume mounts; remove them and verify remaining services start correctly
- [ ] T061 [P] [US5] Remove orphaned configuration or migration files — search for config files, migration SQL files in backend/src/migrations/, or other configuration entries that reference deleted features; verify dynamically loaded migrations are not removed (cross-reference T003 protected-code list)
- [ ] T062 [P] [US5] Clean up stale environment variable references in .env.example — identify variables that reference deleted features or services no longer used, remove them
- [ ] T063 [US5] Run full backend CI (`ruff check`, `pyright`, `pytest`) to verify all US5 changes pass
- [ ] T064 [US5] Run full frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) to verify all US5 changes pass
- [ ] T065 [US5] Commit all US5 changes using `chore: general hygiene and dependency cleanup` commit message

**Checkpoint**: User Story 5 complete — repository configuration accurately reflects the current state of the project, CI green

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, public API contract verification, and PR summary generation

- [ ] T066 Run full backend CI suite (`ruff check`, `pyright`, `pytest`) — confirm all checks pass with zero failures
- [ ] T067 [P] Run full frontend CI suite (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) — confirm all checks pass with zero failures
- [ ] T068 [P] Verify no public API contracts were altered — diff route definitions in backend/src/api/ (route paths and HTTP methods) and response models in backend/src/models/ against the pre-cleanup baseline from T001; confirm zero changes to public endpoint paths or request/response shapes consumed by the frontend
- [ ] T069 [P] Verify codebase line count decreased — compare total line counts (backend/src/, frontend/src/) before and after cleanup to confirm net reduction
- [ ] T070 [P] Verify no dynamically loaded code was removed — cross-reference all deleted files and functions against the protected-code list from T003; confirm zero violations
- [ ] T071 Generate categorized PR summary — create a categorized description covering every change made across all five cleanup categories, explaining why each piece of code was identified as dead, stale, or duplicated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — analysis needs baseline and protected-code list — BLOCKS all cleanup work
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — dead code removal uses analysis reports
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — shim removal uses analysis reports; can run in parallel with US1 (different code patterns)
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion — consolidation is easier after dead code and shims are removed
- **User Story 4 (Phase 6)**: Depends on US1 and US2 completion — stale tests reference code removed in US1/US2
- **User Story 5 (Phase 7)**: Depends on US1 and US2 completion — dependency analysis is more accurate after dead code removal
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Can run in parallel with US1 (different files/patterns)
- **User Story 3 (P2)**: Should start after US1 and US2 — dead code removal reduces duplication analysis scope
- **User Story 4 (P2)**: Should start after US1 and US2 — stale test identification depends on knowing what code was removed
- **User Story 5 (P3)**: Should start after US1 and US2 — dependency and config analysis is more accurate post-cleanup

### Within Each User Story

- Analysis/identification before removal/refactoring
- Backend changes before frontend changes (or in parallel when files differ)
- Auto-fixable issues (linter --fix) before manual removals
- All removals/refactors before CI validation
- CI validation before commit

### Parallel Opportunities

- T001 (backend baseline) and T002 (frontend baseline) can run in parallel — different directories
- T004–T012 (Foundational analysis tasks) are all marked [P] — all scan different files/aspects
- T013–T015 (auto-fix linter issues) can run in parallel with T016–T025 (manual removals) — auto-fixes target different issue classes
- US1 and US2 can proceed in parallel — different code patterns (dead code vs. shims)
- T037–T042 (US3 consolidation tasks) can run in parallel — each targets different file sets
- T046–T052 (US4 stale test tasks) can run in parallel — each targets different test directories
- T056–T062 (US5 hygiene tasks) can run in parallel — each targets different config/comment areas
- T066–T070 (Polish verification tasks) can run in parallel — independent validation checks

---

## Parallel Example: Foundational Analysis

```bash
# Launch all analysis tasks in parallel (different files/aspects):
Task: T004 "Run ruff unused-code analysis on backend/src/"
Task: T005 "Run eslint unused-vars analysis on frontend/src/"
Task: T006 "Search backend for backwards-compatibility patterns"
Task: T007 "Search frontend for backwards-compatibility patterns"
Task: T008 "Identify near-duplicate functions in backend services"
Task: T009 "Identify near-duplicate types in frontend"
Task: T010 "Scan for stale TODO/FIXME/HACK comments"
Task: T011 "Cross-reference backend dependencies against imports"
Task: T012 "Cross-reference frontend dependencies against imports"
```

## Parallel Example: User Story 1 (Dead Code Removal)

```bash
# Launch auto-fix tasks in parallel (different directories):
Task: T013 "Auto-fix unused imports in backend/src/"
Task: T014 "Remove unused variables in backend/src/"
Task: T015 "Auto-fix unused imports in frontend/src/"

# Then launch manual removal tasks in parallel (different files):
Task: T016 "Remove unused functions in backend/src/services/"
Task: T017 "Remove unused functions in backend/src/api/"
Task: T018 "Remove unused Pydantic models in backend/src/models/"
Task: T019 "Remove unused API route handlers in backend/src/api/"
Task: T020 "Remove unused React components in frontend/src/components/"
Task: T021 "Remove unused hooks in frontend/src/hooks/"
Task: T022 "Remove unused utility functions in frontend/src/utils/"
Task: T023 "Remove unused TypeScript types in frontend/src/types/"
```

## Parallel Example: User Story 5 (General Hygiene)

```bash
# Launch all hygiene tasks in parallel (different files/aspects):
Task: T056 "Remove stale comments in backend/"
Task: T057 "Remove stale comments in frontend/"
Task: T058 "Remove unused Python dependencies from pyproject.toml"
Task: T059 "Remove unused JS dependencies from package.json"
Task: T060 "Clean up Docker Compose configuration"
Task: T061 "Remove orphaned config/migration files"
Task: T062 "Clean up stale .env.example entries"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (baseline CI, protected-code list)
2. Complete Phase 2: Foundational (full analysis catalog)
3. Complete Phase 3: User Story 1 (dead code removal)
4. Complete Phase 4: User Story 2 (shim and legacy branch removal)
5. **STOP and VALIDATE**: Run full CI, verify no API contract changes, verify protected code intact
6. This delivers the highest-impact cleanup — dead code and shims gone

### Incremental Delivery

1. Complete Setup + Foundational → Analysis complete
2. Add User Story 1 → Dead code removed → Validate CI (MVP Phase 1!)
3. Add User Story 2 → Shims removed → Validate CI (MVP Complete!)
4. Add User Story 3 → Logic consolidated → Validate CI
5. Add User Story 4 → Stale tests removed → Validate CI
6. Add User Story 5 → Hygiene complete → Validate CI
7. Polish → Final verification + PR summary → Release
8. Each story adds cleanup value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (dead code — backend focus)
   - Developer B: User Story 2 (shims — can work in parallel with US1)
3. After US1 + US2 merge:
   - Developer A: User Story 3 (consolidation)
   - Developer B: User Story 4 (stale tests)
   - Developer C: User Story 5 (hygiene)
4. All developers: Polish phase

---

## Summary

- **Total tasks**: 71
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 9 tasks
- **Phase 3 (US1 — Dead Code Removal)**: 16 tasks
- **Phase 4 (US2 — Shims & Legacy Branches)**: 8 tasks
- **Phase 5 (US3 — Consolidate Duplicates)**: 9 tasks
- **Phase 6 (US4 — Stale Tests)**: 10 tasks
- **Phase 7 (US5 — General Hygiene)**: 10 tasks
- **Phase 8 (Polish)**: 6 tasks
- **Parallel opportunities**: 8 identified (Setup, Foundational, US1 auto-fix, US1 manual, US1/US2 cross-story, US3, US4, US5, Polish)
- **Independent test criteria**: Each user story has a clear CI-based independent test defined
- **Suggested MVP scope**: User Stories 1 + 2 (Dead Code + Shims — Phases 1–4, 36 tasks)
- **Format validation**: ✅ All 71 tasks follow checklist format (checkbox, ID, labels, file paths)
- **Commit convention**: `chore:` for dead code/test removal (US1, US2, US4, US5), `refactor:` for consolidation (US3)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable via CI
- **Dynamic loading caution**: Tasks T003 and T070 establish and verify the protected-code list — migration files in backend/src/migrations/ are discovered by filename pattern, and agent files in .github/agents/ are discovered by regex in backend/src/services/github_projects/service.py
- **No API contract changes**: Tasks T019 and T068 explicitly verify that no public route paths or request/response shapes consumed by the frontend are altered
- Backend follows existing FastAPI + aiosqlite + Pydantic v2 patterns
- Frontend follows existing React 18 + TanStack Query v5 + Tailwind CSS 3.4 + Shadcn UI patterns
- All CI checks must pass after each user story: `ruff check`, `pyright`, `pytest` (backend); `eslint`, `tsc --noEmit`, `vitest run`, `vite build` (frontend)
- Commit convention: `refactor:` for consolidation changes, `chore:` for dead code and test removal
