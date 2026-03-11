# Implementation Plan: Security Review Remediation Program

**Branch**: `001-security-review` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-security-review/spec.md`

## Summary

Systematic remediation of 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across a full-stack FastAPI + React application, organized into 4 priority-phased implementation waves aligned with the OWASP Top 10. Changes span OAuth session handling, startup configuration enforcement, container hardening, project-level authorization, webhook trust verification, HTTP security headers, rate limiting, client-side data privacy, and least-privilege integrations. Each phase is self-contained and deployable independently, with behavioral verification checks replacing line-number-specific audits.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI ≥0.135, Pydantic ≥2.12, cryptography ≥44.0 (Fernet), slowapi ≥0.1.9, aiosqlite ≥0.22, React 19.2, TanStack Query 5.90, Vite 7.3, Zod 4.3
**Storage**: SQLite via aiosqlite (WAL mode, encrypted sessions, migrations 001–020)
**Testing**: pytest + pytest-asyncio (backend), Vitest 4.0 + Playwright 1.58 (frontend)
**Target Platform**: Linux Docker containers (python:3.13-slim backend, nginx:1.27-alpine frontend)
**Project Type**: Web application (backend + frontend + docker-compose orchestration)
**Performance Goals**: No latency regression from security changes; rate limits tuned per-user for write endpoints
**Constraints**: Zero breaking changes to public API contracts; migration path for existing plaintext credentials; users must re-authorize after OAuth scope reduction
**Scale/Scope**: 43K backend LOC, 42K frontend LOC, 18 API route files, 19 model files, 21 migration files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development — **PASS**

The feature has a complete `spec.md` with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each, 25 functional requirements (FR-001–FR-025), 10 measurable success criteria (SC-001–SC-010), explicit scope boundaries, 7 assumptions, and 7 edge cases. No implementation began before specification.

### Principle II: Template-Driven Workflow — **PASS**

All artifacts follow canonical templates: `spec.md` used the spec template, this `plan.md` follows the plan template. Research, data-model, contracts, and quickstart artifacts are generated per the plan-template workflow.

### Principle III: Agent-Orchestrated Execution — **PASS**

Workflow followed: `/speckit.specify` → `/speckit.plan` (this). Each agent produced its defined output before handoff. The plan decomposes into phases with clear deliverables for `/speckit.tasks` to consume.

### Principle IV: Test Optionality with Clarity — **PASS (Tests Required)**

The spec explicitly mandates behavioral verification (10 verification checks in the parent issue). Security changes to authentication, authorization, encryption enforcement, and rate limiting require test coverage to prevent regressions. Existing pytest infrastructure (68 test files) and Vitest infrastructure support this requirement.

### Principle V: Simplicity and DRY — **PASS**

All security changes use existing libraries already in the dependency tree (cryptography, slowapi, hmac stdlib). No new abstractions beyond what is necessary — project authorization is centralized as a shared FastAPI dependency, startup validation extends the existing Pydantic Settings validators. See Complexity Tracking for justified additions.

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file
├── research.md          # Phase 0: security technology decisions & best practices
├── data-model.md        # Phase 1: security entities, middleware, validation models
├── quickstart.md        # Phase 1: developer guide for the security-hardened architecture
├── contracts/           # Phase 1: security contract definitions
│   ├── startup-validation.md
│   ├── project-authorization.md
│   └── rate-limiting.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── config.py                    # Startup validation: encryption, webhook, session, cookie, CORS
│   ├── main.py                      # ENABLE_DOCS toggle independent of DEBUG
│   ├── dependencies.py              # NEW: verify_project_access() shared dependency
│   ├── api/
│   │   ├── auth.py                  # Cookie-based session, POST-only dev login
│   │   ├── tasks.py                 # Add project authorization guard
│   │   ├── projects.py              # Add project authorization guard
│   │   ├── settings.py              # Add project authorization guard
│   │   ├── workflow.py              # Add project authorization guard + rate limiting
│   │   ├── chat.py                  # Rate limiting on AI/write endpoints
│   │   ├── agents.py                # Rate limiting on AI endpoints
│   │   ├── signal.py                # Timing-safe webhook secret comparison
│   │   └── webhooks.py              # Remove debug-conditional signature bypass
│   ├── services/
│   │   ├── encryption.py            # Mandatory encryption in production
│   │   ├── github_auth.py           # Reduced OAuth scopes
│   │   ├── database.py              # 0700/0600 permissions (verify existing)
│   │   └── github_projects/
│   │       └── service.py           # Sanitize GraphQL error messages
│   └── migrations/
│       └── 021_encrypt_existing.sql # Migration path for plaintext credentials
└── tests/
    └── unit/
        ├── test_config_validation.py    # Startup enforcement tests
        ├── test_project_authorization.py # Access control tests
        └── test_webhook_security.py      # Timing-safe + debug-mode tests

frontend/
├── src/
│   ├── hooks/
│   │   ├── useAuth.ts               # Remove URL credential reading
│   │   └── useChatHistory.ts        # ID-only storage, TTL, logout clear
│   └── components/
│       └── board/
│           └── IssueCard.tsx         # Avatar domain validation
├── nginx.conf                        # Full security headers, remove X-XSS-Protection
├── Dockerfile                        # Non-root user (verify existing nginx-app)
docker-compose.yml                    # 127.0.0.1 bindings, external data volume

.github/workflows/
└── branch-issue-link.yml             # Minimize permissions + justification comment
```

