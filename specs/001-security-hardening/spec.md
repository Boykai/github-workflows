# Feature Specification: Phase 4 — Security Hardening

**Feature Branch**: `001-security-hardening`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Phase 4: Security Hardening — Make Encryption Mandatory, Session Revocation API, Webhook Deduplication Cache, OAuth Scope Validation, CSRF SameSite=Strict"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Mandatory Encryption for Stored Tokens (Priority: P1)

As a system administrator, I need all stored tokens to be encrypted at rest so that a missing or misconfigured encryption key causes the application to fail fast rather than silently storing tokens in plaintext.

**Why this priority**: Encryption is the foundational security guarantee. Without it, every other security measure is undermined — session tokens, OAuth tokens, and webhook secrets stored in plaintext are a critical data-breach risk. Failing loudly on a missing key prevents the most dangerous misconfiguration.

**Independent Test**: Can be fully tested by removing the encryption key from the environment and verifying the application refuses to start, then restoring it and confirming tokens are stored encrypted and retrievable.

**Acceptance Scenarios**:

1. **Given** the application is starting up, **When** the encryption key environment variable is absent or empty, **Then** the application MUST refuse to start and log a clear error message indicating that the encryption key is required.
2. **Given** a valid encryption key is configured, **When** a token is stored, **Then** the stored value MUST be encrypted and not readable as plaintext in the data store.
3. **Given** a valid encryption key is configured, **When** a previously stored encrypted token is retrieved, **Then** it MUST be decrypted and returned in its original form.
4. **Given** a valid encryption key is configured, **When** an administrator inspects the data store directly, **Then** no token values are visible in plaintext.

---

### User Story 2 — Session Revocation (Priority: P1)

As a user or administrator, I need the ability to immediately invalidate active sessions so that compromised or stale sessions cannot be used after revocation.

**Why this priority**: Session revocation is a critical security control — without it, a compromised token remains valid until natural expiry. This is a compliance requirement for most security frameworks and essential for incident response.

**Independent Test**: Can be fully tested by creating a session, using it successfully, revoking it, and then verifying that subsequent requests with the revoked session are rejected.

**Acceptance Scenarios**:

1. **Given** a user has an active session, **When** the user requests session revocation, **Then** the session MUST be immediately invalidated and subsequent requests using that session MUST be rejected.
2. **Given** an administrator has access to session management, **When** the administrator revokes a specific user's session, **Then** that session MUST be immediately invalidated.
3. **Given** a user has multiple active sessions, **When** the user revokes all sessions, **Then** all of that user's sessions MUST be invalidated simultaneously.
4. **Given** a session has been revoked, **When** a request is made using the revoked session credential, **Then** the system MUST return an appropriate unauthorized response within 1 second of the revocation taking effect.

---

### User Story 3 — OAuth Scope Validation at Login (Priority: P2)

As a user logging in via OAuth, I need the system to verify that all required permissions (scopes) are granted at the time of login so that I receive a clear, actionable error immediately rather than encountering cryptic failures later when the application attempts restricted operations.

**Why this priority**: Missing scopes cause confusing errors deep in application workflows. Validating upfront prevents wasted user time, reduces support burden, and ensures the application has the permissions it needs before proceeding.

**Independent Test**: Can be fully tested by initiating an OAuth login with insufficient scopes and verifying a clear error is shown, then logging in with all required scopes and verifying success.

**Acceptance Scenarios**:

1. **Given** a user initiates OAuth login, **When** the OAuth provider grants fewer scopes than the application requires, **Then** the system MUST display a clear message identifying which specific scopes are missing and how to grant them.
2. **Given** a user initiates OAuth login, **When** all required scopes are granted, **Then** login proceeds normally with no scope-related warnings.
3. **Given** the application's required scopes change (e.g., new feature added), **When** an existing user logs in again, **Then** the system MUST detect missing scopes from the new requirements and prompt the user to re-authorize.

---

### User Story 4 — Webhook Deduplication (Priority: P2)

As a system processing incoming webhooks, I need duplicate webhook deliveries to be detected and ignored so that the same event is not processed more than once within a defined time window.

