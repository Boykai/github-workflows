# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `025-security-review`
**Created**: 2026-03-06
**Status**: Draft
**Input**: User description: "Security, Privacy & Vulnerability Audit — 3 Critical · 8 High · 9 Medium · 2 Low findings across OWASP Top 10. Covers session management, encryption enforcement, container hardening, access control, rate limiting, data privacy, and supply-chain hygiene."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Credential Leak Prevention (Priority: P1)

As a user logging in via OAuth, I need my session credentials to never appear in the browser URL bar, browser history, server logs, or HTTP Referer headers so that my account cannot be compromised by credential interception.

**Why this priority**: Tokens in URLs are actively exploitable by anyone with access to browser history, proxy logs, or CDN logs. This is the single highest-risk finding because it exposes credentials to passive observers.

**Independent Test**: Complete a full OAuth login flow and verify that at no point does a session token, access token, or any credential appear in the browser address bar or URL parameters. Inspect browser history and network requests to confirm absence of credentials in URLs.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth callback completes, **Then** the backend sets an HttpOnly, SameSite=Strict, Secure cookie and redirects the browser with no credentials in the URL.
2. **Given** a user completes login, **When** inspecting browser history, **Then** no URL entry contains a session token or access token as a query parameter.
3. **Given** a dev-mode login is used, **When** the developer submits credentials, **Then** the credentials are sent in a POST request body (JSON), never as URL query parameters.

---

### User Story 2 — Encryption & Secret Enforcement at Startup (Priority: P1)

As an operator deploying the application, I need the system to refuse to start in production mode when critical secrets are missing or weak so that plaintext credential storage and weak session signing are impossible.

**Why this priority**: Without mandatory encryption keys and strong session secrets, the application silently operates in an insecure state. Enforcement at startup is a zero-cost gate that prevents entire classes of vulnerabilities.

**Independent Test**: Attempt to start the backend in non-debug mode without setting ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET, or with a SESSION_SECRET_KEY shorter than 64 characters. Verify each case causes a startup failure with a clear error message.

**Acceptance Scenarios**:

1. **Given** the application starts in non-debug mode, **When** ENCRYPTION_KEY is not set, **Then** the application refuses to start and logs an explicit error message.
2. **Given** the application starts in non-debug mode, **When** GITHUB_WEBHOOK_SECRET is not set, **Then** the application refuses to start and logs an explicit error message.
3. **Given** SESSION_SECRET_KEY is set to a value shorter than 64 characters, **When** the application starts, **Then** it refuses to start and logs an error indicating the minimum required length.
4. **Given** the application starts in non-debug mode, **When** cookies are not configured as Secure, **Then** the application refuses to start.

---

### User Story 3 — Container Security Hardening (Priority: P1)

As an operator, I need all containers to run as non-root users so that a container escape or compromise does not grant root-level access to the host.

**Why this priority**: Running as root in a container is a critical security misconfiguration. If any vulnerability allows code execution inside the container, root access dramatically amplifies the blast radius.

**Independent Test**: Build and run the frontend container, then execute `id` inside it. Verify the process runs as a non-root user (UID ≠ 0).

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** executing `id` inside the container, **Then** the reported UID is non-zero (a dedicated application user).
2. **Given** the frontend container is running, **When** nginx serves requests, **Then** it operates correctly under the non-root user without permission errors.

---

### User Story 4 — Project-Level Access Control (Priority: P2)

As a user, I need each project I own to be inaccessible to other authenticated users so that my project data, tasks, settings, and workflows are private.

**Why this priority**: Without authorization checks, any authenticated user can read or modify any project by guessing its ID. This is a fundamental access control failure (OWASP A01 — Broken Access Control).

**Independent Test**: Authenticate as User A, create a project, then authenticate as User B and attempt to access User A's project by ID via each endpoint (tasks, settings, workflows, WebSocket). Verify all return 403 Forbidden.

**Acceptance Scenarios**:

1. **Given** User A owns a project, **When** User B sends a request to any endpoint using User A's project_id, **Then** the response is 403 Forbidden.
2. **Given** User A owns a project, **When** User B attempts a WebSocket connection to User A's project, **Then** the connection is rejected before any data is sent.
3. **Given** a project ownership check is needed, **When** any endpoint processes a project_id, **Then** a centralized authorization dependency verifies ownership before any action is performed.

---

### User Story 5 — Secure HTTP Headers & Server Hardening (Priority: P2)

As a user accessing the application in a browser, I need proper security headers to be present on all responses so that I am protected from clickjacking, content injection, protocol downgrade, and information leakage.

**Why this priority**: Missing security headers leave users vulnerable to well-known browser-based attacks. These are configuration-only changes with high security value and low risk.

**Independent Test**: Send a HEAD request to the frontend and verify the response includes Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers. Verify X-XSS-Protection is absent and the Server header does not reveal the nginx version.

