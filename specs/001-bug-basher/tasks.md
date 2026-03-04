# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/001-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are REQUIRED for this feature — every bug fix MUST have at least one regression test (FR-004).

**Organization**: Tasks are grouped by user story (bug category) to enable independent implementation and testing of each category sweep. Each user story maps to one of the five bug categories defined in spec.md (P1–P5).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`, `backend/tests/integration/`
- **Frontend tests**: colocated `*.test.tsx` files in `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline state — ensure all existing tests pass and linting is clean before making any changes. Set up the audit tracking structure.

- [ ] T001 Install backend dependencies and verify environment in backend/ (`pip install -e ".[dev]"`)
- [ ] T002 [P] Install frontend dependencies and verify environment in frontend/ (`npm install`)
- [ ] T003 Run backend lint baseline: `ruff check src tests && ruff format --check src tests` in backend/
- [ ] T004 [P] Run frontend lint baseline: `npx eslint . && npx tsc --noEmit` in frontend/
- [ ] T005 Run backend test baseline: execute each `backend/tests/unit/test_*.py` individually with `timeout 30 python -m pytest <file> -q`
- [ ] T006 [P] Run frontend test baseline: `npx vitest run` in frontend/
- [ ] T007 Record baseline results (pass/fail counts, known failures) for comparison after bug fixes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Understand codebase conventions and error handling patterns that ALL bug fixes must follow. No bug fixes happen in this phase — only knowledge gathering.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Review centralized error handling patterns in backend/src/logging_utils.py — document `handle_service_error()`, `safe_error_response()`, `get_logger()` conventions
- [ ] T009 [P] Review exception hierarchy in backend/src/exceptions.py — document custom exception classes and usage patterns
- [ ] T010 [P] Review authentication dependency injection in backend/src/dependencies.py — document `get_current_user` pattern and auth flow
- [ ] T011 [P] Review configuration management in backend/src/config.py — document environment variable loading and secure defaults
- [ ] T012 [P] Review test helpers and conventions in backend/tests/helpers/factories.py, backend/tests/helpers/mocks.py, backend/tests/helpers/assertions.py, backend/tests/conftest.py
- [ ] T013 Review frontend API service layer in frontend/src/services/api.ts — document API call patterns, token handling, error handling

**Checkpoint**: Foundation ready — codebase conventions understood, all bug fixes will follow established patterns

---

## Phase 3: User Story 1 — Security Vulnerability Remediation (Priority: P1) 🎯 MVP

**Goal**: Audit every file for security vulnerabilities (auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation) and fix all obvious issues with regression tests.

**Independent Test**: Run the full backend + frontend test suite after all P1 fixes. Verify no secrets or tokens remain in source code. Verify all inputs are validated.

### Backend API Security Audit (US1)

- [ ] T014 [US1] Audit authentication endpoints for auth bypass vulnerabilities in backend/src/api/auth.py — fix and add regression tests in backend/tests/unit/test_api_auth.py
- [ ] T015 [P] [US1] Audit board API for input validation and auth issues in backend/src/api/board.py — fix and add regression tests in backend/tests/unit/test_api_board.py
- [ ] T016 [P] [US1] Audit chat API for input validation, injection risks, and error info leakage in backend/src/api/chat.py — fix and add regression tests in backend/tests/unit/test_api_chat.py
- [ ] T017 [P] [US1] Audit chores API for input validation and auth issues in backend/src/api/chores.py — fix and add regression tests in backend/tests/unit/test_chores_api.py
- [ ] T018 [P] [US1] Audit cleanup API for input validation and auth issues in backend/src/api/cleanup.py — fix and add regression tests in backend/tests/unit/test_cleanup_service.py
- [ ] T019 [P] [US1] Audit health API for information disclosure in backend/src/api/health.py
- [ ] T020 [P] [US1] Audit MCP API for input validation and auth issues in backend/src/api/mcp.py — fix and add regression tests in backend/tests/unit/test_api_mcp.py
- [ ] T021 [P] [US1] Audit projects API for input validation and auth issues in backend/src/api/projects.py — fix and add regression tests in backend/tests/unit/test_api_projects.py
- [ ] T022 [P] [US1] Audit settings API for input validation and auth issues in backend/src/api/settings.py — fix and add regression tests in backend/tests/unit/test_api_settings.py
- [ ] T023 [P] [US1] Audit signal API for input validation and auth issues in backend/src/api/signal.py
- [ ] T024 [P] [US1] Audit tasks API for input validation and auth issues in backend/src/api/tasks.py — fix and add regression tests in backend/tests/unit/test_api_tasks.py
- [ ] T025 [P] [US1] Audit webhooks API for verification bypass and injection risks in backend/src/api/webhooks.py — fix and add regression tests in backend/tests/unit/test_webhooks.py
- [ ] T026 [P] [US1] Audit workflow API for input validation and auth issues in backend/src/api/workflow.py — fix and add regression tests in backend/tests/unit/test_api_workflow.py

### Backend Service Security Audit (US1)

