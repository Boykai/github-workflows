# Tasks: Security, Privacy & Vulnerability Audit

**Input**: Design documents from `/home/runner/work/github-workflows/github-workflows/specs/037-security-review/`
**Prerequisites**: `/home/runner/work/github-workflows/github-workflows/specs/037-security-review/plan.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-security-review/spec.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-security-review/research.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-security-review/data-model.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-security-review/quickstart.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-security-review/contracts/security-api.yaml`

**Tests**: Include automated tests where the spec/plan call for regression coverage; retain manual verification for container, nginx, compose, and workflow-only hardening.

**Organization**: Tasks are grouped by user story so each security hardening slice can be implemented and verified independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared configuration, environment wiring, and migration scaffolding used by multiple security stories.

- [ ] T001 Add shared security settings fields, startup validation entrypoints, and rate-limit defaults in /home/runner/work/github-workflows/github-workflows/backend/src/config.py
- [ ] T002 [P] Wire the new security environment variables and localhost-safe defaults in /home/runner/work/github-workflows/github-workflows/docker-compose.yml
- [ ] T003 [P] Create the token re-encryption migration scaffold in /home/runner/work/github-workflows/github-workflows/backend/src/migrations/022_encrypt_existing_tokens.sql

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared security primitives that block user-story implementation until they exist.

**⚠️ CRITICAL**: Complete this phase before starting user-story implementation.

- [ ] T004 Extract reusable session-cookie issuance and current-session plumbing in /home/runner/work/github-workflows/github-workflows/backend/src/api/auth.py
- [ ] T005 [P] Create a centralized verify_project_ownership dependency for project-scoped routes in /home/runner/work/github-workflows/github-workflows/backend/src/dependencies.py
- [ ] T006 [P] Add shared per-user and per-IP limiter key helpers with configurable defaults in /home/runner/work/github-workflows/github-workflows/backend/src/middleware/rate_limit.py
- [ ] T007 Wire ENABLE_DOCS handling and shared rate-limit exception handling into /home/runner/work/github-workflows/github-workflows/backend/src/main.py

**Checkpoint**: Shared security infrastructure is ready; user stories can now proceed in priority order.

---

## Phase 3: User Story 1 - Credential Leakage Prevention (Priority: P1) 🎯 MVP

**Goal**: Remove session credentials from URLs by delivering auth state via secure cookies and cookie-backed session reads.

**Independent Test**: Complete OAuth login and dev login flows and verify no credentials appear in browser URLs, history, or request URLs while authenticated user state still resolves correctly.

### Tests for User Story 1

- [ ] T008 [P] [US1] Add backend auth regression tests for cookie-based OAuth callback and POST-body dev login in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_auth.py
- [ ] T009 [P] [US1] Add frontend auth-hook regression tests proving session tokens are never read from URLs in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useAuth.test.tsx

### Implementation for User Story 1

- [ ] T010 [P] [US1] Update OAuth callback and dev-login handlers to deliver credentials only via HttpOnly cookies in /home/runner/work/github-workflows/github-workflows/backend/src/api/auth.py
- [ ] T011 [P] [US1] Remove query-string session exchange APIs and rely on cookie-backed current-user reads in /home/runner/work/github-workflows/github-workflows/frontend/src/services/api.ts
- [ ] T012 [US1] Update callback cleanup and authenticated state refresh behavior in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useAuth.ts
- [ ] T013 [P] [US1] Synchronize cookie-auth and POST-body login contract details in /home/runner/work/github-workflows/github-workflows/specs/037-security-review/contracts/security-api.yaml

**Checkpoint**: OAuth and dev login flows no longer leak credentials through URLs and remain independently testable.

---

## Phase 4: User Story 2 - Mandatory Encryption and Secret Enforcement (Priority: P1)

**Goal**: Fail startup when critical secrets or secure-cookie settings are missing and provide a migration path for legacy plaintext tokens.

**Independent Test**: Start the backend in non-debug mode with missing secrets, a weak session key, insecure cookies, or malformed CORS origins and verify startup fails with clear errors.

### Tests for User Story 2

