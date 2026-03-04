# Tasks: Audit & Refactor FastAPI+React GitHub Projects Copilot Codebase

**Input**: Design documents from `/specs/018-audit-refactor-codebase/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: No new test infrastructure is required. Existing backend (`pytest`) and frontend (`vitest`) test suites validate all changes. Individual tests may need updates if refactored internals change signatures.

**Organization**: Tasks are grouped by user story (from spec.md). User Story 4 (Backward Compatibility) is cross-cutting and verified at every checkpoint, not a separate phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`
- **Dependency manifests**: `backend/pyproject.toml`, `frontend/package.json`

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Establish that the codebase is in a working state before any changes. Confirm existing tests pass and tooling works.

- [x] T001 Run existing backend test suite per-file to establish passing baseline in `backend/tests/unit/`
- [x] T002 [P] Run existing frontend test suite to establish passing baseline via `cd frontend && npx vitest run`
- [x] T003 [P] Run ruff linting and formatting check to establish baseline via `cd backend && ruff check src tests && ruff format --check src tests`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational infrastructure changes are needed for this refactoring effort. All user stories operate on existing files in-place. The constraint of no new files/modules means no scaffolding is required.

**⚠️ CRITICAL**: Phase 1 baseline verification must pass before proceeding.

**Checkpoint**: Baseline verified — user story implementation can now begin in priority order.

---

## Phase 3: User Story 1 — Modernize All Dependencies (Priority: P1) 🎯 MVP

**Goal**: Update all backend and frontend dependencies to latest stable versions. Remove unused `agent-framework-core` package. Verify all Copilot SDK symbols still resolve.

**Independent Test**: Run `pip install -e ".[dev]"` and `npm install`, then execute existing backend and frontend test suites. If all tests pass after version bumps, the upgrade is verified.

### Implementation for User Story 1

- [x] T004 [US1] Remove `agent-framework-core>=1.0.0a1` dependency and its comment from `backend/pyproject.toml`
- [x] T005 [US1] Bump all backend dependency version specifiers to latest stable in `backend/pyproject.toml`: fastapi>=0.135.0, uvicorn[standard]>=0.41.0, httpx>=0.28.0, pydantic>=2.12.0, pydantic-settings>=2.7.0, python-multipart>=0.0.20, pyyaml>=6.0.2, github-copilot-sdk>=0.1.29, openai>=2.24.0, azure-ai-inference>=1.0.0b9, aiosqlite>=0.22.0, tenacity>=9.1.0, websockets>=14.0
- [x] T006 [P] [US1] Bump `@tanstack/react-query` to `^5.90.0` in `frontend/package.json` and run `npm install` to update lockfile
- [x] T007 [US1] Verify no import references to `agent-framework-core` or `agent_framework_core` exist anywhere in `backend/src/`
- [x] T008 [US1] Verify all Copilot SDK symbols resolve: `CopilotClient`, `CopilotClientOptions`, `SessionConfig`, `MessageOptions`, `PermissionHandler`, `SessionEventType`, `CopilotClient.list_models()` in `backend/src/services/completion_providers.py` and `backend/src/services/model_fetcher.py`
- [x] T009 [US1] Run backend test suite per-file in `backend/tests/unit/` to confirm no regressions from dependency bumps
- [x] T010 [P] [US1] Run frontend test suite via `cd frontend && npx vitest run` and build via `npm run build` to confirm no regressions

**Checkpoint**: All dependencies at latest stable, unused package removed, all tests pass. User Story 1 complete.

---

## Phase 4: User Story 2 — Eliminate Duplicate Code / DRY Consolidation (Priority: P1)

**Goal**: Extract shared abstractions to eliminate duplicated patterns: client caching (CopilotClientPool), fallback chains (_with_fallback), retry documentation, and header construction consolidation.

**Independent Test**: Run the existing backend test suite after each consolidation sub-task. If all tests pass without modifying test expectations, the refactoring preserves correctness.

