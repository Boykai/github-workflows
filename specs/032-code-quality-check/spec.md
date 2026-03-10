# Feature Specification: Code Quality Check

**Feature Branch**: `032-code-quality-check`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Code Quality Check — Fix silent failures, security leaks, DRY violations, god files, type safety gaps, technical debt, performance issues, and testing gaps across the full-stack codebase."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Fix Silent Failures and Security Vulnerabilities (Priority: P0)

As a developer maintaining the backend, I need all error-handling paths to log meaningful context and never silently swallow exceptions, so that runtime bugs are immediately visible in logs and internal error details are never leaked to external consumers.

**Why this priority**: Silent exception swallowing hides production bugs — developers cannot diagnose issues they cannot see. Exception detail leaks expose internal system information to external consumers, creating a security vulnerability. Overly permissive CORS settings widen the attack surface. These are the highest-urgency items because they affect system reliability and security right now.

**Independent Test**: Can be fully tested by running the existing backend test suite after modifying exception-handling blocks, then verifying that (a) log output contains contextual error messages where `pass` previously existed, (b) external-facing error responses contain only generic messages, and (c) CORS configuration restricts allowed methods to those actually used.

**Acceptance Scenarios**:

1. **Given** a backend service encounters an error in any previously silent `except: pass` block, **When** the exception is raised at runtime, **Then** a contextual log message is emitted at an appropriate level (debug, warning, or error) instead of being silently discarded.
2. **Given** a backend service catches an exception near an external-facing boundary, **When** the error response is sent, **Then** the response contains a generic user-safe message and the internal exception details are logged server-side only.
3. **Given** the backend CORS configuration, **When** a cross-origin request is made with an unusual HTTP method not used by the application, **Then** the request is rejected by CORS policy.
4. **Given** a bare `except Exception:` block without `as e`, **When** the code is audited, **Then** every such block is narrowed to specific exception types relevant to the operation being guarded.

---

### User Story 2 — Eliminate Duplicated Code Patterns (Priority: P1)

As a developer working on backend endpoints, I need duplicated patterns — repository resolution, error handling, cache-or-fetch, and validation guards — consolidated into shared helpers, so that bug fixes and behavior changes are applied in one place rather than scattered across dozens of inconsistent copies.

**Why this priority**: Duplicated logic is the most common source of inconsistency bugs. When a fix is applied to one copy but not the others, behavior diverges silently. Consolidation reduces lines of code by 300+ and ensures uniform behavior across all endpoints.

**Independent Test**: Can be fully tested by verifying that each consolidated helper produces identical behavior to the original inline copies, using existing endpoint tests to confirm no regressions. New unit tests for each helper validate the canonical behavior.

**Acceptance Scenarios**:

1. **Given** an endpoint that resolves repository owner and name, **When** the resolution logic executes, **Then** it uses the single canonical resolution function with the full multi-step fallback, and no duplicate resolution logic exists elsewhere.
2. **Given** an endpoint that catches and logs a service error, **When** the error occurs, **Then** the existing error-handling helper is called instead of ad-hoc try/log/raise code.
3. **Given** an endpoint that needs cached data, **When** a cache miss occurs, **Then** the shared cache-or-fetch helper fetches, caches, and returns the data using a single reusable pattern.
4. **Given** an endpoint that requires a selected project, **When** no project is selected in the session, **Then** a shared validation guard raises a consistent error message.

---

### User Story 3 — Break Apart Oversized Files (Priority: P2)

As a developer navigating the codebase, I need large monolithic files (5,000+ lines in backend, 1,000+ lines in frontend) split into focused, single-responsibility modules, so that I can find relevant code quickly, reduce merge conflicts, and test components in isolation.

**Why this priority**: Oversized files slow down code comprehension, increase merge conflict frequency, and make targeted testing difficult. Splitting them is the highest-impact structural improvement, though it requires careful extraction to preserve behavior.

**Independent Test**: Can be fully tested by verifying that all existing tests pass after extraction, that each new module has clear boundaries, and that import paths resolve correctly throughout the application.

**Acceptance Scenarios**:

