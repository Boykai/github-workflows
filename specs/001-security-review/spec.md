# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `001-security-review`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "Security, Privacy & Vulnerability Audit — 3 Critical · 8 High · 9 Medium · 2 Low findings across OWASP Top 10"
**Note**: The original audit header above sums to 22 findings, but the audited finding list used by this feature contains 21 findings. This specification follows the 21 documented findings.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Credentials Never Exposed in URLs (Priority: P1)

As a user logging in via OAuth, I expect that my session credentials are never visible in the browser address bar, browser history, server logs, or HTTP Referer headers, so that my account cannot be hijacked by anyone who inspects those locations.

**Why this priority**: Credential leakage in URLs is actively exploitable today. Browser history, proxy logs, and Referer headers are common attack surfaces. This is rated OWASP A02 Critical because every login creates a new exposure window.

**Independent Test**: Log in via OAuth and verify the browser URL bar, history, and any proxy/CDN access logs contain no session token or credential query parameters.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth callback completes, **Then** the browser URL contains no `session_token`, `access_token`, or other credential query parameters.
2. **Given** a user has completed login, **When** the browser history is inspected, **Then** no entry contains credential values.
3. **Given** a user navigates away from the app after login, **When** the outbound HTTP Referer header is inspected, **Then** it contains no credential values.
4. **Given** a developer uses the dev-login endpoint, **When** providing a GitHub PAT, **Then** the credential is sent in the POST request body (JSON), never as a URL query parameter.

---

### User Story 2 — Encryption and Secrets Enforced at Startup (Priority: P1)

As a system operator deploying the application, I expect that the system refuses to start in production mode if required encryption keys or webhook secrets are missing or weak, so that sensitive data is never stored unprotected and webhook endpoints cannot be spoofed.

**Why this priority**: Running without encryption keys means OAuth tokens are stored in plaintext, and missing webhook secrets allow unauthenticated callers to trigger workflows. Both conditions are silently dangerous.

**Independent Test**: Attempt to start the backend in non-debug mode without `ENCRYPTION_KEY`, without `GITHUB_WEBHOOK_SECRET`, and with a `SESSION_SECRET_KEY` shorter than 64 characters. Each must fail with a clear error.

**Acceptance Scenarios**:

1. **Given** the application is started in non-debug mode, **When** `ENCRYPTION_KEY` is not set, **Then** the application refuses to start and logs a clear error message.
2. **Given** the application is started in non-debug mode, **When** `GITHUB_WEBHOOK_SECRET` is not set, **Then** the application refuses to start and logs a clear error message.
3. **Given** the application is started in non-debug mode, **When** `SESSION_SECRET_KEY` is shorter than 64 characters, **Then** the application refuses to start and logs a clear error message.
4. **Given** the application is started in non-debug mode, **When** `cookie_secure` is not configured as `true`, **Then** the application refuses to start and logs a clear error message.

---

### User Story 3 — Containers Run as Non-Root (Priority: P1)

As a system operator, I expect all containers (frontend and backend) to run as a dedicated non-root system user, so that a container escape does not grant root access to the host.

**Why this priority**: Running containers as root is a Critical finding (OWASP A05). Container breakouts with root privileges can compromise the host system.

**Independent Test**: Execute `id` inside the frontend container and verify the UID is non-root (not 0).

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** `docker exec <container> id` is executed, **Then** the output shows a non-root UID (not uid=0).
2. **Given** the backend container is running, **When** `docker exec <container> id` is executed, **Then** the output shows a non-root UID (not uid=0).

---

### User Story 4 — Project Resources Scoped to Authenticated User (Priority: P2)

As an authenticated user, I expect that I can only access projects I own or have been granted access to, so that no other user can read or modify my projects by guessing a project ID.

**Why this priority**: Broken access control (OWASP A01 High) allows any authenticated user to target any project. This directly impacts data confidentiality and integrity for all users.

**Independent Test**: Authenticate as User A, attempt to access a project owned by User B using User B's project ID. Verify a 403 Forbidden response.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they request a project they do not own, **Then** the system returns 403 Forbidden.
2. **Given** an authenticated user, **When** they attempt to create a task on a project they do not own, **Then** the system returns 403 Forbidden.
3. **Given** an authenticated user, **When** they attempt to subscribe to a WebSocket for a project they do not own, **Then** the connection is rejected before any data is sent.
4. **Given** an authenticated user, **When** they attempt to modify settings for a project they do not own, **Then** the system returns 403 Forbidden.
5. **Given** an authenticated user, **When** they attempt to trigger a workflow on a project they do not own, **Then** the system returns 403 Forbidden.

---

