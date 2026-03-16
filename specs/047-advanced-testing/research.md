# Research: Advanced Testing for Deep Unknown Bugs

**Feature**: 047-advanced-testing  
**Date**: 2026-03-16

## R-001: Concurrency Primitives for Async Race Condition Testing

**Decision**: Use `asyncio.Event` barriers and `asyncio.gather()` to force deterministic task interleaving in pytest-asyncio tests.

**Rationale**: The `copilot_polling/state.py` module has 10+ module-level mutable globals (`_polling_state`, `_polling_task`, `_processed_issue_prs`, `_pending_agent_assignments`, `_claimed_child_prs`, etc.) that are read/written by concurrent async tasks (polling loop, watchdog in `main.py`, API handlers). There is no `asyncio.Lock` protecting these globals — only `pipeline_state_store.py` uses `_store_lock = asyncio.Lock()` for its cache. The standard approach for deterministic concurrency testing in Python's single-threaded async model is to use `asyncio.Event` as barriers: Task A waits on `event_a`, Task B waits on `event_b`, and the test orchestrates which runs first by setting events in a controlled sequence. This doesn't require any external library — `pytest-asyncio` plus standard `asyncio` primitives are sufficient.

**Alternatives considered**:
- `trio` structured concurrency with `trio.testing` — More powerful but would require porting the entire async runtime; too invasive.
- `pytest-timeout` for detecting deadlocks — Useful as a safety net but doesn't help with controlled interleaving. Can be added as a `conftest.py` default.
- Threadpool-based concurrency tests — Inappropriate because the codebase is async-only; threading would test a different execution model.

## R-002: Fault Injection Strategy for External Services

**Decision**: Use `unittest.mock.AsyncMock(side_effect=...)` to inject specific exceptions (`TimeoutError`, `ConnectionError`, `asyncio.CancelledError`, partial-response dicts) into service calls. No external fault-injection library needed.

**Rationale**: The codebase already uses `AsyncMock` extensively in `tests/conftest.py` (mocking `GitHubProjectsService`, `GitHubAuthService`, `AIAgentService`). The `_with_fallback()` pattern in `github_projects/service.py` wraps primary/fallback callables — testing it requires injecting exceptions into both paths. The Signal bridge's `_process_inbound_ws_message()` catches generic `Exception` and logs but drops the message; the watchdog in `main.py` lines 220-270 has exponential backoff only in `_session_cleanup_loop` (correctly), but the `_polling_watchdog_loop` has no backoff — it retries every 30s regardless of failure count. These are concrete bugs to surface.

**Alternatives considered**:
- `toxiproxy` / `chaos-toolkit` — Designed for multi-service network chaos; overkill for a single-process async app with mocked external calls.
- `fault-injection` PyPI package — Unmaintained; `AsyncMock(side_effect=...)` is the standard pytest approach.

## R-003: Hypothesis Stateful Testing for Pipeline State Machine

**Decision**: Use Hypothesis `RuleBasedStateMachine` to model the pipeline lifecycle. The state model lives in `pipeline_state_store.py` and the orchestration logic in `orchestrator.py`.

**Rationale**: The pipeline state includes: `status` (idle/running/completed/failed/cancelled), `current_agent_index` (int), `completed_agents` (list), `execution_mode` (sequential/parallel), and `parallel_agent_statuses` (dict). The `BoundedDict` and `BoundedSet` (from `src/utils.py`) also have invariants (maxlen enforcement, FIFO eviction). Hypothesis `RuleBasedStateMachine` is ideal: rules map to transitions (start, advance, fail, skip, complete, cancel), invariants are checked after each step, and Hypothesis shrinks failing examples automatically. The existing `hypothesis>=6.131.0` dependency already supports this.

**Alternatives considered**:
- `pydantic-stateful` — Not a real package; would need custom implementation anyway.
- Manual state enumeration — Cannot explore the combinatorial space (10,000+ sequences) that Hypothesis traverses. Manual tests would catch only anticipated edge cases.

## R-004: Zod Schema Validation for Frontend API Responses

**Decision**: Add Zod schemas for the 5 highest-traffic API response types (`projectsApi`, `boardApi`, `chatApi`, `settingsApi`, `workflowApi`). Validate in development mode only using `import.meta.env.DEV` guard.

**Rationale**: Zod 4 is already in `package.json` (`"zod": "^4.3.6"`). The frontend has zero runtime validation — all TypeScript types are compile-time only. The five highest-traffic API namespaces (identified from `api.ts`): `projectsApi.getUserProjects()`, `boardApi.getBoardData()`, `chatApi.getMessages()`, `settingsApi.getUserSettings()`, `workflowApi.getPipelineState()`. Each returns a shaped object that the frontend destructures without safety. Wrapping responses in `schema.parse()` (dev mode) or `schema.safeParse()` (logging-only) catches backend drift immediately. The `import.meta.env.DEV` guard ensures zero production overhead (Vite tree-shakes dead dev-only code).

**Alternatives considered**:
- `io-ts` / `runtypes` — Zod is already installed, more ergonomic, and has a larger ecosystem.
- OpenAPI-generated types via `openapi-typescript` — Already in the project (from feature 046) but only generates compile-time types, not runtime validators.
- Validation in a custom `fetch` wrapper — Too coarse; per-endpoint schemas allow precise error messages.

