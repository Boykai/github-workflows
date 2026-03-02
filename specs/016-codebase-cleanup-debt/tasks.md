# Tasks: Repository-Wide Codebase Cleanup to Reduce Technical Debt

**Input**: Design documents from `/specs/016-codebase-cleanup-debt/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Not explicitly requested — test tasks are omitted. Existing tests should be updated only where assertions change due to cleanup.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The four user stories from spec.md map to the five cleanup categories from the parent issue:
- **US1 (P1)**: Remove Dead Code and Backwards-Compatibility Shims (Categories 1 & 2)
- **US2 (P2)**: Consolidate Duplicated Logic (Category 3)
- **US3 (P3)**: Delete Stale Tests and Apply General Hygiene (Categories 4 & 5)
- **US4 (P2)**: Verify Dynamic Loading Safety (cross-cutting verification)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Tests**: `backend/tests/`, `frontend/src/test/`
- **Config**: repository root (`docker-compose.yml`, `backend/Dockerfile`, `backend/pyproject.toml`, `frontend/package.json`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Validate baseline — ensure all CI checks pass before any cleanup changes.

- [ ] T001 Verify existing backend tests pass: `cd backend && python -m pytest -v`
- [ ] T002 Verify existing frontend tests pass: `cd frontend && npm test`
- [ ] T003 [P] Verify backend linting passes: `cd backend && ruff check src tests && ruff format --check src tests`
- [ ] T004 [P] Verify frontend linting passes: `cd frontend && npm run lint`
- [ ] T005 [P] Verify frontend build succeeds: `cd frontend && npm run build`
- [ ] T006 Record baseline metrics (total lines of code, number of files, test count) for before/after comparison

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Identify and document all dynamic loading patterns that MUST be preserved during cleanup. This phase blocks all cleanup work.

**⚠️ CRITICAL**: No cleanup work can begin until dynamic loading patterns are confirmed safe.

- [ ] T007 Audit migration discovery in `backend/src/services/database.py` (lines 160–179) — document the `_discover_migrations()` regex pattern `^(\d{3})_.*\.sql$` and confirm all migration files (from `001_initial_schema.sql` through the latest migration) in `backend/src/migrations/` are in the active chain and must not be removed
- [ ] T008 [P] Audit global state registries — document `PROVIDER_REGISTRY` in `backend/src/services/model_fetcher.py` (line 211–218), workflow config caches in `backend/src/services/workflow_orchestrator/config.py` (lines 18, 21), and pipeline state caches in `backend/src/services/workflow_orchestrator/transitions.py` (lines 10, 15, 22) as protected from removal
- [ ] T009 [P] Audit lazy-loaded service singletons — document `_ai_agent_service_instance` in `backend/src/services/ai_agent.py` (line 799), `_model_fetcher_service` in `backend/src/services/model_fetcher.py` (line 435), `_encryption_service` in `backend/src/services/session_store.py` (line 18), and `_orchestrator_instance` in `backend/src/services/workflow_orchestrator/orchestrator.py` (line 1705) as dynamically initialized and protected from removal
- [ ] T010 [P] Audit optional/conditional imports — confirm `try/except ImportError` blocks in `backend/src/api/workflow.py` (lines 351–357) and `backend/src/services/completion_providers.py` (lines 217–240) are intentional graceful degradation patterns and must not be removed

**Checkpoint**: All dynamic loading patterns documented — cleanup can now proceed safely.

---

## Phase 3: User Story 1 — Remove Dead Code and Backwards-Compatibility Shims (Priority: P1) 🎯 MVP

**Goal**: Remove all dead code paths, unused functions, unused imports, backwards-compatibility shims, and commented-out code that are confirmed safe to remove. This delivers the highest immediate improvement to developer productivity.

**Independent Test**: All existing CI checks (ruff, pyright, pytest, eslint, tsc, vitest, vite build) pass after removal, and no public API contracts change. A before/after comparison of lines of code confirms the cleanup was effective.

### Implementation for User Story 1

#### Backwards-Compatibility Shim Removal

- [ ] T011 [US1] Remove `PREDEFINED_LABELS` backward-compatible alias in `backend/src/prompts/issue_generation.py` (lines 8–9) and update the single consumer in `backend/tests/unit/test_prompts.py` to import `LABELS` from `backend/src/constants.py` instead
- [ ] T012 [US1] Remove `DEFAULT_AGENT_MAPPINGS` re-export from `backend/src/models/chat.py` (line 16) and update the single consumer in `backend/tests/integration/test_custom_agent_assignment.py` to import from `backend/src/constants.py` instead
- [ ] T013 [US1] Evaluate `get_session_dep` alias in `backend/src/api/auth.py` (line 57) — this alias is used in 11 API files and 5 test files; if removing, update all consumers to use `get_current_session` directly: `backend/src/api/chat.py`, `backend/src/api/board.py`, `backend/src/api/workflow.py`, `backend/src/api/mcp.py`, `backend/src/api/housekeeping.py`, `backend/src/api/cleanup.py`, `backend/src/api/settings.py`, `backend/src/api/signal.py`, `backend/src/api/projects.py`, `backend/src/api/tasks.py`, `backend/src/dependencies.py`, `backend/tests/conftest.py`, `backend/tests/integration/test_webhook_verification.py`, `backend/tests/unit/test_api_auth.py`, `backend/tests/unit/test_admin_authorization.py`, `backend/tests/unit/test_auth_security.py`
- [ ] T014 [US1] Evaluate backward-compatible re-exports block in `backend/src/models/chat.py` (lines 18–43) — these re-exports from `src.models.agent`, `src.models.recommendation`, and `src.models.workflow` are used in approximately 35 files across API, service, and test layers; if keeping, add a `# TODO: migrate consumers to direct imports` comment; if removing, update all consumers to import from canonical module locations

