# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/001-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests (regression tests) ARE required — the spec mandates at least one new regression test per bug fix (FR-002, FR-013).

**Organization**: Tasks are grouped by user story (P1–P5 bug categories) to enable independent implementation and validation of each category phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- **Backend tests**: `solune/backend/tests/`
- **Frontend tests**: `solune/frontend/src/**/*.test.*`
- **Infrastructure**: `.github/workflows/`, `solune/scripts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment initialization, baseline validation, and file inventory

- [ ] T001 Set up backend development environment per quickstart.md in solune/backend/ (python venv, pip install -e ".[dev]")
- [ ] T002 Set up frontend development environment per quickstart.md in solune/frontend/ (npm ci)
- [ ] T003 Run full backend CI validation baseline: ruff check, ruff format --check, bandit, pyright, pytest in solune/backend/
- [ ] T004 Run full frontend CI validation baseline: npm run lint, npm run type-check, npm run test, npm run build in solune/frontend/
- [ ] T005 Generate complete file inventory of all source files to audit (~143 backend .py, ~419 frontend .ts/.tsx, ~5 infra files) and record counts

**Checkpoint**: Environment is green, baseline validation passes, file inventory complete — ready to begin category-by-category auditing.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish bug-tracking output structure and commit conventions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create the summary table markdown structure per Contract 3 in specs/001-bug-basher/contracts/process-contracts.md (output template for tracking all findings)
- [ ] T007 Validate commit message format per Contract 4 (format: `fix(<category>): <what> — <why> — <how>`) and TODO flag format per Contract 5
- [ ] T008 Review the existing handle_service_error() pattern in solune/backend/src/logging_utils.py to understand the established error-handling convention for service files

**Checkpoint**: Output tracking structure ready, conventions documented — category auditing can now begin in priority order.

---

## Phase 3: User Story 1 — Security Vulnerability Remediation (Priority: P1) 🎯 MVP

**Goal**: Audit the entire codebase for security vulnerabilities (auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation) and fix all clear bugs with regression tests.

**Independent Test**: Run the full test suite plus new regression tests for each security fix. Verify no secrets or tokens are exposed in code or configuration. Run `bandit -r src/ -ll -ii --skip B104,B608` with zero new findings.

### Authentication & Session Security

- [ ] T009 [US1] Audit authentication logic in solune/backend/src/services/github_auth.py for auth bypass vulnerabilities, token validation issues, and insecure token handling
- [ ] T010 [US1] Audit session management in solune/backend/src/services/session_store.py for session fixation, improper session invalidation, and session data exposure
- [ ] T011 [US1] Audit auth API routes in solune/backend/src/api/auth.py for authentication bypass paths and missing authorization checks
- [ ] T012 [US1] Audit admin access control in solune/backend/src/middleware/admin_guard.py for privilege escalation and bypass vectors

### Encryption & Secrets

- [ ] T013 [US1] Audit encryption handling in solune/backend/src/services/encryption.py for weak algorithms, key management issues, and insecure defaults
- [ ] T014 [P] [US1] Audit configuration for exposed secrets in solune/backend/src/config.py and verify no hardcoded credentials or tokens exist
- [ ] T015 [P] [US1] Scan all .env.example, .toml, .yml, and .json config files for accidentally committed secrets or insecure default values

### Input Validation & Injection Prevention

- [ ] T016 [US1] Audit database operations in solune/backend/src/services/database.py for SQL injection via non-parameterized queries
- [ ] T017 [US1] Audit chat store in solune/backend/src/services/chat_store.py for SQL injection and verify _safe_json_list() is used for all JSON column parsing
- [ ] T018 [P] [US1] Audit all 21 API route files in solune/backend/src/api/ for missing Pydantic validation on request bodies, path parameters, and query parameters
- [ ] T019 [P] [US1] Audit webhook handlers in solune/backend/src/api/webhooks.py and solune/backend/src/api/webhook_models.py for payload injection and unsanitized logging

### Middleware Security

- [ ] T020 [P] [US1] Audit CSRF protection in solune/backend/src/middleware/csrf.py for bypass vectors and misconfiguration
- [ ] T021 [P] [US1] Audit Content Security Policy in solune/backend/src/middleware/csp.py for overly permissive directives
- [ ] T022 [P] [US1] Audit rate limiting in solune/backend/src/middleware/rate_limit.py for bypass vectors and insufficient limits
- [ ] T023 [P] [US1] Audit request ID middleware in solune/backend/src/middleware/request_id.py for header injection

### Frontend Security

- [ ] T024 [P] [US1] Audit all frontend files in solune/frontend/src/ for XSS vulnerabilities, unsafe dangerouslySetInnerHTML usage, and unsanitized user input rendering
- [ ] T025 [P] [US1] Audit frontend token handling and sensitive data storage in solune/frontend/src/services/ and solune/frontend/src/context/ for token exposure in localStorage/sessionStorage or URLs
- [ ] T026 [P] [US1] Audit frontend API service layer in solune/frontend/src/services/ for missing input sanitization before sending to backend

### Regression Tests & Validation

- [ ] T027 [US1] Write regression tests for each security bug fixed in solune/backend/tests/unit/ (one test per fix, per FR-002/FR-013)
- [ ] T028 [US1] Write regression tests for each frontend security bug fixed in solune/frontend/src/ (colocated .test.ts/.test.tsx files)
- [ ] T029 [US1] Run full backend validation: ruff check, ruff format --check, bandit, pyright, pytest in solune/backend/
- [ ] T030 [US1] Run full frontend validation: npm run lint, npm run type-check, npm run test, npm run build in solune/frontend/
- [ ] T031 [US1] Update summary table with all P1 security findings (file, lines, category=Security, description, status ✅ Fixed or ⚠️ Flagged)

**Checkpoint**: All security vulnerabilities identified, clear bugs fixed with regression tests, ambiguous issues flagged with TODO(bug-bash). Full test suite green. Summary table updated.

---

## Phase 4: User Story 2 — Runtime Error Elimination (Priority: P2)

**Goal**: Audit the entire codebase for runtime errors (unhandled exceptions, race conditions, null/None references, missing imports, type errors, resource leaks) and fix all clear bugs with regression tests.

**Independent Test**: Run the full test suite and verify all new regression tests pass. Confirm resource handles (files, database connections, HTTP clients) are properly managed with `async with` or equivalent.

### Backend Service Exception Handling

- [ ] T032 [US2] Audit all 33 service files in solune/backend/src/services/ for consistent use of handle_service_error() pattern and unhandled exceptions in async methods
- [ ] T033 [US2] Audit service sub-packages in solune/backend/src/services/agents/, solune/backend/src/services/chores/, solune/backend/src/services/copilot_polling/, solune/backend/src/services/github_projects/, solune/backend/src/services/pipelines/, solune/backend/src/services/tools/, solune/backend/src/services/workflow_orchestrator/ for unhandled exceptions
- [ ] T034 [US2] Audit dependency injection in solune/backend/src/dependencies.py for missing error handling and null checks on injected services

### Resource Management

- [ ] T035 [P] [US2] Audit database resource management in solune/backend/src/services/database.py for connection leaks — verify all connections use `async with` and cleanup in error paths
- [ ] T036 [P] [US2] Audit settings store in solune/backend/src/services/settings_store.py for database connection leaks and missing async context managers
- [ ] T037 [P] [US2] Audit all httpx/githubkit usage across solune/backend/src/services/ for HTTP client leaks, missing timeouts, and unclosed sessions

### Null/None References & Type Errors

- [ ] T038 [US2] Audit all service files for unguarded .get() calls, optional field access without None checks, and dictionary key access without validation in solune/backend/src/services/
- [ ] T039 [P] [US2] Audit all 25 Pydantic model files in solune/backend/src/models/ for incorrect type annotations, missing Optional markers, and default value issues

### Frontend Runtime Errors

- [ ] T040 [P] [US2] Audit frontend hooks in solune/frontend/src/hooks/ for null/undefined reference errors, missing error boundaries, and unhandled async errors
- [ ] T041 [P] [US2] Audit frontend context providers in solune/frontend/src/context/ for null reference errors in state management and missing initial state handling
- [ ] T042 [P] [US2] Audit frontend services in solune/frontend/src/services/ for unhandled API response errors, missing null checks on response data, and type mismatches
- [ ] T043 [P] [US2] Audit frontend components in solune/frontend/src/components/ for null/undefined rendering errors and missing optional chaining

### Import & Circular Dependency Issues

- [ ] T044 [P] [US2] Run pyright on solune/backend/src/ and review any import resolution errors, circular dependencies, and type incompatibilities
- [ ] T045 [P] [US2] Run npm run type-check on solune/frontend/ and review any TypeScript import resolution errors and type incompatibilities

### Regression Tests & Validation

- [ ] T046 [US2] Write regression tests for each runtime bug fixed in solune/backend/tests/unit/ (one test per fix, per FR-002/FR-013)
- [ ] T047 [US2] Write regression tests for each frontend runtime bug fixed in solune/frontend/src/ (colocated .test.ts/.test.tsx files)
- [ ] T048 [US2] Run full backend validation: ruff check, ruff format --check, bandit, pyright, pytest in solune/backend/
- [ ] T049 [US2] Run full frontend validation: npm run lint, npm run type-check, npm run test, npm run build in solune/frontend/
- [ ] T050 [US2] Update summary table with all P2 runtime findings (file, lines, category=Runtime, description, status)

**Checkpoint**: All runtime errors identified, clear bugs fixed with regression tests, ambiguous issues flagged. Full test suite green. Summary table updated with P1 + P2 findings.

---

## Phase 5: User Story 3 — Logic Bug Correction (Priority: P3)

**Goal**: Audit the entire codebase for logic bugs (incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, incorrect return values) and fix all clear bugs with regression tests.

**Independent Test**: Run the full test suite plus new tests targeting specific logic paths — state transitions, boundary values, return values, and control flow branches.

### State Machines & Workflows

- [ ] T051 [US3] Audit workflow orchestrator in solune/backend/src/services/workflow_orchestrator/ for incorrect state transitions, missing states, and unreachable workflow paths
- [ ] T052 [US3] Audit pipeline logic in solune/backend/src/services/pipelines/ for incorrect step sequencing, broken control flow, and missing error state handling

### API Response & Return Values

- [ ] T053 [P] [US3] Audit all 21 API route files in solune/backend/src/api/ for incorrect HTTP status codes, wrong return values, and missing response fields
- [ ] T054 [P] [US3] Audit service return values across solune/backend/src/services/ for incorrect types, missing returns in conditional branches, and data inconsistencies

### Boundary & Off-by-One Errors

- [ ] T055 [P] [US3] Audit numeric computations, pagination logic, list slicing, and index operations across solune/backend/src/ for off-by-one errors and boundary condition failures
- [ ] T056 [P] [US3] Audit frontend pagination, list rendering, and index-based operations in solune/frontend/src/ for off-by-one errors and boundary conditions

### Control Flow & Data Consistency

- [ ] T057 [US3] Audit data transformation logic in solune/backend/src/models/ and solune/backend/src/services/ for incorrect mappings, missing fields, and data loss during conversion
- [ ] T058 [P] [US3] Audit frontend state management in solune/frontend/src/context/ and solune/frontend/src/hooks/ for state consistency issues, stale state references, and incorrect state updates
- [ ] T059 [P] [US3] Audit frontend components in solune/frontend/src/components/ for incorrect conditional rendering, broken control flow, and incorrect prop handling

### Regression Tests & Validation

- [ ] T060 [US3] Write regression tests for each logic bug fixed in solune/backend/tests/unit/ (one test per fix, per FR-002/FR-013)
- [ ] T061 [US3] Write regression tests for each frontend logic bug fixed in solune/frontend/src/ (colocated .test.ts/.test.tsx files)
- [ ] T062 [US3] Run full backend validation: ruff check, ruff format --check, bandit, pyright, pytest in solune/backend/
- [ ] T063 [US3] Run full frontend validation: npm run lint, npm run type-check, npm run test, npm run build in solune/frontend/
- [ ] T064 [US3] Update summary table with all P3 logic findings (file, lines, category=Logic, description, status)

**Checkpoint**: All logic bugs identified, clear bugs fixed with regression tests, ambiguous issues flagged. Full test suite green. Summary table updated with P1 + P2 + P3 findings.

---

## Phase 6: User Story 4 — Test Quality Improvement (Priority: P4)

**Goal**: Audit test suites for test gaps and quality issues — untested code paths, tests that pass for the wrong reason, mock leaks, assertions that never fail, and missing edge case coverage.

**Independent Test**: Review test coverage reports, verify mock objects do not leak into production code paths, and ensure every assertion can both pass and fail under correct and incorrect conditions.

### Backend Mock Isolation & Leaks

- [ ] T065 [P] [US4] Search all backend test files in solune/backend/tests/ for MagicMock, patch, and Mock usage — verify mocks do not leak into production code paths (e.g., mock values appearing as file paths, database connections, or URLs)
- [ ] T066 [P] [US4] Audit backend tests for overly broad exception catching (bare except, except Exception) that masks real failures in solune/backend/tests/

### Backend Assertion Effectiveness

- [ ] T067 [P] [US4] Audit backend tests in solune/backend/tests/ for tests with no assertions, tautological assertions (always true), and assertions that check mock behavior rather than actual code behavior
- [ ] T068 [P] [US4] Audit backend tests for tests that pass because of mock setup rather than code correctness (test-for-wrong-reason pattern) in solune/backend/tests/

### Backend Coverage Gaps

- [ ] T069 [US4] Cross-reference all 33 service files + 7 sub-packages in solune/backend/src/services/ with test files in solune/backend/tests/ to identify untested services and untested critical code paths
- [ ] T070 [US4] Identify untested edge cases in critical business logic (error paths, boundary conditions, empty inputs) across solune/backend/src/services/ and add missing test coverage

### Frontend Test Quality

- [ ] T071 [P] [US4] Audit frontend test files in solune/frontend/src/ for mock leaks, tautological assertions, and tests that pass for the wrong reason
- [ ] T072 [P] [US4] Audit frontend test files for missing error case testing, missing edge case coverage, and tests that only cover happy paths in solune/frontend/src/

### Frontend Coverage Gaps

- [ ] T073 [US4] Cross-reference frontend components, hooks, and services in solune/frontend/src/ with test files to identify untested modules and critical untested paths
- [ ] T074 [US4] Add missing test coverage for identified critical frontend paths in solune/frontend/src/ (colocated .test.ts/.test.tsx files)

### Regression Tests & Validation

- [ ] T075 [US4] Write regression tests for each test quality bug fixed in solune/backend/tests/ (verify the mock leak or assertion issue no longer exists)
- [ ] T076 [US4] Write regression tests for each frontend test quality bug fixed in solune/frontend/src/ (colocated test files)
- [ ] T077 [US4] Run full backend validation: ruff check, ruff format --check, bandit, pyright, pytest in solune/backend/
- [ ] T078 [US4] Run full frontend validation: npm run lint, npm run type-check, npm run test, npm run build in solune/frontend/
- [ ] T079 [US4] Update summary table with all P4 test quality findings (file, lines, category=Test Quality, description, status)

**Checkpoint**: All test quality issues identified, clear bugs fixed with regression tests, ambiguous issues flagged. Full test suite green. Summary table updated with P1–P4 findings.

---

## Phase 7: User Story 5 — Code Quality Cleanup (Priority: P5)

**Goal**: Audit the codebase for code quality issues — dead code, unreachable branches, duplicated logic, hardcoded values that should be configurable, missing error messages, and silent failures.

**Independent Test**: Run linters, verify removed dead code does not break any tests, and confirm previously hardcoded values are configurable.

### Dead Code & Unreachable Branches

- [ ] T080 [P] [US5] Scan all backend source files in solune/backend/src/ for dead code — unused functions, unreachable branches after early returns, unused variables not caught by ruff
- [ ] T081 [P] [US5] Scan all frontend source files in solune/frontend/src/ for dead code — unused exports, unreachable branches, unused components and utilities

### Duplicated Logic

- [ ] T082 [P] [US5] Audit backend service files in solune/backend/src/services/ for duplicated logic patterns that could be consolidated without altering public interfaces
- [ ] T083 [P] [US5] Audit frontend components and hooks in solune/frontend/src/ for duplicated logic patterns that could be consolidated

### Hardcoded Values

- [ ] T084 [P] [US5] Audit backend source files in solune/backend/src/ for magic numbers, hardcoded URLs, timeouts, and limits that should be extracted to solune/backend/src/config.py or solune/backend/src/constants.py
- [ ] T085 [P] [US5] Audit frontend source files in solune/frontend/src/ for hardcoded values that should be extracted to solune/frontend/src/constants/

### Silent Failures & Error Handling

- [ ] T086 [P] [US5] Audit backend source files in solune/backend/src/ for empty except blocks, swallowed errors, and missing log statements in error paths
- [ ] T087 [P] [US5] Audit frontend source files in solune/frontend/src/ for silent catch blocks, missing error messages, and unlogged failures

### Regression Tests & Validation

- [ ] T088 [US5] Write regression tests for each code quality fix in solune/backend/tests/unit/ (verify dead code removal doesn't break functionality, extracted constants work correctly)
- [ ] T089 [US5] Write regression tests for each frontend code quality fix in solune/frontend/src/ (colocated .test.ts/.test.tsx files)
- [ ] T090 [US5] Run full backend validation: ruff check, ruff format --check, bandit, pyright, pytest in solune/backend/
- [ ] T091 [US5] Run full frontend validation: npm run lint, npm run type-check, npm run test, npm run build in solune/frontend/
- [ ] T092 [US5] Update summary table with all P5 code quality findings (file, lines, category=Code Quality, description, status)

**Checkpoint**: All code quality issues identified, clear bugs fixed with regression tests, ambiguous issues flagged. Full test suite green. Summary table updated with P1–P5 findings.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary output, and cross-cutting quality checks

- [ ] T093 Compile final summary table per Contract 3 format with all findings across all 5 categories — verify every identified bug is accounted for (FR-010, SC-006)
- [ ] T094 Verify no fix changed the project's architecture or public API surface (FR-004, SC-007) by reviewing all modified files
- [ ] T095 Verify no new dependencies were added (FR-005) by diffing solune/backend/pyproject.toml and solune/frontend/package.json against baseline
- [ ] T096 Verify all commit messages follow Contract 4 format: `fix(<category>): <what> — <why> — <how>` with regression test references
- [ ] T097 Verify all TODO(bug-bash) comments follow Contract 5 format (prefix, at least two options, rationale) by searching codebase
- [ ] T098 Run final full backend validation: ruff check, ruff format --check, bandit, pyright, pytest --cov in solune/backend/ — verify coverage ≥ 75%
- [ ] T099 Run final full frontend validation: npm audit --audit-level=high, npm run lint, npm run type-check, npm run test, npm run build in solune/frontend/
- [ ] T100 Verify all 5 bug categories were fully reviewed (SC-001) and all files in the repository were audited (FR-001)
- [ ] T101 Run quickstart.md validation scenario to confirm end-to-end execution guide is accurate
- [ ] T102 Post final summary table as output per Contract 3

**Checkpoint**: All phases complete. Full test suite green. Linting green. Summary table accounts for every finding. All constraints validated. Bug bash complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1: Security (Phase 3)**: Depends on Foundational (Phase 2) — should be completed FIRST per FR-012
- **US2: Runtime (Phase 4)**: Depends on Foundational (Phase 2) — can start after US1 or in parallel if independent files
- **US3: Logic (Phase 5)**: Depends on Foundational (Phase 2) — can start after US2 or in parallel if independent files
- **US4: Test Quality (Phase 6)**: Depends on Foundational (Phase 2) — best done AFTER US1–US3 since those fixes may affect test quality
- **US5: Code Quality (Phase 7)**: Depends on Foundational (Phase 2) — best done AFTER US1–US4 since those fixes may affect code structure
- **Polish (Phase 8)**: Depends on ALL user stories being complete

### User Story Dependencies

- **US1 Security (P1)**: Can start after Phase 2 — SHOULD be first per FR-012 (security category has highest priority)
- **US2 Runtime (P2)**: Can start after Phase 2 — independent of US1 but recommended after since security fixes may introduce runtime considerations
- **US3 Logic (P3)**: Can start after Phase 2 — independent of US1/US2 but recommended after since prior fixes may alter logic paths
- **US4 Test Quality (P4)**: RECOMMENDED after US1–US3 — prior bug fixes create new test context that should be included in quality review
- **US5 Code Quality (P5)**: RECOMMENDED after US1–US4 — prior fixes may remove dead code or alter duplication patterns

### Within Each User Story

- Backend audit tasks marked [P] can run in parallel (different files)
- Frontend audit tasks marked [P] can run in parallel (different files)
- Regression test tasks depend on their audit tasks completing first
- Full validation runs at the end of each phase
- Summary table update is the final task in each phase

### Parallel Opportunities

**Within Phase 3 (US1 Security):**
```
Parallel group A: T014, T015 (config/secrets — different files)
Parallel group B: T018, T019 (API routes/webhooks — different files)
Parallel group C: T020, T021, T022, T023 (middleware — different files)
Parallel group D: T024, T025, T026 (frontend security — different areas)
```

**Within Phase 4 (US2 Runtime):**
```
Parallel group A: T035, T036, T037 (resource management — different files)
Parallel group B: T040, T041, T042, T043 (frontend runtime — different areas)
Parallel group C: T044, T045 (import checks — backend vs frontend)
```

**Within Phase 5 (US3 Logic):**
```
Parallel group A: T053, T054 (API routes vs services — different files)
Parallel group B: T055, T056 (backend vs frontend boundary checks)
Parallel group C: T058, T059 (frontend state vs components)
```

**Within Phase 6 (US4 Test Quality):**
```
Parallel group A: T065, T066 (mock isolation vs exception catching)
Parallel group B: T067, T068 (assertion effectiveness vs wrong-reason)
Parallel group C: T071, T072 (frontend mock leaks vs coverage)
```

**Within Phase 7 (US5 Code Quality):**
```
Parallel group A: T080, T081 (backend vs frontend dead code)
Parallel group B: T082, T083 (backend vs frontend duplication)
Parallel group C: T084, T085 (backend vs frontend hardcoded values)
Parallel group D: T086, T087 (backend vs frontend silent failures)
```

**Cross-phase parallelism (if team capacity allows):**
```
After Phase 2 completes, US1–US3 CAN run in parallel on independent files.
US4 and US5 are RECOMMENDED to run after US1–US3 for best results.
```

---

## Parallel Example: User Story 1 (Security)

```bash
# Backend security audits — different file groups, can run in parallel:
Parallel: T014 (config secrets) + T015 (config files scan)
Parallel: T020 (CSRF middleware) + T021 (CSP middleware) + T022 (rate limit) + T023 (request ID)
Parallel: T024 (frontend XSS) + T025 (frontend tokens) + T026 (frontend sanitization)

