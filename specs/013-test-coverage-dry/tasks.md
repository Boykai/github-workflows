# Tasks: Increase Meaningful Test Coverage, Fix Discovered Bugs, and Enforce DRY Best Practices

**Input**: Design documents from `/specs/013-test-coverage-dry/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests ARE explicitly requested in this feature specification. TDD (red-green-refactor) is required for bug fixes. All tasks include test creation, audit, and refactoring.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend tests: `backend/tests/unit/test_<module>.py` mirroring `backend/src/<module>.py`
- Frontend tests: co-located `*.test.tsx` next to source files
- Shared backend helpers: `backend/tests/helpers/<utility>.py`
- Shared frontend factories: `frontend/src/test/factories/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the shared test helper modules, factory infrastructure, and directory structure needed by all subsequent phases.

- [ ] T001 Create backend test helpers directory and __init__.py at backend/tests/helpers/__init__.py
- [ ] T002 [P] Create backend test data factory module with make_user_session, make_project, make_task, make_board_column, make_chat_message, make_settings factory functions at backend/tests/helpers/factories.py
- [ ] T003 [P] Create backend custom assertion helpers module with assert_api_error, assert_json_structure, assert_api_success helper functions at backend/tests/helpers/assertions.py
- [ ] T004 [P] Create backend reusable mock builder module with pre-configured mock builders for database, GitHub API, AI agent, WebSocket, and Signal services at backend/tests/helpers/mocks.py
- [ ] T005 [P] Create frontend test data factories directory and index module with createMockProject, createMockTask, createMockUser, createMockColumn, createMockChatMessage, createMockSettings factory functions at frontend/src/test/factories/index.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the baseline by running all existing tests, identifying broken/skipped tests, and re-enabling backend tests in CI. MUST complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Run full backend test suite locally (cd backend && pytest -v) to establish baseline — document pass/fail counts and identify any currently broken tests
- [ ] T007 Run full frontend unit test suite locally (cd frontend && npm test) to establish baseline — document pass/fail counts
- [ ] T008 [P] Run backend coverage baseline report (cd backend && pytest --cov=src --cov-report=term-missing) and record per-module coverage percentages
- [ ] T009 [P] Run frontend coverage baseline report (cd frontend && npm run test:coverage) and record per-module coverage percentages
- [ ] T010 Fix any currently broken or failing backend tests discovered in T006 so the full suite passes before audit begins
- [ ] T011 Fix any currently broken or failing frontend tests discovered in T007 so the full suite passes before audit begins
- [ ] T012 Re-enable backend pytest step in CI pipeline by uncommenting lines 44-45 in .github/workflows/ci.yml — change commented `#- name: Run tests` and `#  run: pytest --cov=src --cov-report=term-missing` to active steps

**Checkpoint**: Foundation ready — all existing tests pass locally and in CI, backend tests re-enabled, baselines recorded. User story implementation can now begin.

---

## Phase 3: User Story 1 — Audit and Align Existing Test Suite (Priority: P1) 🎯 MVP

**Goal**: Classify every existing test as meaningful, redundant, or misaligned. Remove or rewrite misaligned/redundant tests so that passing tests give genuine confidence the application works correctly.

**Independent Test**: Run the full test suite after the audit and confirm every remaining test maps to a documented feature or behavior. Review the audit report and verify each classification is accurate.

### Audit: Backend Unit Tests (33 files)

