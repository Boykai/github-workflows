# Tasks: Backend Modernization & Improvement

**Input**: Design documents from `/specs/002-backend-modernization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Verification tests are included per the spec requirement (6 specific verification steps mandated in the parent issue).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/backend/tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — no new project scaffolding needed; this feature modifies an existing codebase.

- [ ] T001 Create feature branch from `002-backend-modernization` and verify Python 3.13 dev environment in `solune/backend/`
- [ ] T002 [P] Verify existing tests pass with `cd solune/backend && python -m pytest tests/ -v`
- [ ] T003 [P] Run baseline lint with `cd solune/backend && python -m ruff check src/` and record current RUF006 suppression state in `solune/backend/pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core async safety infrastructure that MUST be complete before ANY user story can be safely implemented. Phase 1 of the plan (Critical Async Safety) is the foundational prerequisite because TaskRegistry and TaskGroup are used by data integrity (Phase 2), security (Phase 3), and performance (Phase 4) work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### 2A: TaskRegistry (New Module)

- [ ] T004 Create `TaskRegistry` singleton class in `solune/backend/src/services/task_registry.py` with `create_task(coro, *, name)`, `drain(timeout)`, `cancel_all()`, and `pending_count` property per data-model.md and async-safety-contracts.md
- [ ] T005 Add done-callback in `TaskRegistry.create_task()` that auto-removes completed tasks and logs failures at WARNING level in `solune/backend/src/services/task_registry.py`
- [ ] T006 Implement `TaskRegistry.drain(timeout)` using `asyncio.wait()` with timeout, cancelling undrained tasks and returning them for caller inspection in `solune/backend/src/services/task_registry.py`
- [ ] T007 Write unit tests for `TaskRegistry` (create, drain, cancel_all, concurrent create during drain, exception logging) in `solune/backend/tests/test_task_registry.py`

### 2B: TaskGroup Adoption

- [ ] T008 Refactor `lifespan()` in `solune/backend/src/main.py` to use `asyncio.TaskGroup` for startup background tasks (`_session_cleanup_loop`, `_polling_watchdog_loop`, Signal WebSocket listener, agent MCP sync) replacing manual `create_task()` + `cancel()` pattern
- [ ] T009 Ensure each background task loop in `solune/backend/src/main.py` catches `asyncio.CancelledError` for graceful cleanup and catches general `Exception` internally to prevent cross-task cancellation via `ExceptionGroup`
- [ ] T010 Integrate `TaskRegistry.drain()` call in the lifespan shutdown path in `solune/backend/src/main.py` before database connections are closed

### 2C: TaskRegistry Adoption Across Codebase

- [ ] T011 [P] Replace `asyncio.create_task()` with `task_registry.create_task()` in `solune/backend/src/api/chat.py` (signal delivery task ~line 681)
- [ ] T012 [P] Replace `asyncio.create_task()` with `task_registry.create_task()` in `solune/backend/src/api/signal.py` (signal post link task)
- [ ] T013 [P] Replace `asyncio.create_task()` with `task_registry.create_task()` in `solune/backend/src/services/signal_bridge.py` (AI processing task ~line 667)
- [ ] T014 [P] Replace `asyncio.create_task()` with `task_registry.create_task()` in `solune/backend/src/services/signal_delivery.py` (delivery task ~line 279)
- [ ] T015 [P] Replace `asyncio.create_task()` with `task_registry.create_task()` in `solune/backend/src/services/copilot_polling/__init__.py` (poll task ~line 285)
- [ ] T016 [P] Replace `asyncio.create_task()` with `task_registry.create_task()` in `solune/backend/src/services/model_fetcher.py` (background refresh ~line 323)
- [ ] T017 [P] Replace `asyncio.create_task()` with `task_registry.create_task()` in `solune/backend/src/services/github_projects/service.py` (GraphQL execution ~line 328)
- [ ] T018 [P] Replace `loop.create_task()` with `task_registry.create_task()` in `solune/backend/src/services/workflow_orchestrator/transitions.py` (transition coroutines)
- [ ] T019 Remove `"RUF006"` from the `ignore` list in `solune/backend/pyproject.toml` and verify zero violations with `ruff check --select=RUF006 src/`

