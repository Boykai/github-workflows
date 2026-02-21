# Tasks: Test Coverage & Bug Fixes

**Input**: Design documents from `/specs/008-test-coverage-bug-fixes/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests ARE the feature — every implementation task here creates test files or test infrastructure.

**Organization**: Tasks grouped by user story. US5 (shared fixtures) is Phase 2 because it BLOCKS US1 and US2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in every task description

---

## Phase 1: Setup

**Purpose**: Verify existing tests pass, establish baseline coverage numbers

- [X] T001 Run existing backend tests and record baseline coverage in backend/ via `pytest --cov=src --cov-report=term-missing`
- [X] T002 Run existing frontend tests and record baseline coverage in frontend/ via `npm run test:coverage`
- [X] T003 Verify all existing tests pass with zero failures in both backend/ and frontend/

---

## Phase 2: Foundational — Shared Test Fixtures (US5, Priority: P3 but BLOCKS US1/US2)

**Purpose**: Build the DRY test infrastructure that all subsequent test files depend on

**⚠️ CRITICAL**: No US1 or US2 work can begin until this phase is complete

- [X] T004 [US5] Expand backend shared fixtures: add `mock_db` (in-memory SQLite with migrations), `mock_settings`, `mock_github_service`, `mock_ai_agent`, and `mock_websocket_manager` fixtures in backend/tests/conftest.py
- [X] T005 [US5] Add backend `client` fixture: `httpx.AsyncClient` with `ASGITransport(app=create_app())` and dependency overrides for `get_db`, `get_session_dep`, `get_settings` in backend/tests/conftest.py
- [X] T006 [US5] Create frontend shared test utilities: `renderWithProviders()` wrapper with `QueryClientProvider` + `MemoryRouter` in frontend/src/test/test-utils.tsx
- [X] T007 [US5] Expand frontend test setup: add shared API mock factory `createMockApi()` and `crypto.randomUUID` stub in frontend/src/test/setup.ts

**Checkpoint**: Shared fixtures ready — US1 and US2 can now proceed in parallel

---

## Phase 3: User Story 1 — Backend Test Coverage Reaches 85% (Priority: P1) 🎯 MVP

**Goal**: ≥85% aggregate line coverage with ≥70% per-file floor for all backend source modules

**Independent Test**: `cd backend && pytest --cov=src --cov-report=term-missing --cov-fail-under=85`

### Backend: Pure function modules (zero external deps, simple)

- [X] T008 [P] [US1] Create unit tests for prompt construction functions in backend/tests/unit/test_prompts.py covering `create_issue_generation_prompt()`, `create_feature_request_detection_prompt()`, `create_task_generation_prompt()`, `create_status_change_prompt()` from backend/src/prompts/issue_generation.py and backend/src/prompts/task_generation.py
- [X] T009 [P] [US1] Create unit tests for agent tracking pure functions in backend/tests/unit/test_agent_tracking.py covering `build_agent_pipeline_steps()`, `render_tracking_markdown()`, `parse_tracking_from_body()`, `get_current_agent_from_tracking()`, `get_next_pending_agent()`, `determine_next_action()` from backend/src/services/agent_tracking.py
- [X] T010 [P] [US1] Create unit tests for exception classes and config loading in backend/tests/unit/test_config.py covering `Settings` validation, `get_settings()` caching, all `AppException` subclasses from backend/src/config.py and backend/src/exceptions.py, and constants/helpers from backend/src/constants.py

### Backend: Database layer (uses mock_db fixture)

- [X] T011 [P] [US1] Create unit tests for database init and migration runner in backend/tests/unit/test_database.py covering `init_database()`, `_run_migrations()`, `_discover_migrations()`, `seed_global_settings()` from backend/src/services/database.py
- [X] T012 [P] [US1] Create unit tests for session CRUD operations in backend/tests/unit/test_session_store.py covering `save_session()`, `get_session()`, `delete_session()`, `get_sessions_by_user()`, `purge_expired_sessions()` from backend/src/services/session_store.py
- [X] T013 [P] [US1] Create unit tests for settings store operations in backend/tests/unit/test_settings_store.py covering `get_global_settings()`, `update_global_settings()`, `upsert_user_preferences()`, `upsert_project_settings()`, `get_effective_user_settings()`, `get_effective_project_settings()` from backend/src/services/settings_store.py

### Backend: Service layer (uses mock fixtures)

- [X] T014 [US1] Create unit tests for completion provider factory and provider logic in backend/tests/unit/test_completion_providers.py covering `create_completion_provider()` dispatch, `CopilotCompletionProvider`, `AzureOpenAICompletionProvider` initialization and error handling from backend/src/services/completion_providers.py

### Backend: API route layer (uses client fixture)

- [X] T015 [P] [US1] Create unit tests for auth routes in backend/tests/unit/test_api_auth.py covering `get_current_user`, `logout`, `dev_login`, `get_current_session()` dependency, and OAuth flow from backend/src/api/auth.py
- [X] T016 [P] [US1] Create unit tests for board routes in backend/tests/unit/test_api_board.py covering `get_board`, `get_board_items`, `get_board_columns` and any query/filter endpoints from backend/src/api/board.py
- [X] T017 [P] [US1] Create unit tests for settings routes in backend/tests/unit/test_api_settings.py covering `get_user_settings`, `update_user_settings`, `get_global_settings`, `update_global_settings`, `get_project_settings`, `update_project_settings` from backend/src/api/settings.py
- [X] T018 [P] [US1] Create unit tests for tasks routes in backend/tests/unit/test_api_tasks.py covering `create_task`, `update_task_status`, `_resolve_repository_for_project()` from backend/src/api/tasks.py
- [X] T019 [US1] Create unit tests for chat routes in backend/tests/unit/test_api_chat.py covering `get_messages`, `send_message` (feature detection, issue recommendation, status change, task generation branches), `confirm_proposal`, `cancel_proposal` from backend/src/api/chat.py
- [X] T020 [US1] Create unit tests for projects routes in backend/tests/unit/test_api_projects.py covering `list_projects`, `get_project`, `select_project`, `get_project_tasks`, SSE subscribe from backend/src/api/projects.py
- [X] T021 [US1] Create unit tests for workflow routes in backend/tests/unit/test_api_workflow.py covering `confirm_recommendation`, `reject_recommendation`, `get_config`, `update_config`, `list_agents`, `start_polling`, `stop_polling` from backend/src/api/workflow.py

### Backend: App factory

- [X] T022 [US1] Create unit tests for FastAPI app factory in backend/tests/unit/test_main.py covering `create_app()`, lifespan startup/shutdown, `RateLimiter`, exception handlers, CORS configuration from backend/src/main.py

### Backend: Coverage verification

- [X] T023 [US1] Run full backend test suite with coverage and verify ≥85% aggregate and ≥70% per-file in backend/ via `pytest --cov=src --cov-report=term-missing`

**Checkpoint**: Backend at ≥85% coverage. Story 1 is complete and independently verifiable.

---

## Phase 4: User Story 2 — Frontend Test Coverage Reaches 85% (Priority: P2)

**Goal**: ≥85% aggregate line coverage with ≥70% per-file floor for all frontend source modules

**Independent Test**: `cd frontend && npm run test:coverage`

### Frontend: API service layer

- [ ] T024 [P] [US2] Create unit tests for API service module in frontend/src/services/api.test.ts covering `request<T>()` generic fetcher, `ApiError` class, `authApi`, `projectsApi`, `tasksApi`, `chatApi`, `boardApi`, `settingsApi` exports from frontend/src/services/api.ts

### Frontend: Untested hooks

- [ ] T025 [P] [US2] Create unit tests for useAppTheme hook in frontend/src/hooks/useAppTheme.test.tsx covering `isDarkMode`, `toggleTheme`, localStorage sync, CSS class toggle from frontend/src/hooks/useAppTheme.ts
- [ ] T026 [P] [US2] Create unit tests for useSettings hook in frontend/src/hooks/useSettings.test.tsx covering `useUserSettings()`, `useGlobalSettings()`, `useProjectSettings()` query/mutation wrappers from frontend/src/hooks/useSettings.ts
- [ ] T027 [P] [US2] Create unit tests for useProjectBoard hook in frontend/src/hooks/useProjectBoard.test.tsx covering projects list query, board data query, polling refetch from frontend/src/hooks/useProjectBoard.ts
- [ ] T028 [P] [US2] Create unit tests for useWorkflow hook in frontend/src/hooks/useWorkflow.test.tsx covering `confirmRecommendation`, `rejectRecommendation`, `getConfig`, `updateConfig` from frontend/src/hooks/useWorkflow.ts
- [ ] T029 [US2] Create unit tests for useChat hook in frontend/src/hooks/useChat.test.tsx covering messages query, `sendMessage` mutation, `confirmProposal`/`cancelProposal` mutations, pending state maps from frontend/src/hooks/useChat.ts
- [ ] T030 [US2] Create unit tests for useAgentConfig hook in frontend/src/hooks/useAgentConfig.test.tsx covering agent pipeline CRUD, dirty tracking, save/discard, `useAvailableAgents()` from frontend/src/hooks/useAgentConfig.ts

### Frontend: High-value components — auth & common

- [ ] T031 [P] [US2] Create component tests for LoginButton in frontend/src/components/auth/LoginButton.test.tsx covering OAuth redirect trigger, loading state from frontend/src/components/auth/LoginButton.tsx
- [ ] T032 [P] [US2] Create component tests for ErrorDisplay in frontend/src/components/common/ErrorDisplay.test.tsx covering error message rendering, retry button, different error types from frontend/src/components/common/ErrorDisplay.tsx
- [ ] T033 [P] [US2] Create component tests for RateLimitIndicator in frontend/src/components/common/RateLimitIndicator.test.tsx covering rate limit display, visibility toggle from frontend/src/components/common/RateLimitIndicator.tsx

### Frontend: High-value components — board

- [ ] T034 [P] [US2] Create component tests for ProjectBoard in frontend/src/components/board/ProjectBoard.test.tsx covering column rendering, empty state from frontend/src/components/board/ProjectBoard.tsx
- [ ] T035 [P] [US2] Create component tests for IssueCard in frontend/src/components/board/IssueCard.test.tsx covering issue data display, status badge, labels, click handler from frontend/src/components/board/IssueCard.tsx
- [ ] T036 [P] [US2] Create component tests for BoardColumn in frontend/src/components/board/BoardColumn.test.tsx covering column header, issue list rendering from frontend/src/components/board/BoardColumn.tsx
- [ ] T037 [P] [US2] Create component tests for IssueDetailModal in frontend/src/components/board/IssueDetailModal.test.tsx covering modal open/close, issue details display, agent info from frontend/src/components/board/IssueDetailModal.tsx
- [ ] T038 [P] [US2] Create component tests for AgentTile in frontend/src/components/board/AgentTile.test.tsx covering agent name, status display from frontend/src/components/board/AgentTile.tsx
- [ ] T039 [P] [US2] Create unit tests for color utility functions in frontend/src/components/board/colorUtils.test.ts covering color generation, mapping, and edge cases from frontend/src/components/board/colorUtils.ts

### Frontend: High-value components — chat

- [ ] T040 [P] [US2] Create component tests for ChatInterface in frontend/src/components/chat/ChatInterface.test.tsx covering message list rendering, input field, send button, empty state from frontend/src/components/chat/ChatInterface.tsx
- [ ] T041 [P] [US2] Create component tests for MessageBubble in frontend/src/components/chat/MessageBubble.test.tsx covering user vs assistant styling, message content from frontend/src/components/chat/MessageBubble.tsx
- [ ] T042 [P] [US2] Create component tests for IssueRecommendationPreview in frontend/src/components/chat/IssueRecommendationPreview.test.tsx covering recommendation display, confirm/reject buttons from frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T043 [P] [US2] Create component tests for StatusChangePreview in frontend/src/components/chat/StatusChangePreview.test.tsx and TaskPreview in frontend/src/components/chat/TaskPreview.test.tsx covering preview rendering, action buttons

### Frontend: High-value components — settings

- [ ] T044 [P] [US2] Create component tests for GlobalSettings in frontend/src/components/settings/GlobalSettings.test.tsx covering settings form rendering, save, validation from frontend/src/components/settings/GlobalSettings.tsx
- [ ] T045 [P] [US2] Create component tests for SettingsSection in frontend/src/components/settings/SettingsSection.test.tsx, AIPreferences in frontend/src/components/settings/AIPreferences.test.tsx, and DisplayPreferences in frontend/src/components/settings/DisplayPreferences.test.tsx
- [ ] T046 [P] [US2] Create component tests for ProjectSettings in frontend/src/components/settings/ProjectSettings.test.tsx, NotificationPreferences in frontend/src/components/settings/NotificationPreferences.test.tsx, and WorkflowDefaults in frontend/src/components/settings/WorkflowDefaults.test.tsx

### Frontend: High-value components — sidebar

- [ ] T047 [P] [US2] Create component tests for ProjectSidebar in frontend/src/components/sidebar/ProjectSidebar.test.tsx covering project list, selection, collapse from frontend/src/components/sidebar/ProjectSidebar.tsx
- [ ] T048 [P] [US2] Create component tests for ProjectSelector in frontend/src/components/sidebar/ProjectSelector.test.tsx and TaskCard in frontend/src/components/sidebar/TaskCard.test.tsx

### Frontend: Pages & App

- [ ] T049 [P] [US2] Create component tests for ProjectBoardPage in frontend/src/pages/ProjectBoardPage.test.tsx covering page layout, board rendering from frontend/src/pages/ProjectBoardPage.tsx
- [ ] T050 [P] [US2] Create component tests for SettingsPage in frontend/src/pages/SettingsPage.test.tsx covering page layout, settings panel rendering from frontend/src/pages/SettingsPage.tsx
- [ ] T051 [US2] Create component tests for App in frontend/src/App.test.tsx covering authenticated/unauthenticated rendering, view switching (chat/board/settings), theme toggle, settings-driven default view from frontend/src/App.tsx

### Frontend: Remaining board components (coverage gap-fill)

- [ ] T052 [P] [US2] Create component tests for AddAgentPopover in frontend/src/components/board/AddAgentPopover.test.tsx, AgentColumnCell in frontend/src/components/board/AgentColumnCell.test.tsx, AgentConfigRow in frontend/src/components/board/AgentConfigRow.test.tsx, AgentPresetSelector in frontend/src/components/board/AgentPresetSelector.test.tsx, and AgentSaveBar in frontend/src/components/board/AgentSaveBar.test.tsx covering agent configuration UI interactions

### Frontend: Coverage verification

- [ ] T053 [US2] Run full frontend test suite with coverage and verify ≥85% aggregate and ≥70% per-file in frontend/ via `npm run test:coverage`

**Checkpoint**: Frontend at ≥85% coverage. Story 2 is complete and independently verifiable.

---

## Phase 5: User Story 3 — Bugs and Issues Resolved (Priority: P2)

**Goal**: Fix all bugs, dead code, type errors, and incorrect behavior discovered during Phase 3 and Phase 4 test writing

**Independent Test**: Each fix has a corresponding test that fails without the fix

- [ ] T054 [US3] Audit backend test results from Phase 3 for discovered bugs, document each in a bugs list, and fix source code with corresponding test assertions in the relevant backend/tests/unit/test_*.py files
- [ ] T055 [US3] Audit frontend test results from Phase 4 for discovered bugs, document each in a bugs list, and fix source code with corresponding test assertions in the relevant frontend/src/**/*.test.tsx files
- [ ] T056 [US3] Remove dead code and unreachable branches identified during test writing across backend/src/ and frontend/src/, verify no existing tests break
- [ ] T057 [US3] Run full test suite (backend and frontend) to confirm all fixes pass and no regressions introduced

**Checkpoint**: All discovered bugs fixed with validating tests. Zero test failures.

---

## Phase 6: User Story 4 — Coverage Thresholds Enforced (Priority: P3)

**Goal**: Configure tooling to fail if coverage drops below 85% aggregate

**Independent Test**: Remove a test file, run suite, confirm non-zero exit code

- [ ] T058 [P] [US4] Add coverage configuration to backend/pyproject.toml: `[tool.coverage.run]` with `source = ["src"]`, omit patterns, and `[tool.coverage.report]` with `fail_under = 85`, `show_missing = true`, `exclude_lines` per contracts/backend-coverage.toml
- [ ] T059 [P] [US4] Add coverage configuration to frontend/vitest.config.ts: `coverage` block with `provider: 'v8'`, include/exclude patterns, `thresholds: { lines: 85, branches: 70, functions: 80, statements: 85 }`, reporters per contracts/frontend-coverage.json
- [ ] T060 [US4] Verify threshold enforcement: temporarily remove one backend and one frontend test file, confirm test runner exits with non-zero code, then restore the files

**Checkpoint**: Coverage thresholds enforced. Future regressions will be caught automatically.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and documentation

- [ ] T061 Run backend test suite with coverage one final time, confirm ≥85% aggregate and ≥70% per-file in backend/
- [ ] T062 Run frontend test suite with coverage one final time, confirm ≥85% aggregate and ≥70% per-file in frontend/
- [ ] T063 Verify all existing tests (including integration and e2e) still pass unchanged
- [ ] T064 Run quickstart.md validation steps from specs/008-test-coverage-bug-fixes/quickstart.md to confirm documented commands produce expected output

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — run immediately
- **Phase 2 (Foundational/US5)**: Depends on Phase 1 — BLOCKS Phases 3 and 4
- **Phase 3 (US1 Backend)**: Depends on Phase 2 — can run in parallel with Phase 4
- **Phase 4 (US2 Frontend)**: Depends on Phase 2 — can run in parallel with Phase 3
- **Phase 5 (US3 Bug Fixes)**: Depends on Phases 3 and 4 (bugs discovered during test writing)
- **Phase 6 (US4 Thresholds)**: Depends on Phases 3 and 4 (coverage must reach target first)
- **Phase 7 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US5 (P3 — Shared Fixtures)**: Foundational — must complete first despite lower priority
- **US1 (P1 — Backend Coverage)**: Depends on US5 fixtures only. No dependency on US2.
- **US2 (P2 — Frontend Coverage)**: Depends on US5 fixtures only. No dependency on US1.
- **US3 (P2 — Bug Fixes)**: Depends on US1 and US2 (bugs discovered during those phases)
- **US4 (P3 — Thresholds)**: Depends on US1 and US2 (coverage must be at target before enforcing)

### Within Each Phase

- Tasks marked [P] can run in parallel within their phase
- Unmarked tasks must run sequentially
- In Phase 3: pure function tests (T008-T010) → DB tests (T011-T013) → service tests (T014) → API tests (T015-T021) → app factory (T022) → verify (T023)
- In Phase 4: API service (T024) → hooks (T025-T030) → components (T031-T052) → verify (T053)

### Parallel Opportunities

**Phase 2** (backend and frontend fixtures can be built concurrently):
```
T004 + T005 (backend conftest)  |  T006 + T007 (frontend test-utils)
```

**Phase 3** (backend — parallel tracks then sequential API):
```
Track A: T008 (prompts)   → T015 (auth API)     → T019 (chat API)
Track B: T009 (tracking)  → T016 (board API)     → T020 (projects API)
Track C: T010 (config)    → T017 (settings API)  → T021 (workflow API)
DB Track: T011 + T012 + T013 (all parallel, use mock_db)
Service: T014 (after DB track)
API parallel: T015 + T016 + T017 + T018 (all [P])
App: T022 (after API tests)
```

**Phase 4** (frontend — massive parallelism on components):
```
T024 (api.ts) + T025-T028 (simple hooks) — all parallel
T029-T030 (complex hooks) — after T024
T031-T052 (components) — all marked [P], massive parallel batch
T051 (App.tsx) — after hooks and component mocks established
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Baseline measurement
2. Complete Phase 2: Shared fixtures (US5)
3. Complete Phase 3: Backend tests (US1)
4. **STOP and VALIDATE**: `pytest --cov=src --cov-report=term-missing` shows ≥85%
5. Backend is independently shippable at this point

### Incremental Delivery

1. Phase 1 + Phase 2 → Shared fixtures ready
2. Phase 3 (US1) → Backend ≥85% ✓ → **MVP complete**
3. Phase 4 (US2) → Frontend ≥85% ✓
4. Phase 5 (US3) → All bugs fixed ✓
5. Phase 6 (US4) → Thresholds enforced ✓
6. Phase 7 → Final validation ✓

### Parallel Team Strategy

With 2 developers:
1. Both complete Phase 1 + Phase 2 together
2. Developer A: Phase 3 (Backend/US1) | Developer B: Phase 4 (Frontend/US2)
3. Both: Phase 5 (Bug fixes for their respective stack)
4. Either: Phase 6 (Config changes) + Phase 7 (Polish)

---

## Notes

- Total task count: 64
- Tasks per user story: US1=16, US2=30, US3=4, US4=3, US5=4
- Setup/polish: 7 tasks
- Parallel opportunities: 40+ tasks marked [P]
- Commit after each test file or logical group
- Run `pytest`/`vitest` after each new test file to catch issues immediately
- US3 (bug fixes) tasks are intentionally vague — actual bugs are discovered during US1/US2 implementation
