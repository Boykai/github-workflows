# Security & Performance Contracts

**Feature**: 002-backend-modernization | **Date**: 2026-03-15

## Contract: CSRF Protection

All state-changing HTTP methods (POST, PUT, DELETE) MUST be protected against cross-site request forgery.

### Token Lifecycle

```
[Session Created (OAuth callback)]
  → Generate CSRF token: secrets.token_hex(32)
  → Set cookie: csrf_token={token}; SameSite=Lax; Secure; Path=/
    (NOT HttpOnly — frontend JS must read it)
  → Set session cookie (existing flow, unchanged)

[State-Changing Request (POST/PUT/DELETE)]
  → Read csrf_token cookie value
  → Read X-CSRF-Token header value
  → Compare:
    → Match → Proceed to endpoint handler
    → Mismatch or missing → 403 Forbidden

[Exempt Requests]
  → GET, HEAD, OPTIONS → No CSRF validation
  → POST /api/v1/webhooks/* → HMAC-verified, no CSRF
  → GET /api/v1/auth/github/callback → OAuth flow, no session yet
```

### Error Response

```json
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "CSRF token validation failed"
}
```

**Constraints**:
- CSRF token MUST be cryptographically random (≥32 bytes / 64 hex chars)
- CSRF cookie MUST be `SameSite=Lax` (allows navigation GETs), `Secure` (HTTPS only in production), NOT `HttpOnly`
- The `X-CSRF-Token` header MUST match the `csrf_token` cookie exactly (constant-time comparison)
- Webhook endpoints MUST be exempted (they use HMAC-SHA256 verification instead)
- CSRF validation MUST happen before any endpoint logic executes

## Contract: Database Indexes

Critical query columns MUST have indexes to ensure bounded query performance.

### Required Indexes

```sql
-- Admin lookup (used on every admin-verified request)
CREATE INDEX IF NOT EXISTS idx_global_settings_admin
  ON global_settings(admin_github_user_id);

-- Project session lookup (used on every project-scoped request)
CREATE INDEX IF NOT EXISTS idx_user_sessions_project
  ON user_sessions(selected_project_id);

-- Chat message retrieval (used on every chat page load)
CREATE INDEX IF NOT EXISTS idx_chat_messages_session
  ON chat_messages(session_id);

-- Proposal retrieval
CREATE INDEX IF NOT EXISTS idx_chat_proposals_session
  ON chat_proposals(session_id);
```

### Verification

```sql
-- Each indexed query should show "USING INDEX" in its plan
EXPLAIN QUERY PLAN
  SELECT * FROM global_settings WHERE admin_github_user_id = 12345;
-- Expected: SEARCH ... USING INDEX idx_global_settings_admin

EXPLAIN QUERY PLAN
  SELECT * FROM user_sessions WHERE selected_project_id = 'PVT_abc';
-- Expected: SEARCH ... USING INDEX idx_user_sessions_project
```

**Constraints**:
- All indexes use `IF NOT EXISTS` to be idempotent
- Indexes MUST be created in a versioned migration file
- Index creation MUST NOT lock the database for extended periods (SQLite CREATE INDEX is fast for existing tables)

## Contract: Cache Key Scoping

All project-scoped cache keys MUST include the project identifier to prevent cross-project data leakage.

### Key Format

```
Before: "{issue_number}:{pr_number}"
After:  "{project_id}:{issue_number}:{pr_number}"

Before: "{issue_number}:{agent}:{pr_number}"
After:  "{project_id}:{issue_number}:{agent}:{pr_number}"

Before: "copilot_review_requested:{issue_number}"
After:  "{project_id}:copilot_review_requested:{issue_number}"
```

### Function Signatures

```python
# Before
def cache_key_issue_pr(issue_number: int, pr_number: int) -> str:
    return f"{issue_number}:{pr_number}"

# After
def cache_key_issue_pr(project_id: str, issue_number: int, pr_number: int) -> str:
    return f"{project_id}:{issue_number}:{pr_number}"
```

**Constraints**:
- `project_id` is the GitHub Projects V2 node ID (globally unique, format `PVT_*`)
- All callers of `cache_key_issue_pr()`, `cache_key_agent_output()`, and `cache_key_review_requested()` MUST be updated to pass `project_id`
- Non-project-scoped keys (`get_user_projects_cache_key`, `get_repo_agents_cache_key`) are NOT affected
- Cache invalidation is not required — in-memory cache clears on restart

