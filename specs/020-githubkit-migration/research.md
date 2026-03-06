# Research: Simplify GitHub Service with githubkit

**Date**: 2026-03-05  
**Purpose**: Resolve all technical unknowns before Phase 1 design

## 1. githubkit Async Client Patterns

**Decision**: Use `GitHub(TokenAuthStrategy(token))` for per-user async clients  
**Rationale**: githubkit natively supports async. Each user gets an isolated client with `TokenAuthStrategy`.  
**Alternatives considered**: `with_auth()` to derive per-user clients from a base instance — rejected because base client without auth would fail health checks.

### Client Creation Pattern

```python
from githubkit import GitHub, TokenAuthStrategy
from githubkit.retry import RETRY_RATE_LIMIT, RETRY_SERVER_ERROR, RetryChainDecision
from githubkit.throttling import LocalThrottler

def create_client(access_token: str) -> GitHub:
    return GitHub(
        TokenAuthStrategy(access_token),
        auto_retry=RetryChainDecision(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR),
        http_cache=True,
        throttler=LocalThrottler(100),  # max concurrent requests
        timeout=30.0,
    )
```

### Client Pooling Pattern

Pool clients per token hash using the existing `BoundedDict` pattern:

```python
from src.utils import BoundedDict
import hashlib

_client_pool: BoundedDict[str, GitHub] = BoundedDict(maxlen=50)

def get_client(access_token: str) -> GitHub:
    key = hashlib.sha256(access_token.encode()).hexdigest()[:16]
    client = _client_pool.get(key)
    if client is None:
        client = create_client(access_token)
        _client_pool[key] = client
    return client
```

## 2. githubkit Exception Types

**Decision**: Replace all `httpx.HTTPStatusError` catches with githubkit exception types  
**Rationale**: githubkit wraps httpx exceptions — it never raises raw httpx exceptions  

### Exception Hierarchy

```
GitHubException (base)
├── AuthCredentialError
├── AuthExpiredError
├── RequestError
│   ├── RequestTimeout
│   └── RequestFailed          ← replaces httpx.HTTPStatusError
│       └── RateLimitExceeded
│           ├── PrimaryRateLimitExceeded
│           └── SecondaryRateLimitExceeded
├── GraphQLError
│   ├── GraphQLFailed
│   └── GraphQLPaginationError
└── CacheUnsupportedError
```

### Migration Mapping

| Current (httpx) | New (githubkit) | Notes |
|-----------------|-----------------|-------|
| `httpx.HTTPStatusError` | `RequestFailed` | `.response.status_code`, `.response.headers` available |
| `httpx.HTTPError` | `RequestError` | Base class for all request failures |
| `httpx.ConnectError` | `RequestError` | Wrapped |
| `httpx.TimeoutException` | `RequestTimeout` | Wrapped |
| Manual 429 check | `RateLimitExceeded` | Auto-retried; `.retry_after` available |
| Manual secondary limit check | `SecondaryRateLimitExceeded` | Auto-detected |
| Manual GraphQL error parsing | `GraphQLFailed` | `.response.errors` list available |

### Affected Files (exception catch sites)

| File | Current Exception | Migration Action |
|------|-------------------|------------------|
| `services/github_projects/service.py` (5 sites) | `httpx.HTTPStatusError`, `httpx.HTTPError` | Replace with `RequestFailed`, `RequestError` |
| `api/board.py` (2 sites) | `isinstance(exc, httpx.HTTPStatusError)` | Replace with `isinstance(exc, RequestFailed)` |
| `services/metadata_service.py` (2 sites) | `httpx.HTTPStatusError`, `httpx.ConnectError` | Replace with `RequestFailed`, `RequestError` |
| `services/signal_delivery.py` | `httpx.ConnectError`, `httpx.TimeoutException` | NOT in scope (Signal service uses own httpx client) |

**Note**: `signal_bridge.py` and `signal_delivery.py` use httpx for Signal API, not GitHub. These are out of scope.

## 3. GraphQL with Custom Headers

**Decision**: Use `github.arequest("POST", "/graphql", json=..., headers=...)` for GraphQL calls needing `GraphQL-Features` headers  
**Rationale**: `github.graphql()` does NOT accept a `headers` parameter. The generic `arequest()` does.  
**Alternatives considered**: Monkey-patching the graphql namespace — rejected as fragile and SDK-version-dependent.

### Pattern for Standard GraphQL

```python
# Standard GraphQL — use github.graphql() (handles auth + retry + cache)
data = await github.async_graphql(query, variables={"login": username, "first": 20})
```

### Pattern for GraphQL with Custom Headers

```python
# GraphQL requiring custom headers (Copilot assignment, review request)
response = await github.arequest(
    "POST",
    "/graphql",
    json={"query": query, "variables": variables},
    headers={"GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"},
)
data = response.json()
if "errors" in data:
    error_msg = "; ".join(e.get("message", str(e)) for e in data["errors"])
    raise ValueError(f"GraphQL error: {error_msg}")
return data.get("data", {})
```

### Affected Operations

