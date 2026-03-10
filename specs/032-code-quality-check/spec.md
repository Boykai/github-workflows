# Feature Specification: Code Quality Check

**Feature Branch**: `032-code-quality-check`  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "Code Quality Check — comprehensive audit and remediation of silent failures, security leaks, duplicated patterns, oversized files, type safety gaps, technical debt, performance issues, and testing/linting gaps across backend and frontend."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix Silent Failures and Security Vulnerabilities (Priority: P1)

As a developer maintaining the application, I need all exception handling to log meaningful context so that runtime bugs are visible in logs rather than silently swallowed, and I need internal error details hidden from external APIs so that sensitive information is never disclosed to end users.

**Why this priority**: Silent exception swallowing (32 `except → pass` blocks and 94 bare `except Exception:` without context) masks runtime bugs that can degrade the application undetected. Exception detail leaks to external APIs (3 locations in signal_chat.py) and overly permissive CORS configuration are active security risks. These must be fixed first because they affect system reliability and security in production.

**Independent Test**: Can be fully tested by triggering error conditions in backend services and verifying that (a) log output contains error context for every `except` block, (b) no internal exception details appear in responses sent to external APIs, and (c) CORS headers only allow explicitly listed HTTP methods.

**Acceptance Scenarios**:

1. **Given** a backend service encounters an exception in a `try` block, **When** the `except` clause executes, **Then** the error is logged with at least the exception type and a contextual message (no `pass`-only handlers remain).
2. **Given** a bare `except Exception:` block exists, **When** the exception is caught, **Then** the exception is bound to a variable (`as e`) and logged, and the `except` clause catches a specific exception type (not bare `Exception`) wherever feasible.
3. **Given** an internal error occurs in `signal_chat.py` during an external API call, **When** the error is caught, **Then** only a generic user-facing message is returned to the Signal API and the full exception details are logged internally.
4. **Given** a client sends an HTTP request using a non-standard method (e.g., `TRACE`), **When** the CORS middleware evaluates the request, **Then** the request is rejected because only `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, and `OPTIONS` are allowed.

---

### User Story 2 - Eliminate Duplicated Patterns (Priority: P1)

As a developer, I need duplicated code patterns consolidated into shared utilities so that bug fixes and behavior changes only need to happen in one place, reducing maintenance burden and inconsistency.

**Why this priority**: 8 separate repository resolution code paths, unused error handling helpers, repeated cache-or-fetch boilerplate, and duplicated validation guards create inconsistent behavior and multiply the surface area for bugs. Consolidation is foundational work that makes all subsequent refactoring safer.

**Independent Test**: Can be fully tested by verifying that all call sites for repository resolution, error handling, caching, and validation use the canonical shared helper, and that the previous ad-hoc implementations have been removed.

**Acceptance Scenarios**:

1. **Given** an API endpoint needs to resolve a repository owner and name, **When** repository resolution is invoked, **Then** it uses the single canonical `resolve_repository()` utility with consistent 3-step fallback logic.
2. **Given** an API endpoint catches a service-level error, **When** the error is handled, **Then** it uses the existing `handle_service_error()` or `safe_error_response()` helpers rather than ad-hoc try/log/raise patterns.
3. **Given** an API endpoint needs to fetch data with caching, **When** the fetch is performed, **Then** a single shared `cached_fetch()` helper is used instead of inline cache-check/fetch/cache-set boilerplate.
4. **Given** an API endpoint requires a selected project, **When** the validation runs, **Then** a single `require_selected_project()` guard is used with a consistent error message.
5. **Given** a frontend dialog or modal is displayed, **When** the component renders, **Then** it composes the shared `ConfirmationDialog` base pattern with consistent ARIA attributes, focus handling, responsive overflow behavior, and theme-aligned surface styling.
6. **Given** a frontend component constructs dynamic class names, **When** the class string is built, **Then** the `cn()` utility from `lib/utils` is used instead of template literal concatenation.
7. **Given** a dialog contains long issue descriptions, saved pipeline lists, or validation errors, **When** it is viewed on smaller screens or navigated by keyboard, **Then** the content remains scrollable, the action area stays reachable, and focus visibility is preserved throughout the interaction.

---

### User Story 3 - Break Apart Oversized Files (Priority: P2)

As a developer, I need large monolithic files split into focused modules so that I can navigate, test, and review code changes without dealing with 1,000–5,000 line files that mix unrelated concerns.

**Why this priority**: The backend `github_projects/service.py` (5,150 LOC), frontend `services/api.ts` (1,099 LOC), and several large hooks (375–616 LOC) are difficult to navigate, test individually, and cause frequent merge conflicts. Splitting them improves developer productivity and enables more targeted testing.

**Independent Test**: Can be fully tested by verifying that each extracted module has a focused responsibility, the original file re-exports or delegates to submodules maintaining the same public API, and all existing tests continue to pass.

**Acceptance Scenarios**:

1. **Given** the backend GitHub Projects service, **When** the codebase is inspected, **Then** operations are organized into separate modules for issues, pull requests, Copilot operations, board data, and orchestration, each under 500 lines.
2. **Given** the frontend API service, **When** the codebase is inspected, **Then** API functions are organized into domain-specific modules (projects, chat, agents, tools, board) with a shared client module and a re-export index.
3. **Given** a large frontend hook (e.g., `usePipelineConfig`), **When** the codebase is inspected, **Then** the hook is decomposed into focused sub-hooks (state, mutations, validation) each with a single responsibility.

---

### User Story 4 - Strengthen Type Safety (Priority: P2)

As a developer, I need complete type annotations on all public functions and strict compiler checks enabled so that type errors are caught at build time rather than at runtime.

**Why this priority**: Missing return type hints (24 functions), generic `dict`/`list` returns instead of `TypedDict`, disabled TypeScript strict checks (`noUnusedLocals`, `noUnusedParameters`), and unsafe type casts (`as unknown as Record<string, unknown>`) allow bugs to slip through static analysis. Fixing these provides a safety net for all future code changes.

**Independent Test**: Can be fully tested by running the backend type checker with zero errors on all public API and service functions, running the frontend TypeScript compiler with strict unused checks enabled with zero errors, and verifying that no unsafe casts remain in production code.

**Acceptance Scenarios**:

1. **Given** a public function in the backend services or API layer, **When** the function signature is inspected, **Then** it has an explicit return type annotation (not bare `dict` or `list` but specific types where applicable).
2. **Given** the frontend TypeScript configuration, **When** `noUnusedLocals` and `noUnusedParameters` are enabled, **Then** the project compiles with zero errors (unused parameters are prefixed with `_`).
3. **Given** frontend code that parses dynamic API responses, **When** the response data is accessed, **Then** proper discriminated unions or branded types are used instead of unsafe casts.

---

### User Story 5 - Remove Technical Debt and Legacy Patterns (Priority: P3)

As a developer, I need module-level singletons replaced with dependency injection, anti-patterns removed, migration numbering fixed, in-memory stores migrated to persistent storage, unused dependencies removed, and test directories consolidated so that the codebase follows modern best practices and is easier to test and maintain.

**Why this priority**: 9 global singletons complicate testing, the `__import__()` anti-pattern reduces readability, duplicate migration prefixes risk schema corruption, in-memory chat stores cause data loss on restart, unused dependencies increase bundle size, and split test directories confuse contributors. These are lower-urgency but important for long-term health.

**Independent Test**: Can be fully tested by verifying that (a) no module-level singleton instances remain — all services use DI, (b) no `__import__()` calls exist, (c) migration prefixes are unique, (d) chat history persists across restarts, (e) `jsdom` is not in `package.json`, and (f) only one test directory exists.

**Acceptance Scenarios**:

1. **Given** a backend service that was previously instantiated as a module-level singleton, **When** the service is needed by an endpoint, **Then** it is injected via dependency injection rather than imported as a global instance.
2. **Given** `chores/template_builder.py`, **When** the file is inspected, **Then** it uses standard `import` statements instead of `__import__()`.
3. **Given** the database migration directory, **When** migration file prefixes are listed, **Then** each numeric prefix is unique (no duplicates).
4. **Given** a user sends chat messages and the application restarts, **When** the user returns, **Then** their recent chat history (up to the retention limit) is still available from persistent storage.
5. **Given** the frontend `package.json`, **When** dev dependencies are inspected, **Then** `jsdom` is not listed (only `happy-dom` is used).
6. **Given** the frontend source directory, **When** test directories are listed, **Then** only a single test directory exists.
7. **Given** the backend codebase, **When** TODO/FIXME comments are searched, **Then** all previously identified items have been resolved (converted to tracked issues or fixed inline).

---

### User Story 6 - Improve Performance and Observability (Priority: P3)

As a user, I need the frontend to render efficiently without unnecessary re-computations, HTTP requests to be properly cancelled on navigation, and backend in-memory structures to be bounded so that the application remains responsive and does not leak memory over time.

**Why this priority**: Unmemoized derived data on every render, uncancelled fetch requests on route changes, and unbounded in-memory data structures degrade user experience and can cause memory leaks in long-running sessions. These are important but less urgent than correctness and security.

**Independent Test**: Can be fully tested by profiling render counts to verify memoization, checking that navigating away from a page cancels in-flight requests, and monitoring memory usage to confirm in-memory structures do not grow beyond their cap.

**Acceptance Scenarios**:

1. **Given** a page component that computes derived data (e.g., `stageAgentInfoMap`), **When** the component re-renders without data changes, **Then** the derived computation is not re-executed (memoized).
2. **Given** a user navigates away from a page with an in-flight API request, **When** the route changes, **Then** the pending request is cancelled and no stale state is applied.
3. **Given** an in-memory cache or data store in the backend, **When** new entries are added beyond the size limit, **Then** the oldest entries are evicted to maintain the bounded size.

---

### User Story 7 - Close Testing and Linting Gaps (Priority: P4)

As a developer, I need comprehensive test coverage for backend exception paths, frontend pages/components, and proper linting rules so that regressions are caught automatically and code quality standards are enforced.

**Why this priority**: Broad exception handling masks which exceptions tests should cover, page components are largely untested, only a fraction of hooks are tested, and the linting configuration lacks import ordering and React-specific rules. These are ongoing improvements that build on all prior phases.

**Independent Test**: Can be fully tested by running the test suite and confirming coverage targets are met, running the linter with new plugins enabled and confirming zero violations, and running accessibility tests on critical user paths.

**Acceptance Scenarios**:

1. **Given** a backend service method that can throw specific exception types, **When** tests are run, **Then** each specific exception type has a dedicated test case verifying the error handling behavior.
2. **Given** a frontend page component (e.g., `AgentsPage`, `ProjectsPage`), **When** tests are run, **Then** render tests and accessibility assertions pass for the component.
3. **Given** the frontend linting configuration, **When** the linter is run, **Then** import ordering and React-specific rules are enforced with zero violations.
4. **Given** a chat message region in the UI, **When** a screen reader user receives new messages, **Then** the messages are announced via appropriate ARIA live region attributes.

---

### Edge Cases

- What happens when a narrowed exception type does not cover a previously silently-swallowed error? The `except` block should include a final fallback that logs the unexpected exception at `WARNING` level and re-raises it so it surfaces rather than being silently ignored.
- How does the system handle concurrent cache eviction and fetch in the shared `cached_fetch()` helper? The helper should use atomic operations or locking to prevent race conditions between cache reads, writes, and evictions.
- What happens when the database migration uniqueness check finds a conflict at startup? The application should log a clear error message identifying the conflicting migration prefixes and refuse to start until the conflict is resolved.
- What if splitting a large file breaks circular import dependencies? Each extraction should be validated by running the full import graph to confirm no circular references are introduced.
- What happens when request cancellation occurs after a partial response has been received? The cancellation should be handled gracefully — partial data is discarded and no error is shown to the user for intentional cancellations.
- What happens when a dialog refactor introduces long-form content or many actions on a narrow viewport? The shared modal pattern should preserve scrollable content, visible action buttons, and clear focus styling without causing layout overflow or clipped controls.
- What if enabling strict unused-variable checks reveals code that is actually needed but only accessed dynamically? Such cases should be documented with explicit suppression comments or restructured to avoid dynamic access patterns.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — Silent Failures & Security

- **FR-001**: System MUST log contextual error information (exception type and message) in every `except` block — no `except: pass` handlers may remain in the backend codebase.
- **FR-002**: System MUST bind caught exceptions to a variable and narrow `except Exception` clauses to specific exception types wherever the set of expected exceptions can be determined.
- **FR-003**: System MUST NOT expose internal exception details (stack traces, internal variable names, file paths) in responses sent to external APIs; only generic user-facing messages are returned while full details are logged internally.
- **FR-004**: System MUST restrict CORS allowed methods to an explicit list of HTTP methods actually used by the application (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`).

