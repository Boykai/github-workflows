# Tasks: Codebase Cleanup to Reduce Technical Debt

**Input**: Design documents from `/specs/016-codebase-cleanup/`
**Prerequisites**: spec.md (user stories with priorities P1–P5)

**Tests**: No new tests are requested. Existing CI suite (`ruff`, `pyright`, `pytest`, `eslint`, `tsc`, `vitest`, `vite build`) serves as the regression safety net.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each cleanup category.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`
- **Infrastructure**: `docker-compose.yml`, `.env.example`
- **Scripts**: `scripts/`

---

## Phase 1: Setup (Baseline and Safety Net)

**Purpose**: Establish a clean CI baseline and capture metrics so every subsequent cleanup can be verified against the starting state.

- [ ] T001 Run full backend CI suite (`ruff check`, `pyright`, `pytest`) and confirm all checks pass as the pre-cleanup baseline
- [ ] T002 [P] Run full frontend CI suite (`eslint`, `tsc --noEmit`, `vitest run`, `vite build`) and confirm all checks pass as the pre-cleanup baseline
- [ ] T003 [P] Capture pre-cleanup line count metrics for `backend/src/`, `backend/tests/`, and `frontend/src/` using `find | xargs wc -l`
- [ ] T004 [P] Snapshot the public API route registry by extracting all `@router` decorator paths from `backend/src/api/*.py` into a reference list for post-cleanup regression comparison

---

## Phase 2: Foundational (Audit and Inventory)

**Purpose**: Systematic audit of the entire codebase to build the removal/refactor candidate list. MUST complete before any cleanup work begins.

**⚠️ CRITICAL**: No cleanup changes should be made until audits are complete — audits inform all subsequent phases.

- [ ] T005 Audit backend for unused imports and variables by running `ruff check --select F401,F841 backend/src/` and recording all flagged locations
- [ ] T006 [P] Audit frontend for unused imports, variables, and declarations by running `eslint --rule 'no-unused-vars: warn' frontend/src/` and recording all flagged locations
- [ ] T007 [P] Audit for dynamic loading patterns in `backend/src/services/database.py` (migration discovery), `backend/src/services/github_projects/service.py` (agent file discovery), and `backend/src/main.py` (plugin loading) to build a "do-not-remove" safelist
- [ ] T008 [P] Audit for commented-out code blocks (multi-line `#`-prefixed logic, not docstrings/documentation) across all files in `backend/src/` and `frontend/src/`
- [ ] T009 [P] Audit for legacy conditional patterns (`if old_format`, `if legacy`, compatibility shims, adapter/polyfill code) across `backend/src/` and `frontend/src/`
- [ ] T010 [P] Audit for near-duplicate functions and helpers across `backend/src/services/`, `backend/src/api/`, `backend/src/models/`, and `frontend/src/hooks/`, `frontend/src/components/`, `frontend/src/services/api.ts`
- [ ] T011 [P] Audit for stale TODO, FIXME, and HACK comments across the entire codebase and classify each as tied to completed work (remove) or genuine future work (retain)
- [ ] T012 [P] Audit backend test files in `backend/tests/unit/` and `backend/tests/integration/` for tests covering deleted/refactored functionality, over-mocked internals, or nonexistent code paths
- [ ] T013 [P] Audit for unused dependencies in `backend/pyproject.toml` by cross-referencing each listed package against actual imports in `backend/src/`
- [ ] T014 [P] Audit for unused dependencies in `frontend/package.json` by cross-referencing each listed package against actual imports in `frontend/src/`
- [ ] T015 [P] Audit `docker-compose.yml` and `.env.example` for unused services, environment variables, or configuration entries referencing deleted features
- [ ] T016 [P] Audit for leftover test artifacts (e.g., `MagicMock` database files) in the repository root and `backend/` workspace root

**Checkpoint**: Audit complete — all candidate lists compiled for each cleanup category. Cleanup phases can now proceed.

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Eliminate all verified-unused code paths, unreferenced functions, dead imports, commented-out logic, and unused declarations across the entire codebase.

**Independent Test**: Run full CI suite (`ruff`, `pyright`, `pytest`, `eslint`, `tsc`, `vitest`, `vite build`) after each removal batch. All checks must pass with no regressions. Cross-check against the dynamic-loading safelist from T007 before every removal.

### Backend Dead Code Removal

- [ ] T017 [P] [US1] Remove all unused imports flagged by `ruff` (F401) across all files in `backend/src/api/`, `backend/src/services/`, `backend/src/models/`, and `backend/src/middleware/`
- [ ] T018 [P] [US1] Remove all unused variables flagged by `ruff` (F841) across all files in `backend/src/`
- [ ] T019 [US1] Remove unused functions and methods in `backend/src/services/ai_agent.py`, `backend/src/services/github_projects/service.py`, and `backend/src/services/copilot_polling/*.py` that are defined but never imported or called (verify against safelist from T007)
- [ ] T020 [P] [US1] Remove unused functions and methods in `backend/src/services/cleanup_service.py`, `backend/src/services/session_store.py`, `backend/src/services/settings_store.py`, and `backend/src/services/cache.py`
- [ ] T021 [P] [US1] Remove unused functions and methods in `backend/src/api/chat.py`, `backend/src/api/board.py`, `backend/src/api/projects.py`, `backend/src/api/tasks.py`, and `backend/src/api/workflow.py`
- [ ] T022 [P] [US1] Remove unused Pydantic model definitions in `backend/src/models/chat.py`, `backend/src/models/board.py`, `backend/src/models/task.py`, `backend/src/models/workflow.py`, and `backend/src/models/recommendation.py`
- [ ] T023 [US1] Remove unused route handlers in `backend/src/api/*.py` that have no frontend callers (check `frontend/src/services/api.ts`) and no test coverage — without altering any active route paths or response shapes
- [ ] T024 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) in all files under `backend/src/`
- [ ] T025 [US1] Run backend CI (`ruff check`, `ruff format --check`, `pyright`, `pytest`) and confirm all checks pass after backend dead code removal

### Frontend Dead Code Removal

- [ ] T026 [P] [US1] Remove unused imports, variables, and type declarations flagged by `eslint` across all files in `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/pages/`, and `frontend/src/services/`
- [ ] T027 [P] [US1] Remove unused React components in `frontend/src/components/` that are defined but never imported by any page or parent component
- [ ] T028 [P] [US1] Remove unused hooks in `frontend/src/hooks/` that are defined but never imported by any component or page
- [ ] T029 [P] [US1] Remove unused utility functions in `frontend/src/utils/formatTime.ts`, `frontend/src/utils/generateId.ts`, `frontend/src/lib/utils.ts`, and `frontend/src/lib/commands/` that are defined but never called
- [ ] T030 [P] [US1] Remove unused TypeScript type definitions and interfaces in `frontend/src/types/index.ts`
- [ ] T031 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) in all files under `frontend/src/`
- [ ] T032 [US1] Run frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `npx vite build`) and confirm all checks pass after frontend dead code removal

**Checkpoint**: All dead code removed. CI passes. Codebase is leaner and every remaining function/component/type is actively used.

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims and Legacy Branches (Priority: P2)

**Goal**: Remove all compatibility layers, polyfills, adapter code, and dead conditional branches supporting deprecated data shapes or migration-period aliases.

**Independent Test**: Search for legacy conditional patterns (`if old_format`, `if legacy`, adapter wrappers) and confirm zero matches post-cleanup. Full CI suite passes.

### Backend Shim Removal

- [ ] T033 [US2] Remove backwards-compatibility shims, adapter code, and legacy conditional branches (e.g., `if old_format:`, `if legacy:`, deprecated alias handlers) identified in audit T009 from `backend/src/services/` and `backend/src/api/`
- [ ] T034 [P] [US2] Remove deprecated data shape adapters and migration-period alias handling from `backend/src/models/` (Pydantic model compatibility layers, field aliases for old formats)
- [ ] T035 [US2] Run backend CI (`ruff check`, `pyright`, `pytest`) and confirm all checks pass after shim removal

### Frontend Shim Removal

- [ ] T036 [US2] Remove backwards-compatibility shims, polyfills, and adapter code identified in audit T009 from `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/services/api.ts`, and `frontend/src/types/index.ts`
- [ ] T037 [US2] Run frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `npx vite build`) and confirm all checks pass after shim removal

**Checkpoint**: All backwards-compatibility code removed. Only current-behavior code paths remain. CI passes.

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P3)

**Goal**: Merge near-duplicate functions, helpers, service methods, data model definitions, and test patterns into single shared implementations.

**Independent Test**: For each consolidation, verify all call sites are updated and the full CI suite passes. Confirm behavioral equivalence via the existing test suite.

### Backend Consolidation

- [ ] T038 [US3] Identify and merge near-duplicate helper functions and service methods across `backend/src/services/ai_agent.py`, `backend/src/services/github_projects/service.py`, `backend/src/services/copilot_polling/*.py`, and `backend/src/services/workflow_orchestrator/*.py` into single shared implementations
- [ ] T039 [P] [US3] Consolidate overlapping Pydantic model definitions across `backend/src/models/chat.py`, `backend/src/models/board.py`, `backend/src/models/task.py`, `backend/src/models/workflow.py`, and `backend/src/models/agent.py` into unified models where appropriate
- [ ] T040 [P] [US3] Consolidate duplicated API client logic and response-handling patterns across `backend/src/api/*.py` route handlers
- [ ] T041 [US3] Refactor copy-pasted test setup patterns in `backend/tests/unit/` into shared helpers in `backend/tests/helpers/factories.py` and `backend/tests/helpers/mocks.py`
- [ ] T042 [US3] Run backend CI (`ruff check`, `pyright`, `pytest`) and confirm all checks pass after backend consolidation

### Frontend Consolidation

- [ ] T043 [US3] Identify and merge near-duplicate utility functions and hook logic across `frontend/src/hooks/`, `frontend/src/components/`, and `frontend/src/services/api.ts`
- [ ] T044 [P] [US3] Consolidate overlapping TypeScript type definitions and interfaces in `frontend/src/types/index.ts` into unified types
- [ ] T045 [P] [US3] Consolidate duplicated component patterns (e.g., modal/dialog patterns, form handling, loading states) across `frontend/src/components/board/`, `frontend/src/components/chat/`, and `frontend/src/components/settings/`
- [ ] T046 [US3] Run frontend CI (`eslint`, `tsc --noEmit`, `vitest run`, `npx vite build`) and confirm all checks pass after frontend consolidation

**Checkpoint**: All identified duplications consolidated. Single source of truth for shared logic. CI passes.

---

## Phase 6: User Story 4 — Delete Stale and Irrelevant Tests (Priority: P4)

**Goal**: Remove tests that cover deleted functionality, over-mock internals, validate nonexistent code paths, or are leftover artifacts — so the test suite accurately reflects the current system.

**Independent Test**: Run full test suite before and after removal. Confirm no valid coverage is lost (all remaining tests pass, no new warnings).

### Backend Stale Test Removal

- [ ] T047 [US4] Remove stale backend test files and individual test cases in `backend/tests/unit/` that cover deleted or refactored functionality identified in audit T012
- [ ] T048 [P] [US4] Remove backend tests in `backend/tests/unit/` that over-mock internals and no longer validate real behavior (e.g., tests mocking database calls that have been restructured)
- [ ] T049 [P] [US4] Remove stale backend integration test cases in `backend/tests/integration/` covering nonexistent code paths or deleted features

### Frontend Stale Test Removal

- [ ] T050 [P] [US4] Remove stale frontend test files and test cases (`.test.tsx` / `.test.ts`) in `frontend/src/` that cover deleted or refactored components, hooks, or utilities

### Test Artifact Cleanup

- [ ] T051 [US4] Remove leftover test artifacts — delete `MagicMock` database files in the repository root (files matching `<MagicMock name=*>` pattern) and any other test-generated temporary files
- [ ] T052 [US4] Run full CI suite (backend + frontend) and confirm all checks pass and no valid test coverage is lost

**Checkpoint**: Test suite is clean and trustworthy. All remaining tests validate real, current behavior. CI passes.

---

## Phase 7: User Story 5 — General Hygiene and Dependency Cleanup (Priority: P5)

**Goal**: Remove orphaned configurations, stale comments, unused dependencies, and unused infrastructure definitions to ensure the project accurately reflects what is actually in use.

**Independent Test**: Build, lint, and test suites all pass after each removal. Dependency graph is accurate (no missing transitive dependencies).

### Stale Comment Removal

- [ ] T053 [P] [US5] Remove stale TODO, FIXME, and HACK comments tied to completed work (identified in audit T011) across `backend/src/` — retain comments referencing genuine future work
- [ ] T054 [P] [US5] Remove stale TODO, FIXME, and HACK comments tied to completed work (identified in audit T011) across `frontend/src/` — retain comments referencing genuine future work

### Dependency Cleanup

- [ ] T055 [US5] Remove unused Python dependencies from `backend/pyproject.toml` (identified in audit T013) and verify `pip install` and `pytest` still succeed
- [ ] T056 [P] [US5] Remove unused npm dependencies from `frontend/package.json` (identified in audit T014), run `npm install`, and verify `vitest run` and `vite build` still succeed

### Configuration and Infrastructure Cleanup

- [ ] T057 [P] [US5] Remove orphaned migration files in `backend/src/migrations/` that reference deleted features or tables (identified in audit T015), verifying against the dynamic-loading safelist from T007
- [ ] T058 [P] [US5] Remove unused Docker Compose services, environment variables, or volume definitions in `docker-compose.yml` and stale entries in `.env.example` (identified in audit T015)
- [ ] T059 [P] [US5] Remove orphaned configuration files or stale config entries in `backend/src/config.py`, `.pre-commit-config.yaml`, `frontend/eslint.config.js`, and `frontend/tsconfig.json` referencing deleted features
- [ ] T060 [US5] Run full CI suite (backend + frontend) and confirm all checks pass after hygiene cleanup

**Checkpoint**: All orphaned configs, stale comments, and unused dependencies removed. Project configuration and dependency graph accurately reflect active usage. CI passes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, metrics comparison, and PR documentation.

- [ ] T061 Run full CI suite end-to-end: `ruff check`, `ruff format --check`, `pyright`, `pytest` (backend) and `eslint`, `tsc --noEmit`, `vitest run`, `vite build` (frontend)
- [ ] T062 [P] Compare post-cleanup public API route registry against the pre-cleanup snapshot from T004 and confirm zero changes to route paths, request shapes, or response shapes
- [ ] T063 [P] Capture post-cleanup line count metrics for `backend/src/`, `backend/tests/`, and `frontend/src/` and compare against pre-cleanup baseline from T003 to verify material reduction
- [ ] T064 Generate categorized PR description summarizing all changes made across the five cleanup categories, explaining why each piece of code was identified as dead, stale, or duplicated
- [ ] T065 Post a follow-up comment on the PR summarizing cleanup results (total lines removed, changes per category, CI verification status)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all cleanup phases
- **User Stories (Phase 3–7)**: All depend on Foundational phase (audits) completion
  - User stories should proceed sequentially in priority order (P1 → P2 → P3 → P4 → P5) because later stories build on changes from earlier stories
  - P1 (dead code removal) should complete before P4 (stale test removal) since removing dead code reveals stale tests
- **Polish (Phase 8)**: Depends on all cleanup phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2, but benefits from P1 completion (dead code removal may expose hidden shims)
- **User Story 3 (P3)**: Can start after Phase 2 — independently testable, but should follow P1/P2 to avoid consolidating code that will be removed
- **User Story 4 (P4)**: Should follow P1 (dead code removal reveals which tests are stale) — direct dependency on US1
- **User Story 5 (P5)**: Can start after Phase 2 — independently testable, but benefits from all prior cleanups being complete

### Within Each User Story

- Backend changes before frontend changes (within each category)
- Run CI after each batch of changes within a story
- Commit with appropriate conventional commit prefix (`chore:` for removals, `refactor:` for consolidations)

### Parallel Opportunities

- All audit tasks (T005–T016) marked [P] can run in parallel within Phase 2
- Within US1: Backend dead code tasks (T017–T024) marked [P] can run in parallel; frontend tasks (T026–T031) marked [P] can run in parallel
- Within US3: Backend model consolidation (T039) and API consolidation (T040) can run in parallel; frontend type consolidation (T044) and component consolidation (T045) can run in parallel
- Within US4: All [P]-marked test removal tasks (T048–T050) can run in parallel
- Within US5: Comment removal (T053–T054), dependency cleanup (T055–T056), and config cleanup (T057–T059) can all run in parallel

---

## Parallel Example: Phase 2 Audits

```bash
# Launch all audit tasks together:
Task: "Audit backend unused imports/variables via ruff (T005)"
Task: "Audit frontend unused imports/variables via eslint (T006)"
Task: "Audit dynamic loading patterns for safelist (T007)"
Task: "Audit commented-out code blocks (T008)"
Task: "Audit legacy conditional patterns (T009)"
Task: "Audit near-duplicate functions (T010)"
Task: "Audit stale TODO/FIXME/HACK comments (T011)"
Task: "Audit stale tests (T012)"
Task: "Audit unused backend dependencies (T013)"
Task: "Audit unused frontend dependencies (T014)"
Task: "Audit docker-compose and env config (T015)"
Task: "Audit leftover test artifacts (T016)"
```

## Parallel Example: User Story 1 Backend

```bash
# Launch all backend dead code removal tasks together:
Task: "Remove unused imports in backend (T017)"
Task: "Remove unused variables in backend (T018)"
Task: "Remove unused Pydantic models (T022)"
Task: "Remove commented-out code in backend (T024)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline CI + metrics)
2. Complete Phase 2: Foundational (full audit)
3. Complete Phase 3: User Story 1 — Remove Dead Code
4. **STOP and VALIDATE**: Run full CI, compare route registry, measure line reduction
5. This alone delivers the highest-value cleanup (largest reduction in cognitive load and code volume)

### Incremental Delivery

1. Complete Setup + Foundational → Audit inventory ready
2. Add User Story 1 (Dead Code) → CI green → Commit with `chore:` prefix (MVP!)
3. Add User Story 2 (Shims) → CI green → Commit with `chore:` prefix
4. Add User Story 3 (Consolidation) → CI green → Commit with `refactor:` prefix
5. Add User Story 4 (Stale Tests) → CI green → Commit with `chore:` prefix
6. Add User Story 5 (Hygiene) → CI green → Commit with `chore:` prefix
7. Each story adds cleanup value without breaking previous stories

### Sequential Strategy (Recommended for This Feature)

Unlike feature development where stories can be parallelized, cleanup is best done sequentially:

1. Team completes Setup + Foundational together
2. P1 first — dead code removal creates the cleanest baseline for all subsequent work
3. P2 next — shim removal is easier once dead code is gone
4. P3 next — consolidation works on the reduced, shim-free codebase
5. P4 next — stale test removal is informed by all prior code changes
6. P5 last — hygiene cleanup catches any remaining orphaned artifacts

---

## Notes

- [P] tasks = different files, no dependencies on other in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and verifiable via CI
- Use `chore:` commit prefix for dead code/test removal (US1, US2, US4, US5)
- Use `refactor:` commit prefix for consolidation changes (US3)
- NEVER remove code referenced by dynamic loading (migration discovery in `backend/src/services/database.py`, agent discovery in `backend/src/services/github_projects/service.py`) without explicit verification
- The `MagicMock` database files in the repo root are confirmed test artifacts from T016 and are safe to delete
- Stop at any checkpoint to validate independently
- Avoid: removing actively-used code, altering public API contracts, consolidating intentionally-different implementations
