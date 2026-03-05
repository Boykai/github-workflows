# Contract: Unified Retry Strategy

**Module**: `backend/src/services/github_projects/service.py`
**Type**: Enhancement to existing `_request_with_retry()` method

---

## Purpose

Consolidate all retry logic (primary rate limits, secondary rate limits, transient server errors) into a single method with consistent behavior. Remove any inline retry logic in `_graphql()` that duplicates this.

## Interface

```python
async def _request_with_retry(
    self,
    method: str,
    url: str,
    headers: dict[str, str],
    json: dict | None = None,
    *,
    idempotent: bool = True,
) -> httpx.Response:
    """Execute an HTTP request with unified retry logic.
    
    Args:
        method: HTTP method ("GET", "POST", etc.)
        url: Request URL.
        headers: Request headers.
        json: Optional JSON body.
        idempotent: If False, only retries on rate limits (not server errors).
    
    Returns:
        httpx.Response on success (2xx or non-retryable status).
    
    Raises:
        httpx.HTTPStatusError: After MAX_RETRIES exhausted.
        httpx.RequestError: On non-retryable network errors.
    """
    ...
```

## Retry Decision Matrix

| Status Code | Condition | Action | Backoff |
|-------------|-----------|--------|---------|
| 429 | Too Many Requests | Retry | `Retry-After` header or exponential |
| 403 | `X-RateLimit-Remaining == 0` | Retry | Sleep until `X-RateLimit-Reset` + jitter |
| 403 | Secondary rate limit (body contains "secondary rate limit") | Retry | Exponential backoff |
| 502 | Bad Gateway | Retry (if idempotent) | Exponential backoff |
| 503 | Service Unavailable | Retry (if idempotent) | Exponential backoff |
| 401 | Unauthorized | **Fail fast** | — |
| 404 | Not Found | **Fail fast** | — |
| 422 | Unprocessable | **Fail fast** | — |
| Other 4xx | Client error | **Fail fast** | — |

## Constants

```python
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1
MAX_BACKOFF_SECONDS = 30
```

## Behavioral Contract

- **Exponential backoff**: `delay = min(INITIAL * 2^attempt, MAX_BACKOFF)` with optional jitter
- **Rate limit headers**: Respects `X-RateLimit-Reset` and `Retry-After` headers when present
- **Logging**: Logs each retry attempt at WARNING level with attempt number, status, and delay
- **Context propagation**: Uses `contextvars` for per-request rate limit isolation
- **ETag caching**: The `_graphql()` method's ETag/304 handling remains in `_graphql()` (not part of retry logic — it's a caching optimization)

## Migration

- `_graphql()` inline retry loops are removed; all retries go through `_request_with_retry()`
- All consumers benefit from consistent secondary rate limit detection
