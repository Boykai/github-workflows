# Feature Specification: Security Review

**Feature Branch**: `001-security-review`  
**Created**: 2026-03-23  
**Status**: Draft  
**Input**: User description: "Security, Privacy & Vulnerability Audit — 3 Critical · 8 High · 9 Medium · 2 Low across OWASP Top 10"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Credential Leak Prevention (Priority: P1)

As a user logging in via OAuth, I need my session credentials to never appear in the browser URL bar, browser history, server access logs, or HTTP Referer headers so that my account cannot be hijacked by anyone who observes these surfaces.

**Why this priority**: Credential leakage is the most immediately exploitable vulnerability. A single exposed session token grants full account access to an attacker. This is rated Critical (OWASP A02).

**Independent Test**: Can be fully tested by completing an OAuth login flow and verifying that no credentials appear in the browser URL, browser history entries, or network request Referer headers.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth callback completes, **Then** the backend sets an HttpOnly, SameSite=Strict, Secure cookie and redirects with no credentials in the URL.
2. **Given** a user has completed login, **When** inspecting browser history, **Then** no URL entry contains session tokens or credentials.
3. **Given** the frontend navigates after login, **When** any outbound HTTP request is made, **Then** no Referer header contains session tokens.
4. **Given** a developer uses the dev login endpoint, **When** submitting credentials, **Then** credentials are sent in the POST request body (JSON), never as URL query parameters.

---

### User Story 2 - Encryption and Secrets Enforcement at Startup (Priority: P1)

As a system operator deploying the application in production, I need the application to refuse to start if critical security configuration is missing so that sensitive data is never stored unencrypted and sessions are never signed with weak keys.

**Why this priority**: Without enforced encryption and strong secrets, OAuth tokens are stored in plaintext and sessions can be forged. This is rated Critical (OWASP A02) and High (OWASP A07).

**Independent Test**: Can be tested by attempting to start the application in non-debug mode without required environment variables and confirming it fails immediately with a clear error message.

**Acceptance Scenarios**:

1. **Given** the application starts in non-debug mode, **When** ENCRYPTION_KEY is not set, **Then** the application refuses to start with a clear error message.
2. **Given** the application starts in non-debug mode, **When** GITHUB_WEBHOOK_SECRET is not set, **Then** the application refuses to start with a clear error message.
3. **Given** the application starts in non-debug mode, **When** SESSION_SECRET_KEY is shorter than 64 characters, **Then** the application refuses to start with a clear error message.
4. **Given** the application starts in non-debug mode, **When** cookies are not configured as Secure, **Then** the application refuses to start with a clear error message.
5. **Given** the application starts in debug mode, **When** ENCRYPTION_KEY is not set, **Then** the application may start with a warning (development convenience only).

---

### User Story 3 - Container Security Hardening (Priority: P1)

As a system operator, I need all containers to run as non-root users so that a container escape vulnerability cannot grant host-level root access.

**Why this priority**: Running containers as root is a Critical misconfiguration (OWASP A05). Container breakout with root privileges can compromise the entire host.

**Independent Test**: Can be tested by running `docker exec` into each container and verifying the process runs as a non-root UID.

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** checking the process UID, **Then** it must return a non-root UID (not 0).
2. **Given** the backend container is running, **When** checking the process UID, **Then** it must return a non-root UID (not 0).

---

### User Story 4 - Project-Level Access Control (Priority: P2)

As an authenticated user, I need to be prevented from accessing, modifying, or subscribing to projects I do not own so that my data remains private and isolated.

**Why this priority**: Broken access control (OWASP A01) allows any authenticated user to access any project by guessing its ID. This is the most common web application vulnerability.

**Independent Test**: Can be tested by sending an authenticated request with a project_id belonging to a different user and verifying a 403 Forbidden response.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they request a project they do not own via any API endpoint, **Then** the system returns 403 Forbidden.
2. **Given** an authenticated user, **When** they attempt to create tasks in a project they do not own, **Then** the system returns 403 Forbidden.
3. **Given** an authenticated user, **When** they attempt to connect to a WebSocket for a project they do not own, **Then** the connection is rejected before any data is sent.
4. **Given** an authenticated user, **When** they attempt to modify settings for a project they do not own, **Then** the system returns 403 Forbidden.
5. **Given** an authenticated user, **When** they attempt to trigger workflows in a project they do not own, **Then** the system returns 403 Forbidden.

