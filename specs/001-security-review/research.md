# Research: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-23
**Input**: [plan.md](plan.md) Technical Context unknowns

## Research Summary

All 21 security findings were researched and evaluated against the current codebase. Research confirms that all findings have been addressed. Each decision below documents the chosen approach, rationale, and alternatives considered.

---

## Phase 1 — Critical

### Decision 1: Session Token Delivery Mechanism

**Finding**: Session token passed in URL (OWASP A02 Critical)

**Decision**: Use HttpOnly, SameSite=Strict, Secure cookies set directly on the OAuth callback response. The backend redirects the browser to the frontend with no credentials in the URL.

**Rationale**: Cookies with HttpOnly prevent JavaScript access (mitigating XSS token theft). SameSite=Strict prevents CSRF. Secure ensures transmission only over HTTPS. URL-based tokens are logged in browser history, proxy logs, and Referer headers — all of which are common exfiltration vectors.

**Alternatives considered**:
- URL fragment (`#token=...`): Not sent to servers but still visible in browser history and accessible via JavaScript. Rejected.
- Authorization header with localStorage: Requires JavaScript to manage tokens, making it vulnerable to XSS. Rejected.
- Short-lived URL token with immediate exchange: Adds complexity without eliminating the exposure window. Rejected.

**Implementation pattern**:
```python
# Backend OAuth callback sets cookie and redirects cleanly
response = RedirectResponse(url=f"{frontend_url}/auth/callback")
response.set_cookie(
    key=SESSION_COOKIE_NAME,
    value=str(session.session_id),
    httponly=True,
    secure=settings.effective_cookie_secure,
    samesite="strict",
    max_age=settings.cookie_max_age,
    path="/",
)
```

---

### Decision 2: Encryption Key and Secrets Enforcement Strategy

**Finding**: At-rest encryption not enforced (OWASP A02 Critical)

**Decision**: In non-debug mode, the application validates at startup that `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, and `SESSION_SECRET_KEY` (≥64 chars) are all configured. Validation failures collect all errors and raise a single `ValueError` preventing startup.

**Rationale**: Fail-fast at startup ensures no production deployment can accidentally run without encryption. Collecting all errors in a single pass prevents the frustrating cycle of fixing one error only to discover the next.

**Alternatives considered**:
- Runtime checks on each request: Adds per-request overhead and allows the application to run in a vulnerable state. Rejected.
- Warning-only mode: Defeats the purpose of enforcement. Rejected.
- Separate validation CLI command: Adds operational complexity; inline startup validation is simpler and cannot be skipped. Rejected.

**Migration path**: Existing deployments without an encryption key must generate one (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) and set it before upgrading. Existing plaintext data must be migrated using a one-time migration script.

---

### Decision 3: Non-Root Container Execution

**Finding**: Frontend container runs as root (OWASP A05 Critical)

**Decision**: Both frontend and backend containers run as dedicated non-root system users (`nginx-app` and `appuser` respectively). The frontend listens on port 8080 (non-privileged) instead of 80.

**Rationale**: Containers running as root can escalate to host-level access if a container escape vulnerability is exploited. Non-root execution limits the blast radius to the unprivileged user's permissions.

**Alternatives considered**:
- `--cap-drop ALL` with root user: Reduces capabilities but root UID still grants access to root-owned files. Rejected.
- rootless Docker: Good additional layer but does not protect against in-container escalation. Complementary, not a replacement.

**Implementation pattern**:
```dockerfile
# Frontend Dockerfile
RUN addgroup -S nginx-app && adduser -S -G nginx-app nginx-app
# ... configure nginx for non-root (port 8080, writable dirs)
USER nginx-app
EXPOSE 8080
```

---

## Phase 2 — High

### Decision 4: Centralized Project Access Authorization

**Finding**: Project resources not scoped to authenticated user (OWASP A01 High)

**Decision**: A shared `verify_project_access` dependency in `dependencies.py` verifies that the authenticated session has access to the requested project. All endpoints accepting a `project_id` parameter use this dependency (either via FastAPI's `dependencies=[]` or explicit `await` call).

**Rationale**: Centralized authorization prevents inconsistent enforcement across endpoints. A shared dependency ensures that adding new project-scoped endpoints automatically follows the same pattern.

**Alternatives considered**:
- Per-endpoint authorization logic: Error-prone, easy to forget on new endpoints. Rejected.
- Database-level row security: Not supported by SQLite. Rejected.
- Middleware-based path matching: Fragile, depends on URL patterns that may change. Rejected.

**Affected endpoints**: tasks.py, projects.py, settings.py, workflow.py, pipelines.py, agents.py (all verified).

---

### Decision 5: Constant-Time Secret Comparison

**Finding**: Timing attack on Signal webhook (OWASP A07 High)

**Decision**: All secret and token comparisons use `hmac.compare_digest()` from Python's standard library. This applies to Signal webhook secrets, GitHub webhook signatures, and any future secret comparisons.

**Rationale**: Standard string equality (`==`, `!=`) short-circuits on the first differing character, leaking information about how many leading characters are correct. `hmac.compare_digest()` runs in constant time regardless of input.

**Alternatives considered**:
- Custom constant-time comparison: Reinventing cryptographic primitives is error-prone. Rejected.
- Hashing both sides before comparison: Adds computational overhead without benefit when `hmac.compare_digest` is available. Rejected.

---

### Decision 6: HTTP Security Headers Configuration

**Finding**: Missing HTTP security headers in nginx (OWASP A05 High)

**Decision**: Add all five required headers via nginx configuration: Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy, X-Frame-Options. Remove deprecated X-XSS-Protection. Set `server_tokens off` to hide the nginx version.

**Rationale**: Security headers are defense-in-depth measures that protect against clickjacking (X-Frame-Options, CSP frame-ancestors), XSS (CSP script-src), protocol downgrade (HSTS), information leakage (Referrer-Policy, server_tokens), and unauthorized feature access (Permissions-Policy).

**CSP policy chosen**: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com data:; connect-src 'self' ws: wss:; frame-ancestors 'none'`

