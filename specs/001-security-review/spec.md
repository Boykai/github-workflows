# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `001-security-review`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Security Review — 3 Critical · 8 High · 9 Medium · 2 Low findings across OWASP Top 10"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Authentication Flow (Priority: P1)

As a user logging in via OAuth, I expect my session credentials to never appear in the browser URL bar, browser history, server access logs, or HTTP Referer headers. After authentication completes, I am redirected to the application with my session established securely and invisibly.

**Why this priority**: Credential exposure in URLs is the most immediately exploitable vulnerability (OWASP A02, Critical). Tokens in URLs can be harvested from browser history, proxy logs, and Referer headers without any attacker access to the application itself. This is the highest-risk finding.

**Independent Test**: Complete an OAuth login flow and verify no credentials appear in the browser URL at any point. Inspect browser history and network requests to confirm tokens are never transmitted as URL parameters.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth callback completes, **Then** the session is established via a secure, HttpOnly, SameSite-Strict cookie — no credentials appear in the URL
2. **Given** a user has completed login, **When** inspecting browser history and network logs, **Then** no session tokens or credentials are present in any URL
3. **Given** a developer uses the dev login endpoint, **When** submitting credentials, **Then** the credentials are sent in the request body (not as URL parameters)

---

### User Story 2 - Mandatory Encryption and Secret Enforcement (Priority: P1)

As a platform operator deploying the application to production, I expect the system to refuse to start if critical security configuration is missing. This prevents accidental deployment of an insecure instance that stores sensitive data in plaintext or accepts unsigned webhook payloads.

**Why this priority**: Without mandatory encryption enforcement, OAuth tokens are stored in plaintext and webhook secrets may be absent — both Critical/High severity findings (OWASP A02, A07). A single misconfigured deployment exposes all user tokens.

**Independent Test**: Attempt to start the application in production mode without setting the encryption key, webhook secret, or session secret. Verify the application fails to start with a clear error message for each missing value.

**Acceptance Scenarios**:

1. **Given** the application is starting in production mode, **When** the encryption key is not configured, **Then** the application refuses to start and logs an error identifying the missing configuration
2. **Given** the application is starting in production mode, **When** the webhook secret is not configured, **Then** the application refuses to start and logs an error identifying the missing configuration
3. **Given** the application is starting in production mode, **When** the session secret key is shorter than 64 characters, **Then** the application refuses to start and logs an error about insufficient key length
4. **Given** the application is starting in production mode, **When** cookies are not configured as Secure, **Then** the application refuses to start and logs an error about insecure cookie configuration

---

### User Story 3 - Project-Level Access Control (Priority: P1)

As a user with multiple projects, I expect that other authenticated users cannot access, modify, or subscribe to my projects. Every operation that targets a project must verify I own or have access to that project before proceeding.

**Why this priority**: Missing authorization checks (OWASP A01, High) allow any authenticated user to access any other user's projects by guessing or enumerating project IDs. This is a fundamental access control failure affecting data confidentiality and integrity.

**Independent Test**: As User A, create a project. As User B, attempt to access User A's project via API. Verify a 403 Forbidden response is returned for all project-scoped operations.

**Acceptance Scenarios**:

1. **Given** User A owns a project, **When** User B attempts to create a task in User A's project, **Then** the system returns a 403 Forbidden response
2. **Given** User A owns a project, **When** User B attempts to subscribe to User A's project via WebSocket, **Then** the connection is rejected before any data is sent
3. **Given** User A owns a project, **When** User B attempts to modify project settings, **Then** the system returns a 403 Forbidden response
4. **Given** User A owns a project, **When** User B attempts to trigger a workflow on User A's project, **Then** the system returns a 403 Forbidden response

---

### User Story 4 - Container and Infrastructure Hardening (Priority: P2)

As a platform operator, I expect all containers to follow the principle of least privilege. No container should run as root, services should not be exposed on all network interfaces, and data volumes should be stored outside the application directory with restrictive permissions.

**Why this priority**: Running containers as root (OWASP A05, Critical) and exposing services on all interfaces (OWASP A05, High) creates a broad attack surface. While these require infrastructure access to exploit, the impact of compromise is severe.

**Independent Test**: Inspect running containers to verify non-root user, check port bindings are restricted, and verify data directory and database file permissions.

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** checking the container's user identity, **Then** the process runs as a non-root system user
2. **Given** the development environment is running, **When** checking port bindings, **Then** services bind to localhost (127.0.0.1) only, not all interfaces
3. **Given** the application is running, **When** checking data directory permissions, **Then** the database directory has 0700 permissions and database files have 0600 permissions
4. **Given** the production container configuration, **When** inspecting volume mounts, **Then** data volumes are mounted outside the application root directory

---

### User Story 5 - HTTP Security Headers and Webhook Integrity (Priority: P2)