#### Dead Code and Unused Symbol Removal

- [ ] T015 [P] [US1] Remove MagicMock test artifact files leaked at repository root — these are files with names like `<MagicMock name='get_settings().database_path' id='139810626547504'>` (zero-byte files created when a MagicMock object is stringified into a file path); delete all such files and add a `.gitignore` rule to prevent recurrence. Note: T035 in Phase 6 fixes the root cause; this task only removes the existing artifacts
- [ ] T016 [P] [US1] Run `ruff check --select F401` on `backend/src/` to identify unused imports across all backend source files and remove any confirmed-unused imports (respecting `# noqa: F401` markers on intentional re-exports)
- [ ] T017 [P] [US1] Run `ruff check --select F811,F841` on `backend/src/` to identify unused variables and redefined-unused-functions, then remove confirmed-unused items
- [ ] T018 [P] [US1] Run eslint on `frontend/src/` and identify unused imports, variables, and type definitions flagged by `@typescript-eslint/no-unused-vars` — remove confirmed-unused items
- [ ] T019 [P] [US1] Search for commented-out code blocks in `backend/src/` (lines starting with `#` that contain code-like patterns such as `# import`, `# def`, `# class`, `# if`, `# return`) — remove confirmed dead code while preserving documentation comments
- [ ] T020 [P] [US1] Search for commented-out code blocks in `frontend/src/` (lines starting with `//` that contain code patterns such as `// import`, `// const`, `// function`, `// export`) — remove confirmed dead code while preserving documentation comments
- [ ] T021 [US1] Run `cd backend && ruff check src tests && python -m pytest -v` and `cd frontend && npm run lint && npm test && npm run build` to verify all checks pass after dead code removal

**Checkpoint**: All confirmed dead code and safe-to-remove shims are eliminated. Verify: all CI checks pass and no public API contracts changed.

---

## Phase 4: User Story 2 — Consolidate Duplicated Logic (Priority: P2)

**Goal**: Merge near-duplicate functions, helpers, service methods, model definitions, and test patterns into single shared implementations so that future changes only need to be made in one place.

**Independent Test**: All existing tests pass after consolidation, no public API contracts change, and a code similarity analysis shows reduced duplication.

### Implementation for User Story 2

#### Test Factory Consolidation

