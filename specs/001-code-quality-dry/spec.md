# Feature Specification: Code Quality & DRY — Phase 2

**Feature Branch**: `001-code-quality-dry`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Phase 2: Code Quality and DRY — Consolidate repository resolution, generic cached_fetch helper, require_selected_project dependency, activate handle_service_error, simplify REST/GraphQL fallback"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Consolidate Repository Resolution (Priority: P1)

As a backend developer, I want a single `resolve_repository()` call site pattern so that every endpoint that needs owner/repo information uses one consistent, error-handled path instead of duplicating try/except blocks across 20+ call sites.

**Why this priority**: Repository resolution is the most widely duplicated pattern in the codebase (20+ call sites across agents, tasks, chores, workflow, pipelines, and projects routers). Consolidating it eliminates the largest volume of repeated code and prevents future inconsistencies (e.g. workflow.py missing REST fallback).

**Independent Test**: Can be fully tested by invoking any endpoint that previously called `resolve_repository()` and verifying the response is identical — same success payloads, same error codes, same logging output — while confirming the duplicated try/except blocks have been removed from each router.

**Acceptance Scenarios**:

1. **Given** an endpoint that needs repository owner and name, **When** the endpoint calls the consolidated resolution helper, **Then** the helper returns `(owner, repo)` on success or raises the correct `AppException` subclass on failure, with the error logged exactly once.
2. **Given** the primary resolution strategy (GraphQL) fails, **When** the consolidated helper runs, **Then** it falls back to workflow configuration and finally to default app settings, in the same order as today.
3. **Given** a developer adds a new endpoint that needs repository info, **When** they use the consolidated helper, **Then** they write zero error-handling boilerplate — a single function call replaces 5–8 lines of try/except.

---

### User Story 2 — Generic Cached Fetch Helper (Priority: P1)

As a backend developer, I want a reusable `cached_fetch()` helper that encapsulates the cache-check / fetch / store lifecycle so that every router that caches GitHub data uses one pattern instead of reimplementing the same 10–15 lines.

