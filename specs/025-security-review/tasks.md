# Tasks: Security, Privacy & Vulnerability Audit

**Input**: Design documents from `/specs/025-security-review/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/security-contracts.md, quickstart.md

**Tests**: New tests warranted for security-critical paths (startup validation, access control, rate limiting) as specified in the plan and spec acceptance scenarios.

**Organization**: Tasks grouped by user story (12 stories, P1–P4). US1–US3 are Critical (P1), US4–US8 are High (P2), US9–US11 are Medium (P3), US12 is Low (P4). Most stories are independent after the Foundational phase completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Install new dependencies required by later phases

- [ ] T001 Add slowapi dependency to backend/pyproject.toml

**Checkpoint**: New dependency available for rate limiting tasks in US9

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Centralized startup security validators that multiple user stories depend on

**⚠️ CRITICAL**: Config validation changes affect how the app starts. US2, US9, and US11 depend on these validators and config fields being in place.

- [ ] T002 Add ENABLE_DOCS bool field (default=false) and model_validator for production security checks (ENCRYPTION_KEY required, GITHUB_WEBHOOK_SECRET required, SESSION_SECRET_KEY ≥64 chars, cookie_secure enforced, CORS origins format validation) in backend/src/config.py
- [ ] T003 [P] Add startup security validation tests (missing ENCRYPTION_KEY, missing GITHUB_WEBHOOK_SECRET, short SESSION_SECRET_KEY, malformed CORS origins, cookie_secure not set) in backend/tests/unit/test_config_security.py

**Checkpoint**: Foundation ready — all startup security gates enforced. User story implementation can now begin.

---

## Phase 3: User Story 1 — Credential Leak Prevention (Priority: P1) 🎯 MVP

**Goal**: Eliminate all credential exposure in URLs across OAuth and dev-login flows

**Independent Test**: Complete a full OAuth login flow and verify no session token or credential appears in the browser URL bar, browser history, or as a URL query parameter at any point. Verify dev-login only accepts POST with JSON body.

### Implementation for User Story 1

- [ ] T004 [US1] Modify OAuth callback to set HttpOnly/SameSite=Strict/Secure cookie on redirect response and remove session_token from redirect URL in backend/src/api/auth.py
- [ ] T005 [US1] Convert dev-login endpoint from GET with query parameter to POST with JSON request body (Pydantic model) in backend/src/api/auth.py
- [ ] T006 [P] [US1] Remove URL parameter credential reading (window.location.search for session_token) and switch to cookie-only session check in frontend/src/hooks/useAuth.ts

**Checkpoint**: After login, no credentials appear in browser URL bar, history, or access logs. Dev-login accepts POST body only. (Verification Check #1)

---

## Phase 4: User Story 2 — Encryption & Secret Enforcement at Startup (Priority: P1)

**Goal**: Ensure the application never operates with missing encryption keys or stores tokens in plaintext

**Independent Test**: Attempt to start the backend in non-debug mode without ENCRYPTION_KEY set — verify startup failure with explicit error. Verify encrypt() always produces ciphertext, never plaintext passthrough. Verify decrypt() still handles legacy plaintext rows for migration.

### Implementation for User Story 2

- [ ] T007 [US2] Remove plaintext passthrough in encrypt(), raise RuntimeError when encryption unavailable, and retain legacy plaintext detection in decrypt() for migration in backend/src/services/encryption.py

**Checkpoint**: Backend refuses to start without ENCRYPTION_KEY in non-debug mode. Encryption service never stores plaintext. Legacy rows migrated on read. (Verification Check #2)

---

## Phase 5: User Story 3 — Container Security Hardening (Priority: P1)

**Goal**: All containers run as non-root dedicated users

**Independent Test**: Build and run the frontend container, execute `id` inside it — verify UID is non-zero (nginx user). Verify nginx serves requests correctly under the non-root user.

### Implementation for User Story 3

- [ ] T008 [US3] Add non-root USER directive (nginx user), configure ownership for cache/run directories, and change EXPOSE to 8080 in frontend/Dockerfile
- [ ] T009 [P] [US3] Update nginx listen directive from port 80 to 8080 (unprivileged port) in frontend/nginx.conf
- [ ] T010 [US3] Update frontend port mapping from 5173:80 to 5173:8080 in docker-compose.yml

**Checkpoint**: `docker exec <frontend> id` returns non-root UID. nginx serves correctly on port 8080. (Verification Check #3)

---

## Phase 6: User Story 4 — Project-Level Access Control (Priority: P2)

**Goal**: Every endpoint accepting a project_id verifies the authenticated user has access before performing any action

**Independent Test**: Authenticate as User A, create a project. Authenticate as User B, attempt to access User A's project via tasks, settings, workflow, and WebSocket endpoints — all must return 403 Forbidden.

### Implementation for User Story 4

- [ ] T011 [US4] Create centralized require_project_access() FastAPI dependency that verifies session user owns the target project (returns 403 if denied) in backend/src/dependencies.py
- [ ] T012 [P] [US4] Add require_project_access dependency to task creation and listing endpoints in backend/src/api/tasks.py
- [ ] T013 [P] [US4] Add require_project_access dependency to project endpoints in backend/src/api/projects.py
- [ ] T014 [P] [US4] Add require_project_access dependency to settings endpoints in backend/src/api/settings.py
- [ ] T015 [P] [US4] Add require_project_access dependency to workflow operation endpoints in backend/src/api/workflow.py
- [ ] T016 [US4] Add project authorization tests (unowned project returns 403, WebSocket rejected before data sent) in backend/tests/unit/test_project_auth.py

**Checkpoint**: Any authenticated request with an unowned project_id returns 403, not success. WebSocket connections to unowned projects are rejected. (Verification Checks #4, #5)

---

## Phase 7: User Story 5 — Secure HTTP Headers & Server Hardening (Priority: P2)

**Goal**: Frontend responses include all required security headers and expose no server version information

**Independent Test**: `curl -sI http://localhost:5173/` returns Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy headers. X-XSS-Protection is absent. Server header does not disclose nginx version.