- [ ] T014 [P] [US2] Add startup validation tests for missing secrets, weak session keys, insecure cookies, and malformed CORS origins in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_config_validation.py

### Implementation for User Story 2

- [ ] T015 [P] [US2] Enforce mandatory ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET, SESSION_SECRET_KEY, COOKIE_SECURE, and CORS validation in /home/runner/work/github-workflows/github-workflows/backend/src/config.py
- [ ] T016 [US2] Make encryption fail closed outside debug mode and surface clear operator errors in /home/runner/work/github-workflows/github-workflows/backend/src/services/encryption.py
- [ ] T017 [US2] Implement legacy token backfill SQL for existing plaintext rows in /home/runner/work/github-workflows/github-workflows/backend/src/migrations/022_encrypt_existing_tokens.sql

**Checkpoint**: The backend refuses insecure production startup and can safely migrate persisted tokens.

---

## Phase 5: User Story 3 - Project-Level Access Control (Priority: P1)

**Goal**: Enforce project ownership consistently across REST and WebSocket entry points.

**Independent Test**: Authenticate as one user, target another user’s project across task, project, settings, workflow, agent, tool, and websocket paths, and verify 403/rejected access before any data is returned.

### Tests for User Story 3

- [ ] T018 [P] [US3] Add ownership regression tests for REST endpoints and WebSocket subscriptions in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_project_ownership.py

### Implementation for User Story 3

- [ ] T019 [P] [US3] Implement verify_project_ownership against persisted project ownership data in /home/runner/work/github-workflows/github-workflows/backend/src/dependencies.py
- [ ] T020 [P] [US3] Gate project task creation and mutation flows with ownership checks in /home/runner/work/github-workflows/github-workflows/backend/src/api/tasks.py
- [ ] T021 [P] [US3] Gate project fetch, selection, event stream, and WebSocket handshake routes with ownership checks in /home/runner/work/github-workflows/github-workflows/backend/src/api/projects.py
- [ ] T022 [P] [US3] Gate project settings endpoints with ownership checks in /home/runner/work/github-workflows/github-workflows/backend/src/api/settings.py
- [ ] T023 [P] [US3] Gate workflow endpoints that accept project identifiers with ownership checks in /home/runner/work/github-workflows/github-workflows/backend/src/api/workflow.py
- [ ] T024 [P] [US3] Gate project-scoped agent endpoints with ownership checks in /home/runner/work/github-workflows/github-workflows/backend/src/api/agents.py
- [ ] T025 [US3] Gate project-scoped tool endpoints with ownership checks in /home/runner/work/github-workflows/github-workflows/backend/src/api/tools.py

**Checkpoint**: Project ownership is centrally enforced across the full authenticated surface.

---

## Phase 6: User Story 4 - Container and Infrastructure Hardening (Priority: P2)

**Goal**: Run the frontend container as non-root and keep development exposure limited to localhost with data outside the app tree.

**Independent Test**: Run `id` in the frontend container to confirm a non-root UID and inspect compose port bindings and volume locations to verify localhost-only exposure and externalized data storage.

### Implementation for User Story 4

- [ ] T026 [P] [US4] Run nginx as a dedicated non-root user with writable runtime paths in /home/runner/work/github-workflows/github-workflows/frontend/Dockerfile
- [ ] T027 [US4] Restrict service exposure to localhost and move persistent data outside the application tree in /home/runner/work/github-workflows/github-workflows/docker-compose.yml

**Checkpoint**: Container and compose hardening can be validated without depending on later stories.

---

## Phase 7: User Story 5 - HTTP Security Headers and Timing-Safe Comparisons (Priority: P2)

**Goal**: Add modern browser security headers and eliminate timing-vulnerable secret comparisons.

**Independent Test**: Send a HEAD request to the frontend and verify CSP/HSTS/Referrer-Policy/Permissions-Policy are present, X-XSS-Protection is absent, nginx version is hidden, and secret comparisons use constant-time functions.

### Implementation for User Story 5

