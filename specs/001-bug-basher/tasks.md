# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/001-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md, contracts/

**Tests**: Tests are REQUIRED by the feature specification (FR-005: "at least one new regression test per bug"). Regression tests are included within each user story phase.

**Organization**: Tasks are grouped by user story (bug category) to enable independent implementation and testing of each category in strict priority order per SC-009.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## TODO Comment Format (Quick Reference)

For ambiguous bugs, use this format at the relevant code location:

```python
# TODO(bug-bash): <issue description>.
# Options: (a) <option 1>, (b) <option 2>.
# Deferred because: <rationale for human review>.
```

See `specs/001-bug-basher/contracts/bug-report-schema.md` for the full contract.

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`
- **Infrastructure**: Root `docker-compose.yml`, `solune/docker-compose.yml`

---

## Phase 1: Setup

**Purpose**: Establish baseline state and prepare for the code review audit

- [ ] T001 Clone repository with full history and verify branch is `001-bug-basher`
- [ ] T002 Install backend dependencies via `cd solune/backend && uv sync --dev`
- [ ] T003 [P] Install frontend dependencies via `cd solune/frontend && npm ci`
- [ ] T004 Run backend baseline tests via `cd solune/backend && python -m pytest tests/ -v` and save output to `/tmp/baseline-backend-tests.log`
- [ ] T005 [P] Run backend baseline lint via `cd solune/backend && python -m ruff check src tests` and save output to `/tmp/baseline-backend-lint.log`
- [ ] T006 [P] Run frontend baseline tests via `cd solune/frontend && npm test` and save output to `/tmp/baseline-frontend-tests.log`
- [ ] T007 [P] Run frontend baseline lint via `cd solune/frontend && npm run lint` and save output to `/tmp/baseline-frontend-lint.log`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Understand codebase patterns, identify high-risk areas, and set up regression test infrastructure

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Review backend service inventory — catalog all 23 service files in `solune/backend/src/services/` and 6 sub-packages (`github_projects/`, `workflow_orchestrator/`, `agents/`, `copilot_polling/`, `pipelines/`) to identify high-risk modules for each bug category
- [ ] T009 [P] Review backend API route inventory — catalog all 19 route files in `solune/backend/src/api/` and map input validation patterns
- [ ] T010 [P] Review middleware inventory — catalog all 4 middleware files in `solune/backend/src/middleware/` (admin_guard.py, csp.py, rate_limit.py, request_id.py) and identify security-relevant logic
- [ ] T011 [P] Review frontend service and hook inventory — catalog `solune/frontend/src/services/api.ts`, all hooks in `solune/frontend/src/hooks/`, and components with security-sensitive rendering
- [ ] T012 Review SQLite schema at `solune/backend/src/migrations/023_consolidated_schema.sql` and cross-reference with Pydantic models in `solune/backend/src/models/` for type mismatches
- [ ] T013 Review existing test coverage — catalog 50+ unit tests in `solune/backend/tests/unit/`, 4 integration tests in `solune/backend/tests/integration/`, and 70+ frontend tests to identify gaps

**Checkpoint**: Codebase inventory complete — category-specific audits can now proceed in priority order

---

## Phase 3: User Story 1 — Fix Security Vulnerabilities (Priority: P1) 🎯 MVP

**Goal**: Audit every file for security vulnerabilities (auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation) and fix all confirmed issues with regression tests

**Independent Test**: Run `cd solune/backend && python -m pytest tests/ -v` and `cd solune/frontend && npm test` — all pass including new regression tests; no secrets in source; input validation covers known attack vectors

### Audit & Fix: Backend Security — Services

- [ ] T014 [US1] Audit `solune/backend/src/services/encryption.py` for key management flaws, fallback-to-plaintext behavior, and algorithm weaknesses — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_token_encryption.py`
- [ ] T015 [P] [US1] Audit `solune/backend/src/services/github_auth.py` for OAuth scope issues, token handling, and authentication bypass risks — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_github_auth.py`
- [ ] T016 [P] [US1] Audit `solune/backend/src/services/guard_service.py` for path protection bypass risks and guard evaluation logic — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_admin_authorization.py`
- [ ] T017 [P] [US1] Audit `solune/backend/src/services/app_service.py` for path traversal vulnerabilities in `_safe_app_path()` and filesystem operations — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/`
- [ ] T018 [P] [US1] Audit all database stores for SQL injection risks — review parameterized query usage in `solune/backend/src/services/database.py`, `solune/backend/src/services/chat_store.py`, `solune/backend/src/services/settings_store.py`, `solune/backend/src/services/session_store.py`, `solune/backend/src/services/mcp_store.py`, `solune/backend/src/services/pipeline_state_store.py` — fix confirmed bugs, add regression tests
- [ ] T019 [P] [US1] Audit `solune/backend/src/services/signal_bridge.py` and `solune/backend/src/services/signal_chat.py` for input sanitization and injection risks in external service communication — fix confirmed bugs, add regression tests

### Audit & Fix: Backend Security — Middleware & Core

- [ ] T020 [US1] Audit `solune/backend/src/middleware/admin_guard.py` for authentication bypass via missing or spoofable `X-Target-Paths` header validation — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_middleware.py`
- [ ] T021 [P] [US1] Audit `solune/backend/src/middleware/csp.py` for Content Security Policy header completeness and correctness — fix confirmed bugs, add regression tests
- [ ] T022 [P] [US1] Audit `solune/backend/src/middleware/rate_limit.py` for bypass risks and coverage gaps — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_rate_limiting.py`
- [ ] T023 [P] [US1] Audit `solune/backend/src/config.py` for hardcoded secrets, insecure defaults, and missing environment variable validation — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_config.py`
- [ ] T024 [US1] Audit `solune/backend/src/main.py` for CORS misconfiguration (overly permissive origins) and insecure middleware registration order — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_main.py`

### Audit & Fix: Backend Security — API Routes

- [ ] T025 [US1] Audit all 19 API route files in `solune/backend/src/api/` for missing input validation — verify Pydantic model usage on all endpoints in `auth.py`, `board.py`, `chat.py`, `apps.py`, `agents.py`, `settings.py`, `signal.py`, `webhooks.py`, `mcp.py`, `pipelines.py`, `projects.py`, `tasks.py`, `tools.py`, `workflow.py`, `metadata.py`, `health.py`, `chores.py`, `cleanup.py` — fix confirmed bugs, add regression tests

### Audit & Fix: Frontend Security

- [ ] T026 [P] [US1] Audit `solune/frontend/src/` for XSS risks — search for `dangerouslySetInnerHTML` usage across all components, verify `react-markdown` safety configuration — fix confirmed bugs, add regression tests in co-located `*.test.tsx` files
- [ ] T027 [P] [US1] Audit `solune/frontend/src/services/api.ts` for insecure request patterns, missing CSRF protection, and credential handling — fix confirmed bugs, add regression tests
- [ ] T028 [P] [US1] Audit `solune/frontend/nginx.conf` for security header gaps (X-Frame-Options, server_tokens, X-Content-Type-Options) — fix confirmed bugs

### Audit & Fix: Infrastructure Security

- [ ] T029 [P] [US1] Audit root `docker-compose.yml` and `solune/docker-compose.yml` for exposed ports, hardcoded credentials, and insecure volume mounts — fix confirmed bugs
- [ ] T030 [US1] Audit `guard-config.yml` at `solune/guard-config.yml` for path protection completeness — ensure all sensitive paths have appropriate guard levels — fix confirmed bugs

### Security Summary & TODO Flags

- [ ] T031 [US1] For each ambiguous security finding, add `# TODO(bug-bash):` comment per contract format in `specs/001-bug-basher/contracts/bug-report-schema.md` — document issue, options, and rationale for deferral
- [ ] T032 [US1] Run full backend test suite `cd solune/backend && python -m pytest tests/ -v` and frontend test suite `cd solune/frontend && npm test` — verify all pass including new security regression tests
- [ ] T033 [US1] Run linting `cd solune/backend && python -m ruff check src tests` and `cd solune/frontend && npm run lint` — verify clean after security fixes

