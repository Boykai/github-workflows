# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/001-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are REQUIRED — FR-003 mandates at least one regression test per bug fix. Tests are embedded within each user story phase.

**Organization**: Tasks are grouped by bug category (mapped to user stories) to enable independent implementation and validation of each category phase. User Story 6 (Ambiguous Issue Documentation) is cross-cutting and applies within every phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend source**: `solune/backend/src/`
- **Backend tests**: `solune/backend/tests/`
- **Frontend source**: `solune/frontend/src/`
- **Frontend tests**: colocated `*.test.{ts,tsx}` files

---

## Phase 1: Setup (Baseline Establishment)

**Purpose**: Install dependencies, verify baseline tests pass, establish starting point for the bug bash

- [ ] T001 Install backend dependencies with `cd solune/backend && pip install -e ".[dev]"`
- [ ] T002 Install frontend dependencies with `cd solune/frontend && npm install`
- [ ] T003 [P] Run backend baseline tests with `cd solune/backend && pytest --timeout=60`
- [ ] T004 [P] Run frontend baseline tests with `cd solune/frontend && npm run test`
- [ ] T005 [P] Run backend linting baseline with `cd solune/backend && ruff check src tests && ruff format --check src tests`
- [ ] T006 [P] Run frontend linting baseline with `cd solune/frontend && npm run lint && npm run type-check`

**Checkpoint**: All tests and linters pass — baseline established. Record any pre-existing failures to exclude from bug bash scope.

---

## Phase 2: Foundational (Automated Scanning & Triage)

**Purpose**: Run automated security and static analysis tools to generate initial finding lists that guide manual review in subsequent phases

**⚠️ CRITICAL**: Complete automated scanning before starting manual review phases to prioritize effort

- [ ] T007 Run bandit security scan with `cd solune/backend && bandit -r src/ -f json -o /tmp/bandit-report.json` and triage findings
- [ ] T008 Run pyright type checking with `cd solune/backend && pyright src` and triage type errors for null refs, missing imports, type mismatches
- [ ] T009 [P] Run ruff extended checks with `cd solune/backend && ruff check src tests --select F401,F841,E711,E712,W,B,UP` and triage findings
- [ ] T010 [P] Run frontend ESLint analysis with `cd solune/frontend && npm run lint` and triage warnings/errors
- [ ] T011 [P] Run frontend TypeScript strict check with `cd solune/frontend && npm run type-check` and triage type errors
- [ ] T012 Create findings triage list mapping automated results to bug categories (Security/Runtime/Logic/Test Quality/Code Quality) and affected files

**Checkpoint**: Automated findings triaged — manual review phases can now proceed with prioritized file lists.

---

## Phase 3: User Story 1 — Security Vulnerability Discovery & Resolution (Priority: P1) 🎯 MVP

**Goal**: Audit every file for authentication bypasses, injection risks, exposed secrets/tokens, insecure defaults, and improper input validation. Fix confirmed vulnerabilities and add regression tests.

**Independent Test**: Run `pytest --timeout=60` + `ruff check` + `bandit -r src/` — all pass with zero security findings and all new regression tests green.

### Backend Security: Configuration & Secrets

- [ ] T013 [US1] Review `solune/backend/src/config.py` for hardcoded secrets, insecure defaults, exposed tokens, and missing validation of sensitive environment variables
- [ ] T014 [US1] Review `solune/backend/src/services/encryption.py` for weak crypto algorithms, key handling issues, and missing input validation
- [ ] T015 [P] [US1] Review `docker-compose.yml` and `.env.example` for exposed secrets, insecure default values, and missing secret rotation guidance

### Backend Security: Authentication & Authorization

- [ ] T016 [US1] Review `solune/backend/src/api/auth.py` for auth bypass vectors, session fixation, token leakage, and improper error responses that reveal auth state
- [ ] T017 [US1] Review `solune/backend/src/services/github_auth.py` for OAuth flow vulnerabilities, token storage issues, CSRF in OAuth callback, and redirect URI validation
- [ ] T018 [US1] Review `solune/backend/src/services/session_store.py` for session hijacking risks, insecure session ID generation, missing expiration, and improper session invalidation
- [ ] T019 [US1] Review `solune/backend/src/dependencies.py` for auth dependency injection bypasses, missing auth checks on protected endpoints, and improper permission validation