1. **Given** the backend GitHub projects service file exceeds 5,000 lines, **When** the file is refactored, **Then** it is split into focused submodules (issues, pull requests, agent assignment, board data, orchestration facade) each under 500 lines, with a facade module preserving the existing public interface.
2. **Given** the frontend API service file exceeds 1,000 lines, **When** the file is refactored, **Then** it is split into domain-specific modules (client, projects, chat, agents, tools, board) with a re-export index preserving existing import paths.
3. **Given** frontend hooks that exceed 375 lines and mix concerns, **When** the hooks are refactored, **Then** each hook is decomposed into sub-hooks with clear single responsibilities (state, mutations, validation).

---

### User Story 4 — Strengthen Type Safety (Priority: P2)

As a developer writing new features, I need all public functions to have complete type annotations and the frontend to enforce strict unused-variable checks, so that type errors are caught at compile time rather than at runtime.

**Why this priority**: Missing type annotations allow entire categories of bugs to reach production. Strict compiler checks eliminate dead code accumulation. Combined with the structural improvements in Story 3, this creates a codebase where the compiler catches most mistakes before code review.

**Independent Test**: Can be fully tested by running the type checker (backend) and compiler (frontend) with strict settings and confirming zero errors, then verifying that previously untyped functions now have full annotations.

**Acceptance Scenarios**:

1. **Given** a public backend function that returns data, **When** the function signature is inspected, **Then** it includes a specific return type annotation (not bare `dict` or `list`).
2. **Given** the frontend compiler configuration, **When** strict unused-variable checks are enabled, **Then** the codebase compiles with zero errors and unused variables are either removed or prefixed with `_`.
3. **Given** frontend code that uses unsafe type casts for dynamic data, **When** the cast is replaced, **Then** proper typed interfaces or discriminated unions describe the data shape.

---

### User Story 5 — Remove Technical Debt and Legacy Patterns (Priority: P3)

As a developer maintaining the system long-term, I need module-level singletons replaced with proper dependency injection, anti-patterns removed, migration numbering conflicts resolved, in-memory stores migrated to persistent storage, unused dependencies removed, and test directories consolidated, so that the codebase follows modern best practices and is straightforward to test and extend.

**Why this priority**: Technical debt items individually are manageable, but collectively they create friction across every development task. Dependency injection improves testability. Persistent chat storage prevents data loss. Cleaning up unused dependencies and consolidating test structure reduces confusion for new contributors.

**Independent Test**: Can be fully tested by running the full test suite after each change, verifying that singleton replacements use the application's dependency injection mechanism, that chat messages persist across restarts, and that no build or test regressions occur.

**Acceptance Scenarios**:

1. **Given** a service previously accessed via module-level singleton, **When** the service is needed in a request handler, **Then** it is obtained through the application's dependency injection mechanism.
2. **Given** the chat history for a user session, **When** the application restarts, **Then** the most recent messages (up to a bounded limit) are still available.
3. **Given** the frontend dependency manifest, **When** dependencies are audited, **Then** no unused packages remain installed.
4. **Given** the test file structure, **When** a developer looks for test utilities, **Then** there is exactly one canonical test directory.

---

### User Story 6 — Improve Frontend Performance and Observability (Priority: P3)

As an end user of the application, I need pages to render efficiently without unnecessary recomputation, network requests to be cancelled when I navigate away, and in-memory data structures to be bounded, so that the application remains responsive and does not consume unbounded memory.

**Why this priority**: Performance and memory issues degrade user experience over time. While not immediately critical, they compound as usage grows. Memoization, request cancellation, and bounded caches are standard practices that prevent future incidents.

**Independent Test**: Can be fully tested by profiling render counts before and after memoization changes, verifying that navigating away from a page cancels pending requests, and confirming that in-memory stores reject entries beyond their configured maximum.

**Acceptance Scenarios**:

1. **Given** a page with expensive derived data, **When** the page re-renders due to unrelated state changes, **Then** the derived data is not recomputed.
2. **Given** a pending network request on the current page, **When** the user navigates to a different page, **Then** the pending request is cancelled.
3. **Given** an in-memory cache or store, **When** the number of entries exceeds the configured maximum, **Then** the oldest entries are evicted to maintain the bound.