- [ ] T027 [US1] Audit OAuth flow and token handling for security vulnerabilities in backend/src/services/github_auth.py — fix and add regression tests in backend/tests/unit/test_github_auth.py
- [ ] T028 [P] [US1] Audit encryption service for cryptographic weaknesses in backend/src/services/encryption.py — fix and add regression tests in backend/tests/unit/test_token_encryption.py
- [ ] T029 [P] [US1] Audit database service for SQL injection and path traversal in backend/src/services/database.py — fix and add regression tests in backend/tests/unit/test_database.py
- [ ] T030 [P] [US1] Audit session store for session fixation and data exposure in backend/src/services/session_store.py — fix and add regression tests in backend/tests/unit/test_session_store.py
- [ ] T031 [P] [US1] Audit settings store for unauthorized access in backend/src/services/settings_store.py — fix and add regression tests in backend/tests/unit/test_settings_store.py
- [ ] T032 [P] [US1] Audit MCP store for security issues in backend/src/services/mcp_store.py — fix and add regression tests in backend/tests/unit/test_mcp_store.py

### Backend Infrastructure Security Audit (US1)

- [ ] T033 [US1] Audit config for exposed secrets and insecure defaults in backend/src/config.py — fix and add regression tests in backend/tests/unit/test_config.py
- [ ] T034 [P] [US1] Audit dependencies for auth bypass vectors in backend/src/dependencies.py
- [ ] T035 [P] [US1] Audit middleware for missing security headers in backend/src/middleware/request_id.py — fix and add regression tests in backend/tests/unit/test_middleware.py
- [ ] T036 [P] [US1] Audit main app for CORS configuration and insecure defaults in backend/src/main.py — fix and add regression tests in backend/tests/unit/test_main.py
- [ ] T037 [P] [US1] Audit utility functions for input validation gaps in backend/src/utils.py — fix and add regression tests in backend/tests/unit/test_utils.py

### Frontend Security Audit (US1)

- [ ] T038 [US1] Audit API service layer for token leakage and insecure API calls in frontend/src/services/api.ts
- [ ] T039 [P] [US1] Audit auth hook for insecure token storage in frontend/src/hooks/useAuth.ts — fix and add regression tests in frontend/src/hooks/useAuth.test.tsx
- [ ] T040 [P] [US1] Audit all frontend components for XSS risks (dangerouslySetInnerHTML, unsanitized rendering) in frontend/src/components/
- [ ] T041 [P] [US1] Audit frontend type definitions for security-relevant type gaps in frontend/src/types/index.ts

### US1 Validation

- [ ] T042 [US1] Run full backend test suite after all P1 security fixes — all tests must pass
- [ ] T043 [P] [US1] Run full frontend test suite after all P1 security fixes — all tests must pass
- [ ] T044 [US1] Run backend lint after all P1 fixes: `ruff check src tests && ruff format --check src tests` in backend/
- [ ] T045 [P] [US1] Run frontend lint after all P1 fixes: `npx eslint . && npx tsc --noEmit` in frontend/

**Checkpoint**: All security vulnerabilities identified, fixed with regression tests, or flagged as TODO(bug-bash). Test suite and lint pass.

---

## Phase 4: User Story 2 — Runtime Error Elimination (Priority: P2)

**Goal**: Audit every file for runtime errors (unhandled exceptions, race conditions, null/None references, missing imports, type errors, resource leaks) and fix all obvious issues with regression tests.

**Independent Test**: Run the full test suite after all P2 fixes. Verify no unhandled exceptions and all resources are properly managed.

### Backend API Runtime Audit (US2)

- [ ] T046 [US2] Audit exception handling and null safety in backend/src/api/auth.py — fix and add regression tests in backend/tests/unit/test_api_auth.py
- [ ] T047 [P] [US2] Audit exception handling and null safety in backend/src/api/board.py — fix and add regression tests in backend/tests/unit/test_api_board.py
- [ ] T048 [P] [US2] Audit exception handling and null safety in backend/src/api/chat.py — fix and add regression tests in backend/tests/unit/test_api_chat.py
- [ ] T049 [P] [US2] Audit exception handling and null safety in backend/src/api/chores.py — fix and add regression tests in backend/tests/unit/test_chores_api.py
- [ ] T050 [P] [US2] Audit exception handling and null safety in backend/src/api/cleanup.py — fix and add regression tests in backend/tests/unit/test_cleanup_service.py
- [ ] T051 [P] [US2] Audit exception handling and null safety in backend/src/api/mcp.py — fix and add regression tests in backend/tests/unit/test_api_mcp.py
- [ ] T052 [P] [US2] Audit exception handling and null safety in backend/src/api/projects.py — fix and add regression tests in backend/tests/unit/test_api_projects.py
- [ ] T053 [P] [US2] Audit exception handling and null safety in backend/src/api/settings.py — fix and add regression tests in backend/tests/unit/test_api_settings.py
- [ ] T054 [P] [US2] Audit exception handling and null safety in backend/src/api/tasks.py — fix and add regression tests in backend/tests/unit/test_api_tasks.py
- [ ] T055 [P] [US2] Audit exception handling and null safety in backend/src/api/workflow.py — fix and add regression tests in backend/tests/unit/test_api_workflow.py
- [ ] T056 [P] [US2] Audit exception handling and null safety in backend/src/api/webhooks.py — fix and add regression tests in backend/tests/unit/test_webhooks.py
- [ ] T057 [P] [US2] Audit exception handling and null safety in backend/src/api/signal.py

### Backend Service Runtime Audit (US2)

