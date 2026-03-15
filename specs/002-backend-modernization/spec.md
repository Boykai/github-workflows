# Feature Specification: Backend Modernization & Improvement

**Feature Branch**: `002-backend-modernization`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Plan: Backend Modernization & Improvement"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Safe Application Shutdown with No Resource Leaks (Priority: P1)

As a system operator, when the backend application shuts down (planned or unplanned), all background tasks are properly cancelled or completed, and no resources (WebSocket connections, database handles, async tasks) are left in an undefined state. Today, background tasks created at startup leak on shutdown because they are cancelled but never awaited. Fire-and-forget tasks across the codebase are entirely untracked. A hung external API call can block the event loop indefinitely.

**Why this priority**: Resource leaks and hung tasks cause cascading failures, data loss, and make the system unreliable under real-world conditions. This is the highest-priority issue because it blocks safe operation and is a prerequisite for data integrity improvements.

**Independent Test**: Can be fully tested by triggering a graceful shutdown and verifying that all background tasks complete or cancel within a bounded time, all WebSocket connections are closed, and no "task was destroyed but it is pending" warnings appear in logs.

**Acceptance Scenarios**:

1. **Given** the application is running with active background tasks (polling, cleanup, signal bridge), **When** a shutdown signal (SIGTERM/SIGINT) is received, **Then** all background tasks complete or cancel within 30 seconds and no resource leak warnings appear in logs
2. **Given** a fire-and-forget task is created anywhere in the codebase, **When** the task is created, **Then** it is registered in a central task registry that tracks its lifecycle
3. **Given** an external API call (e.g., GitHub GraphQL) is in progress, **When** the remote server becomes unresponsive, **Then** the call times out within a configured duration (e.g., 30 seconds) rather than blocking indefinitely
4. **Given** the Signal WebSocket connection encounters a non-timeout error during message processing, **When** the error occurs, **Then** the WebSocket is properly closed, and reconnection attempts use exponential backoff rather than busy-looping

---

### User Story 2 - Reliable Data Persistence with No Silent Data Loss (Priority: P1)

As a user of the chat system, when I send messages, create proposals, or receive recommendations, my data is reliably persisted and survives application restarts. Today, in-memory dictionaries serve as the primary data store with the database as a fire-and-forget secondary — if persistence fails, data is silently lost on restart. Multi-step database operations can leave data in an inconsistent state because there are no transaction boundaries.

**Why this priority**: Data loss directly impacts users. Silent persistence failures mean users believe their data is saved when it is not, leading to trust erosion and operational issues.

**Independent Test**: Can be fully tested by sending chat messages, forcing a persistence failure (e.g., disk full simulation), verifying the system reports the failure, then restarting the application and confirming all successfully persisted data is restored.

**Acceptance Scenarios**:

1. **Given** a user sends a chat message, **When** the message is saved, **Then** the database is the authoritative source of truth and the in-memory cache is updated from the database
2. **Given** a database write fails (e.g., disk full, locked database), **When** the persistence operation encounters an error, **Then** the error is surfaced to the caller (not silently swallowed) and a retry mechanism attempts to recover
3. **Given** a multi-step database operation is in progress (e.g., updating chat state and related metadata), **When** one step fails, **Then** the entire operation is rolled back to maintain consistency
4. **Given** two concurrent requests both attempt to auto-promote a user to admin when no admin exists, **When** processed simultaneously, **Then** exactly one request succeeds and the other receives an appropriate response indicating an admin already exists

---

### User Story 3 - Hardened Security Posture (Priority: P2)

As a system administrator, the backend has defense-in-depth security measures protecting against common web vulnerabilities. Today, there is no CSRF protection on state-changing endpoints, rate limiting can be trivially bypassed by clearing cookies, cache keys can collide across different projects, and critical database columns lack indexes (which also impacts query performance and could enable denial-of-service through slow queries).

**Why this priority**: Security gaps can be exploited to compromise user data and system integrity. While not causing immediate data loss like P1 issues, they represent significant risk that should be addressed promptly.

