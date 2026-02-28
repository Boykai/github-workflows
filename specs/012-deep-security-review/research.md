# Deep Security Review — Research Findings

**Date**: 2026-02-28
**Status**: Complete
**Scope**: Security audit research for Python/FastAPI + React/TypeScript web application with GitHub Actions CI

---

## Topic 1: GitHub Actions Security Hardening — SHA Pinning and Permissions

### Decision

**Pin all third-party actions to full commit SHAs** and **add explicit least-privilege `permissions` blocks** to every workflow and job.

### Rationale

The current CI workflow (`ci.yml`) uses mutable version tags (`@v4`, `@v5`) for all action references. Tags can be force-pushed, meaning a compromised upstream action could inject malicious code into CI runs without any change to the workflow file. SHA pinning guarantees immutable action references.

The workflow also lacks explicit `permissions` blocks, inheriting the repository's default token permissions. This violates the principle of least privilege — CI jobs only need `contents: read` to check out code and run tests.

**Current state** (1 workflow file, 3 actions to pin):

| Action | Current | Pinned SHA | Tag Equivalent |
|--------|---------|------------|----------------|
| `actions/checkout` | `@v4` | Full SHA at time of implementation | v4 |
| `actions/setup-python` | `@v5` | Full SHA at time of implementation | v5 |
| `actions/setup-node` | `@v4` | Full SHA at time of implementation | v4 |

**Permissions needed per job**:

| Job | Permissions Required |
|-----|---------------------|
| `backend` | `contents: read` |
| `frontend` | `contents: read` |
| `docker` | `contents: read` |

**Best practice**: Set top-level `permissions: {}` (empty/none) and grant specific permissions per job. This follows the GitHub Actions security hardening guide and prevents privilege escalation if new jobs are added without thinking about permissions.

### Alternatives Considered

- **Keep version tags with Dependabot**: Dependabot can auto-update action versions, but tags remain mutable. SHA pinning with Dependabot for automated SHA updates is the ideal combination.
- **Use `@main` branches**: Worse than tags — even more mutable and unpredictable.
- **Do nothing**: Unacceptable per FR-001 and FR-002.

---

## Topic 2: Error Message Information Leakage in Backend API

### Decision

**Replace all `detail=str(e)` and `detail=f"..."` patterns in HTTP error responses** with generic, user-safe messages. Log the original exception details at WARNING/ERROR level for debugging.

### Rationale

Two specific locations in `backend/src/api/auth.py` leak internal exception details to API clients:

1. **Line ~101** (OAuth callback): `detail=str(e)` — exposes `ValueError` messages from the token exchange flow, which may contain OAuth service URLs, error codes, or internal state.
2. **Line ~210** (dev-login): `detail=f"Invalid GitHub token: {e}"` — exposes raw `httpx` exception details including request URLs, timeout values, and connection errors.

This violates FR-009 (API error responses MUST NOT expose internal stack traces, file paths, database details) and OWASP A02:2021 (Cryptographic Failures / Sensitive Data Exposure).

**Fix pattern**:
```python
# BEFORE (leaks details):
raise HTTPException(status_code=400, detail=str(e))

# AFTER (safe):
logger.warning("OAuth token exchange failed: %s", e)
raise HTTPException(status_code=400, detail="Authentication failed")
```

The generic exception handler in `main.py` already correctly returns `"Internal server error"` for unhandled exceptions — no change needed there.

### Alternatives Considered

- **Structured error codes**: Return machine-readable error codes (e.g., `AUTH_TOKEN_EXPIRED`, `AUTH_STATE_INVALID`) instead of generic messages. This is more developer-friendly but adds complexity. Not warranted for this scope — the existing `AppException` pattern with error codes is sufficient.
- **Debug mode exception details**: Return full details when `DEBUG=true`. Rejected because debug mode should not weaken security posture, and the dev-login endpoint already exists as a separate flow.

---

## Topic 3: Secrets Management Audit

### Decision

**No hardcoded secrets found.** The repository correctly uses environment variable substitution for all sensitive configuration. No code changes required.

### Rationale

Comprehensive scan of the repository found:

| Category | Status | Details |
|----------|--------|---------|
| `.env` file | ✅ Not committed | `.gitignore` correctly excludes `.env`, `.env.local`, `.env.*.local` |
| `.env.example` | ✅ Placeholder values only | All secrets use descriptive placeholders (e.g., `your_github_oauth_client_id`) |
| Source code | ✅ No hardcoded secrets | Config loaded via `pydantic-settings` from environment variables |
| `docker-compose.yml` | ✅ Uses `${VAR_NAME}` substitution | All sensitive values reference environment variables |
| Workflow files | ✅ No secrets usage | CI workflow runs lint/test/build only — no secret access needed |
| Test fixtures | ✅ Mock/dummy values only | No real credentials in test files |

The `EncryptionService` correctly handles the optional `ENCRYPTION_KEY`:
- Logs a clear warning when not configured (FR-013 compliant)
- Falls back to passthrough mode (plaintext storage) — acceptable for development but should be documented as a production requirement

### Alternatives Considered

- **Mandatory `ENCRYPTION_KEY`**: Could enforce this via `pydantic-settings` validation. Rejected — the current optional pattern with a startup warning is pragmatic for development while alerting production operators.
- **Git secrets scanning in CI**: Could add `truffleHog` or `gitleaks` as a CI step. Out of scope for this review but recommended as a future enhancement.

---

## Topic 4: Dependency Vulnerability Assessment

### Decision

**Audit both backend (pip) and frontend (npm) dependency trees** for known CVEs. Remediate all critical and high-severity findings by updating to patched versions where available.

### Rationale

The dependency trees include:

**Backend (Python)**:
- `fastapi>=0.109.0` — Web framework
- `python-jose[cryptography]>=3.3.0` — JWT handling
- `httpx>=0.26.0` — HTTP client
- `pydantic>=2.5.0` — Data validation
- `aiosqlite>=0.20.0` — Async SQLite
- `tenacity>=8.2.0` — Retry logic
- `websockets>=12.0` — WebSocket client

**Frontend (npm)**:
- `react@^18.3.1`, `react-dom@^18.3.1` — UI framework
- `@tanstack/react-query@^5.17.0` — Data fetching
- `socket.io-client@^4.7.4` — WebSocket client
- `vite@^5.4.0` — Build tool (dev)
- Various `@radix-ui`, `lucide-react`, `tailwindcss` packages

**Audit approach**:
1. Run `pip audit` (or equivalent) against `pyproject.toml` pinned versions
2. Run `npm audit` against `package-lock.json`
3. Cross-reference findings with GitHub Advisory Database
4. Update packages to fixed versions where available
5. Document any accepted risks for vulnerabilities without available fixes

### Alternatives Considered

- **Snyk/Dependabot integration**: Automated scanning tools. Recommended as ongoing protection but the immediate manual audit satisfies FR-004 for this review.
- **Lock file regeneration**: Could regenerate all lock files with latest versions. Rejected — too broad, may introduce breaking changes unrelated to security.

---

## Topic 5: Authentication and Session Security Patterns

### Decision

**Existing auth implementation is strong.** Minor improvements: sanitize error messages (covered in Topic 2) and document the `cookie_secure=True` production requirement.

### Rationale

Security audit of the authentication flow found:

| Control | Status | Details |
|---------|--------|---------|
| OAuth state parameter | ✅ Strong | `secrets.token_urlsafe(32)`, 10-min TTL, single-use `pop()`, bounded dict (max 1000) |
| Session cookies | ✅ Good | `HttpOnly`, `SameSite=lax`, configurable `Secure` flag, 8-hour max age |
| Token encryption at rest | ✅ Good | Fernet (AEAD) encryption, optional with startup warning |
| Admin authorization | ✅ Adequate | `require_admin()` dependency injection, first-user auto-promotion |
| Session cleanup | ✅ Good | Background task purges expired sessions every hour |
| HMAC webhook verification | ✅ Strong | `hmac.compare_digest()` (timing-safe comparison) |
| Error responses | ❌ Needs fix | Exception details leak in 2 auth endpoints (Topic 2) |

**No structural changes needed.** The existing patterns (centralized `get_current_session()`, `require_admin()` dependency, `EncryptionService` singleton) are already well-factored.

### Alternatives Considered