**Why this priority**: Cache logic is duplicated across projects, board, and chat routers (80+ LOC). Each copy has subtle drift (some support stale-on-error fallback, some support hash-based change detection, some don't). A single helper eliminates duplication and ensures consistent cache behaviour across the application.

**Independent Test**: Can be fully tested by calling any cached endpoint twice — the second call should return cached data without hitting GitHub, and the helper should log a cache-hit message. Force a cache miss (via `refresh=true`) and confirm the helper fetches, stores, and returns fresh data.

**Acceptance Scenarios**:

1. **Given** a cached endpoint receives a request and valid cached data exists, **When** `cached_fetch()` is called, **Then** it returns the cached data without invoking the fetch function.
2. **Given** a cached endpoint receives a request with `refresh=true`, **When** `cached_fetch()` is called, **Then** it bypasses the cache, calls the fetch function, stores the result, and returns fresh data.
3. **Given** the fetch function raises an error and stale cached data exists, **When** `cached_fetch()` is called with stale-fallback enabled, **Then** it returns the stale data and logs a warning.
4. **Given** the fetch function returns data identical to the cached version (same hash), **When** `cached_fetch()` is called with hash-comparison enabled, **Then** it skips the cache write and returns the existing data.

---

### User Story 3 — Enforce require_selected_project() Dependency (Priority: P2)

As a backend developer, I want every endpoint that requires a selected project to use the `require_selected_project()` FastAPI dependency so that project validation is consistent and no endpoint silently defaults to an empty string when no project is selected.

**Why this priority**: The `require_selected_project()` helper already exists in `dependencies.py` but several endpoints bypass it by using inline `session.selected_project_id or ""` checks, which silently degrade instead of raising a clear validation error. Enforcing the dependency prevents subtle bugs.

**Independent Test**: Can be fully tested by calling any affected endpoint without a selected project and verifying a clear validation error is returned (not an empty-string default).

**Acceptance Scenarios**:

1. **Given** an endpoint requires a selected project and the user has not selected one, **When** the endpoint is called, **Then** it raises a `ValidationError` with the message "No project selected. Please select a project first."
2. **Given** an endpoint previously used `session.selected_project_id or ""`, **When** the refactoring is complete, **Then** that inline check is replaced with the `require_selected_project()` dependency.
3. **Given** a developer creates a new endpoint that needs a project context, **When** they declare the dependency, **Then** project validation happens automatically before the endpoint body executes.

---

### User Story 4 — Activate handle_service_error() Consistently (Priority: P2)

As a backend developer, I want all endpoint error-handling to use `handle_service_error()` so that every caught exception is logged and re-raised with a safe, structured message instead of each endpoint reinventing its own catch → log → raise pattern.

**Why this priority**: `handle_service_error()` is already defined in `logging_utils.py` and is used in several routers, but adoption is inconsistent. Some endpoints still have ad-hoc try/except blocks that leak internal details or use inconsistent error classes. Standardising usage improves security (no leaked tracebacks) and debuggability (consistent log format).

**Independent Test**: Can be fully tested by triggering an error in any refactored endpoint and verifying the response contains a generic safe message (e.g. "Failed to {operation}") while the server log contains the full exception context.

**Acceptance Scenarios**:

1. **Given** an endpoint encounters an unexpected exception during a service call, **When** the exception is caught, **Then** `handle_service_error()` is called with the exception, a human-readable operation name, and the appropriate `AppException` subclass.
2. **Given** `handle_service_error()` is called, **When** it processes the exception, **Then** it logs the full exception with traceback at ERROR level and raises the specified `AppException` with a safe user-facing message.
3. **Given** an endpoint currently has a custom try/except block that duplicates the handle_service_error pattern, **When** the refactoring is complete, **Then** that custom block is replaced with a single `handle_service_error()` call.

---

### User Story 5 — Simplify REST/GraphQL Fallback (Priority: P3)

As a backend developer, I want the REST/GraphQL retry logic in `add_issue_to_project()` to use the existing `_with_fallback()` helper so that the multi-strategy approach is expressed in fewer lines and is easier to extend with new strategies.

**Why this priority**: The `add_issue_to_project()` function contains ~100 LOC of multi-step retry logic (GraphQL → verify → REST fallback). A `_with_fallback()` helper already exists in the service layer. Wiring them together simplifies the function and makes the fallback pattern reusable for future operations that may need similar GraphQL-then-REST strategies.

**Independent Test**: Can be fully tested by adding an issue to a project via the API and verifying the item appears in the project. Simulate a GraphQL failure (e.g. mock a 502) and confirm the REST fallback path succeeds.

**Acceptance Scenarios**:

1. **Given** `add_issue_to_project()` is called and GraphQL succeeds, **When** the item is verified on the project, **Then** the function returns the project item ID and logs "primary" strategy.
2. **Given** `add_issue_to_project()` is called and GraphQL fails, **When** the REST fallback is attempted, **Then** the function retries via REST API and returns the project item ID with "fallback" strategy logged.
3. **Given** both GraphQL and REST strategies fail, **When** `_with_fallback()` processes the errors, **Then** a single `RuntimeError` is raised containing context from both failures.

---

### Edge Cases

- What happens when the cache is empty and the fetch function also fails (no stale data available)? The `cached_fetch()` helper must propagate the original exception.
- What happens when `resolve_repository()` returns a valid tuple but the repo has been deleted or renamed? The caller receives the stale data; this is existing behaviour and out of scope for this refactoring.
- What happens when `require_selected_project()` is used in a WebSocket handler instead of a REST endpoint? The dependency must work in both contexts or raise a clear error.
- What happens when `handle_service_error()` is called with an `AppException` that is already structured? It must re-raise the original `AppException` without wrapping it (existing `except AppException: raise` guard).
- What happens when `_with_fallback()` primary succeeds but verification fails? Verification failure triggers the fallback strategy.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a single consolidated helper for repository resolution that encapsulates the fetch call and its error handling, replacing all duplicated try/except blocks.
- **FR-002**: System MUST preserve the existing 4-step resolution order (cache → GraphQL → workflow config → app defaults) when consolidating repository resolution.
- **FR-003**: System MUST provide a generic `cached_fetch()` helper that accepts a cache key, a fetch function, and optional configuration (TTL, refresh flag, stale-fallback, hash-comparison).
- **FR-004**: The `cached_fetch()` helper MUST return cached data on cache hit, call the fetch function on cache miss, and store the result before returning.
- **FR-005**: The `cached_fetch()` helper MUST support a stale-data fallback mode that returns expired cache entries when the fetch function fails.
- **FR-006**: The `cached_fetch()` helper MUST support hash-based change detection to skip unnecessary cache writes when data has not changed.
- **FR-007**: System MUST replace all inline `session.selected_project_id or ""` patterns with the `require_selected_project()` FastAPI dependency.
- **FR-008**: System MUST ensure `require_selected_project()` raises a `ValidationError` with a clear message when no project is selected, rather than silently defaulting.
- **FR-009**: System MUST use `handle_service_error()` in all endpoints where exceptions are caught and re-raised, instead of ad-hoc try/except blocks.
- **FR-010**: `handle_service_error()` MUST preserve the existing behaviour: log full exception context at ERROR level, raise the specified `AppException` subclass with a safe user-facing message.
- **FR-011**: `handle_service_error()` MUST NOT wrap exceptions that are already `AppException` instances — these must be re-raised directly.
- **FR-012**: System MUST refactor `add_issue_to_project()` to use the `_with_fallback()` helper for its GraphQL-then-REST strategy.
- **FR-013**: The `_with_fallback()` helper MUST log which strategy succeeded ("primary" or "fallback") for observability.
- **FR-014**: All refactored code MUST maintain backward compatibility — no changes to API request/response contracts, error codes, or user-visible behaviour.
- **FR-015**: All refactored code MUST preserve existing test coverage — no test removals or weakening of assertions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Lines of code dedicated to repository resolution error handling across all routers is reduced by at least 60% (from ~120 duplicated LOC to ≤48 LOC).
- **SC-002**: Lines of code dedicated to cache check/fetch/store patterns across all routers is reduced by at least 50% (from ~80 duplicated LOC to ≤40 LOC).
- **SC-003**: Zero endpoints use inline `session.selected_project_id or ""` — all project-requiring endpoints use `require_selected_project()`.
- **SC-004**: 100% of endpoint error-handling blocks that catch generic exceptions use `handle_service_error()` instead of ad-hoc logging and re-raising.
- **SC-005**: `add_issue_to_project()` function body is reduced by at least 40% in line count while preserving identical external behaviour.
- **SC-006**: All existing unit tests pass without modification after refactoring (zero regressions).
- **SC-007**: No new lint warnings or type-check errors are introduced (ruff check and pyright pass clean).
- **SC-008**: Developers can add a new cached endpoint in 3 lines or fewer (cache key + fetch function + `cached_fetch()` call).

### Assumptions

- The existing `_with_fallback()` helper in `service.py` is general-purpose enough to accommodate the `add_issue_to_project()` use case, including the verification step between primary and fallback strategies.
- The `handle_service_error()` function signature does not need to change; its current parameters (exception, operation name, optional error class) cover all existing use cases.
- The in-memory cache module already supports `get()`, `set()`, `get_stale()`, and `get_entry()` operations needed by the `cached_fetch()` helper.
- Refactoring is purely internal — no REST API contract changes, no new endpoints, no database migrations.
- All existing tests remain valid and should pass without modification after refactoring.
