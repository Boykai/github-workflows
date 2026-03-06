# Tasks: Simplify GitHub Service with githubkit v0.14.6

**Input**: Design documents from `/specs/019-githubkit-migration/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Test mock updates are included as tasks per FR-013 (spec requires all existing tests pass after mock migration). No TDD approach — test updates follow implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6 from spec.md)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`, `backend/docs/`
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add githubkit dependency and prepare project for migration

- [ ] T001 Add `githubkit>=0.14.0,<0.15.0` to dependencies in `backend/pyproject.toml`
- [ ] T002 [P] Verify httpx remains as a direct dependency in `backend/pyproject.toml` for signal services (`signal_bridge.py`, `signal_delivery.py`) per research R-009

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create core building blocks that ALL user stories depend on — the RateLimitState model and GitHubClientFactory class

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create `RateLimitState` frozen dataclass in `backend/src/models/rate_limit.py` with fields: limit (int), remaining (int), reset_at (int), used (int), resource (str, default "core") per data-model.md
- [ ] T004 [P] Create `GitHubClientFactory` class with `BoundedDict` client pool (max 50) in `backend/src/services/github_projects/client_factory.py` per contracts/client-factory.md — includes `get_client(token)`, `get_rate_limit()`, `clear_rate_limit()`, `close()` methods
- [ ] T005 Export `GitHubClientFactory` from `backend/src/services/github_projects/__init__.py`
- [ ] T006 Register `GitHubClientFactory` on `app.state` and update service initialization in `backend/src/dependencies.py`

**Checkpoint**: Foundation ready — `GitHubClientFactory` creates authenticated clients, bounded pool works, `RateLimitState` model exists. User story implementation can now begin.

---

## Phase 3: User Story 1 — Foundation: Add githubkit and Client Factory (Priority: P1) 🎯 MVP

**Goal**: Wire the GitHubClientFactory into the existing service layer so that subsequent migration steps have a stable integration point with zero behavior changes

**Independent Test**: Verify that the new dependency installs cleanly, the client factory creates authenticated clients, the bounded client pool enforces its size limit, and all existing tests still pass unchanged

### Implementation for User Story 1

- [ ] T007 [US1] Update `GitHubProjectsService.__init__()` to accept `GitHubClientFactory` as a dependency in `backend/src/services/github_projects/service.py`
- [ ] T008 [US1] Add `_get_github_client(access_token: str) -> GitHub` helper method to `GitHubProjectsService` that delegates to `self._client_factory.get_client()` in `backend/src/services/github_projects/service.py`
- [ ] T009 [US1] Update `GitHubProjectsService.close()` to delegate client cleanup to factory in `backend/src/services/github_projects/service.py`
- [ ] T010 [P] [US1] Update test fixtures and service construction in `backend/tests/unit/` to pass `GitHubClientFactory` (or mock) to `GitHubProjectsService`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. All existing tests pass with the new factory wired in. No behavior changes.

---

## Phase 4: User Story 2 — Replace REST API Call Sites (Priority: P1)

**Goal**: Replace all 20+ manual REST call sites in service.py with typed githubkit methods, eliminating ~600–800 LOC of URL construction, header management, response parsing, and manual pagination

**Independent Test**: Run existing test suite for issue creation, issue updates, PR review requests, branch deletion, comment creation, and file listing — each call should produce identical API behavior with significantly less service-layer code

### Implementation for User Story 2

- [ ] T011 [US2] Replace issue write operations (`create_issue`, `update_issue_body`, `update_issue_state`, `assign_issue`) with typed githubkit REST methods (`github.rest.issues.async_create`, `async_update`, `async_add_assignees`) in `backend/src/services/github_projects/service.py`
- [ ] T012 [US2] Replace `create_issue_comment()` with `github.rest.issues.async_create_comment()` in `backend/src/services/github_projects/service.py`
- [ ] T013 [US2] Replace PR read operations (`get_pr_changed_files` with built-in pagination, `has_copilot_reviewed_pr` via `async_list_reviews`, `get_pr_timeline_events` via `github.arequest("GET", ...)`) with typed githubkit methods in `backend/src/services/github_projects/service.py`
- [ ] T014 [US2] Replace PR write operations (`request_copilot_review` via `async_request_reviewers`, `merge_pull_request` via `async_merge`, `update_pr_base` via `async_update`, `link_pull_request_to_issue` via `github.arequest()`) with typed githubkit methods in `backend/src/services/github_projects/service.py`
- [ ] T015 [US2] Replace `delete_branch()` with `github.rest.git.async_delete_ref()` in `backend/src/services/github_projects/service.py`
- [ ] T016 [US2] Replace content retrieval operations (`get_directory_contents`, `get_file_content`) with `github.rest.repos.async_get_content()` in `backend/src/services/github_projects/service.py`
- [ ] T017 [US2] Replace `_search_open_prs_for_issue_rest()` with `github.rest.search.async_issues_and_pull_requests()` in `backend/src/services/github_projects/service.py`
- [ ] T018 [US2] Replace preview API calls (`create_sub_issue`, `get_sub_issues`) with `github.arequest("POST"/"GET", ...)` for Sub-Issues endpoint in `backend/src/services/github_projects/service.py`
- [ ] T019 [US2] Replace internal REST fallback methods (`_add_issue_to_project_rest`, `_assign_copilot_rest`) with `github.arequest("POST", ...)` in `backend/src/services/github_projects/service.py`
- [ ] T020 [US2] Replace `http_get()` public method with `github.arequest("GET", ...)` delegation in `backend/src/services/github_projects/service.py`
- [ ] T021 [P] [US2] Update `github_commit_workflow.py` to use new service API signatures in `backend/src/services/github_commit_workflow.py`
- [ ] T022 [US2] Update test mocks for all REST-migrated methods (mock githubkit client methods instead of raw httpx) in `backend/tests/unit/`

