# Tasks: Simplicity & DRY Refactoring Across Backend and Frontend

**Input**: Design documents from `/specs/028-simplicity-dry-refactor/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Existing test suites must pass after all changes (FR-017). No new test creation mandated beyond test helper consolidation (Phase 5). Tests are NOT added per-task.

**Organization**: Tasks are grouped by user story. Backend stories (US1→US2→US3) are sequential. Frontend stories (US4, US5) are parallel with backend Phases 4–5 (US2, US3). Test cleanup (US6) follows backend completion.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in all descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed — this is a refactoring of an existing codebase. Setup phase ensures the working branch is ready and verifies baseline tests pass.

- [ ] T001 Verify backend test baseline passes with `cd backend && python -m pytest tests/ -v`
- [ ] T002 Verify frontend test baseline passes with `cd frontend && npx vitest run`
- [ ] T003 [P] Verify backend linting passes with `cd backend && ruff check src/ tests/`
- [ ] T004 [P] Verify frontend linting passes with `cd frontend && npx eslint src/`

**Checkpoint**: Baseline green — all existing tests and lints pass before any refactoring begins.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational infrastructure to create — all shared helpers already exist in the codebase (`resolve_repository()` in `utils.py`, `handle_service_error()`/`safe_error_response()` in `logging_utils.py`, `InMemoryCache` in `services/cache.py`). The only foundational additions are the new `require_selected_project()` dependency and `cached_fetch()` wrapper, which are created as part of User Story 1.

**⚠️ CRITICAL**: User Story 1 (Phase 3) MUST complete before User Story 2 (Phase 4) begins. User Story 4 (Phase 6) can proceed in parallel with Phases 4–5.

**Checkpoint**: No blocking foundational work — proceed directly to User Story 1.

---

## Phase 3: User Story 1 — Consistent Error Handling and Validation Across Backend Endpoints (Priority: P1) 🎯 MVP

**Goal**: Replace 8 duplicate repository resolution implementations, 5+ inline error handling blocks, 5 inline project validation guards, and verbose cache patterns with shared helpers. Saves ~230 lines.

**Independent Test**: `grep -r "_get_repository_info" backend/src/` → 0 hits; `grep -rn "if not session.selected_project_id" backend/src/api/` → 0 hits in consolidated endpoints; all existing backend tests pass unchanged.

### Step 1.1 — Unify Repository Resolution (~100 lines saved)

- [ ] T005 [P] [US1] Delete `_get_repository_info()` function from `backend/src/api/workflow.py` and update all callers in that file to use `resolve_repository()` from `backend/src/utils.py`
- [ ] T006 [P] [US1] Update repository resolution callers in `backend/src/api/projects.py` to use canonical `resolve_repository()` from `backend/src/utils.py`
- [ ] T007 [P] [US1] Update repository resolution callers in `backend/src/api/tasks.py` to use canonical `resolve_repository()` from `backend/src/utils.py`
- [ ] T008 [P] [US1] Verify `backend/src/api/chat.py` already uses `resolve_repository()` via wrapper; update if any direct resolution remains
- [ ] T009 [P] [US1] Update repository resolution callers in `backend/src/api/chores.py` to use canonical `resolve_repository()` from `backend/src/utils.py`
- [ ] T010 [P] [US1] Update callers in `backend/src/main.py` to use canonical `resolve_repository()` if any duplicate resolution exists
- [ ] T011 [US1] Update test mocks in `backend/tests/unit/test_api_workflow.py` from `_get_repository_info` to `resolve_repository`
- [ ] T012 [US1] Validate: `grep -r "_get_repository_info" backend/` → 0 results; run `python -m pytest tests/ -v`

### Step 1.2 — Adopt Error Handling Helpers (~50 lines saved)

- [ ] T013 [P] [US1] Replace catch→log→raise blocks in `backend/src/api/auth.py` with `handle_service_error()` from `backend/src/logging_utils.py`
- [ ] T014 [P] [US1] Replace catch→log→raise blocks in `backend/src/api/workflow.py` with `handle_service_error()` from `backend/src/logging_utils.py`
- [ ] T015 [P] [US1] Replace non-rate-limit error paths in `backend/src/api/projects.py` with `handle_service_error()` from `backend/src/logging_utils.py` (keep rate-limit-specific logic inline)
- [ ] T016 [P] [US1] Replace catch blocks in `backend/src/api/board.py` with `handle_service_error()` from `backend/src/logging_utils.py`
- [ ] T017 [US1] Validate: 80%+ of API endpoints use shared error helpers; run `python -m pytest tests/ -v`

### Step 1.3 — Validation Helper (~20 lines saved)

- [ ] T018 [US1] Add `require_selected_project(session: UserSession) -> str` function to `backend/src/dependencies.py` per contract in `contracts/api.md` — validate `session.selected_project_id` is not None/empty, raise `ValidationError("No project selected. Please select a project first.")` on failure
- [ ] T019 [P] [US1] Replace inline `selected_project_id` guard clauses in `backend/src/api/chat.py` (L64, L142) with `require_selected_project()` from `backend/src/dependencies.py`
- [ ] T020 [P] [US1] Replace inline `selected_project_id` guard clauses in `backend/src/api/workflow.py` (L148, L303, L416+) with `require_selected_project()` from `backend/src/dependencies.py`
- [ ] T021 [P] [US1] Replace inline `selected_project_id` guard clause in `backend/src/api/tasks.py` (L31-32) with `project_id = project_id or require_selected_project(session)` pattern
- [ ] T022 [P] [US1] Replace inline `selected_project_id` guard clauses in `backend/src/api/chores.py` with `require_selected_project()` from `backend/src/dependencies.py`
- [ ] T023 [US1] Validate: inline guards removed from consolidated endpoints; run `python -m pytest tests/ -v`

### Step 1.4 — Generic Cache Wrapper (~60 lines saved)

- [ ] T024 [US1] Add `cached_fetch()` async function to `backend/src/services/cache.py` per contract in `contracts/api.md` and signature in `data-model.md` — implement cache-first strategy with optional stale-data fallback on fetch failure
- [ ] T025 [P] [US1] Replace verbose cache check/get/set pattern in `backend/src/api/projects.py` (L114-198) with `cached_fetch()` from `backend/src/services/cache.py`
- [ ] T026 [P] [US1] Replace verbose cache check/get/set pattern in `backend/src/api/board.py` (L205-260) with `cached_fetch()` from `backend/src/services/cache.py`
- [ ] T027 [P] [US1] Replace cache read patterns in `backend/src/api/chat.py` (L161-185) with `cached_fetch()` from `backend/src/services/cache.py`
- [ ] T028 [US1] Validate: all cache patterns consolidated; run full backend test suite `python -m pytest tests/ -v`

**Checkpoint**: User Story 1 complete. All backend quick wins consolidated. `grep _get_repository_info` → 0 hits. Shared helpers adopted across API modules. All backend tests pass.

---

## Phase 4: User Story 2 — Decomposed Backend Service with Backward Compatibility (Priority: P1)

**Goal**: Split the 4,913-line `service.py` monolith (79 methods) into 8 focused modules (<800 LOC each) using composition over inheritance. Maintain backward-compatible facade via `__init__.py` re-exports.

**Independent Test**: `wc -l` on each new module < 800; all existing imports resolve; `python -m pytest tests/ -v` passes unchanged.

**Depends on**: Phase 3 (US1) completion — Phase 1 quick wins reduce line count before splitting.

### Service Module Extraction

- [ ] T029 [US2] Create `backend/src/services/github_projects/client.py` (~400 LOC) — extract `GitHubProjectsClient` class with HTTP client methods (`__init__`, `_rest`, `_rest_response`, `rest_request`, `_graphql`, `_with_fallback`, `close`, rate limit methods, cycle cache methods) from `backend/src/services/github_projects/service.py` per module boundaries in `research.md` R5
- [ ] T030 [US2] Create `backend/src/services/github_projects/projects.py` (~600 LOC) — extract `ProjectsModule` class with project listing and management methods (`list_user_projects`, `list_org_projects`, `_parse_projects`, `get_project_items`, `get_project_field_options`, `update_project_item_field`, `move_project_item`, `get_project_repository`) from `service.py`, accept `GitHubProjectsClient` via constructor
- [ ] T031 [P] [US2] Create `backend/src/services/github_projects/issues.py` (~700 LOC) — extract `IssuesModule` class with issue CRUD methods (`create_issue`, `update_issue`, `get_issue_details`, `add_issue_to_project`, `remove_issue_from_project`, `close_issue`, `reopen_issue`, `add_labels_to_issue`, `list_issue_comments`, `create_issue_comment`, `update_issue_comment`, `get_issue_timeline`) from `service.py`
- [ ] T032 [P] [US2] Create `backend/src/services/github_projects/pull_requests.py` (~500 LOC) — extract `PullRequestsModule` class with PR methods (`list_pull_requests`, `get_pull_request`, `create_pull_request`, `merge_pull_request`, `list_pr_reviews`, `list_pr_files`) from `service.py`
- [ ] T033 [P] [US2] Create `backend/src/services/github_projects/copilot.py` (~500 LOC) — extract `CopilotModule` class with Copilot/AI methods (`is_copilot_author`, `is_copilot_swe_agent`, `list_available_agents`, `get_copilot_metrics`, plus Copilot-specific methods) from `service.py`
- [ ] T034 [P] [US2] Create `backend/src/services/github_projects/fields.py` (~400 LOC) — extract `FieldsModule` class with field management methods (`get_project_fields`, `get_field_values`, `update_field_value`, `create_field`, `delete_field`) from `service.py`
- [ ] T035 [P] [US2] Create `backend/src/services/github_projects/board.py` (~500 LOC) — extract `BoardModule` class with board data and view methods (`get_board_data`, `get_board_columns`, `get_board_items`, `list_board_projects`, board view transformations) from `service.py`
- [ ] T036 [P] [US2] Create `backend/src/services/github_projects/repository.py` (~700 LOC) — extract `RepositoryModule` class with repository and file operations (`get_repository_info`, `get_directory_contents`, `get_file_content`, `get_file_content_from_ref`, `create_branch`, `get_branch_head_oid`, `commit_files`, `_detect_changes`) from `service.py`

### Composition Facade

- [ ] T037 [US2] Refactor `backend/src/services/github_projects/service.py` to composition facade — `GitHubProjectsService.__init__` instantiates `GitHubProjectsClient` + all 8 modules; all 79 public methods delegate to appropriate module per data-model.md facade pattern
- [ ] T038 [US2] Update `backend/src/services/github_projects/__init__.py` with backward-compatible re-exports — import and export `GitHubProjectsClient`, `GitHubProjectsService`, and all module classes per `contracts/api.md` facade contract; ensure `github_projects_service` singleton re-export during migration window
- [ ] T039 [US2] Validate: `wc -l` on each of the 8 new modules < 800 LOC; all existing imports resolve; run `python -m pytest tests/ -v`

**Checkpoint**: User Story 2 complete. Monolith decomposed into 8 focused modules. Backward-compatible facade in place. All tests pass unchanged.

---

## Phase 5: User Story 3 — Unified Service Initialization (Priority: P2)

**Goal**: Consolidate all service instantiation into `lifespan()` → `app.state` → `Depends(get_xxx_service)`. Remove module-level singletons and lazy patterns.

**Independent Test**: Application starts successfully; OAuth flow works; all services accessed via DI; `python -m pytest tests/ -v` passes.

**Depends on**: Phase 4 (US2) completion — service decomposition must be in place before changing initialization.

- [ ] T040 [US3] Consolidate service instantiation in `backend/src/main.py` `lifespan()` — instantiate `GitHubProjectsService()`, `ConnectionManager()`, `GitHubAuthService()` and register all on `app.state` per `contracts/api.md` service registration contract
- [ ] T041 [US3] Remove module-level `github_projects_service = GitHubProjectsService()` singleton from `backend/src/services/github_projects/service.py` — service instance now created in `lifespan()` only
- [ ] T042 [US3] Remove module-level `github_auth_service = GitHubAuthService()` singleton from `backend/src/services/github_auth.py` — service instance now created in `lifespan()` only
- [ ] T043 [US3] Add `get_github_auth_service(request) -> GitHubAuthService` dependency provider to `backend/src/dependencies.py` per `contracts/api.md` dependency providers table
- [ ] T044 [US3] Update `backend/src/services/github_projects/__init__.py` singleton management — facade re-export points to `app.state` instance during migration; remove module-level instantiation
- [ ] T045 [US3] Update background task modules in `backend/src/services/copilot_polling/`, `backend/src/services/signal_chat.py`, and `backend/src/services/agents/service.py` to access `GitHubProjectsService` via `app` reference instead of module-level import per research.md R6 findings
- [ ] T046 [US3] Validate: no module-level singletons remain; all services accessed via `app.state` or `Depends()`; run `python -m pytest tests/ -v`

**Checkpoint**: User Story 3 complete. Single initialization path via lifespan. No module-level singletons. All backend tests pass.

---

## Phase 6: User Story 4 — DRY Frontend Hooks and Shared UI Components (Priority: P2)

**Goal**: Create CRUD hook factory, unified settings hook, shared UI components (Modal, PreviewCard, ErrorAlert), centralized query key registry, and API endpoint factory. Saves ~1,500+ frontend lines.

**Independent Test**: `npx vitest run` fully green; new factories and components are importable and type-check with `npx tsc --noEmit`.

**Parallel with**: Phases 4–5 (US2, US3) — no cross-dependencies with backend changes.

### Step 4.4 — Centralize Query Keys (do first — other steps depend on it)

- [ ] T047 [US4] Create `frontend/src/hooks/queryKeys.ts` — centralized query key registry exporting all 9 key groups (`agents`, `agentTools`, `chores`, `settings`, `signal`, `mcp`, `models`, `pipelines`, `tools`) per `data-model.md` query key registry types and `contracts/components.md` section 6
- [ ] T048 [US4] Update all hook files that define local `xxxKeys` exports to import from `frontend/src/hooks/queryKeys.ts` instead — remove local key definitions from `useAgents.ts`, `useChores.ts`, `useSettings.ts`, `useMcpServers.ts`, `useModels.ts`, `usePipelines.ts`, `useTools.ts`, `useSignal.ts`

### Step 4.6 — API Endpoint Factory

- [ ] T049 [US4] Add `createApiGroup(basePath, methods)` factory function to `frontend/src/services/api.ts` per `contracts/components.md` section 7 — generate typed API call functions from base path and method definitions map
- [ ] T050 [US4] Refactor applicable API groups in `frontend/src/services/api.ts` to use `createApiGroup()` — candidates: `agentsApi`, `choresApi`, `toolsApi`, `pipelinesApi`, `cleanupApi` per contracts; keep manual: `authApi`, `chatApi`, `boardApi`, `settingsApi`, `signalApi`

### Step 4.1 — CRUD Hook Factory

- [ ] T051 [US4] Create `frontend/src/hooks/useCrudResource.ts` — implement `createCrudResource<T, CreateInput, UpdateInput>(config)` factory per `contracts/components.md` section 4 producing `useList`, `useCreate`, `useUpdate`, `useDelete` hooks from configuration
- [ ] T052 [P] [US4] Refactor `frontend/src/hooks/useAgents.ts` to use `createCrudResource()` from `useCrudResource.ts` — replace ~60 lines of duplicated query/mutation setup with factory call; keep custom hooks (e.g., `useAgentChat`) as extensions
- [ ] T053 [P] [US4] Refactor `frontend/src/hooks/useChores.ts` to use `createCrudResource()` from `useCrudResource.ts` — replace ~80 lines of duplicated query/mutation setup with factory call; keep custom hooks (e.g., `useTriggerChore`) as extensions

### Step 4.2 — Settings Hook Unification

- [ ] T054 [US4] Extract generic `useSettingsHook<T>(config)` in `frontend/src/hooks/useSettings.ts` per `contracts/components.md` section 5 — implement shared query/mutation pattern with optimistic updates
- [ ] T055 [US4] Refactor `useUserSettings()`, `useGlobalSettings()`, `useProjectSettings()` in `frontend/src/hooks/useSettings.ts` to use `useSettingsHook<T>()` — reduce ~110 lines of duplicated settings hook logic; keep signal-related hooks unchanged

### Step 4.3 — Shared UI Components

- [ ] T056 [P] [US4] Create `frontend/src/components/common/Modal.tsx` per `contracts/components.md` section 1 — shared dialog wrapper with `isOpen`, `onClose`, `title`, `description`, `children`, `footer`, `className` props; renders centered overlay with focus trap
- [ ] T057 [P] [US4] Create `frontend/src/components/common/PreviewCard.tsx` per `contracts/components.md` section 2 — action card with `title`, `children`, `onConfirm`, `onReject`, `confirmLabel`, `rejectLabel`, `isLoading`, `variant`, `className` props
- [ ] T058 [P] [US4] Create `frontend/src/components/common/ErrorAlert.tsx` per `contracts/components.md` section 3 — error display with `error`, `title`, `onDismiss`, `className` props; hidden when error is null

- [ ] T059 [US4] Validate: `npx tsc --noEmit` passes; `npx vitest run` fully green; `npx eslint src/` clean

**Checkpoint**: User Story 4 complete. CRUD hook factory, settings hook, shared UI components, query key registry, and API factory all implemented. Frontend test suite passes.

---

## Phase 7: User Story 5 — Simplified ChatInterface Component (Priority: P3)

**Goal**: Split the 417-line `ChatInterface.tsx` megacomponent into focused sub-components (`ChatMessageList` and `ChatInput`), each under 200 lines.

**Independent Test**: Chat feature works identically; no single component exceeds 200 lines; `npx vitest run` passes.

**Depends on**: Phase 6 (US4) completion — shared UI components (PreviewCard) may be used in extracted components.

- [ ] T060 [US5] Create `frontend/src/components/chat/ChatMessageList.tsx` per `contracts/components.md` section 8 — extract message rendering logic (auto-scroll, message mapping, inline proposal previews) from `frontend/src/components/chat/ChatInterface.tsx`; target <200 LOC
- [ ] T061 [US5] Create `frontend/src/components/chat/ChatInput.tsx` per `contracts/components.md` section 9 — extract input logic (textarea state, `useCommands()`, `useChatHistory()`, keyboard handlers, send button) from `frontend/src/components/chat/ChatInterface.tsx`; target <200 LOC
- [ ] T062 [US5] Refactor `frontend/src/components/chat/ChatInterface.tsx` to delegate to `ChatMessageList` and `ChatInput` sub-components — parent becomes layout coordinator; target <200 LOC
- [ ] T063 [US5] Validate: `wc -l` on each chat component < 200; `npx vitest run` passes; `npx eslint src/` clean

**Checkpoint**: User Story 5 complete. ChatInterface split into focused sub-components. All frontend tests pass.

---

## Phase 8: User Story 6 — Consolidated Test Helpers (Priority: P3)

**Goal**: Consolidate all `make_mock_*` factories from `tests/helpers/mocks.py` into `tests/conftest.py`. Replace inline patches with conftest fixtures. Saves ~80 lines.

**Independent Test**: All mock factories accessible from conftest; inline patches replaced; `python -m pytest tests/ -v` passes with full suite (57+ unit, 3+ integration).

**Depends on**: Phases 3–5 (US1, US2, US3) completion — backend refactoring must be stable before touching test infrastructure.

- [ ] T064 [US6] Move all `make_mock_*` factory functions from `backend/tests/helpers/mocks.py` to `backend/tests/conftest.py` as pytest fixtures per `contracts/api.md` test consolidation contracts — `mock_github_service_factory`, `mock_github_auth_service_factory`, `mock_ai_agent_service_factory`, `mock_websocket_manager_factory`, `mock_db_connection`
- [ ] T065 [US6] Replace inline `patch.object()` calls in `backend/tests/test_api_e2e.py` (L104–181) with conftest fixtures from T064
- [ ] T066 [US6] Deprecate `backend/tests/helpers/mocks.py` — remove or empty file with deprecation comment pointing to `conftest.py`
- [ ] T067 [US6] Validate: all mock factories in `conftest.py`; no scattered helper files; run `python -m pytest tests/ -v` (full suite: 57+ unit, 3+ integration)

**Checkpoint**: User Story 6 complete. Test helpers consolidated. Full backend and frontend test suites pass.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all user stories.

- [ ] T068 Run full backend test suite: `cd backend && python -m pytest tests/ -v` — confirm 57+ unit and 3+ integration tests pass
- [ ] T069 Run full frontend test suite: `cd frontend && npx vitest run` — confirm all tests pass
- [ ] T070 [P] Run backend linting: `cd backend && ruff check src/ tests/` — confirm clean
- [ ] T071 [P] Run frontend linting: `cd frontend && npx eslint src/` — confirm clean
- [ ] T072 [P] Run frontend type check: `cd frontend && npx tsc --noEmit` — confirm clean
- [ ] T073 Validate service module sizes: `wc -l backend/src/services/github_projects/{client,projects,issues,pull_requests,copilot,fields,board,repository}.py` — each < 800 LOC
- [ ] T074 Validate no legacy patterns remain: `grep -r "_get_repository_info" backend/src/` → 0; verify `selected_project_id` validation only in `dependencies.py`; verify no module-level singletons
- [ ] T075 Run quickstart.md verification checklist from `specs/028-simplicity-dry-refactor/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────────────────────────── (no dependencies)
    │
    ▼