- [ ] T058 [US2] Audit resource management and async error handling in backend/src/services/copilot_polling/pipeline.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T059 [P] [US2] Audit resource management and async error handling in backend/src/services/copilot_polling/polling_loop.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T060 [P] [US2] Audit resource management and async error handling in backend/src/services/copilot_polling/recovery.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T061 [P] [US2] Audit resource management and async error handling in backend/src/services/copilot_polling/state.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T062 [P] [US2] Audit resource management and async error handling in backend/src/services/copilot_polling/completion.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T063 [P] [US2] Audit resource management and async error handling in backend/src/services/copilot_polling/helpers.py
- [ ] T064 [P] [US2] Audit resource management and async error handling in backend/src/services/copilot_polling/agent_output.py
- [ ] T065 [US2] Audit database connection management and resource leaks in backend/src/services/database.py — fix and add regression tests in backend/tests/unit/test_database.py
- [ ] T066 [P] [US2] Audit session store for resource leaks and null safety in backend/src/services/session_store.py — fix and add regression tests in backend/tests/unit/test_session_store.py
- [ ] T067 [P] [US2] Audit websocket service for connection handling and error recovery in backend/src/services/websocket.py — fix and add regression tests in backend/tests/unit/test_websocket.py
- [ ] T068 [P] [US2] Audit workflow orchestrator for unhandled exceptions in backend/src/services/workflow_orchestrator/orchestrator.py — fix and add regression tests in backend/tests/unit/test_workflow_orchestrator.py
- [ ] T069 [P] [US2] Audit workflow transitions for runtime errors in backend/src/services/workflow_orchestrator/transitions.py — fix and add regression tests in backend/tests/unit/test_workflow_orchestrator.py
- [ ] T070 [P] [US2] Audit cleanup service for resource leaks in backend/src/services/cleanup_service.py — fix and add regression tests in backend/tests/unit/test_cleanup_service.py
- [ ] T071 [P] [US2] Audit AI agent service for unhandled exceptions in backend/src/services/ai_agent.py — fix and add regression tests in backend/tests/unit/test_ai_agent.py
- [ ] T072 [P] [US2] Audit agent creator service for runtime errors in backend/src/services/agent_creator.py — fix and add regression tests in backend/tests/unit/test_agent_creator.py
- [ ] T073 [P] [US2] Audit agent tracking service for runtime errors in backend/src/services/agent_tracking.py — fix and add regression tests in backend/tests/unit/test_agent_tracking.py
- [ ] T074 [P] [US2] Audit cache service for runtime errors in backend/src/services/cache.py — fix and add regression tests in backend/tests/unit/test_cache.py
- [ ] T075 [P] [US2] Audit chores services for runtime errors in backend/src/services/chores/service.py, backend/src/services/chores/scheduler.py, backend/src/services/chores/chat.py, backend/src/services/chores/counter.py, backend/src/services/chores/template_builder.py
- [ ] T076 [P] [US2] Audit completion providers for runtime errors in backend/src/services/completion_providers.py — fix and add regression tests in backend/tests/unit/test_completion_providers.py
- [ ] T077 [P] [US2] Audit GitHub Projects service for runtime errors in backend/src/services/github_projects/service.py, backend/src/services/github_projects/graphql.py — fix and add regression tests in backend/tests/unit/test_github_projects.py
- [ ] T078 [P] [US2] Audit model fetcher for runtime errors in backend/src/services/model_fetcher.py — fix and add regression tests in backend/tests/unit/test_model_fetcher.py
- [ ] T079 [P] [US2] Audit signal services for runtime errors in backend/src/services/signal_bridge.py, backend/src/services/signal_chat.py, backend/src/services/signal_delivery.py
- [ ] T080 [P] [US2] Audit encryption service for runtime errors in backend/src/services/encryption.py — fix and add regression tests in backend/tests/unit/test_token_encryption.py

### Backend Infrastructure Runtime Audit (US2)

- [ ] T081 [US2] Audit logging utilities for runtime errors in backend/src/logging_utils.py — fix and add regression tests in backend/tests/unit/test_logging_utils.py
- [ ] T082 [P] [US2] Audit main app startup/shutdown for resource leaks in backend/src/main.py — fix and add regression tests in backend/tests/unit/test_main.py
- [ ] T083 [P] [US2] Audit utility functions for runtime errors in backend/src/utils.py — fix and add regression tests in backend/tests/unit/test_utils.py

### Frontend Runtime Audit (US2)

- [ ] T084 [US2] Audit React hooks for state management errors and stale closures in frontend/src/hooks/useChat.ts, frontend/src/hooks/useAuth.ts, frontend/src/hooks/useWorkflow.ts
- [ ] T085 [P] [US2] Audit React hooks for async operation errors in frontend/src/hooks/useProjects.ts, frontend/src/hooks/useProjectBoard.ts, frontend/src/hooks/useBoardRefresh.ts
- [ ] T086 [P] [US2] Audit React hooks for runtime errors in frontend/src/hooks/useChores.ts, frontend/src/hooks/useCleanup.ts, frontend/src/hooks/useSettings.ts, frontend/src/hooks/useSettingsForm.ts
- [ ] T087 [P] [US2] Audit React hooks for runtime errors in frontend/src/hooks/useMcpSettings.ts, frontend/src/hooks/useCommands.ts, frontend/src/hooks/useRealTimeSync.ts, frontend/src/hooks/useAgentConfig.ts
- [ ] T088 [P] [US2] Audit error boundary component for completeness in frontend/src/components/common/ErrorBoundary.tsx
- [ ] T089 [P] [US2] Audit frontend components for null rendering and undefined access errors in frontend/src/components/board/, frontend/src/components/chat/, frontend/src/components/chores/, frontend/src/components/settings/

