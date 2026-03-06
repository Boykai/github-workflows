# API Contracts: Simplify GitHub Service with githubkit

**Date**: 2026-03-05  
**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

## Overview

This feature changes **internal service interfaces only**. No public HTTP API endpoints are added, removed, or modified. The frontend is unaffected.

All changes are to the internal Python method signatures on `GitHubProjectsService`, `GitHubAuthService`, and the new `GitHubClientFactory`.

## Internal Service Contracts

### GitHubClientFactory

```python
class GitHubClientFactory:
    """Creates and pools authenticated githubkit client instances."""

    def __init__(self, max_pool_size: int = 50) -> None: ...

    def get_client(self, access_token: str) -> GitHub:
        """Return a pooled or newly created client for the given token.
        
        Thread-safe. Clients are keyed by SHA-256 hash prefix (16 chars).
        When pool exceeds max_pool_size, oldest entry is evicted.
        """
        ...

    async def close_all(self) -> None:
        """Close all pooled clients. Called on application shutdown."""
        ...
```

### GitHubProjectsService (Changed Methods)

Method signatures are **unchanged** for all public methods — callers continue to pass `access_token: str` as the first positional argument. The implementation changes from using `self._client` (httpx) to using `self._client_factory.get_client(access_token)` (githubkit).

#### Constructor Change

```python
# Before
class GitHubProjectsService:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        self._etag_cache: dict[str, tuple[str, dict]] = {}
        self._last_request_time: float = 0.0
        self._min_request_interval: float = 0.5
        self._global_cooldown_until: float = 0.0
        self._cooldown_lock = asyncio.Lock()
        # ... 15+ fields

# After
class GitHubProjectsService:
    def __init__(self, client_factory: GitHubClientFactory):
        self._client_factory = client_factory
        self._cycle_cache: dict[str, object] = {}           # preserved
        self._inflight_graphql: BoundedDict[...] = ...      # preserved
        # ... 6 fields (metrics counters)
```

#### Internal GraphQL Method Change

```python
# Before: 80+ LOC with ETag cache, hash key, coalescing setup, error parsing
async def _graphql(
    self,
    access_token: str,
    query: str,
    variables: dict,
    extra_headers: dict | None = None,
    graphql_features: list[str] | None = None,
) -> dict: ...

# After: ~30 LOC — delegates to SDK, preserves coalescing
async def _graphql(
    self,
    access_token: str,
    query: str,
    variables: dict,
    graphql_features: list[str] | None = None,
) -> dict:
    """Execute GraphQL via SDK. Uses arequest() when custom headers needed."""
    ...
```

#### Rate-Limit Interface (Preserved)

```python
# Interface unchanged — implementation simplified
def get_last_rate_limit(self) -> dict[str, int] | None:
    """Return the most recent rate limit info.
    
    Returns dict with keys: limit, remaining, reset_at, used
    Same shape as before, extracted from last SDK response headers.
    """
    ...
```

### GitHubAuthService (Changed Methods)

```python
# Before: manual httpx POST to github.com/login/oauth/access_token
async def exchange_code_for_token(self, code: str, state: str) -> dict: ...

# After: uses githubkit OAuthWebAuthStrategy
async def exchange_code_for_token(self, code: str, state: str) -> dict: ...
# Return shape unchanged: {"access_token": ..., "refresh_token": ..., "expires_in": ...}

# Before: manual httpx POST with refresh_token
async def refresh_token(self, refresh_token: str) -> dict: ...

# After: uses githubkit OAuthTokenAuthStrategy.async_refresh()
async def refresh_token(self, refresh_token: str) -> dict: ...
# Return shape unchanged
```

### Exception Contract

All callers that currently catch `httpx.HTTPStatusError` must be updated:

```python
# Before
from httpx import HTTPStatusError
try:
    result = await service.some_method(token, ...)
except HTTPStatusError as e:
    if e.response.status_code == 404:
        ...

# After
from githubkit.exception import RequestFailed
try:
    result = await service.some_method(token, ...)
except RequestFailed as e:
    if e.response.status_code == 404:
        ...
```

**Critical**: `e.response.status_code` and `e.response.headers` work identically on both `httpx.Response` and `githubkit.Response`. No logic changes required beyond the import and exception class name.

## Backward Compatibility

| Aspect | Compatibility |
|--------|--------------|
| Public HTTP API (FastAPI routes) | 100% — no changes |
| Frontend integration | 100% — no changes |
| Service method signatures | 100% — all public methods keep same `(self, access_token, ...)` signature |
| Service return types | 100% — all methods return same domain objects |
| Rate-limit info interface | 100% — `get_last_rate_limit()` returns same `dict[str, int]` shape |
| Exception types | **BREAKING** (internal only) — catch sites must update import + class name |
| Constructor signature | **BREAKING** (internal only) — requires `client_factory` parameter |
