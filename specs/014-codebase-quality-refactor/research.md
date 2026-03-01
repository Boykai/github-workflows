# Research: Refactor Codebase for Quality, Best Practices, and UX Improvements

## R1: DEFAULT_STATUS_COLUMNS Correct Replacement Value (US1 — FR-001)

**Decision**: Replace `["Todo", "In Progress", "Done"]` with `[StatusNames.BACKLOG, StatusNames.IN_PROGRESS, StatusNames.DONE]`.

**Rationale**: The `StatusNames` class defines five canonical statuses: `Backlog`, `Ready`, `In Progress`, `In Review`, `Done`. The current default uses `"Todo"` which is not a valid status name. The three-column default should represent the most common minimal workflow: `Backlog` (not started), `In Progress` (active), `Done` (complete). These three columns are used as a fallback when a project has no status columns configured (e.g., in `github_projects/service.py:298-303`) and as available statuses for AI chat parsing (e.g., in `api/chat.py:269` and `services/signal_chat.py:634`).

**Alternatives considered**:
- Use all five status names as defaults: Rejected — the default is specifically a minimal fallback for projects without configured columns. All five would be overly prescriptive.
- Replace `"Todo"` with `"Ready"`: Rejected — `Backlog` is the standard "not started" status in the pipeline (it maps to `speckit.specify` in `DEFAULT_AGENT_MAPPINGS`).
- Replace `"Todo"` with `StatusNames.READY`: Considered, but `Backlog` better represents "not yet started" in the Spec Kit pipeline context.

**Impact analysis**: The constant is used in 3 locations:
1. `backend/src/services/github_projects/service.py:302` — fallback status columns for projects with no configured columns
2. `backend/src/api/chat.py:269` — available statuses for AI status change parsing
3. `backend/src/services/signal_chat.py:634` — available statuses for Signal chat status parsing

All three use the values as display names for status matching. Changing from `"Todo"` to `"Backlog"` is a data correction, not a breaking change — `"Todo"` was never a valid status that could match anything.

---

## R2: Atomic Admin Promotion SQL Pattern (US2 — FR-002)

**Decision**: Replace the two-step SELECT + UPDATE with a single atomic `UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1 AND admin_github_user_id IS NULL`. Check `cursor.rowcount` to determine if the promotion succeeded.

**Rationale**: The current code reads `admin_github_user_id`, checks if it's `NULL`, then writes. Between the SELECT and UPDATE, another concurrent request could also see `NULL` and both would be promoted. SQLite serializes writes, so an `UPDATE ... WHERE admin_github_user_id IS NULL` is atomic — only the first write succeeds, and `rowcount == 0` tells the second request that someone else was promoted.

**Alternatives considered**:
- Database-level UNIQUE constraint on admin: Not applicable — the column is nullable and only one row exists.
- Application-level mutex/lock: Rejected — adds complexity and doesn't work across multiple process workers.
- Optimistic concurrency with version column: Rejected — overkill for a single-row singleton table.

**Implementation approach**:
1. Attempt the atomic UPDATE with `WHERE admin_github_user_id IS NULL`
2. If `rowcount == 1`: user was promoted — return session
3. If `rowcount == 0`: someone else was already promoted — re-read to check if it's the current user
4. If current user matches the now-set admin: return session (idempotent)
5. Otherwise: raise 403

---

## R3: Lifespan try/finally Pattern (US3 — FR-003)

**Decision**: Wrap the startup block (from `init_database()` through `start_signal_ws_listener()`) in a `try` block. Move cleanup code (stop listener, cancel task, close DB) into the `finally` block that also contains the `yield`. Use a flag or conditional to only clean up resources that were successfully initialized.

**Rationale**: If `init_database()` or `seed_global_settings()` throws, the current code never reaches `yield`, so the shutdown section after `yield` never executes. Any partially-started resources (e.g., if the cleanup task was created before the signal listener fails) would be orphaned. A `try/finally` ensures cleanup always runs.

