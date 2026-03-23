# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `001-security-review`  
**Created**: 2026-03-23  
**Status**: Draft  
**Input**: User description: "Security Review — 3 Critical · 8 High · 9 Medium · 2 Low across OWASP Top 10"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Authentication Flow (Priority: P1)

As a user logging in via OAuth, my session credentials must never appear in the browser URL bar, browser history, server access logs, or HTTP Referer headers. The system must authenticate me securely using HttpOnly cookies set directly by the backend.

**Why this priority**: Session tokens in URLs are the most exploitable vulnerability (OWASP A02 Critical). Any token leak allows full account takeover. This is the highest-impact fix because it directly protects every user's session.

**Independent Test**: Can be fully tested by completing the OAuth login flow and verifying no credentials appear in the URL, browser history, or network logs. Delivers immediate protection for all authenticated users.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth callback completes, **Then** the backend sets an HttpOnly, SameSite=Strict, Secure cookie and redirects with no credentials in the URL
2. **Given** a user has completed login, **When** inspecting the browser URL bar and history, **Then** no session tokens or credentials are visible
3. **Given** a user navigates after login, **When** the browser sends a Referer header to an external site, **Then** no credentials are included in the Referer value
4. **Given** a developer uses the dev login endpoint, **When** submitting credentials, **Then** credentials are sent in a POST request body (JSON), never as URL query parameters

---

### User Story 2 - Encryption and Secrets Enforcement at Startup (Priority: P1)

As a system operator deploying the application, the system must refuse to start in production mode if critical security configuration is missing — specifically the encryption key, webhook secret, and session secret key. This prevents accidental deployment with plaintext data storage or weak session security.

**Why this priority**: Without enforced encryption, OAuth tokens are stored in plaintext and any database access exposes all user credentials. This is an OWASP A02 Critical finding that affects data-at-rest for every user.

**Independent Test**: Can be tested by attempting to start the application in non-debug mode without required environment variables and verifying it fails with a clear error message.

**Acceptance Scenarios**:

1. **Given** the application starts in non-debug mode, **When** ENCRYPTION_KEY is not set, **Then** the application refuses to start with a clear error message
2. **Given** the application starts in non-debug mode, **When** GITHUB_WEBHOOK_SECRET is not set, **Then** the application refuses to start with a clear error message
3. **Given** the application starts in non-debug mode, **When** SESSION_SECRET_KEY is shorter than 64 characters, **Then** the application refuses to start with a clear error message
4. **Given** the application starts in non-debug mode, **When** cookies are not configured as Secure, **Then** the application refuses to start
5. **Given** the application starts in debug mode, **When** ENCRYPTION_KEY is not set, **Then** the application logs a warning but still starts (for local development)

---

### User Story 3 - Non-Root Container Execution (Priority: P1)

As a system operator, all application containers must run as dedicated non-root system users to limit the blast radius of any container escape or vulnerability exploitation.

**Why this priority**: Running as root (OWASP A05 Critical) means any vulnerability that allows code execution inside the container grants full system-level access. This is a foundational security control.

**Independent Test**: Can be tested by running `docker exec` into each container and verifying that `id` returns a non-root UID.

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** executing `id` inside the container, **Then** the output shows a non-root UID (not uid=0)
2. **Given** the backend container is running, **When** executing `id` inside the container, **Then** the output shows a non-root UID

---

### User Story 4 - Project Resource Authorization (Priority: P2)

As an authenticated user, I must only be able to access, modify, and interact with projects that I own or have been granted access to. Any attempt to access another user's project must be denied.

**Why this priority**: Broken access control (OWASP A01 High) allows any authenticated user to manipulate any project by guessing its ID. This represents a complete authorization bypass.

**Independent Test**: Can be tested by making authenticated requests with a valid session to project endpoints using a project ID that belongs to a different user, and verifying a 403 Forbidden response.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** requesting a project they do not own via any project endpoint (tasks, settings, workflow), **Then** the system returns 403 Forbidden
2. **Given** an authenticated user, **When** attempting a WebSocket connection to a project they do not own, **Then** the connection is rejected before any data is sent
3. **Given** an authenticated user, **When** accessing their own project, **Then** the request succeeds normally

