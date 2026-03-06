# Research: Security, Privacy & Vulnerability Audit

**Branch**: `025-security-review` | **Date**: 2026-03-06
**Status**: Complete — all NEEDS CLARIFICATION resolved

## Findings

### R1: Session Token Delivery — Cookie vs URL Parameter

- **Decision**: Replace URL-based session token delivery with HttpOnly cookie set directly on the OAuth callback response.
- **Rationale**: The current flow redirects to `{frontend_url}/auth/callback?session_token=...`, exposing the token in browser history, server/proxy logs, and HTTP Referer headers. The backend already has `_set_session_cookie()` infrastructure with HttpOnly, Secure, and SameSite=lax. The fix is to set the cookie on the callback redirect response itself and redirect with no query parameters. The frontend `useAuth.ts` currently reads `session_token` from `window.location.search` (line 29) and calls `/api/v1/auth/session` — this must be replaced with a cookie-only flow.
- **Alternatives considered**: Using a short-lived authorization code exchanged via POST — rejected as over-engineering given the cookie approach is already partially implemented. Using `fragment` (`#token=...`) instead of query parameter — rejected because fragments are still visible in browser history.
- **Impact**: `auth.py` (callback endpoint), `useAuth.ts` (remove URL param reading). SameSite should be tightened from `lax` to `strict` for defense-in-depth.

### R2: Encryption Key Enforcement at Startup

- **Decision**: Make ENCRYPTION_KEY mandatory in non-debug mode; fail startup with explicit error.
- **Rationale**: Currently `encryption.py` logs a WARNING and falls through to plaintext storage when ENCRYPTION_KEY is absent (lines 37-42). The `encrypt()` and `decrypt()` functions return plaintext unchanged. This means OAuth tokens are stored in cleartext SQLite, readable by any process with file access. The fix is a pydantic validator in `config.py` that raises `ValueError` at startup when `debug=False` and `ENCRYPTION_KEY` is empty.
- **Alternatives considered**: Runtime enforcement in encryption.py — rejected because startup-time enforcement is zero-cost and prevents any window of insecure operation. Encrypting the entire SQLite database with SQLCipher — rejected as out of scope (would require replacing aiosqlite with pysqlcipher3 and is a larger migration).
- **Migration path**: Existing plaintext token rows must be detected and migrated. The current code already detects legacy plaintext tokens by checking for GitHub token prefixes (`gho_`, `ghp_`, `ghr_`, `ghu_`, `ghs_`, `github_pat_`). A one-time migration script or startup migration step should encrypt all plaintext rows. This is included in the same change per the spec's key decision.

### R3: GITHUB_WEBHOOK_SECRET Enforcement

- **Decision**: Make GITHUB_WEBHOOK_SECRET mandatory in non-debug mode; fail startup with explicit error.
- **Rationale**: The current webhook handler (webhooks.py lines 217-233) has three branches: (1) secret set → verify signature, (2) no secret + production → reject, (3) no secret + debug → skip verification with warning. Branch 3 is the vulnerability. The startup enforcement eliminates branches 2 and 3 entirely in production.
- **Alternatives considered**: Runtime-only enforcement in the webhook handler — rejected because a missing secret should never be a valid production state.

### R4: SESSION_SECRET_KEY Minimum Length

- **Decision**: Enforce minimum 64-character length via pydantic field validator.
- **Rationale**: The current `SESSION_SECRET_KEY` field in `config.py` accepts any string with no validation. A short key enables brute-force session forgery. 64 characters provides ≥256 bits of entropy with alphanumeric characters, consistent with OWASP recommendations.
- **Alternatives considered**: Entropy-based validation (measuring actual randomness) — rejected as overly complex; length is a sufficient proxy. 32-character minimum — rejected as below OWASP recommendation.

### R5: Frontend Container Non-Root User

- **Decision**: Add a dedicated `nginx` user directive to the frontend Dockerfile.
- **Rationale**: The current Dockerfile has no USER directive; nginx runs as root (uid=0). The `nginx:alpine` base image already includes an `nginx` user (uid=101). The fix requires: (1) changing nginx config to listen on port 8080 (unprivileged) instead of 80, (2) updating file ownership for nginx cache/log directories, (3) adding `USER nginx` before the CMD. The docker-compose.yml port mapping changes from `5173:80` to `5173:8080`.
- **Alternatives considered**: Creating a custom user — rejected because the nginx base image already provides one. Using `--cap-drop ALL` without USER change — rejected because running as root is the core issue.

### R6: Centralized Project Authorization

- **Decision**: Create a `require_project_access()` FastAPI dependency in `dependencies.py` that verifies the authenticated user owns the target project.
- **Rationale**: Currently, endpoints implicitly rely on the user's GitHub token for access control — if the token has access to a GitHub project, the endpoint serves it. However, the application maintains its own project settings, tasks, and WebSocket subscriptions that are keyed by project_id without ownership verification. A centralized dependency eliminates per-endpoint duplication (Constitution Principle V: DRY).
- **Alternatives considered**: Per-endpoint inline checks — rejected as violating DRY. Middleware-based approach — rejected because not all endpoints need project authorization (e.g., auth, health).

### R7: OAuth Scope Minimization

