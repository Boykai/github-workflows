# Research: Backend Modernization & Improvement

**Feature**: 002-backend-modernization | **Date**: 2026-03-15

## Phase 0: Unknowns Resolution

All items initially marked as NEEDS CLARIFICATION have been resolved through codebase analysis. This document captures the research findings, decisions, and rationale for each area.

---

### 1. asyncio.TaskGroup Compatibility with Existing Shutdown Logic

**Context**: `main.py` creates 3+ background tasks (lines 380–405) and cancels them individually in the `finally` block (lines 412–426). Replacing with `TaskGroup` changes the shutdown lifecycle.

- **Decision**: Use `asyncio.TaskGroup` for the lifespan-scoped background tasks (session cleanup, polling watchdog, signal listener).
- **Rationale**: `TaskGroup` (Python 3.11+) provides automatic cancellation and awaiting of all child tasks when the `async with` block exits. This eliminates the manual `cancel()` + `await` pattern that currently leaks tasks if an exception occurs between task creation and the finally block. The project targets Python 3.13 (`target-version = "py313"` in pyproject.toml), so TaskGroup is fully available.
- **Alternatives considered**:
  - Keep manual cancel/await (rejected: error-prone, current approach already has the leak bug)
  - Use `anyio.create_task_group()` (rejected: adds external dependency, `asyncio.TaskGroup` is sufficient)
- **Compatibility note**: `TaskGroup` propagates exceptions via `ExceptionGroup`. Wrap long-running loops in `try/except` within each task to prevent one task's failure from cancelling all others. Use `exceptiongroup` backport if needed for structured handling.

---

### 2. TaskRegistry Design: Singleton vs. Dependency Injection

**Context**: 12+ `asyncio.create_task()` calls across 7+ files need centralized tracking. The existing RUF006 suppression (pyproject.toml line 70) acknowledges this is intentional but untracked.

- **Decision**: Implement TaskRegistry as a module-level singleton with a simple API: `task_registry.create_task(coro, name=...)` and `task_registry.drain(timeout=30)`.
- **Rationale**: A singleton avoids threading a registry instance through 12+ call sites. The pattern matches the existing `_ws_listener_task` module-level variable pattern already used in `signal_bridge.py`. FastAPI's dependency injection is request-scoped, not suitable for background tasks created outside request context.
- **Alternatives considered**:
  - FastAPI dependency injection (rejected: background tasks are created outside request lifecycle)
  - Per-module task lists (rejected: fragmented, no unified drain)
  - Global `set()` of tasks (rejected: no lifecycle tracking, no naming, no drain timeout)
- **API surface**:
  ```python
  class TaskRegistry:
      def create_task(self, coro, *, name: str | None = None) -> asyncio.Task
      async def drain(self, timeout: float = 30.0) -> list[asyncio.Task]  # returns undrained
      def cancel_all(self) -> None
      @property
      def pending_count(self) -> int
  ```

---

### 3. Timeout Strategy for External API Calls

**Context**: `github_projects/service.py` line 324 calls `client.async_graphql()` (via githubkit SDK) with no timeout. A hung GitHub API blocks the event loop slot.

- **Decision**: Use `asyncio.wait_for(coro, timeout=30)` wrapping the GraphQL call. Make timeout configurable via `Settings.api_timeout_seconds`.
- **Rationale**: `asyncio.wait_for` works at the coroutine level regardless of the underlying HTTP client. This is more reliable than httpx-level timeout alone because it covers the full GraphQL processing pipeline (auth, retry, response parsing). The 30-second default aligns with GitHub's own recommendation and the spec's SC-003 success criterion.
- **Alternatives considered**:
  - httpx `Timeout(connect=5, read=30)` on the client (rejected: githubkit manages its own httpx client; overriding timeout requires internal API access)
  - `asyncio.timeout()` context manager (rejected: equivalent to `wait_for` but more verbose for single-call wrapping)
  - No timeout, rely on TCP keepalive (rejected: TCP keepalive can take minutes to detect dead connections)
- **Edge case**: `asyncio.TimeoutError` from `wait_for` should be caught and re-raised as a structured `AppException` with a clear message, not silently swallowed.

---

### 4. WebSocket Reconnection Backoff Strategy

