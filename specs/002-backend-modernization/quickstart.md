# Quickstart: Backend Modernization & Improvement

**Feature**: 002-backend-modernization | **Date**: 2026-03-15

## Overview

This feature modernizes the Solune FastAPI backend across 5 phases: async safety (TaskGroup, TaskRegistry, timeouts, WebSocket resilience), data integrity (single source of truth, transactions, race condition prevention), security hardening (CSRF, indexes, scoped cache keys, compound rate-limit keys), performance optimization (filtered queries, pagination, reduced TTL, safe eviction), and modern Python patterns (enums, protocols, TypedDict, consistent error handling).

## Prerequisites

- Python 3.12+ (3.13 recommended per project target)
- Docker & Docker Compose (for integration testing)
- The Solune backend source at `solune/backend/`
- Development dependencies installed: `cd solune/backend && pip install -e ".[dev]"`

## Quick Verification

### Phase 1: Async Safety

#### 1. Verify TaskGroup Shutdown Behavior

```bash
cd solune/backend

# Start the backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 3

# Send SIGTERM and watch logs
kill -TERM $BACKEND_PID
wait $BACKEND_PID 2>/dev/null

# Expected in logs:
#   - "Session cleanup task cancelled" (cleanup loop)
#   - "Polling watchdog task cancelled" (watchdog loop)
#   - NO "task was destroyed but it is pending" warnings
```

#### 2. Verify TaskRegistry Drain

```bash
cd solune/backend

# Run unit tests for TaskRegistry
python -m pytest tests/test_task_registry.py -v

# Expected: All tests pass
# Key test: drain() completes or cancels all tracked tasks within timeout
```

#### 3. Verify RUF006 Compliance

```bash
cd solune/backend

# After TaskRegistry adoption and RUF006 suppression removal:
python -m ruff check --select=ASYNC,RUF006 src/

# Expected: Zero violations
```

#### 4. Verify External API Timeouts

```bash
cd solune/backend

# Run timeout-specific tests
python -m pytest tests/ -k "timeout" -v

# Expected: GraphQL calls that exceed 30s raise TimeoutError/AppException
```

### Phase 2: Data Integrity

#### 5. Verify Database as Single Source of Truth

```bash
cd solune/backend

# Start backend, send a chat message, force-restart, verify message persists
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 3

# Send a test message (adjust session/endpoint as needed)
curl -X POST http://localhost:8000/api/v1/chat/test-session/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "test persistence"}'

# Kill and restart
kill -TERM $BACKEND_PID
wait $BACKEND_PID 2>/dev/null
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 3

# Retrieve messages — should include the test message
curl http://localhost:8000/api/v1/chat/test-session/messages
# Expected: Response includes "test persistence" message

kill -TERM $BACKEND_PID
```

#### 6. Verify Admin Race Condition Fix

```bash
cd solune/backend

# Run concurrent admin promotion test
python -m pytest tests/test_admin_race.py -v

# Expected: Exactly 1 of 10 concurrent requests succeeds; remaining get 403
```

### Phase 3: Security

#### 7. Verify CSRF Protection

```bash
# Attempt a state-changing request without CSRF token
curl -X POST http://localhost:8000/api/v1/chat/test/messages \
  -H "Content-Type: application/json" \
  -H "Cookie: session=valid-session-id" \
  -d '{"content": "no csrf"}'
# Expected: 403 Forbidden (missing CSRF token)

# With valid CSRF token
curl -X POST http://localhost:8000/api/v1/chat/test/messages \
  -H "Content-Type: application/json" \
  -H "Cookie: session=valid-session-id; csrf_token=abc123" \
  -H "X-CSRF-Token: abc123" \
  -d '{"content": "with csrf"}'
# Expected: 200 OK (or appropriate success response)
```

#### 8. Verify Database Indexes

```bash
cd solune/backend

# Check index usage on key queries
python -c "
import asyncio, aiosqlite

async def check():
    async with aiosqlite.connect('/var/lib/solune/data/settings.db') as db:
        cursor = await db.execute(
            'EXPLAIN QUERY PLAN SELECT * FROM global_settings WHERE admin_github_user_id = 12345'
        )
        rows = await cursor.fetchall()
        for row in rows:
            print(row)

asyncio.run(check())
"
# Expected: Plan shows 'USING INDEX idx_global_settings_admin'
```