**Checkpoint**: At this point, all REST call sites use githubkit. Manual URL construction, header building, and response parsing are eliminated from REST paths. All tests pass.

---

## Phase 5: User Story 3 — Simplify the GraphQL Layer (Priority: P2)

**Goal**: Replace the custom `_graphql()` execution method with githubkit's built-in `github.async_graphql()`, eliminating manual ETag caching, error parsing, and hash-key generation (~200 LOC) while preserving all 31 domain-specific query strings and application-layer caching logic

**Independent Test**: Run existing GraphQL-dependent tests (project listing, field value mutations, item queries) and verify identical responses with the SDK's GraphQL method

### Implementation for User Story 3

- [ ] T023 [US3] Replace `_graphql()` method body with `github.async_graphql(query, variables=...)` delegation in `backend/src/services/github_projects/service.py`
- [ ] T024 [US3] Remove manual ETag cache fields (`_etag_cache`, `_ETAG_CACHE_MAX_SIZE`) and related logic from `__init__()` in `backend/src/services/github_projects/service.py` — ETag caching now handled by githubkit's `http_cache=True`
- [ ] T025 [US3] Verify and preserve in-flight coalescing (`_inflight_graphql` BoundedDict) and cycle cache as untouched app-layer logic in `backend/src/services/github_projects/service.py`
- [ ] T026 [US3] Consolidate all GraphQL→REST fallback chains (`add_issue_to_project`, `assign_copilot_to_issue`, `find_existing_pr_for_issue`) to uniformly use `_with_fallback()` helper in `backend/src/services/github_projects/service.py` per research R-010
- [ ] T027 [US3] Update test mocks for GraphQL-migrated execution path in `backend/tests/unit/`

**Checkpoint**: GraphQL layer uses githubkit. ETag caching handled by SDK. App-layer logic (cycle cache, coalescing, cooldown) unchanged. All tests pass.

---

## Phase 6: User Story 6 — Rate Limit Visibility Adapter (Priority: P2)

**Goal**: Implement an adapter that exposes githubkit's internally managed rate-limit state so the polling service can continue to adjust intervals based on remaining API quota without reaching into SDK internals

**Independent Test**: Make API calls through the SDK client and verify the adapter surfaces accurate remaining-request counts and reset timestamps consumable by the polling service

### Implementation for User Story 6

