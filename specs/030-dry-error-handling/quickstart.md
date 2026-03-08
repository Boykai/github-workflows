# Quickstart: DRY Logging & Error Handling Modernization

**Feature**: 030-dry-error-handling | **Date**: 2026-03-08

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 030-dry-error-handling
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install    # Installs sonner (new dependency)
npm run dev
# App available at http://localhost:5173
```

## New Files to Create

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/utils/logger.ts` | NEW: Shared logger utility wrapping console methods, gated by `import.meta.env.DEV` |
| `frontend/src/components/common/ErrorAlert.tsx` | NEW: Shared error display component with retry/dismiss support |

### Backend

| File | Purpose |
|------|---------|
| (none) | No new backend files — only modifications to existing files |

## Files to Modify

### Backend (Phase 1)

| File | Changes |
|------|---------|
| `backend/src/exceptions.py` | Add `ConflictError` class (409) |
| `backend/src/api/agents.py` | Migrate 16 HTTPException → AppException; replace 3 manual logger+raise with `handle_service_error()` |
| `backend/src/api/chores.py` | Migrate 18 HTTPException → AppException; replace 3 manual logger+raise with `handle_service_error()` |
| `backend/src/api/auth.py` | Migrate 5 HTTPException → AppException |
| `backend/src/api/signal.py` | Migrate 11 HTTPException → AppException |
| `backend/src/api/tools.py` | Migrate 12 HTTPException → AppException |
| `backend/src/api/pipelines.py` | Migrate 7 HTTPException → AppException |
| `backend/src/api/webhooks.py` | Migrate 3 HTTPException → AppException |
| `backend/src/dependencies.py` | Migrate 5 HTTPException → AppException |
| `backend/src/api/cleanup.py` | Replace 3 manual logger+raise with `handle_service_error()` |
| `backend/src/api/board.py` | Replace 2 manual logger+raise with `handle_service_error()` |
| `backend/src/api/workflow.py` | Replace 1 manual logger+raise with `handle_service_error()` (if compatible) |
| `backend/src/api/settings.py` | Fix silent `except Exception: pass` with `logger.debug()` |
| `backend/src/main.py` | Add correlation IDs (`bg-<task>-<uuid>`) to 3 background tasks |

### Frontend (Phase 2)

| File | Changes |
|------|---------|
| `frontend/src/App.tsx` | Add `<Toaster />`, add `mutations.onError` default to QueryClient |
| `frontend/src/main.tsx` | Add `unhandledrejection` + `window.onerror` handlers |
| `frontend/src/components/common/ErrorBoundary.tsx` | Replace `console.error` → `logger.error` |
| `frontend/src/services/api.ts` | Replace `console.error` → `logger.error` |
| `frontend/src/hooks/useRealTimeSync.ts` | Replace `console.error` → `logger.error`; add `logger.info` to WebSocket fallback catch |
| `frontend/src/hooks/usePipelineConfig.ts` | Replace `console.warn` → `logger.warn` |
| `frontend/src/hooks/useBoardControls.ts` | Add `logger.warn` to 2 silent catches |
| `frontend/src/hooks/useSidebarState.ts` | Add `logger.warn` to 2 silent catches |
| `frontend/src/hooks/useAppTheme.ts` | Add `logger.warn` to silent catch |
| `frontend/src/pages/ProjectsPage.tsx` | Replace inline error banners with `<ErrorAlert>` |
| `frontend/src/pages/AgentsPipelinePage.tsx` | Replace `console.warn` → `logger.warn` |
| `frontend/src/components/chat/IssueRecommendationPreview.tsx` | Replace inline error displays with `<ErrorAlert>` |
| `frontend/src/components/chat/ChatInterface.tsx` | Replace file error display with `<ErrorAlert>` |

## Implementation Order

### Phase 1: Backend — Exception Hierarchy & Helpers (Steps 1-4)

#### Step 1: Add ConflictError (FR-003)

1. **`backend/src/exceptions.py`** — Add after `NotFoundError`:
   ```python
   class ConflictError(AppException):
       """Resource conflict (e.g., duplicate creation, concurrent modification)."""
       def __init__(self, message: str = "Resource conflict"):
           super().__init__(message, status_code=status.HTTP_409_CONFLICT)
   ```

