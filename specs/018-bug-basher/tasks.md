# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/018-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Regression tests are REQUIRED for each bug fix per FR-004. Each fix must include at least one new regression test.

**Organization**: Tasks are grouped by user story (bug category) to enable independent auditing and fixing per category. Within each story, tasks target specific codebase areas (backend, frontend, scripts, config) for focused review.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/`
- **Frontend tests**: co-located `*.test.tsx` files
- **Scripts**: `scripts/`
- **Config**: root-level config files

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline, validate existing test suite, and prepare tracking infrastructure

- [x] T001 Run full backend test suite via `cd backend && python -m pytest` to establish baseline pass/fail state
- [x] T002 [P] Run backend linting via `cd backend && ruff check src/ tests/` and formatting via `ruff format --check src/ tests/` to establish baseline
- [ ] T003 [P] Run backend type checking via `cd backend && pyright` to establish baseline
- [x] T004 [P] Run frontend linting via `cd frontend && npx eslint src/` to establish baseline
- [x] T005 [P] Run frontend type checking via `cd frontend && npx tsc --noEmit` to establish baseline
- [x] T006 [P] Run frontend test suite via `cd frontend && npx vitest run` to establish baseline
- [x] T007 Create bug tracking summary table template at the end of the final commit message for structured output per FR-010

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Generate file inventory per audit area. These inventories inform all user story phases.

**⚠️ CRITICAL**: Inventory and baseline must be complete before audit work begins.

- [x] T008 Inventory all backend source files in backend/src/ (86 Python files across api/, models/, services/, middleware/, prompts/, and root modules)
- [x] T009 [P] Inventory all backend test files in backend/tests/ (59 test files across unit/, integration/, helpers/)
- [x] T010 [P] Inventory all frontend source files in frontend/src/ (120+ TypeScript files across components/, hooks/, services/, types/, lib/, utils/)
- [x] T011 [P] Inventory all configuration files (.env.example, docker-compose.yml, backend/pyproject.toml, frontend/package.json, frontend/vitest.config.ts, frontend/eslint.config.js, .pre-commit-config.yaml)
- [x] T012 [P] Inventory all script files in scripts/ (setup-hooks.sh, pre-commit)

**Checkpoint**: All baselines established and file inventories complete — audit work can now begin

---

## Phase 3: User Story 1 — Security Vulnerability Audit (Priority: P1) 🎯 MVP

**Goal**: Identify and fix all security vulnerabilities including auth bypasses, injection risks, exposed secrets, insecure defaults, and improper input validation across the entire codebase.

**Independent Test**: Run full test suite after fixes. Verify no secrets in code/config. Confirm input validation and auth checks pass. Run `ruff check` and `pyright` clean.

### Backend Auth & Config Security

- [ ] T013 [P] [US1] Audit authentication logic in backend/src/services/github_auth.py for auth bypass risks, token handling, and session security
- [ ] T014 [P] [US1] Audit auth API endpoint in backend/src/api/auth.py for improper authentication flows, missing validation, and insecure redirects
- [ ] T015 [P] [US1] Audit session management in backend/src/services/session_store.py for session fixation, insecure storage, and missing expiry
- [ ] T016 [P] [US1] Audit encryption service in backend/src/services/encryption.py for weak algorithms, hardcoded keys, and improper IV handling
- [x] T017 [P] [US1] Audit configuration in backend/src/config.py for exposed secrets, insecure defaults (debug mode, permissive CORS), and missing validation
- [x] T018 [P] [US1] Audit environment template in .env.example for accidentally committed real secrets or tokens

### Backend Input Validation & Injection

- [ ] T019 [P] [US1] Audit webhook endpoint in backend/src/api/webhooks.py for missing signature verification, payload injection, and improper input handling
- [ ] T020 [P] [US1] Audit chat API in backend/src/api/chat.py for prompt injection, missing input sanitization, and unsafe message handling
- [ ] T021 [P] [US1] Audit tasks API in backend/src/api/tasks.py for injection risks in task creation and missing input validation
- [ ] T022 [P] [US1] Audit agents API in backend/src/api/agents.py for improper agent configuration validation and command injection risks
- [ ] T023 [P] [US1] Audit board API in backend/src/api/board.py for missing authorization checks and input validation on project board operations
- [ ] T024 [P] [US1] Audit workflow API in backend/src/api/workflow.py for missing authorization and unsafe workflow execution
- [ ] T025 [P] [US1] Audit projects API in backend/src/api/projects.py for missing authorization checks on project access
- [ ] T026 [P] [US1] Audit settings API in backend/src/api/settings.py for sensitive data exposure and missing access controls
- [ ] T027 [P] [US1] Audit MCP API in backend/src/api/mcp.py for insecure MCP server configuration and missing validation
- [ ] T028 [P] [US1] Audit cleanup API in backend/src/api/cleanup.py for unsafe deletion operations and missing authorization
- [ ] T029 [P] [US1] Audit signal API in backend/src/api/signal.py for improper signal handling and missing validation

### Backend Services Security

- [ ] T030 [P] [US1] Audit database service in backend/src/services/database.py for SQL injection risks, unsafe query construction, and connection security
- [ ] T031 [P] [US1] Audit AI agent service in backend/src/services/ai_agent.py for prompt injection, unsafe prompt construction, and API key exposure
- [ ] T032 [P] [US1] Audit completion providers in backend/src/services/completion_providers.py for API key handling and insecure provider configuration
- [ ] T033 [P] [US1] Audit cache service in backend/src/services/cache.py for cache poisoning, sensitive data in cache, and missing invalidation
- [x] T034 [P] [US1] Audit WebSocket service in backend/src/services/websocket.py for missing authentication on WebSocket connections and message injection
- [ ] T035 [P] [US1] Audit Copilot polling pipeline in backend/src/services/copilot_polling/ (5 files) for token exposure, insecure polling, and missing auth
- [ ] T036 [P] [US1] Audit workflow orchestrator in backend/src/services/workflow_orchestrator/ (4 files) for unsafe workflow execution and privilege escalation
- [ ] T037 [P] [US1] Audit GitHub Projects integration in backend/src/services/github_projects/ (3 files) for GraphQL injection and token mishandling
- [ ] T038 [P] [US1] Audit MCP store in backend/src/services/mcp_store.py for insecure server storage and missing validation
- [ ] T039 [P] [US1] Audit signal services in backend/src/services/signal_bridge.py, signal_chat.py, signal_delivery.py for insecure message handling

### Frontend Security

- [ ] T040 [P] [US1] Audit frontend API client in frontend/src/services/api.ts for token exposure, insecure storage, missing CSRF protection, and unsafe URL construction
- [ ] T041 [P] [US1] Audit frontend auth components in frontend/src/components/auth/ for XSS risks, token handling in DOM, and insecure redirect handling
- [ ] T042 [P] [US1] Audit chat components in frontend/src/components/chat/ for XSS via message rendering, unsafe innerHTML, and missing input sanitization
- [ ] T043 [P] [US1] Audit settings components in frontend/src/components/settings/ for sensitive data display and insecure form handling

### Config & Infrastructure Security

- [x] T044 [P] [US1] Audit docker-compose.yml for exposed ports, missing network isolation, insecure volume mounts, and hardcoded credentials
- [ ] T045 [P] [US1] Audit .pre-commit-config.yaml and scripts/pre-commit for insecure hook execution and missing security checks
- [x] T046 [US1] Add regression tests for all security fixes in backend/tests/unit/ and co-located frontend test files per FR-004

**Checkpoint**: All security vulnerabilities identified and either fixed with regression tests or flagged with `# TODO(bug-bash):` comments

