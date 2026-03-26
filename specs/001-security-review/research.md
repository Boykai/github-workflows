# Research: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-26 | **Status**: Complete

## Methodology

Each of the 21 original findings was verified against the current codebase (commit `dc0a85c`) by inspecting the specific files and code paths identified in the audit. Findings are categorized as **REMEDIATED** (fix already present), **JUSTIFIED** (documented exception), or **OPEN** (requires implementation work).

---

## Finding 1 — Session Token Passed in URL (OWASP A02, Critical)

**Status**: ✅ REMEDIATED

- **Decision**: Session credentials are set as `HttpOnly; SameSite=Strict; Secure` cookies on the OAuth callback response. No credentials appear in URL query parameters.
- **Rationale**: `auth.py` lines 22–39 set the session cookie with `httponly=True`, `samesite="strict"`, `secure=settings.effective_cookie_secure`. The OAuth callback redirects to the frontend with no credential parameters in the URL.
- **Alternatives considered**: URL fragment (`#token=...`) — rejected because fragments are still in browser history and some proxy logs.

## Finding 2 — At-Rest Encryption Not Enforced (OWASP A02, Critical)

**Status**: ✅ REMEDIATED

- **Decision**: In non-debug mode, the application refuses to start without `ENCRYPTION_KEY` and `GITHUB_WEBHOOK_SECRET`. `SESSION_SECRET_KEY` must be ≥64 characters. `cookie_secure` must be true.
- **Rationale**: `config.py` `_validate_production_secrets()` (lines 128–227) enforces all mandatory secrets at startup. Fernet encryption in `encryption.py` encrypts all OAuth tokens at rest.
- **Alternatives considered**: Warn-and-continue — rejected because plaintext token storage is an unacceptable risk in production.

## Finding 3 — Frontend Container Runs as Root (OWASP A05, Critical)

**Status**: ✅ REMEDIATED

- **Decision**: Frontend Dockerfile creates a dedicated `nginx-app` user and switches to it before runtime.
- **Rationale**: `Dockerfile` lines 26–41 create user `nginx-app`, change ownership of all nginx directories, and execute `USER nginx-app`. Port 8080 (non-privileged) is used.
- **Alternatives considered**: Using nginx official `unprivileged` image — rejected in favor of explicit user creation for full control over UID/GID.

## Finding 4 — Project Resources Not Scoped to Authenticated User (OWASP A01, High)

**Status**: ✅ REMEDIATED

- **Decision**: Centralized `verify_project_access()` dependency in `dependencies.py` (lines 181–206) verifies the authenticated user owns the project before any action.
- **Rationale**: All endpoints accepting `project_id` use `Depends(verify_project_access)`. The check queries the GitHub API for the user's project list and raises `AuthorizationError` (403) if the project is not found.
- **Alternatives considered**: Database-level ownership check — rejected because project ownership is authoritative in GitHub, not in the local database.

## Finding 5 — Timing Attack on Signal Webhook (OWASP A07, High)

**Status**: ✅ REMEDIATED

- **Decision**: Signal webhook uses `hmac.compare_digest()` for timing-safe comparison.
- **Rationale**: `signal.py` lines 273–274 use `hmac.compare_digest(x_signal_secret, settings.signal_webhook_secret)`. GitHub webhook verification in `webhooks.py` also uses `hmac.compare_digest`. CSRF middleware uses `secrets.compare_digest`.
- **Alternatives considered**: N/A — constant-time comparison is the only correct approach.

## Finding 6 — Missing HTTP Security Headers in Nginx (OWASP A05, High)

**Status**: ✅ REMEDIATED

- **Decision**: Comprehensive security headers configured in `nginx.conf`.
- **Rationale**: Headers present: `Content-Security-Policy`, `Strict-Transport-Security` (max-age=31536000), `Referrer-Policy`, `Permissions-Policy`, `X-Content-Type-Options`, `X-Frame-Options`. Deprecated `X-XSS-Protection` is not present. `server_tokens off` is configured.
- **Alternatives considered**: Helmet.js middleware — not applicable to nginx-served static frontend.

## Finding 7 — Dev Endpoint Accepts GitHub PAT in URL (OWASP A02, High)

