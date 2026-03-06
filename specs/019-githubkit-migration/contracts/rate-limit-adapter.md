# Contract: Rate Limit Visibility Adapter

**Feature**: `019-githubkit-migration`
**Type**: Internal Python API
**Consumers**: `copilot_polling/polling_loop.py`
**Provider**: `GitHubClientFactory` (via `RateLimitState`)

---

## Interface Definition

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitState:
    """Immutable snapshot of GitHub API rate limit status.
    
    Replaces the dict[str, int] returned by the previous
    get_last_rate_limit() method. Provides the same data
    with type safety and immutability.
    
    Attributes:
        limit: Maximum requests allowed per rate limit window.
        remaining: Requests remaining in the current window.
        reset_at: Unix timestamp when the window resets.
        used: Requests consumed (computed as limit - remaining).
        resource: Rate limit resource category (default: "core").
    """
    limit: int
    remaining: int
    reset_at: int
    used: int
    resource: str = "core"
```

## Migration Guide

### Before (current implementation)

```python
# In copilot_polling/polling_loop.py
rl = _cp.github_projects_service.get_last_rate_limit()
# rl is dict[str, int] | None with keys: "limit", "remaining", "reset_at", "used"

if rl:
    remaining = rl["remaining"]
    reset_at = rl["reset_at"]

_cp.github_projects_service.clear_last_rate_limit()
```

### After (githubkit migration)

```python
# In copilot_polling/polling_loop.py
rl = _cp.client_factory.get_rate_limit()
# rl is RateLimitState | None with attributes: limit, remaining, reset_at, used

if rl:
    remaining = rl.remaining
    reset_at = rl.reset_at

_cp.client_factory.clear_rate_limit()
```

## Field Mapping

| Old Key (dict) | New Attribute (dataclass) | Type | Notes |
|-----------------|--------------------------|------|-------|
| `rl["limit"]` | `rl.limit` | `int` | Identical semantics |
| `rl["remaining"]` | `rl.remaining` | `int` | Identical semantics |
| `rl["reset_at"]` | `rl.reset_at` | `int` | Unix timestamp, identical |
| `rl["used"]` | `rl.used` | `int` | `limit - remaining`, identical |

## Implementation Strategy

Rate limit headers are captured from httpx responses via one of two approaches:

### Approach A: httpx Event Hook (Recommended)

```python
def _capture_rate_limit(response: httpx.Response) -> None:
    """Event hook to capture rate limit headers from every response."""
    limit = response.headers.get("X-RateLimit-Limit")
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_at = response.headers.get("X-RateLimit-Reset")
    if limit and remaining and reset_at:
        factory._rate_limit = RateLimitState(
            limit=int(limit),
            remaining=int(remaining),
            reset_at=int(reset_at),
            used=int(limit) - int(remaining),
        )
```

### Approach B: Post-Response Extraction

Extract rate limit data after each `github.rest.*` or `github.graphql()` call from the response object. More explicit but requires changes at every call site.

**Decision**: Approach A is preferred — single integration point, no per-call-site changes.

## Invariants

1. **Immutability**: `RateLimitState` is frozen — consumers cannot accidentally modify shared state
2. **Freshness**: Returns data from the most recent API response across all clients in the pool
3. **Nullability**: Returns `None` before any API call has been made (consumers must handle this)
4. **Backward compatibility**: The data exposed (limit, remaining, reset_at, used) is identical to the previous dict format — only the access pattern changes (attribute vs dict key)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| API response lacks rate limit headers | `_rate_limit` unchanged (stale data or None) |
| Invalid header values (non-numeric) | Silently ignored (try/except ValueError) |
| Multiple concurrent responses | Last write wins (acceptable — race is benign, data is approximate) |
| `clear_rate_limit()` during active request | Next response will repopulate |