**Independent Test**: Can be fully tested by: (1) attempting a CSRF attack on a state-changing endpoint and verifying it is blocked, (2) verifying rate limiting persists after clearing cookies, (3) confirming that two different projects with the same issue number return different cached data.

**Acceptance Scenarios**:

1. **Given** a state-changing request (POST, PUT, DELETE), **When** the request lacks a valid CSRF token, **Then** the request is rejected with an appropriate error
2. **Given** a user clears their session cookie, **When** they continue making requests, **Then** rate limiting still applies based on a secondary identifier (user ID or IP address)
3. **Given** two projects each have an issue numbered #42, **When** cached data is retrieved for issue #42, **Then** each project receives its own correct cached data (no cross-project collision)
4. **Given** frequently queried database columns (admin user ID, selected project ID, chat status), **When** queries filter by these columns, **Then** queries use indexes and complete within expected performance bounds

---

### User Story 4 - Responsive System Under Load (Priority: P2)

As a user with a large volume of chat history and project data, the system responds quickly to my requests even when there are thousands of records. Today, endpoints can return unbounded result sets (100K+ rows), a polling startup performs a full table scan, metadata caches are stale for too long, and evicted background tasks are silently dropped without cleanup.

**Why this priority**: Performance issues directly affect user experience and can cause timeouts, memory pressure, and degraded responsiveness. These are addressable in parallel with security work.

**Independent Test**: Can be fully tested by requesting a paginated chat message endpoint and verifying it returns exactly the requested number of results, and by verifying metadata (branches, labels) refreshes within 5 minutes of external changes.

**Acceptance Scenarios**:

1. **Given** a user requests chat messages, **When** the endpoint is called with `limit=5&offset=0`, **Then** exactly 5 results are returned in the response
2. **Given** the application starts and initializes polling, **When** project settings are loaded, **Then** only projects with valid workflow configuration are queried (not a full table scan)
3. **Given** a repository branch is created or deleted, **When** the metadata cache is checked after 5 minutes, **Then** the updated branch list is reflected
4. **Given** a bounded task collection reaches capacity, **When** the oldest task is evicted, **Then** the evicted task is explicitly cancelled before removal (not silently dropped)

---

### User Story 5 - Maintainable Codebase with Modern Python Patterns (Priority: P3)

As a developer maintaining the backend, the codebase uses modern Python patterns (enums, protocols, typed dicts, consistent error handling) that make it easier to understand, extend, and catch bugs at development time. Today, string constants are used where enums would prevent typos, service interfaces lack formal protocols, untyped dictionaries obscure data shapes, error handling is inconsistent, and some sync-heavy work blocks the async event loop.

**Why this priority**: Code quality improvements reduce long-term maintenance cost and bug risk, but do not address immediate operational issues. These are best tackled after critical safety and reliability fixes.

**Independent Test**: Can be fully tested by running static analysis (type checker, linter) and verifying no type errors or pattern violations are reported for modernized modules, and by verifying that CPU-bound operations do not block the event loop.

**Acceptance Scenarios**:

1. **Given** a service uses string constants for status or type values, **When** the module is modernized, **Then** all such constants are replaced with enum types and existing call sites are updated
2. **Given** a service depends on another service's interface, **When** the dependency is declared, **Then** it references a formal Protocol type rather than a concrete implementation
3. **Given** configuration or metadata is passed as an untyped dictionary, **When** the code is modernized, **Then** the dictionary is replaced with a TypedDict that documents expected keys and value types
4. **Given** an error occurs in a service method, **When** the error is handled, **Then** it uses the standardized error handling decorator consistently across all services
5. **Given** a CPU-bound synchronous operation runs in an async context, **When** the operation executes, **Then** it is offloaded to a thread pool to avoid blocking the event loop
6. **Given** the session cleanup loop encounters an error and then recovers, **When** the next successful iteration runs, **Then** the backoff timer is reset to its base value

---

### Edge Cases