- [ ] T022 [P] [US2] Replace duplicate `_task()` factory in `backend/tests/unit/test_api_tasks.py` (lines 18–27) with import of `make_task` from `backend/tests/helpers/factories.py` — update all call sites in the file to use `make_task()`
- [ ] T023 [P] [US2] Replace duplicate `_task()` factory in `backend/tests/unit/test_api_projects.py` (lines 39–48) with import of `make_task` from `backend/tests/helpers/factories.py` — update all call sites in the file to use `make_task()`
- [ ] T024 [P] [US2] Replace duplicate `_recommendation()` factory in `backend/tests/unit/test_api_workflow.py` (lines 46–60) with import of `make_issue_recommendation` from `backend/tests/helpers/factories.py` — update all call sites in the file
- [ ] T025 [P] [US2] Replace duplicate `_recommendation()` factory in `backend/tests/unit/test_api_chat.py` (lines 28–38) with import of `make_issue_recommendation` from `backend/tests/helpers/factories.py` — update all call sites in the file

#### Test Mock Setup Consolidation

- [ ] T026 [P] [US2] Replace inline mock `AsyncMock(name="GitHubAuthService")` setup in `backend/tests/unit/test_auth_security.py` (lines 37–40 and 69–72) with import of `make_mock_github_auth_service` from `backend/tests/helpers/mocks.py`
- [ ] T027 [P] [US2] Evaluate inline `_make_github_service()` helper in `backend/tests/unit/test_cleanup_service.py` (lines 46–100) — if it can be replaced or extended from `make_mock_github_service` in `backend/tests/helpers/mocks.py`, consolidate; otherwise document why custom setup is needed
- [ ] T028 [P] [US2] Search all files in `backend/tests/unit/` for inline mock setups that duplicate patterns already available in `backend/tests/helpers/mocks.py` (e.g., `mock_github_service.get_project_repository.return_value`, `mock_github_service.create_issue.return_value`) — consolidate where safe

#### Model and Type Consolidation

- [ ] T029 [US2] Audit `backend/src/models/` for overlapping Pydantic model definitions — identify any Create/Update model pairs that share >80% of fields and can be consolidated using inheritance or `ConfigDict` options
- [ ] T030 [P] [US2] Audit `frontend/src/types/` for overlapping TypeScript type definitions — identify duplicate or near-duplicate interfaces and consolidate into canonical definitions
- [ ] T031 [US2] Run `cd backend && python -m pytest -v` and `cd frontend && npm test` to verify all tests pass after consolidation changes

**Checkpoint**: Duplicated logic is consolidated into shared implementations. Verify: all CI checks pass.

---

## Phase 5: User Story 4 — Verify Dynamic Loading Safety (Priority: P2)

**Goal**: Ensure that no code loaded via string-based plugin loading or migration discovery is incorrectly removed during US1 or US2 work. This is a verification pass that accompanies all cleanup work.

**Independent Test**: Review each candidate removal against dynamic loading patterns documented in Phase 2 and confirm migration files are still discovered correctly.

### Implementation for User Story 4

- [ ] T032 [US4] Cross-reference all code removals from US1 (T011–T020) against the dynamic loading audit from Phase 2 (T007–T010) — confirm no removed function, module, or import is loaded dynamically via string-based imports, plugin systems, or migration discovery
- [ ] T033 [US4] Verify all migration files in `backend/src/migrations/` are preserved and correctly discovered by running `cd backend && python -c "from src.services.database import _discover_migrations; print(_discover_migrations())"` or equivalent startup test
- [ ] T034 [US4] Verify the application starts successfully with all migrations applied — run `cd backend && python -m pytest tests/integration/ -v -k migration` or equivalent validation that the migration chain is intact

**Checkpoint**: All removals verified safe against dynamic loading patterns. No runtime failures introduced.

---

## Phase 6: User Story 3 — Delete Stale Tests and Apply General Hygiene (Priority: P3)

**Goal**: Remove stale tests, clean up test artifacts, resolve stale comments, and remove unused dependencies so that the test suite is reliable and project configuration is clean.

**Independent Test**: Remaining test suite passes, dependency audits show no references to deleted code, and no valid test coverage is lost.

### Implementation for User Story 3

#### Stale Test and Artifact Removal

- [ ] T035 [P] [US3] Investigate and fix root cause of MagicMock database file leakage — trace which test(s) in `backend/tests/` cause `get_settings().database_path` to be stringified into a filesystem path and create an actual file; fix the test setup in `backend/tests/conftest.py` (or relevant fixture) to prevent recurrence. Note: T015 in Phase 3 removes existing artifacts; this task prevents new ones from being created
- [ ] T036 [P] [US3] Audit `backend/tests/unit/` for test files or test cases covering functionality that has been deleted or refactored — remove stale tests while preserving tests covering active code paths
- [ ] T037 [P] [US3] Audit `backend/tests/unit/` for tests that over-mock internals (e.g., tests that mock every internal method call and only verify mock interactions without testing real behavior) — remove or refactor identified tests
- [ ] T038 [P] [US3] Audit `backend/tests/integration/` for stale integration tests covering deleted features or non-existent code paths — remove stale tests while preserving active coverage

