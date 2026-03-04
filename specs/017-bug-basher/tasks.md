# Tasks: Bug Basher — Comprehensive Codebase Review & Fix

**Input**: Design documents from `/specs/017-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Regression tests are MANDATORY per FR-003 — each bug fix MUST include at least one regression test that would have detected the original bug.

**Organization**: Tasks are grouped by user story (bug category) to enable independent implementation and testing. Each phase audits the full codebase for one bug category in priority order: Security → Runtime → Logic → Test Quality → Code Quality → Summary Report.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/e2e/`
- **Infrastructure**: `.github/workflows/`, `docker-compose.yml`, `Dockerfile`

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Establish a clean baseline before auditing. Confirm all tests pass and linters are clean so that pre-existing failures are documented and excluded from findings.

- [ ] T001 Run backend test suite to establish baseline via `cd backend && python -m pytest tests/unit/ -q`
- [ ] T002 [P] Run backend linting baseline via `cd backend && ruff check src tests && ruff format --check src tests`
- [ ] T003 [P] Run frontend test suite to establish baseline via `cd frontend && npx vitest run`
- [ ] T004 [P] Run frontend linting baseline via `cd frontend && npx eslint . && npx tsc --noEmit`
- [ ] T005 Document any pre-existing test or lint failures in a baseline-failures note for exclusion from audit findings

**Checkpoint**: Baseline established — all pre-existing test/lint status is documented. Audit phases can begin.

---

## Phase 2: Foundational (Automated Scanning & File Inventory)

**Purpose**: Run automated static analysis tools to surface low-hanging issues before manual review. Generate a file inventory for systematic tracking. MUST complete before user story phases.

**⚠️ CRITICAL**: No manual audit work can begin until this phase is complete.

- [ ] T006 Run Ruff with extended rules on backend to identify potential issues via `cd backend && ruff check src tests --select ALL` and document findings
- [ ] T007 [P] Run type checking on backend via Pyright or mypy to catch type errors and document findings
- [ ] T008 [P] Run ESLint on frontend to identify potential issues via `cd frontend && npx eslint .` and document findings
- [ ] T009 [P] Run TypeScript strict type check on frontend via `cd frontend && npx tsc --noEmit` and document findings
- [ ] T010 Generate file inventory categorized by risk level (High: auth/security/database, Medium: API/services, Low: models/utilities) for systematic audit tracking
- [ ] T011 Triage automated scan findings into the five bug categories (Security, Runtime, Logic, Test Quality, Code Quality) for targeted manual review

**Checkpoint**: Automated scan complete — triaged findings feed into manual review phases. File inventory ready for systematic audit tracking.

---

## Phase 3: User Story 1 — Security Vulnerability Audit and Remediation (Priority: P1) 🎯 MVP

**Goal**: Audit every file for authentication bypasses, injection risks, exposed secrets/tokens, insecure defaults, and improper input validation. Fix confirmed vulnerabilities with regression tests. Flag ambiguous security concerns with `TODO(bug-bash)` comments.

**Independent Test**: Run `cd backend && python -m pytest tests/ -q` and `cd frontend && npx vitest run` — all existing + new regression tests pass. Every security finding has a Fix (with regression test) or Flag (`TODO(bug-bash)` comment).

### Backend Security Audit

- [ ] T012 [US1] Audit OAuth flow, session cookies, redirect validation, and token handling in `backend/src/api/auth.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_api_auth.py`
- [ ] T013 [US1] Audit admin authorization, session validation, and TOCTOU race conditions in `backend/src/dependencies.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_admin_authorization.py`
- [ ] T014 [US1] Audit secret management, environment variable handling, and cookie security defaults in `backend/src/config.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_config.py`
- [ ] T015 [US1] Audit encryption key management and token encryption in `backend/src/services/encryption.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_token_encryption.py`
- [ ] T016 [US1] Audit SQL query construction for injection risks and parameterized query usage in `backend/src/services/database.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_database.py`
- [ ] T017 [US1] Audit GitHub API token usage, input validation, and security of external API calls in `backend/src/services/github_projects/service.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_github_projects.py`
- [ ] T018 [P] [US1] Audit user input handling, command injection risks, and XSS in responses in `backend/src/api/chat.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_api_chat.py`
- [ ] T019 [P] [US1] Audit input validation and authentication enforcement in remaining backend API files: `backend/src/api/board.py`, `backend/src/api/tasks.py`, `backend/src/api/projects.py`, `backend/src/api/settings.py`, `backend/src/api/cleanup.py`, `backend/src/api/workflow.py`, `backend/src/api/chores.py`, `backend/src/api/mcp.py`, `backend/src/api/signal.py`, `backend/src/api/webhooks.py`, `backend/src/api/health.py` — fix confirmed vulnerabilities with regression tests
- [ ] T020 [P] [US1] Audit AI agent orchestration for prompt injection risks and input sanitization in `backend/src/services/ai_agent.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_ai_agent.py`
- [ ] T021 [P] [US1] Audit Signal messaging integration for input validation and credential handling in `backend/src/services/signal_chat.py`, `backend/src/services/signal_bridge.py`, `backend/src/services/signal_delivery.py` — fix confirmed vulnerabilities with regression tests
- [ ] T022 [P] [US1] Audit GitHub authentication service for token handling and OAuth state security in `backend/src/services/github_auth.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_github_auth.py`
- [ ] T023 [P] [US1] Audit session store for session fixation and session data exposure in `backend/src/services/session_store.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_session_store.py`
- [ ] T024 [P] [US1] Audit logging utilities for sensitive data leaks in log output in `backend/src/logging_utils.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_logging_utils.py`