- [ ] T013 [US1] Audit backend/tests/unit/test_api_auth.py — classify each test as meaningful, redundant, or misaligned against documented auth flows in backend/src/api/auth.py; rewrite or remove misaligned tests
- [ ] T014 [P] [US1] Audit backend/tests/unit/test_api_board.py — classify each test against documented board behavior in backend/src/api/board.py; rewrite or remove misaligned tests
- [ ] T015 [P] [US1] Audit backend/tests/unit/test_api_chat.py — classify each test against documented chat behavior in backend/src/api/chat.py; rewrite or remove misaligned tests
- [ ] T016 [P] [US1] Audit backend/tests/unit/test_api_projects.py — classify each test against documented project behavior in backend/src/api/projects.py; rewrite or remove misaligned tests
- [ ] T017 [P] [US1] Audit backend/tests/unit/test_api_settings.py — classify each test against documented settings behavior in backend/src/api/settings.py; rewrite or remove misaligned tests
- [ ] T018 [P] [US1] Audit backend/tests/unit/test_api_tasks.py — classify each test against documented tasks behavior in backend/src/api/tasks.py; rewrite or remove misaligned tests
- [ ] T019 [P] [US1] Audit backend/tests/unit/test_api_workflow.py — classify each test against documented workflow behavior in backend/src/api/workflow.py; rewrite or remove misaligned tests
- [ ] T020 [P] [US1] Audit backend/tests/unit/test_ai_agent.py — classify each test against documented AI agent behavior in backend/src/services/ai_agent.py; rewrite or remove misaligned tests
- [ ] T021 [P] [US1] Audit backend/tests/unit/test_board.py — classify each test against documented board service behavior; rewrite or remove misaligned tests
- [ ] T022 [P] [US1] Audit backend/tests/unit/test_cache.py — classify each test against documented cache behavior in backend/src/services/cache.py; rewrite or remove misaligned tests
- [ ] T023 [P] [US1] Audit backend/tests/unit/test_completion_providers.py — classify each test against documented completion provider behavior in backend/src/services/completion_providers.py; rewrite or remove misaligned tests
- [ ] T024 [P] [US1] Audit backend/tests/unit/test_config.py — classify each test against documented config behavior in backend/src/config.py; rewrite or remove misaligned tests
- [ ] T025 [US1] Audit backend/tests/unit/test_copilot_polling.py (157KB) — classify each test against documented copilot polling behavior in backend/src/services/copilot_polling/; rewrite or remove misaligned tests; flag duplicated setup for DRY extraction in US4
- [ ] T026 [P] [US1] Audit backend/tests/unit/test_database.py — classify each test against documented database behavior in backend/src/services/database.py; rewrite or remove misaligned tests
- [ ] T027 [P] [US1] Audit backend/tests/unit/test_github_auth.py — classify each test against documented GitHub auth behavior in backend/src/services/github_auth.py; rewrite or remove misaligned tests
- [ ] T028 [US1] Audit backend/tests/unit/test_github_projects.py (124KB) — classify each test against documented GitHub projects behavior in backend/src/services/github_projects/; rewrite or remove misaligned tests; flag duplicated setup for DRY extraction in US4
- [ ] T029 [P] [US1] Audit backend/tests/unit/test_main.py — classify each test against documented app factory behavior in backend/src/main.py; rewrite or remove misaligned tests
- [ ] T030 [P] [US1] Audit backend/tests/unit/test_models.py — classify each test against documented model behavior in backend/src/models/; rewrite or remove misaligned tests
- [ ] T031 [P] [US1] Audit backend/tests/unit/test_session_store.py — classify each test against documented session store behavior in backend/src/services/session_store.py; rewrite or remove misaligned tests
- [ ] T032 [P] [US1] Audit backend/tests/unit/test_settings_store.py — classify each test against documented settings store behavior in backend/src/services/settings_store.py; rewrite or remove misaligned tests
- [ ] T033 [P] [US1] Audit backend/tests/unit/test_token_encryption.py — classify each test against documented encryption behavior in backend/src/services/encryption.py; rewrite or remove misaligned tests
- [ ] T034 [P] [US1] Audit backend/tests/unit/test_webhooks.py — classify each test against documented webhook behavior in backend/src/api/webhooks.py; rewrite or remove misaligned tests
- [ ] T035 [P] [US1] Audit backend/tests/unit/test_websocket.py — classify each test against documented websocket behavior in backend/src/services/websocket.py; rewrite or remove misaligned tests
- [ ] T036 [US1] Audit backend/tests/unit/test_workflow_orchestrator.py (107KB) — classify each test against documented orchestrator behavior in backend/src/services/workflow_orchestrator/; rewrite or remove misaligned tests; flag duplicated setup for DRY extraction in US4
- [ ] T037 [P] [US1] Audit backend/tests/unit/test_admin_authorization.py — classify each test against documented admin auth behavior; rewrite or remove misaligned tests
- [ ] T038 [P] [US1] Audit backend/tests/unit/test_agent_tracking.py — classify each test against documented agent tracking behavior in backend/src/services/agent_tracking.py; rewrite or remove misaligned tests
- [ ] T039 [P] [US1] Audit backend/tests/unit/test_auth_security.py — classify each test against documented auth security behavior; rewrite or remove misaligned tests
- [ ] T040 [P] [US1] Audit backend/tests/unit/test_completion_false_positive.py — classify each test against documented completion false positive behavior; rewrite or remove misaligned tests
- [ ] T041 [P] [US1] Audit backend/tests/unit/test_error_responses.py — classify each test against documented error response behavior in backend/src/exceptions.py; rewrite or remove misaligned tests
- [ ] T042 [P] [US1] Audit backend/tests/unit/test_issue_creation_retry.py — classify each test against documented issue creation retry behavior; rewrite or remove misaligned tests
- [ ] T043 [P] [US1] Audit backend/tests/unit/test_module_boundaries.py — classify each test for testing real behavior vs implementation details; rewrite or remove misaligned tests
- [ ] T044 [P] [US1] Audit backend/tests/unit/test_oauth_state.py — classify each test against documented OAuth state behavior; rewrite or remove misaligned tests
- [ ] T045 [P] [US1] Audit backend/tests/unit/test_prompts.py — classify each test against documented prompt generation behavior in backend/src/prompts/; rewrite or remove misaligned tests

### Audit: Backend Integration and E2E Tests (4 files)

