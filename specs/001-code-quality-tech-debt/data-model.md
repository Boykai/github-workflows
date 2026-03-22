# Data Model: Code Quality & Technical Debt — Cache Wrapper Extraction, Error Handling Consolidation & Dead Code Sweep

**Feature**: 001-code-quality-tech-debt | **Date**: 2026-03-22

## Overview

This feature is a pure internal refactoring — no new persistent entities, database tables, or data models are introduced. The data model document captures the **in-memory abstractions** being consolidated and the **type signatures** of the new/modified helper methods.

---

## Entities

### E-001: `cached_fetch()` — Existing Global Cache Helper

**Location**: `solune/backend/src/services/cache.py` (lines 187–277)
**Status**: Already exists — no changes to the function itself; only call-site refactoring.

```python
async def cached_fetch(
    cache_key: str,
    fetch_fn: Callable[[], Awaitable[T]],
    ttl_seconds: int = 300,
    force_refresh: bool = False,
    stale_fallback: bool = True,
    cache_instance: InMemoryCache | None = None,
) -> T:
    """Cache-aside helper: get → freshness check → fetch → set with TTL → stale fallback."""
```

**Fields/Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `cache_key` | `str` | Unique key identifying the cached data |
| `fetch_fn` | `Callable[[], Awaitable[T]]` | Async callable that fetches fresh data on cache miss |
| `ttl_seconds` | `int` (default: 300) | Time-to-live for cached entries in seconds |
| `force_refresh` | `bool` (default: False) | When True, bypasses cache and always fetches |
| `stale_fallback` | `bool` (default: True) | When True, returns stale data if fetch fails |
| `cache_instance` | `InMemoryCache \| None` | Optional cache instance; uses global `cache` if None |

**Validation Rules**:
- `cache_key` must be non-empty
- `fetch_fn` must be an async callable
- `ttl_seconds` must be positive

**Relationships**:
- Uses `InMemoryCache.get()`, `InMemoryCache.set()`, `InMemoryCache.get_stale()`
- Called by: board.py, projects.py, utils.py, issues.py, service.py (after refactoring)

---

### E-002: `_cycle_cached()` — New Cycle Cache Instance Method

**Location**: `solune/backend/src/services/github_projects/service.py` (to be added to `GitHubProjectsService`)
**Status**: **NEW** — to be implemented.

```python
async def _cycle_cached(
    self,
    cache_key: str,
    fetch_fn: Callable[[], Awaitable[T]],
) -> T:
    """Per-poll-cycle cache helper: get → hit-count check → fetch → set."""
```

**Fields/Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `self` | `GitHubProjectsService` | Service instance owning the `_cycle_cache` dict |
| `cache_key` | `str` | Key in `self._cycle_cache` (e.g., `"linked_prs:owner/repo/42"`) |
| `fetch_fn` | `Callable[[], Awaitable[T]]` | Async callable that fetches data on cache miss |

**Return**: `T` — the cached or freshly-fetched value

**Behavior**:
1. Check `self._cycle_cache.get(cache_key)`
2. If hit: increment `self._cycle_cache_hit_count`, return cached value
3. If miss: `result = await fetch_fn()`, set `self._cycle_cache[cache_key] = result`, return result

**Validation Rules**:
- `cache_key` must be non-empty string
- `fetch_fn` must be an async callable

**Relationships**:
- Part of `GitHubProjectsService` class
- Uses `self._cycle_cache` (dict) and `self._cycle_cache_hit_count` (int)
- Existing invalidation via `self._invalidate_cycle_cache()` and `self.clear_cycle_cache()` remains unchanged
- Called by: pull_requests.py (3 sites), projects.py (1 site), copilot.py (2 sites), issues.py (1 site)

---

### E-003: `handle_service_error()` — Extended Error Handler

**Location**: `solune/backend/src/logging_utils.py` (lines 224–262)
**Status**: Existing — type signature relaxation required.

**Current Signature**:
```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
```

**Modified Signature**:
```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[Exception] | None = None,
) -> NoReturn:
```

**Fields/Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `exc` | `Exception` | The original exception to log and wrap |
| `operation` | `str` | Human-readable operation name (e.g., "fetch board projects") |
| `error_cls` | `type[Exception] \| None` (relaxed) | Exception class to raise; defaults to `GitHubAPIError` if None |

**Behavior Change**:
- When `error_cls` is an `AppException` subclass: `raise error_cls(message=f"Failed to {operation}") from exc`
- When `error_cls` is a non-`AppException` type (e.g., `ValueError`): `raise error_cls(f"Failed to {operation}") from exc`
- Default behavior (None): unchanged — raises `GitHubAPIError`

**Relationships**:
- Imported by: api/board.py, services/ai_agent.py, services/agents/service.py (after migration)
- Tested in: tests/unit/test_logging_utils.py

---

