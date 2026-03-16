# Data Integrity Contracts

**Feature**: 002-backend-modernization | **Date**: 2026-03-15

## Contract: Chat Persistence (Single Source of Truth)

The database MUST be the authoritative store for all chat data. In-memory structures serve only as a read-through cache.

### Write Path

```
Client sends message/proposal/recommendation
  → Acquire asyncio.Lock for session
  → BEGIN IMMEDIATE transaction in SQLite
  → INSERT/REPLACE into chat table
  → COMMIT
  → Update in-memory cache
  → Release lock
  → Return success to client
```

**Constraints**:
- Writes MUST go to SQLite BEFORE updating the in-memory cache
- If the SQLite write fails, the in-memory cache MUST NOT be updated
- Cache updates MUST be protected by `asyncio.Lock` per session
- The lock is per-session (not global) to minimize contention

### Read Path

```
Client requests message/proposal/recommendation
  → Check in-memory cache (lock-free read)
    → Cache hit: return cached data
    → Cache miss:
      → Query SQLite
      → Populate cache (within asyncio.Lock)
      → Return data
```

**Constraints**:
- Cache reads MAY be lock-free (stale reads are acceptable for display)
- Cache population MUST acquire the lock to prevent concurrent SQLite queries for the same session
- Cache entries MUST NOT have expiration (they're invalidated on write, cleared on session close)

### Failure Handling

```
SQLite write attempt:
  → Success: update cache, return success
  → Transient failure (SQLITE_BUSY, SQLITE_LOCKED, IOError):
    → Retry 1: wait 100ms, retry
    → Retry 2: wait 200ms, retry
    → Retry 3: wait 400ms, retry
    → All retries failed: raise PersistenceError to caller
  → Permanent failure (schema error, constraint violation):
    → Raise immediately (no retry)
```

**Constraints**:
- Transient failures MUST be retried (up to 3 attempts with exponential backoff)
- Permanent failures MUST propagate immediately
- Each retry MUST log the attempt number, error type, and session context
- The caller (endpoint handler) MUST handle `PersistenceError` and return an appropriate HTTP error (500/503)

## Contract: Transaction Boundaries

Multi-step database operations MUST be wrapped in explicit transactions.

### Single-Operation Writes

```python
# For single INSERT/UPDATE/DELETE: no explicit transaction needed
# aiosqlite auto-commits single statements
await db.execute("INSERT INTO chat_messages ...", params)
await db.commit()
```

### Multi-Operation Writes

```python
# For multi-step operations: explicit transaction required
await db.execute("BEGIN IMMEDIATE")
try:
    await db.execute("INSERT INTO chat_messages ...", params1)
    await db.execute("UPDATE chat_state SET ...", params2)
    await db.commit()
except Exception:
    await db.rollback()
    raise
```

**Constraints**:
- `BEGIN IMMEDIATE` MUST be used for write transactions (prevents write starvation)
- Transactions MUST be committed on success
- Transactions MUST be rolled back on any exception
- Nested transactions MUST use savepoints: `SAVEPOINT name` / `RELEASE name` / `ROLLBACK TO name`
- Transaction duration SHOULD be minimized (no external API calls within a transaction)
- If `BEGIN IMMEDIATE` fails with `SQLITE_BUSY`, treat as transient and retry per the persistence retry policy

### Migration Transactions

```python
# Schema migrations use savepoints for rollback capability
await db.execute("SAVEPOINT migration_NNN")
try:
    await db.execute("CREATE INDEX IF NOT EXISTS ...")
    await db.execute("ALTER TABLE ...")
    await db.execute("RELEASE migration_NNN")
except Exception:
    await db.execute("ROLLBACK TO migration_NNN")
    raise
```

## Contract: Admin Auto-Promotion (Race Condition Prevention)

Admin promotion in debug mode MUST be atomic and prevent TOCTOU races.

### Promotion Flow

```
Request arrives with no admin set (admin_github_user_id IS NULL):

[Check ADMIN_GITHUB_USER_ID env var]
  → Env var set:
    → Verify request user matches env var value
    → If match: UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1
    → If no match: raise 403
  → Env var not set + production mode:
    → Raise 500 ("ADMIN_GITHUB_USER_ID must be set in production mode")
  → Env var not set + debug mode:
    → Atomic conditional UPDATE:
      UPDATE global_settings
      SET admin_github_user_id = ?
      WHERE id = 1 AND admin_github_user_id IS NULL
    → Check rowcount:
      → rowcount > 0: User promoted successfully
      → rowcount == 0: Another user won the race
        → Re-read admin_github_user_id
        → If current user matches new admin: return session (idempotent)
        → If current user differs: raise 403
```

**Constraints**:
- The `WHERE admin_github_user_id IS NULL` clause MUST be in the UPDATE statement (not a separate SELECT + UPDATE)
- `cursor.rowcount` MUST be checked to determine if the update succeeded
- If `rowcount == 0` (race lost), the code MUST re-read the admin and compare
- The promotion MUST be committed atomically (single UPDATE + COMMIT)
- 10 concurrent promotion requests MUST result in exactly 1 successful promotion (SC-006)

### Verification Test

```python
async def test_concurrent_admin_promotion():
    """10 concurrent requests, exactly 1 succeeds."""
    results = await asyncio.gather(
        *[attempt_admin_promotion(user_id=i) for i in range(10)],
        return_exceptions=True
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 1
```
