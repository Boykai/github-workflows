# Tasks: Achieve 90% Test Coverage with Best Practices

**Input**: Design documents from `/specs/005-test-coverage/`
**Prerequisites**: spec.md (user stories with priorities P1–P3)

**Tests**: Test writing IS the core deliverable of this feature. All test tasks produce automated tests following best practices (AAA pattern, isolation, mocking).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`, `frontend/src/`, `frontend/e2e/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Fix existing lint failures and ensure test tooling is properly configured for coverage measurement

- [ ] T001 Fix unused import `waitFor` in frontend/src/hooks/useWorkflow.test.tsx
- [ ] T002 [P] Fix unsorted imports (I001) in backend/tests/unit/test_completion_providers.py
- [ ] T003 [P] Add E402 exception for backend/tests/unit/test_api_endpoints.py in backend/pyproject.toml ruff per-file-ignores
- [ ] T004 Verify backend coverage tool configuration — confirm `pytest-cov` is installed and `pytest --cov=src --cov-report=term-missing --cov-report=xml:coverage.xml` produces a valid report in backend/
- [ ] T005 [P] Verify frontend coverage tool configuration — confirm `vitest run --coverage` produces text, lcov, and json-summary reports in frontend/coverage/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish baseline coverage measurements and configure coverage exclusions so all subsequent test-writing work targets real gaps

**⚠️ CRITICAL**: No user story work can begin until baseline coverage is measured

