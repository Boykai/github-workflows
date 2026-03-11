# Tasks: Security Review Remediation Program

**Input**: Design documents from `/specs/001-security-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are required for this feature. Add or extend backend pytest coverage, frontend Vitest coverage, and behavior-based verification steps for every user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story while covering all 21 findings, the plaintext-credential remediation path, staging verification for OAuth scope reduction, and the 10 behavior-based verification checks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact repository-relative file paths in every task

## Path Conventions

- **Backend**: `backend/src/` and `backend/tests/`
- **Frontend**: `frontend/src/`
- **Infra / Ops**: `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `docker-compose.yml`, `.github/workflows/`
- **Feature docs**: `specs/001-security-review/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the remediation matrix, shared fixtures, and reusable test helpers before touching story code.

- [ ] T001 Update the remediation matrix, staging prerequisites, and 10-check verification tracker in specs/001-security-review/quickstart.md
- [ ] T002 Add shared backend security fixtures for production settings, sessions, and webhook secrets in backend/tests/conftest.py
- [ ] T003 [P] Add frontend security test helpers for cookie-auth redirects and localStorage cleanup in frontend/src/test/setup.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core security infrastructure that MUST be ready before user-story implementation begins.

**⚠️ CRITICAL**: No user story work should start until this phase is complete.

- [ ] T004 Extend shared security settings parsing and aggregated validation helpers in backend/src/config.py
- [ ] T005 [P] Add FastAPI request.state-backed project-access cache helpers in backend/src/dependencies.py
- [ ] T006 [P] Configure the shared slowapi limiter, rate-limit exception handling, and docs-toggle plumbing in backend/src/main.py
- [ ] T007 [P] Add reusable security assertions for HTTP errors, cookies, and headers in backend/tests/helpers/assertions.py

**Checkpoint**: Shared validation, authorization, rate-limit, and test infrastructure is ready for story work.

---

## Phase 3: User Story 1 - Safe Authentication and Startup Guardrails (Priority: P1) 🎯 MVP

**Goal**: Remove credential exposure from authentication flows and fail closed when core production secrets or cookie protections are unsafe.

**Independent Test**: Complete OAuth and dev-login flows, then start the backend with missing secrets, weak session secrets, and unsafe cookie settings to confirm unsafe deployments fail while safe configurations succeed.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests first, ensure they fail before implementation.**

- [ ] T008 [P] [US1] Extend OAuth callback and dev-login regressions in backend/tests/unit/test_api_auth.py
- [ ] T009 [P] [US1] Add startup guardrail regression coverage for missing secrets, weak session secrets, and cookie policy failures in backend/tests/unit/test_config_validation.py
- [ ] T010 [P] [US1] Extend cookie-only authentication flow coverage in frontend/src/hooks/useAuth.test.tsx

### Implementation for User Story 1

- [ ] T011 [P] [US1] Set HttpOnly redirect cookies and reject query-parameter dev credentials in backend/src/api/auth.py
- [ ] T012 [P] [US1] Remove URL credential parsing and rely on cookie-backed session refresh in frontend/src/hooks/useAuth.ts
- [ ] T013 [US1] Enforce non-debug secret, session-secret-length, and cookie-secure startup checks in backend/src/config.py
- [ ] T014 [US1] Update operator-facing authentication and startup remediation steps in specs/001-security-review/quickstart.md

**Checkpoint**: Authentication is cookie-only, credentials no longer leak via URLs, and production startup blocks weak or missing security settings.

---

## Phase 4: User Story 2 - Authorized Project Access and Trusted Webhooks (Priority: P1)

**Goal**: Enforce consistent ownership checks for every project-aware entry point and require trusted webhook verification in every environment.

**Independent Test**: Attempt project API calls and WebSocket subscriptions against unowned projects, then send valid and invalid webhook secrets to confirm access is denied before any project data or automation runs.

### Tests for User Story 2 ⚠️

- [ ] T015 [P] [US2] Add owned-versus-unowned project access coverage in backend/tests/unit/test_project_authorization.py
- [ ] T016 [P] [US2] Extend real-time project subscription denial coverage in backend/tests/unit/test_websocket.py
- [ ] T017 [P] [US2] Add Signal and GitHub webhook signature regressions in backend/tests/unit/test_webhook_security.py

### Implementation for User Story 2

- [ ] T018 [US2] Harden verify_project_access with consistent 401 and 403 behavior in backend/src/dependencies.py
- [ ] T019 [P] [US2] Apply verified project access to task routes in backend/src/api/tasks.py
- [ ] T020 [P] [US2] Apply verified project access and subscription rejection to project routes in backend/src/api/projects.py
- [ ] T021 [P] [US2] Apply verified project access to project settings routes in backend/src/api/settings.py
- [ ] T022 [P] [US2] Apply verified project access to workflow routes in backend/src/api/workflow.py
- [ ] T023 [P] [US2] Enforce timing-safe Signal secret validation in backend/src/api/signal.py
- [ ] T024 [P] [US2] Remove the debug-mode webhook signature bypass in backend/src/api/webhooks.py

**Checkpoint**: Unowned project requests and subscriptions are denied consistently, and all protected webhook endpoints require trusted signatures.

---

## Phase 5: User Story 3 - Hardened Runtime and Browser Surface (Priority: P2)

**Goal**: Reduce infrastructure and browser attack surface by hardening docs exposure, origin validation, container users, headers, and deployment bindings.

**Independent Test**: Inspect container identities, published ports, mounted volumes, API docs exposure, startup behavior with malformed origins, and frontend response headers.

### Tests for User Story 3 ⚠️

- [ ] T025 [P] [US3] Add API-docs toggle regression coverage in backend/tests/unit/test_main.py
- [ ] T026 [US3] Extend malformed-origin startup validation coverage in backend/tests/unit/test_config_validation.py

### Implementation for User Story 3

- [ ] T027 [US3] Gate Swagger and ReDoc on explicit ENABLE_DOCS settings in backend/src/main.py
- [ ] T028 [US3] Validate production CORS origins with clear operator errors in backend/src/config.py
- [ ] T029 [P] [US3] Preserve dedicated non-root backend runtime directives in backend/Dockerfile
- [ ] T030 [P] [US3] Preserve dedicated non-root frontend runtime directives in frontend/Dockerfile
- [ ] T031 [P] [US3] Maintain required security headers and hide server version in frontend/nginx.conf
- [ ] T032 [P] [US3] Preserve loopback-only bindings and external data volume placement in docker-compose.yml

**Checkpoint**: Runtime and browser-facing surfaces expose only approved docs, origins, headers, ports, users, and storage locations.

---

## Phase 6: User Story 4 - Protected Data Storage and User Privacy (Priority: P2)

**Goal**: Protect stored credentials, browser-retained chat data, external-service failures, and avatar rendering so sensitive data and internal details are not exposed.

**Independent Test**: Verify new credentials are protected at rest, remediation exists for legacy plaintext data, database files remain owner-only, chat data is cleared or expired appropriately, GraphQL failures are sanitized, and untrusted avatars fall back safely.

### Tests for User Story 4 ⚠️

- [ ] T033 [P] [US4] Add encryption-at-rest and remediation regression coverage in backend/tests/unit/test_auth_security.py
- [ ] T034 [P] [US4] Add database permission regression coverage in backend/tests/unit/test_database.py
- [ ] T035 [P] [US4] Extend chat history privacy and TTL coverage in frontend/src/hooks/useChatHistory.test.ts
- [ ] T036 [P] [US4] Add GitHub GraphQL sanitization coverage in backend/tests/unit/test_github_projects.py
- [ ] T037 [P] [US4] Add avatar allowlist and placeholder coverage in frontend/src/components/board/IssueCard.test.tsx

### Implementation for User Story 4

- [ ] T038 [US4] Remove production plaintext fallback and support remediation state handling in backend/src/services/encryption.py
- [ ] T039 [US4] Add plaintext-credential remediation metadata in backend/src/migrations/021_encrypt_existing.sql
- [ ] T040 [US4] Enforce owner-only database directory and file permissions in backend/src/services/database.py
- [ ] T041 [US4] Persist only TTL-bound chat references and clear chat storage on logout in frontend/src/hooks/useChatHistory.ts
- [ ] T042 [US4] Sanitize GitHub GraphQL failures while retaining internal logs in backend/src/services/github_projects/service.py
- [ ] T043 [US4] Validate GitHub avatar hosts and safe placeholder fallback in frontend/src/components/board/IssueCard.tsx

**Checkpoint**: Sensitive data is protected at rest and in the browser, user-facing failures are sanitized, and unsafe avatar sources never render.

---

## Phase 7: User Story 5 - Abuse Prevention and Least-Privilege Integrations (Priority: P3)

**Goal**: Add targeted abuse controls and least-privilege integrations without breaking supported write workflows.

**Independent Test**: Exceed protected endpoint thresholds, confirm authenticated users on shared networks remain isolated from each other, verify OAuth callback throttling, and validate staged write operations after scope reduction.

### Tests for User Story 5 ⚠️

- [ ] T044 [P] [US5] Add per-user and per-IP throttling coverage in backend/tests/unit/test_rate_limiting.py
- [ ] T045 [P] [US5] Extend reduced-scope OAuth and reauthorization coverage in backend/tests/unit/test_github_auth.py
- [ ] T046 [P] [US5] Add the reduced-scope staging verification checklist and supported write-action matrix in specs/001-security-review/quickstart.md

### Implementation for User Story 5

- [ ] T047 [US5] Apply per-IP throttles to OAuth callback flows in backend/src/api/auth.py
- [ ] T048 [P] [US5] Apply per-user throttles to chat endpoints in backend/src/api/chat.py
- [ ] T049 [P] [US5] Apply per-user throttles to agent invocation endpoints in backend/src/api/agents.py
- [ ] T050 [P] [US5] Apply per-user throttles to workflow trigger endpoints in backend/src/api/workflow.py
- [ ] T051 [US5] Reduce GitHub OAuth scopes and surface reauthorization guidance in backend/src/services/github_auth.py
- [ ] T052 [US5] Minimize GitHub Actions permissions and add justification comments in .github/workflows/branch-issue-link.yml

**Checkpoint**: Expensive endpoints throttle correctly, OAuth scopes are least-privilege, staged write actions remain intact, and automation permissions are minimized.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete remediation set, finish rollout documentation, and capture cross-story verification evidence.

- [ ] T053 [P] Run the backend security regression suite and log results in specs/001-security-review/quickstart.md
- [ ] T054 [P] Run the frontend security regression suite and log results in specs/001-security-review/quickstart.md
- [ ] T055 [P] Execute and record the 10 behavior-based verification checks in specs/001-security-review/quickstart.md
- [ ] T056 [P] Update rollout, staging, and operator remediation notes in README.md and specs/001-security-review/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — No dependencies; start immediately.
- **Phase 2: Foundational** — Depends on T001-T003; blocks all user stories.
- **Phase 3: US1** — Depends on T004-T007; delivers the MVP.
- **Phase 4: US2** — Depends on T004-T007; can proceed in parallel with US1 once foundation is complete.
- **Phase 5: US3** — Depends on T004-T007; can proceed in parallel with US1/US2 after foundation is complete.
- **Phase 6: US4** — Depends on T004-T007; strongly recommended after T008-T014 because credential remediation assumes the US1 fail-closed startup and authentication baseline is already in place.
- **Phase 7: US5** — Depends on T004-T007; strongly recommended after T008-T014 and T018-T022 because callback throttling extends the hardened auth flow and workflow throttles should land on already-guarded project routes.
- **Phase 8: Polish** — Depends on every story that is in scope for the release.

### User Story Dependencies

- **US1 (P1)** — No story dependency after the foundational phase; recommended MVP scope.
- **US2 (P1)** — No story dependency after the foundational phase; may ship alongside or immediately after US1.
- **US3 (P2)** — No story dependency after the foundational phase; complements the first P1 release.
- **US4 (P2)** — Best implemented after US1 because encryption remediation and privacy cleanup rely on the hardened startup and auth baselines.
- **US5 (P3)** — Best implemented after US1 and US2 because throttling and OAuth scope reduction touch shared auth, workflow, and project-aware entry points.

### Within Each User Story

- Tests must be written and fail before implementation tasks begin.
- Shared entry-point changes should land before downstream verification docs for that story.
- Endpoint guard and throttle tasks marked `[P]` can run in parallel once the shared dependency or limiter task for that story is complete.
- Story verification documentation should be updated only after implementation and tests pass.

### Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel after T001 defines the verification matrix.
- **Foundational**: T005, T006, and T007 can run in parallel after T004 establishes shared settings behavior.
- **US1**: T008, T009, and T010 can run in parallel; T011 and T012 can run in parallel after those tests fail.
- **US2**: T015, T016, and T017 can run in parallel; T019-T024 can run in parallel after T018 hardens the shared authorization dependency.
- **US3**: T029-T032 can run in parallel after T027 and T028 lock down docs exposure and origin validation.
- **US4**: T033-T037 can run in parallel; T040-T043 can run in parallel after T038 and T039 establish the remediation path.
- **US5**: T044-T046 can run in parallel; T048-T050 can run in parallel after T047 and T051 confirm the auth and scope baselines.
- **Polish**: T053-T055 can run in parallel once all selected stories are complete.

---

## Parallel Example: User Story 1

```bash
# Write the failing auth and startup tests together:
Task: "T008 Extend OAuth callback and dev-login regressions in backend/tests/unit/test_api_auth.py"
Task: "T009 Add startup guardrail regression coverage in backend/tests/unit/test_config_validation.py"
Task: "T010 Extend cookie-only authentication flow coverage in frontend/src/hooks/useAuth.test.tsx"