**Checkpoint**: All security vulnerabilities fixed or flagged. Full test suite and lint pass. US1 is independently testable and complete.

---

## Phase 4: User Story 2 — Fix Runtime Errors (Priority: P2)

**Goal**: Audit every file for runtime errors (unhandled exceptions, race conditions, null/None references, missing imports, type errors, resource leaks) and fix all confirmed issues with regression tests

**Independent Test**: Run full backend and frontend test suites — all pass including new regression tests; no unhandled exceptions or resource leaks in fixed code paths

### Audit & Fix: Backend Runtime — Exception Handling

- [ ] T034 [US2] Audit all API route files in `solune/backend/src/api/` for unhandled exceptions — review try/except coverage, check for bare `except:` clauses that swallow errors — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_error_responses.py`
- [ ] T035 [P] [US2] Audit all service files in `solune/backend/src/services/` for unhandled exceptions in async methods — focus on `ai_agent.py`, `completion_providers.py`, `model_fetcher.py`, `metadata_service.py` — fix confirmed bugs, add regression tests

### Audit & Fix: Backend Runtime — Resource Leaks

- [ ] T036 [US2] Audit `solune/backend/src/services/database.py` for database connection leaks — verify all `aiosqlite` connections use context managers — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_database.py`
- [ ] T037 [P] [US2] Audit `solune/backend/src/services/chat_store.py`, `solune/backend/src/services/settings_store.py`, `solune/backend/src/services/session_store.py`, `solune/backend/src/services/mcp_store.py`, `solune/backend/src/services/pipeline_state_store.py` for database connection leaks — fix confirmed bugs, add regression tests
- [ ] T038 [P] [US2] Audit `solune/backend/src/attachment_formatter.py` and `solune/backend/src/services/app_service.py` for file handle leaks — verify proper use of context managers for file I/O — fix confirmed bugs, add regression tests