- [ ] T028 [P] [US5] Add CSP, HSTS, Referrer-Policy, Permissions-Policy, and version-suppression headers in /home/runner/work/github-workflows/github-workflows/frontend/nginx.conf
- [ ] T029 [P] [US5] Replace remaining timing-vulnerable secret comparisons with hmac.compare_digest in /home/runner/work/github-workflows/github-workflows/backend/src/api/signal.py
- [ ] T030 [US5] Audit webhook secret verification paths for constant-time comparison consistency in /home/runner/work/github-workflows/github-workflows/backend/src/api/webhooks.py

**Checkpoint**: Browser-facing hardening and secret-comparison safety are complete and manually verifiable.

---

## Phase 8: User Story 6 - OAuth Scope Minimization (Priority: P2)

**Goal**: Request only the GitHub OAuth scopes the application actually needs.

**Independent Test**: Start a new OAuth authorization flow and verify the generated GitHub authorize URL requests project-management scopes without broad full-repository access.

### Tests for User Story 6

- [ ] T031 [P] [US6] Add authorization URL regression tests for minimized OAuth scopes in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_github_auth.py

### Implementation for User Story 6

- [ ] T032 [US6] Narrow requested GitHub OAuth scopes and document reauthorization expectations in /home/runner/work/github-workflows/github-workflows/backend/src/services/github_auth.py

**Checkpoint**: OAuth scope requests are minimized and covered by focused regression tests.

---

## Phase 9: User Story 7 - Rate Limiting on Sensitive Endpoints (Priority: P3)

**Goal**: Throttle expensive authenticated actions per user and unauthenticated auth callbacks per IP.

**Independent Test**: Exceed configured thresholds for chat, agents, workflow, and OAuth callback routes and verify 429 responses with sane retry behavior while the limiter fails open if its state store is unavailable.

### Tests for User Story 7

- [ ] T033 [P] [US7] Add threshold and fail-open rate-limit tests for user and IP keyed limits in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_rate_limiting.py

### Implementation for User Story 7

- [ ] T034 [P] [US7] Finalize limiter configuration, retry-after behavior, and fail-open warnings in /home/runner/work/github-workflows/github-workflows/backend/src/middleware/rate_limit.py
- [ ] T035 [P] [US7] Apply per-user throttles to chat send and upload endpoints in /home/runner/work/github-workflows/github-workflows/backend/src/api/chat.py
- [ ] T036 [P] [US7] Apply per-user throttles to workflow confirmation and mutation endpoints in /home/runner/work/github-workflows/github-workflows/backend/src/api/workflow.py
- [ ] T037 [P] [US7] Apply per-user throttles to agent execution endpoints in /home/runner/work/github-workflows/github-workflows/backend/src/api/agents.py
- [ ] T038 [US7] Apply per-IP throttling to OAuth callback and related unauthenticated auth entrypoints in /home/runner/work/github-workflows/github-workflows/backend/src/api/auth.py

**Checkpoint**: Sensitive endpoints enforce rate limits without blocking unrelated feature work.

---

## Phase 10: User Story 8 - Secure Local Storage and Error Sanitization (Priority: P3)

**Goal**: Limit browser persistence to lightweight chat references and prevent raw third-party API errors from reaching users.

**Independent Test**: Verify logout clears chat storage, stored chat metadata contains only message references with TTL metadata, and third-party API failures return generic error messages while detailed errors remain server-side.

### Tests for User Story 8

- [ ] T039 [P] [US8] Add chat-history TTL and logout cleanup tests in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useChatHistory.test.ts
- [ ] T040 [P] [US8] Add sanitized third-party error response tests in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_error_responses.py

### Implementation for User Story 8

- [ ] T041 [P] [US8] Refactor chat history persistence to message references with TTL and legacy-data migration in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useChatHistory.ts
- [ ] T042 [US8] Clear chat reference storage on logout and session expiry in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useAuth.ts
- [ ] T043 [US8] Sanitize GitHub GraphQL and API failures before surfacing responses in /home/runner/work/github-workflows/github-workflows/backend/src/services/github_projects/service.py

**Checkpoint**: Browser persistence and backend error exposure are both reduced without depending on lower-priority stories.

---