---

### User Story 7 — Expand Test Coverage and Linting (Priority: P4)

As a team maintaining the codebase, we need comprehensive tests for each specific exception type in backend services, render tests for all frontend pages, accessibility assertions on critical user paths, and enhanced linting rules for import ordering, so that regressions are caught early and code quality standards are enforced automatically.

**Why this priority**: Testing and linting are ongoing investments. They are lower urgency than the structural and security fixes but are essential for long-term maintainability. Each phase of work above should ship with corresponding test updates.

**Independent Test**: Can be fully tested by measuring code coverage before and after, running accessibility audit tools against rendered components, and verifying that linting rules catch import ordering violations.

**Acceptance Scenarios**:

1. **Given** a backend service method with narrowed exception handling, **When** specific exception types are triggered in tests, **Then** each exception type is covered by at least one test case.
2. **Given** a frontend page component, **When** the component is rendered in a test, **Then** it renders without errors and passes accessibility assertions.
3. **Given** the frontend linting configuration, **When** imports are unordered in a source file, **Then** the linter reports a violation.

---

### Edge Cases

- What happens when a refactored module's public interface is imported by external scripts or CI tooling outside the main application? All existing public exports must be preserved through re-export facades.
- How does the system handle the transition period where both old singleton patterns and new dependency injection coexist? A phased migration ensures backward compatibility until all callers are updated.
- What happens when narrowing a broad `except Exception` removes handling for an exception type that actually occurs in production? Each narrowed block must be accompanied by a test that exercises the specific exception types, and a catch-all fallback must remain at the outermost boundary to prevent unhandled crashes.
- How does persistent chat storage handle migration from in-memory to database for sessions that are currently active? Active sessions should write-through to persistent storage; on restart, the system loads from the database.
- What happens when splitting large files if circular import dependencies are introduced? Module extraction must follow a strict dependency direction (shared utilities → domain modules → facade), verified by import cycle detection in CI.
- What happens if enabling strict unused-variable checks reveals hundreds of violations? A staged approach handles violations file-by-file, with a tracking mechanism to ensure all files are addressed.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1: Critical — Fix Silent Failures and Security

- **FR-001**: The system MUST log a contextual message (including exception type and relevant operation context) for every exception that was previously silently discarded via `except: pass` blocks.
- **FR-002**: The system MUST narrow all bare `except Exception:` blocks to specific exception types appropriate to the operation being guarded.
- **FR-003**: The system MUST NOT expose internal exception messages, stack traces, or system details in any response sent to external consumers.
- **FR-004**: The system MUST restrict cross-origin resource sharing to only the HTTP methods actively used by the application.

#### Phase 2: DRY — Consolidate Duplicated Patterns

- **FR-005**: The system MUST use a single canonical function for resolving repository owner and name, with no duplicate resolution logic in any other module.
- **FR-006**: The system MUST use existing shared error-handling helpers for all endpoint error responses, with no ad-hoc try/catch/log/raise patterns.
- **FR-007**: The system MUST provide a reusable cache-or-fetch helper that encapsulates the cache-check, fetch, and cache-set pattern.
- **FR-008**: The system MUST provide a shared validation guard for requiring a selected project, producing a consistent error message across all endpoints.
- **FR-009**: The frontend MUST use a single base dialog/modal component pattern for all modal interactions, with consistent accessibility attributes.
- **FR-010**: The frontend MUST use the shared class-name composition utility for all dynamic class name construction.

#### Phase 3: Break Apart Oversized Files

- **FR-011**: No single source file in the backend MUST exceed 500 lines of code after refactoring, with functionality split into focused single-responsibility modules.
- **FR-012**: No single source file in the frontend MUST exceed 500 lines of code after refactoring, with functionality split into domain-specific modules.
- **FR-013**: All refactored modules MUST preserve the existing public interface through re-export facades, ensuring zero breaking changes to callers.

#### Phase 4: Type Safety and Strictness

