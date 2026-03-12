# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `037-security-review`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Security, Privacy & Vulnerability Audit — 3 Critical · 8 High · 9 Medium · 2 Low findings across OWASP Top 10"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Credential Leakage Prevention (Priority: P1)

As a user logging in via OAuth, I expect that my session credentials are never exposed in the browser URL bar, browser history, server access logs, or HTTP Referer headers so that my account cannot be hijacked by anyone with access to those locations.

**Why this priority**: Session token exposure in URLs is the most directly exploitable vulnerability. Any log aggregator, shared browser, proxy, or CDN cache could capture and replay a valid session, leading to full account takeover.

**Independent Test**: Complete an OAuth login flow and verify that no credentials appear in the browser address bar, navigation history, or network request URLs at any point.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth provider redirects back to the application, **Then** the session credential is delivered via a secure, HttpOnly cookie — never as a URL parameter.
2. **Given** a completed OAuth login, **When** the user inspects browser history and the URL bar, **Then** no session tokens or secrets appear in any URL.
3. **Given** a dev-mode login, **When** a developer authenticates with a personal access token, **Then** the credential is transmitted in the request body, never in the URL.

---

### User Story 2 — Mandatory Encryption and Secret Enforcement (Priority: P1)

As a deployment operator, I expect the application to refuse to start in production if critical security secrets are missing or weak, so that misconfigured deployments never silently run in an insecure state.

**Why this priority**: Storing OAuth tokens in plaintext or accepting weak session secrets means a single database leak or memory dump exposes all user credentials. Failing loudly at startup prevents silent misconfigurations that are far harder to detect after deployment.

**Independent Test**: Attempt to start the backend in non-debug mode without setting the encryption key, webhook secret, or with a short session key, and verify the application exits with a clear error.

**Acceptance Scenarios**:

1. **Given** the application is starting in non-debug mode, **When** the encryption key environment variable is not set, **Then** the application refuses to start and logs a clear error message.
2. **Given** the application is starting in non-debug mode, **When** the webhook secret environment variable is not set, **Then** the application refuses to start and logs a clear error message.
3. **Given** the application is starting in any mode, **When** the session secret key is fewer than 64 characters, **Then** the application refuses to start and logs a clear error message.
4. **Given** the application is starting in non-debug mode, **When** cookies are not configured as Secure, **Then** the application refuses to start and logs a clear error message.

---

### User Story 3 — Project-Level Access Control (Priority: P1)

As an authenticated user, I expect that I can only access, modify, and subscribe to projects that I own, so that my project data is protected from other users who might guess or enumerate project identifiers.

**Why this priority**: Without authorization checks, any authenticated user can read, modify, or subscribe to any project by guessing its ID — a broken access control vulnerability that directly compromises data confidentiality and integrity for every user.

**Independent Test**: Authenticate as User A, attempt to access a project owned by User B using its identifier, and verify the request is rejected with a 403 Forbidden response.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they attempt to create a task under a project they do not own, **Then** the system returns a 403 Forbidden response.
2. **Given** an authenticated user, **When** they attempt to open a WebSocket subscription to a project they do not own, **Then** the connection is rejected before any data is sent.
3. **Given** an authenticated user, **When** they attempt to modify settings for a project they do not own, **Then** the system returns a 403 Forbidden response.
4. **Given** an authenticated user, **When** they attempt to trigger a workflow on a project they do not own, **Then** the system returns a 403 Forbidden response.

---

### User Story 4 — Container and Infrastructure Hardening (Priority: P2)

As a deployment operator, I expect all containers to run as non-root users, bind only to localhost in development, and expose services only through a reverse proxy in production, so that the attack surface is minimized in case of a container escape or network misconfiguration.

**Why this priority**: Running containers as root and binding to all network interfaces are high-severity misconfigurations that amplify the impact of any other vulnerability. Hardening these reduces blast radius.

**Independent Test**: Exec into the frontend container, run `id`, and verify a non-root UID is returned. Inspect docker-compose port bindings and verify they target localhost only.

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** a user inspects the running process, **Then** it runs as a dedicated non-root system user.
2. **Given** a development docker-compose configuration, **When** services are started, **Then** ports are bound to 127.0.0.1 only.
3. **Given** a production deployment, **When** services are running, **Then** backend and frontend are accessible only via the reverse proxy, not via direct container ports.
4. **Given** a docker-compose configuration, **When** data volumes are mounted, **Then** they are located outside the application root directory.

---