---

### User Story 5 - HTTP Security Headers and Network Hardening (Priority: P2)

As a user accessing the application through a web browser, the application must return proper HTTP security headers to protect against common web attacks and must not expose internal infrastructure details.

**Why this priority**: Missing security headers (OWASP A05 High) leave users vulnerable to clickjacking, XSS, protocol downgrade attacks, and information leakage. These are defense-in-depth measures that protect all users.

**Independent Test**: Can be tested by sending a HEAD request to the frontend and verifying all required headers are present and the web server version is hidden.

**Acceptance Scenarios**:

1. **Given** a request to the frontend, **When** inspecting response headers, **Then** Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers are present
2. **Given** a request to the frontend, **When** inspecting the Server header, **Then** no web server version number is disclosed
3. **Given** a request to the frontend, **When** inspecting response headers, **Then** the deprecated X-XSS-Protection header is not present
4. **Given** Docker services in development mode, **When** checking port bindings, **Then** services are bound to 127.0.0.1 only, not 0.0.0.0

---

### User Story 6 - Constant-Time Secret Comparison and OAuth Scope Minimization (Priority: P2)

As a system maintainer, all secret/token comparisons must use constant-time comparison functions to prevent timing attacks, and OAuth scopes must be limited to the minimum necessary permissions.

**Why this priority**: Timing attacks (OWASP A07 High) allow attackers to extract secrets character-by-character. Overly broad OAuth scopes (OWASP A01 High) grant unnecessary access to all private repositories when only project management access is needed.

**Independent Test**: Can be verified via code review confirming all secret comparisons use constant-time functions, and by testing that OAuth authorization requests specify minimal scopes.

**Acceptance Scenarios**:

1. **Given** a webhook request with a secret, **When** comparing the provided secret against the stored secret, **Then** the system uses a constant-time comparison function (not standard string equality)
2. **Given** a user initiating OAuth authorization, **When** the system constructs the OAuth URL, **Then** only minimum necessary scopes are requested (not the broad `repo` scope)

---

### User Story 7 - Rate Limiting on Sensitive Endpoints (Priority: P3)

As a system operator, expensive and sensitive endpoints (chat, agent invocation, workflow, OAuth callback) must enforce per-user and per-IP rate limits to prevent resource exhaustion and abuse.

**Why this priority**: Without rate limiting (OWASP A04 Medium), a single user or attacker can exhaust shared AI and third-party API quotas, causing denial of service for all users.

**Independent Test**: Can be tested by sending requests above the rate limit threshold and verifying the system returns 429 Too Many Requests.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they exceed the per-user rate limit on a write/AI endpoint, **Then** the system returns 429 Too Many Requests
2. **Given** an IP address, **When** it exceeds the per-IP rate limit on the OAuth callback endpoint, **Then** the system returns 429 Too Many Requests

---

### User Story 8 - Secure Data Storage and Privacy (Priority: P3)

As a user, my chat history and database files must be stored securely — chat content must not persist in browser local storage after logout, and database directories must have restrictive permissions.

**Why this priority**: Unencrypted local storage data (OWASP A02 / Privacy Medium) survives logout and is readable by any XSS attack. World-readable database directories (OWASP A02 Medium) allow any container process to access sensitive data.

**Independent Test**: Can be tested by logging out and verifying localStorage contains no message content, and by checking database directory permissions are 0700 and file permissions are 0600.

**Acceptance Scenarios**:

1. **Given** a user logs out, **When** inspecting browser localStorage, **Then** no chat message content is present
2. **Given** the application creates a database directory, **When** checking directory permissions, **Then** they are set to 0700
3. **Given** the application creates a database file, **When** checking file permissions, **Then** they are set to 0600
4. **Given** a user is logged in, **When** chat history is loaded, **Then** only lightweight references (message IDs) are stored locally and content is loaded from the backend on demand

---

### User Story 9 - Secure Configuration and Error Handling (Priority: P3)

As a system operator, the application must validate configuration inputs, gate API documentation independently from debug mode, never bypass webhook verification based on debug mode, sanitize error messages, and mount data volumes outside the application root.

