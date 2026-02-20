# Feature Specification: Codebase Cleanup & Refactor

**Feature Branch**: `007-codebase-cleanup-refactor`  
**Created**: 2026-02-19  
**Status**: Draft  
**Input**: User description: "refactor codebase to clean-up codebase. Keep it simple. Keep it DRY. Use best practices."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Break Apart Oversized Modules (Priority: P1)

As a developer working on this codebase, I need the two largest service files — `github_projects.py` (~4,400 lines) and `copilot_polling.py` (~4,000 lines) — split into focused, single-responsibility modules so that I can understand, navigate, and modify them without context-switching through thousands of lines.

**Why this priority**: These two files are the biggest barrier to maintainability. Their size makes code review difficult, merge conflicts frequent, and onboarding slow. Every other refactoring effort becomes easier once these are manageable.

**Independent Test**: Can be fully tested by verifying all existing unit and integration tests pass after the split, and that each new module has a clear, documented responsibility.

**Acceptance Scenarios**:

1. **Given** the existing `github_projects.py` service, **When** refactored, **Then** it is split into focused modules (e.g., repository resolution, issue/PR management, project board operations, label/status management) each under ~500 lines, with no change in external behavior.
2. **Given** the existing `copilot_polling.py` service, **When** refactored, **Then** it is split into focused modules (e.g., polling lifecycle, event processing, response parsing, status tracking) each under ~500 lines, with no change in external behavior.
3. **Given** any module that imports from `github_projects` or `copilot_polling`, **When** the split is complete, **Then** all imports resolve correctly and the application starts and serves requests identically.

---

### User Story 2 - Eliminate Duplicated Code Patterns (Priority: P1)

As a developer, I need duplicated logic consolidated into shared utilities so that bug fixes and behavior changes only need to happen in one place.

**Why this priority**: Duplicated code is the root cause of inconsistent behavior and wasted effort. Fixing a bug in one copy but not another leads to subtle production issues.

**Independent Test**: Can be fully tested by searching the codebase for previously-duplicated patterns and confirming each exists in exactly one location, with all callers using the shared version.

**Acceptance Scenarios**:

1. **Given** repository resolution logic appears in three separate locations (GitHub projects service, webhook handler, and copilot polling), **When** refactored, **Then** a single shared utility handles repository resolution and all three callers use it.
2. **Given** polling start/initialization logic is repeated in multiple places, **When** refactored, **Then** a single entry point manages polling lifecycle.
3. **Given** session reconstruction logic is duplicated across request handlers, **When** refactored, **Then** a shared session-management utility is used consistently.
4. **Given** cache key construction is scattered with inline string formatting, **When** refactored, **Then** cache keys are built through a centralized helper with consistent naming conventions.

---

### User Story 3 - Standardize Error Handling (Priority: P2)

As a developer, I need a single, consistent error-handling strategy across the entire backend so that errors are reported predictably and debugging is straightforward.

**Why this priority**: Currently, some modules raise `HTTPException` directly, others use custom `AppException` classes, and some silently swallow errors. This inconsistency makes it hard to trace failures and deliver reliable error messages to users.

**Independent Test**: Can be fully tested by triggering known error conditions in each API endpoint and verifying the response format, status code, and logged output follow the same pattern.

**Acceptance Scenarios**:

1. **Given** the backend has mixed error-handling patterns, **When** refactored, **Then** all API route handlers use a unified error-handling approach where domain exceptions are translated to HTTP responses in one place (e.g., a middleware or exception handler).
2. **Given** some service functions silently catch and ignore exceptions, **When** refactored, **Then** all exceptions are either handled explicitly with appropriate logging or propagated to the caller.
3. **Given** error responses vary in shape across endpoints, **When** refactored, **Then** all error responses follow a consistent structure (status code, error message, optional detail).

---

### User Story 4 - Consolidate Hardcoded Values and Magic Numbers (Priority: P2)

As a developer, I need all magic numbers, hardcoded strings, and configuration values moved to a central location so that tuning behavior doesn't require hunting through source code.

**Why this priority**: Hardcoded values scattered throughout the codebase (timeouts, retry counts, cache TTLs, default limits) make it impossible to adjust behavior without risk of missing an occurrence.

**Independent Test**: Can be fully tested by searching the codebase for numeric literals and string constants in business logic and confirming they reference named constants or configuration values.

**Acceptance Scenarios**:

1. **Given** timeout values, retry counts, and polling intervals are hardcoded in service files, **When** refactored, **Then** they are defined as named constants in the configuration or constants module.
2. **Given** cache TTL values are embedded inline, **When** refactored, **Then** all cache durations reference a single configuration source.
3. **Given** default pagination limits, batch sizes, and similar operational values are scattered, **When** refactored, **Then** they are centralized and documented.

---

### User Story 5 - Unify Frontend API Communication Layer (Priority: P2)