### 2A: CopilotClientPool Extraction

- [x] T011 [US2] Add `CopilotClientPool` class in `backend/src/services/completion_providers.py` with `BoundedDict(maxlen=50)` for `_clients`, static `token_key()` method using SHA-256 truncated to 16 chars, async `get_or_create()` method, and async `cleanup()` method — per data-model.md entity spec
- [x] T012 [US2] Refactor `CopilotCompletionProvider` in `backend/src/services/completion_providers.py` to remove its duplicate `_clients` dict, `_token_key()`, and `_get_or_create_client()` methods, delegating to the shared `CopilotClientPool` instance instead
- [x] T013 [US2] Refactor `GitHubCopilotModelFetcher` in `backend/src/services/model_fetcher.py` to import and use the shared `CopilotClientPool` from `completion_providers`, removing its duplicate `_clients` dict, `_token_key()`, and `_get_or_create_client()` methods
- [x] T014 [US2] Update any tests in `backend/tests/unit/test_completion_providers.py` and `backend/tests/unit/test_model_fetcher.py` that mock the removed methods to use the new `CopilotClientPool` interface

### 2B: Fallback Helper Extraction

- [x] T015 [US2] Add `async _with_fallback(self, primary_fn, fallback_fn, context_msg)` private method on `GitHubProjectsService` in `backend/src/services/github_projects/service.py` — calls primary, logs warning on failure, calls fallback per data-model.md spec
- [x] T016 [US2] Refactor `assign_copilot()` in `backend/src/services/github_projects/service.py` to use `_with_fallback()` for GraphQL-primary → REST-fallback chain
- [x] T017 [US2] Refactor `add_issue_to_project()` in `backend/src/services/github_projects/service.py` to use `_with_fallback()` for GraphQL-primary → REST-fallback chain
- [x] T018 [US2] Refactor `request_copilot_review()` in `backend/src/services/github_projects/service.py` to use `_with_fallback()` for REST-primary → GraphQL-fallback chain

### 2C: Retry Logic Documentation

- [x] T019 [P] [US2] Add clear docstring to `_request_with_retry()` in `backend/src/services/github_projects/service.py` documenting it as THE single retry strategy handling 429/502/503 with exponential backoff
- [x] T020 [P] [US2] Add clear docstring to `_graphql()` in `backend/src/services/github_projects/service.py` documenting it as a higher-level wrapper that delegates to `_request_with_retry()` and adds ETag caching

### 2D: Header Construction Consolidation

- [x] T021 [US2] Add optional `graphql_features: str | None = None` parameter to `_build_headers()` in `backend/src/services/github_projects/service.py` that includes `GraphQL-Features` header when provided
- [x] T022 [US2] Replace all inline header construction (scattered `{"Authorization": ..., "Accept": ...}` dicts) in `backend/src/services/github_projects/service.py` with calls to the enhanced `_build_headers()`

### Verification

- [x] T023 [US2] Run backend test suite per-file in `backend/tests/unit/` to confirm no regressions from DRY consolidation

**Checkpoint**: All duplicated patterns consolidated — shared CopilotClientPool, _with_fallback helper, documented retry logic, unified header builder. All tests pass. User Story 2 complete.

---

## Phase 5: User Story 3 — Fix Anti-Patterns (Priority: P2)

**Goal**: Resolve all identified anti-patterns: parameterize hardcoded model, document/bound chat state, implement delete_files, document OAuth state, consolidate singletons, bound all caches.

**Independent Test**: Each anti-pattern fix can be verified independently through the existing test suite and targeted verification (grep for hardcoded strings, code review for documentation, etc.).

### 3A: Parameterize Hardcoded Model