### E-004: `AppException` Hierarchy — No Changes

**Location**: `solune/backend/src/exceptions.py`
**Status**: Unchanged — documented for reference.

```
Exception
├── AppException (base, 500)
│   ├── GitHubAPIError (502)
│   ├── AuthenticationError (401)
│   ├── AuthorizationError (403)
│   ├── NotFoundError (404)
│   ├── ValidationError (422)
│   ├── RateLimitError (429)
│   ├── ConflictError (409)
│   └── DatabaseError (500)
└── ValueError (stdlib — used by ai_agent.py, NOT part of AppException hierarchy)
```

---

### E-005: `InMemoryCache` — No Changes

**Location**: `solune/backend/src/services/cache.py`
**Status**: Unchanged — documented for reference.

Key methods used by this refactoring:
- `get(key: str) -> T | None` — returns cached value or None if expired
- `get_stale(key: str) -> T | None` — returns cached value even when expired
- `set(key: str, value: T, ttl_seconds: int = 300, ...) -> None` — stores with TTL
- `get_entry(key: str) -> CacheEntry | None` — full entry including metadata

---

## State Transitions

No state transitions are introduced by this refactoring. The existing cache lifecycle (empty → populated → expired → stale-fallback) is unchanged.

---

## Call-Site Mapping

### Global Cache Pattern (FR-001) — 10 Sites → `cached_fetch()`

| # | File | Line | Cache Key Pattern | TTL | Stale Fallback | Refactorable |
|---|------|------|-------------------|-----|----------------|--------------|
| 1 | api/board.py | ~221 | `board:{project_id}` | 300s | Yes (dual-key) | ⚠️ Maybe (dual-key) |
| 2 | api/projects.py | ~128 | `user_projects:{username}` | 300s | Yes | ✅ Yes |
| 3 | api/projects.py | ~150 | (stale fallback for #2) | — | Yes | ✅ Yes (part of #2) |
| 4 | api/projects.py | ~170 | (rate-limit fallback for #2) | — | Yes | ✅ Yes (part of #2) |
| 5 | api/projects.py | ~190 | (error fallback for #2) | — | Yes | ✅ Yes (part of #2) |
| 6 | utils.py | ~238 | `resolve_repo:{hash}:{id}` | 300s | No | ✅ Yes |
| 7 | issues.py | ~751 | `sub_issues:{owner}/{repo}/{num}` | 600s | No | ✅ Yes |
| 8 | service.py | ~108 | Various | Various | Varies | ✅ Yes |
| 9 | api/board.py | ~293 | (error handling for #1) | — | Yes | ⚠️ Maybe |
| 10 | api/board.py | ~432 | `board_data:{id}` | 300s | Yes (dual-key) | ⚠️ Maybe |

### Cycle Cache Pattern (FR-002) — 7 Sites → `_cycle_cached()`

| # | File | Line | Cache Key Pattern | Refactorable |
|---|------|------|-------------------|--------------|
| 1 | pull_requests.py | ~295 | `linked_prs:{owner}/{repo}/{num}` | ✅ Yes |
| 2 | pull_requests.py | ~375 | `pr:{owner}/{repo}/{num}` | ✅ Yes |
| 3 | pull_requests.py | ~450 | `pr_reviews:{owner}/{repo}/{num}` | ✅ Yes |
| 4 | projects.py | ~354 | `items:{project_id}` | ✅ Yes |
| 5 | copilot.py | ~230 | `assigned:{owner}/{repo}/{num}` | ✅ Yes |
| 6 | copilot.py | ~280 | `copilot_status:{owner}/{repo}` | ✅ Yes |
| 7 | issues.py | ~437 | `issue:{owner}/{repo}/{num}` | ✅ Yes |

### Error Handling Pattern (FR-003) — 8 Sites → `handle_service_error()`

| # | File | Line | Current Exception | Migration Target |
|---|------|------|-------------------|-----------------|
| 1 | api/board.py | ~293 | `GitHubAPIError` | `handle_service_error(e, "fetch board projects")` |
| 2 | api/board.py | ~432 | `GitHubAPIError` | `handle_service_error(e, "fetch board data")` |
| 3 | api/board.py | ~532 | `GitHubAPIError` | `handle_service_error(e, "update item status")` |
| 4 | ai_agent.py | ~193 | `ValueError` | `handle_service_error(e, "generate recommendation", ValueError)` |
| 5 | ai_agent.py | ~262 | `ValueError` | `handle_service_error(e, "analyse transcript", ValueError)` |
| 6 | ai_agent.py | ~595 | `ValueError` | `handle_service_error(e, "generate task", ValueError)` |
| 7 | ai_agent.py | ~769 | `ValueError` | `handle_service_error(e, "parse JSON response", ValueError)` |
| 8 | agents/service.py | ~1176 | bare `raise` | `handle_service_error(exc, "agent chat completion")` |
