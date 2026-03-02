# Tasks: Repository-Wide Codebase Cleanup

**Input**: Design documents from `/specs/016-repo-wide-cleanup/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Not explicitly requested — no new test tasks are generated. Existing tests must continue to pass after each cleanup change. Stale tests are removed as part of User Story 2 (US2).

**Organization**: Tasks are grouped by user story (cleanup category) to enable independent implementation and testing of each category. Each user story maps to one of the five cleanup categories described in the specification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/`
- **Docker/Infra config**: repository root (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`)
- **Dependency manifests**: `backend/pyproject.toml`, `frontend/package.json`
- **Migrations**: `backend/src/migrations/`
- **Scripts**: `scripts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline — confirm all CI checks pass before any cleanup changes are made. Record line counts for SC-004 measurement.

- [ ] T001 Record pre-cleanup baseline: run `find backend/src frontend/src -name '*.py' -o -name '*.ts' -o -name '*.tsx' | xargs wc -l` and save total non-blank, non-comment line count for before/after comparison
- [ ] T002 Verify backend linting passes: run `cd backend && ruff check src tests && ruff format --check src tests`
- [ ] T003 Verify backend type checking passes: run `cd backend && pyright`
- [ ] T004 Verify backend tests pass: run `cd backend && pytest -v`
- [ ] T005 Verify frontend linting passes: run `cd frontend && npm run lint`
- [ ] T006 Verify frontend type checking passes: run `cd frontend && npx tsc --noEmit`
- [ ] T007 Verify frontend tests pass: run `cd frontend && npm test`
- [ ] T008 Verify frontend production build passes: run `cd frontend && npm run build`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure needed — all changes target existing files. This phase validates awareness of dynamic loading patterns that must NOT be removed.

**⚠️ CRITICAL**: Before removing any code, confirm it is not loaded dynamically.

- [ ] T009 Audit dynamic loading patterns in backend: review `backend/src/services/database.py` migration discovery, `backend/src/services/github_projects/service.py` agent discovery (`*.agent.md`), and any string-based plugin loading — document which files/functions must be preserved
- [ ] T010 Audit dynamic loading patterns in frontend: review lazy-loaded routes, dynamic imports in `frontend/src/App.tsx`, and any code-split entry points — document which components must be preserved
- [ ] T011 Verify no public API contracts will be altered: review all route registrations in `backend/src/api/__init__.py` and document current route paths and response shapes that must remain unchanged

**Checkpoint**: Baseline validated, dynamic loading audit complete — cleanup work can now begin

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all dead code paths, unused imports, unreferenced functions/components, commented-out logic blocks, and unused type definitions across backend and frontend.

**Independent Test**: Run all CI checks (`ruff`, `pyright`, `pytest`, `eslint`, `tsc`, `vitest`, `vite build`) after removal. All must pass with no public API contract changes.

### Backend Dead Code Removal

- [ ] T012 [P] [US1] Run `ruff check --select F401 backend/src/` to identify and remove all unused imports across `backend/src/**/*.py`
- [ ] T013 [P] [US1] Run `ruff check --select F841 backend/src/` to identify and remove all unused local variables across `backend/src/**/*.py`
- [ ] T014 [P] [US1] Scan for unused functions and methods in `backend/src/services/` — remove functions that are defined but never imported or called by any other module (cross-reference with `grep -r` for all call sites)
- [ ] T015 [P] [US1] Scan for unused functions and methods in `backend/src/api/` — remove route handler helper functions that are defined but never called (do NOT remove registered route handlers without confirming they have no frontend callers)
- [ ] T016 [P] [US1] Scan for unused Pydantic models in `backend/src/models/` — remove models that are defined but never referenced in API routes, services, or tests (cross-reference with `backend/src/models/__init__.py` re-exports)
- [ ] T017 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) across all files in `backend/src/` — use `grep -rn '^\s*#.*=' backend/src/` and manual review to distinguish commented code from doc comments
- [ ] T018 [P] [US1] Remove unused type definitions and type aliases in `backend/src/models/` and `backend/src/services/`

### Frontend Dead Code Removal

