# Tasks: Simplify GitHub Service with githubkit

**Input**: Design documents from `/specs/020-githubkit-migration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Existing test mock-targets updated where needed (not test-first).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add githubkit dependency, remove httpx direct dependency

- [x] T001 Add `githubkit>=0.14.0` to dependencies and remove `httpx>=0.26.0` in backend/pyproject.toml
- [x] T002 Run `pip install -e .` to install githubkit and verify import in backend/.venv

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the GitHubClientFactory and simplified `_graphql()` wrapper that ALL subsequent user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement `GitHubClientFactory` class with `get_client()` and `close_all()` in backend/src/services/github_projects/__init__.py
- [x] T004 Update `GitHubProjectsService.__init__()` to accept `client_factory: GitHubClientFactory` parameter, add `_client_factory` field, preserve domain-specific fields (`_cycle_cache`, `_inflight_graphql`, metrics counters) in backend/src/services/github_projects/service.py
- [x] T005 Rewrite `_graphql()` method to delegate to SDK's `async_graphql()` for standard calls and `arequest("POST", "/graphql", ...)` for calls requiring `GraphQL-Features` headers, preserving inflight coalescing in backend/src/services/github_projects/service.py
- [x] T006 Simplify `get_last_rate_limit()` to extract rate-limit info from last SDK response headers (preserve contextvar + instance-level dual storage, same return shape `dict[str, int] | None`) in backend/src/services/github_projects/service.py
- [x] T007 Update `GitHubProjectsService` and `GitHubClientFactory` initialization in backend/src/dependencies.py to create factory at startup and pass to service constructor
- [x] T008 Update `close()` method to delegate to `self._client_factory.close_all()` in backend/src/services/github_projects/service.py

**Checkpoint**: Foundation ready — SDK client factory works, `_graphql()` delegates to SDK, service initializes correctly. User story implementation can begin.

---

## Phase 3: User Story 1 — SDK Foundation and Client Factory (Priority: P1) 🎯 MVP

**Goal**: All GraphQL-based operations work through the new SDK client factory

**Independent Test**: Run full backend test suite — all GraphQL-dependent operations (list projects, get items, assign Copilot, poll) pass

### Implementation for User Story 1

- [x] T009 [US1] Migrate `list_user_projects()` and `list_org_projects()` to use `self._client_factory.get_client(access_token)` and `_graphql()` SDK delegation in backend/src/services/github_projects/service.py
- [x] T010 [US1] Migrate `get_project_items()` to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T011 [US1] Migrate `list_board_projects()` and `get_board_data()` to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T012 [US1] Migrate `get_copilot_bot_id()` to use SDK client via `_graphql()` with `graphql_features` parameter in backend/src/services/github_projects/service.py
- [x] T013 [US1] Migrate `assign_copilot_to_issue()` / `_assign_copilot_graphql()` to use SDK client via `_graphql()` with `graphql_features` parameter in backend/src/services/github_projects/service.py
- [x] T014 [US1] Migrate `get_issue_with_comments()` and `get_linked_pull_requests()` to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T015 [US1] Migrate `get_pull_request()` and `find_existing_pr_for_issue()` GraphQL parts to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T016 [US1] Migrate `get_repository_info()`, `create_branch()`, `get_branch_head_oid()`, `commit_files()`, `create_pull_request()` to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T017 [US1] Migrate `create_draft_item()`, `update_item_status()`, `add_issue_to_project()`, `_verify_item_on_project()`, `get_project_fields()`, `update_project_item_field()` to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T018 [US1] Migrate `mark_pr_ready_for_review()`, `merge_pull_request()`, `request_copilot_review()` GraphQL fallback, `_reconcile_board_items()` to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T019 [US1] Migrate `poll_project_changes()`, `_detect_changes()` to use SDK client via `_graphql()` in backend/src/services/github_projects/service.py
- [x] T020 [US1] Migrate `list_available_agents()` to use SDK client via `arequest()` for REST part in backend/src/services/github_projects/service.py

**Checkpoint**: All GraphQL and SDK-client-dependent methods work. `_graphql()` routes through SDK. Inflight coalescing and cycle cache preserved.

---

## Phase 4: User Story 2 — Typed REST API Call Replacement (Priority: P1)

**Goal**: All manually-constructed REST API calls replaced with typed SDK methods or `arequest()`

**Independent Test**: Each replaced REST call can be unit-tested by verifying the SDK method produces the same domain result

### Implementation for User Story 2

#### Issue Operations
- [x] T021 [P] [US2] Replace `create_issue()` raw httpx POST with `client.rest.issues.async_create()` in backend/src/services/github_projects/service.py
- [x] T022 [P] [US2] Replace `update_issue_body()` raw httpx PATCH with `client.rest.issues.async_update()` in backend/src/services/github_projects/service.py
- [x] T023 [P] [US2] Replace `update_issue_state()` raw httpx PATCH (state + labels) with `client.rest.issues.async_update()` and typed label methods in backend/src/services/github_projects/service.py
- [x] T024 [P] [US2] Replace `assign_issue()` raw httpx PATCH with `client.rest.issues.async_update(assignees=[...])` in backend/src/services/github_projects/service.py
- [x] T025 [P] [US2] Replace `check_issue_closed()` raw httpx GET with `client.rest.issues.async_get()` and check `.state` in backend/src/services/github_projects/service.py
- [x] T026 [P] [US2] Replace `is_copilot_assigned_to_issue()` raw httpx GET with `client.rest.issues.async_get()` and check `.assignees` in backend/src/services/github_projects/service.py
- [x] T027 [P] [US2] Replace `unassign_copilot_from_issue()` raw httpx DELETE with `client.rest.issues.async_remove_assignees()` in backend/src/services/github_projects/service.py
- [x] T028 [P] [US2] Replace `validate_assignee()` raw httpx GET with `client.rest.issues.async_check_user_can_be_assigned()` in backend/src/services/github_projects/service.py
- [x] T029 [P] [US2] Replace `create_issue_comment()` raw httpx POST with `client.rest.issues.async_create_comment()` in backend/src/services/github_projects/service.py

#### Pull Request Operations
- [x] T030 [P] [US2] Replace `request_copilot_review()` REST primary path raw httpx POST with `client.rest.pulls.async_request_reviewers()` in backend/src/services/github_projects/service.py
- [x] T031 [P] [US2] Replace `delete_branch()` raw httpx DELETE with `client.rest.git.async_delete_ref()` in backend/src/services/github_projects/service.py
- [x] T032 [P] [US2] Replace `update_pr_base()` and `link_pull_request_to_issue()` raw httpx PATCH with `client.rest.pulls.async_update()` in backend/src/services/github_projects/service.py
- [x] T033 [P] [US2] Replace `get_pr_changed_files()` raw httpx GET with `client.rest.pulls.async_list_files()` using SDK pagination in backend/src/services/github_projects/service.py
- [x] T034 [P] [US2] Replace `has_copilot_reviewed_pr()` raw httpx GET logic to use SDK typed PR review methods in backend/src/services/github_projects/service.py

#### Repository & Content Operations
- [x] T035 [P] [US2] Replace `get_repository_owner()` raw httpx GET with `client.rest.repos.async_get()` in backend/src/services/github_projects/service.py
- [x] T036 [P] [US2] Replace `get_directory_contents()`, `get_file_content()`, `get_file_content_from_ref()` raw httpx GET with `client.rest.repos.async_get_content()` in backend/src/services/github_projects/service.py
- [x] T037 [P] [US2] Replace `get_pr_timeline_events()` raw httpx GET with `client.rest.issues.async_list_events_for_timeline()` in backend/src/services/github_projects/service.py

#### Preview API Operations (generic arequest)
- [x] T038 [P] [US2] Replace `_assign_copilot_rest()` raw httpx POST with `client.arequest("POST", ...)` in backend/src/services/github_projects/service.py
- [x] T039 [P] [US2] Replace `create_sub_issue()` and `get_sub_issues()` raw httpx calls with `client.arequest()` in backend/src/services/github_projects/service.py
- [x] T040 [P] [US2] Replace `_add_issue_to_project_rest()` and `_get_project_rest_info()` raw httpx calls with `client.arequest()` in backend/src/services/github_projects/service.py
- [x] T041 [P] [US2] Replace `_search_open_prs_for_issue_rest()` raw httpx GET with `client.rest.pulls.async_list()` in backend/src/services/github_projects/service.py

#### Exception Migration
- [x] T042 [US2] Replace all `httpx.HTTPStatusError` catches in service.py (5 sites) with `RequestFailed` from `githubkit.exception` in backend/src/services/github_projects/service.py
- [x] T043 [US2] Replace `httpx.HTTPError` catch with `RequestError` from `githubkit.exception` in backend/src/services/github_projects/service.py
- [x] T044 [P] [US2] Replace `isinstance(exc, httpx.HTTPStatusError)` checks (2 sites) with `isinstance(exc, RequestFailed)` in backend/src/api/board.py
- [x] T045 [P] [US2] Replace `httpx.HTTPStatusError` and `httpx.ConnectError` catches with `RequestFailed` and `RequestError` in backend/src/services/metadata_service.py

**Checkpoint**: All REST calls use SDK typed methods or `arequest()`. All exception types migrated. No raw httpx URL construction remains.

---

## Phase 5: User Story 3 — OAuth Flow Simplification (Priority: P2)

**Goal**: OAuth web flow replaced with githubkit's built-in OAuth strategies

**Independent Test**: Full OAuth login flow: redirect → authorize → callback → token stored → API calls succeed

### Implementation for User Story 3

- [x] T046 [US3] Replace `exchange_code_for_token()` httpx POST with `OAuthWebAuthStrategy` + `async_exchange_token()` in backend/src/services/github_auth.py
- [x] T047 [US3] Replace `refresh_token()` httpx POST with `OAuthTokenAuthStrategy` + `async_refresh()` in backend/src/services/github_auth.py
- [x] T048 [US3] Replace `generate_oauth_url()` manual URL construction with SDK-based auth URL generation in backend/src/services/github_auth.py
- [x] T049 [US3] Remove `httpx.AsyncClient` from `GitHubAuthService.__init__()` and `close()` in backend/src/services/github_auth.py
- [x] T050 [US3] Remove `import httpx` from backend/src/services/github_auth.py

**Checkpoint**: OAuth flow uses SDK strategies. SQLite session persistence unchanged. CSRF state validation unchanged.

---

## Phase 6: User Story 4 — GraphQL Layer Simplification (Priority: P2)

**Goal**: Custom GraphQL wrapper simplified — ETag cache removed, error parsing delegated to SDK

**Independent Test**: Polling loop runs correctly, cycle cache prevents redundant queries, GraphQL-Features headers accepted

### Implementation for User Story 4

- [x] T051 [US4] Remove ETag cache logic (hash key generation, `_etag_cache` dict, 304 Not Modified handling, LRU eviction) from `_graphql()` in backend/src/services/github_projects/service.py
- [x] T052 [US4] Remove manual GraphQL error parsing from `_graphql()` — SDK's `async_graphql()` raises `GraphQLFailed` automatically in backend/src/services/github_projects/service.py
- [x] T053 [US4] Remove `extra_headers` parameter from `_graphql()` — replaced by `graphql_features` parameter routing to `arequest()` in backend/src/services/github_projects/service.py
- [x] T054 [US4] Remove `GITHUB_GRAPHQL_URL` constant usage from service.py — SDK handles the GraphQL endpoint URL in backend/src/services/github_projects/service.py
- [x] T055 [P] [US4] Remove `MAX_RETRIES`, `INITIAL_BACKOFF_SECONDS`, `MAX_BACKOFF_SECONDS` constants from backend/src/services/github_projects/graphql.py
- [x] T056 [P] [US4] Remove `GITHUB_GRAPHQL_URL` constant from backend/src/services/github_projects/graphql.py (verify no remaining imports)

**Checkpoint**: `_graphql()` is ~30 LOC. Inflight coalescing and cycle cache preserved. SDK handles caching, retry, error parsing.

---

## Phase 7: User Story 5 — Infrastructure Code Removal and Cleanup (Priority: P3)

**Goal**: Remove all deprecated infrastructure methods, fields, and imports

**Independent Test**: Full test suite passes, `grep -r "import httpx" backend/src/` returns zero GitHub-related hits

### Implementation for User Story 5

#### Remove Infrastructure Methods
- [x] T057 [P] [US5] Remove `_request_with_retry()` method from backend/src/services/github_projects/service.py
- [x] T058 [P] [US5] Remove `_build_headers()` static method from backend/src/services/github_projects/service.py
- [x] T059 [P] [US5] Remove `_extract_rate_limit_headers()` method from backend/src/services/github_projects/service.py
- [x] T060 [P] [US5] Remove `_parse_retry_after_seconds()` static method from backend/src/services/github_projects/service.py
- [x] T061 [P] [US5] Remove `_is_secondary_limit()` static method from backend/src/services/github_projects/service.py
- [x] T062 [P] [US5] Remove `_apply_global_cooldown()` and `_respect_global_cooldown()` methods from backend/src/services/github_projects/service.py
- [x] T063 [P] [US5] Remove `http_get()` public method from backend/src/services/github_projects/service.py
- [x] T064 [P] [US5] Remove `_maybe_log_request_management_metrics()` method (if no longer referenced) from backend/src/services/github_projects/service.py
- [x] T065 [P] [US5] Remove `clear_last_rate_limit()` method (if no longer referenced by polling service) from backend/src/services/github_projects/service.py

#### Remove Infrastructure Fields from Constructor
- [x] T066 [US5] Remove deprecated fields from `__init__()`: `_client`, `_etag_cache`, `_ETAG_CACHE_MAX_SIZE`, `_last_request_time`, `_min_request_interval`, `_global_cooldown_until`, `_cooldown_lock`, `_low_quota_threshold`, `_cooldown_hit_count` in backend/src/services/github_projects/service.py

#### Remove Imports and Constants
- [x] T067 [US5] Remove `import httpx` from backend/src/services/github_projects/service.py
- [x] T068 [P] [US5] Remove `import httpx` from backend/src/api/board.py — replace with `from githubkit.exception import RequestFailed`
- [x] T069 [P] [US5] Remove `import httpx` from backend/src/services/metadata_service.py — replace with githubkit exception imports
- [x] T070 [US5] Remove `API_ACTION_DELAY_SECONDS` constant if no longer used in backend/src/services/github_projects/service.py

#### Update Downstream Callers
- [x] T071 [US5] Update `github_commit_workflow.py` to use new service initialization pattern in backend/src/services/github_commit_workflow.py
- [x] T072 [P] [US5] Update any remaining `http_get()` callers to use SDK `arequest()` pattern across backend/src/

#### Update Test Mocks
- [x] T073 [US5] Update test mock targets from httpx to githubkit in backend/tests/ — replace `httpx.AsyncClient` mocks with githubkit client mocks

**Checkpoint**: All infrastructure code removed. No `import httpx` in GitHub-related production code. Line count reduced by ~1,500+.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation

- [x] T074 [P] Update architecture documentation to reference githubkit in docs/architecture.md
- [x] T075 [P] Update configuration documentation with new SDK config options in docs/configuration.md
- [x] T076 Run `ruff check backend/src/` and fix any lint issues
- [x] T077 Run `pyright` type checking and fix any type errors
- [x] T078 Run full test suite `pytest backend/tests/` and verify all pass
- [x] T079 Run `grep -r "import httpx" backend/src/ --include="*.py"` and verify zero GitHub-related hits
- [x] T080 Verify line count: `wc -l backend/src/services/github_projects/service.py backend/src/services/github_projects/graphql.py backend/src/services/github_auth.py` — target ≤5,100 total (down from ~6,400)
- [x] T081 Run quickstart.md validation steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — GraphQL migration via SDK
- **US2 (Phase 4)**: Depends on Phase 2 — REST call replacement (can run parallel with US1)
- **US3 (Phase 5)**: Depends on Phase 1 only — OAuth is independent (can run parallel with US1/US2)
- **US4 (Phase 6)**: Depends on Phase 3 (US1) — GraphQL cleanup after migration
- **US5 (Phase 7)**: Depends on Phases 3, 4, 5, 6 — cleanup after all migrations complete
- **Polish (Phase 8)**: Depends on Phase 7

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational — no dependencies on other stories
- **US2 (P1)**: Depends on Foundational — no dependencies on other stories. Can run **parallel** with US1
- **US3 (P2)**: Depends on Phase 1 only — can run **parallel** with US1 and US2
- **US4 (P2)**: Depends on US1 completion — simplifies the GraphQL layer after US1 migrates all queries
- **US5 (P3)**: Depends on US1 + US2 + US3 + US4 — final cleanup after all migrations

### Within Each User Story

- Task order within a story is sequential unless marked [P]
- [P] tasks within a story can run in parallel
- Exception migration tasks (T042-T045) should run after all REST replacements in their story

### Parallel Opportunities

- **US1 + US2 + US3** can all proceed in parallel after Phase 2 (Foundational)
- Within US2: All issue operations (T021-T029) can run in parallel
- Within US2: All PR operations (T030-T034) can run in parallel
- Within US2: All repo/content operations (T035-T037) can run in parallel
- Within US2: All preview API operations (T038-T041) can run in parallel
- Within US5: All method removals (T057-T065) can run in parallel
- Within US5: All import removals (T067-T069) can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all issue REST replacements in parallel:
Task T021: "Replace create_issue() with client.rest.issues.async_create()"
Task T022: "Replace update_issue_body() with client.rest.issues.async_update()"
Task T023: "Replace update_issue_state() with client.rest.issues.async_update()"
Task T024: "Replace assign_issue() with client.rest.issues.async_update()"
Task T025: "Replace check_issue_closed() with client.rest.issues.async_get()"

# After all REST replacements complete, run exception migration:
Task T042: "Replace httpx.HTTPStatusError catches with RequestFailed"
Task T043: "Replace httpx.HTTPError catches with RequestError"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T008)
3. Complete Phase 3: User Story 1 (T009-T020)
4. **STOP and VALIDATE**: All GraphQL operations work through SDK
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → SDK client factory works
2. US1 → All GraphQL through SDK → Validate
3. US2 → All REST through SDK → Validate (biggest LOC reduction)
4. US3 → OAuth through SDK → Validate
5. US4 → GraphQL layer cleanup → Validate
6. US5 → Remove dead infrastructure code → Validate (~1,500 LOC removed)
7. Polish → Docs + lint + type check + final line count

### Parallel Strategy

With capacity for parallel work:

1. Complete Setup + Foundational together
2. Once Foundational done, launch in parallel:
   - Track A: US1 (GraphQL migration)
   - Track B: US2 (REST migration)
   - Track C: US3 (OAuth migration)
3. After US1 completes: US4 (GraphQL cleanup)
4. After all US1-US4 complete: US5 (infrastructure removal)
5. Polish phase validates everything

---

## Notes

- Signal services (`signal_bridge.py`, `signal_delivery.py`) use httpx for Signal API — these are **out of scope**
- `api/health.py` has a local `import httpx` for liveness checks — verify if this should remain or migrate
- The `_with_fallback()` helper method is **preserved** — it's domain logic, not infrastructure
- `is_copilot_author()` and `is_copilot_swe_agent()` static methods are **preserved** — pure logic, no transport
- All 31 GraphQL query/mutation strings in `graphql.py` are **preserved** — only retry constants removed
