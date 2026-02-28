# Data Model: Refactor Codebase for Quality, Best Practices, and UX Improvements

## Overview

This refactor modifies no database schema. All changes target application-level constants, configuration properties, and runtime behavior. This document describes the entities affected and the nature of each change.

## Entities

### 1. StatusNames (class in `backend/src/constants.py`)

**Type**: Application constant (class with string attributes)
**Change**: None — `StatusNames` is the source of truth and remains unchanged.

| Attribute | Value |
|-----------|-------|
| BACKLOG | `"Backlog"` |
| READY | `"Ready"` |
| IN_PROGRESS | `"In Progress"` |
| IN_REVIEW | `"In Review"` |
| DONE | `"Done"` |

### 2. DEFAULT_STATUS_COLUMNS (constant in `backend/src/constants.py`)

**Type**: Module-level list constant
**Change**: Replace hardcoded strings with `StatusNames` references.

| Field | Before | After |
|-------|--------|-------|
| Value | `["Todo", "In Progress", "Done"]` | `[StatusNames.BACKLOG, StatusNames.IN_PROGRESS, StatusNames.DONE]` |

**Relationships**: Used as a fallback in:
- `GitHubProjectsService.get_user_projects()` — default status columns when project has none
- `chat_endpoint()` — available statuses for AI status change parsing
- `signal_chat.process_signal_message()` — available statuses for Signal chat parsing

### 3. GlobalSettings (database table, singleton row)

**Type**: SQLite table (1 row, `id = 1`)
**Schema change**: None
**Behavioral change**: The `require_admin` dependency now uses an atomic UPDATE to set `admin_github_user_id`.

| Column | Type | Relevance |
|--------|------|-----------|
| `admin_github_user_id` | `INTEGER DEFAULT NULL` | Atomic `UPDATE ... WHERE admin_github_user_id IS NULL` prevents race condition |

**State transitions for `admin_github_user_id`**:
```
NULL → user_id (atomic promotion — exactly one request succeeds)
user_id → user_id (no change — same admin re-authenticated)
```

### 4. Settings (Pydantic model in `backend/src/config.py`)

**Type**: Pydantic `BaseSettings` with `lru_cache` wrapper
**Changes**:

| Change | Detail |
|--------|--------|
| New property: `effective_cookie_secure` | `@property` returning `bool` — `True` if `cookie_secure` is `True` OR `frontend_url` starts with `"https://"` |
| Updated `env_file` | From `"../.env"` to `("../.env", ".env")` — supports both local dev and Docker |

**Validation rules**:
- `effective_cookie_secure` is read-only (computed property)
- `.env` file precedence: `.env` (local) overrides `../.env` (parent) when both exist

### 5. clear_settings_cache (function in `backend/src/config.py`)

**Type**: New module-level function
**Signature**: `def clear_settings_cache() -> None`
**Implementation**: Delegates to `get_settings.cache_clear()`
**Purpose**: Explicit cache-clearing utility for test teardown

### 6. BoundedDict (generic class in `backend/src/utils.py`)

**Type**: Application utility class
**Change**: None — all required dict methods already implemented.

Confirmed interface:
- `__setitem__`, `__getitem__`, `__delitem__`, `__contains__`, `__len__`
- `__iter__`, `get`, `pop`, `keys`, `values`, `items`, `clear`, `__repr__`

### 7. _session_cleanup_loop (async function in `backend/src/main.py`)

**Type**: Background asyncio task
**Change**: Add exponential backoff on consecutive failures.

| Parameter | Value |
|-----------|-------|
| Base interval | `settings.session_cleanup_interval` (default 3600s) |
| Backoff formula | `min(interval × 2^consecutive_failures, 300)` |
| Max backoff | 300 seconds (5 minutes) |
| Reset condition | Successful cleanup run |

**State transitions**:
```
consecutive_failures = 0 → success → stays 0
consecutive_failures = 0 → failure → 1 (next sleep: min(interval×2, 300))
consecutive_failures = N → failure → N+1 (next sleep: min(interval×2^(N+1), 300))
consecutive_failures = N → success → 0 (next sleep: interval)
```

## Non-Entities (Configuration / Infrastructure)

### Docker Healthcheck

**Files**: `backend/Dockerfile`, `docker-compose.yml`
**Change**: Replace `python -c "import httpx; ..."` with `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"`

### Frontend Dependencies

**File**: `frontend/package.json`
**Change**: Remove `jsdom` from `devDependencies`

### Lifespan Handler

**File**: `backend/src/main.py`
**Change**: Wrap startup in `try/finally` to ensure cleanup on failure