## Phase 11: User Story 9 - Secure Configuration and Debug Isolation (Priority: P3)

**Goal**: Decouple security controls from debug mode, keep docs exposure explicit, validate CORS at startup, and lock down database permissions.

**Independent Test**: Run with DEBUG=true and verify webhook signature verification still applies, docs stay disabled unless ENABLE_DOCS=true, malformed CORS origins fail startup, and SQLite directories/files are created with 0700/0600 permissions.

### Tests for User Story 9

- [ ] T044 [P] [US9] Add startup and docs-toggle regression tests in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_main.py
- [ ] T045 [P] [US9] Add webhook debug-isolation regression tests in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_webhooks.py
- [ ] T046 [P] [US9] Add filesystem permission regression tests for SQLite initialization in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_database.py

### Implementation for User Story 9

- [ ] T047 [P] [US9] Gate Swagger and ReDoc exposure on ENABLE_DOCS instead of DEBUG in /home/runner/work/github-workflows/github-workflows/backend/src/main.py
- [ ] T048 [P] [US9] Remove debug-mode webhook verification bypasses and require configured local test secrets in /home/runner/work/github-workflows/github-workflows/backend/src/api/webhooks.py
- [ ] T049 [US9] Enforce 0700 directory and 0600 database file permissions during SQLite setup in /home/runner/work/github-workflows/github-workflows/backend/src/services/database.py

**Checkpoint**: Debug mode no longer weakens security controls and startup behavior is explicitly hardened.

---

## Phase 12: User Story 10 - Supply Chain and Frontend Asset Safety (Priority: P4)

**Goal**: Minimize GitHub Actions workflow permissions and validate avatar sources before rendering.

**Independent Test**: Review workflow permissions for least privilege and render an issue card with an invalid avatar URL to confirm the UI falls back to a safe placeholder.

### Tests for User Story 10

- [ ] T050 [P] [US10] Add invalid-avatar fallback tests for issue cards in /home/runner/work/github-workflows/github-workflows/frontend/src/components/board/IssueCard.test.tsx

### Implementation for User Story 10

- [ ] T051 [P] [US10] Minimize job permissions and justify required issue-comment access in /home/runner/work/github-workflows/github-workflows/.github/workflows/branch-issue-link.yml
- [ ] T052 [US10] Validate GitHub avatar domains and fallback rendering in /home/runner/work/github-workflows/github-workflows/frontend/src/components/board/IssueCard.tsx

**Checkpoint**: CI permissions and avatar rendering are both least-privilege / safe-by-default.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Finish cross-story documentation and validation updates needed to roll the hardening out safely.

- [ ] T053 [P] Update operator security configuration guidance for new env vars and secrets in /home/runner/work/github-workflows/github-workflows/docs/configuration.md
- [ ] T054 [P] Update deployment and reverse-proxy hardening notes for localhost binding and non-root containers in /home/runner/work/github-workflows/github-workflows/docs/setup.md
- [ ] T055 [P] Update API and architecture references for cookie auth, ownership checks, and rate limiting in /home/runner/work/github-workflows/github-workflows/docs/api-reference.md
- [ ] T056 Validate and refresh manual verification steps against implemented security hardening in /home/runner/work/github-workflows/github-workflows/specs/037-security-review/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** → no dependencies; establishes shared config, compose wiring, and the migration file.
- **Phase 2: Foundational** → depends on Setup; blocks all user stories by creating shared auth, ownership, limiter, and startup hooks.
- **Phase 3–5 (P1 stories)** → start after Foundational; US1 is the suggested MVP, while US2 and US3 should follow before production rollout.
- **Phase 6–8 (P2 stories)** → depend on Foundational; can proceed in parallel once P1 risk is under control.
- **Phase 9–11 (P3 stories)** → depend on Foundational and reuse earlier auth/config primitives.
- **Phase 12 (P4 story)** → depends on Foundational only and can be scheduled after higher-risk fixes.
- **Phase 13: Polish** → depends on every completed story you intend to ship.

### User Story Dependencies