### Frontend Security Audit

- [ ] T025 [US1] Audit credential handling, CORS configuration, and sensitive data exposure in API URLs in `frontend/src/services/api.ts` — fix confirmed vulnerabilities with regression tests
- [ ] T026 [P] [US1] Audit all React components for XSS via `dangerouslySetInnerHTML`, unsanitized user content rendering, and URL handling in `frontend/src/components/**/*.tsx` — fix confirmed vulnerabilities with regression tests
- [ ] T027 [P] [US1] Audit frontend hooks for sensitive data leaks, token storage, and insecure state management in `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/useChat.ts`, and all other `frontend/src/hooks/*.ts` — fix confirmed vulnerabilities with regression tests

### Infrastructure Security Audit

- [ ] T028 [P] [US1] Audit GitHub Actions workflows for secret exposure, insecure action versions, and injection risks in `.github/workflows/ci.yml`, `.github/workflows/housekeeping-cron.yml`, `.github/workflows/branch-issue-link.yml` — fix confirmed vulnerabilities
- [ ] T029 [P] [US1] Audit Docker configuration for insecure defaults, exposed ports, and secret leaks in `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` — fix confirmed vulnerabilities

### US1 Verification

- [ ] T030 [US1] Run full backend test suite `cd backend && python -m pytest tests/ -q` to verify all security fixes and regression tests pass
- [ ] T031 [US1] Run full frontend test suite `cd frontend && npx vitest run` to verify all security fixes and regression tests pass

**Checkpoint**: Security audit complete — all confirmed security vulnerabilities have fixes with regression tests. Ambiguous security concerns flagged with `TODO(bug-bash)` comments.

---

## Phase 4: User Story 2 — Runtime Error Detection and Resolution (Priority: P1)

**Goal**: Audit every file for unhandled exceptions, race conditions, null/None references, missing imports, type errors, file handle leaks, and database connection leaks. Fix confirmed runtime errors with regression tests. Flag ambiguous runtime concerns.

**Independent Test**: Run `cd backend && python -m pytest tests/ -q` and `cd frontend && npx vitest run` — all existing + new regression tests pass. Every runtime error finding has a Fix or Flag.

### Backend Runtime Error Audit