### 2D: External API Timeout Guards

- [ ] T020 Add `api_timeout_seconds` setting (default: 30) to `solune/backend/src/config.py`
- [ ] T021 Wrap `client.async_graphql()` calls with `asyncio.wait_for(coro, timeout=settings.api_timeout_seconds)` in `solune/backend/src/services/github_projects/service.py` and raise structured `AppException` on timeout
- [ ] T022 [P] Audit and add timeout guards to model fetcher external calls in `solune/backend/src/services/model_fetcher.py`
- [ ] T023 [P] Audit and add timeout guards to copilot polling external calls in `solune/backend/src/services/copilot_polling/__init__.py`

### 2E: WebSocket Reconnection Fix

- [ ] T024 Add exponential backoff with jitter (base=1s, cap=300s) for WebSocket reconnection in `solune/backend/src/services/signal_bridge.py` replacing flat 5s/10s sleep delays
- [ ] T025 Add `finally` block ensuring WebSocket is explicitly closed before reconnection attempt in `solune/backend/src/services/signal_bridge.py`
- [ ] T026 Reset backoff counter to zero on successful WebSocket connection in `solune/backend/src/services/signal_bridge.py`

**Checkpoint**: Foundation ready — all async safety infrastructure in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Safe Application Shutdown with No Resource Leaks (Priority: P1) 🎯 MVP

**Goal**: When the backend shuts down, all background tasks complete or cancel within 30s, all WebSocket connections close, and no "task was destroyed but it is pending" warnings appear.

**Independent Test**: Trigger graceful shutdown (SIGTERM), verify all tasks complete/cancel within bounded time, zero resource leak warnings in logs.

### Verification Tests for User Story 1

- [ ] T027 [US1] Write shutdown integration test: send SIGTERM, verify no "task was destroyed but it is pending" warnings and all tasks complete/cancel within 30s in `solune/backend/tests/test_shutdown.py`
- [ ] T028 [US1] Write verification test: run `ruff check --select=ASYNC,RUF006 src/` and assert zero violations in `solune/backend/tests/test_lint_async.py`
- [ ] T029 [US1] Write integration test: drop signal-cli WebSocket mid-connection, verify reconnect with exponential backoff timing in `solune/backend/tests/test_signal_reconnect.py`

### Validation for User Story 1

- [ ] T030 [US1] Run full test suite and lint to verify Phase 2 + US1 changes work together: `cd solune/backend && python -m pytest tests/ -v && python -m ruff check src/`

**Checkpoint**: User Story 1 is complete — safe shutdown with no resource leaks.

---

## Phase 4: User Story 2 — Reliable Data Persistence with No Silent Data Loss (Priority: P1)

**Goal**: Chat messages, proposals, and recommendations are reliably persisted to SQLite as the single source of truth. Persistence failures are surfaced (not silently swallowed). Multi-step operations use transactions. Admin promotion is race-condition-safe.

**Independent Test**: Send chat messages, force a persistence failure, verify the error is reported, restart the app, confirm all successfully persisted data is restored.

### Implementation for User Story 2