---

## Phase 4: User Story 2 — Runtime Error Detection and Fix (Priority: P1)

**Goal**: Identify and fix all runtime errors including unhandled exceptions, null/None references, missing imports, type errors, file handle leaks, and database connection leaks.

**Independent Test**: Run full test suite after fixes. Verify all exception handling paths are covered. Confirm resource cleanup occurs correctly in success and error paths.

### Backend Exception Handling

- [ ] T047 [P] [US2] Audit exception handling in backend/src/main.py for unhandled startup/shutdown errors and missing global exception handlers
- [ ] T048 [P] [US2] Audit custom exceptions in backend/src/exceptions.py for incomplete exception hierarchy and missing error context
- [ ] T049 [P] [US2] Audit dependencies module in backend/src/dependencies.py for unhandled dependency resolution errors and missing null checks
- [ ] T050 [P] [US2] Audit middleware in backend/src/middleware/request_id.py for unhandled middleware errors and missing error propagation

### Backend Service Runtime Errors

- [x] T051 [P] [US2] Audit database service in backend/src/services/database.py for connection leaks, unhandled query errors, and missing context managers
- [ ] T052 [P] [US2] Audit AI agent service in backend/src/services/ai_agent.py for unhandled API call failures, timeout errors, and missing retry logic
- [ ] T053 [P] [US2] Audit completion providers in backend/src/services/completion_providers.py for unhandled provider errors and missing fallback handling
- [ ] T054 [P] [US2] Audit cache service in backend/src/services/cache.py for unhandled cache errors and missing null checks on cache reads
- [ ] T055 [P] [US2] Audit session store in backend/src/services/session_store.py for race conditions in session access and missing null checks
- [ ] T056 [P] [US2] Audit settings store in backend/src/services/settings_store.py for unhandled file I/O errors and missing default values
- [ ] T057 [P] [US2] Audit WebSocket service in backend/src/services/websocket.py for unhandled connection drops, race conditions in broadcast, and missing error recovery
- [ ] T058 [P] [US2] Audit model fetcher in backend/src/services/model_fetcher.py for unhandled API errors and missing timeout handling
- [ ] T059 [P] [US2] Audit cleanup service in backend/src/services/cleanup_service.py for unhandled cleanup errors and resource leaks during cleanup operations
- [ ] T060 [P] [US2] Audit agent tracking service in backend/src/services/agent_tracking.py for race conditions and unhandled tracking errors
- [ ] T061 [P] [US2] Audit agent creator service in backend/src/services/agent_creator.py for unhandled creation errors and missing validation
- [ ] T062 [P] [US2] Audit Copilot polling pipeline in backend/src/services/copilot_polling/ for unhandled polling errors, timeout issues, and missing retry mechanisms
- [ ] T063 [P] [US2] Audit workflow orchestrator in backend/src/services/workflow_orchestrator/ for unhandled orchestration errors and state corruption on failure
- [ ] T064 [P] [US2] Audit GitHub Projects services in backend/src/services/github_projects/ for unhandled GraphQL errors and rate limit handling
- [ ] T065 [P] [US2] Audit chores services in backend/src/services/chores/ (4 files) for scheduler errors, missed triggers, and unhandled timer failures
- [ ] T066 [P] [US2] Audit signal services (signal_bridge.py, signal_chat.py, signal_delivery.py) for unhandled message delivery failures and connection drops

