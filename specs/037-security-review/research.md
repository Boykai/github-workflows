# Research: Security, Privacy & Vulnerability Audit

**Feature**: 037-security-review | **Date**: 2026-03-12

## R1: Cookie-Based Session Delivery — Replacing URL Token Parameter

**Decision**: Replace the `?session_token=...` URL redirect with an `HttpOnly; SameSite=Strict; Secure` cookie set directly on the OAuth callback response. The backend redirects to the frontend with no credentials in the URL. The frontend reads session state from a `/me` or `/session` endpoint using the cookie, never from URL parameters.

**Rationale**: Session tokens in URLs are recorded in browser history, server/proxy/CDN access logs, and HTTP `Referer` headers (OWASP A02). The cookie approach is the industry standard for browser-based OAuth flows — the backend is the only party that sets and reads the credential. `HttpOnly` prevents JavaScript access (XSS mitigation), `SameSite=Strict` prevents CSRF, and `Secure` ensures HTTPS-only transmission.

**Alternatives considered**:
- Short-lived authorization code exchanged for a cookie via a POST request (rejected: adds an extra round-trip and complexity; the backend already controls the callback)
- `sessionStorage` with a one-time redirect token (rejected: still exposes the token in the URL during the redirect)
- Token in `Authorization` header managed by frontend (rejected: requires JavaScript access to the token, negating `HttpOnly` protection)

## R2: Mandatory Startup Validation — Encryption Key, Webhook Secret, Session Key, Cookie Secure

**Decision**: Consolidate all mandatory secret/configuration validation into `config.py` initialization. In non-debug mode, the application raises `SystemExit` if: (1) `ENCRYPTION_KEY` is unset, (2) `GITHUB_WEBHOOK_SECRET` is unset, (3) `SESSION_SECRET_KEY` is fewer than 64 characters, or (4) `cookie_secure` is `False`. In debug mode, only the session key length check applies (secrets may be optional for local development).

**Rationale**: Failing loudly at startup prevents silent misconfigurations that are far harder to detect after deployment. The 64-character minimum for session keys provides ~256 bits of entropy (assuming base64 or hex encoding), exceeding OWASP recommendations. Consolidating checks in `config.py` follows the existing pattern where settings are validated on construction.

**Alternatives considered**:
- Runtime checks on first use (rejected: delays error detection, may go unnoticed in low-traffic deployments)
- Environment variable validation via a separate pre-flight script (rejected: adds deployment complexity, can be bypassed)
- Warning-only mode (rejected: the audit explicitly requires refusal to start, not just logging)

## R3: Non-Root Container Execution — Frontend Dockerfile

**Decision**: Add a `USER` directive to the frontend Dockerfile creating a dedicated `nginx` system user (UID 101, already exists in the official nginx image). Configure nginx to write to `/tmp` for temporary files and adjust log paths. The backend already runs non-root.

**Rationale**: Running as root inside a container means any container escape or code execution vulnerability gives the attacker root privileges on the host (in default Docker configurations). The official `nginx` Docker image includes a pre-created `nginx` user (UID 101), so no additional user creation is needed — just switching to it and ensuring writable paths.

**Alternatives considered**:
- Using a distroless or scratch-based image (rejected: more complex, loses shell access for debugging)
- Running nginx as an arbitrary non-root UID without a named user (rejected: complicates file permission management)
- Using `--user` flag in docker-compose instead of Dockerfile (rejected: not self-documenting, easy to forget)

## R4: Centralized Project Ownership Verification

**Decision**: Implement a FastAPI dependency (`verify_project_ownership`) that takes the current session and `project_id` parameter, queries the database for project ownership, and raises `HTTPException(403)` if the user does not own the project. Inject this dependency into all project-scoped endpoints (tasks, projects, settings, workflow). For WebSocket connections, perform the same check during the connection handshake before accepting the upgrade.

**Rationale**: Centralizing the check as a single dependency (DRY principle) ensures consistent enforcement across all endpoints. A forgotten check on one endpoint is immediately visible during code review because the dependency injection is absent. The 403 response code is correct for authorization failures (as opposed to 401 for authentication failures).

**Alternatives considered**:
- Middleware-based check (rejected: middleware runs on every request, not just project-scoped ones; requires path matching)
- Decorator pattern (rejected: less visible than dependency injection in FastAPI; harder to enforce)
- Per-endpoint inline check (rejected: violates DRY, easy to forget on new endpoints)

## R5: Constant-Time Secret Comparison

**Decision**: Replace all `!=` / `==` string comparisons for secrets with `hmac.compare_digest()` from Python's standard library. This applies to the Signal webhook secret comparison in `signal.py` and any other secret comparisons found during implementation.

**Rationale**: Standard string equality comparison short-circuits on the first differing byte, leaking timing information that can be used to reconstruct the secret one byte at a time. `hmac.compare_digest()` runs in constant time regardless of where strings differ. The GitHub webhook handler already uses this correctly.