- [ ] T031 [US2] Refactor `_messages`, `_proposals`, `_recommendations` in `solune/backend/src/api/chat.py` from primary stores to read-through caches backed by SQLite as single source of truth per data-integrity-contracts.md
- [ ] T032 [US2] Add `asyncio.Lock` per session for cache updates in `solune/backend/src/api/chat.py` to prevent concurrent modification during writes
- [ ] T033 [US2] Implement read-through cache path: cache hit returns cached data, cache miss queries SQLite and populates cache under lock in `solune/backend/src/api/chat.py`
- [ ] T034 [US2] Replace bare `except Exception` + `logger.warning()` in `_persist_*` functions with retry mechanism (3 attempts, exponential backoff: 100ms/200ms/400ms) in `solune/backend/src/api/chat.py`
- [ ] T035 [US2] Propagate persistent failures (non-transient) to caller as `PersistenceError` exception after retries exhausted in `solune/backend/src/api/chat.py`
- [ ] T036 [US2] Add structured logging with failure context (session_id, message_id, attempt number) to persistence retry logic in `solune/backend/src/api/chat.py`
- [ ] T037 [US2] Add `BEGIN IMMEDIATE` transaction boundaries to multi-step write operations in `solune/backend/src/services/chat_store.py` with commit on success and rollback on exception
- [ ] T038 [US2] Add savepoint support for nested transactions in `solune/backend/src/services/chat_store.py` using `SAVEPOINT`/`RELEASE`/`ROLLBACK TO` pattern
- [ ] T039 [US2] Fix admin auto-promotion race condition in `solune/backend/src/dependencies.py`: verify `cursor.rowcount` after conditional `UPDATE ... WHERE admin_github_user_id IS NULL`, handle lost-race case (rowcount==0) by re-reading admin and returning 403
- [ ] T040 [US2] Write concurrent admin promotion test: `asyncio.gather` with 10 simultaneous requests, assert exactly 1 succeeds in `solune/backend/tests/test_admin_race.py`

### Validation for User Story 2

- [ ] T041 [US2] Run persistence and admin race tests: `cd solune/backend && python -m pytest tests/test_admin_race.py -v`

**Checkpoint**: User Story 2 is complete — reliable data persistence with no silent data loss.

---

## Phase 5: User Story 3 — Hardened Security Posture (Priority: P2)

**Goal**: CSRF protection on state-changing endpoints, rate limiting that persists across session changes, project-scoped cache keys, and database indexes on critical columns.

**Independent Test**: Attempt CSRF attack and verify it is blocked; clear cookies and verify rate limits persist; confirm two projects with same issue number get different cached data.

### Implementation for User Story 3

- [ ] T042 [P] [US3] Create CSRF middleware implementing double-submit cookie pattern in `solune/backend/src/middleware/csrf.py`: generate token on session creation, validate `X-CSRF-Token` header against `csrf_token` cookie on POST/PUT/DELETE, exempt webhooks and OAuth callback
- [ ] T043 [US3] Register CSRF middleware in application startup in `solune/backend/src/main.py`
- [ ] T044 [P] [US3] Create database migration adding performance indexes in `solune/backend/src/migrations/` (new file): `idx_global_settings_admin`, `idx_user_sessions_project`, `idx_chat_messages_session`, `idx_chat_proposals_session` per security-performance-contracts.md
- [ ] T045 [P] [US3] Add `project_id` parameter to `cache_key_issue_pr()`, `cache_key_agent_output()`, and `cache_key_review_requested()` in `solune/backend/src/constants.py`, prefixing all project-scoped keys with `{project_id}:`
- [ ] T046 [US3] Update all callers of modified cache key functions to pass `project_id` across `solune/backend/src/services/` and `solune/backend/src/api/`
- [ ] T047 [P] [US3] Implement compound rate-limit key resolution middleware in `solune/backend/src/middleware/rate_limit.py`: pre-resolve `github_user_id` from session store, store in `request.state.rate_limit_key`, fall back to `ip:{remote_address}` for unauthenticated requests
- [ ] T048 [US3] Update slowapi `key_func` to read from `request.state.rate_limit_key` instead of session cookie in `solune/backend/src/middleware/rate_limit.py`

### Validation for User Story 3