**Acceptance Scenarios**:

1. **Given** a request to the frontend, **When** examining response headers, **Then** Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers are present.
2. **Given** a request to the frontend, **When** examining response headers, **Then** X-XSS-Protection is absent and the Server header does not disclose the nginx version.

---

### User Story 6 — Constant-Time Secret Comparison (Priority: P2)

As a system receiving webhook requests, I need all secret comparisons to use constant-time algorithms so that timing side-channel attacks cannot be used to guess webhook secrets.

**Why this priority**: Standard string comparison leaks timing information proportional to the number of matching prefix bytes. This enables practical brute-force extraction of secrets.

**Independent Test**: Code review all secret/token comparison call sites and verify each uses `hmac.compare_digest` or an equivalent constant-time function.

**Acceptance Scenarios**:

1. **Given** the Signal webhook receives a request with a secret, **When** the secret is compared, **Then** `hmac.compare_digest` (or equivalent constant-time comparison) is used.
2. **Given** any code path compares a secret or token, **When** performing the comparison, **Then** constant-time comparison is used throughout the codebase.

---

### User Story 7 — OAuth Scope Minimization (Priority: P2)

As a user authorizing the application via GitHub OAuth, I need the application to request only the minimum necessary permissions so that my private repositories are not exposed to unnecessary read/write access.

**Why this priority**: The `repo` scope grants full access to all private repositories. Reducing to minimum necessary scopes limits the blast radius if tokens are compromised.

**Independent Test**: Initiate the OAuth flow and inspect the authorization URL. Verify the requested scopes are the minimum necessary for application functionality (no full `repo` scope). Verify all application write operations still work with the narrower scopes.

**Acceptance Scenarios**:

1. **Given** the OAuth authorization URL is generated, **When** inspecting the requested scopes, **Then** the `repo` scope is not requested; only minimum necessary scopes are included.
2. **Given** a user has authorized with narrower scopes, **When** performing all application write operations, **Then** all operations succeed without scope-related errors.

---

### User Story 8 — Network Binding & Docker Hardening (Priority: P2)

As an operator, I need Docker services to bind only to localhost in development and to be accessible only via reverse proxy in production so that backend and frontend ports are not exposed on all network interfaces.

**Why this priority**: Binding to 0.0.0.0 exposes services on all interfaces, making them reachable from any network the host is connected to.

**Independent Test**: Inspect the Docker Compose configuration for development and production. Verify development services bind to 127.0.0.1 and production services do not expose ports directly.

**Acceptance Scenarios**:

1. **Given** the development Docker Compose configuration, **When** services are started, **Then** backend and frontend ports bind to 127.0.0.1 only.
2. **Given** the production Docker Compose configuration, **When** services are started, **Then** services are only accessible via the reverse proxy, not via directly exposed container ports.
3. **Given** the Docker Compose configuration, **When** data volumes are mounted, **Then** they mount outside the application root directory (e.g., `/var/lib/ghchat/data`).

---

### User Story 9 — Rate Limiting on Sensitive Endpoints (Priority: P3)

As a user of the application, I need expensive and sensitive endpoints to have rate limits so that a single user cannot exhaust shared AI or GitHub API quotas and degrade service for everyone.

**Why this priority**: Without rate limits, malicious or misbehaving clients can consume all shared resources. This is a medium-priority defense-in-depth measure.

**Independent Test**: Send requests above the configured rate limit threshold to chat, agent, workflow, and OAuth callback endpoints. Verify the system returns 429 Too Many Requests after the limit is exceeded.

**Acceptance Scenarios**:

1. **Given** a user sends requests to a rate-limited write/AI endpoint, **When** the per-user limit is exceeded, **Then** subsequent requests return 429 Too Many Requests.
2. **Given** an IP sends requests to the OAuth callback endpoint, **When** the per-IP limit is exceeded, **Then** subsequent requests return 429 Too Many Requests.

---

### User Story 10 — Secure Data Storage & Privacy (Priority: P3)

As a user, I need my chat history and other sensitive data to be stored securely so that it is not exposed to XSS attacks, persisted indefinitely, or readable by unauthorized processes.

**Why this priority**: Plaintext localStorage data survives logout and is fully readable by any XSS vulnerability. Combined with restrictive file permissions, this story addresses multiple data-at-rest concerns.

**Independent Test**: Log in, send chat messages, then log out. Inspect localStorage in browser devtools and verify no message content remains. Inspect the database directory permissions (0700) and file permissions (0600).

**Acceptance Scenarios**:

1. **Given** a user is logged in and has chat messages, **When** the user logs out, **Then** localStorage contains no message content (only lightweight references if any).
2. **Given** the application creates its database directory, **When** checking directory permissions, **Then** they are set to 0700.
3. **Given** the application creates its database file, **When** checking file permissions, **Then** they are set to 0600.
4. **Given** chat history is loaded in the browser, **When** examining what is stored locally, **Then** only message IDs (not full content) are stored, with a time-to-live expiration.

