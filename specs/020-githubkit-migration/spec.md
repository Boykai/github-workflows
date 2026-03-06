# Feature Specification: Simplify GitHub Service with githubkit

**Feature Branch**: `020-githubkit-migration`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "Replace the 6,500+ LOC hand-rolled GitHub integration (raw httpx + manual retry/caching/rate-limiting + 31 GraphQL string constants) with githubkit (v0.14.6), a modern async Python GitHub SDK. This eliminates ~1,500-2,000 LOC of infrastructure code, replaces the custom OAuth flow, and provides built-in retry, HTTP caching, throttling, and typed REST API methods — while keeping domain-specific GraphQL queries for Projects V2 and Copilot agent assignment preview APIs."

## Clarifications

### Session 2026-03-05

- Q: Should the application-level global cooldown lock be preserved alongside the SDK's throttler, or eliminated in favor of it? → A: Eliminate the global cooldown lock — rely on the SDK's throttler for all rate-limit spacing.
- Q: Should unrecoverable SDK errors propagate as the SDK's native exception type, or be wrapped in a domain-specific exception? → A: Let SDK exceptions propagate natively — callers catch the SDK's exception types directly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - SDK Foundation and Client Factory (Priority: P1)

As a developer maintaining the GitHub integration layer, I want the application to use a dedicated GitHub SDK with built-in retry, caching, throttling, and typed API methods so that I no longer need to maintain ~1,200 lines of hand-rolled HTTP infrastructure code (retry logic, header construction, ETag caching, rate-limit parsing, inter-call throttling) that duplicates what a mature SDK provides out of the box.

**Why this priority**: The infrastructure code — `_request_with_retry()`, `_build_headers()`, `_extract_rate_limit_headers()`, ETag cache management, inter-call throttling — is the foundational layer that every other method depends on. Replacing it first unblocks all subsequent simplifications. Without this, none of the REST or GraphQL call replacements can happen.

**Independent Test**: Can be tested by running the full backend test suite after swapping the HTTP client layer. A single integration test proving "list user projects" works end-to-end through the new SDK client validates the foundation. Delivers immediate value by reducing the maintenance surface of the most complex, hardest-to-debug code in the application.

**Acceptance Scenarios**:

1. **Given** the application uses raw httpx with custom retry/backoff/caching/throttling infrastructure, **When** the HTTP client layer is replaced with an SDK that provides these features natively, **Then** all existing API operations (list projects, create issues, assign Copilot, poll for changes) continue working identically with no user-visible behavior change.
2. **Given** the SDK client is configured with automatic retry for rate-limit and server-error responses, **When** the GitHub API returns a 429 or 5xx response, **Then** the SDK retries the request automatically using the `Retry-After` header value or exponential backoff, matching the current behavior.
3. **Given** the SDK client is configured with HTTP caching, **When** the same GraphQL query is made twice with unchanged data, **Then** the second request receives a cache hit (304 Not Modified) without consuming rate limit quota, matching the current ETag caching behavior.
4. **Given** the SDK client is configured with request throttling, **When** multiple API calls are made in rapid succession, **Then** the SDK spaces them out automatically to respect rate limit budgets, matching the current 500ms inter-call throttle behavior.
5. **Given** the application needs per-user isolation (different access tokens), **When** multiple users are active concurrently, **Then** each user's API calls use their own authenticated client instance with isolated rate-limit state.

---

### User Story 2 - Typed REST API Call Replacement (Priority: P1)

As a developer modifying GitHub REST API interactions, I want all REST API calls to use typed SDK methods with Pydantic-validated responses so that I get compile-time type safety, automatic URL construction, built-in pagination, and response parsing — eliminating repetitive boilerplate code across 20+ call sites.

**Why this priority**: The REST API calls represent the largest volume of boilerplate code (manual URL construction, header building, response parsing, error handling at each call site). Replacing them delivers the biggest line-count reduction per unit of effort and the most immediate improvement to developer experience. This is tied P1 with the foundation because it delivers the primary user value.

**Independent Test**: Can be tested call-by-call — each REST method replacement can be independently unit-tested by verifying the typed SDK call produces the same domain result as the raw httpx call it replaces. Integration test: create an issue via the new typed method and verify it appears on GitHub.

**Acceptance Scenarios**:

