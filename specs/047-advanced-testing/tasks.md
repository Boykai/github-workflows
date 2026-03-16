# Tasks: Advanced Testing for Deep Unknown Bugs

**Input**: Design documents from `/specs/047-advanced-testing/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests ARE the feature deliverable — every phase produces test infrastructure or test code.

**Organization**: Tasks grouped by user story (7 stories from spec.md, P1–P7). Each story can be implemented and tested independently after Setup completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in this phase)
- **[Story]**: Which user story this task belongs to (US1–US7)
- All paths are relative to workspace root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and install dependencies for all 7 testing disciplines.

- [X] T001 Create backend test directory structure: `solune/backend/tests/concurrency/`, `solune/backend/tests/chaos/`, `solune/backend/tests/fuzz/` with `__init__.py` files in each
- [X] T002 [P] Add `pytest-repeat>=0.9.3` and `pytest-timeout>=2.2` to dev dependencies in `solune/backend/pyproject.toml`
- [X] T003 [P] Create frontend fuzz test directory `solune/frontend/src/__tests__/fuzz/` with a placeholder `.gitkeep`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared test utilities that multiple user stories depend on. MUST complete before user story phases.

**⚠️ CRITICAL**: US1 tasks depend on T004 for barrier helpers. US4/US5 reference models from T005.

- [X] T004 Create concurrency test conftest with `asyncio.Event` barrier helpers (`force_interleave`, `run_concurrent`) and common fixtures (fresh `PollingState`, isolated module globals) in `solune/backend/tests/concurrency/conftest.py`
- [X] T005 [P] Create Pydantic webhook payload models (`PullRequestEvent`, `IssuesEvent`, `PingEvent` with nested types as specified in `contracts/webhook-payloads.md`) in `solune/backend/src/api/webhook_models.py`
- [X] T006 [P] Create Zod dev-mode validation helper function `validateResponse<T>(schema, data, endpoint)` guarded by `import.meta.env.DEV` in `solune/frontend/src/services/schemas/validate.ts`

**Checkpoint**: Foundation ready — user story implementation can begin. Stories US1–US7 can proceed in parallel.

---

## Phase 3: User Story 1 — Concurrency & Race Condition Testing (Priority: P1) 🎯 MVP

**Goal**: Detect race conditions in shared polling state, multi-step database operations, and concurrent async task access. Covers FR-001, FR-002, FR-003.

**Independent Test**: Run `pytest solune/backend/tests/concurrency/ -v` — any invariant violation or duplicate polling loop is a confirmed bug.

### Implementation for User Story 1

- [X] T007 [P] [US1] Create polling state race condition stress tests (spawn 10+ concurrent coroutines accessing `_polling_state`, `_polling_task`, `_processed_issue_prs`, `_pending_agent_assignments`; assert single-active-loop invariant and bounded-collection size invariants) in `solune/backend/tests/concurrency/test_polling_races.py`
- [X] T008 [P] [US1] Create transaction safety tests that inject `asyncio.CancelledError` and `aiosqlite.OperationalError` between steps of `update_pipeline_state()` and `bulk_update()` in `pipeline_state_store.py`, verifying no half-committed state remains in `solune/backend/tests/concurrency/test_transaction_safety.py`
- [X] T009 [US1] Create forced-interleaving tests using `asyncio.Event` barriers from T004 conftest to reproduce specific orderings (Task A reads state → Task B writes state → Task A writes stale value) against `copilot_polling/state.py` globals in `solune/backend/tests/concurrency/test_interleaving.py`

**Checkpoint**: Concurrency test suite runs independently. SC-001 verified — at least one real race condition reproduced.

---

## Phase 4: User Story 2 — Fault Injection & Chaos Testing (Priority: P2)

**Goal**: Systematically inject failures into every external service dependency and background loop. Covers FR-004, FR-005, FR-006.

**Independent Test**: Run `pytest solune/backend/tests/chaos/ -v` — expected behaviors: correct retry/backoff, no spin-looping, message loss logged.

### Implementation for User Story 2

- [X] T010 [P] [US2] Create external service fault injection tests: inject `TimeoutError`, `ConnectionError`, `httpx.ReadTimeout`, partial-response dicts, and `asyncio.CancelledError` into `GitHubProjectsService._with_fallback()` (both primary and fallback paths), `AIAgentService`, and `GitHubAuthService` calls; verify correct error propagation and logging in `solune/backend/tests/chaos/test_fault_injection.py`
- [X] T011 [P] [US2] Create background loop resilience tests: start `_polling_watchdog_loop()` and `_session_cleanup_loop()` from `main.py` with mocked inner tasks that raise exceptions; verify watchdog restarts without spin-looping (assert minimum interval between restarts), verify cleanup loop uses exponential backoff in `solune/backend/tests/chaos/test_background_loops.py`
- [X] T012 [US2] Create Signal message loss demonstration test: start `_process_inbound_ws_message()` from `signal_bridge.py` with a message that triggers a processing error; assert the message content is logged with sufficient detail for reconstruction (SC-003) in `solune/backend/tests/chaos/test_signal_message_loss.py`

**Checkpoint**: Fault injection suite runs independently. SC-002 verified — at least one unhandled failure path discovered. SC-003 verified — Signal message loss demonstrated.

---

## Phase 5: User Story 3 — Stateful Property-Based Testing (Priority: P3)

**Goal**: Explore thousands of random state transitions for pipeline lifecycle and bounded caches. Covers FR-007, FR-008.

**Independent Test**: Run `pytest solune/backend/tests/property/test_pipeline_state_machine.py solune/backend/tests/property/test_bounded_cache_stateful.py -v` — 10,000+ transitions explored per test.

### Implementation for User Story 3

- [X] T013 [P] [US3] Create pipeline state machine model using Hypothesis `RuleBasedStateMachine`: define rules for start, advance_agent, fail_agent, skip_agent, complete_pipeline, cancel_pipeline; enforce invariants after each step (`current_agent_index` in bounds, `completed_agents` subset of all agents, no back-transitions from terminal states, parallel-mode completion requires all agents done); configure `settings(max_examples=200, stateful_step_count=50)` for 10,000+ transitions in `solune/backend/tests/property/test_pipeline_state_machine.py`
- [X] T014 [P] [US3] Create bounded cache stateful property tests using Hypothesis `RuleBasedStateMachine`: define rules for `add`, `get`, `delete`, `contains`, `len` on `BoundedDict` and `BoundedSet` from `src/utils.py`; enforce invariants (`len <= maxlen`, FIFO eviction order, LRU refresh on re-add, `on_evict` callback count matches evictions) in `solune/backend/tests/property/test_bounded_cache_stateful.py`

**Checkpoint**: Stateful property suite runs independently. SC-004 verified — 10,000+ transitions with zero invalid states (or confirmed bug found).

---

## Phase 6: User Story 4 — Runtime Type Validation (Priority: P4)

**Goal**: Add runtime validation schemas for the 5 highest-traffic frontend API responses (Zod) and webhook payloads (Pydantic). Covers FR-009, FR-010, FR-011.

**Independent Test**: Deliberately change a backend response field → frontend Zod catches it in dev mode. Send webhook missing a required field → Pydantic rejects it.

### Implementation for User Story 4

- [X] T015 [P] [US4] Create Zod schema for `ProjectsListResponse` (matching `contracts/api-response-schemas.md` ProjectSchema definition) in `solune/frontend/src/services/schemas/projects.ts`
- [X] T016 [P] [US4] Create Zod schema for `BoardDataResponse` (matching `contracts/api-response-schemas.md` BoardDataResponseSchema definition) in `solune/frontend/src/services/schemas/board.ts`
- [X] T017 [P] [US4] Create Zod schema for `ChatMessagesResponse` (matching `contracts/api-response-schemas.md` ChatMessagesResponseSchema definition) in `solune/frontend/src/services/schemas/chat.ts`
- [X] T018 [P] [US4] Create Zod schema for `PipelineStateInfo` (matching `contracts/api-response-schemas.md` PipelineStateInfoSchema definition) in `solune/frontend/src/services/schemas/pipeline.ts`
- [X] T019 [P] [US4] Create Zod schema for `EffectiveUserSettings` (matching `contracts/api-response-schemas.md` EffectiveUserSettingsSchema definition) in `solune/frontend/src/services/schemas/settings.ts`
- [X] T020 [US4] Integrate dev-mode Zod validation into the 5 API response methods (`projectsApi.getUserProjects`, `boardApi.getBoardData`, `chatApi.getMessages`, `settingsApi.getUserSettings`, `workflowApi.getPipelineState`) using `validateResponse()` from T006 in `solune/frontend/src/services/api.ts`
- [X] T021 [US4] Integrate Pydantic webhook models from T005 into the `github_webhook()` handler: parse `pull_request` events with `PullRequestEvent.model_validate(raw)`, `issues` events with `IssuesEvent.model_validate(raw)`, `ping` events with `PingEvent.model_validate(raw)`; add `try/except ValidationError` returning 422 with detail in `solune/backend/src/api/webhooks.py`
- [X] T022 [US4] Wrap unguarded `JSON.parse(event.data)` at line 49 of `useRealTimeSync.ts` in try-catch with `console.warn` on parse failure (matching the existing pattern in `usePipelineReducer.ts` line 103) in `solune/frontend/src/hooks/useRealTimeSync.ts`
- [X] T023 [US4] Create untyped data round-trip tests: store unexpected shapes (deeply nested objects, null values, unicode keys, empty objects, arrays-as-values) through `pipeline_state_store.py` write/read cycle and `webhook_models.py` parse/serialize cycle; assert data is preserved or correctly rejected in `solune/backend/tests/integration/test_runtime_validation.py`
- [X] T023b [P] [US4] Create Zod field-rename verification test: pass a mock API response with a deliberately renamed required field (e.g., `project_id` → `projectId`) through `validateResponse()` and assert a `ZodError` is thrown in dev mode in `solune/frontend/src/__tests__/fuzz/zodFieldRename.test.ts`

**Checkpoint**: Runtime validation active in dev mode. SC-005 verified — backend field rename caught by frontend (T023b). SC-006 verified — malformed webhook rejected with clear error.

---

## Phase 7: User Story 5 — Fuzz Testing for Parsing Boundaries (Priority: P5)

**Goal**: Fuzz all parsing boundaries where external/untrusted data enters the system. Covers FR-012, FR-013, FR-014.

**Independent Test**: Run `pytest solune/backend/tests/fuzz/ -v` and `npx vitest run solune/frontend/src/__tests__/fuzz/` — no unhandled exceptions on any generated input.

### Implementation for User Story 5

- [X] T024 [P] [US5] Create webhook payload fuzz tests using Hypothesis strategies (`st.dictionaries(st.text(), st.recursive(st.none() | st.booleans() | st.integers() | st.text(), lambda children: st.lists(children) | st.dictionaries(st.text(), children)))`) against `handle_pull_request_event()`, `handle_issues_event()`, webhook model `model_validate()`, AND the `github_webhook()` dispatch path with random `x-github-event` header values (including unrecognized event types); assert no unhandled exceptions in `solune/backend/tests/fuzz/test_webhook_fuzz.py`
- [X] T025 [P] [US5] Create markdown rendering fuzz tests using Hypothesis `st.text(alphabet=st.characters(categories=("L","N","P","S","Z")))` for agent names and model names passed to `format_agent_status_table()` and markdown table generation functions in `agent_tracking.py`; verify output contains no broken table syntax in `solune/backend/tests/fuzz/test_markdown_fuzz.py`
- [X] T026 [P] [US5] Create frontend JSON.parse fuzz tests using `@fast-check/vitest` with `fc.json()`, `fc.string()`, empty strings, `"{}"`, deeply nested objects (depth 50+), and valid-but-empty objects (`{}`); exercise the `onmessage` handler pattern from `useRealTimeSync.ts` and `usePipelineReducer.ts` DISCARD_EDITING case; also test Zod schema `.parse({})` with empty objects to verify graceful error; assert no unhandled throw in `solune/frontend/src/__tests__/fuzz/jsonParse.test.ts`

**Checkpoint**: Fuzz suite runs independently. SC-007 verified — at least one crash/exception found and subsequently fixed.

---

## Phase 8: User Story 6 — Integration Testing Without Mocks (Priority: P6)

**Goal**: Wire real internal components (database, services, middleware) with only external services mocked. Covers FR-015, FR-016.

**Independent Test**: Run `pytest solune/backend/tests/integration/ -v` — critical user flows succeed with real wiring, migrations apply sequentially.

### Implementation for User Story 6

- [X] T027 [US6] Create thin-mock integration conftest: provide a `TestClient` using the real FastAPI `app` with `dependency_overrides` for ONLY `GitHubProjectsService`, `GitHubAuthService`, `AIAgentService`, and Signal bridge (keep real database via in-memory SQLite with migrations applied, real middleware, real `WebSocketManager`, real settings); include an `autouse` session-scoped fixture that calls `ws_manager.shutdown()` in teardown to ensure WebSocket connections are cleaned up between tests in `solune/backend/tests/integration/conftest.py`
- [X] T028 [US6] Create migration regression tests: apply each of the 5 SQL migration files (023–027) one at a time to a fresh in-memory SQLite database; after each migration verify expected tables/columns exist; insert test data at migration N and verify it survives migration N+1; verify final schema matches consolidated schema in `solune/backend/tests/integration/test_migrations.py`
- [X] T029 [US6] Create thin-mock user flow integration tests: exercise critical paths (project selection → board data fetch, chat message send → response, pipeline start → state query) through the real HTTP endpoint layer with the thin-mock conftest from T027; assert successful end-to-end behavior without any `dependency_overrides` beyond external services in `solune/backend/tests/integration/test_thin_mock_flows.py`

**Checkpoint**: Integration suite runs independently. SC-008 verified — at least one wiring bug found. SC-009 verified — all 5 migrations apply sequentially.

---

## Phase 9: User Story 7 — Flaky Test Detection & Test Quality (Priority: P7)

**Goal**: Automated flaky test detection and slow test reporting in CI. Covers FR-017, FR-018.

**Independent Test**: Trigger the flaky-detection workflow manually via `gh workflow run flaky-detection.yml`; verify it runs the suite 3x and reports inconsistent results.

### Implementation for User Story 7

- [X] T030 [P] [US7] Create `flaky-detection.yml` GitHub Actions workflow: schedule weekly cron; run backend `pytest --count=3 --timeout=60` (using pytest-repeat from T002) and frontend `npx vitest run --repeat=3`; compare results across runs and flag any test with inconsistent pass/fail; include summary annotation and artifact upload of flaky report in `.github/workflows/flaky-detection.yml`
- [X] T031 [US7] Add `--durations=20` flag to the existing backend pytest step in `.github/workflows/ci.yml` to report the 20 slowest tests on every CI run

**Checkpoint**: Flaky detection workflow deployable. SC-010 verified — flaky tests identifiable. SC-011 verified — new tests within 60s CI budget.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Threshold updates, documentation, and final validation across all stories.

- [X] T032 [P] Update backend `pytest` coverage `fail_under` threshold in `solune/backend/pyproject.toml` if new test files shift the measured coverage
- [X] T033 [P] Update frontend Vitest coverage thresholds in `solune/frontend/vitest.config.ts` if new schema files or test files shift coverage metrics
- [X] T034 [P] Add new test directories to pytest discovery in `solune/backend/pyproject.toml` `[tool.pytest.ini_options]` `testpaths` if not auto-discovered
- [X] T035 Measure CI time budget: run `pytest solune/backend/tests/ --durations=0 -q` and record total execution time; verify new tests add no more than 60 seconds vs baseline (SC-011)
- [X] T036 Run `quickstart.md` validation: execute all verification commands from `specs/047-advanced-testing/quickstart.md` and confirm expected outcomes

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └──→ Phase 2 (Foundational: T004 barriers, T005 models, T006 Zod helper)
        ├──→ Phase 3 (US1: Concurrency) — depends on T004 barrier helpers
        ├──→ Phase 4 (US2: Fault Injection) — no foundational dependency
        ├──→ Phase 5 (US3: Stateful Property) — no foundational dependency
        ├──→ Phase 6 (US4: Runtime Validation) — depends on T005 models, T006 helper
        ├──→ Phase 7 (US5: Fuzz Testing) — optionally uses T005 models
        ├──→ Phase 8 (US6: Integration) — no foundational dependency
        └──→ Phase 9 (US7: Flaky Detection) — depends on T002 pytest-repeat
              └──→ Phase 10 (Polish) — after all desired stories complete
```