# Sequential dependencies within US1:
T009 → T010 → T011 → T012 (auth chain: auth logic → sessions → auth API → admin guard)
T016 → T017 (database injection: database.py → chat_store.py — related patterns)
All audit tasks → T027, T028 (regression tests after findings)
T027, T028 → T029, T030 (validation after tests written)
T029, T030 → T031 (summary table after validation green)
```

---

## Implementation Strategy

### MVP First (User Story 1 — Security Only)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundational (T006–T008)
3. Complete Phase 3: User Story 1 — Security (T009–T031)
4. **STOP and VALIDATE**: Run full CI pipeline, verify all security fixes are green, summary table has all P1 findings
5. This alone delivers the highest-value outcome (security vulnerabilities fixed)

### Incremental Delivery

1. Complete Setup + Foundational → Environment ready
2. Add US1 Security → Validate → Commit (MVP — highest risk mitigated)
3. Add US2 Runtime → Validate → Commit (stability improved)
4. Add US3 Logic → Validate → Commit (correctness improved)
5. Add US4 Test Quality → Validate → Commit (confidence improved)
6. Add US5 Code Quality → Validate → Commit (maintainability improved)
7. Each phase adds value and each summary table update is independently useful

### Validation Cadence

Per research.md R-007, run full validation after each category phase:
- **After Phase 3 (P1)**: Full backend + frontend CI pipeline
- **After Phase 4 (P2)**: Full backend + frontend CI pipeline
- **After Phase 5 (P3)**: Full backend + frontend CI pipeline
- **After Phase 6 (P4)**: Full backend + frontend CI pipeline
- **After Phase 7 (P5)**: Full backend + frontend CI pipeline
- **Phase 8**: Final comprehensive validation

This prevents cascading failures and ensures each phase leaves the codebase green.

---

## Codebase Scope Reference

From plan.md and verified file inventory:

| Area | File Count | Key Directories |
|------|-----------|-----------------|
| Backend source | ~143 .py files | solune/backend/src/ |
| Frontend source | ~419 .ts/.tsx files | solune/frontend/src/ |
| Backend tests | ~194 test files | solune/backend/tests/ (144 unit, 15 integration, 8 property, 3 fuzz, 5 chaos, 5 concurrency, 1 arch, 2 helpers) |
| Frontend tests | ~155 test files | solune/frontend/src/**/*.test.* |
| API routes | 21 files | solune/backend/src/api/ |
| Middleware | 5 files | solune/backend/src/middleware/ |
| Services | 33 + 7 sub-packages | solune/backend/src/services/ |
| Models | 25 files | solune/backend/src/models/ |
| Infrastructure | ~5 files | .github/workflows/, solune/scripts/ |

**Total files to audit**: ~560+ source files, ~349+ test files

---

## Notes

- [P] tasks = different files, no dependencies — safe to run concurrently
- [US1]–[US5] labels map to the 5 user stories (security → runtime → logic → test quality → code quality)
- Regression tests are MANDATORY per FR-002, FR-013 — at least one new test per bug fix
- Each phase should leave the codebase in a green state (all tests pass, all linting passes)
- For ambiguous bugs: add `TODO(bug-bash)` comment per Contract 5 format, mark as ⚠️ Flagged in summary table
- For clear bugs: fix directly, add regression test, mark as ✅ Fixed in summary table
- Commit after each task or logical group using Contract 4 format
- Stop at any checkpoint to validate phase independently