### Backend API Endpoint Runtime Errors

- [ ] T067 [P] [US2] Audit health endpoint in backend/src/api/health.py for unhandled health check failures and missing dependency checks
- [ ] T068 [P] [US2] Audit all API endpoints in backend/src/api/ (15 files) for missing try/except blocks, unhandled async errors, and incorrect HTTP status codes

### Backend Model & Import Errors

- [ ] T069 [P] [US2] Audit all models in backend/src/models/ (14 files) for missing imports, type errors in Pydantic validators, and incorrect field defaults
- [ ] T070 [P] [US2] Audit all imports across backend/src/ for missing, circular, or incorrect imports

### Frontend Runtime Errors

- [ ] T071 [P] [US2] Audit frontend hooks in frontend/src/hooks/ (25 files) for unhandled promise rejections, missing error states, and race conditions in async operations
- [ ] T072 [P] [US2] Audit frontend API client in frontend/src/services/api.ts for unhandled fetch errors, missing timeout handling, and incorrect error propagation
- [ ] T073 [P] [US2] Audit frontend ErrorBoundary in frontend/src/components/ErrorBoundary.tsx for incomplete error catching and missing recovery paths
- [ ] T074 [P] [US2] Audit frontend components in frontend/src/components/ for unhandled null/undefined props, missing loading states, and conditional rendering errors
- [ ] T075 [P] [US2] Audit frontend TypeScript types in frontend/src/types/index.ts for incorrect type definitions that could cause runtime type errors

### Regression Tests for Runtime Fixes

- [x] T076 [US2] Add regression tests for all runtime error fixes in backend/tests/unit/ and co-located frontend test files per FR-004

**Checkpoint**: All runtime errors identified and either fixed with regression tests or flagged with `# TODO(bug-bash):` comments