- [x] T024 [US3] Parameterize `ASSIGN_COPILOT_MUTATION` in `backend/src/services/github_projects/graphql.py` to accept `$model: String!` variable instead of hardcoded `"claude-opus-4.6"`
- [x] T025 [US3] Update the `assign_copilot()` GraphQL mutation invocation in `backend/src/services/github_projects/service.py` to pass `model` variable from `AgentAssignmentConfig.model` to the parameterized mutation
- [x] T026 [US3] Update REST API payload in `backend/src/services/github_projects/service.py` to use `AgentAssignmentConfig.model` instead of hardcoded model string

### 3B: Document and Bound Chat State

- [x] T027 [P] [US3] Import `BoundedDict` from `src.utils` in `backend/src/api/chat.py` and convert `_messages`, `_proposals`, and `_recommendations` from plain `dict` to `BoundedDict(maxlen=1000)` with TODO comment: `# TODO: Migrate to SQLite for persistence across restarts (MVP: in-memory only)`

### 3C: Implement delete_files

- [x] T028 [P] [US3] Implement `delete_files` support in `backend/src/services/github_commit_workflow.py` by adding `fileChanges.deletions` entries to the `createCommitOnBranch` GraphQL mutation payload when `delete_files` parameter is provided, and remove the warning log stub

### 3D: Document OAuth State

- [x] T029 [P] [US3] Add documentation comment above `_oauth_states` in `backend/src/services/github_auth.py` explaining: single-instance only, bounded to 1000 entries with FIFO eviction, multi-instance deployment limitation, and SQLite migration path

### 3E: Consolidate Singleton Registration

- [x] T030 [US3] Update `backend/src/dependencies.py` to remove module-level fallback imports and have each dependency function raise a clear error if the `app.state` attribute is missing
- [x] T031 [US3] Verify `backend/src/main.py` sets all `app.state` attributes (github_service, connection_manager, db) before routes are registered, ensuring no dual-registration pattern remains

### 3F: Bound Workflow Orchestrator Caches

- [x] T032 [P] [US3] Import `BoundedDict` from `src.utils` in `backend/src/services/workflow_orchestrator/transitions.py` and convert `_pipeline_states`, `_issue_main_branches`, and `_issue_sub_issue_map` from plain `dict` to `BoundedDict(maxlen=500)`

### Verification

- [x] T033 [US3] Run backend test suite per-file in `backend/tests/unit/` to confirm no regressions from anti-pattern fixes
- [x] T034 [P] [US3] Verify no hardcoded `"claude-opus-4.6"` strings remain via `grep -r "claude-opus-4.6" backend/src/`

**Checkpoint**: All anti-patterns resolved — model parameterized, chat state documented and bounded, delete_files implemented, OAuth state documented, singletons consolidated, all caches bounded. All tests pass. User Story 3 complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories. Ensures backward compatibility (US4) and code quality.

- [x] T035 Run full backend test suite per-file in `backend/tests/unit/` — all tests pass with zero regressions
- [x] T036 [P] Run full frontend test suite via `cd frontend && npx vitest run` — all tests pass with zero regressions
- [x] T037 [P] Run `cd frontend && npm run build` — builds successfully
- [x] T038 [P] Run `cd backend && ruff check src tests && ruff format --check src tests` — no linting or formatting errors
- [x] T039 Verify `grep -r "agent.framework" backend/` returns no results (agent-framework-core fully removed)
- [x] T040 [P] Verify `grep -r "claude-opus-4.6" backend/src/` returns no results (no hardcoded model strings)
- [x] T041 [P] Audit all in-memory caches and confirm every cache uses `BoundedDict`/`BoundedSet` from `backend/src/utils.py`
- [x] T042 Generate concise completion summary documenting: total lines of duplicated code eliminated, dependencies updated, anti-patterns resolved

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — establishes baseline
- **Foundational (Phase 2)**: No implementation tasks — baseline verification gates user stories
- **US1: Modernize Dependencies (Phase 3)**: Depends on Phase 1 baseline — should execute first because later phases need stable dependency tree
- **US2: DRY Consolidation (Phase 4)**: Depends on Phase 3 (US1) — refactoring should happen on updated dependency versions
- **US3: Fix Anti-Patterns (Phase 5)**: Depends on Phase 4 (US2) — some fixes (3F bounding caches) interact with 2A (CopilotClientPool already uses BoundedDict)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **User Story 2 (P1)**: Should start after US1 — refactoring should target updated dependencies. Sub-tasks 2A→2B→2C→2D can proceed sequentially within the phase
- **User Story 3 (P2)**: Should start after US2 — some anti-pattern fixes (3A model parameterization, 3E singletons) build on DRY-consolidated code. Sub-tasks 3A–3F are largely independent within the phase
- **User Story 4 (P1)**: Cross-cutting — verified at every checkpoint via existing test suites

