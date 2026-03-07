# Feature Specification: Eliminate Duplicated Backend Code (DRY Phase 1)

**Feature Branch**: `028-backend-dry-refactor`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Refactor: Eliminate ~1,500+ Lines of Duplicated Backend Code (DRY Phase 1)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unified Repository Resolution (Priority: P1)

As a developer maintaining the backend, I want a single canonical way to resolve repository information so that I don't need to understand or maintain multiple divergent implementations that each handle the same task differently.

**Why this priority**: Repository resolution is foundational — it is called from 8+ locations and directly affects correctness of every feature that operates on a repository context. Consolidating to one implementation reduces the surface area for bugs and makes the behavior predictable across all endpoints.

**Independent Test**: Can be fully tested by verifying that all endpoints that previously used `_get_repository_info()` or inline fallback logic now delegate to `resolve_repository()` and produce identical results, while the full test suite remains green.

**Acceptance Scenarios**:

1. **Given** the function `_get_repository_info()` exists in `workflow.py`, **When** the refactoring is applied, **Then** the function is deleted and all its former callers use `resolve_repository()` from `utils.py` instead.
2. **Given** `main.py` contains an inline 3-step repository fallback (~100 lines), **When** the refactoring is applied, **Then** the inline logic is replaced with a single call to `resolve_repository()`.
3. **Given** the callers in `projects.py`, `tasks.py`, `chat.py`, and `chores.py` each resolve repository information independently, **When** the refactoring is applied, **Then** each caller delegates to `resolve_repository()` and no inline resolution logic remains.
4. **Given** the refactoring has been applied, **When** the full test suite is run, **Then** all existing tests pass without modification (behavior is unchanged).

---

### User Story 2 - Adopted Error Handling Helpers (Priority: P1)

As a developer writing or reviewing endpoint code, I want consistent error handling across all endpoints so that error responses follow a uniform format and I don't have to re-implement the same catch-log-raise boilerplate in every route handler.

**Why this priority**: Inconsistent error handling is a common source of production issues — different endpoints may return differently structured error responses, omit logging, or swallow exceptions. Centralizing this through the already-written (but unused) helpers improves reliability and auditability.

**Independent Test**: Can be fully tested by confirming that `handle_service_error()` and `safe_error_response()` from `logging_utils.py` are called in place of manual boilerplate in `board.py`, `workflow.py`, `projects.py`, and `auth.py`, while error responses remain structurally identical.

**Acceptance Scenarios**:

1. **Given** `handle_service_error()` and `safe_error_response()` exist in `logging_utils.py` but are never called, **When** the refactoring is applied, **Then** they are actively used in at least the 4 identified endpoint files.
2. **Given** `board.py`, `workflow.py`, `projects.py`, and `auth.py` contain hand-rolled catch→log→raise blocks, **When** the refactoring is applied, **Then** each block is replaced with a call to the centralized helper.
3. **Given** the refactoring has been applied, **When** error conditions are triggered in affected endpoints, **Then** the error response format and HTTP status codes remain unchanged from the current behavior.
4. **Given** the refactoring has been applied, **When** the full test suite is run, **Then** all existing tests pass without modification.

---

### User Story 3 - Selected Project Validation Helper (Priority: P2)

As a developer adding new endpoints that require a selected project, I want a single reusable validation function so that I can enforce the "project must be selected" invariant without copy-pasting the same conditional check into every route handler.

**Why this priority**: The repeated `if not session.selected_project_id: raise ValidationError(...)` pattern appears in 12+ locations. While each instance is small, the cumulative inconsistency risk is high — different messages, different exception types, or missing checks in new endpoints.

**Independent Test**: Can be fully tested by verifying that a new `require_selected_project(session)` function exists in `dependencies.py`, is called from all endpoints that previously had inline validation, and raises the expected error when no project is selected.

**Acceptance Scenarios**:

1. **Given** no `require_selected_project()` function exists, **When** the refactoring is applied, **Then** a function `require_selected_project(session) -> str` is added to `dependencies.py` that returns the selected project ID or raises an appropriate error.
2. **Given** `chat.py`, `workflow.py`, `tasks.py`, and `chores.py` each contain inline project-selection checks, **When** the refactoring is applied, **Then** each inline check is replaced with a call to `require_selected_project()`.
3. **Given** a request is made without a selected project, **When** the endpoint calls `require_selected_project()`, **Then** the same error response is returned as before the refactoring.
4. **Given** the refactoring has been applied, **When** the full test suite is run, **Then** all existing tests pass without modification.

---

### User Story 4 - Generic Cache Wrapper (Priority: P2)

As a developer working with cached data, I want a high-level cache wrapper that encapsulates the common check/get/set pattern so that I can add caching to any data-fetching operation without duplicating the same multi-step logic.

**Why this priority**: The verbose cache pattern (check if cached → return cached value → call fetch function → cache result → return) is repeated across multiple service files. A generic wrapper reduces boilerplate and ensures consistent cache behavior (TTL, stale fallback, refresh logic) across all call sites.