### User Story Dependencies

- **US1 (P1)**: Depends on T004 (concurrency conftest). No dependency on other stories.
- **US2 (P2)**: No foundational dependency. No dependency on other stories.
- **US3 (P3)**: No foundational dependency. No dependency on other stories.
- **US4 (P4)**: Depends on T005 (Pydantic models) and T006 (Zod helper). No dependency on other stories.
- **US5 (P5)**: Optionally uses T005 models as fuzz targets. Can also fuzz raw dict parsing without them.
- **US6 (P6)**: No foundational dependency. No dependency on other stories.
- **US7 (P7)**: Depends on T002 (pytest-repeat). No dependency on other stories.

### Within Each User Story

- Models/schemas before integration code
- Conftest/utilities before test files
- Core tests before cross-cutting validations

### Parallel Opportunities

**Setup (Phase 1)**: T002, T003 run in parallel.

**Foundational (Phase 2)**: T005, T006 run in parallel; T004 is independent.

**After Foundational completes, ALL user stories can run in parallel**:
- US1 (Phase 3): T007, T008 in parallel; T009 after
- US2 (Phase 4): T010, T011 in parallel; T012 after
- US3 (Phase 5): T013, T014 fully parallel
- US4 (Phase 6): T015–T019 (all 5 Zod schemas) fully parallel → T020, T021 after → T022, T023 after
- US5 (Phase 7): T024, T025, T026 fully parallel
- US6 (Phase 8): T027 first → T028, T029 parallel after
- US7 (Phase 9): T030, T031 parallel