- [ ] T032 [US2] Audit async exception handling and error propagation in all FastAPI route handlers in `backend/src/api/auth.py`, `backend/src/api/chat.py`, `backend/src/api/board.py`, `backend/src/api/workflow.py`, `backend/src/api/tasks.py`, `backend/src/api/projects.py`, `backend/src/api/settings.py`, `backend/src/api/cleanup.py`, `backend/src/api/chores.py`, `backend/src/api/mcp.py`, `backend/src/api/signal.py`, `backend/src/api/webhooks.py` — fix unhandled exceptions with regression tests
- [ ] T033 [US2] Audit SQLite connection and transaction management for resource leaks in `backend/src/services/database.py` and all callers of `get_db()` — fix confirmed leaks with regression tests in `backend/tests/unit/test_database.py`
- [ ] T034 [US2] Audit null/None reference patterns and optional field access in `backend/src/services/github_projects/service.py` — fix confirmed null reference errors with regression tests in `backend/tests/unit/test_github_projects.py`
- [ ] T035 [P] [US2] Audit async context errors and exception handling in `backend/src/services/ai_agent.py` — fix confirmed runtime errors with regression tests in `backend/tests/unit/test_ai_agent.py`
- [ ] T036 [P] [US2] Audit resource cleanup and error handling in `backend/src/services/signal_chat.py`, `backend/src/services/signal_bridge.py`, `backend/src/services/signal_delivery.py` — fix confirmed runtime errors with regression tests
- [ ] T037 [P] [US2] Audit exception handling in `backend/src/services/cleanup_service.py`, `backend/src/services/cache.py`, `backend/src/services/model_fetcher.py`, `backend/src/services/mcp_store.py`, `backend/src/services/settings_store.py`, `backend/src/services/websocket.py` — fix confirmed runtime errors with regression tests
- [ ] T038 [P] [US2] Audit exception handling in copilot polling pipeline: `backend/src/services/copilot_polling/polling_loop.py`, `backend/src/services/copilot_polling/pipeline.py`, `backend/src/services/copilot_polling/recovery.py`, `backend/src/services/copilot_polling/completion.py`, `backend/src/services/copilot_polling/state.py`, `backend/src/services/copilot_polling/agent_output.py`, `backend/src/services/copilot_polling/helpers.py` — fix confirmed runtime errors with regression tests
- [ ] T039 [P] [US2] Audit exception handling in workflow orchestrator: `backend/src/services/workflow_orchestrator/orchestrator.py`, `backend/src/services/workflow_orchestrator/transitions.py`, `backend/src/services/workflow_orchestrator/config.py`, `backend/src/services/workflow_orchestrator/models.py` — fix confirmed runtime errors with regression tests in `backend/tests/unit/test_workflow_orchestrator.py`
- [ ] T040 [P] [US2] Audit exception handling in chores subsystem: `backend/src/services/chores/service.py`, `backend/src/services/chores/scheduler.py`, `backend/src/services/chores/counter.py`, `backend/src/services/chores/chat.py`, `backend/src/services/chores/template_builder.py` — fix confirmed runtime errors with regression tests
- [ ] T041 [P] [US2] Audit missing imports and type errors across all backend source files using findings from T007 — fix confirmed import/type errors
- [ ] T042 [US2] Audit FastAPI lifespan management, cleanup loop, and background task error handling in `backend/src/main.py` — fix confirmed runtime errors with regression tests in `backend/tests/unit/test_main.py`
- [ ] T043 [P] [US2] Audit `backend/src/utils.py` for unhandled exceptions in utility functions (e.g., `resolve_repository`) — fix confirmed runtime errors with regression tests in `backend/tests/unit/test_utils.py`

### Frontend Runtime Error Audit

- [ ] T044 [US2] Audit WebSocket lifecycle management and reconnection handling in `frontend/src/hooks/useRealTimeSync.ts` — fix confirmed runtime errors with regression tests in `frontend/src/hooks/useRealTimeSync.test.tsx`
- [ ] T045 [P] [US2] Audit React error boundary coverage and error recovery in `frontend/src/components/common/ErrorBoundary.tsx` — fix confirmed gaps with regression tests in `frontend/src/components/common/ErrorBoundary.test.tsx`
- [ ] T046 [P] [US2] Audit React hook error handling, stale data, and race conditions in `frontend/src/hooks/useProjectBoard.ts`, `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useBoardRefresh.ts`, `frontend/src/hooks/useWorkflow.ts`, `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/useProjects.ts`, `frontend/src/hooks/useCommands.ts`, `frontend/src/hooks/useSettingsForm.ts`, `frontend/src/hooks/useSettings.ts`, `frontend/src/hooks/useChores.ts`, `frontend/src/hooks/useCleanup.ts`, `frontend/src/hooks/useMcpSettings.ts`, `frontend/src/hooks/useAgentConfig.ts`, `frontend/src/hooks/useAppTheme.ts` — fix confirmed runtime errors with regression tests
- [ ] T047 [P] [US2] Audit null/undefined reference patterns in frontend components `frontend/src/components/board/*.tsx`, `frontend/src/components/chat/*.tsx`, `frontend/src/components/settings/*.tsx`, `frontend/src/components/chores/*.tsx` — fix confirmed runtime errors with regression tests

### US2 Verification

- [ ] T048 [US2] Run full backend test suite `cd backend && python -m pytest tests/ -q` to verify all runtime error fixes and regression tests pass
- [ ] T049 [US2] Run full frontend test suite `cd frontend && npx vitest run` to verify all runtime error fixes and regression tests pass

**Checkpoint**: Runtime error audit complete — all confirmed runtime errors have fixes with regression tests. Ambiguous runtime concerns flagged with `TODO(bug-bash)` comments.

---

## Phase 5: User Story 3 — Logic Bug Identification and Correction (Priority: P2)

**Goal**: Audit every file for incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, and incorrect return values. Fix confirmed logic bugs with regression tests. Flag ambiguous logic concerns.

**Independent Test**: Run `cd backend && python -m pytest tests/ -q` and `cd frontend && npx vitest run` — all existing + new regression tests pass. Every logic bug finding has a Fix or Flag.

### Backend Logic Bug Audit

