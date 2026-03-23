# Security Behavioral Contracts

**Feature**: 001-security-review | **Date**: 2026-03-23
**Input**: [spec.md](../spec.md) acceptance scenarios, [data-model.md](../data-model.md) validation rules

## Overview

This document defines the behavioral contracts for each security finding. Contracts specify the expected inputs, outputs, and invariants that the implementation must satisfy. They are organized by implementation phase and map directly to functional requirements (FR-001 through FR-029).

---

## Phase 1 — Critical Contracts

### Contract C-001: OAuth Callback Session Delivery (FR-001, FR-002)

**Precondition**: User completes GitHub OAuth authorization flow
**Input**: OAuth callback with `code` and `state` parameters
**Expected behavior**:
1. Backend exchanges `code` for GitHub access token
2. Backend creates a `UserSession` and stores it server-side
3. Backend sets response cookie:
   - Name: `SESSION_COOKIE_NAME` constant
   - Flags: `httponly=True`, `secure=effective_cookie_secure`, `samesite="strict"`
   - Max-age: `cookie_max_age` (8 hours default)
4. Backend redirects to `{frontend_url}/auth/callback` with no query parameters
5. Frontend `useAuth` hook reads session from cookie automatically (via browser cookie jar)
6. Frontend never reads credentials from `window.location.search` or `window.location.hash`

**Postcondition**: User is authenticated; no credentials in URL, history, or logs
**Error behavior**: Invalid OAuth state → redirect to frontend with error page

### Contract C-002: Startup Configuration Enforcement (FR-003, FR-004, FR-014, FR-019)

**Precondition**: Application startup in non-debug mode
**Input**: Environment variables: `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, `SESSION_SECRET_KEY`, `COOKIE_SECURE` / `FRONTEND_URL`
**Expected behavior**:
1. Validator collects all errors in a list
2. Missing `ENCRYPTION_KEY` → error appended
3. Missing `GITHUB_WEBHOOK_SECRET` → error appended
4. `SESSION_SECRET_KEY` length < 64 → error appended with current length
5. `effective_cookie_secure` is False → error appended
6. If error list is non-empty → raise `ValueError` with all errors joined
7. Application exits before binding to any port

**Postcondition**: Application runs only with all security configuration present
**Debug mode behavior**: Warnings logged instead of errors; application starts

### Contract C-003: Non-Root Container Execution (FR-005)

**Precondition**: Docker container image built and started
**Input**: Dockerfile build context and container runtime configuration
**Expected behavior**:
1. Backend container: `USER appuser` directive in Dockerfile
2. Frontend container: `USER nginx-app` directive in Dockerfile
3. Frontend listens on port 8080 (non-privileged)
4. `docker exec <container> id` returns non-zero UID

**Postcondition**: No container process runs as root (UID 0)

---

## Phase 2 — High Contracts

### Contract C-004: Project Access Verification (FR-006, FR-007)

**Precondition**: Authenticated user makes request with `project_id` parameter
**Input**: `project_id` path parameter, session cookie
**Expected behavior**:
1. `verify_project_access(request, project_id, session)` is invoked
2. Function checks session user has access to the specified project
3. If access denied → raise `HTTPException(status_code=403)`
4. If access granted → request proceeds normally

**Postcondition**: No unauthorized project access possible
**Coverage**: tasks.py, projects.py, settings.py, workflow.py, pipelines.py, agents.py

### Contract C-005: Constant-Time Secret Comparison (FR-008)

**Precondition**: Incoming request contains a secret/token for verification
**Input**: Client-provided secret, server-stored secret
**Expected behavior**:
1. All comparisons use `hmac.compare_digest(a, b)`
2. No `==`, `!=`, or `in` operators used for secret comparison
3. Response time is independent of how many leading characters match

**Postcondition**: Timing analysis cannot extract secret characters
**Coverage**: signal.py (Signal webhook), webhooks.py (GitHub webhook)

### Contract C-006: HTTP Security Headers (FR-009, FR-010, FR-011)

**Precondition**: Any HTTP request to the frontend
**Input**: HTTP request
**Expected response headers**:
1. `Content-Security-Policy`: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com data:; connect-src 'self' ws: wss:; frame-ancestors 'none'`
2. `Strict-Transport-Security`: `max-age=31536000; includeSubDomains`
3. `Referrer-Policy`: `strict-origin-when-cross-origin`
4. `Permissions-Policy`: `camera=(), microphone=(), geolocation=()`
5. `X-Frame-Options`: `SAMEORIGIN`
6. `X-Content-Type-Options`: `nosniff`
7. `server_tokens off` → `Server` header contains no version

**Absent headers**: `X-XSS-Protection` (deprecated, removed)
**Postcondition**: All defense-in-depth headers present

### Contract C-007: Dev Login POST Body Only (FR-012)

**Precondition**: Developer uses dev-login endpoint (debug mode only)
**Input**: POST `/api/auth/dev-login` with JSON body `{"github_token": "..."}`
**Expected behavior**:
1. Endpoint accepts `DevLoginRequest` Pydantic model (POST body)
2. No query parameters accepted for credentials
3. Returns `UserResponse` with user info
4. Sets session cookie (same as OAuth flow)

**Postcondition**: No credentials in URL, logs, or history
**Error behavior**: Missing/invalid body → 422 Unprocessable Entity

### Contract C-008: OAuth Minimum Scopes (FR-013)

**Precondition**: User initiates OAuth authorization
**Input**: OAuth authorization URL construction
**Expected behavior**:
1. Scopes requested: `read:user read:org project repo`
2. Code comment documents why `repo` is required
3. No additional scopes beyond what is documented

**Postcondition**: OAuth authorization requests the documented scope set
**Note**: `repo` scope retained per research Decision 8 — GitHub API requires it for issue/PR operations