#### Phase 2 — DRY Consolidation

- **FR-005**: System MUST use a single canonical repository resolution function for all repository owner/name resolution, with all call sites converted and ad-hoc implementations removed.
- **FR-006**: System MUST use the existing error handling utilities from `logging_utils.py` across all API route files, replacing ad-hoc try/log/raise patterns.
- **FR-007**: System MUST provide a shared cache-or-fetch async helper that encapsulates the cache-check, fetch, and cache-set pattern, used by all endpoints requiring cached data.
- **FR-008**: System MUST provide a selected-project validation guard that raises a consistent error when no project is selected, used by all endpoints requiring a selected project.
- **FR-009**: Frontend MUST compose all modal and dialog components using a shared base pattern with consistent ARIA attributes, focus management, responsive overflow handling, and theme-consistent surface styling.
- **FR-010**: Frontend MUST use a single class name utility for all dynamic class name construction, replacing template literal concatenation so shared variant styling remains visually consistent.

#### Phase 3 — Module Decomposition

- **FR-011**: Backend GitHub Projects service MUST be split into focused submodules (issues, pull requests, Copilot operations, board data, orchestration) with no individual file exceeding 500 lines of code.
- **FR-012**: Frontend API service MUST be split into domain-specific modules (client, projects, chat, agents, tools, board) with a re-export index maintaining backward compatibility.
- **FR-013**: Frontend hooks exceeding 400 lines of code MUST be decomposed into focused sub-hooks with single responsibilities.