**Verify**: `python -c "from src.exceptions import ConflictError; print(ConflictError().status_code)"` → prints `409`

#### Step 2: Migrate HTTPException → AppException (FR-002, FR-006)

For each file, apply this mechanical transformation:

```python
# Before
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Agent not found")

# After
from src.exceptions import NotFoundError
raise NotFoundError("Agent not found")
```

**Mapping guide per status code**:
- `status_code=400` → `ValidationError("message")` (or `McpValidationError` in MCP contexts)
- `status_code=401` → `AuthenticationError("message")`
- `status_code=403` → `AuthorizationError("message")`
- `status_code=404` → `NotFoundError("message")`
- `status_code=409` → `ConflictError("message")` (or `McpLimitExceededError` in MCP contexts)
- `status_code=500` → `GitHubAPIError("message")` for GitHub-related, or `AppException("message", status_code=500)` for generic

**Work through files in order**: `dependencies.py` → `auth.py` → `agents.py` → `chores.py` → `signal.py` → `tools.py` → `pipelines.py` → `webhooks.py`

**After each file**: Run `python -m pytest tests/unit/ -v` to check for regressions.

**Final check**: `grep -r "from fastapi import.*HTTPException" backend/src/api/ backend/src/dependencies.py` should return zero results (excluding `__pycache__`).

#### Step 3: Activate handle_service_error() (FR-001)

Replace manual `logger.error(..., exc_info=True)` + `raise AppException(...)` patterns:

```python
# Before
try:
    result = await service.do_thing(...)
except Exception as e:
    logger.error("Failed to do thing: %s", e, exc_info=True)
    raise GitHubAPIError(message="Failed to do thing") from e

# After
from src.logging_utils import handle_service_error
try:
    result = await service.do_thing(...)
except Exception as e:
    handle_service_error(e, "do thing", GitHubAPIError)
```

**Files**: `cleanup.py` (3), `agents.py` (3), `chores.py` (3), `board.py` (2), `workflow.py` (1)

**Verify**: `grep -r "handle_service_error" backend/src/api/` should show 12+ results.

#### Step 4: Fix Silent Catches & Add Background Task Correlation IDs (FR-004, FR-005)

1. **`settings.py` L156**: Add `logger.debug("Cache invalidation skipped: %s", e)` to the bare except block
2. **`main.py` background tasks**: Add `request_id_var.set(f"bg-<task>-{uuid4().hex[:8]}")` at the start of each iteration, with `request_id_var.reset(token)` in a finally block

**Verify**: Start the server and check logs for `bg-polling-`, `bg-cleanup-`, `bg-copilot-` prefixed correlation IDs.

### Phase 2: Frontend — Logger, ErrorAlert, Toast, Global Handlers (Steps 5-9)

#### Step 5: Create Logger Utility (FR-007)

Create `frontend/src/utils/logger.ts`:
```typescript
const logger = {
  error: (...args: unknown[]) => { console.error(...args); },
  warn: (...args: unknown[]) => { if (import.meta.env.DEV) console.warn(...args); },
  info: (...args: unknown[]) => { if (import.meta.env.DEV) console.info(...args); },
};
export { logger };
```

#### Step 6: Replace console.* calls and fix silent catches (FR-008, FR-009)

Work through each file listed in the "Files to Modify" table above.

**Verify**: `grep -r "console\.\(error\|warn\)" frontend/src/ --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v logger.ts` should return zero results.

#### Step 7: Create ErrorAlert Component (FR-010)

Create `frontend/src/components/common/ErrorAlert.tsx` with the interface and styling documented in `contracts/components.md`.

#### Step 8: Replace Inline Error Displays (FR-011)

Work through `ProjectsPage.tsx`, `IssueRecommendationPreview.tsx`, `ChatInterface.tsx` replacing destructive-styled inline divs with `<ErrorAlert>`.

**Verify**: Navigate to each page, trigger an error condition, confirm the ErrorAlert renders correctly.

