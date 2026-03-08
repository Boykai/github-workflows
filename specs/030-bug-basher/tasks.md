# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/030-bug-basher/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: REQUIRED — FR-004 mandates at least one regression test per bug fix.

**Organization**: Tasks are grouped by user story (US1–US5) to enable independent implementation and testing of each priority category.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`, `backend/tests/integration/`
- **Frontend tests**: Co-located `__tests__/` directories or `.test.{ts,tsx}` files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the review environment, verify all tooling works, and confirm the test baseline is green before making any changes.

- [ ] T001 Install backend dev dependencies and verify pytest baseline in `backend/` (`pip install -e ".[dev]" && python -m pytest tests/unit/ -v`)
- [ ] T002 Install frontend dependencies and verify vitest baseline in `frontend/` (`npm install && npx vitest run`)
- [ ] T003 [P] Verify backend linting baseline with ruff in `backend/` (`ruff check src/ tests/`)
- [ ] T004 [P] Verify frontend linting and type-check baseline in `frontend/` (`npx eslint src/ && npx tsc --noEmit`)
- [ ] T005 Document any pre-existing test failures or lint warnings as baseline (do not fix — these are out of scope unless they are bugs)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the review methodology and audit scope. Catalog all files to review. This phase produces the file audit checklist that all subsequent phases will work through.

**⚠️ CRITICAL**: No bug fix work can begin until this phase is complete.

- [ ] T006 Catalog all backend source files to audit: 18 API modules in `backend/src/api/`, 7 core modules in `backend/src/`, 18 model files in `backend/src/models/`, all service files in `backend/src/services/` (47 files across 6 subdirectories), and 19 migration files in `backend/src/migrations/`
- [ ] T007 [P] Catalog all frontend source files to audit: 9 pages in `frontend/src/pages/`, 30 hooks in `frontend/src/hooks/`, 1 API service in `frontend/src/services/api.ts`, and all components in `frontend/src/components/` (agents/, board/, chat/, chores/, common/, pipeline/, settings/, tools/, ui/)
- [ ] T008 [P] Catalog all test files to audit: 43 unit tests in `backend/tests/unit/`, 3 integration tests in `backend/tests/integration/`, test helpers in `backend/tests/helpers/`, and all co-located frontend test files (`*.test.tsx`, `*.test.ts`)
- [ ] T009 Review known issues from `specs/030-bug-basher/research.md` (R-001 through R-008) and integrate findings into the audit plan

**Checkpoint**: File audit catalog complete — bug fix work can now begin in priority order.

---

## Phase 3: User Story 1 — Security Vulnerability Audit (Priority: P1) 🎯 MVP

**Goal**: Identify and fix all security vulnerabilities in the codebase: auth bypasses, injection risks, exposed secrets/tokens, insecure defaults, and improper input validation.

**Independent Test**: Run the full test suite after applying security fixes. Every security fix must have at least one regression test that would fail if the vulnerability were reintroduced.

### Backend API Security Audit

- [ ] T010 [P] [US1] Audit authentication and authorization logic in `backend/src/api/auth.py` — check for auth bypasses, token validation gaps, session fixation
- [ ] T011 [P] [US1] Audit webhook signature verification in `backend/src/api/webhooks.py` — check for timing attacks, missing signature validation
- [ ] T012 [P] [US1] Audit chat endpoint input handling in `backend/src/api/chat.py` — check for injection risks, file upload validation, path traversal in temp file handling
- [ ] T013 [P] [US1] Audit agent endpoints in `backend/src/api/agents.py` — check for input validation, authorization on bulk operations
- [ ] T014 [P] [US1] Audit workflow endpoints in `backend/src/api/workflow.py` — check for input validation, auth checks on workflow actions
- [ ] T015 [P] [US1] Audit settings endpoints in `backend/src/api/settings.py` — check for sensitive data exposure, authorization on settings changes
- [ ] T016 [P] [US1] Audit signal endpoints in `backend/src/api/signal.py` — check for input validation, phone number handling
- [ ] T017 [P] [US1] Audit board, projects, tasks, tools, mcp, pipelines, chores, cleanup, health, metadata endpoints in `backend/src/api/board.py`, `backend/src/api/projects.py`, `backend/src/api/tasks.py`, `backend/src/api/tools.py`, `backend/src/api/mcp.py`, `backend/src/api/pipelines.py`, `backend/src/api/chores.py`, `backend/src/api/cleanup.py`, `backend/src/api/health.py`, `backend/src/api/metadata.py`

### Backend Core & Config Security Audit

- [ ] T018 [P] [US1] Audit application configuration and secrets management in `backend/src/config.py` — check for hardcoded secrets, insecure defaults, missing validation
- [ ] T019 [P] [US1] Audit encryption service in `backend/src/services/encryption.py` — check for weak algorithms, key management issues, padding oracle risks
- [ ] T020 [P] [US1] Audit GitHub authentication service in `backend/src/services/github_auth.py` — check for token handling, OAuth flow security, state parameter validation
- [ ] T021 [P] [US1] Audit session management in `backend/src/services/session_store.py` — check for session fixation, insecure session storage, missing expiry
- [ ] T022 [P] [US1] Audit main application setup in `backend/src/main.py` — check CORS configuration, middleware order, error handler information leakage

### Backend Service Security Audit

- [ ] T023 [P] [US1] Audit AI agent service for prompt injection and input sanitization in `backend/src/services/ai_agent.py`
- [ ] T024 [P] [US1] Audit database service for SQL injection risks in `backend/src/services/database.py` — check parameterized queries, migration runner safety
- [ ] T025 [P] [US1] Audit signal chat and bridge services for input validation in `backend/src/services/signal_chat.py` and `backend/src/services/signal_bridge.py`
- [ ] T026 [P] [US1] Audit settings store for sensitive data handling in `backend/src/services/settings_store.py`
- [ ] T027 [P] [US1] Audit MCP store for input validation in `backend/src/services/mcp_store.py`

### Frontend Security Audit

- [ ] T028 [P] [US1] Audit API client for token handling and request security in `frontend/src/services/api.ts` — check for token exposure in URLs, missing auth headers, insecure storage
- [ ] T029 [P] [US1] Audit auth hook and login flow in `frontend/src/hooks/useAuth.ts` and `frontend/src/components/auth/LoginButton.tsx` — check for OAuth state validation, token storage security
- [ ] T030 [P] [US1] Audit chat interface for XSS risks in rendered content in `frontend/src/components/chat/MessageBubble.tsx`, `frontend/src/components/chat/ChatInterface.tsx` — check for unsafe HTML rendering, markdown injection

### Security Regression Tests

- [ ] T031 [US1] Add regression tests for each security fix found in backend — create test functions in appropriate files under `backend/tests/unit/`
- [ ] T032 [US1] Add regression tests for each security fix found in frontend — create test cases in appropriate co-located test files under `frontend/src/`
- [ ] T033 [US1] Run full backend test suite (`python -m pytest tests/unit/ -v`) and verify all tests pass including new security regression tests
- [ ] T034 [US1] Run full frontend test suite (`npx vitest run`) and verify all tests pass including new security regression tests
- [ ] T035 [US1] Run backend linting (`ruff check src/ tests/`) and verify zero errors after security fixes
- [ ] T036 [US1] Run frontend linting and type-check (`npx eslint src/ && npx tsc --noEmit`) and verify zero errors after security fixes

**Checkpoint**: All security vulnerabilities identified and fixed. Each fix has a regression test. Full test suite passes. This is the MVP deliverable.

---

## Phase 4: User Story 2 — Runtime Error & Logic Bug Resolution (Priority: P2)

**Goal**: Identify and fix all runtime errors (unhandled exceptions, race conditions, null references, resource leaks) and logic bugs (incorrect state transitions, off-by-one errors, wrong return values, broken control flow).

**Independent Test**: Run the full test suite after applying fixes. Every runtime/logic fix must have at least one regression test.

### Backend Runtime Error Audit

- [ ] T037 [P] [US2] Audit exception handling and resource management in `backend/src/services/database.py` — check for connection leaks, unclosed cursors, migration runner error paths
- [ ] T038 [P] [US2] Audit GitHub Projects service for unhandled exceptions and resource management in `backend/src/services/github_projects/service.py` and `backend/src/services/github_projects/graphql.py` — check for uncaught GraphQL errors, pagination edge cases, null field access
- [ ] T039 [P] [US2] Audit agent service for method naming mismatches and incorrect calls in `backend/src/services/agents/service.py` — check `get_model_preferences()` vs `get_agent_preferences()` naming, `_save_runtime_model_selection()` vs `_save_runtime_preferences()` calls, `bulk_update_models()` method references
- [ ] T040 [P] [US2] Audit copilot polling services for race conditions and error handling in `backend/src/services/copilot_polling/polling_loop.py`, `backend/src/services/copilot_polling/state.py`, `backend/src/services/copilot_polling/recovery.py`
- [ ] T041 [P] [US2] Audit websocket service for connection management and error handling in `backend/src/services/websocket.py`
- [ ] T042 [P] [US2] Audit cache service for expiry handling and concurrent access in `backend/src/services/cache.py`
- [ ] T043 [P] [US2] Audit signal delivery service for error handling and retry logic in `backend/src/services/signal_delivery.py`

### Backend Logic Bug Audit

- [ ] T044 [P] [US2] Audit workflow orchestrator for incorrect state transitions in `backend/src/services/workflow_orchestrator/orchestrator.py` and `backend/src/services/workflow_orchestrator/transitions.py`
- [ ] T045 [P] [US2] Audit chores scheduler for timing logic bugs in `backend/src/services/chores/scheduler.py` and `backend/src/services/chores/counter.py`
- [ ] T046 [P] [US2] Audit chores service for SQLite boolean handling and data consistency in `backend/src/services/chores/service.py`
- [ ] T047 [P] [US2] Audit completion providers for incorrect return values and edge cases in `backend/src/services/completion_providers.py`
- [ ] T048 [P] [US2] Audit model fetcher for API call correctness in `backend/src/services/model_fetcher.py`
- [ ] T049 [P] [US2] Audit cleanup service for logic correctness in `backend/src/services/cleanup_service.py`
- [ ] T050 [P] [US2] Audit GitHub commit workflow for control flow correctness in `backend/src/services/github_commit_workflow.py`
- [ ] T051 [P] [US2] Audit agent creator, agent tracking, and metadata services for logic correctness in `backend/src/services/agent_creator.py`, `backend/src/services/agent_tracking.py`, `backend/src/services/metadata_service.py`
- [ ] T052 [P] [US2] Audit pipeline service for logic bugs in `backend/src/services/pipelines/service.py`
- [ ] T053 [P] [US2] Audit tools service for logic bugs in `backend/src/services/tools/service.py`

### Backend API Logic Audit

- [ ] T054 [P] [US2] Audit chat API for fallback path logic (ai_enhance=True vs ai_enhance=False branches) in `backend/src/api/chat.py` — verify both branches handle errors independently per recent fix
- [ ] T055 [P] [US2] Audit workflow API for incorrect method calls in `backend/src/api/workflow.py` — check `get_agent_preferences()` call matches service method name
- [ ] T056 [P] [US2] Audit chores API for inline-update and create-with-merge logic in `backend/src/api/chores.py`

### Backend Model Validation Audit

- [ ] T057 [P] [US2] Audit all Pydantic models for type safety and validation rules in `backend/src/models/` — check for missing validators, incorrect types, serialization issues across all 18 model files

### Frontend Runtime Error Audit

- [ ] T058 [P] [US2] Audit error boundary implementation in `frontend/src/components/common/ErrorBoundary.tsx` — check for uncaught promise rejections, missing error boundaries in page components
- [ ] T059 [P] [US2] Audit null/undefined access patterns in board components in `frontend/src/components/board/ProjectBoard.tsx`, `frontend/src/components/board/BoardColumn.tsx`, `frontend/src/components/board/IssueCard.tsx`, `frontend/src/components/board/IssueDetailModal.tsx`
- [ ] T060 [P] [US2] Audit hooks for stale closures and race conditions in `frontend/src/hooks/useProjectBoard.ts`, `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useRealTimeSync.ts`, `frontend/src/hooks/useBoardRefresh.ts`
- [ ] T061 [P] [US2] Audit pipeline components for runtime errors in `frontend/src/components/pipeline/PipelineBoard.tsx`, `frontend/src/components/pipeline/PipelineFlowGraph.tsx`, `frontend/src/components/pipeline/StageCard.tsx`
- [ ] T062 [P] [US2] Audit chores components for runtime errors in `frontend/src/components/chores/ChoresPanel.tsx`, `frontend/src/components/chores/ChoreCard.tsx`, `frontend/src/components/chores/ChoreInlineEditor.tsx`

### Frontend Logic Bug Audit

- [ ] T063 [P] [US2] Audit board controls hook for filter/sort/group state management bugs in `frontend/src/hooks/useBoardControls.ts` — check localStorage persistence, state reset edge cases
- [ ] T064 [P] [US2] Audit agent usage count computation for off-by-one or missing-count errors in `frontend/src/pages/AgentsPage.tsx` and `frontend/src/components/agents/AgentsPanel.tsx` — verify Featured Agents two-pass algorithm correctness
- [ ] T065 [P] [US2] Audit settings form hooks for state management bugs in `frontend/src/hooks/useSettings.ts`, `frontend/src/hooks/useSettingsForm.ts`
- [ ] T066 [P] [US2] Audit chat history hook for data consistency in `frontend/src/hooks/useChatHistory.ts`
- [ ] T067 [P] [US2] Audit pipeline config hook for state management bugs in `frontend/src/hooks/usePipelineConfig.ts`

### Runtime & Logic Regression Tests

- [ ] T068 [US2] Add regression tests for each runtime error and logic bug fix found in backend — create test functions in appropriate files under `backend/tests/unit/`
- [ ] T069 [US2] Add regression tests for each runtime error and logic bug fix found in frontend — create test cases in appropriate co-located test files
- [ ] T070 [US2] Run full backend test suite (`python -m pytest tests/unit/ -v`) and verify all tests pass including new regression tests
- [ ] T071 [US2] Run full frontend test suite (`npx vitest run`) and verify all tests pass including new regression tests
- [ ] T072 [US2] Run all linting checks (`ruff check src/ tests/` backend, `npx eslint src/ && npx tsc --noEmit` frontend) and verify zero errors

**Checkpoint**: All runtime errors and logic bugs identified and fixed. Each fix has a regression test. Full test suite passes.

---

## Phase 5: User Story 3 — Test Quality Improvement (Priority: P3)

**Goal**: Identify and fix test gaps and low-quality tests: mock leaks, tautological assertions, untested code paths, and tests that pass for the wrong reason.

**Independent Test**: Verify corrected tests properly validate the behavior they claim to test by confirming that intentionally broken code causes the relevant test to fail.

### Backend Test Quality Audit

- [ ] T073 [P] [US3] Audit test helpers for mock leaks in `backend/tests/helpers/mocks.py` — check for MagicMock objects leaking into production paths (e.g., mock objects used as file paths, database URLs, or config values)
- [ ] T074 [P] [US3] Audit test factories for correctness in `backend/tests/helpers/factories.py` — check that factory-generated test data matches production data shapes
- [ ] T075 [P] [US3] Audit test assertions for tautological checks in `backend/tests/helpers/assertions.py` — check for assertions that can never fail
- [ ] T076 [P] [US3] Audit conftest fixtures for shared state issues in `backend/tests/conftest.py` — check for fixture leaks between tests
- [ ] T077 [P] [US3] Audit database and migration tests for mock leaks in `backend/tests/unit/test_database.py` — check that mock database paths don't leak into migration runner
- [ ] T078 [P] [US3] Audit agent service tests for assertion quality in `backend/tests/unit/test_agents_service.py` — check that tests verify actual behavior, not just that mocks were called
- [ ] T079 [P] [US3] Audit AI agent tests for coverage gaps in `backend/tests/unit/test_ai_agent.py` — check for untested error paths, missing edge cases in title generation and task creation
- [ ] T080 [P] [US3] Audit API endpoint tests for coverage completeness in `backend/tests/unit/test_api_auth.py`, `backend/tests/unit/test_api_chat.py`, `backend/tests/unit/test_api_board.py`, `backend/tests/unit/test_api_workflow.py`, `backend/tests/unit/test_api_projects.py`, `backend/tests/unit/test_api_settings.py`, `backend/tests/unit/test_api_mcp.py`, `backend/tests/unit/test_api_tasks.py`
- [ ] T081 [P] [US3] Audit chores tests for mock correctness in `backend/tests/unit/test_chores_service.py`, `backend/tests/unit/test_chores_scheduler.py`, `backend/tests/unit/test_chores_counter.py`, `backend/tests/unit/test_chores_api.py`
- [ ] T082 [P] [US3] Audit remaining backend unit tests for assertion quality and mock leaks in `backend/tests/unit/test_config.py`, `backend/tests/unit/test_main.py`, `backend/tests/unit/test_middleware.py`, `backend/tests/unit/test_github_auth.py`, `backend/tests/unit/test_github_projects.py`, `backend/tests/unit/test_copilot_polling.py`, `backend/tests/unit/test_completion_providers.py`, `backend/tests/unit/test_webhooks.py`, `backend/tests/unit/test_websocket.py`, `backend/tests/unit/test_models.py`
- [ ] T083 [P] [US3] Audit utility and infrastructure tests in `backend/tests/unit/test_utils.py`, `backend/tests/unit/test_cache.py`, `backend/tests/unit/test_session_store.py`, `backend/tests/unit/test_settings_store.py`, `backend/tests/unit/test_token_encryption.py`, `backend/tests/unit/test_mcp_store.py`, `backend/tests/unit/test_cleanup_service.py`, `backend/tests/unit/test_logging_utils.py`
- [ ] T084 [P] [US3] Audit edge-case and specialized tests in `backend/tests/unit/test_error_responses.py`, `backend/tests/unit/test_exceptions.py`, `backend/tests/unit/test_oauth_state.py`, `backend/tests/unit/test_auth_security.py`, `backend/tests/unit/test_completion_false_positive.py`, `backend/tests/unit/test_issue_creation_retry.py`, `backend/tests/unit/test_prompts.py`, `backend/tests/unit/test_recommendation_models.py`, `backend/tests/unit/test_module_boundaries.py`
- [ ] T085 [P] [US3] Audit integration tests for correctness in `backend/tests/integration/test_custom_agent_assignment.py`, `backend/tests/integration/test_health_endpoint.py`, `backend/tests/integration/test_webhook_verification.py`

### Frontend Test Quality Audit

- [ ] T086 [P] [US3] Audit board component tests for assertion quality and mock correctness in `frontend/src/components/board/BoardColumn.test.tsx`, `frontend/src/components/board/IssueCard.test.tsx`, `frontend/src/components/board/IssueDetailModal.test.tsx`, `frontend/src/components/board/AgentSaveBar.test.tsx`, `frontend/src/components/board/AgentTile.test.tsx`
- [ ] T087 [P] [US3] Audit chat component tests for coverage gaps in `frontend/src/components/chat/CommandAutocomplete.test.tsx`, `frontend/src/components/chat/MessageBubble.test.tsx`, `frontend/src/components/chat/StatusChangePreview.test.tsx`, `frontend/src/components/chat/TaskPreview.test.tsx`, `frontend/src/components/chat/IssueRecommendationPreview.test.tsx`
- [ ] T088 [P] [US3] Audit pipeline component tests for correctness in `frontend/src/components/pipeline/PipelineBoard.test.tsx`, `frontend/src/components/pipeline/PipelineFlowGraph.test.tsx`, `frontend/src/components/pipeline/StageCard.test.tsx`, `frontend/src/components/pipeline/AgentNode.test.tsx`
- [ ] T089 [P] [US3] Audit agent and chores component tests in `frontend/src/components/agents/__tests__/AddAgentModal.test.tsx`, `frontend/src/components/agents/__tests__/AgentsPanel.test.tsx`, `frontend/src/components/chores/__tests__/AddChoreModal.test.tsx`, `frontend/src/components/chores/__tests__/ChoreScheduleConfig.test.tsx`, `frontend/src/components/chores/__tests__/ChoresPanel.test.tsx`, `frontend/src/components/chores/__tests__/FeaturedRitualsPanel.test.tsx`
- [ ] T090 [P] [US3] Audit UI, settings, common, and theme tests in `frontend/src/components/ui/button.test.tsx`, `frontend/src/components/ui/card.test.tsx`, `frontend/src/components/ui/input.test.tsx`, `frontend/src/components/settings/DynamicDropdown.test.tsx`, `frontend/src/components/settings/SettingsSection.test.tsx`, `frontend/src/components/common/ErrorBoundary.test.tsx`, `frontend/src/components/common/ThemedAgentIcon.test.tsx`, `frontend/src/components/ThemeProvider.test.tsx`
- [ ] T091 [P] [US3] Audit hook tests and auth tests in `frontend/src/hooks/useChatHistory.test.ts`, `frontend/src/components/auth/LoginButton.test.tsx`
- [ ] T092 [P] [US3] Audit test utilities and factories for correctness in `frontend/src/test/test-utils.tsx`, `frontend/src/test/factories/index.ts`, `frontend/src/test/setup.ts`, `frontend/src/test/a11y-helpers.ts`

### Test Quality Fixes and Validation

- [ ] T093 [US3] Fix all identified mock leaks — ensure no MagicMock or vi.fn() objects are used as production values (file paths, URLs, config)
- [ ] T094 [US3] Fix all identified tautological assertions — replace with meaningful assertions that would fail if behavior changed
- [ ] T095 [US3] Add new tests for identified untested critical code paths in both `backend/tests/` and `frontend/src/`
- [ ] T096 [US3] Run full backend test suite (`python -m pytest tests/unit/ -v`) and verify all tests pass after quality improvements
- [ ] T097 [US3] Run full frontend test suite (`npx vitest run`) and verify all tests pass after quality improvements

**Checkpoint**: All test quality issues identified and fixed. Mock leaks removed, tautological assertions replaced, coverage gaps filled. Test suite validates real behavior.

---

## Phase 6: User Story 4 — Code Quality Cleanup (Priority: P4)

**Goal**: Remove dead code, unreachable branches, duplicated logic, and address silent failures. Improve maintainability without changing architecture or public API.

**Independent Test**: Verify that removal of dead code and unreachable branches does not change any test outcome. Previously silent failures now produce appropriate error feedback.

### Backend Code Quality Audit

- [ ] T098 [P] [US4] Audit for dead code and unused imports across all files in `backend/src/api/` (18 modules) — remove dead imports and unreachable branches
- [ ] T099 [P] [US4] Audit for dead code and unused imports across all files in `backend/src/services/` (47 modules) — remove dead imports and unreachable branches
- [ ] T100 [P] [US4] Audit for dead code and unused imports in `backend/src/models/` (18 modules) and core files (`backend/src/config.py`, `backend/src/constants.py`, `backend/src/dependencies.py`, `backend/src/exceptions.py`, `backend/src/logging_utils.py`, `backend/src/main.py`, `backend/src/utils.py`)
- [ ] T101 [P] [US4] Audit for silent failures (swallowed exceptions, missing error messages) in `backend/src/services/` — add appropriate error feedback where exceptions are caught and silently discarded
- [ ] T102 [P] [US4] Audit for hardcoded values that should be configurable in `backend/src/config.py`, `backend/src/constants.py`, `backend/src/services/` — note (do not fix) any that require config changes

### Frontend Code Quality Audit

- [ ] T103 [P] [US4] Audit for dead code, unused imports, and unreachable branches across all files in `frontend/src/components/` — remove dead imports and unreachable code
- [ ] T104 [P] [US4] Audit for dead code and unused imports in `frontend/src/pages/` (9 page components), `frontend/src/hooks/` (30 hooks), and `frontend/src/services/api.ts`
- [ ] T105 [P] [US4] Audit for silent failures in frontend error handling — check for swallowed promise rejections, missing user feedback on errors in `frontend/src/hooks/` and `frontend/src/components/`

### Code Quality Fixes and Validation

- [ ] T106 [US4] Add regression tests for any silent failure fixes (where previously silent errors now produce feedback) in `backend/tests/unit/` and `frontend/src/`
- [ ] T107 [US4] Run full backend test suite (`python -m pytest tests/unit/ -v`) and verify all tests pass after code quality cleanup
- [ ] T108 [US4] Run full frontend test suite (`npx vitest run`) and verify all tests pass after code quality cleanup
- [ ] T109 [US4] Run all linting checks (`ruff check src/ tests/` backend, `npx eslint src/ && npx tsc --noEmit` frontend) and verify zero errors after cleanup

**Checkpoint**: Dead code removed, unreachable branches eliminated, silent failures addressed. All tests continue to pass.

---

## Phase 7: User Story 5 — Ambiguous Issue Flagging (Priority: P5)

**Goal**: Document all ambiguous or trade-off situations with `TODO(bug-bash):` comments. These are issues where multiple valid approaches exist or where a fix might change public API behavior.

**Independent Test**: Search the codebase for `TODO(bug-bash):` comments and verify each includes: issue description, available options, and rationale for human review.

### Known Ambiguous Issues (from research.md)

- [ ] T110 [P] [US5] Add or verify `TODO(bug-bash):` comment for migration numbering conflicts (R-001) at `backend/src/services/database.py` near migration discovery logic — document the duplicate prefix issue (013, 014, 015), the deployment impact, and the options for resolution
- [ ] T111 [P] [US5] Verify existing `TODO(bug-bash):` comments for Signal error message leakage (R-002) in `backend/src/services/signal_chat.py` — confirm comments describe the trade-off between sanitized vs. detailed error messages
- [ ] T112 [P] [US5] Add or verify `TODO(bug-bash):` comment for CORS configuration permissiveness (R-004) at `backend/src/main.py` near CORS middleware setup — document `allow_methods=["*"]` and `allow_headers=["*"]` with options and rationale

### Discovered Ambiguous Issues

- [ ] T113 [US5] Add `TODO(bug-bash):` comments for any additional ambiguous issues discovered during Phases 3–6 that were not fixed
- [ ] T114 [US5] Compile list of all `TODO(bug-bash):` comments in the codebase (grep for `TODO(bug-bash):`) and verify each follows the format: `# TODO(bug-bash): <description>. Options: (1) <A>, (2) <B>. Human decision needed: <rationale>.`