### Within Each User Story

- US1: Remove unused dep → bump backend deps → bump frontend deps → verify symbols → run tests
- US2: CopilotClientPool (2A) → _with_fallback (2B) → retry docs (2C) → headers (2D) → run tests
- US3: Anti-patterns 3A–3F can proceed in parallel (different files) → run tests

### Parallel Opportunities

**Within Phase 3 (US1)**:
- T006 (frontend deps) can run in parallel with T004–T005 (backend deps)
- T009 (backend tests) and T010 (frontend tests) can run in parallel

**Within Phase 4 (US2)**:
- T019 and T020 (retry docs, different methods) can run in parallel
- Sub-task groups 2C and 2D can potentially overlap if 2B is complete

**Within Phase 5 (US3)**:
- T027 (chat.py), T028 (github_commit_workflow.py), T029 (github_auth.py), T032 (transitions.py) all operate on different files and can run in parallel
- T024–T026 (model parameterization across graphql.py and service.py) must be sequential

---

## Parallel Example: User Story 3 Anti-Pattern Fixes

```bash
# These tasks operate on different files and can run simultaneously:
Task T027: "Convert chat state dicts to BoundedDict in backend/src/api/chat.py"
Task T028: "Implement delete_files in backend/src/services/github_commit_workflow.py"
Task T029: "Document OAuth state in backend/src/services/github_auth.py"
Task T032: "Bound orchestrator caches in backend/src/services/workflow_orchestrator/transitions.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Baseline verification
2. Complete Phase 3: Modernize all dependencies (US1)
3. **STOP and VALIDATE**: Run full test suites — if all pass, dependency modernization is verified
4. This is the lowest-risk increment and provides immediate security/maintenance value

### Incremental Delivery

1. Phase 1 → Baseline verified
2. Phase 3 (US1) → Dependencies modernized → Test → ✅ MVP!
3. Phase 4 (US2) → Code deduplicated → Test → ✅ DRY codebase
4. Phase 5 (US3) → Anti-patterns fixed → Test → ✅ Production-ready
5. Phase 6 → Final verification → Generate summary → ✅ Complete
6. Each phase adds value without breaking previous work

### Single Developer Strategy

Execute phases sequentially in priority order (P1 first):
1. Setup + US1 (dependencies) — quick wins, low risk
2. US2 (DRY) — structural improvements, moderate risk
3. US3 (anti-patterns) — targeted fixes, low-to-moderate risk
4. Polish — verification sweep

### Constraint Reminders

- **In-place only**: Do not create new files or modules (FR-015)
- **Preserve API contracts**: No changes to request/response shapes (FR-017)
- **Code style**: ruff formatting, 100-char lines, double quotes (FR-018)
- **Dual AI provider**: Maintain Copilot SDK primary + Azure OpenAI fallback (FR-016)
- **Python 3.11+**: Use `match/case`, `type` aliases where appropriate

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [US1/US2/US3] labels map tasks to specific user stories from spec.md
- User Story 4 (Backward Compatibility) is cross-cutting — verified at every checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate the user story independently
- Tests are run using per-file execution: `timeout 30 python -m pytest tests/unit/test_X.py -q`
- Frontend tests: `cd frontend && npx vitest run`
- Linting: `cd backend && ruff check src tests && ruff format --check src tests`