#### Stale Comment Cleanup

- [ ] T039 [P] [US3] Audit `TODO` comment in `backend/src/api/projects.py` (line 54: `# TODO: Also fetch org projects the user has access to`) — determine if this references completed or actively planned work; remove if completed, preserve if active
- [ ] T040 [P] [US3] Search `backend/src/` and `frontend/src/` for all `TODO`, `FIXME`, and `HACK` comments — for each, determine whether the referenced work is completed; remove completed items, preserve active/planned items

#### Unused Dependency Removal

- [ ] T041 [P] [US3] Audit `backend/pyproject.toml` dependencies — run `pip install pipdeptree && pipdeptree` or equivalent to identify any dependencies not imported by any source file in `backend/src/`; remove confirmed-unused dependencies after verifying they are not transitive requirements
- [ ] T042 [P] [US3] Audit `frontend/package.json` dependencies — search `frontend/src/` for imports of each dependency listed in `dependencies` and `devDependencies`; remove confirmed-unused packages via `npm uninstall`
- [ ] T043 [P] [US3] Check for unused Docker Compose environment variables in `docker-compose.yml` — cross-reference each environment variable against `backend/src/config.py` Settings fields and remove any that reference deleted features

#### Orphaned Configuration Cleanup

- [ ] T044 [P] [US3] Check `.env.example` for environment variables referencing deleted features — cross-reference against `backend/src/config.py` and remove orphaned entries
- [ ] T045 [US3] Run `cd backend && ruff check src tests && python -m pytest -v` and `cd frontend && npm run lint && npm test && npm run build` to verify all checks pass after hygiene changes

**Checkpoint**: Test suite is clean, dependencies are lean, and configuration references only active features. Verify: all CI checks pass.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and PR documentation.

- [ ] T046 Run full backend CI suite: `cd backend && ruff check src tests && ruff format --check src tests && python -m pytest -v`
- [ ] T047 Run full frontend CI suite: `cd frontend && npm run lint && npx tsc --noEmit && npm test && npm run build`
- [ ] T048 Record final metrics (total lines of code, number of files, test count) and compute net reduction from Phase 1 baseline (target: at least 100 lines net reduction per spec.md Success Criterion SC-004)
- [ ] T049 Verify no public API contracts changed — compare API route definitions in `backend/src/api/__init__.py` and all route handler files before and after cleanup to confirm all route paths and request/response shapes are unchanged
- [ ] T050 Prepare categorized PR summary covering all changes organized by the five cleanup categories (backwards-compat shims, dead code, duplicated logic, stale tests, general hygiene) with justifications for each removal or consolidation
- [ ] T051 Commit all changes using conventional commit format: `refactor:` for consolidation changes (US2), `chore:` for dead code removal (US1), test removal (US3), and hygiene fixes (US3)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — documents dynamic loading patterns
- **US1 Dead Code (Phase 3)**: Depends on Phase 2 — needs dynamic loading audit before removing code
- **US2 Consolidation (Phase 4)**: Depends on Phase 2 — can start in parallel with US1
- **US4 Dynamic Verification (Phase 5)**: Depends on US1 and US2 — verifies their removals are safe
- **US3 Stale Tests & Hygiene (Phase 6)**: Depends on US1 and US2 — cleanup should reflect changes from earlier phases
- **Polish (Phase 7)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Can start after Phase 2 — can run in parallel with US1 (different files)
- **US4 (P2)**: Depends on US1 and US2 — verification pass for their changes
- **US3 (P3)**: Can start after Phase 2 — best run after US1/US2 so stale test detection accounts for removed/consolidated code

### Within Each User Story

- Shim/dead-code removals before validation runs
- Model/type consolidation before test consolidation
- Individual file changes before cross-file validation
- CI verification as final task in each phase

### Parallel Opportunities

