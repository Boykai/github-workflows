# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `027-security-review`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Security, Privacy & Vulnerability Audit — 3 Critical, 8 High, 9 Medium, 2 Low findings across OWASP Top 10 categories"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Secure Authentication Flow (Priority: P1)

As a user logging in via OAuth, I need my session credentials to be delivered securely so that my tokens are never exposed in browser history, server logs, or HTTP referrer headers.

**Why this priority**: Credential leakage in the URL is the most immediately exploitable vulnerability. Any proxy, CDN, or browser extension can capture the session token today. Fixing this eliminates the single largest attack surface.

**Independent Test**: Can be fully tested by completing an OAuth login and verifying that no credentials appear in the browser address bar, browser history entries, or server access logs. The session cookie is present as HttpOnly and Secure.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth callback completes, **Then** the backend sets an HttpOnly, SameSite=Strict, Secure cookie and redirects the browser with no credentials in the URL.
2. **Given** a user completes login, **When** the browser URL bar and history are inspected, **Then** no session token or credential value appears in any URL.
3. **Given** the frontend application, **When** it handles the post-login redirect, **Then** it never reads credentials from URL query parameters.

---

### User Story 2 — Mandatory Encryption & Secrets at Startup (Priority: P1)

As an operator deploying the application, I need the system to refuse to start in production mode without required encryption keys and webhook secrets so that sensitive data is never stored unprotected.

**Why this priority**: Without enforced encryption, OAuth tokens are stored in plaintext and a database leak exposes all user credentials. This is a critical data-at-rest protection that gates all other security measures.

**Independent Test**: Can be fully tested by attempting to start the backend in non-debug mode without ENCRYPTION_KEY or GITHUB_WEBHOOK_SECRET set and verifying the application exits with a clear error message.

**Acceptance Scenarios**:

1. **Given** the application starts in non-debug mode, **When** ENCRYPTION_KEY is not set, **Then** the application refuses to start and outputs a clear error indicating the missing key.
2. **Given** the application starts in non-debug mode, **When** GITHUB_WEBHOOK_SECRET is not set, **Then** the application refuses to start and outputs a clear error.
3. **Given** the application starts in debug mode, **When** ENCRYPTION_KEY is not set, **Then** the application starts with a warning (development convenience preserved).
4. **Given** an existing deployment with plaintext data, **When** an encryption key is configured for the first time, **Then** a migration path encrypts existing plaintext rows.

---

### User Story 3 — Non-Root Container Execution (Priority: P1)

As an operator, I need all containers to run as non-root users so that a container breakout does not grant host-level root access.

**Why this priority**: Running as root in a container is a critical misconfiguration that amplifies the impact of any other vulnerability. This is a foundational security control.

**Independent Test**: Can be fully tested by running `docker exec` into the frontend container and verifying that `id` returns a non-root UID.

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** `id` is executed inside the container, **Then** the output shows a non-root UID (not uid=0).
2. **Given** the frontend container, **When** nginx serves requests, **Then** it operates correctly under the non-root user.

---

### User Story 4 — Project-Level Access Control (Priority: P2)

As a user, I need the system to verify I own or have access to a project before allowing any operation on it so that other users cannot view or modify my projects by guessing project IDs.

**Why this priority**: Broken access control (OWASP A01) allows any authenticated user to access any project. This is the highest-severity authorization flaw and affects multiple endpoints.

**Independent Test**: Can be fully tested by authenticating as User A, creating a project, then authenticating as User B and attempting to access User A's project by ID — expecting a 403 Forbidden response.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they request a project they do not own, **Then** the system returns 403 Forbidden.
2. **Given** an authenticated user, **When** they attempt to create a task on a project they do not own, **Then** the system returns 403 Forbidden.
3. **Given** an authenticated user, **When** they attempt a WebSocket subscription to a project they do not own, **Then** the connection is rejected before any data is sent.
4. **Given** any endpoint accepting a project identifier, **When** a request is received, **Then** ownership is verified via a centralized shared check before any action is performed.

---

### User Story 5 — Secure Secret Comparisons (Priority: P2)