### Audit & Fix: Backend Runtime — Null/None & Type Errors

- [ ] T039 [US2] Audit `solune/backend/src/models/` for missing `Optional` annotations and unguarded attribute access — cross-reference Pydantic model fields with SQLite schema columns in `solune/backend/src/migrations/023_consolidated_schema.sql` — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_models.py`
- [ ] T040 [P] [US2] Audit the known `accepted` vs `confirmed` status mapping in `solune/backend/src/services/chat_store.py` and `solune/backend/src/models/recommendation.py` — verify mapping correctness between DB values and enum values — fix if buggy, add regression test in `solune/backend/tests/unit/test_recommendation_models.py`

### Audit & Fix: Backend Runtime — Async & Timestamps

- [ ] T041 [US2] Audit `solune/backend/src/services/websocket.py`, `solune/backend/src/services/signal_bridge.py`, and `solune/backend/src/services/copilot_polling/` for race conditions on shared mutable state — focus on `polling_loop.py`, `state.py`, `recovery.py` — fix confirmed bugs, add regression tests
- [ ] T042 [P] [US2] Audit all `datetime.fromisoformat()` calls across backend for trailing `Z` handling — verify Python 3.13 compatibility and check for incorrect manual Z-stripping workarounds — fix confirmed bugs, add regression tests
- [ ] T043 [P] [US2] Audit `solune/backend/src/services/cleanup_service.py` for resource cleanup edge cases and unhandled errors during cleanup operations — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_cleanup_service.py`

### Audit & Fix: Frontend Runtime

- [ ] T044 [P] [US2] Audit `solune/frontend/src/hooks/` for missing `useEffect` cleanup functions — focus on WebSocket connections, timers, and event listeners in `useRealTimeSync`, `useChat`, `useBoardRefresh`, `useVoiceInput` — fix confirmed bugs, add regression tests in co-located `*.test.tsx` files
- [ ] T045 [P] [US2] Audit `solune/frontend/src/services/api.ts` for missing error handling on API calls — verify all fetch/axios calls have proper catch handlers — fix confirmed bugs, add regression tests
- [ ] T046 [P] [US2] Audit `solune/frontend/src/components/` for missing error boundary coverage and unhandled Promise rejections — fix confirmed bugs, add regression tests

### Runtime TODO Flags & Validation

- [ ] T047 [US2] For each ambiguous runtime finding, add `# TODO(bug-bash):` comment per contract format — document issue, options, and rationale for deferral
- [ ] T048 [US2] Run full backend and frontend test suites — verify all pass including new runtime regression tests
- [ ] T049 [US2] Run linting checks — verify clean after runtime fixes

**Checkpoint**: All runtime errors fixed or flagged. Full test suite and lint pass. US2 is independently testable and complete.

---

## Phase 5: User Story 3 — Fix Logic Bugs (Priority: P3)

