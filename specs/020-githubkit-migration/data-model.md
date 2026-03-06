# Data Model: Simplify GitHub Service with githubkit

**Date**: 2026-03-05  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Entity Changes

This feature is a refactoring — no new database tables or persistent entities are created. The changes are to in-memory service-layer entities.

### New Entities

#### GitHubClientFactory

A singleton factory/pool that creates and manages authenticated githubkit client instances.

| Attribute | Type | Description |
|-----------|------|-------------|
| `_pool` | `BoundedDict[str, GitHub]` | Bounded pool of active clients keyed by token hash (max 50) |
| `_auto_retry` | `RetryChainDecision` | Shared retry policy (rate-limit + server-error) |
| `_throttler` | `LocalThrottler` | Shared concurrency limiter (100 concurrent requests) |

**Methods**:
- `get_client(access_token: str) -> GitHub` — Returns pooled client or creates new one
- `close_all() -> None` — Closes all pooled clients on shutdown

**Lifecycle**: Created once at application startup in `dependencies.py`, stored on `app.state`.

#### GraphQL Helper (within service)

A thin wrapper method on `GitHubProjectsService` for GraphQL calls requiring custom headers.

| Parameter | Type | Description |
|-----------|------|-------------|
| `client` | `GitHub` | Authenticated SDK client |
| `query` | `str` | GraphQL query string |
| `variables` | `dict` | Query variables |
| `graphql_features` | `list[str] \| None` | Optional feature flags for `GraphQL-Features` header |

**Returns**: `dict` (parsed GraphQL response data)

### Modified Entities

#### GitHubProjectsService

The primary service class. Changes to the constructor and method signatures:

**Removed fields** (replaced by SDK):
- `_client: httpx.AsyncClient` → Replaced by per-call `GitHub` client from factory
- `_etag_cache: dict[str, tuple[str, dict]]` → Replaced by SDK `http_cache=True`
- `_ETAG_CACHE_MAX_SIZE: int` → Removed
- `_last_request_time: float` → Removed (SDK throttler handles)
- `_min_request_interval: float` → Removed
- `_global_cooldown_until: float` → Removed (SDK handles per-client)
- `_cooldown_lock: asyncio.Lock` → Removed
- `_last_rate_limit: dict[str, int] | None` → Simplified to response-header extraction

**Preserved fields** (domain-specific):
- `_cycle_cache: dict[str, object]` — Per-polling-cycle read cache
- `_inflight_graphql: BoundedDict[str, asyncio.Task[dict]]` — Request coalescing
- `_coalesced_hit_count`, `_cooldown_hit_count`, `_cycle_cache_hit_count` — Metrics counters

**Changed fields**:
- `_client_factory: GitHubClientFactory` — New: reference to client factory (replaces `_client`)

**Method signature changes**:
- Most public methods keep their `access_token: str` parameter — the service calls `self._client_factory.get_client(access_token)` internally
- `_graphql()` method simplified to delegate to SDK's `async_graphql()` or `arequest()` for custom-header cases
- `close()` → Delegates to `self._client_factory.close_all()`

**Removed methods** (infrastructure):
- `_request_with_retry()` — SDK handles retry
- `_build_headers()` — SDK handles auth headers
- `_extract_rate_limit_headers()` — Simplified to response header read
- `_parse_retry_after_seconds()` — SDK handles Retry-After
- `_is_secondary_limit()` — SDK detects via `SecondaryRateLimitExceeded`
- `_apply_global_cooldown()` — Removed (SDK throttler)
- `_respect_global_cooldown()` — Removed (SDK throttler)
- `http_get()` — Replaced by SDK `arequest("GET", ...)`

#### GitHubAuthService

**Removed fields**:
- `_client: httpx.AsyncClient` → Replaced by githubkit OAuth strategies

**Simplified methods**:
- `exchange_code_for_token()` → Uses `OAuthWebAuthStrategy` + `exchange_token()`
- `refresh_token()` → Uses `OAuthTokenAuthStrategy` + `async_refresh()`

**Preserved** (unchanged):
- SQLite session persistence
- CSRF state validation (in-memory `BoundedDict`)
- `UserSession` model

### Exception Type Mapping

| Domain Usage | Old Type | New Type | Import |
|-------------|----------|----------|--------|
| HTTP status error | `httpx.HTTPStatusError` | `RequestFailed` | `githubkit.exception` |
| General HTTP error | `httpx.HTTPError` | `RequestError` | `githubkit.exception` |
| Connection error | `httpx.ConnectError` | `RequestError` | `githubkit.exception` |
| Timeout | `httpx.TimeoutException` | `RequestTimeout` | `githubkit.exception` |
| Rate limit (auto-handled) | Manual 403/429 check | `RateLimitExceeded` | `githubkit.exception` |
| GraphQL error | Manual `"errors"` key check | `GraphQLFailed` | `githubkit.exception` |

### Unchanged Entities

| Entity | File | Reason |
|--------|------|--------|
| `GitHubProject` | `models/project.py` | Data model — no transport dependency |
| `Task` | `models/task.py` | Data model — no transport dependency |
| `StatusColumn` | `models/project.py` | Data model — no transport dependency |
| `UserSession` | `models/user.py` | Persistence model — unchanged |
| GraphQL queries/mutations | `graphql.py` | Domain query strings — transport-agnostic |
| `CommitWorkflowResult` | `github_commit_workflow.py` | Dataclass — no transport dependency |

## Relationships

```
GitHubClientFactory (singleton, app.state)
    │
    ├── creates → GitHub (SDK client, per-user, pooled)
    │                │
    │                ├── used by → GitHubProjectsService._graphql()
    │                ├── used by → GitHubProjectsService.create_issue()
    │                ├── used by → GitHubProjectsService.assign_copilot_to_issue()
    │                └── used by → ... (all 85 methods)
    │
    └── used by → GitHubAuthService (OAuth token exchange/refresh)

GitHubProjectsService
    │
    ├── _client_factory → GitHubClientFactory
    ├── _cycle_cache (domain, unchanged)
    ├── _inflight_graphql (domain, unchanged)
    └── get_last_rate_limit() → reads from last Response.headers
```