- [ ] T050 [US3] Audit state transitions, board column moves, and task status changes in `backend/src/services/github_projects/service.py` — fix confirmed logic bugs with regression tests in `backend/tests/unit/test_github_projects.py`
- [ ] T051 [P] [US3] Audit workflow orchestration state machine transitions in `backend/src/services/workflow_orchestrator/orchestrator.py`, `backend/src/services/workflow_orchestrator/transitions.py` — fix confirmed logic bugs with regression tests in `backend/tests/unit/test_workflow_orchestrator.py`
- [ ] T052 [P] [US3] Audit pagination logic, list slicing, and loop boundaries in all backend API handlers `backend/src/api/*.py` — fix confirmed off-by-one errors with regression tests
- [ ] T053 [P] [US3] Audit permission checks, boolean logic, and comparison operators in `backend/src/dependencies.py` and `backend/src/api/auth.py` — fix confirmed logic bugs with regression tests
- [ ] T054 [P] [US3] Audit return values, data transformation, and control flow in `backend/src/services/completion_providers.py`, `backend/src/services/agent_creator.py`, `backend/src/services/agent_tracking.py` — fix confirmed logic bugs with regression tests
- [ ] T055 [P] [US3] Audit copilot polling logic for state management and completion detection in `backend/src/services/copilot_polling/polling_loop.py`, `backend/src/services/copilot_polling/completion.py`, `backend/src/services/copilot_polling/state.py` — fix confirmed logic bugs with regression tests in `backend/tests/unit/test_copilot_polling.py`
- [ ] T056 [P] [US3] Audit chores scheduling logic, counter arithmetic, and template generation in `backend/src/services/chores/scheduler.py`, `backend/src/services/chores/counter.py`, `backend/src/services/chores/template_builder.py` — fix confirmed logic bugs with regression tests
- [ ] T057 [P] [US3] Audit data model validation and field constraints in `backend/src/models/*.py` — fix confirmed data consistency issues with regression tests in `backend/tests/unit/test_models.py`
- [ ] T058 [P] [US3] Audit prompt construction logic in `backend/src/prompts/issue_generation.py`, `backend/src/prompts/task_generation.py` — fix confirmed logic bugs with regression tests in `backend/tests/unit/test_prompts.py`
- [ ] T059 [P] [US3] Audit GraphQL query construction in `backend/src/services/github_projects/graphql.py` — fix confirmed logic bugs with regression tests

### Frontend Logic Bug Audit

- [ ] T060 [US3] Audit state management, data flow, and conditional rendering logic in `frontend/src/components/board/ProjectBoard.tsx`, `frontend/src/components/board/BoardColumn.tsx`, `frontend/src/components/board/IssueCard.tsx`, `frontend/src/components/board/IssueDetailModal.tsx`, and other `frontend/src/components/board/*.tsx` — fix confirmed logic bugs with regression tests
- [ ] T061 [P] [US3] Audit state management and message handling in `frontend/src/components/chat/ChatInterface.tsx`, `frontend/src/components/chat/ChatPopup.tsx`, `frontend/src/components/chat/MessageBubble.tsx`, `frontend/src/components/chat/CommandAutocomplete.tsx`, `frontend/src/components/chat/SystemMessage.tsx` — fix confirmed logic bugs with regression tests
- [ ] T062 [P] [US3] Audit form validation and settings update logic in `frontend/src/components/settings/GlobalSettings.tsx`, `frontend/src/components/settings/ProjectSettings.tsx`, `frontend/src/components/settings/PrimarySettings.tsx`, `frontend/src/components/settings/AIPreferences.tsx`, `frontend/src/components/settings/AdvancedSettings.tsx`, `frontend/src/components/settings/McpSettings.tsx`, `frontend/src/components/settings/SignalConnection.tsx`, `frontend/src/components/settings/DynamicDropdown.tsx` — fix confirmed logic bugs with regression tests
- [ ] T063 [P] [US3] Audit custom hook logic, data transformation, and edge case handling in `frontend/src/hooks/*.ts` — fix confirmed logic bugs with regression tests
- [ ] T064 [P] [US3] Audit API client request/response handling and error mapping in `frontend/src/services/api.ts` — fix confirmed logic bugs with regression tests
- [ ] T065 [P] [US3] Audit command registry and handler logic in `frontend/src/lib/commands/registry.ts`, `frontend/src/lib/commands/handlers/agent.ts`, `frontend/src/lib/commands/handlers/help.ts`, `frontend/src/lib/commands/handlers/settings.ts` — fix confirmed logic bugs with regression tests

### US3 Verification

- [ ] T066 [US3] Run full backend test suite `cd backend && python -m pytest tests/ -q` to verify all logic bug fixes and regression tests pass
- [ ] T067 [US3] Run full frontend test suite `cd frontend && npx vitest run` to verify all logic bug fixes and regression tests pass

**Checkpoint**: Logic bug audit complete — all confirmed logic bugs have fixes with regression tests. Ambiguous logic concerns flagged with `TODO(bug-bash)` comments.

---

## Phase 6: User Story 4 — Test Gap and Quality Assessment (Priority: P2)