**Why this priority**: These Medium-severity findings (OWASP A05, A09) represent defense-in-depth measures that prevent accidental misconfiguration in production and reduce information leakage.

**Independent Test**: Can be tested independently by verifying each configuration validation at startup, checking that webhook verification is always enforced, and confirming error responses do not expose internal details.

**Acceptance Scenarios**:

1. **Given** CORS origins are configured, **When** any origin value is not a well-formed URL with scheme and hostname, **Then** the application refuses to start
2. **Given** DEBUG=true in production, **When** a webhook request arrives without a valid signature, **Then** signature verification is still enforced (no debug bypass)
3. **Given** ENABLE_DOCS is not set, **When** accessing API documentation endpoints, **Then** documentation is not available (independent of DEBUG setting)
4. **Given** a GitHub GraphQL API error occurs, **When** the error reaches the API response, **Then** only a generic sanitized message is returned (no internal query structure or token details)
5. **Given** Docker containers in production, **When** checking the data volume mount point, **Then** it is outside the application root directory

---

### User Story 10 - Supply Chain and Client-Side Safety (Priority: P4)

As a developer and user, GitHub Actions workflows must use minimum necessary permissions, and externally sourced avatar URLs must be validated before rendering.

**Why this priority**: These are Low-severity findings that provide additional defense-in-depth but have limited exploitability in practice.

**Independent Test**: Can be verified by code review of workflow permission declarations and by testing avatar rendering with various URL formats.

**Acceptance Scenarios**:

1. **Given** the GitHub Actions workflow file, **When** reviewing permissions, **Then** the `issues` permission is scoped to the minimum needed with a justification comment
2. **Given** an avatar URL from the GitHub API, **When** the URL does not use https: or does not originate from a known GitHub avatar domain, **Then** the system falls back to a placeholder image

---

### Edge Cases

- What happens when an existing deployment has plaintext-encrypted data and the encryption enforcement is turned on? A migration path must be provided.
- What happens when OAuth scope is narrowed and existing users have tokens with the old broader scope? Users must re-authorize.
- What happens when a user is behind a shared NAT/VPN and rate limiting is applied per-IP? Per-user limits are preferred over per-IP to avoid penalizing shared network users.
- What happens when the CORS origins environment variable contains trailing whitespace or empty entries? Validation must trim and reject empty values.
- What happens when the frontend container switches to a non-root user but the web server needs to bind to a privileged port? The container must use a port above 1024 or configure appropriate capabilities.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST set session credentials as HttpOnly, SameSite=Strict, Secure cookies on the OAuth callback response and redirect with no credentials in the URL
- **FR-002**: Frontend MUST NOT read credentials from URL parameters
- **FR-003**: System MUST refuse to start in non-debug mode if ENCRYPTION_KEY environment variable is not set
- **FR-004**: System MUST refuse to start in non-debug mode if GITHUB_WEBHOOK_SECRET environment variable is not set
- **FR-005**: All containers MUST run as a dedicated non-root system user with a non-zero UID

**Phase 2 — High**

- **FR-006**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action
- **FR-007**: Project access verification MUST be centralized as a shared dependency usable across all endpoints
- **FR-008**: All secret and token comparisons MUST use constant-time comparison functions
- **FR-009**: Frontend MUST include Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy response headers
- **FR-010**: Frontend MUST NOT include the deprecated X-XSS-Protection header
- **FR-011**: Frontend MUST NOT disclose the web server version in the Server response header
- **FR-012**: All credential inputs (including dev-only endpoints) MUST arrive in POST request bodies, never in URL parameters
- **FR-013**: OAuth authorization requests MUST use minimum necessary scopes instead of the broad `repo` scope
- **FR-014**: System MUST reject SESSION_SECRET_KEY values shorter than 64 characters at startup
- **FR-015**: Development Docker services MUST bind to 127.0.0.1, not 0.0.0.0

**Phase 3 — Medium**

