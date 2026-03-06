# Feature Specification: Simplify GitHub Service with githubkit v0.14.6

**Feature Branch**: `019-githubkit-migration`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Simplify GitHub Service with githubkit v0.14.6: Replace Hand-Rolled httpx Integration (~1,500–2,000 LOC Reduction)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Foundation: Add githubkit and Client Factory (Priority: P1)

As a backend engineer, I want the project to depend on githubkit as its sole GitHub SDK so that every subsequent migration step has a stable, tested client factory to build on.

**Why this priority**: Nothing else can proceed until a properly configured client factory exists. This story delivers the foundational dependency change and client pool with zero behavior changes, making it safe to merge independently.

**Independent Test**: Can be fully tested by verifying that the new dependency installs cleanly, the client factory creates authenticated clients, and the bounded client pool enforces its size limit — all without changing any existing GitHub API call paths.

**Acceptance Scenarios**:

1. **Given** the project's dependency manifest lists the hand-rolled HTTP library as a direct dependency, **When** a developer installs dependencies after this change, **Then** the GitHub SDK is installed instead and the hand-rolled HTTP library is no longer a direct dependency (it may still be present as a transitive dependency of the SDK).
2. **Given** a valid user access token, **When** the client factory is asked to create a client, **Then** it returns an authenticated async client configured with automatic retry, HTTP caching, and request throttling.
3. **Given** the client pool already holds 50 entries, **When** a 51st unique user token is presented, **Then** the oldest entry is evicted and the new client is stored, keeping the pool at 50.
4. **Given** a user token that was already used, **When** the client factory is called again with the same token, **Then** it returns the previously created client from the pool instead of creating a new one.

---

### User Story 2 — Replace REST API Call Sites (Priority: P1)

As a backend engineer, I want every manual REST call in the service layer to use the SDK's typed methods so that URL construction, header management, response parsing, and pagination are handled automatically — eliminating the largest block of infrastructure code.

**Why this priority**: This delivers the biggest code reduction (~600–800 lines) and the most immediate maintainability improvement. It depends on Story 1 (client factory) but is the highest-value migration step.

**Independent Test**: Can be fully tested by running the existing integration/unit test suite for issue creation, issue updates, PR review requests, branch deletion, comment creation, and file listing — each call should produce identical API behavior with significantly less service-layer code.

**Acceptance Scenarios**:

1. **Given** valid inputs for creating an issue (owner, repo, title, body, labels), **When** the service's create-issue method is called, **Then** it delegates to the SDK's typed issue-creation method and returns the same response shape as before.
2. **Given** valid inputs for updating an issue body, **When** the service's update method is called, **Then** it delegates to the SDK's typed issue-update method.
3. **Given** a pull request number, **When** the service requests changed files, **Then** it delegates to the SDK's typed file-listing method with built-in pagination, returning all changed files without manual page iteration.
4. **Given** a preview API endpoint that lacks a typed SDK method (e.g., Sub-Issues or Copilot assignment), **When** the service calls that endpoint, **Then** it uses the SDK's generic request method, still benefiting from automatic retry and throttling.
5. **Given** the migration is complete, **When** a developer searches the codebase for direct imports of the hand-rolled HTTP library, **Then** zero hits appear outside of test mock files.

---

### User Story 3 — Simplify the GraphQL Layer (Priority: P2)

As a backend engineer, I want the custom GraphQL execution method replaced with the SDK's built-in GraphQL method so that manual ETag caching, error parsing, and hash-key generation are eliminated — while all 31 domain-specific query strings and application-layer caching logic remain untouched.

**Why this priority**: Delivers ~200 lines of code reduction and removes fragile hand-rolled cache/error logic. Depends on Story 1 but is independent of Story 2. Lower priority than REST replacement because fewer call sites are affected.

**Independent Test**: Can be fully tested by running existing GraphQL-dependent tests (project listing, field value mutations, item queries) and verifying identical responses with the SDK's GraphQL method.

**Acceptance Scenarios**:

1. **Given** a GraphQL query string and variables, **When** the service executes the query, **Then** it delegates to the SDK's built-in GraphQL method instead of the hand-rolled execution path.
2. **Given** the GraphQL layer migration is complete, **When** a developer inspects the service, **Then** manual ETag cache fields, error-parsing helpers, and hash-key generation code are no longer present.
3. **Given** the application-layer caching logic (cycle cache, in-flight request coalescing, global cooldown), **When** GraphQL queries are executed after migration, **Then** these domain-specific behaviors continue to function identically.
4. **Given** methods that fall back from GraphQL to REST on failure, **When** any such fallback is invoked, **Then** it uses the unified fallback helper pattern consistently.

---

### User Story 4 — Migrate OAuth Authentication (Priority: P2)

As a backend engineer, I want the manual OAuth implementation replaced with the SDK's built-in OAuth strategies so that the authentication module is reduced from ~150 lines to ~100 lines while preserving all session-management behavior.