- What happens when the task registry receives a shutdown signal while new tasks are still being submitted?
- How does the system behave when the database file is corrupted or inaccessible at startup?
- What happens when the GitHub API returns rate-limit (429) responses during a timeout-guarded call?
- How does exponential backoff behave when the Signal WebSocket server is down for an extended period (hours)?
- What happens when two concurrent admin promotion attempts race with the database lock?
- How does pagination behave when the offset exceeds the total number of records?
- What happens if a CSRF token expires mid-session during a long-running user interaction?
- How does cache invalidation handle rapid successive changes to the same resource?

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1: Critical Async Safety**

- **FR-001**: System MUST use structured task groups for lifecycle-managed background tasks at application startup, ensuring all tasks are automatically cancelled and awaited on shutdown
- **FR-002**: System MUST provide a central task registry that tracks all fire-and-forget tasks created via `asyncio.create_task()`, supports graceful draining on shutdown, and logs any tasks that fail to complete within the drain timeout
- **FR-003**: System MUST enforce timeout guards on all external API calls (GitHub GraphQL, third-party HTTP requests) to prevent indefinite event loop blocking
- **FR-004**: System MUST properly close WebSocket connections on any error (not just timeout errors) and use exponential backoff with a configurable maximum delay for reconnection attempts

**Phase 2: Data Integrity & Persistence**

- **FR-005**: System MUST use the database as the single source of truth for chat messages, proposals, and recommendations, with in-memory structures serving only as a read cache
- **FR-006**: System MUST surface persistence failures to callers rather than silently swallowing exceptions, and MUST implement a retry mechanism for transient failures
- **FR-007**: System MUST wrap multi-step database operations in explicit transactions with rollback capability to prevent partial state updates
- **FR-008**: System MUST prevent race conditions in admin auto-promotion by using atomic database operations or locking to ensure exactly one user is promoted

**Phase 3: Security Hardening**

- **FR-009**: System MUST validate a CSRF token on all state-changing HTTP methods (POST, PUT, DELETE)
- **FR-010**: System MUST include database indexes on frequently queried columns: admin user ID on global settings, selected project ID on user sessions, and status fields on chat tables
- **FR-011**: System MUST scope cache keys to include project identification so that identically numbered issues or PRs from different projects are cached independently
- **FR-012**: System MUST use a compound key for rate limiting that combines authenticated user identity with IP address as a fallback, so that clearing session cookies does not bypass rate limits

**Phase 4: Performance Optimization**

- **FR-013**: System MUST filter project settings queries to only load records with valid workflow configuration, avoiding full table scans at startup, and MUST handle malformed configuration data gracefully
- **FR-014**: System MUST support pagination on all list endpoints (chat messages, tasks) with configurable `limit` (default 50, maximum 200) and `offset` query parameters
- **FR-015**: System MUST reduce metadata cache time-to-live for frequently changing data (branches, labels) to 5 minutes or support event-driven cache invalidation
- **FR-016**: System MUST explicitly cancel evicted tasks in bounded collections before removing them, rather than silently dropping references

**Phase 5: Modern Python Patterns**

- **FR-017**: System MUST replace string-based constants with enum types in cleanup service and model files
- **FR-018**: System MUST define Protocol types for key service interfaces to enable loose coupling and easier testing
- **FR-019**: System MUST use TypedDict for untyped dictionary structures used in rate-limit information and configuration parsing
- **FR-020**: System MUST apply the standardized error handling decorator consistently across all service modules
- **FR-021**: System MUST offload CPU-bound synchronous work to thread pools when running in an async context
- **FR-022**: System MUST reset backoff timers to base values after successful recovery in retry/cleanup loops

### Key Entities *(include if feature involves data)*