Phase 3: US1 — Backend Quick Wins ──────────────── (depends on Phase 1)
    │                                    ╲
    ▼                                     ╲
Phase 4: US2 — Service Decomposition ─────╲─────── (depends on US1)
    │                                      ╲
    ▼                                       ╲
Phase 5: US3 — Init Consolidation ──────────╲──── (depends on US2)
    │                                        ╲
    ▼                                         ╲
Phase 8: US6 — Test Cleanup ─────────────────╲── (depends on US1, US2, US3)
    │                                         │
    ▼                                         │
Phase 9: Polish ──────────────────────────────┤
                                              │
Phase 6: US4 — Frontend DRY ──────────────────┤── (parallel with Phases 4–5)
    │                                         │
    ▼                                         │
Phase 7: US5 — ChatInterface Split ───────────┘── (depends on US4)
```

### User Story Dependencies

- **US1 (P1)**: Can start after Setup (Phase 1) — no dependencies on other stories
- **US2 (P1)**: Depends on US1 completion — Phase 1 quick wins reduce monolith size before splitting
- **US3 (P2)**: Depends on US2 completion — service decomposition must be in place before changing initialization
- **US4 (P2)**: Can start after Setup (Phase 1) — **parallel with US2 and US3** (no backend cross-dependencies)
- **US5 (P3)**: Depends on US4 completion — shared UI components may be used in chat sub-components
- **US6 (P3)**: Depends on US1, US2, US3 completion — backend must be stable before test infrastructure changes

### Within Each User Story

- Helpers/utilities created before adoption tasks
- Adoption tasks across different files can run in parallel [P]
- Validation task runs last in each story
- Story checkpoint confirms independent testability

### Parallel Opportunities

- **Phase 3 (US1)**: Steps 1.1–1.4 can run in parallel (different files, different helpers)
- **Phase 3 (US1)**: Within each step, [P]-marked tasks target different files
- **Phase 4 (US2)**: T031–T036 module extractions can run in parallel (different output files)
- **Phase 6 (US4)**: Steps 4.1/4.2/4.3 can partially overlap; T052/T053 parallel; T056/T057/T058 parallel
- **Cross-phase**: US4 (frontend) is fully parallel with US2+US3 (backend)

---

## Parallel Example: User Story 1, Step 1.1

```bash
# All file-level adoption tasks can run in parallel:
Task T005: "Delete _get_repository_info() from backend/src/api/workflow.py, adopt resolve_repository()"
Task T006: "Update resolution in backend/src/api/projects.py"
Task T007: "Update resolution in backend/src/api/tasks.py"
Task T008: "Verify backend/src/api/chat.py consistency"
Task T009: "Update resolution in backend/src/api/chores.py"
Task T010: "Update resolution in backend/src/main.py"
```

## Parallel Example: User Story 2, Module Extraction

```bash
# After T029 (client.py) and T030 (projects.py) are done, remaining modules can run in parallel:
Task T031: "Extract IssuesModule to backend/src/services/github_projects/issues.py"
Task T032: "Extract PullRequestsModule to backend/src/services/github_projects/pull_requests.py"
Task T033: "Extract CopilotModule to backend/src/services/github_projects/copilot.py"
Task T034: "Extract FieldsModule to backend/src/services/github_projects/fields.py"
Task T035: "Extract BoardModule to backend/src/services/github_projects/board.py"
Task T036: "Extract RepositoryModule to backend/src/services/github_projects/repository.py"
```

## Parallel Example: User Story 4, Shared Components

```bash
# All shared UI components target different files:
Task T056: "Create Modal.tsx in frontend/src/components/common/"
Task T057: "Create PreviewCard.tsx in frontend/src/components/common/"
Task T058: "Create ErrorAlert.tsx in frontend/src/components/common/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — verify baseline
2. Complete Phase 3: User Story 1 — backend quick wins
3. **STOP and VALIDATE**: All backend tests pass; shared helpers adopted; ~230 lines saved
4. This alone delivers measurable improvement with minimal risk