### User Story 5 — Secure HTTP Headers and Server Hardening (Priority: P2)

As a user browsing the application, I expect the frontend to serve all recommended HTTP security headers and not expose server version information, so that common web attacks (clickjacking, XSS, MIME sniffing, protocol downgrade) are mitigated by default.

**Why this priority**: Missing security headers (OWASP A05 High) leave the application vulnerable to well-known attack classes that browsers can block automatically if instructed.

**Independent Test**: Send `curl -I` to the frontend and verify the response includes `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`, and `X-Content-Type-Options`. Verify no `X-XSS-Protection` header is present and the `Server` header does not reveal server software version.

**Acceptance Scenarios**:

1. **Given** a user requests any page, **When** the response headers are inspected, **Then** `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`, and `X-Content-Type-Options` headers are present.
2. **Given** a user requests any page, **When** the response headers are inspected, **Then** no `X-XSS-Protection` header is present.
3. **Given** a user requests any page, **When** the `Server` response header is inspected, **Then** no server software version number is revealed.

---

### User Story 6 — Constant-Time Secret Comparisons (Priority: P2)

As a system operator, I expect all webhook secret and token comparisons to use constant-time comparison functions, so that timing side-channel attacks cannot be used to guess secrets.

**Why this priority**: Timing attacks (OWASP A07 High) on secret comparisons are well-documented and exploitable remotely with statistical analysis.

**Independent Test**: Code review confirms all secret/token comparisons use `hmac.compare_digest` or equivalent constant-time function.

**Acceptance Scenarios**:

1. **Given** the Signal webhook endpoint receives a request, **When** the webhook secret is verified, **Then** a constant-time comparison function is used.
2. **Given** any endpoint performs a secret or token comparison, **When** the comparison is executed, **Then** a constant-time comparison function is used throughout the codebase.

---

### User Story 7 — Minimum OAuth Scopes (Priority: P2)

As a user authorizing the application via OAuth, I expect the application to request only the minimum permissions it needs, so that my private repositories are not unnecessarily exposed.

**Why this priority**: Overly broad scopes (OWASP A01 High) grant the application full read/write access to all private repositories, exceeding the principle of least privilege.

**Independent Test**: Inspect the OAuth authorization URL and verify only the minimum necessary scopes are requested by default, and that any broader scope retained for core write operations (such as full `repo`) is explicitly justified and documented.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth authorization, **When** the authorization URL is constructed, **Then** the requested scopes include only the minimum necessary permissions, with any broader retained scope explicitly justified in the security review documentation.
2. **Given** the application retains a broader scope such as full `repo` for core write operations, **When** the security review documentation and tests are inspected, **Then** the justification and affected capabilities are clearly documented.

---

### User Story 8 — Network Binding and Service Isolation (Priority: P2)

As a system operator, I expect development services to bind only to localhost and production services to be accessible only through a reverse proxy, so that internal services are not directly exposed to the network.

**Why this priority**: Binding to all network interfaces (OWASP A05 High) exposes development services to the entire network and production services without the protection of a reverse proxy.

**Independent Test**: Inspect docker-compose configuration and verify development services bind to `127.0.0.1` and production services are not directly exposed via container ports.

**Acceptance Scenarios**:

1. **Given** the application runs in development mode, **When** docker-compose configuration is inspected, **Then** backend and frontend ports are bound to `127.0.0.1` only.
2. **Given** the application runs in production mode, **When** docker-compose configuration is inspected, **Then** services are exposed only via a reverse proxy, not directly via container ports.

---

### User Story 9 — Rate Limiting on Expensive Endpoints (Priority: P3)

As a user of the application, I expect that expensive or sensitive operations (chat, AI agents, workflows, OAuth) are rate-limited, so that one user cannot exhaust shared resources or abuse AI/GitHub API quotas.

**Why this priority**: Missing rate limiting (OWASP A04 Medium) allows resource exhaustion and abuse. Per-user limits are preferred over per-IP to avoid penalizing shared NAT/VPN users.

**Independent Test**: Rapidly call a rate-limited endpoint beyond the threshold and verify the system returns HTTP 429 Too Many Requests.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they exceed the rate limit on chat endpoints, **Then** the system returns 429 Too Many Requests.
2. **Given** an authenticated user, **When** they exceed the rate limit on agent invocation endpoints, **Then** the system returns 429 Too Many Requests.
3. **Given** an authenticated user, **When** they exceed the rate limit on workflow endpoints, **Then** the system returns 429 Too Many Requests.
4. **Given** any IP address, **When** it exceeds the rate limit on the OAuth callback endpoint, **Then** the system returns 429 Too Many Requests.

---