- [ ] T028 [US6] Implement httpx response event hook (`_capture_rate_limit`) that extracts `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers and stores as `RateLimitState` in `backend/src/services/github_projects/client_factory.py` per contracts/rate-limit-adapter.md Approach A
- [ ] T029 [US6] Wire the rate limit event hook into GitHub client creation in `GitHubClientFactory.get_client()` in `backend/src/services/github_projects/client_factory.py`
- [ ] T030 [US6] Migrate `copilot_polling/polling_loop.py` from `get_last_rate_limit()` dict access to `factory.get_rate_limit()` attribute access (`rl.remaining`, `rl.reset_at`) in `backend/src/services/copilot_polling/polling_loop.py`
- [ ] T031 [US6] Migrate `clear_last_rate_limit()` calls to `factory.clear_rate_limit()` in `backend/src/services/copilot_polling/polling_loop.py`

**Checkpoint**: Polling service reads rate limit data from the factory adapter. No direct access to service internals or SDK internals. Polling behavior unchanged.

---

## Phase 7: User Story 4 — Migrate OAuth Authentication (Priority: P2)

**Goal**: Replace the manual OAuth implementation in github_auth.py with githubkit's built-in OAuth strategies, reducing infrastructure code while preserving all SQLite session management logic (~313 LOC → ~270 LOC per research R-004)

**Independent Test**: Perform a complete OAuth login flow (redirect → callback → token exchange → session storage) and verify sessions are created, stored, and retrievable from the database identically to before

### Implementation for User Story 4

- [ ] T032 [US4] Replace `exchange_code_for_token()` with githubkit OAuth token exchange (via `github.request()` or `OAuthWebAuthStrategy`) in `backend/src/services/github_auth.py`
- [ ] T033 [P] [US4] Replace `get_github_user()` with `github.rest.users.async_get_authenticated()` in `backend/src/services/github_auth.py`
- [ ] T034 [P] [US4] Replace `refresh_token()` with githubkit token refresh strategy in `backend/src/services/github_auth.py`
- [ ] T035 [US4] Remove `self._client = httpx.AsyncClient(...)` from `GitHubAuthService.__init__()` and update `close()` to no-op in `backend/src/services/github_auth.py`
- [ ] T036 [P] [US4] Update `create_session_from_token()` to use factory `get_client()` for user info in `backend/src/services/github_auth.py`
- [ ] T037 [US4] Update test mocks for OAuth-migrated methods in `backend/tests/unit/`

**Checkpoint**: OAuth authentication uses githubkit. All session management preserved. github_auth.py reduced to ~270 LOC. All tests pass.

---

## Phase 8: User Story 5 — Delete Deprecated Infrastructure and Clean Up (Priority: P3)

**Goal**: Remove all deprecated infrastructure methods, retry constants, and stale code from service.py and graphql.py — delivering the final LOC reduction with zero behavior changes since all callers have been migrated in previous phases

**Independent Test**: Run full test suite after deletion, verify zero references to removed methods in production code, and confirm documentation accurately describes the new architecture

### Implementation for User Story 5

- [ ] T038 [US5] Delete `_request_with_retry()` method (~150 LOC) from `backend/src/services/github_projects/service.py`
- [ ] T039 [US5] Delete `_build_headers()` method from `backend/src/services/github_projects/service.py`
- [ ] T040 [US5] Delete `_extract_rate_limit_headers()` method from `backend/src/services/github_projects/service.py`
- [ ] T041 [US5] Delete `get_last_rate_limit()` and `clear_last_rate_limit()` methods from `backend/src/services/github_projects/service.py`
- [ ] T042 [US5] Delete `_parse_retry_after_seconds()` and `_is_secondary_limit()` methods from `backend/src/services/github_projects/service.py`
- [ ] T043 [US5] Delete `_apply_global_cooldown()` and `_respect_global_cooldown()` methods from `backend/src/services/github_projects/service.py`
- [ ] T044 [US5] Remove remaining infrastructure fields from `__init__()` (`_last_rate_limit`, `_last_request_time`, `_min_request_interval`, `_global_cooldown_until`, `_cooldown_lock`, `_low_quota_threshold`, `_cooldown_hit_count`) in `backend/src/services/github_projects/service.py`
- [ ] T045 [P] [US5] Remove `MAX_RETRIES`, `INITIAL_BACKOFF_SECONDS`, `MAX_BACKOFF_SECONDS` constants from `backend/src/services/github_projects/graphql.py`
- [ ] T046 [P] [US5] Remove `GITHUB_GRAPHQL_URL` constant from `backend/src/services/github_projects/graphql.py` (githubkit manages endpoint)
- [ ] T047 [US5] Verify zero references to deleted methods in production code via `grep` — no hits for `_request_with_retry`, `_build_headers`, `_extract_rate_limit_headers`, `_parse_retry_after_seconds`, `_is_secondary_limit`, `_apply_global_cooldown`, `_respect_global_cooldown` in `backend/src/`

**Checkpoint**: All deprecated infrastructure code deleted. No dead code remains. Full test suite passes.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, final verification, and cross-cutting validation

- [ ] T048 [P] Update GitHub integration section in `backend/docs/architecture.md` to describe githubkit-based architecture (FR-014)
- [ ] T049 [P] Update configuration reference in `backend/docs/configuration.md` to reflect new githubkit configuration options (FR-014)
- [ ] T050 Run full test suite (`pytest`) and verify all 1,411+ tests pass with zero failures
- [ ] T051 Run `pyright src/` type checking and verify no new type errors (SC-002)
- [ ] T052 Run `ruff check src/` and `ruff format --check src/` for clean lint (SC-008)
- [ ] T053 Verify `grep -r "import httpx" backend/src/services/github_projects/` returns zero hits (FR-016, SC-004)
- [ ] T054 Measure and verify net LOC reduction of 1,500–2,000 lines across all affected files (SC-001)
- [ ] T055 Run quickstart.md verification commands from `specs/019-githubkit-migration/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — wires factory into service
- **US2 (Phase 4)**: Depends on US1 — uses factory for REST calls
- **US3 (Phase 5)**: Depends on US1 — uses factory for GraphQL calls (independent of US2)
- **US6 (Phase 6)**: Depends on US1 — extends factory with rate limit adapter (independent of US2/US3)
- **US4 (Phase 7)**: Depends on US1 — uses factory for OAuth (independent of US2/US3/US6)
- **US5 (Phase 8)**: Depends on US2, US3, US4, US6 — deletes methods that other stories migrated away from
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
    └── Phase 2 (Foundational)
            └── Phase 3 (US1 - Foundation) ──────────────────────┐
                    ├── Phase 4 (US2 - REST replacement)          │
                    ├── Phase 5 (US3 - GraphQL simplify)          ├── All must complete
                    ├── Phase 6 (US6 - Rate limit adapter)        │   before Phase 8
                    └── Phase 7 (US4 - OAuth migration)           │
                                                                   ▼
                                                    Phase 8 (US5 - Delete infrastructure)
                                                           └── Phase 9 (Polish)