- [ ] T019 [P] [US1] Run `cd frontend && npx eslint --rule '{"no-unused-vars": "error"}' src/` to identify unused imports and variables, then remove them across `frontend/src/**/*.ts` and `frontend/src/**/*.tsx`
- [ ] T020 [P] [US1] Scan for unused React components in `frontend/src/components/` — remove components that are defined but never imported or rendered by any parent component (cross-reference with `grep -r` for all import sites)
- [ ] T021 [P] [US1] Scan for unused hooks in `frontend/src/hooks/` — remove hooks that are defined but never imported or called by any component
- [ ] T022 [P] [US1] Scan for unused utility functions in `frontend/src/utils/` and `frontend/src/lib/` — remove functions that are defined but never imported
- [ ] T023 [P] [US1] Remove commented-out logic blocks (excluding documentation comments) across all files in `frontend/src/`
- [ ] T024 [P] [US1] Remove unused TypeScript type definitions and interfaces in `frontend/src/types/index.ts` — cross-reference each exported type with all import sites across `frontend/src/`
- [ ] T025 [US1] Run full backend CI checks after dead code removal: `cd backend && ruff check src tests && ruff format --check src tests && pyright && pytest -v`
- [ ] T026 [US1] Run full frontend CI checks after dead code removal: `cd frontend && npm run lint && npx tsc --noEmit && npm test && npm run build`

**Checkpoint**: All dead code removed. All CI checks pass. Commit with `chore: remove dead code and unused artifacts across backend and frontend`

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims and Stale Tests (Priority: P2)

**Goal**: Remove compatibility layers, polyfills, adapter code for deprecated API shapes, dead conditional branches, stale test files, over-mocked tests, and leftover test artifacts.

**Independent Test**: All remaining tests pass, no new test failures appear, no public API contracts altered.

### Backwards-Compatibility Shim Removal

- [ ] T027 [P] [US2] Scan `backend/src/` for backwards-compatibility patterns — search for `if old_format`, `if legacy`, `# legacy`, `# deprecated`, `# backwards-compat`, `# compat`, adapter/shim functions, and migration-period aliases. Remove confirmed dead branches
- [ ] T028 [P] [US2] Scan `frontend/src/` for backwards-compatibility patterns — search for polyfills, adapter code, deprecated API shape handling, and conditional branches for old data formats. Remove confirmed dead branches
- [ ] T029 [P] [US2] Review `backend/src/models/` for deprecated model aliases or compatibility re-exports in `backend/src/models/__init__.py` — remove any that are no longer referenced

### Stale Test Removal

- [ ] T030 [P] [US2] Audit `backend/tests/unit/` for test files covering deleted or refactored functionality — remove test files and cases that test code paths which no longer exist
- [ ] T031 [P] [US2] Audit `backend/tests/unit/` for tests that over-mock internals — identify tests using excessive `MagicMock`/`patch` that no longer validate real behavior and remove them
- [ ] T032 [P] [US2] Audit `frontend/src/` for test files (`.test.tsx`, `.test.ts`) covering deleted or refactored components — remove stale test cases
- [ ] T033 [P] [US2] Audit `backend/tests/integration/` for integration tests covering deleted functionality — remove stale integration tests

### Test Artifact Cleanup

- [ ] T034 [US2] Delete all leftover MagicMock database files from the repository root: remove all `<MagicMock name='get_settings().database_path' id='*'>` files from `/` (8 files currently present)
- [ ] T035 [US2] Add `.gitignore` entry to prevent future MagicMock file leaks: add `<MagicMock*` pattern to root `.gitignore`
- [ ] T036 [US2] Run full backend CI checks after shim and stale test removal: `cd backend && ruff check src tests && ruff format --check src tests && pyright && pytest -v`
- [ ] T037 [US2] Run full frontend CI checks after shim and stale test removal: `cd frontend && npm run lint && npx tsc --noEmit && npm test && npm run build`

**Checkpoint**: All shims removed, stale tests cleaned up, test artifacts deleted. All CI checks pass. Commit with `chore: remove backwards-compatibility shims and stale tests`

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P3)

**Goal**: Merge near-duplicate functions, helpers, service methods, test patterns, and overlapping model definitions into single implementations.

**Independent Test**: All CI checks pass after consolidation. All callers produce identical results as before.

### Backend Consolidation

