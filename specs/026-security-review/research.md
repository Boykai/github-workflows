# Research: Security, Privacy & Vulnerability Audit

**Feature Branch**: `026-security-review`
**Date**: 2026-03-07
**Status**: Complete — all NEEDS CLARIFICATION resolved

## Findings

### 1. Cookie-Based Session Delivery (FR-001, FR-002)

- **Decision**: Replace URL-based session token delivery with HttpOnly cookie set directly on the OAuth callback response. Frontend no longer reads credentials from URL parameters.
- **Rationale**: The current flow passes `session_token` as a URL query parameter (via `POST /session?session_token=...` and the frontend `useAuth.ts` reading `window.location.search`). Tokens in URLs are recorded in browser history, server/proxy/CDN access logs, and HTTP Referer headers. The industry standard is to set an HttpOnly; SameSite=Strict; Secure cookie on the OAuth callback response and redirect with a clean URL.
- **Alternatives considered**:
  - POST body with CSRF token — adds complexity without benefit since the backend controls the redirect
  - Short-lived exchange code — unnecessary indirection when the backend can set the cookie directly
- **Implementation approach**:
  - `backend/src/services/github_auth.py`: After OAuth token exchange, create session and set cookie directly on the redirect response (already partially done via `_set_session_cookie`)
  - `backend/src/api/auth.py`: OAuth callback endpoint sets cookie on the `RedirectResponse` to frontend. Remove the `POST /session?session_token=...` endpoint.
  - `frontend/src/hooks/useAuth.ts`: Remove the `useEffect` that reads `session_token` from URL params. Authentication state is derived from the cookie-authenticated `/api/v1/auth/me` endpoint.
  - SameSite policy: Change from `lax` to `strict` per spec requirement

### 2. Mandatory Encryption Key and Secrets (FR-003, FR-004, FR-015)

