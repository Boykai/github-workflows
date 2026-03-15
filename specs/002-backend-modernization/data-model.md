# Data Model: Backend Modernization & Improvement

**Feature**: 002-backend-modernization | **Date**: 2026-03-15

## Overview

This modernization introduces one new entity (TaskRegistry) and modifies several existing entities to improve lifecycle management, data integrity, and security. The data model documents new entities, modified fields, validation rules, and state transitions.

## New Entities

### TaskRegistry

A centralized singleton that tracks all fire-and-forget background tasks created via `asyncio.create_task()`.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| _tasks | `dict[str, asyncio.Task]` | Task name → Task object | Keys are auto-generated or caller-provided names |
| _pending_count | `int` | `>= 0` | Count of non-done tasks (computed property) |

**Lifecycle states** per tracked task:

```
[Created] → create_task(coro) → [Pending/Running] → coro completes → [Completed]
[Created] → create_task(coro) → [Pending/Running] → coro raises → [Failed]
[Created] → create_task(coro) → [Pending/Running] → cancel() or drain() → [Cancelled]
```

**Operations**:

| Method | Input | Output | Side Effects |
|--------|-------|--------|-------------|
| `create_task(coro, name)` | Coroutine + optional name | `asyncio.Task` | Registers task, adds done-callback for cleanup |
| `drain(timeout)` | Timeout in seconds | `list[asyncio.Task]` (undrained) | Awaits all pending tasks; returns tasks exceeding timeout |
| `cancel_all()` | — | `None` | Cancels all non-done tasks |
| `pending_count` | — | `int` | Returns count of non-done tasks |

**Invariants**:
- A task is removed from the registry automatically on completion (via done-callback)
- `drain()` cancels tasks that exceed the timeout and returns them for caller inspection
- `create_task()` is safe to call during `drain()` — new tasks are tracked but not awaited by the in-progress drain

### CSRFToken (Request-scoped, ephemeral)

Tracks the CSRF token lifecycle per session. Not persisted to database — lives in cookies.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| token | `str` | Random hex, ≥32 bytes | Generated on session creation |
| cookie_name | `str` | `"csrf_token"` | Non-HttpOnly, SameSite=Lax, Secure |

**Validation flow**:

```
[Session Created] → Set csrf_token cookie (non-HttpOnly)
[State-Changing Request] → Read X-CSRF-Token header → Compare with cookie value
  → Match → Proceed
  → Mismatch or missing → 403 Forbidden
```

## Modified Entities

### ChatMessage / Proposal / Recommendation (Persistence Model)

**Current**: In-memory dicts (`_messages`, `_proposals`, `_recommendations`) are the primary store; SQLite is fire-and-forget secondary.

**After**: SQLite is the single source of truth. In-memory dicts become a read-through cache protected by `asyncio.Lock`.

| Aspect | Before | After |
|--------|--------|-------|
| Primary store | In-memory dict | SQLite (via chat_store.py) |
| Cache | SQLite (fire-and-forget) | In-memory dict (read-through) |
| Write path | Dict first → async persist (may fail silently) | SQLite first → update cache on success |
| Read path | Dict (always hit) | Cache → SQLite on miss |
| Failure handling | `logger.warning()` only | Retry (3x) + propagate persistent failures |
| Concurrency | No locking | `asyncio.Lock` per session for cache updates |

**State transitions for persistence**:

```
[Write Request] → SQLite INSERT/REPLACE (within transaction)
  → Success → Update in-memory cache → Return success
  → Transient failure → Retry (up to 3x, exponential backoff)
    → All retries failed → Raise exception to caller
```

### GlobalSettings (Admin Promotion)

**Current**: TOCTOU-prone admin auto-promotion in debug mode.

**After**: Atomic conditional UPDATE verified by rowcount.

| Field | Type | Change | Notes |
|-------|------|--------|-------|
| admin_github_user_id | `INTEGER` | No schema change | Promotion logic hardened |

**Auto-promotion state machine** (debug mode only):

```
[admin_github_user_id IS NULL]
  → Concurrent request A: UPDATE ... WHERE admin_github_user_id IS NULL
    → rowcount = 1 → User A promoted → Return session
    → rowcount = 0 → Another user won → Re-read admin → Return 403
  → Concurrent request B: UPDATE ... WHERE admin_github_user_id IS NULL
    → rowcount = 0 (A already committed) → Re-read admin → Return 403
```

### CacheEntry (Project-Scoped Keys)

**Current**: Cache keys like `"{issue_number}:{pr_number}"` have no project scope.

**After**: Cache keys prefixed with `{project_id}:`.

| Key Function | Before | After |
|-------------|--------|-------|
| `cache_key_issue_pr(issue, pr)` | `"42:101"` | `"PVT_abc:42:101"` |
| `cache_key_agent_output(issue, agent, pr)` | `"42:bot:101"` | `"PVT_abc:42:bot:101"` |
| `cache_key_review_requested(issue)` | `"copilot_review_requested:42"` | `"PVT_abc:copilot_review_requested:42"` |

**Signature changes**:

```python
# Before
def cache_key_issue_pr(issue_number: int, pr_number: int) -> str

# After
def cache_key_issue_pr(project_id: str, issue_number: int, pr_number: int) -> str
```

### RateLimitRecord (Compound Key)

**Current**: Per-session cookie key (`"user:{session_id}"`), IP fallback.

