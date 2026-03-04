# Review Contract: Runtime Error Audit (P2)

**Category**: Runtime Errors
**Priority**: P2
**Scope**: All files in `backend/src/` and `frontend/src/`

## Checklist

### Exception Handling
- [ ] All `try/except` blocks catch specific exceptions (not bare `except:`)
- [ ] All caught exceptions are either handled, re-raised, or logged (no silent swallowing)
- [ ] Async operations have proper error handling (no unhandled `asyncio` exceptions)
- [ ] HTTP client calls (`httpx`) handle connection errors, timeouts, and non-2xx responses
- [ ] WebSocket connections handle disconnection and reconnection gracefully

### Null/None Safety
- [ ] Dictionary access uses `.get()` or explicit key checks before access
- [ ] Optional return values are checked before use
- [ ] API response parsing handles missing fields gracefully
- [ ] Database query results are checked for None before attribute access
- [ ] Frontend state is initialized with safe defaults (not undefined)

### Import & Type Safety
- [ ] All imports resolve to existing modules
- [ ] Type annotations match actual usage (no `Any` hiding real bugs)
- [ ] Pydantic model fields have correct types matching data sources
- [ ] Frontend TypeScript types match backend API contracts
- [ ] No runtime type coercion errors (string vs int, etc.)

### Resource Management
- [ ] File handles use `with` statements or explicit close
- [ ] Database connections are properly closed/returned to pool
- [ ] Async generators and context managers use `async with`
- [ ] Background tasks have proper cleanup on shutdown
- [ ] WebSocket connections are closed on error/disconnect

### Race Conditions
- [ ] Shared mutable state is protected by locks where needed
- [ ] Database operations that read-then-write use transactions
- [ ] Frontend state updates handle concurrent async operations
- [ ] Polling loops handle overlapping invocations

## Acceptance Criteria
- All unhandled exceptions have proper error handling
- All resource leaks are fixed with cleanup patterns
- All fixes validated by `pytest` and `ruff check`