**Alternatives considered**:
- Application-level headers via FastAPI middleware: Would not protect static assets served directly by nginx. Rejected.
- Report-only CSP initially: Good for monitoring but does not provide protection. Can be used as a transition strategy.

---

### Decision 7: Dev Login Endpoint Security

**Finding**: Dev endpoint accepts GitHub PAT in URL (OWASP A02 High)

**Decision**: The dev-login endpoint accepts credentials exclusively in the POST request body (JSON). A Pydantic `DevLoginRequest` model validates the request body structure. The endpoint is only available in debug mode.

**Rationale**: URL parameters appear in server access logs, browser history, and Referer headers. POST body data is not logged by default and is not visible in the URL bar.

**Alternatives considered**:
- Remove dev login entirely: Makes local development harder. Rejected.
- Authorization header: More complex for developer tooling (curl, httpie). POST body is simpler.

---

### Decision 8: OAuth Scope Management

**Finding**: OAuth requests overly broad `repo` scope (OWASP A01 High)

**Decision**: The current scopes are `read:user read:org project repo`. The `repo` scope is **retained** because GitHub's API returns misleading 404 errors for issue/PR creation operations without it. This is documented with a code comment explaining the necessity.

**Rationale**: The application creates issues, sub-issues, comments, labels, and PRs as part of its core workflow. Testing with narrower scopes (`public_repo`, `project` only) confirmed that GitHub returns 404 errors for these write operations without `repo` scope.

**Alternatives considered**:
- `public_repo` only: Does not grant access to private repository operations. Rejected for users with private repos.
- `project` only: Insufficient for issue/PR creation. Rejected.
- GitHub App installation tokens: Would provide fine-grained permissions but requires significant architectural changes and a different authentication model. Deferred to future enhancement.

**Risk mitigation**: The scope is documented with justification, and the decision is tracked in the plan's Complexity Tracking section.

---

### Decision 9: Session Secret Key Entropy

**Finding**: Session secret key has no minimum entropy check (OWASP A07 High)

**Decision**: Startup validation rejects `SESSION_SECRET_KEY` values shorter than 64 characters in non-debug mode. Generation command documented: `openssl rand -hex 32`.

**Rationale**: 64 characters (256 bits when hex-encoded) provides sufficient entropy for cryptographic session signing. The check runs at startup, failing fast before any sessions are created.

**Alternatives considered**:
- No minimum length: Allows weak keys that can be brute-forced. Rejected.
- Higher minimum (128 characters): Unnecessarily strict; 64 characters already provides 256 bits of entropy. Rejected.

---

### Decision 10: Docker Network Binding

**Finding**: Docker services bound to all network interfaces (OWASP A05 High)