---

## Phase 5: User Story 3 — Logic Bug Identification and Correction (Priority: P2)

**Goal**: Identify and fix all logic bugs including incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, and incorrect return values.

**Independent Test**: Run full test suite after fixes. Verify correct return values for boundary conditions. Confirm state transitions follow expected paths.

### Backend Service Logic

- [x] T077 [P] [US3] Audit state management logic in backend/src/services/workflow_orchestrator/ for incorrect state transitions and broken workflow sequencing
- [ ] T078 [P] [US3] Audit Copilot polling pipeline logic in backend/src/services/copilot_polling/ for incorrect polling intervals, wrong status checks, and missed event handling
- [x] T079 [P] [US3] Audit chores scheduler logic in backend/src/services/chores/ for incorrect scheduling, missed triggers, and wrong time calculations
- [ ] T080 [P] [US3] Audit agent services in backend/src/services/agents/ and backend/src/services/agent_tracking.py for incorrect agent state management
- [ ] T081 [P] [US3] Audit AI agent service in backend/src/services/ai_agent.py for incorrect prompt construction, wrong API call parameters, and broken response parsing
- [ ] T082 [P] [US3] Audit cache service in backend/src/services/cache.py for incorrect TTL handling, wrong cache key construction, and stale data serving
- [ ] T083 [P] [US3] Audit cleanup service in backend/src/services/cleanup_service.py for incorrect cleanup logic, wrong selection criteria, and data loss risks
- [ ] T084 [P] [US3] Audit GitHub Projects integration in backend/src/services/github_projects/ for incorrect GraphQL query construction and wrong field mapping

### Backend API Logic

- [ ] T085 [P] [US3] Audit all API endpoints in backend/src/api/ (15 files) for incorrect HTTP methods, wrong response codes, broken pagination, and incorrect filter logic
- [ ] T086 [P] [US3] Audit backend/src/utils.py and backend/src/constants.py for incorrect utility function logic and wrong constant values

### Backend Model Logic

- [ ] T087 [P] [US3] Audit all models in backend/src/models/ (14 files) for incorrect validators, wrong default values, broken serialization, and data inconsistencies
- [ ] T088 [P] [US3] Audit prompt templates in backend/src/prompts/ for incorrect template variables, broken formatting, and wrong prompt logic

### Frontend Logic

- [ ] T089 [P] [US3] Audit frontend hooks in frontend/src/hooks/ (25 files) for incorrect state transitions, wrong optimistic updates, broken cache invalidation, and stale data
- [ ] T090 [P] [US3] Audit frontend command system in frontend/src/lib/commands/ for incorrect command parsing, wrong command routing, and broken command execution
- [ ] T091 [P] [US3] Audit frontend utility functions in frontend/src/utils/ (formatTime.ts, generateId.ts) for off-by-one errors and incorrect formatting logic
- [ ] T092 [P] [US3] Audit frontend board components in frontend/src/components/board/ for incorrect drag-and-drop logic, wrong column assignments, and broken issue state management
- [ ] T093 [P] [US3] Audit frontend chat components in frontend/src/components/chat/ for incorrect message ordering, wrong sender attribution, and broken message rendering logic

### Regression Tests for Logic Fixes

- [ ] T094 [US3] Add regression tests for all logic bug fixes in backend/tests/unit/ and co-located frontend test files per FR-004

**Checkpoint**: All logic bugs identified and either fixed with regression tests or flagged with `# TODO(bug-bash):` comments

---

## Phase 6: User Story 4 — Test Gap Analysis and Quality Improvement (Priority: P2)

**Goal**: Identify and fix test gaps and low-quality tests so the test suite provides reliable coverage and catches real bugs.

**Independent Test**: Run test suite with coverage analysis. Verify all new regression tests pass. Confirm mock objects do not leak into production code paths.

### Backend Test Quality