- [ ] T046 [P] [US1] Audit backend/tests/integration/test_custom_agent_assignment.py — classify each test against documented agent assignment behavior; rewrite or remove misaligned tests
- [ ] T047 [P] [US1] Audit backend/tests/integration/test_health_endpoint.py — classify each test against documented health endpoint behavior in backend/src/api/health.py; rewrite or remove misaligned tests
- [ ] T048 [P] [US1] Audit backend/tests/integration/test_webhook_verification.py — classify each test against documented webhook verification behavior; rewrite or remove misaligned tests
- [ ] T049 [P] [US1] Audit backend/tests/test_api_e2e.py — classify each test against documented end-to-end API behavior; rewrite or remove misaligned tests

### Audit: Frontend Unit Tests (3 files)

- [ ] T050 [P] [US1] Audit frontend/src/hooks/useAuth.test.tsx — classify each test against documented auth hook behavior in frontend/src/hooks/useAuth.ts; rewrite or remove misaligned tests
- [ ] T051 [P] [US1] Audit frontend/src/hooks/useProjects.test.tsx — classify each test against documented projects hook behavior in frontend/src/hooks/useProjects.ts; rewrite or remove misaligned tests
- [ ] T052 [P] [US1] Audit frontend/src/hooks/useRealTimeSync.test.tsx — classify each test against documented real-time sync hook behavior in frontend/src/hooks/useRealTimeSync.ts; rewrite or remove misaligned tests

### Audit: Frontend E2E Tests (3 files)

- [ ] T053 [P] [US1] Audit frontend/e2e/auth.spec.ts — classify each test against documented auth E2E flows; rewrite or remove misaligned tests
- [ ] T054 [P] [US1] Audit frontend/e2e/integration.spec.ts — classify each test against documented integration E2E flows; rewrite or remove misaligned tests
- [ ] T055 [P] [US1] Audit frontend/e2e/ui.spec.ts — classify each test against documented UI E2E flows; rewrite or remove misaligned tests

### Audit: Shared Test Infrastructure

- [ ] T056 [US1] Audit backend/tests/conftest.py — review all shared fixtures for correctness and completeness; document fixtures available for reuse; identify any fixtures that create incorrect test state
- [ ] T057 [P] [US1] Audit frontend/src/test/setup.ts — review createMockApi and global mocks for correctness; document mock factories available for reuse
- [ ] T058 [P] [US1] Audit frontend/src/test/test-utils.tsx — review renderWithProviders and createTestQueryClient for correctness

### Audit Report

- [ ] T059 [US1] Compile complete test audit report documenting classification (meaningful/redundant/misaligned), action taken (keep/rewrite/remove), and rationale for every test in the suite — store as a comment in the PR or a summary section in each modified test file

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Every remaining test in the suite validates documented real application behavior. No misaligned or redundant tests remain.

---

## Phase 4: User Story 2 — Add Missing Coverage for Critical Application Flows (Priority: P1)

**Goal**: Add tests for all critical application flows described in project documentation that currently lack coverage, ensuring each test validates real, user-facing or system-level behavior.

**Independent Test**: Run a coverage report and confirm that each documented critical flow has at least one test exercising its happy path and primary error cases.

### Backend: Missing Signal Integration Tests

- [ ] T060 [P] [US2] Create unit tests for Signal chat service — happy path message send/receive, error handling for invalid phone numbers, connection failure recovery — at backend/tests/unit/test_signal_chat.py testing backend/src/services/signal_chat.py
- [ ] T061 [P] [US2] Create unit tests for Signal delivery service — message delivery confirmation, retry on failure, delivery status tracking — at backend/tests/unit/test_signal_delivery.py testing backend/src/services/signal_delivery.py
- [ ] T062 [P] [US2] Create unit tests for Signal bridge service — bridge initialization, message routing between Signal and app, error propagation — at backend/tests/unit/test_signal_bridge.py testing backend/src/services/signal_bridge.py

### Backend: Missing Signal API Tests

- [ ] T063 [P] [US2] Create unit tests for Signal API endpoints — all endpoints in backend/src/api/signal.py including happy paths and error cases — at backend/tests/unit/test_api_signal.py

### Backend: Missing Middleware Tests

- [ ] T064 [P] [US2] Create unit tests for request ID middleware — request ID generation, propagation, header handling — at backend/tests/unit/test_middleware.py testing backend/src/middleware/request_id.py

### Backend: Missing Copilot Polling Sub-module Tests

