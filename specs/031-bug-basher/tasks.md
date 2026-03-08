# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/031-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED — the spec (FR-004) mandates at least one regression test per bug fix.

**Organization**: Tasks are grouped by user story (bug category) to enable independent implementation and testing of each category.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`
- **Frontend tests**: Co-located `*.test.tsx` / `*.test.ts` files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify tooling, establish branch, confirm test suites pass before any changes

- [ ] T001 Install backend dev dependencies with `cd backend && pip install -e ".[dev]"`
- [ ] T002 [P] Install frontend dependencies with `cd frontend && npm install`
- [ ] T003 Run backend test suite baseline with `cd backend && python -m pytest tests/unit/ -v --tb=short` and record pass count
- [ ] T004 [P] Run frontend test suite baseline with `cd frontend && npx vitest run` and record pass count
- [ ] T005 [P] Run backend linting baseline with `cd backend && ruff check src/ tests/`
- [ ] T006 [P] Run frontend linting baseline with `cd frontend && npx eslint src/ && npx tsc --noEmit`
- [ ] T007 Verify existing `TODO(bug-bash):` comments from previous bug bash (030) are still present in `backend/src/services/signal_chat.py` lines 175-179, 538-541, 818-824 and `backend/src/main.py` lines 388-394 and `backend/src/services/database.py` lines 213-221

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish review tracking infrastructure and summary template that ALL user stories will use

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Create a summary tracking document at `/tmp/bug-bash-summary.md` using the schema from `specs/031-bug-basher/contracts/summary-table.md` with empty table ready to append entries
- [ ] T009 Identify full file inventory for audit: list all files under `backend/src/api/` (18 modules), `backend/src/services/` (49 modules), `backend/src/models/` (19 files), `backend/src/migrations/` (20 files), `backend/tests/unit/` (53 files), `frontend/src/` (183 files)

**Checkpoint**: Foundation ready — category-based bug bash can now begin in priority order

---

## Phase 3: User Story 1 — Security Vulnerability Audit (Priority: P1) 🎯 MVP

**Goal**: Identify and fix all security vulnerabilities including auth bypasses, injection risks, exposed secrets, insecure defaults, and improper input validation across the entire codebase.

**Independent Test**: Run the full test suite after applying all security fixes. Every fix must have at least one regression test that would fail if the vulnerability were reintroduced.

### Implementation for User Story 1

#### Backend API Security Audit (18 modules)

- [ ] T010 [US1] Audit authentication and authorization logic in `backend/src/api/auth.py` — check for auth bypasses, token validation issues, session handling vulnerabilities
- [ ] T011 [P] [US1] Audit input validation and injection risks in `backend/src/api/chat.py` — check request handling, file upload validation, user input sanitization
- [ ] T012 [P] [US1] Audit input validation in `backend/src/api/agents.py` — check for unsafe input handling in agent configuration endpoints
- [ ] T013 [P] [US1] Audit input validation in `backend/src/api/board.py` — check for unsafe input in board/project operations
- [ ] T014 [P] [US1] Audit input validation in `backend/src/api/pipelines.py` — check for unsafe input in pipeline CRUD operations
- [ ] T015 [P] [US1] Audit input validation in `backend/src/api/projects.py` — check for unsafe input in project management endpoints
- [ ] T016 [P] [US1] Audit input validation in `backend/src/api/tasks.py` — check for unsafe input in task management endpoints
- [ ] T017 [P] [US1] Audit input validation in `backend/src/api/tools.py` — check for unsafe input in MCP tool configuration endpoints
- [ ] T018 [P] [US1] Audit input validation in `backend/src/api/webhooks.py` — check webhook signature validation, payload sanitization
- [ ] T019 [P] [US1] Audit input validation in `backend/src/api/workflow.py` — check for unsafe input in workflow trigger endpoints
- [ ] T020 [P] [US1] Audit remaining API modules: `backend/src/api/chores.py`, `backend/src/api/cleanup.py`, `backend/src/api/health.py`, `backend/src/api/mcp.py`, `backend/src/api/metadata.py`, `backend/src/api/settings.py`, `backend/src/api/signal.py`

#### Backend Core Security Audit

- [ ] T021 [US1] Audit secrets and configuration validation in `backend/src/config.py` — verify secret enforcement, CORS config, cookie security settings
- [ ] T022 [P] [US1] Audit CORS middleware and security headers in `backend/src/main.py` — verify existing TODO(bug-bash) for wildcard methods/headers, check middleware ordering
- [ ] T023 [P] [US1] Audit encryption implementation in `backend/src/services/encryption.py` — check key management, cipher mode, padding
- [ ] T024 [P] [US1] Audit session management in `backend/src/services/session_store.py` — check session lifecycle, token security
- [ ] T025 [P] [US1] Audit GitHub auth flow in `backend/src/services/github_auth.py` — check OAuth token handling, state parameter validation

#### Backend Service Security Audit

- [ ] T026 [P] [US1] Audit `backend/src/services/signal_chat.py` — verify existing TODO(bug-bash) comments for error message leakage (lines 175-179, 538-541, 818-824), check for additional injection risks
- [ ] T027 [P] [US1] Audit `backend/src/services/database.py` — check SQL injection risks in migration runner, verify migration numbering TODO (R-001)
- [ ] T028 [P] [US1] Audit `backend/src/services/tools/service.py` — check MCP server configuration validation for command injection risks
- [ ] T029 [P] [US1] Audit `backend/src/services/tools/presets.py` — check preset MCP config for insecure defaults

#### Frontend Security Audit

- [ ] T030 [P] [US1] Audit XSS risks in `frontend/src/components/chat/MessageBubble.tsx` — check for unsafe HTML rendering, `dangerouslySetInnerHTML` usage
- [ ] T031 [P] [US1] Audit token handling in `frontend/src/services/api.ts` — check how auth tokens are stored/transmitted, cookie security
- [ ] T032 [P] [US1] Audit user input handling across `frontend/src/components/chat/ChatInterface.tsx` and `frontend/src/components/chat/MentionInput.tsx` — check for client-side injection vectors

#### Security Fix Validation

- [ ] T033 [US1] Fix temp file accumulation in `backend/src/api/chat.py` (research R-003) — add cleanup logic after file content is read in `/chat/upload` endpoint, add regression test in `backend/tests/unit/test_chat.py`
- [ ] T034 [US1] Add regression tests for any security bugs found during audit to appropriate test files under `backend/tests/unit/` or co-located frontend test files
- [ ] T035 [US1] Run full backend test suite with `python -m pytest tests/unit/ -v --tb=short` and verify all tests pass including new security regression tests
- [ ] T036 [P] [US1] Run full frontend test suite with `npx vitest run` and verify all tests pass

**Checkpoint**: All security vulnerabilities identified and fixed with regression tests. Test suite green.

---

## Phase 4: User Story 2 — Runtime Error Resolution (Priority: P2)

**Goal**: Identify and fix all runtime errors including unhandled exceptions, race conditions, null references, missing imports, type errors, file handle leaks, and database connection leaks.

**Independent Test**: Run the full test suite after applying all runtime error fixes. Every fix must have at least one regression test.

### Implementation for User Story 2

#### Backend Runtime Error Audit

- [ ] T037 [US2] Audit exception handling and resource management in `backend/src/services/database.py` — check connection lifecycle, migration error handling, resource cleanup
- [ ] T038 [P] [US2] Audit exception handling in `backend/src/services/github_projects/service.py` — check for unhandled exceptions in 50 `except Exception` sites, resource cleanup in GraphQL client
- [ ] T039 [P] [US2] Audit exception handling in `backend/src/services/github_projects/graphql_client.py` — check for connection leaks, timeout handling, retry logic
- [ ] T040 [P] [US2] Audit async patterns in `backend/src/services/workflow_orchestrator/orchestrator.py` — check for race conditions in 23 exception handling sites, state management
- [ ] T041 [P] [US2] Audit async patterns in `backend/src/services/copilot_polling/` — check polling lifecycle, cancellation handling, resource cleanup
- [ ] T042 [P] [US2] Audit resource management in `backend/src/services/blocking_queue.py` — check asyncio.Lock usage, connection handling, error propagation
- [ ] T043 [P] [US2] Audit resource management in `backend/src/services/blocking_queue_store.py` — check SQLite operations, connection handling
- [ ] T044 [P] [US2] Audit exception handling in `backend/src/services/signal_chat.py` — check for unhandled exceptions beyond the known error message leakage issues
- [ ] T045 [P] [US2] Audit exception handling in `backend/src/services/signal_bridge.py` and `backend/src/services/signal_delivery.py` — check for resource leaks and unhandled errors
- [ ] T046 [P] [US2] Audit startup/shutdown lifecycle in `backend/src/main.py` — check lifespan handler for proper resource cleanup, error handling during startup/shutdown
- [ ] T047 [P] [US2] Audit exception handling in `backend/src/api/chat.py` — check for unhandled exceptions in 12 `except Exception` sites, verify proper error responses
- [ ] T048 [P] [US2] Audit remaining service modules for runtime errors: `backend/src/services/ai_agent.py`, `backend/src/services/agent_creator.py`, `backend/src/services/agent_tracking.py`, `backend/src/services/cache.py`, `backend/src/services/cleanup_service.py`, `backend/src/services/metadata_service.py`, `backend/src/services/model_fetcher.py`, `backend/src/services/websocket.py`
- [ ] T049 [P] [US2] Audit `backend/src/services/agents/` package — check for null references, missing error handling in agent service methods
- [ ] T050 [P] [US2] Audit `backend/src/services/pipelines/` package — check for null references, missing error handling in pipeline service methods
- [ ] T051 [P] [US2] Audit `backend/src/services/mcp_store.py` and `backend/src/services/settings_store.py` — check SQLite operations for proper error handling

#### Backend Model Type Safety Audit

- [ ] T052 [P] [US2] Audit Pydantic model validation in `backend/src/models/` (19 files) — check for type errors, missing validators, incorrect Optional usage across all model files

#### Frontend Runtime Error Audit

- [ ] T053 [P] [US2] Audit null/undefined handling in `frontend/src/hooks/` — check all custom hooks for uncaught promise rejections, null access on optional data
- [ ] T054 [P] [US2] Audit error boundaries in `frontend/src/components/common/ErrorBoundary.tsx` — check coverage and error handling completeness
- [ ] T055 [P] [US2] Audit loading/error states in `frontend/src/pages/` — check all page components for unhandled loading states and missing error handling
- [ ] T056 [P] [US2] Audit API client error handling in `frontend/src/services/api.ts` — check for unhandled promise rejections, missing error responses

#### Runtime Error Fix Validation

- [ ] T057 [US2] Add regression tests for any runtime error bugs found during audit to appropriate test files
- [ ] T058 [US2] Run full backend test suite with `python -m pytest tests/unit/ -v --tb=short` and verify all tests pass
- [ ] T059 [P] [US2] Run full frontend test suite with `npx vitest run` and verify all tests pass

**Checkpoint**: All runtime errors identified and fixed with regression tests. Test suite green.

---

## Phase 5: User Story 3 — Logic Bug Resolution (Priority: P3)

**Goal**: Identify and fix all logic bugs including incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, and incorrect return values.

**Independent Test**: Run the full test suite after applying all logic bug fixes. Every fix must have at least one regression test that validates the corrected behavior.

### Implementation for User Story 3

#### Backend Logic Bug Audit

- [ ] T060 [US3] Audit state transitions in `backend/src/services/workflow_orchestrator/orchestrator.py` — check workflow state machine correctness, step ordering, error state handling
- [ ] T061 [P] [US3] Audit state transitions in `backend/src/services/blocking_queue.py` — check pending→active→in_review→completed state machine, verify no invalid transitions
- [ ] T062 [P] [US3] Audit API call correctness in `backend/src/services/github_projects/service.py` — check GraphQL queries, mutation parameters, response parsing
- [ ] T063 [P] [US3] Audit business logic in `backend/src/services/agents/` package — check method naming consistency, preferences handling, config lifecycle
- [ ] T064 [P] [US3] Audit business logic in `backend/src/services/workflow_orchestrator/config.py` — check 3-tier pipeline resolution fallback (project→user→defaults), mapping correctness
- [ ] T065 [P] [US3] Audit return value correctness in `backend/src/api/` (18 modules) — check for incorrect HTTP status codes, wrong response models, missing fields
- [ ] T066 [P] [US3] Audit control flow in `backend/src/services/signal_chat.py` — check command parsing, dispatch logic, response formatting
- [ ] T067 [P] [US3] Audit data consistency in `backend/src/services/agent_tracking.py` — check 5-column table parsing, model name resolution, status tracking (known semantic inconsistency: empty string vs "TBD" for unassigned models)
- [ ] T068 [P] [US3] Audit migration SQL correctness in `backend/src/migrations/` (20 files) — check SQL statements, constraints, index definitions, idempotency
- [ ] T069 [P] [US3] Audit business logic in `backend/src/services/completion_providers.py`, `backend/src/services/github_commit_workflow.py`, `backend/src/services/chores/` — check for off-by-one errors, incorrect calculations

#### Frontend Logic Bug Audit

- [ ] T070 [P] [US3] Audit state management in `frontend/src/hooks/useChat.ts` — check pipeline_id passing, message submission flow, state updates
- [ ] T071 [P] [US3] Audit React Query cache management in `frontend/src/hooks/useSelectedPipeline.ts` and `frontend/src/hooks/useBlockingQueue.ts` — check query key consistency, cache invalidation correctness
- [ ] T072 [P] [US3] Audit stale closures and hook dependencies in `frontend/src/hooks/useMentionAutocomplete.ts` — check effect dependencies, callback memoization
- [ ] T073 [P] [US3] Audit component logic in `frontend/src/components/board/` — check issue tracking, drag-and-drop logic, blocking chain panel rendering
- [ ] T074 [P] [US3] Audit component logic in `frontend/src/components/chat/` — check message rendering, mention token handling, file preview, voice input
- [ ] T075 [P] [US3] Audit page-level logic in `frontend/src/pages/` — check data fetching, state management, routing logic

#### Logic Bug Fix Validation

- [ ] T076 [US3] Add regression tests for any logic bugs found during audit to appropriate test files
- [ ] T077 [US3] Run full backend test suite with `python -m pytest tests/unit/ -v --tb=short` and verify all tests pass
- [ ] T078 [P] [US3] Run full frontend test suite with `npx vitest run` and verify all tests pass

**Checkpoint**: All logic bugs identified and fixed with regression tests. Test suite green.

---

## Phase 6: User Story 4 — Test Quality Improvement (Priority: P4)

**Goal**: Identify and fix test gaps and low-quality tests including untested code paths, tests that pass for the wrong reason, mock leaks, tautological assertions, and missing edge case coverage.

**Independent Test**: Verify that corrected tests now properly validate the behavior they claim to test. Intentionally breaking code should cause the relevant test to fail.

### Implementation for User Story 4

#### Backend Test Quality Audit (53 test files)

- [ ] T079 [US4] Audit mock usage in `backend/tests/conftest.py` — check shared fixtures (`mock_db`, `mock_session`, `mock_settings`, `mock_github_service`, `client`) for mock objects leaking into production paths
- [ ] T080 [P] [US4] Audit mock usage in `backend/tests/unit/test_chat.py` — check for MagicMock objects used as file paths, database paths, or other production values
- [ ] T081 [P] [US4] Audit mock usage in `backend/tests/unit/test_database.py` — check for mock leaks in migration testing
- [ ] T082 [P] [US4] Audit mock usage in `backend/tests/unit/test_workflow_orchestrator.py` — check for mock leaks in workflow testing
- [ ] T083 [P] [US4] Audit assertion quality in `backend/tests/unit/test_agents*.py` — check for tautological assertions (e.g., `assert mock.called`, assertions that always pass)
- [ ] T084 [P] [US4] Audit assertion quality in `backend/tests/unit/test_blocking_queue*.py` — check for tautological assertions and missing edge case coverage
- [ ] T085 [P] [US4] Audit assertion quality in `backend/tests/unit/test_signal*.py` — check for assertions that never fail, missing error path testing
- [ ] T086 [P] [US4] Audit remaining backend test files for mock leaks and assertion quality: scan all files in `backend/tests/unit/` not covered by T080-T085
- [ ] T087 [P] [US4] Audit test coverage gaps in `backend/tests/unit/` — identify critical backend code paths that have no corresponding test

#### Frontend Test Quality Audit

- [ ] T088 [P] [US4] Audit mock configuration in `frontend/src/test/test-utils.tsx` — verify TooltipProvider wrapping does not cause false positives, check test utility completeness
- [ ] T089 [P] [US4] Audit assertion quality in `frontend/src/components/**/*.test.tsx` — check for tautological assertions, missing user interaction testing, snapshot-only tests
- [ ] T090 [P] [US4] Audit assertion quality in `frontend/src/hooks/**/*.test.ts` — check for missing async testing, incomplete mock setups
- [ ] T091 [P] [US4] Identify frontend coverage gaps — find components and hooks with no test file or insufficient test coverage

#### Test Quality Fix Validation

- [ ] T092 [US4] Fix identified mock leaks by replacing mock objects with realistic test values in affected test files
- [ ] T093 [US4] Fix identified tautological assertions by replacing with meaningful assertions that would fail on incorrect behavior
- [ ] T094 [US4] Add tests for identified coverage gaps in highest-risk code paths
- [ ] T095 [US4] Run full backend test suite with `python -m pytest tests/unit/ -v --tb=short` and verify all tests pass and no test passes for the wrong reason
- [ ] T096 [P] [US4] Run full frontend test suite with `npx vitest run` and verify all tests pass

**Checkpoint**: Test quality improved — mock leaks fixed, tautological assertions replaced, critical coverage gaps filled. Test suite green.

---

## Phase 7: User Story 5 — Code Quality Cleanup (Priority: P5)

**Goal**: Address dead code, unreachable branches, duplicated logic, and silent failures to improve codebase maintainability.

**Independent Test**: Verify that removal of dead code does not change any test outcome and that previously silent failures now produce appropriate error feedback.

### Implementation for User Story 5

#### Backend Code Quality Audit

- [ ] T097 [P] [US5] Audit for dead code and unused imports in `backend/src/api/` (18 modules) — identify and remove unused imports, unreachable code paths
- [ ] T098 [P] [US5] Audit for dead code and unused imports in `backend/src/services/` (49 modules) — identify and remove unused imports, dead functions
- [ ] T099 [P] [US5] Audit for dead code in `backend/src/models/` (19 files) — identify unused model fields, deprecated models
- [ ] T100 [P] [US5] Audit for silent failures in `backend/src/services/` — identify swallowed exceptions (bare `except: pass` or `except Exception: pass` with no logging), add appropriate error feedback
- [ ] T101 [P] [US5] Audit for duplicated logic in `backend/src/services/` — identify duplicated code patterns that could indicate copy-paste bugs
- [ ] T102 [P] [US5] Flag hardcoded values that should be configurable with `TODO(bug-bash):` comments in backend source files

#### Frontend Code Quality Audit

- [ ] T103 [P] [US5] Audit for dead code in `frontend/src/components/` — identify unused components (e.g., known dead code: `MentionToken.tsx`), unused imports
- [ ] T104 [P] [US5] Audit for dead code in `frontend/src/hooks/` — identify unused hooks, unused exports
- [ ] T105 [P] [US5] Audit for dead code in `frontend/src/pages/` and `frontend/src/services/` — identify unused pages, dead API methods
- [ ] T106 [P] [US5] Audit for silent failures in frontend components — identify swallowed promise rejections, missing error displays

#### Code Quality Fix Validation

- [ ] T107 [US5] Remove identified dead code and unused imports from backend and frontend files
- [ ] T108 [US5] Add error feedback for identified silent failures with regression tests
- [ ] T109 [US5] Run full backend test suite with `python -m pytest tests/unit/ -v --tb=short` and verify all tests pass
- [ ] T110 [P] [US5] Run full frontend test suite with `npx vitest run` and verify all tests pass
- [ ] T111 [P] [US5] Run backend linting with `cd backend && ruff check src/ tests/` and verify zero violations
- [ ] T112 [P] [US5] Run frontend linting with `cd frontend && npx eslint src/ && npx tsc --noEmit` and verify zero violations

**Checkpoint**: Dead code removed, silent failures addressed, linting clean. Test suite green.

---

## Phase 8: User Story 6 — Ambiguous Issue Documentation (Priority: P6)

**Goal**: Ensure all ambiguous or trade-off situations are clearly documented with `TODO(bug-bash):` comments for human review.

**Independent Test**: Search the codebase for `TODO(bug-bash):` comments and verify each includes issue description, options, and rationale.

### Implementation for User Story 6

- [ ] T113 [US6] Review all issues flagged during US1–US5 audits that were marked as ambiguous — compile list of items needing `TODO(bug-bash):` comments
- [ ] T114 [US6] Verify each `TODO(bug-bash):` comment includes: (1) issue description, (2) available options (at least two), (3) rationale for human review
- [ ] T115 [US6] Verify existing `TODO(bug-bash):` comments from previous bug bash (030) in `backend/src/services/signal_chat.py`, `backend/src/main.py`, and `backend/src/services/database.py` are still accurate and complete
- [ ] T116 [US6] Ensure migration numbering conflict (R-001) is documented with `TODO(bug-bash):` in `backend/src/services/database.py` with full context about prefixes 013, 014, 015 and deployment reconciliation options
- [ ] T117 [US6] Ensure CORS wildcard configuration (R-004) is documented with `TODO(bug-bash):` in `backend/src/main.py` with full context about `allow_methods=["*"]` and `allow_headers=["*"]`
- [ ] T118 [P] [US6] Search entire codebase with `grep -r "TODO(bug-bash):" backend/ frontend/` to produce a complete inventory of all flagged items

**Checkpoint**: All ambiguous issues documented with structured TODO comments. Each has description, options, and rationale.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary generation, and cross-cutting checks across all user stories

- [ ] T119 Run complete backend test suite one final time with `cd backend && python -m pytest tests/unit/ -v --tb=short` — all tests must pass with zero failures
- [ ] T120 [P] Run complete frontend test suite one final time with `cd frontend && npx vitest run` — all tests must pass with zero failures
- [ ] T121 [P] Run backend linting one final time with `cd backend && ruff check src/ tests/` — zero violations
- [ ] T122 [P] Run frontend linting one final time with `cd frontend && npx eslint src/` — zero violations
- [ ] T123 [P] Run frontend type check one final time with `cd frontend && npx tsc --noEmit` — zero type errors
- [ ] T124 Generate the final summary table following the schema in `specs/031-bug-basher/contracts/summary-table.md` — one row per bug found, ordered by category priority then file path then line number
- [ ] T125 Verify summary table completeness: every `✅ Fixed` entry has a corresponding regression test, every `⚠️ Flagged (TODO)` entry has a corresponding `TODO(bug-bash):` comment in source
- [ ] T126 Verify zero new dependencies were introduced by checking `backend/pyproject.toml` and `frontend/package.json` against baseline
- [ ] T127 Verify no architecture or public API surface changes by reviewing all modified files for endpoint signature changes, model schema changes, or structural reorganization
- [ ] T128 Write commit messages for each fix following the format: `fix(<category>): <short description>` with body explaining bug, why, and fix

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 Security (Phase 3)**: Depends on Foundational — highest priority, do first
- **US2 Runtime (Phase 4)**: Depends on Foundational — can start after US1 or in parallel
- **US3 Logic (Phase 5)**: Depends on Foundational — can start after US2 or in parallel
- **US4 Test Quality (Phase 6)**: Depends on Foundational — benefits from US1-US3 fixes being complete
- **US5 Code Quality (Phase 7)**: Depends on Foundational — benefits from US1-US4 being complete
- **US6 Ambiguous Docs (Phase 8)**: Depends on US1-US5 to know all flagged items
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1) Security**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2) Runtime**: Can start after Foundational (Phase 2) — Independent of US1 but ideally done after
- **US3 (P3) Logic**: Can start after Foundational (Phase 2) — Independent of US1/US2 but ideally done after
- **US4 (P4) Test Quality**: Can start after Foundational (Phase 2) — Benefits from US1-US3 being complete (fixes inform test improvements)
- **US5 (P5) Code Quality**: Can start after Foundational (Phase 2) — Benefits from US1-US4 being complete (dead code clearer after fixes)
- **US6 (P6) Ambiguous Docs**: Depends on US1-US5 completion — collects all flagged items from other stories

### Within Each User Story

- Audit tasks within a story are parallelizable (different files)
- Fix tasks depend on audit completion (must know what to fix)
- Regression tests are created alongside fixes
- Validation (test suite run) comes after all fixes for that story
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002 with T001, T004-T006 with T003)
- All audit tasks within a user story marked [P] can run in parallel (e.g., T011-T020 can all run simultaneously)
- Backend and frontend audits within the same story can run in parallel
- Backend and frontend test suites can run in parallel (e.g., T035 + T036)
- Different user stories can be worked on in parallel if team capacity allows (US1-US3 are independent)

---

## Parallel Example: User Story 1 (Security)

```bash
# Launch all backend API security audits in parallel:
Task: "Audit auth logic in backend/src/api/auth.py"               # T010
Task: "Audit input validation in backend/src/api/chat.py"          # T011
Task: "Audit input validation in backend/src/api/agents.py"        # T012
Task: "Audit input validation in backend/src/api/board.py"         # T013
Task: "Audit input validation in backend/src/api/pipelines.py"     # T014
# ... all [P] tasks in Phase 3 can run simultaneously