### Backend Security: Middleware

- [ ] T020 [P] [US1] Review `solune/backend/src/middleware/csrf.py` for CSRF protection bypasses, missing token validation on state-changing endpoints, and improper origin checking
- [ ] T021 [P] [US1] Review `solune/backend/src/middleware/admin_guard.py` for admin authorization bypasses and privilege escalation vectors
- [ ] T022 [P] [US1] Review `solune/backend/src/middleware/csp.py` for overly permissive Content Security Policy directives and missing security headers
- [ ] T023 [P] [US1] Review `solune/backend/src/middleware/rate_limit.py` for rate limit bypasses, missing rate limiting on auth endpoints, and IP spoofing via headers

### Backend Security: Input Validation & Injection

- [ ] T024 [US1] Review `solune/backend/src/services/database.py` for SQL injection risks, parameterized query usage, and unsafe string interpolation in SQL
- [ ] T025 [US1] Review all `solune/backend/src/api/*.py` endpoint handlers for missing input validation, path traversal risks, and improper error disclosure (audit: activity.py, agents.py, apps.py, board.py, chat.py, chores.py, cleanup.py, health.py, mcp.py, metadata.py, onboarding.py, pipelines.py, projects.py, settings.py, signal.py, tasks.py, tools.py, webhook_models.py, webhooks.py, workflow.py)
- [ ] T026 [P] [US1] Review `solune/backend/src/models/*.py` Pydantic models for missing field validators, overly permissive types, and unsafe defaults (audit all 25 model files)
- [ ] T027 [P] [US1] Review `solune/backend/src/services/signal_bridge.py`, `solune/backend/src/services/signal_chat.py`, and `solune/backend/src/services/signal_delivery.py` for command injection in external service calls

### Frontend Security

- [ ] T028 [P] [US1] Review `solune/frontend/src/services/api.ts` and `solune/frontend/src/services/*.ts` for insecure API calls, missing auth headers, token exposure in URLs, and XSS vectors
- [ ] T029 [P] [US1] Review `solune/frontend/src/components/auth/` for auth state leaks, insecure token storage in localStorage/sessionStorage, and improper redirect handling

### Security Regression Tests

- [ ] T030 [US1] Add regression tests in `solune/backend/tests/unit/` for each confirmed security fix — one test per vulnerability ensuring the fix prevents the attack vector
- [ ] T031 [US1] Run full backend validation: `cd solune/backend && pytest --timeout=60 && ruff check src tests && bandit -r src/`

### Security: Ambiguous Issue Documentation

- [ ] T032 [US1] For any ambiguous security findings, add `# TODO(bug-bash):` comments at relevant locations describing the issue, options, and rationale per FR-007

**Checkpoint**: All security vulnerabilities are fixed with regression tests, or flagged as TODOs. `pytest`, `ruff`, and `bandit` all pass.

---

## Phase 4: User Story 2 — Runtime Error Identification & Resolution (Priority: P2)

**Goal**: Audit every file for unhandled exceptions, race conditions, null/None references, missing imports, type errors, file handle leaks, and database connection leaks. Fix confirmed errors and add regression tests.

**Independent Test**: Run `pytest --timeout=60` + `pyright src` — all pass with zero type errors and all new regression tests green.

### Backend Runtime: Resource Management

