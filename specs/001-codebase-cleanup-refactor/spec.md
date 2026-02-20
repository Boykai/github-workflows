# Feature Specification: Codebase Cleanup & Refactor

**Feature Branch**: `001-codebase-cleanup-refactor`  
**Created**: 2026-02-20  
**Status**: Draft  
**Input**: User description: "refactor codebase to clean-up codebase. Keep it simple. Keep it DRY. Use best practices."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Break Apart Oversized Modules (Priority: P1)

As a developer working on this codebase, I need the largest service files — `github_projects.py` (~4,400 lines), `copilot_polling.py` (~4,000 lines), and `workflow_orchestrator.py` (~2,000 lines) — split into focused, single-responsibility modules so that I can understand, navigate, and modify them without context-switching through thousands of lines.

**Why this priority**: These files are the biggest barrier to maintainability. Their size makes code review difficult, merge conflicts frequent, and onboarding slow. Every other refactoring effort becomes easier once these are manageable.

**Independent Test**: Can be fully tested by verifying all existing unit and integration tests pass after the split, and that each new module has a clear, documented responsibility.

**Acceptance Scenarios**:

1. **Given** the existing `github_projects.py` service (4,448 lines), **When** refactored, **Then** it is split into focused modules (e.g., repository resolution, issue/PR management, project board operations, label/status management) each under ~500 lines, with no change in external behavior.
2. **Given** the existing `copilot_polling.py` service (3,987 lines), **When** refactored, **Then** it is split into focused modules (e.g., polling lifecycle, event processing, response parsing, status tracking) each under ~500 lines, with no change in external behavior.
3. **Given** the existing `workflow_orchestrator.py` service (1,959 lines), **When** refactored, **Then** it is split into focused modules each under ~500 lines, with no change in external behavior.
4. **Given** any module that imports from `github_projects`, `copilot_polling`, or `workflow_orchestrator`, **When** the split is complete, **Then** all imports resolve correctly and the application starts and serves requests identically.
5. **Given** each original service file path, **When** the split is complete, **Then** a thin re-export facade remains at the original path preserving backward compatibility for any external or internal consumer.

---

### User Story 2 - Eliminate Duplicated Code Patterns (Priority: P1)

As a developer, I need duplicated logic consolidated into shared utilities so that bug fixes and behavior changes only need to happen in one place.

**Why this priority**: Duplicated code is the root cause of inconsistent behavior and wasted effort. Fixing a bug in one copy but not another leads to subtle production issues.

**Independent Test**: Can be fully tested by searching the codebase for previously-duplicated patterns and confirming each exists in exactly one location, with all callers using the shared version.

**Acceptance Scenarios**:

1. **Given** repository resolution logic appears in multiple locations (GitHub projects service, webhook handler, and copilot polling), **When** refactored, **Then** a single shared utility handles repository resolution and all callers use it.
2. **Given** polling start/initialization logic is repeated in multiple places, **When** refactored, **Then** a single entry point manages polling lifecycle.
3. **Given** session reconstruction logic is duplicated across request handlers, **When** refactored, **Then** a shared session-management utility is used consistently.
4. **Given** cache key construction is scattered with inline string formatting, **When** refactored, **Then** cache keys are built through a centralized helper with consistent naming conventions.

---

### User Story 3 - Standardize Error Handling (Priority: P2)

As a developer, I need a single, consistent error-handling strategy across the entire backend so that errors are reported predictably and debugging is straightforward.

**Why this priority**: The codebase already has a well-structured exception hierarchy (`AppException` and subclasses in `exceptions.py`) and global handlers in `main.py`, but usage is inconsistent. Some API routes raise `HTTPException` directly (e.g., `auth.py`), others use custom `AppException` classes, and some silently swallow errors. Standardizing usage will deliver consistent, sanitized error responses.

**Independent Test**: Can be fully tested by triggering known error conditions in each API endpoint and verifying the response format, status code, and logged output follow the same pattern.

**Acceptance Scenarios**:

1. **Given** the backend has mixed error-handling patterns (some routes use `HTTPException`, others use `AppException` subclasses), **When** refactored, **Then** all API route handlers exclusively use the existing `AppException` hierarchy and the global exception handlers in `main.py` translate them to HTTP responses.
2. **Given** some service functions silently catch and ignore exceptions, **When** refactored, **Then** all exceptions are either handled explicitly with appropriate logging or propagated to the caller.
3. **Given** error responses vary in shape across endpoints, **When** refactored, **Then** all error responses follow the consistent structure already defined in `main.py`'s global handler: status code, error message, and optional detail — with no internal details (stack traces, exception class names) ever returned to the client.

---

