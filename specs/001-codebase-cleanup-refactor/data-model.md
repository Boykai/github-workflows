# Data Model: Codebase Cleanup & Refactor

**Feature**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-20

> This refactoring does not introduce new database entities or API models. It restructures existing code into modules and shared utilities. This document defines the **module entities** and **shared utilities** that will be created.

## Module Entities

### Backend Service Modules

#### 1. `github_projects/` Package

**Location**: `backend/src/services/github_projects/`

| Module | Responsibility | Max Lines |
|--------|---------------|-----------|
| `__init__.py` | Re-export facade: imports and exposes `GitHubProjectsService` with all public methods from sub-modules | ~60 |
| `_client.py` | HTTP client initialization, GraphQL execution, request retry with exponential backoff and rate-limit handling | ~125 |
| `_projects.py` | Project listing (user/org), board data retrieval, project item pagination | ~550 |
| `_issues.py` | Issue CRUD (create, update body/state), draft item creation, status updates, project attachment, user assignment | ~293 |
| `_copilot_assignment.py` | Copilot bot ID resolution, agent assignment (GraphQL + REST fallback), issue context formatting, completion detection | ~623 |
| `_fields.py` | Project field schema retrieval, item field updates (Priority, Size, Estimate, dates), status-by-name helper | ~359 |
| `_pull_requests.py` | PR search, detail retrieval, merge, review request, branch operations, issue-PR linking | ~745 |
| `_pr_completion.py` | PR completion detection via timeline events, Copilot review checks | ~282 |
| `_sub_issues.py` | Sub-issue creation/retrieval, agent body tailoring, comments, file content, change detection, agent discovery | ~500 |

**Relationships**: All sub-modules share the `GitHubProjectsService` class instance. `_client.py` provides the shared `httpx.AsyncClient` used by all other modules. The class is reassembled in `__init__.py`.

#### 2. `copilot_polling/` Package

**Location**: `backend/src/services/copilot_polling/`

| Module | Responsibility | Max Lines |
|--------|---------------|-----------|
| `__init__.py` | Re-export facade: imports and exposes all public functions from sub-modules | ~40 |
| `_lifecycle.py` | Polling loop entry point, start/stop, status reporting, `PollingState` dataclass | ~200 |
| `_issue_tracking.py` | Sub-issue number resolution, Done! marker detection, issue body tracking table updates | ~200 |
| `_pipeline.py` | Pipeline state get/reconstruct, completion processing, advancement, status transitions | ~500 |
| `_agent_outputs.py` | PR output posting (markdown files + Done! markers to issues), child PR merging during output posting | ~570 |
| `_status_checks.py` | Per-status issue processing (Backlog → Ready → In Progress → In Review), review request management | ~500 |
| `_pr_completion.py` | Child PR completion detection, main PR completion detection, timeline event filtering | ~500 |
| `_recovery.py` | Stalled issue recovery with cooldown, legacy in-progress handling | ~500 |

**Relationships**: `_lifecycle.py` orchestrates the polling loop calling functions from `_status_checks.py` and `_recovery.py`. `_pipeline.py` is called by `_status_checks.py` and `_agent_outputs.py` for pipeline state management. `_pr_completion.py` is called by `_status_checks.py` and `_pipeline.py`.

### Shared Utilities

#### 3. `shared/` Directory

**Location**: `backend/src/services/shared/` (new)

| Module | Responsibility | Functions |
|--------|---------------|-----------|
| `repo_utils.py` | Repository owner/name resolution from various data formats | `resolve_repository(repo_data) -> tuple[str, str]` |

**Note**: Cache key construction is already partially centralized in `constants.py` and `cache.py`. Extension of existing modules is preferred over a new shared utility.

### Extended Existing Modules

#### 4. `constants.py` Extensions

**Location**: `backend/src/constants.py`

New named constants:

```python
# Polling & Timing
POLLING_INTERVAL_SECONDS = 60
HTTP_TIMEOUT_SECONDS = 30.0
SQLITE_BUSY_TIMEOUT_MS = 5000
COMPLETION_TIMEOUT_SECONDS = 120

# Collection Limits
MAX_COLLECTION_SIZE = 500
COLLECTION_TRIM_SIZE = 250

# Retry
MAX_RETRY_ATTEMPTS = 3
```

#### 5. `exceptions.py` Extensions

**Location**: `backend/src/exceptions.py`

No new exception classes needed — the existing hierarchy (`AppException`, `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ValidationError`, `GitHubAPIError`, `RateLimitError`) covers all required cases. A catch-all `Exception` handler will be added to `main.py`.

### Frontend Entities

#### 6. Error Boundary Component

**Location**: `frontend/src/components/common/ErrorBoundary.tsx` (new)

```typescript
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;  // Optional custom fallback
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}
```

**Behavior**: Class component using `componentDidCatch`. Displays fallback UI with error message and Reload button. Resets error state on retry.

#### 7. Session State Hook

**Location**: `frontend/src/hooks/useSessionState.ts` (new)

```typescript
function useSessionState<T>(key: string, defaultValue: T): [T, (value: T) => void]
```

**Behavior**: Mirrors `useState` API but persists to `sessionStorage`. Reads initial value from storage on mount. Writes on every state update.

#### 8. Shared HTTP Client Extensions

**Location**: `frontend/src/services/api.ts` (existing)

No new exports needed. The existing `request<T>()`, `authApi`, `projectsApi`, `tasksApi`, `chatApi`, `boardApi`, `settingsApi` cover all API operations. The work is to:
- Add missing API functions for workflow and agent config operations
- Migrate `useWorkflow.ts` and `useAgentConfig.ts` to use the centralized client

## State Transitions

### Module Split Migration

```
github_projects.py (monolithic)
    → github_projects/ (package)
        → __init__.py (re-export facade)
        → _client.py, _projects.py, _issues.py, ...

copilot_polling.py (monolithic)
    → copilot_polling/ (package)
        → __init__.py (re-export facade)
        → _lifecycle.py, _pipeline.py, _status_checks.py, ...
```

**Backward compatibility**: All external imports (`from services.github_projects import GitHubProjectsService`) continue to work via the `__init__.py` facade. Internal code migrates to direct sub-module imports.

### Error Handling Flow

```
Service raises AppException subclass
    → Global exception handler (main.py) catches AppException
    → Returns sanitized JSON: {"error": "message", "status_code": N}
    → Logs full details server-side

Service raises unexpected Exception
    → Catch-all handler (main.py) catches Exception
    → Returns generic JSON: {"error": "Internal server error", "status_code": 500}
    → Logs full stack trace server-side
```

### WebSocket / Polling Flow

```
Component mounts
    → Attempt WebSocket connection (5s timeout)
    → Success: status = "connected", receive real-time updates
    → Failure/timeout: status = "polling", start interval polling (5s)
    → WebSocket reconnects: stop polling, status = "connected"
    → WebSocket disconnects: start polling fallback
```

## Validation Rules

- No backend source file exceeds ~500 lines (excluding tests, generated files)
- All `__init__.py` facade files only contain imports and re-exports
- All API error responses match the standardized JSON structure
- All operational constants reference named values from `constants.py` or `config.py`
- All frontend API calls route through `services/api.ts`
- All existing tests pass without assertion changes