---

### User Story 11 — Configuration Validation & Debug Isolation (Priority: P3)

As an operator, I need configuration to be validated at startup and debug features to be properly isolated so that misconfigurations and accidental debug mode in production do not create security holes.

**Why this priority**: Several findings relate to configuration that silently accepts invalid or dangerous values. Centralizing validation prevents an entire class of operational security issues.

**Independent Test**: Start the application with malformed CORS origins, with debug mode on and no webhook secret, and with docs gated only on DEBUG. Verify each case either fails at startup or behaves securely.

**Acceptance Scenarios**:

1. **Given** CORS_ORIGINS contains a malformed URL, **When** the application starts, **Then** it fails with an error identifying the invalid origin.
2. **Given** DEBUG is true and no webhook secret is set, **When** a webhook request arrives, **Then** signature verification is still enforced (uses a locally configured test secret).
3. **Given** API docs exposure, **When** checking docs availability, **Then** it is gated by a separate ENABLE_DOCS environment variable, independent of DEBUG.
4. **Given** GraphQL errors are received from external APIs, **When** errors are surfaced to the user, **Then** only a generic sanitized message is returned; full details are logged internally.

---

### User Story 12 — Supply Chain & Injection Safeguards (Priority: P4)

As a user, I need the application to validate external content and minimize workflow permissions so that supply-chain and injection risks are reduced.

**Why this priority**: These are lower-risk findings that provide defense-in-depth but do not represent immediate exploitable vulnerabilities.

**Independent Test**: Review the GitHub Actions workflow permissions and verify they are scoped to the minimum needed. Render a page with avatar URLs and verify only HTTPS URLs from known GitHub domains are displayed; others show a placeholder.

**Acceptance Scenarios**:

1. **Given** the GitHub Actions workflow file, **When** reviewing permissions, **Then** `issues: write` (or narrower) is scoped to the minimum needed, with a justification comment.
2. **Given** an avatar URL from the GitHub API, **When** rendering the avatar image, **Then** only HTTPS URLs from known GitHub avatar domains are used; all others fall back to a placeholder image.

---

### Edge Cases

- What happens when ENCRYPTION_KEY is set but contains insufficient entropy or is malformed?
- What happens when a user's OAuth token is stored in plaintext from a previous deployment and encryption is now enforced?
- What happens when a user accesses a project that was shared but sharing was later revoked?
- What happens when rate limit state is lost due to application restart?
- What happens when the GitHub API returns avatar URLs from a newly added CDN domain not in the allowlist?
- What happens when a user has an active session but their project ownership changes concurrently?

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: The OAuth callback MUST set session credentials as an HttpOnly, SameSite=Strict, Secure cookie and MUST NOT include any credentials in the redirect URL.
- **FR-002**: The frontend MUST NOT read session credentials from URL parameters.
- **FR-003**: The application MUST refuse to start in non-debug mode if ENCRYPTION_KEY is not set.
- **FR-004**: The application MUST refuse to start in non-debug mode if GITHUB_WEBHOOK_SECRET is not set.
- **FR-005**: All containers MUST run as a dedicated non-root system user.

**Phase 2 — High**

- **FR-006**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action.
- **FR-007**: Project authorization MUST be implemented as a centralized, shared dependency (not duplicated per endpoint).
- **FR-008**: All secret and token comparisons MUST use constant-time comparison functions.
- **FR-009**: The frontend reverse proxy MUST include Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers on all responses.
- **FR-010**: The frontend reverse proxy MUST NOT include X-XSS-Protection or expose the server software version.
- **FR-011**: The dev login endpoint MUST accept credentials in the POST request body (JSON), not as URL query parameters.
- **FR-012**: The OAuth authorization request MUST use minimum necessary scopes (not the full `repo` scope).
- **FR-013**: The application MUST reject SESSION_SECRET_KEY values shorter than 64 characters at startup.
- **FR-014**: Development Docker services MUST bind to 127.0.0.1 only; production services MUST NOT expose ports directly.

**Phase 3 — Medium**

- **FR-015**: Chat, agent invocation, workflow, and OAuth callback endpoints MUST enforce rate limits (per-user for write/AI endpoints, per-IP for OAuth callback).
- **FR-016**: Rate-limited endpoints MUST return 429 Too Many Requests when limits are exceeded.
- **FR-017**: The application MUST fail to start in non-debug mode if cookies are not configured as Secure.
- **FR-018**: Webhook signature verification MUST NOT be conditional on debug mode.
- **FR-019**: API documentation exposure MUST be controlled by a dedicated ENABLE_DOCS environment variable, independent of DEBUG.
- **FR-020**: The database directory MUST be created with 0700 permissions; the database file MUST be created with 0600 permissions.
- **FR-021**: CORS origins MUST be validated as well-formed URLs with scheme and hostname at startup; malformed values MUST cause startup failure.
- **FR-022**: Data volumes MUST mount outside the application root directory.
- **FR-023**: The browser MUST store only lightweight message references (IDs) with a TTL, not full message content. All local data MUST be cleared on logout.
- **FR-024**: GraphQL error messages from external APIs MUST be logged internally and replaced with generic sanitized messages in API responses.

