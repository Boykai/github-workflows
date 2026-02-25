# Feature Specification: Bug Bash — Codebase Quality & Reliability Sweep

**Feature Branch**: `010-bug-bash`  
**Created**: 2026-02-23  
**Status**: Draft  
**Input**: User description: "conduct a bug bash exercise. Look for errors and issues in the codebase and resolve. Use best practices. Keep code DRY. Keep code simple."

## Clarifications

### Session 2026-02-24

- Q: Who counts as "authorized" for settings modification (FR-005)? → A: Only the session owner (first authenticated user / app deployer) is admin.
- Q: What is explicitly out of scope for this bug bash? → A: Database migration (SQLite→Postgres), full RBAC system, new features, UI redesign, polling-to-event-driven architecture rewrite.
- Q: Where does the token encryption key come from? → A: Read from an environment variable (e.g., ENCRYPTION_KEY); if missing on first startup, auto-generate and log a warning to persist it.
- Q: Should structured logging / observability be in scope? → A: Add only a request-ID middleware (correlation ID per request); defer full structured JSON logging to a future feature.
- Q: How is production vs. development mode detected? → A: Reuse the existing `debug: bool = False` field in Settings; dev-only endpoints are available only when `debug=True`, which defaults to `False` (production-safe).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Secure Authentication Flow (Priority: P1)

A user authenticates via GitHub OAuth. Their session token is transmitted securely and never exposed in URLs, browser history, or server logs. Developer-only login shortcuts are disabled in production environments. OAuth state entries expire and are cleaned up automatically to prevent memory exhaustion.

**Why this priority**: Authentication is the trust boundary for the entire application. A token leak or auth bypass compromises every user's GitHub access token and all connected repositories.

**Independent Test**: Can be fully tested by completing the OAuth login flow and confirming the session token never appears in any URL, log, or response header. Verify that the dev-login endpoint is unreachable in production mode.

**Acceptance Scenarios**:

1. **Given** a user initiates GitHub OAuth login, **When** the OAuth callback completes, **Then** the session token is delivered via a secure mechanism (e.g., Set-Cookie with HttpOnly and Secure flags) and never appears in the URL query string.
2. **Given** the application is running in production mode, **When** a request is made to the developer login shortcut endpoint, **Then** the system responds with a 404 or 403 error.
3. **Given** a user starts an OAuth flow but does not complete it within 10 minutes, **When** the expiry window passes, **Then** the pending OAuth state entry is automatically removed from memory.
4. **Given** the application restarts, **When** an in-flight OAuth flow attempts to complete, **Then** the system gracefully rejects the stale state and prompts the user to re-authenticate.

---

### User Story 2 — Reliable Pipeline Progression (Priority: P1)

A user kicks off an AI agent pipeline for an issue. The pipeline only advances to the next stage when the current agent has verifiably completed meaningful work (code pushed, deliverables present). The pipeline does not silently advance on false-positive completion signals such as agent unassignment without commits.

**Why this priority**: False-positive pipeline advancement is the core correctness bug — it causes the system to skip entire workflow stages, producing PRs with no real work and breaking user trust in automation.

**Independent Test**: Can be fully tested by simulating a Copilot agent that is unassigned from an issue without pushing any commits and verifying the pipeline does NOT advance.

**Acceptance Scenarios**:

1. **Given** an agent is assigned to a sub-issue, **When** the agent is unassigned but no new commits are detected on the branch, **Then** the pipeline does NOT mark the stage as complete.
2. **Given** an agent completes work and pushes commits, **When** the completion check runs, **Then** the pipeline verifies the presence of new commits before advancing.
3. **Given** a transient GitHub API failure occurs during issue creation, **When** the request fails, **Then** the system retries the operation with exponential backoff rather than silently failing.

---

### User Story 3 — Eliminate Duplicated Code Patterns (Priority: P2)

A developer working on the codebase encounters consistent, centralized patterns for common operations — repository resolution, API header construction, cache size limiting, and PR search filtering. There is one canonical way to perform each of these operations rather than copy-pasted variants scattered across modules.

**Why this priority**: DRY violations increase the surface area for inconsistent bugs and make maintenance expensive. Centralizing these patterns reduces the chance that a fix in one place is missed in another.

**Independent Test**: Can be fully tested by searching the codebase for the known duplicated patterns and confirming each has been consolidated into a single shared utility, with all call sites using the shared version.

**Acceptance Scenarios**:

1. **Given** an API endpoint needs the current repository owner and name, **When** the endpoint resolves the repository, **Then** it uses a single shared utility function rather than inline resolution logic.
2. **Given** a service needs to make a GitHub REST API call, **When** it constructs HTTP headers, **Then** it uses a shared header-builder method rather than inline dictionary construction.
3. **Given** an in-memory cache reaches its size threshold, **When** the pruning logic runs, **Then** all caches use the same centralized pruning utility with configurable thresholds.
4. **Given** a PR search needs Copilot-author filtering, **When** the filtering runs, **Then** it delegates to a single shared filter function.

---

### User Story 4 — Robust Error Handling & API Responses (Priority: P2)

A user or integration consuming the API receives correct HTTP semantics — rate limit responses include a Retry-After header, stub endpoints either function fully or clearly indicate they are not yet implemented, and error responses contain actionable information.

**Why this priority**: Incorrect error responses cause clients to retry too aggressively (missing Retry-After), assume operations succeeded when they didn't (stub endpoints returning 200), or fail to diagnose problems (generic error messages).

**Independent Test**: Can be fully tested by triggering a rate limit condition and verifying the response includes the Retry-After header, and by calling the task status update endpoint and verifying it either updates GitHub or returns a 501 Not Implemented status.

**Acceptance Scenarios**:

1. **Given** the GitHub API returns a rate limit error with a retry-after value, **When** the system returns a 429 response, **Then** the response includes a `Retry-After` header with the correct value.
2. **Given** a user calls the task status update endpoint, **When** the endpoint processes the request, **Then** it either performs the actual GitHub project item status update or returns a 501 Not Implemented response.
3. **Given** an internal service encounters an error with contextual metadata, **When** the error propagates to the API layer, **Then** the response preserves relevant context without leaking internal implementation details.

---

### User Story 5 — Reliable Real-Time Frontend Updates (Priority: P2)

A user viewing the project board receives consistent real-time updates. When the WebSocket connection is established, redundant polling stops. When the WebSocket disconnects, polling resumes with exponential backoff on reconnection attempts to avoid thundering-herd behavior.

**Why this priority**: Running both WebSocket and polling simultaneously wastes resources and can cause UI flicker from out-of-order updates. Lack of backoff on reconnection can overwhelm the server after a restart.

**Independent Test**: Can be fully tested by establishing a WebSocket connection and verifying polling stops, then severing the connection and verifying reconnection attempts use increasing delays.

**Acceptance Scenarios**:

1. **Given** the frontend successfully connects via WebSocket, **When** the connection is established, **Then** HTTP polling for board updates is paused.
2. **Given** the WebSocket connection drops, **When** the frontend attempts to reconnect, **Then** reconnection delays increase exponentially up to a maximum interval.
3. **Given** the WebSocket reconnection succeeds, **When** the connection is re-established, **Then** polling is paused again and the board state is refreshed.

---

### User Story 6 — Security Hardening (Priority: P1)

Sensitive data (access tokens) stored by the application is protected appropriately. Webhook payloads from GitHub are verified against the webhook secret before processing. Settings that control application behavior (AI provider, polling intervals, agent mappings) are protected from unauthorized modification.

**Why this priority**: Unencrypted tokens, unverified webhooks, and unprotected settings endpoints are direct security vulnerabilities that can lead to account compromise, data tampering, or service abuse.

**Independent Test**: Can be fully tested by inspecting stored tokens for encryption, sending an unsigned webhook payload and verifying rejection, and attempting to modify settings without appropriate authorization.

**Acceptance Scenarios**:

1. **Given** a user authenticates via OAuth, **When** the access token is stored, **Then** the token is encrypted at rest and is not readable as plaintext from the database.
2. **Given** a webhook request arrives without a valid signature, **When** the webhook handler processes the request, **Then** the request is rejected with a 401 or 403 status.
3. **Given** a user without administrative privileges attempts to change global settings, **When** the request reaches the settings endpoint, **Then** the system denies the change and returns an authorization error.

---

### User Story 7 — Meaningful Health Checks (Priority: P3)

An operations team monitoring the application can determine whether the system is truly healthy — not just that the process is running, but that the database is reachable, the GitHub API is accessible, and the background polling loop is active.

**Why this priority**: A health endpoint that always returns "ok" masks real failures, causing load balancers and orchestrators to route traffic to broken instances.

**Independent Test**: Can be fully tested by taking the database offline and verifying the health endpoint reports unhealthy.

**Acceptance Scenarios**:

1. **Given** the database is unreachable, **When** the health endpoint is called, **Then** it returns an unhealthy status indicating the database is down.
2. **Given** all subsystems are operational, **When** the health endpoint is called, **Then** it returns a healthy status with individual component check results.
3. **Given** the background polling loop has crashed, **When** the health endpoint is called, **Then** it reports the polling loop as unhealthy.

---

### User Story 8 — Clean Module Boundaries & Dependency Injection (Priority: P3)

A developer adding a new feature or writing tests can rely on consistent dependency injection patterns. No service accesses private attributes of another service. Import cycles are resolved through proper architectural layering rather than runtime try/except hacks.

**Why this priority**: Inconsistent DI and private attribute access make the codebase fragile — changes to internal implementations break unrelated modules, and runtime import hacks mask real errors.

**Independent Test**: Can be fully tested by running a static analysis check confirming no cross-module private attribute access and that all service dependencies are injected via constructor or framework DI.

**Acceptance Scenarios**:

1. **Given** a service needs to call another service, **When** the call is made, **Then** it uses a public method on the dependency's interface rather than accessing private attributes.
2. **Given** a circular dependency exists between modules, **When** the dependency is resolved, **Then** it uses an architectural pattern (interface extraction, event bus, or dependency inversion) rather than runtime try/except imports.
3. **Given** the chat API module needs the WebSocket connection manager, **When** the dependency is used, **Then** it is injected via the framework's dependency injection mechanism.

---

### Edge Cases

- What happens when the GitHub API is completely unreachable during a pipeline stage transition? The system should mark the stage as failed-pending-retry rather than silently dropping the transition.
- What happens when two polling loop iterations race to advance the same pipeline stage? The system should use optimistic concurrency or a locking mechanism to prevent double-advancement.
- What happens when an in-memory cache (`_pipeline_states`, `_processed_issue_prs`, etc.) grows past its threshold while a pipeline operation is in progress? The pruning should not remove entries for actively running pipelines.
- What happens when a GraphQL issue has more than 100 comments? The system should paginate through all comments rather than silently truncating.
- What happens when a user's OAuth token expires or is revoked while a pipeline is running? The system should detect the 401 and surface the error to the user rather than retrying indefinitely.
- What happens when the `useWorkflow` hook fetches config while a mutation is in flight? Using a query instead of a mutation for reads avoids this race condition.

## Requirements *(mandatory)*

### Functional Requirements

#### Security

- **FR-001**: System MUST NOT expose session tokens in URL query parameters, browser history, Referer headers, or server access logs.
- **FR-002**: System MUST disable developer-only login endpoints when running outside of development mode.
- **FR-003**: System MUST encrypt stored access tokens at rest; plaintext tokens MUST NOT be readable from the database.
- **FR-004**: System MUST verify the cryptographic signature of incoming webhook payloads before processing them.
- **FR-005**: System MUST enforce authorization checks on settings modification endpoints so that only the session owner (the first authenticated user or app deployer) can change global configuration.
- **FR-006**: System MUST automatically expire and remove stale OAuth state entries after a configurable timeout (default: 10 minutes).

#### Pipeline Correctness

- **FR-007**: System MUST verify that new commits exist on the agent's branch before marking a pipeline stage as complete. Agent unassignment alone is NOT a sufficient completion signal.
- **FR-008**: System MUST retry issue creation failures using the existing retry-with-backoff mechanism rather than making a single unretried request.
- **FR-009**: System MUST include the `Retry-After` header in 429 (rate limit) responses when the upstream retry-after value is known.
- **FR-010**: Task status update endpoint MUST either perform the actual status update on GitHub or return a 501 Not Implemented response — it MUST NOT return a success response for unimplemented functionality.

#### Code Quality & DRY

- **FR-011**: System MUST consolidate repository resolution logic (owner/name lookup from settings) into a single shared utility used by all API endpoints.
- **FR-012**: System MUST consolidate GitHub REST API header construction into a single shared method used by all service methods that make REST calls.
- **FR-013**: System MUST consolidate in-memory cache pruning into a single reusable utility with configurable size thresholds.
- **FR-014**: System MUST consolidate Copilot-author PR filtering logic into a single shared function.
- **FR-015**: System MUST eliminate cross-module private attribute access; all inter-service communication MUST use public methods.
- **FR-016**: System MUST resolve circular dependencies through proper architectural patterns rather than runtime try/except import guards.

#### Real-Time & Resilience