As an operator, I need all secret and token comparisons in the system to use constant-time algorithms so that timing side-channel attacks cannot be used to guess webhook secrets.

**Why this priority**: The Signal webhook uses a standard string comparison that leaks timing information, while the GitHub webhook already uses constant-time comparison. Consistency across all secret comparisons eliminates this class of attack.

**Independent Test**: Can be verified via code review confirming all secret/token string comparisons use a constant-time comparison function.

**Acceptance Scenarios**:

1. **Given** the Signal webhook endpoint, **When** it verifies the incoming request secret, **Then** it uses a constant-time comparison function.
2. **Given** any code path that compares secrets or tokens, **When** reviewed, **Then** all comparisons use constant-time functions.

---

### User Story 6 — HTTP Security Headers (Priority: P2)

As a user accessing the application through a browser, I need the server to return modern security headers so that the browser enforces content policies, transport security, and referrer restrictions.

**Why this priority**: Missing security headers leave users vulnerable to cross-site scripting, clickjacking, and information leakage. These are defense-in-depth measures that protect every user session.

**Independent Test**: Can be fully tested by sending a HEAD request to the frontend and verifying the presence of Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy headers and the absence of the nginx version in the Server header.

**Acceptance Scenarios**:

1. **Given** a request to the frontend, **When** the response headers are inspected, **Then** Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers are present.
2. **Given** a request to the frontend, **When** the response headers are inspected, **Then** the deprecated X-XSS-Protection header is absent.
3. **Given** a request to the frontend, **When** the Server header is inspected, **Then** the nginx version number is not disclosed.

---

### User Story 7 — Secure Dev Login Endpoint (Priority: P2)

As a developer testing locally, I need the dev login endpoint to accept credentials only via POST request body so that tokens never appear in server logs or browser history.

**Why this priority**: Even development-only endpoints should follow secure credential handling patterns to prevent accidental exposure and to establish safe habits.

**Independent Test**: Can be fully tested by attempting to pass credentials as URL query parameters to the dev login endpoint and verifying the request is rejected, then confirming POST body delivery works.

**Acceptance Scenarios**:

1. **Given** the dev login endpoint, **When** a credential is passed as a URL query parameter, **Then** the request is rejected.
2. **Given** the dev login endpoint, **When** a credential is sent in the POST request body as JSON, **Then** authentication succeeds.

---

### User Story 8 — Minimum OAuth Scopes (Priority: P2)

As a user authorizing the application, I need it to request only the minimum necessary permissions so that my private repositories are not unnecessarily exposed.

**Why this priority**: The current `repo` scope grants full read/write access to all private repositories when only project management access is needed. Reducing scope minimizes the blast radius of a token compromise.

**Independent Test**: Can be fully tested by initiating an OAuth flow and verifying the requested scopes do not include `repo`, and then confirming all application write operations succeed with the narrower scopes.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth authorization, **When** the authorization URL is generated, **Then** it requests only the minimum scopes needed for project management.
2. **Given** narrower OAuth scopes are configured, **When** users perform all standard write operations, **Then** all operations succeed without errors.
3. **Given** existing users authorized with broader scopes, **When** the scope change is deployed, **Then** users are prompted to re-authorize with the new scopes.

---

### User Story 9 — Session Secret Key Entropy (Priority: P2)

As an operator, I need the system to reject weak session secret keys so that session tokens cannot be brute-forced.

**Why this priority**: A weak session secret key undermines all session security. Enforcing minimum entropy prevents deployment with insecure defaults.

**Independent Test**: Can be fully tested by attempting to start the application with a session secret key shorter than 64 characters and verifying the application rejects it.

**Acceptance Scenarios**:

1. **Given** startup configuration, **When** SESSION_SECRET_KEY is shorter than 64 characters, **Then** the application refuses to start with a clear error message.
2. **Given** startup configuration, **When** SESSION_SECRET_KEY is 64 or more characters, **Then** the application starts normally.

---

### User Story 10 — Localhost-Only Service Binding (Priority: P2)

As an operator, I need Docker services to bind only to the loopback interface in development so that backend and frontend ports are not exposed on all network interfaces.