**Why this priority**: Webhook providers frequently retry deliveries, and network issues can cause duplicates. Processing the same event twice can lead to data corruption, duplicate notifications, or incorrect state transitions. This is especially important for financial or state-changing operations.

**Independent Test**: Can be fully tested by sending the same webhook delivery ID twice within the deduplication window and verifying only the first is processed, then sending it again after the window expires and verifying it is processed.

**Acceptance Scenarios**:

1. **Given** a webhook delivery arrives, **When** the same delivery ID has been received within the last 60 minutes, **Then** the system MUST skip processing and return a success response (to prevent the sender from retrying).
2. **Given** a webhook delivery arrives, **When** the delivery ID has not been seen within the last 60 minutes, **Then** the system MUST process the event normally.
3. **Given** a webhook delivery was received 61 or more minutes ago, **When** the same delivery ID arrives again, **Then** the system MUST process it as a new event (the deduplication window has expired).
4. **Given** multiple webhook deliveries arrive simultaneously with different delivery IDs, **When** all are new, **Then** each MUST be processed independently without interference.

---

### User Story 5 — CSRF Protection Upgrade to SameSite=Strict (Priority: P3)

As a user of the application, I need cookies to use the strictest cross-site protections available so that cross-site request forgery attacks are mitigated even in edge cases not covered by SameSite=Lax.

**Why this priority**: Upgrading from Lax to Strict closes specific attack vectors involving top-level navigations from external sites. While Lax covers most CSRF scenarios, Strict provides defense-in-depth. This is a lower-risk change but strengthens the overall security posture.

**Independent Test**: Can be fully tested by verifying that session cookies are set with SameSite=Strict, and that cross-origin requests do not include the session cookie even on top-level navigations from external sites.

**Acceptance Scenarios**:

1. **Given** a user logs in, **When** a session cookie is set, **Then** the cookie MUST include the SameSite=Strict attribute.
2. **Given** a user is authenticated, **When** the user navigates to the application from a same-site page, **Then** the session cookie MUST be sent and the user remains authenticated.
3. **Given** a user is authenticated, **When** a cross-origin site initiates a top-level navigation to the application, **Then** the session cookie MUST NOT be sent with the initial request, requiring the user to re-authenticate or refresh.
4. **Given** the SameSite=Strict policy is in effect, **When** a user accesses the application through a bookmark or directly typed URL, **Then** the session cookie MUST be sent normally and the user remains authenticated.

---

### Edge Cases

- What happens when the encryption key is rotated? The system must support key rotation by allowing a primary key and a list of previous keys for decryption of legacy-encrypted tokens.
- What happens when a session is revoked while a long-running request is in progress? The request should complete, but any subsequent request must be rejected.
- What happens when the deduplication cache storage is full or unavailable? The system should log a warning and process the event (fail open for availability, but log for monitoring). Alternatively, the system may reject the event with a retryable error code.
- What happens if a webhook arrives with no delivery ID? The system should process it normally (no deduplication possible) and log a warning.
- What happens if a user's OAuth token is valid but scopes have been revoked externally after login? The system should handle scope-related API errors gracefully and prompt re-authorization rather than showing cryptic errors.
- What happens when SameSite=Strict blocks a legitimate cross-site flow (e.g., email link to authenticated page)? The user should see the login page rather than an error, and after authenticating, be redirected to the intended destination.

## Requirements *(mandatory)*

### Functional Requirements

**Mandatory Encryption (4.1)**

- **FR-001**: System MUST require an encryption key at startup and refuse to start without one, logging a descriptive error.
- **FR-002**: System MUST encrypt all token values before persisting them to the data store.
- **FR-003**: System MUST decrypt stored tokens transparently when they are retrieved for use.
- **FR-004**: System MUST support encryption key rotation — decrypting with previous keys while encrypting with the current key.
- **FR-005**: System MUST NOT log or expose plaintext token values in any output (logs, error messages, API responses).

**Session Revocation (4.2)**