**After**: Per-user key (`"user:{github_user_id}"`), IP fallback.

| Aspect | Before | After |
|--------|--------|-------|
| Authenticated key | `"user:{session_id}"` | `"user:{github_user_id}"` |
| Unauthenticated key | `"{ip_address}"` | `"ip:{ip_address}"` |
| Bypass via cookie clear | Yes (new session = new key) | No (same user ID = same key) |

### BoundedDict (Task-Aware Eviction)

**Current**: FIFO eviction via `popitem(last=False)` — evicted value silently dropped.

**After**: Optional `on_evict` callback invoked before entry removal.

| Field | Type | Change | Notes |
|-------|------|--------|-------|
| `_on_evict` | `Callable[[K, V], None] \| None` | NEW | Called with (key, value) before eviction |

**Eviction flow**:

```
[__setitem__ with full capacity]
  → Pop oldest entry (key, value)
  → If on_evict callback set → on_evict(key, value)
    → For task instances: callback calls task.cancel()
  → Insert new entry
```

## New Database Objects

### Migration: Add Performance Indexes

```sql
-- Migration: NNN_add_performance_indexes.sql
CREATE INDEX IF NOT EXISTS idx_global_settings_admin 
  ON global_settings(admin_github_user_id);

CREATE INDEX IF NOT EXISTS idx_user_sessions_project 
  ON user_sessions(selected_project_id);

-- Only if status column exists on chat tables:
CREATE INDEX IF NOT EXISTS idx_chat_messages_session 
  ON chat_messages(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_proposals_session 
  ON chat_proposals(session_id);
```

## Relationships

```
TaskRegistry (singleton)
  └── 1:N → asyncio.Task (tracked background tasks)
       ├── Fire-and-forget tasks (Signal delivery, AI processing, model refresh)
       └── Lifecycle tasks (cleanup loop, watchdog, polling) — managed by TaskGroup

ChatMessage / Proposal / Recommendation
  ├── Primary store: SQLite (chat_store.py)
  ├── Read cache: In-memory dict (asyncio.Lock protected)
  └── Write path: SQLite → cache (atomic via transaction)

CacheEntry
  ├── Scoped by: project_id (prevents cross-project collision)
  ├── TTL: 300s for metadata (branches, labels), default for others
  └── Container: InMemoryCache (BoundedDict with on_evict for tasks)

RateLimitRecord
  ├── Key: github_user_id (authenticated) or IP (fallback)
  └── Storage: In-memory via slowapi (no persistence)
```

## Validation Rules

### TaskRegistry

1. `create_task()` MUST only be called with a valid coroutine
2. `drain()` MUST await all tasks for up to `timeout` seconds, then cancel remaining
3. `drain()` MUST be called during application shutdown before closing database connections
4. Tasks that raise exceptions MUST be logged but not re-raised (fire-and-forget semantics)

### Chat Persistence (Post-Refactor)

1. All writes MUST go through SQLite first — in-memory cache is NEVER the primary store
2. Failed writes MUST be retried up to 3 times with exponential backoff (100ms, 200ms, 400ms)
3. After 3 failed retries, the exception MUST propagate to the caller
4. Cache updates MUST be protected by `asyncio.Lock` per session to prevent concurrent modification
5. Cache misses MUST load from SQLite and populate the cache

### Transaction Boundaries

1. Multi-step write operations MUST use `BEGIN IMMEDIATE` transactions
2. Transactions MUST be committed on success, rolled back on any exception
3. Read-only operations do NOT require explicit transactions (WAL mode provides consistent reads)
4. Nested transactions MUST use savepoints (`SAVEPOINT` / `RELEASE` / `ROLLBACK TO`)

### Cache Key Scoping

1. All project-scoped cache keys MUST include `project_id` as the first segment
2. `project_id` is the GitHub Projects V2 node ID (globally unique string starting with `PVT_`)
3. Non-project-scoped keys (user projects list, repo agents) do NOT require project prefix

### Rate Limiting

1. Authenticated requests MUST be keyed by `github_user_id` (not session cookie)
2. Unauthenticated requests MUST be keyed by client IP address
3. Key resolution MUST happen in middleware before endpoint execution
4. Key resolution failure (e.g., expired session) MUST fall back to IP-based limiting

### CSRF Protection

1. CSRF token MUST be generated on session creation (cryptographically random, ≥32 bytes)
2. CSRF cookie MUST be non-HttpOnly (frontend JS needs to read it)
3. POST, PUT, DELETE requests MUST include `X-CSRF-Token` header matching cookie value
4. GET, HEAD, OPTIONS requests are exempt from CSRF validation
5. Webhook endpoints (HMAC-verified) are exempt from CSRF validation
6. CSRF validation failure MUST return 403 Forbidden with a clear error message

## Enum Definitions (Phase 5)

### ItemType (StrEnum)

```python
class ItemType(StrEnum):
    BRANCH = "branch"
    PR = "pr"
    ORPHAN = "orphan"
```

### LinkMethod (StrEnum)

```python
class LinkMethod(StrEnum):
    BRANCH_NAME = "branch_name"
    PR_BODY = "pr_body"
    OWNERSHIP = "ownership"
```

### PollingStatus (TypedDict)

```python
class PollingStatus(TypedDict):
    is_running: bool
    errors_count: int
    last_error: str | None
```
