# Data Model: Full Codebase Review & Refactoring

**Branch**: `023-codebase-review-refactor` | **Date**: 2026-03-06

## Overview

This feature does not introduce new data entities. It restructures existing code without changing data shapes or API contracts. This document maps the **service decomposition entity model** — how the 78 methods in the `GitHubProjectsService` monolith map to focused module classes and how they share state.

## Entity: GitHubProjectsService (Facade)

**What it represents**: The backward-compatible entry point that preserves the existing public API. After decomposition, it delegates to focused sub-services.

**Key attributes**:
- `_client`: `GitHubClient` — shared HTTP infrastructure (from `client.py`)
- `_projects`: `ProjectsService` — project listing/querying
- `_board`: `BoardService` — board data, reconciliation, status
- `_issues`: `IssuesService` — issue CRUD, sub-issues, labels
- `_pull_requests`: `PullRequestsService` — PR operations
- `_copilot`: `CopilotService` — Copilot assignment and status
- `_fields`: `FieldsService` — project field operations
- `_repository`: `RepositoryService` — repo info, branches, commits, files

**Relationships**: Owns all sub-services. Each sub-service receives the shared `GitHubClient` instance. The facade re-exports every public method for backward compatibility.

## Entity: GitHubClient (Shared Infrastructure)

**What it represents**: The HTTP client infrastructure shared by all sub-services. Encapsulates REST and GraphQL request methods, rate limit tracking, retry logic, and the client factory.

**Key attributes**:
- `_client_factory`: `GitHubClientFactory` — creates authenticated httpx clients
- `_cycle_cache`: `BoundedDict` — per-polling-cycle cache (shared across sub-services)
- `_cycle_cache_hit_count`: `int` — metrics counter
- `_request_rate_limit`: `contextvars.ContextVar` — last rate limit info

**State transitions**: 
- `clear_cycle_cache()` → resets cache between polling cycles
- `close()` → cleanup on shutdown

**Validation rules**: Rate limit headers extracted from every REST response. Cache size bounded by `BoundedDict` capacity.

## Entity: Sub-Service Modules

Each sub-service has the same structural pattern:

**Pattern**:
```
class XxxService:
    def __init__(self, client: GitHubClient):
        self._client = client

    # Public methods (delegated from facade)
    # Private methods (_helpers)
```

**Module inventory**:

| Module | Class | Public Methods | Estimated LOC |
|--------|-------|----------------|---------------|
| `projects.py` | `ProjectsService` | 4 | ~170 |
| `board.py` | `BoardService` | 5 | ~720 |
| `issues.py` | `IssuesService` | 17 | ~750 |
| `copilot.py` | `CopilotService` | 8 | ~400 |
| `pull_requests.py` | `PullRequestsService` | 15 | ~700 |
| `fields.py` | `FieldsService` | 5 | ~350 |
| `repository.py` | `RepositoryService` | 11 | ~450 |

**Relationships**: All sub-services depend on `GitHubClient` (injected via constructor). Sub-services may call each other through the facade when cross-concern operations are needed (e.g., `board.py` calls `issues.py` methods for sub-issue fetching). Cross-calls go through the facade reference, not direct imports, to avoid circular dependencies.

## Entity: Error Handling Helpers

**What they represent**: Shared error handling utilities in `logging_utils.py`.

**Key attributes**:
- `handle_service_error(exc, operation, error_cls)` — logs error with structured context, raises appropriate exception
- `safe_error_response(exc, operation)` — returns safe error dict without exposing internals

**Validation rules**: `operation` string must describe what was being attempted. `error_cls` defaults to `HTTPException` for API endpoints.

## Entity: Validation Dependency

**What it represents**: A shared FastAPI dependency for common validation patterns.

**Key attributes**:
- `require_selected_project(session)` — raises `HTTPException(400)` if no project selected
- Returns the validated `selected_project_id` for use in the endpoint

**Relationships**: Used by all endpoints that need a selected project (chat, workflow, tasks, board operations).

## Entity: Cache Wrapper

**What it represents**: A generic cache-fetch method on `GitHubClient` that eliminates duplicated inline cache check/set patterns.

**Key attributes**:
- `_cycle_cached(key, fetch_fn)` — checks `_cycle_cache`, calls `fetch_fn` on miss, stores result
- Type-safe generic `T` return

**Relationships**: Used by 7+ methods across sub-services that currently have inline cache patterns.
