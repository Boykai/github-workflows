# Contract: Rate Limiting

**Feature**: 001-security-review | **Date**: 2026-03-11

## Overview

Defines the rate limiting contract for expensive and security-sensitive endpoints using the `slowapi` library (already in `pyproject.toml`). Rate limits distinguish between authenticated user abuse and anonymous callback abuse.

## Key Function

```python
def get_rate_limit_key(request: Request) -> str:
    """
    Authenticated requests: keyed by truncated session token ("user:{token[:16]}")
    Unauthenticated requests: keyed by client IP address
    """
```

**Rationale**: Per-user limits prevent authenticated abuse without penalizing other users on the same NAT/VPN. Per-IP limits are used only for unauthenticated endpoints where no user identity exists.

## Rate Limit Definitions

| Endpoint Category | File | Limit | Key | FR Reference |
|-------------------|------|-------|-----|-------------|
| Chat messages (send) | `chat.py` | 30/minute | Per-user | FR-022 |
| Agent invocation | `agents.py` | 10/minute | Per-user | FR-022 |
| Workflow triggers | `workflow.py` | 10/minute | Per-user | FR-022 |
| OAuth callback | `auth.py` | 5/minute | Per-IP | FR-022 |

**Note**: Rate limit values should be configurable via environment variables for deployment flexibility. The values above are recommended defaults.

## Response Contract

### Rate Limit Exceeded (429)

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

Response headers:

- `Retry-After: 60` (seconds until limit resets)
- `X-RateLimit-Limit: 30` (configured limit)
- `X-RateLimit-Remaining: 0` (remaining requests)
- `X-RateLimit-Reset: 1709300000` (Unix timestamp of reset)

### Normal Response

Rate limit headers are included on all responses from limited endpoints:

- `X-RateLimit-Limit: 30`
- `X-RateLimit-Remaining: 28`
- `X-RateLimit-Reset: 1709300000`

## Integration Pattern

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# In main.py
limiter = Limiter(key_func=get_rate_limit_key)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# In endpoint files
@router.post("/chat/{project_id}/send")
@limiter.limit("30/minute")
async def send_message(request: Request, ...):
    ...
```

## Test Contract

| # | Input | Expected |
|---|-------|----------|
| 1 | User sends 30 chat messages in 1 minute | First 30 succeed, 31st returns 429 |
| 2 | User invokes 10 agents in 1 minute | First 10 succeed, 11th returns 429 |
| 3 | Same IP, different authenticated users | Each user gets independent limit |
| 4 | OAuth callback from same IP, 5 requests | First 5 succeed, 6th returns 429 |
| 5 | After rate limit window resets | Requests succeed again |
| 6 | 429 response includes Retry-After header | Header present with correct value |

## Storage

In-memory storage backend (default `slowapi` behavior). Sufficient for single-instance deployment. If horizontal scaling is added later, switch to Redis backend.