**Goal**: Audit every file for logic bugs (incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, incorrect return values) and fix all confirmed issues with regression tests

**Independent Test**: Run full test suites — all pass including new regression tests; expected outputs match actual outputs for corrected logic paths

### Audit & Fix: Backend Logic — State Machines & Workflows

- [ ] T050 [US3] Audit `solune/backend/src/services/workflow_orchestrator/transitions.py` and `solune/backend/src/services/workflow_orchestrator/orchestrator.py` for incorrect state transitions — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_workflow_orchestrator.py`
- [ ] T051 [P] [US3] Audit `solune/backend/src/services/copilot_polling/state_validation.py` and `solune/backend/src/services/copilot_polling/completion.py` for incorrect completion detection or state validation logic — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_copilot_polling.py`
- [ ] T052 [P] [US3] Audit `solune/backend/src/services/copilot_polling/pipeline.py` and `solune/backend/src/services/copilot_polling/recovery.py` for incorrect pipeline step ordering or recovery logic — fix confirmed bugs, add regression tests

### Audit & Fix: Backend Logic — API & Service Layer

- [ ] T053 [US3] Audit all API route files in `solune/backend/src/api/` for off-by-one errors in pagination, incorrect HTTP status codes, and wrong return values — fix confirmed bugs, add regression tests
- [ ] T054 [P] [US3] Audit `solune/backend/src/services/github_projects/` sub-package (all 11 files: `service.py`, `graphql.py`, `board.py`, `issues.py`, `projects.py`, `pull_requests.py`, `copilot.py`, `agents.py`, `identities.py`, `branches.py`, `repository.py`) for incorrect GitHub API calls and data mapping errors — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_github_projects.py`
- [ ] T055 [P] [US3] Audit `solune/backend/src/services/agent_creator.py`, `solune/backend/src/services/agent_tracking.py`, and `solune/backend/src/services/ai_agent.py` for logic errors in agent lifecycle management — fix confirmed bugs, add regression tests
- [ ] T056 [P] [US3] Audit `solune/backend/src/services/cache.py` for cache invalidation logic errors and stale data issues — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_cache.py`

### Audit & Fix: Backend Logic — Data Consistency

- [ ] T057 [US3] Audit `solune/backend/src/services/chat_store.py` for data consistency issues between in-memory state and SQLite persistence — focus on recommendation status mapping and message ordering — fix confirmed bugs, add regression tests
- [ ] T058 [P] [US3] Audit `solune/backend/src/api/board.py` for board data aggregation logic errors and stale cache serving — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_api_board.py`
- [ ] T059 [P] [US3] Audit `solune/backend/src/utils.py` and `solune/backend/src/constants.py` for incorrect utility function logic and constant values — fix confirmed bugs, add regression tests in `solune/backend/tests/unit/test_utils.py`

### Audit & Fix: Frontend Logic

- [ ] T060 [P] [US3] Audit `solune/frontend/src/hooks/` for stale closures — check `useCallback`/`useMemo` dependency arrays in `useBoardControls`, `useChat`, `useBoardRefresh`, `useCommands`, `usePipelineConfig`, `useProjectBoard`, `useProjects`, `useWorkflow` — fix confirmed bugs, add regression tests
- [ ] T061 [P] [US3] Audit `solune/frontend/src/context/` for incorrect state management and data flow errors — fix confirmed bugs, add regression tests
- [ ] T062 [P] [US3] Audit `solune/frontend/src/lib/` for logic errors in utility functions (including `pipelineMigration`, `buildGitHubMcpConfig`, command registry) — fix confirmed bugs, add regression tests in co-located `*.test.ts` files

### Logic TODO Flags & Validation

- [ ] T063 [US3] For each ambiguous logic finding, add `# TODO(bug-bash):` comment per contract format — document current vs. expected behavior and trade-offs
- [ ] T064 [US3] Run full backend and frontend test suites — verify all pass including new logic regression tests
- [ ] T065 [US3] Run linting checks — verify clean after logic fixes

**Checkpoint**: All logic bugs fixed or flagged. Full test suite and lint pass. US3 is independently testable and complete.

---

## Phase 6: User Story 4 — Close Test Gaps and Improve Test Quality (Priority: P4)

**Goal**: Audit the test suite for quality issues (untested code paths, tests that pass for the wrong reason, mock leaks, vacuous assertions, missing edge case coverage) and close all gaps