---

### User Story 5 - Secure Server Configuration (Priority: P2)

As a user of the application, I need the server to send proper HTTP security headers and hide internal version information so that my browser enforces content security policies and attackers cannot fingerprint the server.

**Why this priority**: Missing security headers (OWASP A05) leave users vulnerable to XSS, clickjacking, and protocol downgrade attacks. These are standard hardening measures.

**Independent Test**: Can be tested by issuing a HEAD request to the frontend and verifying the presence of required security headers and absence of server version information.

**Acceptance Scenarios**:

1. **Given** a client makes a request to the frontend, **When** inspecting response headers, **Then** Content-Security-Policy is present.
2. **Given** a client makes a request to the frontend, **When** inspecting response headers, **Then** Strict-Transport-Security is present.
3. **Given** a client makes a request to the frontend, **When** inspecting response headers, **Then** Referrer-Policy is present.
4. **Given** a client makes a request to the frontend, **When** inspecting response headers, **Then** Permissions-Policy is present.
5. **Given** a client makes a request to the frontend, **When** inspecting response headers, **Then** X-XSS-Protection is not present (deprecated).
6. **Given** a client makes a request to the frontend, **When** inspecting the Server header, **Then** nginx version information is not disclosed.

---

### User Story 6 - Timing-Safe Secret Comparison (Priority: P2)

As a system integrator sending webhooks, I need all webhook secret validations to use constant-time comparison so that attackers cannot use timing analysis to guess the webhook secret.

**Why this priority**: Timing attacks (OWASP A07) on secret comparison can leak secret values byte-by-byte.

**Independent Test**: Can be tested via code review confirming all secret/token comparisons use constant-time functions.

**Acceptance Scenarios**:

1. **Given** a Signal webhook request arrives, **When** the secret is verified, **Then** constant-time comparison is used.
2. **Given** any secret or token comparison in the codebase, **When** reviewed, **Then** it uses `hmac.compare_digest` or equivalent constant-time function.

---

### User Story 7 - Minimal OAuth Scopes (Priority: P2)

As a user authorizing the application via GitHub OAuth, I need the application to request only the minimum necessary permissions so that my private repository data is not exposed to unnecessary risk.

**Why this priority**: Overly broad OAuth scopes (OWASP A01) grant the application full read/write access to all private repositories when only project management access is needed.

**Independent Test**: Can be tested by initiating the OAuth flow and verifying the requested scopes are minimal, then confirming all application features still work.

**Acceptance Scenarios**:

1. **Given** a user starts the OAuth authorization flow, **When** GitHub displays the permission request, **Then** the requested scope does not include full `repo` access.
2. **Given** a user has authorized with minimal scopes, **When** they use all application features, **Then** all features function correctly.

---

### User Story 8 - Network Binding Restriction (Priority: P2)

As a system operator, I need Docker services to only bind to localhost in development and not expose ports directly in production so that services are not accessible from the public network.

**Why this priority**: Services bound to all network interfaces (OWASP A05) are exposed to the entire network, bypassing any firewall or reverse proxy protections.

**Independent Test**: Can be tested by inspecting Docker Compose configuration to verify port bindings use 127.0.0.1 for development.

**Acceptance Scenarios**:

1. **Given** Docker Compose development configuration, **When** inspecting port bindings, **Then** backend and frontend ports are bound to 127.0.0.1 only.
2. **Given** Docker Compose production configuration, **When** inspecting port bindings, **Then** services are exposed only via reverse proxy, not directly via container ports.

---

### User Story 9 - Rate Limiting on Sensitive Endpoints (Priority: P3)

As a user of the application, I need expensive and sensitive endpoints to enforce rate limits so that a single user or attacker cannot exhaust shared resources or brute-force authentication.

**Why this priority**: Without rate limiting (OWASP A04), a single user can exhaust shared AI/GitHub API quotas, causing denial of service for all users.

