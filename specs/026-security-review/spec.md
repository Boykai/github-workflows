# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `026-security-review`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Security, Privacy & Vulnerability Audit — 3 Critical, 8 High, 9 Medium, 2 Low findings across OWASP Top 10. Phased remediation plan covering authentication, authorization, container hardening, HTTP security, rate limiting, and data protection."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Credentials Never Appear in URLs (Priority: P1)

A user initiates the OAuth login flow to authenticate with the application. After authorizing with GitHub, the browser is redirected back to the application. At no point does a session token, access token, or personal access token appear in the browser URL bar, browser history, or HTTP Referer headers. The user is seamlessly authenticated via a secure cookie set by the backend.

**Why this priority**: Credentials in URLs are the highest-severity finding (OWASP A02, Critical). Tokens in URLs are passively leaked to browser history, proxy logs, CDN logs, and third-party analytics. This is the most exploitable vulnerability and must be fixed before any other change.

**Independent Test**: Can be fully tested by completing the OAuth login flow, inspecting the browser URL bar and history for any token parameters, and verifying authentication works via an HttpOnly cookie instead.

**Acceptance Scenarios**:

1. **Given** a user completes GitHub OAuth authorization, **When** the browser is redirected back to the application, **Then** the URL contains no `session_token`, `access_token`, or any credential parameters.
2. **Given** a user has completed login, **When** inspecting browser history, **Then** no entry contains credential values in the URL.
3. **Given** the backend processes an OAuth callback, **When** it redirects to the frontend, **Then** it sets an HttpOnly, SameSite=Strict, Secure cookie containing the session credential.
4. **Given** the dev login endpoint is used, **When** a developer authenticates, **Then** credentials are submitted via a POST request body (JSON), never as URL query parameters.

---

### User Story 2 — Application Refuses to Start Without Required Secrets (Priority: P1)

An operator deploys the application in production (non-debug) mode. If any required secret — encryption key, webhook secret, or session secret key — is missing or insufficiently strong, the application refuses to start and logs a clear error message explaining which configuration is missing or invalid. This prevents silent misconfiguration that could lead to plaintext data storage or insecure sessions.

**Why this priority**: Missing encryption and weak secrets are Critical/High findings (OWASP A02, A07). Without enforcement, production deployments can silently run with plaintext token storage, no webhook verification, or guessable session keys.

**Independent Test**: Can be fully tested by attempting to start the application in non-debug mode with each required secret missing or invalid, and verifying it fails with a clear error message each time.

**Acceptance Scenarios**:

1. **Given** the application is started in non-debug mode, **When** `ENCRYPTION_KEY` is not set, **Then** the application refuses to start and logs an error indicating the missing key.
2. **Given** the application is started in non-debug mode, **When** `GITHUB_WEBHOOK_SECRET` is not set, **Then** the application refuses to start and logs an error indicating the missing secret.
3. **Given** the application is started in non-debug mode, **When** `SESSION_SECRET_KEY` is shorter than 64 characters, **Then** the application refuses to start and logs an error indicating insufficient key length.
4. **Given** the application is started in non-debug mode, **When** cookie Secure flag is not enabled, **Then** the application refuses to start and logs an error indicating the misconfiguration.
5. **Given** the application is started in debug mode, **When** optional secrets are missing, **Then** the application starts with a warning (development convenience is preserved).

---

### User Story 3 — Containers Run as Non-Root Users (Priority: P1)

An operator deploys the application using Docker containers. Every container — frontend and backend — runs as a dedicated non-root system user. If an attacker exploits a vulnerability in the application, they cannot escalate to root privileges within the container.

**Why this priority**: Running containers as root is a Critical finding (OWASP A05). A root-level container compromise grants the attacker full control over the container filesystem and increases the blast radius of any exploit.

**Independent Test**: Can be fully tested by running `docker exec` into each container and verifying that `id` returns a non-root UID.

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** an operator runs `id` inside the container, **Then** the output shows a non-root UID (not uid=0).
2. **Given** the backend container is running, **When** an operator runs `id` inside the container, **Then** the output shows a non-root UID (not uid=0).
3. **Given** the frontend container runs as non-root, **When** the nginx process serves requests, **Then** all functionality continues to work correctly.