**Independent Test**: Run full test suites — all pass; intentionally broken code causes expected test failures (tests are not vacuously passing)

### Audit & Fix: Backend Test Quality — Mock Leaks

- [ ] T066 [US4] Audit all backend test files in `solune/backend/tests/unit/` for `MagicMock` objects leaking into production code paths — search for mocks used as file paths, URLs, database values, or configuration — fix confirmed issues by properly scoping mocks
- [ ] T067 [P] [US4] Audit `solune/backend/tests/conftest.py` and `solune/backend/tests/helpers/` for fixture scope issues (session-scoped fixtures leaking state between tests) — fix confirmed issues

### Audit & Fix: Backend Test Quality — Assertions & Markers

- [ ] T068 [US4] Audit all backend test files in `solune/backend/tests/unit/` for vacuous assertions — search for `assert True`, `assert mock.called` without argument verification, and assertions that always pass regardless of code behavior — fix confirmed issues with meaningful assertions
- [ ] T069 [P] [US4] Audit all async test functions in `solune/backend/tests/` for missing `pytest-asyncio` markers — verify all async tests use proper `@pytest.mark.asyncio` decorators — fix confirmed issues

### Audit & Fix: Backend Test Quality — Coverage Gaps

- [ ] T070 [US4] Identify untested code paths in `solune/backend/src/services/` — focus on error handlers, boundary conditions, and empty input paths in `encryption.py`, `guard_service.py`, `app_service.py`, `websocket.py`, `signal_bridge.py` — add missing tests
- [ ] T071 [P] [US4] Identify untested code paths in `solune/backend/src/api/` — focus on error responses, edge cases, and validation failures in `auth.py`, `chat.py`, `apps.py`, `webhooks.py`, `pipelines.py` — add missing tests
- [ ] T072 [P] [US4] Identify untested code paths in `solune/backend/src/middleware/` — ensure `admin_guard.py`, `csp.py`, `rate_limit.py`, `request_id.py` have adequate error path coverage — add missing tests

### Audit & Fix: Frontend Test Quality

- [ ] T073 [P] [US4] Audit frontend test files in `solune/frontend/src/` for mock leaks, vacuous assertions, and missing cleanup — focus on component tests using `vi.mock()` that may leak between tests — fix confirmed issues
- [ ] T074 [P] [US4] Identify untested frontend code paths — focus on error states in hooks (`useChat`, `useProjectBoard`, `useWorkflow`), components with conditional rendering, and `solune/frontend/src/services/api.ts` error handling — add missing tests
- [ ] T075 [P] [US4] Audit `solune/frontend/src/components/common/ErrorBoundary.test.tsx` and other error boundary tests for completeness — verify error boundaries are tested with real error scenarios — fix confirmed issues

### Test Quality Validation

- [ ] T076 [US4] Run full backend test suite with coverage `cd solune/backend && python -m pytest --cov=src --cov-report=term-missing` — verify coverage improved after new tests
- [ ] T077 [US4] Run full frontend test suite `cd solune/frontend && npm test` — verify all new and corrected tests pass
- [ ] T078 [US4] Run linting checks on test files — verify clean after test quality fixes

**Checkpoint**: All test gaps closed, mock leaks fixed, vacuous assertions corrected. Full test suite passes with improved coverage. US4 is independently testable and complete.

---

## Phase 7: User Story 5 — Resolve Code Quality Issues (Priority: P5)

**Goal**: Audit every file for code quality issues (dead code, unreachable branches, duplicated logic, hardcoded values, missing error messages, silent failures) and resolve all confirmed issues with focused, minimal fixes

**Independent Test**: Run full test suites — all pass; removed dead code does not affect coverage metrics; no existing tests break

### Audit & Fix: Backend Code Quality — Dead Code & Unreachable Branches

- [ ] T079 [US5] Audit all backend service files in `solune/backend/src/services/` for dead code — identify functions/methods that are never called from any route or other service — remove confirmed dead code, verify test suite still passes
- [ ] T080 [P] [US5] Audit all backend API route files in `solune/backend/src/api/` for unreachable branches — identify conditional blocks that can never be entered based on upstream validation — remove confirmed unreachable code
- [ ] T081 [P] [US5] Audit `solune/backend/src/models/` for unused model fields or model classes that are defined but never used — remove confirmed dead code