### User Story 4 - Consolidate Hardcoded Values and Magic Numbers (Priority: P2)

As a developer, I need all magic numbers, hardcoded strings, and configuration values moved to a central location so that tuning behavior doesn't require hunting through source code.

**Why this priority**: While some constants are already centralized (e.g., `MAX_RETRIES`, `INITIAL_BACKOFF_SECONDS` in `github_projects.py`, and `session_expire_hours`/`cache_ttl_seconds` in `config.py`), many operational values remain scattered in API route files (e.g., sleep durations, polling intervals, timeouts, and refresh rates in `api/projects.py`).

**Independent Test**: Can be fully tested by searching the codebase for numeric literals and string constants in business logic and confirming they reference named constants or configuration values.

**Acceptance Scenarios**:

1. **Given** timeout values, retry counts, and polling intervals are hardcoded in API route and service files, **When** refactored, **Then** they are defined as named constants in a centralized constants module or configuration.
2. **Given** cache TTL values are embedded inline, **When** refactored, **Then** all cache durations reference a single configuration source.
3. **Given** default pagination limits, batch sizes, sleep durations, and similar operational values are scattered across route handlers, **When** refactored, **Then** they are centralized and documented.

---

### User Story 5 - Unify Frontend API Communication Layer (Priority: P2)

As a frontend developer, I need all hooks to consistently use the existing shared API client (`services/api.ts`) so that error handling, authentication headers, and response parsing are handled uniformly.

**Why this priority**: The codebase already has a centralized API client (`api.ts`) with typed modules (`authApi`, `projectsApi`, `tasksApi`, `chatApi`, `boardApi`, `settingsApi`), but some hooks (notably `useWorkflow`) still use raw `fetch()` calls with manual state management. This inconsistency leads to duplicated auth header logic and inconsistent error handling.

**Independent Test**: Can be fully tested by verifying all API calls in hooks route through the `api.ts` client, with zero direct `fetch()` calls outside the client module.

**Acceptance Scenarios**:

1. **Given** `useWorkflow` and any other hooks make direct `fetch()` calls bypassing the shared client, **When** refactored, **Then** all API calls use the existing `api.ts` client that handles authentication headers and base URL configuration.
2. **Given** error handling in API calls varies across hooks, **When** refactored, **Then** the shared client provides consistent error parsing via the `ApiError` class.
3. **Given** the frontend has no centralized response interceptor, **When** refactored, **Then** common concerns (401 redirect, network errors, response parsing) are handled in the `api.ts` client.

---

### User Story 6 - Improve Frontend State Management and Resilience (Priority: P3)

As a user, I need the application to handle page refreshes, errors, and edge cases gracefully so that I don't lose context or encounter blank screens.

**Why this priority**: Currently, in-memory state is lost on page refresh, there are no error boundaries (only `ErrorToast`/`ErrorBanner` display components exist), and redundant polling alongside WebSocket connections wastes resources. These are quality-of-life improvements that make the app feel robust.

**Independent Test**: Can be fully tested by refreshing the page mid-workflow and verifying state is preserved, and by simulating API failures and verifying error boundaries display helpful messages.

**Acceptance Scenarios**:

1. **Given** critical application state (selected project, board filters) is stored only in memory, **When** refactored, **Then** essential state is persisted to `sessionStorage` so that a page refresh restores the user's context within the same tab.
2. **Given** no class-based error boundaries exist in the component tree, **When** refactored, **Then** error boundaries catch rendering failures and display a fallback UI (e.g., a card with an error message and a "Retry" or "Reload" option) instead of a blank screen.
3. **Given** some views use both polling and WebSocket for the same data, **When** refactored, **Then** WebSocket is the primary real-time channel per data stream, with automatic polling fallback on disconnect that ceases when WebSocket reconnects.

---

### User Story 7 - Increase Test Coverage for Untested Modules (Priority: P3)

As a developer, I need test coverage for currently-untested services and hooks so that refactoring can proceed safely with a regression safety net.

**Why this priority**: Four backend services and six frontend hooks lack any test coverage. Without tests, the refactoring work in P1 and P2 stories carries higher risk of silent regressions.

**Independent Test**: Can be fully tested by running the test suite and verifying coverage reports show tests exist for previously-untested modules.

**Acceptance Scenarios**:

1. **Given** backend services `completion_providers.py`, `session_store.py`, `settings_store.py`, and `agent_tracking.py` have no dedicated tests, **When** tests are added, **Then** each service has unit tests covering its primary functions and edge cases.
2. **Given** frontend hooks `useSettings`, `useWorkflow`, `useAgentConfig`, `useChat`, `useProjectBoard`, and `useAppTheme` are untested, **When** tests are added, **Then** each hook has tests verifying its core behavior using the established patterns (TanStack React Query wrapper, `vi.mock()`, `waitFor()`).
3. **Given** no frontend component tests exist for key views, **When** basic component tests are added, **Then** key user-facing components (board view, chat panel, settings page) have rendering and interaction tests.