**Why this priority**: Binding to 0.0.0.0 exposes services to the entire network, creating an unnecessary attack surface in development environments.

**Independent Test**: Can be fully tested by inspecting the Docker Compose configuration and verifying ports are bound to 127.0.0.1 in development and not directly exposed in production.

**Acceptance Scenarios**:

1. **Given** the development Docker Compose configuration, **When** services are started, **Then** ports are bound to 127.0.0.1 only.
2. **Given** the production deployment, **When** services are started, **Then** backend and frontend are not directly exposed via container ports but are accessed only through a reverse proxy.

---

### User Story 11 — Rate Limiting on Sensitive Endpoints (Priority: P3)

As a user, I need expensive and sensitive endpoints to enforce rate limits so that a single user or IP cannot exhaust shared resources or abuse the OAuth flow.

**Why this priority**: Without rate limiting, a single actor can exhaust AI/GitHub quotas or perform brute-force attacks on the OAuth callback. Per-user limits protect shared resources fairly.

**Independent Test**: Can be fully tested by sending requests above the rate limit threshold to a protected endpoint and verifying that subsequent requests receive a 429 Too Many Requests response.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they exceed the rate limit on a write or AI endpoint, **Then** the system returns 429 Too Many Requests.
2. **Given** an unauthenticated IP, **When** it exceeds the rate limit on the OAuth callback, **Then** the system returns 429 Too Many Requests.
3. **Given** rate limits are enforced, **When** a user behind shared NAT/VPN makes requests, **Then** per-user limits are applied rather than per-IP to avoid penalizing co-located users.

---

### User Story 12 — Secure Cookie Configuration in Production (Priority: P3)

As an operator, I need the system to enforce the Secure flag on cookies in production so that session cookies are never sent over unencrypted connections.

**Why this priority**: A missing Secure flag means cookies can be intercepted over HTTP. Enforcing this at startup eliminates silent misconfiguration.

**Independent Test**: Can be fully tested by starting the application in non-debug mode without Secure cookie configuration and verifying the application refuses to start.

**Acceptance Scenarios**:

1. **Given** non-debug mode startup, **When** cookies are not configured as Secure, **Then** the application refuses to start with a clear error.
2. **Given** non-debug mode startup, **When** cookies are configured as Secure, **Then** the application starts normally.

---

### User Story 13 — Unconditional Webhook Verification (Priority: P3)

As an operator, I need webhook signature verification to always be enforced regardless of debug mode so that an accidental debug-mode deployment cannot bypass authentication.

**Why this priority**: Conditional verification based on debug mode creates a path where production deployments accidentally skip authentication, allowing unauthenticated callers to trigger workflows.

**Independent Test**: Can be fully tested by running the application in debug mode with a webhook secret configured and sending a request with an invalid signature — expecting rejection.

**Acceptance Scenarios**:

1. **Given** the application runs in debug mode, **When** a webhook request arrives with an invalid signature, **Then** the request is rejected.
2. **Given** the application runs in any mode, **When** webhook signature verification is evaluated, **Then** verification is never skipped based on debug state.

---

### User Story 14 — Independent API Documentation Toggle (Priority: P3)

As an operator, I need API documentation visibility to be controlled by a dedicated setting, independent of debug mode, so that debug mode cannot accidentally expose the full API schema in production.

**Why this priority**: Coupling API docs to debug mode means any accidental debug-on deployment leaks the complete API surface. A separate toggle gives explicit control.

**Independent Test**: Can be fully tested by running the application with DEBUG enabled but API docs disabled and verifying that Swagger/ReDoc are not accessible.

**Acceptance Scenarios**:

1. **Given** the application runs with DEBUG=true and ENABLE_DOCS=false, **When** a user accesses the API documentation URL, **Then** a 404 response is returned.
2. **Given** the application runs with DEBUG=false and ENABLE_DOCS=true, **When** a user accesses the API documentation URL, **Then** the documentation is accessible.

---

### User Story 15 — Restrictive Database File Permissions (Priority: P3)

As an operator, I need the database directory and files to have restrictive permissions so that only the application user can read the database.