- [ ] T065 [P] [US2] Create unit tests for copilot polling agent_output sub-module — output parsing, validation, error handling — at backend/tests/unit/test_copilot_polling_agent_output.py testing backend/src/services/copilot_polling/agent_output.py
- [ ] T066 [P] [US2] Create unit tests for copilot polling completion sub-module — completion detection, status transitions — at backend/tests/unit/test_copilot_polling_completion.py testing backend/src/services/copilot_polling/completion.py
- [ ] T067 [P] [US2] Create unit tests for copilot polling helpers sub-module — utility functions, data transformations — at backend/tests/unit/test_copilot_polling_helpers.py testing backend/src/services/copilot_polling/helpers.py
- [ ] T068 [P] [US2] Create unit tests for copilot polling pipeline sub-module — pipeline execution, step sequencing, error propagation — at backend/tests/unit/test_copilot_polling_pipeline.py testing backend/src/services/copilot_polling/pipeline.py
- [ ] T069 [P] [US2] Create unit tests for copilot polling recovery sub-module — recovery strategies, retry logic, state restoration — at backend/tests/unit/test_copilot_polling_recovery.py testing backend/src/services/copilot_polling/recovery.py
- [ ] T070 [P] [US2] Create unit tests for copilot polling state sub-module — state management, transitions, persistence — at backend/tests/unit/test_copilot_polling_state.py testing backend/src/services/copilot_polling/state.py
- [ ] T071 [P] [US2] Create unit tests for copilot polling polling_loop sub-module — loop lifecycle, interval management, cancellation — at backend/tests/unit/test_copilot_polling_polling_loop.py testing backend/src/services/copilot_polling/polling_loop.py

### Backend: Missing Workflow Orchestrator Sub-module Tests

- [ ] T072 [P] [US2] Create unit tests for workflow orchestrator config sub-module — configuration loading, validation, defaults — at backend/tests/unit/test_workflow_orchestrator_config.py testing backend/src/services/workflow_orchestrator/config.py
- [ ] T073 [P] [US2] Create unit tests for workflow orchestrator models sub-module — model validation, serialization, state representation — at backend/tests/unit/test_workflow_orchestrator_models.py testing backend/src/services/workflow_orchestrator/models.py
- [ ] T074 [P] [US2] Create unit tests for workflow orchestrator transitions sub-module — state transitions, guard conditions, invalid transitions — at backend/tests/unit/test_workflow_orchestrator_transitions.py testing backend/src/services/workflow_orchestrator/transitions.py

### Backend: Missing GitHub Projects Sub-module Tests

- [ ] T075 [P] [US2] Create unit tests for GitHub projects GraphQL sub-module — query building, response parsing, error handling — at backend/tests/unit/test_github_projects_graphql.py testing backend/src/services/github_projects/graphql.py

### Backend: Missing Utility and Other Module Tests

- [ ] T076 [P] [US2] Create unit tests for backend utilities — all utility functions in backend/src/utils.py — at backend/tests/unit/test_utils.py
- [ ] T077 [P] [US2] Create unit tests for encryption service — key generation, encrypt/decrypt roundtrip, invalid key handling — at backend/tests/unit/test_encryption.py testing backend/src/services/encryption.py (expand beyond existing test_token_encryption.py)
- [ ] T078 [P] [US2] Create unit tests for constants module — validate constant values and types — at backend/tests/unit/test_constants.py testing backend/src/constants.py
- [ ] T079 [P] [US2] Create unit tests for dependencies module — dependency injection, service resolution — at backend/tests/unit/test_dependencies.py testing backend/src/dependencies.py
- [ ] T080 [P] [US2] Create unit tests for exceptions module — custom exception creation, serialization, error codes — at backend/tests/unit/test_exceptions.py testing backend/src/exceptions.py

### Frontend: Missing Hook Tests (10 untested hooks)

- [ ] T081 [P] [US2] Create unit tests for useChat hook — message send/receive, loading states, error handling, real-time updates — at frontend/src/hooks/useChat.test.tsx testing frontend/src/hooks/useChat.ts
- [ ] T082 [P] [US2] Create unit tests for useWorkflow hook — workflow step execution, status transitions, error states — at frontend/src/hooks/useWorkflow.test.tsx testing frontend/src/hooks/useWorkflow.ts
- [ ] T083 [P] [US2] Create unit tests for useProjectBoard hook — board data fetching, column/card operations, drag-and-drop state — at frontend/src/hooks/useProjectBoard.test.tsx testing frontend/src/hooks/useProjectBoard.ts
- [ ] T084 [P] [US2] Create unit tests for useSettings hook — settings loading, saving, validation, default values — at frontend/src/hooks/useSettings.test.tsx testing frontend/src/hooks/useSettings.ts
- [ ] T085 [P] [US2] Create unit tests for useSettingsForm hook — form state management, validation, submission, dirty tracking — at frontend/src/hooks/useSettingsForm.test.tsx testing frontend/src/hooks/useSettingsForm.ts
- [ ] T086 [P] [US2] Create unit tests for useAgentConfig hook — agent configuration loading, updating, preset selection — at frontend/src/hooks/useAgentConfig.test.tsx testing frontend/src/hooks/useAgentConfig.ts
- [ ] T087 [P] [US2] Create unit tests for useAppTheme hook — theme switching, persistence, system preference detection — at frontend/src/hooks/useAppTheme.test.tsx testing frontend/src/hooks/useAppTheme.ts

### Frontend: Missing Component Tests (critical components)

