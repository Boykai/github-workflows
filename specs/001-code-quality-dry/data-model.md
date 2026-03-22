# Data Model: Phase 2 — Code Quality & DRY Consolidation

**Feature**: 001-code-quality-dry  
**Date**: 2026-03-22  
**Input**: [spec.md](spec.md), [research.md](research.md)

## Overview

This feature is a pure refactoring — no new persistent data entities are introduced. All changes affect in-memory utilities, function signatures, and call-site patterns. The "entities" below describe the contracts and structures being created or modified.

---

## Entity 1: Extended `cached_fetch()` Signature

**Location**: `solune/backend/src/services/cache.py`  
**Type**: Function signature extension (backward-compatible)

### Fields (Parameters)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_instance` | `InMemoryCache` | *(required)* | Cache instance to use |
| `key` | `str` | *(required)* | Cache key |
| `fetch_fn` | `Callable[[], Awaitable[T]]` | *(required)* | Async function to fetch data on cache miss |
| `ttl_seconds` | `int \| None` | `None` | Time-to-live for cached entry |
| `refresh` | `bool` | `False` | Force bypass cache and fetch fresh data |
| `stale_fallback` | `bool` | `False` | Return stale data on fetch failure |
| `rate_limit_fallback` | `bool` | `False` | **(NEW)** Return stale data specifically on `RateLimitError`, log rate-limit warning |
| `data_hash_fn` | `Callable[[T], str] \| None` | `None` | **(NEW)** Hash function for data-change detection; if hash matches cached entry, refresh TTL only |

### Validation Rules

- `rate_limit_fallback` and `stale_fallback` are independent — `rate_limit_fallback=True` handles `RateLimitError` specifically, while `stale_fallback=True` handles all exceptions.
- If both are `True`, `RateLimitError` is handled by `rate_limit_fallback` (with its specific log message) and other exceptions by `stale_fallback`.
- `data_hash_fn` is called only on successful fetch. If it returns a hash matching the existing cache entry's `data_hash`, `refresh_ttl()` is called instead of `set()`.

### State Transitions

```
Cache Miss → fetch_fn() → Success → [data_hash_fn check] → set() or refresh_ttl() → Return data
Cache Miss → fetch_fn() → RateLimitError + rate_limit_fallback → get_stale() → Return stale or re-raise
Cache Miss → fetch_fn() → Exception + stale_fallback → get_stale() → Return stale or re-raise
Cache Hit → Return cached data
```

---

## Entity 2: `_with_fallback()` Method

**Location**: `solune/backend/src/services/github_projects/service.py` (on base service class)  
**Type**: New async method

### Fields (Parameters)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primary_fn` | `Callable[[], Awaitable[T]]` | *(required)* | Primary strategy function |
| `fallback_fn` | `Callable[[], Awaitable[T]]` | *(required)* | Fallback strategy function |
| `operation` | `str` | *(required)* | Human-readable operation name for logging |
| `verify_fn` | `Callable[[], Awaitable[bool]] \| None` | `None` | Optional verification between primary and fallback |

### Return Type

`T | None` — Returns the result of the first successful strategy, or `None` if all strategies fail.

### Validation Rules

- All exceptions in `primary_fn`, `verify_fn`, and `fallback_fn` are caught and logged — never propagated.
- If `verify_fn` raises, it is treated as verification failure (proceed to fallback).
- If `primary_fn` succeeds and no `verify_fn` is provided, returns the primary result.
- If `primary_fn` succeeds and `verify_fn` returns `True`, returns the primary result.
- If `primary_fn` succeeds but `verify_fn` returns `False` (or raises), proceeds to `fallback_fn`.
- If `primary_fn` raises, proceeds directly to `fallback_fn` (skips `verify_fn`).

### State Transitions

```
primary_fn() ──Success──► [verify_fn?] ──Yes/None──► Return result
                              │
                           No/Raises
                              │
                              ▼
                       fallback_fn() ──Success──► Return result
                              │
                           Raises
                              │
                              ▼
                        Return None (soft failure)

primary_fn() ──Raises──► fallback_fn() ──Success──► Return result
                              │
                           Raises
                              │
                              ▼
                        Return None (soft failure)
```

---

## Entity 3: `handle_service_error()` Migration Sites

**Location**: `solune/backend/src/logging_utils.py` (utility function)  
**Type**: Existing function — no signature changes

### Current Signature

```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
```

### Migration Mapping

| # | Source File | Pattern | Target `error_cls` | Migrate? |
|---|------------|---------|-------------------|----------|
| 1 | `board.py:246-256` | `except Exception` → rate-limit/auth check → raise | `RateLimitError` / `AuthenticationError` | Yes (split by exception type) |
| 2 | `board.py:405-407` | `except ValueError` → `NotFoundError` | `NotFoundError` | Yes |
| 3 | `board.py:408-433` | `except Exception` → rate-limit/auth/generic → raise | `GitHubAPIError` | Yes (split by exception type) |
| 4-10 | `tools.py` (7 sites) | Mixed `HTTPException` / `AppException` raises | Per-site decision | See research.md Task 1 |
| 11 | `pipelines.py:140` | `except Exception` → re-raise | Per-site | Yes |
| 12 | `tasks.py:137` | Conditional raise | `ValidationError` | Yes |
| 13-14 | `webhooks.py:246` (2 sites) | `except Exception` → raise | `AuthenticationError` / `AppException` | Yes |

### Validation Rules for Migration

- Each migrated site MUST produce identical client-visible responses (status code, message format).
- Sites raising `HTTPException` (tools.py) require individual assessment — see research.md.
- Excluded patterns: health check endpoints, WebSocket handlers, error-returning webhook handlers (return dicts, not raise).

---

## Entity 4: `resolve_repository()` Extended Fallback Chain

**Location**: `solune/backend/src/utils.py`  
**Type**: Function modification — new fallback step inserted

### Current Fallback Chain

```
Step 1: Check in-memory cache (token-scoped)
Step 2: GraphQL project-items lookup
Step 3: Workflow configuration (in-memory/DB)
Step 4: Default repository from settings (.env)
```

### New Fallback Chain

```
Step 1: Check in-memory cache (token-scoped)
Step 2: GraphQL project-items lookup
Step 3: REST-based repository lookup ← NEW
Step 4: Workflow configuration (in-memory/DB)
Step 5: Default repository from settings (.env)
```

### New Step 3 Contract

| Aspect | Detail |
|--------|--------|
| Input | `access_token: str`, `project_id: str` |
| Output | `tuple[str, str] \| None` (owner, repo) or None on failure |
| Method | REST API via `github_projects_service` |
| Error handling | Catches all exceptions, logs warning, returns None (allows next step) |
| Caching | On success, caches result same as other steps (300s TTL, token-scoped key) |

---

## Relationships

```
cached_fetch() ◄── list_projects()        [migrated caller]
               ◄── list_board_projects()   [migrated caller, composed fetch_fn]
               ◄── get_board_data()        [migrated caller]
               ◄── send_message()          [migrated caller, read-only cache]
               ◄── send_tasks()            [NOT migrated — see research.md]

_with_fallback() ◄── add_issue_to_project()  [migrated caller]
                 ◄── assign_copilot_to_issue()  [NOT migrated — see research.md]
                 ◄── find_existing_pr_for_issue()  [NOT migrated — see research.md]

handle_service_error() ◄── 14 catch→raise sites  [migrated callers]

resolve_repository() ◄── main.py startup  [deduplication — replaces inline logic]
```
