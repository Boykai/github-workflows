# Tasks: Bug Bash — Codebase Quality & Reliability Sweep

**Input**: Design documents from `/specs/010-bug-bash/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included — spec mandates test coverage for security and correctness fixes (SC-001 through SC-010).

**Organization**: Tasks grouped by user story to enable independent implementation and testing. User stories ordered by priority (P1 → P2 → P3).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in all descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`, `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new shared utilities and modules that multiple user stories depend on. No existing behavior changes — purely additive.

- [x] T001 Add BoundedSet and BoundedDict utility classes with configurable maxlen to backend/src/utils.py
- [x] T002 [P] Create EncryptionService with Fernet encrypt/decrypt and passthrough mode in backend/src/services/encryption.py
- [x] T003 [P] Create RequestIDMiddleware with X-Request-ID header propagation and request_id_var ContextVar in backend/src/middleware/request_id.py
- [x] T004 [P] Add encryption_key: str | None = None field to Settings in backend/src/config.py
- [x] T005 [P] Create migration 003 adding admin_github_user_id TEXT DEFAULT NULL column to global_settings in backend/src/migrations/003_add_admin_column.sql

**Checkpoint**: Run `pytest` — all existing tests pass. New modules are additive, no breaking changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register infrastructure and create shared dependencies that MUST exist before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Register RequestIDMiddleware after CORSMiddleware in app startup in backend/src/main.py
- [x] T007 [P] Add require_admin FastAPI dependency (checks session github_user_id against global_settings.admin_github_user_id, auto-promotes first user) in backend/src/dependencies.py

**Checkpoint**: Foundation ready — all existing tests still pass, middleware active, admin dependency available.

---

## Phase 3: User Story 1 — Secure Authentication Flow (Priority: P1) 🎯 MVP

**Goal**: Session tokens never appear in URLs/logs. Dev-login disabled in production. OAuth states expire automatically.

**Independent Test**: Complete OAuth login flow and confirm token is in Set-Cookie header only (never URL). Hit /dev-login with debug=False and get 404.

**FRs**: FR-001, FR-002, FR-006 | **SCs**: SC-001, SC-002

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T008 [P] [US1] Write tests for cookie-based session token delivery (SC-001) and dev-login returns 404 when debug=False (SC-002) in backend/tests/unit/test_auth_security.py
- [x] T009 [P] [US1] Write test for OAuth state auto-expiry after 10 minutes and BoundedDict eviction at capacity in backend/tests/unit/test_oauth_state.py

### Implementation for User Story 1

- [x] T010 [US1] Move session token from URL query parameter to Set-Cookie (HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=28800) in OAuth callback in backend/src/api/auth.py
- [x] T011 [US1] Gate /dev-login endpoint — return 404 when Settings.debug is False in backend/src/api/auth.py
- [x] T012 [US1] Replace unbounded _oauth_states dict with BoundedDict(maxlen=1000) and add TTL-based expiry (10 min default) with cleanup on access in backend/src/services/github_auth.py

**Checkpoint**: User Story 1 fully functional. Token never in URL, dev-login gated, OAuth states bounded and expiring.

---

## Phase 4: User Story 6 — Security Hardening (Priority: P1)

**Goal**: Tokens encrypted at rest. Webhooks verified in production. Settings protected by admin authorization.

**Independent Test**: Inspect DB — access_token column contains Fernet ciphertext (starts with gAAAAA). Send unsigned webhook → 401. Non-admin PUT /settings/global → 403.

**FRs**: FR-003, FR-004, FR-005 | **SCs**: SC-009

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T013 [P] [US6] Write tests for token encryption at rest and legacy plaintext fallback on decrypt in backend/tests/unit/test_token_encryption.py
- [x] T014 [P] [US6] Write test for unsigned webhook payload rejection with 401 in production mode (SC-009) in backend/tests/integration/test_webhook_verification.py
- [x] T015 [P] [US6] Write test for non-admin user receiving 403 on global settings PUT in backend/tests/unit/test_admin_authorization.py

### Implementation for User Story 6

- [x] T016 [US6] Integrate EncryptionService into SessionStore — encrypt tokens on write, decrypt on read with legacy plaintext fallback (detect gho_/ghp_/ghr_ prefix) in backend/src/services/session_store.py
- [x] T017 [US6] Enforce webhook signature verification — reject unsigned payloads with 401 when debug=False, log warning and allow when debug=True in backend/src/api/webhooks.py
- [x] T018 [US6] Apply Depends(require_admin) to global settings PUT endpoint in backend/src/api/settings.py

**Checkpoint**: User Story 6 fully functional. Tokens encrypted, webhooks verified, settings admin-gated.

---

## Phase 5: User Story 2 — Reliable Pipeline Progression (Priority: P1)

**Goal**: Pipeline only advances when agent has verifiably committed code. Issue creation retries on failure. Comments fully paginated.

**Independent Test**: Simulate agent unassignment without commits → pipeline does NOT advance. Simulate issue creation failure → retried with backoff.

**FRs**: FR-007, FR-008, FR-021 | **SCs**: SC-003

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T019 [P] [US2] Write test for false-positive Signal 3 rejection — pipeline must NOT advance when agent unassigned without SHA change (SC-003) in backend/tests/unit/test_completion_false_positive.py
- [x] T020 [P] [US2] Write test for issue creation retry with backoff on failure in backend/tests/unit/test_issue_creation_retry.py

### Implementation for User Story 2

- [x] T021 [US2] Fix false-positive Signal 3 — require branch HEAD SHA to advance from agent_assigned_sha before marking completion in backend/src/services/copilot_polling/completion.py
- [x] T022 [US2] Add retry-with-backoff to create_issue method (use existing retry utility pattern) in backend/src/services/github_projects/service.py
- [x] T023 [US2] Implement cursor-based pagination for issue comments — add $after parameter to query and while-hasNextPage loop with max_pages=10 safety cap in backend/src/services/github_projects/graphql.py and backend/src/services/github_projects/service.py

**Checkpoint**: User Story 2 fully functional. No false-positive advancement, issue creation resilient, comments fully paginated.

---

## Phase 6: User Story 3 — Eliminate Duplicated Code Patterns (Priority: P2)

**Goal**: One canonical implementation for repository resolution, header construction, cache pruning, and PR filtering. All call sites use shared utilities.

**Independent Test**: Grep codebase for known duplicated patterns — each consolidated to a single shared implementation (SC-005).

**FRs**: FR-011, FR-012, FR-013, FR-014, FR-022

### Implementation for User Story 3

- [x] T024 [P] [US3] Replace 4+ inline repo resolution patterns with resolve_repository() calls in backend/src/api/workflow.py
- [x] T025 [P] [US3] Replace inline repo resolution with resolve_repository() call in backend/src/api/projects.py
- [x] T026 [US3] Extract _build_headers() method and replace 10+ inline header dict constructions in backend/src/services/github_projects/service.py
- [x] T027 [US3] Extract _filter_pull_requests() helper and replace 3 inline Copilot-author PR filter implementations in backend/src/services/github_projects/service.py
- [x] T028 [P] [US3] Consolidate cache pruning — replace ad-hoc size checks with BoundedSet/BoundedDict in backend/src/services/copilot_polling/pipeline.py and backend/src/services/copilot_polling/recovery.py
- [x] T029 [US3] Replace hardcoded asyncio.sleep delays with configurable timing parameters from Settings in backend/src/services/copilot_polling/pipeline.py

**Checkpoint**: User Story 3 complete. No inline repo resolution, no inline headers, no scattered cache pruning, no duplicated PR filtering. Verify with grep search (SC-005).

---

## Phase 7: User Story 4 — Robust Error Handling & API Responses (Priority: P2)

**Goal**: Rate limit responses include Retry-After. Stub endpoints return 501 instead of fake success.

**Independent Test**: Trigger 429 → response has Retry-After header. Call task status endpoint → returns 501.

**FRs**: FR-009, FR-010 | **SCs**: SC-004

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T030 [US4] Write tests for 429 response including Retry-After header (SC-004) and task status endpoint returning 501 in backend/tests/unit/test_error_responses.py

### Implementation for User Story 4

- [x] T031 [P] [US4] Add Retry-After header to 429 error handler — extract value from upstream GitHub retry-after/x-ratelimit-reset in backend/src/main.py
- [x] T032 [P] [US4] Return 501 Not Implemented with descriptive message for task status update endpoint in backend/src/api/tasks.py

**Checkpoint**: User Story 4 complete. All 429 responses have Retry-After, stub returns 501.

---

## Phase 8: User Story 5 — Reliable Real-Time Frontend Updates (Priority: P2)

**Goal**: Polling stops when WebSocket connects. Reconnection uses exponential backoff. Config fetch uses query not mutation.

**Independent Test**: Establish WebSocket → confirm polling inactive. Sever connection → confirm backoff delays increase (SC-007).

**FRs**: FR-017, FR-018, FR-019 | **SCs**: SC-007

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T033 [US5] Write tests for polling stop on WS connect (SC-007) and exponential backoff on WS reconnect in frontend/src/test/useRealTimeSync.test.ts

### Implementation for User Story 5

- [x] T034 [P] [US5] Stop HTTP polling on WebSocket connect, resume on disconnect with exponential backoff (delay = min(1000 * 2^attempt, 30000) + jitter) in frontend/src/hooks/useRealTimeSync.ts
- [x] T035 [P] [US5] Change workflow config fetch from useMutation to useQuery in frontend/src/hooks/useWorkflow.ts

**Checkpoint**: User Story 5 complete. No dual WS+polling, graceful reconnection backoff, proper data fetching pattern.

---

## Phase 9: User Story 7 — Meaningful Health Checks (Priority: P3)

**Goal**: Health endpoint checks DB, GitHub API, and polling loop — returns structured status with per-component results.

**Independent Test**: Take DB offline → health returns 503 with database check failed (SC-008).

**FRs**: FR-020 | **SCs**: SC-008

### Tests for User Story 7

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T036 [US7] Write test for structured health response and unhealthy status when DB is unreachable (SC-008) in backend/tests/integration/test_health_endpoint.py

### Implementation for User Story 7

- [x] T037 [US7] Replace static {"status": "ok"} with structured health check — asyncio.gather for DB (SELECT 1), GitHub API (/rate_limit), and polling loop (task.done()) — return 200/503 per IETF format in backend/src/main.py

**Checkpoint**: User Story 7 complete. Health endpoint reflects real system state.

---

## Phase 10: User Story 8 — Clean Module Boundaries & Dependency Injection (Priority: P3)

**Goal**: No cross-module private attribute access. Circular imports resolved properly. In-memory state bounded. DI used consistently.

**Independent Test**: Static analysis confirms no `_private` attribute access across module boundaries (SC-006). All services injected via DI.

**FRs**: FR-015, FR-016, FR-023 | **SCs**: SC-006

### Tests for User Story 8

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T038 [US8] Write test verifying no cross-module private attribute access via AST/grep analysis (SC-006) in backend/tests/unit/test_module_boundaries.py

### Implementation for User Story 8

- [x] T039 [US8] Eliminate _client private access — add public HTTP method to GitHubProjectsService interface and update webhooks.py to use it in backend/src/services/github_projects/service.py and backend/src/api/webhooks.py
- [x] T040 [P] [US8] Resolve circular imports — replace try/except ImportError blocks with lazy imports in factory function in backend/src/services/workflow_orchestrator/orchestrator.py
- [x] T041 [P] [US8] Replace 8 global mutable variables with BoundedSet/BoundedDict instances in backend/src/services/copilot_polling/state.py
- [x] T042 [US8] Replace direct service imports with FastAPI Depends() DI pattern in backend/src/api/chat.py

**Checkpoint**: User Story 8 complete. Clean module boundaries, no private access, no circular import hacks, bounded state.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Full validation across all user stories, regression check, end-to-end verification.

- [x] T043 Run full backend test suite (pytest --tb=short -q) — verify zero regressions (SC-010)
- [x] T044 [P] Run full frontend test suite (npm run test in frontend/) — verify zero regressions
- [x] T045 Run quickstart.md verification checklist end-to-end — confirm all 10 items pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (uses BoundedDict from T001)
- **US6 (Phase 4)**: Depends on Phase 2 (uses EncryptionService from T002, require_admin from T007)
- **US2 (Phase 5)**: Depends on Phase 2 only (no dependency on US1 or US6)
- **US3 (Phase 6)**: Depends on Phase 2 (uses BoundedSet from T001 for cache consolidation)
- **US4 (Phase 7)**: Depends on Phase 2 only
- **US5 (Phase 8)**: Depends on Phase 2 only (frontend-only, no backend dependencies beyond foundation)
- **US7 (Phase 9)**: Depends on Phase 2; also after US4 since both modify backend/src/main.py
- **US8 (Phase 10)**: Depends on Phase 2 (uses BoundedSet/Dict from T001)
- **Polish (Phase 11)**: Depends on ALL user story phases being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational → independent of other stories
- **US6 (P1)**: After Foundational → independent of other stories
- **US2 (P1)**: After Foundational → independent of other stories
- **US3 (P2)**: After Foundational → independent of other stories
- **US4 (P2)**: After Foundational → independent of other stories
- **US5 (P2)**: After Foundational → independent (frontend-only)
- **US7 (P3)**: After US4 (both modify main.py) → sequence after Phase 7
- **US8 (P3)**: After Foundational → independent of other stories

### File Conflict Dependencies

- **backend/src/main.py**: T006 (Phase 2) → T031 (US4) → T037 (US7) — must be sequential
- **backend/src/api/auth.py**: T010 → T011 (both US1) — sequential within story
- **backend/src/services/github_projects/service.py**: T022 (US2) → T026, T027 (US3) → T039 (US8) — sequential across stories
- **backend/src/api/webhooks.py**: T017 (US6) → T039 (US8) — sequential across stories
- **backend/src/services/copilot_polling/pipeline.py**: T028 → T029 (both US3) — sequential within story

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T001 (utils.py)  ┐
T002 (encryption) ├── All parallel (independent new files/additions)
T003 (middleware)  │
T004 (config.py)  │
T005 (migration)  ┘
```

