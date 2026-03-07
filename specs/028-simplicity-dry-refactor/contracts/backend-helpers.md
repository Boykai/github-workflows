# Contract: Backend Shared Helpers

**Feature**: `028-simplicity-dry-refactor` | **Phase**: 1

---

## 1. `require_selected_project` — Session Validation Helper

**Location**: `backend/src/dependencies.py`

### Signature

```python
def require_selected_project(session: UserSession) -> str:
    """Return the selected project ID or raise HTTP 400.

    Args:
        session: The authenticated user session.

    Returns:
        The selected project ID string.

    Raises:
        HTTPException: 400 if no project is selected.
    """
```

### Behavior

| Condition | Result |
|-----------|--------|
| `session.selected_project_id` is truthy | Returns the project ID string |
| `session.selected_project_id` is `None` or empty | Raises `HTTPException(status_code=400, detail="No project selected")` |

### Consumers

| File | Current Pattern | After |
|------|----------------|-------|
| `api/chat.py` | Inline `if not session.selected_project_id` | `project_id = require_selected_project(session)` |
| `api/workflow.py` | Inline guard | Same |
| `api/tasks.py` | Inline guard | Same |
| `api/chores.py` | Inline guard | Same |
| `api/board.py` | Inline guard (some variants) | Same |

### Validation

- `grep -rn "if not.*selected_project_id" backend/src/api/` returns zero hits outside `dependencies.py` after migration.
- All existing tests pass unchanged.

---

## 2. `cached_fetch` — Generic Cache Wrapper

**Location**: `backend/src/services/cache.py`

### Signature

```python
async def cached_fetch(
    cache: InMemoryCache,
    key: str,
    fetch_fn: Callable[..., Awaitable[T]],
    *args: Any,
    refresh: bool = False,
    ttl_seconds: int = 300,
) -> T:
    """Fetch a value from cache or compute it.

    Args:
        cache: The cache instance.
        key: Cache key string.
        fetch_fn: Async callable that produces the value.
        *args: Arguments passed to fetch_fn.
        refresh: If True, bypass cache and force a fresh fetch.
        ttl_seconds: Time-to-live for the cached entry.

    Returns:
        The cached or freshly fetched value.
    """
```

### Behavior

| Condition | Result |
|-----------|--------|
| `refresh=False` and cache hit | Returns cached value (no fetch call) |
| `refresh=False` and cache miss | Calls `fetch_fn(*args)`, stores result, returns it |
| `refresh=True` | Always calls `fetch_fn(*args)`, stores result, returns it |
| `fetch_fn` raises | Exception propagates (no caching of errors) |

### Consumers

| File | Current Pattern | After |
|------|----------------|-------|
| `api/projects.py` | 8-12 line check/get/set block | `await cached_fetch(cache, key, fetch_fn, ...)` |
| `api/board.py` | Same verbose pattern | Same |
| `api/chat.py` | Same verbose pattern | Same |

### Validation

- Existing cache tests in `tests/unit/test_cache.py` continue to pass.
- New unit tests for `cached_fetch` cover: cache hit, cache miss, refresh bypass, exception propagation.

---

## 3. Error Handling Helper Wiring

**Location**: `backend/src/logging_utils.py` (existing, lines 215-276)

### Existing Signatures (No Changes)

```python
def safe_error_response(exc: Exception, operation: str) -> str:
    """Log and return a user-safe error message."""

def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
    """Log the exception and raise an AppException with a safe message."""
```

### Wiring Contract

| File | Current Pattern | After |
|------|----------------|-------|
| `api/board.py` | `except Exception as e: logger.error(...); raise HTTPException(...)` | `except Exception as e: handle_service_error(e, "board operation")` |
| `api/workflow.py` | Similar boilerplate | Same replacement |
| `api/projects.py` | Mix of HTTPException and JSONResponse | Same replacement |
| `api/auth.py` | Catch-log-raise | Same replacement |

### Validation

- 80%+ of endpoint error handlers use `handle_service_error` or `safe_error_response` after migration.
- Error responses remain structured JSON with `error` and `details` fields (via `AppException` handler in `main.py`).
- `tests/unit/test_logging_utils.py` existing tests pass unchanged.

---

## 4. Repository Resolution Consolidation

**Location**: `backend/src/utils.py` (existing, lines 145-186)

### Existing Signature (No Changes)

```python
async def resolve_repository(access_token: str, project_id: str) -> tuple[str, str]:
    """Resolve repository owner and name using 3-step fallback."""
```

### Elimination Contract

| Location | Current Implementation | After |
|----------|----------------------|-------|
| `api/workflow.py:83-111` | `_get_repository_info(session)` | Deleted; callers use `resolve_repository()` |
| `main.py:~38-140` | Inline 3-step fallback | Calls `resolve_repository()` |
| `api/projects.py` | Inline resolution | Calls `resolve_repository()` |
| `api/tasks.py` | Inline resolution | Calls `resolve_repository()` |
| `api/chat.py` | Inline resolution | Calls `resolve_repository()` |
| `api/chores.py` | Inline resolution | Calls `resolve_repository()` |

### Validation

- `grep -rn "_get_repository_info" backend/` returns zero hits after migration.
- `resolve_repository` is the sole resolution path in the codebase.
- All existing tests pass unchanged.