As a user accessing the application through a web browser, I expect the server to send modern security headers that protect against common web attacks. As a platform operator, I expect all webhook signature verifications to be tamper-resistant and never bypassed.

**Why this priority**: Missing security headers (OWASP A05, High) leave users vulnerable to clickjacking, XSS, and protocol downgrade attacks. Timing-vulnerable and bypassable webhook verification (OWASP A07, High; A05, Medium) can allow unauthorized workflow triggers.

**Independent Test**: Send an HTTP HEAD request to the frontend and verify all required security headers are present. Review code to confirm all secret comparisons use constant-time functions and webhook verification is never conditional on debug mode.

**Acceptance Scenarios**:

1. **Given** a client makes a request to the frontend, **When** inspecting response headers, **Then** Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers are present
2. **Given** a client makes a request to the frontend, **When** inspecting the Server header, **Then** the web server software version is not disclosed
3. **Given** the deprecated X-XSS-Protection header, **When** inspecting response headers, **Then** it is no longer present
4. **Given** a webhook payload arrives, **When** the system verifies the signature, **Then** a constant-time comparison function is used regardless of debug mode
5. **Given** debug mode is enabled, **When** a webhook arrives without a valid signature, **Then** the webhook is still rejected (verification is never skipped)

---

### User Story 6 - Rate Limiting on Sensitive Endpoints (Priority: P3)

As a platform operator, I expect that no single user or IP address can exhaust shared resources (AI quotas, GitHub API limits) by flooding expensive endpoints. The system must enforce per-user rate limits on write and AI-powered endpoints, and per-IP limits on the OAuth callback.

**Why this priority**: While rate limiting (OWASP A04, Medium) is important for operational stability, it does not expose data or enable unauthorized access. It protects against resource exhaustion and abuse.

**Independent Test**: Send requests exceeding the rate limit threshold to a rate-limited endpoint and verify a 429 Too Many Requests response is returned.

**Acceptance Scenarios**:

1. **Given** a user sends requests to an AI-powered endpoint, **When** the request rate exceeds the per-user limit, **Then** subsequent requests receive a 429 Too Many Requests response
2. **Given** an IP address sends OAuth callback requests, **When** the request rate exceeds the per-IP limit, **Then** subsequent requests receive a 429 Too Many Requests response
3. **Given** a user is rate-limited, **When** the rate limit window expires, **Then** the user can resume making requests normally

---

### User Story 7 - Privacy-Respecting Client-Side Storage (Priority: P3)

As a user, I expect that sensitive data like chat message content is not stored indefinitely in my browser's local storage. On logout, all locally cached data must be cleared. While logged in, only lightweight references should be stored locally, with full content loaded from the server on demand.

**Why this priority**: Storing chat history in localStorage (Privacy/OWASP A02, Medium) creates a data persistence risk that survives logout and is readable by any XSS. Important for privacy but lower urgency than authentication and authorization fixes.

**Independent Test**: Log in, use the chat feature, then log out. Inspect localStorage to verify no message content remains. Verify that while logged in, localStorage contains only message IDs (not full content).

**Acceptance Scenarios**:

1. **Given** a user is logged in and has chat history, **When** inspecting localStorage, **Then** only lightweight message references (IDs) are stored, not full message content
2. **Given** a user logs out, **When** inspecting localStorage, **Then** all application data including message references has been cleared
3. **Given** locally stored message references, **When** the reference age exceeds the configured time-to-live, **Then** the expired references are automatically removed

---

### User Story 8 - Secure Configuration and Error Handling (Priority: P3)

As a platform operator, I expect the system to validate all configuration at startup, sanitize error messages exposed to end users, apply minimum-privilege OAuth scopes, and control API documentation exposure independently of debug mode.

**Why this priority**: These Medium/Low severity items (OWASP A01, A05, A09) reduce the overall attack surface. They are important hardening measures but are less immediately exploitable than Critical and High findings.

**Independent Test**: Start the application with a malformed CORS origin and verify startup fails. Trigger an upstream API error and verify the response contains only a generic message. Verify API documentation is controlled by its own toggle, not by debug mode.

**Acceptance Scenarios**:

1. **Given** a CORS origins configuration with a malformed URL, **When** the application starts, **Then** startup fails with an error identifying the invalid origin
2. **Given** an upstream API returns a detailed error, **When** the error propagates to the user, **Then** only a generic sanitized message is shown; full details are logged internally
3. **Given** debug mode is enabled but the API docs toggle is disabled, **When** accessing the API documentation endpoint, **Then** the documentation is not available
4. **Given** the OAuth configuration, **When** reviewing requested scopes, **Then** only the minimum necessary scopes are requested (not full repository access)
5. **Given** a GitHub Actions workflow, **When** reviewing its permissions, **Then** only the minimum required permission is granted with a justification comment
6. **Given** avatar URLs from external APIs, **When** rendering user avatars, **Then** only HTTPS URLs from known avatar domains are accepted; invalid URLs fall back to a placeholder image