#### Phase 4 — Type Safety

- **FR-014**: All public functions in backend services and API layers MUST have explicit return type annotations, with structured types used instead of generic dictionary/list returns for structured data.
- **FR-015**: Frontend build configuration MUST enable strict unused-variable and unused-parameter checks, with all resulting errors resolved.
- **FR-016**: Frontend MUST replace all unsafe type casts for dynamic API responses with properly defined discriminated unions or branded types.

#### Phase 5 — Technical Debt Removal

- **FR-017**: All module-level singleton service instances MUST be replaced with proper dependency injection patterns.
- **FR-018**: The `__import__()` anti-pattern MUST be replaced with standard import statements.
- **FR-019**: All database migration file prefixes MUST be unique; duplicate prefixes MUST be renumbered.
- **FR-020**: Chat message history MUST be persisted to durable storage with bounded retention (configurable, default 1,000 messages per session).
- **FR-021**: Frontend MUST remove unused test framework dependencies that duplicate the active test environment.
- **FR-022**: Frontend test files MUST be consolidated into a single test directory.
- **FR-023**: All existing TODO/FIXME comments tagged for remediation MUST be resolved (fixed inline or converted to tracked issues).

#### Phase 6 — Performance & Observability

- **FR-024**: Frontend page components MUST memoize expensive derived computations and wrap pure child components for render optimization.
- **FR-025**: Frontend API layer MUST support request cancellation via abort signals, integrated with the data-fetching library's signal mechanism.
- **FR-026**: All backend in-memory data structures (caches, stores) MUST have an explicit maximum size with eviction policy.