- [ ] T033 [US2] Review `solune/backend/src/services/database.py` for database connection leaks in error paths, missing context managers, and unclosed connections on exception
- [ ] T034 [US2] Review `solune/backend/src/services/pipeline_state_store.py` for connection leaks, race conditions in cache operations, and missing error handling in async persistence
- [ ] T035 [P] [US2] Review `solune/backend/src/services/settings_store.py` for cache invalidation race conditions, connection leaks, and missing error handling in TTL cache
- [ ] T036 [P] [US2] Review `solune/backend/src/services/chat_store.py` for database connection leaks and unhandled exceptions in chat message persistence
- [ ] T037 [P] [US2] Review `solune/backend/src/services/done_items_store.py` for connection handling issues and missing error paths
- [ ] T038 [P] [US2] Review `solune/backend/src/services/mcp_store.py` for resource leaks and unhandled exceptions

### Backend Runtime: Exception Handling

- [ ] T039 [US2] Review `solune/backend/src/main.py` for unhandled exceptions in lifespan startup/shutdown, missing error handling in route registration, and global exception handlers
- [ ] T040 [US2] Review `solune/backend/src/services/copilot_polling/polling_loop.py` for unhandled exceptions in async polling loop, missing recovery from transient errors, and resource cleanup on shutdown
- [ ] T041 [P] [US2] Review `solune/backend/src/services/copilot_polling/pipeline.py` for unhandled exceptions in pipeline processing and missing null checks
- [ ] T042 [P] [US2] Review `solune/backend/src/services/copilot_polling/recovery.py` for error handling gaps in recovery logic and race conditions
- [ ] T043 [P] [US2] Review `solune/backend/src/services/copilot_polling/state.py` and `solune/backend/src/services/copilot_polling/state_validation.py` for null reference errors and missing state validation
- [ ] T044 [P] [US2] Review `solune/backend/src/services/workflow_orchestrator/orchestrator.py` and `solune/backend/src/services/workflow_orchestrator/transitions.py` for unhandled state transition exceptions and race conditions

### Backend Runtime: Null/None References & Type Errors

- [ ] T045 [US2] Review `solune/backend/src/services/github_projects/service.py` and all submodules (`agents.py`, `board.py`, `branches.py`, `copilot.py`, `identities.py`, `issues.py`, `projects.py`, `pull_requests.py`, `repository.py`) for None reference errors on API responses and missing optional field handling
- [ ] T046 [P] [US2] Review `solune/backend/src/services/ai_agent.py` and `solune/backend/src/services/completion_providers.py` for unhandled exceptions from external AI API calls and missing None checks on responses
- [ ] T047 [P] [US2] Review `solune/backend/src/services/app_service.py` for null reference errors and unhandled exceptions
- [ ] T048 [P] [US2] Review `solune/backend/src/services/guard_service.py` for missing null checks and unhandled error paths
- [ ] T049 [P] [US2] Review `solune/backend/src/services/activity_logger.py`, `solune/backend/src/services/alert_dispatcher.py`, and `solune/backend/src/services/task_registry.py` for fire-and-forget task error handling and missing exception propagation

### Frontend Runtime

- [ ] T050 [P] [US2] Review `solune/frontend/src/hooks/*.ts` (106 files) for unhandled promise rejections, missing error boundaries, null reference errors on API responses, and missing loading state handling
- [ ] T051 [P] [US2] Review `solune/frontend/src/services/api.ts` and related service files for unhandled HTTP errors, missing response type validation, and race conditions in concurrent requests
- [ ] T052 [P] [US2] Review `solune/frontend/src/components/common/ErrorBoundary.tsx` and error handling utilities in `solune/frontend/src/utils/errorHints.ts` for missing error categories and unhandled edge cases

### Runtime Regression Tests

- [ ] T053 [US2] Add regression tests in `solune/backend/tests/unit/` for each confirmed runtime error fix — one test per error path exercising the corrected exception handling or resource cleanup
- [ ] T054 [US2] Run full backend validation: `cd solune/backend && pytest --timeout=60 && pyright src`

### Runtime: Ambiguous Issue Documentation

- [ ] T055 [US2] For any ambiguous runtime findings, add `# TODO(bug-bash):` comments at relevant locations describing the issue, options, and rationale per FR-007

**Checkpoint**: All runtime errors are fixed with regression tests, or flagged as TODOs. `pytest` and `pyright` pass.