### Incremental Delivery

1. **US1 (Backend Quick Wins)** → Test → Merge-ready (~230 lines saved)
2. **US2 (Service Decomposition)** → Test → Merge-ready (monolith eliminated)
3. **US3 (Init Consolidation)** → Test → Merge-ready (single init path)
4. **US4 (Frontend DRY)** → Test → Merge-ready (~1,500 frontend lines saved)
5. **US5 (ChatInterface Split)** → Test → Merge-ready (component clarity)
6. **US6 (Test Cleanup)** → Test → Merge-ready (test infrastructure clean)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. All developers verify Setup (Phase 1) together
2. Once Setup is done:
   - **Backend Developer A**: US1 → US2 → US3 → US6 (sequential backend path)
   - **Frontend Developer B**: US4 → US5 (parallel frontend path, can start immediately)
3. Stories integrate independently; no cross-team blocking except final Polish

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 75 |
| **US1 tasks** | 24 (T005–T028) |
| **US2 tasks** | 11 (T029–T039) |
| **US3 tasks** | 7 (T040–T046) |
| **US4 tasks** | 13 (T047–T059) |
| **US5 tasks** | 4 (T060–T063) |
| **US6 tasks** | 4 (T064–T067) |
| **Setup tasks** | 4 (T001–T004) |
| **Polish tasks** | 8 (T068–T075) |
| **Parallel opportunities** | 33 tasks marked [P] |
| **Estimated lines saved** | ~1,830+ (backend ~330, frontend ~1,500) |
| **Suggested MVP scope** | User Story 1 (Phase 3, 24 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable at its checkpoint
- All existing tests must pass after each phase (FR-017)
- No new tests are added per-task; test helper consolidation in US6 only
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
