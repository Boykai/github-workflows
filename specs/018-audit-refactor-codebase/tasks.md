# Tasks: Audit & Refactor FastAPI + React GitHub Projects V2 Codebase

**Input**: Design documents from `/specs/018-audit-refactor-codebase/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Existing tests must pass and affected tests must be updated (FR-018, FR-019). No new test files are created — all refactoring is in-place.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/package.json`
- **Config**: `backend/pyproject.toml`, `frontend/package.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a baseline by auditing key files and running existing tests to detect any pre-existing failures.

- [x] T001 Read and audit current backend dependencies in backend/pyproject.toml
- [x] T002 [P] Read and audit current frontend dependencies in frontend/package.json
- [x] T003 [P] Read key backend service files to understand current duplication patterns in backend/src/services/completion_providers.py, backend/src/services/model_fetcher.py, and backend/src/services/github_projects/service.py
- [x] T004 Run existing backend test suite (pytest) to establish a passing baseline
- [x] T005 [P] Run existing frontend test suite (npm test) and build (npm run build) to establish a passing baseline
- [x] T006 [P] Run ruff check and ruff format --check on backend/src/ to confirm lint baseline

**Checkpoint**: Baseline established — all existing tests pass, current state of code is understood.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new foundational infrastructure is needed for this refactor. All changes are in-place within existing files (FR-015). This phase is intentionally empty — proceed directly to user stories.

**⚠️ NOTE**: The in-place refactoring constraint (FR-015) means no new files or modules. All shared helpers are added to existing modules.

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Modernize Backend and Frontend Dependencies (Priority: P1) 🎯 MVP

**Goal**: Update all backend and frontend dependencies to latest stable versions, remove unused `agent-framework-core`, and confirm zero import errors and no behavioral regressions.

**Independent Test**: Run the full backend test suite (`pytest`) and frontend test suite (`npm test`) after dependency updates. Confirm zero import errors, zero test failures, and successful frontend build.

### Implementation for User Story 1

#### Backend Dependency Updates

- [x] T007 [US1] Remove `agent-framework-core>=1.0.0a1` from dependencies in backend/pyproject.toml
- [x] T008 [US1] Bump `github-copilot-sdk` from `>=0.1.0` to `>=0.1.30` in backend/pyproject.toml
- [x] T009 [P] [US1] Bump `openai` from `>=1.0.0` to `>=2.24.0` in backend/pyproject.toml
- [x] T010 [P] [US1] Bump `azure-ai-inference` from `>=1.0.0b1` to `>=1.0.0b9` in backend/pyproject.toml
- [x] T011 [US1] Install updated backend dependencies (`pip install -e ".[dev]"`) and verify no import breakage in backend/
- [x] T012 [US1] Run backend test suite (`pytest`) to verify no regressions after dependency updates
- [x] T013 [US1] Run ruff check on backend/src/ to verify no lint regressions from dependency changes

#### Frontend Dependency Updates

- [x] T014 [P] [US1] Bump `@tanstack/react-query` from `^5.17.0` to `^5.90.7` in frontend/package.json
- [x] T015 [P] [US1] Bump `vite` from `^5.4.0` to `^7.3.1` and update `@vitejs/plugin-react` to a Vite 7–compatible version in frontend/package.json
- [x] T016 [US1] Install updated frontend dependencies (`npm install`) in frontend/
- [x] T017 [US1] Run frontend build (`npm run build`) and test suite (`npm test`) to verify no regressions

**Checkpoint**: All dependencies modernized. Backend and frontend tests pass. `agent-framework-core` removed. Application starts without import errors.

---

## Phase 4: User Story 2 — Eliminate Duplicate Code Through DRY Consolidation (Priority: P1)

**Goal**: Extract shared helpers for client pooling, fallback chains, retry logic, and header construction — eliminating duplicated patterns across the backend codebase.

**Independent Test**: Run the existing backend test suite (`pytest`) after each sub-phase (2A–2D). Confirm all tests pass and behavior is identical before and after each consolidation.

### Implementation for User Story 2

#### 2A: Extract CopilotClientPool

- [x] T018 [US2] Add `CopilotClientPool` class (with `token_key`, `get_or_create`, `remove`, `clear` methods) in backend/src/services/completion_providers.py
- [x] T019 [US2] Refactor `CopilotCompletionProvider` to delegate client caching to the shared `CopilotClientPool` in backend/src/services/completion_providers.py
- [x] T020 [US2] Refactor `GitHubCopilotModelFetcher` to import and use the shared `CopilotClientPool` from `completion_providers` in backend/src/services/model_fetcher.py
- [x] T021 [US2] Remove duplicate `_token_key()` and `_get_or_create_client()` methods from `GitHubCopilotModelFetcher` in backend/src/services/model_fetcher.py

#### 2B: Introduce Fallback Helper

- [x] T022 [US2] Add `async _with_fallback(primary_fn, fallback_fn, context_msg)` method to `GitHubProjectsService` in backend/src/services/github_projects/service.py
- [x] T023 [US2] Refactor `assign_copilot_to_issue()` to use `_with_fallback` (GraphQL primary, REST fallback) in backend/src/services/github_projects/service.py
- [x] T024 [P] [US2] Refactor review request methods to use `_with_fallback` (REST primary, GraphQL fallback) in backend/src/services/github_projects/service.py
- [x] T025 [US2] Refactor `add_issue_to_project()` to use `_with_fallback` (GraphQL primary, REST fallback) in backend/src/services/github_projects/service.py

#### 2C: Unify Retry Logic

- [x] T026 [US2] Enhance `_request_with_retry()` to handle secondary rate limits (403 with `X-RateLimit-Remaining: 0` and body-based detection) in backend/src/services/github_projects/service.py
- [x] T027 [US2] Remove inline retry-on-secondary-rate-limit logic from `_graphql()` method in backend/src/services/github_projects/service.py

#### 2D: Consolidate Header Builder

- [x] T028 [US2] Enhance `_build_headers()` to accept optional `extra_headers: dict[str, str] | None` and `graphql_features: list[str] | None` parameters in backend/src/services/github_projects/service.py
- [x] T029 [US2] Remove `_build_graphql_headers()` if it exists and update all call sites to use the unified `_build_headers()` in backend/src/services/github_projects/service.py

#### Verification

- [x] T030 [US2] Run backend test suite (`pytest`) to verify DRY consolidation introduces no regressions
- [x] T031 [US2] Update any affected backend tests to match refactored method signatures and behavior in backend/tests/

**Checkpoint**: All DRY consolidation complete. Duplicate client caching eliminated. Fallback chains use shared helper. Retry logic unified. Header construction consolidated. All tests pass.

---

## Phase 5: User Story 3 — Fix Anti-Patterns in Backend Code (Priority: P2)

**Goal**: Resolve six identified anti-patterns (3A–3F): parameterize hardcoded model, document/persist chat state, implement file deletions, document OAuth bounds, standardize singletons, and bound all caches.

**Independent Test**: Each anti-pattern fix is independently testable. Run `pytest` after completing each sub-group. Hardcoded model fix: pass different model values. Bounded caches: verify capacity limits are enforced. Singleton standardization: verify test isolation.

### Implementation for User Story 3

#### 3A: Parameterize Hardcoded Model

- [x] T032 [US3] Add `$model: String!` variable to `ASSIGN_COPILOT_MUTATION` GraphQL string, replacing hardcoded `model: "claude-opus-4.6"` in backend/src/services/github_projects/graphql.py
- [x] T033 [US3] Pass `model` value from `AgentAssignmentConfig.model` (or a default constant) at the call site in `_assign_copilot_graphql()` in backend/src/services/github_projects/service.py

#### 3B: Document/Persist Chat State as MVP

- [x] T034 [P] [US3] Add explicit TODO comments documenting the intentional MVP in-memory approach for `_messages`, `_proposals`, and `_recommendations` dicts in backend/src/api/chat.py
- [x] T035 [P] [US3] Convert `_messages`, `_proposals`, and `_recommendations` from plain `dict` to `BoundedDict(maxlen=500)` in backend/src/api/chat.py

#### 3C: Implement File Deletion in Commit Workflow

- [x] T036 [P] [US3] Implement `delete_files` parameter using `fileChanges.deletions` in the GraphQL `createCommitOnBranch` mutation in backend/src/services/github_commit_workflow.py

#### 3D: Document OAuth State Bounds

- [x] T037 [P] [US3] Add code comment to `_oauth_states` documenting bounded capacity (max 1000 entries), loss-on-restart behavior, and optional SQLite migration path in backend/src/services/github_auth.py

#### 3E: Standardize Singleton Registration

- [x] T038 [US3] Ensure all service singletons are registered on `app.state` exclusively in backend/src/main.py
- [x] T039 [US3] Remove module-global fallback variables for service singletons in backend/src/dependencies.py
- [x] T040 [US3] Update any affected tests that relied on module-global fallbacks to use `app.state` overrides in backend/tests/

#### 3F: Bound All In-Memory Caches

- [x] T041 [P] [US3] Convert `_recent_requests` from plain `dict` to `BoundedDict(maxlen=1000)` in backend/src/api/workflow.py
- [x] T042 [P] [US3] Convert `_conversations` from plain `dict` to `BoundedDict(maxlen=200)` in backend/src/services/chores/chat.py
- [x] T043 [P] [US3] Convert `_pipeline_states` to `BoundedDict(maxlen=500)`, `_issue_main_branches` to `BoundedDict(maxlen=1000)`, and `_issue_sub_issue_map` to `BoundedDict(maxlen=1000)` in backend/src/services/workflow_orchestrator/transitions.py
- [x] T044 [P] [US3] Convert `_workflow_configs` from plain `dict` to `BoundedDict(maxlen=100)` in backend/src/services/workflow_orchestrator/config.py
- [x] T045 [P] [US3] Convert `_chat_sessions` and `_chat_session_timestamps` to `BoundedDict(maxlen=200)` in backend/src/services/agents/service.py
- [x] T046 [P] [US3] Convert `_signal_pending` from plain `dict` to `BoundedDict(maxlen=500)` in backend/src/services/signal_chat.py

#### Verification

- [x] T047 [US3] Run backend test suite (`pytest`) to verify anti-pattern fixes introduce no regressions
- [x] T048 [US3] Update any affected backend tests to match changes (BoundedDict imports, singleton access patterns, parameterized model) in backend/tests/

**Checkpoint**: All six anti-patterns resolved. Hardcoded model parameterized. Chat state documented as MVP with bounded caches. File deletion implemented. OAuth state documented. Singletons standardized. All caches bounded. All tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, cleanup, and summary across all user stories.

- [x] T049 Run full backend test suite (`pytest -v`) for final verification in backend/
- [x] T050 [P] Run full frontend test suite (`npm test`) and build (`npm run build`) for final verification in frontend/
- [x] T051 [P] Run ruff check and ruff format --check on all changed backend files in backend/src/
- [x] T052 [P] Run frontend type-check (`npm run type-check`) and lint verification in frontend/
- [x] T053 Verify application startup with smoke test: `python -c "from src.main import create_app; print('Import OK')"` in backend/
- [x] T054 Run quickstart.md validation checklist against all phases
- [x] T055 Produce concise summary of all changes made (dependency versions, DRY patterns consolidated, anti-patterns resolved)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Intentionally empty for this in-place refactor
- **US1 — Dependencies (Phase 3)**: Depends on Setup completion. Must complete before US2 and US3 (updated deps are the baseline for all code changes)
- **US2 — DRY (Phase 4)**: Depends on US1 completion (code changes assume updated dependencies)
- **US3 — Anti-Patterns (Phase 5)**: Depends on US1 completion. Can run in parallel with US2 if working on different files, but recommended to run sequentially for simpler merge conflict avoidance
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — No dependencies on other stories. **MUST complete first** as all subsequent code changes assume updated dependencies.
- **User Story 2 (P1)**: Can start after US1 (Phase 3) — DRY consolidation operates on files that must have correct dependencies installed.
- **User Story 3 (P2)**: Can start after US1 (Phase 3) — Most anti-pattern fixes (3A, 3B, 3C, 3D, 3F) are independent of US2. However, 3E (singleton standardization) may interact with service changes in US2.
  - **Sub-dependencies within US3**: Tasks 3A–3D and 3F are independent of each other and can run in parallel. Task 3E (singletons) should run after other US3 tasks to avoid conflicts.

### Within Each User Story

- Backend dependency updates before frontend (US1)
- `pip install`/`npm install` after manifest changes
- CopilotClientPool extraction (2A) before fallback helper (2B) — no dependency, but logical ordering
- Retry unification (2C) before header consolidation (2D) — no dependency, but logical ordering
- Parameterize model (3A) before singleton standardization (3E) — the model call site may be affected
- Cache bounding (3F) can run fully in parallel across all files
- Tests run after each logical sub-phase

### Parallel Opportunities

- **Phase 1**: T002, T003, T005, T006 can all run in parallel with T001
- **Phase 3 (US1)**: T009, T010 (backend deps) can run in parallel; T014, T015 (frontend deps) can run in parallel
- **Phase 4 (US2)**: T024 (review request refactor) can run in parallel with T023/T025; 2A, 2B, 2C, 2D sub-phases are sequential within service.py
- **Phase 5 (US3)**: T034–T037 (3B, 3C, 3D) can all run in parallel (different files); T041–T046 (3F cache bounding) can all run in parallel (different files)
- **Phase 6**: T050, T051, T052 can run in parallel with T049

---

## Parallel Example: User Story 1 (Dependency Updates)

```text
# Backend dependency edits can be parallelized (different lines in same file):
Task T009: "Bump openai to >=2.24.0 in backend/pyproject.toml"
Task T010: "Bump azure-ai-inference to >=1.0.0b9 in backend/pyproject.toml"