- [ ] T088 [P] [US2] Create unit tests for ProjectBoard component — board rendering, column layout, empty state — at frontend/src/components/board/ProjectBoard.test.tsx testing frontend/src/components/board/ProjectBoard.tsx
- [ ] T089 [P] [US2] Create unit tests for BoardColumn component — column rendering, card list, drag zone — at frontend/src/components/board/BoardColumn.test.tsx testing frontend/src/components/board/BoardColumn.tsx
- [ ] T090 [P] [US2] Create unit tests for IssueCard component — card rendering, status display, click handling — at frontend/src/components/board/IssueCard.test.tsx testing frontend/src/components/board/IssueCard.tsx
- [ ] T091 [P] [US2] Create unit tests for ChatInterface component — message list rendering, input handling, send action — at frontend/src/components/chat/ChatInterface.test.tsx testing frontend/src/components/chat/ChatInterface.tsx
- [ ] T092 [P] [US2] Create unit tests for ChatPopup component — open/close toggle, position, message display — at frontend/src/components/chat/ChatPopup.test.tsx testing frontend/src/components/chat/ChatPopup.tsx
- [ ] T093 [P] [US2] Create unit tests for MessageBubble component — message rendering, sender distinction, timestamp display — at frontend/src/components/chat/MessageBubble.test.tsx testing frontend/src/components/chat/MessageBubble.tsx
- [ ] T094 [P] [US2] Create unit tests for LoginButton component — login trigger, loading state, error display — at frontend/src/components/auth/LoginButton.test.tsx testing frontend/src/components/auth/LoginButton.tsx
- [ ] T095 [P] [US2] Create unit tests for ErrorBoundary component — error catching, fallback rendering, error reporting — at frontend/src/components/common/ErrorBoundary.test.tsx testing frontend/src/components/common/ErrorBoundary.tsx
- [ ] T096 [P] [US2] Create unit tests for GlobalSettings component — settings display, form interactions — at frontend/src/components/settings/GlobalSettings.test.tsx testing frontend/src/components/settings/GlobalSettings.tsx
- [ ] T097 [P] [US2] Create unit tests for ProjectSettings component — project-specific settings display and editing — at frontend/src/components/settings/ProjectSettings.test.tsx testing frontend/src/components/settings/ProjectSettings.tsx
- [ ] T098 [P] [US2] Create unit tests for IssueDetailModal component — modal rendering, detail display, close behavior — at frontend/src/components/board/IssueDetailModal.test.tsx testing frontend/src/components/board/IssueDetailModal.tsx

### Frontend: Missing Service and Page Tests

- [ ] T099 [P] [US2] Create unit tests for API service module — request building, response parsing, error handling, auth header injection — at frontend/src/services/api.test.ts testing frontend/src/services/api.ts
- [ ] T100 [P] [US2] Create unit tests for ProjectBoardPage — page rendering, data loading, error states — at frontend/src/pages/ProjectBoardPage.test.tsx testing frontend/src/pages/ProjectBoardPage.tsx
- [ ] T101 [P] [US2] Create unit tests for SettingsPage — page rendering, navigation, tab switching — at frontend/src/pages/SettingsPage.test.tsx testing frontend/src/pages/SettingsPage.tsx

### Frontend: Missing Utility Tests

- [ ] T102 [P] [US2] Create unit tests for formatTime utility — formatting edge cases, locale handling, invalid inputs — at frontend/src/utils/formatTime.test.ts testing frontend/src/utils/formatTime.ts
- [ ] T103 [P] [US2] Create unit tests for generateId utility — ID format, uniqueness, collision resistance — at frontend/src/utils/generateId.test.ts testing frontend/src/utils/generateId.ts

### Post-Coverage Verification

- [ ] T104 [US2] Run backend coverage report (cd backend && pytest --cov=src --cov-report=term-missing) and verify all documented critical flows now have non-zero coverage
- [ ] T105 [US2] Run frontend coverage report (cd frontend && npm run test:coverage) and verify all documented critical flows now have non-zero coverage

**Checkpoint**: At this point, User Story 2 should be fully functional. Every documented critical application flow has at least one happy-path test and one error/edge-case test. Coverage has meaningfully increased from the baseline.

---

## Phase 5: User Story 3 — Discover, Fix, and Regression-Test Bugs (Priority: P2)

**Goal**: Fix all bugs discovered during the test audit and coverage expansion, with each fix accompanied by a dedicated regression test following TDD red-green-refactor.

**Independent Test**: Run the regression test for each discovered bug in isolation, confirming it fails before the fix and passes after.

- [ ] T106 [US3] Review audit findings from Phase 3 (T013–T059) and catalog all bugs discovered during the test audit — document each bug with description, affected module, and reproduction steps
- [ ] T107 [US3] Review coverage expansion findings from Phase 4 (T060–T103) and catalog any additional bugs discovered while writing new tests — document each bug with description, affected module, and reproduction steps
- [ ] T108 [US3] For each discovered backend bug: write a failing regression test in the appropriate backend/tests/unit/test_<module>.py file that reproduces the bug (red phase)
- [ ] T109 [US3] For each discovered backend bug: apply the minimal code fix in the appropriate backend/src/ file and confirm the regression test passes (green phase) while all other tests continue to pass
- [ ] T110 [US3] For each discovered frontend bug: write a failing regression test in the appropriate frontend/src/**/*.test.tsx file that reproduces the bug (red phase)
- [ ] T111 [US3] For each discovered frontend bug: apply the minimal code fix in the appropriate frontend/src/ file and confirm the regression test passes (green phase) while all other tests continue to pass
- [ ] T112 [US3] Run full test suite (backend + frontend) to verify all regression tests pass and no previously passing tests have been broken