### Validation

- [ ] T115 [US5] Run full backend test suite (`python -m pytest tests/unit/ -v`) and verify no TODO comments accidentally broke anything
- [ ] T116 [US5] Run full frontend test suite (`npx vitest run`) and verify no TODO comments accidentally broke anything

**Checkpoint**: All ambiguous issues documented with properly formatted `TODO(bug-bash):` comments. No code behavior changed.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary generation, and documentation.

- [ ] T117 Run full backend test suite one final time (`cd backend && python -m pytest tests/unit/ -v`) — must be zero failures
- [ ] T118 Run full frontend test suite one final time (`cd frontend && npx vitest run`) — must be zero failures
- [ ] T119 [P] Run backend linting one final time (`cd backend && ruff check src/ tests/`) — must be zero errors
- [ ] T120 [P] Run frontend linting and type-check one final time (`cd frontend && npx eslint src/ && npx tsc --noEmit`) — must be zero errors
- [ ] T121 Generate the Bug Bash Summary Table following the format in `specs/030-bug-basher/contracts/summary-table.md` — list every bug found with file, line(s), category, description, and status (✅ Fixed or ⚠️ Flagged)
- [ ] T122 Verify summary table ordering: entries grouped by category (Security → Runtime → Logic → Test Quality → Code Quality), within category by file path (alphabetical), within file by line number (ascending)
- [ ] T123 Verify every `✅ Fixed` entry in summary has a corresponding regression test
- [ ] T124 Verify every `⚠️ Flagged (TODO)` entry has a corresponding `TODO(bug-bash):` comment in source code
- [ ] T125 Final review: confirm no new dependencies added, no architecture changes, no public API changes, code style preserved

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1: Security (Phase 3)**: Depends on Foundational phase — highest priority, do first
- **US2: Runtime & Logic (Phase 4)**: Depends on Foundational phase — can start after US1 or in parallel
- **US3: Test Quality (Phase 5)**: Depends on Foundational phase — ideally after US1+US2 (so test fixes don't conflict with code changes)
- **US4: Code Quality (Phase 6)**: Depends on Foundational phase — ideally after US1+US2+US3 (dead code may be exposed by earlier fixes)
- **US5: Ambiguous Flagging (Phase 7)**: Depends on Phases 3–6 — collects all deferred issues
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1) — Security**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2) — Runtime & Logic**: Can start after Foundational (Phase 2) — Independent of US1, but recommended after US1 to avoid merge conflicts
- **US3 (P3) — Test Quality**: Best done after US1+US2 so that test fixes account for code changes already made
- **US4 (P4) — Code Quality**: Best done after US1+US2+US3 so that dead code from earlier fixes is included
- **US5 (P5) — Ambiguous Flagging**: Must be done last among story phases since it collects deferred issues from all prior phases

