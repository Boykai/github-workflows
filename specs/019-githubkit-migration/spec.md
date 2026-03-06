# Feature Specification: Simplify GitHub Service with githubkit — Replace Hand-Rolled Integration

**Feature Branch**: `019-githubkit-migration`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Simplify GitHub Service with githubkit v0.14.6: Replace Hand-Rolled httpx Integration (~1,500–2,000 LOC Reduction)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Zero-Regression Backend Migration (Priority: P1)

As a backend engineer, I want the GitHub service to use a modern, maintained SDK so that all existing externally observable behavior — OAuth login, project listing, issue creation, Copilot assignment, PR review requests, branch deletion, sub-issue management, and polling — remains identical before and after the migration, with no user-facing changes.

**Why this priority**: This is the foundation of the entire effort. If any existing behavior regresses, the migration has failed regardless of how much code it removes. Every other story depends on behavioral equivalence.

**Independent Test**: Can be fully tested by running the full existing automated test suite (all 1,400+ tests) and executing a manual smoke test of the critical path: OAuth login → list projects → create issue → assign Copilot → poll status → completion. If all pass with no regressions, this story is satisfied.

**Acceptance Scenarios**:

1. **Given** the current system passes all automated tests, **When** the migration is complete, **Then** all existing automated tests pass with updated mocks and no new type errors or lint violations
2. **Given** a user performs OAuth login followed by listing projects, creating an issue, assigning Copilot, and polling to completion, **When** these actions are performed on the migrated system, **Then** every step produces identical outcomes to the pre-migration system
3. **Given** the system handles preview APIs (sub-issues, Copilot assignment) via untyped endpoints, **When** these APIs are called after migration, **Then** they still benefit from automatic retry and throttling behavior

---

### User Story 2 — Eliminate Infrastructure Boilerplate (Priority: P1)

As a backend engineer, I want the GitHub service to delegate retry logic, HTTP caching (ETag-based), throttling, and rate-limit handling to the SDK so that 1,500–2,000 lines of hand-rolled infrastructure code can be removed, reducing maintenance burden and bug surface area.

**Why this priority**: The hand-rolled retry, caching, throttling, and rate-limiting code is the single largest source of accidental complexity. Removing it is the primary value proposition of this migration and delivers the biggest maintenance win.

**Independent Test**: Can be fully tested by verifying a net reduction of 1,500–2,000 lines across the codebase, confirming that no direct low-level HTTP client imports remain outside of test mocks, and confirming that the deprecated infrastructure methods are no longer present.

**Acceptance Scenarios**:

1. **Given** the current service has 6,500+ lines including ~1,500–2,000 lines of infrastructure code (retry, caching, throttling, rate-limiting, header management), **When** the migration is complete, **Then** the codebase has a net reduction of 1,500–2,000 lines
2. **Given** the current service manually builds HTTP headers, parses retry-after values, manages ETag caches, and applies global cooldown logic, **When** the migration is complete, **Then** none of these manual infrastructure methods exist in the codebase
3. **Given** the current service imports the low-level HTTP client directly for API calls, **When** the migration is complete, **Then** no direct low-level HTTP client imports remain outside of test mocks

---

### User Story 3 — Replace Manual REST Calls with Typed SDK Methods (Priority: P2)

As a backend engineer, I want all 20+ manual REST call sites to use the SDK's typed methods so that I get compile-time type safety, automatic parameter validation, and built-in pagination — reducing the chance of URL construction errors and response parsing bugs.

**Why this priority**: This is the largest single source of LOC reduction (~600–800 lines) and replaces the most error-prone code (manual URL construction, header management, response parsing). It depends on Story 1's foundation being in place.

**Independent Test**: Can be fully tested by verifying each REST call site (issue creation, issue update, PR reviewer requests, branch deletion, comment creation, file listing, etc.) works correctly through the typed SDK methods, confirmed by both automated tests and manual verification.

**Acceptance Scenarios**:

1. **Given** the service has 20+ REST call sites that manually construct URLs and parse responses, **When** the migration is complete, **Then** all call sites use typed SDK methods with validated parameters and structured response models
2. **Given** the service manually implements pagination for list endpoints, **When** the migration is complete, **Then** all paginated endpoints use the SDK's built-in pagination
3. **Given** preview APIs (sub-issues, Copilot assignment) lack typed SDK methods, **When** these APIs are called, **Then** they use the SDK's generic request method and still receive automatic retry and throttling

---

### User Story 4 — Simplify OAuth Authentication Flow (Priority: P2)

As a backend engineer, I want the OAuth authentication flow to use the SDK's built-in OAuth strategies so that ~150 lines of manual OAuth code are eliminated while all session management behavior is preserved.

**Why this priority**: The OAuth flow is security-critical and currently hand-rolled. Using the SDK's built-in strategies reduces the chance of authentication bugs and simplifies the auth module to ~100 lines focused solely on session management.

**Independent Test**: Can be fully tested by performing a complete OAuth login flow (redirect → callback → token exchange → session creation) and verifying that session persistence, expiry, and cleanup work identically to the current implementation.

**Acceptance Scenarios**:

1. **Given** the current auth module has ~150 lines of manual OAuth code, **When** the migration is complete, **Then** the auth module is reduced to ~100 lines focused on session management
2. **Given** a user initiates OAuth login, **When** the authentication flow completes, **Then** the session is created and persisted identically to the pre-migration system
3. **Given** session data is stored in SQLite, **When** the OAuth migration is complete, **Then** all SQLite session management logic (storage, retrieval, expiry, cleanup) is preserved unchanged

---

### User Story 5 — Simplify GraphQL Layer (Priority: P3)

As a backend engineer, I want the custom GraphQL execution method to be replaced with the SDK's built-in GraphQL support so that ~200 lines of manual ETag caching, error parsing, and hash key generation are eliminated — while all 31 domain-specific query strings and app-layer caching logic (cycle cache, in-flight coalescing, global cooldown) remain unchanged.

**Why this priority**: This delivers meaningful LOC reduction but is lower risk since the GraphQL query strings themselves don't change. The app-layer caching logic must be carefully preserved, making this more nuanced than the REST replacement.

**Independent Test**: Can be fully tested by executing each of the 31 GraphQL queries/mutations and verifying identical results, confirming that cycle caching, in-flight coalescing, and global cooldown continue to work, and verifying the GraphQL-to-REST fallback chains use a unified helper pattern.

**Acceptance Scenarios**:

1. **Given** the current service has a custom GraphQL execution method with manual ETag caching, error parsing, and hash key generation, **When** the migration is complete, **Then** the custom method is replaced by the SDK's built-in GraphQL support (~200 lines removed)
2. **Given** 31 domain-specific GraphQL query/mutation strings exist, **When** the migration is complete, **Then** all 31 strings remain in their current module with no structural changes
3. **Given** app-layer caching logic (cycle cache, in-flight coalescing, global cooldown) exists, **When** the migration is complete, **Then** all app-layer caching logic is preserved and functional
4. **Given** some operations use GraphQL-to-REST fallback chains, **When** the migration is complete, **Then** all fallback chains use a unified helper pattern

---

### User Story 6 — Maintain Rate-Limit Visibility for Polling (Priority: P3)

As the system's polling service, I need continued access to rate-limit state information so that I can dynamically adjust polling intervals based on remaining API quota — even after the SDK takes over rate-limit management internally.

**Why this priority**: This is a focused integration concern. The polling service currently reads rate-limit state to adjust its behavior. Without an adapter, the polling service would lose this capability, degrading its ability to be a good API citizen.

**Independent Test**: Can be fully tested by simulating API calls that consume rate-limit quota and verifying that the polling service receives accurate remaining-quota and reset-time information through the adapter layer.

**Acceptance Scenarios**:

1. **Given** the polling service currently calls a rate-limit accessor to adjust polling intervals, **When** the SDK takes over rate-limit management, **Then** an adapter exposes the SDK-managed rate-limit state to the polling service
2. **Given** the adapter provides rate-limit information, **When** the polling service reads remaining quota and reset time, **Then** the values accurately reflect the current state from the most recent API response

---