---

### Edge Cases

- What happens when a user's session cookie expires mid-operation? The system must return a 401 Unauthorized response and the user must re-authenticate — no silent failures or data exposure.
- What happens when the encryption key is rotated? Existing encrypted data must remain accessible during a migration window. A migration path for re-encrypting existing rows must be provided.
- What happens when rate limit storage is unavailable? The system should fail open with logging (allow requests but log the rate-limit failure) rather than blocking all traffic.
- What happens when a user has access to a project that is subsequently deleted? The system must handle this gracefully without exposing internal errors.
- What happens when debug mode is accidentally enabled in production? Security controls (webhook verification, encryption enforcement, cookie security) must remain active regardless of debug mode.
- What happens when the OAuth provider changes its scope model? The application should request well-documented, narrow scopes and fail clearly if a required scope is unavailable.
- What happens during a brute-force attempt on project IDs? The 403 response must not reveal whether the project exists (no difference between "not found" and "forbidden" for unauthorized users).
- What happens when the CORS origins list is empty? The system should reject all cross-origin requests rather than allowing all.
- What happens when localStorage is full or unavailable? The application must degrade gracefully without data loss — the chat feature should remain functional by loading all content from the server.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST deliver session credentials via a secure, HttpOnly, SameSite-Strict cookie on the OAuth callback response — never as URL parameters
- **FR-002**: Frontend MUST NOT read or extract credentials from URL parameters at any point in the authentication flow
- **FR-003**: System MUST refuse to start in production mode when the encryption key environment variable is not set
- **FR-004**: System MUST refuse to start in production mode when the webhook secret environment variable is not set
- **FR-005**: All containers MUST run as a dedicated non-root system user with minimal privileges

**Phase 2 — High**

- **FR-006**: Every endpoint and WebSocket connection that accepts a project identifier MUST verify the authenticated user has access to that project before performing any action
- **FR-007**: Project ownership verification MUST be implemented as a shared, centralized check used by all project-scoped operations
- **FR-008**: All secret and token comparisons throughout the codebase MUST use a constant-time comparison function
- **FR-009**: The frontend web server MUST include Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers in all responses
- **FR-010**: The frontend web server MUST remove the deprecated X-XSS-Protection header and MUST NOT disclose its version in the Server header
- **FR-011**: All credential inputs — including development-only endpoints — MUST be transmitted in the request body, never as URL parameters
- **FR-012**: OAuth authorization MUST request only the minimum scopes necessary for the application's functionality
- **FR-013**: System MUST reject session secret keys shorter than 64 characters at startup
- **FR-014**: In development mode, services MUST bind to 127.0.0.1 only; in production mode, services MUST NOT expose ports directly and MUST be accessed only through a reverse proxy

**Phase 3 — Medium**

- **FR-015**: System MUST enforce per-user rate limits on write and AI-powered endpoints
- **FR-016**: System MUST enforce per-IP rate limits on the OAuth callback endpoint
- **FR-017**: Rate-limited endpoints MUST return 429 Too Many Requests when limits are exceeded
- **FR-018**: System MUST refuse to start in production mode when cookie Secure flag is not enabled
- **FR-019**: Webhook signature verification MUST NOT be conditional on debug mode; it MUST always be enforced when a webhook secret is configured
- **FR-020**: API documentation availability MUST be controlled by a dedicated environment variable, independent of the debug mode flag
- **FR-021**: Database directory MUST be created with 0700 permissions; database files MUST be created with 0600 permissions
- **FR-022**: System MUST validate all configured CORS origins as well-formed URLs with a scheme and hostname at startup; malformed values MUST cause startup failure
- **FR-023**: Data volumes MUST be mounted outside the application root directory
- **FR-024**: Client-side chat storage MUST contain only lightweight message references (IDs) with a configurable time-to-live, not full message content
- **FR-025**: All locally stored application data MUST be cleared on user logout
- **FR-026**: Error messages from upstream APIs MUST be logged internally at full detail but MUST be sanitized to a generic message before being returned to users

**Phase 4 — Low**

- **FR-027**: CI/CD workflow permissions MUST be scoped to the minimum required level with a justification comment
- **FR-028**: External avatar URLs MUST be validated to use HTTPS and originate from a known avatar domain; invalid URLs MUST fall back to a placeholder image

### Key Entities