**Alternatives considered**:
- Nested try/except blocks for each resource: Rejected — overly verbose. A single try/finally with conditional cleanup (check if variable is bound) is simpler.
- ExitStack pattern: Considered — more Pythonic for resource management, but adds complexity for only 3 resources. The try/finally is more readable given the async context.

**Implementation approach**:
- Initialize `cleanup_task = None` before the try block
- In `try`: do init, create task, start listener, then `yield`
- In `finally`: stop listener (if started), cancel task (if created), close DB (if opened)

---

## R4: Docker Healthcheck Lightweight Alternative (US4 — FR-004)

**Decision**: Replace `python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')"` with `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"` in both the `Dockerfile` and `docker-compose.yml`.

**Rationale**: `urllib.request` is part of Python's standard library — no transitive dependency imports needed. The Python interpreter is already available in the container (it's a Python app), so `curl` would require an additional package install. Using stdlib Python avoids adding system dependencies while still being lightweight compared to importing `httpx` (which pulls in `httpcore`, `certifi`, `anyio`, etc.).

**Alternatives considered**:
- `curl -f http://localhost:8000/api/v1/health`: Requires installing `curl` in the slim image (adds ~7MB). The image currently uses `python:3.12-slim` which doesn't include curl.
- `wget`: Not available in the slim image either.
- Custom healthcheck script: Overkill for a one-liner.

**Implementation approach**: Update the `HEALTHCHECK CMD` in `backend/Dockerfile` and the `healthcheck.test` in `docker-compose.yml`. Both should use the same `urllib.request.urlopen` command.

---

## R5: effective_cookie_secure Property Design (US5 — FR-005, FR-006)

**Decision**: Add a `@property` method `effective_cookie_secure` to the `Settings` class that returns `True` if `self.cookie_secure` is `True` OR if `self.frontend_url` starts with `"https://"`. Update `_set_session_cookie()` in `auth.py` to use `settings.effective_cookie_secure` instead of `settings.cookie_secure`.

**Rationale**: This provides defense-in-depth — if a deployer sets an HTTPS frontend URL but forgets to set `cookie_secure=True`, the property auto-detects and enforces secure cookies. The explicit `cookie_secure=True` override is preserved as an OR condition, so it can always force secure cookies regardless of URL scheme.

**Alternatives considered**:
- Pydantic validator that overrides `cookie_secure` on construction: Rejected — mutating the raw field makes debugging harder. A separate computed property is more transparent.
- Middleware-based detection: Rejected — the secure flag needs to be set at cookie creation time, not per-request.

**Edge cases**:
- `frontend_url` is `http://` and `cookie_secure` is `False` → `effective_cookie_secure` is `False` (local dev)
- `frontend_url` is `https://` and `cookie_secure` is `False` → `effective_cookie_secure` is `True` (auto-detect)
- `cookie_secure` is `True` regardless of URL → `effective_cookie_secure` is `True` (explicit override)
- `frontend_url` is empty or invalid → falls back to `cookie_secure` value

---

## R6: BoundedDict Interface Completeness (US6 — FR-007)

**Decision**: No implementation changes needed. The current `BoundedDict` already implements all required methods: `get()`, `pop()`, `keys()`, `values()`, `items()`, `__iter__()`, `clear()`, and `__repr__()`.

**Rationale**: Code inspection of `backend/src/utils.py` lines 63-133 confirms all methods are present. The existing test suite in `test_utils.py` covers `get_existing`, `get_missing_default`, `pop_existing`, `pop_missing_with_default`, `iter`, plus the basic dict operations. This user story is already implemented.

**Verification**: The following methods are confirmed present:
- `__iter__()` at line 101
- `get()` at line 108 (with overloads)
- `pop()` at line 117 (with overloads)
- `keys()` at line 120
- `values()` at line 123
- `items()` at line 126
- `clear()` at line 129
- `__repr__()` at line 132

**Action**: Mark US6 as already complete. No code changes required.

---