**Goal**: Audit all test files for untested code paths, tests passing for wrong reasons, mock leaks (e.g., `MagicMock` objects leaking into production paths like database file paths), assertions that never fail, and missing edge case coverage. Fix confirmed test quality issues. Flag ambiguous test concerns.

**Independent Test**: Run `cd backend && python -m pytest tests/ -q` and `cd frontend && npx vitest run` — all tests pass. Deliberately breaking code under test causes corrected tests to fail.

### Backend Test Quality Audit

- [ ] T068 [US4] Audit all backend unit test files in `backend/tests/unit/test_api_auth.py`, `backend/tests/unit/test_api_board.py`, `backend/tests/unit/test_api_chat.py`, `backend/tests/unit/test_api_mcp.py`, `backend/tests/unit/test_api_projects.py`, `backend/tests/unit/test_api_settings.py`, `backend/tests/unit/test_api_tasks.py`, `backend/tests/unit/test_api_workflow.py` for assertions against mocks that are never called, never-failing asserts, and mock leaks into production paths — fix confirmed test quality issues
- [ ] T069 [P] [US4] Audit backend unit tests in `backend/tests/unit/test_admin_authorization.py`, `backend/tests/unit/test_agent_creator.py`, `backend/tests/unit/test_agent_tracking.py`, `backend/tests/unit/test_ai_agent.py`, `backend/tests/unit/test_auth_security.py`, `backend/tests/unit/test_board.py`, `backend/tests/unit/test_cache.py` for test correctness and mock leaks — fix confirmed test quality issues
- [ ] T070 [P] [US4] Audit backend unit tests in `backend/tests/unit/test_chores_api.py`, `backend/tests/unit/test_chores_counter.py`, `backend/tests/unit/test_chores_scheduler.py`, `backend/tests/unit/test_chores_service.py`, `backend/tests/unit/test_cleanup_service.py`, `backend/tests/unit/test_completion_false_positive.py`, `backend/tests/unit/test_completion_providers.py` for test correctness and mock leaks — fix confirmed test quality issues
- [ ] T071 [P] [US4] Audit backend unit tests in `backend/tests/unit/test_config.py`, `backend/tests/unit/test_copilot_polling.py`, `backend/tests/unit/test_database.py`, `backend/tests/unit/test_error_responses.py`, `backend/tests/unit/test_exceptions.py`, `backend/tests/unit/test_github_auth.py`, `backend/tests/unit/test_github_projects.py` for test correctness and mock leaks — fix confirmed test quality issues
- [ ] T072 [P] [US4] Audit backend unit tests in `backend/tests/unit/test_issue_creation_retry.py`, `backend/tests/unit/test_logging_utils.py`, `backend/tests/unit/test_main.py`, `backend/tests/unit/test_mcp_store.py`, `backend/tests/unit/test_middleware.py`, `backend/tests/unit/test_model_fetcher.py`, `backend/tests/unit/test_models.py` for test correctness and mock leaks — fix confirmed test quality issues
- [ ] T073 [P] [US4] Audit backend unit tests in `backend/tests/unit/test_module_boundaries.py`, `backend/tests/unit/test_oauth_state.py`, `backend/tests/unit/test_prompts.py`, `backend/tests/unit/test_recommendation_models.py`, `backend/tests/unit/test_session_store.py`, `backend/tests/unit/test_settings_store.py`, `backend/tests/unit/test_token_encryption.py` for test correctness and mock leaks — fix confirmed test quality issues
- [ ] T074 [P] [US4] Audit backend unit tests in `backend/tests/unit/test_utils.py`, `backend/tests/unit/test_webhooks.py`, `backend/tests/unit/test_websocket.py`, `backend/tests/unit/test_workflow_orchestrator.py` for test correctness and mock leaks — fix confirmed test quality issues
- [ ] T075 [P] [US4] Audit backend integration tests in `backend/tests/integration/test_custom_agent_assignment.py`, `backend/tests/integration/test_health_endpoint.py`, `backend/tests/integration/test_webhook_verification.py` and E2E test `backend/tests/test_api_e2e.py` for proper test isolation and meaningful assertions — fix confirmed test quality issues
- [ ] T076 [P] [US4] Audit `backend/tests/conftest.py` and test helpers in `backend/tests/helpers/assertions.py`, `backend/tests/helpers/factories.py`, `backend/tests/helpers/mocks.py` for shared fixture correctness, proper scope management, and potential cross-test contamination — fix confirmed issues
- [ ] T077 [US4] Identify untested critical code paths by comparing backend source files (`backend/src/`) against test files (`backend/tests/`) — add regression tests for the highest-risk uncovered paths

### Frontend Test Quality Audit