---

## Phase 5: User Story 3 — Logic Bug Detection & Resolution (Priority: P3)

**Goal**: Audit every file for incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, and incorrect return values. Fix confirmed logic bugs and add regression tests.

**Independent Test**: Run `pytest --timeout=60` + `vitest run` — all pass with regression tests validating corrected logic.

### Backend Logic: State Machines & Workflows

- [ ] T056 [US3] Review `solune/backend/src/services/workflow_orchestrator/orchestrator.py` for incorrect state transitions, missing transition guards, and wrong state values
- [ ] T057 [US3] Review `solune/backend/src/services/workflow_orchestrator/transitions.py` for incorrect state persistence, wrong cache update logic, and missing state validation
- [ ] T058 [US3] Review `solune/backend/src/services/workflow_orchestrator/models.py` and `solune/backend/src/services/workflow_orchestrator/config.py` for incorrect state enums, wrong defaults, and inconsistent configuration
- [ ] T059 [US3] Review `solune/backend/src/services/copilot_polling/pipeline.py` and `solune/backend/src/services/copilot_polling/completion.py` for incorrect pipeline stage logic, wrong completion detection, and off-by-one in retry counts
- [ ] T060 [P] [US3] Review `solune/backend/src/services/copilot_polling/label_manager.py` for incorrect label state transitions and wrong label matching logic
- [ ] T061 [P] [US3] Review `solune/backend/src/services/copilot_polling/agent_output.py` and `solune/backend/src/services/copilot_polling/helpers.py` for incorrect output parsing and wrong helper logic

### Backend Logic: API Handlers & Services

- [ ] T062 [US3] Review `solune/backend/src/api/workflow.py` for incorrect API response construction, wrong status codes, broken control flow, and incorrect return values
- [ ] T063 [US3] Review `solune/backend/src/api/pipelines.py` for incorrect pipeline API logic, wrong filtering, and data inconsistencies
- [ ] T064 [P] [US3] Review `solune/backend/src/api/chat.py` for incorrect chat message handling, wrong ordering, and broken pagination logic
- [ ] T065 [P] [US3] Review `solune/backend/src/api/board.py` for incorrect board state management, wrong item ordering, and data inconsistencies
- [ ] T066 [P] [US3] Review `solune/backend/src/api/chores.py` for incorrect chore scheduling logic, wrong template resolution, and broken CRUD operations
- [ ] T067 [P] [US3] Review `solune/backend/src/api/projects.py` and `solune/backend/src/api/apps.py` for incorrect project/app management logic and wrong return values
- [ ] T068 [P] [US3] Review `solune/backend/src/api/webhooks.py` and `solune/backend/src/api/webhook_models.py` for incorrect webhook event handling, wrong payload parsing, and missed events
- [ ] T069 [P] [US3] Review `solune/backend/src/api/agents.py` and `solune/backend/src/api/tools.py` for incorrect agent/tool management logic

### Backend Logic: Core Services

- [ ] T070 [US3] Review `solune/backend/src/services/pipelines/service.py` for incorrect pipeline creation/update logic, wrong status calculations, and data inconsistencies
- [ ] T071 [P] [US3] Review `solune/backend/src/services/chores/service.py`, `solune/backend/src/services/chores/scheduler.py`, and `solune/backend/src/services/chores/counter.py` for incorrect scheduling logic, wrong counter increments, and off-by-one errors
- [ ] T072 [P] [US3] Review `solune/backend/src/services/agents/service.py` and `solune/backend/src/services/agents/agent_mcp_sync.py` for incorrect agent sync logic and wrong MCP configuration
- [ ] T073 [P] [US3] Review `solune/backend/src/services/github_projects/graphql.py` for incorrect GraphQL query construction and wrong response parsing
- [ ] T074 [P] [US3] Review `solune/backend/src/utils.py` and `solune/backend/src/constants.py` for incorrect utility function logic, wrong constants, and off-by-one errors
- [ ] T075 [P] [US3] Review `solune/backend/src/services/pagination.py` for off-by-one errors in page calculation, incorrect boundary handling, and wrong total count