#### 9. Verify Cache Key Scoping

```bash
cd solune/backend

# Unit test: different projects with same issue number get different cache keys
python -c "
from src.constants import cache_key_issue_pr
key1 = cache_key_issue_pr('PVT_project_a', 42, 101)
key2 = cache_key_issue_pr('PVT_project_b', 42, 101)
assert key1 != key2, f'Cache keys should differ: {key1} vs {key2}'
print(f'Project A: {key1}')
print(f'Project B: {key2}')
print('✅ Cache keys are correctly scoped by project')
"
```

### Phase 4: Performance

#### 10. Verify Pagination

```bash
# Request paginated chat messages
curl "http://localhost:8000/api/v1/chat/test-session/messages?limit=5&offset=0"
# Expected: Response contains exactly 5 items (if ≥5 exist)

curl "http://localhost:8000/api/v1/chat/test-session/messages?limit=5&offset=5"
# Expected: Response contains next 5 items (page 2)
```

#### 11. Verify Metadata Cache TTL

```bash
cd solune/backend

# Check cache configuration
python -c "
from src.config import get_settings
settings = get_settings()
print(f'Metadata cache TTL: {settings.cache_ttl_metadata_seconds}s')
# Expected: 300 (5 minutes)
"
```

### Phase 5: Modern Patterns

#### 12. Verify Enum Usage

```bash
cd solune/backend

# Type check modernized modules
python -m ruff check src/services/cleanup_service.py --select=E,W,F
# Expected: No errors

# Verify enum values
python -c "
from src.services.cleanup_service import ItemType, LinkMethod
print(f'Item types: {list(ItemType)}')
print(f'Link methods: {list(LinkMethod)}')
# Expected: enum members matching original string constants
"
```

#### 13. Verify Error Handling Consistency

```bash
cd solune/backend

# Lint for undecorated service methods
python -m ruff check src/ --select=E,W,F,B
# Expected: No new violations

# Run full test suite
python -m pytest tests/ -v
# Expected: All tests pass
```

## Running Tests

```bash
# Backend unit tests (all phases)
cd solune/backend && python -m pytest tests/ -v

# Backend lint (including RUF006 after Phase 1.2)
cd solune/backend && python -m ruff check src/

# Specific phase tests
cd solune/backend && python -m pytest tests/test_task_registry.py -v    # Phase 1
cd solune/backend && python -m pytest tests/test_admin_race.py -v       # Phase 2
cd solune/backend && python -m pytest tests/test_pagination.py -v       # Phase 4
```

## Key Files Reference

| Phase | Files |
|-------|-------|
| 1.1 TaskGroup | `solune/backend/src/main.py` |
| 1.2 TaskRegistry | `solune/backend/src/services/task_registry.py` (NEW), `pyproject.toml` |
| 1.3 Timeouts | `solune/backend/src/services/github_projects/service.py` |
| 1.4 WebSocket Fix | `solune/backend/src/services/signal_bridge.py` |
| 2.1 Chat Persistence | `solune/backend/src/api/chat.py`, `solune/backend/src/services/chat_store.py` |
| 2.2 Silent Failures | `solune/backend/src/api/chat.py` |
| 2.3 Transactions | `solune/backend/src/services/chat_store.py` |
| 2.4 Admin Race | `solune/backend/src/dependencies.py` |
| 3.1 CSRF | New middleware file |
| 3.2 Indexes | `solune/backend/src/migrations/` (new migration) |
| 3.3 Cache Keys | `solune/backend/src/constants.py` |
| 3.4 Rate Limiting | `solune/backend/src/middleware/rate_limit.py` |
| 4.1 Polling Query | `solune/backend/src/main.py` |
| 4.2 Pagination | `solune/backend/src/api/chat.py`, task endpoints |
| 4.3 Cache TTL | `solune/backend/src/config.py`, cache callers |
| 4.4 BoundedDict | `solune/backend/src/utils.py` |
| 5.1 Enums | `solune/backend/src/services/cleanup_service.py` |
| 5.2 Protocols | `solune/backend/src/protocols.py` (NEW) |
| 5.3 TypedDict | Various service files |
| 5.4 Error Handling | Service layer files |
| 5.5 Thread Offload | `solune/backend/src/services/cleanup_service.py` |
| 5.6 Backoff Reset | `solune/backend/src/main.py` |