## Contract: Rate Limiting (Compound Key)

Rate limiting MUST use a compound key that persists across session changes.

### Key Resolution

```
[Request arrives]
  → Middleware resolves rate-limit key:
    → If session cookie present AND session is valid:
      → Resolve github_user_id from session store
      → Key = "user:{github_user_id}"
    → If session cookie absent OR session invalid:
      → Key = "ip:{remote_address}"
  → Store key in request.state.rate_limit_key
  → slowapi key_func reads from request.state.rate_limit_key
```

### Endpoint Limits

| Endpoint Pattern | Limit | Key Type |
|-----------------|-------|----------|
| `POST /api/v1/chat/*/messages` | 10/minute | Per-user (or per-IP) |
| `POST /api/v1/agents/*` | 5/minute | Per-user (or per-IP) |
| `POST /api/v1/workflow/*` | 10/minute | Per-user (or per-IP) |
| `GET /api/v1/auth/github/callback` | 20/minute | Per-IP only |

### Rate Limit Response

```json
HTTP/1.1 429 Too Many Requests
Retry-After: {seconds}
Content-Type: application/json

{
  "detail": "Rate limit exceeded. Try again in {seconds} seconds."
}
```

**Constraints**:
- Clearing session cookies MUST NOT reset rate limits for the same user (SC-008)
- The middleware MUST be non-blocking (async session lookup, not sync)
- Session lookup failures MUST fall back to IP-based limiting (not fail open)
- Rate limit state is in-memory only (no persistence required)

## Contract: Pagination

List endpoints MUST support bounded pagination.

### Query Parameters

| Parameter | Type | Default | Min | Max | Notes |
|-----------|------|---------|-----|-----|-------|
| `limit` | int | 50 | 1 | 200 | Number of items to return |
| `offset` | int | 0 | 0 | — | Number of items to skip |

### Response Format

```json
{
  "items": [...],
  "total": 1234,
  "limit": 50,
  "offset": 0
}
```

### SQL Implementation

```sql
SELECT *, COUNT(*) OVER() as total_count
FROM chat_messages
WHERE session_id = ?
ORDER BY created_at DESC
LIMIT ? OFFSET ?
```

**Constraints**:
- `limit` exceeding 200 MUST be clamped to 200 (not rejected)
- `limit` below 1 MUST be clamped to 1
- `offset` exceeding total results MUST return an empty `items` list with correct `total`
- `total` MUST reflect the unfiltered count for the query (before limit/offset)
- Default sort order is newest-first (`created_at DESC`)

## Contract: Metadata Cache TTL

Frequently changing metadata MUST have a shorter cache TTL than general data.

### TTL Configuration

| Data Type | TTL | Setting |
|-----------|-----|---------|
| Branch list | 300s (5 min) | `CACHE_TTL_METADATA_SECONDS` |
| Label list | 300s (5 min) | `CACHE_TTL_METADATA_SECONDS` |
| Project items | Default | `CACHE_TTL_SECONDS` |
| User projects | Default | `CACHE_TTL_SECONDS` |

**Constraints**:
- `CACHE_TTL_METADATA_SECONDS` defaults to 300 if not set
- The setting MUST be configurable via environment variable
- Branch and label cache entries MUST use the metadata TTL, not the general TTL
- Cache TTL reduction does NOT require cache invalidation (existing entries expire naturally)

## Contract: BoundedDict Task-Aware Eviction

When a `BoundedDict` evicts an entry whose value is a cancellable task, the task MUST be cancelled.

### Eviction Behavior

```python
# Construction with eviction callback
tasks: BoundedDict[str, asyncio.Task] = BoundedDict(
    maxlen=256,
    on_evict=lambda key, task: task.cancel() if not task.done() else None
)

# On capacity overflow:
# 1. Pop oldest entry
# 2. Call on_evict(key, value)
# 3. Insert new entry
```

**Constraints**:
- `on_evict` callback MUST be called before the entry is removed
- `on_evict` is optional — `BoundedDict` without it behaves as before (backward compatible)
- `on_evict` MUST NOT raise exceptions (wrap in try/except internally)
- Task cancellation via `on_evict` MUST log the cancelled task's key at DEBUG level