### Within Each User Story

- Audit tasks marked [P] can run in parallel (they target different files/modules)
- Regression test creation depends on audit tasks completing first
- Test suite validation depends on regression tests being written
- Linting validation depends on all code changes being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004)
- All Foundational tasks marked [P] can run in parallel (T007, T008)
- Within US1: All audit tasks (T010–T030) can run in parallel — they audit different files
- Within US2: All audit tasks (T037–T067) can run in parallel — they audit different files
- Within US3: All audit tasks (T073–T092) can run in parallel — they review different test files
- Within US4: All audit tasks (T098–T105) can run in parallel — they audit different files
- Within US5: Known issue tasks (T110–T112) can run in parallel
- US1 and US2 can theoretically run in parallel (different focus areas) though sequential is safer

---

## Parallel Example: User Story 1 (Security)

```bash
# Launch all backend API security audits together (different files, no dependencies):
Task T010: "Audit auth.py for auth bypasses"
Task T011: "Audit webhooks.py for signature verification"
Task T012: "Audit chat.py for injection risks"
Task T013: "Audit agents.py for input validation"
Task T014: "Audit workflow.py for input validation"
Task T015: "Audit settings.py for data exposure"
Task T016: "Audit signal.py for input validation"
Task T017: "Audit remaining API modules"

# Launch all backend service security audits together:
Task T018: "Audit config.py for hardcoded secrets"
Task T019: "Audit encryption.py for weak algorithms"
Task T020: "Audit github_auth.py for token handling"
Task T021: "Audit session_store.py for session fixation"
Task T022: "Audit main.py for CORS and error leakage"

# Launch all frontend security audits together:
Task T028: "Audit api.ts for token handling"
Task T029: "Audit auth hook for OAuth security"
Task T030: "Audit chat components for XSS"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — verify test baselines
2. Complete Phase 2: Foundational — catalog audit scope
3. Complete Phase 3: US1 Security — fix all security vulnerabilities
4. **STOP and VALIDATE**: Run full test suite, verify all regression tests pass
5. Deploy/demo if ready — codebase is secure

### Incremental Delivery

1. Complete Setup + Foundational → Review environment ready
2. Add US1: Security → Test independently → **MVP delivered** (most critical bugs fixed)
3. Add US2: Runtime & Logic → Test independently → Reliable application
4. Add US3: Test Quality → Test independently → Trustworthy test suite
5. Add US4: Code Quality → Test independently → Clean, maintainable codebase
6. Add US5: Ambiguous Flagging → Document remaining → Complete audit trail
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Security — backend)
   - Developer B: US1 (Security — frontend)
   - Developer C: US2 (Runtime & Logic — backend)
3. After US1 completes:
   - Developer A: US3 (Test Quality — backend)
   - Developer B: US3 (Test Quality — frontend)
   - Developer C: US2 (continues Runtime & Logic)
4. After US2+US3 complete:
   - All developers: US4 (Code Quality) + US5 (Flagging)
5. Final: Polish phase together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are REQUIRED per FR-004 — every bug fix needs a regression test
- Commit after each task or logical group using format: `fix(<category>): <short description>`
- Stop at any checkpoint to validate story independently
- Known issues from research.md (R-001 through R-008) are pre-integrated into the appropriate phases
- Summary table format follows `specs/030-bug-basher/contracts/summary-table.md`
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