1. **Given** the system creates GitHub Issues by manually building POST requests to `/repos/{owner}/{repo}/issues`, **When** the call is replaced with a typed SDK method, **Then** issue creation works identically: title, body, labels, milestone, and assignees are set correctly, and the response includes the issue number and node ID.
2. **Given** the system updates issue state/body by manually building PATCH requests, **When** these calls are replaced with typed SDK methods, **Then** issue updates work identically, including state transitions (open/closed) with state_reason parameters.
3. **Given** the system requests Copilot code reviews by manually building POST requests to `/pulls/{n}/requested_reviewers`, **When** the call is replaced with a typed SDK method, **Then** the review request succeeds and the Copilot reviewer appears on the pull request.
4. **Given** the system retrieves PR changed files by manually building GET requests with pagination, **When** the call is replaced with a typed SDK method using built-in pagination, **Then** all changed files are returned correctly without manual page-cursor management.
5. **Given** the system accesses preview APIs (Sub-Issues, Copilot assignment) that may not have typed SDK methods, **When** these are called via the SDK's generic request method, **Then** they still benefit from the SDK's retry, throttling, and header management while preserving current behavior.

---

### User Story 3 - OAuth Flow Simplification (Priority: P2)

As a developer maintaining the authentication layer, I want the OAuth web flow (authorization URL generation, code-for-token exchange, token refresh) to be handled by the SDK's built-in OAuth strategies so that the custom OAuth implementation (~150 LOC) is eliminated, reducing maintenance burden and the risk of auth-related bugs.

**Why this priority**: Authentication is critical but changes infrequently. The existing code works but is hand-rolled duplicating what the SDK provides. Replacing it reduces attack surface (fewer custom auth code paths to audit) and simplifies onboarding for new developers. It is P2 because the existing code works correctly and this is lower-risk than the REST/GraphQL changes.

**Independent Test**: Can be tested by performing a full OAuth login flow in a staging environment: redirect to GitHub → authorize → callback → token stored → API calls succeed. Token refresh can be tested by setting a short expiration and verifying auto-refresh occurs.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the authorization URL is generated using the SDK's OAuth strategy, **Then** the URL is correctly formed with the required scopes (`read:user read:org project repo`) and CSRF state parameter.
2. **Given** GitHub redirects back with an authorization code, **When** the code is exchanged for an access token using the SDK's token exchange method, **Then** the access token and refresh token are returned and persisted in the SQLite session store.
3. **Given** a user's access token has expired, **When** the SDK's token refresh mechanism is invoked, **Then** a new access token is obtained using the stored refresh token and the session store is updated.
4. **Given** token storage and session management are application-specific concerns, **When** the OAuth flow is migrated to the SDK, **Then** the SQLite session persistence layer is preserved unchanged — only the HTTP-level token exchange logic is replaced.

---

### User Story 4 - GraphQL Layer Simplification (Priority: P2)

As a developer writing GraphQL queries against GitHub's API, I want the custom GraphQL execution wrapper (manual header construction, error parsing, ETag cache key hashing, inflight deduplication setup) to be simplified by delegating transport-level concerns to the SDK while preserving domain-specific optimizations (cycle cache, request coalescing, cooldown coordination).

**Why this priority**: The GraphQL layer is the second-largest source of infrastructure boilerplate after REST calls. However, it requires more care than REST because the application relies on domain-specific caching layers (cycle cache, inflight coalescing) that sit above the transport. This makes it P2 — important for code simplification but requires careful separation of transport from domain caching.

**Independent Test**: Can be tested by running the existing polling loop in a staging environment and verifying that project items are fetched correctly, Copilot assignments use the correct GraphQL-Features headers, and the cycle cache still prevents redundant queries within a single poll iteration.

**Acceptance Scenarios**:

1. **Given** the application executes GraphQL queries by manually building POST requests with auth headers, ETag cache keys, and error parsing, **When** the transport is delegated to the SDK's GraphQL method, **Then** queries execute correctly with automatic authentication, error handling, and HTTP-level caching.
2. **Given** certain GraphQL operations require preview feature flags via the `GraphQL-Features` header, **When** these operations are executed through the SDK, **Then** the custom headers are passed through to the SDK's request method and GitHub accepts them.
3. **Given** the application maintains a per-polling-cycle cache to avoid redundant API calls within a single 60-second cycle, **When** the GraphQL transport is simplified, **Then** the domain-specific cycle cache continues to work independently of the SDK's HTTP cache.
4. **Given** the application deduplicates concurrent identical GraphQL requests via inflight task coalescing, **When** the transport layer changes, **Then** inflight coalescing continues to prevent duplicate simultaneous requests.

