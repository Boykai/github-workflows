# Tasks: Security, Privacy & Vulnerability Audit

**Input**: Design documents from `/specs/026-security-review/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are NOT explicitly requested in this specification. Behavior-based verification checks are defined in quickstart.md. Existing backend and frontend test suites serve as regression gates. Implementers may add unit tests at their discretion for critical paths (auth, authorization).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend: Python 3.13 / FastAPI / Pydantic 2.x / aiosqlite
- Frontend: TypeScript 5.9 / React 19.2 / Vite 7.3
- Infrastructure: Docker Compose, nginx, GitHub Actions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and create new files needed across multiple user stories

- [ ] T001 Add `slowapi` dependency to backend/pyproject.toml for rate limiting middleware
- [ ] T002 Create rate limiting middleware module at backend/src/middleware/rate_limit.py with Limiter configuration and `get_user_key` helper
- [ ] T003 [P] Create centralized project authorization dependency `verify_project_access` in backend/src/dependencies.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Configuration validation and startup enforcement that MUST be complete before any user story can ship safely to production

**⚠️ CRITICAL**: No user story work can begin until this phase is complete — startup validation failures block all runtime behavior changes

- [ ] T004 Add `enable_docs: bool = False` field to `Settings` in backend/src/config.py
- [ ] T005 Add `_validate_production_secrets` model validator to `Settings` in backend/src/config.py that enforces in non-debug mode: ENCRYPTION_KEY required, GITHUB_WEBHOOK_SECRET required, SESSION_SECRET_KEY ≥ 64 chars, effective_cookie_secure must be True
- [ ] T006 Add CORS origins URL format validation to `cors_origins_list` property in backend/src/config.py — each origin must have scheme and hostname; fail on malformed values
- [ ] T007 Update default `database_path` in backend/src/config.py from `/app/data/settings.db` to `/var/lib/ghchat/data/settings.db`

**Checkpoint**: Foundation ready — startup validation enforced, new dependencies installed, shared dependencies created. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Credentials Never Appear in URLs (Priority: P1) 🎯 MVP

**Goal**: Eliminate all instances of credentials (session tokens, access tokens, PATs) being passed via URL query parameters. Deliver cookie-based session management and POST-based dev login.

**Independent Test**: Complete the OAuth login flow, inspect browser URL bar and history for any token parameters, and verify authentication works via HttpOnly cookie. Verify dev login uses POST body.

### Implementation for User Story 1

- [ ] T008 [US1] Modify OAuth callback in backend/src/api/auth.py to set HttpOnly, SameSite=Strict, Secure cookie on the RedirectResponse and redirect to frontend `/auth/callback` with no credentials in the URL
- [ ] T009 [US1] Remove the `POST /session?session_token=...` endpoint from backend/src/api/auth.py
- [ ] T010 [US1] Change dev login endpoint in backend/src/api/auth.py from GET with query parameter to POST with JSON body using a `DevLoginRequest` Pydantic model (`{"github_token": "..."}`)
- [ ] T011 [US1] Update `_set_session_cookie` in backend/src/api/auth.py (or backend/src/services/github_auth.py) to use `samesite="strict"` instead of `"lax"`
- [ ] T012 [US1] Remove URL parameter token reading from frontend/src/hooks/useAuth.ts — authentication state must be derived solely from the cookie-authenticated `/api/v1/auth/me` endpoint

**Checkpoint**: After login, no credentials appear in the browser URL bar, history, or access logs. Dev login accepts credentials via POST body only.

---

## Phase 4: User Story 2 — Application Refuses to Start Without Required Secrets (Priority: P1)

**Goal**: Ensure the application fails fast with clear error messages when required secrets are missing or insufficiently strong in production (non-debug) mode.

**Independent Test**: Start the application in non-debug mode with each required secret missing or invalid, and verify it fails with a clear error message each time.

### Implementation for User Story 2

- [ ] T013 [US2] Wire the `_validate_production_secrets` model validator (from T005) to reject startup when ENCRYPTION_KEY is unset in non-debug mode in backend/src/config.py
- [ ] T014 [US2] Wire the validator to reject startup when GITHUB_WEBHOOK_SECRET is unset in non-debug mode in backend/src/config.py
- [ ] T015 [US2] Wire the validator to reject startup when SESSION_SECRET_KEY < 64 characters in non-debug mode in backend/src/config.py
- [ ] T016 [US2] Wire the validator to reject startup when effective_cookie_secure is False in non-debug mode in backend/src/config.py
- [ ] T017 [P] [US2] Add migration path documentation/logging for existing deployments with plaintext OAuth tokens in backend/src/services/encryption.py — detect and log warning about unencrypted rows at startup

**Checkpoint**: Application refuses to start in non-debug mode without ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET, or with a short SESSION_SECRET_KEY. Debug mode remains permissive with warnings.

---

## Phase 5: User Story 3 — Containers Run as Non-Root Users (Priority: P1)

**Goal**: Ensure all Docker containers run as dedicated non-root system users, reducing the blast radius of any container compromise.

**Independent Test**: Run `docker exec` into each container and verify `id` returns a non-root UID (not uid=0).

### Implementation for User Story 3

- [ ] T018 [US3] Update frontend/Dockerfile to add a non-root `nginx-app` user with correct ownership of `/var/cache/nginx`, `/var/run`, `/tmp/nginx`, `/usr/share/nginx/html`, and `/etc/nginx/conf.d`
- [ ] T019 [US3] Add `USER nginx-app` directive and change `EXPOSE` to `8080` in frontend/Dockerfile
- [ ] T020 [US3] Update `HEALTHCHECK` in frontend/Dockerfile to use port 8080 instead of 80
- [ ] T021 [US3] Update docker-compose.yml frontend service port mapping from `5173:80` to `127.0.0.1:5173:8080`

**Checkpoint**: Frontend container runs as non-root. Backend already runs as `appuser`. All containers are non-root.

---

## Phase 6: User Story 4 — Users Can Only Access Their Own Projects (Priority: P1)

**Goal**: Every endpoint accepting a project identifier verifies the authenticated user owns that project. Centralize the check as a FastAPI shared dependency.

**Independent Test**: Authenticate as User A, request User B's project via API, verify the response is 403 Forbidden with no data leaked. Verify WebSocket to unowned project is rejected.

### Implementation for User Story 4

- [ ] T022 [US4] Implement `verify_project_access` in backend/src/dependencies.py — query user's project list, confirm project_id is in set, raise HTTPException(403) if not
- [ ] T023 [P] [US4] Add `Depends(verify_project_access)` to all project-accepting endpoints in backend/src/api/tasks.py
- [ ] T024 [P] [US4] Add `Depends(verify_project_access)` to all project-accepting endpoints in backend/src/api/settings.py
- [ ] T025 [P] [US4] Add `Depends(verify_project_access)` to all project-accepting endpoints in backend/src/api/workflow.py
- [ ] T026 [US4] Add `Depends(verify_project_access)` to project-accepting endpoints in backend/src/api/projects.py and add WebSocket project ownership verification (reject with close code 4403 before accepting connection)

**Checkpoint**: Authenticated requests targeting an unowned project return 403 Forbidden. WebSocket connections to unowned projects are rejected before any data is sent.

---

## Phase 7: User Story 5 — Security Headers Protect Users from Common Web Attacks (Priority: P2)

**Goal**: Add all modern security headers to the nginx configuration, remove deprecated headers, and hide the server version.

**Independent Test**: Send an HTTP HEAD request to the frontend and verify all required security headers are present and nginx version is not disclosed.

### Implementation for User Story 5

- [ ] T027 [US5] Add `server_tokens off;` to the http context in frontend/nginx.conf
- [ ] T028 [US5] Add `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy`, and `Permissions-Policy` headers in frontend/nginx.conf
- [ ] T029 [US5] Remove the deprecated `X-XSS-Protection` header from frontend/nginx.conf
- [ ] T030 [US5] Change nginx `listen` port from `80` to `8080` in frontend/nginx.conf for non-root compatibility

**Checkpoint**: `curl -I` returns Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy headers. No nginx version in Server header. No X-XSS-Protection.

---

## Phase 8: User Story 6 — Timing-Safe Secret Comparisons (Priority: P2)

**Goal**: Replace all standard string equality operators used for secret comparisons with constant-time comparison functions.

**Independent Test**: Code review confirming all secret/token comparisons use `hmac.compare_digest()`.

### Implementation for User Story 6

- [ ] T031 [US6] Replace `!=` comparison of Signal webhook secret with `hmac.compare_digest()` in backend/src/api/signal.py
- [ ] T032 [US6] Audit entire backend codebase for other `==`/`!=` comparisons of secrets or tokens and replace with `hmac.compare_digest()` where found

**Checkpoint**: `grep -n "!=" backend/src/api/signal.py | grep -i "secret"` returns no results. All secret comparisons use constant-time functions.

---

## Phase 9: User Story 7 — OAuth Scope Follows Least Privilege (Priority: P2)

**Goal**: Remove the overly broad `repo` scope from OAuth requests, keeping only the minimum scopes needed for project management.

**Independent Test**: Initiate OAuth flow and inspect the GitHub authorization page for requested scopes. Verify all project management operations still function.

### Implementation for User Story 7

- [ ] T033 [US7] Change OAuth scope string from `"read:user read:org project repo"` to `"read:user read:org project"` in backend/src/services/github_auth.py
- [ ] T034 [US7] Add a code comment in backend/src/services/github_auth.py documenting the scope change, the removed `repo` scope, and the requirement for existing users to re-authorize

**Checkpoint**: OAuth authorization page requests only `read:user`, `read:org`, and `project` scopes. No `repo` scope.

---

## Phase 10: User Story 8 — Rate Limiting Prevents Abuse (Priority: P2)

**Goal**: Enforce per-user and per-IP rate limits on expensive/sensitive endpoints to prevent resource exhaustion.

**Independent Test**: Send requests above the rate limit threshold and verify 429 Too Many Requests responses are returned with Retry-After headers.

### Implementation for User Story 8

- [ ] T035 [US8] Configure slowapi Limiter in backend/src/middleware/rate_limit.py with per-user key function using session user ID and per-IP fallback via `get_remote_address`
- [ ] T036 [US8] Register slowapi middleware and exception handler in backend/src/main.py
- [ ] T037 [P] [US8] Apply `@limiter.limit("10/minute")` per-user rate limit to chat endpoints in backend/src/api/chat.py
- [ ] T038 [P] [US8] Apply `@limiter.limit("5/minute")` per-user rate limit to agent endpoints in backend/src/api/agents.py
- [ ] T039 [P] [US8] Apply `@limiter.limit("10/minute")` per-user rate limit to workflow endpoints in backend/src/api/workflow.py
- [ ] T040 [US8] Apply `@limiter.limit("20/minute", key_func=get_remote_address)` per-IP rate limit to OAuth callback in backend/src/api/auth.py

**Checkpoint**: After rate limit threshold, expensive endpoints return 429 Too Many Requests with Retry-After header.

---

## Phase 11: User Story 9 — Sensitive Data Protected at Rest and in Transit (Priority: P2)

**Goal**: Harden data protection: restricted database permissions, TTL-based chat history references, and logout clearing of local data.

**Independent Test**: Check database file permissions (0700 directory, 0600 file), verify localStorage contains no message content after logout.

### Implementation for User Story 9

- [ ] T041 [US9] Update database directory creation in backend/src/services/database.py to use `mode=0o700` and set database file permissions to `0o600` after creation
- [ ] T042 [P] [US9] Refactor frontend/src/hooks/useChatHistory.ts to store only lightweight references (input entries) with a TTL-based expiration wrapper (`{ entries: [...], expiresAt: timestamp }`)
- [ ] T043 [US9] Add `clearOnLogout()` function to frontend/src/hooks/useChatHistory.ts that clears all chat data from localStorage
- [ ] T044 [US9] Call `clearOnLogout()` from the logout flow in frontend/src/hooks/useAuth.ts to ensure all local data is cleared on logout

**Checkpoint**: Database directory is 0700, file is 0600. After logout, localStorage contains no chat message content.

---

## Phase 12: User Story 10 — Secure Configuration and Infrastructure Defaults (Priority: P3)

**Goal**: Harden infrastructure configuration defaults — localhost port binding, external volume mount, webhook debug bypass removal, API docs toggle, GraphQL error sanitization, Actions permissions, avatar URL validation.

**Independent Test**: Review Docker Compose config, verify CORS validation rejects malformed origins, confirm webhook verification is not debug-conditional, check GraphQL error responses are sanitized.

### Implementation for User Story 10

- [ ] T045 [P] [US10] Update docker-compose.yml backend service port binding from `8000:8000` to `127.0.0.1:8000:8000`
- [ ] T046 [P] [US10] Update docker-compose.yml backend service volume mount from `ghchat-data:/app/data` to `ghchat-data:/var/lib/ghchat/data`
- [ ] T047 [P] [US10] Add `ENABLE_DOCS` and `DATABASE_PATH` environment variables to docker-compose.yml backend service
- [ ] T048 [US10] Remove debug-mode bypass of webhook signature verification in backend/src/api/webhooks.py — always require signature verification regardless of debug setting
- [ ] T049 [US10] Change API docs gating in backend/src/main.py from `settings.debug` to `settings.enable_docs` for `docs_url` and `redoc_url`
- [ ] T050 [US10] Sanitize GraphQL error messages in backend/src/services/github_projects/service.py — log full error internally, raise only generic `"GitHub API request failed"` message in API responses
- [ ] T051 [P] [US10] Add justification comments to permission declarations in .github/workflows/branch-issue-link.yml
- [ ] T052 [US10] Create `validateAvatarUrl` utility function in frontend/src/components/board/IssueCard.tsx (or a shared utility) that validates avatar URLs use `https:` protocol from `avatars.githubusercontent.com` and falls back to a placeholder on failure
- [ ] T053 [US10] Apply `validateAvatarUrl` to all avatar `<img>` elements in frontend/src/components/board/IssueCard.tsx

**Checkpoint**: Docker services bind to localhost only. Webhook verification is unconditional. API docs gated on ENABLE_DOCS. GraphQL errors sanitized. Avatar URLs validated.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cross-cutting improvements

- [ ] T054 [P] Update backend/Dockerfile to create `/var/lib/ghchat/data` directory with correct ownership for the application user
- [ ] T055 [P] Update .env.example with new environment variables (ENABLE_DOCS, DATABASE_PATH) and updated documentation for mandatory secrets
- [ ] T056 Run quickstart.md verification commands to validate all security findings are resolved
- [ ] T057 Run existing backend test suite (pytest) to verify no regressions from security changes
- [ ] T058 Run existing frontend checks (tsc --noEmit, eslint, vitest, npm run build) to verify no regressions from security changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001 for slowapi) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (T005, T006 provide the validators)
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion
- **User Story 4 (Phase 6)**: Depends on Foundational phase completion (T003 provides verify_project_access)
- **User Story 5 (Phase 7)**: Depends on Foundational phase completion
- **User Story 6 (Phase 8)**: Depends on Foundational phase completion
- **User Story 7 (Phase 9)**: Depends on Foundational phase completion
- **User Story 8 (Phase 10)**: Depends on Foundational phase (T001, T002 for slowapi setup)
- **User Story 9 (Phase 11)**: Depends on Foundational phase completion
- **User Story 10 (Phase 12)**: Depends on Foundational phase completion
- **Polish (Phase 13)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Credentials in URLs — Can start after Foundational. No dependencies on other stories.
- **US2 (P1)**: Required Secrets — Can start after Foundational. T013–T016 depend on T005 validator. Independent of other stories.
- **US3 (P1)**: Non-Root Containers — Can start after Foundational. Independent of other stories. T021 shares docker-compose.yml with US10 T045/T046.
- **US4 (P1)**: Project Authorization — Can start after Foundational. Depends on T003 (verify_project_access). Independent of other stories.
- **US5 (P2)**: Security Headers — Can start after Foundational. T030 shares nginx.conf with US3 (Dockerfile port change). Independent of other stories.
- **US6 (P2)**: Timing-Safe Comparisons — Can start after Foundational. Independent of other stories.
- **US7 (P2)**: OAuth Scope — Can start after Foundational. Independent of other stories.
- **US8 (P2)**: Rate Limiting — Can start after Foundational. Depends on T001, T002 (slowapi setup). Independent of other stories.
- **US9 (P2)**: Data Protection — Can start after Foundational. Independent of other stories.
- **US10 (P3)**: Infrastructure Defaults — Can start after Foundational. T045/T046 share docker-compose.yml with US3 T021.

### Within Each User Story

- Models/shared dependencies before service layer changes
- Service layer before endpoint changes
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks can run sequentially (same file: config.py) or in parallel where files differ
- Once Foundational phase completes, all P1 stories can start in parallel:
  - US1 (auth.py, useAuth.ts), US2 (config.py, encryption.py), US3 (Dockerfile, docker-compose.yml), US4 (dependencies.py, tasks.py, projects.py, settings.py, workflow.py)
- P2 stories can start in parallel after Foundational:
  - US5 (nginx.conf), US6 (signal.py), US7 (github_auth.py), US8 (rate_limit.py, chat.py, agents.py, workflow.py), US9 (database.py, useChatHistory.ts, useAuth.ts)
- Within US4: T023, T024, T025 can run in parallel (different files)
- Within US8: T037, T038, T039 can run in parallel (different files)
- Within US10: T045, T046, T047, T051 can run in parallel (different files or independent sections)

---

## Parallel Example: User Story 1

```bash
# OAuth callback and dev login can be done sequentially (same file: auth.py)
Task T008: "Modify OAuth callback in backend/src/api/auth.py"
Task T009: "Remove POST /session endpoint from backend/src/api/auth.py"
Task T010: "Change dev login to POST in backend/src/api/auth.py"
Task T011: "Update _set_session_cookie samesite to strict"