### User Story 7 — Efficient Client Connection Reuse (Priority: P3)

As the system processing concurrent requests for multiple users, I need GitHub client instances to be pooled and reused per user so that TCP connections are efficiently shared rather than creating a new connection pool for every API call.

**Why this priority**: This is a performance optimization. The current system creates connections per-request. Pooling clients per user (bounded to prevent unbounded growth) improves efficiency. It is important but not a behavioral requirement.

**Independent Test**: Can be fully tested by verifying that multiple API calls for the same user token reuse the same client instance, that the pool evicts entries when the maximum size (50) is reached, and that different user tokens receive distinct client instances.

**Acceptance Scenarios**:

1. **Given** multiple API calls are made for the same user, **When** the client factory is invoked, **Then** the same client instance is returned (not a new one)
2. **Given** the client pool has reached its maximum capacity of 50 entries, **When** a new user's client is requested, **Then** the least-recently-used entry is evicted to make room
3. **Given** two different users make API calls, **When** client instances are created, **Then** each user receives a distinct client instance

---

### Edge Cases

- What happens when a user's OAuth token expires mid-operation? The system must handle token refresh or re-authentication gracefully, identical to current behavior.
- What happens when the client pool reaches maximum capacity (50 entries) during a burst of concurrent requests from many distinct users? The pool must evict least-recently-used entries without blocking or erroring.
- How does the system handle GitHub API rate-limit exhaustion? The SDK's built-in retry and backoff must handle this transparently, with the rate-limit adapter accurately reflecting the exhausted state to the polling service.
- What happens when preview APIs (sub-issues, Copilot assignment) return unexpected responses? The SDK's generic request method must surface errors in the same way the current manual implementation does.
- What happens when GitHub's API returns a secondary rate-limit response (HTTP 403 with retry-after)? The SDK must handle this automatically without any custom secondary-rate-limit parsing code.
- How does the system behave if the SDK's built-in HTTP cache (ETag) is unavailable or returns stale data? The system must fall back gracefully, identical to current ETag cache miss behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST preserve all externally observable behavior — OAuth login, project listing, issue creation, issue update, Copilot assignment, PR review requests, branch deletion, sub-issue management, comment creation, file listing, and polling — with no regressions after migration
- **FR-002**: System MUST replace the direct low-level HTTP client dependency with the SDK dependency in the project configuration, such that no direct low-level HTTP client imports remain outside of test mocks after all phases complete
- **FR-003**: System MUST implement a client factory that creates per-user async GitHub clients with automatic retry, HTTP caching, and throttling enabled, using a bounded pool (maximum 50 entries) keyed by token hash for connection reuse with least-recently-used eviction
- **FR-004**: System MUST migrate the OAuth authentication flow from ~150 lines of manual implementation to the SDK's built-in OAuth strategies, reducing the auth module to ~100 lines while retaining all SQLite session management logic (storage, retrieval, expiry, cleanup)
- **FR-005**: System MUST replace all 20+ manual REST call sites with typed SDK methods, including: issue creation, issue update, pull request reviewer requests, branch/ref deletion, issue comment creation, and pull request file listing with built-in pagination
- **FR-006**: System MUST use the SDK's generic request method for preview APIs (sub-issues, Copilot assignment) that lack typed methods, ensuring these calls still benefit from built-in retry and throttling
- **FR-007**: System MUST replace the custom GraphQL execution method with the SDK's built-in GraphQL support, eliminating manual ETag cache logic, error parsing, and hash key generation (~200 lines), while preserving all 31 domain-specific query/mutation strings without structural changes
- **FR-008**: System MUST preserve all app-layer caching logic — cycle cache, in-flight coalescing, and global cooldown — as these represent domain business logic, not infrastructure
- **FR-009**: System MUST consolidate all GraphQL-to-REST fallback chains to use a unified helper pattern
- **FR-010**: System MUST implement a rate-limit visibility adapter that exposes SDK-managed rate-limit state (remaining quota, reset time) to the polling service, replacing the current direct rate-limit accessor
- **FR-011**: System MUST delete all deprecated infrastructure methods after migration: manual retry logic, header builder, rate-limit header extractor, rate-limit accessors, retry-after parser, secondary rate-limit detector, global cooldown applicator/respecter, and all associated ETag cache and throttling fields
- **FR-012**: System MUST remove retry constants (maximum retries, initial backoff, and related constants) from the GraphQL query module after the SDK takes over retry management
- **FR-013**: System MUST update all test mocks from low-level HTTP client mocks to SDK-appropriate mocks, and update the dependency injection module for new service initialization patterns
- **FR-014**: System MUST pass all existing automated tests after mock updates, with no new type errors and clean lint checks
- **FR-015**: System MUST update architecture and configuration documentation to reflect the new SDK-based integration
- **FR-016**: System MUST achieve a net code reduction of 1,500–2,000 lines across the codebase, with the largest single reduction (~600–800 lines) coming from REST call site replacements