**Structure Decision**: Web application structure. Backend and frontend are separate top-level directories. All changes are modifications to existing files — no new top-level directories. The only new files are the project authorization dependency function, migration SQL, and security-focused test files.

## Complexity Tracking

> Potential concerns from Constitution Principle V (Simplicity and DRY)

| Concern | Why Needed | Simpler Alternative Rejected Because |
|---------|------------|-------------------------------------|
| Centralized `verify_project_access()` dependency | FR-007 requires consistent access control across 4+ endpoint files and WebSocket handlers | Per-endpoint inline checks would duplicate the same query and create drift risk |
| Startup validation in `config.py` | FR-003/004/005/015 require 5 new validators that fail-fast on unsafe config | Logging warnings (current behavior) silently permits unsafe production deployments |
| `slowapi` rate limiting decorators on 6+ endpoints | FR-022 requires per-user and per-IP rate limits on expensive endpoints | Manual token-bucket implementation would be more complex and less tested than the existing `slowapi` dependency already in pyproject.toml |
| Migration 021 for plaintext credential remediation | FR-016 requires a migration path for existing unprotected values | Silently ignoring existing plaintext credentials violates the fail-closed principle |

## Implementation Phases

### Phase 1 — Critical (Fix Immediately)

**Objective**: Eliminate the 3 critical vulnerabilities that can compromise every account or deployment.

#### 1.1 Session Token Removal from URL (Finding #1 — OWASP A02)

**Files**: `backend/src/api/auth.py`, `frontend/src/hooks/useAuth.ts`

**Changes**:

- **Backend**: Modify OAuth callback to set session token as an `HttpOnly; SameSite=Strict; Secure` cookie directly on the response, then redirect to frontend with no credentials in the URL
- **Frontend**: Remove any logic that reads `session_token` from URL query parameters; rely solely on the cookie for session state
- **Verification**: After login, no credentials appear in browser URL bar, history, or access logs

#### 1.2 Mandatory Encryption and Webhook Secret at Startup (Finding #2 — OWASP A02)

**Files**: `backend/src/config.py`, `backend/src/services/encryption.py`

**Changes**:

- **config.py**: Add Pydantic `model_validator` that refuses startup when `debug=False` and `encryption_key` is `None` or `github_webhook_secret` is empty
- **encryption.py**: Remove the fallback passthrough mode that allows plaintext storage when no key is set in production
- **Migration**: Add `021_encrypt_existing.sql` with a documented remediation path for existing plaintext rows
- **Verification**: Backend refuses to start in non-debug mode without `ENCRYPTION_KEY` set

#### 1.3 Frontend Container Non-Root User (Finding #3 — OWASP A05)

**Files**: `frontend/Dockerfile`

**Changes**:

- Verify existing `nginx-app` non-root user directive (codebase review confirmed this already exists in the Dockerfile)
- If not present, add `USER` directive with dedicated non-root system user
- **Verification**: `docker exec` into frontend container — `id` must return non-root UID