As a frontend developer, I need a single, consistent approach to calling backend APIs so that error handling, authentication headers, and retry logic are handled uniformly.

**Why this priority**: Currently the frontend mixes raw `fetch()` calls with inconsistent patterns across hooks. This leads to duplicated auth header logic, inconsistent error handling, and makes it easy to forget edge cases.

**Independent Test**: Can be fully tested by verifying all API calls route through a shared client, with consistent error handling and auth header injection.

**Acceptance Scenarios**:

1. **Given** frontend hooks make direct `fetch()` calls with manually constructed headers, **When** refactored, **Then** all API calls use a shared HTTP client that automatically handles authentication headers and base URL configuration.
2. **Given** error handling in API calls varies across hooks, **When** refactored, **Then** the shared client provides consistent error parsing and notification.
3. **Given** the frontend has no centralized response interceptor, **When** refactored, **Then** common concerns (401 redirect, network errors, response parsing) are handled in one place.

---

### User Story 6 - Improve Frontend State Management and Resilience (Priority: P3)

As a user, I need the application to handle page refreshes, errors, and edge cases gracefully so that I don't lose context or encounter blank screens.

**Why this priority**: Currently, in-memory state is lost on page refresh, there are no error boundaries, and redundant polling alongside WebSocket connections wastes resources. These are quality-of-life improvements that make the app feel robust.

**Independent Test**: Can be fully tested by refreshing the page mid-workflow and verifying state is preserved, and by simulating API failures and verifying error boundaries display helpful messages.

**Acceptance Scenarios**:

1. **Given** critical application state (selected project, board filters) is stored only in memory, **When** refactored, **Then** essential state is persisted to `sessionStorage` so that a page refresh restores the user's context within the same tab.
2. **Given** no error boundaries exist in the component tree, **When** refactored, **Then** error boundaries catch rendering failures and display fallback UI instead of a blank screen.
3. **Given** some views use both polling and WebSocket for the same data, **When** refactored, **Then** WebSocket is the primary real-time channel per data stream, with automatic polling fallback on disconnect that ceases when WebSocket reconnects.

---

### User Story 7 - Increase Test Coverage for Untested Modules (Priority: P3)

As a developer, I need test coverage for currently-untested services and hooks so that refactoring can proceed safely with a regression safety net.

**Why this priority**: Several backend services and most frontend hooks lack any test coverage. Without tests, the refactoring work in P1 and P2 stories carries higher risk of silent regressions.

**Independent Test**: Can be fully tested by running the test suite and verifying coverage reports show tests exist for previously-untested modules.

**Acceptance Scenarios**:

1. **Given** backend services `completion_providers.py`, `session_store.py`, `settings_store.py`, `agent_tracking.py`, and `workflow_orchestrator.py` have no dedicated tests, **When** tests are added, **Then** each service has unit tests covering its primary functions and edge cases.
2. **Given** frontend hooks `useSettings`, `useWorkflow`, `useAgentConfig`, `useChat`, `useProjectBoard`, and `useAppTheme` are untested, **When** tests are added, **Then** each hook has tests verifying its core behavior.
3. **Given** no frontend component tests exist, **When** basic component tests are added, **Then** key user-facing components (board view, chat panel, settings page) have rendering and interaction tests.

---

### Edge Cases

- What happens if a refactored module is imported by a third-party integration or script outside the main application? Thin re-export facades at the original module paths ensure backward compatibility. Internal code imports directly from new sub-modules.
- How does the system handle in-progress WebSocket connections during a deployment that includes the refactored modules? Existing connections should gracefully degrade.
- What happens when the centralized error handler encounters an unexpected exception type? It must fall back to a generic 500 response with appropriate logging rather than crashing.
- What if removing duplicate code reveals that the copies had diverged in subtle ways? The refactoring must reconcile differences explicitly, choosing the correct behavior and documenting the decision.

## Clarifications

### Session 2026-02-19