# After audits complete, fixes are applied sequentially:
Task: "Fix temp file accumulation in backend/src/api/chat.py"      # T033
Task: "Add regression tests for security bugs"                     # T034

# Final validation runs backend + frontend in parallel:
Task: "Run backend test suite"                                     # T035
Task: "Run frontend test suite"                                    # T036
```

---

## Parallel Example: Cross-Story Parallelism

```bash
# After Foundational phase, multiple stories can run in parallel with different developers:

# Developer A: User Story 1 (Security)
Task: T010-T036

# Developer B: User Story 2 (Runtime)
Task: T037-T059

# Developer C: User Story 3 (Logic)
Task: T060-T078

# Each developer works independently, each story has its own validation checkpoint
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T009)
3. Complete Phase 3: User Story 1 — Security (T010-T036)
4. **STOP and VALIDATE**: Run full test suite, verify all security fixes have regression tests
5. This is a deployable MVP — all security vulnerabilities are addressed

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 Security → Test independently → **MVP! Security hardened**
3. Add US2 Runtime → Test independently → Runtime stability improved
4. Add US3 Logic → Test independently → Logic correctness verified
5. Add US4 Test Quality → Test independently → Test suite strengthened
6. Add US5 Code Quality → Test independently → Codebase cleaned
7. Add US6 Ambiguous Docs → Verify independently → All trade-offs documented
8. Complete Phase 9 Polish → Final validation and summary table
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Security) — highest priority
   - Developer B: User Story 2 (Runtime) — can start in parallel
   - Developer C: User Story 3 (Logic) — can start in parallel
3. After US1-US3 complete:
   - Developer A: User Story 4 (Test Quality)
   - Developer B: User Story 5 (Code Quality)
4. After US4-US5 complete:
   - Any developer: User Story 6 (Ambiguous Docs)
5. Final: Polish phase with full team validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story maps to one bug category: US1=Security, US2=Runtime, US3=Logic, US4=Test Quality, US5=Code Quality, US6=Ambiguous Docs
- Tests are REQUIRED per FR-004 — every bug fix must have at least one regression test
- Commit message format: `fix(<category>): <short description>` with bug/why/fix body
- Existing `TODO(bug-bash):` comments from bug bash 030 must be verified, not duplicated
- No new dependencies (FR-011), no architecture changes (FR-010), minimal focused fixes (FR-013)
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