---

### User Story 5 - Infrastructure Code Removal and Cleanup (Priority: P3)

As a developer onboarding to this codebase, I want the GitHub service module to contain only business logic (project management, Copilot orchestration, board reconciliation) without interleaved HTTP infrastructure code so that I can understand what the code does without first understanding a custom HTTP client implementation.

**Why this priority**: This is the cleanup phase that follows the functional replacements. It delivers value through improved readability and reduced line count but does not change behavior. It depends on Stories 1-4 being complete before the deprecated infrastructure can be safely removed.

**Independent Test**: Can be tested by running the full test suite after removing deprecated methods/fields and verifying no import errors, no runtime references to deleted code, and the line count of the service module is reduced by the expected amount.

**Acceptance Scenarios**:

1. **Given** the infrastructure methods (`_request_with_retry`, `_build_headers`, `_extract_rate_limit_headers`, `_parse_retry_after_seconds`, `_is_secondary_limit`, `_apply_global_cooldown`, `_respect_global_cooldown`) are no longer called by any code path, **When** they are removed from the service module, **Then** all tests pass and no runtime errors occur.
2. **Given** the ETag cache fields (`_etag_cache`, `_ETAG_CACHE_MAX_SIZE`) and throttling fields (`_last_request_time`, `_min_request_interval`) on the service class are no longer used, **When** they are removed from the constructor, **Then** the service initializes correctly and memory usage decreases.
3. **Given** retry-related constants (`MAX_RETRIES`, `INITIAL_BACKOFF_SECONDS`, `MAX_BACKOFF_SECONDS`) in the GraphQL module are no longer referenced, **When** they are removed, **Then** no import errors occur across the codebase.
4. **Given** all REST and GraphQL calls now go through the SDK, **When** the raw httpx import is removed from the service modules, **Then** `grep -r "import httpx"` returns zero hits in production code (test utilities excepted).

---

### Edge Cases

- What happens when the SDK's built-in retry exhausts all attempts? The SDK raises its native exception type with full error context (status code, response body, retry count). Callers handle this the same way they handle the current `httpx.HTTPStatusError` after max retries — no domain-wrapping is applied. The `_with_fallback()` helper's catch-all `Exception` handler covers this naturally.
- What happens when GitHub introduces a new preview API not yet in the SDK's typed methods? The SDK's generic `github.request("METHOD", url, json=body)` method allows calling any endpoint with full retry/throttle/auth support, matching current behavior with raw httpx but with less boilerplate.
- What happens when rate-limit information needs to be exposed to the polling service for adaptive decisions? The SDK manages rate limits internally; the polling service needs an adapter pattern to query the SDK's rate-limit state (or the SDK's response headers) rather than the previous instance-level cache.
- What happens when two concurrent users trigger conflicting rate-limit states? Each user gets an isolated SDK client with independent rate-limit tracking. Cross-user rate-limit coordination (same IP quota) is handled by the SDK's built-in throttler, which replaces the hand-rolled global cooldown lock.
- What happens when the application restarts mid-OAuth-flow? The CSRF state validation remains in-memory (documented limitation as per spec 018). The SDK does not change this — the in-memory state store with TTL and bounded size is preserved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the raw httpx HTTP client with a GitHub SDK that provides native async support, automatic retry on rate-limit (429) and server-error (5xx) responses, HTTP-level caching (ETag/304), and request throttling.
- **FR-002**: System MUST create SDK client instances scoped per-user access token, ensuring no cross-user data leakage and supporting concurrent requests from multiple authenticated users.
- **FR-003**: System MUST replace all manually-constructed REST API calls (20+ call sites covering issues, pull requests, branches, repository contents, timeline events, sub-issues, and assignee validation) with typed SDK methods or the SDK's generic request method.
- **FR-004**: System MUST replace the custom OAuth web flow implementation (authorization URL generation, code-for-token exchange, token refresh) with the SDK's built-in OAuth strategies while preserving the existing SQLite session persistence layer.
- **FR-005**: System MUST replace the custom GraphQL execution wrapper with the SDK's GraphQL method while preserving domain-specific optimizations: per-polling-cycle cache and inflight request coalescing. The application-level global cooldown lock is eliminated in favor of the SDK's built-in throttler.
- **FR-006**: System MUST support passing custom HTTP headers (notably `GraphQL-Features` for preview APIs like Copilot agent assignment and coding agent model selection) through the SDK for operations that require them.
- **FR-007**: System MUST support calling preview/undocumented REST API endpoints (Sub-Issues, Copilot assignment with custom agent/instructions) via the SDK's generic request method, with automatic retry, throttling, and auth header injection.
- **FR-008**: System MUST preserve the `_with_fallback()` pattern for operations that use GraphQL as primary and REST as fallback (or vice versa), ensuring both strategies benefit from SDK features.
- **FR-009**: System MUST remove all deprecated infrastructure code (retry methods, header builders, ETag cache, throttling fields, rate-limit parsers) after migration is complete, with no dead code remaining.
- **FR-010**: System MUST expose rate-limit state to the polling service so that adaptive polling (doubling intervals when quota is low, pausing when exhausted) continues to function after the migration.
- **FR-011**: System MUST preserve the existing `BoundedDict`-based client pooling pattern, adapting it to pool SDK client instances per token hash to reuse connections efficiently.
- **FR-012**: System MUST handle the SDK's exception types in all error-handling code paths, replacing references to `httpx.HTTPStatusError` with the SDK's native exception types. SDK exceptions propagate directly to callers without domain-wrapping, preserving rich error context (status code, response body, retry count).