## R-005: Pydantic Models for Webhook Payloads

**Decision**: Create discriminated-union Pydantic models for the 3 handled webhook event types (`PullRequestEvent`, `IssuesEvent`, `PingEvent`) and validate payloads in the `github_webhook()` handler.

**Rationale**: Currently `webhooks.py` parses payloads as `dict[str, Any]` and navigates with chained `.get()` calls (e.g., `payload.get("pull_request", {}).get("user", {}).get("login", "")`). This silently returns empty strings on missing fields instead of raising errors. Pydantic 2 models with discriminated unions (`event_type` field) will: (a) validate required fields at parse time, (b) provide IDE autocompletion, (c) self-document the expected payload structure. The models only need to cover the fields actually accessed — not the entire GitHub API schema.

**Alternatives considered**:
- Full GitHub webhook type stubs from `githubkit` — Already in the venv but the models are massive (hundreds of optional fields). A focused subset covering only accessed fields is simpler and more maintainable.
- `TypedDict` — Provides type hints but no runtime validation; defeats the purpose.

## R-006: Fuzz Testing Approach

**Decision**: Use Hypothesis strategies (`st.dictionaries()`, `st.text()`, `st.recursive()`) for backend fuzz testing. Use Vitest with `@fast-check/vitest` for frontend JSON.parse fuzz testing.

**Rationale**: Backend: Hypothesis is already a dependency and provides composable strategies for generating random JSON-like payloads. The webhook handler's `handle_pull_request_event()` and `_process_inbound_ws_message()` accept `dict` arguments — Hypothesis can generate arbitrary dicts that pass structural checks but have unexpected shapes. Frontend: `@fast-check/vitest` is already installed (from feature 046) and integrates property-based testing directly into Vitest test files. The `JSON.parse` call in `useRealTimeSync.ts` (line 49) has no try-catch; `usePipelineReducer.ts` (line 103) wraps it in try-catch correctly.

**Alternatives considered**:
- `atheris` (Python coverage-guided fuzzer) — Requires C compilation, complex setup, and is designed for finding memory corruption bugs in C extensions. Overkill for Python-level logic bugs.
- Manual malformed-payload lists — Cannot match the coverage of random generation. Used as a supplement (known-bad inputs) alongside generated ones.

## R-007: Thin-Mock Integration Testing Strategy

**Decision**: Create a second `conftest.py` in `tests/integration/` that provides a test client with real internal wiring (real database, real services, real middleware) but mocked external calls (GitHub API, LLM, Signal API).

**Rationale**: The current root `tests/conftest.py` has 5 `dependency_overrides` and 7 mock fixtures (GitHub service, auth service, AI agent service, WebSocket manager, session, access token, settings). This means tests never exercise the real dependency injection wiring. A thin-mock fixture would: override only `GitHubProjectsService`, `GitHubAuthService`, `AIAgentService`, and Signal bridge calls while keeping the real database, real middleware, real WebSocket manager, and real settings. The existing migration system (5 SQL files, 023–027) applies in-memory during test setup. Critical flows to test: project selection → board data fetch → chat message send.

**Alternatives considered**:
- Testcontainers — Not applicable (SQLite is already in-memory; no external database to containerize).
- Full E2E with Playwright — Already exists for visual regression; the goal here is backend wiring, not frontend rendering.

## R-008: Flaky Test Detection CI Strategy

**Decision**: Add a `flaky-detection.yml` GitHub Actions workflow running weekly with `pytest --count=3` (via `pytest-repeat`) and `vitest --repeat=3`. Flag any test with inconsistent results.

**Rationale**: Running the full suite 3x catches time-dependent, order-dependent, and resource-dependent flakiness. Using `pytest-repeat` allows running N times without tripling CI config complexity. The `--durations=20` flag (for slowest tests) can be added to the existing `ci.yml` backend step with zero additional CI time. The flaky detection run is scheduled (weekly cron), not per-PR, to avoid CI cost multiplication.

**Alternatives considered**:
- `pytest-flaky` plugin — Automatically retries failed tests, which masks flakiness rather than surfacing it.
- Running 10x — Diminishing returns beyond 3x for flaky detection; 3x is the standard threshold.

## R-009: Migration Regression Testing

**Decision**: Test migrations sequentially by applying them one-at-a-time to a fresh in-memory SQLite database and verifying schema integrity at each step.

**Rationale**: The project has 5 SQL migration files (023_consolidated_schema through 027_done_items_cache). The `_run_migrations()` function in `database.py` applies them sequentially in transactions. Migration regression tests will: (a) apply each migration individually and verify the expected tables/columns exist, (b) insert test data at migration N and verify it survives migration N+1, (c) verify the final schema matches the full consolidated schema. These tests are fast (~100ms for 5 migrations against in-memory SQLite).

**Alternatives considered**:
- Schema snapshot comparisons — Fragile across SQLite versions; direct table/column assertions are more robust.
- `alembic`-style migration framework — The project uses a custom sequential SQL migration system, not Alembic. Testing the actual system is more valuable.
