# Tasks: Security, Privacy & Vulnerability Audit

**Input**: Design documents from `/specs/001-security-review/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. The 10-item behavior-based verification matrix (spec.md) serves as acceptance criteria. No test tasks are generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and verification of each story. Most findings (~19/21) are already remediated — tasks focus on closing remaining gaps and performing comprehensive verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app (monorepo)**: `solune/backend/src/`, `solune/frontend/src/`
- **Config/infra**: `docker-compose.yml`, `solune/frontend/nginx.conf`, `solune/frontend/Dockerfile`, `solune/backend/Dockerfile`
- **Specs**: `specs/001-security-review/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization required — this is a hardening exercise on an existing codebase. Setup phase ensures the working environment is ready for verification and targeted fixes.

- [ ] T001 Review current codebase state against the 21-finding audit matrix in specs/001-security-review/research.md
- [ ] T002 [P] Verify backend development environment runs successfully via `cd solune/backend && python -m pytest tests/ -v`
- [ ] T003 [P] Verify frontend development environment builds successfully via `cd solune/frontend && npm run build`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new foundational infrastructure needed — all security primitives (Fernet encryption, slowapi rate limiting, verify_project_access dependency, cookie-based sessions) are already in place. This phase is intentionally empty.

**⚠️ CRITICAL**: All foundational security infrastructure already exists. Proceed directly to user story phases.

**Checkpoint**: Foundation confirmed ready — user story verification and gap-closing can begin.

---

## Phase 3: User Story 1 — Secure Authentication Flow (Priority: P1) 🎯 MVP

**Goal**: Verify session credentials never appear in browser URL bar, history, or access logs. Confirm dev login endpoint accepts credentials via POST body only.

**Independent Test**: Complete an OAuth login flow and verify no credentials appear in the browser URL at any point. Inspect browser history and network requests to confirm tokens are never transmitted as URL parameters.

**Findings**: #1 (Critical, ✅ Remediated), #7 (High, 🔍 Verify)

### Implementation for User Story 1