### Assumptions

- The SDK (version ≥0.14.0) provides stable, production-ready support for async operations, GraphQL with raw query strings, built-in retry/rate-limit handling, HTTP caching via ETag, throttling, and OAuth strategies. The initial integration should pin to a narrow version range (e.g., <0.15.0) to avoid unexpected breaking changes until the migration is validated, then relax the constraint
- The SDK uses the same underlying HTTP transport as the current implementation, so there is no dependency regression
- Preview APIs (sub-issues, Copilot assignment) may not have typed methods in the SDK, requiring use of generic request methods
- The existing BoundedDict utility in the codebase can be reused for the client connection pool
- The 31 existing GraphQL query/mutation strings are compatible with the SDK's GraphQL method without modification
- Standard web application performance expectations apply (no special latency targets beyond current behavior)
- The SDK's built-in HTTP caching and throttling provide equivalent or better behavior compared to the current manual implementation

### Key Entities

- **GitHub Client**: A per-user authenticated client instance that encapsulates connection management, retry logic, caching, and throttling. Keyed by user token hash. Pooled with a maximum of 50 concurrent instances.
- **Client Factory**: The entry point for obtaining GitHub client instances. Manages the bounded client pool, creates new clients on cache miss, and evicts least-recently-used entries when the pool is full.
- **Rate-Limit State**: A lightweight data structure exposing remaining API quota and reset timestamp, consumed by the polling service to dynamically adjust intervals. Populated from API response headers.
- **OAuth Session**: Represents an authenticated user session. Persisted in SQLite with expiry and cleanup logic. The authentication flow is delegated to the SDK's OAuth strategies while session persistence remains application-managed.
- **GraphQL Query**: One of 31 domain-specific query/mutation string constants used for Projects V2 and Copilot operations. These remain as raw strings, executed through the SDK's GraphQL method rather than a custom execution wrapper.
- **Fallback Chain**: A pattern where a GraphQL operation falls back to a REST operation (or vice versa) on failure. All such chains must use a unified helper to ensure consistent error handling and retry behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing automated tests (1,400+) pass after migration with updated mocks, with zero new type errors and clean lint output
- **SC-002**: Net codebase reduction of 1,500–2,000 lines, verified by line-count comparison before and after migration
- **SC-003**: Manual smoke test of the full critical path (OAuth login → list projects → create issue → assign Copilot → poll → completion) completes successfully with no behavioral differences
- **SC-004**: Zero direct low-level HTTP client imports remain in production code (outside of test mocks), verified by codebase search
- **SC-005**: All deprecated infrastructure methods (at least 10 methods covering retry, caching, throttling, rate-limiting, and header management) are removed from the codebase
- **SC-006**: The authentication module is reduced from ~250 lines to ~100 lines while preserving all session management functionality
- **SC-007**: The client connection pool correctly reuses instances for repeated same-user requests and evicts entries at the 50-entry boundary, verified by automated tests
- **SC-008**: The polling service accurately receives rate-limit state (remaining quota and reset time) through the adapter layer, verified by automated tests
- **SC-009**: All 31 GraphQL query/mutation strings remain functionally unchanged, with results identical to pre-migration execution
- **SC-010**: Architecture and configuration documentation accurately reflects the new integration approach, with no references to removed infrastructure