- [ ] T049 [US3] Verify CSRF protection: test that POST without `X-CSRF-Token` returns 403 and POST with valid token succeeds in `solune/backend/tests/test_csrf.py`
- [ ] T050 [US3] Verify cache key scoping: assert `cache_key_issue_pr('PVT_a', 42, 101) != cache_key_issue_pr('PVT_b', 42, 101)` in `solune/backend/tests/`
- [ ] T051 [US3] Verify database indexes with `EXPLAIN QUERY PLAN` on indexed columns per security-performance-contracts.md

**Checkpoint**: User Story 3 is complete — hardened security posture.

---

## Phase 6: User Story 4 — Responsive System Under Load (Priority: P2)

**Goal**: Paginated endpoints, filtered startup queries, reduced metadata cache TTL, and safe task eviction in bounded collections.

**Independent Test**: Request paginated chat messages with `limit=5&offset=0` and verify exactly 5 results; verify metadata refreshes within 5 minutes.

### Implementation for User Story 4

- [ ] T052 [P] [US4] Add `WHERE workflow_config IS NOT NULL` filter and `LIMIT` clause to polling startup query in `solune/backend/src/main.py`, wrap JSON parse in `try/except` for malformed config
- [ ] T053 [US4] Add `limit` (default 50, max 200) and `offset` (default 0) query parameters to chat message endpoint in `solune/backend/src/api/chat.py`, apply `LIMIT ? OFFSET ?` in SQL via `solune/backend/src/services/chat_store.py`
- [ ] T054 [US4] Add pagination support to task listing endpoints in `solune/backend/src/api/` with same `limit`/`offset` parameters
- [ ] T055 [US4] Return pagination metadata (`items`, `total`, `limit`, `offset`) in paginated endpoint responses using `COUNT(*) OVER()` window function in `solune/backend/src/services/chat_store.py`
- [ ] T056 [P] [US4] Add `CACHE_TTL_METADATA_SECONDS` setting (default: 300) to `solune/backend/src/config.py` and apply to branch/label cache entries in `solune/backend/src/services/cache.py`
- [ ] T057 [P] [US4] Add optional `on_evict` callback to `BoundedDict` in `solune/backend/src/utils.py`: invoke callback with (key, value) before eviction, wrap in `try/except`, log at DEBUG level
- [ ] T058 [US4] Configure `BoundedDict` instances holding `asyncio.Task` values in `solune/backend/src/services/github_projects/service.py` and `solune/backend/src/services/model_fetcher.py` with `on_evict` callback that cancels non-done tasks

### Verification Tests for User Story 4

- [ ] T059 [US4] Write pagination test: `limit=5&offset=0` returns exactly 5 results, `offset` beyond total returns empty list with correct total in `solune/backend/tests/test_pagination.py`
- [ ] T060 [US4] Verify metadata cache TTL is 300s (5 minutes) in `solune/backend/src/config.py`

**Checkpoint**: User Story 4 is complete — responsive system under load.

---

## Phase 7: User Story 5 — Maintainable Codebase with Modern Python Patterns (Priority: P3)

**Goal**: Modern Python patterns (enums, protocols, TypedDict, consistent error handling) improve maintainability. CPU-bound work does not block the event loop. Backoff resets on success.

**Independent Test**: Run static analysis (type checker, linter) and verify no violations in modernized modules; verify CPU-bound operations do not block the event loop.

### Implementation for User Story 5