- [ ] T078 [US4] Audit all frontend test files `frontend/src/**/*.test.tsx` and `frontend/src/**/*.test.ts` for missing async waits, incomplete mock cleanup, and assertions that never fail — fix confirmed test quality issues
- [ ] T079 [P] [US4] Audit frontend test infrastructure in `frontend/src/test/setup.ts`, `frontend/src/test/test-utils.tsx`, `frontend/src/test/factories/index.ts`, `frontend/src/test/a11y-helpers.ts` for factory correctness, mock API completeness, and test utility reliability — fix confirmed issues
- [ ] T080 [P] [US4] Audit E2E test files in `frontend/e2e/auth.spec.ts`, `frontend/e2e/board-navigation.spec.ts`, `frontend/e2e/chat-interaction.spec.ts`, `frontend/e2e/integration.spec.ts`, `frontend/e2e/responsive-board.spec.ts`, `frontend/e2e/responsive-home.spec.ts`, `frontend/e2e/responsive-settings.spec.ts`, `frontend/e2e/settings-flow.spec.ts`, `frontend/e2e/ui.spec.ts` for flaky selectors, missing assertions, and incomplete test cleanup — fix confirmed test quality issues
- [ ] T081 [US4] Identify untested critical code paths by comparing frontend source files (`frontend/src/`) against test files — add regression tests for the highest-risk uncovered paths

### US4 Verification

- [ ] T082 [US4] Run full backend test suite `cd backend && python -m pytest tests/ -q` to verify all test quality fixes pass
- [ ] T083 [US4] Run full frontend test suite `cd frontend && npx vitest run` to verify all test quality fixes pass

**Checkpoint**: Test quality audit complete — all confirmed test quality issues have fixes. Test suite meaningfully validates code behavior.

---

## Phase 7: User Story 5 — Code Quality Cleanup (Priority: P3)

**Goal**: Audit every file for dead code, unreachable branches, duplicated logic, hardcoded values that should be configurable, missing error messages, and silent failures. Fix clear code quality issues. Flag ambiguous cases.

**Independent Test**: Run `cd backend && python -m pytest tests/ -q` and `cd frontend && npx vitest run` — all tests pass unchanged (code quality fixes must not change observable behavior).

### Backend Code Quality Audit

- [ ] T084 [US5] Audit for dead code, unused imports, and unreachable branches in `backend/src/services/github_projects/service.py` (largest file, highest priority) — remove confirmed dead code
- [ ] T085 [P] [US5] Audit for empty except blocks and silent error swallowing in all backend source files `backend/src/**/*.py` — add proper error handling or logging
- [ ] T086 [P] [US5] Audit for hardcoded values that should be in `backend/src/config.py` or `backend/src/constants.py` across all backend source files — move confirmed hardcoded values to config
- [ ] T087 [P] [US5] Audit for duplicated logic across backend service files `backend/src/services/*.py` — document DRY violations (flag for human review, as consolidation may be a refactor)
- [ ] T088 [P] [US5] Audit for dead code and unused imports in remaining backend files: `backend/src/api/*.py`, `backend/src/models/*.py`, `backend/src/middleware/*.py`, `backend/src/prompts/*.py` — remove confirmed dead code

### Frontend Code Quality Audit

- [ ] T089 [US5] Audit for dead code, unused imports, and unreachable branches in frontend components `frontend/src/components/**/*.tsx` — remove confirmed dead code
- [ ] T090 [P] [US5] Audit for silent failures and missing error messages in frontend hooks `frontend/src/hooks/*.ts` — add proper error handling or user-facing messages
- [ ] T091 [P] [US5] Audit for hardcoded values and duplicated logic in `frontend/src/services/api.ts`, `frontend/src/lib/utils.ts`, `frontend/src/lib/commands/*.ts`, `frontend/src/utils/*.ts`, `frontend/src/constants.ts` — fix or flag
- [ ] T092 [P] [US5] Audit for dead code and unused configuration in `frontend/src/App.tsx`, `frontend/src/main.tsx`, and config files `frontend/vite.config.ts`, `frontend/vitest.config.ts`, `frontend/eslint.config.js`, `frontend/tsconfig.json` — remove confirmed dead code

### Infrastructure Code Quality Audit

- [ ] T093 [P] [US5] Audit Docker configuration for dead/unused directives and hardcoded values in `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` — fix or flag
- [ ] T094 [P] [US5] Audit GitHub Actions workflows for dead steps, unused variables, and hardcoded values in `.github/workflows/ci.yml`, `.github/workflows/housekeeping-cron.yml`, `.github/workflows/branch-issue-link.yml` — fix or flag

### US5 Verification

- [ ] T095 [US5] Run full backend test suite and lint `cd backend && python -m pytest tests/ -q && ruff check src tests` to verify code quality fixes don't change behavior
- [ ] T096 [US5] Run full frontend test suite and lint `cd frontend && npx vitest run && npx eslint .` to verify code quality fixes don't change behavior