### US2 Validation

- [ ] T090 [US2] Run full backend test suite after all P2 runtime fixes — all tests must pass
- [ ] T091 [P] [US2] Run full frontend test suite after all P2 runtime fixes — all tests must pass
- [ ] T092 [US2] Run backend lint after all P2 fixes: `ruff check src tests && ruff format --check src tests` in backend/
- [ ] T093 [P] [US2] Run frontend lint after all P2 fixes: `npx eslint . && npx tsc --noEmit` in frontend/

**Checkpoint**: All runtime errors identified, fixed with regression tests, or flagged as TODO(bug-bash). Test suite and lint pass.

---

## Phase 5: User Story 3 — Logic Bug Resolution (Priority: P3)

**Goal**: Audit every file for logic bugs (incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, incorrect return values) and fix all obvious issues with regression tests.

**Independent Test**: Run the full test suite after all P3 fixes. Verify that corrected functions produce expected outputs for all defined inputs.

### Backend Service Logic Audit (US3)

- [ ] T094 [US3] Audit workflow orchestrator state machine for illegal state transitions in backend/src/services/workflow_orchestrator/orchestrator.py — fix and add regression tests in backend/tests/unit/test_workflow_orchestrator.py
- [ ] T095 [P] [US3] Audit workflow transitions for incorrect state transition logic in backend/src/services/workflow_orchestrator/transitions.py — fix and add regression tests in backend/tests/unit/test_workflow_orchestrator.py
- [ ] T096 [P] [US3] Audit workflow models for data consistency issues in backend/src/services/workflow_orchestrator/models.py — fix and add regression tests in backend/tests/unit/test_workflow_orchestrator.py
- [ ] T097 [P] [US3] Audit workflow config for logic errors in backend/src/services/workflow_orchestrator/config.py — fix and add regression tests in backend/tests/unit/test_workflow_orchestrator.py
- [ ] T098 [US3] Audit copilot polling pipeline for control flow and data consistency bugs in backend/src/services/copilot_polling/pipeline.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T099 [P] [US3] Audit copilot polling state management for logic bugs in backend/src/services/copilot_polling/state.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T100 [P] [US3] Audit copilot polling completion for logic bugs in backend/src/services/copilot_polling/completion.py — fix and add regression tests in backend/tests/unit/test_copilot_polling.py
- [ ] T101 [P] [US3] Audit cleanup service for logic bugs and incorrect return values in backend/src/services/cleanup_service.py — fix and add regression tests in backend/tests/unit/test_cleanup_service.py
- [ ] T102 [P] [US3] Audit GitHub Projects service for logic bugs in backend/src/services/github_projects/service.py, backend/src/services/github_projects/graphql.py — fix and add regression tests in backend/tests/unit/test_github_projects.py
- [ ] T103 [P] [US3] Audit chores service for scheduling logic bugs in backend/src/services/chores/service.py, backend/src/services/chores/scheduler.py — fix and add regression tests in backend/tests/unit/test_chores_service.py, backend/tests/unit/test_chores_scheduler.py
- [ ] T104 [P] [US3] Audit AI agent and completion providers for logic bugs in backend/src/services/ai_agent.py, backend/src/services/completion_providers.py — fix and add regression tests in backend/tests/unit/test_ai_agent.py, backend/tests/unit/test_completion_providers.py
- [ ] T105 [P] [US3] Audit database service for data consistency and boundary condition bugs in backend/src/services/database.py — fix and add regression tests in backend/tests/unit/test_database.py
- [ ] T106 [P] [US3] Audit session store for logic bugs in backend/src/services/session_store.py — fix and add regression tests in backend/tests/unit/test_session_store.py

### Backend API Logic Audit (US3)

- [ ] T107 [US3] Audit board API for pagination, ordering, and boundary condition bugs in backend/src/api/board.py — fix and add regression tests in backend/tests/unit/test_api_board.py
- [ ] T108 [P] [US3] Audit chat API for control flow and return value bugs in backend/src/api/chat.py — fix and add regression tests in backend/tests/unit/test_api_chat.py
- [ ] T109 [P] [US3] Audit workflow API for logic bugs in backend/src/api/workflow.py — fix and add regression tests in backend/tests/unit/test_api_workflow.py
- [ ] T110 [P] [US3] Audit tasks API for logic bugs in backend/src/api/tasks.py — fix and add regression tests in backend/tests/unit/test_api_tasks.py
- [ ] T111 [P] [US3] Audit projects API for logic bugs in backend/src/api/projects.py — fix and add regression tests in backend/tests/unit/test_api_projects.py

### Backend Infrastructure Logic Audit (US3)

- [ ] T112 [US3] Audit utility functions for off-by-one and boundary condition bugs in backend/src/utils.py — fix and add regression tests in backend/tests/unit/test_utils.py
- [ ] T113 [P] [US3] Audit Pydantic models for data consistency and validation logic bugs across backend/src/models/ — fix and add regression tests in backend/tests/unit/test_models.py

