# Data Model: Simplify GitHub Service with githubkit v0.14.6

**Feature**: `019-githubkit-migration`
**Date**: 2026-03-06
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

---

## Entity Definitions

### 1. RateLimitState

**Purpose**: Lightweight data object exposing GitHub API rate limit status to consumers (primarily `copilot_polling.py`) without coupling them to githubkit internals or httpx response objects.

**Location**: `backend/src/models/rate_limit.py`

| Field | Type | Description | Nullable |
|-------|------|-------------|----------|
| `limit` | `int` | Maximum requests allowed per hour | No |
| `remaining` | `int` | Requests remaining in the current window | No |
| `reset_at` | `int` | Unix timestamp when the rate limit window resets | No |
| `used` | `int` | Requests consumed in the current window (`limit - remaining`) | No |
| `resource` | `str` | Rate limit resource category (default: `"core"`) | No |

**Validation Rules**:
- `limit >= 0`
- `remaining >= 0`
- `remaining <= limit`
- `reset_at > 0`
- `used == limit - remaining` (computed)
- `resource` is one of `"core"`, `"graphql"`, `"search"`, `"integration_manifest"`

**State Transitions**: None — immutable value object. New instances are created on each API response.

**Relationships**: Consumed by `copilot_polling/polling_loop.py` via `GitHubClientFactory.get_rate_limit()`.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class RateLimitState:
    """Immutable snapshot of GitHub API rate limit status."""
    limit: int
    remaining: int
    reset_at: int
    used: int
    resource: str = "core"
```

---

### 2. GitHubClientFactory

**Purpose**: Creates and pools authenticated githubkit `GitHub` client instances per user token. Manages client lifecycle, connection pooling, and rate limit event capture.

**Location**: `backend/src/services/github_projects/client_factory.py`

| Field | Type | Description | Nullable |
|-------|------|-------------|----------|
| `_pool` | `BoundedDict[str, GitHub]` | Client pool keyed by token hash (max 50) | No |
| `_rate_limit` | `RateLimitState \| None` | Most recent rate limit state from any response | Yes |
| `_max_pool_size` | `int` | Maximum number of pooled clients (default: 50) | No |

**Validation Rules**:
- Pool key is `hashlib.sha256(token.encode()).hexdigest()[:16]` (consistent with existing pattern in `_graphql()`)
- Pool size never exceeds `_max_pool_size` (enforced by `BoundedDict`)
- Token is never stored in plain text in the pool — only the hash is used as key

**State Transitions**:
```
Empty Pool → Client Created (on first get_client() call for a token)
Pool at Capacity → Oldest Evicted (FIFO via BoundedDict when 51st unique token arrives)
Client Retrieved → Moved to End (LRU refresh on access)
Factory Closed → All Clients Closed (cleanup on shutdown)
```

**Relationships**:
- Creates `GitHub` instances (githubkit SDK)
- Uses `BoundedDict` from `src/utils.py` for pool management
- Produces `RateLimitState` instances for consumers
- Consumed by `GitHubProjectsService` for all API operations
- Registered on `app.state` via `dependencies.py`

**Key Methods**:

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_client` | `(token: str) -> GitHub` | Get or create a pooled githubkit client for the given token |
| `get_rate_limit` | `() -> RateLimitState \| None` | Return the most recent rate limit state |
| `clear_rate_limit` | `() -> None` | Clear cached rate limit state |
| `close` | `async () -> None` | Close all pooled clients and release resources |

```python
class GitHubClientFactory:
    """Factory for creating and pooling authenticated GitHub SDK clients."""

    def __init__(self, max_pool_size: int = 50) -> None:
        self._pool: BoundedDict[str, GitHub] = BoundedDict(maxlen=max_pool_size)
        self._rate_limit: RateLimitState | None = None
        self._max_pool_size = max_pool_size

    def get_client(self, token: str) -> GitHub:
        """Get or create a pooled GitHub client for the given access token."""
        key = hashlib.sha256(token.encode()).hexdigest()[:16]
        client = self._pool.get(key)
        if client is not None:
            return client
        client = GitHub(
            TokenAuthStrategy(token),
            auto_retry=RetryOption(enabled=True),
            http_cache=True,
            throttler=LocalThrottler(),
        )
        self._pool[key] = client
        return client

    def get_rate_limit(self) -> RateLimitState | None:
        return self._rate_limit

    def clear_rate_limit(self) -> None:
        self._rate_limit = None

    async def close(self) -> None:
        for client in self._pool.values():
            await client.aclose()
        self._pool.clear()
```

---

### 3. GitHubProjectsService (Modified)

**Purpose**: Existing service class modified to accept `GitHubClientFactory` and delegate infrastructure concerns to githubkit.

**Location**: `backend/src/services/github_projects/service.py` (existing, modified)

**Key Changes to Fields**:

| Field | Before | After | Rationale |
|-------|--------|-------|-----------|
| `_client` | `httpx.AsyncClient` | Removed | githubkit manages its own httpx client |
| `_client_factory` | N/A | `GitHubClientFactory` | New dependency injection point |
| `_last_rate_limit` | `dict[str, int] \| None` | Removed | Replaced by `RateLimitState` on factory |
| `_etag_cache` | `dict[str, tuple[str, dict]]` | Removed | githubkit handles ETag caching |
| `_ETAG_CACHE_MAX_SIZE` | `int = 256` | Removed | githubkit handles cache sizing |
| `_last_request_time` | `float` | Removed | githubkit `LocalThrottler` handles this |
| `_min_request_interval` | `float = 0.5` | Removed | githubkit `LocalThrottler` handles this |
| `_global_cooldown_until` | `float` | Removed | githubkit retry handles cooldowns |
| `_cooldown_lock` | `asyncio.Lock` | Removed | No longer needed |
| `_inflight_graphql` | `BoundedDict[str, asyncio.Task]` | Preserved | Application-layer deduplication |
| `_cycle_cache` | `dict[str, object]` | Preserved | Application-layer per-poll caching |
| `_low_quota_threshold` | `int = 150` | Removed | githubkit manages throttling |
| `_coalesced_hit_count` | `int` | Preserved | Metrics for in-flight coalescing |
| `_cooldown_hit_count` | `int` | Removed | githubkit manages cooldowns |
| `_cycle_cache_hit_count` | `int` | Preserved | Metrics for cycle cache |

**Methods Removed** (infrastructure replaced by githubkit):
- `_request_with_retry()` (~150 LOC)
- `_build_headers()` (~8 LOC)
- `_extract_rate_limit_headers()` (~30 LOC)
- `get_last_rate_limit()` (~10 LOC)
- `clear_last_rate_limit()` (~15 LOC)
- `_parse_retry_after_seconds()` (~22 LOC)
- `_is_secondary_limit()` (~15 LOC)
- `_apply_global_cooldown()` (~8 LOC)
- `_respect_global_cooldown()` (~8 LOC)
- `http_get()` (~5 LOC) — replaced by `github.request("GET", ...)`
- `close()` — simplified to delegate to factory

**Methods Preserved** (application-layer logic):
- `_with_fallback()` — retry strategy helper
- `clear_cycle_cache()` — per-poll cache management
- `_invalidate_cycle_cache()` — targeted cache invalidation
- `_maybe_log_request_management_metrics()` — observability
- `is_copilot_author()` — domain logic
- `is_copilot_swe_agent()` — domain logic

---

### 4. GitHubAuthService (Modified)

**Purpose**: Existing OAuth service modified to use githubkit for token exchange and user info, preserving all SQLite session management.

**Location**: `backend/src/services/github_auth.py` (existing, modified)

**Key Changes to Fields**:

| Field | Before | After | Rationale |
|-------|--------|-------|-----------|
| `_client` | `httpx.AsyncClient(timeout=30.0)` | Removed | githubkit manages HTTP transport |
| `_client_factory` | N/A | `GitHubClientFactory` (optional) | For user info retrieval via SDK |

**Methods Modified**:
- `exchange_code_for_token()` — uses githubkit OAuth strategy or direct `github.request()`
- `get_github_user()` — uses `github.rest.users.get_authenticated()`
- `refresh_token()` — uses githubkit token refresh strategy
- `create_session_from_token()` — uses factory to get client
- `close()` — no-op (factory manages client lifecycle)

**Methods Preserved** (application logic):
- `generate_oauth_url()` — URL generation stays (simple string formatting)
- `validate_state()` — OAuth state validation (in-memory BoundedDict)
- `create_session()` — session creation (SQLite via session_store)
- `get_session()` — session retrieval
- `update_session()` — session update
- `revoke_session()` — session revocation

---

## Entity Relationship Summary

```
┌─────────────────────┐         ┌──────────────────────────┐
│  GitHubClientFactory│ ──1:N──▶│  GitHub (githubkit SDK)  │
│                     │         │  - per-user async client  │
│  pool: BoundedDict  │         │  - retry, cache, throttle│
│  rate_limit: State  │         └──────────────────────────┘
└─────────┬───────────┘
          │ consumed by
          ▼
┌─────────────────────┐         ┌──────────────────────────┐
│GitHubProjectsService│ ──uses──▶│  graphql.py (31 queries) │
│  - 85 business      │         │  - query/mutation strings │
│    methods           │         │  - no infrastructure     │
│  - cycle cache      │         └──────────────────────────┘
│  - inflight dedup   │
└─────────────────────┘
          │ rate limit exposed to
          ▼
┌─────────────────────┐
│  RateLimitState     │◀── read by copilot_polling.py
│  (frozen dataclass) │
│  - limit, remaining │
│  - reset_at, used   │
└─────────────────────┘
```