- **Decision**: Add startup validation in `config.py` that refuses to start in non-debug mode without `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, and a `SESSION_SECRET_KEY` of at least 64 characters.
- **Rationale**: Currently `ENCRYPTION_KEY` is optional (tokens stored in plaintext when absent), `GITHUB_WEBHOOK_SECRET` is optional (webhooks unverified), and `SESSION_SECRET_KEY` has no minimum length. Production deployments can silently run insecure.
- **Alternatives considered**:
  - Runtime warnings only — rejected because warnings are ignored in practice
  - Auto-generation of keys — rejected because auto-generated keys are lost on restart and don't persist across instances
- **Migration path**: Existing deployments with plaintext tokens need a one-time migration. The `encryption.py` service already detects legacy plaintext tokens by prefix (`gho_`, `ghp_`, etc.) and returns them as-is during decryption. Once `ENCRYPTION_KEY` is mandatory, a migration script or first-run process encrypts all existing plaintext rows.

### 3. Non-Root Frontend Container (FR-005)

- **Decision**: Add a dedicated `nginx` user to the frontend Dockerfile and configure nginx to run as non-root.
- **Rationale**: The frontend Dockerfile currently has no `USER` directive; nginx runs as uid=0. The backend already runs as `appuser`. Running as root increases the blast radius of any container compromise.
- **Alternatives considered**:
  - nginx unprivileged image (`nginxinc/nginx-unprivileged`) — rejected because it changes the base image and may have different behavior; adding a USER directive to the existing `nginx:alpine` is simpler and more controlled
  - Distroless nginx — rejected as too restrictive for debugging
- **Implementation approach**:
  - Change nginx to listen on port 8080 (non-privileged port) instead of 80
  - Add `RUN addgroup -S nginx-app && adduser -S -G nginx-app nginx-app` and `USER nginx-app`
  - Create necessary directories with correct ownership (`/var/cache/nginx`, `/var/run`, `/tmp`)
  - Update `docker-compose.yml` to map `5173:8080` instead of `5173:80`

### 4. Centralized Project Ownership Authorization (FR-006, FR-007, FR-008)

- **Decision**: Create a shared FastAPI dependency (`verify_project_access`) that validates the authenticated user owns/has access to the target project. Apply to all endpoints accepting `project_id`.
- **Rationale**: Currently, endpoints like tasks, settings, workflow, and WebSocket accept `project_id` without verifying ownership. Any authenticated user can access any project by guessing its ID. The spec requires centralization (FR-007) to prevent future endpoints from forgetting the check.
- **Alternatives considered**:
  - Per-endpoint inline checks — rejected because it violates DRY and is error-prone
  - Database-level row security — SQLite doesn't support this natively
- **Implementation approach**:
  - Create `verify_project_access(session: UserSession, project_id: str)` in `dependencies.py`
  - The check queries the user's project list (already fetched by `github_projects_service.list_projects`) and confirms `project_id` is in the set
  - Apply as a FastAPI `Depends()` on `tasks.py`, `projects.py`, `settings.py`, `workflow.py`
  - For WebSocket: verify before accepting the connection; reject with close code 4403 if unauthorized

### 5. Constant-Time Secret Comparison (FR-009)

- **Decision**: Replace `!=` comparison in Signal webhook with `hmac.compare_digest()`.
- **Rationale**: `signal.py` line 287 uses `x_signal_secret != settings.signal_webhook_secret` which leaks timing information. The GitHub webhook in `webhooks.py` already correctly uses `hmac.compare_digest()`.
- **Alternatives considered**: None — `hmac.compare_digest` is the standard Python constant-time comparison function.
- **Implementation**: Single-line change in `signal.py`. Also audit entire codebase for other `==`/`!=` comparisons of secrets.

### 6. HTTP Security Headers (FR-010, FR-011, FR-012)

- **Decision**: Add Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy headers. Remove X-XSS-Protection. Add `server_tokens off`.
- **Rationale**: The current `nginx.conf` only sets X-Frame-Options, X-Content-Type-Options, and the deprecated X-XSS-Protection. Modern browsers need CSP, HSTS, and Referrer-Policy for defense-in-depth.
- **Alternatives considered**:
  - Backend middleware for headers — rejected because nginx is the edge server; headers should be set at the edge
  - Meta tags in HTML — rejected because some headers (HSTS) can only be set via HTTP headers
- **Header values**:
  - `Content-Security-Policy`: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com; connect-src 'self' wss:; frame-ancestors 'none'`
  - `Strict-Transport-Security`: `max-age=31536000; includeSubDomains`
  - `Referrer-Policy`: `strict-origin-when-cross-origin`
  - `Permissions-Policy`: `camera=(), microphone=(), geolocation=()`
  - Remove: `X-XSS-Protection`
  - Add: `server_tokens off` in http context

### 7. Dev Login POST Migration (FR-013)

- **Decision**: Change dev login from `GET /dev-login?github_token=...` to `POST /dev-login` with JSON body `{"github_token": "..."}`.
- **Rationale**: Current endpoint uses `Query(...)` parameter, recording the PAT in server logs and browser history. Even dev-only endpoints should follow secure credential handling.
- **Alternatives considered**: None — POST body is the standard approach.
- **Implementation**: Change `Query(...)` to `Body(...)` with a Pydantic request model. Frontend dev tooling must update to POST.

### 8. OAuth Scope Reduction (FR-014)

- **Decision**: Replace `repo` scope with `read:user read:org project` (remove `repo`).
- **Rationale**: The current scope string is `"read:user read:org project repo"`. The `repo` scope grants full read/write to all private repositories. The application only needs project management access. The `project` scope provides access to GitHub Projects V2.
- **Alternatives considered**:
  - `repo:status` + `public_repo` — still too broad; `project` scope alone is sufficient for project management
  - Keep `repo` with audit logging — rejected because principle of least privilege requires removing unnecessary access
- **Risk**: Some write operations may depend on `repo` scope. Must test in staging before deploying. Existing users need to re-authorize on next login to downgrade their token scopes.
- **Testing approach**: Verify all GitHub Projects V2 operations (create issue, move item, update status) work with `project` scope only.