- [ ] T006 Run backend baseline coverage audit — execute `pytest --cov=src --cov-report=term-missing` in backend/ and record per-module coverage percentages
- [ ] T007 [P] Run frontend baseline coverage audit — execute `npx vitest run --coverage` in frontend/ and record per-module coverage percentages
- [ ] T008 Review and update backend coverage exclusions — ensure non-application files (__init__.py, constants with only literals) are handled appropriately in backend/pyproject.toml pytest config
- [ ] T009 [P] Review and update frontend coverage exclusions — confirm frontend/vitest.config.ts excludes src/test/**, src/vite-env.d.ts, src/main.tsx, and test files from coverage calculations

**Checkpoint**: Baseline coverage measured for both backend and frontend. Gaps identified per module.

---

## Phase 3: User Story 1 — Coverage Gap Audit and Reporting (Priority: P1) 🎯 MVP

**Goal**: Ensure coverage tools produce clear, actionable reports showing line, branch, and function coverage per module so developers can identify files below 90%

**Independent Test**: Run `pytest --cov=src --cov-report=term-missing --cov-report=html:htmlcov` in backend/ and `npx vitest run --coverage` in frontend/; verify reports are generated and readable

### Implementation for User Story 1

- [ ] T010 [US1] Configure backend pytest-cov to produce HTML report — add `--cov-report=html:htmlcov` to backend pytest invocation and add `htmlcov/` to backend/.dockerignore
- [ ] T011 [P] [US1] Configure frontend vitest coverage to include branch coverage — verify frontend/vitest.config.ts reporter list includes `['text', 'lcov', 'json-summary', 'html']` for local developer use
- [ ] T012 [US1] Document coverage commands in backend/README.md — add a "Running Tests & Coverage" section with commands for generating and viewing coverage reports
- [ ] T013 [P] [US1] Document coverage commands in frontend README or package.json scripts — ensure `npm run test:coverage` script exists and produces full report

**Checkpoint**: Developers can run a single command in each project to generate a human-readable coverage report identifying all gaps below 90%.

---

## Phase 4: User Story 2 — Comprehensive Test Suite Expansion (Priority: P1)

**Goal**: Write and refactor tests to achieve ≥90% line coverage across both backend and frontend, following AAA pattern, isolation, and proper mocking

**Independent Test**: Run full test suite with coverage enforcement — `pytest --cov=src --cov-fail-under=90` in backend/ and `npx vitest run --coverage` (with thresholds) in frontend/; verify all tests pass and coverage thresholds are met

### Backend Test Expansion

- [ ] T014 [P] [US2] Write/expand unit tests for backend/src/api/workflow.py in backend/tests/unit/test_workflow_api.py — cover GET/PUT workflow config, GET available agents endpoints with mocked services
- [ ] T015 [P] [US2] Write/expand unit tests for backend/src/prompts/issue_generation.py in backend/tests/unit/test_prompts.py — cover prompt template generation and variable substitution
- [ ] T016 [P] [US2] Write/expand unit tests for backend/src/prompts/task_generation.py in backend/tests/unit/test_prompts.py — cover task prompt generation paths
- [ ] T017 [P] [US2] Review and expand tests for backend/src/services/ai_agent.py in backend/tests/unit/test_ai_agent.py — cover uncovered branches, error paths, and async operations with proper mocking
- [ ] T018 [P] [US2] Review and expand tests for backend/src/services/completion_providers.py in backend/tests/unit/test_completion_providers.py — cover all provider types, error handling, and edge cases
- [ ] T019 [P] [US2] Review and expand tests for backend/src/services/github_projects.py in backend/tests/unit/test_github_projects.py — cover list_available_agents, API error handling, and edge cases
- [ ] T020 [P] [US2] Review and expand tests for backend/src/services/workflow_orchestrator.py in backend/tests/unit/test_workflow_orchestrator.py — cover pass-through logic, agent assignment coercion, and error paths
- [ ] T021 [P] [US2] Review and expand tests for backend/src/services/copilot_polling.py in backend/tests/unit/test_copilot_polling.py — cover polling lifecycle, error handling, and timeout paths
- [ ] T022 [P] [US2] Review and expand tests for backend/src/services/websocket.py in backend/tests/unit/test_websocket.py — cover connection management, message broadcasting, and disconnect handling
- [ ] T023 [P] [US2] Review and expand tests for backend/src/services/cache.py in backend/tests/unit/test_cache.py — cover all cache operations, expiry, and edge cases
- [ ] T024 [P] [US2] Review and expand tests for backend/src/services/github_auth.py in backend/tests/unit/test_github_auth.py — cover token exchange, validation, and error paths
- [ ] T025 [P] [US2] Review and expand tests for backend/src/api/auth.py, board.py, chat.py, projects.py, tasks.py in backend/tests/unit/test_api_endpoints.py — cover untested endpoint paths and error handling
- [ ] T026 [P] [US2] Review and expand tests for backend/src/api/webhooks.py in backend/tests/unit/test_webhooks.py — cover webhook verification, event handling, and error paths
- [ ] T027 [P] [US2] Review and expand tests for backend/src/models/ in backend/tests/unit/test_models.py — cover model validation, serialization, and edge cases for all Pydantic models
- [ ] T028 [P] [US2] Review and expand tests for backend/src/main.py in backend/tests/unit/test_main.py — cover app startup, middleware, and CORS configuration
- [ ] T029 [P] [US2] Review and expand tests for backend/src/config.py in backend/tests/unit/test_config.py — cover settings loading, defaults, and validation
- [ ] T030 [P] [US2] Review and expand tests for backend/src/exceptions.py in backend/tests/unit/test_exceptions.py — cover custom exception classes and error handling utilities
- [ ] T031 [US2] Refactor any flaky or poorly structured backend tests — review all backend/tests/ files for shared mutable state, non-deterministic behavior, missing mocks for external services, and tests that don't follow AAA pattern
- [ ] T032 [US2] Run backend coverage audit and verify ≥90% — execute `pytest --cov=src --cov-report=term-missing --cov-fail-under=90` in backend/ and confirm all modules pass threshold

### Frontend Test Expansion

- [ ] T033 [P] [US2] Review and expand tests for frontend/src/App.tsx in frontend/src/App.test.tsx — cover routing, auth state rendering, and error boundaries
- [ ] T034 [P] [US2] Review and expand tests for frontend/src/services/api.ts in frontend/src/services/api.test.ts — cover all API functions, error handling, and response parsing
- [ ] T035 [P] [US2] Review and expand tests for frontend/src/hooks/useAuth.ts in frontend/src/hooks/useAuth.test.tsx — cover login flow, logout, token handling, and error states
- [ ] T036 [P] [US2] Review and expand tests for frontend/src/hooks/useChat.ts in frontend/src/hooks/useChat.test.tsx — cover message sending, receiving, WebSocket integration, and error states
- [ ] T037 [P] [US2] Review and expand tests for frontend/src/hooks/useProjectBoard.ts in frontend/src/hooks/useProjectBoard.test.tsx — cover board data fetching, column operations, and error states
- [ ] T038 [P] [US2] Review and expand tests for frontend/src/hooks/useProjects.ts in frontend/src/hooks/useProjects.test.tsx — cover project listing, selection, and error states
- [ ] T039 [P] [US2] Review and expand tests for frontend/src/hooks/useRealTimeSync.ts in frontend/src/hooks/useRealTimeSync.test.tsx — cover WebSocket connection, reconnection, and event handling
- [ ] T040 [P] [US2] Review and expand tests for frontend/src/hooks/useWorkflow.ts in frontend/src/hooks/useWorkflow.test.tsx — cover workflow config fetching, updating, and error states
- [ ] T041 [P] [US2] Review and expand tests for frontend/src/hooks/useAgentConfig.ts in frontend/src/hooks/useAgentConfig.test.tsx — cover agent config state management, save/discard, and preset application
- [ ] T042 [P] [US2] Review and expand tests for frontend/src/hooks/useAppTheme.ts in frontend/src/hooks/useAppTheme.test.tsx — cover theme toggling, persistence, and system preference detection
- [ ] T043 [P] [US2] Review and expand tests for frontend/src/components/board/ProjectBoard.tsx in frontend/src/components/board/ProjectBoard.test.tsx — cover board rendering, column display, and interaction
- [ ] T044 [P] [US2] Review and expand tests for frontend/src/components/board/BoardColumn.tsx in frontend/src/components/board/BoardColumn.test.tsx — cover column rendering, card display, and drag interactions
- [ ] T045 [P] [US2] Review and expand tests for frontend/src/components/board/IssueCard.tsx in frontend/src/components/board/IssueCard.test.tsx — cover card rendering, click handling, and status display
- [ ] T046 [P] [US2] Review and expand tests for frontend/src/components/board/IssueDetailModal.tsx in frontend/src/components/board/IssueDetailModal.test.tsx — cover modal open/close, detail display, and actions
- [ ] T047 [P] [US2] Review and expand tests for frontend/src/components/board/AgentConfigRow.tsx in frontend/src/components/board/AgentConfigRow.test.tsx — cover expand/collapse, column rendering, and save bar integration
- [ ] T048 [P] [US2] Review and expand tests for frontend/src/components/board/AgentColumnCell.tsx in frontend/src/components/board/AgentColumnCell.test.tsx — cover agent display, add/remove, and drag-and-drop
- [ ] T049 [P] [US2] Review and expand tests for frontend/src/components/board/AgentTile.tsx in frontend/src/components/board/AgentTile.test.tsx — cover tile rendering, expand/collapse, and remove action
- [ ] T050 [P] [US2] Review and expand tests for frontend/src/components/board/AgentSaveBar.tsx in frontend/src/components/board/AgentSaveBar.test.tsx — cover save/discard buttons, loading states, and error display
- [ ] T051 [P] [US2] Review and expand tests for frontend/src/components/board/AddAgentPopover.tsx in frontend/src/components/board/AddAgentPopover.test.tsx — cover popover open/close, agent selection, and loading states
- [ ] T052 [P] [US2] Review and expand tests for frontend/src/components/board/AgentPresetSelector.tsx in frontend/src/components/board/AgentPresetSelector.test.tsx — cover preset selection, confirmation dialog, and application
- [ ] T053 [P] [US2] Review and expand tests for frontend/src/components/board/colorUtils.ts in frontend/src/components/board/colorUtils.test.ts — cover all color utility functions and edge cases
- [ ] T054 [P] [US2] Review and expand tests for frontend/src/components/chat/ChatInterface.tsx in frontend/src/components/chat/ChatInterface.test.tsx — cover message display, input handling, and send functionality
- [ ] T055 [P] [US2] Review and expand tests for frontend/src/components/chat/MessageBubble.tsx in frontend/src/components/chat/MessageBubble.test.tsx — cover message rendering, user/bot distinction, and timestamps
- [ ] T056 [P] [US2] Review and expand tests for frontend/src/components/chat/TaskPreview.tsx in frontend/src/components/chat/TaskPreview.test.tsx — cover task preview rendering and interaction
- [ ] T057 [P] [US2] Review and expand tests for frontend/src/components/chat/StatusChangePreview.tsx in frontend/src/components/chat/StatusChangePreview.test.tsx — cover status change display and confirmation
- [ ] T058 [P] [US2] Review and expand tests for frontend/src/components/chat/IssueRecommendationPreview.tsx in frontend/src/components/chat/IssueRecommendationPreview.test.tsx — cover recommendation rendering and actions
- [ ] T059 [P] [US2] Review and expand tests for frontend/src/components/auth/LoginButton.tsx in frontend/src/components/auth/LoginButton.test.tsx — cover login button rendering and click behavior
- [ ] T060 [P] [US2] Review and expand tests for frontend/src/components/sidebar/ProjectSelector.tsx in frontend/src/components/sidebar/ProjectSelector.test.tsx — cover project list display, selection, and empty state
- [ ] T061 [P] [US2] Review and expand tests for frontend/src/components/sidebar/ProjectSidebar.tsx in frontend/src/components/sidebar/ProjectSidebar.test.tsx — cover sidebar rendering, navigation, and collapse
- [ ] T062 [P] [US2] Review and expand tests for frontend/src/components/sidebar/TaskCard.tsx in frontend/src/components/sidebar/TaskCard.test.tsx — cover task card rendering and click handling
- [ ] T063 [P] [US2] Review and expand tests for frontend/src/components/common/ErrorDisplay.tsx in frontend/src/components/common/ErrorDisplay.test.tsx — cover error message rendering and retry actions
- [ ] T064 [P] [US2] Review and expand tests for frontend/src/components/common/RateLimitIndicator.tsx in frontend/src/components/common/RateLimitIndicator.test.tsx — cover rate limit display and warning states
- [ ] T065 [P] [US2] Review and expand tests for frontend/src/pages/ProjectBoardPage.tsx in frontend/src/pages/ProjectBoardPage.test.tsx — cover page rendering, data loading, and integration with board components
- [ ] T066 [US2] Refactor any flaky or poorly structured frontend tests — review all frontend/src/**/*.test.{ts,tsx} files for shared mutable state, non-deterministic behavior, missing mocks, and tests that don't follow AAA pattern
- [ ] T067 [US2] Run frontend coverage audit and verify ≥90% — execute `npx vitest run --coverage` in frontend/ and confirm all thresholds pass (lines: 90%, functions: 90%, branches: 80%, statements: 90%)