### User Story 10 — Secure Local Data Handling and Logout Cleanup (Priority: P3)

As a user, I expect that after I log out, no sensitive data (such as chat messages) remains stored in my browser, and while logged in, only lightweight references are stored locally rather than full message content.

**Why this priority**: Storing full chat history in localStorage (OWASP A02 Medium) means data survives logout, is unencrypted, and is readable by any XSS exploit.

**Independent Test**: Log in, use the chat feature, log out, then inspect `localStorage` in browser DevTools. Verify no message content remains.

**Acceptance Scenarios**:

1. **Given** a logged-in user has used the chat feature, **When** localStorage is inspected, **Then** only lightweight references (message IDs) are stored, not full message content.
2. **Given** a user logs out, **When** localStorage is inspected, **Then** all application data has been cleared.
3. **Given** locally stored references exist, **When** a configurable TTL expires, **Then** the expired references are automatically removed.

---

### User Story 11 — Webhook Verification Independent of Debug Mode (Priority: P3)

As a system operator, I expect webhook signature verification to be enforced regardless of the application's debug mode setting, so that accidentally enabling debug mode in production does not bypass security.

**Why this priority**: Conditional webhook verification (OWASP A05 Medium) means debug mode in production silently disables authentication for webhook callers.

**Independent Test**: Start the application with `DEBUG=true` and no webhook secret. Verify that webhook requests without valid signatures are still rejected.

**Acceptance Scenarios**:

1. **Given** the application runs with `DEBUG=true`, **When** a webhook request arrives without a valid signature, **Then** the request is rejected.
2. **Given** the application runs in any mode, **When** webhook verification is performed, **Then** the verification logic does not branch on the DEBUG flag.

---

### User Story 12 — Secure Database Permissions and Data Volume Isolation (Priority: P3)

As a system operator, I expect the database directory and files to have restricted permissions and the data volume to be mounted outside the application root, so that co-located processes cannot read the database and runtime data does not commingle with application code.

**Why this priority**: World-readable database directories (OWASP A02 Medium) and data volumes inside the application root (OWASP A05 Medium) are both container security hygiene issues.

**Independent Test**: Inspect database directory permissions (expect 0700) and file permissions (expect 0600). Verify the data volume mount point is outside the application directory.

**Acceptance Scenarios**:

1. **Given** the application initializes the database, **When** the database directory permissions are inspected, **Then** they are set to 0700.
2. **Given** the application initializes the database, **When** the database file permissions are inspected, **Then** they are set to 0600.
3. **Given** the docker-compose configuration, **When** the data volume mount point is inspected, **Then** it is located outside the application root directory (e.g., `/var/lib/solune/data`).

---

### User Story 13 — Secure Configuration Validation (Priority: P3)

As a system operator, I expect the application to validate all configuration values at startup, including CORS origins and API documentation settings, so that misconfigurations are caught immediately rather than silently causing security issues.

**Why this priority**: Unvalidated CORS origins (OWASP A05 Medium) and debug-gated API docs (OWASP A05 Medium) are configuration hygiene issues that compound into security gaps.

**Independent Test**: Start the application with malformed CORS origins. Verify the application fails to start with a descriptive error. Verify API docs availability is controlled by a dedicated `ENABLE_DOCS` toggle, not `DEBUG`.

**Acceptance Scenarios**:

1. **Given** a CORS origins environment variable contains a malformed URL, **When** the application starts, **Then** it fails with a descriptive validation error.
2. **Given** CORS origins are properly formatted, **When** the application starts, **Then** startup succeeds.
3. **Given** `DEBUG=true` but `ENABLE_DOCS` is not set, **When** a user accesses `/docs` or `/redoc`, **Then** the API documentation is not available.
4. **Given** `ENABLE_DOCS=true`, **When** a user accesses `/docs` or `/redoc`, **Then** the API documentation is available regardless of DEBUG setting.

---

### User Story 14 — Sanitized Error Messages (Priority: P3)

As a user, I expect that error responses from the application never expose internal details such as query structures, token scope details, or stack traces, so that attackers cannot use error messages to discover internal architecture.

**Why this priority**: Verbose error messages (OWASP A09 Medium) from GraphQL and other internal APIs can leak query structure or token scope details.

**Independent Test**: Trigger an error condition in the GraphQL integration and verify the user-facing error message is generic while the full error is logged internally.

**Acceptance Scenarios**:

1. **Given** the GitHub GraphQL API returns an error, **When** the error propagates to the API response, **Then** only a generic sanitized message is returned to the user.
2. **Given** the GitHub GraphQL API returns an error, **When** the error is processed internally, **Then** the full error details are logged for debugging.

