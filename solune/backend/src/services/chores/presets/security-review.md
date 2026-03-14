---
name: Security Review
about: Recurring chore — Security Review
title: '[CHORE] Security Review'
labels: chore
assignees: ''
---

Plan: Security, Privacy & Vulnerability Audit
3 Critical · 8 High · 9 Medium · 2 Low — across OWASP Top 10. Findings describe the vulnerable pattern/behavior, not tied to specific function or line numbers.

Phase 1 — Critical (Fix Immediately)
1. Session token passed in URL — OWASP A02 (Critical)
The OAuth flow redirects the browser to the frontend with ?session_token=... in the URL. Tokens in URLs are recorded in browser history, server/proxy/CDN access logs, and HTTP Referer headers.

Correct behavior: Backend sets an HttpOnly; SameSite=Strict; Secure cookie directly on the OAuth callback response and redirects with no credentials in the URL. Frontend must never read credentials from URL params.
Files: auth.py, useAuth.ts
2. At-rest encryption not enforced — OWASP A02 (Critical)
ENCRYPTION_KEY is optional; when absent the app logs a warning and stores OAuth tokens in plaintext SQLite.

Correct behavior: On startup in non-debug mode, the application must refuse to start if ENCRYPTION_KEY is not set. Also apply the same mandatory rule to GITHUB_WEBHOOK_SECRET.
Files: config.py, encryption.py
3. Frontend container runs as root — OWASP A05 (Critical)
The frontend Dockerfile has no USER directive; nginx runs as uid=0. The backend already runs non-root.

Correct behavior: All containers must run as a dedicated non-root system user.
Files: Dockerfile
Phase 2 — High (This Week)
4. Project resources not scoped to authenticated user — OWASP A01 (High)
Endpoints that accept a project_id (task creation, WebSocket subscription, project settings, workflow operations) do not verify the authenticated user owns that project. Any authenticated user can target any project by guessing its ID.

Correct behavior: Every endpoint accepting a project identifier must verify the session has access to that project before performing any action. Centralize this check as a shared dependency.
Files: tasks.py, projects.py, settings.py, workflow.py
5. Timing attack on Signal webhook — OWASP A07 (High)
Signal webhook secret comparison uses standard string equality (!=), which leaks timing information. The GitHub webhook already uses hmac.compare_digest correctly.

Correct behavior: All secret/token comparisons throughout the codebase must use constant-time comparison.
Files: signal.py
6. Missing HTTP security headers in nginx — OWASP A05 (High)
Only basic headers are set. Missing: Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy. The present X-XSS-Protection is deprecated in modern browsers.

Correct behavior: Add all five headers; remove X-XSS-Protection; set server_tokens off to hide nginx version.
Files: nginx.conf
7. Dev endpoint accepts GitHub PAT in URL — OWASP A02 (High)
The dev login endpoint receives a GitHub Personal Access Token as a URL query parameter.

Correct behavior: All credential inputs, even dev-only, must arrive in the POST request body (JSON), never in the URL.
Files: auth.py
8. OAuth requests overly broad repo scope — OWASP A01 (High)
The app requests the repo scope, which grants full read/write access to all private repositories. Only project management access is needed.

Correct behavior: Request minimum necessary scopes. Test that all write operations work with narrower scopes before removing repo.
Files: github_auth.py
9. Session secret key has no minimum entropy check — OWASP A07 (High)
SESSION_SECRET_KEY is accepted at any length with no validation.

Correct behavior: Startup must reject keys shorter than 64 characters.
Files: config.py
10. Docker services bound to all network interfaces — OWASP A05 (High)
Backend and frontend ports are bound to 0.0.0.0, exposing them on all interfaces.

Correct behavior: Development: bind to 127.0.0.1 only. Production: expose only via a reverse proxy, not directly via container ports.
Files: docker-compose.yml
Phase 3 — Medium (Next Sprint)
11. No rate limiting on expensive/sensitive endpoints — OWASP A04 (Medium)
Chat, agent invocation, workflow, and OAuth callback endpoints have no per-user or per-IP rate limits. A single user can exhaust shared AI/GitHub quotas.