- [ ] T095 [P] [US4] Audit backend test configuration in backend/tests/conftest.py for missing fixtures, incorrect setup/teardown, and shared mutable state
- [ ] T096 [P] [US4] Audit backend test factories in backend/tests/helpers/factories.py for incorrect factory defaults, missing required fields, and MagicMock leaks into production paths
- [ ] T097 [P] [US4] Audit backend test mocks in backend/tests/helpers/mocks.py for MagicMock objects leaking into production code paths (e.g., file paths, database connections)
- [ ] T098 [P] [US4] Audit backend test assertions in backend/tests/helpers/assertions.py for assertions that can never fail and incomplete validation helpers
- [ ] T099 [P] [US4] Audit backend unit tests in backend/tests/unit/ (41 files) for tests passing for wrong reasons, missing edge cases, and weak assertions
- [ ] T100 [P] [US4] Audit backend integration tests in backend/tests/integration/ (3 files) for incomplete integration scenarios and missing failure path tests

### Backend Test Coverage Gaps

- [ ] T101 [P] [US4] Identify untested backend services by comparing backend/src/services/ (28 files) against backend/tests/unit/test_*.py for missing coverage
- [ ] T102 [P] [US4] Identify untested backend API endpoints by comparing backend/src/api/ (15 files) against backend/tests/unit/test_api_*.py for missing coverage
- [ ] T103 [P] [US4] Identify untested backend models by comparing backend/src/models/ (14 files) against backend/tests/unit/test_models*.py for missing coverage

### Frontend Test Quality

- [ ] T104 [P] [US4] Audit frontend test setup in frontend/src/test/ for incorrect mock configuration and missing cleanup
- [ ] T105 [P] [US4] Audit frontend hook tests in frontend/src/hooks/*.test.tsx (25+ files) for incomplete async testing, missing error state tests, and weak assertions
- [ ] T106 [P] [US4] Audit frontend component tests in frontend/src/components/**/*.test.tsx for missing interaction tests, incomplete rendering tests, and snapshot-only coverage

### Frontend Test Coverage Gaps