**Checkpoint**: At this point, User Story 3 should be complete. Every discovered bug has a dedicated regression test. All fixes are minimal and verified.

---

## Phase 6: User Story 4 — Enforce DRY Principles in the Test Suite (Priority: P2)

**Goal**: Extract duplicated test setup, fixtures, mocks, and helper utilities into shared reusable modules. No substantive test setup logic duplicated across more than two test files.

**Independent Test**: Review the test codebase and confirm no substantive test setup logic is duplicated across more than two test files, and shared utilities are imported from dedicated helper modules.

### Backend DRY Refactoring

- [ ] T113 [US4] Identify all duplicated setup patterns across backend test files — catalog instances of repeated mock creation, test data setup, and assertion patterns across backend/tests/unit/ and backend/tests/integration/
- [ ] T114 [US4] Refactor backend/tests/unit/test_copilot_polling.py (157KB) — extract shared setup into backend/tests/helpers/factories.py and backend/tests/helpers/mocks.py; split into focused sub-files if beneficial (e.g., test_copilot_polling_run_creation.py, test_copilot_polling_status_check.py)
- [ ] T115 [US4] Refactor backend/tests/unit/test_github_projects.py (124KB) — extract shared setup into backend/tests/helpers/factories.py and backend/tests/helpers/mocks.py; split into focused sub-files if beneficial
- [ ] T116 [US4] Refactor backend/tests/unit/test_workflow_orchestrator.py (107KB) — extract shared setup into backend/tests/helpers/factories.py and backend/tests/helpers/mocks.py; split into focused sub-files if beneficial
- [ ] T117 [US4] Refactor remaining backend test files to use shared factories from backend/tests/helpers/factories.py instead of inline test data creation — update imports across all backend/tests/unit/ files
- [ ] T118 [US4] Refactor remaining backend test files to use shared mock builders from backend/tests/helpers/mocks.py instead of duplicated mock setup — update imports across all backend/tests/unit/ files
- [ ] T119 [US4] Refactor remaining backend test files to use shared assertion helpers from backend/tests/helpers/assertions.py instead of repeated assertion patterns — update imports across all backend/tests/unit/ files
- [ ] T120 [US4] Update backend/tests/conftest.py to leverage new shared helpers — ensure root fixtures use factories and mock builders; add any new shared fixtures needed by multiple test files

### Frontend DRY Refactoring

- [ ] T121 [US4] Identify all duplicated setup patterns across frontend test files — catalog instances of repeated mock creation, render wrappers, and test data setup across frontend/src/**/*.test.tsx
- [ ] T122 [US4] Refactor frontend test files to use shared factories from frontend/src/test/factories/index.ts instead of inline test data creation — update imports across all test files
- [ ] T123 [US4] Extend frontend/src/test/test-utils.tsx with any additional shared render helpers identified during the audit — ensure all component tests use renderWithProviders consistently
- [ ] T124 [US4] Ensure frontend/src/test/setup.ts createMockApi is used consistently across all test files that mock the API — eliminate any duplicated API mock setup

### DRY Verification

- [ ] T125 [US4] Run full backend test suite (cd backend && pytest -v) to verify all tests pass after DRY refactoring with identical behavior
- [ ] T126 [US4] Run full frontend test suite (cd frontend && npm test) to verify all tests pass after DRY refactoring with identical behavior

**Checkpoint**: At this point, User Story 4 should be complete. No substantive test setup logic is duplicated across more than two test files. All shared utilities are centralized.

---

## Phase 7: User Story 5 — Enforce Testing Best Practices and CI Stability (Priority: P3)

**Goal**: Apply consistent AAA structure, descriptive naming, proper isolation, and meaningful assertions to all tests. Ensure CI runs reliably with zero flaky failures.

**Independent Test**: Review a sample of tests against the best-practices checklist from contracts/test-conventions.md. Confirm all tests pass consistently across multiple CI runs with no flaky failures.

### Best Practices Application