- **US1** depends on T004 and T007.
- **US2** depends on T001 and T003.
- **US3** depends on T005.
- **US4** depends on T002.
- **US5** depends on Foundational only.
- **US6** depends on US1’s stabilized auth flow for end-to-end verification.
- **US7** depends on T006 and should be validated after US1/US3 auth behavior is stable.
- **US8** depends on US1 logout/session behavior.
- **US9** depends on T001 and T007 and complements US2 startup validation.
- **US10** depends on Foundational only.

### Recommended Story Completion Order

1. **US1** Credential Leakage Prevention
2. **US2** Mandatory Encryption and Secret Enforcement
3. **US3** Project-Level Access Control
4. **US4** Container and Infrastructure Hardening
5. **US5** HTTP Security Headers and Timing-Safe Comparisons
6. **US6** OAuth Scope Minimization
7. **US7** Rate Limiting on Sensitive Endpoints
8. **US8** Secure Local Storage and Error Sanitization
9. **US9** Secure Configuration and Debug Isolation
10. **US10** Supply Chain and Frontend Asset Safety

### Within Each User Story

- Write test tasks first where they are listed.
- Finish implementation tasks in listed order when multiple tasks touch the same file.
- Prefer merging each story only after its independent test criteria passes.

---

## Parallel Opportunities

### User Story 1

```bash
# Parallel test authoring
T008 backend auth regression tests
T009 frontend auth-hook regression tests

# Parallel implementation after tests are in place
T010 backend cookie delivery changes
T011 frontend auth API changes
T013 contract updates
```

### User Story 2

```bash
T014 startup validation tests
T017 legacy token migration SQL
```

### User Story 3

```bash
T020 task endpoint ownership enforcement
T021 project route and websocket ownership enforcement
T022 settings ownership enforcement
T023 workflow ownership enforcement
T024 agent ownership enforcement
```

### User Story 4

```bash
T026 frontend container non-root runtime
T027 docker-compose localhost/data-path hardening
```

### User Story 5

```bash
T028 nginx header hardening
T029 timing-safe Signal secret comparison
```

### User Story 6

```bash
T031 OAuth scope regression tests
T032 scope minimization in GitHub auth service
```

### User Story 7

```bash
T035 chat endpoint throttling
T036 workflow endpoint throttling
T037 agent endpoint throttling
```

### User Story 8

```bash
T039 frontend chat-history tests
T040 backend error-sanitization tests
T041 frontend chat-history refactor
```

### User Story 9

```bash
T044 startup/docs tests
T045 webhook debug-isolation tests
T046 database permission tests
T047 docs toggle wiring
T048 webhook debug isolation
```

### User Story 10

```bash
T050 issue-card avatar fallback tests
T051 workflow permission tightening
T052 avatar URL validation
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete **Phase 1: Setup**.
2. Complete **Phase 2: Foundational**.
3. Complete **Phase 3: US1**.
4. Validate the independent US1 auth-flow test before expanding scope.
5. Demo the cookie-based auth flow with zero credentials in URLs.

### Incremental Delivery

1. Ship the **P1 bundle**: US1 → US2 → US3.
2. Add **P2 hardening**: US4 → US5 → US6.
3. Add **P3 defense-in-depth**: US7 → US8 → US9.
4. Finish with **P4 cleanup**: US10.
5. Close with **Phase 13 Polish** documentation and quickstart validation.

### Parallel Team Strategy

1. One engineer handles shared Setup + Foundational work.
2. After Foundational completes:
   - Engineer A: US1 / US6 auth changes
   - Engineer B: US2 / US9 startup, docs, and database hardening
   - Engineer C: US3 / US7 access control and rate limiting
   - Engineer D: US4 / US5 / US10 infra, nginx, and workflow/frontend safety
3. Fold US8 into the frontend/backend pair once auth changes stabilize.

---

## Notes

- Every checklist item uses the required `- [ ] T### [P?] [US?] Description with file path` format.
- Setup, Foundational, and Polish tasks intentionally omit story labels.
- Story tasks include exact repository file paths so they can be executed directly without re-discovery.
- Manual verification remains important for container, nginx header, and workflow permission changes even when no dedicated automated test task is listed.