- **FR-014**: All public backend functions MUST have complete return type annotations using specific types rather than generic containers.
- **FR-015**: The frontend compiler MUST enforce unused-variable and unused-parameter checks with zero violations.
- **FR-016**: The frontend MUST NOT use unsafe type casting patterns for dynamic data; proper typed interfaces MUST describe all data shapes.

#### Phase 5: Technical Debt Removal

- **FR-017**: All service instances MUST be obtained through the application's dependency injection mechanism, with no module-level singleton patterns.
- **FR-018**: The system MUST NOT use dynamic import anti-patterns where standard imports suffice.
- **FR-019**: Database migration numbering MUST be unique across all migration files, with an automated check to prevent future conflicts.
- **FR-020**: Chat message history MUST be persisted to durable storage with bounded retention, surviving application restarts.
- **FR-021**: The frontend MUST NOT include unused dependencies in its package manifest.
- **FR-022**: The frontend MUST have exactly one canonical test utility directory.
- **FR-023**: All TODO and FIXME comments tagged with security or bug identifiers MUST be resolved (fixed inline or converted to tracked issues).

#### Phase 6: Performance and Observability

- **FR-024**: The frontend MUST memoize expensive derived computations to prevent unnecessary recalculation on unrelated re-renders.
- **FR-025**: The frontend MUST cancel pending network requests when the user navigates away from the initiating page.
- **FR-026**: All in-memory caches and stores in the backend MUST enforce a maximum size with eviction of oldest entries when the limit is reached.
- **FR-027**: The frontend build MUST include bundle size analysis output for tracking in continuous integration.

#### Phase 7: Testing and Linting

- **FR-028**: Backend tests MUST cover each specific exception type in service methods that have narrowed exception handling.
- **FR-029**: All frontend page components MUST have render tests that verify successful rendering and pass accessibility assertions.
- **FR-030**: The frontend linting configuration MUST enforce import ordering rules and include checks for common accessibility patterns.

### Assumptions

- The existing backend test suite provides adequate baseline coverage to detect regressions from refactoring (as indicated by the 53 unit test files currently present).
- The existing frontend test infrastructure (Vitest with happy-dom) is the standard for new tests; no additional test framework is needed.
- The application's dependency injection mechanism is available and documented (the framework's built-in DI pattern).
- Migration to persistent chat storage can use the existing database infrastructure (currently up to migration 020).
- The 500-line file size guideline applies to source files, not generated or configuration files.
- Bundle analysis output is intended for CI reporting and does not block builds.
- "External consumers" in FR-003 includes any API or messaging integration that sends responses outside the application boundary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero silent exception blocks remain in the backend — every `except` block either handles, logs, or propagates the exception with context (measured by static analysis scan).
- **SC-002**: Zero instances of internal error details appearing in external-facing responses (verified by security audit of all response paths).
- **SC-003**: Total lines of duplicated code reduced by at least 300 lines through consolidation of repository resolution, error handling, caching, and validation patterns.
- **SC-004**: No backend source file exceeds 500 lines of code; the largest backend service file is reduced from 5,150 lines to five or fewer focused modules.
- **SC-005**: No frontend source file exceeds 500 lines of code; the largest frontend service file is split into domain-specific modules.
- **SC-006**: 100% of public backend functions have specific return type annotations (not bare `dict` or `list`).
- **SC-007**: Frontend compiles cleanly with strict unused-variable and unused-parameter checks enabled.
- **SC-008**: Zero module-level singleton patterns remain; all services are obtained via dependency injection.
- **SC-009**: Chat message history survives application restarts, with the most recent 1,000 messages per session persisted.
- **SC-010**: Frontend page components achieve at least 70% test coverage with accessibility assertions on critical user paths.
- **SC-011**: All existing tests continue to pass after each phase of refactoring (zero regressions).
- **SC-012**: In-memory caches and stores enforce maximum size limits, verified by tests that exceed the limit and confirm eviction.
- **SC-013**: All security-tagged TODO/FIXME comments are resolved (fixed or converted to tracked issues with owners assigned).