---

### Edge Cases

- What happens if a refactored module is imported by a third-party integration or script outside the main application? Thin re-export facades at the original module paths ensure backward compatibility. Internal code imports directly from new sub-modules.
- How does the system handle in-progress WebSocket connections during a deployment that includes the refactored modules? Existing connections should gracefully degrade — the existing WebSocket error handling and reconnection logic in `useRealTimeSync` should be preserved.
- What happens when the centralized error handler encounters an unexpected exception type? The existing generic `Exception` handler in `main.py` already falls back to a 500 response with logging — this behavior must be preserved.
- What if removing duplicate code reveals that the copies had diverged in subtle ways? The refactoring must reconcile differences explicitly, choosing the correct behavior and documenting the decision.
- What if a sub-module split introduces circular dependencies between new sub-modules? Extract shared state into a dedicated context or data class rather than creating circular imports.

## Clarifications

### Session 2026-02-19

- Q: Should error responses include internal details (stack traces, exception class names) or only sanitized user-safe messages? → A: Sanitized user-safe messages always; full details logged server-side only.
- Q: Which browser storage mechanism should be used for persisting navigation state across page refreshes? → A: `sessionStorage` (per-tab, clears on tab close, no cross-tab leakage).
- Q: When the WebSocket connection drops, what should the fallback behavior be? → A: WebSocket primary + automatic polling fallback on disconnect; polling stops when WS reconnects.
- Q: Should original service file paths remain as re-export facades after the module split? → A: Yes — keep thin re-export facades at original paths; internal code imports from new sub-modules.
- Q: Where should the shared frontend HTTP client obtain the auth token from? → A: Client reads from a centralized auth context/store at request time (lazy lookup).

### Session 2026-02-20

- Q: Does `workflow_orchestrator.py` already have test coverage? → A: Yes — `test_workflow_orchestrator.py` (958 lines) already exists. It is excluded from the "untested services" list. Only `completion_providers.py`, `session_store.py`, `settings_store.py`, and `agent_tracking.py` lack dedicated tests.
- Q: Does the frontend already have a shared HTTP client? → A: Yes — `services/api.ts` provides a typed client with `ApiError` handling. The refactor focuses on ensuring all hooks use it consistently (e.g., migrating `useWorkflow` from raw `fetch()`).
- Q: Does the backend already have an exception hierarchy? → A: Yes — `exceptions.py` defines `AppException` with subclasses (`AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ValidationError`, `GitHubAPIError`, `RateLimitError`) and `main.py` registers global handlers. The refactor standardizes usage, not creation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain identical external API behavior (request/response contracts) after all refactoring — no endpoint signatures, response shapes, or status codes may change.
- **FR-002**: System MUST split `github_projects.py` (4,448 lines) into focused sub-modules with single responsibilities, each no larger than ~500 lines. The original module path MUST remain as a thin re-export facade preserving the existing public API for backward compatibility.
- **FR-003**: System MUST split `copilot_polling.py` (3,987 lines) into focused sub-modules with single responsibilities, each no larger than ~500 lines. The original module path MUST remain as a thin re-export facade preserving the existing public API for backward compatibility.
- **FR-004**: System MUST split `workflow_orchestrator.py` (1,959 lines) into focused sub-modules with single responsibilities, each no larger than ~500 lines. The original module path MUST remain as a thin re-export facade.
- **FR-005**: System MUST consolidate duplicate repository-resolution logic into a single shared utility used by all callers (GitHub projects service, webhook handler, copilot polling).
- **FR-006**: System MUST consolidate duplicate polling-initialization logic into a single entry point.
- **FR-007**: System MUST consolidate duplicate session-reconstruction logic into a shared utility.
- **FR-008**: System MUST centralize all cache key construction through a shared helper with consistent naming.
- **FR-009**: System MUST standardize error handling so that all API route handlers exclusively use the existing `AppException` hierarchy, with domain exceptions translated to HTTP responses through the global exception handlers in `main.py`. No route handler should raise `HTTPException` directly.
- **FR-010**: System MUST ensure all error responses follow the consistent, sanitized structure defined by the global handler — no internal details (stack traces, exception class names, database info) are ever returned to the client. Full diagnostic details MUST be logged server-side only.
- **FR-011**: System MUST move all remaining hardcoded magic numbers, timeouts, retry counts, TTLs, sleep durations, and default limits from API route handlers and service files to named constants in a centralized constants module or configuration.
- **FR-012**: Frontend MUST ensure all hooks route API calls through the existing `services/api.ts` client — no direct `fetch()` calls outside the client module. Hooks currently using raw `fetch()` (e.g., `useWorkflow`) MUST be migrated.
- **FR-013**: Frontend MUST implement class-based error boundaries to catch rendering failures and display a fallback UI (error message with "Retry"/"Reload" option) instead of a blank screen.
- **FR-014**: Frontend MUST persist essential navigation state (selected project, board context) across page refreshes using `sessionStorage`, scoped per browser tab.
- **FR-015**: Frontend MUST use WebSocket as the primary real-time update channel with automatic polling fallback when the WebSocket connection is lost. Polling MUST stop automatically once the WebSocket reconnects. No data stream may use both channels simultaneously.
- **FR-016**: System MUST have unit tests for all backend services that currently lack coverage: `completion_providers.py`, `session_store.py`, `settings_store.py`, and `agent_tracking.py`.
- **FR-017**: Frontend MUST have tests for all hooks that currently lack coverage: `useSettings`, `useWorkflow`, `useAgentConfig`, `useChat`, `useProjectBoard`, and `useAppTheme`.