**Why this priority**: World-readable database files allow any process in the container to access sensitive data. Restricting permissions limits the impact of a compromised co-located process.

**Independent Test**: Can be fully tested by inspecting the database directory and file permissions after application startup and verifying 0700 for the directory and 0600 for the file.

**Acceptance Scenarios**:

1. **Given** the application creates the database directory, **When** permissions are inspected, **Then** the directory has 0700 permissions.
2. **Given** the application creates the database file, **When** permissions are inspected, **Then** the file has 0600 permissions.

---

### User Story 16 — CORS Origins Validation (Priority: P3)

As an operator, I need CORS origin values to be validated at startup so that typos and malformed entries do not silently create security holes.

**Why this priority**: Invalid CORS origins can silently allow unauthorized cross-origin requests. Validation at startup catches configuration errors before they reach production.

**Independent Test**: Can be fully tested by providing a malformed CORS origin value and verifying the application refuses to start with a clear error.

**Acceptance Scenarios**:

1. **Given** a CORS origins configuration, **When** an origin is missing a scheme or hostname, **Then** the application refuses to start with an error identifying the malformed value.
2. **Given** a CORS origins configuration, **When** all origins are well-formed URLs, **Then** the application starts normally.

---

### User Story 17 — Isolated Data Volume Mount (Priority: P3)

As an operator, I need runtime data volumes to be mounted outside the application directory so that runtime data and application code are not commingled.

**Why this priority**: Mounting data inside the application directory risks accidental data exposure through the web server and complicates container image management.

**Independent Test**: Can be fully tested by inspecting the Docker Compose volume mount paths and verifying data is mounted to a path outside the application root.

**Acceptance Scenarios**:

1. **Given** the Docker Compose configuration, **When** the data volume mount is inspected, **Then** it is mounted to a path outside the application root directory (e.g., /var/lib/ghchat/data).

---

### User Story 18 — Secure Client-Side Chat Storage (Priority: P3)

As a user, I need my chat history to not persist full message content in browser storage so that a cross-site scripting attack cannot exfiltrate my conversation history.

**Why this priority**: Full message content in localStorage is readable by any XSS vector, survives logout, and has no expiration. Storing only lightweight references and loading on demand limits the data exposed.

**Independent Test**: Can be fully tested by logging in, exchanging messages, logging out, and then inspecting localStorage to verify no message content remains.

**Acceptance Scenarios**:

1. **Given** a user exchanges chat messages, **When** localStorage is inspected, **Then** only lightweight references (message IDs) are stored, not full message content.
2. **Given** stored local references, **When** they are inspected, **Then** each entry has a time-to-live expiration.
3. **Given** a user logs out, **When** localStorage is inspected, **Then** all chat-related local data has been cleared.

---

### User Story 19 — Sanitized Error Messages (Priority: P3)

As a user, I need error messages returned from the system to contain only generic information so that internal system details, query structures, or token scopes are never leaked.

**Why this priority**: Exposing raw error messages from third-party APIs reveals internal architecture and can aid further attacks.

**Independent Test**: Can be fully tested by triggering an error condition and verifying the user-facing message is generic while the detailed error is logged internally.

**Acceptance Scenarios**:

1. **Given** a third-party API returns an error, **When** the error is propagated to the user, **Then** only a generic sanitized message is returned.
2. **Given** a third-party API returns an error, **When** the system processes it, **Then** the full error detail is logged internally for debugging.

---

### User Story 20 — Least-Privilege CI Workflow Permissions (Priority: P4)

As a repository maintainer, I need CI workflow permissions to follow the principle of least privilege so that a compromised workflow token cannot modify unrelated resources.

**Why this priority**: Overly broad workflow permissions increase supply-chain risk. Scoping to minimum needed reduces blast radius. Low severity as this requires a supply-chain attack vector.

**Independent Test**: Can be verified by reviewing the workflow file and confirming permissions are scoped to the minimum needed with justification comments.

**Acceptance Scenarios**:

1. **Given** the branch-issue-link workflow, **When** its permissions are reviewed, **Then** they are scoped to the minimum required (not broad `issues: write`).
2. **Given** the workflow file, **When** reviewed, **Then** each permission includes a justification comment.

