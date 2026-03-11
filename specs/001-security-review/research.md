# Research: Security Review Remediation Program

**Branch**: `001-security-review` | **Date**: 2026-03-11

## Research Tasks & Findings

### R-001: Cookie-Based Session Transfer — Best Practices for OAuth Callback

**Context**: Finding #1 requires removing session tokens from URL parameters. The current flow redirects with `?session_token=...`, exposing credentials in browser history, server logs, and Referer headers.

**Decision**: Set an `HttpOnly; SameSite=Strict; Secure` cookie on the OAuth callback response and issue a clean `302` redirect to the frontend root with no query parameters.

**Rationale**: The backend already uses FastAPI's `Response` object for cookie management. The OAuth callback endpoint (`/api/v1/auth/github/callback`) can set the session cookie directly on the redirect response. The frontend `useAuth.ts` hook already supports cookie-based authentication for API calls via `credentials: "include"` — the URL parameter reading path is the only one that needs removal.

Implementation approach:

1. In `auth.py` callback: replace `RedirectResponse(url=f"{frontend_url}?session_token={token}")` with setting the cookie on the response and redirecting to `frontend_url` without parameters
2. Cookie attributes: `httponly=True`, `samesite="strict"`, `secure=settings.cookie_secure`, `max_age=settings.cookie_max_age`, `path="/"`
3. In `useAuth.ts`: remove URL search parameter parsing for `session_token`; the browser automatically sends the cookie on subsequent requests

**Alternatives Considered**:

- POST-based token transfer (frontend fetches token via POST after redirect) — Rejected: adds a network round-trip and requires temporary state management; cookie is simpler and more standard
- `window.postMessage` from a popup — Rejected: complicates the flow and doesn't work with redirect-based OAuth
- Fragment-based token (`#token=...`) — Rejected: fragments are not sent to servers but are still visible in browser history and accessible via JavaScript

### R-002: Pydantic Settings Validation — Production Fail-Fast Pattern

**Context**: Findings #2, #9, #12, #16 require startup validation that blocks the application from running with unsafe configuration in non-debug mode.

**Decision**: Use Pydantic `@model_validator(mode="after")` in the existing `Settings` class to enforce all production security requirements in a single validation pass.

**Rationale**: The `Settings` class already extends `pydantic_settings.BaseSettings` and is instantiated once at startup. Pydantic validators run automatically during `__init__`, making them ideal for fail-fast behavior. A single `model_validator` can check all conditions and raise `ValueError` with a clear message listing all violations.

Validation rules (non-debug mode only):

1. `encryption_key` must not be `None`
2. `github_webhook_secret` must not be empty
3. `session_secret_key` must be ≥64 characters
4. `cookie_secure` must be `True`
5. Each CORS origin must be a well-formed URL with `http://` or `https://` scheme and a valid hostname

**Alternatives Considered**:

- Separate startup script that validates before launching uvicorn — Rejected: adds deployment complexity and can be bypassed
- Runtime checks in middleware — Rejected: too late; the application is already accepting requests
- Environment variable validation in Docker entrypoint — Rejected: doesn't cover non-Docker deployments

### R-003: Project-Level Authorization — Centralized FastAPI Dependency

**Context**: Finding #4 requires project ownership verification across 4+ endpoint files and WebSocket handlers. The codebase already uses `require_selected_project(session)` for project selection validation.

**Decision**: Add `verify_project_access(session, project_id)` as a shared async dependency in `dependencies.py` that queries whether the authenticated user has access to the specified project.

**Rationale**: The existing pattern in `dependencies.py` provides `require_selected_project()` which validates that a project is selected but does not verify ownership. The new dependency follows the same pattern:

1. Accept the session (from existing auth dependency) and the project_id (from path/query parameter)
2. Query the GitHub Projects API (using the user's token) to verify the user can access the project
3. Return the verified project_id on success; raise `HTTPException(status_code=403)` on failure
4. Cache the result per session+project for the duration of the request to avoid redundant API calls

This approach centralizes the check, ensuring consistency across `tasks.py`, `projects.py`, `settings.py`, `workflow.py`, and WebSocket handlers.

**Alternatives Considered**:

- Per-endpoint inline checks — Rejected: duplicates logic across 4+ files, creates drift risk when new endpoints are added
- Middleware-based approach — Rejected: project_id extraction varies by endpoint (path param, query param, body); middleware can't reliably parse all cases
- Database-based ownership table — Rejected: adds storage complexity; the authoritative source is GitHub's API, and the codebase already makes GitHub API calls for project operations

### R-004: Timing-Safe Secret Comparison — stdlib hmac.compare_digest

**Context**: Finding #5 identifies timing attack vulnerability in Signal webhook secret comparison using `!=` operator.

**Decision**: Use Python's `hmac.compare_digest()` from the standard library for all secret/token comparisons.

**Rationale**: `hmac.compare_digest()` is specifically designed for constant-time string comparison to prevent timing attacks. It's already used correctly in the GitHub webhook handler (`webhooks.py`). The Signal webhook handler (`signal.py`) is the only identified instance using standard `!=` comparison.

Audit scope:

1. `signal.py`: Replace `!=` with `hmac.compare_digest()` for webhook secret
2. Codebase-wide grep for `secret` + `!=` or `==` patterns to catch any other instances
3. Verify `webhooks.py` already uses `hmac.compare_digest()` (confirmed)

**Alternatives Considered**:

- Third-party constant-time comparison library — Rejected: stdlib `hmac.compare_digest` is sufficient and already in use
- Custom comparison function — Rejected: security-critical code should use well-tested stdlib

### R-005: Rate Limiting — slowapi Integration Pattern

**Context**: Finding #11 requires per-user and per-IP rate limits on expensive endpoints. The `slowapi` library is already a dependency in `pyproject.toml`.

**Decision**: Use `slowapi` with a custom key function that identifies authenticated users by session ID and falls back to IP for unauthenticated endpoints (OAuth callback).

**Rationale**: `slowapi` wraps `limits` and integrates natively with FastAPI. It supports:

- Custom key functions (per-user via session, per-IP via `request.client.host`)
- Decorator-based rate limits per endpoint
- Configurable storage backends (in-memory is sufficient for single-instance deployment)
- Standard `429 Too Many Requests` responses

Implementation approach:

1. Initialize `Limiter` in `main.py` with a default key function using session ID
2. Add `@limiter.limit("X/minute")` decorators to: chat endpoints, agent invocation, workflow triggers, OAuth callback
3. OAuth callback uses IP-based key function (no session available)
4. Rate limit values: research suggests 30/minute for write endpoints, 10/minute for AI endpoints, 5/minute for OAuth callback (configurable via environment variables)

**Alternatives Considered**:

- Custom middleware with token bucket — Rejected: more code to maintain, less tested than `slowapi`
- nginx-level rate limiting — Rejected: cannot distinguish per-user; only operates on IP
- Redis-backed rate limiting — Rejected: over-engineered for single-instance SQLite deployment; adds infrastructure dependency

### R-006: OAuth Scope Reduction — GitHub Permission Analysis

**Context**: Finding #8 identifies overly broad `repo` scope. The application only needs project management access.

**Decision**: Replace `repo` scope with `read:org` + `project` scopes. If `project` scope alone is insufficient for write operations, add `public_repo` as a fallback (narrower than full `repo`).

**Rationale**: The application's GitHub API usage (based on codebase analysis) includes:

- Reading/writing GitHub Projects V2 items (requires `project` scope)
- Reading repository metadata, branches, PRs (requires `repo` or `public_repo`)
- Creating issues and PRs (requires `repo` or `public_repo`)
- Reading organization membership (requires `read:org`)

The `project` scope was introduced by GitHub specifically for Projects V2 and is the minimum required for project board operations. Repository operations on public repos work with `public_repo`; private repos need `repo`. This must be tested in staging.

**Key Decision**: This is a potentially breaking change. The migration path:

1. Deploy with reduced scopes
2. Existing users continue with their current token until it expires
3. On re-authorization, users grant the reduced scope set
4. Monitor for 403 errors in staging to identify any operations that require broader access
5. If critical operations fail, add the minimum additional scope needed

**Alternatives Considered**:

- Keep `repo` scope — Rejected: violates least-privilege principle (Finding #8)
- Fine-grained personal access tokens — Rejected: not applicable to OAuth app flow; fine-grained tokens are for PATs only
- Separate OAuth apps per scope — Rejected: unnecessarily complex

### R-007: Client-Side Chat Privacy — localStorage TTL Pattern

**Context**: Finding #18 requires replacing full message body storage in localStorage with lightweight references that expire automatically.

**Decision**: Store only `{ messageId, conversationId, timestamp }` references in localStorage with a 24-hour TTL. Load full message content from the backend on demand. Clear all chat data on logout.

**Rationale**: The current `useChatHistory.ts` hook persists full message content to localStorage, which survives logout and is accessible to any XSS attack. The remediation:

1. Replace stored messages with reference objects: `{ id: string, conversationId: string, storedAt: number }`
2. On read, filter out references older than 24 hours (lazy TTL enforcement)
3. On logout, call `localStorage.removeItem()` for all chat-related keys
4. When the user navigates to a conversation, fetch full messages from the backend API

This matches the spec assumption: "Client-side chat history may retain lightweight references for usability, but those references should expire automatically within 24 hours and be cleared on logout."

**Alternatives Considered**:

- sessionStorage instead of localStorage — Rejected: loses references on tab close, which is too aggressive for usability
- Encrypted localStorage — Rejected: key management in the browser is insecure; reducing stored data is more effective
- No local storage at all — Rejected: loses the ability to show recent conversation list without a network call

### R-008: GraphQL Error Sanitization — Logging vs. User-Facing Pattern

**Context**: Finding #19 identifies raw GitHub GraphQL API error messages being surfaced to users, potentially leaking query structure or token scope details.

**Decision**: Catch GraphQL exceptions in `service.py`, log the full error with `logger.error()` including all details, and re-raise a generic `HTTPException(502, "External service error")` or equivalent sanitized message.

**Rationale**: The existing codebase uses Python's `logging` module consistently. The pattern:

1. In `service.py` GraphQL methods: wrap API calls in try/except
2. On `GraphQLError` or HTTP error from GitHub: `logger.error("GitHub API error", extra={"query": query_name, "error": str(e)})`
3. Raise a new exception with a generic message: `"An error occurred while communicating with GitHub. Please try again later."`
4. Never include the original error message, query text, or scope details in the user-facing response

**Alternatives Considered**:

- Error code mapping (specific codes for specific GitHub errors) — Rejected: over-engineered for the current need; a generic message is sufficient
- Error sanitization middleware — Rejected: too broad; only GraphQL service errors need this treatment

### R-009: Avatar URL Validation — Domain Allowlist Pattern

**Context**: Finding #21 identifies external avatar URLs rendered without protocol or hostname validation.

**Decision**: Create a validation utility function that checks `https:` protocol and hostname against an allowlist of known GitHub avatar domains. Fall back to a placeholder SVG on validation failure.

**Rationale**: GitHub avatar URLs consistently use `https://avatars.githubusercontent.com/u/{id}` format. The validation:

1. Parse the URL
2. Verify protocol is `https:`
3. Verify hostname is in the allowlist: `["avatars.githubusercontent.com"]`
4. On failure, return a default placeholder image (inline SVG or static asset)

This is implemented in the `IssueCard.tsx` component where avatar URLs are rendered.

**Alternatives Considered**:

- Content-Security-Policy `img-src` restriction only — Rejected: CSP already restricts to `https://avatars.githubusercontent.com`, but a malformed URL could still cause rendering issues; component-level validation provides defense in depth
- Server-side avatar proxy — Rejected: adds infrastructure complexity for a low-severity finding
- Subresource Integrity (SRI) for images — Rejected: SRI doesn't apply to `<img>` tags

### R-010: Nginx Security Headers — Modern Best Practices

**Context**: Finding #6 requires adding missing security headers and removing deprecated ones.

**Decision**: The current `nginx.conf` already includes CSP, HSTS, Referrer-Policy, and Permissions-Policy headers. The remaining changes are: remove `X-XSS-Protection` (deprecated) and add `server_tokens off`.

**Rationale**: Codebase review confirmed the following headers are already present:

- `Content-Security-Policy` with appropriate directives
- `Strict-Transport-Security` with `max-age=31536000; includeSubDomains`
- `Referrer-Policy` set to `strict-origin-when-cross-origin`
- `Permissions-Policy` disabling camera, microphone, geolocation
- `X-Frame-Options` set to `SAMEORIGIN`
- `X-Content-Type-Options` set to `nosniff`

Missing:

- `server_tokens off` — prevents nginx version disclosure in `Server:` header
- Remove `X-XSS-Protection` — deprecated in modern browsers, can cause false positives

**Alternatives Considered**:

- Additional CSP directives (e.g., `require-trusted-types-for 'script'`) — Deferred: Trusted Types is still evolving and may break existing inline styles
- `Cross-Origin-Embedder-Policy` / `Cross-Origin-Opener-Policy` — Deferred: may break WebSocket connections; requires testing