### Key Entities

- **Service Module**: A focused backend module with a single responsibility, defined public interface, and clear dependency boundaries. Replaces the current monolithic service files. Each module includes a single-sentence docstring describing its responsibility.
- **Re-export Facade**: A thin module at the original file path that imports and re-exports all public symbols from the new sub-modules, ensuring backward compatibility for existing consumers.
- **Shared Utility**: A reusable function or class extracted from duplicated code, consumed by multiple callers. Lives in a dedicated utilities layer within the services directory.
- **Error Response**: A standardized, sanitized structure returned by all API endpoints on failure via the global `AppException` handler, containing status code, error type, and user-facing message. Internal diagnostic details are logged server-side only.
- **Named Constant**: A configuration value or operational parameter defined in a central location (`constants.py` or `config.py`) with a descriptive name, replacing inline magic numbers.
- **Error Boundary**: A React class component that catches JavaScript errors in its child component tree and renders a fallback UI instead of a blank screen.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No backend source file exceeds ~500 lines of code (excluding tests and generated files). Files may slightly exceed this if splitting further would harm cohesion.
- **SC-002**: Zero instances of duplicated logic patterns — each business operation (repository resolution, polling initialization, session construction, cache key building) exists in exactly one location.
- **SC-003**: All API error responses conform to the structure defined by the global exception handlers in `main.py`, verifiable by running the full test suite.
- **SC-004**: All operational parameters (timeouts, retries, TTLs, sleep durations, limits) are traceable to named constants — zero magic numbers in business logic outside the constants/configuration modules.
- **SC-005**: 100% of frontend API calls route through the `services/api.ts` client — zero direct `fetch()` calls outside the client module.
- **SC-006**: Application state survives a page refresh for all primary workflows (project selection, board view, active chat) via `sessionStorage`, without leaking state across tabs.
- **SC-007**: All existing tests pass without modification to test assertions (test infrastructure changes are acceptable).
- **SC-008**: Backend test coverage increases to include all four currently-untested service modules (`completion_providers`, `session_store`, `settings_store`, `agent_tracking`).
- **SC-009**: Frontend test coverage increases to include all six currently-untested hooks (`useSettings`, `useWorkflow`, `useAgentConfig`, `useChat`, `useProjectBoard`, `useAppTheme`).
- **SC-010**: Developer onboarding time for understanding a single module decreases — measured by each module having a clear, single-sentence description of its responsibility in its docstring or module header.

## Assumptions

- The existing test suite is trusted as the correctness baseline. If all tests pass after refactoring, behavior is considered preserved.
- "No larger than ~500 lines" is a guideline, not a hard rule — a module may slightly exceed this if splitting further would harm cohesion.
- Backend database schema and migration files are out of scope for this refactoring effort.
- Third-party API contracts (GitHub API, Copilot API) are unchanged and the refactoring only affects internal code organization.
- The frontend build toolchain (Vite, TypeScript, ESLint) and backend framework (FastAPI) remain unchanged.
- Performance characteristics should remain unchanged or improve — no refactoring should introduce additional latency or resource consumption.
- `workflow_orchestrator.py` already has test coverage (958-line test file) and is excluded from the "untested services" list; only `completion_providers.py`, `session_store.py`, `settings_store.py`, and `agent_tracking.py` need new tests.
- The existing `services/api.ts` frontend client is the target for API call consolidation — no new client library needs to be introduced.
- The existing `AppException` hierarchy and global handlers in `main.py` are the target for error handling standardization — no new exception framework needs to be created.