- **Decision**: Replace `repo` scope with `read:user read:org project` scopes.
- **Rationale**: The current scope string is `"read:user read:org project repo"` (github_auth.py line 67-71). The `repo` scope grants full read/write to all private repositories. The application only needs project management access. Removing `repo` and keeping `project` (GitHub Projects V2 access) should suffice for all current operations. The `read:org` scope provides organization membership info needed for project listing.
- **Alternatives considered**: Adding `public_repo` instead of full `repo` — rejected because even `public_repo` is broader than needed. Adding `repo:status` — only needed if the app reads commit statuses, which it doesn't.
- **Risk**: May break operations that implicitly depended on repo-level access. Must be tested in staging. Users will need to re-authorize after the scope change.

### R8: Rate Limiting Library — slowapi

- **Decision**: Use `slowapi` for rate limiting on FastAPI endpoints.
- **Rationale**: slowapi is the de facto rate limiting library for FastAPI, built on top of `limits`. It provides decorator-based rate limiting with per-user and per-IP strategies, automatic 429 responses, and in-memory or Redis backends. The in-memory backend is sufficient for single-instance deployment (current architecture). Per-user limits are preferred over per-IP to avoid penalizing shared NAT/VPN users (spec key decision).
- **Alternatives considered**: Custom middleware — rejected as reinventing the wheel. `fastapi-limiter` — less maintained than slowapi. Redis-backed distributed limiter — out of scope for current single-instance architecture.
- **Suggested limits**: Chat/agent endpoints: 30 requests/minute per user. Workflow endpoints: 20 requests/minute per user. OAuth callback: 10 requests/minute per IP.

### R9: nginx Security Headers

- **Decision**: Add Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy; remove X-XSS-Protection; add `server_tokens off`.
- **Rationale**: Current nginx.conf has only X-Frame-Options, X-Content-Type-Options, and X-XSS-Protection (deprecated). Modern browsers ignore X-XSS-Protection; the CSP header replaces it. HSTS prevents protocol downgrade. Referrer-Policy prevents credential leakage in referrer headers. Permissions-Policy restricts browser feature access.
- **Suggested CSP**: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com; connect-src 'self' wss:; frame-ancestors 'none'` — allows self-hosted assets, GitHub avatars, WebSocket connections, and inline styles (needed for Tailwind).
- **Alternatives considered**: Strict CSP with nonces — rejected as requiring server-side rendering integration which the SPA doesn't have. Report-only mode first — recommended for CSP to catch violations before enforcing.

### R10: Docker Network Binding

- **Decision**: Bind development services to `127.0.0.1`; production services accessible only via reverse proxy.
- **Rationale**: Current docker-compose.yml binds backend to `"8000:8000"` and frontend to `"5173:80"`, which defaults to 0.0.0.0 (all interfaces). The fix is to prefix with `127.0.0.1:` for development. For production, remove port mappings entirely and use Docker networking with nginx as the entry point.
- **Alternatives considered**: Using Docker network mode `host` — rejected as less portable. Separate production compose file — acceptable but a single file with environment-aware configuration is simpler.

### R11: Data Volume Mount Path

- **Decision**: Move data volume from `/app/data` to `/var/lib/ghchat/data`.
- **Rationale**: Currently the SQLite volume mounts at `data` (relative to workdir `/app`), commingling runtime data with application code inside the container. Moving to `/var/lib/ghchat/data` follows the Linux FHS convention and isolates data from code.
- **Impact**: `docker-compose.yml` volume mount path, `config.py` database path default, `database.py` directory creation.

### R12: localStorage Chat History Privacy

- **Decision**: Store only message IDs with a TTL in localStorage; load content on demand from backend; clear all local data on logout.
- **Rationale**: Currently `useChatHistory.ts` stores full message content (up to 100 messages) in localStorage under `chat-message-history`. This data survives logout and is readable by any XSS. Storing only IDs with a TTL limits exposure. Clearing on logout prevents post-session data leakage.
- **Alternatives considered**: Encrypting localStorage content — rejected because the encryption key would also be in the browser, providing no real security. Using sessionStorage — rejected because it doesn't persist across tabs, degrading UX.

### R13: Debug Mode Webhook Bypass Removal

- **Decision**: Remove the debug-mode bypass for webhook signature verification. Require a locally configured test secret for development.
- **Rationale**: Current webhooks.py (lines 224-233) skips signature verification when `DEBUG=True` and no webhook secret is set. If debug mode is accidentally enabled in production, this allows unauthenticated webhook triggers. The fix removes the debug branch entirely — developers must set a test secret in `.env` for local webhook testing.
- **Alternatives considered**: Adding a separate `DISABLE_WEBHOOK_VERIFICATION` flag — rejected as too dangerous; explicit test secret is safer.

### R14: ENABLE_DOCS Environment Variable

- **Decision**: Gate API docs (Swagger/ReDoc) on a separate `ENABLE_DOCS` environment variable, independent of DEBUG.
- **Rationale**: Current main.py (lines 371-372) uses `settings.debug` to control docs_url and redoc_url. If debug is accidentally on in production, full API schema is public. A dedicated toggle allows docs in development without requiring full debug mode.
- **Alternatives considered**: Always disable docs and use a separate docs server — over-engineering for current scale.