---

### User Story 15 — Least-Privilege CI Permissions and Safe Avatar Rendering (Priority: P4)

As a repository maintainer, I expect CI workflows to request only the minimum permissions needed, and as a user, I expect avatar images to be validated before rendering, so that supply chain risk is minimized and injection via external image URLs is prevented.

**Why this priority**: Overly broad CI permissions (Supply Chain, Low) and unvalidated avatar URLs (OWASP A03, Low) are lower-risk but still represent defense-in-depth gaps.

**Independent Test**: Inspect the CI workflow file for scoped permissions. Render an issue card with a non-GitHub avatar URL and verify it falls back to a placeholder.

**Acceptance Scenarios**:

1. **Given** the CI workflow file, **When** its permissions block is inspected, **Then** only the minimum necessary permissions are declared with justification comments.
2. **Given** an issue card receives an avatar URL, **When** the URL uses `https:` and originates from a known GitHub avatar domain, **Then** the image is rendered.
3. **Given** an issue card receives an avatar URL, **When** the URL does not use `https:` or does not originate from a known GitHub avatar domain, **Then** a placeholder image is rendered instead.

---

### Edge Cases

- What happens when `ENCRYPTION_KEY` is set but invalid (e.g., wrong length, non-base64)?
- What happens when a user's OAuth token was stored in plaintext before encryption enforcement? (Migration path required)
- What happens when a rate-limited user's request arrives at the exact moment the rate limit window resets?
- What happens when the OAuth provider changes required scopes or deprecates the current ones?
- What happens when CORS origins contain duplicate entries or trailing slashes?
- What happens when the database directory already exists with incorrect permissions?
- What happens when a WebSocket connection is established for an owned project, but ownership is revoked while the connection is active?
- What happens when `DEBUG=true` and `ENABLE_DOCS=true` are both set (should docs be available)?

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST set session credentials as `HttpOnly; SameSite=Strict; Secure` cookies on the OAuth callback response and MUST NOT include any credentials as URL query parameters.
- **FR-002**: Frontend MUST NOT read or process any credentials from URL parameters.
- **FR-003**: System MUST refuse to start in non-debug mode if `ENCRYPTION_KEY` environment variable is not set.
- **FR-004**: System MUST refuse to start in non-debug mode if `GITHUB_WEBHOOK_SECRET` environment variable is not set.
- **FR-005**: All containers (frontend and backend) MUST run as a dedicated non-root system user with a non-zero UID.

**Phase 2 — High**

- **FR-006**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action.
- **FR-007**: The project access check MUST be centralized as a shared dependency (not duplicated in each endpoint).
- **FR-008**: WebSocket connections MUST verify project ownership before transmitting any data.
- **FR-009**: All secret and token comparisons throughout the codebase MUST use constant-time comparison functions (e.g., `hmac.compare_digest`).
- **FR-010**: The frontend reverse proxy MUST serve the following HTTP security headers: `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`, and `X-Content-Type-Options`.
- **FR-011**: The frontend reverse proxy MUST NOT serve the deprecated `X-XSS-Protection` header.
- **FR-012**: The frontend reverse proxy MUST NOT expose server software version information.
- **FR-013**: All credential inputs, including dev-only endpoints, MUST arrive in the POST request body (JSON), never in URL query parameters.
- **FR-014**: The OAuth authorization flow MUST request only the minimum necessary scopes for project management operations, and any broader retained scope MUST be explicitly justified and documented.
- **FR-015**: System MUST reject `SESSION_SECRET_KEY` values shorter than 64 characters in non-debug mode and MUST emit a clear warning in debug mode.
- **FR-016**: Development services MUST bind to `127.0.0.1` only; production services MUST NOT be directly exposed via container ports.

**Phase 3 — Medium**

- **FR-017**: Sensitive and expensive endpoints (chat, AI agents, workflows) MUST enforce per-user rate limits.
- **FR-018**: The OAuth callback endpoint MUST enforce per-IP rate limits.
- **FR-019**: System MUST refuse to start in non-debug mode if `cookie_secure` is not configured as enabled.
- **FR-020**: Webhook signature verification MUST NOT be conditional on the DEBUG flag.
- **FR-021**: API documentation availability MUST be controlled by a dedicated `ENABLE_DOCS` environment variable, independent of DEBUG.
- **FR-022**: The database directory MUST be created with 0700 permissions and database files MUST be created with 0600 permissions.
- **FR-023**: CORS origins MUST be validated at startup; each origin must be a well-formed URL with scheme and hostname; the application MUST fail on any malformed value.
- **FR-024**: Data volumes MUST be mounted outside the application root directory.
- **FR-025**: Frontend MUST store only lightweight references (message IDs) in localStorage, not full message content.
- **FR-026**: Frontend MUST clear all application data from localStorage on logout.
- **FR-027**: Locally stored references MUST have a configurable time-to-live (TTL) and be automatically removed when expired.
- **FR-028**: Errors from external APIs (e.g., GitHub GraphQL) MUST be logged internally with full details but MUST return only a generic sanitized message to the user.