**Independent Test**: Can be tested by exceeding the rate limit threshold on a protected endpoint and verifying a 429 Too Many Requests response.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they exceed the per-user rate limit on chat/AI endpoints, **Then** the system returns 429 Too Many Requests.
2. **Given** a client IP, **When** it exceeds the per-IP rate limit on the OAuth callback, **Then** the system returns 429 Too Many Requests.
3. **Given** a user within their rate limit, **When** they make normal requests, **Then** requests succeed without throttling.

---

### User Story 10 - Webhook Verification Independence from Debug Mode (Priority: P3)

As a system operator, I need webhook signature verification to be enforced regardless of debug mode so that accidentally enabling debug in production does not allow unauthenticated webhook triggers.

**Why this priority**: Debug-conditional security bypasses (OWASP A05) create a single misconfiguration point that disables authentication entirely.

**Independent Test**: Can be tested by enabling debug mode and sending a webhook without a valid signature, verifying the request is rejected.

**Acceptance Scenarios**:

1. **Given** the application runs with DEBUG=true, **When** a webhook request arrives without a valid signature, **Then** the request is rejected.
2. **Given** a developer working locally, **When** they configure a test webhook secret, **Then** webhook verification works with the local secret.

---

### User Story 11 - Secure Data Storage and Privacy (Priority: P3)

As a user of the application, I need my chat history and database files to be securely stored with appropriate access controls so that my data is protected at rest and cleaned up on logout.

**Why this priority**: Unencrypted indefinite local storage (Privacy / OWASP A02) and world-readable database files (OWASP A02) expose sensitive data to XSS attacks and unauthorized processes.

**Independent Test**: Can be tested by checking localStorage after logout (must contain no message content) and verifying database directory/file permissions.

**Acceptance Scenarios**:

1. **Given** a user logs out, **When** inspecting browser localStorage, **Then** no chat message content is present.
2. **Given** the application creates a database directory, **When** checking permissions, **Then** the directory has 0700 permissions.
3. **Given** the application creates a database file, **When** checking permissions, **Then** the file has 0600 permissions.
4. **Given** chat history is loaded, **When** the frontend requests messages, **Then** only lightweight references (message IDs) are stored locally, with content loaded on demand from the backend.

---

### User Story 12 - Secure API Documentation and Error Handling (Priority: P3)

As a system operator, I need API documentation exposure and error message content to be securely managed so that internal details are never leaked to end users.

**Why this priority**: Exposed API schemas (OWASP A05) and verbose error messages (OWASP A09) provide attackers with detailed information about the application's internal structure.

**Independent Test**: Can be tested by verifying API docs are gated on a dedicated toggle and error responses contain only generic messages.

**Acceptance Scenarios**:

1. **Given** the application runs with DEBUG=true but ENABLE_DOCS is not set, **When** accessing Swagger/ReDoc URLs, **Then** they are not available.
2. **Given** a GitHub GraphQL API error occurs, **When** the error is returned to the user, **Then** only a generic sanitized message is shown.
3. **Given** a GitHub GraphQL API error occurs, **When** the error is logged internally, **Then** the full error details are captured in the application logs.

---

### User Story 13 - CORS and Configuration Validation (Priority: P3)

As a system operator, I need CORS origins configuration to be validated at startup so that typos or malformed values do not silently create security vulnerabilities.

**Why this priority**: Unvalidated CORS configuration (OWASP A05) can silently allow cross-origin requests from unintended domains.

**Independent Test**: Can be tested by providing a malformed CORS origin at startup and verifying the application fails with a clear error.

**Acceptance Scenarios**:

1. **Given** a CORS origins configuration with a malformed URL, **When** the application starts, **Then** it fails with a clear error identifying the invalid origin.
2. **Given** a valid CORS origins configuration, **When** the application starts, **Then** it accepts the configuration and starts normally.

---

### User Story 14 - Supply Chain and Rendering Safety (Priority: P4)

As a developer and user, I need GitHub Actions workflows to use minimal permissions and avatar URLs to be validated so that supply chain risks and injection attacks are minimized.

**Why this priority**: These are lower-severity items (Low) that reduce the overall attack surface but are not immediately exploitable.

**Independent Test**: Can be tested by reviewing workflow permissions and verifying avatar URL validation in the frontend.

**Acceptance Scenarios**:

1. **Given** the branch-issue-link GitHub Actions workflow, **When** reviewing its permissions, **Then** it has the minimum required scope with a justification comment.
2. **Given** an avatar URL from the GitHub API, **When** rendered in the frontend, **Then** it is validated to use https: and originate from a known GitHub avatar domain.
3. **Given** an invalid avatar URL, **When** the frontend attempts to render it, **Then** a placeholder image is displayed instead.

---

### Edge Cases

- What happens when a user has an existing plaintext-encrypted database and ENCRYPTION_KEY becomes mandatory? A migration path must be provided.
- How does the system handle users who authorized with broad OAuth scopes when scopes are narrowed? Users must re-authorize after scope changes.
- What happens when rate limits are hit mid-operation (e.g., during a multi-step workflow)? The operation should fail gracefully with a clear message.
- What if CORS origins contain valid URLs but with wildcard subdomains (e.g., `https://*.example.com`)? Wildcard patterns should be explicitly handled or rejected.
- What happens if the data volume mount path change breaks existing deployments? Clear migration documentation must be provided.
- How does the system handle concurrent WebSocket connections from the same user to different projects? Each connection must independently verify project ownership.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST set session credentials via HttpOnly, SameSite=Strict, Secure cookies on the OAuth callback response and redirect with no credentials in the URL.
- **FR-002**: Frontend MUST NOT read credentials from URL parameters.
- **FR-003**: System MUST refuse to start in non-debug mode if ENCRYPTION_KEY is not set.
- **FR-004**: System MUST refuse to start in non-debug mode if GITHUB_WEBHOOK_SECRET is not set.
- **FR-005**: All containers MUST run as a dedicated non-root system user (UID ≠ 0).

**Phase 2 — High**

- **FR-006**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action.
- **FR-007**: Project ownership checks MUST be centralized as a shared dependency (not duplicated per endpoint).
- **FR-008**: All secret and token comparisons MUST use constant-time comparison functions.
- **FR-009**: The frontend MUST send Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers on all responses.
- **FR-010**: The frontend MUST NOT send the deprecated X-XSS-Protection header.
- **FR-011**: The frontend MUST hide the web server version in the Server response header.
- **FR-012**: All credential inputs, including dev-only endpoints, MUST arrive in the POST request body (JSON), never in the URL.
- **FR-013**: OAuth authorization MUST request only the minimum necessary scopes (not the full `repo` scope).
- **FR-014**: System MUST reject SESSION_SECRET_KEY values shorter than 64 characters at startup.
- **FR-015**: Docker services in development MUST bind to 127.0.0.1 only, not 0.0.0.0.
- **FR-016**: Docker services in production MUST be exposed only via reverse proxy, not directly via container ports.

**Phase 3 — Medium**

- **FR-017**: Chat, agent invocation, workflow, and OAuth callback endpoints MUST enforce rate limits (per-user for write/AI endpoints; per-IP for OAuth callback).
- **FR-018**: System MUST return 429 Too Many Requests when rate limits are exceeded.
- **FR-019**: System MUST refuse to start in non-debug mode if cookie Secure flag is not configured.
- **FR-020**: Webhook signature verification MUST NOT be conditional on debug mode.
- **FR-021**: API documentation availability MUST be controlled by a dedicated ENABLE_DOCS environment variable, independent of DEBUG.
- **FR-022**: Database directory MUST be created with 0700 permissions; database file with 0600 permissions.
- **FR-023**: CORS origins configuration MUST be validated at startup; each origin must be a well-formed URL with scheme and hostname; startup MUST fail on any malformed value.
- **FR-024**: Data volumes MUST be mounted outside the application root directory (e.g., /var/lib/solune/data).
- **FR-025**: Frontend MUST store only lightweight references (message IDs) in localStorage with a TTL, not full message content.
- **FR-026**: Frontend MUST clear all local data on logout.
- **FR-027**: GraphQL error messages MUST be sanitized before being returned in API responses; full errors MUST be logged internally.

**Phase 4 — Low**

- **FR-028**: GitHub Actions workflows MUST use minimum required permissions with justification comments.
- **FR-029**: Avatar URLs MUST be validated to use https: protocol and originate from a known GitHub avatar domain before rendering.
- **FR-030**: Invalid avatar URLs MUST fall back to a placeholder image.