**Status**: ✅ REMEDIATED

- **Decision**: Dev login endpoint (`/dev-login`) accepts GitHub PAT in POST request body (JSON), not in URL query parameters. Only available when `DEBUG=true`.
- **Rationale**: `auth.py` lines 190–218 implement the dev-login as a POST endpoint with the PAT in the request body.
- **Alternatives considered**: Remove dev-login entirely — rejected because it is needed for local development without full OAuth setup.

## Finding 8 — OAuth Requests Overly Broad Repo Scope (OWASP A01, High)

**Status**: ⚠️ JUSTIFIED EXCEPTION

- **Decision**: The `repo` scope is retained because GitHub returns misleading 404 errors for issue/PR/comment write operations when only `project` or `read:org` scopes are granted.
- **Rationale**: `github_auth.py` lines 70–74 document this: "GitHub returns misleading 404s for many of those writes when the OAuth token only has project/read scopes, so repository scope is required here for the core workflow to function." The app creates issues, sub-issues, comments, labels, and PRs — all requiring `repo` scope.
- **Alternatives considered**: `public_repo` + `repo:status` — rejected after testing showed 404 failures on private repository operations. Fine-grained PATs were evaluated but are not supported for OAuth Apps (only GitHub Apps).

## Finding 9 — Session Secret Key Has No Minimum Entropy Check (OWASP A07, High)

**Status**: ✅ REMEDIATED

- **Decision**: In non-debug mode, startup rejects `SESSION_SECRET_KEY` values shorter than 64 characters; in debug mode, the same condition produces a warning.
- **Rationale**: `config.py` `_validate_production_secrets()` enforces `len(session_secret_key) >= 64` as a fatal check only when `debug` is false, while the debug-mode branch logs a warning so local development is not blocked.
- **Alternatives considered**: Entropy measurement — rejected as overly complex; length ≥64 with random generation guidance is sufficient.

## Finding 10 — Docker Services Bound to All Network Interfaces (OWASP A05, High)

**Status**: ✅ REMEDIATED

- **Decision**: Both backend and frontend bind to `127.0.0.1` only in `docker-compose.yml`.
- **Rationale**: Backend: `127.0.0.1:8000:8000`. Frontend: `127.0.0.1:5173:8080`. Signal API uses `expose` (internal only, not published to host).
- **Alternatives considered**: Firewall rules — rejected as less reliable than address binding; defense-in-depth recommends both.

## Finding 11 — No Rate Limiting on Expensive Endpoints (OWASP A04, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: `slowapi` Limiter with per-user key function applied to expensive endpoints.
- **Rationale**: `rate_limit.py` implements `RateLimitKeyMiddleware` that resolves user identity (GitHub user ID → session ID → IP). Chat endpoint (`chat.py` line 948) has `@limiter.limit("10/minute")`. Rate limiting infrastructure supports all endpoint categories.
- **Alternatives considered**: Custom middleware — rejected in favor of `slowapi` (FastAPI-compatible, well-maintained).

## Finding 12 — Cookie Secure Flag Not Enforced in Production (OWASP A02, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: Production startup fails if `cookie_secure` is not configured as enabled.
- **Rationale**: `config.py` `_validate_production_secrets()` checks `cookie_secure` in non-debug mode and refuses to start if not set. Additionally, `effective_cookie_secure` auto-enables when `frontend_url` starts with `https://`.
- **Alternatives considered**: Auto-enable based on URL only — rejected as fragile; explicit configuration is safer.

## Finding 13 — Debug Mode Bypasses Webhook Signature Verification (OWASP A05, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: Webhook verification is always enforced regardless of debug mode.
- **Rationale**: `webhooks.py` lines 209–240 verify webhook signatures unconditionally. If `github_webhook_secret` is not configured, the request is rejected (not bypassed). Comment confirms: "Verify signature — always required regardless of debug mode."
- **Alternatives considered**: N/A — conditional verification is never acceptable.

## Finding 14 — API Docs Exposed When Debug Is Enabled (OWASP A05, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: API docs availability is controlled by `ENABLE_DOCS` environment variable, independent of `DEBUG`.
- **Rationale**: `main.py` lines 591–592 use `settings.enable_docs` (defaults to `False`). `config.py` line 95 defines `enable_docs: bool = False`.
- **Alternatives considered**: Gating on DEBUG — rejected as the original vulnerability.