---

### User Story 21 — Avatar URL Validation (Priority: P4)

As a user viewing project boards, I need avatar images to only load from validated sources so that a malicious avatar URL cannot be used for tracking or content injection.

**Why this priority**: Unvalidated external URLs in image tags can be exploited for user tracking or mixed-content injection. Low severity as it requires a compromised upstream API response.

**Independent Test**: Can be fully tested by rendering a component with a non-GitHub, non-HTTPS avatar URL and verifying a placeholder image is displayed instead.

**Acceptance Scenarios**:

1. **Given** an avatar URL from the API, **When** it uses HTTPS and originates from a known GitHub avatar domain, **Then** the image renders normally.
2. **Given** an avatar URL from the API, **When** it uses HTTP or originates from an unknown domain, **Then** a placeholder image is displayed instead.

---

### Edge Cases

- What happens when an operator upgrades from plaintext storage to encrypted storage? A migration path must handle re-encrypting existing rows without data loss.
- What happens when a user's OAuth scope is reduced? The user must be prompted to re-authorize, and the application must handle the interim state gracefully.
- What happens when rate limits are hit by legitimate burst activity? Rate limit responses must include Retry-After headers so clients can back off appropriately.
- What happens when the CORS origins environment variable contains trailing whitespace or empty entries? The validation must trim and ignore empty entries rather than treating them as malformed.
- What happens when the database directory already exists with incorrect permissions on application restart? The application must correct the permissions or refuse to start.
- What happens when a Content-Security-Policy header blocks a legitimate frontend resource? The CSP must be tuned to allow all application assets while blocking inline scripts and external resources.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST deliver session credentials via HttpOnly, SameSite=Strict, Secure cookies on the OAuth callback response, never via URL parameters.
- **FR-002**: Frontend MUST NOT read credentials from URL query parameters at any point in the authentication flow.
- **FR-003**: System MUST refuse to start in non-debug mode if ENCRYPTION_KEY is not set.
- **FR-004**: System MUST refuse to start in non-debug mode if GITHUB_WEBHOOK_SECRET is not set.
- **FR-005**: System MUST provide a migration path to encrypt existing plaintext data when ENCRYPTION_KEY is configured for the first time.
- **FR-006**: All containers MUST run as a dedicated non-root system user.

**Phase 2 — High**

- **FR-007**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action.
- **FR-008**: Project ownership verification MUST be implemented as a centralized, shared dependency used by all project-scoped endpoints.
- **FR-009**: WebSocket connections to project resources MUST verify project ownership before transmitting any data.
- **FR-010**: All secret and token comparisons MUST use constant-time comparison functions.
- **FR-011**: System MUST return Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers on all frontend responses.
- **FR-012**: System MUST NOT return the deprecated X-XSS-Protection header.
- **FR-013**: System MUST NOT disclose the web server version in the Server response header.
- **FR-014**: The dev login endpoint MUST accept credentials only via POST request body (JSON), never via URL query parameters.
- **FR-015**: OAuth authorization requests MUST use the minimum necessary scopes for project management operations.
- **FR-016**: System MUST reject SESSION_SECRET_KEY values shorter than 64 characters at startup.
- **FR-017**: Development Docker services MUST bind ports to 127.0.0.1 only, not 0.0.0.0.
- **FR-018**: Production deployments MUST NOT expose backend or frontend ports directly; services MUST be accessible only through a reverse proxy.

**Phase 3 — Medium**