### Frontend Logic Audit (US3)

- [ ] T114 [US3] Audit frontend hooks for data fetching logic, mutation logic, and state management bugs in frontend/src/hooks/useChat.ts, frontend/src/hooks/useProjectBoard.ts, frontend/src/hooks/useWorkflow.ts
- [ ] T115 [P] [US3] Audit frontend hooks for logic bugs in frontend/src/hooks/useProjects.ts, frontend/src/hooks/useBoardRefresh.ts, frontend/src/hooks/useCommands.ts, frontend/src/hooks/useRealTimeSync.ts
- [ ] T116 [P] [US3] Audit board components for UI logic bugs (ordering, drag-drop, rendering) in frontend/src/components/board/
- [ ] T117 [P] [US3] Audit chat components for message handling and command logic bugs in frontend/src/components/chat/
- [ ] T118 [P] [US3] Audit settings components for form logic bugs in frontend/src/components/settings/
- [ ] T119 [P] [US3] Audit utility functions for logic bugs in frontend/src/utils/formatTime.ts, frontend/src/utils/generateId.ts

### US3 Validation

- [ ] T120 [US3] Run full backend test suite after all P3 logic fixes — all tests must pass
- [ ] T121 [P] [US3] Run full frontend test suite after all P3 logic fixes — all tests must pass
- [ ] T122 [US3] Run backend lint after all P3 fixes: `ruff check src tests && ruff format --check src tests` in backend/
- [ ] T123 [P] [US3] Run frontend lint after all P3 fixes: `npx eslint . && npx tsc --noEmit` in frontend/

**Checkpoint**: All logic bugs identified, fixed with regression tests, or flagged as TODO(bug-bash). Test suite and lint pass.

---

## Phase 6: User Story 4 — Test Gap Coverage (Priority: P4)

**Goal**: Audit all test files for test quality issues (untested code paths, tests that pass for wrong reasons, mock leaks, assertions that never fail, missing edge case coverage) and fix all obvious issues.

**Independent Test**: Review test coverage; verify that corrected tests fail when the feature they validate is intentionally broken.

### Backend Test Quality Audit (US4)

- [ ] T124 [US4] Audit test helpers for mock quality issues (MagicMock leaking into production paths) in backend/tests/helpers/mocks.py — fix mock objects to return realistic values
- [ ] T125 [P] [US4] Audit test helpers for factory correctness in backend/tests/helpers/factories.py — fix factories to produce realistic test data
- [ ] T126 [P] [US4] Audit test helpers for assertion quality in backend/tests/helpers/assertions.py — ensure assertions are specific and descriptive
- [ ] T127 [P] [US4] Audit shared fixtures for correctness in backend/tests/conftest.py — fix any fixtures that enable wrong-reason passing

- [ ] T128 [US4] Audit backend/tests/unit/test_api_auth.py for mock leaks, weak assertions, and untested paths — fix and verify tests fail when feature is broken
- [ ] T129 [P] [US4] Audit backend/tests/unit/test_api_board.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T130 [P] [US4] Audit backend/tests/unit/test_api_chat.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T131 [P] [US4] Audit backend/tests/unit/test_api_mcp.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T132 [P] [US4] Audit backend/tests/unit/test_api_projects.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T133 [P] [US4] Audit backend/tests/unit/test_api_settings.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T134 [P] [US4] Audit backend/tests/unit/test_api_tasks.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T135 [P] [US4] Audit backend/tests/unit/test_api_workflow.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T136 [P] [US4] Audit backend/tests/unit/test_copilot_polling.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T137 [P] [US4] Audit backend/tests/unit/test_workflow_orchestrator.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T138 [P] [US4] Audit backend/tests/unit/test_database.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T139 [P] [US4] Audit backend/tests/unit/test_cleanup_service.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T140 [P] [US4] Audit backend/tests/unit/test_github_auth.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T141 [P] [US4] Audit backend/tests/unit/test_github_projects.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T142 [P] [US4] Audit backend/tests/unit/test_session_store.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T143 [P] [US4] Audit backend/tests/unit/test_settings_store.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T144 [P] [US4] Audit backend/tests/unit/test_logging_utils.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T145 [P] [US4] Audit backend/tests/unit/test_config.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T146 [P] [US4] Audit backend/tests/unit/test_utils.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T147 [P] [US4] Audit backend/tests/unit/test_models.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T148 [P] [US4] Audit backend/tests/unit/test_token_encryption.py for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T149 [P] [US4] Audit backend/tests/unit/test_ai_agent.py, backend/tests/unit/test_agent_creator.py, backend/tests/unit/test_agent_tracking.py for test quality — fix and verify
- [ ] T150 [P] [US4] Audit backend/tests/unit/test_cache.py, backend/tests/unit/test_completion_providers.py, backend/tests/unit/test_model_fetcher.py for test quality — fix and verify
- [ ] T151 [P] [US4] Audit backend/tests/unit/test_chores_api.py, backend/tests/unit/test_chores_service.py, backend/tests/unit/test_chores_scheduler.py, backend/tests/unit/test_chores_counter.py for test quality — fix and verify
- [ ] T152 [P] [US4] Audit backend/tests/unit/test_websocket.py, backend/tests/unit/test_middleware.py, backend/tests/unit/test_main.py for test quality — fix and verify
- [ ] T153 [P] [US4] Audit backend/tests/unit/test_webhooks.py, backend/tests/unit/test_mcp_store.py for test quality — fix and verify
- [ ] T154 [P] [US4] Audit backend/tests/unit/test_error_responses.py, backend/tests/unit/test_exceptions.py, backend/tests/unit/test_auth_security.py, backend/tests/unit/test_oauth_state.py for test quality — fix and verify
- [ ] T155 [P] [US4] Audit backend/tests/unit/test_admin_authorization.py, backend/tests/unit/test_board.py, backend/tests/unit/test_prompts.py, backend/tests/unit/test_recommendation_models.py, backend/tests/unit/test_module_boundaries.py for test quality — fix and verify
- [ ] T156 [P] [US4] Audit backend/tests/unit/test_completion_false_positive.py, backend/tests/unit/test_issue_creation_retry.py for test quality — fix and verify
- [ ] T157 [US4] Audit backend/tests/integration/test_custom_agent_assignment.py, backend/tests/integration/test_health_endpoint.py, backend/tests/integration/test_webhook_verification.py for test quality — fix and verify