---

### User Story 4 — Users Can Only Access Their Own Projects (Priority: P1)

An authenticated user interacts with project-related features — creating tasks, subscribing to WebSocket updates, modifying project settings, or triggering workflows. The system verifies the user owns or has access to the target project before performing any action. If a user attempts to access another user's project (e.g., by guessing or manipulating a project ID), the request is rejected with a 403 Forbidden response.

**Why this priority**: Missing authorization checks are a High finding (OWASP A01) — the #1 item on the OWASP Top 10. Any authenticated user could access, modify, or delete another user's project data by simply changing the project ID in requests.

**Independent Test**: Can be fully tested by authenticating as User A, attempting to access User B's project via API, and verifying the response is 403 Forbidden.

**Acceptance Scenarios**:

1. **Given** User A is authenticated, **When** they request a project they own, **Then** the request succeeds normally.
2. **Given** User A is authenticated, **When** they send a request with User B's project ID, **Then** the response is 403 Forbidden with no data leaked.
3. **Given** User A is authenticated, **When** they attempt a WebSocket connection to User B's project, **Then** the connection is rejected before any data is sent.
4. **Given** an authorization check is centralized, **When** any new endpoint is added that accepts a project ID, **Then** it inherits the authorization check automatically via the shared dependency.

---

### User Story 5 — Security Headers Protect Users from Common Web Attacks (Priority: P2)

A user accesses the application through their browser. The HTTP response headers include modern security protections: Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy. The nginx server does not reveal its version. These headers protect users from cross-site scripting, clickjacking, MIME-type attacks, and information leakage.

**Why this priority**: Missing security headers are a High finding (OWASP A05). While not directly exploitable on their own, they are a critical defense-in-depth layer that reduces the impact of other vulnerabilities (especially XSS).

**Independent Test**: Can be fully tested by sending an HTTP HEAD request to the frontend and inspecting the response headers for the presence of all required security headers and the absence of the nginx version string.

**Acceptance Scenarios**:

1. **Given** a user makes any HTTP request to the frontend, **When** they inspect response headers, **Then** `Content-Security-Policy` is present and configured.
2. **Given** a user makes any HTTP request to the frontend, **When** they inspect response headers, **Then** `Strict-Transport-Security` is present.
3. **Given** a user makes any HTTP request to the frontend, **When** they inspect response headers, **Then** `Referrer-Policy` is present and set to a restrictive value.
4. **Given** a user makes any HTTP request to the frontend, **When** they inspect response headers, **Then** `Permissions-Policy` is present.
5. **Given** a user makes any HTTP request to the frontend, **When** they inspect the `Server` header, **Then** the nginx version number is not disclosed.
6. **Given** the existing `X-XSS-Protection` header, **When** the security headers are updated, **Then** it is removed (deprecated in modern browsers).

---

### User Story 6 — Timing-Safe Secret Comparisons Prevent Side-Channel Attacks (Priority: P2)

The system compares secrets (webhook signatures, tokens) using constant-time comparison functions throughout the codebase. An attacker who sends many requests with different secret values cannot determine the correct secret by measuring response times.

**Why this priority**: Timing attacks are a High finding (OWASP A07). While harder to exploit remotely, they allow methodical secret recovery and are trivial to fix with constant-time comparison functions.

**Independent Test**: Can be fully tested via code review confirming all secret/token comparisons use constant-time functions.

**Acceptance Scenarios**:

1. **Given** a webhook request arrives with a signature, **When** the signature is compared to the expected value, **Then** a constant-time comparison function is used.
2. **Given** any code path compares secrets or tokens, **When** reviewed, **Then** no standard string equality operators (`==`, `!=`) are used for secret comparison.

---

### User Story 7 — OAuth Scope Follows Least Privilege (Priority: P2)

The application requests only the minimum necessary OAuth scopes from GitHub. Instead of the broad `repo` scope (full read/write to all private repositories), the application requests only the specific scopes needed for project management operations.

**Why this priority**: Over-scoped OAuth is a High finding (OWASP A01). If a user's token is compromised, the attacker gains full access to all private repositories instead of just project management data.