# Frontend change can run in parallel with backend changes:
Task T012: "Remove URL token reading from frontend/src/hooks/useAuth.ts"
```

## Parallel Example: User Story 4

```bash
# After T022 (verify_project_access), these can run in parallel:
Task T023: "Add Depends(verify_project_access) to backend/src/api/tasks.py"
Task T024: "Add Depends(verify_project_access) to backend/src/api/settings.py"
Task T025: "Add Depends(verify_project_access) to backend/src/api/workflow.py"

# Then T026 (projects.py + WebSocket) which may depend on patterns established above
```

## Parallel Example: User Story 8

```bash
# After T035 (Limiter config) and T036 (middleware registration):
Task T037: "Apply rate limit to backend/src/api/chat.py"
Task T038: "Apply rate limit to backend/src/api/agents.py"
Task T039: "Apply rate limit to backend/src/api/workflow.py"
Task T040: "Apply per-IP rate limit to backend/src/api/auth.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1–4, P1 Critical/High)

1. Complete Phase 1: Setup (slowapi dep, rate_limit.py, verify_project_access)
2. Complete Phase 2: Foundational (config validation, CORS validation)
3. Complete Phase 3: US1 — Credentials not in URLs
4. Complete Phase 4: US2 — Required secrets enforcement
5. Complete Phase 5: US3 — Non-root containers
6. Complete Phase 6: US4 — Project authorization
7. **STOP and VALIDATE**: All Critical and High-priority findings addressed. Zero Critical/High findings remain (SC-012).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 → Test: no credentials in URLs → Deploy (Critical fix!)
3. Add US2 → Test: startup rejects missing secrets → Deploy
4. Add US3 → Test: containers non-root → Deploy
5. Add US4 → Test: project auth enforced → Deploy (All P1 complete!)
6. Add US5–US9 → Test each independently → Deploy (All P2 complete!)
7. Add US10 → Test infrastructure defaults → Deploy (All P3 complete!)
8. Polish → Final regression + verification → Release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (auth flow) + US2 (config validation)
   - Developer B: US3 (Dockerfile) + US5 (nginx headers)
   - Developer C: US4 (project authorization) + US6 (timing-safe)
3. After P1 stories complete:
   - Developer A: US7 (OAuth scope) + US8 (rate limiting)
   - Developer B: US9 (data protection) + US10 (infrastructure)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- 58 total tasks across 13 phases
- docker-compose.yml is touched by US3 (T021), US10 (T045, T046, T047) — coordinate edits
- config.py is touched by Phase 2 (T004–T007) and US2 (T013–T016) — Phase 2 creates validators, US2 wires them
- auth.py is touched by US1 (T008–T011) and US8 (T040) — different sections, but coordinate edits
- useAuth.ts is touched by US1 (T012) and US9 (T044) — US1 removes token reading, US9 adds logout clearing