- [ ] T061 [P] [US5] Replace string constants with `ItemType(StrEnum)` and `LinkMethod(StrEnum)` in `solune/backend/src/services/cleanup_service.py` and update all call sites
- [ ] T062 [P] [US5] Create `Protocol` types for `ModelProvider` and `CacheInvalidationPolicy` interfaces in `solune/backend/src/protocols.py` (new file) and use in type hints
- [ ] T063 [P] [US5] Replace `dict[str, Any]` with `PollingStatus(TypedDict)` for `get_polling_status()` return type in `solune/backend/src/services/copilot_polling/__init__.py` and rate-limit info structures in `solune/backend/src/middleware/rate_limit.py`
- [ ] T064 [P] [US5] Apply `@handle_github_errors(operation)` decorator consistently to service methods making external calls in `solune/backend/src/services/github_projects/service.py`, `solune/backend/src/services/copilot_polling/__init__.py`, and `solune/backend/src/services/model_fetcher.py`
- [ ] T065 [US5] Add conditional `asyncio.to_thread()` wrapping for regex-heavy batch processing (>100 items) in `solune/backend/src/services/cleanup_service.py`
- [ ] T066 [US5] Verify and document backoff reset on success in `_polling_watchdog_loop()` and `_session_cleanup_loop()` in `solune/backend/src/main.py` — ensure `consecutive_failures = 0` is set after successful iteration

### Validation for User Story 5

- [ ] T067 [US5] Run linter and type checks on modernized modules: `cd solune/backend && python -m ruff check src/services/cleanup_service.py src/protocols.py --select=E,W,F`

**Checkpoint**: User Story 5 is complete — maintainable codebase with modern Python patterns.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation, and cross-cutting improvements across all user stories.

- [ ] T068 Run full test suite across all phases: `cd solune/backend && python -m pytest tests/ -v`
- [ ] T069 Run full lint including async safety rules: `cd solune/backend && python -m ruff check --select=ASYNC,RUF006 src/` — verify zero violations
- [ ] T070 Run quickstart.md end-to-end verification: execute all 13 verification scenarios from `specs/002-backend-modernization/quickstart.md` (TaskGroup shutdown, TaskRegistry drain, RUF006 compliance, API timeouts, persistence, admin race, CSRF, indexes, cache scoping, pagination, cache TTL, enums, error handling)
- [ ] T071 [P] Update inline code comments in modified files across `solune/backend/src/` to reflect new patterns (TaskRegistry usage, transaction boundaries, cache key scoping)
- [ ] T072 [P] Review all `except Exception` blocks across modified files in `solune/backend/src/` to ensure none silently swallow errors: every handler must either re-raise, log at ERROR level with full context, or return an error response to the caller

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
  - Phase 2A (TaskRegistry): No internal deps
  - Phase 2B (TaskGroup): No internal deps (parallel with 2A)
  - Phase 2C (TaskRegistry Adoption): Depends on 2A completion
  - Phase 2D (Timeout Guards): No internal deps (parallel with 2A/2B)
  - Phase 2E (WebSocket Fix): No internal deps (parallel with 2A/2B)
- **User Story 1 (Phase 3)**: Depends on Phase 2 — verification of foundational work
- **User Story 2 (Phase 4)**: Depends on Phase 2 (TaskRegistry for fire-and-forget)
- **User Story 3 (Phase 5)**: Depends on Phase 2 — can run in parallel with US2
- **User Story 4 (Phase 6)**: Depends on Phase 4 (specifically T031-T033 chat refactor for pagination)
- **User Story 5 (Phase 7)**: No story dependencies — can run in parallel with US3/US4
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Verification-only phase — tests that Phase 2 foundational work is correct
- **User Story 2 (P1)**: Can start after Phase 2 — independent of US1 verification tests
- **User Story 3 (P2)**: Can start after Phase 2 — fully independent of US1 and US2
- **User Story 4 (P2)**: Depends on US2 (chat endpoint refactor) for pagination; other tasks are independent
- **User Story 5 (P3)**: Fully independent — can start after Phase 2

### Within Each User Story

- Models/infrastructure before services
- Services before endpoints
- Core implementation before integration
- Validation at the end of each story

### Parallel Opportunities

- **Phase 2A + 2B + 2D + 2E**: All can run in parallel (different files, no dependencies)
- **Phase 2C**: All T011–T018 can run in parallel (different files)
- **US2 + US3 + US5**: Can proceed in parallel after Phase 2
- **Within US3**: T042 + T044 + T045 + T047 can all run in parallel (different files)
- **Within US4**: T052 + T056 + T057 can run in parallel (different files)
- **Within US5**: T061 + T062 + T063 + T064 can all run in parallel (different files)