### 9. Rate Limiting with slowapi (FR-017, FR-018, FR-019)

- **Decision**: Use `slowapi` library (FastAPI-compatible, based on `limits`) for per-user and per-IP rate limiting.
- **Rationale**: slowapi is the recommended FastAPI rate limiting library. It integrates via middleware and decorators, supports multiple storage backends (in-memory for single-instance, Redis for multi-instance), and provides per-user and per-IP limiting strategies.
- **Alternatives considered**:
  - Custom middleware with BoundedDict — more code, less battle-tested
  - fastapi-limiter — less maintained than slowapi
  - Reverse proxy rate limiting (nginx) — doesn't support per-user limits, only per-IP
- **Implementation approach**:
  - Add `slowapi` to `pyproject.toml` dependencies
  - Create `backend/src/middleware/rate_limit.py` with limiter configuration
  - Apply per-user limits on: `chat.py`, `agents.py`, `workflow.py` endpoints
  - Apply per-IP limit on: `auth.py` OAuth callback endpoint
  - Return 429 with `Retry-After` header

### 10. Cookie Secure Flag Enforcement (FR-020)

- **Decision**: Startup validation in non-debug mode requires `cookie_secure=True` (or auto-detected from HTTPS frontend URL).
- **Rationale**: `cookie_secure` defaults to `False` and relies on `effective_cookie_secure` auto-detection from `frontend_url`. If the URL detection fails or is misconfigured, cookies are sent over HTTP.
- **Implementation**: Add validation in `config.py` startup: in non-debug mode, `effective_cookie_secure` must be True.

### 11. Webhook Verification Independence from Debug (FR-021)

- **Decision**: Remove the debug-mode bypass in webhook signature verification. Developers must configure a local test secret.
- **Rationale**: Lines 224–233 of `webhooks.py` skip verification when `debug=True` and no secret is configured. If debug is accidentally enabled in production, unauthenticated callers can trigger workflows.
- **Implementation**: Remove the `elif not settings.debug` / `else: logger.warning(...)` branch. Always require `github_webhook_secret` to be set (enforced by FR-004 startup validation).

### 12. API Docs Toggle (FR-022)

- **Decision**: Add `ENABLE_DOCS` environment variable, independent of `DEBUG`.
- **Rationale**: Currently `docs_url` and `redoc_url` are gated on `settings.debug`. A separate toggle allows docs in staging (for testing) without enabling all debug features.
- **Implementation**: Add `enable_docs: bool = False` to config. Use `settings.enable_docs` instead of `settings.debug` for docs URLs in `main.py`.

### 13. Database Permission Hardening (FR-023)

- **Decision**: Set directory permissions to 0o700 and file permissions to 0o600 after creation.
- **Rationale**: `database.py` uses `mkdir(parents=True, exist_ok=True)` with default permissions. Depending on umask, the directory could be world-readable.
- **Implementation**: `db_dir.mkdir(parents=True, exist_ok=True, mode=0o700)` and `os.chmod(db_path, 0o600)` after database file creation.

### 14. CORS Origin Validation (FR-024)

- **Decision**: Validate each CORS origin as a well-formed URL with scheme and hostname at config startup.
- **Rationale**: Current `cors_origins_list` property splits on commas with no URL validation. Typos silently pass.
- **Implementation**: Add URL parsing validation in the `cors_origins_list` property or a `model_validator`. Use `urllib.parse.urlparse` to verify scheme (http/https) and hostname presence.

### 15. External Volume Mount (FR-025)

- **Decision**: Change volume mount from `/app/data` to `/var/lib/ghchat/data`.
- **Rationale**: Current mount at `data` (relative to `/app`) commingles runtime data with application code.
- **Implementation**: Update `docker-compose.yml` volume mount path. Update `backend/Dockerfile` to create `/var/lib/ghchat/data` with correct ownership. Update `config.py` default `database_path` if it references `/app/data`.

### 16. Chat History Lightweight References (FR-026, FR-027)