- **Phase 2**: T007, T008, T009, T010 can all run in parallel (different audit targets)
- **Phase 3 (US1)**: T015, T016, T017, T018, T019, T020 can all run in parallel (different files/tools)
- **Phase 4 (US2)**: T022, T023, T024, T025 can run in parallel (different test files); T026, T027, T028 can run in parallel
- **Phase 6 (US3)**: T035, T036, T037, T038, T039, T040, T041, T042, T043, T044 can mostly run in parallel (different targets)

---

## Parallel Example: Phase 3 (US1) Dead Code Removal

```bash
# All linter-assisted removals can run simultaneously:
Task T016: "Run ruff --select F401 on backend/src/ for unused imports"
Task T017: "Run ruff --select F811,F841 on backend/src/ for unused variables"
Task T018: "Run eslint on frontend/src/ for unused TS imports/variables"

# All manual search-and-remove tasks can run simultaneously:
Task T015: "Remove MagicMock files at repository root"
Task T019: "Search for commented-out code in backend/src/"
Task T020: "Search for commented-out code in frontend/src/"
```

## Parallel Example: Phase 4 (US2) Consolidation

```bash
# All test factory replacements can run simultaneously (different files):
Task T022: "Replace _task() in test_api_tasks.py"
Task T023: "Replace _task() in test_api_projects.py"
Task T024: "Replace _recommendation() in test_api_workflow.py"
Task T025: "Replace _recommendation() in test_api_chat.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Validate baseline
2. Complete Phase 2: Document dynamic loading patterns
3. Complete Phase 3: US1 — Remove dead code and backwards-compat shims
4. **STOP and VALIDATE**: Run all CI checks — dead code eliminated, shims removed
5. Deploy/demo if ready — codebase is cleaner and easier to navigate

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation validated, dynamic loading documented
2. Phase 3: US1 → Dead code removed → Validate (MVP!)
3. Phase 4: US2 → Duplicated logic consolidated → Validate
4. Phase 5: US4 → Dynamic loading verified → Validate
5. Phase 6: US3 → Stale tests and hygiene cleaned → Validate
6. Phase 7: Polish → Final validation and PR documentation → Done
7. Each phase adds value without breaking previous changes

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + Phase 2 together
2. Once Phase 2 is done:
   - Developer A: US1 (Phase 3) — dead code and shim removal
   - Developer B: US2 (Phase 4) — test and code consolidation
3. After US1 + US2 complete:
   - Developer A: US4 (Phase 5) — verification pass
   - Developer B: US3 (Phase 6) — stale tests and hygiene
4. Team completes Phase 7 (Polish) together

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 51 (T001–T051) |
| **Setup tasks** | 6 (T001–T006) |
| **Foundational tasks** | 4 (T007–T010) |
| **US1 tasks (P1 — Dead Code/Shims)** | 11 (T011–T021) |
| **US2 tasks (P2 — Consolidation)** | 10 (T022–T031) |
| **US4 tasks (P2 — Dynamic Verification)** | 3 (T032–T034) |
| **US3 tasks (P3 — Stale Tests/Hygiene)** | 11 (T035–T045) |
| **Polish tasks** | 6 (T046–T051) |
| **User stories** | 4 (US1–US4) |
| **Parallel opportunities** | 4 groups identified (Phase 2, Phase 3, Phase 4, Phase 6) |
| **Suggested MVP scope** | US1 (P1 — 11 tasks: dead code and shim removal) |
| **Independent test criteria** | Each story validated by full CI suite pass + API contract comparison |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- The `models/chat.py` re-export block (lines 18–43) is used in 30+ files — a full migration is a separate story; T014 evaluates and documents the decision
- The `get_session_dep` alias is used in 16 files — T013 evaluates whether to remove or defer based on effort-to-value ratio
- Legacy encryption handling in `backend/src/services/encryption.py` (plaintext token detection) is runtime-critical and must NOT be removed — it handles pre-encryption data gracefully
- Legacy pipeline/sub-issue backward compat in `backend/src/services/copilot_polling/` is runtime-critical and must NOT be removed — it handles issues created before policy changes
- Commit after each task or logical group using `refactor:` (consolidation) or `chore:` (removal/cleanup)
- Stop at any checkpoint to validate story independently
- Avoid: removing dynamically-loaded code, altering public API contracts, removing tests for active features