Correct behavior: Per-user limits on write/AI endpoints; per-IP limit on OAuth callback. slowapi (FastAPI-compatible) is the recommended library.
Files: chat.py, agents.py, workflow.py, auth.py
12. Cookie Secure flag not enforced in production — OWASP A02 (Medium)
cookie_secure defaults to False and relies on indirect URL-prefix detection to enable it — fragile and silently misconfigures.

Correct behavior: Startup in non-debug mode must fail if cookies are not configured as Secure.
Files: config.py
13. Debug mode bypasses webhook signature verification — OWASP A05 (Medium)
When DEBUG=true and no webhook secret is set, signature verification is skipped. If debug mode is accidentally on in production, unauthenticated callers can trigger workflows.

Correct behavior: Webhook verification must never be conditional on debug mode. Developers use a locally configured test secret.
Files: webhooks.py
14. API docs exposed when debug is enabled — OWASP A05 (Medium)
Swagger/ReDoc availability is gated on DEBUG, not a dedicated toggle. If debug is on in production, full API schema is public.

Correct behavior: Gate on a separate ENABLE_DOCS environment variable, independent of DEBUG.
Files: main.py
15. SQLite database directory is world-readable — OWASP A02 (Medium)
Database directory is created with default 0755 permissions; any process on the container can read the DB file.

Correct behavior: Create directory with 0700, database file with 0600. Only the application user needs access.
Files: database.py
16. CORS origins configuration not validated — OWASP A05 (Medium)
The comma-separated CORS origins env var is parsed with no URL format validation. Typos silently pass.

Correct behavior: Config startup validates each origin is a well-formed URL with scheme and hostname. Fail on any malformed value.
Files: config.py
17. Data volume mounted inside application directory — OWASP A05 (Medium)
The SQLite volume is mounted at data, commingling runtime data with application code.

Correct behavior: Mount data volumes outside the application root (e.g., /var/lib/solune/data).
Files: docker-compose.yml
18. Chat history stored unencrypted and indefinitely in localStorage — Privacy / OWASP A02 (Medium)
Full message content is persisted to localStorage with no expiration, survives logout, and is readable by any XSS.

Correct behavior: Store only lightweight references (message IDs) locally with a TTL. Load content from backend on demand. Clear all local data on logout.
Files: useChatHistory.ts
19. GraphQL error messages expose internal details — OWASP A09 (Medium)
Raw error messages from the GitHub GraphQL API are surfaced as internal exceptions without sanitization, potentially leaking query structure or token scope details.

Correct behavior: Log full error internally; raise only a generic sanitized message toward the API response.
Files: service.py
Phase 4 — Low (Backlog)
20. GitHub Actions workflow has broad issues: write permission — Supply Chain (Low)

Correct behavior: Scope to minimum permission needed; add a justification comment.
Files: branch-issue-link.yml
21. Avatar URLs rendered without domain validation — OWASP A03 (Low)
External avatar URLs from the GitHub API are used in <img src> without validating protocol or hostname.

Correct behavior: Validate URLs use https: and originate from a known GitHub avatar domain. Fall back to a placeholder on validation failure.
Files: IssueCard.tsx
Verification (Behavior-Based)
#	Check
1	After login, no credentials appear in browser URL bar, history, or access logs
2	Backend refuses to start in non-debug mode without ENCRYPTION_KEY set
3	docker exec into frontend container — id must return non-root UID
4	Authenticated request with unowned project_id returns 403, not success
5	WebSocket connection to an unowned project ID is rejected before any data is sent
6	All webhook secret comparisons use constant-time function (code review)
7	curl -I frontend returns Content-Security-Policy, Strict-Transport-Security, Referrer-Policy; no nginx version in Server: header
8	After rate limit threshold, expensive endpoints return 429 Too Many Requests
9	After logout, localStorage contains no message content (browser devtools)
10	DB directory permissions are 0700; file permissions are 0600
Key Decisions
OAuth scope removal (step 8): May break write operations. Test in staging; users must re-authorize after scope change.
Encryption enforcement (step 2): Breaking change for deployments without a key. Migration path for existing plaintext rows must be included in the same change.
Rate limiting: Per-user limits preferred over per-IP to avoid penalizing shared NAT/VPN users.
Out of scope: GitHub API security, MCP server internals, network-layer infrastructure.