- [ ] T038 [P] [US3] Scan `backend/src/services/` for near-duplicate helper functions — identify functions with similar logic across service files (e.g., HTTP request helpers, response parsing, error handling patterns) and consolidate into shared utilities in `backend/src/utils.py` or a new `backend/src/services/common.py`
- [ ] T039 [P] [US3] Scan `backend/src/models/` for overlapping Pydantic model definitions — identify models with near-identical field sets and consolidate using inheritance or shared base models
- [ ] T040 [P] [US3] Scan `backend/src/api/` for duplicated request validation, error handling, or response formatting patterns — consolidate into shared helpers in `backend/src/dependencies.py` or `backend/src/utils.py`
- [ ] T041 [P] [US3] Refactor copy-pasted test patterns in `backend/tests/unit/` — identify repeated setup/teardown logic, mock configurations, and assertion patterns, then consolidate using shared helpers in `backend/tests/helpers/factories.py` and `backend/tests/helpers/mocks.py`

### Frontend Consolidation

- [ ] T042 [P] [US3] Scan `frontend/src/services/api.ts` for duplicated API client logic — identify repeated request patterns (headers, error handling, response parsing) and consolidate into shared helper functions
- [ ] T043 [P] [US3] Scan `frontend/src/hooks/` for duplicated hook logic — identify hooks with similar query/mutation patterns and consolidate shared logic into utility hooks or helper functions
- [ ] T044 [P] [US3] Scan `frontend/src/types/index.ts` for overlapping TypeScript type definitions — identify types with near-identical shapes and consolidate using intersection types, generics, or shared base types
- [ ] T045 [P] [US3] Scan `frontend/src/components/` for duplicated component patterns — identify near-duplicate UI logic across components and consolidate into shared sub-components or utility functions
- [ ] T046 [US3] Run full backend CI checks after consolidation: `cd backend && ruff check src tests && ruff format --check src tests && pyright && pytest -v`
- [ ] T047 [US3] Run full frontend CI checks after consolidation: `cd frontend && npm run lint && npx tsc --noEmit && npm test && npm run build`

**Checkpoint**: Duplicated logic consolidated. All CI checks pass. Commit with `refactor: consolidate duplicated logic across backend and frontend`

---

## Phase 6: User Story 4 — General Hygiene Cleanup (Priority: P4)

**Goal**: Remove orphaned configurations, stale comments, unused dependencies, and unused infrastructure definitions.

**Independent Test**: All CI checks pass, dependency installation succeeds, no configuration references deleted features.

### Stale Comment Cleanup

- [ ] T048 [P] [US4] Scan `backend/src/` for stale `TODO`, `FIXME`, and `HACK` comments — review each comment, remove those tied to verifiably completed work (cross-reference with closed GitHub issues or merged PRs), preserve comments referencing open issues or future plans
- [ ] T049 [P] [US4] Scan `frontend/src/` for stale `TODO`, `FIXME`, and `HACK` comments — apply the same review criteria as T048

### Orphaned Configuration Cleanup

- [ ] T050 [P] [US4] Review `backend/src/migrations/` for orphaned migration files referencing deleted features — verify each migration file (001-008) is still relevant; note the duplicate `007_` prefix files (`007_agent_configs.sql` and `007_housekeeping.sql`)
- [ ] T051 [P] [US4] Review `.env.example` for environment variables referencing deleted features or unused services — remove stale entries

### Unused Dependency Removal

- [ ] T052 [P] [US4] Audit `backend/pyproject.toml` for unused Python dependencies — cross-reference each dependency with `grep -r` for import statements across `backend/src/` and `backend/tests/`; remove packages with zero import references; run `cd backend && pip install -e ".[dev]" && pytest -v` to validate
- [ ] T053 [P] [US4] Audit `frontend/package.json` for unused JavaScript dependencies — cross-reference each dependency with `grep -r` for import/require statements across `frontend/src/`; remove packages with zero import references (note: `jsdom` may already be unused since `vitest.config.ts` uses `happy-dom`); run `cd frontend && npm install && npm test && npm run build` to validate

### Infrastructure Cleanup