## R7: DOM Library Cleanup — happy-dom vs jsdom (US7 — FR-008)

**Decision**: Remove `jsdom` from `frontend/package.json` devDependencies.

**Rationale**: `frontend/vitest.config.ts` explicitly sets `environment: 'happy-dom'` (line 15). There are no imports or references to `jsdom` in the frontend source or test files beyond `package.json` and `package-lock.json`. The `jsdom` dependency was likely added as a fallback during initial setup and is no longer needed.

**Alternatives considered**:
- Remove `happy-dom` and keep `jsdom`: Rejected — `happy-dom` is already configured and working. Switching would require updating `vitest.config.ts` and potentially fixing test compatibility issues.

---

## R8: Settings Cache Clearing Utility (US8 — FR-009)

**Decision**: Add a `clear_settings_cache()` function to `backend/src/config.py` that calls `get_settings.cache_clear()`. Export it for use in test teardown.

**Rationale**: While `get_settings.cache_clear()` already works (it's an `lru_cache` method), a named utility is more discoverable and communicates intent. Tests currently call `get_settings.cache_clear()` directly (seen in `test_config.py:98, 108, 113, 119`), which requires knowing the implementation detail that `get_settings` is an `lru_cache`. A dedicated function makes the intent explicit.

**Alternatives considered**:
- Document `get_settings.cache_clear()` and leave it: Rejected — a named function is trivial to add and improves developer experience.
- Create a test fixture that auto-clears: Out of scope — the utility function is the minimal change. Tests can use it in their own fixtures.

---

## R9: Exponential Backoff for Session Cleanup (US9 — FR-010)

**Decision**: Add exponential backoff to `_session_cleanup_loop` in `main.py`. Use a `consecutive_failures` counter that doubles the sleep interval on each failure, capped at 300 seconds (5 minutes). Reset to 0 on success.

**Rationale**: The current loop sleeps for a fixed `interval` regardless of errors. Repeated failures (e.g., database lock) produce one error log per interval forever. Exponential backoff (base interval × 2^failures, capped at 5 min) reduces log noise while still retrying.

**Implementation approach**:
```python
consecutive_failures = 0
while True:
    try:
        backoff = min(interval * (2 ** consecutive_failures), 300)
        await asyncio.sleep(backoff)
        db = get_db()
        count = await purge_expired_sessions(db)
        consecutive_failures = 0  # reset on success
        if count > 0:
            logger.info(...)
    except asyncio.CancelledError:
        break
    except Exception:
        consecutive_failures += 1
        logger.exception("Error in session cleanup task")
```

**Alternatives considered**:
- Fixed retry with jitter: Considered — jitter helps in distributed systems but is unnecessary for a single background task.
- Circuit breaker pattern: Rejected — overkill for a simple cleanup loop.
- Separate error counter + max retries: Rejected — the loop should retry forever (it's a daemon task), just with decreasing frequency.

---

## R10: Pydantic env_file Multi-Path Resolution (US10 — FR-011)

**Decision**: Update `Settings.model_config` to set `env_file` to `("../.env", ".env")` — a tuple of paths. Pydantic Settings v2 supports a tuple/list of env files, loading them in order (later files override earlier ones).

**Rationale**: The current config only checks `../.env`, which works in Docker (where the working directory is `/app` and `.env` is at `/app/../.env` or bind-mounted). For local development running from `backend/`, the `.env` is typically in the repo root (`../`) or in `backend/` itself. Supporting both paths ensures env file resolution works in both contexts.

**Alternatives considered**:
- Programmatic path detection in `get_settings()`: Rejected — Pydantic Settings already supports multi-path env files natively. Using the built-in feature is simpler and more maintainable.
- Only `".env"`: Rejected — breaks the existing Docker setup where `../.env` is the conventional location.

**Precedence**: When both files exist, Pydantic loads them left-to-right. The rightmost file (`.env`) wins on conflicts. This means a local `.env` in the backend directory takes precedence over the repo-root `../.env`, which is the expected behavior for local overrides.