- [ ] T107 [P] [US4] Identify untested frontend components by comparing frontend/src/components/ against co-located *.test.tsx files for missing test coverage
- [ ] T108 [P] [US4] Identify untested frontend hooks by comparing frontend/src/hooks/*.ts against *.test.tsx files for missing hook test coverage
- [ ] T109 [P] [US4] Identify untested frontend utilities and services (frontend/src/utils/, frontend/src/services/api.ts, frontend/src/lib/) for missing test files

### Add Missing Tests

- [ ] T110 [US4] Add critical missing edge case tests for backend boundary conditions, empty inputs, and error paths in backend/tests/unit/
- [ ] T111 [P] [US4] Add critical missing edge case tests for frontend boundary conditions, empty inputs, and error paths in co-located test files
- [ ] T112 [US4] Fix all identified mock leaks, weak assertions, and tests passing for wrong reasons across both backend and frontend test suites

**Checkpoint**: Test quality improved — mock leaks fixed, weak assertions replaced, critical coverage gaps filled

---

## Phase 7: User Story 5 — Code Quality Cleanup (Priority: P3)

**Goal**: Clean up code quality issues including dead code, duplicated logic, hardcoded values, and silent failures.

**Independent Test**: Run linting checks. Verify dead code is removed. Confirm hardcoded values are extracted to configuration or constants.

### Backend Dead Code & Unused Imports

- [ ] T113 [P] [US5] Audit backend/src/ for dead code: unused functions, unreachable branches, and unused variables across all 86 source files
- [ ] T114 [P] [US5] Audit backend/src/ for unused imports across all Python files using ruff check --select F401

### Backend Duplicated Logic & Hardcoded Values

- [ ] T115 [P] [US5] Audit backend/src/services/ for duplicated logic patterns across the 28 service files (common patterns: error handling, database queries, API calls)
- [ ] T116 [P] [US5] Audit backend/src/api/ for duplicated endpoint patterns across 15 router files (common patterns: auth checks, request validation, response formatting)
- [ ] T117 [P] [US5] Audit backend/src/config.py and backend/src/constants.py for hardcoded values that should be configurable (URLs, timeouts, limits, magic numbers)
- [ ] T118 [P] [US5] Audit backend/src/ for hardcoded strings, magic numbers, and values that should be in constants.py or config.py

### Backend Silent Failures

- [x] T119 [P] [US5] Audit backend/src/services/ for silent failures: caught exceptions with no logging, bare except clauses, and swallowed errors
- [x] T120 [P] [US5] Audit backend/src/api/ for silent failures: empty error responses, missing error logging, and incorrect error status codes

### Frontend Dead Code & Unused Imports

- [ ] T121 [P] [US5] Audit frontend/src/ for dead code: unused components, unreachable branches, unused exports, and unused variables
- [ ] T122 [P] [US5] Audit frontend/src/ for unused imports across all TypeScript files using ESLint no-unused-vars

### Frontend Duplicated Logic & Hardcoded Values

- [ ] T123 [P] [US5] Audit frontend/src/hooks/ for duplicated logic patterns across 25 hook files (common patterns: fetch/cache/error handling)
- [ ] T124 [P] [US5] Audit frontend/src/components/ for duplicated component patterns and hardcoded values (URLs, timeouts, magic numbers)
- [ ] T125 [P] [US5] Audit frontend/src/services/api.ts for hardcoded API URLs, missing base URL configuration, and duplicated fetch patterns

### Frontend Silent Failures

- [ ] T126 [P] [US5] Audit frontend/src/ for silent failures: empty catch blocks, missing error toasts, and swallowed promise rejections

### Scripts & Config Quality

- [ ] T127 [P] [US5] Audit scripts/pre-commit and scripts/setup-hooks.sh for dead code, hardcoded paths, and silent failures
- [ ] T128 [P] [US5] Audit docker-compose.yml for unnecessary configurations, hardcoded values, and missing health checks

### Regression Tests for Quality Fixes

- [ ] T129 [US5] Add regression tests for code quality fixes that changed behavior (silent failures → logged errors, hardcoded → configurable) per FR-004

**Checkpoint**: Code quality issues cleaned up — dead code removed, duplications addressed, silent failures fixed

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cross-file regression checks, and summary generation

- [x] T130 Run full backend test suite via `cd backend && python -m pytest` to verify all fixes pass per FR-007
- [x] T131 [P] Run backend linting via `cd backend && ruff check src/ tests/` and formatting via `ruff format --check src/ tests/` per FR-008
- [ ] T132 [P] Run backend type checking via `cd backend && pyright` per FR-008
- [x] T133 [P] Run frontend test suite via `cd frontend && npx vitest run` to verify all fixes pass per FR-007
- [x] T134 [P] Run frontend linting via `cd frontend && npx eslint src/` per FR-008
- [x] T135 [P] Run frontend type checking via `cd frontend && npx tsc --noEmit` per FR-008
- [x] T136 Verify no fixes changed the project's public API surface per FR-011
- [x] T137 Verify no new dependencies were added per FR-012
- [x] T138 Generate final bug summary table per FR-010 with columns: #, File, Line(s), Category, Description, Status (✅ Fixed or ⚠️ Flagged)
- [x] T139 Write clear commit messages for each fix explaining: what the bug was, why it is a bug, and how the fix resolves it per FR-005

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — establishes baselines that inform all audits
- **US1: Security (Phase 3)**: Depends on Phase 2 — highest priority, MVP scope
- **US2: Runtime (Phase 4)**: Depends on Phase 2 — can run in parallel with US1 (different bug categories, different file sections)
- **US3: Logic (Phase 5)**: Depends on Phase 2 — can run in parallel with US1/US2 but benefits from security/runtime fixes being applied first
- **US4: Test Gaps (Phase 6)**: Depends on Phases 3-5 — test quality audit should happen after bug fixes to evaluate coverage of new code
- **US5: Code Quality (Phase 7)**: Depends on Phases 3-5 — dead code analysis is more accurate after bug fixes remove workarounds
- **Polish (Phase 8)**: Depends on ALL previous phases — final validation

### User Story Dependencies

- **US1 (P1) Security**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1) Runtime**: Can start after Phase 2 — Independent of US1 (different bug category)
- **US3 (P2) Logic**: Can start after Phase 2 — Independent but benefits from US1/US2 being done first
- **US4 (P2) Test Gaps**: Should follow US1-US3 — needs final code state to assess coverage accurately
- **US5 (P3) Code Quality**: Should follow US1-US3 — dead code analysis most accurate after fixes

### Within Each User Story

- Audit tasks within a story are all [P] (parallelizable by file/area)
- Regression test task depends on all audit/fix tasks in that story being complete
- Backend and frontend audits within same story can run in parallel

### Parallel Opportunities

- All Setup tasks (T001-T007) marked [P] can run in parallel (except T001 baseline)
- All Foundational inventory tasks (T008-T012) marked [P] can run in parallel
- Within US1: All backend auth tasks (T013-T018) can run in parallel, all injection tasks (T019-T029) in parallel, all service security tasks (T030-T039) in parallel, all frontend tasks (T040-T043) in parallel
- Within US2: All exception handling tasks in parallel, all service runtime tasks in parallel, all frontend tasks in parallel
- Within US3: All service logic tasks in parallel, all frontend logic tasks in parallel
- Within US4: All test quality audit tasks in parallel, all coverage gap tasks in parallel
- Within US5: All dead code tasks in parallel, all duplication tasks in parallel
- US1 and US2 can run fully in parallel (different bug categories on different file aspects)

---

## Parallel Example: User Story 1 (Security Audit)

```bash
# Launch all backend auth security audits together:
Task T013: "Audit authentication logic in backend/src/services/github_auth.py"
Task T014: "Audit auth API endpoint in backend/src/api/auth.py"
Task T015: "Audit session management in backend/src/services/session_store.py"
Task T016: "Audit encryption service in backend/src/services/encryption.py"
Task T017: "Audit configuration in backend/src/config.py"
Task T018: "Audit environment template in .env.example"

# Then launch all backend input validation audits together:
Task T019: "Audit webhook endpoint in backend/src/api/webhooks.py"
Task T020: "Audit chat API in backend/src/api/chat.py"
Task T021: "Audit tasks API in backend/src/api/tasks.py"
# ... (all T019-T029 in parallel)

# Launch all frontend security audits together:
Task T040: "Audit frontend API client in frontend/src/services/api.ts"
Task T041: "Audit frontend auth components"
Task T042: "Audit chat components"
Task T043: "Audit settings components"
```

---

## Parallel Example: User Story 2 (Runtime Errors)

```bash
# Launch all backend service runtime audits together:
Task T051: "Audit database service for connection leaks"
Task T052: "Audit AI agent service for unhandled failures"
Task T053: "Audit completion providers for unhandled errors"
# ... (all T051-T066 in parallel)

# Launch all frontend runtime audits together:
Task T071: "Audit frontend hooks for race conditions"
Task T072: "Audit API client for unhandled fetch errors"
Task T073: "Audit ErrorBoundary for incomplete catching"
```

---

## Implementation Strategy

### MVP First (User Story 1 — Security Only)

1. Complete Phase 1: Setup (establish baselines)
2. Complete Phase 2: Foundational (file inventories)
3. Complete Phase 3: User Story 1 — Security Vulnerability Audit
4. **STOP and VALIDATE**: Run full test suite, verify all security fixes pass, no regressions
5. Generate partial summary table with security findings only

### Incremental Delivery

1. Complete Setup + Foundational → Baselines established
2. Add US1: Security Audit → Test → Commit (MVP! Highest-risk bugs fixed)
3. Add US2: Runtime Errors → Test → Commit (Application stability improved)
4. Add US3: Logic Bugs → Test → Commit (Correctness improved)
5. Add US4: Test Gaps → Test → Commit (Safety net improved)
6. Add US5: Code Quality → Test → Commit (Maintainability improved)
7. Final validation + summary table → Complete
8. Each category adds value without breaking previous fixes

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Security) — backend focus
   - Developer B: US2 (Runtime) — backend focus
   - Developer C: US1 (Security) — frontend focus
   - Developer D: US2 (Runtime) — frontend focus
3. After US1/US2 complete:
   - Developer A: US3 (Logic)
   - Developer B: US4 (Test Gaps)
   - Developer C: US5 (Code Quality)
4. All converge for Phase 8: Polish & Final Validation

---

## Notes

- [P] tasks = different files/areas, no dependencies on each other
- [Story] label maps task to specific user story (bug category) for traceability
- Each user story/phase can be independently completed and validated
- Commit after each bug fix with descriptive message per FR-005
- Ambiguous issues get `# TODO(bug-bash):` comments per FR-006, NOT fixes
- Fixes must be minimal and focused — no drive-by refactors per FR-014
- Files with no bugs are skipped — not mentioned in summary per FR-015
- Run full test suite after each phase to catch cross-file regressions
- Total task count: 139 tasks across 8 phases