### Frontend Test Quality Audit (US4)

- [ ] T158 [US4] Audit frontend/src/hooks/useAuth.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T159 [P] [US4] Audit frontend/src/hooks/useChat.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T160 [P] [US4] Audit frontend/src/hooks/useProjectBoard.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T161 [P] [US4] Audit frontend/src/hooks/useProjects.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T162 [P] [US4] Audit frontend/src/hooks/useBoardRefresh.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T163 [P] [US4] Audit frontend/src/hooks/useWorkflow.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T164 [P] [US4] Audit frontend/src/hooks/useCommands.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T165 [P] [US4] Audit frontend/src/hooks/useRealTimeSync.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T166 [P] [US4] Audit frontend/src/hooks/useSettingsForm.test.tsx for mock leaks, weak assertions, and untested paths — fix and verify
- [ ] T167 [P] [US4] Audit frontend/src/components/board/BoardColumn.test.tsx, frontend/src/components/board/IssueCard.test.tsx, frontend/src/components/board/IssueDetailModal.test.tsx, frontend/src/components/board/AgentSaveBar.test.tsx for test quality — fix and verify
- [ ] T168 [P] [US4] Audit frontend/src/components/chat/CommandAutocomplete.test.tsx, frontend/src/components/chat/MessageBubble.test.tsx, frontend/src/components/chat/StatusChangePreview.test.tsx, frontend/src/components/chat/TaskPreview.test.tsx, frontend/src/components/chat/IssueRecommendationPreview.test.tsx for test quality — fix and verify
- [ ] T169 [P] [US4] Audit frontend/src/components/chores/__tests__/AddChoreModal.test.tsx, frontend/src/components/chores/__tests__/ChoreScheduleConfig.test.tsx, frontend/src/components/chores/__tests__/ChoresPanel.test.tsx for test quality — fix and verify
- [ ] T170 [P] [US4] Audit frontend/src/components/settings/DynamicDropdown.test.tsx, frontend/src/components/settings/SettingsSection.test.tsx for test quality — fix and verify
- [ ] T171 [P] [US4] Audit frontend/src/components/common/ErrorBoundary.test.tsx, frontend/src/components/ThemeProvider.test.tsx for test quality — fix and verify
- [ ] T172 [P] [US4] Audit frontend/src/components/auth/LoginButton.test.tsx for test quality — fix and verify
- [ ] T173 [P] [US4] Audit frontend/src/components/ui/button.test.tsx, frontend/src/components/ui/card.test.tsx, frontend/src/components/ui/input.test.tsx for test quality — fix and verify

### US4 Validation

- [ ] T174 [US4] Run full backend test suite after all P4 test quality fixes — all tests must pass
- [ ] T175 [P] [US4] Run full frontend test suite after all P4 test quality fixes — all tests must pass
- [ ] T176 [US4] Run backend lint after all P4 fixes: `ruff check src tests && ruff format --check src tests` in backend/
- [ ] T177 [P] [US4] Run frontend lint after all P4 fixes: `npx eslint . && npx tsc --noEmit` in frontend/

**Checkpoint**: All test quality issues identified and fixed. Corrected tests fail when feature they validate is broken. Test suite and lint pass.

---

## Phase 7: User Story 5 — Code Quality Improvement (Priority: P5)

**Goal**: Audit every file for code quality issues (dead code, unreachable branches, duplicated logic, hardcoded values, silent failures) and fix all obvious issues.

**Independent Test**: Run linting checks and verify that existing tests continue to pass after changes.

### Backend Code Quality Audit (US5)