- **TaskRegistry**: A centralized registry that tracks all background and fire-and-forget async tasks, supports graceful shutdown draining, and provides observability into task lifecycle states (pending, running, completed, cancelled, failed)
- **ChatMessage / Proposal / Recommendation**: Core chat data entities that must be persisted reliably to the database as the single source of truth, with in-memory caching for performance
- **GlobalSettings**: System-wide configuration entity including admin user identification, requiring indexed lookups and race-condition-safe promotion logic
- **UserSession**: Per-user session entity tracking selected project and authentication state, requiring indexed queries for performance
- **CacheEntry**: Cached metadata (branches, labels, issue/PR data) scoped by project to prevent cross-project collisions, with configurable TTL
- **RateLimitRecord**: Rate limiting state keyed by compound identifier (user ID + IP fallback) rather than session cookie alone

### Assumptions

- The application runs on Python 3.12+ (TaskGroup available since 3.11)
- SQLite remains the database backend; no migration to PostgreSQL is planned
- The application is single-instance (no Redis or distributed cache needed)
- Frontend, Docker configuration, CI/CD pipelines, and Signal sidecar are out of scope
- Existing test infrastructure (~50 unit tests) will be extended but not replaced
- The `handle_github_errors()` decorator in `logging_utils.py` is the established pattern for standardized error handling
- The `RUF006` ruff suppression will be removed after the TaskRegistry is implemented
- Exponential backoff maximum delay defaults to a reasonable ceiling (e.g., 5 minutes) unless otherwise specified
- CSRF protection follows standard double-submit cookie or synchronizer token pattern
- Cache TTL reduction to 5 minutes is the initial approach; webhook-driven invalidation is a future enhancement option

### Dependencies

- Python 3.12+ runtime (for `asyncio.TaskGroup` and modern async features)
- Existing FastAPI framework and middleware stack
- Existing SQLite database and `aiosqlite` async driver
- Existing `httpx` HTTP client library (for timeout configuration)
- Existing `ruff` linter (for verification of async safety rules)

### Scope Boundaries

**In Scope:**
- All 5 phases (async safety, data integrity, security hardening, performance optimization, modern patterns) as described in the 20 steps
- Backend Python code only
- SQLite transaction discipline improvements
- In-memory cache improvements (TTL, scoping, invalidation)

**Out of Scope:**
- Frontend changes
- Docker configuration changes
- CI/CD pipeline changes
- Signal sidecar modifications
- Migration to PostgreSQL or Redis
- Circuit breaker implementation (recommended as follow-up)
- Test coverage gate in CI (recommended as separate task)
- Deep structured logging audit (lightly addressed in Phase 5)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On application shutdown, all tracked background tasks complete or cancel within 30 seconds, with zero "task was destroyed but it is pending" warnings in logs
- **SC-002**: After linter rule enforcement (async safety rules), zero violations are reported for untracked task creation across the entire codebase
- **SC-003**: External API calls time out and return a meaningful error within 30 seconds of the remote endpoint becoming unresponsive
- **SC-004**: WebSocket reconnection after a connection failure uses exponential backoff, with no reconnection attempts occurring faster than 1 second apart
- **SC-005**: Chat data survives application restart with zero data loss for all successfully acknowledged operations
- **SC-006**: When 10 concurrent requests attempt admin auto-promotion simultaneously, exactly one succeeds and the remaining 9 receive a consistent non-error response
- **SC-007**: CSRF-protected endpoints reject 100% of requests lacking valid tokens, returning appropriate error responses
- **SC-008**: Rate limiting remains effective regardless of session cookie state — users cannot exceed rate limits by clearing cookies
- **SC-009**: Two different projects with identically numbered issues return distinct, correct cached data with zero cross-project cache collisions
- **SC-010**: Paginated endpoints return the exact number of requested results (e.g., `limit=5` returns exactly 5 items when sufficient data exists), with correct offset behavior
- **SC-011**: Application startup queries for polling load only relevant project settings (not full table scans), completing within expected time bounds
- **SC-012**: Branch and label metadata reflects external changes within 5 minutes of the change occurring
- **SC-013**: Static analysis (type checker, linter) reports zero type errors or pattern violations in modernized modules after Phase 5 changes
- **SC-014**: CPU-bound operations in async contexts do not block the event loop for more than 100 milliseconds