### Frontend Logic

- [ ] T076 [P] [US3] Review `solune/frontend/src/services/api.ts` for incorrect API call parameters, wrong URL construction, and broken request/response mapping
- [ ] T077 [P] [US3] Review `solune/frontend/src/hooks/` for incorrect React hook logic — wrong dependency arrays in useEffect, stale closures, incorrect memoization, and broken optimistic updates
- [ ] T078 [P] [US3] Review `solune/frontend/src/components/board/` for incorrect drag-and-drop logic, wrong item ordering, and broken state management
- [ ] T079 [P] [US3] Review `solune/frontend/src/components/pipeline/` for incorrect pipeline visualization logic, wrong stage status display, and broken progress calculations
- [ ] T080 [P] [US3] Review `solune/frontend/src/lib/` (25 files) for incorrect utility logic, wrong calculations, and broken helper functions

### Logic Regression Tests

- [ ] T081 [US3] Add regression tests in `solune/backend/tests/unit/` for each confirmed logic bug fix — one test per bug with assertions that would fail on the original code
- [ ] T082 [US3] Run full validation: `cd solune/backend && pytest --timeout=60` and `cd solune/frontend && npm run test`

### Logic: Ambiguous Issue Documentation

- [ ] T083 [US3] For any ambiguous logic findings, add `# TODO(bug-bash):` comments at relevant locations describing the issue, options, and rationale per FR-007

**Checkpoint**: All logic bugs are fixed with regression tests, or flagged as TODOs. `pytest` and `vitest` pass.

---

## Phase 6: User Story 6 — Ambiguous Issue Documentation (Priority: P3)

**Goal**: Review all `TODO(bug-bash)` comments added during Phases 3–5 for completeness. Ensure each documents the issue, available options, and rationale for deferral.

**Independent Test**: Search the codebase for `TODO(bug-bash)` and verify each comment includes: issue description, available options, and rationale.

- [ ] T084 [US6] Search all files for `TODO(bug-bash)` comments added during previous phases and validate each one includes: (1) issue description, (2) available options, (3) rationale for deferral
- [ ] T085 [US6] For any incomplete `TODO(bug-bash)` comments, update them to include all required fields per FR-007
- [ ] T086 [US6] Verify no `TODO(bug-bash)` comment was placed where the fix was actually obvious — move any such items back to their respective phase for fixing

**Checkpoint**: All `TODO(bug-bash)` comments are complete and well-documented.

---

## Phase 7: User Story 4 — Test Gap & Test Quality Improvement (Priority: P4)

**Goal**: Review existing tests for mock leaks, dead assertions, tests that pass for the wrong reason, untested code paths, and missing edge case coverage. Fix test quality issues and add missing tests.

**Independent Test**: Run `pytest --cov=src --cov-report=term-missing --timeout=60` and `vitest run --coverage` — all tests pass, coverage increases, and no mock leaks remain.

### Backend Test Quality: Mock Leaks

- [ ] T087 [US4] Search `solune/backend/tests/` for `MagicMock` usage in file paths, database paths, or production code paths — fix any mock objects that leak into runtime behavior
- [ ] T088 [P] [US4] Review `solune/backend/tests/conftest.py` for mock scope issues, missing cleanup, incorrect fixture teardown, and autouse fixtures that may interfere with test isolation
- [ ] T089 [P] [US4] Review `solune/backend/tests/unit/test_main.py` for incomplete mock settings (missing observability fields), incorrect lifespan mock setup, and wrong mock targets

### Backend Test Quality: Dead Assertions & Wrong Mocks