- **FR-006**: System MUST provide a mechanism for users to revoke their own active sessions.
- **FR-007**: System MUST provide a mechanism for administrators to revoke any user's sessions.
- **FR-008**: System MUST support revoking all sessions for a given user in a single operation.
- **FR-009**: System MUST reject requests using revoked session credentials immediately (within 1 second of revocation).
- **FR-010**: System MUST return an appropriate unauthorized response when a revoked session is used.

**Webhook Deduplication (4.3)**

- **FR-011**: System MUST maintain a cache of recently processed webhook delivery IDs.
- **FR-012**: System MUST skip processing for webhook deliveries whose ID has been seen within the last 60 minutes.
- **FR-013**: System MUST return a success response for deduplicated (skipped) webhook deliveries to prevent sender retries.
- **FR-014**: System MUST expire cached delivery IDs after 60 minutes.
- **FR-015**: System MUST process webhook deliveries with no delivery ID normally and log a warning.

**OAuth Scope Validation (4.5)**

- **FR-016**: System MUST define and maintain a list of required OAuth scopes.
- **FR-017**: System MUST compare granted scopes against required scopes immediately after OAuth authorization completes.
- **FR-018**: System MUST display a clear, user-friendly message listing missing scopes when scope validation fails.
- **FR-019**: System MUST provide a way for users to re-authorize with updated scopes.
- **FR-020**: System MUST handle scope-related API errors gracefully at runtime, prompting re-authorization instead of showing raw error messages.

**CSRF SameSite=Strict (4.7)**

- **FR-021**: System MUST set the SameSite=Strict attribute on all session cookies.
- **FR-022**: System MUST preserve user-intended destinations when SameSite=Strict causes a re-authentication (redirect after login to the originally requested page).

### Key Entities

- **Encryption Key**: The secret key used for encrypting and decrypting stored tokens. Must be present at startup. Supports rotation via a primary key and optional list of previous keys.
- **Session**: Represents an authenticated user session. Has attributes including session identifier, user reference, creation time, and revocation status.
- **Revocation Record**: Represents a revoked session. Tracks which session was revoked, when, and by whom (user self-revocation or administrator).
- **Webhook Delivery**: An incoming webhook event. Identified by a unique delivery ID provided by the sender. Has attributes including delivery ID, timestamp, and processing status.
- **Deduplication Cache Entry**: A record of a processed delivery ID with an expiration time (60 minutes from first receipt).
- **OAuth Scope Set**: The collection of permissions (scopes) required by the application and the set granted by the OAuth provider for a given user. Used for comparison at login and at runtime.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application startup fails within 5 seconds with a clear error message when no encryption key is configured — 100% of the time.
- **SC-002**: Zero tokens are stored in plaintext in the data store after this feature is deployed.
- **SC-003**: Users can revoke an active session and have it take effect within 1 second.
- **SC-004**: Duplicate webhook deliveries (same delivery ID within 60 minutes) are processed zero times after the first.
- **SC-005**: Users who log in via OAuth with insufficient scopes see a clear, actionable error message identifying missing scopes — 100% of the time.
- **SC-006**: Support tickets related to cryptic scope-related API failures decrease by 80% within 30 days of deployment.
- **SC-007**: All session cookies include SameSite=Strict attribute — verifiable by inspecting response headers.
- **SC-008**: Encryption key rotation completes without any user-facing downtime or data loss.

## Assumptions

- The application already has an authentication and session management system in place.
- The data store supports atomic read-write operations needed for session revocation checks.
- Webhook senders include a unique delivery ID header (e.g., `X-GitHub-Delivery` for GitHub webhooks). Webhooks without delivery IDs are processed without deduplication.
- The OAuth provider supports scope inspection (i.e., the granted scopes are available after authorization).
- The application primarily serves same-site requests; cross-site top-level navigations (e.g., from external links) will require the user to re-authenticate once per session due to SameSite=Strict.
- The deduplication cache storage mechanism (in-memory, external cache, etc.) will be determined during implementation planning. The spec defines behavior, not mechanism.
- Standard web application performance expectations apply unless otherwise specified (page loads under 3 seconds, API responses under 1 second).