**Independent Test**: Can be fully tested by initiating the OAuth flow, inspecting the GitHub authorization page for requested scopes, and verifying all application write operations still function with the reduced scopes.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** they reach the GitHub authorization page, **Then** only minimum necessary scopes are requested (not `repo`).
2. **Given** the application uses reduced scopes, **When** users perform all supported project management operations, **Then** all operations succeed without errors.
3. **Given** existing users had authorized with broad scopes, **When** the scope is narrowed, **Then** a migration path is provided (users re-authorize on next login).

---

### User Story 8 — Rate Limiting Prevents Abuse of Expensive Endpoints (Priority: P2)

The system enforces rate limits on expensive and sensitive endpoints — chat, agent invocation, workflow triggers, and OAuth callbacks. When a user or IP exceeds the rate limit, they receive a 429 Too Many Requests response. This prevents a single user from exhausting shared AI/GitHub quotas and protects the OAuth callback from brute-force attacks.

**Why this priority**: Missing rate limiting is a Medium finding (OWASP A04), but it directly impacts availability and cost. A single abusive user can exhaust shared resources, affecting all other users.

**Independent Test**: Can be fully tested by sending requests above the rate limit threshold and verifying 429 responses are returned.

**Acceptance Scenarios**:

1. **Given** a user sends requests to an AI/chat endpoint, **When** they exceed the per-user rate limit, **Then** subsequent requests return 429 Too Many Requests.
2. **Given** an IP sends requests to the OAuth callback endpoint, **When** it exceeds the per-IP rate limit, **Then** subsequent requests return 429 Too Many Requests.
3. **Given** rate limits are configured, **When** a user is within their allowed rate, **Then** requests are processed normally with no degradation.
4. **Given** rate limits are per-user (not per-IP), **When** multiple users share a NAT/VPN IP, **Then** each user has their own independent rate limit.

---

### User Story 9 — Sensitive Data is Protected at Rest and in Transit (Priority: P2)

Sensitive data — OAuth tokens, chat history, and the SQLite database — are protected both at rest and in the browser. OAuth tokens are encrypted before storage. Chat history is not persisted in plaintext in the browser's localStorage. The database directory and file have restricted permissions so only the application user can read them.

**Why this priority**: Multiple Medium findings (OWASP A02) relate to data protection. Collectively they represent significant risk: plaintext tokens, world-readable database files, and persistent browser storage that survives logout.

**Independent Test**: Can be fully tested by checking database file permissions (0700 directory, 0600 file), verifying localStorage contains no message content after logout, and confirming tokens are encrypted in the database.

**Acceptance Scenarios**:

1. **Given** the database directory is created, **When** checking file permissions, **Then** the directory is 0700 and the database file is 0600.
2. **Given** a user logs out, **When** inspecting browser localStorage, **Then** no chat message content is stored (only lightweight references with TTL if any).
3. **Given** OAuth tokens are stored, **When** inspecting the database directly, **Then** tokens are encrypted (not plaintext).

---

### User Story 10 — Secure Configuration and Infrastructure Defaults (Priority: P3)

The application's infrastructure configuration follows security best practices: Docker services are not exposed on all network interfaces, data volumes are mounted outside the application directory, CORS origins are validated, webhook verification is never bypassed, API documentation is gated on a dedicated toggle, and GraphQL errors do not expose internal details.

**Why this priority**: These are Medium and Low findings that harden the overall security posture. Individually each has limited impact, but collectively they reduce the attack surface significantly.

**Independent Test**: Can be tested by reviewing Docker Compose configuration, verifying CORS validation rejects malformed origins, confirming webhook verification is not debug-conditional, and checking GraphQL error responses are sanitized.

**Acceptance Scenarios**:

1. **Given** the Docker Compose configuration for development, **When** services bind ports, **Then** they bind to `127.0.0.1` only (not `0.0.0.0`).
2. **Given** a CORS origin environment variable contains a malformed URL, **When** the application starts, **Then** it fails with a clear error message.
3. **Given** debug mode is enabled, **When** a webhook arrives without a signature, **Then** verification is still enforced (debug mode does not bypass security).
4. **Given** the API documentation toggle, **When** `ENABLE_DOCS` is not set, **Then** Swagger/ReDoc are not accessible regardless of DEBUG setting.
5. **Given** a GitHub GraphQL API call fails, **When** the error is returned to the API consumer, **Then** only a generic sanitized message is returned (no query structure or token details).
6. **Given** the data volume mount, **When** reviewing the Docker Compose file, **Then** the volume is mounted outside the application root directory.
7. **Given** the GitHub Actions workflow file, **When** reviewing permissions, **Then** `issues: write` is scoped to minimum needed with a justification comment.
8. **Given** an avatar URL is received from the GitHub API, **When** it is rendered in the UI, **Then** only `https:` URLs from known GitHub avatar domains are accepted; others show a placeholder.

---

### Edge Cases

- What happens when an existing deployment has plaintext encrypted tokens and `ENCRYPTION_KEY` is now mandatory? A migration path must be provided for existing data rows.
- What happens when OAuth scopes are narrowed and a user's existing token was granted with broader scopes? Users must re-authorize on next login.
- What happens when the rate limit is hit during an active chat conversation? The user receives a clear 429 response with retry-after information; no partial or corrupted state results.
- What happens when a WebSocket connection is established and then project ownership changes? The connection should be validated at establishment time; existing connections are not retroactively terminated.
- What happens when `ENABLE_DOCS` is set but `DEBUG` is false? API docs should be available (the two settings are independent).
- What happens when a GitHub avatar URL uses `http:` instead of `https:`? The URL is rejected and a placeholder avatar is shown.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST set session credentials via HttpOnly, SameSite=Strict, Secure cookies on the OAuth callback response, never placing credentials in URL parameters.
- **FR-002**: Frontend MUST NOT read authentication credentials from URL parameters.
- **FR-003**: System MUST refuse to start in non-debug mode if `ENCRYPTION_KEY` is not set.
- **FR-004**: System MUST refuse to start in non-debug mode if `GITHUB_WEBHOOK_SECRET` is not set.
- **FR-005**: All containers MUST run as a dedicated non-root system user with a non-zero UID.

**Phase 2 — High**

- **FR-006**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action.
- **FR-007**: Project authorization MUST be implemented as a centralized shared dependency (not duplicated per endpoint).
- **FR-008**: WebSocket connections MUST verify project ownership before accepting the connection.
- **FR-009**: All secret and token comparisons MUST use constant-time comparison functions.
- **FR-010**: The frontend MUST include Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy response headers.
- **FR-011**: The deprecated X-XSS-Protection header MUST be removed.
- **FR-012**: The frontend web server MUST NOT disclose its version via the Server response header.
- **FR-013**: The dev login endpoint MUST accept credentials via POST request body (JSON), not URL query parameters.
- **FR-014**: OAuth authorization MUST request minimum necessary scopes instead of the broad `repo` scope.
- **FR-015**: System MUST reject `SESSION_SECRET_KEY` values shorter than 64 characters at startup.
- **FR-016**: Docker services in development MUST bind to `127.0.0.1` only, not `0.0.0.0`.

**Phase 3 — Medium**

- **FR-017**: Per-user rate limits MUST be enforced on chat, agent invocation, and workflow endpoints.
- **FR-018**: Per-IP rate limits MUST be enforced on the OAuth callback endpoint.
- **FR-019**: Rate-limited requests MUST return HTTP 429 Too Many Requests.
- **FR-020**: System MUST refuse to start in non-debug mode if cookie Secure flag is not enabled.
- **FR-021**: Webhook signature verification MUST NOT be conditional on debug mode.
- **FR-022**: API documentation (Swagger/ReDoc) availability MUST be controlled by a dedicated `ENABLE_DOCS` environment variable, independent of `DEBUG`.
- **FR-023**: Database directory MUST be created with 0700 permissions; database files MUST have 0600 permissions.
- **FR-024**: CORS origins MUST be validated as well-formed URLs with scheme and hostname at startup; malformed values MUST cause startup failure.
- **FR-025**: Data volumes MUST be mounted outside the application root directory.
- **FR-026**: Browser localStorage MUST NOT store full chat message content; only lightweight references (message IDs) with a TTL are permitted.
- **FR-027**: All local data MUST be cleared on user logout.
- **FR-028**: GraphQL error messages from GitHub API MUST be logged internally but MUST NOT be exposed in API responses; only generic sanitized messages are returned.

