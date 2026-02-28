# Research: Deep Security Review of GitHub Workflows App

**Feature**: 012-deep-security-review
**Date**: 2026-02-28
**Status**: Complete

## Research Tasks

### RT-001: FastAPI Security Best Practices

**Context**: Backend uses FastAPI; need to identify security hardening patterns specific to this framework.

**Decision**: Apply FastAPI-specific security middleware stack including CORS tightening, HTTP security headers, and rate limiting.

**Rationale**: FastAPI provides native middleware support and dependency injection that makes security enforcement clean and testable. The `starlette` base already includes CORS middleware — the current configuration is overly permissive and needs tightening.

**Alternatives Considered**:
- **Custom ASGI middleware**: More flexible but harder to maintain. FastAPI's built-in middleware classes are sufficient.
- **Third-party security packages (e.g., `fastapi-security`)**: Adds dependency; the required changes are simple enough to implement directly.

**Findings**:
1. CORS: Replace wildcard `allow_methods` and `allow_headers` with explicit lists. Only `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS` are needed. Headers should be limited to `Content-Type`, `Authorization`, `X-Request-ID`.
2. Security Headers: Add middleware for `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`.
3. Rate Limiting: Use `slowapi` (built on `limits` library) for endpoint-specific rate limiting, or implement lightweight token-bucket middleware.

---

### RT-002: GitHub Actions Security Hardening

**Context**: CI workflow uses floating version tags for third-party actions (e.g., `@v4`). Need to identify current SHA commits for pinning and establish least-privilege permissions.

**Decision**: Pin all third-party GitHub Actions to specific SHA commits and add explicit `permissions:` blocks at workflow and job levels.

**Rationale**: Floating tags (e.g., `@v4`) can be retarget to any commit, including potentially malicious ones. SHA pinning eliminates supply-chain risk from compromised action tags. Least-privilege permissions limit blast radius if a job is compromised.

**Alternatives Considered**:
- **Version tags with Dependabot updates**: Still vulnerable between Dependabot check intervals. SHA pinning is the gold standard per GitHub's own security hardening guide.
- **Self-hosted action mirrors**: Operationally heavy for a project of this scale.

**Findings**:
1. Actions to pin: `actions/checkout`, `actions/setup-python`, `actions/setup-node`
2. Permissions needed per job:
   - Backend lint/check: `contents: read`
   - Frontend build/test: `contents: read`
   - Docker build: `contents: read`, `packages: read`
3. Add top-level `permissions: read-all` as a safe default, then restrict per job

---

### RT-003: Encryption and Secrets Management

**Context**: `encryption.py` makes Fernet encryption optional — if `ENCRYPTION_KEY` is not set, tokens are stored in plaintext. Need to determine the correct enforcement strategy.

**Decision**: Make encryption mandatory in production. Generate a default key if not provided (with a startup warning) rather than falling back to plaintext.

**Rationale**: Plaintext token storage is a critical vulnerability. Even a generated key (which would change on restart) is better than no encryption. In production, the key must be provided via environment variable.

**Alternatives Considered**:
- **Hard-fail if no key**: Could break development/testing workflows. A generated key with a loud warning is more practical.
- **Keep optional with documentation**: Insufficient — developers forget to configure, and plaintext tokens in the database are exploitable.

**Findings**:
1. `ENCRYPTION_KEY` should be auto-generated using `Fernet.generate_key()` when missing, with a WARNING-level log
2. Production mode (when `DEBUG=false`) should raise a startup error if `ENCRYPTION_KEY` is not explicitly set
3. Add documentation in `.env.example` clarifying the encryption key requirement

---

### RT-004: OWASP Top 10 Applicability Assessment

**Context**: Spec requires using OWASP Top 10 as a baseline. Need to map each OWASP category to the specific application.

**Decision**: Address all applicable OWASP Top 10 (2021) categories through targeted remediation.

**Rationale**: OWASP Top 10 is the industry standard for web application security. Systematically mapping each category ensures comprehensive coverage.

**Findings**:

| OWASP Category | Applicability | Current Status | Action Required |
|---------------|--------------|----------------|-----------------|
| A01: Broken Access Control | **High** | First-user auto-admin; dev-login bypass | Secure admin promotion; guard dev-login |
| A02: Cryptographic Failures | **High** | Optional encryption for tokens | Make encryption mandatory |
| A03: Injection | **Medium** | Pydantic validates API input; webhook payloads lack schema | Add webhook payload validation |
| A04: Insecure Design | **Medium** | No rate limiting; overly permissive CORS | Add rate limiting; tighten CORS |
| A05: Security Misconfiguration | **High** | Debug mode disables security controls; no security headers | Add security headers; guard debug mode |
| A06: Vulnerable Components | **Unknown** | Dependencies not yet audited | Run `npm audit`, `pip audit` |
| A07: Auth Failures | **Medium** | OAuth implementation sound; no PKCE | Document PKCE as future enhancement |
| A08: Data Integrity Failures | **High** | Unpinned CI actions; no software supply chain checks | Pin actions to SHAs |
| A09: Logging & Monitoring | **Low** | Request ID middleware exists; basic logging | Adequate for current scale |
| A10: SSRF | **Low** | No user-controlled URL fetching observed | No action needed |

---

### RT-005: Rate Limiting Strategy

**Context**: No rate limiting enforcement exists despite a `RateLimitError` exception handler in `main.py`. Need to determine the right approach for FastAPI.

**Decision**: Implement lightweight rate limiting using `slowapi` for critical endpoints (auth, webhooks, chat) with sensible defaults.

**Rationale**: `slowapi` is a well-maintained FastAPI/Starlette rate limiting library built on the `limits` library. It provides decorator-based per-endpoint rate limiting with in-memory or Redis-backed storage.

**Alternatives Considered**:
- **Custom token-bucket middleware**: More control but more code to maintain. `slowapi` handles the common cases well.
- **Nginx/reverse-proxy rate limiting**: Frontend uses Nginx, but backend needs app-level protection for internal Docker network traffic.
- **No rate limiting (document as recommendation)**: Insufficient — auth endpoints are actively vulnerable to brute force.

**Findings**:
1. Auth endpoints: 10 requests/minute per IP
2. Webhook endpoint: 60 requests/minute per IP (GitHub sends bursts)
3. Chat/API endpoints: 30 requests/minute per session
4. Use in-memory storage (default); recommend Redis for production scaling

---

### RT-006: Duplicated Security Logic Identification

**Context**: Spec requires consolidation of duplicated security patterns. Need to identify all instances of repeated security logic.

**Decision**: Consolidate token validation, permission checks, and input sanitization into `backend/src/services/security/` shared utilities.

**Rationale**: Multiple files implement similar security patterns independently. Consolidation reduces bug surface area and ensures consistent behavior.

**Findings**:

| Pattern | Locations | Proposed Utility |
|---------|-----------|-----------------|
| Session token extraction/validation | `dependencies.py`, `auth.py` | `auth_helpers.get_current_session()` |
| Admin permission check | `dependencies.py` (multiple endpoints) | `auth_helpers.require_admin()` |
| Webhook HMAC verification | `webhooks.py` | `validators.verify_webhook_signature()` |
| GitHub token encryption/decryption | `encryption.py`, `github_auth.py`, `session_store.py` | Keep in `encryption.py` (already centralized) |
| Input string sanitization | Ad-hoc in various handlers | `input_sanitizer.sanitize_string()` |
| OAuth state management | `github_auth.py` | Keep in place (already single location) |

---

### RT-007: Dependency Vulnerability Assessment Strategy

**Context**: Both frontend (npm) and backend (pip) dependencies need vulnerability scanning. Need to identify the right tools and process.

**Decision**: Use `npm audit` for frontend, `pip-audit` for backend, and add both to the CI pipeline.

**Rationale**: These are the standard, zero-configuration audit tools for their respective ecosystems. Adding them to CI ensures ongoing monitoring.

**Alternatives Considered**:
- **Trivy**: More comprehensive (covers Docker images too) but heavier setup. Recommend as a future enhancement.
- **Dependabot**: GitHub-native but only alerts — doesn't block CI. Both approaches are complementary.
- **Snyk**: Commercial tool with better remediation suggestions but adds external dependency.

**Findings**:
1. Backend: `pip-audit` scans `pyproject.toml` / installed packages for known CVEs
2. Frontend: `npm audit --audit-level=high` flags high+ severity issues
3. Both should be added as CI jobs that fail on critical/high findings
4. Initial audit results will be documented in the security review report

---

### RT-008: HTTP Security Headers for FastAPI

**Context**: No security headers middleware exists. Need to determine the appropriate headers for a FastAPI application serving an API behind a frontend reverse proxy.

**Decision**: Add a custom ASGI middleware that sets standard security headers on all responses.

**Rationale**: Security headers provide defense-in-depth against common web attacks. Since the backend API serves responses consumed by both the frontend and potentially direct API clients, headers should be set at the application level.

**Findings**:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | CSP for API responses |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Restrict browser features |
| `Cache-Control` | `no-store` (on auth endpoints) | Prevent caching of sensitive responses |