**Checkpoint**: Code quality audit complete — all confirmed dead code, silent failures, and unreachable branches fixed. Ambiguous cases flagged with `TODO(bug-bash)` comments.

---

## Phase 8: User Story 6 — Findings Summary Report (Priority: P1)

**Goal**: Produce a comprehensive summary table listing every finding from all audit phases. Each entry includes file path, line number(s), bug category, description, and resolution status (✅ Fixed or ⚠️ Flagged).

**Independent Test**: Every entry in the summary has a corresponding Fix commit or `TODO(bug-bash)` comment in the codebase. Every Fix commit and `TODO(bug-bash)` comment appears in the summary. Category counts match actual findings.

- [ ] T097 [US6] Compile all security findings (Phase 3) into the summary table with file path, line numbers, category (🔴 Security), description, and status (✅ Fixed / ⚠️ Flagged)
- [ ] T098 [P] [US6] Compile all runtime error findings (Phase 4) into the summary table with file path, line numbers, category (🟠 Runtime), description, and status
- [ ] T099 [P] [US6] Compile all logic bug findings (Phase 5) into the summary table with file path, line numbers, category (🟡 Logic), description, and status
- [ ] T100 [P] [US6] Compile all test quality findings (Phase 6) into the summary table with file path, line numbers, category (🔵 Test Quality), description, and status
- [ ] T101 [P] [US6] Compile all code quality findings (Phase 7) into the summary table with file path, line numbers, category (⚪ Code Quality), description, and status
- [ ] T102 [US6] Merge all category tables into a single findings summary report in `specs/017-bug-basher/summary-report.md` with counts per category, fixed/flagged totals, and overall test/lint status
- [ ] T103 [US6] Cross-reference summary report against actual codebase — verify every ✅ Fixed entry has a corresponding commit and regression test, and every ⚠️ Flagged entry has a `TODO(bug-bash)` comment at the documented location
- [ ] T104 [US6] Verify zero-finding categories are explicitly noted in the summary report with a "0 findings" entry

**Checkpoint**: Summary report complete and cross-referenced — every finding is documented and traceable.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all audit phases. Ensure complete consistency between fixes, flags, tests, and the summary report.

- [ ] T105 Run complete backend verification: `cd backend && python -m pytest tests/ -q && ruff check src tests && ruff format --check src tests`
- [ ] T106 Run complete frontend verification: `cd frontend && npx vitest run && npx eslint . && npx tsc --noEmit`
- [ ] T107 Verify all `TODO(bug-bash)` comments in the codebase are present in the summary report via `grep -rn "TODO(bug-bash)" backend/ frontend/ .github/`
- [ ] T108 Verify all regression test functions added during the bug bash are listed in the summary report
- [ ] T109 Final review of summary report for completeness: confirm every fix commit has a matching entry, category counts are accurate, and overall status reflects current test/lint state

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user story phases
- **US1: Security (Phase 3)**: Depends on Foundational — should complete FIRST (highest risk)
- **US2: Runtime (Phase 4)**: Depends on Foundational — can start after or in parallel with US1 (different focus areas)
- **US3: Logic (Phase 5)**: Depends on Foundational — can start after US1/US2 or in parallel
- **US4: Test Quality (Phase 6)**: Depends on US1–US3 completion (need all fixes applied before assessing test quality)
- **US5: Code Quality (Phase 7)**: Depends on Foundational — can start in parallel with US3
- **US6: Summary (Phase 8)**: Depends on ALL previous phases — must be last audit phase
- **Polish (Phase 9)**: Depends on US6 completion — final verification

### User Story Dependencies

- **US1 Security (P1)**: Can start immediately after Foundational — no dependencies on other stories
- **US2 Runtime (P1)**: Can start after Foundational — independent of US1 (different bug category)
- **US3 Logic (P2)**: Can start after Foundational — independent of US1/US2
- **US4 Test Quality (P2)**: Depends on US1–US3 — needs all fixes applied to assess test quality accurately; fixing a bug may reveal test gaps
- **US5 Code Quality (P3)**: Can start after Foundational — independent of US1–US3 but benefits from earlier fixes revealing dead code
- **US6 Summary Report (P1)**: Depends on ALL audit phases — cannot compile until all findings are documented