**Checkpoint**: All backend and frontend tests pass with ≥90% coverage. No flaky tests. All tests follow AAA pattern with proper isolation and mocking.

---

## Phase 5: User Story 3 — CI/CD Coverage Enforcement (Priority: P2)

**Goal**: Configure the CI pipeline to enforce 90% coverage thresholds for both backend and frontend so coverage cannot regress below the required level

**Independent Test**: Submit a change that reduces coverage below 90% and verify the CI pipeline fails the build with a clear coverage deficit report

### Implementation for User Story 3

- [ ] T068 [US3] Verify backend CI coverage enforcement — confirm .github/workflows/ci.yml backend job runs `pytest --cov=src --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=90` and fails on coverage drop
- [ ] T069 [P] [US3] Verify frontend CI coverage enforcement — confirm frontend/vitest.config.ts thresholds (lines: 90, functions: 90, branches: 80, statements: 90) cause `npx vitest run --coverage` to fail when thresholds are not met
- [ ] T070 [US3] Ensure CI pipeline reports test failures clearly — verify .github/workflows/ci.yml uploads coverage artifacts on failure (if: always()) for both backend and frontend jobs

**Checkpoint**: CI pipeline enforces 90% coverage threshold on every PR. Any coverage regression is caught automatically.

---

## Phase 6: User Story 4 — Coverage Report Accessibility (Priority: P3)