**Phase 3 (US1) — Tests**:
```
T008 (test_auth_security.py)  ┐
T009 (test_oauth_state.py)    ┘── Parallel test writing
```

**Phase 4 (US6) — Tests**:
```
T013 (test_token_encryption.py)      ┐
T014 (test_webhook_verification.py)  ├── Parallel test writing
T015 (test_admin_authorization.py)   ┘
```

**Phase 5 (US2) — Tests**:
```
T019 (test_completion_false_positive.py)  ┐
T020 (test_issue_creation_retry.py)       ┘── Parallel test writing
```

**Phase 6 (US3)**:
```
T024 (workflow.py)  ┐
T025 (projects.py)  ├── Parallel (different files)
T028 (pipeline.py)  ┘
```

**Phase 8 (US5) — Implementation**:
```
T034 (useRealTimeSync.ts)  ┐
T035 (useWorkflow.ts)      ┘── Parallel (different files)
```

**Phase 10 (US8) — Implementation**:
```
T040 (orchestrator.py)  ┐
T041 (state.py)         ┘── Parallel (different files)
```

**Cross-Story Parallelism** (if multiple developers):
```
After Phase 2 completes:
  Developer A: US1 (Phase 3) → US6 (Phase 4)
  Developer B: US2 (Phase 5) → US3 (Phase 6)
  Developer C: US5 (Phase 8, frontend-only)
Then:
  Developer A: US4 (Phase 7) → US7 (Phase 9)  [main.py sequential]
  Developer B: US8 (Phase 10)
Finally:
  All: Phase 11 (Polish)
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup (5 tasks)
2. Complete Phase 2: Foundational (2 tasks)
3. Complete Phase 3: US1 — Secure Auth (5 tasks)
4. **STOP and VALIDATE**: Session token secure, dev-login gated, OAuth bounded
5. Complete Phase 4: US6 — Security Hardening (6 tasks)
6. Complete Phase 5: US2 — Pipeline Progression (5 tasks)
7. **MVP VALIDATED**: All P1 security + correctness fixes deployed

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Test independently → Secure auth (MVP increment 1)
3. US6 → Test independently → Hardened security (MVP increment 2)
4. US2 → Test independently → Reliable pipeline (MVP increment 3)
5. US3 → Test independently → DRY codebase (quality increment)
6. US4 + US5 → Test independently → Better errors + real-time (UX increment)
7. US7 + US8 → Test independently → Observability + clean architecture (polish increment)
8. Phase 11 → Full regression validation

### Single Developer Strategy

Work stories sequentially by priority: US1 → US6 → US2 → US3 → US4 → US5 → US7 → US8 → Polish.

---

## FR Coverage Matrix

| FR | Task(s) | User Story |
|----|---------|------------|
| FR-001 | T010 | US1 |
| FR-002 | T011 | US1 |
| FR-003 | T002, T016 | Setup + US6 |
| FR-004 | T017 | US6 |
| FR-005 | T007, T018 | Foundational + US6 |
| FR-006 | T012 | US1 |
| FR-007 | T021 | US2 |
| FR-008 | T022 | US2 |
| FR-009 | T031 | US4 |
| FR-010 | T032 | US4 |
| FR-011 | T024, T025 | US3 |
| FR-012 | T026 | US3 |
| FR-013 | T028 | US3 |
| FR-014 | T027 | US3 |
| FR-015 | T039 | US8 |
| FR-016 | T040 | US8 |
| FR-017 | T034 | US5 |
| FR-018 | T034 | US5 |
| FR-019 | T035 | US5 |
| FR-020 | T037 | US7 |
| FR-021 | T023 | US2 |
| FR-022 | T029 | US3 |
| FR-023 | T041 | US8 |
| FR-024 | T003, T006 | Setup + Foundational |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests follow Red-Green-Refactor: write failing tests before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