### User Story 5 — HTTP Security Headers and Timing-Safe Comparisons (Priority: P2)

As a user browsing the application, I expect the server to send modern security headers that protect against clickjacking, XSS, and protocol downgrade attacks. As a developer, I expect all secret comparisons to be resistant to timing attacks.

**Why this priority**: Missing security headers and timing-vulnerable comparisons are straightforward fixes that meaningfully reduce the application's exposure to common web attacks.

**Independent Test**: Send a HEAD request to the frontend and verify the presence of Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers, and the absence of the deprecated X-XSS-Protection header and nginx version in the Server header. Review all secret comparisons in the codebase for constant-time usage.

**Acceptance Scenarios**:

1. **Given** a request to the frontend, **When** the response headers are inspected, **Then** Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers are present.
2. **Given** a request to the frontend, **When** the response headers are inspected, **Then** the X-XSS-Protection header is absent and the Server header does not reveal the nginx version.
3. **Given** a webhook request with a secret, **When** the secret is compared for validation, **Then** a constant-time comparison function is used.

---

### User Story 6 — OAuth Scope Minimization (Priority: P2)

As a user authorizing the application via OAuth, I expect the application to request only the minimum permissions it needs, so that a compromised token cannot be used to read or modify my private repositories.

**Why this priority**: Overly broad OAuth scopes violate the principle of least privilege. If a token is leaked, the blast radius is far larger than necessary.

**Independent Test**: Initiate an OAuth authorization flow and verify the requested scopes are limited to project-management-level access, excluding full repository read/write.

**Acceptance Scenarios**:

1. **Given** a user begins OAuth authorization, **When** the authorization URL is constructed, **Then** it requests only the minimum scopes needed for project management features.
2. **Given** the scopes have been narrowed, **When** a user performs all supported write operations, **Then** all operations succeed without errors.

---

### User Story 7 — Rate Limiting on Sensitive Endpoints (Priority: P3)

As a platform operator, I expect expensive and sensitive endpoints (chat, agent invocation, workflow triggers, OAuth callback) to enforce rate limits, so that a single user or attacker cannot exhaust shared resources or abuse the OAuth flow.

**Why this priority**: Without rate limits, a single abusive user can exhaust shared AI and GitHub API quotas, impacting all users. This is a resource-exhaustion risk rather than a direct data breach, so it is prioritized below access control and credential safety.

**Independent Test**: Send requests to a rate-limited endpoint exceeding the configured threshold and verify a 429 Too Many Requests response is returned.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they exceed the per-user rate limit on a write or AI endpoint, **Then** the system returns 429 Too Many Requests.
2. **Given** an unauthenticated client, **When** they exceed the per-IP rate limit on the OAuth callback, **Then** the system returns 429 Too Many Requests.

---

### User Story 8 — Secure Local Storage and Error Sanitization (Priority: P3)

As a user, I expect the application to not persist full chat message content in browser local storage indefinitely, and I expect that internal error details from third-party APIs are never exposed to me in error messages.

**Why this priority**: Storing full chat content in localStorage with no TTL or logout cleanup creates a privacy risk (readable by any XSS) and a data retention concern. Leaking internal error details aids attackers in reconnaissance.

**Independent Test**: Log out of the application and verify localStorage contains no message content. Trigger a backend error originating from a third-party API and verify the response contains only a generic error message.

**Acceptance Scenarios**:

1. **Given** a user has an active chat history, **When** they log out, **Then** all chat-related data is cleared from localStorage.
2. **Given** a chat session, **When** messages are stored locally, **Then** only lightweight references (message IDs) are persisted, not full message content.
3. **Given** a request that triggers a third-party API error, **When** the error response is returned to the client, **Then** only a generic sanitized message is included; internal details are logged server-side only.

---

### User Story 9 — Secure Configuration and Debug Isolation (Priority: P3)

As a deployment operator, I expect that debug mode does not bypass any security controls, that API documentation exposure is controlled independently of debug mode, and that misconfigured CORS origins are rejected at startup.

**Why this priority**: Coupling security controls to debug flags creates risk of silent security degradation if debug is accidentally enabled in production. These are defense-in-depth measures that prevent misconfiguration from becoming exploitable.

**Independent Test**: Start the application with DEBUG=true and verify that webhook signature verification still occurs, API docs are only available when explicitly enabled, CORS origins are validated, and database directories have restrictive permissions.

**Acceptance Scenarios**:

1. **Given** the application is running with DEBUG=true, **When** a webhook request arrives without a valid signature, **Then** it is rejected.
2. **Given** the application is starting, **When** a separate docs-enablement flag is not set, **Then** API documentation endpoints are disabled regardless of debug mode.
3. **Given** the application is starting, **When** a CORS origin value is malformed, **Then** the application refuses to start with a clear error message.
4. **Given** the application creates its database directory, **When** the directory and files are created, **Then** the directory has 0700 permissions and database files have 0600 permissions.

---

### User Story 10 — Supply Chain and Frontend Asset Safety (Priority: P4)

As a developer maintaining the CI/CD pipeline, I expect GitHub Actions workflows to use least-privilege permissions. As a user viewing issues, I expect avatar images to be validated against known safe domains.

**Why this priority**: These are low-severity findings with limited blast radius. Workflow permission tightening reduces supply-chain risk, and avatar URL validation is a defense-in-depth measure against injection via untrusted image sources.

**Independent Test**: Review the workflow YAML for minimal permission declarations. Render an issue card with a non-GitHub avatar URL and verify a placeholder image is displayed instead.

**Acceptance Scenarios**:

1. **Given** the branch-issue-link workflow, **When** its permissions are reviewed, **Then** it requests only the minimum permission needed with a justification comment.
2. **Given** an issue card displaying an avatar, **When** the avatar URL does not use HTTPS or does not originate from a known GitHub avatar domain, **Then** a placeholder image is rendered instead.

---

### Edge Cases

- What happens when an existing deployment has plaintext-encrypted OAuth tokens in the database and the encryption key enforcement is enabled? A migration path must exist to encrypt existing rows.
- What happens when a user who previously authorized with the broad `repo` scope attempts to use the application after scopes are narrowed? The user must be prompted to re-authorize.
- What happens when the rate limiter state store is unavailable? The system should fail open with a logged warning rather than blocking all requests.
- What happens when a legitimate user shares a NAT/VPN IP with an abusive user? Per-user rate limits (preferred over per-IP) prevent penalizing innocent users on shared networks.
- What happens when a webhook secret is rotated while requests are in flight? The system should accept signatures from both the old and new secret during a brief overlap window, or clearly document the need for a brief downtime.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST deliver session credentials via HttpOnly, SameSite=Strict, Secure cookies on the OAuth callback response, with no credentials in the redirect URL.
- **FR-002**: Frontend MUST NOT read session credentials from URL parameters.
- **FR-003**: System MUST refuse to start in non-debug mode if the encryption key is not set.
- **FR-004**: System MUST refuse to start in non-debug mode if the webhook secret is not set.
- **FR-005**: All containers MUST run as a dedicated non-root system user.

**Phase 2 — High**

- **FR-006**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action.
- **FR-007**: The project-ownership check MUST be centralized as a shared dependency to ensure consistent enforcement.
- **FR-008**: All secret and token comparisons MUST use constant-time comparison functions.
- **FR-009**: The frontend reverse proxy MUST send Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers on every response.
- **FR-010**: The frontend reverse proxy MUST NOT send the deprecated X-XSS-Protection header and MUST NOT reveal server software version information.
- **FR-011**: All credential inputs, including dev-mode endpoints, MUST be transmitted in the request body, never in the URL.
- **FR-012**: OAuth authorization MUST request only the minimum scopes necessary for the application's features.
- **FR-013**: System MUST reject session secret keys shorter than 64 characters at startup.
- **FR-014**: Development Docker services MUST bind to 127.0.0.1 only; production services MUST be exposed only via a reverse proxy.

**Phase 3 — Medium**

- **FR-015**: Write, AI, and workflow endpoints MUST enforce per-user rate limits; the OAuth callback MUST enforce per-IP rate limits.
- **FR-016**: System MUST refuse to start in non-debug mode if cookie Secure flag is not enabled.
- **FR-017**: Webhook signature verification MUST NOT be conditional on debug mode; developers MUST use a locally configured test secret.
- **FR-018**: API documentation endpoint availability MUST be controlled by a dedicated toggle independent of debug mode.
- **FR-019**: The database directory MUST be created with 0700 permissions and database files with 0600 permissions.
- **FR-020**: CORS origin configuration MUST be validated at startup; malformed URLs MUST cause startup failure.
- **FR-021**: Data volumes MUST be mounted outside the application root directory.
- **FR-022**: Chat history in browser local storage MUST contain only lightweight references (message IDs), not full message content, and MUST be cleared on logout.
- **FR-023**: Error responses originating from third-party API failures MUST contain only generic sanitized messages; full error details MUST be logged internally only.