### Recommended Execution Order (Sequential)

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1: Security) → Phase 4 (US2: Runtime) → Phase 5 (US3: Logic) → Phase 6 (US4: Test Quality) → Phase 7 (US5: Code Quality) → Phase 8 (US6: Summary) → Phase 9 (Polish)
```

### Within Each User Story

- Audit backend files first (higher risk surface)
- Then audit frontend files
- Then audit infrastructure files (where applicable)
- Fix confirmed bugs immediately with regression tests
- Flag ambiguous issues with `TODO(bug-bash)` comments
- Run verification tests after completing each story phase

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T006, T007, T008, T009 can all run in parallel (independent tool scans)

**Within Phase 3 (US1: Security)**:
- T018, T019, T020, T021, T022, T023, T024 can run in parallel (different backend files)
- T026, T027 can run in parallel (different frontend areas)
- T028, T029 can run in parallel (different infrastructure files)

**Within Phase 4 (US2: Runtime)**:
- T035, T036, T037, T038, T039, T040, T041, T043 can run in parallel (different backend areas)
- T045, T046, T047 can run in parallel (different frontend areas)

**Within Phase 5 (US3: Logic)**:
- T051, T052, T053, T054, T055, T056, T057, T058, T059 can run in parallel (different file groups)
- T061, T062, T063, T064, T065 can run in parallel (different frontend areas)

**Within Phase 6 (US4: Test Quality)**:
- T069, T070, T071, T072, T073, T074, T075, T076 can run in parallel (different test file groups)
- T079, T080 can run in parallel (different frontend test areas)

**Within Phase 7 (US5: Code Quality)**:
- T085, T086, T087, T088 can run in parallel (different backend files)
- T090, T091, T092 can run in parallel (different frontend areas)
- T093, T094 can run in parallel (different infrastructure files)

**Within Phase 8 (US6: Summary)**:
- T098, T099, T100, T101 can run in parallel (independent category compilations)

**Cross-Story Parallelism** (with separate developers):
- US1 (Security) + US5 (Code Quality) can proceed simultaneously
- US2 (Runtime) + US3 (Logic) can proceed simultaneously after US1
- US4 (Test Quality) must wait for US1–US3

---

## Parallel Example: User Story 1 (Security Audit)

```bash
# Sequential: Backend critical files first (highest risk)
Task T012: "Audit auth.py for OAuth and session security"
Task T013: "Audit dependencies.py for authorization"
Task T014: "Audit config.py for secret management"
Task T015: "Audit encryption.py for key management"
Task T016: "Audit database.py for SQL injection"
Task T017: "Audit service.py for token security"

# Parallel: Remaining backend files (different files, no dependencies)
Task T018: "Audit chat.py for input handling"               # [P]
Task T019: "Audit remaining API files"                       # [P]
Task T020: "Audit ai_agent.py for prompt injection"          # [P]
Task T021: "Audit signal services for input validation"      # [P]
Task T022: "Audit github_auth.py for token handling"         # [P]
Task T023: "Audit session_store.py for session security"     # [P]
Task T024: "Audit logging_utils.py for data leaks"           # [P]

# Parallel: Frontend files (different files)
Task T025: "Audit api.ts for credential handling"
Task T026: "Audit components for XSS"                        # [P]
Task T027: "Audit hooks for data leaks"                      # [P]

# Parallel: Infrastructure files (different files)
Task T028: "Audit GitHub Actions workflows"                  # [P]
Task T029: "Audit Docker configuration"                      # [P]
```

---

## Implementation Strategy

### MVP First (Security Audit Only — US1)

1. Complete Phase 1: Setup (baseline verification)
2. Complete Phase 2: Foundational (automated scanning)
3. Complete Phase 3: US1 — Security Vulnerability Audit
4. **STOP and VALIDATE**: All security fixes have regression tests, all tests pass
5. This is the highest-value increment — security vulnerabilities pose the greatest risk

### Incremental Delivery

1. Setup + Foundational → Baseline established
2. US1: Security Audit → Fix all security bugs → Verify (MVP!)
3. US2: Runtime Errors → Fix all runtime bugs → Verify
4. US3: Logic Bugs → Fix all logic bugs → Verify
5. US4: Test Quality → Fix weak tests, add missing coverage → Verify
6. US5: Code Quality → Clean up dead code and silent failures → Verify
7. US6: Summary Report → Compile all findings → Cross-reference → Deliver
8. Each phase adds value and can be delivered independently

### Single Developer Strategy

Execute phases sequentially in strict priority order:
1. Security (P1) → Runtime (P1) → Logic (P2) → Test Quality (P2) → Code Quality (P3) → Summary (P1) → Polish
2. Within each phase: backend → frontend → infrastructure
3. Fix immediately when confirmed, flag immediately when ambiguous
4. Commit each fix individually with a descriptive commit message

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story (bug category) for traceability
- Each user story (bug category) should be independently completable and testable
- Tests are MANDATORY per FR-003: every fix must include ≥1 regression test
- Use flag format: `# TODO(bug-bash): <Category> — <Description>` for ambiguous issues
- Commit after each fix — one bug per commit, no bundled changes
- Run verification tests after completing each user story phase
- Stop at any checkpoint to validate phase independently
- Pre-existing failures documented in Phase 1 are EXCLUDED from audit findings