- **FR-017**: Frontend MUST stop HTTP polling when a WebSocket connection is successfully established.
- **FR-018**: Frontend MUST use exponential backoff for WebSocket reconnection attempts.
- **FR-019**: Frontend MUST use a read-oriented data fetching pattern (query) rather than a mutation for fetching workflow configuration.
- **FR-020**: System health endpoint MUST check database connectivity, GitHub API reachability, and background polling loop status — not return a static success response.
- **FR-021**: System MUST paginate GitHub GraphQL queries for issue comments rather than limiting to a fixed maximum of 100.
- **FR-022**: System MUST remove configurable hardcoded sleep delays from pipeline status transitions and replace them with configurable timing parameters.
- **FR-023**: System MUST implement bounded growth for in-memory state maps (`_pipeline_states`, `_issue_main_branches`, `_issue_sub_issue_map`, `_transitions`) with consistent pruning that protects actively-running pipeline entries.
- **FR-024**: System MUST add a request-ID middleware that generates or propagates a unique correlation ID per HTTP request and includes it in response headers for debugging.

### Key Entities

- **Session**: Represents an authenticated user session; contains a session identifier and references the user's encrypted access token. Related to User.
- **OAuth State**: A temporary record of an in-progress OAuth flow; contains a state parameter, creation timestamp, and expiry. Automatically cleaned after timeout.
- **Pipeline State**: Tracks the current stage and progress of an AI agent pipeline for a given issue; includes stage identifier, assigned agent, branch reference, and completion status. Related to Issue.
- **In-Memory Cache**: A bounded collection of processing records (processed PRs, posted outputs, claimed PRs, etc.) with a maximum size threshold and a pruning strategy. Shared utility parameterized per cache purpose.
- **Health Status**: A composite check result containing individual component statuses (database, GitHub API, polling loop) and an overall health determination.

## Assumptions

- The application will continue to use SQLite as its database for the near term; encryption-at-rest for tokens will use application-level Fernet symmetric encryption. The encryption key is read from an `ENCRYPTION_KEY` environment variable; if absent on first startup, the app auto-generates a key, uses it for the session, and logs a warning instructing the operator to persist it for future restarts.
- "Production mode" vs. "development mode" is determined by the existing `debug: bool = False` field in the Settings model. Developer-only features (e.g., dev-login endpoint) are gated behind `debug=True`. No new environment variable is needed.
- Authorization for settings endpoints will use a session-owner check: the first authenticated user (or app deployer) is treated as the sole admin. No external role lookup or configurable admin list is required.
- Webhook signature verification will use GitHub's standard HMAC-SHA256 mechanism with a configured webhook secret.
- The existing test suite (926+ tests) will be extended to cover the new behaviors introduced by this bug bash, not rewritten.
- Hardcoded sleep delays will be replaced with values sourced from settings/configuration, defaulting to current values to avoid behavioral change for existing deployments.

## Out of Scope

- Database migration (e.g., SQLite to PostgreSQL) — the application continues on SQLite for this effort.
- Full role-based access control (RBAC) system — authorization is limited to a session-owner admin check.
- New user-facing features — this effort fixes existing bugs and improves code quality only.
- UI redesign or visual overhaul — frontend changes are limited to behavioral fixes (polling/WebSocket, data fetching patterns).
- Architectural rewrite of the polling loop to an event-driven model — fixes are scoped to correctness and configurability of the existing polling mechanism.
- Full structured JSON logging overhaul — only a request-ID correlation middleware is in scope; converting all log statements to structured format is deferred.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero session tokens appear in URL query strings across all authentication flows — verified by automated test and log inspection.
- **SC-002**: Developer-only login endpoint returns 404/403 in production mode — verified by integration test.
- **SC-003**: Pipeline does not advance when an agent is unassigned without new commits — verified by unit test simulating the false-positive scenario.
- **SC-004**: All 429 responses from the API include a `Retry-After` header — verified by unit test.
- **SC-005**: Known DRY violations (repository resolution, header construction, cache pruning, PR filtering) are each reduced to a single implementation — verified by grep/search confirming no duplicated patterns remain.
- **SC-006**: All inter-service calls use public methods only — verified by static analysis or code review confirming no `_private` attribute access across module boundaries.
- **SC-007**: WebSocket connection establishment stops HTTP polling — verified by frontend unit test.
- **SC-008**: Health endpoint returns unhealthy when the database is unreachable — verified by integration test.
- **SC-009**: Webhook requests without valid signatures are rejected — verified by integration test sending an unsigned payload.
- **SC-010**: Existing test suite continues to pass with no regressions — verified by full test suite run.
