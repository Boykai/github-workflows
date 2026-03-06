# Feature Specification: Security, Privacy & Vulnerability Audit

**Feature Branch**: `021-security-review`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Security, Privacy & Vulnerability Audit — 3 Critical · 8 High · 9 Medium · 2 Low across OWASP Top 10"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Credentials Never Exposed in Browser (Priority: P1)

As an application user, I want my authentication credentials to never appear in the browser URL bar, browser history, or server/proxy logs so that my account cannot be compromised through credential leakage.

**Why this priority**: Session tokens in URLs are the highest-severity finding (OWASP A02 Critical). Tokens in URLs are passively recorded by browsers, proxies, CDNs, and analytics tools — creating multiple attack vectors with no user action required. This is the single most impactful fix for user safety.

**Independent Test**: Complete an OAuth login flow and verify that at no point does any credential or token value appear in the browser address bar, browser history entries, or HTTP Referer headers sent to third parties.

**Acceptance Scenarios**:

1. **Given** a user initiates GitHub OAuth login, **When** the OAuth callback completes, **Then** the backend sets authentication via an HttpOnly, SameSite=Strict, Secure cookie and redirects the browser with no credentials in the URL.
2. **Given** a user has completed login, **When** the browser history is inspected, **Then** no entry contains a session token, access token, or any credential parameter.
3. **Given** a user is authenticated, **When** the browser navigates to an external link, **Then** the HTTP Referer header contains no credential information.
4. **Given** a developer uses the dev login endpoint, **When** they authenticate with a GitHub PAT, **Then** the PAT is sent in the POST request body (JSON), never as a URL query parameter.

---

### User Story 2 - Application Refuses to Start Without Required Security Configuration (Priority: P1)

As a deployment operator, I want the application to refuse to start in production mode when critical security configuration is missing so that the system never runs in an insecure state.

**Why this priority**: Encryption keys and webhook secrets being optional means production deployments can silently store sensitive data in plaintext or accept unverified webhook payloads. Mandatory startup checks prevent entire classes of misconfiguration.