- [ ] T090 [US4] Search `solune/backend/tests/unit/` (142 files) for dead assertions: `assert True`, `assert mock.called` without call_args verification, assertions on constants, and assertions that can never fail
- [ ] T091 [US4] Search `solune/backend/tests/unit/` for incorrect mock targets — function-level imports must be patched at the source module, not the consuming module (e.g., `src.services.settings_store.is_queue_mode_enabled` not `src.api.pipelines.is_queue_mode_enabled`)
- [ ] T092 [P] [US4] Review `solune/backend/tests/property/` (9 files) for incorrect property test strategies, missing shrinking, and weak property assertions
- [ ] T093 [P] [US4] Review `solune/backend/tests/integration/` (16 files) for test isolation issues, shared state between tests, and incorrect setup/teardown

### Backend Test Quality: Coverage Gaps

- [ ] T094 [US4] Run `cd solune/backend && pytest --cov=src --cov-report=term-missing --timeout=60` and identify critical untested code paths in `src/api/`, `src/services/`, and `src/middleware/`
- [ ] T095 [US4] Add tests for identified critical untested paths — prioritize error handling paths, edge cases, and boundary conditions in the most important modules

### Frontend Test Quality

- [ ] T096 [P] [US4] Review `solune/frontend/src/**/*.test.{ts,tsx}` for dead assertions, incorrect mock setups, and tests that pass regardless of implementation
- [ ] T097 [P] [US4] Review `solune/frontend/src/test/` test utilities for incorrect factory functions, stale mock data, and missing test helpers
- [ ] T098 [P] [US4] Run `cd solune/frontend && npm run test:coverage` and identify critical untested hooks and components

### Test Quality Fixes

- [ ] T099 [US4] Fix all identified mock leaks, dead assertions, and incorrect mock targets in backend tests
- [ ] T100 [US4] Fix all identified test quality issues in frontend tests
- [ ] T101 [US4] Run full validation: `cd solune/backend && pytest --timeout=60` and `cd solune/frontend && npm run test`

**Checkpoint**: Test quality improved — mock leaks fixed, dead assertions replaced, coverage increased. Full test suite passes.

---

## Phase 8: User Story 5 — Code Quality Issue Resolution (Priority: P5)

**Goal**: Review the codebase for dead code, unreachable branches, duplicated logic, hardcoded values that should be configurable, missing error messages, and silent failures. Fix obvious issues; flag ambiguous trade-offs.

**Independent Test**: Run `ruff check src tests` + `eslint` — all pass. Full test suite passes with no regressions from dead code removal.

### Backend Code Quality: Dead Code & Unreachable Branches

- [ ] T102 [P] [US5] Review `solune/backend/src/api/*.py` (21 files) for dead code, unreachable branches after early returns, unused imports, and unused variables
- [ ] T103 [P] [US5] Review `solune/backend/src/services/*.py` (top-level, ~30 files) for dead code, unused functions, and unreachable error handlers
- [ ] T104 [P] [US5] Review `solune/backend/src/services/copilot_polling/*.py` (11 files) for dead code and unreachable branches in polling logic
- [ ] T105 [P] [US5] Review `solune/backend/src/services/github_projects/*.py` (13 files) for dead code and unused GraphQL fragments
- [ ] T106 [P] [US5] Review `solune/backend/src/models/*.py` (25 files) for unused model fields, dead validation logic, and unreachable model methods

### Backend Code Quality: Silent Failures & Missing Error Messages

- [ ] T107 [US5] Search `solune/backend/src/` for bare `except:` and `except Exception:` blocks without logging — add appropriate error logging or re-raise
- [ ] T108 [P] [US5] Review `solune/backend/src/services/` for silent `pass` in except blocks, swallowed exceptions, and missing error context in error messages

### Backend Code Quality: Hardcoded Values & Duplication

- [ ] T109 [P] [US5] Review `solune/backend/src/config.py` and `solune/backend/src/constants.py` for magic numbers, hardcoded URLs, and values that should be environment-configurable
- [ ] T110 [P] [US5] Review `solune/backend/src/api/*.py` for duplicated validation logic, repeated error handling patterns, and copy-paste code across endpoint handlers
- [ ] T111 [P] [US5] Review `solune/backend/src/services/` for duplicated utility patterns and repeated database query constructions

### Frontend Code Quality