**Alternatives considered**:
- `secrets.compare_digest()` (rejected: does not exist in the Python standard library; `hmac.compare_digest` is the canonical choice)
- Double-HMAC comparison (rejected: over-engineering; `hmac.compare_digest` is sufficient for direct comparison)
- Switching to HMAC-based signature verification like the GitHub webhook (rejected: would require coordinating signature generation with the Signal bridge; direct secret comparison with constant-time is sufficient)

## R6: Nginx Security Headers Configuration

**Decision**: Add the following headers to `nginx.conf`: `Content-Security-Policy` (restrictive default-src with necessary exceptions for the SPA), `Strict-Transport-Security` (max-age=31536000; includeSubDomains), `Referrer-Policy` (strict-origin-when-cross-origin), `Permissions-Policy` (deny all sensitive features not used by the app). Remove `X-XSS-Protection` (deprecated, can cause issues in modern browsers). Add `server_tokens off` to hide the nginx version.

**Rationale**: These headers are defense-in-depth measures recommended by OWASP. CSP prevents XSS by controlling allowed script sources. HSTS prevents protocol downgrade attacks. Referrer-Policy limits information leakage. Permissions-Policy disables APIs the app doesn't need. The CSP policy must be tested against the existing frontend to avoid breaking legitimate functionality (inline styles from UI libraries, WebSocket connections, etc.).

**Alternatives considered**:
- CSP in report-only mode first (preferred as a migration step: deploy with `Content-Security-Policy-Report-Only` first, then enforce after verifying no violations)
- Helmet.js middleware in the backend (rejected: nginx is the correct place for static header injection; the backend API may need different CSP rules)
- Per-route header configuration (rejected: over-engineering; a single set of headers covers the SPA)

## R7: OAuth Scope Minimization

**Decision**: Replace the `repo` scope with the minimum set needed for the application's features. Based on the application's use of GitHub Projects, Issues, and repository metadata, the recommended scopes are: `read:user` (user profile), `repo:status` (commit status), `public_repo` (public repository access), and `project` (project board access). If write operations require more access, `repo` can be narrowed to specific sub-scopes. Existing users must re-authorize after the scope change.

**Rationale**: The `repo` scope grants full read/write access to all private repositories — far more than needed for project management. Narrowing scopes limits the blast radius if a token is compromised. This is a potentially breaking change that requires staging validation.

**Alternatives considered**:
- Keep `repo` scope (rejected: violates principle of least privilege, explicitly called out in the audit)
- Use fine-grained personal access tokens instead of OAuth app tokens (rejected: different authentication model, out of scope for this audit)
- Gradual scope reduction with feature flags (considered: may be the implementation approach if testing reveals dependencies on `repo`)

## R8: Rate Limiting with slowapi

**Decision**: Use `slowapi` (a FastAPI-compatible wrapper around `limits`) to enforce per-user rate limits on write/AI endpoints (chat, agents, workflow) and per-IP rate limits on the OAuth callback. Configure limits as environment variables with sensible defaults. Use in-memory storage for the rate limiter state (suitable for single-instance deployment).

**Rationale**: `slowapi` is the de facto rate limiting library for FastAPI, providing decorator-based configuration that integrates naturally with existing endpoint definitions. Per-user limits (keyed by session user ID) are preferred over per-IP to avoid penalizing users behind shared NAT/VPN. Per-IP is used only for unauthenticated endpoints (OAuth callback).

**Alternatives considered**:
- Custom middleware with Redis backend (rejected: over-engineering for current scale; adds Redis dependency)
- nginx `limit_req` module (rejected: operates at the IP level only, cannot do per-user limiting)
- Token bucket algorithm from scratch (rejected: `slowapi` already implements this correctly)

## R9: localStorage Security — Chat History Refactor

**Decision**: Refactor `useChatHistory.ts` to store only lightweight references (message IDs and metadata) in localStorage with a configurable TTL. Full message content is loaded from the backend on demand via the existing chat API. All chat-related localStorage data is cleared on logout. The migration path: on first load after the update, detect old-format data, extract message IDs, and discard the full content.

**Rationale**: Storing full message content in localStorage with no expiration is a privacy risk — the data survives logout, is readable by any XSS, and accumulates indefinitely. Storing only message IDs limits the exposure surface. The TTL ensures stale references are cleaned up. Clearing on logout ensures no data persists after the session ends.

**Alternatives considered**:
- Encrypt localStorage data (rejected: the encryption key would need to be in JavaScript, negating the protection against XSS)
- Use `sessionStorage` instead (rejected: data is lost on tab close, which would break the user experience for multi-tab usage)
- Remove localStorage caching entirely (rejected: would degrade performance for users who frequently revisit chats)

## R10: GraphQL Error Message Sanitization

**Decision**: In `github_projects/service.py`, wrap all GitHub GraphQL API calls in a try/except that logs the full error internally and raises a generic `ServiceError("GitHub API request failed")` toward the API response. The internal log includes the raw error message, query structure, and request context for debugging.

**Rationale**: Raw GraphQL error messages can leak internal query structure, token scope details, and API rate limit information. Sanitizing error messages is a standard defense-in-depth measure (OWASP A09). The generic message provides enough information for the user to understand the failure without exposing internals.

