# Tasks: Codebase Cleanup & Refactor

**Input**: Design documents from `/specs/001-codebase-cleanup-refactor/`
**Prerequisites**: ✅ spec.md

**Tests**: Test tasks included in Phase 9 (User Story 7) as explicitly requested by FR-015 and FR-016.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/`
- **Frontend tests**: `frontend/src/hooks/*.test.tsx`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure for new sub-modules; no behavior changes

- [ ] T001 Create `backend/src/services/github_projects/` package directory with `__init__.py`
- [ ] T002 Create `backend/src/services/copilot_polling/` package directory with `__init__.py`
- [ ] T003 [P] Create `backend/src/services/workflow_orchestrator/` package directory with `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared utilities and infrastructure that MUST be complete before user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create shared repository-resolution utility in `backend/src/services/repo_resolution.py` — extract `_resolve_repository` pattern (project_id → owner, repo) from `backend/src/api/chat.py:53`, `backend/src/api/tasks.py:21`, `backend/src/api/workflow.py:146` into a single async function
- [ ] T005 [P] Create shared cache-key builder module in `backend/src/services/cache_keys.py` — consolidate helpers from `backend/src/constants.py` (`cache_key_issue_pr`, `cache_key_agent_output`, `cache_key_review_requested`) plus any inline `f"..."` cache-key patterns in service files into one module; update `backend/src/constants.py` to re-export from new location
- [ ] T006 [P] Create shared frontend HTTP client in `frontend/src/services/httpClient.ts` — wrap `fetch()` with automatic base-URL, credentials, Content-Type header, lazy auth-token lookup from auth context, consistent error parsing, and 401 redirect handling; export typed `get`, `post`, `put`, `patch`, `delete` helpers

**Checkpoint**: Foundation ready — shared utilities available for all user stories

---

## Phase 3: User Story 1 — Break Apart Oversized Modules (Priority: P1) 🎯 MVP

**Goal**: Split `github_projects.py` (4,448 lines), `copilot_polling.py` (3,987 lines), and `workflow_orchestrator.py` (1,959 lines) into focused sub-modules each under ~500 lines, with re-export facades at original paths

**Independent Test**: All existing unit and integration tests pass after the split; each new module has a docstring describing its single responsibility

### Implementation for User Story 1

#### Split `github_projects.py`

- [ ] T007 [US1] Extract GraphQL queries and fragments (lines 1–711) into `backend/src/services/github_projects/graphql_queries.py`
- [ ] T008 [P] [US1] Extract HTTP/GraphQL infrastructure methods (`_request_with_retry`, `_graphql`, `close`, `__init__`) into `backend/src/services/github_projects/client.py`
- [ ] T009 [P] [US1] Extract project listing and board methods (`list_user_projects`, `list_org_projects`, `_parse_projects`, `get_project_items`, `list_board_projects`, `get_board_data`, `poll_project_changes`) into `backend/src/services/github_projects/project_board.py`
- [ ] T010 [P] [US1] Extract issue CRUD methods (`create_issue`, `update_issue_body`, `update_issue_state`, `add_issue_to_project`, `assign_issue`, `get_issue_with_comments`, `format_issue_context_as_prompt`, `set_issue_metadata`, `create_issue_comment`, `create_sub_issue`, `get_sub_issues`, `tailor_body_for_agent`, `create_draft_item`) into `backend/src/services/github_projects/issues.py`
- [ ] T011 [P] [US1] Extract PR operations (`_search_open_prs_for_issue_rest`, `find_existing_pr_for_issue`, `get_linked_pull_requests`, `get_pull_request`, `mark_pr_ready_for_review`, `merge_pull_request`, `delete_branch`, `update_pr_base`, `link_pull_request_to_issue`, `get_pr_changed_files`, `get_file_content_from_ref`, `_detect_changes`) into `backend/src/services/github_projects/pull_requests.py`
- [ ] T012 [P] [US1] Extract Copilot integration methods (`get_copilot_bot_id`, `check_agent_completion_comment`, `unassign_copilot_from_issue`, `is_copilot_assigned_to_issue`, `assign_copilot_to_issue`, `_assign_copilot_rest`, `_assign_copilot_graphql`, `request_copilot_review`, `has_copilot_reviewed_pr`, `get_pr_timeline_events`, `_check_copilot_finished_events`, `check_copilot_pr_completion`) into `backend/src/services/github_projects/copilot_integration.py`
- [ ] T013 [P] [US1] Extract project field and status methods (`update_item_status`, `update_item_status_by_name`, `update_sub_issue_project_status`, `get_project_fields`, `update_project_item_field`, `validate_assignee`, `get_repository_owner`, `get_project_repository`, `list_available_agents`) into `backend/src/services/github_projects/fields_and_status.py`
- [ ] T014 [US1] Convert `backend/src/services/github_projects.py` into a thin re-export facade that imports from sub-modules and exposes `GitHubProjectsService` and `github_projects_service` singleton — verify all external imports resolve

#### Split `copilot_polling.py`

- [ ] T015 [P] [US1] Extract `PollingState` dataclass and helper functions (`_get_sub_issue_number`, `_check_agent_done_on_sub_or_parent`, `_update_issue_tracking`, `_get_tracking_state_from_issue`, `_reconstruct_sub_issue_mappings`, `_get_or_reconstruct_pipeline`) into `backend/src/services/copilot_polling/helpers.py`
- [ ] T016 [P] [US1] Extract pipeline processing functions (`_process_pipeline_completion`, `post_agent_outputs_from_pr`) into `backend/src/services/copilot_polling/pipeline_processing.py`
- [ ] T017 [P] [US1] Extract status-checking functions (`check_backlog_issues`, `check_ready_issues`, `check_in_progress_issues`, `check_in_review_issues_for_copilot_review`, `ensure_copilot_review_requested`, `process_in_progress_issue`) into `backend/src/services/copilot_polling/status_handlers.py`
- [ ] T018 [P] [US1] Extract PR completion functions (`_merge_child_pr_if_applicable`, `_find_completed_child_pr`, `_check_child_pr_completion`, `_check_main_pr_completion`) into `backend/src/services/copilot_polling/pr_completion.py`
- [ ] T019 [P] [US1] Extract pipeline management functions (`_filter_events_after`, `_reconstruct_pipeline_state`, `_advance_pipeline`, `_transition_after_pipeline_complete`) into `backend/src/services/copilot_polling/pipeline_management.py`
- [ ] T020 [P] [US1] Extract polling lifecycle and recovery functions (`recover_stalled_issues`, `poll_for_copilot_completion`, `_poll_loop`, `stop_polling`, `get_polling_status`, `check_issue_for_copilot_completion`) into `backend/src/services/copilot_polling/polling_lifecycle.py`
- [ ] T021 [US1] Convert `backend/src/services/copilot_polling.py` into a thin re-export facade that imports from sub-modules and exposes all public functions — verify all external imports resolve

#### Split `workflow_orchestrator.py`

- [ ] T022 [P] [US1] Extract workflow state models, enums, and helper functions (lines 1–482: `WorkflowState`, `WorkflowContext`, `PipelineState`, `MainBranchInfo`, and standalone helpers like `get_agent_slugs`, `get_status_order`, `find_next_actionable_status`, etc.) into `backend/src/services/workflow_orchestrator/models.py`
- [ ] T023 [P] [US1] Extract pipeline state management functions (`get_pipeline_state`, `set_pipeline_state`, `remove_pipeline_state`, `get_workflow_config`, `set_workflow_config`, `get_issue_main_branch`, `set_issue_main_branch`, `update_issue_main_branch_sha`, `get_workflow_orchestrator`) into `backend/src/services/workflow_orchestrator/state.py`
- [ ] T024 [P] [US1] Extract `WorkflowOrchestrator` class methods into `backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T025 [US1] Convert `backend/src/services/workflow_orchestrator.py` into a thin re-export facade — verify all external imports (from `copilot_polling.py`, `api/workflow.py`, `api/chat.py`) resolve

**Checkpoint**: All three oversized modules split into sub-modules under ~500 lines each; all existing tests pass

---

## Phase 4: User Story 2 — Eliminate Duplicated Code Patterns (Priority: P1)

**Goal**: Consolidate duplicated repository resolution, polling initialization, session reconstruction, and cache key construction into shared utilities

**Independent Test**: Search codebase for previously-duplicated patterns; each exists in exactly one location with all callers using the shared version

### Implementation for User Story 2

- [ ] T026 [US2] Replace `_resolve_repository` in `backend/src/api/chat.py:53-68` with call to shared `repo_resolution.resolve_repository()` from T004
- [ ] T027 [P] [US2] Replace `_resolve_repository_for_project` in `backend/src/api/tasks.py:21-30` with call to shared `repo_resolution.resolve_repository()`
- [ ] T028 [P] [US2] Replace inline repository resolution in `backend/src/api/workflow.py` (lines calling `get_project_repository`) with shared `repo_resolution.resolve_repository()`
- [ ] T029 [P] [US2] Replace inline repository resolution in `backend/src/api/projects.py:154` with shared utility
- [ ] T030 [US2] Consolidate polling start/initialization — ensure a single entry point in `backend/src/services/copilot_polling/polling_lifecycle.py` manages the polling lifecycle; remove duplicate start logic from `backend/src/api/workflow.py` and `backend/src/api/chat.py`
- [ ] T031 [P] [US2] Consolidate session reconstruction — extract `_get_session` / `_require_session` pattern duplicated across `backend/src/api/chat.py`, `backend/src/api/projects.py`, `backend/src/api/workflow.py`, `backend/src/api/tasks.py` into a shared dependency in `backend/src/api/dependencies.py`
- [ ] T032 [P] [US2] Replace all inline cache-key `f"..."` patterns in `backend/src/services/` with calls to the centralized `cache_keys.py` helpers from T005

**Checkpoint**: Zero duplicated patterns; all callers use shared utilities; all existing tests pass

---

## Phase 5: User Story 3 — Standardize Error Handling (Priority: P2)

**Goal**: Unified error-handling strategy — domain exceptions translated to HTTP responses in one place; all error responses follow consistent sanitized structure

**Independent Test**: Trigger known error conditions in each API endpoint; verify response format (`{"error": "...", "details": {...}}`) and status code are consistent; no stack traces or class names in response bodies

### Implementation for User Story 3

- [ ] T033 [US3] Audit and update `backend/src/exceptions.py` — ensure all domain exceptions extend `AppException`; add any missing exception types found during audit
- [ ] T034 [US3] Refactor `backend/src/api/auth.py` — replace `HTTPException` raises (lines 61, 90, 96, 115, 172, 196) with appropriate `AppException` subclasses; remove bare `except Exception` blocks that swallow errors
- [ ] T035 [P] [US3] Refactor `backend/src/api/webhooks.py` — replace `HTTPException` raises (lines 219, 244) with `AppException` subclasses; ensure `except Exception` blocks (lines 179, 242, 458, 522) log and re-raise or return proper error responses
- [ ] T036 [P] [US3] Audit `backend/src/api/chat.py` error handling — ensure all `except Exception` blocks (lines 177, 244, 363, 594, 597, 606) either log with `logger.exception()` and raise `AppException`, or handle explicitly; remove silent swallowing
- [ ] T037 [P] [US3] Audit `backend/src/api/workflow.py` error handling — ensure `except Exception` blocks (lines 285, 290) follow the unified pattern
- [ ] T038 [P] [US3] Audit `backend/src/api/projects.py` error handling — ensure `except Exception` blocks (lines 225, 245) follow the unified pattern
- [ ] T039 [US3] Verify `backend/src/main.py` exception handlers (`app_exception_handler` and `generic_exception_handler`) produce consistent `{"error": "...", "details": {...}}` structure with no internal details; update if needed

**Checkpoint**: All API error responses use unified AppException → JSONResponse flow; no `HTTPException` outside auth.py webhook signature validation; all responses sanitized

---

## Phase 6: User Story 4 — Consolidate Hardcoded Values and Magic Numbers (Priority: P2)

**Goal**: All magic numbers, timeouts, retry counts, TTLs, and default limits defined as named constants in `backend/src/constants.py` or `backend/src/config.py`

**Independent Test**: Search codebase for numeric literals and inline string constants in business logic; all reference named constants or configuration

### Implementation for User Story 4

- [ ] T040 [US4] Audit `backend/src/services/github_projects/` sub-modules for hardcoded values (e.g., `MAX_RETRIES = 3`, `INITIAL_BACKOFF_SECONDS = 1`, `MAX_BACKOFF_SECONDS = 30`, pagination `limit` defaults, `first: 100` in GraphQL) — move to `backend/src/constants.py`
- [ ] T041 [P] [US4] Audit `backend/src/services/copilot_polling/` sub-modules for hardcoded timeouts, retry counts, sleep durations, and batch sizes — move to `backend/src/constants.py`
- [ ] T042 [P] [US4] Audit `backend/src/services/workflow_orchestrator/` sub-modules for hardcoded values — move to `backend/src/constants.py`
- [ ] T043 [P] [US4] Audit `backend/src/services/ai_agent.py` for hardcoded values (model names, token limits, retry counts) — move to `backend/src/constants.py` or `backend/src/config.py`
- [ ] T044 [P] [US4] Audit `backend/src/services/cache.py` for hardcoded TTL values — ensure all reference `backend/src/config.py` `cache_ttl_seconds` or named constants
- [ ] T045 [P] [US4] Audit `backend/src/api/` route files for hardcoded limits, default values, and magic numbers — replace with named constants
- [ ] T046 [US4] Add documentation comments to `backend/src/constants.py` describing each constant group and their intended use

**Checkpoint**: Zero magic numbers in business logic; all operational parameters traceable to named constants

---

## Phase 7: User Story 5 — Unify Frontend API Communication Layer (Priority: P2)

**Goal**: All frontend API calls route through the shared HTTP client; consistent error handling and auth header injection

**Independent Test**: Verify all API calls use the shared `httpClient.ts`; no direct `fetch()` calls outside the client module

### Implementation for User Story 5

- [ ] T047 [US5] Refactor `frontend/src/services/api.ts` to use the shared HTTP client from `frontend/src/services/httpClient.ts` (T006) instead of direct `fetch()` — preserve all existing `authApi`, `projectsApi`, `tasksApi`, `chatApi`, `boardApi`, `settingsApi` exports
- [ ] T048 [P] [US5] Refactor `frontend/src/hooks/useWorkflow.ts` — replace direct `fetch()` calls (lines 32, 67, 98, 127) with shared HTTP client methods
- [ ] T049 [P] [US5] Refactor `frontend/src/hooks/useAgentConfig.ts` — replace direct `fetch()` call (line 206) with shared HTTP client method
- [ ] T050 [US5] Verify zero direct `fetch()` calls remain outside `frontend/src/services/httpClient.ts` — run `grep -rn "fetch(" frontend/src/ --include="*.ts" --include="*.tsx"` and confirm only httpClient.ts contains raw fetch

**Checkpoint**: 100% of frontend API calls route through shared HTTP client; consistent error handling across all hooks

---

## Phase 8: User Story 6 — Improve Frontend State Management and Resilience (Priority: P3)

**Goal**: sessionStorage-backed state persistence, error boundaries, WebSocket-primary/polling-fallback real-time updates

**Independent Test**: Refresh page mid-workflow — state (selected project, board context) is preserved; simulate API failure — error boundary displays fallback UI

### Implementation for User Story 6

- [ ] T051 [US6] Create `ErrorBoundary` component in `frontend/src/components/common/ErrorBoundary.tsx` — catch rendering failures, display fallback UI card with error message and Reload button
- [ ] T052 [US6] Wrap top-level component tree in `frontend/src/App.tsx` with `ErrorBoundary`; add section-level error boundaries around board, chat, and settings panels
- [ ] T053 [P] [US6] Implement sessionStorage persistence for selected project and board context in `frontend/src/hooks/useProjects.ts` and `frontend/src/hooks/useProjectBoard.ts` — save to `sessionStorage` on state change, restore on mount
- [ ] T054 [P] [US6] Refactor `frontend/src/hooks/useRealTimeSync.ts` — ensure WebSocket is primary channel; implement automatic polling fallback on WebSocket disconnect; stop polling when WebSocket reconnects; prevent both channels running simultaneously

**Checkpoint**: Page refresh preserves state; error boundaries prevent blank screens; WebSocket-primary with polling fallback

---

## Phase 9: User Story 7 — Increase Test Coverage for Untested Modules (Priority: P3)

**Goal**: Unit tests for five untested backend services and six untested frontend hooks

**Independent Test**: Run test suite; coverage reports show tests exist for all previously-untested modules

### Backend Tests for User Story 7

- [ ] T055 [P] [US7] Create `backend/tests/unit/test_completion_providers.py` — unit tests for `backend/src/services/completion_providers.py` covering primary functions and edge cases
- [ ] T056 [P] [US7] Create `backend/tests/unit/test_session_store.py` — unit tests for `backend/src/services/session_store.py` covering session CRUD and expiration
- [ ] T057 [P] [US7] Create `backend/tests/unit/test_settings_store.py` — unit tests for `backend/src/services/settings_store.py` covering settings retrieval and update
- [ ] T058 [P] [US7] Create `backend/tests/unit/test_agent_tracking.py` — unit tests for `backend/src/services/agent_tracking.py` covering tracking state parsing and mutation
- [ ] T059 [P] [US7] Expand `backend/tests/unit/test_workflow_orchestrator.py` — add tests for `WorkflowOrchestrator` class methods, state transitions, and edge cases (file exists but may lack comprehensive coverage)

### Frontend Tests for User Story 7

- [ ] T060 [P] [US7] Create `frontend/src/hooks/useSettings.test.tsx` — tests for `useSettings` hook covering settings fetch, update, and error handling
- [ ] T061 [P] [US7] Create `frontend/src/hooks/useWorkflow.test.tsx` — tests for `useWorkflow` hook covering workflow operations and state management
- [ ] T062 [P] [US7] Create `frontend/src/hooks/useAgentConfig.test.tsx` — tests for `useAgentConfig` hook covering agent configuration CRUD
- [ ] T063 [P] [US7] Create `frontend/src/hooks/useChat.test.tsx` — tests for `useChat` hook covering message send/receive and polling
- [ ] T064 [P] [US7] Create `frontend/src/hooks/useProjectBoard.test.tsx` — tests for `useProjectBoard` hook covering board data loading and status updates
- [ ] T065 [P] [US7] Create `frontend/src/hooks/useAppTheme.test.tsx` — tests for `useAppTheme` hook covering theme toggle and localStorage persistence

**Checkpoint**: All five backend services and all six frontend hooks have dedicated tests; test suite passes

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and validation

- [ ] T066 [P] Add single-sentence docstrings to all new sub-module files describing their single responsibility
- [ ] T067 [P] Verify no backend source file (excluding tests and generated files) exceeds ~500 lines — `find backend/src -name "*.py" -exec wc -l {} + | sort -rn`
- [ ] T068 Run full backend test suite — `cd backend && python -m pytest` — all tests pass
- [ ] T069 Run full frontend test suite — `cd frontend && npm test` — all tests pass
- [ ] T070 Run frontend build — `cd frontend && npm run build` — no TypeScript or build errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup; BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Setup (T001–T003); can start after Setup
- **US2 (Phase 4)**: Depends on Foundational (T004–T006) and US1 (T014, T021, T025)
- **US3 (Phase 5)**: Depends on Foundational; independent of US1/US2
- **US4 (Phase 6)**: Depends on US1 (sub-modules must exist before auditing them)
- **US5 (Phase 7)**: Depends on Foundational (T006 shared HTTP client)
- **US6 (Phase 8)**: Independent; can start after Foundational
- **US7 (Phase 9)**: Depends on US1 (module splits complete before writing tests against new structure)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Setup (Phase 1) — No dependencies on other stories
- **US2 (P1)**: Requires US1 completion (shared utilities need to reference new sub-module paths)
- **US3 (P2)**: Independent — can run in parallel with US1/US2
- **US4 (P2)**: Requires US1 completion (audits new sub-module files)
- **US5 (P2)**: Requires Foundational T006 — independent of backend stories
- **US6 (P3)**: Independent — can run in parallel with other frontend stories
- **US7 (P3)**: Requires US1 completion (tests should target final module structure)

### Within Each User Story

- Models/shared utilities before consumers
- Sub-module extraction before facade creation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001–T003) can run in parallel
- Foundational tasks T004, T005, T006 can run in parallel
- Within US1: All sub-module extraction tasks marked [P] can run in parallel per service file (T008–T013 for github_projects; T015–T020 for copilot_polling; T022–T024 for workflow_orchestrator); facade creation tasks (T014, T021, T025) must wait
- Within US2: T026–T029 and T031–T032 can run in parallel
- US3 tasks T034–T038 can run in parallel
- US4 tasks T041–T045 can run in parallel
- US5 tasks T048–T049 can run in parallel
- US6 tasks T053–T054 can run in parallel
- All US7 test tasks (T055–T065) can run in parallel
- US3, US5, US6 can all start in parallel after their prerequisites are met

---

## Parallel Example: User Story 1

```bash
# Launch all github_projects sub-module extractions together:
Task: "Extract GraphQL queries into backend/src/services/github_projects/graphql_queries.py"
Task: "Extract HTTP/GraphQL client into backend/src/services/github_projects/client.py"
Task: "Extract project board methods into backend/src/services/github_projects/project_board.py"
Task: "Extract issue CRUD into backend/src/services/github_projects/issues.py"
Task: "Extract PR operations into backend/src/services/github_projects/pull_requests.py"
Task: "Extract Copilot integration into backend/src/services/github_projects/copilot_integration.py"
Task: "Extract fields/status methods into backend/src/services/github_projects/fields_and_status.py"

# Then create the re-export facade (depends on all above):
Task: "Convert github_projects.py into thin re-export facade"

# Similarly for copilot_polling and workflow_orchestrator sub-modules
```

## Parallel Example: User Story 7

```bash
# All backend test files can be written in parallel:
Task: "Create test_completion_providers.py"
Task: "Create test_session_store.py"
Task: "Create test_settings_store.py"
Task: "Create test_agent_tracking.py"
Task: "Expand test_workflow_orchestrator.py"

# All frontend test files can be written in parallel:
Task: "Create useSettings.test.tsx"
Task: "Create useWorkflow.test.tsx"
Task: "Create useAgentConfig.test.tsx"
Task: "Create useChat.test.tsx"
Task: "Create useProjectBoard.test.tsx"
Task: "Create useAppTheme.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (create package directories)
2. Complete Phase 2: Foundational (shared utilities)
3. Complete Phase 3: User Story 1 (split oversized modules)
4. **STOP and VALIDATE**: Run full test suite — all existing tests pass with split modules
5. Each module under ~500 lines with clear docstring

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (split modules) → Test independently → Validate (MVP!)
3. Add US2 (DRY consolidation) → Test independently → Validate
4. Add US3 (error handling) → Test independently → Validate
5. Add US4 (constants) → Test independently → Validate
6. Add US5 (frontend HTTP client) → Test independently → Validate
7. Add US6 (frontend resilience) → Test independently → Validate
8. Add US7 (test coverage) → Run full suite → Validate
9. Polish → Final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (module splits) → US2 (DRY) → US4 (constants)
   - Developer B: US3 (error handling) → US5 (frontend HTTP client)
   - Developer C: US6 (frontend resilience) → US7 (test coverage)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- `workflow_orchestrator.py` (1,959 lines) is also above the ~500 line threshold per SC-001 and is included in the US1 module split
- Re-export facades preserve backward compatibility per FR-002, FR-003 clarification
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