---

## Parallel Example: Foundational Phase

```
# Launch Phase 2A (TaskRegistry) and 2B (TaskGroup) in parallel:
Task: T004 "Create TaskRegistry singleton in solune/backend/src/services/task_registry.py"
Task: T008 "Refactor lifespan() to use asyncio.TaskGroup in solune/backend/src/main.py"

# Simultaneously launch timeout and WebSocket work:
Task: T020 "Add api_timeout_seconds setting in solune/backend/src/config.py"
Task: T024 "Add exponential backoff in solune/backend/src/services/signal_bridge.py"

# After TaskRegistry is ready, launch all adoption tasks in parallel:
Task: T011 "Replace create_task in solune/backend/src/api/chat.py"
Task: T012 "Replace create_task in solune/backend/src/api/signal.py"
Task: T013 "Replace create_task in solune/backend/src/services/signal_bridge.py"
Task: T014 "Replace create_task in solune/backend/src/services/signal_delivery.py"
Task: T015 "Replace create_task in solune/backend/src/services/copilot_polling/__init__.py"
Task: T016 "Replace create_task in solune/backend/src/services/model_fetcher.py"
Task: T017 "Replace create_task in solune/backend/src/services/github_projects/service.py"
Task: T018 "Replace create_task in solune/backend/src/services/workflow_orchestrator/transitions.py"
```

## Parallel Example: User Story 3 (Security Hardening)

```
# Launch all independent security tasks in parallel:
Task: T042 "Create CSRF middleware in solune/backend/src/middleware/csrf.py"
Task: T044 "Create database migration for indexes in solune/backend/src/migrations/"
Task: T045 "Add project_id to cache key functions in solune/backend/src/constants.py"
Task: T047 "Implement compound rate-limit key in solune/backend/src/middleware/rate_limit.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational — async safety infrastructure (T004–T026)
3. Complete Phase 3: User Story 1 — verify shutdown behavior (T027–T030)
4. **STOP and VALIDATE**: Trigger shutdown, verify zero resource leaks
5. Deploy/demo if ready — critical safety fixes are in place

### Incremental Delivery

1. Complete Setup + Foundational → Async safety infrastructure ready
2. Add User Story 1 (verification) → Confirm shutdown safety → **MVP delivered**
3. Add User Story 2 (data integrity) → Test persistence reliability → Deploy
4. Add User Story 3 (security) → Test CSRF/rate-limit/cache scoping → Deploy
5. Add User Story 4 (performance) → Test pagination/TTL/eviction → Deploy
6. Add User Story 5 (modern patterns) → Lint/type-check clean → Deploy
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 2 (data integrity)
   - Developer B: User Story 3 (security hardening)
   - Developer C: User Story 5 (modern patterns)
3. After User Story 2 completes:
   - Developer A picks up User Story 4 (performance — depends on US2 chat refactor)
4. Stories integrate independently

---

## Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 72 |
| **Setup (Phase 1)** | 3 |
| **Foundational (Phase 2)** | 23 |
| **User Story 1 — Safe Shutdown (P1)** | 4 |
| **User Story 2 — Data Persistence (P1)** | 11 |
| **User Story 3 — Security Hardening (P2)** | 10 |
| **User Story 4 — Performance (P2)** | 9 |
| **User Story 5 — Modern Patterns (P3)** | 7 |
| **Polish (Phase 8)** | 5 |
| **Parallel opportunities** | 35 tasks marked [P] or parallelizable within phase |
| **MVP scope** | Phase 1 + Phase 2 + User Story 1 (30 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Phase 2 (Foundational) is the critical path — invest most upfront effort here
- User Stories 2 + 3 + 5 can proceed in parallel after foundational phase
- User Story 4 depends on User Story 2's chat endpoint refactor for pagination