## Finding 15 — SQLite Database Directory Is World-Readable (OWASP A02, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: Directory created with `0o700`, database file set to `0o600`.
- **Rationale**: `database.py` lines 32–42 create directory with `mode=0o700` and enforce `chmod(0o700)`. Lines 50–56 set database file to `chmod(0o600)`.
- **Alternatives considered**: Relying on Docker isolation only — rejected; defense-in-depth requires filesystem permissions too.

## Finding 16 — CORS Origins Configuration Not Validated (OWASP A05, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: Each CORS origin is validated as a well-formed URL with scheme and hostname at startup.
- **Rationale**: `config.py` `cors_origins_list` property (lines 230–248) uses `urlparse()` to validate each origin has `http`/`https` scheme and valid hostname. Raises `ValueError` on malformed values.
- **Alternatives considered**: Regex validation — rejected in favor of `urlparse()` for robustness.

## Finding 17 — Data Volume Mounted Inside Application Directory (OWASP A05, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: Data volume mounted at `/var/lib/solune/data` (outside application root).
- **Rationale**: `docker-compose.yml` uses named volume `solune-data:/var/lib/solune/data`, separate from the application directory.
- **Alternatives considered**: Bind mount — rejected; named volumes are managed by Docker and provide better isolation.

## Finding 18 — Chat History Stored in localStorage (Privacy / OWASP A02, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: Chat history is stored in React memory state only. No localStorage persistence. Legacy data is cleaned up.
- **Rationale**: `useChatHistory.ts` stores messages in `useState` (memory only). `clearLegacyStorage()` removes any pre-v2 localStorage data. `clearHistory()` wipes both memory and legacy storage on logout.
- **Alternatives considered**: Encrypted localStorage — rejected; memory-only is simpler and more secure.

## Finding 19 — GraphQL Error Messages Expose Internal Details (OWASP A09, Medium)

**Status**: ✅ REMEDIATED

- **Decision**: `handle_service_error()` logs full exception internally and raises a sanitized generic message to callers.
- **Rationale**: `logging_utils.py` `handle_service_error()` (lines 224–267) catches exceptions, logs full details, and raises a safe generic message. This pattern is used across service files.
- **Alternatives considered**: Error codes only — rejected; generic messages provide minimal user context without leaking internals.

## Finding 20 — GitHub Actions Workflow Has Broad Permissions (Supply Chain, Low)

**Status**: ✅ REMEDIATED

- **Decision**: Workflow declares minimum permissions with justification comments.
- **Rationale**: `branch-issue-link.yml` sets `permissions: {}` at workflow level and scopes per-job: `issues: write` (with comment "Required to post comments on issues") and `contents: read` (with comment "Required to read repository metadata").
- **Alternatives considered**: No explicit permissions — rejected; GitHub defaults are too broad.

## Finding 21 — Avatar URLs Rendered Without Domain Validation (OWASP A03, Low)

**Status**: ✅ REMEDIATED

- **Decision**: Avatar URLs validated for `https:` protocol and `avatars.githubusercontent.com` hostname. Falls back to SVG placeholder on failure.
- **Rationale**: `IssueCard.tsx` `validateAvatarUrl()` function checks `parsed.protocol === 'https:'` and `ALLOWED_AVATAR_HOSTS.includes(parsed.hostname)`. Returns an inline SVG placeholder for invalid URLs.
- **Alternatives considered**: Content-Security-Policy `img-src` only — rejected; URL validation provides an additional layer beyond CSP.

---

## Summary of Remaining Work

| Finding | Status | Action Required |
|---------|--------|----------------|
| 1–7 | ✅ Remediated | Verification only |
| 8 (OAuth scopes) | ⚠️ Justified | Document exception; consider re-evaluation when GitHub fine-grained PATs support OAuth Apps |
| 9–21 | ✅ Remediated | Verification only |

**All NEEDS CLARIFICATION items have been resolved through codebase analysis.** The primary implementation task is behavioral verification of all 21 controls, plus documentation of the OAuth scope justified exception.
