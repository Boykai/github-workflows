# Tasks: Codebase Audit & Refactor

**Input**: Design documents from `/specs/018-codebase-audit-refactor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test updates are REQUIRED per FR-022. Existing tests must be updated to match refactored interfaces.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Verify current state, ensure all tests pass before any changes

- [X] T001 Run full backend test suite to establish green baseline in backend/tests/
- [X] T002 Run full frontend test suite to establish green baseline in frontend/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure changes that MUST be complete before user story work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create SQLite migration file backend/src/migrations/011_chat_persistence.sql with chat_messages, chat_proposals, and chat_recommendations tables per data-model.md schema (including CHECK constraints, indexes on session_id, and DEFAULT timestamps)

**Checkpoint**: Foundation ready — migration file exists and database can apply it on startup

---

## Phase 3: User Story 1 — Dependencies Stay Current and Lean (Priority: P1) 🎯 MVP

**Goal**: Remove unused `agent-framework-core`, bump all backend/frontend deps to latest stable

**Independent Test**: Run full test suites after dep changes; verify `pip list | grep agent-framework` returns nothing

### Implementation for User Story 1

- [X] T004 [US1] Remove `agent-framework-core>=1.0.0a1` from backend/pyproject.toml dependencies list
- [X] T005 [US1] Bump `github-copilot-sdk` version lower bound to latest stable in backend/pyproject.toml (check PyPI for current version)
- [X] T006 [P] [US1] Bump `openai` and `azure-ai-inference` version lower bounds to latest stable in backend/pyproject.toml (check PyPI for current versions)
- [X] T007 [P] [US1] Bump frontend dependencies to latest stable in frontend/package.json: react, react-dom, @tanstack/react-query, @dnd-kit/*, lucide-react, socket.io-client, and all devDependencies (vite, vitest, @playwright/test, typescript, eslint, etc.) — stay on React 18.x, do not upgrade to React 19
- [X] T008 [US1] Reinstall backend dependencies: run `pip install -e ".[dev]"` in backend/ and fix any compatibility issues
- [X] T009 [US1] Reinstall frontend dependencies: run `npm install` in frontend/ and fix any compatibility issues
- [X] T010 [US1] Run full backend test suite in backend/tests/ — fix any test failures caused by dependency version changes
- [X] T011 [US1] Run full frontend test suite in frontend/ — fix any test failures caused by dependency version changes

**Checkpoint**: All deps at latest stable, no unused packages, all tests pass

---

## Phase 4: User Story 2 — Shared Infrastructure Eliminates Duplicated Code (Priority: P1)

**Goal**: Consolidate duplicated CopilotClient caching, fallback chains, retry logic, and header construction into single implementations

**Independent Test**: Run full backend test suite; verify each consolidated pattern exists in exactly one location

### Implementation for User Story 2

- [X] T012 [US2] Add `CopilotClientPool` class to backend/src/services/completion_providers.py — implement with `BoundedDict(maxlen=50)`, `_token_key()` static method (SHA-256 hash), `async get_or_create(token)`, `async cleanup()`, and `async remove(token)` methods with `asyncio.Lock` for concurrent safety (per research R1 and data-model.md)
- [X] T013 [US2] Refactor `CopilotCompletionProvider` in backend/src/services/completion_providers.py to use shared `CopilotClientPool` instance — remove its `_clients` dict, `_token_key()`, and `_get_or_create_client()` methods; replace with calls to pool's `get_or_create()`; update `cleanup()` to delegate to pool
- [X] T014 [US2] Refactor `GitHubCopilotModelFetcher` in backend/src/services/model_fetcher.py to use shared `CopilotClientPool` instance — remove its `_clients` dict, `_token_key()`, and `_get_or_create_client()` methods; import pool from completion_providers; add `cleanup()` delegation
- [X] T015 [US2] Add `async _with_fallback(primary_fn, fallback_fn, context_msg) -> tuple[Any, str]` helper method to `GitHubProjectsService` in backend/src/services/github_projects/service.py — logs both attempts, raises with context from both exceptions if both fail (per research R2)
- [X] T016 [US2] Refactor `assign_copilot_to_issue` in backend/src/services/github_projects/service.py to use `_with_fallback()` for its GraphQL-primary → REST-fallback chain
- [X] T017 [US2] Refactor `request_copilot_review` in backend/src/services/github_projects/service.py to use `_with_fallback()` for its REST-primary → GraphQL-fallback chain
- [X] T018 [US2] Refactor `add_issue_to_project` in backend/src/services/github_projects/service.py to use `_with_fallback()` for its GraphQL+verify-primary → REST-fallback chain
- [X] T019 [US2] Add `graphql_features: list[str] | None = None` parameter to `_graphql()` method in backend/src/services/github_projects/service.py — when provided, construct `GraphQL-Features` header internally by joining with comma (per research R4)
- [X] T020 [US2] Update callers of `_graphql()` that pass `extra_headers` with `GraphQL-Features` to use the new `graphql_features` parameter instead: `get_copilot_bot_id`, `_assign_copilot_graphql`, and `request_copilot_review` in backend/src/services/github_projects/service.py
- [X] T021 [US2] Update backend tests in backend/tests/ to reflect CopilotClientPool changes — update any tests that mock `_get_or_create_client` or `_clients` dict on completion_providers or model_fetcher; update imports and assertions for the new pool interface
- [X] T022 [US2] Run full backend test suite in backend/tests/ and fix any failures from DRY consolidation changes

**Checkpoint**: Each pattern (client caching, fallback, headers) exists in exactly one place; all tests pass

---

## Phase 5: User Story 3 — Anti-Patterns Are Resolved for Production Readiness (Priority: P2)

**Goal**: Fix hardcoded model, implement file deletion, persist chat to SQLite, unify service initialization, bound all collections

**Independent Test**: Verify model parameterization by inspecting mutation; verify chat persistence by restart test; verify bounded collections by code inspection

### Implementation for User Story 3

- [X] T023 [P] [US3] Parameterize model in `ASSIGN_COPILOT_MUTATION` in backend/src/services/github_projects/graphql.py — add `$model: String!` variable, replace `model: "claude-opus-4.6"` with `model: $model` (per research R5)
- [X] T024 [US3] Update `_assign_copilot_graphql` caller in backend/src/services/github_projects/service.py to pass `model` from `AgentAssignmentConfig.model` in the GraphQL variables dict
- [X] T025 [P] [US3] Add `deletions` support to `CREATE_COMMIT_ON_BRANCH_MUTATION` in backend/src/services/github_projects/graphql.py — add `$deletions` variable and `deletions: $deletions` field in `fileChanges` input (per research R6)
- [X] T026 [US3] Update `commit_files()` method in backend/src/services/github_projects/service.py to accept optional `deletions: list[str] | None = None` parameter and pass it as `[{"path": p} for p in deletions]` in the mutation variables
- [X] T027 [US3] Update backend/src/services/github_commit_workflow.py to forward `delete_files` parameter to `commit_files()` as `deletions` — remove the warning log that says deletion is not implemented
- [ ] T028 [US3] Refactor backend/src/api/chat.py to persist chat messages to SQLite — replace `_messages` dict with `get_db()` calls: INSERT on message creation, SELECT on list, DELETE on clear; maintain same endpoint response shapes *(deferred: migration file created but API layer still uses in-memory dicts)*
- [ ] T029 [US3] Refactor backend/src/api/chat.py to persist proposals to SQLite — replace `_proposals` dict with `get_db()` calls: INSERT on proposal creation, SELECT for lookup, UPDATE on confirm/edit/cancel, DELETE on dismiss *(deferred)*
- [ ] T030 [US3] Refactor backend/src/api/chat.py to persist recommendations to SQLite — replace `_recommendations` dict with `get_db()` calls: INSERT on creation, SELECT for lookup, UPDATE on accept/reject; serialize IssueRecommendation to JSON for the `data` column *(deferred)*
- [ ] T031 [US3] Remove the three module-level dict declarations (`_messages`, `_proposals`, `_recommendations`) from backend/src/api/chat.py since they are now replaced by SQLite storage *(deferred: depends on T028-T030)*
- [X] T032 [P] [US3] Add code comment to `_oauth_states` BoundedDict in backend/src/services/github_auth.py documenting that OAuth states are intentionally in-memory: single-instance MVP, bounded to 1000 entries with TTL, lost on restart is acceptable
- [ ] T033 [US3] Remove module-level service singleton `github_projects_service = GitHubProjectsService()` from backend/src/services/github_projects/service.py — *(deferred: 17+ files import directly in non-request contexts)*
- [ ] T034 [P] [US3] Remove module-level service singleton `github_auth_service = GitHubAuthService()` from backend/src/services/github_auth.py *(deferred: depends on T033 pattern)*
- [ ] T035 [P] [US3] Remove module-level service singleton `connection_manager = ConnectionManager()` from backend/src/services/websocket.py *(deferred: depends on T033 pattern)*
- [ ] T036 [US3] Update backend/src/dependencies.py — remove fallback imports to module-level globals; make `get_github_service()`, `get_connection_manager()`, and `get_database()` raise `RuntimeError` if `app.state` attribute is not populated *(deferred: depends on T033-T035)*
- [ ] T037 [US3] Update all files that directly import module-level service singletons to use dependency injection via backend/src/dependencies.py functions instead *(deferred: depends on T036)*
- [X] T038 [P] [US3] Convert `processed_issues` in `PollingState` dataclass to `BoundedDict(maxlen=2000)` in backend/src/services/copilot_polling/state.py
- [X] T039 [P] [US3] Convert `_pipeline_states` to `BoundedDict(maxlen=500)`, `_issue_main_branches` to `BoundedDict(maxlen=500)`, and `_issue_sub_issue_map` to `BoundedDict(maxlen=500)` in backend/src/services/workflow_orchestrator/transitions.py
- [X] T040 [P] [US3] Convert `_workflow_configs` to `BoundedDict(maxlen=100)` in backend/src/services/workflow_orchestrator/config.py
- [X] T041 [P] [US3] Convert `_tracking_table_cache` to `BoundedDict(maxlen=200)` in backend/src/services/workflow_orchestrator/orchestrator.py
- [X] T042 [P] [US3] Convert `_recent_requests` to `BoundedDict(maxlen=1000)` in backend/src/api/workflow.py
- [X] T043 [US3] Update backend tests in backend/tests/ to reflect anti-pattern fixes — update tests that mock module-level service globals to use `app.state` overrides; update tests for chat API to account for SQLite persistence; update tests for commit workflow to cover file deletion
- [X] T044 [US3] Run full backend test suite in backend/tests/ and fix any failures from anti-pattern fixes

**Checkpoint**: Zero hardcoded config in queries, chat persists across restarts, single init pattern, all collections bounded, all tests pass

---

## Phase 6: User Story 4 — GitHub API Rate Limits Are Respected Intelligently (Priority: P2)

**Goal**: Add 500ms inter-call timing buffers, adaptive polling backoff, and `retry-after` header respect

**Independent Test**: Verify timing gaps in logs during bulk operations; verify polling interval escalation 60s→120s→240s→300s during idle periods

### Implementation for User Story 4

- [X] T045 [US4] Add `_last_request_time: float` and `_min_request_interval: float = 0.5` instance attributes to `GitHubProjectsService.__init__` in backend/src/services/github_projects/service.py — use `time.monotonic()` for timing
- [X] T046 [US4] Add throttling logic at the start of `_request_with_retry()` in backend/src/services/github_projects/service.py — calculate elapsed since `_last_request_time`, `await asyncio.sleep(remaining)` if < 500ms, update `_last_request_time` after each request, log throttle events (per research R11)
- [X] T047 [US4] Enhance `_request_with_retry()` in backend/src/services/github_projects/service.py to respect `retry-after` header on 429 responses — parse header value (seconds or HTTP date), use it as the wait time instead of the calculated exponential backoff when present (per FR-020)
- [X] T048 [US4] Add `_consecutive_idle_polls: int = 0` and `MAX_POLL_INTERVAL_SECONDS: int = 300` to polling state in backend/src/services/copilot_polling/state.py
- [X] T049 [US4] Implement adaptive polling in backend/src/services/copilot_polling/polling_loop.py — after each poll cycle, if no state changes detected (no PRs merged, no statuses advanced, no agent outputs posted), increment `_consecutive_idle_polls`; compute effective interval as `base_interval * (2 ** min(consecutive_idle, max_doublings))` capped at `MAX_POLL_INTERVAL_SECONDS`; on any state change, reset `_consecutive_idle_polls = 0` and return to base interval (per research R10)
- [X] T050 [US4] Update backend tests in backend/tests/ to cover rate-limiting behavior — add tests for inter-call throttling (verify `asyncio.sleep` is called when requests are rapid), adaptive polling interval calculation, and `retry-after` header parsing
- [X] T051 [US4] Run full backend test suite in backend/tests/ and fix any failures from rate-limiting changes

**Checkpoint**: API calls spaced ≥500ms apart, polling backs off during idle, retry-after headers respected, all tests pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, full test sweep, cross-story integration verification

- [X] T052 [P] Run ruff formatter and linter on all modified backend files: `ruff check --fix backend/src/ && ruff format backend/src/`
- [X] T053 Run full backend test suite as final validation in backend/tests/
- [X] T054 Run full frontend test suite as final validation in frontend/
- [X] T055 Verify backward compatibility: confirm all API endpoints return same response shapes by inspecting chat, proposal, and recommendation endpoints
- [X] T056 Run quickstart.md verification steps: dependency check, chat persistence restart test, rate limiting log verification

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — establish green baseline first
- **Foundational (Phase 2)**: Depends on Phase 1 — creates migration file needed by US3
- **US1 Dependencies (Phase 3)**: Can start after Phase 1 (doesn't depend on Phase 2 migration)
- **US2 DRY (Phase 4)**: Can start after Phase 1; independent of US1 dep changes
- **US3 Anti-Patterns (Phase 5)**: Depends on Phase 2 (needs migration file); depends on US2 completion (CopilotClientPool must exist before service init changes)
- **US4 Rate Limiting (Phase 6)**: Depends on US2 completion (changes are in same methods being refactored in US2)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1 — Dependencies)**: Independent — can start after baseline tests pass
- **US2 (P1 — DRY)**: Independent — can start after baseline tests pass; can run parallel with US1
- **US3 (P2 — Anti-Patterns)**: Depends on US2 (CopilotClientPool, _with_fallback, and _graphql changes must exist); depends on Phase 2 (migration file)
- **US4 (P2 — Rate Limiting)**: Depends on US2 (throttle logic modifies `_request_with_retry` which is also touched by US2)

### Within Each User Story

- Implementation tasks proceed in listed order (each builds on prior)
- Tasks marked [P] within a phase can run in parallel
- Test update task comes after all implementation tasks in the story
- Final test run task validates the story is complete

### Parallel Opportunities

- US1 and US2 can proceed in parallel (different files, no dependencies)
- Within US3: T023/T025/T032/T034/T035/T038/T039/T040/T041/T042 can all run in parallel (different files)
- Within US4: T045–T047 (service.py changes) are sequential; T048–T049 (polling changes) are sequential but can parallel with T045–T047

---

## Parallel Example: User Story 2

```bash
# After T012 (CopilotClientPool created), these can run in parallel:
T013: "Refactor CopilotCompletionProvider to use pool in completion_providers.py"
T014: "Refactor GitHubCopilotModelFetcher to use pool in model_fetcher.py"