**Context**: `signal_bridge.py` lines 524/529 use flat 5s/10s sleep for reconnection. A downed Signal server causes rapid reconnection attempts.

- **Decision**: Exponential backoff with jitter. Base=1s, multiplier=2, cap=300s (5 minutes). Reset to base on successful connection.
- **Rationale**: Exponential backoff is the industry standard for reconnection. Jitter prevents thundering herd if multiple instances reconnect simultaneously. The 5-minute cap prevents extremely long waits while still protecting against connection storms. Resetting on success ensures normal operation resumes quickly after recovery.
- **Alternatives considered**:
  - Fixed backoff (current, 5s/10s) — rejected: too aggressive for extended outages, too slow for transient failures
  - Linear backoff — rejected: grows too slowly for long outages
  - Circuit breaker — rejected: adds complexity; exponential backoff achieves similar protection. Circuit breaker recommended as follow-up.
- **Formula**: `delay = min(base * (2 ** consecutive_failures) + random.uniform(0, 1), cap)`

---

### 5. CSRF Protection Approach for FastAPI

**Context**: No CSRF protection exists on state-changing endpoints. The app uses cookie-based session auth which is vulnerable to cross-site request forgery.

- **Decision**: Implement double-submit cookie CSRF pattern using a lightweight custom middleware. Generate a random CSRF token on session creation, set it as a non-HttpOnly cookie (readable by JavaScript). Require the value in `X-CSRF-Token` header on POST/PUT/DELETE requests.
- **Rationale**: Double-submit cookie is stateless (no server-side token storage), works with the existing cookie-based session model, and is straightforward to implement. The CSRF cookie must NOT be HttpOnly so the frontend JavaScript can read and include it in request headers.
- **Alternatives considered**:
  - `starlette-csrf` package (considered: adds a dependency for a simple pattern; evaluate if it provides additional features worth the dependency)
  - Synchronizer token pattern (rejected: requires server-side token storage, doesn't match current stateless session model)
  - SameSite=Strict cookie only (rejected: already set, but insufficient defense against subdomain attacks or older browser bugs)
- **Exemptions**: Webhook endpoints (use HMAC verification), OAuth callback endpoint (no session yet).

---

### 6. SQLite Transaction Discipline with aiosqlite

**Context**: `chat_store.py` uses per-operation `await db.commit()` with no explicit transaction boundaries. Multi-step operations can leave inconsistent state.

- **Decision**: Use `BEGIN IMMEDIATE` transactions for write operations. Wrap multi-step writes in explicit transaction blocks using aiosqlite's `execute("BEGIN IMMEDIATE")` / `commit()` / `rollback()` pattern.
- **Rationale**: `BEGIN IMMEDIATE` acquires a write lock immediately, preventing write starvation in WAL mode. This is preferred over `BEGIN DEFERRED` (which can fail on lock promotion) for write-heavy operations. aiosqlite doesn't provide a native transaction context manager, so use explicit SQL statements.
- **Alternatives considered**:
  - `BEGIN DEFERRED` (rejected: can fail with `SQLITE_BUSY` when promoted from reader to writer)
  - `BEGIN EXCLUSIVE` (rejected: too aggressive, blocks all readers)
  - Savepoints only (rejected: savepoints work within transactions, still need BEGIN for the outer boundary)
- **Implementation pattern**:
  ```python
  await db.execute("BEGIN IMMEDIATE")
  try:
      await db.execute("INSERT ...")
      await db.execute("UPDATE ...")
      await db.commit()
  except Exception:
      await db.rollback()
      raise
  ```

---

### 7. Rate Limiting Key Resolution: Async in Sync Context

**Context**: `slowapi`'s `key_func` is synchronous, but resolving `github_user_id` from a session cookie requires an async database lookup.

- **Decision**: Use a request-scoped middleware that pre-resolves the rate-limit key and stores it in `request.state.rate_limit_key`. The synchronous `key_func` reads from `request.state`.
- **Rationale**: This avoids blocking the event loop with a sync database call. The middleware runs once per request (before the endpoint), so the overhead is minimal. The pre-resolved key is already available by the time slowapi's `key_func` is called.
- **Alternatives considered**:
  - `asyncio.run()` inside key_func (rejected: creates nested event loop, fails with "already running")
  - Monkeypatch slowapi for async key_func (rejected: fragile, breaks on library updates)
  - Switch to custom rate limiter (rejected: slowapi works well, just needs the key function workaround)
- **Key format**: `user:{github_user_id}` when authenticated, `ip:{remote_address}` as fallback. This ensures rate limits persist across session cookie changes for the same user.

---

### 8. Cache Key Scoping Strategy

**Context**: `constants.py:95` defines `cache_key_issue_pr()` as `f"{issue_number}:{pr_number}"` — no project context. Two projects with issue #42 share cached data.

- **Decision**: Prefix all project-scoped cache keys with `{project_id}:`. The `project_id` is the GitHub Projects V2 node ID (globally unique).
- **Rationale**: GitHub Projects V2 node IDs (`PVT_...`) are globally unique, so they serve as natural namespace separators. This is the simplest change that prevents collisions while maintaining cache key readability.
- **Alternatives considered**:
  - `{owner}/{repo}` prefix (rejected: a project can span multiple repos in Projects V2)
  - Hash-based namespace (rejected: harder to debug, no benefit over direct ID prefix)
  - Nested cache structure (rejected: overengineered, simple prefix is sufficient)

---

### 9. Pagination Design for Chat Endpoints

**Context**: Chat message endpoints can return 100K+ rows unbounded. Need `limit`/`offset` pagination.

- **Decision**: Add `limit` (default 50, max 200) and `offset` (default 0) query parameters. Apply SQL `LIMIT ? OFFSET ?`. Return total count in response for client-side pagination UI.
- **Rationale**: Offset-based pagination is simple, works with SQLite, and meets the spec requirement (FR-014, SC-010). The 200-item max prevents memory pressure from large fetches. Including total count enables "page X of Y" UI without a separate count query (use `COUNT(*) OVER()` window function).
- **Alternatives considered**:
  - Cursor-based pagination (rejected: more complex, SQLite doesn't have native cursor support; offset is sufficient for this scale)
  - Keyset pagination (rejected: requires monotonic sort key, adds complexity)
  - No pagination, client-side truncation (rejected: transfers entire dataset, defeats the purpose)

---

### 10. BoundedDict Task-Aware Eviction

**Context**: `utils.py:90-91` evicts the oldest entry from `BoundedDict` via `popitem(last=False)`. When the evicted value is an `asyncio.Task`, the task continues running unsupervised.

- **Decision**: Add an optional `on_evict` callback to `BoundedDict`. For task-holding instances, pass a callback that cancels the evicted task.
- **Rationale**: Making eviction behavior configurable keeps `BoundedDict` general-purpose while allowing task-specific cleanup. The callback approach is cleaner than type-checking for `asyncio.Task` inside the container.
- **Alternatives considered**:
  - Always cancel if value is `asyncio.Task` (rejected: couples BoundedDict to asyncio, violates separation of concerns)
  - Subclass `BoundedDict` for tasks (rejected: adds a class for a single-line behavior change)
  - Increase `maxlen` to avoid eviction (rejected: just delays the problem, doesn't fix the root cause)

---

### 11. Modern Python Pattern Adoption Scope

**Context**: Phase 5 introduces enums, protocols, TypedDict, and standardized error handling. Need to determine scope to avoid over-engineering.

- **Decision**: Apply patterns surgically to the specific locations identified in the spec. Do not refactor the entire codebase.
- **Rationale**: The constitution (Principle V: Simplicity and DRY) favors YAGNI. Converting every string to an enum or every dict to TypedDict would be premature. Focus on the locations where the anti-patterns cause actual bugs or maintenance burden.
- **Specific scope**:
  - Enums: `cleanup_service.py` ItemClassification fields only (most string-constant-heavy)
  - Protocols: `ModelProvider` and `CacheInvalidationPolicy` only (spec-mandated)
  - TypedDict: `get_polling_status()` return type and rate-limit info dicts only
  - Error decorator: Apply to service methods making external calls (GitHub API, model fetcher) — not to internal utility functions
  - Thread offloading: Only if profiling shows regex loops >100ms. Cleanup service processes branches in batches; typical batch size is <50.

---

### 12. Thread Offloading Threshold for Cleanup Service

**Context**: `cleanup_service.py` uses regex pattern matching (lines 47-55) for branch/PR classification. The spec suggests `asyncio.to_thread()` for CPU-bound work.

- **Decision**: Only offload to thread if batch size exceeds 100 items. Below that threshold, regex matching is fast enough (<10ms) to run inline.
- **Rationale**: `asyncio.to_thread()` has overhead (thread pool scheduling, context switch). For small batches, the overhead exceeds the benefit. The cleanup service processes branches in batches typically under 50 items.
- **Alternatives considered**:
  - Always offload (rejected: unnecessary overhead for typical workloads)
  - Never offload (rejected: could block event loop with unusually large repos)
  - Compile regex at module level (already done at lines 47-55 — `re.compile()` is used)

---

## Technology Best Practices

### asyncio.TaskGroup Best Practices (Python 3.11+)

- **Decision**: Use TaskGroup for lifecycle-scoped tasks; keep long-running loops resilient to exceptions
- **Rationale**: TaskGroup cancels all sibling tasks if any task raises an unhandled exception. Each background loop (cleanup, watchdog) must catch its own exceptions internally to prevent cross-task cancellation.
- **Key pattern**:
  ```python
  async with asyncio.TaskGroup() as tg:
      tg.create_task(long_running_loop_1())  # handles own exceptions
      tg.create_task(long_running_loop_2())  # handles own exceptions
      yield  # FastAPI lifespan: hold open during app lifetime
  # TaskGroup __aexit__ cancels and awaits all tasks
  ```

### aiosqlite Transaction Patterns

- **Decision**: Explicit `BEGIN IMMEDIATE` + `commit()`/`rollback()` for write transactions
- **Rationale**: aiosqlite doesn't provide a native async context manager for transactions. The explicit pattern is clear and matches SQLite semantics directly.
- **Key constraint**: Don't nest `BEGIN` statements — use savepoints for nested transactions: `SAVEPOINT sp1` / `RELEASE sp1` / `ROLLBACK TO sp1`.

### FastAPI CSRF Protection

- **Decision**: Custom middleware implementing double-submit cookie pattern
- **Rationale**: No standard FastAPI CSRF middleware. The pattern is simple enough to implement correctly without a library dependency.
- **Key constraints**: CSRF cookie must be `SameSite=Lax` (not Strict — needs to be sent on cross-site GET for the initial page load), not HttpOnly (frontend JS must read it), and Secure in production.

### slowapi Rate Limiting with Pre-Resolved Keys

- **Decision**: Middleware pre-resolves async key, synchronous key_func reads from request state
- **Rationale**: Avoids event loop blocking in synchronous callback. Pattern is used by other FastAPI+slowapi projects.
- **Key pattern**:
  ```python
  @app.middleware("http")
  async def resolve_rate_limit_key(request, call_next):
      user_id = await get_user_id_from_session(request)
      request.state.rate_limit_key = f"user:{user_id}" if user_id else get_remote_address(request)
      return await call_next(request)
  ```

## Summary

All 12 technical unknowns have been resolved through codebase analysis:

| # | Unknown | Resolution |
|---|---------|-----------|
| 1 | TaskGroup compatibility | Compatible; wrap loop exceptions internally |
| 2 | TaskRegistry design | Module-level singleton with drain API |
| 3 | Timeout strategy | `asyncio.wait_for()` with 30s default |
| 4 | WebSocket backoff | Exponential with jitter, base=1s, cap=300s |
| 5 | CSRF approach | Double-submit cookie middleware |
| 6 | Transaction discipline | `BEGIN IMMEDIATE` with explicit commit/rollback |
| 7 | Async rate-limit key | Middleware pre-resolution + request.state |
| 8 | Cache key scoping | `{project_id}:` prefix on all project-scoped keys |
| 9 | Pagination design | `limit`/`offset` with 200-item max, total count via window function |
| 10 | Task eviction | `on_evict` callback on BoundedDict |
| 11 | Modern patterns scope | Surgical application to spec-identified locations only |
| 12 | Thread offloading threshold | Batch size >100 triggers `to_thread()`; typical <50 stays inline |

No NEEDS CLARIFICATION items remain. All decisions are backed by codebase evidence and aligned with the constitution's Simplicity principle.