#### Phase 7 — Testing & Linting

- **FR-027**: Backend test suite MUST include specific test cases for each narrowed exception type introduced in Phase 1.
- **FR-028**: Frontend test suite MUST include render tests for all page components and accessibility assertions for critical user paths.
- **FR-029**: Frontend linting configuration MUST include import ordering and React-specific checking rules.
- **FR-030**: Frontend chat message regions MUST include appropriate ARIA live region attributes for screen reader support of real-time updates.

### Key Entities

- **Exception Handler**: A try/except block with its caught exception type, bound variable, and recovery action (log, propagate, or return).
- **Repository Resolution**: The canonical function that resolves repository owner and name from request parameters, session state, or configuration with a defined fallback order.
- **Cached Fetch Helper**: A reusable async function that takes a cache key, fetch function, and refresh flag, returning cached or freshly fetched data.
- **Validation Guard**: A reusable function that checks a precondition (e.g., selected project exists) and raises a consistent error if not met.
- **Service Module**: A focused backend file containing operations for a single domain (issues, pull requests, board, etc.) with a clear public API.
- **Chat Message Store**: A persistent storage mechanism for chat messages with bounded retention and session-scoped access.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero `except: pass` handlers remain in the backend codebase — every exception handler logs or propagates with context.
- **SC-002**: Zero instances of internal exception details (stack traces, file paths) appearing in responses to external APIs.
- **SC-003**: CORS configuration explicitly lists only the HTTP methods used by the application.
- **SC-004**: Repository resolution uses a single canonical function across all call sites — no duplicate implementations remain.
- **SC-005**: Error handling helpers are actively used in all API route files — no ad-hoc try/log/raise patterns remain.
- **SC-006**: No backend file exceeds 500 lines of code after module decomposition.
- **SC-007**: No frontend service or hook file exceeds 400 lines of code after decomposition.
- **SC-008**: 100% of public functions in backend services and API layers have explicit return type annotations.
- **SC-009**: Frontend compiles cleanly with strict unused-variable and unused-parameter checks enabled.
- **SC-010**: Zero unsafe type casts for dynamic API responses remain in frontend production code.
- **SC-011**: Chat history survives application restarts — users can retrieve their recent messages after a restart.
- **SC-012**: All backend in-memory data structures enforce a configurable maximum size.
- **SC-013**: Frontend bundle analysis tooling is integrated into the build pipeline.
- **SC-014**: Backend test suite achieves specific exception-type coverage for all narrowed exception handlers.
- **SC-015**: Frontend test coverage reaches 70% or higher for components and pages.
- **SC-016**: All page components and critical user paths pass accessibility assertions.
- **SC-017**: Dialogs and modals touched by the initiative preserve consistent focus visibility, responsive overflow handling, and theme-aligned surface treatment across desktop and narrow viewports.

## Assumptions

- The existing `resolve_repository()` utility implements the correct 3-step fallback logic and can serve as the single canonical implementation without modification.
- The existing `handle_service_error()` and `safe_error_response()` utilities are correctly implemented and suitable for adoption across all API routes.
- The `ConfirmationDialog` component is the most complete and accessible modal implementation and is a suitable base for composition.
- SQLite is the appropriate persistent storage for chat messages given the existing use of SQLite for other application data.
- The `happy-dom` test environment is the correct and preferred choice over `jsdom`.
- The bounded retention of 1,000 messages per session for chat storage is a reasonable default that balances storage with user needs.
- Data retention follows industry-standard practices for the application domain.
- Performance targets assume standard web application expectations (sub-second interactions) unless specific metrics are stated.
- The 500 LOC file size threshold for backend and 400 LOC for frontend hooks are guidelines that may be exceeded when a file has a tightly cohesive single responsibility.
