# Tasks: Codebase Cleanup & Refactor

**Input**: Design documents from `/specs/001-codebase-cleanup-refactor/`
**Prerequisites**: spec.md (required — user stories with priorities P1–P3)

**Tests**: Tests ARE explicitly requested in User Story 7 (P3). Test tasks are included in Phase 9.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`, `backend/tests/integration/`
- **Frontend tests**: `frontend/src/hooks/*.test.tsx`, `frontend/src/components/*.test.tsx`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new directories and module scaffolding for the refactored sub-modules

- [ ] T001 Create backend sub-module directories: `backend/src/services/github/` with `__init__.py`, `backend/src/services/polling/` with `__init__.py`, `backend/src/services/workflow/` with `__init__.py`
- [ ] T002 [P] Create shared utilities directory `backend/src/services/shared/` with `__init__.py` for cross-cutting shared helpers
- [ ] T003 [P] Create frontend shared client directory `frontend/src/services/` (already exists — verify) and plan `frontend/src/services/httpClient.ts` file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared utilities and infrastructure that ALL user stories depend on before splitting modules

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create shared repository-resolution utility in `backend/src/services/shared/repo_resolution.py` — extract the common pattern (try GitHub API → try workflow config → fall back to settings) found in `backend/src/api/tasks.py:21-43`, `backend/src/api/chat.py:53-83`, `backend/src/api/workflow.py:609-650`, and `backend/src/api/projects.py:154-170`
- [ ] T005 [P] Create shared cache-key builder in `backend/src/services/shared/cache_keys.py` — consolidate cache key helpers currently split between `backend/src/constants.py` (cache_key_issue_pr, cache_key_agent_output, cache_key_review_requested) and `backend/src/services/cache.py` (get_cache_key, get_user_projects_cache_key, get_project_items_cache_key) into one module
- [ ] T006 [P] Create backend constants/config consolidation module `backend/src/constants.py` — audit all hardcoded magic numbers (timeouts, retry counts, TTLs, polling intervals, pagination limits, batch sizes) across `backend/src/services/` and `backend/src/api/` and define named constants; update `backend/src/config.py` for environment-driven values
- [ ] T007 Create unified error-handling middleware in `backend/src/exceptions.py` — extend the existing AppException hierarchy and ensure `backend/src/main.py` registers exception handlers that map all domain exceptions to a consistent sanitized JSON response `{status_code, error, message}` with server-side-only logging of diagnostics

**Checkpoint**: Foundation ready — shared utilities, constants, and error handling in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Break Apart Oversized Modules (Priority: P1) 🎯 MVP

**Goal**: Split `github_projects.py` (~4,448 lines), `copilot_polling.py` (~3,987 lines), and `workflow_orchestrator.py` (~1,959 lines) into focused sub-modules each under ~500 lines, with thin re-export facades at original paths.

**Independent Test**: All existing unit and integration tests pass unchanged; each new module has a docstring describing its single responsibility.

### Implementation for User Story 1

#### Split `github_projects.py` → `backend/src/services/github/`

- [ ] T008 [US1] Extract HTTP/GraphQL layer into `backend/src/services/github/client.py` — move `__init__`, `close`, `_request_with_retry`, `_graphql` (~150 lines)
- [ ] T009 [P] [US1] Extract project discovery & listing into `backend/src/services/github/projects.py` — move `list_user_projects`, `list_org_projects`, `_parse_projects`, `get_project_items`, `list_board_projects`, `get_board_data` (~400 lines)
- [ ] T010 [P] [US1] Extract issue management into `backend/src/services/github/issues.py` — move `create_issue`, `update_issue_body`, `update_issue_state`, `add_issue_to_project`, `assign_issue`, `get_issue_with_comments`, `format_issue_context_as_prompt`, `check_agent_completion_comment`, `create_issue_comment` (~450 lines)
- [ ] T011 [P] [US1] Extract sub-issue management into `backend/src/services/github/sub_issues.py` — move `create_sub_issue`, `get_sub_issues`, `tailor_body_for_agent` (~200 lines)
- [ ] T012 [P] [US1] Extract Copilot assignment logic into `backend/src/services/github/copilot_assignment.py` — move `get_copilot_bot_id`, `assign_copilot_to_issue`, `_assign_copilot_rest`, `_assign_copilot_graphql`, `is_copilot_assigned_to_issue`, `unassign_copilot_from_issue` (~400 lines)
- [ ] T013 [P] [US1] Extract PR management into `backend/src/services/github/pull_requests.py` — move `find_existing_pr_for_issue`, `_search_open_prs_for_issue_rest`, `get_linked_pull_requests`, `get_pull_request`, `mark_pr_ready_for_review`, `request_copilot_review`, `merge_pull_request`, `delete_branch`, `update_pr_base`, `link_pull_request_to_issue`, `has_copilot_reviewed_pr`, `get_pr_timeline_events`, `_check_copilot_finished_events`, `check_copilot_pr_completion` (~500 lines)
- [ ] T014 [P] [US1] Extract project field management into `backend/src/services/github/project_fields.py` — move `get_project_fields`, `update_project_item_field`, `set_issue_metadata`, `update_item_status`, `update_item_status_by_name`, `update_sub_issue_project_status`, `create_draft_item` (~350 lines)
- [ ] T015 [P] [US1] Extract repository/user validation and file retrieval into `backend/src/services/github/repo_utils.py` — move `validate_assignee`, `get_repository_owner`, `get_project_repository`, `get_pr_changed_files`, `get_file_content_from_ref`, `list_available_agents` (~300 lines)
- [ ] T016 [P] [US1] Extract change detection and project polling into `backend/src/services/github/change_detection.py` — move `_detect_changes`, `poll_project_changes` (~200 lines)
- [ ] T017 [US1] Convert `backend/src/services/github_projects.py` into a thin re-export facade — import all public symbols from sub-modules and re-export them, preserving `github_projects_service` singleton; verify no external behavior change

#### Split `copilot_polling.py` → `backend/src/services/polling/`

- [ ] T018 [P] [US1] Extract polling lifecycle into `backend/src/services/polling/lifecycle.py` — move `poll_for_copilot_completion`, `_poll_loop`, `stop_polling`, `get_polling_status`, `PollingState` dataclass (~250 lines)
- [ ] T019 [P] [US1] Extract issue tracking & body management into `backend/src/services/polling/issue_tracking.py` — move `_get_sub_issue_number`, `_check_agent_done_on_sub_or_parent`, `_update_issue_tracking`, `_get_tracking_state_from_issue`, `_reconstruct_sub_issue_mappings` (~300 lines)
- [ ] T020 [P] [US1] Extract pipeline state management into `backend/src/services/polling/pipeline.py` — move `_get_or_reconstruct_pipeline`, `_reconstruct_pipeline_state`, `_advance_pipeline`, `_transition_after_pipeline_complete` (~350 lines)
- [ ] T021 [P] [US1] Extract status-specific polling handlers into `backend/src/services/polling/status_handlers.py` — move `check_backlog_issues`, `check_ready_issues`, `check_in_progress_issues`, `process_in_progress_issue` (~500 lines)
- [ ] T022 [P] [US1] Extract PR completion detection into `backend/src/services/polling/pr_completion.py` — move `_merge_child_pr_if_applicable`, `_find_completed_child_pr`, `_check_child_pr_completion`, `_check_main_pr_completion`, `_filter_events_after` (~400 lines)
- [ ] T023 [P] [US1] Extract agent output processing and review into `backend/src/services/polling/agent_output.py` — move `post_agent_outputs_from_pr`, `_process_pipeline_completion`, `check_in_review_issues_for_copilot_review`, `ensure_copilot_review_requested`, `recover_stalled_issues`, `check_issue_for_copilot_completion` (~400 lines)
- [ ] T024 [US1] Convert `backend/src/services/copilot_polling.py` into a thin re-export facade — import all public symbols from sub-modules and re-export them; verify no external behavior change

#### Split `workflow_orchestrator.py` → `backend/src/services/workflow/`

- [ ] T025 [P] [US1] Extract workflow configuration management into `backend/src/services/workflow/config.py` — move `get_workflow_config`, `set_workflow_config`, `_load_workflow_config_from_db`, `_persist_workflow_config_to_db` (~150 lines)
- [ ] T026 [P] [US1] Extract pipeline state tracking into `backend/src/services/workflow/state.py` — move `PipelineState`, `get_pipeline_state`, `set_pipeline_state`, `remove_pipeline_state`, `get_issue_main_branch`, `set_issue_main_branch`, `clear_issue_main_branch`, `update_issue_main_branch_sha`, `get_transitions`, `MainBranchInfo`, `WorkflowState`, `WorkflowContext`, `WorkflowTransition` data classes (~250 lines)
- [ ] T027 [P] [US1] Extract workflow execution core into `backend/src/services/workflow/execution.py` — move `create_issue_from_recommendation`, `add_to_project_with_backlog`, `transition_to_ready`, `assign_agent_for_status`, `handle_ready_status`, `handle_in_progress_status`, `handle_completion`, `execute_full_workflow` (~500 lines)
- [ ] T028 [P] [US1] Extract workflow helpers/utilities into `backend/src/services/workflow/helpers.py` — move `format_issue_body`, `_update_agent_tracking_state`, `log_transition`, `create_all_sub_issues`, `detect_completion_signal`, `_set_issue_metadata`, `get_status_order`, `get_agent_slugs`, `get_next_status`, `find_next_actionable_status` (~400 lines)
- [ ] T029 [US1] Convert `backend/src/services/workflow_orchestrator.py` into a thin re-export facade — import all public symbols from sub-modules and re-export them; preserve `get_workflow_orchestrator` singleton; verify no external behavior change

#### Verify Split Integrity

- [ ] T030 [US1] Update all internal imports across `backend/src/api/` and `backend/src/services/` to import directly from new sub-modules instead of the facade (facades are for backward compatibility only)
- [ ] T031 [US1] Run full backend test suite (`cd backend && python -m pytest`) — confirm all existing tests pass with zero assertion changes
- [ ] T032 [US1] Verify every new sub-module has a module-level docstring describing its single responsibility

**Checkpoint**: User Story 1 complete — all three oversized modules split into focused sub-modules under ~500 lines each; all tests pass.

---

## Phase 4: User Story 2 — Eliminate Duplicated Code Patterns (Priority: P1)

**Goal**: Consolidate duplicated repository-resolution, polling-initialization, session-management, and cache-key-construction logic so each pattern exists in exactly one place.

**Independent Test**: Search codebase for previously-duplicated patterns; each exists in exactly one location with all callers using the shared version.

### Implementation for User Story 2

- [ ] T033 [US2] Replace duplicate repository-resolution in `backend/src/api/tasks.py` (`_resolve_repository_for_project`) with call to shared utility from `backend/src/services/shared/repo_resolution.py` (created in T004)
- [ ] T034 [P] [US2] Replace duplicate repository-resolution in `backend/src/api/chat.py` (`_resolve_repository`) with call to shared utility from `backend/src/services/shared/repo_resolution.py`
- [ ] T035 [P] [US2] Replace duplicate repository-resolution in `backend/src/api/workflow.py` (`start_copilot_polling` repo-resolution block) with call to shared utility
- [ ] T036 [P] [US2] Replace duplicate repository-resolution in `backend/src/api/projects.py` (`_start_copilot_polling` repo-resolution block) with call to shared utility
- [ ] T037 [US2] Consolidate polling-initialization logic — deduplicate `backend/src/api/projects.py:_start_copilot_polling` and `backend/src/api/workflow.py:start_copilot_polling` into a single entry point in `backend/src/services/shared/polling_init.py`; update both callers
- [ ] T038 [P] [US2] Consolidate cache-key construction — ensure all callers reference the unified module from `backend/src/services/shared/cache_keys.py` (created in T005); remove any remaining scattered inline cache-key construction
- [ ] T039 [US2] Run full backend test suite to confirm all existing tests pass after deduplication

**Checkpoint**: User Story 2 complete — all duplicated patterns consolidated; each business operation exists in exactly one location.

---

## Phase 5: User Story 3 — Standardize Error Handling (Priority: P2)

**Goal**: All API endpoints use a unified error-handling approach; all error responses follow a consistent sanitized structure; no exceptions silently swallowed.

**Independent Test**: Trigger known error conditions in each endpoint; verify response format `{status_code, error, message}`, correct HTTP status, and server-side diagnostic logging.

### Implementation for User Story 3

- [ ] T040 [US3] Audit all `backend/src/api/*.py` route handlers — catalog every `raise HTTPException`, `raise AppException`, and bare `except` block; document which need migration
- [ ] T041 [US3] Update `backend/src/main.py` exception handlers (from T007) to ensure every `AppException` subclass maps to the consistent response shape `{"error": "<type>", "message": "<user-safe>", "detail": null}`; add catch-all handler for unexpected exceptions → 500 with generic message and full server-side logging
- [ ] T042 [P] [US3] Refactor `backend/src/api/webhooks.py` — replace raw `HTTPException` raises with domain exceptions from `backend/src/exceptions.py`; remove any silent exception swallowing
- [ ] T043 [P] [US3] Refactor `backend/src/api/workflow.py` — replace mixed error patterns with domain exceptions; ensure all caught exceptions are logged before propagation
- [ ] T044 [P] [US3] Refactor `backend/src/api/chat.py` — replace mixed error patterns with domain exceptions; ensure consistent error response shape
- [ ] T045 [P] [US3] Refactor `backend/src/api/projects.py` — replace raw HTTPException raises with domain exceptions
- [ ] T046 [P] [US3] Refactor `backend/src/api/tasks.py` and `backend/src/api/board.py` — replace mixed error patterns with domain exceptions
- [ ] T047 [P] [US3] Refactor `backend/src/api/settings.py` and `backend/src/api/auth.py` — replace any remaining HTTPException raises with domain exceptions
- [ ] T048 [US3] Audit service files (`backend/src/services/`) — replace any silent `except: pass` or bare `except Exception` blocks with explicit logging + propagation; ensure no stack traces leak to client
- [ ] T049 [US3] Run full backend test suite to confirm error handling changes preserve behavior

**Checkpoint**: User Story 3 complete — unified error handling across all endpoints.

---

## Phase 6: User Story 4 — Consolidate Hardcoded Values and Magic Numbers (Priority: P2)

**Goal**: All magic numbers, timeouts, retry counts, cache TTLs, and default limits moved to named constants in `backend/src/constants.py` or `backend/src/config.py`.

**Independent Test**: Search codebase for numeric literals and string constants in business logic; all reference named constants or configuration values.

### Implementation for User Story 4

- [ ] T050 [US4] Audit `backend/src/services/github/` sub-modules for hardcoded numeric literals (retry counts, timeouts, pagination limits, batch sizes) — extract to named constants in `backend/src/constants.py`
- [ ] T051 [P] [US4] Audit `backend/src/services/polling/` sub-modules for hardcoded values (polling intervals, max retries, stall thresholds) — extract to named constants in `backend/src/constants.py`
- [ ] T052 [P] [US4] Audit `backend/src/services/workflow/` sub-modules for hardcoded values — extract to named constants
- [ ] T053 [P] [US4] Audit `backend/src/api/*.py` for hardcoded values (pagination defaults, rate limits, timeout values) — replace with named constants from `backend/src/constants.py`
- [ ] T054 [P] [US4] Audit `backend/src/services/cache.py` for inline TTL values — ensure all cache durations reference `backend/src/config.py` or `backend/src/constants.py`
- [ ] T055 [US4] Document all extracted constants with inline comments explaining their purpose in `backend/src/constants.py`
- [ ] T056 [US4] Run full backend test suite to confirm constant extraction preserves behavior

**Checkpoint**: User Story 4 complete — zero magic numbers in business logic.

---

## Phase 7: User Story 5 — Unify Frontend API Communication Layer (Priority: P2)

**Goal**: All frontend API calls route through a shared HTTP client with automatic auth headers (lazy lookup), base URL config, and consistent error handling.

**Independent Test**: Verify all API calls use shared client; zero direct `fetch()` calls outside the client module.

### Implementation for User Story 5

- [ ] T057 [US5] Create shared HTTP client in `frontend/src/services/httpClient.ts` — wraps `fetch()` with automatic base URL from `VITE_API_BASE_URL`, lazy auth-token lookup from centralized auth context, consistent error parsing (ApiError), 401 redirect handling, and network error handling
- [ ] T058 [US5] Refactor `frontend/src/services/api.ts` — replace internal `fetch()` calls with the shared HTTP client from `frontend/src/services/httpClient.ts`; preserve all existing API function signatures
- [ ] T059 [P] [US5] Refactor `frontend/src/hooks/useWorkflow.ts` — replace direct `fetch()` calls with API functions from `frontend/src/services/api.ts` (which now uses the shared client)
- [ ] T060 [P] [US5] Refactor `frontend/src/hooks/useAgentConfig.ts` — replace any direct `fetch()` calls (in `useAvailableAgents`) with API functions from `frontend/src/services/api.ts`
- [ ] T061 [US5] Verify zero remaining direct `fetch()` calls outside `frontend/src/services/httpClient.ts` — search all `frontend/src/` files for `fetch(` usage
- [ ] T062 [US5] Run frontend build (`cd frontend && npm run build`) and existing frontend tests (`cd frontend && npm test`) to confirm no regressions

**Checkpoint**: User Story 5 complete — all API calls flow through shared HTTP client.

---

## Phase 8: User Story 6 — Improve Frontend State Management and Resilience (Priority: P3)

**Goal**: Error boundaries prevent blank screens; sessionStorage persists essential navigation state; WebSocket-primary with polling fallback (no simultaneous dual channels).

**Independent Test**: Page refresh preserves project selection and board context; simulated failures display fallback UI; WebSocket disconnect triggers polling, reconnect stops it.

### Implementation for User Story 6

- [ ] T063 [US6] Create `ErrorBoundary` component in `frontend/src/components/common/ErrorBoundary.tsx` — React class component that catches rendering errors and displays fallback UI (error message + Retry/Reload button)
- [ ] T064 [US6] Wrap top-level routes in `frontend/src/App.tsx` with the `ErrorBoundary` component to prevent blank screens
- [ ] T065 [P] [US6] Add `sessionStorage` persistence for selected project ID and board context in `frontend/src/hooks/useProjectBoard.ts` — save on change, restore on mount; scoped per tab
- [ ] T066 [P] [US6] Add `sessionStorage` persistence for active chat context in `frontend/src/hooks/useChat.ts` — save selected project/issue on change, restore on mount
- [ ] T067 [US6] Refactor `frontend/src/hooks/useRealTimeSync.ts` — ensure WebSocket is the primary real-time channel; automatic polling fallback on disconnect that ceases when WebSocket reconnects; no data stream uses both channels simultaneously (review existing implementation and fix if needed)
- [ ] T068 [US6] Run frontend build and existing tests to confirm no regressions

**Checkpoint**: User Story 6 complete — resilient frontend with error boundaries, session persistence, and clean WebSocket/polling fallback.

---

## Phase 9: User Story 7 — Increase Test Coverage for Untested Modules (Priority: P3)

**Goal**: Unit tests for 5 untested backend services and 6 untested frontend hooks.

**Independent Test**: Run test suite; coverage reports show tests exist for all previously-untested modules.

### Backend Tests

- [ ] T069 [P] [US7] Create `backend/tests/unit/test_completion_providers.py` — unit tests for `CopilotCompletionProvider`, `AzureOpenAICompletionProvider`, and `create_completion_provider` factory covering primary functions and edge cases (mock HTTP calls)
- [ ] T070 [P] [US7] Create `backend/tests/unit/test_session_store.py` — unit tests for `save_session`, `get_session`, `delete_session`, `get_sessions_by_user`, `purge_expired_sessions` with mock database
- [ ] T071 [P] [US7] Create `backend/tests/unit/test_settings_store.py` — unit tests for `get_global_settings`, `update_global_settings`, `get_effective_user_settings`, `get_effective_project_settings`, `upsert_user_preferences` with mock database
- [ ] T072 [P] [US7] Create `backend/tests/unit/test_agent_tracking.py` — unit tests for `build_agent_pipeline_steps`, `render_tracking_markdown`, `parse_tracking_from_body`, `get_current_agent_from_tracking`, `get_next_pending_agent`, `determine_next_action`, `mark_agent_active`, `mark_agent_done`
- [ ] T073 [P] [US7] Expand `backend/tests/unit/test_workflow_orchestrator.py` — add tests for `execute_full_workflow`, `transition_to_ready`, `handle_completion`, `detect_completion_signal`, and pipeline state management functions not currently covered

### Frontend Tests

- [ ] T074 [P] [US7] Create `frontend/src/hooks/useSettings.test.tsx` — tests for `useUserSettings`, `useGlobalSettings`, `useProjectSettings` verifying fetch, update, and error behavior (using `renderHook` + `QueryClientProvider` wrapper + `vi.mock`)
- [ ] T075 [P] [US7] Create `frontend/src/hooks/useWorkflow.test.tsx` — tests for `useWorkflow` verifying workflow recommendation confirm/reject and configuration get/update
- [ ] T076 [P] [US7] Create `frontend/src/hooks/useAgentConfig.test.tsx` — tests for `useAgentConfig` and `useAvailableAgents` verifying agent mapping state, dirty tracking, save/discard, and agent listing
- [ ] T077 [P] [US7] Create `frontend/src/hooks/useChat.test.tsx` — tests for `useChat` verifying message send, task proposal confirm/reject, and status change handling
- [ ] T078 [P] [US7] Create `frontend/src/hooks/useProjectBoard.test.tsx` — tests for `useProjectBoard` verifying project list fetch, board data fetch, and polling behavior
- [ ] T079 [P] [US7] Create `frontend/src/hooks/useAppTheme.test.tsx` — tests for `useAppTheme` verifying theme toggle, API sync when authenticated, and localStorage fallback

### Run Tests

- [ ] T080 [US7] Run full backend test suite (`cd backend && python -m pytest --cov`) — confirm all new and existing tests pass
- [ ] T081 [US7] Run full frontend test suite (`cd frontend && npm test -- --coverage`) — confirm all new and existing tests pass

**Checkpoint**: User Story 7 complete — all five backend services and six frontend hooks have dedicated test coverage.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [ ] T082 [P] Add module-level docstrings to every new sub-module under `backend/src/services/github/`, `backend/src/services/polling/`, `backend/src/services/workflow/`, and `backend/src/services/shared/` — each must have a single-sentence description of its responsibility
- [ ] T083 [P] Verify no backend source file (excluding tests and generated files) exceeds ~500 lines — `find backend/src -name "*.py" -exec wc -l {} + | sort -rn`
- [ ] T084 Run full end-to-end test suite (`cd backend && python -m pytest && cd ../frontend && npm test && npm run build`) — confirm all tests pass and application builds cleanly
- [ ] T085 Verify re-export facades (`backend/src/services/github_projects.py`, `backend/src/services/copilot_polling.py`, `backend/src/services/workflow_orchestrator.py`) expose identical public APIs as before the split

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — Module splits
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) — Can start after Phase 2, but ideally after US1 (Phase 3) since deduplication is easier once modules are split
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — Can run in parallel with US2
- **US4 (Phase 6)**: Depends on Foundational (Phase 2) — Can run in parallel with US2/US3
- **US5 (Phase 7)**: No backend dependencies — Can start after Setup
- **US6 (Phase 8)**: Depends on US5 (shared HTTP client) for consistency
- **US7 (Phase 9)**: Depends on US1 (new module structure) for backend tests; can start frontend tests in parallel with US5/US6
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — Benefits from US1 completion but not strictly required
- **US3 (P2)**: Can start after Phase 2 — Independent of US1/US2
- **US4 (P2)**: Can start after Phase 2 — Independent of other stories
- **US5 (P2)**: Frontend-only — Independent of backend stories
- **US6 (P3)**: Depends on US5 for shared client — Otherwise independent
- **US7 (P3)**: Backend tests benefit from US1 structure; frontend tests benefit from US5/US6

### Within Each User Story

- Shared utilities/infrastructure before consumers
- Models/types before services
- Services before endpoints/hooks
- Core implementation before integration
- Test suite validation at each checkpoint

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- US3, US4, and US5 can run in parallel after Phase 2 completion
- Within US1: All sub-module extractions for different files/directories marked [P] can run in parallel
- Within US7: All backend test tasks [P] can run in parallel; all frontend test tasks [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all github_projects sub-module extractions in parallel:
Task T009: "Extract project discovery into backend/src/services/github/projects.py"
Task T010: "Extract issue management into backend/src/services/github/issues.py"
Task T011: "Extract sub-issue management into backend/src/services/github/sub_issues.py"
Task T012: "Extract Copilot assignment into backend/src/services/github/copilot_assignment.py"
Task T013: "Extract PR management into backend/src/services/github/pull_requests.py"
Task T014: "Extract project field management into backend/src/services/github/project_fields.py"
Task T015: "Extract repo utilities into backend/src/services/github/repo_utils.py"
Task T016: "Extract change detection into backend/src/services/github/change_detection.py"

# Then sequentially:
Task T017: "Convert github_projects.py into thin re-export facade"
```

## Parallel Example: User Story 7

```bash
# Launch all backend test creation tasks in parallel:
Task T069: "Create test_completion_providers.py"
Task T070: "Create test_session_store.py"
Task T071: "Create test_settings_store.py"
Task T072: "Create test_agent_tracking.py"
Task T073: "Expand test_workflow_orchestrator.py"

# Launch all frontend test creation tasks in parallel:
Task T074: "Create useSettings.test.tsx"
Task T075: "Create useWorkflow.test.tsx"
Task T076: "Create useAgentConfig.test.tsx"
Task T077: "Create useChat.test.tsx"
Task T078: "Create useProjectBoard.test.tsx"
Task T079: "Create useAppTheme.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 — Break Apart Oversized Modules
4. **STOP and VALIDATE**: Run full test suite; verify all modules under ~500 lines
5. Deploy/demo if ready — codebase is already significantly more maintainable

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → MVP! (modules split, navigable codebase)
3. Add User Story 2 → Test → DRY codebase (no more duplicated patterns)
4. Add User Stories 3 + 4 → Test → Consistent errors + no magic numbers
5. Add User Story 5 → Test → Unified frontend API layer
6. Add User Story 6 → Test → Resilient frontend
7. Add User Story 7 → Test → Full test safety net

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend module splits)
   - Developer B: User Story 5 (frontend HTTP client) + User Story 6 (frontend resilience)
3. After US1 completes:
   - Developer A: User Stories 2 + 3 + 4 (backend DRY + errors + constants)
   - Developer B: User Story 7 (frontend tests)
4. Developer A: User Story 7 (backend tests)
5. All: Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Facades at original paths ensure backward compatibility for any external consumers
- The ~500 line limit is a guideline; a module may slightly exceed this if splitting further harms cohesion