- [ ] T054 [P] [US4] Review `docker-compose.yml` for unused services, environment variables, or volumes — remove any entries referencing deleted features or unused configurations
- [ ] T055 [P] [US4] Review `backend/Dockerfile` and `frontend/Dockerfile` for stale build steps, unused environment variables, or references to removed dependencies
- [ ] T056 [US4] Run full backend CI checks after hygiene cleanup: `cd backend && ruff check src tests && ruff format --check src tests && pyright && pytest -v`
- [ ] T057 [US4] Run full frontend CI checks after hygiene cleanup: `cd frontend && npm run lint && npx tsc --noEmit && npm test && npm run build`

**Checkpoint**: All general hygiene tasks complete. All CI checks pass. Commit with `chore: clean up stale comments, orphaned configs, and unused dependencies`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all cleanup categories, post-cleanup baseline measurement, and PR summary preparation.

- [ ] T058 Run full backend CI suite: `cd backend && ruff check src tests && ruff format --check src tests && pyright && pytest -v`
- [ ] T059 Run full frontend CI suite: `cd frontend && npm run lint && npx tsc --noEmit && npm test && npm run build`
- [ ] T060 Record post-cleanup line count and compute reduction percentage for SC-004 validation
- [ ] T061 Verify no public API contracts were altered: compare pre-cleanup and post-cleanup route registrations in `backend/src/api/__init__.py` and confirm all route paths and response shapes are identical
- [ ] T062 Verify all commits follow conventional commit convention: audit git log for `refactor:` and `chore:` prefixes on all cleanup commits
- [ ] T063 Prepare categorized PR summary mapping each change to one of the five cleanup categories with rationale for why each piece of code was identified for removal or consolidation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all cleanup work
- **User Stories (Phases 3–6)**: All depend on Foundational phase (dynamic loading audit) completion
  - US1 (dead code) should be done first — removing dead code before consolidation (US3) reduces noise
  - US2 (shims/stale tests) can start after or in parallel with US1
  - US3 (consolidation) benefits from US1 and US2 being complete first
  - US4 (hygiene) is fully independent and can proceed in parallel with any other story
- **Polish (Phase 7)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1 — Dead Code)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P2 — Shims/Stale Tests)**: Can start after Foundational (Phase 2) — independent of US1 but benefits from running after
- **US3 (P3 — Consolidation)**: Should start after US1 and US2 — consolidation is easier when dead code is already removed
- **US4 (P4 — Hygiene)**: Can start after Foundational (Phase 2) — fully independent of other stories

### Recommended Execution Order

```
Phase 1 (Setup) → Phase 2 (Foundational)
    ↓
Phase 3 (US1: Dead Code) ←→ Phase 6 (US4: Hygiene) [parallel]
    ↓
Phase 4 (US2: Shims/Stale Tests)
    ↓
Phase 5 (US3: Consolidation)
    ↓
Phase 7 (Polish)
```

### Within Each User Story

- Backend and frontend tasks marked [P] can run in parallel (different codebases)
- Scan/identify tasks before removal tasks
- CI validation after each story's changes
- Commit after each completed story using appropriate conventional commit prefix

### Parallel Opportunities

- **Within Phase 1**: All validation tasks (T002–T008) can run in parallel
- **Within Phase 2**: All audit tasks (T009–T011) can run in parallel
- **Within US1**: All backend scan tasks (T012–T018) can run in parallel; all frontend scan tasks (T019–T024) can run in parallel
- **Within US2**: All shim scan tasks (T027–T029) can run in parallel; all test audit tasks (T030–T033) can run in parallel
- **Within US3**: All backend consolidation tasks (T038–T041) can run in parallel; all frontend consolidation tasks (T042–T045) can run in parallel
- **Within US4**: All comment, config, dependency, and infrastructure tasks (T048–T055) can run in parallel
- **Cross-story**: US1 and US4 can proceed simultaneously after Phase 2

---

## Parallel Example: US1 Dead Code Removal