- Q: Should error responses include internal details (stack traces, exception class names) or only sanitized user-safe messages? → A: Sanitized user-safe messages always; full details logged server-side only.
- Q: Which browser storage mechanism should be used for persisting navigation state across page refreshes? → A: `sessionStorage` (per-tab, clears on tab close, no cross-tab leakage).
- Q: When the WebSocket connection drops, what should the fallback behavior be? → A: WebSocket primary + automatic polling fallback on disconnect; polling stops when WS reconnects.
- Q: Should original service file paths remain as re-export facades after the module split? → A: Yes — keep thin re-export facades at original paths; internal code imports from new sub-modules.
- Q: Where should the shared frontend HTTP client obtain the auth token from? → A: Client reads from a centralized auth context/store at request time (lazy lookup).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain identical external API behavior (request/response contracts) after all refactoring — no endpoint signatures, response shapes, or status codes may change.
- **FR-002**: System MUST split `github_projects.py` into focused sub-modules with single responsibilities, each no larger than ~500 lines. The original module path MUST remain as a thin re-export facade preserving the existing public API for backward compatibility.
- **FR-003**: System MUST split `copilot_polling.py` into focused sub-modules with single responsibilities, each no larger than ~500 lines. The original module path MUST remain as a thin re-export facade preserving the existing public API for backward compatibility.
- **FR-004**: System MUST consolidate duplicate repository-resolution logic into a single shared utility used by all callers.
- **FR-005**: System MUST consolidate duplicate polling-initialization logic into a single entry point.
- **FR-006**: System MUST consolidate duplicate session-reconstruction logic into a shared utility.
- **FR-007**: System MUST centralize all cache key construction through a shared helper with consistent naming.
- **FR-008**: System MUST use a unified error-handling strategy where domain exceptions map to HTTP responses through a single mechanism (middleware or handler).
- **FR-009**: System MUST ensure all error responses follow a consistent, sanitized structure across all endpoints — no internal details (stack traces, exception class names, database info) are ever returned to the client. Full diagnostic details MUST be logged server-side only.
- **FR-010**: System MUST move all hardcoded magic numbers, timeouts, retry counts, TTLs, and default limits to named constants or configuration.
- **FR-011**: Frontend MUST route all API calls through a shared HTTP client with automatic base URL configuration. The client MUST obtain the auth token via lazy lookup from a centralized auth context/store at request time, avoiding stale tokens.
- **FR-012**: Frontend MUST implement error boundaries to prevent blank screens on component rendering failures.
- **FR-013**: Frontend MUST persist essential navigation state (selected project, board context) across page refreshes using `sessionStorage`, scoped per browser tab.
- **FR-014**: Frontend MUST use WebSocket as the primary real-time update channel with automatic polling fallback when the WebSocket connection is lost. Polling MUST stop automatically once the WebSocket reconnects. No data stream may use both channels simultaneously.
- **FR-015**: System MUST have unit tests for all backend services that currently lack coverage (`completion_providers`, `session_store`, `settings_store`, `agent_tracking`, `workflow_orchestrator`).
- **FR-016**: Frontend MUST have tests for all hooks that currently lack coverage (`useSettings`, `useWorkflow`, `useAgentConfig`, `useChat`, `useProjectBoard`, `useAppTheme`).

### Key Entities

- **Service Module**: A focused backend module with a single responsibility, defined public interface, and clear dependency boundaries. Replaces the current monolithic service files.
- **Shared Utility**: A reusable function or class extracted from duplicated code, consumed by multiple callers. Lives in a dedicated utilities layer.
- **HTTP Client**: A frontend abstraction over `fetch()` that centralizes base URL, error handling, and response parsing for all API communication. Obtains the auth token via lazy lookup from a centralized auth context/store at each request time, ensuring tokens are never stale.
- **Error Response**: A standardized, sanitized structure returned by all API endpoints on failure, containing status code, error type, and user-facing message. Internal diagnostic details (stack traces, exception classes) are never included in the response body; they are logged server-side only.
- **Named Constant**: A configuration value or operational parameter defined in a central location with a descriptive name, replacing inline magic numbers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No backend source file exceeds 500 lines of code (excluding tests and generated files).
- **SC-002**: Zero instances of duplicated logic patterns — each business operation (repo resolution, polling init, session construction, cache key building) exists in exactly one location.
- **SC-003**: All API error responses conform to a single documented structure, verifiable by running the full test suite.
- **SC-004**: All operational parameters (timeouts, retries, TTLs, limits) are traceable to named constants — zero magic numbers in business logic.
- **SC-005**: 100% of frontend API calls route through the shared HTTP client — zero direct `fetch()` calls outside the client module.
- **SC-006**: Application state survives a page refresh for all primary workflows (project selection, board view, active chat) via `sessionStorage`, without leaking state across tabs.
- **SC-007**: All existing tests pass without modification to test assertions (test infrastructure changes are acceptable).
- **SC-008**: Backend test coverage increases to include all five currently-untested service modules.
- **SC-009**: Frontend test coverage increases to include all six currently-untested hooks.
- **SC-010**: Developer onboarding time for understanding a single module decreases — measured by each module having a clear, single-sentence description of its responsibility in its docstring.

## Assumptions

- The existing test suite is trusted as the correctness baseline. If all tests pass after refactoring, behavior is considered preserved.
- "No larger than ~500 lines" is a guideline, not a hard rule — a module may slightly exceed this if splitting further would harm cohesion.
- Backend database schema and migration files are out of scope for this refactoring effort.
- Third-party API contracts (GitHub API, Copilot API) are unchanged and the refactoring only affects internal code organization.
- The frontend build toolchain (Vite, TypeScript, ESLint) and backend framework (FastAPI) remain unchanged.
- Performance characteristics should remain unchanged or improve — no refactoring should introduce additional latency or resource consumption.