- [ ] T127 [US5] Review and update all backend test class and method names to follow the convention Test<Feature><Behavior> and test_<behavior_description> per contracts/test-conventions.md — update naming in all backend/tests/unit/ files
- [ ] T128 [P] [US5] Review and update all frontend test describe/it block names to follow the convention from contracts/test-conventions.md — update naming in all frontend/src/**/*.test.tsx files
- [ ] T129 [US5] Verify all backend tests follow the Arrange-Act-Assert pattern with clearly separated phases — add section comments (# Arrange, # Act, # Assert) where missing in backend/tests/unit/ and backend/tests/integration/ files
- [ ] T130 [P] [US5] Verify all frontend tests follow the Arrange-Act-Assert pattern with clearly separated phases — add section comments where missing in frontend/src/**/*.test.tsx files
- [ ] T131 [US5] Add meaningful assertion messages to all non-obvious assertions in backend tests — update assertions in backend/tests/unit/ and backend/tests/integration/ files to include descriptive failure messages
- [ ] T132 [P] [US5] Add meaningful assertion messages to all non-obvious assertions in frontend tests — update assertions in frontend/src/**/*.test.tsx files to include descriptive failure messages

### Test Isolation Verification

- [ ] T133 [US5] Verify backend test isolation by running each test file independently (pytest tests/unit/test_<module>.py for each file) and comparing results to full suite run — fix any hidden dependencies
- [ ] T134 [P] [US5] Verify frontend test isolation by running each test file independently (npx vitest run <file> for each file) and comparing results to full suite run — fix any hidden dependencies

### Skipped/Broken Test Cleanup

- [ ] T135 [US5] Search for all skipped tests (@pytest.mark.skip, pytest.skip(), it.skip, describe.skip, test.skip) across backend and frontend — fix each skipped test or remove with documented rationale

### CI Stability Verification

- [ ] T136 [US5] Run the full backend test suite five consecutive times (cd backend && for i in {1..5}; do pytest -v; done) to verify zero flaky failures
- [ ] T137 [US5] Run the full frontend test suite five consecutive times (cd frontend && for i in {1..5}; do npm test; done) to verify zero flaky failures
- [ ] T138 [US5] Verify CI pipeline runs successfully with backend tests re-enabled — confirm .github/workflows/ci.yml passes on a test push

**Checkpoint**: At this point, User Story 5 should be complete. All tests follow best practices, CI is stable, and no skipped/broken tests remain.

---

## Phase 8: User Story 6 — Organize Tests to Mirror Application Structure (Priority: P3)

**Goal**: Organize test files logically to mirror the application's module structure so any module's tests are locatable in a predictable directory.

**Independent Test**: Select any application module and locate its corresponding test file(s) within a predictable, consistent directory structure.

- [ ] T139 [US6] Verify backend test file naming matches the module structure — ensure every backend/src/<path>/<module>.py has a corresponding backend/tests/unit/test_<module>.py; document any gaps
- [ ] T140 [P] [US6] Verify frontend test file co-location — ensure every tested frontend/src/<path>/<Component>.tsx has a co-located <Component>.test.tsx; document any gaps
- [ ] T141 [US6] Create any missing __init__.py files in backend/tests/ subdirectories to ensure proper module resolution
- [ ] T142 [US6] If any test files created in Phase 4 (US2) are not yet in the correct location per the naming convention, move them to the correct paths maintaining the mirrored structure

**Checkpoint**: At this point, User Story 6 should be complete. All test files follow a consistent, predictable structure that mirrors the application.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation, and cleanup that affects multiple user stories.

- [ ] T143 Run final full backend test suite with coverage (cd backend && pytest --cov=src --cov-report=term-missing) and document final coverage percentages
- [ ] T144 Run final full frontend test suite with coverage (cd frontend && npm run test:coverage) and document final coverage percentages
- [ ] T145 Compare final coverage numbers against Phase 2 baselines (T008, T009) and document the improvement
- [ ] T146 [P] Run backend linting (cd backend && ruff check src tests && ruff format --check src tests) to verify all new and modified test files pass lint
- [ ] T147 [P] Run frontend linting (cd frontend && npm run lint) to verify all new and modified test files pass lint
- [ ] T148 [P] Run backend type checking (cd backend && pyright src) to verify no type regressions
- [ ] T149 [P] Run frontend type checking (cd frontend && npm run type-check) to verify no type regressions
- [ ] T150 Perform final CI verification — push all changes and confirm .github/workflows/ci.yml passes with backend tests re-enabled, all frontend tests passing, and Docker builds succeeding
- [ ] T151 Run quickstart.md validation — follow the steps in specs/013-test-coverage-dry/quickstart.md to verify all documented commands work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 - Audit (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 - Coverage (Phase 4)**: Depends on Phase 3 (audit informs coverage gaps)
- **User Story 3 - Bug Fixes (Phase 5)**: Depends on Phase 3 and Phase 4 (bugs discovered during audit and coverage work)
- **User Story 4 - DRY (Phase 6)**: Can start after Phase 3 (audit flags duplication); best after Phase 4 (new tests may introduce duplication)
- **User Story 5 - Best Practices (Phase 7)**: Depends on Phases 3, 4, 6 (apply best practices to final test code)
- **User Story 6 - Organization (Phase 8)**: Depends on Phases 3, 4, 6 (organize final test file structure)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Should start after US1 (Phase 3) — audit findings inform where coverage is truly missing vs. misaligned
- **User Story 3 (P2)**: Should start after US1 + US2 — bugs are discovered during audit and coverage expansion
- **User Story 4 (P2)**: Can start after US1 — audit flags duplication; best combined with or after US2
- **User Story 5 (P3)**: Should start after US1 + US2 + US4 — apply best practices to the final, deduplicated test suite
- **User Story 6 (P3)**: Can start after US2 + US4 — organize the final set of test files

### Within Each User Story

- Audit/identify duplication before refactoring
- Write failing tests before implementing fixes (TDD for bug fixes)
- Extract shared utilities before updating consumers
- Core changes before verification runs
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 1 tasks marked [P] can run in parallel (T002–T005 create independent helper modules)
- Phase 2 baseline tasks T008 and T009 can run in parallel
- Most Phase 3 audit tasks marked [P] can run in parallel (each audits a different test file)
- All Phase 4 new test creation tasks marked [P] can run in parallel (each creates a new test file)
- Phase 6 backend and frontend DRY refactoring can be parallelized (T113–T120 vs T121–T124)
- Phase 7 backend and frontend best practice tasks can be parallelized (T127/T129/T131 vs T128/T130/T132)

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all helper module creation in parallel:
Task T002: "Create backend test data factory module at backend/tests/helpers/factories.py"
Task T003: "Create backend custom assertion helpers at backend/tests/helpers/assertions.py"
Task T004: "Create backend reusable mock builders at backend/tests/helpers/mocks.py"
Task T005: "Create frontend test data factories at frontend/src/test/factories/index.ts"
```

## Parallel Example: Phase 4 Backend New Tests

```bash
# Launch all new backend Signal tests in parallel:
Task T060: "Create unit tests for Signal chat service at backend/tests/unit/test_signal_chat.py"
Task T061: "Create unit tests for Signal delivery service at backend/tests/unit/test_signal_delivery.py"
Task T062: "Create unit tests for Signal bridge service at backend/tests/unit/test_signal_bridge.py"
Task T063: "Create unit tests for Signal API endpoints at backend/tests/unit/test_api_signal.py"
```

## Parallel Example: Phase 4 Frontend New Hook Tests

```bash
# Launch all new frontend hook tests in parallel:
Task T081: "Create unit tests for useChat hook at frontend/src/hooks/useChat.test.tsx"
Task T082: "Create unit tests for useWorkflow hook at frontend/src/hooks/useWorkflow.test.tsx"
Task T083: "Create unit tests for useProjectBoard hook at frontend/src/hooks/useProjectBoard.test.tsx"
Task T084: "Create unit tests for useSettings hook at frontend/src/hooks/useSettings.test.tsx"
Task T085: "Create unit tests for useSettingsForm hook at frontend/src/hooks/useSettingsForm.test.tsx"
Task T086: "Create unit tests for useAgentConfig hook at frontend/src/hooks/useAgentConfig.test.tsx"
Task T087: "Create unit tests for useAppTheme hook at frontend/src/hooks/useAppTheme.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (shared helper infrastructure)
2. Complete Phase 2: Foundational (baselines, CI re-enablement)
3. Complete Phase 3: User Story 1 (test audit and alignment)
4. **STOP and VALIDATE**: Run full suite, verify every remaining test maps to documented behavior
5. Deploy/demo if ready — the test suite now gives genuine confidence

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Audit) → Validate independently → Clean test suite (MVP!)
3. Add User Story 2 (Coverage) → Validate independently → All critical flows tested
4. Add User Story 3 (Bug Fixes) → Validate independently → All discovered bugs fixed with regression tests
5. Add User Story 4 (DRY) → Validate independently → No duplicated test logic
6. Add User Story 5 (Best Practices) → Validate independently → Consistent structure, CI stable
7. Add User Story 6 (Organization) → Validate independently → Predictable test file structure
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Audit — should go first, informs others)
3. Once Audit is done:
   - Developer A: User Story 2 (Coverage — backend tests)
   - Developer B: User Story 2 (Coverage — frontend tests)
   - Developer C: User Story 4 (DRY — extract from audited files)
4. Once Coverage + DRY are done:
   - Developer A: User Story 3 (Bug Fixes)
   - Developer B: User Story 5 (Best Practices)
   - Developer C: User Story 6 (Organization)
5. All complete Polish phase together

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 151 |
| **Phase 1 (Setup)** | 5 tasks |
| **Phase 2 (Foundational)** | 7 tasks |
| **Phase 3 (US1 — Audit)** | 47 tasks |
| **Phase 4 (US2 — Coverage)** | 46 tasks |
| **Phase 5 (US3 — Bug Fixes)** | 7 tasks |
| **Phase 6 (US4 — DRY)** | 14 tasks |
| **Phase 7 (US5 — Best Practices)** | 12 tasks |
| **Phase 8 (US6 — Organization)** | 4 tasks |
| **Phase 9 (Polish)** | 9 tasks |
| **Parallel opportunities** | 108 tasks marked [P] |
| **Suggested MVP scope** | Phase 1 + 2 + 3 (User Story 1: Audit) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD (red-green-refactor) is required for bug fixes in US3
- Tests ARE explicitly requested throughout this feature
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The three largest test files (157KB, 124KB, 107KB) are high-priority DRY targets in US4
- Backend CI re-enablement (T012) is a blocking foundational task
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