- [ ] T178 [US5] Audit backend/src/api/ (all 13 route modules) for dead code, duplicated error handling, hardcoded values, and silent failures — fix and verify tests pass
- [ ] T179 [P] [US5] Audit backend/src/services/copilot_polling/ (all 7 modules) for dead code, unreachable branches, duplicated logic — fix and verify tests pass
- [ ] T180 [P] [US5] Audit backend/src/services/workflow_orchestrator/ (all 5 modules) for dead code, unreachable branches, duplicated logic — fix and verify tests pass
- [ ] T181 [P] [US5] Audit backend/src/services/chores/ (all 5 modules) for dead code, duplicated logic, hardcoded values — fix and verify tests pass
- [ ] T182 [P] [US5] Audit backend/src/services/github_projects/ (all 3 modules) for dead code, duplicated logic — fix and verify tests pass
- [ ] T183 [P] [US5] Audit backend/src/services/database.py, backend/src/services/session_store.py, backend/src/services/settings_store.py, backend/src/services/mcp_store.py for dead code and silent failures — fix and verify tests pass
- [ ] T184 [P] [US5] Audit backend/src/services/encryption.py, backend/src/services/github_auth.py, backend/src/services/cache.py for dead code and hardcoded values — fix and verify tests pass
- [ ] T185 [P] [US5] Audit backend/src/services/ai_agent.py, backend/src/services/agent_creator.py, backend/src/services/agent_tracking.py, backend/src/services/completion_providers.py, backend/src/services/model_fetcher.py for dead code — fix and verify tests pass
- [ ] T186 [P] [US5] Audit backend/src/services/websocket.py, backend/src/services/signal_bridge.py, backend/src/services/signal_chat.py, backend/src/services/signal_delivery.py, backend/src/services/cleanup_service.py for dead code and silent failures — fix and verify tests pass
- [ ] T187 [P] [US5] Audit backend/src/config.py, backend/src/constants.py, backend/src/dependencies.py, backend/src/exceptions.py, backend/src/logging_utils.py, backend/src/main.py, backend/src/utils.py for dead code and hardcoded values — fix and verify tests pass
- [ ] T188 [P] [US5] Audit backend/src/models/ (all 14 model modules) for unused fields, dead validation logic, duplicated definitions — fix and verify tests pass

### Frontend Code Quality Audit (US5)

- [ ] T189 [US5] Audit frontend/src/services/api.ts for dead code, duplicated fetch logic, hardcoded URLs — fix and verify tests pass
- [ ] T190 [P] [US5] Audit frontend/src/hooks/ (all 16 hook files) for dead code, duplicated logic, hardcoded values — fix and verify tests pass
- [ ] T191 [P] [US5] Audit frontend/src/components/board/ (all 14 component files) for dead code, duplicated rendering logic, hardcoded values — fix and verify tests pass
- [ ] T192 [P] [US5] Audit frontend/src/components/chat/ (all 8 component files) for dead code, duplicated logic — fix and verify tests pass
- [ ] T193 [P] [US5] Audit frontend/src/components/chores/ (all 5 component files) for dead code, duplicated logic — fix and verify tests pass
- [ ] T194 [P] [US5] Audit frontend/src/components/settings/ (all 11 component files) for dead code, duplicated logic, hardcoded values — fix and verify tests pass
- [ ] T195 [P] [US5] Audit frontend/src/components/common/, frontend/src/components/auth/, frontend/src/components/ui/ for dead code — fix and verify tests pass
- [ ] T196 [P] [US5] Audit frontend/src/types/index.ts for unused type definitions — fix and verify tests pass
- [ ] T197 [P] [US5] Audit frontend/src/utils/formatTime.ts, frontend/src/utils/generateId.ts for dead code and hardcoded values — fix and verify tests pass
- [ ] T198 [P] [US5] Audit frontend/src/pages/ProjectBoardPage.tsx, frontend/src/pages/SettingsPage.tsx for dead code — fix and verify tests pass

### US5 Validation

- [ ] T199 [US5] Run full backend test suite after all P5 code quality fixes — all tests must pass
- [ ] T200 [P] [US5] Run full frontend test suite after all P5 code quality fixes — all tests must pass
- [ ] T201 [US5] Run backend lint after all P5 fixes: `ruff check src tests && ruff format --check src tests` in backend/
- [ ] T202 [P] [US5] Run frontend lint after all P5 fixes: `npx eslint . && npx tsc --noEmit` in frontend/

**Checkpoint**: All code quality issues identified and fixed. Dead code removed without changing behavior. Test suite and lint pass.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary table generation, and documentation

- [ ] T203 Run full backend test suite (all 45+ test files individually) — confirm zero failures
- [ ] T204 [P] Run full frontend test suite (`npx vitest run`) — confirm zero failures
- [ ] T205 Run backend lint and format check: `ruff check src tests && ruff format --check src tests` in backend/
- [ ] T206 [P] Run frontend lint and type check: `npx eslint . && npx tsc --noEmit` in frontend/
- [ ] T207 Generate the summary table listing every bug found with: sequential number, file path, line numbers, category, description, and status (✅ Fixed or ⚠️ Flagged TODO)
- [ ] T208 Verify summary table completeness: no files with bugs omitted, no files without bugs included (FR-015, SC-007)
- [ ] T209 Verify each fix is independently verifiable: reverting a single fix causes its regression test to fail (SC-008)
- [ ] T210 Run quickstart.md validation steps from specs/001-bug-basher/quickstart.md to confirm end-to-end process

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–7)**: All depend on Foundational phase completion
  - User stories MUST proceed sequentially in priority order (P1 → P2 → P3 → P4 → P5) because:
    - Security fixes (P1) may change error handling patterns used by later phases
    - Runtime fixes (P2) may change control flow that logic audit (P3) depends on
    - Logic fixes (P3) may change behavior that test quality audit (P4) validates
    - Test fixes (P4) should be applied before code quality (P5) to ensure safety net
- **Polish (Phase 8)**: Depends on ALL user stories being complete