- [ ] T112 [P] [US5] Review `solune/frontend/src/components/` for dead components (never imported), unreachable code paths, and unused props
- [ ] T113 [P] [US5] Review `solune/frontend/src/hooks/` for dead hooks (never imported), duplicated hook logic, and hooks with hardcoded values
- [ ] T114 [P] [US5] Review `solune/frontend/src/utils/` and `solune/frontend/src/lib/` for dead utility functions, duplicated logic, and hardcoded values
- [ ] T115 [P] [US5] Review `solune/frontend/src/services/` for dead API methods, duplicated request patterns, and hardcoded API paths

### Code Quality Fixes

- [ ] T116 [US5] Apply all confirmed code quality fixes (dead code removal, logging additions, value externalization) across backend and frontend
- [ ] T117 [US5] Run full validation: `cd solune/backend && ruff check src tests && pytest --timeout=60` and `cd solune/frontend && npm run lint && npm run test`

### Code Quality: Ambiguous Issue Documentation

- [ ] T118 [US5] For any ambiguous code quality findings (e.g., removing code that might be used in unreleased features), add `# TODO(bug-bash):` comments per FR-007

**Checkpoint**: Code quality issues fixed where obvious, flagged where ambiguous. All linters and tests pass.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary report generation, and cross-cutting quality checks

- [ ] T119 Run full backend validation suite: `cd solune/backend && ruff check src tests && ruff format --check src tests && pyright src && bandit -r src/ && pytest --timeout=60`
- [ ] T120 Run full frontend validation suite: `cd solune/frontend && npm run lint && npm run type-check && npm run test && npm run build`
- [ ] T121 Generate summary report table with all findings: number, file, line(s), category, description, and status (✅ Fixed or ⚠️ Flagged) per FR-011
- [ ] T122 Verify no new dependencies were introduced — compare `pyproject.toml` and `package.json` with baseline per FR-008
- [ ] T123 Verify no public API surface changes — diff all `api/*.py` route decorators and endpoint signatures per FR-002
- [ ] T124 Verify all commit messages follow format: `fix(<category>): <what> — <why> — <how>` with regression test reference per FR-004
- [ ] T125 Run quickstart.md validation steps to confirm end-to-end workflow works
- [ ] T126 Final review of all `TODO(bug-bash)` comments for completeness and accuracy

**Checkpoint**: All phases complete. Summary report generated. Full test suite passes. No new dependencies. No API changes. All findings documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user story phases
- **US1: Security (Phase 3)**: Depends on Foundational — highest priority, execute first
- **US2: Runtime (Phase 4)**: Depends on Foundational — can start after US1 or in parallel if different files
- **US3: Logic (Phase 5)**: Depends on Foundational — can start after US2 or in parallel if different files
- **US6: Ambiguous Docs (Phase 6)**: Depends on Phases 3–5 — validates all TODO comments
- **US4: Test Quality (Phase 7)**: Depends on Phases 3–5 — reviews tests after fixes are applied
- **US5: Code Quality (Phase 8)**: Depends on Phases 3–5 — reviews code after fixes are applied
- **Polish (Phase 9)**: Depends on all previous phases — final validation and reporting

### User Story Dependencies

- **US1 (Security, P1)**: Can start after Phase 2. RECOMMENDED to complete first — security fixes may affect other phases.
- **US2 (Runtime, P2)**: Can start after Phase 2. May overlap with US1 on different files.
- **US3 (Logic, P3)**: Can start after Phase 2. May overlap with US1/US2 on different files.
- **US6 (Ambiguous, P3)**: Depends on US1+US2+US3 — validates documentation completeness.
- **US4 (Test Quality, P4)**: Should run after US1+US2+US3 — needs stable codebase to review tests against.
- **US5 (Code Quality, P5)**: Should run after US1+US2+US3 — needs stable codebase to identify dead code.

### Within Each User Story