### Phase 2 — High (This Week)

**Objective**: Close the 7 high-severity access control, webhook trust, and configuration hardening gaps.

#### 2.1 Project-Level Authorization (Finding #4 — OWASP A01)

**Files**: `backend/src/dependencies.py`, `backend/src/api/tasks.py`, `backend/src/api/projects.py`, `backend/src/api/settings.py`, `backend/src/api/workflow.py`

**Changes**:

- **dependencies.py**: Add `verify_project_access(session, project_id)` async dependency that queries project ownership and raises `HTTPException(403)` if the session user does not own the project
- **Endpoint files**: Add `Depends(verify_project_access)` to every route accepting `project_id`
- **WebSocket**: Add authorization check before subscribing to project events
- **Verification**: Authenticated request with unowned `project_id` returns 403; WebSocket to unowned project is rejected before data

#### 2.2 Timing-Safe Webhook Comparison (Finding #5 — OWASP A07)

**Files**: `backend/src/api/signal.py`

**Changes**:

- Replace `!=` string comparison with `hmac.compare_digest()` for Signal webhook secret validation
- Audit all other secret comparisons in the codebase for consistency
- **Verification**: All webhook secret comparisons use constant-time function (code review)

#### 2.3 HTTP Security Headers (Finding #6 — OWASP A05)

**Files**: `frontend/nginx.conf`

**Changes**:

- Verify existing headers (CSP, HSTS, Referrer-Policy, Permissions-Policy already present)
- Remove deprecated `X-XSS-Protection` if present
- Add `server_tokens off` to hide nginx version
- **Verification**: `curl -I frontend` returns all required headers; no nginx version in `Server:` header

#### 2.4 Dev Login POST-Only Credentials (Finding #7 — OWASP A02)

**Files**: `backend/src/api/auth.py`

**Changes**:

- Change dev login endpoint to accept GitHub PAT only in POST request body (JSON), reject query parameter input
- **Verification**: Dev login with URL parameter fails; POST body succeeds

#### 2.5 OAuth Scope Reduction (Finding #8 — OWASP A01)

**Files**: `backend/src/services/github_auth.py`

**Changes**:

- Replace `repo` scope with minimum necessary scopes (`read:org`, `project`, or equivalent narrower scopes)
- Document which write operations were tested and confirmed working with reduced scopes
- **Key Decision**: Users must re-authorize after scope change; test in staging first
- **Verification**: Requested permissions match minimum required for supported project management actions

#### 2.6 Session Secret Minimum Entropy (Finding #9 — OWASP A07)

**Files**: `backend/src/config.py`

**Changes**:

- Add `model_validator` rejecting `session_secret_key` shorter than 64 characters in non-debug mode
- **Verification**: Startup with short key is rejected with clear error

#### 2.7 Docker Loopback Binding (Finding #10 — OWASP A05)

**Files**: `docker-compose.yml`

**Changes**:

- Verify existing `127.0.0.1` binding (codebase review confirmed this already exists)
- Ensure production documentation specifies reverse-proxy-only exposure
- **Verification**: Development ports listen only on loopback addresses

### Phase 3 — Medium (Next Sprint)

**Objective**: Add defense-in-depth controls for rate limiting, data privacy, and configuration hardening.

#### 3.1 Rate Limiting on Expensive Endpoints (Finding #11 — OWASP A04)

**Files**: `backend/src/api/chat.py`, `backend/src/api/agents.py`, `backend/src/api/workflow.py`, `backend/src/api/auth.py`

**Changes**:

- Add `slowapi` rate limit decorators to chat, agent invocation, workflow, and OAuth callback endpoints
- Per-user limits on authenticated write/AI endpoints; per-IP limit on OAuth callback
- **Key Decision**: Per-user limits preferred over per-IP to avoid penalizing shared NAT/VPN users
- **Verification**: After rate limit threshold, expensive endpoints return 429 Too Many Requests

#### 3.2 Cookie Secure Flag Enforcement (Finding #12 — OWASP A02)

**Files**: `backend/src/config.py`

**Changes**:

- Add startup validator: non-debug mode must fail if `cookie_secure` is not `True`
- Remove fragile URL-prefix auto-detection logic
- **Verification**: Startup with `cookie_secure=False` in production is rejected

#### 3.3 Unconditional Webhook Verification (Finding #13 — OWASP A05)

**Files**: `backend/src/api/webhooks.py`

**Changes**:

- Remove debug-mode conditional that skips signature verification
- Require a locally configured test secret for development
- **Verification**: Webhook without valid signature is rejected in both debug and non-debug modes

#### 3.4 API Docs Independent Toggle (Finding #14 — OWASP A05)

**Files**: `backend/src/main.py`

**Changes**:

- Gate Swagger/ReDoc on `ENABLE_DOCS` environment variable instead of `DEBUG`
- **Verification**: API docs are unavailable with `ENABLE_DOCS=false` regardless of `DEBUG` setting

#### 3.5 Database Directory Permissions (Finding #15 — OWASP A02)

**Files**: `backend/src/services/database.py`

**Changes**:

- Verify existing 0700 directory and 0600 file permissions (codebase review confirmed these exist)
- Ensure `os.makedirs()` and file creation use restrictive permissions explicitly
- **Verification**: DB directory permissions are 0700; file permissions are 0600

#### 3.6 CORS Origins Validation (Finding #16 — OWASP A05)

**Files**: `backend/src/config.py`

**Changes**:

- Add `model_validator` that parses each CORS origin, validates URL format (scheme + hostname), and fails on malformed values
- **Verification**: Startup with malformed CORS origin is rejected

#### 3.7 Data Volume Separation (Finding #17 — OWASP A05)

**Files**: `docker-compose.yml`

**Changes**:

- Verify existing volume mount at `/var/lib/ghchat/data` (already outside app root)
- Ensure no `data/` relative mount exists that commingles with application code
- **Verification**: Data volume is mounted outside the application root

#### 3.8 Client-Side Chat History Privacy (Finding #18 — Privacy / OWASP A02)

**Files**: `frontend/src/hooks/useChatHistory.ts`

**Changes**:

- Replace full message body storage with lightweight message ID references
- Add 24-hour TTL with automatic expiration check on read
- Clear all chat-related localStorage data on logout
- **Verification**: After logout, localStorage contains no message content

#### 3.9 GraphQL Error Sanitization (Finding #19 — OWASP A09)

**Files**: `backend/src/services/github_projects/service.py`

**Changes**:

- Wrap GitHub GraphQL API error handling to log full error internally but raise only a generic sanitized message toward the API response
- **Verification**: External service errors return sanitized messages to users

### Phase 4 — Low (Backlog)

**Objective**: Close remaining supply-chain and input validation findings.

#### 4.1 GitHub Actions Permissions (Finding #20 — Supply Chain)

**Files**: `.github/workflows/branch-issue-link.yml`

**Changes**:

- Reduce `issues: write` to minimum needed permission
- Add justification comment for any remaining elevated permissions
- **Verification**: Workflow permissions are minimum necessary with justification

#### 4.2 Avatar URL Domain Validation (Finding #21 — OWASP A03)

**Files**: `frontend/src/components/board/IssueCard.tsx`

**Changes**:

- Add URL validation function: check `https:` protocol and hostname matches `avatars.githubusercontent.com` or other known GitHub avatar domains
- Fall back to a placeholder image on validation failure
- **Verification**: Untrusted avatar URLs render a placeholder instead of loading

## Acceptance Criteria

- [ ] All 3 Critical findings (Phase 1) are remediated with passing verification checks
- [ ] All 7 High findings (Phase 2) are remediated with passing verification checks
- [ ] All 9 Medium findings (Phase 3) are remediated with passing verification checks
- [ ] All 2 Low findings (Phase 4) are remediated with passing verification checks
- [ ] All 10 behavioral verification checks from the parent issue pass
- [ ] Existing test suites pass (backend pytest, frontend Vitest)
- [ ] No new security vulnerabilities introduced (CodeQL scan clean)
- [ ] Migration path documented for existing plaintext credentials
- [ ] OAuth scope reduction tested in staging before rollout