**Alternatives considered**:
- Error code mapping (e.g., map specific GraphQL errors to user-friendly messages) (considered: may be added later, but a generic message is sufficient for the security fix)
- Stripping only sensitive fields from the error (rejected: difficult to maintain a comprehensive blocklist; safer to use a generic message)

## R11: Debug Mode Isolation — Webhook Verification and API Docs

**Decision**: (1) Remove the `if debug and not secret` bypass from webhook signature verification in `webhooks.py`. Developers must configure a local test secret for webhook testing. (2) Gate API documentation (Swagger/ReDoc) on a new `ENABLE_DOCS` environment variable instead of `DEBUG`. This decouples documentation exposure from the debug flag.

**Rationale**: Coupling security controls to debug flags creates risk if debug mode is accidentally enabled in production. Webhook verification must always occur — developers can use a known test secret locally. API docs exposure is a separate concern from debugging; a dedicated toggle makes the decision explicit.

**Alternatives considered**:
- Allow bypass only when both DEBUG and a specific `ALLOW_UNSIGNED_WEBHOOKS` flag are set (rejected: still couples to debug mode)
- Auto-generate a random webhook secret in debug mode (rejected: makes local webhook testing unpredictable)

## R12: CORS Origin Validation

**Decision**: Add URL format validation to the CORS origins parser in `config.py`. Each origin must have a valid scheme (`http` or `https`) and a non-empty hostname. Malformed values cause startup failure with a descriptive error message.

**Rationale**: The current comma-separated parsing silently accepts typos (e.g., `htps://example.com` or `example.com` without a scheme). Validating at startup catches misconfigurations before they reach production. Using `urllib.parse.urlparse` from the standard library avoids adding dependencies.

**Alternatives considered**:
- Regex-based validation (rejected: fragile, hard to maintain)
- Runtime validation on each CORS request (rejected: delays error detection)
- Strict allowlist from a config file (rejected: over-engineering for the current deployment model)

## R13: Docker Compose Hardening — Port Binding and Volume Mounting

**Decision**: (1) Change port bindings from `"0.0.0.0:PORT:PORT"` to `"127.0.0.1:PORT:PORT"` in the development docker-compose.yml. (2) Move the SQLite data volume from `./data` (inside the app directory) to `/var/lib/ghchat/data` (outside the application root).

**Rationale**: Binding to `0.0.0.0` exposes services on all network interfaces, making them accessible from the local network. Binding to `127.0.0.1` restricts access to localhost only. Mounting the data volume inside the application directory risks commingling runtime data with application code and makes accidental inclusion in container builds more likely.

**Alternatives considered**:
- Named Docker volumes instead of bind mounts (considered: cleaner, but less transparent for development; the bind mount at an external path is a good compromise)
- Production-only compose override (considered: may be added as a follow-up; the development compose should also be secure by default)

## R14: Database File Permissions

**Decision**: Modify `database.py` to create the database directory with `0o700` permissions and set database files to `0o600` permissions after creation. Use `os.chmod()` after directory/file creation to ensure correct permissions regardless of umask.

**Rationale**: Default `0o755` directory permissions allow any process on the container to read the database file, which contains encrypted (but still sensitive) OAuth tokens and user data. Restricting to owner-only access limits exposure in case of a compromised process running as a different user.

**Alternatives considered**:
- Setting umask globally (rejected: affects all file creation, not just the database)
- Docker volume permissions via docker-compose (rejected: doesn't apply to files created at runtime)

## R15: GitHub Actions Workflow Permission Scoping

**Decision**: Narrow the `branch-issue-link.yml` workflow permissions from `issues: write` (or broader) to the minimum needed. The workflow links branches to issues, which requires `issues: write` for commenting. Add a justification comment explaining why the permission is needed.

**Rationale**: Broad permissions in GitHub Actions workflows increase supply-chain risk. If the workflow is compromised (e.g., via a dependency injection), minimal permissions limit what the attacker can do.

**Alternatives considered**:
- Using a GitHub App with scoped permissions instead of workflow permissions (rejected: over-engineering for a simple workflow)
- Read-only permissions with a separate bot account for writes (rejected: adds operational complexity)

## R16: Avatar URL Domain Validation

**Decision**: In `IssueCard.tsx`, validate that avatar URLs use the `https:` protocol and originate from the known GitHub avatar domain `avatars.githubusercontent.com`. URLs that fail validation fall back to a placeholder avatar image.

**Rationale**: External avatar URLs from the GitHub API could theoretically be manipulated if the API response is tampered with (e.g., via a MITM on the GitHub API, which is unlikely but a defense-in-depth measure). Validating the domain prevents loading images from arbitrary external sources, which could be used for tracking or phishing.

**Alternatives considered**:
- Proxying all avatar images through the backend (rejected: adds latency and bandwidth usage for minimal security benefit)
- CSP `img-src` directive (complementary: should be part of the CSP header configuration in R6, but does not replace per-component validation)
