# Internal API Contracts: Phase 2 — Code Quality & DRY Consolidation

**Feature**: 001-code-quality-dry  
**Date**: 2026-03-22  
**Type**: Internal Python function contracts (no external API changes)

> **Note**: This feature is a pure backend refactoring. No external HTTP API contracts change.
> All contracts below describe internal Python function signatures and their behavioural guarantees.

---

## Contract 1: `cached_fetch()` — Extended Signature

**File**: `solune/backend/src/services/cache.py`

```python
async def cached_fetch[T](
    cache_instance: InMemoryCache,
    key: str,
    fetch_fn: Callable[[], Awaitable[T]],
    ttl_seconds: int | None = None,
    refresh: bool = False,
    stale_fallback: bool = False,
    *,
    rate_limit_fallback: bool = False,
    data_hash_fn: Callable[[T], str] | None = None,
) -> T:
    """Cache-aside fetch with optional rate-limit-aware fallback and data-hash deduplication.

    Args:
        cache_instance: InMemoryCache instance to use for get/set operations.
        key: Cache key string.
        fetch_fn: Async callable that fetches fresh data. Called on cache miss or refresh.
        ttl_seconds: Optional TTL for the cache entry. Uses cache default if None.
        refresh: If True, bypass cache and always call fetch_fn.
        stale_fallback: If True, return stale cached data on any fetch_fn exception.
        rate_limit_fallback: If True, return stale cached data specifically on RateLimitError.
            Logs a rate-limit-specific warning. Independent of stale_fallback.
        data_hash_fn: Optional function to compute a hash of the fetched data.
            If the hash matches the existing cache entry's data_hash, only refresh the TTL
            (avoids replacing the cached value with identical data).

    Returns:
        The cached or freshly-fetched data of type T.

    Raises:
        Re-raises the original exception from fetch_fn if no stale data is available
        and the fallback conditions are not met.

    Backward Compatibility:
        All new parameters are optional with defaults that preserve existing behaviour.
        Existing callers require zero changes.
    """
```

### Behavioural Contract

| Scenario | stale_fallback | rate_limit_fallback | Behaviour |
|----------|---------------|-------------------|-----------|
| Cache hit | any | any | Return cached value |
| Cache miss, fetch succeeds | any | any | Cache and return fresh value |
| Cache miss, fetch raises `RateLimitError` | False | True | Return stale if available, else re-raise |
| Cache miss, fetch raises `RateLimitError` | True | True | Return stale (rate_limit_fallback takes priority for logging) |
| Cache miss, fetch raises `RateLimitError` | True | False | Return stale if available (handled by stale_fallback) |
| Cache miss, fetch raises other exception | True | any | Return stale if available, else re-raise |
| Cache miss, fetch raises other exception | False | any | Re-raise |
| Fetch succeeds, data_hash_fn matches | any | any | refresh_ttl() only, return data |
| Fetch succeeds, data_hash_fn differs | any | any | set() with new hash, return data |

---

## Contract 2: `_with_fallback()` — Fallback Abstraction

**File**: `solune/backend/src/services/github_projects/service.py`

```python
async def _with_fallback[T](
    self,
    primary_fn: Callable[[], Awaitable[T]],
    fallback_fn: Callable[[], Awaitable[T]],
    operation: str,
    verify_fn: Callable[[], Awaitable[bool]] | None = None,
) -> T | None:
    """Execute primary strategy with optional verification and fallback.

    Implements the primary → verify → fallback pattern with a soft-failure contract:
    returns None on total failure, never raises exceptions to the caller.

    Args:
        primary_fn: Async callable for the primary strategy.
        fallback_fn: Async callable for the fallback strategy.
        operation: Human-readable name for logging (e.g., "add_issue_to_project").
        verify_fn: Optional async callable that returns True if primary result is verified.
            Called only when primary_fn succeeds. If it raises, treated as False.

    Returns:
        Result of the first successful strategy, or None if all fail.

    Contract:
        - NEVER raises exceptions to the caller.
        - Returns None on total failure (soft-failure contract).
        - All internal exceptions are caught and logged.
        - verify_fn failure = verification failed (proceed to fallback).
    """
```

### Behavioural Contract

| primary_fn | verify_fn | fallback_fn | Result |
|-----------|-----------|-------------|--------|
| Succeeds | None (not provided) | Not called | primary result |
| Succeeds | Returns True | Not called | primary result |
| Succeeds | Returns False | Succeeds | fallback result |
| Succeeds | Returns False | Raises | None |
| Succeeds | Raises | Succeeds | fallback result |
| Succeeds | Raises | Raises | None |
| Raises | Not called | Succeeds | fallback result |
| Raises | Not called | Raises | None |

---

## Contract 3: `handle_service_error()` — Unchanged

**File**: `solune/backend/src/logging_utils.py`

```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
    """Log exception details and raise a structured AppException.

    No signature changes in this phase. Migration involves replacing inline
    catch→raise blocks with calls to this function.

    Args:
        exc: The caught exception.
        operation: Human-readable description of the failed operation.
        error_cls: AppException subclass to raise. Defaults to GitHubAPIError.

    Raises:
        AppException (or subclass): Always raises; return type is NoReturn.
    """
```

### Migration Call-Site Pattern

**Before** (inline):
```python
try:
    result = await some_api_call()
except Exception as e:
    logger.exception("Failed to do X: %s", e)
    raise GitHubAPIError(
        message="Failed to do X",
        details={"error": str(e)},
    ) from e
```

**After** (consolidated):
```python
try:
    result = await some_api_call()
except Exception as e:
    handle_service_error(e, "do X", GitHubAPIError)
```

---

## Contract 4: `resolve_repository()` — Extended Fallback

**File**: `solune/backend/src/utils.py`

```python
async def resolve_repository(
    access_token: str,
    project_id: str,
) -> tuple[str, str]:
    """Resolve repository owner and name from a project ID.

    Unchanged signature. Internal implementation adds a REST-based lookup
    as step 3 (between GraphQL project-items and workflow-config).

    Args:
        access_token: GitHub access token (scoped to caller).
        project_id: GitHub Projects V2 node ID.

    Returns:
        Tuple of (owner, repo_name).

    Raises:
        ValidationError: If no repository can be resolved from any source.
    """
```

### Fallback Chain Contract

| Step | Source | Failure Mode | Next Step |
|------|--------|-------------|-----------|
| 1 | In-memory cache (token-scoped) | Cache miss | Step 2 |
| 2 | GraphQL project-items | API error, empty result | Step 3 |
| 3 | **REST repository lookup** *(NEW)* | API error, empty result | Step 4 |
| 4 | Workflow configuration (DB) | No config, missing fields | Step 5 |
| 5 | Default repository (settings) | Not configured | Raise `ValidationError` |

---

## No External API Changes

This refactoring does not modify any HTTP endpoint contracts:

- **Response shapes**: Unchanged (same JSON structure, status codes, headers).
- **Request parameters**: Unchanged.
- **Error responses**: Unchanged (same error messages, status codes, `Retry-After` headers).
- **WebSocket messages**: Unchanged.
- **Authentication**: Unchanged.

All changes are internal to the Python function layer. External consumers (frontend, MCP tools, webhooks) require zero modifications.