- **Add rate limiting**: Would protect auth endpoints from brute-force attacks. Out of scope for this review — requires new middleware and configuration. Recommended as a future enhancement.
- **Add CSRF tokens**: `SameSite=lax` cookies provide CSRF protection for state-changing requests. Additional CSRF tokens would add complexity without meaningful security improvement for this application's threat model.

---

## Topic 6: Input Validation and Data Exposure

### Decision

**Current input validation is adequate for the application's threat model.** FastAPI's Pydantic validation and type system provide baseline protection. The frontend correctly avoids `dangerouslySetInnerHTML` and XSS vectors.

### Rationale

| Category | Status | Details |
|----------|--------|---------|
| SQL injection | ✅ Safe | Uses `aiosqlite` with parameterized queries throughout |
| XSS | ✅ Safe | React's JSX auto-escaping; no `dangerouslySetInnerHTML` usage; backend never renders HTML |
| Command injection | ✅ Safe | No `os.system()`, `subprocess`, or shell invocations in application code |
| Input length limits | ⚠️ Implicit | FastAPI/Pydantic provide type validation but no explicit `max_length` on all string fields |
| API error responses | ❌ Fix needed | Two endpoints leak exception details (Topic 2) |
| Log sanitization | ✅ Good | Logger uses `%s` formatting (no f-strings with user data); no credentials in log patterns |

**No changes needed** beyond the error message fixes in Topic 2. The Pydantic models and FastAPI type annotations provide sufficient input validation for the current API surface.

### Alternatives Considered

- **Add explicit `max_length` constraints to all Pydantic fields**: Would add defense-in-depth but the OAuth code/state parameters are validated by GitHub's API. The effort-to-benefit ratio is low for this scope.
- **Add a WAF or input sanitization middleware**: Over-engineered for this application. FastAPI's built-in protections are sufficient.

---

## Topic 7: Security Logic Consolidation (DRY)

### Decision

**Security logic is already well-consolidated.** No significant duplication found. Minor documentation improvements recommended.

### Rationale

Audit of security-related code patterns:

| Pattern | Instances | Location | Duplicated? |
|---------|-----------|----------|-------------|
| Session validation | 1 | `get_current_session()` in `api/auth.py` | No — single canonical implementation used as FastAPI dependency |
| Admin authorization | 1 | `require_admin()` in `dependencies.py` | No — single dependency |
| Token encryption | 1 | `EncryptionService` in `services/encryption.py` | No — lazy singleton |
| OAuth state management | 1 | `GitHubAuthService` in `services/github_auth.py` | No — single service |
| Webhook HMAC verification | 1 | `verify_webhook_signature()` in `api/webhooks.py` | No — single function |
| Cookie setting | 2 | `auth.py` lines ~81-89 and ~193-201 | Yes — login and dev-login both set cookies with identical parameters |

The only duplication found is the cookie-setting code in the OAuth login and dev-login endpoints. Both set the same cookie with the same flags (`httponly`, `samesite`, `secure`, `max_age`). This could be extracted to a shared helper, but the duplication is minimal (7 lines × 2) and both instances are in the same file.

**Recommendation**: Extract cookie-setting to a helper function in the same file for DRY compliance, but this is a low-priority improvement.

### Alternatives Considered

- **Create a `security/` module**: Would add a new directory and files. Rejected — the existing structure is already well-organized with security logic in appropriate locations (auth in `api/auth.py`, encryption in `services/encryption.py`, etc.).
- **Create middleware for all security checks**: Over-abstraction. FastAPI's dependency injection pattern is the correct approach for this application.

---

## Summary of Decisions

| Topic | Decision | Confidence | Action Required |
|-------|----------|------------|-----------------|
| **1. GitHub Actions Hardening** | Pin actions to SHAs, add permissions blocks | High | Yes — modify `ci.yml` |
| **2. Error Message Leakage** | Replace `detail=str(e)` with generic messages | High | Yes — modify `auth.py` |
| **3. Secrets Management** | No hardcoded secrets found | High | No — document finding |
| **4. Dependency Audit** | Audit and update vulnerable dependencies | High | Yes — run audits, update as needed |
| **5. Auth/Session Security** | Existing patterns are strong | High | No — minor documentation only |
| **6. Input Validation** | Adequate for threat model | High | No — covered by error message fix |
| **7. Security Logic DRY** | Already consolidated; minor cookie helper extraction | Medium | Low priority — optional refactor |