### Key Entities

- **GitHubClient**: An authenticated SDK client instance scoped to a single user's access token. Key attributes: token identity (hashed), auto-retry configuration, throttler, HTTP cache enablement. Created by the client factory, optionally pooled and reused.
- **GitHubClientFactory**: A factory or pool that creates and manages SDK client instances. Key attributes: shared configuration (retry policy, throttle limits, cache settings), bounded pool of active clients keyed by token hash.
- **GraphQL Query/Mutation Strings**: The 31 existing GraphQL query and mutation strings for Projects V2 API operations. These are domain-specific and remain unchanged — only the transport that executes them changes.
- **OAuthSession**: The existing SQLite-persisted user session (access token, refresh token, expiration, username). The session entity is unchanged; only the code that populates it during token exchange/refresh is simplified.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The GitHub service module (service.py + graphql.py + github_auth.py) has a net reduction of at least 1,500 lines of code compared to the pre-migration state, while all existing test cases pass.
- **SC-002**: All 20+ REST API operations complete successfully through the SDK with identical functional outcomes as the pre-migration implementation, verified by the full backend test suite passing without modification to test assertions (only mock targets change).
- **SC-003**: The OAuth login flow completes end-to-end (authorize → callback → token persisted → authenticated API call succeeds) with the SDK-based implementation in under 5 seconds total roundtrip time, matching the current performance.
- **SC-004**: When the GitHub API returns rate-limit responses (429), the system automatically retries and recovers without user-visible errors, matching or improving on the current retry behavior.
- **SC-005**: Zero raw httpx imports remain in production code (`grep -r "import httpx" backend/src/` returns no matches), confirming complete migration.
- **SC-006**: The polling service continues to adapt its interval based on rate-limit state, verifiable by observing interval changes in logs during sustained API activity.
- **SC-007**: Developer onboarding time to understand the GitHub service layer is measurably reduced by having business logic separated from HTTP infrastructure — assessed qualitatively through code review feedback.

## Assumptions

- githubkit (v0.14.6) remains stable and actively maintained. If a breaking change occurs in a future version, the application pins to a compatible version.
- The SDK's built-in HTTP cache (Hishel) handles ETag/304 scenarios equivalently to the current custom implementation. If edge cases arise, the application-level cycle cache provides a fallback.
- Preview API endpoints (Copilot agent assignment, Sub-Issues) remain accessible via the SDK's generic request method even without typed SDK support.
- The current test suite adequately covers the GitHub API integration surface such that passing tests after migration validates functional equivalence.
- httpx remains available as a transitive dependency through githubkit for any remaining direct usage in test utilities.