```

- **US1 (P1)**: Can start after Foundational (Phase 2) — no other story dependencies
- **US2 (P1)**: Can start after US1 — independent of US3, US4, US6
- **US3 (P2)**: Can start after US1 — independent of US2, US4, US6
- **US6 (P2)**: Can start after US1 — independent of US2, US3, US4
- **US4 (P2)**: Can start after US1 — independent of US2, US3, US6
- **US5 (P3)**: BLOCKED until US2, US3, US4, and US6 are all complete

### Within Each User Story

- Models/entities before services
- Factory/infrastructure before business logic
- Core implementation before test mock updates
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T003 (RateLimitState) and T004 (GitHubClientFactory) can run in parallel — different files
- **Phase 3**: T010 (test fixtures) can run in parallel with T007–T009 — different files
- **After US1 completes**: US2, US3, US6, and US4 can ALL start in parallel (if team capacity allows)
- **Phase 7**: T033 (get_github_user) and T034 (refresh_token) can run in parallel — different methods, same file but independent
- **Phase 8**: T045 and T046 (graphql.py constants) can run in parallel with service.py deletions — different files
- **Phase 9**: T048 and T049 (documentation) can run in parallel — different files

---

## Parallel Example: After US1 Completes

```bash
# With multiple developers, all four P2 streams can start simultaneously:
Developer A: Phase 4 (US2) — REST API call site replacements in service.py
Developer B: Phase 5 (US3) — GraphQL layer simplification in service.py
Developer C: Phase 6 (US6) — Rate limit adapter in client_factory.py + polling_loop.py
Developer D: Phase 7 (US4) — OAuth migration in github_auth.py

# Note: US2 and US3 both modify service.py — coordinate merges carefully
# US6 and US4 modify different files — safe to merge independently
```

## Parallel Example: Foundational Phase

```bash
# Launch both foundational tasks together:
Task T003: "Create RateLimitState frozen dataclass in backend/src/models/rate_limit.py"
Task T004: "Create GitHubClientFactory with BoundedDict pool in backend/src/services/github_projects/client_factory.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (add githubkit dependency)
2. Complete Phase 2: Foundational (RateLimitState + GitHubClientFactory)
3. Complete Phase 3: User Story 1 (wire factory into service)
4. **STOP and VALIDATE**: All existing tests pass, factory creates clients, pool works
5. This is a safe merge point — zero behavior changes, additive only

### Incremental Delivery

1. Complete Setup + Foundational + US1 → Foundation ready (safe to merge)
2. Add US2 (REST replacement) → Test independently → **Biggest LOC win (~600–800 lines)** 
3. Add US3 (GraphQL simplification) → Test independently → ~200 LOC reduction
4. Add US6 (Rate limit adapter) → Test independently → Polling loop updated
5. Add US4 (OAuth migration) → Test independently → github_auth.py simplified
6. Add US5 (Delete infrastructure) → Test independently → Final ~400 LOC cleanup
7. Polish → Docs + verification → **Total: ~1,500–2,000 net LOC reduction**

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + US1 together (required foundation)
2. Once US1 is done:
   - Developer A: US2 (REST replacement) — service.py focus
   - Developer B: US3 (GraphQL simplify) — service.py focus (coordinate with A)
   - Developer C: US6 (Rate limit adapter) — client_factory.py + polling_loop.py
   - Developer D: US4 (OAuth migration) — github_auth.py focus
3. Once all four are merged → US5 (Delete infrastructure) — safe cleanup
4. Polish: Documentation and final verification

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability (US1–US6)
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- httpx remains a direct dependency for signal services (R-009) — "zero httpx imports" applies only to GitHub service code
- github_auth.py target is ~270 LOC (not 100 LOC) per research R-004 — session management is application logic
- BoundedDict from `src/utils.py` is reused for client pool — no new data structure needed
- All 31 GraphQL query/mutation strings in graphql.py are compatible with githubkit as-is (R-006)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
