# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/042-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md, contracts/

**Tests**: Tests are **mandatory** for this feature (FR-003, FR-004, FR-006). Every bug fix MUST include at least one regression test.

**Organization**: Tasks are grouped by user story (bug category) to enable independent, priority-ordered implementation. Each user story maps to one bug category and can be validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=Security, US2=Runtime, US3=Logic, US4=Test Quality, US5=Code Quality)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`
- **Config**: `docker-compose.yml`, `solune/docker-compose.yml`, `solune/.env.example`, `solune/guard-config.yml`
- **Tests**: Backend unit → `solune/backend/tests/unit/`, Backend integration → `solune/backend/tests/integration/`, Frontend → co-located `*.test.{ts,tsx}`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the environment, verify all tools are operational, and establish the baseline test state before making any changes.

- [ ] T001 Verify backend test suite passes with `cd solune/backend && python -m pytest tests/ -v`
- [ ] T002 [P] Verify frontend test suite passes with `cd solune/frontend && npx vitest run`
- [ ] T003 [P] Verify backend linting passes with `cd solune/backend && python -m ruff check src/`
- [ ] T004 [P] Verify frontend linting passes with `cd solune/frontend && npm run lint`
- [ ] T005 Record baseline test counts and existing failures for comparison after all fixes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Generate the file inventory for all five review categories and identify high-level patterns before diving into per-file review. This ensures no file is skipped and review is systematic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Inventory all backend source files in `solune/backend/src/` (API routes, services, models, middleware, config, utils) and record count
- [ ] T007 [P] Inventory all frontend source files in `solune/frontend/src/` (components, hooks, pages, services, utils, types) and record count
- [ ] T008 [P] Inventory all configuration files (`docker-compose.yml`, `solune/docker-compose.yml`, `solune/.env.example`, `solune/guard-config.yml`, `solune/frontend/nginx.conf`, `.devcontainer/`) and record count
- [ ] T009 [P] Inventory all test files in `solune/backend/tests/` and `solune/frontend/src/**/*.test.{ts,tsx}` and record count
- [ ] T010 Create tracking document (in-memory or temporary) mapping each file to its review status (not-started / reviewed / bugs-found / clean) to ensure SC-001 (100% file review)

**Checkpoint**: File inventory complete — all files catalogued, review can proceed by category.

---

## Phase 3: User Story 1 — Security Vulnerability Remediation (Priority: P1) 🎯 MVP

**Goal**: Identify and fix all security vulnerabilities — auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation — across the entire codebase per the security-review contract.

**Independent Test**: Run full backend + frontend test suite after all security fixes; verify no hardcoded secrets remain in source; verify all API routes have proper auth; verify input validation on all user-facing endpoints.

### 3a: Secret & Credential Exposure (Security Contract §CQ: Secrets)

- [ ] T011 [P] [US1] Audit `solune/backend/src/config.py` for hardcoded secrets, tokens, or API keys; fix by replacing with environment variable references and add regression test in `solune/backend/tests/unit/test_config_security.py`
- [ ] T012 [P] [US1] Audit `solune/.env.example` for real secret values (should contain only placeholder patterns); fix any real values and add validation test in `solune/backend/tests/unit/test_config_security.py`
- [ ] T013 [P] [US1] Audit `docker-compose.yml` and `solune/docker-compose.yml` for hardcoded secrets in environment variables or build args; fix by referencing env vars and add regression test
- [ ] T014 [P] [US1] Search all backend source files `solune/backend/src/**/*.py` for hardcoded passwords, tokens, API keys, or secret strings using pattern search (`password=`, `token=`, `secret=`, `api_key=`); fix each finding with env var reference and add regression tests in `solune/backend/tests/unit/test_config_security.py`
- [ ] T015 [P] [US1] Search all frontend source files `solune/frontend/src/**/*.{ts,tsx}` for hardcoded secrets or tokens; fix each finding and add regression tests

### 3b: Authentication & Authorization Bypasses (Security Contract §Auth)

- [ ] T016 [P] [US1] Audit every API route file in `solune/backend/src/api/*.py` to verify all sensitive endpoints include auth dependency injection; fix missing auth checks and add regression tests in `solune/backend/tests/unit/test_auth_enforcement.py`
- [ ] T017 [P] [US1] Audit `solune/backend/src/middleware/admin_guard.py` and `solune/guard-config.yml` for guard configuration correctness — verify protected paths are correctly specified; fix misconfigurations and add regression test in `solune/backend/tests/unit/test_guard_config.py`
- [ ] T018 [P] [US1] Audit `solune/backend/src/middleware/` (all middleware files) for correct ordering and security header enforcement; fix issues and add regression tests in `solune/backend/tests/unit/test_middleware_security.py`

### 3c: Injection Risks (Security Contract §Injection)

- [ ] T019 [P] [US1] Search all backend files for SQL injection vectors: f-strings or `.format()` in SQL queries (`solune/backend/src/**/*.py`); fix by converting to parameterized queries and add regression tests in `solune/backend/tests/unit/test_sql_injection.py`
- [ ] T020 [P] [US1] Search all backend files for command injection vectors: `subprocess`, `os.system`, `os.popen` calls with unsanitized user input (`solune/backend/src/**/*.py`); fix by adding input validation and add regression tests
- [ ] T021 [P] [US1] Audit prompt template files in `solune/backend/src/prompts/` for template injection risks; fix by sanitizing user inputs before interpolation and add regression tests
- [ ] T022 [P] [US1] Audit `solune/backend/src/services/app_service.py` for path traversal — verify all filesystem operations use `_safe_app_path()` consistently; fix any direct path construction and add regression test in `solune/backend/tests/unit/test_path_traversal.py`

### 3d: Input Validation (Security Contract §Validation)

- [ ] T023 [P] [US1] Audit all API route files in `solune/backend/src/api/*.py` for endpoints accepting user input without Pydantic model validation; fix by adding proper request body validation and add regression tests
- [ ] T024 [P] [US1] Audit file upload endpoints for missing file type/size validation; fix by adding validation checks and add regression tests

### 3e: Insecure Defaults (Security Contract §Defaults)

- [ ] T025 [P] [US1] Audit `solune/backend/src/config.py` for insecure default settings (debug mode, permissive CORS, disabled security checks); fix by applying secure defaults and add regression tests in `solune/backend/tests/unit/test_secure_defaults.py`
- [ ] T026 [P] [US1] Audit `solune/frontend/nginx.conf` for missing security headers (CSP, X-Frame-Options, server_tokens); fix and add configuration validation test
- [ ] T027 [P] [US1] Audit `solune/backend/src/services/encryption.py` for silent fallback to plaintext on invalid key (known issue from security audit); fix by raising explicit error and add regression test in `solune/backend/tests/unit/test_encryption_security.py`
- [ ] T028 [P] [US1] Audit `solune/backend/src/services/github_auth.py` for OAuth scope configuration (known issue: broad `repo` scope); fix or flag with `TODO(bug-bash)` if scope change requires API surface change

### 3f: Security Phase Validation

- [ ] T029 [US1] Run full backend test suite `cd solune/backend && python -m pytest tests/ -v` and verify all tests pass including new security regression tests
- [ ] T030 [US1] Run full frontend test suite `cd solune/frontend && npx vitest run` and verify all tests pass
- [ ] T031 [US1] Run backend linting `cd solune/backend && python -m ruff check src/` and verify zero new violations
- [ ] T032 [US1] Run frontend linting `cd solune/frontend && npm run lint` and verify zero new violations

**Checkpoint**: All security vulnerabilities addressed. Application is protected against common attack vectors. Full test suite green.

---

## Phase 4: User Story 2 — Runtime Error Elimination (Priority: P2)

**Goal**: Identify and fix all runtime errors — unhandled exceptions, resource leaks, null/None references, missing imports, type errors — across the entire codebase per the runtime-error-review contract.

**Independent Test**: Run full test suite after all runtime fixes; verify no unhandled exceptions on error paths; verify all resources are properly cleaned up.

### 4a: Database & Resource Leaks (Runtime Contract §RT2)

- [ ] T033 [P] [US2] Audit `solune/backend/src/services/database.py` for database connection leaks — verify all connections use context managers or try/finally; fix and add regression test in `solune/backend/tests/unit/test_database_resource_cleanup.py`
- [ ] T034 [P] [US2] Audit `solune/backend/src/services/chat_store.py` for connection lifecycle issues and resource cleanup; fix and add regression test in `solune/backend/tests/unit/test_chat_store_resource.py`
- [ ] T035 [P] [US2] Search all backend service files `solune/backend/src/services/**/*.py` for `open()` calls not wrapped in `with` statements; fix with context managers and add regression tests
- [ ] T036 [P] [US2] Audit `solune/backend/src/services/websocket.py` for WebSocket connection lifecycle — verify close handlers and cleanup; fix and add regression test

### 4b: Unhandled Exceptions (Runtime Contract §RT1)

- [ ] T037 [P] [US2] Audit all async route handlers in `solune/backend/src/api/*.py` for operations that can fail (DB queries, file I/O, HTTP calls, JSON parsing) without try/except; fix with appropriate error handling and add regression tests in `solune/backend/tests/unit/test_error_handling.py`
- [ ] T038 [P] [US2] Audit all service files in `solune/backend/src/services/*.py` for unhandled exceptions in critical operations; fix with try/except and appropriate logging and add regression tests
- [ ] T039 [P] [US2] Audit `solune/backend/src/main.py` for startup error handling — verify graceful handling of missing config, unavailable DB, port conflicts; fix and add regression test

### 4c: Null/None References (Runtime Contract §RT3)

- [ ] T040 [P] [US2] Search all backend files for unsafe dictionary access (`dict["key"]` on optional keys instead of `dict.get("key")`); fix with safe access patterns and add regression tests in `solune/backend/tests/unit/test_null_safety.py`
- [ ] T041 [P] [US2] Audit backend model files `solune/backend/src/models/*.py` for optional fields accessed without null guards; fix and add regression tests
- [ ] T042 [P] [US2] Audit frontend hooks `solune/frontend/src/hooks/*.ts` for missing optional chaining (`?.`) on potentially undefined values; fix and add regression tests

### 4d: Type Errors & Import Issues (Runtime Contract §RT4/RT5)

- [ ] T043 [P] [US2] Audit all backend files for datetime parsing issues with `Z` suffix (known issue: `fromisoformat` cannot parse trailing `Z`); fix by normalizing to `+00:00` and add regression test in `solune/backend/tests/unit/test_datetime_parsing.py`
- [ ] T044 [P] [US2] Audit `solune/backend/src/models/*.py` for enum value mismatches between database schema and code (known issue: `chat_recommendations` stores `accepted`, code uses `confirmed`); fix or flag with `TODO(bug-bash)` and add regression test
- [ ] T045 [P] [US2] Search all backend files for missing or incorrect imports that would fail at runtime; fix and add regression tests

### 4e: Frontend Runtime Issues (Runtime Contract §Hooks/Components)

- [ ] T046 [P] [US2] Audit all frontend hooks in `solune/frontend/src/hooks/*.ts` for `useEffect` missing cleanup return functions (potential memory leaks and race conditions); fix and add regression tests in co-located test files
- [ ] T047 [P] [US2] Audit frontend components for uncaught promise rejections in async handlers; fix with error boundaries or try/catch and add regression tests

### 4f: Runtime Phase Validation

- [ ] T048 [US2] Run full backend test suite `cd solune/backend && python -m pytest tests/ -v` and verify all tests pass including new runtime regression tests
- [ ] T049 [US2] Run full frontend test suite `cd solune/frontend && npx vitest run` and verify all tests pass
- [ ] T050 [US2] Run linting (backend + frontend) and verify zero new violations

**Checkpoint**: All runtime errors addressed. Application runs reliably without crashes or resource leaks. Full test suite green.

---

## Phase 5: User Story 3 — Logic Bug Correction (Priority: P3)

**Goal**: Identify and fix all logic bugs — incorrect state transitions, off-by-one errors, wrong return values, broken control flow, data inconsistencies — across the entire codebase per the logic-bug-review contract.

**Independent Test**: Run full test suite after all logic fixes; verify correct behavior at boundary conditions; verify state transitions are valid.

### 5a: State Transition & Enum Errors (Logic Contract §LB1)

- [ ] T051 [P] [US3] Audit all model files `solune/backend/src/models/*.py` for enum-based status fields and verify transitions match database constraints; fix mismatches and add regression tests in `solune/backend/tests/unit/test_state_transitions.py`
- [ ] T052 [P] [US3] Audit service files that perform status updates `solune/backend/src/services/*.py` for missing state validation before transitions; fix by adding pre-transition checks and add regression tests
- [ ] T053 [P] [US3] Audit frontend state management in `solune/frontend/src/hooks/*.ts` for incorrect state transitions in reducers; fix and add regression tests

### 5b: Off-by-One & Boundary Errors (Logic Contract §LB2)

- [ ] T054 [P] [US3] Audit all API route files `solune/backend/src/api/*.py` for pagination logic errors (page number, offset calculation, total count); fix boundary conditions and add regression tests in `solune/backend/tests/unit/test_pagination.py`
- [ ] T055 [P] [US3] Search all backend files for array slicing and loop boundary issues; fix and add regression tests

### 5c: Incorrect Return Values (Logic Contract §LB3)

- [ ] T056 [P] [US3] Audit API route handlers `solune/backend/src/api/*.py` for incorrect HTTP status codes in responses; fix and add regression tests in `solune/backend/tests/unit/test_status_codes.py`
- [ ] T057 [P] [US3] Audit service methods with multiple return paths `solune/backend/src/services/*.py` for incorrect or inconsistent return types; fix and add regression tests

### 5d: Control Flow & Data Flow Errors (Logic Contract §LB4/LB5)

- [ ] T058 [P] [US3] Search all backend files for unreachable code after early returns, raise, or break statements; fix by removing or reordering and add regression tests
- [ ] T059 [P] [US3] Audit boolean logic in conditionals across `solune/backend/src/services/*.py` for inverted or incorrect operators (`and` vs `or`); fix and add regression tests
- [ ] T060 [P] [US3] Audit data transformations between API → service → database layers for field mapping correctness (Pydantic serialization, dict conversions); fix inconsistencies and add regression tests in `solune/backend/tests/unit/test_data_flow.py`
- [ ] T061 [P] [US3] Audit frontend service files `solune/frontend/src/services/*.ts` for API response mapping errors (field names, type coercions); fix and add regression tests

### 5e: Logic Phase Validation

- [ ] T062 [US3] Run full backend test suite and verify all tests pass including new logic regression tests
- [ ] T063 [US3] Run full frontend test suite and verify all tests pass
- [ ] T064 [US3] Run linting (backend + frontend) and verify zero new violations

**Checkpoint**: All logic bugs addressed. Application produces correct results and handles edge cases properly. Full test suite green.

---

## Phase 6: User Story 4 — Test Quality Improvement (Priority: P4)

**Goal**: Identify and fix test gaps and low-quality tests — mock leaks, weak assertions, tests that pass for the wrong reason, missing coverage — per the test-quality-review contract.

**Independent Test**: Verify that each updated test fails when the behavior it guards is intentionally broken (mutation testing principle).

### 6a: Mock Leaks (Test Quality Contract §TQ1)

- [ ] T065 [P] [US4] Audit all backend test files `solune/backend/tests/**/*.py` for `MagicMock` or `Mock()` objects that leak into production code paths (e.g., as file paths, DB URIs, config values); fix by properly scoping mocks with `with` statements or `@patch` decorators
- [ ] T066 [P] [US4] Audit backend `solune/backend/tests/conftest.py` for fixtures that create mock objects used across multiple tests without proper cleanup; fix scope issues

### 6b: Weak & Meaningless Assertions (Test Quality Contract §TQ2)

- [ ] T067 [P] [US4] Search backend tests for `assert True`, `assert response is not None`, or other tautological assertions in `solune/backend/tests/**/*.py`; replace with meaningful assertions that validate specific behavior
- [ ] T068 [P] [US4] Search frontend tests for `expect(...).toBeTruthy()`, `expect(...).toBeDefined()`, or other weak assertions in `solune/frontend/src/**/*.test.{ts,tsx}`; replace with specific value or behavior assertions

### 6c: Tests That Pass for Wrong Reason (Test Quality Contract §TQ3)

- [ ] T069 [P] [US4] Audit backend tests for tests that mock the exact function they should be testing (asserting against mock return values instead of real behavior) in `solune/backend/tests/**/*.py`; fix by restructuring test to validate actual logic
- [ ] T070 [P] [US4] Audit frontend tests for tests with no assertions or where the assertion can never fail in `solune/frontend/src/**/*.test.{ts,tsx}`; fix with meaningful assertions

### 6d: Missing Test Coverage (Test Quality Contract §TQ4)

- [ ] T071 [P] [US4] Identify critical backend code paths with no test coverage (security-relevant code, error handlers, edge cases in services) by cross-referencing `solune/backend/src/services/*.py` against `solune/backend/tests/`; add tests for highest-risk uncovered paths
- [ ] T072 [P] [US4] Identify critical frontend code paths with no test coverage (error states, edge cases in hooks/components) by cross-referencing `solune/frontend/src/hooks/*.ts` against co-located test files; add tests for highest-risk uncovered paths

### 6e: Test Isolation Issues (Test Quality Contract §TQ5)

- [ ] T073 [P] [US4] Audit backend tests for test order dependencies and shared mutable state between tests in `solune/backend/tests/**/*.py`; fix by ensuring each test sets up and tears down its own state
- [ ] T074 [P] [US4] Audit frontend tests for improper cleanup of rendered components and event listeners; fix by adding proper cleanup in afterEach blocks

### 6f: Test Quality Phase Validation

- [ ] T075 [US4] Run full backend test suite and verify all tests pass with improved assertions
- [ ] T076 [US4] Run full frontend test suite and verify all tests pass
- [ ] T077 [US4] Run linting (backend + frontend) and verify zero new violations

**Checkpoint**: Test suite is trustworthy — tests validate real behavior, mocks are properly scoped, and critical paths are covered. Full test suite green.

---

## Phase 7: User Story 5 — Code Quality Cleanup (Priority: P5)

**Goal**: Remove dead code, resolve duplicated logic, extract hardcoded values, surface silent failures — per the code-quality-review contract.

**Independent Test**: Verify that removed dead code does not break any tests; verify that consolidated logic passes all existing tests; verify that newly added error messages are surfaced.

### 7a: Dead Code Removal (Code Quality Contract §CQ1)

- [ ] T078 [P] [US5] Run `cd solune/backend && python -m ruff check src/ --select F841,F401` to identify unused variables (F841) and unused imports (F401) across all backend files; remove dead code
- [ ] T079 [P] [US5] Search all backend service files `solune/backend/src/services/*.py` for functions defined but never called (compare definitions vs usages); remove or flag with `TODO(bug-bash)` if unsure about dynamic usage
- [ ] T080 [P] [US5] Search all frontend source files `solune/frontend/src/**/*.{ts,tsx}` for unused exports, unreferenced components, and dead utility functions; remove dead code
- [ ] T081 [P] [US5] Search backend files for commented-out code blocks and `if False:` patterns in `solune/backend/src/**/*.py`; remove

### 7b: Silent Failures (Code Quality Contract §CQ5)

- [ ] T082 [P] [US5] Search all backend files for bare `except: pass`, `except Exception: pass`, or empty except blocks in `solune/backend/src/**/*.py`; add appropriate error logging at WARNING or ERROR level and add regression tests
- [ ] T083 [P] [US5] Search frontend files for empty `.catch(() => {})` blocks in `solune/frontend/src/**/*.{ts,tsx}`; add error logging or user feedback and add regression tests
- [ ] T084 [P] [US5] Audit `solune/backend/src/logging_utils.py` and verify that `StructuredJsonFormatter` does not silently drop error context (known concern: only whitelisted extra fields are emitted); fix or flag with `TODO(bug-bash)`

### 7c: Hardcoded Values (Code Quality Contract §CQ4)

- [ ] T085 [P] [US5] Search all backend files for magic numbers in business logic (timeout values, retry counts, page sizes, cache TTLs) in `solune/backend/src/**/*.py`; extract to named constants in `solune/backend/src/constants.py`
- [ ] T086 [P] [US5] Search frontend files for hardcoded URLs, numeric literals, or string constants that appear in multiple locations in `solune/frontend/src/**/*.{ts,tsx}`; extract to shared constants

### 7d: Duplicated Logic (Code Quality Contract §CQ3)

- [ ] T087 [P] [US5] Identify duplicated code blocks (5+ identical lines) across backend service files `solune/backend/src/services/**/*.py`; consolidate into shared utilities or flag with `TODO(bug-bash)` if consolidation would change architecture
- [ ] T088 [P] [US5] Identify duplicated logic across frontend component files `solune/frontend/src/components/**/*.{ts,tsx}`; consolidate into shared hooks/utilities or flag with `TODO(bug-bash)`

### 7e: Unreachable Branches (Code Quality Contract §CQ2)

- [ ] T089 [P] [US5] Search backend files for code after unconditional `return`, `raise`, `break`, or `continue` in `solune/backend/src/**/*.py`; remove unreachable code
- [ ] T090 [P] [US5] Search frontend files for unreachable branches and always-true/false conditions in `solune/frontend/src/**/*.{ts,tsx}`; remove

### 7f: Code Quality Phase Validation

- [ ] T091 [US5] Run full backend test suite and verify all tests pass after dead code removal and refactoring
- [ ] T092 [US5] Run full frontend test suite and verify all tests pass
- [ ] T093 [US5] Run linting (backend + frontend) and verify zero new violations
- [ ] T094 [US5] Verify no architecture or public API changes by reviewing `git diff --stat` scope

**Checkpoint**: Codebase is clean — no dead code, no silent failures, no magic numbers, no duplicated logic. Full test suite green.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary generation, and cross-cutting checks that span all user stories.

- [ ] T095 Run full backend test suite one final time: `cd solune/backend && python -m pytest tests/ -v`
- [ ] T096 [P] Run full frontend test suite one final time: `cd solune/frontend && npx vitest run`
- [ ] T097 [P] Run backend linting one final time: `cd solune/backend && python -m ruff check src/`
- [ ] T098 [P] Run frontend linting one final time: `cd solune/frontend && npm run lint`
- [ ] T099 Verify SC-001: Confirm 100% of files were reviewed by cross-referencing file inventory (T006–T009) against review tracking
- [ ] T100 Verify SC-007: Confirm no architecture changes, no public API changes, no new dependencies by reviewing complete `git diff --stat`
- [ ] T101 Generate final Summary Table (FR-013) with all BugReportEntry items: sequential number, file path, line(s), category, description, status (✅ Fixed / ⚠️ Flagged)
- [ ] T102 Verify Summary Table completeness: every fixed bug has commit SHA and regression test; every flagged bug has `TODO(bug-bash)` comment in source
- [ ] T103 Run quickstart.md validation — execute the verification steps from `solune/specs/042-bug-basher/quickstart.md` to confirm the entire workflow completes successfully

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 — Security (Phase 3)**: Depends on Foundational phase completion — should be done first (P1)
- **User Story 2 — Runtime (Phase 4)**: Depends on Foundational; can start after Phase 3 or in parallel if different files
- **User Story 3 — Logic (Phase 5)**: Depends on Foundational; can start after Phase 4 or in parallel if different files
- **User Story 4 — Test Quality (Phase 6)**: Depends on Foundational; should follow Phases 3–5 to avoid re-fixing tests broken by earlier fixes
- **User Story 5 — Code Quality (Phase 7)**: Depends on Foundational; should be last user story since dead code identification is affected by earlier changes
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 — Security (P1)**: Can start after Foundational — highest priority, should complete first
- **US2 — Runtime (P2)**: Can start after Foundational — recommended to follow US1 to avoid fixing code that was already changed for security
- **US3 — Logic (P3)**: Can start after Foundational — recommended to follow US2 to avoid fixing code that was already changed for runtime errors
- **US4 — Test Quality (P4)**: Should follow US1–US3 since earlier bug fixes may break or modify existing tests
- **US5 — Code Quality (P5)**: Should be last since dead code identification depends on knowing which code is actually used after all fixes

### Within Each User Story

- Audit tasks marked [P] can run in parallel (different files)
- Validation tasks (T029–T032, T048–T050, T062–T064, T075–T077, T091–T094) must run after all fixes in that phase
- Each fix must include its regression test in the same commit
- Test suite must be green before moving to next user story

### Parallel Opportunities

- All Setup tasks T002–T004 can run in parallel
- All Foundational inventory tasks T006–T009 can run in parallel
- Within US1 (Security): Sub-sections 3a–3e can run in parallel (different file groups)
- Within US2 (Runtime): Sub-sections 4a–4e can run in parallel (different file groups)
- Within US3 (Logic): Sub-sections 5a–5d can run in parallel (different file groups)
- Within US4 (Test Quality): Sub-sections 6a–6e can run in parallel (backend vs frontend)
- Within US5 (Code Quality): Sub-sections 7a–7e can run in parallel (different concerns)
- Phase 8 validation tasks T096–T098 can run in parallel

---

## Parallel Example: User Story 1 (Security)

```bash
# Launch all secret/credential audits together (different files):
Task T011: "Audit config.py for hardcoded secrets"
Task T012: "Audit .env.example for real secret values"
Task T013: "Audit docker-compose.yml for hardcoded secrets"
Task T014: "Search all backend source for hardcoded credentials"
Task T015: "Search all frontend source for hardcoded secrets"