# Implement backend and frontend auth changes together after the tests fail:
Task: "T011 Set HttpOnly redirect cookies and reject query-parameter dev credentials in backend/src/api/auth.py"
Task: "T012 Remove URL credential parsing and rely on cookie-backed session refresh in frontend/src/hooks/useAuth.ts"
```

## Parallel Example: User Story 2

```bash
# Build the failing authorization and webhook tests together:
Task: "T015 Add owned-versus-unowned project access coverage in backend/tests/unit/test_project_authorization.py"
Task: "T016 Extend real-time project subscription denial coverage in backend/tests/unit/test_websocket.py"
Task: "T017 Add Signal and GitHub webhook signature regressions in backend/tests/unit/test_webhook_security.py"

# Guard the project-aware routes in parallel after T018 is complete:
Task: "T019 Apply verified project access to task routes in backend/src/api/tasks.py"
Task: "T020 Apply verified project access and subscription rejection to project routes in backend/src/api/projects.py"
Task: "T021 Apply verified project access to project settings routes in backend/src/api/settings.py"
Task: "T022 Apply verified project access to workflow routes in backend/src/api/workflow.py"
```

## Parallel Example: User Story 3

```bash
# Verify the two startup/runtime regressions first:
Task: "T025 Add API-docs toggle regression coverage in backend/tests/unit/test_main.py"
Task: "T026 Extend malformed-origin startup validation coverage in backend/tests/unit/test_config_validation.py"

