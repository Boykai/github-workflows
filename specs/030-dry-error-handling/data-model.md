# Data Model: DRY Logging & Error Handling Modernization

**Feature**: 030-dry-error-handling | **Date**: 2026-03-08

## Backend Entities (Python)

### ConflictError (New)

New exception class in the AppException hierarchy for general-purpose 409 Conflict responses.

```python
class ConflictError(AppException):
    """Resource conflict (e.g., duplicate creation, concurrent modification)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)
```

**Placement**: `backend/src/exceptions.py`, after `NotFoundError` and before `ValidationError`.

**Usage Pattern**: Replaces `HTTPException(status_code=409, detail=...)` in non-MCP contexts. MCP-specific 409 conflicts continue to use `McpLimitExceededError`.

### Complete AppException Hierarchy (Post-Migration)

```
AppException (500)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
├── ConflictError (409) ← NEW
├── ValidationError (422)
├── GitHubAPIError (502)
├── RateLimitError (429)
├── McpValidationError (400)
└── McpLimitExceededError (409)
```

### Existing Entities (Unchanged)

The following backend entities are referenced but not structurally modified:

- **`handle_service_error(exc, operation, error_cls)`** in `logging_utils.py` — function signature and behavior unchanged. Default `error_cls` is `GitHubAPIError`. Logs at ERROR level with `exc_info=True`, then raises the specified `AppException` subclass with message `"Failed to {operation}"`.
- **`safe_error_response(exc, operation)`** in `logging_utils.py` — unchanged. Returns a safe error string without raising.
- **`request_id_var`** in `middleware/request_id.py` — `contextvars.ContextVar[str]`. Set per-request by `RequestIDMiddleware`. Will also be set in background tasks with `bg-<task-name>-<uuid>` pattern.
- **Global `app_exception_handler`** in `main.py` — handles all `AppException` subclasses. Returns `JSONResponse` with `{"error": exc.message, "details": exc.details}`. No changes needed — `ConflictError` is automatically handled by virtue of inheriting from `AppException`.
- **Global `generic_exception_handler`** in `main.py` — catches all unhandled `Exception` types. Logs with request_id context. Returns generic 500 response. No changes needed.

---

## Frontend Types (TypeScript)

### Logger Utility (New)

```typescript
// frontend/src/utils/logger.ts

interface Logger {
  error: (...args: unknown[]) => void;
  warn: (...args: unknown[]) => void;
  info: (...args: unknown[]) => void;
}

const logger: Logger = {
  error: (...args: unknown[]) => {
    // Always emit errors regardless of environment
    console.error(...args);
  },
  warn: (...args: unknown[]) => {
    if (import.meta.env.DEV) {
      console.warn(...args);
    }
  },
  info: (...args: unknown[]) => {
    if (import.meta.env.DEV) {
      console.info(...args);
    }
  },
};

export { logger };
```

