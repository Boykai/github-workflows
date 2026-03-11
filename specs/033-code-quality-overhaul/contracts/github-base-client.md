# Contract: GitHubBaseClient

**Branch**: `033-code-quality-overhaul` | **Phase**: 4.3

## Purpose

Shared HTTP/caching/rate-limit infrastructure extracted from `GitHubProjectsService`. All domain services inherit from this class.

## Interface

```python
class GitHubBaseClient:
    """Base client providing GitHub API infrastructure.

    Handles authentication, rate limiting, ETag caching, request coalescing,
    and retry logic. Domain services inherit this and add domain methods.
    """

    def __init__(self, token: str, rate_limit: RateLimitManager | None = None) -> None:
        """Initialize with GitHub token and optional rate limiter."""

    async def _graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query against GitHub API.

        Handles rate limiting, retries, and error extraction.
        Raises: GitHubAPIError on non-retryable failures.
        """

    async def _rest(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute a REST API call against GitHub API.

        Handles ETag caching, rate limiting, and retries.
        """

    async def _request_with_retry(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        max_retries: int = 3,
    ) -> T:
        """Retry a request function with exponential backoff on rate limits."""
```

## Invariants

- All HTTP requests go through `_request_with_retry`
- Rate limit headers are extracted from every response
- ETag cache is checked before every GET request
- Concurrent identical requests are coalesced (only one in-flight)
- Token is never logged or exposed in error messages
