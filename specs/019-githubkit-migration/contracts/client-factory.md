# Contract: GitHubClientFactory

**Feature**: `019-githubkit-migration`
**Type**: Internal Python API
**Consumers**: `GitHubProjectsService`, `GitHubAuthService`, `dependencies.py`

---

## Interface Definition

```python
from githubkit import GitHub
from src.models.rate_limit import RateLimitState


class GitHubClientFactory:
    """Factory for creating and pooling authenticated GitHub SDK clients.
    
    Manages a bounded pool of GitHub client instances keyed by token hash.
    Provides rate limit visibility to consumers without exposing SDK internals.
    """

    def __init__(self, max_pool_size: int = 50) -> None:
        """Initialize the factory with a bounded client pool.
        
        Args:
            max_pool_size: Maximum number of pooled clients. Oldest evicted
                when capacity is reached. Default: 50.
        """
        ...

    def get_client(self, token: str) -> GitHub:
        """Get or create a pooled GitHub client for the given access token.
        
        If a client already exists for this token (matched by SHA-256 hash prefix),
        it is returned from the pool. Otherwise, a new client is created with:
        - TokenAuthStrategy for authentication
        - Auto-retry enabled for rate limit and server errors
        - HTTP caching enabled (ETag/If-None-Match)
        - Local request throttling enabled
        
        Args:
            token: GitHub OAuth access token or PAT.
        
        Returns:
            Authenticated async GitHub client instance.
        
        Thread Safety:
            Safe for single-threaded asyncio. No await points between
            pool check and client creation.
        """
        ...

    def get_rate_limit(self) -> RateLimitState | None:
        """Return the most recent rate limit state from any API response.
        
        Returns None if no API calls have been made yet.
        
        Returns:
            Frozen RateLimitState dataclass or None.
        """
        ...

    def clear_rate_limit(self) -> None:
        """Clear the cached rate limit state.
        
        Called by polling loop when stale rate limit data is detected
        (e.g., reset window has passed but remaining count is still zero).
        """
        ...

    async def close(self) -> None:
        """Close all pooled clients and release resources.
        
        Called during application shutdown via FastAPI lifespan.
        After close(), get_client() should not be called.
        """
        ...
```

## Usage Examples

### Service Initialization (dependencies.py)

```python
from src.services.github_projects.client_factory import GitHubClientFactory

# In FastAPI lifespan
async def lifespan(app: FastAPI):
    app.state.client_factory = GitHubClientFactory(max_pool_size=50)
    app.state.github_service = GitHubProjectsService(app.state.client_factory)
    yield
    await app.state.client_factory.close()
```

### Service Method Usage (service.py)

```python
class GitHubProjectsService:
    def __init__(self, client_factory: GitHubClientFactory) -> None:
        self._client_factory = client_factory

    async def create_issue(self, access_token: str, owner: str, repo: str, ...) -> dict:
        github = self._client_factory.get_client(access_token)
        response = await github.rest.issues.async_create(
            owner=owner, repo=repo, title=title, body=body, labels=labels
        )
        return response.parsed_data.model_dump()
```

### Polling Loop Usage (copilot_polling/polling_loop.py)

```python
# Before:
rl = _cp.github_projects_service.get_last_rate_limit()

# After:
rl = _cp.client_factory.get_rate_limit()
if rl is not None:
    remaining = rl.remaining
    reset_at = rl.reset_at
```

## Invariants

1. **Pool size**: `len(self._pool) <= self._max_pool_size` at all times
2. **Token privacy**: Plain-text tokens are never stored as pool keys
3. **Client reuse**: Same token always returns the same client (until evicted)
4. **Shutdown safety**: `close()` is idempotent — safe to call multiple times
5. **Rate limit freshness**: `get_rate_limit()` returns data from the most recent API response, not a historical aggregate

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Invalid token | Client is created (validation happens on first API call, not at pool time) |
| Pool eviction during active request | Evicted client's in-flight requests complete normally (httpx handles this) |
| `close()` called with active requests | In-flight requests may fail with connection errors |
| `get_client()` after `close()` | Creates a new client (no explicit guard — caller's responsibility) |