# Harden deploy-time artifacts in parallel:
Task: "T029 Preserve dedicated non-root backend runtime directives in backend/Dockerfile"
Task: "T030 Preserve dedicated non-root frontend runtime directives in frontend/Dockerfile"
Task: "T031 Maintain required security headers and hide server version in frontend/nginx.conf"
Task: "T032 Preserve loopback-only bindings and external data volume placement in docker-compose.yml"
```

## Parallel Example: User Story 4

```bash
# Write the failing privacy and storage regressions together:
Task: "T033 Add encryption-at-rest and remediation regression coverage in backend/tests/unit/test_auth_security.py"
Task: "T034 Add database permission regression coverage in backend/tests/unit/test_database.py"
Task: "T035 Extend chat history privacy and TTL coverage in frontend/src/hooks/useChatHistory.test.ts"
Task: "T036 Add GitHub GraphQL sanitization coverage in backend/tests/unit/test_github_projects.py"
Task: "T037 Add avatar allowlist and placeholder coverage in frontend/src/components/board/IssueCard.test.tsx"

# Implement the independent privacy hardening changes together:
Task: "T040 Enforce owner-only database directory and file permissions in backend/src/services/database.py"
Task: "T041 Persist only TTL-bound chat references and clear chat storage on logout in frontend/src/hooks/useChatHistory.ts"
Task: "T042 Sanitize GitHub GraphQL failures while retaining internal logs in backend/src/services/github_projects/service.py"
Task: "T043 Validate GitHub avatar hosts and safe placeholder fallback in frontend/src/components/board/IssueCard.tsx"
```

## Parallel Example: User Story 5

```bash
# Start the failing abuse-control and scope tests together:
Task: "T044 Add per-user and per-IP throttling coverage in backend/tests/unit/test_rate_limiting.py"
Task: "T045 Extend reduced-scope OAuth and reauthorization coverage in backend/tests/unit/test_github_auth.py"
Task: "T046 Add the reduced-scope staging verification checklist and supported write-action matrix in specs/001-security-review/quickstart.md"