- **Decision**: Replace full message content storage in localStorage with lightweight message ID references. Clear all local data on logout.
- **Rationale**: Current `useChatHistory.ts` stores full message text in localStorage with no expiration. This data survives logout and is readable by any XSS.
- **Implementation approach**:
  - `useChatHistory.ts`: Store only message IDs (or input history for the shell-like navigation) with a TTL
  - Note: The current hook stores *sent message input history* (shell-like navigation), not full chat conversation content. The security requirement applies to ensuring no sensitive content persists. Add TTL-based expiration and logout clearing.
  - Add a `clearOnLogout()` function called from the logout flow in `useAuth.ts`

### 17. GraphQL Error Sanitization (FR-028)

- **Decision**: Log full GitHub GraphQL errors internally; raise only generic sanitized messages in API responses.
- **Rationale**: `service.py` line 345–347 concatenates raw GraphQL error messages and raises them as `ValueError`. These could expose query structure or token scope details.
- **Implementation**: `logger.error("GraphQL error: %s", error_msg)` + `raise ValueError("GitHub API request failed")` (generic message).

### 18. GitHub Actions Permission Scoping (FR-029)

- **Decision**: Permissions are already minimal (`issues: write`, `contents: read` at job level, `permissions: {}` at workflow level). Add justification comments.
- **Rationale**: The workflow already follows least-privilege with job-level permission grants. Adding comments explains *why* each permission is needed.
- **Implementation**: Add inline YAML comments next to each permission declaration.

### 19. Avatar URL Domain Validation (FR-030)

- **Decision**: Validate avatar URLs use `https:` protocol and originate from `avatars.githubusercontent.com`. Fall back to a placeholder on validation failure.
- **Rationale**: External URLs from the GitHub API are rendered in `<img>` tags without validation. A compromised or spoofed API response could inject arbitrary image URLs.
- **Implementation**: Create a utility function `validateAvatarUrl(url: string): string` that checks protocol and hostname, returning the URL if valid or a placeholder SVG/data URI if invalid.

## Implementation Order

The recommended execution order follows the phased priority from the spec:

### Phase 1 — Critical (Fix Immediately)
1. Cookie-based session delivery (FR-001, FR-002) — `auth.py`, `github_auth.py`, `useAuth.ts`
2. Mandatory encryption key + secrets validation (FR-003, FR-004, FR-015) — `config.py`, `encryption.py`
3. Non-root frontend container (FR-005) — `frontend/Dockerfile`, `docker-compose.yml`

### Phase 2 — High (This Week)
4. Centralized project ownership (FR-006, FR-007, FR-008) — `dependencies.py`, `tasks.py`, `projects.py`, `settings.py`, `workflow.py`
5. Constant-time comparisons (FR-009) — `signal.py`
6. HTTP security headers (FR-010, FR-011, FR-012) — `nginx.conf`
7. Dev login POST migration (FR-013) — `auth.py`
8. OAuth scope reduction (FR-014) — `github_auth.py`
9. Session secret key minimum length (FR-015) — `config.py` (grouped with #2)
10. Localhost port binding (FR-016) — `docker-compose.yml`

### Phase 3 — Medium (Next Sprint)
11. Rate limiting (FR-017, FR-018, FR-019) — `middleware/rate_limit.py`, `chat.py`, `agents.py`, `workflow.py`, `auth.py`
12. Cookie Secure enforcement (FR-020) — `config.py`
13. Webhook debug bypass removal (FR-021) — `webhooks.py`
14. API docs toggle (FR-022) — `config.py`, `main.py`
15. Database permissions (FR-023) — `database.py`
16. CORS validation (FR-024) — `config.py`
17. External volume mount (FR-025) — `docker-compose.yml`, `Dockerfile`
18. Chat history refs + logout clear (FR-026, FR-027) — `useChatHistory.ts`, `useAuth.ts`
19. GraphQL error sanitization (FR-028) — `service.py`

### Phase 4 — Low (Backlog)
20. Actions permissions comments (FR-029) — `branch-issue-link.yml`
21. Avatar URL validation (FR-030) — `IssueCard.tsx`