| Operation | Needs Custom Headers | Pattern |
|-----------|---------------------|---------|
| List projects, get items, get issue, get PR | No | `github.async_graphql()` |
| Assign Copilot to issue | Yes (`GraphQL-Features`) | `github.arequest("POST", "/graphql", ...)` |
| Get suggested actors | Yes (`GraphQL-Features`) | `github.arequest("POST", "/graphql", ...)` |
| All mutations (create branch, commit, PR, merge) | No | `github.async_graphql()` |

## 4. OAuth Web Flow via githubkit

**Decision**: Replace manual OAuth with `OAuthWebAuthStrategy` + `OAuthTokenAuthStrategy`  
**Rationale**: SDK handles token exchange HTTP calls, PKCE, and error handling natively  

### Current vs. New Flow

| Step | Current (manual httpx) | New (githubkit) |
|------|----------------------|-----------------|
| Generate auth URL | Manual URL construction | `GitHub(OAuthAppAuthStrategy(client_id, client_secret)).auth.get_auth_url(scopes=[...])` |
| Exchange code for token | `httpx.post("github.com/login/oauth/access_token")` | `OAuthWebAuthStrategy(client_id, client_secret, code)` → `exchange_token()` |
| Refresh token | `httpx.post(...)` with refresh_token | `OAuthTokenAuthStrategy(client_id, client_secret, refresh_token=...)` → `async_refresh()` |
| Session storage | SQLite (unchanged) | SQLite (unchanged) |

### What stays

- CSRF state generation and validation (in-memory `BoundedDict`, TTL 10min, max 1000)
- SQLite session persistence (UserSession model)
- Token expiration tracking

## 5. Throttler Behavior

**Decision**: `LocalThrottler(100)` replaces the hand-rolled 500ms inter-call delay  
**Rationale**: The throttler controls max concurrency (100 concurrent requests), not inter-call timing. This is a different mechanism than the current 500ms delay.  

### Key Finding

`LocalThrottler` is a **concurrency limiter**, not a rate spacer. It caps concurrent in-flight requests to `max_concurrency`.

The current 500ms inter-call delay is more aggressive than needed because:
1. The SDK's `auto_retry` handles 429 responses with proper `Retry-After` backoff
2. The SDK's `http_cache` prevents redundant requests from consuming quota
3. GitHub's actual rate limit is 5,000 req/hour ≈ 1.2 req/sec average

**Migration approach**: Remove the manual 500ms delay. Let the SDK's retry + cache handle rate management. If rate-limit issues arise in production, add a custom `BaseThrottler` implementation that enforces minimum inter-call spacing.

## 6. Rate-Limit Visibility for Polling Service

**Decision**: Extract rate-limit info from SDK response headers post-request  
**Rationale**: githubkit `Response` exposes `.headers` directly, so `X-RateLimit-Remaining` etc. are accessible  

### Current Pattern

```python
# Current: service extracts from httpx response headers into contextvar/instance
self._extract_rate_limit_headers(response)
# Polling service reads:
rl = github_projects_service.get_last_rate_limit()
```

### New Pattern

```python
# New: after any SDK call, response.headers has rate-limit info
resp = await github.rest.repos.get(owner, repo)
remaining = int(resp.headers.get("X-RateLimit-Remaining", "5000"))
reset_at = int(resp.headers.get("X-RateLimit-Reset", "0"))

# Keep get_last_rate_limit() as a thin wrapper that reads last response headers
```

### Consumers to Update

| Consumer | File | Current Access | Migration |
|----------|------|---------------|-----------|
| Board API rate-limit info | `api/board.py` L142, L274 | `github_projects_service.get_last_rate_limit()` | Keep method, backed by response header extraction |
| Polling loop budget check | `copilot_polling/polling_loop.py` L30, L456 | `github_projects_service.get_last_rate_limit()` | Keep method, same interface |

**Approach**: Keep `get_last_rate_limit()` method signature. Implementation changes from "extract from httpx response" to "extract from last githubkit response headers". Same contextvar + instance-level dual-storage pattern.

## 7. Preview API Compatibility

**Decision**: Use `github.arequest()` for Sub-Issues and Copilot assignment REST APIs  
**Rationale**: These are preview/undocumented endpoints that don't have typed SDK methods  

### Preview API Inventory

| API | Current Endpoint | Has Typed SDK Method? | Migration Pattern |
|-----|-----------------|----------------------|-------------------|
| Create sub-issue | `POST /repos/{o}/{r}/issues/{n}/sub_issues` | No | `github.arequest("POST", url, json=body)` |
| Get sub-issues | `GET /repos/{o}/{r}/issues/{n}/sub_issues` | No | `github.arequest("GET", url)` |
| Assign Copilot (REST) | `POST /repos/{o}/{r}/issues/{n}/assignees` | Partial (`github.rest.issues.add_assignees`) | Try typed method; fall back to `arequest` if custom body needed |
| Unassign Copilot | `DELETE /repos/{o}/{r}/issues/{n}/assignees` | Yes (`github.rest.issues.remove_assignees`) | Typed method |

### Benefits of `arequest()` over current raw httpx

- Auth header injected automatically
- SDK throttler applies
- Auto-retry on 429/5xx
- No manual URL base construction (`/repos/...` relative paths work)
