# Tasks: Security, Privacy & Vulnerability Audit

**Input**: Design documents from `/specs/001-security-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are not explicitly requested in the specification. Verification is behavior-based (code review + inspection per quickstart.md). Existing unit tests (3575 backend, 152 frontend) already cover security controls.

**Organization**: Tasks are grouped by user story to enable independent verification and implementation. Since 17 of 21 findings are already remediated (per research.md), most tasks are verification-focused.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish verification baseline and audit framework

- [ ] T001 Document remediation status matrix mapping each of the 21 findings to codebase evidence in `specs/001-security-review/research.md`
- [ ] T002 [P] Verify existing backend test suite passes: `cd solune/backend && pytest tests/unit/ --timeout=30 -q`
- [ ] T003 [P] Verify existing frontend test suite passes: `cd solune/frontend && npm run test`
- [ ] T004 [P] Verify linting passes: `cd solune/backend && ruff check src tests && ruff format --check src tests`

---

## Phase 2: User Story 1 — Credentials Never Exposed in URLs (Priority: P1) 🎯 MVP

**Goal**: Verify session credentials never appear in browser URLs, history, logs, or Referer headers

**Independent Test**: Log in via OAuth and verify the browser URL, history, and proxy logs contain no credential query parameters

### Verification for User Story 1

- [ ] T005 [P] [US1] Verify OAuth callback sets HttpOnly/SameSite=Strict/Secure cookie in `solune/backend/src/api/auth.py` (FR-001) — inspect lines 22–39 for `httponly=True`, `samesite="strict"`, `secure=settings.effective_cookie_secure`
- [ ] T006 [P] [US1] Verify no credential query parameters in OAuth redirect URL in `solune/backend/src/api/auth.py` (FR-001) — confirm redirect has no `?session_token=` or `?access_token=` params
- [ ] T007 [P] [US1] Verify frontend does not read credentials from URL params in `solune/frontend/src/hooks/useAuth.ts` (FR-002) — confirm no `window.location.search` token extraction
- [ ] T008 [P] [US1] Verify dev-login endpoint uses POST body in `solune/backend/src/api/auth.py` (FR-013) — inspect lines 190–218 for POST method with JSON body

**Checkpoint**: SC-001 validated — no credentials in URLs

---

## Phase 3: User Story 2 — Encryption and Secrets Enforced at Startup (Priority: P1) 🎯 MVP

**Goal**: Verify production startup fails without mandatory secrets

**Independent Test**: Start backend without ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET, or short SESSION_SECRET_KEY — each must fail

### Verification for User Story 2

- [ ] T009 [P] [US2] Verify ENCRYPTION_KEY enforcement in `solune/backend/src/config.py` `_validate_production_secrets()` (FR-003) — lines 128–227
- [ ] T010 [P] [US2] Verify GITHUB_WEBHOOK_SECRET enforcement in `solune/backend/src/config.py` (FR-004)
- [ ] T011 [P] [US2] Verify SESSION_SECRET_KEY ≥64 chars enforcement in `solune/backend/src/config.py` (FR-015)
- [ ] T012 [P] [US2] Verify cookie_secure enforcement in production in `solune/backend/src/config.py` (FR-019)
- [ ] T013 [P] [US2] Verify Fernet encryption applied to OAuth tokens in `solune/backend/src/services/encryption.py` (FR-003)

**Checkpoint**: SC-002 validated — startup refuses without mandatory secrets

---

## Phase 4: User Story 3 — Containers Run as Non-Root (Priority: P1) 🎯 MVP

**Goal**: Verify all containers run as dedicated non-root system users

**Independent Test**: Execute `docker exec <container> id` and verify non-root UID

### Verification for User Story 3

- [ ] T014 [P] [US3] Verify frontend Dockerfile creates non-root user in `solune/frontend/Dockerfile` (FR-005) — inspect USER directive, lines 26–41
- [ ] T015 [P] [US3] Verify nginx runs on non-privileged port 8080 in `solune/frontend/Dockerfile` and `solune/frontend/nginx.conf`

**Checkpoint**: SC-003 validated — non-root containers

---

## Phase 5: User Story 4 — Project Resources Scoped to Authenticated User (Priority: P2)

**Goal**: Verify all project-scoped endpoints enforce ownership checks via centralized dependency

**Independent Test**: Authenticate as User A, attempt to access User B's project — expect 403

### Verification for User Story 4

- [ ] T016 [US4] Verify centralized `verify_project_access()` in `solune/backend/src/dependencies.py` (FR-006, FR-007) — lines 181–206
- [ ] T017 [P] [US4] Verify tasks endpoint uses `verify_project_access` in `solune/backend/src/api/tasks.py` (FR-006)
- [ ] T018 [P] [US4] Verify projects endpoint uses `verify_project_access` in `solune/backend/src/api/projects.py` (FR-006)
- [ ] T019 [P] [US4] Verify settings endpoint uses `verify_project_access` in `solune/backend/src/api/settings.py` (FR-006)
- [ ] T020 [P] [US4] Verify workflow endpoint uses `verify_project_access` in `solune/backend/src/api/workflow.py` (FR-006)
- [ ] T021 [US4] Verify WebSocket verifies project ownership before data transmission in `solune/backend/src/api/workflow.py` (FR-008)

**Checkpoint**: SC-004, SC-005 validated — project access control enforced

---

## Phase 6: User Story 5 — Secure HTTP Headers and Server Hardening (Priority: P2)

**Goal**: Verify nginx serves all required security headers and hides server version

**Independent Test**: `curl -I` frontend and verify headers

### Verification for User Story 5

- [ ] T022 [P] [US5] Verify Content-Security-Policy header in `solune/frontend/nginx.conf` (FR-010)
- [ ] T023 [P] [US5] Verify Strict-Transport-Security header in `solune/frontend/nginx.conf` (FR-010)
- [ ] T024 [P] [US5] Verify Referrer-Policy, Permissions-Policy, X-Content-Type-Options headers in `solune/frontend/nginx.conf` (FR-010)
- [ ] T025 [P] [US5] Verify X-XSS-Protection is NOT present in `solune/frontend/nginx.conf` (FR-011)
- [ ] T026 [P] [US5] Verify `server_tokens off` in `solune/frontend/nginx.conf` (FR-012)

**Checkpoint**: SC-007 validated — security headers complete

---

## Phase 7: User Story 6 — Constant-Time Secret Comparisons (Priority: P2)

**Goal**: Verify all secret/token comparisons use constant-time functions

**Independent Test**: Code review confirms `hmac.compare_digest` or `secrets.compare_digest` throughout

### Verification for User Story 6

- [ ] T027 [P] [US6] Verify Signal webhook uses `hmac.compare_digest` in `solune/backend/src/api/signal.py` (FR-009) — lines 273–274
- [ ] T028 [P] [US6] Verify GitHub webhook uses `hmac.compare_digest` in `solune/backend/src/api/webhooks.py` (FR-009)
- [ ] T029 [P] [US6] Verify CSRF middleware uses `secrets.compare_digest` in `solune/backend/src/middleware/csrf.py` (FR-009)
- [ ] T030 [US6] Audit codebase for any remaining non-constant-time secret comparisons: `grep -rn "!=" solune/backend/src/ | grep -i "secret\|token\|key"`

**Checkpoint**: SC-006 validated — constant-time comparisons

---

## Phase 8: User Story 7 — Minimum OAuth Scopes (Priority: P2)

**Goal**: Document OAuth scope justification (repo scope retained as justified exception per research.md Finding 8)

**Independent Test**: Inspect OAuth authorization URL scopes

### Verification for User Story 7

- [ ] T031 [US7] Verify OAuth scopes configuration and justification comment in `solune/backend/src/services/github_auth.py` (FR-014) — lines 70–74
- [ ] T032 [US7] Document justified exception for `repo` scope: GitHub returns misleading 404s for issue/PR/comment writes with narrower scopes

**Checkpoint**: SC-011 validated — scopes documented with justification

---

## Phase 9: User Story 8 — Network Binding and Service Isolation (Priority: P2)

**Goal**: Verify development services bind to localhost only

**Independent Test**: Inspect docker-compose.yml port bindings

### Verification for User Story 8

- [ ] T033 [P] [US8] Verify backend binds to `127.0.0.1:8000:8000` in `solune/docker-compose.yml` (FR-016)
- [ ] T034 [P] [US8] Verify frontend binds to `127.0.0.1:5173:8080` in `solune/docker-compose.yml` (FR-016)
- [ ] T035 [P] [US8] Verify Signal API uses `expose` (internal only) in `solune/docker-compose.yml` (FR-016)

**Checkpoint**: No direct 0.0.0.0 bindings

---

## Phase 10: User Story 9 — Rate Limiting on Expensive Endpoints (Priority: P3)

**Goal**: Verify rate limiting is applied to all expensive/sensitive endpoints

**Independent Test**: Rapidly call rate-limited endpoint and verify 429 response

### Verification for User Story 9

- [ ] T036 [P] [US9] Verify `RateLimitKeyMiddleware` in `solune/backend/src/middleware/rate_limit.py` (FR-017)
- [ ] T037 [P] [US9] Verify chat endpoint rate limit decorator in `solune/backend/src/api/chat.py` (FR-017) — line 948
- [ ] T038 [P] [US9] Verify agent endpoint rate limit in `solune/backend/src/api/agents.py` (FR-017)
- [ ] T039 [P] [US9] Verify workflow endpoint rate limit in `solune/backend/src/api/workflow.py` (FR-017)
- [ ] T040 [US9] Verify OAuth callback per-IP rate limit in `solune/backend/src/api/auth.py` (FR-018)

**Checkpoint**: SC-008 validated — rate limiting enforced

---

## Phase 11: User Story 10 — Secure Local Data Handling and Logout Cleanup (Priority: P3)

**Goal**: Verify chat messages are memory-only and logout clears all local data

**Independent Test**: Inspect localStorage after chat usage and after logout

### Verification for User Story 10

- [ ] T041 [P] [US10] Verify memory-only chat storage (`useState`) in `solune/frontend/src/hooks/useChatHistory.ts` (FR-025)
- [ ] T042 [P] [US10] Verify `clearLegacyStorage()` removes pre-v2 localStorage data in `solune/frontend/src/hooks/useChatHistory.ts` (FR-026)
- [ ] T043 [US10] Verify `clearHistory()` wipes memory and legacy storage on logout in `solune/frontend/src/hooks/useChatHistory.ts` (FR-026)

**Checkpoint**: SC-009 validated — no message content in localStorage

---

## Phase 12: User Story 11 — Webhook Verification Independent of Debug Mode (Priority: P3)

**Goal**: Verify webhook signature verification is unconditional

**Independent Test**: Start with DEBUG=true, send webhook without valid signature — must be rejected

### Verification for User Story 11

- [ ] T044 [P] [US11] Verify webhook verification is unconditional in `solune/backend/src/api/webhooks.py` (FR-020) — lines 209–240
- [ ] T045 [P] [US11] Verify no DEBUG branching in webhook verification path in `solune/backend/src/api/webhooks.py` (FR-020)

**Checkpoint**: Webhook security independent of debug mode

---

## Phase 13: User Story 12 — Secure Database Permissions and Data Volume Isolation (Priority: P3)

**Goal**: Verify database directory/file permissions and data volume location

**Independent Test**: Inspect permissions and docker-compose volume mount

### Verification for User Story 12

- [ ] T046 [P] [US12] Verify directory `0o700` and file `0o600` permissions in `solune/backend/src/services/database.py` (FR-022) — lines 32–56
- [ ] T047 [P] [US12] Verify data volume mounted at `/var/lib/solune/data` in `solune/docker-compose.yml` (FR-024)

**Checkpoint**: SC-010 validated — correct permissions and volume location

---

## Phase 14: User Story 13 — Secure Configuration Validation (Priority: P3)

**Goal**: Verify CORS origins validation and ENABLE_DOCS toggle

**Independent Test**: Start with malformed CORS origins — must fail

### Verification for User Story 13

- [ ] T048 [P] [US13] Verify CORS origins validation with `urlparse()` in `solune/backend/src/config.py` `cors_origins_list` property (FR-023) — lines 230–248
- [ ] T049 [P] [US13] Verify `ENABLE_DOCS` toggle independent of DEBUG in `solune/backend/src/main.py` (FR-021) — lines 591–592
- [ ] T050 [P] [US13] Verify `enable_docs` defaults to `False` in `solune/backend/src/config.py` (FR-021) — line 95

**Checkpoint**: Configuration validation complete

---

## Phase 15: User Story 14 — Sanitized Error Messages (Priority: P3)

**Goal**: Verify error responses never expose internal details

**Independent Test**: Trigger GraphQL error and verify generic response

### Verification for User Story 14

- [ ] T051 [P] [US14] Verify `handle_service_error()` sanitizes errors in `solune/backend/src/logging_utils.py` (FR-028) — lines 224–267
- [ ] T052 [US14] Audit service files for consistent use of `handle_service_error()` in `solune/backend/src/services/`

**Checkpoint**: SC-012 validated — no internal details in error responses

---

## Phase 16: User Story 15 — Least-Privilege CI Permissions and Safe Avatar Rendering (Priority: P4)

**Goal**: Verify CI permissions and avatar URL validation

**Independent Test**: Inspect workflow permissions and render issue card with non-GitHub avatar

### Verification for User Story 15

- [ ] T053 [P] [US15] Verify scoped permissions with justification comments in `.github/workflows/branch-issue-link.yml` (FR-029)
- [ ] T054 [P] [US15] Verify `validateAvatarUrl()` checks HTTPS and hostname allowlist in `solune/frontend/src/components/IssueCard.tsx` (FR-030)
- [ ] T055 [P] [US15] Verify SVG placeholder fallback for invalid avatar URLs in `solune/frontend/src/components/IssueCard.tsx` (FR-030)

**Checkpoint**: Low-priority controls verified

---

## Phase 17: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all findings

- [ ] T056 Run full backend test suite to confirm no regressions: `cd solune/backend && pytest tests/unit/ --timeout=30 -q`
- [ ] T057 [P] Run full frontend test suite: `cd solune/frontend && npm run test`
- [ ] T058 [P] Run backend linting: `cd solune/backend && ruff check src tests && ruff format --check src tests`
- [ ] T059 Run quickstart.md verification checklist (all 12 verification steps per `specs/001-security-review/quickstart.md`)
- [ ] T060 Produce final remediation status report confirming all 21 findings addressed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — establish baseline
- **User Stories (Phases 2–16)**: Depend on Phase 1 setup completion
  - P1 stories (Phases 2–4) can run in parallel
  - P2 stories (Phases 5–9) can run in parallel after P1
  - P3 stories (Phases 10–15) can run in parallel after P2
  - P4 story (Phase 16) can run after P3
- **Polish (Phase 17)**: Depends on all user stories being verified

### User Story Dependencies

- **US1–US3 (P1)**: Independent of each other — can verify in parallel
- **US4–US8 (P2)**: Independent of each other — can verify in parallel
- **US9–US14 (P3)**: Independent of each other — can verify in parallel
- **US15 (P4)**: Independent — can verify anytime after setup

### Parallel Opportunities

- All tasks marked [P] within a phase can run in parallel
- User stories within the same priority tier can run in parallel
- Backend and frontend verification tasks are always parallelizable

---

## Notes

- 17 of 21 original findings are already remediated (per research.md)
- Finding 8 (OAuth scopes) is a documented justified exception — `repo` scope retained
- Primary work is behavioral verification, not new implementation
- Existing test suites (3575 backend unit, 152 frontend) provide regression safety
- Commit after each verification phase checkpoint
