# Error Response Contracts: DRY Logging & Error Handling Modernization

**Feature**: 030-dry-error-handling | **Date**: 2026-03-08

## Overview

This feature does **not** introduce new API endpoints. All changes are to the error response behavior of existing endpoints. After migration, all API error responses will conform to the unified `AppException` response shape, replacing the inconsistent `HTTPException` response shape.

---

## Error Response Shape (Post-Migration)

### AppException Response (Unified)

All errors raised via `AppException` subclasses are handled by the global `app_exception_handler` in `main.py` and return this shape:

```json
{
  "error": "Human-readable error message",
  "details": {
    "key": "value"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | string | Yes | Human-readable error message (from `exc.message`). Never contains internal stack traces or implementation details. |
| `details` | object | No | Additional structured context (from `exc.details`). May contain domain-specific information like `{"reason": "token_expired"}`. Empty object `{}` when no details provided. |

**Response Headers**:
- `Retry-After`: Only included for `RateLimitError` (429) responses. Value is the number of seconds until the rate limit resets.

### Status Code Mapping

| Status Code | Exception Class | When Used |
|-------------|----------------|-----------|
| 400 | `McpValidationError` | MCP configuration validation failures |
| 401 | `AuthenticationError` | Missing/expired/invalid credentials |
| 403 | `AuthorizationError` | Authenticated but lacking permission |
| 404 | `NotFoundError` | Resource does not exist |
| 409 | `ConflictError` | General resource conflicts (duplicate, concurrent modification) |
| 409 | `McpLimitExceededError` | MCP-specific: max configurations reached |
| 422 | `ValidationError` | Input validation failures (semantic, not syntactic) |
| 429 | `RateLimitError` | Rate limit exceeded (includes `Retry-After` header) |
| 500 | `AppException` (base) | Generic server errors not attributable to a specific category |
| 502 | `GitHubAPIError` | GitHub API call failures (timeout, auth, server error) |

### Generic Exception Response (Unchanged)

Unhandled exceptions (not `AppException` subclasses) are caught by the `generic_exception_handler` and return:

```json
{
  "error": "Internal server error"
}
```

Status code: 500. The exception is logged server-side with full traceback and correlation ID.

---

## Pre-Migration vs Post-Migration Comparison

### Before (HTTPException Pattern)

```python
# ❌ Anti-pattern: raw HTTPException
raise HTTPException(
    status_code=404,
    detail="Agent not found"
)
```

**Response shape** (FastAPI default):
```json
{
  "detail": "Agent not found"
}
```

### After (AppException Pattern)

```python
# ✅ Correct: AppException subclass
raise NotFoundError("Agent not found")
```

**Response shape** (global handler):
```json
{
  "error": "Agent not found",
  "details": {}
}
```

### Key Differences

| Aspect | HTTPException (Before) | AppException (After) |
|--------|----------------------|---------------------|
| Response field | `detail` (string) | `error` (string) + `details` (object) |
| Structured details | Not supported | `details` dict for machine-readable context |
| Correlation ID | Logged in generic handler only | Logged in both specific and generic handlers |
| Log integration | Manual (varies by caller) | Automatic via `handle_service_error()` or manual |
| Consistency | Inconsistent shapes across endpoints | Uniform shape for all error types |

**Note on Frontend Impact**: The frontend `normalizeApiError()` function in `api.ts` already handles both shapes — it checks for `raw.error` (AppException shape) and falls back to `raw.detail` (HTTPException shape). The migration will not break the frontend, but the `detail` fallback path will eventually become dead code once all endpoints use AppException.

---

## handle_service_error() Contract

The existing function in `logging_utils.py` that will gain callers:

```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
```

**Behavior**:
1. Logs at ERROR level: `"Operation '{operation}' failed: {exc}"` with `exc_info=True`
2. Raises `error_cls(message=f"Failed to {operation}")` with `from exc` chaining
3. If `error_cls` is `None`, defaults to `GitHubAPIError`

**Usage Pattern**:
```python
# Before
try:
    result = await some_service.do_thing(...)
except Exception as e:
    logger.error("Failed to do thing: %s", e, exc_info=True)
    raise GitHubAPIError(message="Failed to do thing") from e

# After
try:
    result = await some_service.do_thing(...)
except Exception as e:
    handle_service_error(e, "do thing", GitHubAPIError)
```

**Edge Case — AppException Re-Raise**: If the caught `exc` is already an `AppException` subclass, `handle_service_error()` will still wrap it in the specified `error_cls`. Callers that want to preserve the original AppException type should check `isinstance(exc, AppException)` before calling `handle_service_error()`, or re-raise directly.

---

## Background Task Correlation ID Contract

### Pattern

Each background task loop iteration sets a unique correlation ID before executing its work:

```python
from uuid import uuid4
from src.middleware.request_id import request_id_var

# At start of each iteration
token = request_id_var.set(f"bg-polling-{uuid4().hex[:8]}")
try:
    # ... task work ...
finally:
    request_id_var.reset(token)
```

### Correlation ID Format

| Task | Pattern | Example |
|------|---------|---------|
| `_polling_watchdog_loop` | `bg-polling-<hex8>` | `bg-polling-a1b2c3d4` |
| `_session_cleanup_loop` | `bg-cleanup-<hex8>` | `bg-cleanup-e5f6g7h8` |
| `_auto_start_copilot_polling` | `bg-copilot-<hex8>` | `bg-copilot-i9j0k1l2` |

The 8-character hex suffix provides 4 billion unique values, sufficient for distinguishing iterations without the overhead of full UUIDs.

### Log Output (Post-Implementation)

```
2026-03-08T06:18:02Z [INFO] request_id=bg-polling-a1b2c3d4 Checking copilot polling status...
2026-03-08T06:18:02Z [WARN] request_id=bg-polling-a1b2c3d4 Polling stopped unexpectedly, restarting...
2026-03-08T06:18:05Z [INFO] request_id=bg-cleanup-e5f6g7h8 Running session cleanup...
```

---

## Toast Notification Contract (Frontend)

### Default Mutation Error Toast

Triggered by `QueryClient.defaultOptions.mutations.onError`:

```typescript
toast.error(error instanceof Error ? error.message : 'An error occurred');
```

**Visual**: Sonner default error toast styled to match the design system:
- Position: top-right (configurable via `<Toaster position="top-right" />`)
- Duration: 5 seconds (auto-dismiss)
- Appearance: destructive theme (red accent)
- Stackable: Multiple toasts stack vertically

### Override Behavior

Per-mutation `onError` callbacks take precedence:

```typescript
// This mutation will NOT trigger the default toast
useMutation({
  mutationFn: async () => { ... },
  onError: (error) => {
    // Custom error handling — default toast is bypassed
    setLocalError(error.message);
  },
});
```

This is standard TanStack Query v5 behavior — the global default `onError` only fires when no per-mutation `onError` is defined.