**Phase 4 — Low**

- **FR-025**: GitHub Actions workflows MUST use minimum necessary permissions with justification comments.
- **FR-026**: Avatar URLs MUST be validated to use HTTPS from known GitHub avatar domains; invalid URLs MUST fall back to a placeholder image.

### Key Entities

- **Session**: Represents an authenticated user's session; stored as an HttpOnly cookie; associated with a user and their project permissions.
- **Project**: A user-owned resource; all operations on a project must be gated by an ownership or access check.
- **Configuration**: The set of environment variables and startup parameters; validated at startup for completeness, correctness, and security requirements.
- **Rate Limit State**: Per-user and per-IP counters for sensitive endpoints; resets on a sliding or fixed time window.
- **Chat Reference**: A lightweight local storage entry containing only a message ID and TTL, replacing full message content storage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, no credentials appear in the browser URL bar, browser history, or application access logs — verified by manual and automated testing across all login flows.
- **SC-002**: The application fails to start within 5 seconds with a clear error when any mandatory secret (ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET) is missing in non-debug mode.
- **SC-003**: All containers report a non-root UID when inspected via `docker exec <container> id`.
- **SC-004**: 100% of API requests with an unowned project_id receive a 403 response, with zero data leakage.
- **SC-005**: WebSocket connections to unowned projects are rejected before any project data is transmitted.
- **SC-006**: Code review confirms 100% of secret/token comparisons use constant-time functions.
- **SC-007**: Frontend HTTP responses include all four required security headers and expose no server version information.
- **SC-008**: Endpoints return 429 Too Many Requests within 1 second of exceeding configured rate limits.
- **SC-009**: After logout, browser localStorage contains zero bytes of message content.
- **SC-010**: Database directory permissions are 0700 and file permissions are 0600 as verified by `stat` commands inside the container.
- **SC-011**: The OAuth authorization URL requests only minimum necessary scopes; users are not prompted for full private repository access.
- **SC-012**: All 10 behavior-based verification checks defined in the audit pass in a staging environment.

## Assumptions

- The existing backend authentication middleware provides the current user's identity, which can be used to implement project ownership checks.
- A centralized project authorization dependency can be injected into existing endpoint handlers without restructuring the API layer.
- The `repo` scope can be replaced with narrower scopes (e.g., `read:org`, `project`) without breaking existing application functionality; this requires staging validation before production rollout.
- Existing plaintext OAuth token rows will require a one-time migration to encrypted format when ENCRYPTION_KEY enforcement is enabled; a migration path is included in the same change.
- A rate limiting library compatible with the current backend framework is available and can be integrated without major refactoring.
- The frontend build process can accommodate the nginx non-root user change without modification to the build pipeline.
- Per-user rate limits are preferred over per-IP limits to avoid penalizing users behind shared NAT or VPN connections.
- GitHub API security, MCP server internals, and network-layer infrastructure are out of scope for this audit.

## Scope Boundaries

### In Scope

- All 21 findings listed in the audit across Phases 1–4
- Behavior-based verification checks (10 items)
- Migration path for existing plaintext encrypted data
- Configuration validation improvements

### Out of Scope

- GitHub API security (GitHub's responsibility)
- MCP server internals
- Network-layer infrastructure (firewalls, load balancers, DNS)
- Penetration testing (separate engagement)
- Third-party dependency vulnerability scanning (separate tooling)

## Key Decisions

- **OAuth scope removal**: May break write operations. Must be tested in staging; users must re-authorize after scope change.
- **Encryption enforcement**: Breaking change for deployments without a key. Migration path for existing plaintext rows must be included in the same change.
- **Rate limiting strategy**: Per-user limits preferred over per-IP to avoid penalizing shared NAT/VPN users.
- **Phased rollout**: Findings are prioritized by severity (Critical → Low) to enable incremental delivery and risk reduction.

## Dependencies

- Existing OAuth flow implementation (auth.py, useAuth.ts)
- Existing configuration loading (config.py)
- Existing Docker infrastructure (Dockerfile, docker-compose.yml, nginx.conf)
- Existing API endpoint handlers (tasks.py, projects.py, settings.py, workflow.py, chat.py, agents.py)
- Rate limiting library compatible with the backend framework
- Staging environment for OAuth scope validation