---

## Parallel Example: User Story 4 (Runtime Type Validation)

```
               ┌─ T015 projects.ts ─┐
               ├─ T016 board.ts     ─┤
 T005,T006 ──→ ├─ T017 chat.ts      ─├──→ T020 (api.ts integration) ──→ T023 (round-trip tests)
               ├─ T018 pipeline.ts  ─┤    T021 (webhooks.py integration)
               └─ T019 settings.ts  ─┘    T022 (useRealTimeSync.ts)
```

## Implementation Strategy

### MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US1 Concurrency)**: The highest-confidence bug finder. Known unprotected shared state means real race conditions exist today. Delivers immediate value with 9 tasks (T001–T009).

### Incremental Delivery

Each subsequent phase adds an independent testing discipline:
1. **MVP**: US1 Concurrency (9 tasks) — finds bugs in shared polling state
2. **+US2**: Fault Injection (3 tasks) — surfaces unhandled failure paths and Signal message loss
3. **+US3**: Stateful Property (2 tasks) — explores 10,000+ pipeline state transitions
4. **+US4**: Runtime Validation (9 tasks) — catches type drift at frontend/backend boundary
5. **+US5**: Fuzz Testing (3 tasks) — finds parsing crashes from malformed input
6. **+US6**: Integration (3 tasks) — discovers wiring bugs hidden by mocks
7. **+US7**: Flaky Detection (2 tasks) + Polish (4 tasks) — ongoing test quality