**Independent Test**: Can be fully tested by verifying that a `cached_fetch()` function exists in `cache.py`, is used by `projects.py`, `board.py`, and `chat.py` in place of their current inline cache patterns, and produces identical caching behavior.

**Acceptance Scenarios**:

1. **Given** no `cached_fetch()` function exists, **When** the refactoring is applied, **Then** a function `cached_fetch(cache_key, fetch_fn, refresh, *args)` is added to `cache.py`.
2. **Given** `projects.py`, `board.py`, and `chat.py` contain verbose check/get/set cache patterns, **When** the refactoring is applied, **Then** each pattern is replaced with a call to `cached_fetch()`.
3. **Given** `cached_fetch()` is called with `refresh=False` and valid cached data exists, **When** the function executes, **Then** the cached value is returned without calling the fetch function.
4. **Given** `cached_fetch()` is called with `refresh=True`, **When** the function executes, **Then** the fetch function is called, the result is cached, and the fresh value is returned.
5. **Given** the refactoring has been applied, **When** the full test suite is run, **Then** all existing tests pass without modification.

---

### Edge Cases

- What happens when `resolve_repository()` is called with a session that has no project context and no default repository configured? The existing 3-step fallback must still raise an appropriate error.
- What happens when `cached_fetch()` encounters an exception in the fetch function? The wrapper must not cache error states and should propagate the exception to the caller, while returning stale data if available.
- What happens when `require_selected_project()` is called from an endpoint that currently uses a different exception type (e.g., `NotFoundError` vs `ValidationError`)? The refactoring must preserve the existing error behavior per endpoint or unify to a single consistent error type with team agreement.
- What happens when error handling helpers are applied to endpoints that currently catch specific exception subtypes differently? The helper must support the same level of granularity or the endpoint must retain specialized handling where needed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST consolidate all repository resolution to the single `resolve_repository()` function in `utils.py`, eliminating `_get_repository_info()` and all inline resolution logic.
- **FR-002**: System MUST adopt the existing `handle_service_error()` and `safe_error_response()` helpers from `logging_utils.py` in all endpoint files that currently contain hand-rolled error handling boilerplate.
- **FR-003**: System MUST provide a `require_selected_project(session)` function in `dependencies.py` that returns the selected project ID or raises an error, replacing all inline validation blocks.
- **FR-004**: System MUST provide a `cached_fetch(cache_key, fetch_fn, refresh, *args)` function in `cache.py` that encapsulates the common cache check/get/set pattern.
- **FR-005**: Each of the four refactoring steps MUST be independently executable — applying any single step in isolation must leave the test suite fully passing.
- **FR-006**: System MUST preserve all existing external behavior (HTTP response formats, status codes, error messages, caching semantics) after each refactoring step is applied.
- **FR-007**: After each refactoring step, the duplicated pattern targeted by that step MUST no longer exist anywhere in the codebase (verified by text search).

### Key Entities

- **Repository Resolution**: The process of determining the `(owner, repo_name)` tuple for a given session context, using a prioritized fallback chain (project API → workflow config → default env).
- **Error Response**: A structured HTTP error response consisting of a status code, error message, and optional detail payload, produced consistently by centralized helpers.
- **Selected Project Validation**: A guard check that ensures a project ID is present in the user's session before allowing project-scoped operations to proceed.
- **Cached Fetch**: A higher-order operation that wraps a data-fetching function with cache lookup (before) and cache storage (after), supporting forced refresh and stale-data fallback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The total number of distinct repository-resolution code paths is reduced from 8+ to exactly 1, verified by searching for resolution-related function definitions and inline fallback patterns.
- **SC-002**: The `handle_service_error()` and `safe_error_response()` functions are called from at least 4 endpoint files, verified by searching for import and usage statements.
- **SC-003**: All inline selected-project validation blocks (12+ instances) are replaced by calls to `require_selected_project()`, verified by searching for the old pattern and confirming zero matches.
- **SC-004**: The verbose cache check/get/set pattern in `projects.py`, `board.py`, and `chat.py` is replaced by `cached_fetch()` calls, reducing cache-related lines by at least 50% across those files.
- **SC-005**: The full automated test suite passes with zero new failures after all four refactoring steps are applied, both individually and collectively.
- **SC-006**: No regressions are introduced in user-facing behavior — error responses, caching behavior, and repository resolution results remain identical pre- and post-refactoring.

## Assumptions

- The existing `resolve_repository()` function in `utils.py` is considered the correct and complete implementation; its behavior is the reference standard.
- The existing `handle_service_error()` and `safe_error_response()` helpers in `logging_utils.py` are correctly implemented and ready for adoption without modification (or with minimal adaptation).
- The current test suite provides sufficient coverage to detect behavioral regressions from the refactoring — no new tests are required to validate unchanged external behavior (though unit tests for the new helper functions themselves should be added).
- Each of the four refactoring steps can be performed in any order, and any subset of steps can be applied independently without creating an inconsistent state.
- The inline cache patterns across `projects.py`, `board.py`, and `chat.py` are semantically equivalent and can be unified under a single generic wrapper without loss of functionality.