**Decision**: All Docker Compose port bindings use `127.0.0.1:hostPort:containerPort` format, restricting access to the loopback interface only. Production deployments use a reverse proxy in front.

**Rationale**: Binding to `0.0.0.0` exposes services on all network interfaces, allowing external access to what should be internal services. Binding to `127.0.0.1` ensures only local access.

**Alternatives considered**:
- Docker network isolation without port mapping: Prevents direct host access but complicates development. The `127.0.0.1` binding is simpler.
- Firewall rules: Additional layer of defense but should not be the primary control. Network binding is more reliable.

---

## Phase 3 — Medium

### Decision 11: Rate Limiting Strategy

**Finding**: No rate limiting on expensive/sensitive endpoints (OWASP A04 Medium)

**Decision**: Use `slowapi` (FastAPI-compatible, already a dependency) with per-user limits on write/AI endpoints and per-IP limits on the OAuth callback. Specific limits: chat 10/min, agents 5/min, workflow 10/min, OAuth callback 20/min (per-IP).

**Rationale**: Per-user limits prevent individual abuse while avoiding penalizing shared NAT/VPN users. Per-IP limits on the OAuth callback prevent brute-force attacks against the authentication endpoint.

**Alternatives considered**:
- Per-IP only: Penalizes users behind shared NAT/VPN. Rejected as primary strategy.
- Redis-backed rate limiting: Adds infrastructure complexity. SQLite-backed slowapi is sufficient for current scale. Rejected.
- API gateway rate limiting: Would require additional infrastructure. Rejected for current deployment model.

---

### Decision 12: Cookie Secure Flag Enforcement

**Finding**: Cookie Secure flag not enforced in production (OWASP A02 Medium)

**Decision**: Auto-detect HTTPS from `FRONTEND_URL` prefix. In non-debug mode, startup fails if `effective_cookie_secure` is False. Override available via `COOKIE_SECURE=true` environment variable.

**Rationale**: Auto-detection from the frontend URL is convenient and correct in most configurations. The explicit override handles edge cases (e.g., TLS termination at load balancer with HTTP internally).

**Alternatives considered**:
- Manual-only configuration: Requires operators to always set `COOKIE_SECURE=true` explicitly, easy to forget. Rejected.
- Always enforce Secure regardless of mode: Breaks local HTTP development. Rejected.

---

### Decision 13: Webhook Verification Independence from Debug Mode

**Finding**: Debug mode bypasses webhook signature verification (OWASP A05 Medium)

**Decision**: Webhook signature verification is always required, regardless of debug mode. Developers must configure a local test secret (`GITHUB_WEBHOOK_SECRET`). If no secret is configured, webhooks are rejected.

**Rationale**: Conditional security controls based on debug mode create a risk of accidental production exposure. A locally configured test secret is equally convenient for development.

**Alternatives considered**:
- Keep debug bypass with warning: Acceptable risk trade-off for developer convenience — rejected because a single misconfiguration in production exposes the endpoint.
- Allow unsigned webhooks in a separate `ALLOW_UNSIGNED_WEBHOOKS` flag: Adds a dedicated toggle but still creates the same risk. Rejected.

---

### Decision 14: API Documentation Toggle

**Finding**: API docs exposed when debug is enabled (OWASP A05 Medium)

**Decision**: API documentation (Swagger/ReDoc) is gated on a dedicated `ENABLE_DOCS` environment variable, independent of `DEBUG`. Defaults to `false`.

**Rationale**: Separating docs visibility from debug mode prevents accidental API schema exposure. Developers who need docs explicitly opt in.

**Alternatives considered**:
- IP-allowlisted docs: More complex to configure; an env var toggle is simpler. Rejected.
- Authentication-gated docs: Adds overhead for a development tool. Rejected.

---

### Decision 15: Database File Permissions

**Finding**: SQLite database directory is world-readable (OWASP A02 Medium)

**Decision**: Create database directory with `0o700` (owner only). Set database file permissions to `0o600` (owner read/write). Re-enforce permissions on database recovery.

**Rationale**: Restrictive file permissions are the simplest and most reliable access control mechanism at the filesystem level. The application user is the only process that needs database access.

**Alternatives considered**:
- SQLite encryption (SQLCipher): Adds a build dependency and performance overhead; filesystem permissions are sufficient for the container threat model. Rejected.
- Docker volume-level ACLs: Platform-dependent and not portable across all Docker hosts. Rejected.