### Audit & Fix: Backend Code Quality — Duplicated Logic & Hardcoded Values

- [ ] T082 [US5] Audit backend services for duplicated logic — identify repeated patterns across `solune/backend/src/services/chat_store.py`, `solune/backend/src/services/settings_store.py`, `solune/backend/src/services/session_store.py`, `solune/backend/src/services/mcp_store.py` — consolidate to shared helper if safe, add regression tests
- [ ] T083 [P] [US5] Audit `solune/backend/src/` for hardcoded values that should be configurable — check magic numbers, timeout values, and size limits that should be in `solune/backend/src/config.py` or `solune/backend/src/constants.py` — externalize confirmed issues, add regression tests
- [ ] T084 [P] [US5] Audit `solune/backend/src/services/` for silent failures — identify except blocks that swallow errors without logging or re-raising — add appropriate error logging or handling

### Audit & Fix: Frontend Code Quality

- [ ] T085 [P] [US5] Audit `solune/frontend/src/components/` for dead code — identify unused components, unused props, and unused imports — remove confirmed dead code
- [ ] T086 [P] [US5] Audit `solune/frontend/src/hooks/` and `solune/frontend/src/utils/` for duplicated logic and hardcoded values — consolidate duplicates, externalize constants — add regression tests
- [ ] T087 [P] [US5] Audit `solune/frontend/src/types/` for unused type definitions and type inconsistencies — remove unused types, fix confirmed inconsistencies

### Audit & Fix: Infrastructure Code Quality

- [ ] T088 [P] [US5] Audit `solune/scripts/` for dead code, duplicated logic, and hardcoded values — fix confirmed issues
- [ ] T089 [P] [US5] Audit `solune/docs/` for outdated or incorrect documentation that references changed code — fix confirmed issues

### Code Quality TODO Flags & Validation

- [ ] T090 [US5] For each ambiguous code quality finding that would require API changes or architectural modification, add `# TODO(bug-bash):` comment per contract format
- [ ] T091 [US5] Run full backend and frontend test suites — verify all pass after code quality fixes
- [ ] T092 [US5] Run linting and formatting checks — `cd solune/backend && python -m ruff check src tests && python -m ruff format --check src tests` and `cd solune/frontend && npm run lint` — verify clean

**Checkpoint**: All code quality issues resolved or flagged. Full test suite and lint pass. US5 is independently testable and complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary generation, and cross-story verification

- [ ] T093 Run full backend validation suite — `cd solune/backend && python -m pytest tests/ -v && python -m ruff check src tests && python -m ruff format --check src tests && python -m pyright src`
- [ ] T094 [P] Run full frontend validation suite — `cd solune/frontend && npm test && npm run lint && npm run type-check && npm run build`
- [ ] T095 Compile the Bug Report Summary Table per contract in `specs/001-bug-basher/contracts/bug-report-schema.md` — list every bug found with sequential number, file path, line(s), category, description, and status (✅ Fixed or ⚠️ Flagged)
- [ ] T096 Verify commit messages follow the contract format `fix(<category>): <short description>` per `specs/001-bug-basher/contracts/bug-report-schema.md`
- [ ] T097 Verify no new dependencies added — compare `solune/backend/pyproject.toml` and `solune/frontend/package.json` before and after all fixes
- [ ] T098 Verify no public API surface changes — compare HTTP endpoint signatures in `solune/backend/src/api/` before and after all fixes
- [ ] T099 Run quickstart.md final validation steps per `specs/001-bug-basher/quickstart.md` Step 4 — all backend and frontend checks must pass
- [ ] T100 Cross-reference all `# TODO(bug-bash):` comments in the codebase against the summary table — ensure every flagged entry has a corresponding TODO comment and vice versa

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1: Security (Phase 3)**: Depends on Foundational completion — MUST complete before any other user story per SC-009
- **US2: Runtime (Phase 4)**: Depends on US1 completion (SC-009: no lower-priority fix while known security issues remain)
- **US3: Logic (Phase 5)**: Depends on US2 completion (SC-009 priority ordering)
- **US4: Test Gaps (Phase 6)**: Depends on US3 completion (prior fixes may introduce new test requirements)
- **US5: Code Quality (Phase 7)**: Depends on US4 completion (test quality must be established before removing code)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: MUST complete first — security is highest priority (SC-009)
- **US2 (P2)**: Can start after US1 is complete and validated
- **US3 (P3)**: Can start after US2 is complete and validated
- **US4 (P4)**: Can start after US3 is complete (bug fixes may change test requirements)
- **US5 (P5)**: Can start after US4 is complete (need accurate test coverage before removing code)