# Launch all injection risk audits together (different files):
Task T019: "Search backend for SQL injection vectors"
Task T020: "Search backend for command injection vectors"
Task T021: "Audit prompt templates for injection risks"
Task T022: "Audit app_service.py for path traversal"
```

---

## Parallel Example: User Story 2 (Runtime)

```bash
# Launch all resource leak audits together (different files):
Task T033: "Audit database.py for connection leaks"
Task T034: "Audit chat_store.py for connection lifecycle"
Task T035: "Search services for open() without context managers"
Task T036: "Audit websocket.py for connection cleanup"

# Launch all null safety audits together (different files):
Task T040: "Search backend for unsafe dictionary access"
Task T041: "Audit model files for optional field access"
Task T042: "Audit frontend hooks for missing optional chaining"
```

---

## Implementation Strategy

### MVP First (User Story 1 — Security Only)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 2: Foundational (file inventory)
3. Complete Phase 3: User Story 1 — Security (P1)
4. **STOP and VALIDATE**: Full test suite passes, all security fixes verified
5. Deploy/demo if ready — application is now secure

### Incremental Delivery

1. Complete Setup + Foundational → Baseline established
2. Add US1 — Security → Test independently → Commit (MVP! 🎯)
3. Add US2 — Runtime → Test independently → Commit (stable application)
4. Add US3 — Logic → Test independently → Commit (correct application)
5. Add US4 — Test Quality → Test independently → Commit (trustworthy tests)
6. Add US5 — Code Quality → Test independently → Commit (clean codebase)
7. Complete Polish → Generate Summary Table → Final validation
8. Each story adds value without breaking previous stories

### Recommended Sequential Strategy

Given that bug fixes in one category can affect files reviewed in another category, the **recommended** approach is sequential by priority:

1. Team completes Setup + Foundational together
2. **Security (P1)** → complete and validate before moving on
3. **Runtime (P2)** → complete and validate
4. **Logic (P3)** → complete and validate
5. **Test Quality (P4)** → complete and validate
6. **Code Quality (P5)** → complete and validate
7. **Polish** → final validation and summary generation

This sequential approach avoids merge conflicts and ensures earlier priority fixes are not overwritten by later changes.

---

## Notes

- [P] tasks = different files, no dependencies between them
- [Story] label maps task to specific user story for traceability (US1=Security, US2=Runtime, US3=Logic, US4=Test Quality, US5=Code Quality)
- Each user story maps to one bug category from the spec
- Tests are **mandatory** — every bug fix requires at least one regression test (FR-003)
- Commit format: `fix(<category>): <short description>` with What/Why/How body (FR-008)
- Ambiguous issues → `TODO(bug-bash):` comment, no code change (FR-005)
- No architecture changes, no new dependencies, no public API changes (FR-009, FR-010)
- Preserve existing code style (FR-011) — ruff line-length=100 for Python
- Only include files with bugs in summary table (FR-014)
- Stop at any checkpoint to validate the story independently