---

### Decision 16: CORS Origins Validation

**Finding**: CORS origins configuration not validated (OWASP A05 Medium)

**Decision**: The `cors_origins_list` property parses the comma-separated string, trims whitespace, skips empty entries, and validates that each origin has a valid scheme (http/https) and hostname. Raises `ValueError` on any malformed value.

**Rationale**: Silent acceptance of malformed CORS origins can lead to unexpected cross-origin behavior. Strict validation at startup catches typos immediately.

**Alternatives considered**:
- Runtime validation on each CORS request: Adds per-request overhead and allows the application to start with misconfigured CORS. Rejected.
- Wildcard origin support: Too permissive for a security-focused application. Rejected.

---

### Decision 17: Data Volume Mount Location

**Finding**: Data volume mounted inside application directory (OWASP A05 Medium)

**Decision**: Mount named Docker volume at `/var/lib/solune/data` (outside the application root). Database path defaults to `/var/lib/solune/data/settings.db`.

**Rationale**: Commingling runtime data with application code increases the attack surface. Separating data into a standard location (`/var/lib/`) follows Linux Filesystem Hierarchy Standard conventions.

**Alternatives considered**:
- Subdirectory within app root with restricted permissions: Still comingles data with code, making container volume management less clean. Rejected.
- `/opt/solune/data`: Valid but `/var/lib/` is the conventional Linux location for variable application data. Rejected.

---

### Decision 18: Chat History Storage Model

**Finding**: Chat history stored unencrypted and indefinitely in localStorage (Privacy / OWASP A02 Medium)

**Decision**: Chat history is kept in React state (memory only). No content is persisted to localStorage. Legacy localStorage data is explicitly cleared. On logout, all local state is reset.

**Rationale**: Memory-only storage ensures chat content does not survive page reloads, logout, or XSS attacks. This is the simplest approach that provides the strongest privacy guarantee.

**Alternatives considered**:
- Encrypted localStorage with TTL: Adds complexity and still exposes the encryption key to JavaScript. Rejected.
- SessionStorage: Survives page reloads within the same tab but cleared on tab close. Less private than memory-only. Rejected.
- IndexedDB with encryption: Over-engineered for chat input history. Rejected.

---

### Decision 19: GraphQL Error Sanitization

**Finding**: GraphQL error messages expose internal details (OWASP A09 Medium)

**Decision**: Exceptions from GitHub API calls are caught, logged server-side with full details, and generic responses are returned to clients. Error handlers return `{}`, `False`, or raise `HTTPException` with sanitized messages.

**Rationale**: Logging full errors server-side preserves debuggability. Returning generic responses to clients prevents leakage of query structure, token scopes, or internal identifiers.

**Alternatives considered**:
- Error code mapping: Map specific GitHub API errors to user-facing error codes. Adds complexity without sufficient benefit for the current use case. Rejected.
- Structured error objects with redacted fields: More informative but risks partial information leakage. Rejected.

---

## Phase 4 — Low

### Decision 20: GitHub Actions Workflow Permissions

**Finding**: GitHub Actions workflow has broad `issues: write` permission (Supply Chain Low)

**Decision**: Set default permissions to `{}` (empty) at the workflow level. Grant only `issues: write` and `contents: read` at the job level with justification comments explaining why each permission is needed.

**Rationale**: Principle of least privilege. Explicit justification comments help future maintainers understand why each permission is granted and evaluate whether it can be narrowed.

**Alternatives considered**:
- Separate workflow for each permission level: Over-engineers the CI pipeline for a simple linking job. Rejected.
- Repository-level default permissions: Less granular and affects all workflows. Rejected.

---

### Decision 21: Avatar URL Validation

**Finding**: Avatar URLs rendered without domain validation (OWASP A03 Low)

**Decision**: Validate avatar URLs client-side before rendering. Accept only `https:` protocol from `avatars.githubusercontent.com`. Fall back to an inline SVG placeholder for invalid URLs.

**Rationale**: Rendering arbitrary external URLs in `<img>` tags can lead to SSRF-like behavior (information disclosure via image loading from attacker-controlled servers). Allowlisting the known GitHub avatar domain eliminates this risk.

**Alternatives considered**:
- Backend avatar proxying: Adds latency and infrastructure. Rejected for current scale.
- CSP img-src restriction only: Does not provide a graceful fallback. Used as defense-in-depth alongside client-side validation.