**Independent Test**: Attempt to start the backend in non-debug mode without setting `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, or `SESSION_SECRET_KEY` (with fewer than 64 characters) and verify the application exits with a clear error message for each.

**Acceptance Scenarios**:

1. **Given** the application is started in non-debug mode, **When** `ENCRYPTION_KEY` is not set, **Then** the application refuses to start and displays a clear error message indicating the missing configuration.
2. **Given** the application is started in non-debug mode, **When** `GITHUB_WEBHOOK_SECRET` is not set, **Then** the application refuses to start with a clear error message.
3. **Given** the application is started in non-debug mode, **When** `SESSION_SECRET_KEY` is shorter than 64 characters, **Then** the application refuses to start with a clear error indicating the minimum length requirement.
4. **Given** the application is started in non-debug mode, **When** cookie Secure flag is not configured, **Then** the application refuses to start with a clear error.
5. **Given** the application is started in non-debug mode, **When** any CORS origin value is malformed (missing scheme or hostname), **Then** the application refuses to start with a clear error identifying the invalid origin.
6. **Given** the application is started in debug mode, **When** optional security configuration is missing, **Then** the application starts with visible warnings but does not block startup.

---

### User Story 3 - Project Resources Are Access-Controlled (Priority: P1)

As an authenticated user, I want project resources to be restricted to authorized users so that no other user can view, modify, or interact with my projects by guessing a project identifier.

**Why this priority**: Broken access control (OWASP A01) allows any authenticated user to access any project. This is a direct data breach vector affecting all users and all project data.

**Independent Test**: Authenticate as User A, create a project, then authenticate as User B and attempt to access User A's project by ID across all endpoint types (REST, WebSocket).

**Acceptance Scenarios**:

1. **Given** User A owns a project, **When** User B (who does not have access) sends a request using that project's ID to any endpoint (task creation, settings, workflow operations), **Then** the system returns a 403 Forbidden response.
2. **Given** User A owns a project, **When** User B attempts to subscribe to that project's WebSocket channel, **Then** the connection is rejected before any data is sent.
3. **Given** User A owns a project, **When** User A sends a request using their own project ID, **Then** the request succeeds normally.
4. **Given** a centralized authorization check exists, **When** any new endpoint is added that accepts a project identifier, **Then** the authorization check is applied automatically as a shared dependency.

---

### User Story 4 - Containers Run with Least Privilege (Priority: P2)

As a deployment operator, I want all containers to run as non-root users with restricted file permissions and network bindings so that a container compromise does not grant system-level access.

**Why this priority**: Running as root (OWASP A05 Critical) means any container escape or vulnerability exploitation grants full host-level access. Combined with overly permissive file permissions and open network bindings, this creates a large attack surface.

**Independent Test**: Start the application containers, exec into each one, and verify the process runs as a non-root user, database directories have 0700 permissions, database files have 0600 permissions, and services are bound to 127.0.0.1 (development) or only exposed via reverse proxy (production).

**Acceptance Scenarios**:

1. **Given** the frontend container is running, **When** `id` is executed inside it, **Then** it returns a non-root UID.
2. **Given** the backend container is running, **When** the database directory permissions are checked, **Then** the directory has 0700 permissions and database files have 0600 permissions.
3. **Given** the development Docker Compose configuration, **When** services are started, **Then** backend and frontend ports are bound to 127.0.0.1 only.
4. **Given** the production Docker Compose configuration, **When** services are started, **Then** services are not directly exposed via container ports but only through a reverse proxy.
5. **Given** the Docker Compose configuration, **When** data volumes are examined, **Then** data volumes are mounted outside the application root directory.

---

### User Story 5 - HTTP Security Headers Protect Against Common Attacks (Priority: P2)

As an application user, I want the web server to send proper security headers so that my browser enforces protections against cross-site scripting, clickjacking, and other common web attacks.

**Why this priority**: Missing security headers (OWASP A05 High) leave users vulnerable to well-known browser-based attacks. These headers are a low-effort, high-impact defense layer.

**Independent Test**: Send a HEAD request to the frontend and verify all required security headers are present and the nginx version is not disclosed.

**Acceptance Scenarios**:

1. **Given** a request is made to the frontend, **When** response headers are inspected, **Then** Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers are present.
2. **Given** a request is made to the frontend, **When** the Server response header is inspected, **Then** the nginx version number is not disclosed.
3. **Given** a request is made to the frontend, **When** response headers are inspected, **Then** the deprecated X-XSS-Protection header is not present.

---

### User Story 6 - Sensitive Endpoints Are Rate-Limited (Priority: P2)

As an application operator, I want expensive and sensitive endpoints to enforce rate limits so that a single user or attacker cannot exhaust shared resources (AI quotas, GitHub API limits) or brute-force authentication.

**Why this priority**: Without rate limiting (OWASP A04 Medium), a single user can consume all AI and GitHub API quotas, causing denial of service for all other users.

**Independent Test**: Send requests exceeding the rate limit threshold to chat, agent, workflow, and OAuth callback endpoints and verify 429 Too Many Requests responses.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they exceed the per-user rate limit on chat/agent/workflow endpoints, **Then** subsequent requests return 429 Too Many Requests until the rate window resets.
2. **Given** an unauthenticated IP address, **When** it exceeds the per-IP rate limit on the OAuth callback endpoint, **Then** subsequent requests return 429 Too Many Requests.
3. **Given** rate limits are enforced, **When** the rate window resets, **Then** the user/IP can resume making requests normally.

---

### User Story 7 - Webhook Verification Is Always Enforced (Priority: P2)

As an application operator, I want webhook signature verification to always be enforced regardless of debug mode so that attackers cannot trigger workflows by sending forged webhook payloads.

**Why this priority**: Debug mode bypassing verification (OWASP A05 Medium) means a single misconfiguration flag in production opens the application to unauthenticated workflow execution.

**Independent Test**: Enable debug mode, send a webhook request without a valid signature, and verify it is rejected.

**Acceptance Scenarios**:

1. **Given** the application is running in debug mode, **When** a webhook request arrives without a valid signature, **Then** the request is rejected with an appropriate error.
2. **Given** all secret/token comparisons in the codebase, **When** the comparison logic is reviewed, **Then** every comparison uses constant-time comparison functions.
3. **Given** a developer environment, **When** webhook testing is needed, **Then** developers configure a local test secret rather than bypassing verification.

---

### User Story 8 - Client-Side Data Is Minimized and Cleared on Logout (Priority: P3)

As an application user, I want my chat history and personal data to be cleared from the browser when I log out, and for only minimal references to be stored locally during my session, so that my private data is not exposed to subsequent users of the same browser or to XSS attacks.

**Why this priority**: Chat history in localStorage (OWASP A02 Medium) survives logout and is readable by any XSS. While lower severity than server-side issues, this is a direct privacy concern.

**Independent Test**: Log in, send chat messages, log out, then inspect localStorage and verify no message content remains.

**Acceptance Scenarios**:

1. **Given** a user is logged in, **When** chat history is examined in localStorage, **Then** only lightweight references (message IDs) are stored, not full message content.
2. **Given** a user logs out, **When** localStorage is inspected, **Then** no chat message content, session data, or personal information remains.
3. **Given** stored references in localStorage, **When** the user returns, **Then** full message content is loaded on demand from the backend, not from local storage.

---

### User Story 9 - OAuth Scope Is Minimally Permissive (Priority: P3)

As an application user, I want the application to request only the minimum necessary GitHub permissions so that I am not granting unnecessary access to my private repositories.

**Why this priority**: Overly broad OAuth scopes (OWASP A01 High) mean a compromised token grants full read/write access to all private repos. Reducing scope limits blast radius.

**Independent Test**: Initiate the OAuth flow and verify the requested scopes are the minimum required for the application's project management features.

**Acceptance Scenarios**:

1. **Given** a user initiates GitHub OAuth, **When** the authorization page is displayed, **Then** only minimum necessary scopes are requested (not the full `repo` scope).
2. **Given** the OAuth scopes have been narrowed, **When** all application write operations are tested, **Then** all operations succeed with the narrower scopes.
3. **Given** existing users authorized with broader scopes, **When** the scope change is deployed, **Then** users are prompted to re-authorize with the new scopes.

---

### User Story 10 - Internal Error Details Are Not Exposed to Users (Priority: P3)

As an application user, I want error messages to be user-friendly and not reveal internal system details so that attackers cannot use error responses to learn about the system's internals.

**Why this priority**: GraphQL error exposure (OWASP A09 Medium) leaks query structure and token scope details. Combined with other issues, this provides attackers with reconnaissance information.

**Independent Test**: Trigger a GitHub API error and verify the response contains a generic user-friendly message, not raw internal error details.

**Acceptance Scenarios**:

1. **Given** a GitHub GraphQL API call fails, **When** the error propagates to the API response, **Then** only a generic sanitized message is returned to the user.
2. **Given** a GitHub GraphQL API call fails, **When** the error is handled internally, **Then** the full error details are logged for debugging purposes.
3. **Given** any API endpoint encounters an internal error, **When** the response is sent to the user, **Then** no stack traces, query structures, or token details are included.

---

### User Story 11 - API Documentation Is Independently Controlled (Priority: P3)

As a deployment operator, I want API documentation visibility to be controlled by a dedicated setting, independent of debug mode, so that debug mode in production does not accidentally expose the full API schema.

**Why this priority**: Tying API docs to debug mode (OWASP A05 Medium) means any production debugging session exposes the full API surface to potential attackers.

**Independent Test**: Enable debug mode without the docs toggle and verify Swagger/ReDoc is not accessible. Then enable the docs toggle without debug mode and verify it is accessible.

**Acceptance Scenarios**:

1. **Given** `DEBUG=true` and `ENABLE_DOCS` is not set, **When** Swagger/ReDoc endpoints are accessed, **Then** they return 404 Not Found.
2. **Given** `ENABLE_DOCS=true` regardless of debug mode, **When** Swagger/ReDoc endpoints are accessed, **Then** API documentation is available.

---

### User Story 12 - Avatar URLs Are Validated Before Rendering (Priority: P3)

As an application user, I want external avatar images to be validated before rendering so that malicious image URLs cannot be used for tracking or injection attacks.

**Why this priority**: While low severity (OWASP A03 Low), unvalidated external URLs in image tags can be used for user tracking or as part of larger attack chains.

**Independent Test**: Render an issue card with a non-GitHub avatar URL and verify a placeholder image is shown instead.

**Acceptance Scenarios**:

1. **Given** an issue card displays an avatar, **When** the URL uses HTTPS and originates from a known GitHub avatar domain, **Then** the avatar image is rendered normally.
2. **Given** an issue card displays an avatar, **When** the URL does not use HTTPS or does not originate from a known GitHub domain, **Then** a placeholder image is displayed instead.

---

### User Story 13 - GitHub Actions Workflow Permissions Are Minimal (Priority: P3)

As a repository maintainer, I want GitHub Actions workflow permissions to be scoped to the minimum necessary so that a compromised or malicious workflow cannot make unauthorized changes.

**Why this priority**: Broad workflow permissions (Supply Chain, Low) increase the potential damage from supply chain attacks, though the immediate risk is low.

**Independent Test**: Review the workflow YAML file and verify permissions are scoped to the minimum needed with justification comments.

**Acceptance Scenarios**:

1. **Given** the branch-issue-link workflow, **When** its permissions are reviewed, **Then** it requests only the minimum permission needed, with a justification comment explaining why.

---

### Edge Cases

- What happens when an existing deployment has plaintext-encrypted data and the encryption enforcement is enabled? A migration path must exist to re-encrypt existing plaintext rows before enforcement takes effect.
- What happens when OAuth scope is narrowed and existing users have tokens with broader scopes? Users must be prompted to re-authorize; existing operations must not silently fail.
- What happens when a CORS origin contains a valid URL with a trailing slash or port number? The validator must handle common URL variations correctly.
- What happens when the rate limit is reached exactly at a request boundary? The system must clearly communicate the reset time to the client.
- What happens when a developer sets DEBUG=true in production? All security controls (webhook verification, encryption enforcement, secure cookies) must remain active regardless of debug mode.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Critical**

- **FR-001**: System MUST set authentication tokens via HttpOnly, SameSite=Strict, Secure cookies on the OAuth callback response and redirect with no credentials in the URL.
- **FR-002**: Frontend MUST NOT read authentication credentials from URL parameters.
- **FR-003**: System MUST refuse to start in non-debug mode if `ENCRYPTION_KEY` environment variable is not set.
- **FR-004**: System MUST refuse to start in non-debug mode if `GITHUB_WEBHOOK_SECRET` environment variable is not set.
- **FR-005**: All containers MUST run as a dedicated non-root system user.

**Phase 2 — High**

- **FR-006**: Every endpoint accepting a project identifier MUST verify the authenticated user has access to that project before performing any action.
- **FR-007**: Project authorization MUST be implemented as a centralized shared dependency, not duplicated per endpoint.
- **FR-008**: All secret and token comparisons MUST use constant-time comparison functions.
- **FR-009**: The web server MUST include Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy response headers.
- **FR-010**: The web server MUST NOT include the deprecated X-XSS-Protection header.
- **FR-011**: The web server MUST NOT disclose its software version in response headers.
- **FR-012**: All credential inputs, including dev-only endpoints, MUST be transmitted in the POST request body, never in URL parameters.
- **FR-013**: OAuth authorization MUST request only the minimum necessary scopes for the application's functionality.
- **FR-014**: System MUST reject `SESSION_SECRET_KEY` values shorter than 64 characters on startup.
- **FR-015**: Development Docker services MUST bind to 127.0.0.1 only; production services MUST NOT be directly exposed via container ports.

**Phase 3 — Medium**

- **FR-016**: Chat, agent invocation, workflow, and OAuth callback endpoints MUST enforce rate limits (per-user for authenticated endpoints, per-IP for OAuth callback).
- **FR-017**: Rate-limited endpoints MUST return 429 Too Many Requests when limits are exceeded.
- **FR-018**: System MUST refuse to start in non-debug mode if cookie Secure flag is not configured.
- **FR-019**: Webhook signature verification MUST NOT be conditional on debug mode.
- **FR-020**: API documentation availability MUST be controlled by a dedicated `ENABLE_DOCS` environment variable, independent of `DEBUG`.
- **FR-021**: Database directory MUST be created with 0700 permissions; database files MUST be created with 0600 permissions.
- **FR-022**: CORS origins configuration MUST be validated on startup; malformed URLs MUST cause startup failure.
- **FR-023**: Data volumes MUST be mounted outside the application root directory.
- **FR-024**: Client-side storage MUST contain only lightweight references (message IDs) with a TTL, not full message content.
- **FR-025**: All local data MUST be cleared on user logout.
- **FR-026**: GraphQL error messages MUST be sanitized before being returned in API responses; full error details MUST be logged internally.

**Phase 4 — Low**

- **FR-027**: GitHub Actions workflow permissions MUST be scoped to the minimum necessary with justification comments.
- **FR-028**: Avatar URLs MUST be validated to ensure HTTPS protocol and a known GitHub avatar domain before rendering; invalid URLs MUST fall back to a placeholder image.

### Key Entities

- **Session**: Represents an authenticated user session; key attributes include user identity, associated project access rights, expiration time, and the HttpOnly cookie binding.
- **Project Authorization**: Represents the access relationship between a user and a project; checked on every project-scoped request.
- **Rate Limit Bucket**: Represents the request quota for a user (per-user) or IP address (per-IP); tracks request count within a sliding time window.
- **Security Configuration**: Represents the set of mandatory environment variables and their validation rules that must pass before application startup.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After login, no credentials appear in the browser URL bar, browser history, or server access logs — verified by inspecting browser state and log files after a complete login flow.
- **SC-002**: Application refuses to start in non-debug mode within 5 seconds when any mandatory security configuration is missing, displaying a clear error message identifying the missing value.
- **SC-003**: Executing `id` inside the frontend container returns a non-root UID (not uid=0).
- **SC-004**: An authenticated request with an unowned project ID returns 403 Forbidden, not a success response, across 100% of project-scoped endpoints.
- **SC-005**: A WebSocket connection attempt to an unowned project ID is rejected before any project data is transmitted.
- **SC-006**: 100% of secret/token comparisons in the codebase use constant-time comparison functions, verified by code review.
- **SC-007**: A HEAD request to the frontend returns Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy headers; the Server header contains no version number.
- **SC-008**: After exceeding the rate limit threshold, expensive endpoints return 429 Too Many Requests within 1 second.
- **SC-009**: After logout, browser localStorage contains no message content — verified via browser developer tools inspection.
- **SC-010**: Database directory permissions are 0700 and database file permissions are 0600 — verified by file system inspection inside the container.
- **SC-011**: OAuth authorization requests only the minimum necessary scopes — verified by inspecting the authorization URL parameters.
- **SC-012**: All 21 audit findings are addressed and pass their corresponding verification checks.

## Assumptions

- The application uses a Python-based backend framework and nginx as the frontend reverse proxy, based on existing codebase structure.
- "Non-debug mode" refers to when the `DEBUG` environment variable is not set to `true`.
- The existing GitHub OAuth flow can be modified to use cookie-based token delivery without breaking the overall authentication architecture.
- Per-user rate limits are preferred over per-IP limits for authenticated endpoints to avoid penalizing users behind shared NAT/VPN connections.
- Existing plaintext-encrypted data rows will need a migration path when encryption enforcement is enabled — this migration must be part of the same change.
- Narrowing OAuth scopes may require existing users to re-authorize; this is an expected and acceptable user-facing change that should be communicated.
- The known GitHub avatar domains are `avatars.githubusercontent.com` and `github.com`.
- The `ENABLE_DOCS` environment variable defaults to `false` (docs disabled) when not set.
- Rate limit thresholds will be tuned based on observed usage patterns; initial values should be conservative and configurable.
- The data volume mount path change (to outside the application root) is a breaking change for existing deployments and requires migration documentation.

## Dependencies

- **Encryption Migration**: Enforcing encryption at rest (FR-003, FR-004) requires a data migration strategy for existing plaintext rows before it can be safely deployed.
- **OAuth Scope Testing**: Narrowing OAuth scopes (FR-013) requires staging environment testing to confirm all write operations work with reduced permissions before production deployment.
- **User Re-authorization**: After OAuth scope changes, existing users must re-authorize, requiring a user communication plan.
- **Rate Limiting Library**: Adding rate limiting (FR-016, FR-017) requires integration of a rate limiting library compatible with the application framework.

## Out of Scope

- GitHub API internal security mechanisms
- MCP server internals
- Network-layer infrastructure (firewalls, load balancers, DNS)
- Third-party dependency vulnerability scanning (covered by separate tooling)
- Penetration testing execution (this spec covers remediation of known findings only)