- **Session**: Represents an authenticated user's active session; attributes include user identity, creation timestamp, expiration, and associated project access grants. Stored server-side; referenced client-side via a secure cookie.
- **Project**: A user-owned workspace; attributes include owner identity, name, and associated tasks/workflows. Central to authorization checks — all operations scoped to a project require verified ownership.
- **Encryption Key**: A server-side secret used for at-rest encryption of sensitive data (OAuth tokens). Must be present in production; absent key triggers startup failure.
- **Rate Limit Record**: Tracks request counts per user (or per IP for anonymous endpoints) within a time window. Attributes include identifier, endpoint, count, and window expiration.
- **Chat Message Reference**: A lightweight client-side pointer to a server-stored message; attributes include message ID and a TTL. Full message content is loaded from the server on demand.

## Assumptions

- The application uses an OAuth-based authentication flow with a single OAuth provider (GitHub).
- "Production mode" is determined by a debug/environment flag (e.g., `DEBUG=false`); all mandatory security checks apply when this flag indicates production.
- The backend already runs as a non-root user; the finding applies specifically to the frontend container.
- A migration path for existing plaintext-encrypted data will be part of the encryption enforcement implementation, not a separate feature.
- Per-user rate limits are preferred over per-IP to avoid penalizing users on shared NAT/VPN connections, as noted in the audit key decisions.
- Known GitHub avatar domains include `avatars.githubusercontent.com` and `github.com`.
- The minimum session secret key length of 64 characters provides sufficient entropy for session signing.

## Out of Scope

- GitHub API internal security (outside application control)
- MCP server internals
- Network-layer infrastructure (firewalls, load balancers, TLS termination)
- Third-party dependency vulnerability scanning (covered by separate Dependabot/supply-chain tooling)
- Penetration testing execution (this spec defines what to fix; penetration testing validates the fixes)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, no credentials appear in the browser URL bar, browser history, or server access logs — verified across all authentication flows (OAuth and dev login)
- **SC-002**: Application refuses to start in production mode within 5 seconds when any mandatory security configuration is missing (encryption key, webhook secret, session key length, cookie secure flag)
- **SC-003**: 100% of project-scoped operations return 403 Forbidden when accessed by an unauthorized user — verified for task creation, WebSocket subscription, project settings, and workflow operations
- **SC-004**: Frontend container runs as a non-root user — `id` command inside the container returns a non-zero UID
- **SC-005**: HTTP response from the frontend includes Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers; no web server version is disclosed in the Server header
- **SC-006**: 100% of secret/token comparisons in the codebase use a constant-time comparison function — verified by code review
- **SC-007**: After exceeding the rate limit threshold, affected endpoints return 429 Too Many Requests; normal service resumes after the rate window expires
- **SC-008**: After logout, browser localStorage contains no application message content — verified via browser developer tools
- **SC-009**: Database directory permissions are 0700 and database file permissions are 0600 — verified on a running instance
- **SC-010**: Zero OWASP Top 10 Critical or High findings remain in the application after all Phase 1 and Phase 2 items are addressed

## Key Decisions

- **OAuth scope reduction (FR-012)**: Reducing from `repo` to narrower scopes may break existing write operations. Implementation must include staging validation, and users must re-authorize after the scope change.
- **Encryption enforcement (FR-003)**: This is a breaking change for existing deployments without a configured encryption key. The implementation must include a migration path for re-encrypting existing plaintext rows within the same change.
- **Rate limiting strategy (FR-015, FR-016)**: Per-user limits are preferred over per-IP to avoid penalizing shared NAT/VPN users. Per-IP is used only for anonymous endpoints (OAuth callback).
- **API documentation toggle (FR-020)**: A new dedicated environment variable controls documentation visibility independently of debug mode, preventing accidental exposure in production.

## Verification Matrix

| #  | Behavior Check                                                                                   | Related Requirements    |
|----|--------------------------------------------------------------------------------------------------|-------------------------|
| 1  | After login, no credentials appear in browser URL bar, history, or access logs                   | FR-001, FR-002, SC-001  |
| 2  | Backend refuses to start in non-debug mode without encryption key set                            | FR-003, SC-002          |
| 3  | Execute into frontend container — `id` must return non-root UID                                  | FR-005, SC-004          |
| 4  | Authenticated request with unowned project_id returns 403, not success                           | FR-006, FR-007, SC-003  |
| 5  | WebSocket connection to an unowned project ID is rejected before any data is sent                | FR-006, SC-003          |
| 6  | All webhook secret comparisons use constant-time function (code review)                          | FR-008, SC-006          |
| 7  | HTTP HEAD to frontend returns CSP, HSTS, Referrer-Policy; no server version in Server header     | FR-009, FR-010, SC-005  |
| 8  | After rate limit threshold, expensive endpoints return 429 Too Many Requests                     | FR-015, FR-016, SC-007  |
| 9  | After logout, localStorage contains no message content (browser devtools)                        | FR-024, FR-025, SC-008  |
| 10 | DB directory permissions are 0700; file permissions are 0600                                     | FR-021, SC-009          |