**Design Decisions**:
- `logger.error()` always emits (even in production) — errors should never be silently suppressed per spec assumptions.
- `logger.warn()` and `logger.info()` only emit in development mode — controlled by `import.meta.env.DEV` (Vite's built-in env flag).
- No initialization step — the logger is a plain object, immediately functional upon import.
- Stateless — no internal state, no configuration object, no setup function.

### ErrorAlert Component (New)

```typescript
// frontend/src/components/common/ErrorAlert.tsx

interface ErrorAlertProps {
  /** Error message to display */
  message: string;
  /** Optional retry callback — renders a Retry button when provided */
  onRetry?: () => void;
  /** Optional dismiss callback — renders a dismiss (×) button when provided */
  onDismiss?: () => void;
  /** Additional CSS classes for the root element */
  className?: string;
}
```

**Visual Structure**:
```
┌─────────────────────────────────────────────┐
│  ⚠️  Error message text here                │ [×]
│                                    [Retry]  │
└─────────────────────────────────────────────┘
```

**Styling**: Uses existing design system tokens:
- Border: `border border-destructive/30`
- Background: `bg-destructive/10`
- Text: `text-destructive`
- Rounding: `rounded-[1.1rem]` (matches ProjectsPage banners)
- Padding: `p-4`
- Retry button: `bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90`
- Dismiss button: `text-destructive/60 hover:text-destructive`

### Existing Types (Unchanged)

```typescript
// frontend/src/services/api.ts — unchanged
export class ApiError extends Error {
  constructor(
    public status: number,
    public error: APIError
  ) {
    super(error.error);
    this.name = 'ApiError';
  }
}

// APIError shape — matches backend AppException handler output
interface APIError {
  error: string;          // Maps to exc.message
  details?: Record<string, unknown>;  // Maps to exc.details
}
```

---

## State Machines

### Backend Error Flow (Post-Migration)

```
API Request Arrives
    │
    ▼
┌────────────────────────┐
│  Route Handler          │
│  (agents.py, chores.py, │
│   auth.py, etc.)        │
└────────────┬───────────┘
             │
    ┌────────┴────────┐
    │                 │
  Success          Exception
    │                 │
    ▼                 ▼
┌────────┐    ┌──────────────────┐
│ Return  │    │ Is it an AppException │
│ response│    │ subclass already?     │
└────────┘    └──────────┬───────────┘
                   ┌─────┴─────┐
                   │           │
                  Yes          No
                   │           │
                   ▼           ▼
            ┌──────────┐  ┌──────────────────┐
            │ Re-raise  │  │ handle_service_error() │
            │ as-is     │  │ or manual AppException  │
            └─────┬────┘  └──────────┬───────────┘
                  │                  │
                  └────────┬─────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ app_exception_handler   │
              │ (main.py)              │
              │ Returns JSONResponse:  │
              │ {error, details}       │
              │ + status_code          │
              └────────────────────────┘
```

### Background Task Correlation ID Flow (New)

```
Application Startup (lifespan)
    │
    ├─── _polling_watchdog_loop()
    │        │
    │        ▼
    │    Each iteration:
    │    request_id_var.set(f"bg-polling-{uuid4().hex[:8]}")
    │    ├── Log lines include "bg-polling-a1b2c3d4"
    │    └── request_id_var.set("") at iteration end
    │
    ├─── _session_cleanup_loop()
    │        │
    │        ▼
    │    Each iteration:
    │    request_id_var.set(f"bg-cleanup-{uuid4().hex[:8]}")
    │    ├── Log lines include "bg-cleanup-e5f6g7h8"
    │    └── request_id_var.set("") at iteration end
    │
    └─── _auto_start_copilot_polling()
             │
             ▼
         On invocation:
         request_id_var.set(f"bg-copilot-{uuid4().hex[:8]}")
         ├── Log lines include "bg-copilot-i9j0k1l2"
         └── request_id_var.set("") on completion
```

### Frontend Error Flow (Post-Implementation)

```
Mutation / Query Error Occurs
    │
    ├─── Mutation Error (TanStack Query)
    │        │
    │        ▼
    │    Per-mutation onError defined?
    │    ├── Yes → Call per-mutation handler (default skipped)
    │    └── No  → Default onError fires:
    │                ├── logger.error('Mutation failed:', error)
    │                └── toast.error(error.message)
    │
    ├─── Query Error (TanStack Query)
    │        │
    │        ▼
    │    Component renders <ErrorAlert> with error.message
    │    Optional: onRetry triggers query refetch
    │
    ├─── Unhandled Promise Rejection
    │        │
    │        ▼
    │    window.addEventListener('unhandledrejection', ...)
    │    └── logger.error('Unhandled rejection:', event.reason)
    │
    └─── Uncaught Error (window.onerror)
             │
             ▼
         logger.error('Uncaught error:', message, source, line, col, error)
```

---

## HTTPException Migration Map

Complete mapping of all 79 `HTTPException` usages across the codebase to their replacement AppException subclasses:

| File | HTTPException Status | Replacement | Count |
|------|---------------------|-------------|-------|
| `agents.py` | 400, 404, 500 | `ValidationError` / `NotFoundError` / `GitHubAPIError` | 16 |
| `chores.py` | 400, 404, 500 | `ValidationError` / `NotFoundError` / `GitHubAPIError` | 18 |
| `tools.py` | 400, 404, 500 | `ValidationError` / `NotFoundError` / `GitHubAPIError` | 12 |
| `signal.py` | 400, 404, 500 | `ValidationError` / `NotFoundError` / `GitHubAPIError` | 11 |
| `pipelines.py` | 400, 404, 500 | `ValidationError` / `NotFoundError` / `GitHubAPIError` | 7 |
| `auth.py` | 400, 401, 500 | `ValidationError` / `AuthenticationError` / `AppException` | 5 |
| `webhooks.py` | 400, 401, 500 | `ValidationError` / `AuthenticationError` / `AppException` | 3 |
| `dependencies.py` | 401, 500 | `AuthenticationError` / `AppException` | 5 |

**Note**: Each individual replacement requires reading the semantic context of the error to select the correct AppException subclass. The status codes listed are approximate groupings — the actual `detail` messages and exception types are determined per-instance during implementation.

---

## Database Changes

### No Schema Changes Required

This feature involves no database schema modifications. All changes are to Python exception handling patterns (backend) and TypeScript error display/logging patterns (frontend). The SQLite database schema, migrations, and query patterns are entirely unaffected.

---

## New npm Dependency

### sonner

| Property | Value |
|----------|-------|
| Package | `sonner` |
| Version | `^2.x` (latest v2 stable) |
| Size | ~3KB gzip |
| Purpose | Toast notification system for mutation error feedback |
| Peer Dependencies | `react` (satisfied), `react-dom` (satisfied) |
| Mount Point | `<Toaster />` in `frontend/src/App.tsx` |
| API | `import { toast } from 'sonner'` — `toast.error()`, `toast.success()`, `toast.info()` |

---

## localStorage Keys

No new localStorage keys are introduced by this feature.

---

## Environment Variables

No new environment variables. The logger utility uses `import.meta.env.DEV` which is a built-in Vite environment flag (true in dev mode, false in production builds).