### Implementation for User Story 5

- [ ] T017 [US5] Add Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy headers; remove X-XSS-Protection; add server_tokens off in frontend/nginx.conf

**Checkpoint**: All four required security headers present. No nginx version in Server header. X-XSS-Protection removed. (Verification Check #7)

---

## Phase 8: User Story 6 — Constant-Time Secret Comparison (Priority: P2)

**Goal**: All secret/token comparisons use constant-time algorithms to prevent timing side-channel attacks

**Independent Test**: Code review all secret comparison call sites — verify each uses hmac.compare_digest.

### Implementation for User Story 6

- [ ] T018 [US6] Replace string equality (!=) with hmac.compare_digest for Signal webhook secret comparison in backend/src/api/signal.py

**Checkpoint**: All webhook secret comparisons use constant-time function. (Verification Check #6)

---

## Phase 9: User Story 7 — OAuth Scope Minimization (Priority: P2)

**Goal**: OAuth authorization requests use minimum necessary scopes — no full repo access

**Independent Test**: Initiate OAuth flow and inspect authorization URL — verify scope parameter does not include `repo`. Verify all application operations still work with narrower scopes.

### Implementation for User Story 7

- [ ] T019 [US7] Remove `repo` scope from OAuth authorization URL parameters, keeping only `read:user read:org project` in backend/src/services/github_auth.py

**Checkpoint**: OAuth authorization URL no longer requests repo scope. (Verification Check per SC-011)

---

## Phase 10: User Story 8 — Network Binding & Docker Hardening (Priority: P2)

**Goal**: Docker services bind to localhost only in development; data volumes mount outside application root

**Independent Test**: Inspect docker-compose.yml — verify all port bindings use 127.0.0.1 prefix. Verify data volume mounts to /var/lib/ghchat/data.

### Implementation for User Story 8

- [ ] T020 [US8] Bind backend and frontend ports to 127.0.0.1, move data volume mount from ./data to /var/lib/ghchat/data in docker-compose.yml
- [ ] T021 [P] [US8] Update default database directory path in backend/src/config.py to /var/lib/ghchat/data (if hardcoded)

**Checkpoint**: Services bind to localhost only. Data volumes isolated from application root.

---

## Phase 11: User Story 9 — Rate Limiting on Sensitive Endpoints (Priority: P3)

**Goal**: Expensive and sensitive endpoints enforce per-user or per-IP rate limits, returning 429 when exceeded

**Independent Test**: Send 35 rapid requests to a rate-limited endpoint — first ~30 return success, remaining return 429 Too Many Requests.

### Implementation for User Story 9

- [ ] T022 [US9] Configure slowapi Limiter with per-user key function (extract user ID from session, fallback to IP) and add rate limit exception handler in backend/src/main.py
- [ ] T023 [P] [US9] Add @limiter.limit("30/minute") per-user rate limit to chat message endpoints in backend/src/api/chat.py
- [ ] T024 [P] [US9] Add @limiter.limit("30/minute") per-user rate limit to agent invocation endpoints in backend/src/api/agents.py
- [ ] T025 [P] [US9] Add @limiter.limit("20/minute") per-user rate limit to workflow operation endpoints in backend/src/api/workflow.py
- [ ] T026 [US9] Add @limiter.limit("10/minute", key_func=get_remote_address) per-IP rate limit to OAuth callback endpoint in backend/src/api/auth.py

**Checkpoint**: Rate-limited endpoints return 429 after exceeding configured thresholds. (Verification Check #8)

---

## Phase 12: User Story 10 — Secure Data Storage & Privacy (Priority: P3)

**Goal**: Chat history stored as lightweight references with TTL; database files have restrictive permissions; all local data cleared on logout

**Independent Test**: After logout, `localStorage.getItem('chat-message-history')` returns null. Database directory has 0700 permissions, file has 0600.

### Implementation for User Story 10

- [ ] T027 [P] [US10] Set database directory permissions to 0700 and file permissions to 0600 after creation in backend/src/services/database.py
- [ ] T028 [US10] Replace full message content storage with lightweight ID references ({id, timestamp}) with 24h TTL, add expired entry pruning, and clear all localStorage on logout in frontend/src/hooks/useChatHistory.ts

**Checkpoint**: No message content in localStorage after logout. DB directory 0700, file 0600. (Verification Checks #9, #10)

---

## Phase 13: User Story 11 — Configuration Validation & Debug Isolation (Priority: P3)

**Goal**: Debug mode cannot bypass security controls; configuration validated at startup; API docs decoupled from debug flag; error messages sanitized

**Independent Test**: Start with DEBUG=true and no webhook secret — webhook requests are still verified (not bypassed). Set ENABLE_DOCS=false with DEBUG=true — docs endpoint returns 404. Trigger a GraphQL error — API response contains only generic message, not internal details.

### Implementation for User Story 11

- [ ] T029 [US11] Remove debug-mode bypass branch for webhook signature verification (always require configured secret) in backend/src/api/webhooks.py
- [ ] T030 [P] [US11] Gate API docs (docs_url, redoc_url) on settings.enable_docs instead of settings.debug in backend/src/main.py
- [ ] T031 [P] [US11] Sanitize GraphQL error messages — log full error internally, raise generic message toward API response in backend/src/services/github_projects/service.py

**Checkpoint**: Webhook verification never bypassed. Docs decoupled from DEBUG. GraphQL errors sanitized.

---

## Phase 14: User Story 12 — Supply Chain & Injection Safeguards (Priority: P4)

**Goal**: Minimize CI workflow permissions; validate external avatar URLs before rendering

**Independent Test**: Review branch-issue-link.yml — permissions scoped to minimum with justification comment. Render IssueCard with a non-GitHub avatar URL — placeholder image displayed instead.

### Implementation for User Story 12

- [ ] T032 [P] [US12] Scope workflow permissions to minimum needed (issues: write, contents: read) with justification comment in .github/workflows/branch-issue-link.yml
- [ ] T033 [P] [US12] Add avatar URL validation (HTTPS + known GitHub avatar domains) with fallback to placeholder image in frontend/src/components/board/IssueCard.tsx

**Checkpoint**: Workflow permissions minimized. Avatar URLs validated and sanitized.

---

## Phase 15: Polish & Cross-Cutting Concerns

**Purpose**: Regression verification and final validation across all stories

- [ ] T034 Run full backend test suite as regression gate: `cd backend && pytest`
- [ ] T035 [P] Run full frontend test suite as regression gate: `cd frontend && npm run test`
- [ ] T036 [P] Run backend lint and type check: `cd backend && ruff check src/ && pyright src/`
- [ ] T037 [P] Run frontend lint and type check: `cd frontend && npx eslint . && npx tsc --noEmit`
- [ ] T038 Run quickstart.md verification commands against staging environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS User Stories 2 and 11 (config.py validators)
- **User Stories (Phases 3–14)**: Most depend only on Foundational phase completion
  - US1 (P1): Independent after Foundational
  - US2 (P1): Depends on Foundational (config validators enforce ENCRYPTION_KEY)
  - US3 (P1): Independent — can start immediately after Setup
  - US4 (P2): Independent after Foundational
  - US5 (P2): Depends on US3 completing nginx.conf port change (same file)
  - US6 (P2): Independent — no shared files
  - US7 (P2): Independent — no shared files
  - US8 (P2): Depends on US3 completing docker-compose.yml port mapping (same file)
  - US9 (P3): Depends on Setup (slowapi dependency) and Foundational (main.py limiter setup)
  - US10 (P3): Independent — no shared files
  - US11 (P3): Depends on Foundational (config.py ENABLE_DOCS field)
  - US12 (P4): Independent — no shared files
- **Polish (Phase 15)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — No dependencies on other stories
- **US2 (P1)**: Can start after Foundational — No dependencies on other stories
- **US3 (P1)**: Can start after Setup — No dependencies on other stories
- **US4 (P2)**: Can start after Foundational — Independent of all other stories
- **US5 (P2)**: Should follow US3 (both modify nginx.conf) — otherwise independent
- **US6 (P2)**: Fully independent — can start after Setup
- **US7 (P2)**: Fully independent — can start after Setup
- **US8 (P2)**: Should follow US3 (both modify docker-compose.yml) — otherwise independent
- **US9 (P3)**: Depends on Setup (T001) and Foundational — otherwise independent
- **US10 (P3)**: Fully independent — can start after Setup
- **US11 (P3)**: Depends on Foundational (T002 adds ENABLE_DOCS) — otherwise independent
- **US12 (P4)**: Fully independent — can start anytime

### Within Each User Story

- Models/entities before services
- Services before endpoints
- Core implementation before integration
- Tests validate the story independently
- Commit after each task or logical group

### Parallel Opportunities

- US1, US2, US3 (all P1) can proceed in parallel — they modify different files
- US4, US5, US6, US7 (all P2) can largely proceed in parallel after US3 completes
- US9, US10, US11 (all P3) can proceed in parallel
- US12 (P4) is fully independent and can be worked on anytime
- Within US4: T012, T013, T014, T015 can all run in parallel (different endpoint files)
- Within US9: T023, T024, T025 can all run in parallel (different endpoint files)

---

## Parallel Example: User Story 4 (Project-Level Access Control)

```bash
# First: Create the centralized dependency (blocking)
Task T011: "Create require_project_access() dependency in backend/src/dependencies.py"

# Then: Apply to all endpoints in parallel
Task T012: "Add project auth to backend/src/api/tasks.py"
Task T013: "Add project auth to backend/src/api/projects.py"
Task T014: "Add project auth to backend/src/api/settings.py"
Task T015: "Add project auth to backend/src/api/workflow.py"
```

## Parallel Example: User Story 9 (Rate Limiting)

```bash
# First: Configure the limiter in main.py (blocking)
Task T022: "Configure slowapi Limiter in backend/src/main.py"

# Then: Decorate all endpoints in parallel
Task T023: "Rate limit chat in backend/src/api/chat.py"
Task T024: "Rate limit agents in backend/src/api/agents.py"
Task T025: "Rate limit workflow in backend/src/api/workflow.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 — Critical Fixes)

1. Complete Phase 1: Setup (add slowapi dependency)
2. Complete Phase 2: Foundational (config validators)
3. Complete Phase 3: US1 — Credential Leak Prevention
4. Complete Phase 4: US2 — Encryption Enforcement
5. Complete Phase 5: US3 — Container Hardening
6. **STOP and VALIDATE**: Run Verification Checks #1, #2, #3
7. Deploy if critical fixes are needed urgently

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 + US2 + US3 (P1 Critical) → Test independently → Deploy (Critical MVP!)
3. US4 + US5 + US6 + US7 + US8 (P2 High) → Test independently → Deploy
4. US9 + US10 + US11 (P3 Medium) → Test independently → Deploy
5. US12 (P4 Low) → Test independently → Deploy
6. Each severity tier adds security value without breaking previous fixes

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (auth.py, useAuth.ts) + US4 (dependencies.py, endpoint files)
   - Developer B: US2 (encryption.py) + US5 (nginx.conf) + US6 (signal.py)
   - Developer C: US3 (Dockerfile, docker-compose.yml) + US7 (github_auth.py) + US8 (docker-compose.yml — must follow US3 due to shared file)
3. ⚠️ Note: US3 and US8 both modify docker-compose.yml; US3 and US5 both modify nginx.conf — schedule these sequentially within the same developer
4. Medium/Low priority stories assigned as capacity frees up

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 38 |
| Phases | 15 (Setup, Foundational, 12 User Stories, Polish) |
| User stories | 12 (3 Critical, 5 High, 3 Medium, 1 Low) |
| Audit findings covered | 21/21 |
| Files modified (backend) | ~15 |
| Files modified (frontend) | ~5 |
| Files modified (infra) | 3 (Dockerfile, nginx.conf, docker-compose.yml) |
| Files modified (CI) | 1 (branch-issue-link.yml) |
| New dependency | 1 (slowapi) |
| Parallel opportunities | US1/US2/US3 in parallel; US4 endpoint tasks in parallel; US9 endpoint tasks in parallel; US12 tasks in parallel |
| Suggested MVP scope | US1 + US2 + US3 (Critical fixes — Phases 1–5) |

### Tasks Per User Story

| Story | Priority | Tasks | Key Files |
|-------|----------|-------|-----------|
| US1 | P1 | T004–T006 (3) | auth.py, useAuth.ts |
| US2 | P1 | T007 (1) | encryption.py |
| US3 | P1 | T008–T010 (3) | Dockerfile, nginx.conf, docker-compose.yml |
| US4 | P2 | T011–T016 (6) | dependencies.py, tasks.py, projects.py, settings.py, workflow.py |
| US5 | P2 | T017 (1) | nginx.conf |
| US6 | P2 | T018 (1) | signal.py |
| US7 | P2 | T019 (1) | github_auth.py |
| US8 | P2 | T020–T021 (2) | docker-compose.yml, config.py |
| US9 | P3 | T022–T026 (5) | main.py, chat.py, agents.py, workflow.py, auth.py |
| US10 | P3 | T027–T028 (2) | database.py, useChatHistory.ts |
| US11 | P3 | T029–T031 (3) | webhooks.py, main.py, service.py |
| US12 | P4 | T032–T033 (2) | branch-issue-link.yml, IssueCard.tsx |
| Setup | — | T001 (1) | pyproject.toml |
| Foundational | — | T002–T003 (2) | config.py, test_config_security.py |
| Polish | — | T034–T038 (5) | Regression + verification |

### Independent Test Criteria Per Story

| Story | Independent Test |
|-------|-----------------|
| US1 | No credentials in browser URL, history, or logs after OAuth login |
| US2 | Backend fails to start without ENCRYPTION_KEY in non-debug mode |
| US3 | `docker exec <frontend> id` returns non-root UID |
| US4 | Request with unowned project_id returns 403 |
| US5 | `curl -sI` returns all required security headers |
| US6 | All secret comparisons use hmac.compare_digest (code review) |
| US7 | OAuth URL does not include `repo` scope |
| US8 | docker-compose.yml binds to 127.0.0.1; volume at /var/lib/ghchat/data |
| US9 | Rapid requests return 429 after exceeding threshold |
| US10 | localStorage empty after logout; DB permissions 0700/0600 |
| US11 | Webhook verification active in debug mode; docs gated on ENABLE_DOCS |
| US12 | Workflow permissions scoped; non-GitHub avatar shows placeholder |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Config.py is modified in Foundational (T002) and US8 (T021) — ensure T002 completes first
- nginx.conf is modified in US3 (T009) and US5 (T017) — US5 should follow US3
- docker-compose.yml is modified in US3 (T010) and US8 (T020) — US8 should follow US3
- main.py is modified in US9 (T022 — adds slowapi limiter/handler) and US11 (T030 — changes docs_url/redoc_url gating) — these are independent sections of the same file, but should be coordinated if worked on in parallel to avoid merge conflicts
- auth.py is modified in US1 (T004, T005) and US9 (T026) — US9 adds rate limit decorator to existing endpoint