**Why this priority**: Reduces a security-sensitive area of code by leveraging a well-tested SDK implementation. Independent of Stories 2 and 3. Moderate priority because the existing OAuth code works but is unnecessarily verbose.

**Independent Test**: Can be fully tested by performing a complete OAuth login flow (redirect → callback → token exchange → session storage) and verifying that sessions are created, stored, and retrievable from the database identically to before.

**Acceptance Scenarios**:

1. **Given** a user initiating OAuth login, **When** the authentication module generates the authorization URL, **Then** it uses the SDK's OAuth strategy to produce a valid redirect URL.
2. **Given** a user returning from the OAuth callback with a valid code, **When** the authentication module exchanges the code for a token, **Then** it uses the SDK's token-exchange strategy and stores the token in the session database.
3. **Given** the migration is complete, **When** a developer reviews the authentication module, **Then** it contains approximately 100 lines of code with all SQLite session management logic preserved.

---

### User Story 5 — Delete Deprecated Infrastructure and Clean Up (Priority: P3)

As a backend engineer, I want all deprecated infrastructure methods, retry constants, and stale documentation removed so that the codebase reflects the new SDK-based architecture with no dead code.

**Why this priority**: Pure cleanup with no behavior changes. Must happen last because it removes methods that other stories depend on during the transition. Low risk but delivers the final LOC reduction and documentation accuracy.

**Independent Test**: Can be fully tested by running the full test suite after deletion, verifying zero references to removed methods, and confirming documentation accurately describes the new architecture.

**Acceptance Scenarios**:

1. **Given** all REST and GraphQL call sites have been migrated, **When** the deprecated infrastructure methods are removed, **Then** the full test suite passes with no regressions.
2. **Given** the infrastructure deletion is complete, **When** a developer searches for the removed method names, **Then** zero references exist in production code.
3. **Given** the cleanup phase is complete, **When** a developer reviews the architecture and configuration documentation, **Then** it accurately describes the SDK-based integration without referencing removed concepts.
4. **Given** the retry constants in the GraphQL module, **When** they are removed, **Then** no production code references them.

---

### User Story 6 — Rate Limit Visibility Adapter (Priority: P2)

As a backend engineer, I want an adapter that exposes the SDK's internally managed rate-limit state so that the polling service can continue to adjust its intervals based on remaining API quota — without reaching into SDK internals.

**Why this priority**: The polling service currently reads rate-limit data to make intelligent throttling decisions. Without this adapter, the polling service would lose visibility into rate limits after migration, potentially causing excessive API calls or unnecessary delays. This is a correctness concern.

**Independent Test**: Can be fully tested by making API calls through the SDK client and verifying that the adapter surfaces accurate remaining-request counts and reset timestamps that the polling service can consume.

**Acceptance Scenarios**:

1. **Given** an API call has been made through the SDK client, **When** the polling service queries the rate-limit adapter, **Then** it receives the current remaining-request count and reset timestamp.
2. **Given** the rate-limit adapter is in place, **When** the polling service adjusts its interval, **Then** it makes the same throttling decisions as it did with the previous direct rate-limit access.
3. **Given** no API calls have been made yet, **When** the polling service queries the adapter, **Then** it receives a sensible default indicating full quota availability.

---

### Edge Cases