- Automated tool findings (from Phase 2) guide manual review priorities
- Review configuration files before implementation files
- Review core services before API endpoints
- Review backend before frontend (backend has more critical surface)
- Fix bugs before adding regression tests
- Run validation suite after all fixes in a phase
- Document ambiguous findings with TODO comments as they are discovered

### Parallel Opportunities

- **Phase 1**: T003, T004, T005, T006 can all run in parallel (different projects/tools)
- **Phase 2**: T009, T010, T011 can run in parallel (different tools/projects)
- **Phase 3 (US1)**: Middleware reviews (T020–T023) can run in parallel; model/signal reviews (T026–T027) in parallel; frontend security (T028–T029) in parallel
- **Phase 4 (US2)**: Resource reviews (T035–T038) can run in parallel; exception reviews (T041–T044) can run in parallel; frontend (T050–T052) in parallel
- **Phase 5 (US3)**: Polling reviews (T060–T061) in parallel; API reviews (T064–T069) in parallel; frontend (T076–T080) in parallel
- **Phase 7 (US4)**: Mock reviews (T088–T089) in parallel; property/integration reviews (T092–T093) in parallel; frontend (T096–T098) in parallel
- **Phase 8 (US5)**: All code quality reviews (T102–T106) can run in parallel; frontend reviews (T112–T115) in parallel

---

## Parallel Example: User Story 1 (Security)

```bash
# Parallel: Middleware security reviews (different files, no dependencies)
Task T020: "Review csrf.py for CSRF protection bypasses"
Task T021: "Review admin_guard.py for authorization bypasses"
Task T022: "Review csp.py for overly permissive CSP"
Task T023: "Review rate_limit.py for rate limit bypasses"

# Parallel: Model and signal reviews (different files, no dependencies)
Task T026: "Review models/*.py for missing validators"
Task T027: "Review signal_bridge.py, signal_chat.py, signal_delivery.py"

# Parallel: Frontend security (different project from backend)
Task T028: "Review frontend api.ts for insecure API calls"
Task T029: "Review frontend auth components for token leaks"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — establish baseline
2. Complete Phase 2: Foundational — run all automated scanners
3. Complete Phase 3: User Story 1 (Security) — fix all security vulnerabilities
4. **STOP and VALIDATE**: Run full test suite + security scanners
5. Security hardening delivered as first increment

### Incremental Delivery

1. Setup + Foundational → Baseline established, automated findings triaged
2. Add US1 (Security) → Test independently → Security hardened (**MVP!**)
3. Add US2 (Runtime) → Test independently → Runtime stability improved
4. Add US3 (Logic) → Test independently → Correctness verified
5. Add US6 (Ambiguous) → Validate documentation → All trade-offs documented
6. Add US4 (Test Quality) → Test independently → Test suite reliability improved
7. Add US5 (Code Quality) → Test independently → Maintainability improved
8. Polish → Final validation → Summary report generated
9. Each phase adds value without breaking previous phases

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Security) — backend focus
   - Developer B: US1 (Security) — frontend focus
3. After US1 complete:
   - Developer A: US2 (Runtime errors)
   - Developer B: US3 (Logic bugs)
4. After US2+US3 complete:
   - Developer A: US4 (Test quality)
   - Developer B: US5 (Code quality)
5. Team completes US6 (Ambiguous) + Polish together

---

## Notes

- [P] tasks = different files, no dependencies on other tasks in the same phase
- [Story] label maps task to specific user story for traceability
- Each user story corresponds to one bug category (US1=Security, US2=Runtime, US3=Logic, US4=Test Quality, US5=Code Quality, US6=Ambiguous)
- Tests are MANDATORY per FR-003 — each fix gets at least one regression test
- Validation runs after each phase — never commit while tests fail (FR-005)
- Commit format: `fix(<category>): <description>` with regression test reference
- Total scope: ~152 Python backend files + ~406 TypeScript/TSX frontend files + ~190 backend test files + ~151 frontend test files
- Ambiguous findings get `# TODO(bug-bash):` comments — do NOT fix trade-off decisions
- No new dependencies (FR-008), no API changes (FR-002), no architecture changes