# Frontend dependency edits can be parallelized (different lines in same file):
Task T014: "Bump @tanstack/react-query to ^5.90.7 in frontend/package.json"
Task T015: "Bump vite to ^7.3.1 in frontend/package.json"
```

## Parallel Example: User Story 3 (Cache Bounding)

```text
# All cache bounding tasks operate on different files:
Task T041: "Convert _recent_requests to BoundedDict in backend/src/api/workflow.py"
Task T042: "Convert _conversations to BoundedDict in backend/src/services/chores/chat.py"
Task T043: "Convert pipeline caches to BoundedDict in backend/src/services/workflow_orchestrator/transitions.py"
Task T044: "Convert _workflow_configs to BoundedDict in backend/src/services/workflow_orchestrator/config.py"
Task T045: "Convert chat session caches to BoundedDict in backend/src/services/agents/service.py"
Task T046: "Convert _signal_pending to BoundedDict in backend/src/services/signal_chat.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (read key files, establish test baseline)
2. Complete Phase 3: User Story 1 — Modernize Dependencies
3. **STOP and VALIDATE**: All backend and frontend tests pass with updated deps
4. This is deployable on its own — updated deps with zero regressions

### Incremental Delivery

1. Complete Setup → Baseline established
2. Add User Story 1 (Dependencies) → Test independently → **MVP ready!**
3. Add User Story 2 (DRY Consolidation) → Test independently → Cleaner codebase
4. Add User Story 3 (Anti-Patterns) → Test independently → All tech debt resolved
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + US1 (Dependencies) together — **this MUST be first**
2. Once US1 is done:
   - Developer A: User Story 2 (DRY Consolidation — service.py, completion_providers.py, model_fetcher.py)
   - Developer B: User Story 3 sub-tasks 3A–3D, 3F (anti-patterns on different files)
   - Developer C: User Story 3 sub-task 3E (singleton standardization — main.py, dependencies.py)