**Goal**: Make coverage metrics visible and accessible without running commands locally via CI artifacts and repository documentation

**Independent Test**: Check the repository README for a coverage section and verify CI artifacts include coverage reports after a pipeline run

### Implementation for User Story 4

- [ ] T071 [US4] Add coverage summary section to project README.md — include current coverage status, links to coverage reports, and instructions for generating reports locally
- [ ] T072 [P] [US4] Ensure CI uploads backend coverage artifact — verify .github/workflows/ci.yml uploads backend/coverage.xml as a CI artifact on every run
- [ ] T073 [P] [US4] Ensure CI uploads frontend coverage artifact — verify .github/workflows/ci.yml uploads frontend/coverage/ directory as a CI artifact on every run

**Checkpoint**: Coverage reports are accessible as CI artifacts after every pipeline run. README documents coverage status and how to generate reports.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup across all user stories

- [ ] T074 Run full backend test suite with coverage and verify ≥90% — execute `pytest --cov=src --cov-report=term-missing --cov-fail-under=90` in backend/
- [ ] T075 [P] Run full frontend test suite with coverage and verify ≥90% — execute `npx vitest run --coverage` in frontend/
- [ ] T076 Verify backend ruff lint passes — run `ruff check src tests` in backend/
- [ ] T077 [P] Verify frontend eslint passes — run `npm run lint` in frontend/
- [ ] T078 [P] Verify backend ruff format check passes — run `ruff format --check src tests` in backend/
- [ ] T079 Review all test files for best-practice compliance — confirm AAA pattern, isolation, determinism, behavior-focus, and proper mocking across both codebases
- [ ] T080 Final CI pipeline validation — push changes and verify CI workflow passes all jobs (Backend, Frontend, Docker Build)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (lint fixes) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (baseline coverage measured)
- **US2 (Phase 4)**: Depends on Phase 2 (baseline coverage identified gaps to fill)
- **US3 (Phase 5)**: Depends on Phase 4 (tests must achieve 90% before enforcement is meaningful)
- **US4 (Phase 6)**: Depends on Phase 5 (CI must be configured before documenting artifacts)
- **Polish (Phase 7)**: Depends on all prior phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories, but benefits from US1 reports to identify gaps
- **US3 (P2)**: Can start after US2 (Phase 4) — coverage must be at 90% before threshold enforcement is useful
- **US4 (P3)**: Can start after US3 (Phase 5) — CI artifacts must exist before documenting accessibility