### Contract C-009: Session Key Minimum Length (FR-014)

**Precondition**: Application startup
**Input**: `SESSION_SECRET_KEY` environment variable
**Expected behavior**:
1. Length validated: `len(session_secret_key) >= 64`
2. If shorter → error appended (in non-debug mode)
3. Error message includes current length and generation command

**Postcondition**: Sessions are signed with a key of sufficient entropy

### Contract C-010: Docker Port Binding (FR-015)

**Precondition**: Docker Compose starts services
**Input**: `docker-compose.yml` port mappings
**Expected behavior**:
1. Backend: `"127.0.0.1:8000:8000"`
2. Frontend: `"127.0.0.1:5173:8080"`
3. No `0.0.0.0` bindings

**Postcondition**: Services accessible only from localhost

---

## Phase 3 — Medium Contracts

### Contract C-011: Rate Limiting (FR-016, FR-017, FR-018)

**Precondition**: Authenticated user sends requests to rate-limited endpoints
**Input**: Repeated requests exceeding threshold
**Expected behavior**:
1. Chat endpoints: 10 requests/minute per user → 429 on excess
2. Agent endpoints: 5 requests/minute per user → 429 on excess
3. Workflow endpoints: 10 requests/minute per user → 429 on excess
4. OAuth callback: 20 requests/minute per IP → 429 on excess

**Postcondition**: Resource exhaustion prevented; legitimate users not impacted

### Contract C-012: Webhook Verification Independence (FR-020)

**Precondition**: Webhook request arrives, regardless of `DEBUG` setting
**Input**: Webhook payload with or without valid signature
**Expected behavior**:
1. If `GITHUB_WEBHOOK_SECRET` is configured: verify signature with `hmac.compare_digest()`
2. If `GITHUB_WEBHOOK_SECRET` is not configured: reject with 401 (do not skip verification)
3. Debug mode has no effect on verification logic

**Postcondition**: Webhooks are always authenticated

### Contract C-013: API Documentation Gate (FR-021)

**Precondition**: Request to `/api/docs` or `/api/redoc`
**Input**: `ENABLE_DOCS` environment variable (default: `false`)
**Expected behavior**:
1. `ENABLE_DOCS=true` → Swagger at `/api/docs`, ReDoc at `/api/redoc`
2. `ENABLE_DOCS=false` or unset → both endpoints return 404
3. `DEBUG` setting has no effect on docs availability

**Postcondition**: API schema not accidentally exposed

### Contract C-014: Database Permissions (FR-022)

**Precondition**: Application creates or accesses database
**Input**: Database path (default: `/var/lib/solune/data/settings.db`)
**Expected behavior**:
1. Directory created with `mode=0o700` and `chmod(0o700)`
2. Database file created with `chmod(0o600)`
3. Permissions re-enforced on database recovery

**Postcondition**: Only the application user can read/write the database

### Contract C-015: CORS Origins Validation (FR-023)

**Precondition**: Application startup with `CORS_ORIGINS` configured
**Input**: Comma-separated origin strings
**Expected behavior**:
1. Each origin trimmed of whitespace
2. Empty entries skipped
3. Each origin validated: scheme ∈ {http, https} AND hostname present
4. Malformed origin → `ValueError` raised with specific error message

**Postcondition**: Only valid origins accepted in CORS configuration

### Contract C-016: Data Volume Mount (FR-024)

**Precondition**: Docker Compose starts backend service
**Input**: Volume mount configuration
**Expected behavior**:
1. Named volume `solune-data` mounted at `/var/lib/solune/data`
2. Database path is absolute: `/var/lib/solune/data/settings.db`
3. No volumes mounted inside the application root directory

**Postcondition**: Runtime data separated from application code

### Contract C-017: Chat History Privacy (FR-025, FR-026)

**Precondition**: User interacts with chat
**Input**: Chat messages
**Expected behavior**:
1. Chat input history stored in React state only (`useState`)
2. No `localStorage.setItem()` calls with message content
3. Legacy localStorage entries cleared via `clearLegacyStorage()`
4. On logout: all React state reset, no residual data

**Postcondition**: No chat content survives logout or page reload

### Contract C-018: Error Message Sanitization (FR-027)

**Precondition**: GitHub GraphQL API returns an error
**Input**: Exception from GitHub API call
**Expected behavior**:
1. Full error details logged server-side: `logger.error("Failed to ...: %s", e)`
2. Client receives generic response: empty dict `{}`, `False`, or sanitized HTTPException
3. No internal query structure, token scopes, or API paths in client response

**Postcondition**: Internal details not leaked to API consumers

---

## Phase 4 — Low Contracts

### Contract C-019: Workflow Permission Minimization (FR-028)

**Precondition**: GitHub Actions workflow execution
**Input**: `branch-issue-link.yml` workflow file
**Expected behavior**:
1. Workflow-level `permissions: {}` (deny by default)
2. Job-level permissions explicitly granted with comments:
   - `issues: write` — required for `gh issue comment`
   - `contents: read` — required for branch detection

**Postcondition**: Workflow has minimum necessary permissions

### Contract C-020: Avatar URL Validation (FR-029)

**Precondition**: Avatar URL from GitHub API rendered in UI
**Input**: `assignee.avatar_url` string
**Expected behavior**:
1. URL parsed with `new URL(url)`
2. Protocol check: `parsed.protocol === 'https:'`
3. Hostname check: `ALLOWED_AVATAR_HOSTS.includes(parsed.hostname)`
4. Allowed hosts: `['avatars.githubusercontent.com']`
5. Invalid URL → inline SVG placeholder returned

**Postcondition**: Only trusted HTTPS avatar URLs rendered