- What happens when a user's OAuth token expires mid-session? The SDK's retry logic should handle 401 responses gracefully, and the session store should trigger re-authentication.
- What happens when the GitHub API returns a secondary rate limit (HTTP 403 with Retry-After header)? The SDK's built-in retry must respect the Retry-After value automatically.
- What happens when the client pool is concurrently accessed by multiple async requests? The pool must be safe for concurrent reads and writes without data corruption.
- What happens when the SDK's GraphQL method encounters a partial-success response (some data returned with errors)? The service must handle this identically to the current behavior.
- What happens when a preview API endpoint changes its URL or behavior? The generic request method should allow URL and header customization without code changes to the SDK layer.
- What happens when the network is temporarily unavailable? The SDK's retry logic with exponential backoff must handle transient failures transparently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the direct HTTP library dependency with githubkit (pinned to >=0.14.0,<0.15.0) in the project's dependency manifest, ensuring the hand-rolled HTTP library is no longer listed as a direct dependency.
- **FR-002**: System MUST implement a client factory that creates per-user async GitHub clients configured with token-based authentication, automatic retry, HTTP caching, and request throttling.
- **FR-003**: System MUST implement a bounded client pool (maximum 50 entries) keyed on a hash of the user's access token, using least-recently-used eviction to reuse existing clients and their underlying connection pools.
- **FR-004**: System MUST migrate the OAuth authentication module from its hand-rolled implementation (~150 LOC) to the SDK's built-in OAuth strategies, retaining all existing SQLite session management logic, and reducing the module to approximately 100 LOC.
- **FR-005**: System MUST replace all manual REST call sites in the service layer (20+ methods) with the SDK's typed methods, including but not limited to: issue creation, issue updates, pull request reviewer requests, git reference deletion, issue comment creation, and pull request file listing with built-in pagination.
- **FR-006**: System MUST use the SDK's generic request method for preview API endpoints (Sub-Issues and Copilot assignment APIs) that lack typed SDK methods, ensuring these calls benefit from the SDK's built-in retry and throttling.
- **FR-007**: System MUST replace the custom GraphQL execution method with the SDK's built-in GraphQL method, eliminating manual ETag caching, error parsing, and hash-key generation while preserving all 31 domain-specific query and mutation strings.
- **FR-008**: System MUST preserve all application-layer logic that operates above the infrastructure layer: cycle-based caching, in-flight request coalescing, and global cooldown behavior.
- **FR-009**: System MUST consolidate all GraphQL-to-REST fallback chains to use a single unified fallback helper pattern.
- **FR-010**: System MUST implement a rate-limit visibility adapter that exposes the SDK's internally managed rate-limit state (remaining requests, reset timestamp) to the polling service without exposing SDK internals.
- **FR-011**: System MUST delete all deprecated infrastructure methods after migration, including: the retry-with-backoff method, header-building method, rate-limit header extraction, rate-limit state accessors, retry-after parsing, secondary rate-limit detection, global cooldown application, global cooldown respect method, and all associated ETag cache and throttling fields.
- **FR-012**: System MUST remove retry-related constants (maximum retries, initial backoff duration, and related values) from the GraphQL module after migration.
- **FR-013**: System MUST update all test mocks from the hand-rolled HTTP library to the SDK's mocking approach, and update the dependency-injection module's service initialization accordingly.
- **FR-014**: System MUST update architecture and configuration documentation to reflect the new SDK-based integration.
- **FR-015**: System MUST maintain identical externally observable behavior across all features: OAuth login, project listing, issue creation, Copilot assignment, PR review requests, branch deletion, sub-issue management, and polling.
- **FR-016**: System MUST ensure zero direct imports of the hand-rolled HTTP library remain in production code after all phases are complete (imports within test mock files are acceptable).
- **FR-017**: System MUST execute the migration in phased order — Foundation first, then REST replacement and GraphQL simplification (which may proceed in parallel), then infrastructure deletion and cleanup — to enable incremental code review and safe rollback at each phase boundary.

### Key Entities

- **GitHubClient**: An authenticated, async SDK client instance configured for a specific user. Key attributes: user token hash, retry policy, caching policy, throttle configuration.
- **ClientPool**: A bounded collection of GitHubClient instances keyed by token hash. Key attributes: maximum capacity (50), eviction policy (least-recently-used), thread-safety for async access.
- **RateLimitState**: A lightweight data object exposing the current rate-limit status. Key attributes: remaining request count, reset timestamp, resource category.
- **OAuthSession**: The persisted authentication session linking a user to their access token. Key attributes: token, expiry, refresh token, user identifier. Stored in SQLite (existing behavior preserved).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Net codebase reduction of 1,500–2,000 lines of code across all affected files after all five phases are complete.
- **SC-002**: All existing automated tests pass after migration with updated mocks — zero test failures and zero new type-checking errors.
- **SC-003**: A full end-to-end workflow — OAuth login → list projects → create issue → assign Copilot → poll status → completion — completes successfully with no behavioral differences.
- **SC-004**: Zero direct imports of the hand-rolled HTTP library exist in production code (verified by codebase search).
- **SC-005**: The bounded client pool maintains at most 50 entries under concurrent load, verified by test scenarios with more than 50 unique tokens.
- **SC-006**: The rate-limit adapter accurately reports remaining API quota within 1 request of the actual value, verified by comparing adapter output against raw response headers in tests.
- **SC-007**: The authentication module is reduced to approximately 100 lines of code (down from ~150) while passing all existing OAuth flow tests.
- **SC-008**: Style-checking and linting tools report a clean pass with no new violations after migration.
- **SC-009**: Each migration phase can be independently reviewed and merged without breaking the system at any intermediate state.

### Assumptions

- githubkit v0.14.x provides stable, well-documented methods for all standard GitHub REST and GraphQL operations referenced in this specification.
- The SDK's built-in retry, caching, and throttling behaviors are functionally equivalent to or better than the current hand-rolled implementations for the project's usage patterns.
- Preview API endpoints (Sub-Issues, Copilot assignment) will continue to be accessible via the SDK's generic request method even if they lack typed method support.
- The existing 31 GraphQL query/mutation strings are compatible with the SDK's GraphQL method without modification.
- The SDK's OAuth strategies support the same OAuth flow currently implemented (web-based authorization code grant with token exchange).
- The bounded client pool size of 50 is sufficient for the expected number of concurrent users; this can be made configurable if needed.
- The current test suite provides adequate coverage to detect behavioral regressions during migration; no new feature tests are needed beyond mock updates.