### Key Entities

- **Session**: Represents an authenticated user session; key attributes include session token, user identity, creation time, and expiration. Stored as an HttpOnly secure cookie.
- **Project**: Represents a user-owned project; key attributes include project ID and owner user ID. All project operations require verified ownership.
- **OAuth Token**: Represents an encrypted OAuth credential; stored encrypted at rest using ENCRYPTION_KEY. Must never be stored in plaintext in non-debug mode.
- **Webhook Secret**: Represents a shared secret for webhook signature verification; compared using constant-time functions only.
- **Rate Limit Record**: Represents per-user or per-IP request counts within a time window; key attributes include identifier, endpoint, count, and window expiration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, no credentials appear in browser URL bar, browser history, or server access logs — verified by manual inspection across 3 different browsers.
- **SC-002**: Application refuses to start in non-debug mode without ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET, or cookie Secure flag within 5 seconds of startup attempt.
- **SC-003**: Application refuses to start in non-debug mode with SESSION_SECRET_KEY shorter than 64 characters within 5 seconds.
- **SC-004**: All containers run as non-root users — verified by `id` command returning UID > 0.
- **SC-005**: Authenticated requests with unowned project_id return 403 Forbidden for 100% of protected endpoints.
- **SC-006**: WebSocket connections to unowned project IDs are rejected before any data frames are sent.
- **SC-007**: 100% of webhook secret comparisons use constant-time comparison functions — verified by code review.
- **SC-008**: Frontend responses include Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers — verified by HTTP HEAD request.
- **SC-009**: Server header does not disclose nginx version — verified by HTTP HEAD request.
- **SC-010**: After exceeding rate limit threshold, expensive endpoints return 429 Too Many Requests within 1 second.
- **SC-011**: After logout, browser localStorage contains no message content — verified via browser developer tools.
- **SC-012**: Database directory permissions are 0700; file permissions are 0600 — verified via `stat` command.
- **SC-013**: CORS origins with malformed URLs cause startup failure with descriptive error — verified by providing invalid input.
- **SC-014**: All GraphQL API error responses contain only generic messages; no internal query structure or token scope details are exposed.
- **SC-015**: OAuth authorization scope is reduced to minimum necessary — verified by inspecting the authorization URL.
- **SC-016**: Docker services bind to 127.0.0.1 in development configuration — verified by inspecting Docker Compose files.

## Assumptions

- The application currently uses Python (FastAPI) for the backend and React/TypeScript for the frontend, served via nginx.
- Debug mode is determined by a DEBUG environment variable.
- The backend already has a working OAuth flow with GitHub that can be modified.
- SQLite is the current database backend.
- The application already has a working session management system.
- Existing deployments may have plaintext-encrypted data that will need a migration path when encryption becomes mandatory.
- Users who authorized with the `repo` scope will need to re-authorize after scope reduction.
- The `slowapi` library is available for FastAPI rate limiting.
- Docker Compose is used for both development and production deployments.
- GitHub avatar URLs come from `avatars.githubusercontent.com` or similar known domains.

## Dependencies

- Encryption enforcement requires a migration path for existing plaintext data.
- OAuth scope reduction requires staging testing to verify all features work with narrower scopes.
- Rate limiting requires selection and integration of a rate-limiting library.
- Non-root container execution requires nginx configuration changes to work without root privileges.
- Data volume path changes require documentation and migration guidance for existing deployments.

## Risks

- **OAuth scope reduction may break features**: Some write operations may require broader scopes. Testing in staging is essential before production deployment.
- **Encryption enforcement is a breaking change**: Existing deployments without ENCRYPTION_KEY will fail to start. A migration path must be documented and provided.
- **Rate limiting may impact legitimate heavy users**: Per-user limits are preferred over per-IP to avoid penalizing shared NAT/VPN users. Thresholds must be tuned based on usage patterns.
- **Data volume mount path changes may break existing deployments**: Migration documentation must be provided.

## Out of Scope

- GitHub API internal security (GitHub's platform security is out of our control).
- MCP server internals (not part of this application's security boundary).
- Network-layer infrastructure (firewalls, load balancers, DNS — managed separately).
- Penetration testing execution (this specification defines what to fix, not how to verify via external pen test).