#### Step 9: Install sonner and Wire Toast System (FR-012, FR-013, FR-014, FR-015)

```bash
cd frontend
npm install sonner
```

1. Add `<Toaster position="top-right" richColors />` to `App.tsx`
2. Add `mutations.onError` default to QueryClient config
3. Add global error handlers to `main.tsx`

**Verify**: Trigger a mutation failure → toast notification appears. Check browser console → `logger.error` output visible.

### Phase 3: Verification (Steps 10-11)

#### Step 10: Backend Tests (FR-016, FR-018)

```bash
cd backend
python -m pytest tests/unit/ -v
```

Confirm zero regressions. Then verify:
```bash
# Zero HTTPException in API routes
grep -r "from fastapi import.*HTTPException" backend/src/api/ backend/src/dependencies.py | grep -v __pycache__

# Non-zero handle_service_error callers
grep -r "handle_service_error" backend/src/api/ | grep -v __pycache__ | wc -l
```

#### Step 11: Frontend Tests (FR-017)

```bash
cd frontend
npx vitest run
npx tsc --noEmit
```

Confirm zero regressions and zero type errors.

## Key Patterns to Follow

### Backend: HTTPException Replacement Pattern

```python
# Step 1: Remove HTTPException import
# Step 2: Add AppException subclass imports
from src.exceptions import NotFoundError, ValidationError, GitHubAPIError

# Step 3: Replace each raise
# 404 errors
raise NotFoundError("Agent not found")

# 400/422 validation errors
raise ValidationError("Invalid agent name", details={"field": "name"})

# 500 errors with GitHub context
raise GitHubAPIError("Failed to create agent", details={"reason": str(e)})

# 500 errors without GitHub context (use base class)
raise AppException("Server configuration error", status_code=500)
```

### Backend: handle_service_error Pattern

```python
from src.logging_utils import handle_service_error

try:
    result = await service.operation(...)
except Exception as e:
    handle_service_error(e, "perform operation", GitHubAPIError)
    # Note: handle_service_error always raises — no code after this line executes
```

### Frontend: Logger Import Pattern

```typescript
import { logger } from '@/utils/logger';

// Replace console.error
logger.error('Something failed:', error);

// Replace console.warn
logger.warn('Something unexpected:', value);

// Add to silent catches
try {
  localStorage.setItem(key, value);
} catch {
  logger.warn('Failed to save to localStorage');
}
```

### Frontend: ErrorAlert Usage Pattern

```tsx
import { ErrorAlert } from '@/components/common/ErrorAlert';

// Simple error display
{error && <ErrorAlert message={error.message} />}

// With retry
{error && <ErrorAlert message={error.message} onRetry={() => refetch()} />}

// With dismiss
{error && <ErrorAlert message={error.message} onDismiss={() => setError(null)} />}

// With custom class
{error && <ErrorAlert message={error.message} className="mt-4" />}
```

## Verification Checklist

After implementation, verify:

1. **ConflictError**: Import and instantiate — status code is 409
2. **Zero HTTPException**: `grep` across API routes returns zero matches
3. **handle_service_error callers**: `grep` shows 12+ call sites (up from 0)
4. **Silent catches fixed**: No bare `except: pass` blocks remain in API routes
5. **Background task logs**: Server logs show `bg-polling-*`, `bg-cleanup-*`, `bg-copilot-*` correlation IDs
6. **Logger utility**: Import works, `logger.error()` emits in all modes, `logger.warn()`/`logger.info()` only in dev
7. **Console.* replaced**: Zero `console.error()`/`console.warn()` calls remain in frontend source (excluding logger.ts)
8. **ErrorAlert renders**: Each replacement target shows consistent error styling
9. **Toast fires**: Trigger a mutation error without per-mutation `onError` → toast appears
10. **Global handlers**: Trigger an unhandled promise rejection → `logger.error()` fires in console
11. **Backend tests pass**: `python -m pytest tests/unit/ -v` — zero regressions
12. **Frontend tests pass**: `npx vitest run` — zero regressions
13. **TypeScript compiles**: `npx tsc --noEmit` — zero errors