# Apply endpoint throttles in parallel after the auth callback baseline is updated:
Task: "T048 Apply per-user throttles to chat endpoints in backend/src/api/chat.py"
Task: "T049 Apply per-user throttles to agent invocation endpoints in backend/src/api/agents.py"
Task: "T050 Apply per-user throttles to workflow trigger endpoints in backend/src/api/workflow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the US1 independent test end to end.
5. Demo or deploy the safe-authentication baseline before moving on.

### Incremental Delivery

1. Finish Setup + Foundational once.
2. Deliver **US1** to remove credential leaks and unsafe startup behavior.
3. Deliver **US2** to close broken access control and webhook trust gaps.
4. Deliver **US3** to harden runtime and browser surface controls.
5. Deliver **US4** to finish data-at-rest, privacy, and sanitization remediation.
6. Deliver **US5** to add abuse controls and least-privilege integration hardening.
7. Run Phase 8 polish tasks before rollout approval.

### Parallel Team Strategy

With multiple developers after Phase 2:

1. **Developer A**: US1 authentication and startup tasks.
2. **Developer B**: US2 authorization and webhook tasks.
3. **Developer C**: US3 runtime/browser hardening tasks.
4. **Developer D**: US4 privacy and storage tasks after US1 reaches the fail-closed baseline.
5. **Developer E**: US5 throttling and least-privilege tasks after the shared limiter/auth scaffolding is stable.

---

## Notes

- Every audit finding from `specs/001-security-review/spec.md` and `specs/001-security-review/plan.md` is covered by at least one task, and T001 maintains the traceability matrix that maps all 21 findings plus the 10 behavior checks to their implementation and verification tasks.
- The 10 behavior-based verification checks should be recorded in `specs/001-security-review/quickstart.md` as evidence during T055.
- Prefer shipping in priority order: US1 → US2 → US3/US4 → US5.
- Keep endpoint behavior backward compatible except where the specification explicitly requires a safer contract (cookie-only auth, POST-only dev login, denied unowned access, throttling, reduced OAuth scopes).