### Within Each User Story

- Backend and frontend tasks marked [P] can run in parallel (different codebases)
- Within backend: each module's test file can be worked on independently (all marked [P])
- Within frontend: each component's test file can be worked on independently (all marked [P])
- Refactoring tasks (T031, T066) should run after individual module tests are expanded
- Final coverage verification (T032, T067) must run after all test expansion tasks complete

### Parallel Opportunities

- **Phase 1**: All three lint fixes (T001, T002, T003) can run in parallel
- **Phase 2**: Backend audit (T006) and frontend audit (T007) can run in parallel
- **Phase 3**: Backend report config (T010) and frontend report config (T011) can run in parallel
- **Phase 4**: ALL backend test tasks (T014–T030) can run in parallel with each other; ALL frontend test tasks (T033–T065) can run in parallel with each other; backend and frontend work can run in parallel
- **Phase 5**: Backend CI verification (T068) and frontend CI verification (T069) can run in parallel
- **Phase 6**: All artifact tasks (T071, T072, T073) can run in parallel
- **Phase 7**: Backend validation (T074) and frontend validation (T075) can run in parallel

---

## Parallel Example: Phase 4 (US2 — Test Suite Expansion)

```bash
# Backend tests — all can run in parallel (different test files):
Task T014: Write tests for api/workflow.py in backend/tests/unit/test_workflow_api.py
Task T017: Expand tests for services/ai_agent.py in backend/tests/unit/test_ai_agent.py
Task T019: Expand tests for services/github_projects.py in backend/tests/unit/test_github_projects.py
Task T020: Expand tests for services/workflow_orchestrator.py in backend/tests/unit/test_workflow_orchestrator.py

# Frontend tests — all can run in parallel (different test files):
Task T033: Expand tests for App.tsx in frontend/src/App.test.tsx
Task T034: Expand tests for services/api.ts in frontend/src/services/api.test.ts
Task T043: Expand tests for ProjectBoard.tsx in frontend/src/components/board/ProjectBoard.test.tsx
Task T054: Expand tests for ChatInterface.tsx in frontend/src/components/chat/ChatInterface.test.tsx

# Backend and frontend work can happen simultaneously by different developers
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + 3)

1. Complete Phase 1: Fix lint failures
2. Complete Phase 2: Run baseline coverage audit
3. Complete Phase 3: Configure coverage reporting (US1)
4. **STOP and VALIDATE**: Coverage reports are generated and readable for both codebases
5. Visibility into coverage gaps achieved

### Incremental Delivery

1. Setup + Foundational → Lint fixed, baseline measured
2. Add US1 → Coverage reports configured → **Visibility MVP!**
3. Add US2 → Tests expanded to ≥90% → **Core deliverable!**
4. Add US3 → CI enforcement active → **Regression protection!**
5. Add US4 → Reports accessible in repo → **Transparency!**
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Backend test expansion (T014–T032)
   - Developer B: Frontend test expansion (T033–T067)
   - Developer C: Coverage reporting configuration (T010–T013)
3. After US2 is complete:
   - Any developer: CI enforcement (T068–T070) + Report accessibility (T071–T073)

---

## Summary

| Category | Count |
|---|---|
| **Total tasks** | 80 |
| **Phase 1 (Setup)** | 5 |
| **Phase 2 (Foundational)** | 4 |
| **US1 tasks (Coverage Audit)** | 4 |
| **US2 tasks (Test Expansion)** | 54 |
| **US3 tasks (CI Enforcement)** | 3 |
| **US4 tasks (Report Accessibility)** | 3 |
| **Polish tasks** | 7 |
| **Parallelizable tasks** | 62 |
| **MVP scope** | Phases 1–3 (US1 only, 13 tasks) |

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US2 (Test Suite Expansion) is the largest phase (~54 tasks) because it covers every source module
- Backend has 29 source files with 21 existing test files; frontend has 37 source files with 33 existing test files
- Most tasks are "review and expand" rather than "create new" since test infrastructure already exists
- Existing CI pipeline already has coverage enforcement (`--cov-fail-under=90` backend, thresholds in vitest.config.ts frontend)
- Commit after each task or logical group
- Stop at any checkpoint to validate progress independently
