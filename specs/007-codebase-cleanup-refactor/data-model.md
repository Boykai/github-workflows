# Data Model: Codebase Cleanup & Refactor

**Feature**: `007-codebase-cleanup-refactor` | **Date**: 2026-02-19

> This refactoring creates no new data entities. All existing models, database schemas, and API contracts remain unchanged (FR-001). This document describes the **code organization entities** — the structural building blocks introduced or modified by the refactoring.

## Code Organization Entities

### 1. Service Package

A Python package that replaces a monolithic service file.

| Attribute | Description |
|-----------|-------------|
| `__init__.py` | Re-export facade preserving the original public API |
| Sub-modules | Focused files with single responsibility, each ~500 lines max |
| Shared state | Module-level singletons/state variables live in a dedicated `state.py` or `client.py` |
| Internal imports | Sub-modules import from siblings within the package |
| External imports | External consumers import from `__init__.py` only |

**Instances**:

```
services/github_projects/     →  replaces github_projects.py (4,449 lines)
├── __init__.py                   re-exports GitHubProjectsService + github_projects_service
├── client.py                     HTTP client, retry, GraphQL
├── queries.py                    GraphQL query/mutation constants
├── projects.py                   Project listing, board data
├── issues.py                     Issue CRUD, sub-issues
├── pull_requests.py              PR lifecycle, merge, review
├── assignments.py                Copilot/agent assignment
├── status.py                     Status field updates
└── agents.py                     Agent listing/discovery

services/copilot_polling/      →  replaces copilot_polling.py (3,988 lines)
├── __init__.py                   re-exports all public functions
├── state.py                      PollingState + mutable state vars
├── loop.py                       start/stop/poll cycle
├── backlog.py                    Backlog + Ready processing
├── in_progress.py                In-progress processing
├── pipeline.py                   Pipeline state management
├── completion.py                 PR completion detection
├── outputs.py                    Agent output posting
├── recovery.py                   Stalled issue recovery
└── manual.py                     Manual single-issue check
```

**Relationships**:
- `copilot_polling/*` → depends on → `github_projects/*` (via `github_projects_service`)
- `copilot_polling/*` → depends on → `workflow_orchestrator` (pipeline state)
- `api/*` → depends on → `github_projects/*` (via re-export facade)
- `api/workflow.py` → depends on → `copilot_polling/*` (via re-export facade)

### 2. Shared Utility

A focused module in `services/shared/` providing a single reusable capability.

| Attribute | Description |
|-----------|-------------|
| Purpose | One well-defined responsibility extracted from duplicated code |
| Interface | Module-level functions (no classes unless justified) |
| Dependencies | Minimal — standard library + project constants only |
| Consumers | 2+ callers minimum (proven duplication) |

**Instances**:

| Module | Interface | Consumers |
|--------|-----------|-----------|
| `github_headers.py` | `build_github_rest_headers(token: str) → dict` | `github_projects/*`, `webhooks.py` |
| `bounded_set.py` | `BoundedSet(max_size, prune_size)` with `add()`, `__contains__()`, `discard()` | `copilot_polling/state.py`, `webhooks.py` |
| `datetime_utils.py` | `parse_iso8601(s: str) → datetime`, `is_after(dt, cutoff) → bool` | `copilot_polling/completion.py`, `github_projects/pull_requests.py` |
| `cache_keys.py` | `cache_key_*(...)` functions (consolidated from 3 files) | All cache consumers |
| `issue_parsing.py` | `extract_issue_number_from_pr(pr) → int | None` | `webhooks.py`, `github_projects/pull_requests.py` |

### 3. Error Response (standardized)

| Field | Type | Description |
|-------|------|-------------|
| `error` | `string` | User-facing error message (sanitized, no internal details) |
| `details` | `dict | null` | Optional structured metadata (field validation errors, etc.) — never contains stack traces |

**Status code mapping** (from `AppException` hierarchy):

| Exception | Status | Default message |
|-----------|--------|----------------|
| `AuthenticationError` | 401 | "Authentication required" |
| `AuthorizationError` | 403 | "Access denied" |
| `NotFoundError` | 404 | "Resource not found" |
| `ValidationError` | 422 | "Validation failed" |
| `RateLimitError` | 429 | "Rate limit exceeded" |
| `GitHubAPIError` | 502 | "GitHub API error" |
| Unhandled `Exception` | 500 | "Internal server error" |

### 4. Named Constants (organizational)

**Backend** (`constants.py` additions):

| Group | Constants |
|-------|-----------|
| `GITHUB_API_*` | `GITHUB_API_VERSION`, `GITHUB_API_MAX_RETRIES`, `GITHUB_API_INITIAL_BACKOFF_SECONDS`, `GITHUB_API_MAX_BACKOFF_SECONDS` |
| `POLLING_*` | `POLLING_ASSIGNMENT_GRACE_SECONDS`, `POLLING_RECOVERY_COOLDOWN_SECONDS`, `POLLING_STATUS_TRANSITION_DELAY`, `POLLING_PROCESSED_MAX_SIZE`, `POLLING_PROCESSED_PRUNE_SIZE`, `POLLING_RECOVERY_MAX_SIZE`, `POLLING_RECOVERY_PRUNE_SIZE` |
| `WEBHOOK_*` | `WEBHOOK_MAX_DELIVERY_IDS` |

**Frontend** (new `constants.ts`):

| Constant | Value | Description |
|----------|-------|-------------|
| `WS_POLLING_FALLBACK_MS` | `5000` | Polling interval when WS disconnected |
| `BOARD_POLL_INTERVAL_MS` | `15000` | (Retained for reference but removed from useProjectBoard) |
| `WS_MAX_RECONNECT_ATTEMPTS` | `3` | Max WS reconnection attempts before fallback |
| `AUTH_STALE_TIME_MS` | `300000` | Auth check cache duration |
| `DATA_STALE_TIME_MS` | `10000` | Generic data cache duration |

### 5. Frontend Infrastructure

**SessionState** (`services/sessionState.ts`):

| Function | Signature | Description |
|----------|-----------|-------------|
| `getPersistedState` | `<T>(key: string): T \| null` | Read + JSON parse from sessionStorage |
| `setPersistedState` | `<T>(key: string, value: T): void` | JSON stringify + write to sessionStorage |
| `clearPersistedState` | `(key: string): void` | Remove key from sessionStorage |

**Persisted keys**: `selectedProjectId`, `boardFilters`

**ErrorBoundary** (`components/common/ErrorBoundary.tsx`):

| Prop | Type | Description |
|------|------|-------------|
| `children` | `ReactNode` | Content to render |
| `fallback?` | `ReactNode` | Optional custom fallback (default: "Something went wrong" + Reload button) |

## State Transition: No Changes

All existing state machines (issue statuses, pipeline states, agent tracking states) remain unchanged. The refactoring only reorganizes the code that manages these states — it does not alter the state transitions themselves.

## Validation Rules: No Changes

All existing validation (Pydantic models, API input validation) remains unchanged. The error handling standardization ensures validation errors surface consistently via `ValidationError` (422) but does not change what is validated.