- **FR-019**: System MUST enforce per-user rate limits on write and AI-powered endpoints.
- **FR-020**: System MUST enforce per-IP rate limits on the OAuth callback endpoint.
- **FR-021**: Rate limit responses MUST include appropriate Retry-After information.
- **FR-022**: System MUST refuse to start in non-debug mode if cookie Secure flag is not enabled.
- **FR-023**: Webhook signature verification MUST NOT be conditional on debug mode; it MUST always be enforced when a secret is configured.
- **FR-024**: API documentation visibility MUST be controlled by a dedicated ENABLE_DOCS setting, independent of DEBUG.
- **FR-025**: Database directory MUST be created with 0700 permissions and database files with 0600 permissions.
- **FR-026**: CORS origins MUST be validated at startup as well-formed URLs with scheme and hostname; malformed values MUST cause startup failure.
- **FR-027**: Data volumes MUST be mounted outside the application root directory.
- **FR-028**: Client-side storage MUST store only lightweight references (message IDs) with a time-to-live, not full message content.
- **FR-029**: All locally stored chat data MUST be cleared on user logout.
- **FR-030**: Error messages from third-party APIs MUST be sanitized before being returned to users; full error details MUST be logged internally.

**Phase 4 — Low**

- **FR-031**: CI workflow permissions MUST be scoped to the minimum necessary with justification comments for each permission.
- **FR-032**: Avatar URLs MUST be validated to use HTTPS and originate from known GitHub avatar domains; invalid URLs MUST fall back to a placeholder image.

### Key Entities

- **Session**: Represents an authenticated user session; attributes include user identity, expiration, and associated project access. Delivered via secure cookie, never via URL.
- **Project Ownership**: Relationship between a user and their projects; verified on every project-scoped operation. Centralized as a shared access-control check.
- **Rate Limit State**: Tracks request counts per user or per IP for protected endpoints; attributes include counter, window, and threshold.
- **Chat Reference**: Lightweight local storage entry containing only a message ID and TTL, replacing full message content storage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, zero credentials appear in browser URL bar, browser history, or server access logs.
- **SC-002**: Application refuses to start in non-debug mode without required encryption keys — 100% of startup attempts without keys fail with a clear error.
- **SC-003**: All running containers report non-root UID when inspected — 100% container compliance.
- **SC-004**: Authenticated requests to unowned project resources return 403 Forbidden — zero unauthorized data access across all project-scoped endpoints.
- **SC-005**: WebSocket connections to unowned project IDs are rejected before any data is transmitted.
- **SC-006**: 100% of secret/token comparisons in the codebase use constant-time functions, verified by code review.
- **SC-007**: Frontend responses include all required security headers (Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy) and do not disclose the server version.
- **SC-008**: Endpoints return 429 Too Many Requests when rate limits are exceeded — verified for both per-user and per-IP limits.
- **SC-009**: After logout, localStorage contains zero chat message content entries.
- **SC-010**: Database directory permissions are 0700 and file permissions are 0600 — verified on every application startup.
- **SC-011**: Application blocks startup when SESSION_SECRET_KEY is shorter than 64 characters — zero successful starts with weak keys.
- **SC-012**: All user-facing error messages from third-party API failures are generic — zero internal detail leakage in responses.

## Assumptions

- The application uses an OAuth-based authentication flow with GitHub as the identity provider.
- "Non-debug mode" refers to the production configuration where DEBUG is false or unset.
- The existing backend already runs as non-root; only the frontend container needs remediation.
- Per-user rate limiting is preferred over per-IP to accommodate users behind shared NAT/VPN.
- The migration path for encrypting existing plaintext data will be a one-time operation triggered on first startup with an encryption key present.
- Reducing OAuth scopes from `repo` to narrower scopes may require a staged rollout with testing in a staging environment. Users will need to re-authorize after the scope change.
- The CSP header will need to be tuned to the specific frontend assets and may require iteration to avoid breaking legitimate resources.
- "Known GitHub avatar domains" include `avatars.githubusercontent.com` and `github.com`.

## Dependencies

- Existing OAuth flow implementation (auth.py, useAuth.ts)
- Existing encryption module (encryption.py) and configuration (config.py)
- Frontend Dockerfile and nginx configuration
- Docker Compose service definitions
- Client-side chat storage hooks (useChatHistory.ts)
- CI workflow files (.github/workflows/branch-issue-link.yml)

## Out of Scope

- GitHub API security and rate limits (upstream, not within application control)
- MCP server internals
- Network-layer infrastructure (firewalls, load balancers, DNS)
- Penetration testing or dynamic application security testing (DAST)
- Third-party dependency vulnerability scanning (covered by separate tooling)