**Phase 4 — Low**

- **FR-029**: GitHub Actions workflow permissions MUST be scoped to the minimum needed with justification comments.
- **FR-030**: Avatar URLs MUST be validated to use `https:` protocol and originate from known GitHub avatar domains before rendering; invalid URLs MUST fall back to a placeholder image.

### Key Entities

- **Session**: Represents an authenticated user session. Contains a session token stored in an HttpOnly cookie, linked to a user identity and their authorized project access.
- **Project**: Represents a GitHub project managed by a user. Has an owner relationship that must be verified on every access. Key attributes: project ID, owner user ID.
- **OAuth Token**: Represents a user's GitHub OAuth token. Stored encrypted at rest. Associated with specific OAuth scopes. Must be re-issued when scopes change.
- **Rate Limit**: Tracks request counts per user (or per IP for specific endpoints). Key attributes: identifier (user ID or IP), endpoint category, request count, time window, threshold.
- **Chat Message Reference**: A lightweight pointer to a chat message stored in the backend. Contains only a message ID and a TTL timestamp. Full message content is loaded on demand from the backend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, no credentials appear in the browser URL bar, browser history, or server access logs — verified by automated end-to-end test and manual inspection.
- **SC-002**: Application refuses to start in non-debug mode when any required secret is missing or invalid — verified by startup tests for each required configuration value.
- **SC-003**: All containers run as non-root — verified by `id` command returning non-zero UID in every container.
- **SC-004**: Authenticated requests targeting an unowned project return 403 Forbidden — verified by cross-user API tests returning 403 with no data leakage.
- **SC-005**: WebSocket connections to unowned projects are rejected before any data is sent — verified by connection rejection test.
- **SC-006**: All secret comparisons in the codebase use constant-time functions — verified by code review and static analysis.
- **SC-007**: Frontend HTTP responses include Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers; no nginx version is disclosed — verified by HTTP HEAD request inspection.
- **SC-008**: Expensive endpoints return 429 Too Many Requests when rate limits are exceeded — verified by rate limit threshold tests.
- **SC-009**: After logout, browser localStorage contains no chat message content — verified by browser devtools inspection.
- **SC-010**: Database directory permissions are 0700 and file permissions are 0600 — verified by filesystem inspection inside the container.
- **SC-011**: 100% of the 21 identified security findings are addressed with corresponding verification checks passing.
- **SC-012**: Zero Critical or High findings remain unresolved after Phase 2 completion.

### Assumptions

- The application has two deployment modes: debug (development) and non-debug (production). Security enforcement is strict in non-debug mode; debug mode may be more permissive for developer convenience but never disables security verification (e.g., webhook signatures).
- The backend framework is FastAPI-compatible, allowing use of dependency injection for centralized authorization checks and middleware for rate limiting.
- The frontend is a React single-page application served by nginx.
- The existing backend already runs as a non-root user; only the frontend container needs this change.
- GitHub avatar URLs originate from domains like `avatars.githubusercontent.com` — this is the known domain to allowlist.
- Existing deployments without `ENCRYPTION_KEY` will need a one-time migration to encrypt existing plaintext OAuth tokens before the enforcement takes effect.
- Rate limiting uses per-user identification (preferred over per-IP) to avoid penalizing users behind shared NAT/VPN connections. Per-IP is used only for unauthenticated endpoints like OAuth callback.
- OAuth scope changes will require existing users to re-authorize on their next login.

### Out of Scope

- GitHub API security (GitHub's own platform security).
- MCP server internals.
- Network-layer infrastructure (firewalls, load balancers, DNS).
- Penetration testing or red-team exercises.
- Compliance certifications (SOC 2, ISO 27001, etc.).

### Dependencies

- The OAuth scope reduction (FR-014) requires staging environment testing to verify all write operations work with narrower scopes before deployment to production.
- The encryption enforcement (FR-003) requires a data migration path for existing deployments with plaintext OAuth tokens.
- Rate limiting (FR-017, FR-018) depends on a FastAPI-compatible rate limiting solution being available.
