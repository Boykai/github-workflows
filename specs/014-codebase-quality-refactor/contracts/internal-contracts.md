# Internal Contracts: Module Boundaries & Modified Interfaces

This document defines the internal contracts for modules modified by this refactor. No new API endpoints are introduced — all changes are to internal module interfaces.

## 1. Constants Module (`backend/src/constants.py`)

### DEFAULT_STATUS_COLUMNS — MODIFIED

```python
# Before
DEFAULT_STATUS_COLUMNS = ["Todo", "In Progress", "Done"]

# After
DEFAULT_STATUS_COLUMNS = [StatusNames.BACKLOG, StatusNames.IN_PROGRESS, StatusNames.DONE]
```

**Contract**: `DEFAULT_STATUS_COLUMNS` is a `list[str]` containing exactly 3 elements, each of which is a valid value from the `StatusNames` class. All consumers receive `StatusNames`-compatible values without code changes.

**Consumers**:
- `backend/src/services/github_projects/service.py` — fallback status columns
- `backend/src/api/chat.py` — AI status change parsing
- `backend/src/services/signal_chat.py` — Signal message status parsing

---

## 2. Admin Authorization (`backend/src/dependencies.py`) — MODIFIED

### require_admin — Behavioral Change

```python
async def require_admin(
    request: Request,
    session=Depends(_get_session_dep()),
) -> UserSession:
    """
    Verify the current session belongs to the admin user.

    CHANGED: Uses atomic UPDATE ... WHERE admin_github_user_id IS NULL
    instead of SELECT-then-UPDATE to prevent TOCTOU race condition.

    Returns:
        UserSession if authorized

    Raises:
        HTTPException(403) if user is not admin and cannot be promoted
    """
```

**Contract**:
- **Atomic promotion**: At most one user is ever promoted to admin, guaranteed by SQL WHERE clause
- **Idempotent**: If the current user is already admin, returns session without modification
- **403 on conflict**: If another user was promoted between the request arriving and the UPDATE executing, returns 403
- **Return type**: `UserSession` (unchanged)
- **Side effects**: May commit a single UPDATE to `global_settings` (unchanged)

---

## 3. Settings Module (`backend/src/config.py`) — MODIFIED

### Settings.effective_cookie_secure — NEW PROPERTY

```python
class Settings(BaseSettings):
    @property
    def effective_cookie_secure(self) -> bool:
        """Auto-detect secure cookie flag from frontend_url scheme.

        Returns True if:
        - cookie_secure is explicitly True, OR
        - frontend_url starts with 'https://'
        """
```

**Contract**:
- Read-only computed property
- Returns `bool`
- Does NOT modify `cookie_secure` field
- Backward-compatible: `cookie_secure=True` always forces `True`

### Settings.model_config.env_file — MODIFIED

```python
# Before
model_config = SettingsConfigDict(env_file="../.env", ...)

# After
model_config = SettingsConfigDict(env_file=("../.env", ".env"), ...)
```

**Contract**: Pydantic loads env files left-to-right; rightmost (`.env`) takes precedence on conflicts.

### clear_settings_cache() — NEW FUNCTION

```python
def clear_settings_cache() -> None:
    """Clear the cached Settings instance.

    Call in test teardown to prevent mock leaks between tests.
    Delegates to get_settings.cache_clear().
    """
```

**Contract**:
- Idempotent — safe to call multiple times
- After calling, next `get_settings()` creates a fresh `Settings()` instance
- No parameters, no return value

---

## 4. Cookie Setting (`backend/src/api/auth.py`) — MODIFIED

### _set_session_cookie — Behavioral Change

```python
def _set_session_cookie(response: Response, session_id: str) -> None:
    """
    CHANGED: Uses settings.effective_cookie_secure instead of
    settings.cookie_secure for the `secure` flag.
    """
```

**Contract**:
- Function signature unchanged
- `secure` flag now auto-detects HTTPS from `frontend_url`
- All other cookie parameters unchanged (`httponly=True`, `samesite="lax"`, `max_age`, `path="/"`)

---

## 5. Lifespan Handler (`backend/src/main.py`) — MODIFIED

### lifespan — Behavioral Change

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    CHANGED: Wrapped startup in try/finally to ensure cleanup on failure.

    Resources are only cleaned up if they were successfully initialized
    (checked via variable binding / None guards).
    """
```

**Contract**:
- **Success path**: Identical to current behavior (init → yield → cleanup)
- **Failure path**: Any exception during startup triggers cleanup of already-initialized resources
- **Cleanup order**: stop signal listener → cancel cleanup task → close database (reverse of init order)

### _session_cleanup_loop — Behavioral Change

```python
async def _session_cleanup_loop() -> None:
    """
    CHANGED: Adds exponential backoff on consecutive failures.

    - Base interval: settings.session_cleanup_interval
    - Backoff: min(interval * 2^consecutive_failures, 300)
    - Resets to base interval on successful run
    """
```

**Contract**:
- CancelledError still breaks the loop cleanly (unchanged)
- Successful runs use the base interval (unchanged behavior for healthy systems)
- Failed runs increase sleep time exponentially, capped at 5 minutes
- No new exceptions raised

---

## 6. Docker Configuration — MODIFIED

### backend/Dockerfile HEALTHCHECK

```dockerfile
# Before
CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')" || exit 1

# After
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1
```

### docker-compose.yml backend healthcheck

```yaml
# Before
test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/api/v1/health')"]

# After
test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"]
```

**Contract**:
- Health endpoint URL unchanged: `http://localhost:8000/api/v1/health`
- Exit code 0 on success, non-zero on failure (unchanged)
- No external dependency required (stdlib only)

---

## 7. Frontend Dependencies — MODIFIED

### package.json devDependencies

```json
// Removed
"jsdom": "^27.4.0"
```

**Contract**:
- `vitest.config.ts` continues to use `environment: 'happy-dom'` (unchanged)
- All frontend tests pass without `jsdom` installed