- [ ] T004 [US1] Verify OAuth callback in solune/backend/src/api/auth.py sets HttpOnly; SameSite=Strict; Secure cookie and redirects with no credentials in URL (Finding #1 — code review, confirm remediation)
- [ ] T005 [P] [US1] Verify solune/frontend/src/hooks/useAuth.ts cleans OAuth callback URL via history.replaceState and never reads credentials from URL params (Finding #1 — code review, confirm remediation)
- [ ] T006 [US1] Verify dev login endpoint in solune/backend/src/api/auth.py accepts credentials via POST JSON body only, not URL query parameters (Finding #7 — code review; if URL params accepted, migrate to POST body)
- [ ] T007 [US1] Verify dev login contract matches specs/001-security-review/contracts/security-contracts.md: POST /api/v1/auth/dev/login with JSON body, endpoint absent when DEBUG=false

**Checkpoint**: User Story 1 verified — authentication flow is secure, no credentials in URLs.

---

## Phase 4: User Story 2 — Mandatory Encryption and Secret Enforcement (Priority: P1)

**Goal**: Ensure the application refuses to start in production mode when critical security configuration is missing or invalid. Close the remaining gap: invalid encryption key silent fallback.

**Independent Test**: Attempt to start the application in production mode without setting the encryption key, with an invalid encryption key, without webhook secret, or with a short session key. Verify startup fails with a clear error message for each case.

**Findings**: #2 (Critical, ⚠️ Partial), #9 (High, ✅ Remediated)

### Implementation for User Story 2

- [ ] T008 [US2] Harden invalid encryption key handling in solune/backend/src/services/encryption.py — in production mode (DEBUG=false), an invalid ENCRYPTION_KEY (set but not a valid Fernet key) must raise ValueError at startup instead of silently falling back to plaintext (Finding #2 gap)
- [ ] T009 [US2] Verify solune/backend/src/config.py enforces mandatory ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET, SESSION_SECRET_KEY (≥64 chars), and COOKIE_SECURE in non-debug mode (Finding #2, #9 — code review, confirm remediation)
- [ ] T010 [P] [US2] Verify startup validation contract matches specs/001-security-review/contracts/security-contracts.md: all required env vars validated, CORS origins validated as well-formed URLs

**Checkpoint**: User Story 2 complete — production startup gate enforces all mandatory security configuration including invalid key detection.

---

## Phase 5: User Story 3 — Project-Level Access Control (Priority: P1)

**Goal**: Verify every endpoint and WebSocket connection accepting a project_id checks that the authenticated user owns the project before performing any action.

**Independent Test**: As User A, create a project. As User B, attempt to access User A's project via API. Verify 403 Forbidden is returned for all project-scoped operations.

**Findings**: #4 (High, ✅ Remediated)

### Implementation for User Story 3

- [ ] T011 [P] [US3] Verify solune/backend/src/api/tasks.py uses Depends(verify_project_access) on all project-scoped endpoints (Finding #4 — code review)
- [ ] T012 [P] [US3] Verify solune/backend/src/api/projects.py uses Depends(verify_project_access) on all project-scoped endpoints (Finding #4 — code review)
- [ ] T013 [P] [US3] Verify solune/backend/src/api/settings.py uses Depends(verify_project_access) on all project-scoped endpoints (Finding #4 — code review)
- [ ] T014 [P] [US3] Verify solune/backend/src/api/workflow.py uses Depends(verify_project_access) on all project-scoped endpoints (Finding #4 — code review)
- [ ] T015 [US3] Verify WebSocket handler rejects connections to unowned project IDs before sending any data frame (Finding #4 — code review, check close code 4003)

**Checkpoint**: User Story 3 verified — all project-scoped operations enforce ownership checks.

---

## Phase 6: User Story 4 — Container and Infrastructure Hardening (Priority: P2)

**Goal**: Verify all containers run as non-root, services bind to localhost only, data volumes are mounted outside app root, and database permissions are restrictive.

**Independent Test**: Inspect running containers for non-root user, check port bindings are localhost-only, verify data directory/file permissions.

**Findings**: #3 (Critical, ✅ Remediated), #10 (High, ✅ Remediated), #15 (Medium, ✅ Remediated), #17 (Medium, ✅ Remediated)

### Implementation for User Story 4

- [ ] T016 [P] [US4] Verify solune/frontend/Dockerfile creates a non-root user (nginx-app) and runs nginx on unprivileged port 8080 (Finding #3 — code review)
- [ ] T017 [P] [US4] Verify solune/backend/Dockerfile runs as non-root appuser (Finding #3 — code review)
- [ ] T018 [P] [US4] Verify docker-compose.yml binds backend to 127.0.0.1:8000 and frontend to 127.0.0.1:5173 (Finding #10 — code review)
- [ ] T019 [P] [US4] Verify docker-compose.yml mounts data volume at /var/lib/solune/data via solune-data named volume, outside application root (Finding #17 — code review)
- [ ] T020 [P] [US4] Verify solune/backend/src/services/database.py creates database directory with 0o700 and database files with 0o600 permissions (Finding #15 — code review)

**Checkpoint**: User Story 4 verified — containers are hardened, infrastructure follows least privilege.

---

## Phase 7: User Story 5 — HTTP Security Headers and Webhook Integrity (Priority: P2)

**Goal**: Verify all required security headers are present in nginx responses, no version disclosure, all secret comparisons use constant-time functions, and webhook verification is never bypassed.

**Independent Test**: Send HTTP HEAD to frontend and verify all headers present. Review code for constant-time comparisons and debug-independent webhook verification.

**Findings**: #5 (High, ✅ Remediated), #6 (High, ⚠️ Partial), #13 (Medium, ✅ Remediated)

### Implementation for User Story 5

- [ ] T021 [US5] Add explicit `server_tokens off;` directive to solune/frontend/nginx.conf in the server block — do not rely on alpine defaults (Finding #6 gap)
- [ ] T022 [P] [US5] Verify solune/frontend/nginx.conf includes Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy, X-Frame-Options, X-Content-Type-Options headers and does NOT include deprecated X-XSS-Protection (Finding #6 — code review)
- [ ] T023 [P] [US5] Verify solune/backend/src/api/signal.py uses hmac.compare_digest for secret comparison (Finding #5 — code review)
- [ ] T024 [P] [US5] Verify solune/backend/src/api/webhooks.py enforces HMAC-SHA256 signature verification regardless of DEBUG mode (Finding #13 — code review)

**Checkpoint**: User Story 5 complete — security headers hardened, webhook integrity confirmed.

---

## Phase 8: User Story 6 — Rate Limiting on Sensitive Endpoints (Priority: P3)

**Goal**: Verify rate limits are applied to all sensitive endpoints (chat, agents, workflow, OAuth callback). Add missing rate limit decorators if any are found.

**Independent Test**: Send requests exceeding the rate limit threshold and verify 429 Too Many Requests response.

**Findings**: #11 (Medium, ⚠️ Partial)

### Implementation for User Story 6

- [ ] T025 [US6] Verify solune/backend/src/middleware/rate_limit.py is properly configured with slowapi and per-user/per-IP key functions (Finding #11 — code review)
- [ ] T026 [P] [US6] Audit solune/backend/src/api/chat.py for rate limit decorators on all message-sending endpoints (Finding #11 — add @limiter.limit() if missing)
- [ ] T027 [P] [US6] Audit solune/backend/src/api/agents.py for rate limit decorators on agent invocation endpoints (Finding #11 — add @limiter.limit() if missing)
- [ ] T028 [P] [US6] Audit solune/backend/src/api/workflow.py for rate limit decorators on workflow trigger endpoints (Finding #11 — add @limiter.limit() if missing)
- [ ] T029 [US6] Audit solune/backend/src/api/auth.py for per-IP rate limit on OAuth callback endpoint (Finding #11 — add @limiter.limit() if missing)

**Checkpoint**: User Story 6 complete — all sensitive endpoints have rate limits applied.

---

## Phase 9: User Story 7 — Privacy-Respecting Client-Side Storage (Priority: P3)

**Goal**: Verify chat message content is not stored in localStorage, only lightweight references are kept in memory, and all local data is cleared on logout.

**Independent Test**: Log in, use chat, log out. Inspect localStorage to confirm no message content remains.

**Findings**: #18 (Medium, ✅ Remediated)

### Implementation for User Story 7

- [ ] T030 [US7] Verify solune/frontend/src/hooks/useChatHistory.ts stores messages in React state only (in-memory), not localStorage — localStorage may contain only lightweight message IDs with bounded history (max 100, FIFO) (Finding #18 — code review)
- [ ] T031 [US7] Verify solune/frontend/src/hooks/useChatHistory.ts clears all local data on logout, including legacy localStorage entries (Finding #18 — code review)

**Checkpoint**: User Story 7 verified — client-side storage is privacy-respecting.

---

## Phase 10: User Story 8 — Secure Configuration and Error Handling (Priority: P3)

**Goal**: Verify CORS validation, error message sanitization, API docs toggle, OAuth scope documentation, avatar URL validation, and CI/CD permissions.

**Independent Test**: Start with malformed CORS origin (fails), trigger upstream API error (generic message), verify API docs controlled by ENABLE_DOCS.

**Findings**: #8 (High, ⚠️ Known limitation), #12 (Medium, ✅ Remediated), #14 (Medium, ✅ Remediated), #16 (Medium, ✅ Remediated), #19 (Medium, ✅ Remediated), #20 (Low, ✅ Remediated), #21 (Low, ✅ Remediated)

### Implementation for User Story 8

- [ ] T032 [US8] Add explanatory comment in solune/backend/src/services/github_auth.py near the OAuth scope definition documenting why `repo` scope is still required (GitHub Projects V2 needs it for issue writes) and noting it as a known limitation (Finding #8)
- [ ] T033 [P] [US8] Verify solune/backend/src/config.py validates CORS origins as well-formed URLs with scheme and hostname at startup, failing on malformed values (Finding #16 — code review)
- [ ] T034 [P] [US8] Verify solune/backend/src/config.py enforces COOKIE_SECURE=true in production mode (Finding #12 — code review)
- [ ] T035 [P] [US8] Verify solune/backend/src/main.py gates API docs on ENABLE_DOCS env var, independent of DEBUG (Finding #14 — code review)
- [ ] T036 [P] [US8] Verify solune/backend/src/services/github_projects/service.py logs full GraphQL errors internally but raises only generic ValueError to API callers (Finding #19 — code review)
- [ ] T037 [P] [US8] Verify .github/workflows/branch-issue-link.yml uses permissions: {} default with per-job minimum grants and justification comments (Finding #20 — code review)
- [ ] T038 [P] [US8] Verify solune/frontend/src/components/board/IssueCard.tsx validates avatar URLs use HTTPS and originate from avatars.githubusercontent.com, falling back to placeholder on failure (Finding #21 — code review)

**Checkpoint**: User Story 8 complete — all configuration, error handling, and low-priority items verified.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Execute the full 10-item verification matrix from the spec, confirm all remediations are effective, and finalize documentation.

- [ ] T039 Execute verification check #1: After login, no credentials appear in browser URL bar, history, or access logs (FR-001, FR-002, SC-001)
- [ ] T040 Execute verification check #2: Backend refuses to start in non-debug mode without ENCRYPTION_KEY set (FR-003, SC-002)
- [ ] T041 Execute verification check #3: docker exec into frontend container — id must return non-root UID (FR-005, SC-004)
- [ ] T042 Execute verification check #4: Authenticated request with unowned project_id returns 403 (FR-006, FR-007, SC-003)
- [ ] T043 Execute verification check #5: WebSocket connection to unowned project ID is rejected before any data is sent (FR-006, SC-003)
- [ ] T044 Execute verification check #6: All webhook secret comparisons use constant-time function (FR-008, SC-006)
- [ ] T045 Execute verification check #7: curl -I frontend returns CSP, HSTS, Referrer-Policy; no nginx version in Server header (FR-009, FR-010, SC-005)
- [ ] T046 Execute verification check #8: After rate limit threshold, expensive endpoints return 429 (FR-015, FR-016, SC-007)
- [ ] T047 Execute verification check #9: After logout, localStorage contains no message content (FR-024, FR-025, SC-008)
- [ ] T048 Execute verification check #10: DB directory permissions are 0700; file permissions are 0600 (FR-021, SC-009)
- [ ] T049 Update specs/001-security-review/research.md with final verification results for all 21 findings
- [ ] T050 Run quickstart.md validation: execute all steps in specs/001-security-review/quickstart.md and confirm expected outputs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Empty — all infrastructure already exists
- **User Stories (Phase 3–10)**: All depend on Setup (Phase 1) completion for environment verification
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 11)**: Depends on all user story phases being complete (verification matrix validates everything together)

### User Story Dependencies

- **US1 (P1)** — Secure Auth: Independent, no dependencies on other stories
- **US2 (P1)** — Encryption Enforcement: Independent; T008 is the only code change task (encryption.py hardening)
- **US3 (P1)** — Access Control: Independent, no dependencies on other stories
- **US4 (P2)** — Container Hardening: Independent, no dependencies on other stories
- **US5 (P2)** — Headers & Webhooks: Independent; T021 is a code change task (server_tokens off)
- **US6 (P3)** — Rate Limiting: Independent; may produce code changes if gaps found in audit (T026–T029)
- **US7 (P3)** — Client Storage: Independent, no dependencies on other stories
- **US8 (P3)** — Config & Error Handling: Independent; T032 is a code change task (OAuth scope documentation)

### Within Each User Story

- Verification tasks (code review) before any code changes
- Code changes (if needed) after understanding current state
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks T002–T003 marked [P] can run in parallel
- All US3 verification tasks T011–T014 marked [P] can run in parallel (different files)
- All US4 verification tasks T016–T020 marked [P] can run in parallel (different files)
- All US5 verification tasks T022–T024 marked [P] can run in parallel (different files)
- All US6 audit tasks T026–T028 marked [P] can run in parallel (different files)
- All US8 verification tasks T033–T038 marked [P] can run in parallel (different files)
- Once Setup completes, all user stories (US1–US8) can start in parallel (if team capacity allows)

---

## Parallel Example: User Story 4 (Container Hardening)

```bash
# Launch all verification tasks for US4 together:
Task: T016 "Verify frontend Dockerfile non-root user in solune/frontend/Dockerfile"
Task: T017 "Verify backend Dockerfile non-root user in solune/backend/Dockerfile"
Task: T018 "Verify docker-compose.yml localhost bindings in docker-compose.yml"
Task: T019 "Verify data volume mount path in docker-compose.yml"
Task: T020 "Verify database permissions in solune/backend/src/services/database.py"
```

## Parallel Example: User Story 5 (Headers & Webhooks)

```bash
# Fix task first (not parallelizable with verification of same file):
Task: T021 "Add server_tokens off in solune/frontend/nginx.conf"

# Then verify headers and webhooks in parallel:
Task: T022 "Verify security headers in solune/frontend/nginx.conf"
Task: T023 "Verify constant-time comparison in solune/backend/src/api/signal.py"
Task: T024 "Verify webhook verification in solune/backend/src/api/webhooks.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 Only — All P1)

1. Complete Phase 1: Setup — verify environment
2. Complete Phase 3: US1 — verify secure auth flow
3. Complete Phase 4: US2 — harden encryption key validation (T008 is the primary code change)
4. Complete Phase 5: US3 — verify project access control
5. **STOP and VALIDATE**: All Critical and P1-High findings verified/fixed
6. Zero Critical findings remaining after this checkpoint

### Incremental Delivery

1. Complete Setup → Environment ready
2. US1 + US2 + US3 (P1) → All Critical/P1-High verified → **MVP milestone** (SC-010: zero Critical/High remaining)
3. US4 + US5 (P2) → Container + header hardening verified → Deploy confidence
4. US6 + US7 + US8 (P3) → Rate limits + privacy + config verified → Full audit closure
5. Polish (Phase 11) → Full verification matrix executed → Audit complete

### Parallel Team Strategy

With multiple developers:

1. Team reviews Setup together (Phase 1)
2. Once Setup is confirmed:
   - Developer A: US1 (auth) + US2 (encryption) — both P1, related to auth/secrets
   - Developer B: US3 (access control) + US4 (containers) — authorization + infrastructure
   - Developer C: US5 (headers/webhooks) + US6 (rate limits) — HTTP layer hardening
3. After P1/P2 complete:
   - Any developer: US7 (client storage) + US8 (config/error handling) — independent verification
4. Full team: Phase 11 verification matrix

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- ~19/21 findings already remediated — most tasks are verification (code review) not implementation
- Only 3 tasks produce code changes: T008 (encryption.py), T021 (nginx.conf), T032 (github_auth.py)
- T026–T029 (rate limit audit) may produce code changes if gaps are discovered
- T006 (dev login) may produce a code change if URL params are still accepted
- Tests are not mandated; the 10-item verification matrix (Phase 11) serves as acceptance criteria
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