### User Story Dependencies

- **US1 — Security (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. **Start here.**
- **US2 — Runtime (P2)**: Should start after US1 completion — security fixes may change error handling code
- **US3 — Logic (P3)**: Should start after US2 completion — runtime fixes may change control flow
- **US4 — Test Quality (P4)**: Should start after US3 completion — logic fixes may affect test expectations
- **US5 — Code Quality (P5)**: Should start after US4 completion — test fixes ensure safety net for dead code removal

### Within Each User Story

- Backend API audit tasks marked [P] can run in parallel (different files)
- Backend service audit tasks marked [P] can run in parallel (different files)
- Frontend audit tasks marked [P] can run in parallel (different files)
- Validation tasks run AFTER all audit/fix tasks in that story are complete
- Each fix: audit → fix → add regression test → verify existing tests still pass

### Parallel Opportunities

- Within Phase 1: T001–T007 setup tasks marked [P] can run in parallel
- Within Phase 2: T008–T013 foundational review tasks marked [P] can run in parallel
- Within each US phase: All tasks marked [P] targeting different files can run in parallel
- Backend and frontend audit tasks within the same phase can run in parallel
- Validation tasks (test + lint) can run backend and frontend in parallel

---

## Parallel Example: User Story 1 (Security)

```bash
# Launch all backend API security audits together (different files):
Task: T015 "Audit board API security in backend/src/api/board.py"
Task: T016 "Audit chat API security in backend/src/api/chat.py"
Task: T017 "Audit chores API security in backend/src/api/chores.py"
Task: T018 "Audit cleanup API security in backend/src/api/cleanup.py"
Task: T020 "Audit MCP API security in backend/src/api/mcp.py"
Task: T021 "Audit projects API security in backend/src/api/projects.py"

# Launch backend service security audits together (different files):
Task: T028 "Audit encryption service in backend/src/services/encryption.py"
Task: T029 "Audit database service in backend/src/services/database.py"
Task: T030 "Audit session store in backend/src/services/session_store.py"
Task: T031 "Audit settings store in backend/src/services/settings_store.py"

# Launch backend + frontend validation in parallel:
Task: T042 "Run full backend test suite"
Task: T043 "Run full frontend test suite"
```

---

## Parallel Example: User Story 4 (Test Quality)

```bash
# Launch backend test file audits together (different test files):
Task: T128 "Audit test_api_auth.py"
Task: T129 "Audit test_api_board.py"
Task: T130 "Audit test_api_chat.py"
Task: T136 "Audit test_copilot_polling.py"
Task: T137 "Audit test_workflow_orchestrator.py"

# Launch frontend test file audits together:
Task: T158 "Audit useAuth.test.tsx"
Task: T159 "Audit useChat.test.tsx"
Task: T160 "Audit useProjectBoard.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 — Security Only)

1. Complete Phase 1: Setup — establish baseline
2. Complete Phase 2: Foundational — understand conventions
3. Complete Phase 3: User Story 1 (Security) — highest priority
4. **STOP and VALIDATE**: Run full test suite and lint, verify all security fixes
5. Generate interim summary table for security findings only
6. Deploy/review if ready — security is the most critical category

### Incremental Delivery

1. Complete Setup + Foundational → Baseline established
2. Add US1 (Security) → Validate → Interim summary (MVP!)
3. Add US2 (Runtime) → Validate → Updated summary
4. Add US3 (Logic) → Validate → Updated summary
5. Add US4 (Test Quality) → Validate → Updated summary
6. Add US5 (Code Quality) → Validate → Final summary
7. Complete Polish phase → Final validation and complete summary table
8. Each category sweep adds value without breaking previous fixes

### Sequential Category Strategy

This bug bash MUST proceed sequentially through categories because:

1. Security fixes (P1) establish the error handling baseline
2. Runtime fixes (P2) depend on the security-hardened error patterns
3. Logic fixes (P3) depend on the runtime-safe control flow
4. Test quality fixes (P4) validate the behavior established by P1–P3
5. Code quality fixes (P5) can safely remove dead code knowing tests are reliable

---

## Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 210 |
| **Phase 1 — Setup** | 7 tasks |
| **Phase 2 — Foundational** | 6 tasks |
| **Phase 3 — US1 Security (P1)** | 32 tasks |
| **Phase 4 — US2 Runtime (P2)** | 48 tasks |
| **Phase 5 — US3 Logic (P3)** | 30 tasks |
| **Phase 6 — US4 Test Quality (P4)** | 54 tasks |
| **Phase 7 — US5 Code Quality (P5)** | 25 tasks |
| **Phase 8 — Polish** | 8 tasks |
| **Parallelizable tasks** | ~160 (within their respective phases) |
| **Suggested MVP scope** | Phase 1 + Phase 2 + Phase 3 (US1 Security — 45 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story (US1–US5) for traceability
- Each user story corresponds to one bug category: US1=Security, US2=Runtime, US3=Logic, US4=Test Quality, US5=Code Quality
- Each bug fix MUST include at least one regression test (FR-004)
- Ambiguous issues get `TODO(bug-bash)` comments, not code changes (FR-006)
- Commit after each task or logical group with descriptive messages (FR-005)
- Stop at any checkpoint to validate the category independently
- Avoid: vague fixes, same file conflicts across parallel tasks, API surface changes (FR-010)