3. All developers run full test suite before merging

---

## Task Summary

| Phase | Story | Task Count | Parallel Tasks |
|-------|-------|------------|----------------|
| Phase 1: Setup | — | 6 | 4 |
| Phase 2: Foundational | — | 0 | — |
| Phase 3: US1 — Dependencies | US1 | 11 | 4 |
| Phase 4: US2 — DRY Consolidation | US2 | 14 | 1 |
| Phase 5: US3 — Anti-Patterns | US3 | 17 | 12 |
| Phase 6: Polish | — | 7 | 3 |
| **Total** | | **55** | **24** |

### Tasks Per User Story

- **US1 (Modernize Dependencies)**: 11 tasks — Backend deps (7) + Frontend deps (4)
- **US2 (DRY Consolidation)**: 14 tasks — Pool (4) + Fallback (4) + Retry (2) + Headers (2) + Verify (2)
- **US3 (Fix Anti-Patterns)**: 17 tasks — 3A (2) + 3B (2) + 3C (1) + 3D (1) + 3E (3) + 3F (6) + Verify (2)

### Suggested MVP Scope

**User Story 1 only** (Modernize Dependencies) — 11 tasks. This delivers immediate security and compatibility value with the lowest risk of regressions.

### Independent Test Criteria

- **US1**: `pytest` passes + `npm test` passes + `npm run build` succeeds + zero import errors
- **US2**: `pytest` passes + all DRY-consolidated methods produce identical behavior to originals
- **US3**: `pytest` passes + bounded caches enforce capacity limits + model is parameterized + file deletions work + singletons use `app.state` exclusively

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **FR-015**: All changes are in-place — no new files or modules
- **FR-016**: Dual AI provider pattern (Copilot SDK + Azure OpenAI fallback) is preserved
- **FR-017**: All API endpoint contracts are unchanged
- React version kept at ^18.3.1 (React 19 migration is out of scope per research.md R2.1)
- Vitest (^4.0.18) and Playwright (^1.58.1) already at latest — no changes needed