```bash
# Backend dead code scan (all in parallel — different files/tools):
Task T012: "Unused imports via ruff F401 in backend/src/"
Task T013: "Unused variables via ruff F841 in backend/src/"
Task T014: "Unused functions in backend/src/services/"
Task T015: "Unused functions in backend/src/api/"
Task T016: "Unused Pydantic models in backend/src/models/"
Task T017: "Commented-out code in backend/src/"
Task T018: "Unused type definitions in backend/src/"

# Frontend dead code scan (all in parallel — different files/tools):
Task T019: "Unused imports/variables via eslint in frontend/src/"
Task T020: "Unused React components in frontend/src/components/"
Task T021: "Unused hooks in frontend/src/hooks/"
Task T022: "Unused utilities in frontend/src/utils/ and frontend/src/lib/"
Task T023: "Commented-out code in frontend/src/"
Task T024: "Unused TypeScript types in frontend/src/types/"

# Then CI validation (sequential):
Task T025: "Backend CI check"
Task T026: "Frontend CI check"
```

## Parallel Example: US4 Hygiene Cleanup

```bash
# All hygiene tasks in parallel (different files):
Task T048: "Stale comments in backend/src/"
Task T049: "Stale comments in frontend/src/"
Task T050: "Orphaned migrations in backend/src/migrations/"
Task T051: "Stale env vars in .env.example"
Task T052: "Unused Python deps in backend/pyproject.toml"
Task T053: "Unused JS deps in frontend/package.json"
Task T054: "Unused Docker services in docker-compose.yml"
Task T055: "Stale Dockerfile entries"
```

---

## Implementation Strategy

### MVP First (US1 Dead Code Only)

1. Complete Phase 1: Validate baseline (T001–T008)
2. Complete Phase 2: Audit dynamic loading (T009–T011)
3. Complete Phase 3: US1 — Remove dead code (T012–T026)
4. **STOP and VALIDATE**: All CI checks pass, no API contracts altered
5. This alone delivers the highest-value cleanup — reduced codebase size and cognitive load

### Incremental Delivery

1. Phase 1 + 2 → Baseline validated, dynamic loading patterns documented
2. US1 (Dead Code) → Validate → Commit (`chore:`) — MVP delivered
3. US2 (Shims/Stale Tests) → Validate → Commit (`chore:`) — False coverage eliminated
4. US3 (Consolidation) → Validate → Commit (`refactor:`) — Duplication reduced
5. US4 (Hygiene) → Validate → Commit (`chore:`) — Configuration cleaned
6. Phase 7 (Polish) → Final validation, line count comparison, PR summary
7. Each story adds value without breaking previous cleanup work

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + 2 together (baseline + audit)
2. Once Foundational is done:
   - Developer A: US1 (dead code — backend focus)
   - Developer B: US1 (dead code — frontend focus) + US4 (hygiene)
   - Developer C: US2 (shims/stale tests) after US1 merges
   - Developer D: US3 (consolidation) after US1 + US2 merge
3. All stories merge independently with their own CI validation

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 63 (T001–T063) |
| **Setup tasks** | 8 (T001–T008) |
| **Foundational tasks** | 3 (T009–T011) |
| **US1 tasks (Dead Code)** | 15 (T012–T026) |
| **US2 tasks (Shims/Stale Tests)** | 11 (T027–T037) |
| **US3 tasks (Consolidation)** | 10 (T038–T047) |
| **US4 tasks (Hygiene)** | 10 (T048–T057) |
| **Polish tasks** | 6 (T058–T063) |
| **User stories** | 4 (US1–US4) |
| **Parallel opportunities** | 8 groups identified |
| **Suggested MVP scope** | US1 only (15 tasks — dead code removal) |
| **Independent test per story** | Full CI suite (`ruff`, `pyright`, `pytest`, `eslint`, `tsc`, `vitest`, `vite build`) |

---

## Notes

- [P] tasks = different files, no dependencies — safe to run in parallel
- [Story] label maps task to specific user story / cleanup category for traceability
- Each user story is independently completable and testable via full CI suite
- Dynamic loading audit (Phase 2) is CRITICAL — do NOT skip before removing code
- The 8 MagicMock database files in the repository root (T034) are confirmed stale test artifacts
- Duplicate migration prefix `007_` (`007_agent_configs.sql` and `007_housekeeping.sql`) should be reviewed in T050
- `jsdom` in `frontend/package.json` devDependencies may be unused (vitest uses `happy-dom`) — verify in T053
- Use `chore:` prefix for removal commits (US1, US2, US4) and `refactor:` prefix for consolidation commits (US3)
- Commit after each completed user story, not after each individual task
- Stop at any checkpoint to validate the story independently before moving to the next