**Phase 4 — Low**

- **FR-024**: CI/CD workflows MUST declare minimum necessary permissions with justification comments.
- **FR-025**: External avatar URLs MUST be validated to use HTTPS and originate from a known GitHub avatar domain; invalid URLs MUST fall back to a placeholder image.

### Key Entities

- **Session**: Represents an authenticated user's login state; delivered via secure cookie; associated with a user identity and project access permissions.
- **Project**: A user-owned resource; all access must be gated by ownership verification against the authenticated session.
- **OAuth Token**: A stored credential for GitHub API access; must be encrypted at rest; scoped to minimum necessary permissions.
- **Rate Limit State**: Per-user or per-IP counters tracking request frequency to sensitive endpoints; used to enforce throttling thresholds.
- **Chat Message Reference**: A lightweight identifier (message ID) stored in browser local storage with a TTL; full content loaded from backend on demand.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, no credentials appear in the browser URL bar, browser history, or server access logs — verified by inspecting all three locations post-login.
- **SC-002**: The backend refuses to start in non-debug mode when any mandatory secret (encryption key, webhook secret) is unset or when the session key is shorter than 64 characters — verified by attempting startup with each missing/short value.
- **SC-003**: Executing a shell inside the frontend container returns a non-root user ID — verified by running `id` inside the container.
- **SC-004**: An authenticated request targeting an unowned project returns 403 Forbidden — verified by cross-user project access attempts for all project-scoped endpoints.
- **SC-005**: A WebSocket connection attempt to an unowned project is rejected before any data is sent — verified by monitoring the connection lifecycle.
- **SC-006**: All webhook secret comparisons in the codebase use a constant-time function — verified by code review.
- **SC-007**: A HEAD request to the frontend returns Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers; the Server header reveals no software version — verified by inspecting response headers.
- **SC-008**: After exceeding the rate limit threshold, expensive endpoints return 429 Too Many Requests — verified by automated load testing against each rate-limited endpoint.
- **SC-009**: After logout, browser localStorage contains no chat message content — verified by inspecting localStorage in browser developer tools.
- **SC-010**: The database directory has 0700 permissions and database files have 0600 permissions — verified by inspecting filesystem permissions inside the container.

## Assumptions

- The application uses OAuth (GitHub) as its primary authentication mechanism; no other auth providers are in scope.
- The backend is built on a Python async framework compatible with middleware-based rate limiting.
- The frontend is a single-page application served by nginx as a reverse proxy.
- Docker and docker-compose are the standard deployment mechanism.
- Debug mode is controlled by a `DEBUG` environment variable.
- SQLite is the database engine; encryption refers to application-level encryption of sensitive fields, not full-disk encryption.
- GitHub API security, MCP server internals, and network-layer infrastructure are out of scope per the audit findings.
- For the OAuth scope narrowing (FR-012), a staging validation period is assumed before production rollout, and users will be prompted to re-authorize.
- For encryption enforcement (FR-003), a migration path for existing plaintext rows is required as part of the same change.
- Per-user rate limits are preferred over per-IP to avoid penalizing users behind shared NAT/VPN.

## Dependencies

- Existing OAuth flow implementation (auth.py, useAuth.ts, github_auth.py)
- Existing Docker and docker-compose deployment configuration
- Existing nginx reverse proxy configuration
- Existing webhook handling (webhooks.py, signal.py)
- Existing project/task/settings/workflow endpoint implementations
- Existing chat history local storage implementation (useChatHistory.ts)
- Existing GitHub GraphQL service layer (service.py)
- Existing CI/CD workflow configuration (branch-issue-link.yml)

## Risks

- **OAuth scope narrowing may break write operations**: Narrowing from `repo` to a smaller scope set could cause previously-working operations to fail. Mitigation: test all write operations in staging before production rollout.
- **Encryption enforcement is a breaking change**: Deployments without an encryption key will fail to start. Mitigation: include a migration path for existing plaintext data and document the upgrade procedure.
- **Rate limiting may impact legitimate high-volume users**: Aggressive rate limits could throttle power users. Mitigation: configure limits based on observed usage patterns; use per-user limits instead of per-IP.
- **CSP header may break existing frontend behavior**: A restrictive Content-Security-Policy could block legitimate inline scripts or external resources. Mitigation: audit the frontend for CSP compatibility before enforcing.