### Within Each User Story

1. Audit high-risk files first (services → middleware → API routes → config → frontend)
2. Fix confirmed bugs with regression tests
3. Flag ambiguous issues with `# TODO(bug-bash):` comments
4. Run full test suite + lint to validate the story's fixes
5. Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (backend/frontend deps); T004–T007 can run in parallel (independent baseline checks)
- **Phase 2**: T009, T010, T011 can run in parallel (independent inventory tasks)
- **Within each User Story**: Tasks marked [P] within the same category can run in parallel (they audit different files)
- **Cross-story**: User stories CANNOT run in parallel — strict priority ordering per SC-009

---

## Parallel Example: User Story 1 (Security)

```bash
# Launch parallel security audits for independent service files:
Task T014: "Audit encryption.py for key management flaws"
Task T015: "Audit github_auth.py for OAuth scope issues"
Task T016: "Audit guard_service.py for path protection bypass"
Task T017: "Audit app_service.py for path traversal"
Task T018: "Audit database stores for SQL injection"
Task T019: "Audit signal services for injection risks"

# Launch parallel security audits for independent middleware:
Task T021: "Audit csp.py for CSP header completeness"
Task T022: "Audit rate_limit.py for bypass risks"
Task T023: "Audit config.py for hardcoded secrets"

# Launch parallel frontend security audits:
Task T026: "Audit frontend components for XSS risks"
Task T027: "Audit api.ts for insecure request patterns"
Task T028: "Audit nginx.conf for security header gaps"
Task T029: "Audit docker-compose.yml for infrastructure security"
```

---

## Parallel Example: User Story 4 (Test Quality)

```bash
# Launch parallel test quality audits:
Task T067: "Audit conftest.py and helpers for fixture scope issues"
Task T069: "Audit async tests for missing pytest-asyncio markers"
Task T071: "Identify untested code paths in API routes"
Task T072: "Identify untested code paths in middleware"
Task T073: "Audit frontend tests for mock leaks"
Task T074: "Identify untested frontend code paths"
Task T075: "Audit error boundary tests for completeness"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — Security)

1. Complete Phase 1: Setup — establish baseline
2. Complete Phase 2: Foundational — understand codebase
3. Complete Phase 3: User Story 1 — fix all security vulnerabilities
4. **STOP and VALIDATE**: Run full test suite + lint, verify security regression tests
5. Deliver MVP: Security-hardened codebase with regression tests

### Incremental Delivery

1. Complete Setup + Foundational → Baseline established
2. Add US1 (Security) → Test independently → Deliver (MVP: security hardened!)
3. Add US2 (Runtime) → Test independently → Deliver (stable + secure)
4. Add US3 (Logic) → Test independently → Deliver (correct + stable + secure)
5. Add US4 (Test Quality) → Test independently → Deliver (well-tested codebase)
6. Add US5 (Code Quality) → Test independently → Deliver (clean, maintainable codebase)
7. Each story adds value without breaking previous stories

### Sequential Execution (Required)

Due to SC-009 (no lower-priority fix while known higher-priority issues remain), user stories MUST be executed sequentially:
- Developer completes US1 (Security) fully before starting US2 (Runtime)
- Developer completes US2 (Runtime) fully before starting US3 (Logic)
- And so on through US5 (Code Quality)
- Within each story, parallel tasks can be executed by multiple developers

---

## Notes

- [P] tasks = different files, no dependencies on other in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- Per SC-009, strict priority ordering: P1 → P2 → P3 → P4 → P5
- Commit after each fix with format `fix(<category>): <short description>`
- Regression test naming: `test_bug_NNN_<descriptive_name>` (backend) or `it('bug #NNN: <name>')` (frontend)
- Total files to audit: ~100+ backend files, ~80+ frontend files, ~10 infrastructure files
- Expected output: Summary table per `specs/001-bug-basher/contracts/bug-report-schema.md`