- **FR-016**: Expensive and sensitive endpoints MUST enforce per-user rate limits on write/AI operations
- **FR-017**: OAuth callback endpoint MUST enforce per-IP rate limits
- **FR-018**: Rate-limited requests MUST return HTTP 429 Too Many Requests
- **FR-019**: System MUST refuse to start in non-debug mode if cookie Secure flag is not enabled
- **FR-020**: Webhook signature verification MUST NOT be conditional on debug mode
- **FR-021**: API documentation availability MUST be gated on a dedicated ENABLE_DOCS environment variable, independent of DEBUG
- **FR-022**: Database directory MUST be created with 0700 permissions; database files MUST be created with 0600 permissions
- **FR-023**: CORS origins configuration MUST validate each origin is a well-formed URL with scheme and hostname; system MUST fail on any malformed value
- **FR-024**: Data volumes MUST be mounted outside the application root directory
- **FR-025**: Chat history MUST store only lightweight references (message IDs) locally with a TTL; full content MUST be loaded from the backend on demand
- **FR-026**: All local chat data MUST be cleared on logout
- **FR-027**: Error messages from third-party API integrations MUST be logged internally and only generic sanitized messages MUST be returned in API responses

**Phase 4 — Low**

- **FR-028**: GitHub Actions workflow permissions MUST be scoped to the minimum necessary with justification comments
- **FR-029**: External avatar URLs MUST be validated to use https: protocol and originate from a known GitHub avatar domain; invalid URLs MUST fall back to a placeholder image

### Key Entities

- **Session**: Represents an authenticated user's active session; key attributes include session token (stored as HttpOnly cookie), user identity, expiration, and associated project access rights
- **Project**: Represents a user's project; must be associated with an owning user for access control enforcement
- **Configuration**: Represents application startup configuration; includes encryption key, webhook secret, session secret key, cookie settings, CORS origins, and docs toggle — all subject to validation at startup
- **Chat Message Reference**: Lightweight local reference to a chat message (message ID and timestamp); actual content fetched from backend

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, zero credentials appear in the browser URL bar, browser history, or server access logs
- **SC-002**: Application refuses to start in production mode when any required security configuration (encryption key, webhook secret, session key, cookie secure flag) is missing or invalid — 100% enforcement
- **SC-003**: All containers run as non-root — verified by `id` command returning non-zero UID in every container
- **SC-004**: 100% of authenticated requests to a project not owned by the requester return 403 Forbidden
- **SC-005**: WebSocket connections to unowned projects are rejected before any data is transmitted
- **SC-006**: 100% of secret/token comparisons use constant-time functions (verified by code review)
- **SC-007**: All five required HTTP security headers are present in frontend responses; no server version disclosed
- **SC-008**: Requests exceeding rate limit thresholds return 429 Too Many Requests within 1 second
- **SC-009**: After logout, zero chat message content remains in browser localStorage
- **SC-010**: Database directory permissions are 0700; database file permissions are 0600
- **SC-011**: CORS validation rejects 100% of malformed origin URLs at startup
- **SC-012**: Zero internal error details (query structure, token scope) appear in user-facing API responses

## Assumptions

- The backend already runs as a non-root user; only the frontend container needs the non-root user fix
- The application uses FastAPI for the backend and nginx for the frontend reverse proxy
- Debug mode is a legitimate development configuration where some restrictions (encryption key enforcement) may be relaxed
- The existing `hmac.compare_digest` usage for GitHub webhooks is the correct pattern to replicate for all secret comparisons
- OAuth scope narrowing may require users to re-authorize; this is an acceptable trade-off for security
- Per-user rate limiting is preferred over per-IP to avoid penalizing shared NAT/VPN users
- A migration path for existing plaintext-encrypted data will be included with the encryption enforcement change
- The `slowapi` library is recommended for rate limiting as it is FastAPI-compatible
- GitHub avatar domains (e.g., `avatars.githubusercontent.com`) are the only trusted domains for avatar URLs
- Data volumes will be mounted at `/var/lib/solune/data` or equivalent path outside the application root

## Dependencies

- The encryption enforcement change is a breaking change for existing deployments without an encryption key configured
- OAuth scope narrowing must be tested in staging before production deployment to verify all required write operations still work
- Rate limiting requires adding the `slowapi` library as a new backend dependency
- Frontend container non-root user change may require nginx configuration adjustments for port binding