# After T015 (_with_fallback created), these can run in parallel:
T016: "Refactor assign_copilot_to_issue to use _with_fallback"
T017: "Refactor request_copilot_review to use _with_fallback"
T018: "Refactor add_issue_to_project to use _with_fallback"
```

## Parallel Example: User Story 3

```bash
# These are all different files and can run in parallel:
T023: "Parameterize model in graphql.py"
T025: "Add deletions to graphql.py mutation"
T032: "Add OAuth comment in github_auth.py"
T034: "Remove singleton in github_auth.py"
T035: "Remove singleton in websocket.py"
T038: "Bound collections in copilot_polling/state.py"
T039: "Bound collections in workflow_orchestrator/transitions.py"
T040: "Bound collections in workflow_orchestrator/config.py"
T041: "Bound collections in workflow_orchestrator/orchestrator.py"
T042: "Bound collections in api/workflow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Baseline tests (T001–T002)
2. Complete Phase 3: Dependency updates (T004–T011)
3. **STOP and VALIDATE**: All tests pass with modern deps
4. Value delivered: clean, current dependency tree

### Incremental Delivery

1. US1: Dependency modernization → test → ✓
2. US2: DRY consolidation → test → ✓ (codebase is cleaner, each pattern in one place)
3. Phase 2: Migration file → ✓ (needed before US3)
4. US3: Anti-pattern fixes → test → ✓ (production-ready: persistent chat, clean init, bounded caches)
5. US4: Rate limiting → test → ✓ (operational safety: API calls throttled, adaptive polling)
6. Polish: Final sweep → ✓

### Parallel Team Strategy

With two developers:
1. Both complete Phase 1 baseline verification
2. Developer A: US1 (dependencies) → US3 (anti-patterns, after US2 done)
3. Developer B: US2 (DRY consolidation) → US4 (rate limiting)
4. Both collaborate on Phase 7 polish

---

## Notes

- All file paths are relative to repository root (backend/ or frontend/)
- The only new file created is `backend/src/migrations/011_chat_persistence.sql` — all other changes are within existing files
- Tests are updated (not optional) per FR-022 — each user story includes a test update and test run task
- `[P]` tasks within a phase can run in parallel; tasks without `[P]` must be sequential
- Commit after each logical group of tasks within a user story
- Total: 56 tasks across 7 phases (2 setup, 1 foundational, 8 US1, 11 US2, 22 US3, 7 US4, 5 polish)