**Phase 4 — Low**

- **FR-029**: CI workflow files MUST declare only the minimum necessary permissions with justification comments.
- **FR-030**: Avatar URLs MUST be validated to use `https:` protocol and originate from a known GitHub avatar domain before rendering; invalid URLs MUST fall back to a placeholder image.

### Key Entities

- **Session**: Represents an authenticated user session. Contains session token (stored in HttpOnly cookie), user identifier, associated OAuth scopes, creation timestamp, and expiration.
- **Project**: Represents a user's project. Has an owner relationship to a User; all project endpoints must verify this ownership.
- **Rate Limit Record**: Tracks request counts per user (or per IP for anonymous endpoints) per time window. Contains user/IP identifier, endpoint category, request count, and window expiration.
- **Chat Reference**: A lightweight local storage entry containing a message ID, creation timestamp, and TTL. Does not contain message content.
- **Configuration**: Startup-validated set of environment variables including `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, `SESSION_SECRET_KEY`, `CORS_ORIGINS`, `ENABLE_DOCS`, and `cookie_secure`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, no credentials appear in the browser URL bar, browser history, or server access logs — verified by inspection.
- **SC-002**: The application refuses to start in production mode when any mandatory secret (`ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, `SESSION_SECRET_KEY` with 64+ characters) is missing or invalid — verified by startup tests.
- **SC-003**: All containers run as non-root users — verified by `docker exec <container> id` returning non-zero UID.
- **SC-004**: Authenticated requests targeting unowned project IDs return 403 Forbidden in 100% of tested endpoint categories (task creation, WebSocket subscription, project settings, workflow operations) — verified by integration tests.
- **SC-005**: WebSocket connections to unowned project IDs are rejected before any data is sent — verified by WebSocket integration test.
- **SC-006**: 100% of secret/token comparisons in the codebase use constant-time comparison functions — verified by code review audit.
- **SC-007**: Frontend responses include all five required security headers (`Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`, `X-Content-Type-Options`) and do not include deprecated headers or server version — verified by `curl -I` inspection.
- **SC-008**: After exceeding rate limit thresholds, expensive endpoints return 429 Too Many Requests — verified by load testing.
- **SC-009**: After logout, browser localStorage contains no application message content — verified by DevTools inspection.
- **SC-010**: Database directory permissions are 0700 and file permissions are 0600 — verified by filesystem inspection inside the container.
- **SC-011**: OAuth authorization requests use minimum necessary scopes by default, with any broader retained scope explicitly justified in the review artifacts — verified by intercepting the authorization URL during login and checking the linked rationale.
- **SC-012**: No user-facing error response contains internal details such as query structures, token scopes, or stack traces — verified by triggering error conditions in integration tests.

## Assumptions

- The application uses a Python (FastAPI) backend and a React (TypeScript) frontend served by nginx.
- The backend already runs as a non-root user; only the frontend Dockerfile requires changes.
- The existing `hmac.compare_digest` pattern in GitHub webhook verification serves as the reference implementation for other secret comparisons.
- OAuth scope narrowing may require existing users to re-authorize. A staging test phase is needed before production rollout.
- Encryption enforcement is a breaking change for deployments without a key. A migration path for existing plaintext rows must be included.
- Per-user rate limits are preferred over per-IP limits to avoid penalizing users behind shared NAT/VPN.
- The data retention period for chat references follows industry-standard TTL practices (e.g., 24-hour default, configurable).
- Known GitHub avatar domains include `avatars.githubusercontent.com` and `github.com`.
- Out of scope: GitHub API internal security, MCP server internals, network-layer infrastructure.

## Key Decisions

- **OAuth scope removal (FR-014)**: May break write operations. Must be tested in staging; users must re-authorize after scope change.
- **Encryption enforcement (FR-003, FR-004)**: Breaking change for deployments without a key. Migration path for existing plaintext rows must be included in the same change.
- **Rate limiting strategy (FR-017, FR-018)**: Per-user limits preferred over per-IP to avoid penalizing shared NAT/VPN users. Per-IP used only for anonymous endpoints (OAuth callback).
- **Phased rollout**: Findings are prioritized into four phases (Critical → High → Medium → Low) to manage risk and development capacity.
