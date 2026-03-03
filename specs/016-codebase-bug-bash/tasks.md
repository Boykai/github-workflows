# Tasks: Bug Bash — Full Codebase Review & Fix

**Input**: Design documents from `/specs/016-codebase-bug-bash/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/audit-standards.md, quickstart.md

**Tests**: Regression tests are MANDATORY per FR-003 — each bug fix MUST include at least one regression test. Test tasks are embedded within each audit phase.

**Organization**: Tasks are grouped by user story (bug category) to enable independent implementation and testing. Each phase audits the full codebase for one bug category in the order: Security → Runtime → Logic → Test Quality → Code Quality → Summary Report.

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

- [ ] T001 Run backend test suite to establish baseline via `cd backend && pytest -v`
- [ ] T002 [P] Run backend linting baseline via `cd backend && ruff check src tests && ruff format --check src tests`
- [ ] T003 [P] Run frontend test suite to establish baseline via `cd frontend && npm test`
- [ ] T004 [P] Run frontend linting baseline via `cd frontend && npm run lint && npm run type-check`
- [ ] T005 Document any pre-existing failures in a baseline-failures note for exclusion from audit findings

**Checkpoint**: Baseline established — all pre-existing test/lint status is documented. Audit phases can begin.

---

## Phase 2: Foundational (Automated Scanning & File Inventory)

**Purpose**: Run automated static analysis tools to catch low-hanging issues before manual review. Generate a file inventory for systematic tracking. MUST complete before user story phases.

**⚠️ CRITICAL**: No manual audit work can begin until this phase is complete.

- [ ] T006 Run Ruff with all rules enabled on backend to identify potential issues via `cd backend && ruff check src tests --select ALL` and document findings
- [ ] T007 [P] Run Pyright type checker on backend to catch type errors via `cd backend && pyright` and document findings
- [ ] T008 [P] Run ESLint on frontend to identify potential issues via `cd frontend && npm run lint` and document findings
- [ ] T009 [P] Run TypeScript strict type check on frontend via `cd frontend && npm run type-check` and document findings
- [ ] T010 Generate file inventory categorized by risk level (High/Medium/Low) per plan.md project structure for systematic audit tracking
- [ ] T011 Triage automated scan findings into the five bug categories (Security, Runtime, Logic, Test Quality, Code Quality) for targeted manual review

**Checkpoint**: Automated scan complete — triaged findings feed into manual review phases. File inventory ready for systematic audit tracking.

---

## Phase 3: User Story 1 — Security Vulnerability Audit and Remediation (Priority: P1) 🎯 MVP

**Goal**: Audit every file for authentication bypasses, injection risks, exposed secrets/tokens, insecure defaults, and improper input validation. Fix confirmed vulnerabilities with regression tests. Flag ambiguous security concerns.

**Independent Test**: Run `cd backend && pytest -v` and `cd frontend && npm test` — all existing + new regression tests pass. Every security finding has a Fix (with regression test) or Flag (`TODO(bug-bash)` comment).

### Backend Security Audit

- [ ] T012 [US1] Audit OAuth flow, session cookies, redirect validation, and token handling in `backend/src/api/auth.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_auth.py`
- [ ] T013 [US1] Audit admin authorization, session validation, and TOCTOU race conditions in `backend/src/dependencies.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_dependencies.py`
- [ ] T014 [US1] Audit secret management, environment variable handling, and cookie security defaults in `backend/src/config.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_config.py`
- [ ] T015 [US1] Audit SQL query construction for injection risks and parameterized query usage in `backend/src/services/database.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_database.py`
- [ ] T016 [US1] Audit GitHub API token usage, input validation, and security of external API calls in `backend/src/services/github_projects/service.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_github_projects_service.py`
- [ ] T017 [P] [US1] Audit user input handling, command injection risks, and XSS in responses in `backend/src/api/chat.py` — fix confirmed vulnerabilities with regression tests in `backend/tests/unit/test_chat.py`
- [ ] T018 [P] [US1] Audit input validation and authentication enforcement in remaining backend API files: `backend/src/api/projects.py`, `backend/src/api/board.py`, `backend/src/api/tasks.py`, `backend/src/api/settings.py`, and all other `backend/src/api/*.py` — fix confirmed vulnerabilities with regression tests
- [ ] T019 [P] [US1] Audit AI agent orchestration for prompt injection and input sanitization in `backend/src/services/ai_agent.py` — fix confirmed vulnerabilities with regression tests
- [ ] T020 [P] [US1] Audit Signal messaging integration for input validation in `backend/src/services/signal_chat.py` — fix confirmed vulnerabilities with regression tests

### Frontend Security Audit

- [ ] T021 [US1] Audit credential handling, CORS configuration, and sensitive data exposure in API URLs in `frontend/src/services/api.ts` — fix confirmed vulnerabilities with regression tests
- [ ] T022 [P] [US1] Audit all React components for XSS via `dangerouslySetInnerHTML`, unsanitized user content rendering, and URL handling in `frontend/src/components/**/*.tsx` — fix confirmed vulnerabilities with regression tests
- [ ] T023 [P] [US1] Audit frontend hooks for sensitive data leaks and insecure state management in `frontend/src/hooks/*.ts` — fix confirmed vulnerabilities with regression tests

### Infrastructure Security Audit

- [ ] T024 [P] [US1] Audit GitHub Actions workflows for secret exposure, insecure action versions, and injection risks in `.github/workflows/ci.yml`, `.github/workflows/housekeeping-cron.yml`, `.github/workflows/branch-issue-link.yml` — fix confirmed vulnerabilities
- [ ] T025 [P] [US1] Audit Docker configuration for insecure defaults, exposed ports, and secret leaks in `docker-compose.yml`, `backend/Dockerfile`, and `frontend/Dockerfile` — fix confirmed vulnerabilities

### US1 Verification

- [ ] T026 [US1] Run full backend test suite `cd backend && pytest -v` to verify all security fixes and regression tests pass
- [ ] T027 [US1] Run full frontend test suite `cd frontend && npm test` to verify all security fixes and regression tests pass

**Checkpoint**: Security audit complete — all confirmed security vulnerabilities have fixes with regression tests. Ambiguous security concerns flagged with `TODO(bug-bash)` comments.

---

## Phase 4: User Story 2 — Runtime Error Detection and Resolution (Priority: P1)

**Goal**: Audit every file for unhandled exceptions, race conditions, null/None references, missing imports, type errors, and resource leaks. Fix confirmed runtime errors with regression tests. Flag ambiguous runtime concerns.

**Independent Test**: Run `cd backend && pytest -v` and `cd frontend && npm test` — all existing + new regression tests pass. Every runtime error finding has a Fix or Flag.

### Backend Runtime Error Audit

- [ ] T028 [US2] Audit async exception handling and error propagation in all FastAPI route handlers in `backend/src/api/*.py` — fix unhandled exceptions with regression tests
- [ ] T029 [US2] Audit SQLite connection and transaction management for resource leaks in `backend/src/services/database.py` and all callers of `get_db()` — fix confirmed leaks with regression tests
- [ ] T030 [US2] Audit null/None reference patterns and optional field access in `backend/src/services/github_projects/service.py` (4000+ line main service, highest priority) — fix confirmed null reference errors with regression tests
- [ ] T031 [P] [US2] Audit async context errors and exception handling in `backend/src/services/ai_agent.py` — fix confirmed runtime errors with regression tests
- [ ] T032 [P] [US2] Audit resource cleanup and error handling in `backend/src/services/signal_chat.py` — fix confirmed runtime errors with regression tests
- [ ] T033 [P] [US2] Audit exception handling in remaining backend service files: `backend/src/services/*.py` (excluding already-audited files) — fix confirmed runtime errors with regression tests
- [ ] T034 [P] [US2] Audit missing imports and type errors across all backend source files using Pyright output from T007 — fix confirmed import/type errors
- [ ] T035 [US2] Audit FastAPI lifespan management, cleanup loop, and background task error handling in `backend/src/main.py` — fix confirmed runtime errors with regression tests

### Frontend Runtime Error Audit

- [ ] T036 [US2] Audit WebSocket lifecycle management, cleanup on unmount, and reconnection handling in `frontend/src/hooks/useSocket*.ts` — fix confirmed runtime errors with regression tests
- [ ] T037 [P] [US2] Audit React error boundary coverage and error recovery in `frontend/src/components/common/ErrorBoundary.tsx` and all major component trees — fix confirmed gaps with regression tests
- [ ] T038 [P] [US2] Audit React Query usage for error handling, stale data, and race conditions in `frontend/src/hooks/*.ts` — fix confirmed runtime errors with regression tests
- [ ] T039 [P] [US2] Audit null/undefined reference patterns in frontend components `frontend/src/components/**/*.tsx` — fix confirmed runtime errors with regression tests

### US2 Verification

- [ ] T040 [US2] Run full backend test suite `cd backend && pytest -v` to verify all runtime error fixes and regression tests pass
- [ ] T041 [US2] Run full frontend test suite `cd frontend && npm test` to verify all runtime error fixes and regression tests pass

**Checkpoint**: Runtime error audit complete — all confirmed runtime errors have fixes with regression tests. Ambiguous runtime concerns flagged with `TODO(bug-bash)` comments.

---

## Phase 5: User Story 3 — Logic Bug Identification and Correction (Priority: P2)

**Goal**: Audit every file for incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, and incorrect return values. Fix confirmed logic bugs with regression tests. Flag ambiguous logic concerns.

**Independent Test**: Run `cd backend && pytest -v` and `cd frontend && npm test` — all existing + new regression tests pass. Every logic bug finding has a Fix or Flag.

### Backend Logic Bug Audit

- [ ] T042 [US3] Audit state transitions, board column moves, and task status changes in `backend/src/services/github_projects/service.py` — fix confirmed logic bugs with regression tests
- [ ] T043 [P] [US3] Audit pagination logic, list slicing, and loop boundaries in all backend API handlers `backend/src/api/*.py` — fix confirmed off-by-one errors with regression tests
- [ ] T044 [P] [US3] Audit permission checks, boolean logic, and comparison operators in `backend/src/dependencies.py` and `backend/src/api/auth.py` — fix confirmed logic bugs with regression tests
- [ ] T045 [P] [US3] Audit return values, data transformation, and control flow in backend service files `backend/src/services/*.py` — fix confirmed logic bugs with regression tests
- [ ] T046 [P] [US3] Audit data model validation and field constraints in `backend/src/models/*.py` — fix confirmed data consistency issues with regression tests
- [ ] T047 [P] [US3] Audit SQL migration logic and data integrity in `backend/src/migrations/*.sql` — fix confirmed logic bugs and document in summary

### Frontend Logic Bug Audit

- [ ] T048 [US3] Audit state management, data flow, and conditional rendering logic in `frontend/src/components/board/*.tsx` (11 board components) — fix confirmed logic bugs with regression tests
- [ ] T049 [P] [US3] Audit state management and message handling in `frontend/src/components/chat/*.tsx` (6 chat components) — fix confirmed logic bugs with regression tests
- [ ] T050 [P] [US3] Audit form validation and settings update logic in `frontend/src/components/settings/*.tsx` (12 settings components) — fix confirmed logic bugs with regression tests
- [ ] T051 [P] [US3] Audit custom hook logic, data transformation, and edge case handling in `frontend/src/hooks/*.ts` (18 hooks) — fix confirmed logic bugs with regression tests
- [ ] T052 [P] [US3] Audit API client request/response handling and error mapping in `frontend/src/services/api.ts` — fix confirmed logic bugs with regression tests

### US3 Verification

- [ ] T053 [US3] Run full backend test suite `cd backend && pytest -v` to verify all logic bug fixes and regression tests pass
- [ ] T054 [US3] Run full frontend test suite `cd frontend && npm test` to verify all logic bug fixes and regression tests pass

**Checkpoint**: Logic bug audit complete — all confirmed logic bugs have fixes with regression tests. Ambiguous logic concerns flagged with `TODO(bug-bash)` comments.

---

## Phase 6: User Story 4 — Test Gap and Quality Assessment (Priority: P2)

**Goal**: Audit all test files for untested code paths, tests passing for wrong reasons, mock leaks, assertions that never fail, and missing edge case coverage. Fix confirmed test quality issues. Flag ambiguous test concerns.

**Independent Test**: Run `cd backend && pytest -v` and `cd frontend && npm test` — all tests pass. Deliberately breaking code under test causes corrected tests to fail.

### Backend Test Quality Audit

- [ ] T055 [US4] Audit all backend unit test files in `backend/tests/unit/*.py` (~45 files) for assertions against mocks that are never called, never-failing asserts, and mock leaks into production paths — fix confirmed test quality issues
- [ ] T056 [P] [US4] Audit backend integration test files in `backend/tests/integration/*.py` (~4 files) for proper test isolation, shared state contamination, and meaningful assertions — fix confirmed test quality issues
- [ ] T057 [P] [US4] Audit `backend/tests/conftest.py` for shared fixture correctness, proper scope management, and potential cross-test contamination — fix confirmed issues
- [ ] T058 [US4] Identify untested critical code paths by comparing backend source files (`backend/src/`) against test files (`backend/tests/`) — add regression tests for the highest-risk uncovered paths

### Frontend Test Quality Audit

- [ ] T059 [US4] Audit all frontend test files in `frontend/src/**/*.test.tsx` (~29 files) for missing async waits, incomplete mock cleanup, and assertions that never fail — fix confirmed test quality issues
- [ ] T060 [P] [US4] Audit frontend test infrastructure in `frontend/src/test/` for factory correctness, mock API completeness, and test utility reliability — fix confirmed issues
- [ ] T061 [P] [US4] Audit E2E test files in `frontend/e2e/*.spec.ts` (9 files) for flaky selectors, missing assertions, and incomplete test cleanup — fix confirmed test quality issues
- [ ] T062 [US4] Identify untested critical code paths by comparing frontend source files against test files — add regression tests for the highest-risk uncovered paths

### US4 Verification

- [ ] T063 [US4] Run full backend test suite `cd backend && pytest -v` to verify all test quality fixes pass
- [ ] T064 [US4] Run full frontend test suite `cd frontend && npm test` to verify all test quality fixes pass

**Checkpoint**: Test quality audit complete — all confirmed test quality issues have fixes. Test suite meaningfully validates code behavior.

---

## Phase 7: User Story 5 — Code Quality Cleanup (Priority: P3)

**Goal**: Audit every file for dead code, unreachable branches, duplicated logic, hardcoded values, silent failures, and missing error messages. Fix clear code quality issues. Flag ambiguous cases.

**Independent Test**: Run `cd backend && pytest -v` and `cd frontend && npm test` — all tests pass unchanged (code quality fixes must not change observable behavior).

### Backend Code Quality Audit

- [ ] T065 [US5] Audit for dead code, unused imports, and unreachable branches in `backend/src/services/github_projects/service.py` (4000+ lines, highest priority) — remove confirmed dead code
- [ ] T066 [P] [US5] Audit for empty except blocks and silent error swallowing in all backend source files `backend/src/**/*.py` — add proper error handling or logging
- [ ] T067 [P] [US5] Audit for hardcoded values that should be in `backend/src/config.py` or `backend/src/constants.py` across all backend source files — move confirmed hardcoded values to config
- [ ] T068 [P] [US5] Audit for duplicated logic across backend service files `backend/src/services/*.py` — document DRY violations (flag for human review, as consolidation may be a refactor)
- [ ] T069 [P] [US5] Audit for dead code and unused imports in remaining backend files: `backend/src/api/*.py`, `backend/src/models/*.py`, `backend/src/middleware/*.py` — remove confirmed dead code

### Frontend Code Quality Audit

- [ ] T070 [US5] Audit for dead code, unused imports, and unreachable branches in frontend components `frontend/src/components/**/*.tsx` — remove confirmed dead code
- [ ] T071 [P] [US5] Audit for silent failures and missing error messages in frontend hooks `frontend/src/hooks/*.ts` — add proper error handling or logging
- [ ] T072 [P] [US5] Audit for hardcoded values and duplicated logic in frontend services and utilities `frontend/src/services/*.ts`, `frontend/src/lib/*.ts` — fix or flag
- [ ] T073 [P] [US5] Audit for dead code and unused configuration in `frontend/src/App.tsx`, `frontend/src/main.tsx`, and config files (`frontend/vite.config.ts`, `frontend/vitest.config.ts`, `frontend/eslint.config.js`) — remove confirmed dead code

### Infrastructure Code Quality Audit

- [ ] T074 [P] [US5] Audit Docker configuration for dead/unused directives and hardcoded values in `docker-compose.yml`, `backend/Dockerfile`, and frontend Dockerfile — fix or flag
- [ ] T075 [P] [US5] Audit GitHub Actions workflows for dead steps, unused variables, and hardcoded values in `.github/workflows/*.yml` — fix or flag

### US5 Verification

- [ ] T076 [US5] Run full backend test suite and lint `cd backend && pytest -v && ruff check src tests` to verify code quality fixes don't change behavior
- [ ] T077 [US5] Run full frontend test suite and lint `cd frontend && npm test && npm run lint` to verify code quality fixes don't change behavior

**Checkpoint**: Code quality audit complete — all confirmed dead code, silent failures, and unreachable branches fixed. Ambiguous cases flagged with `TODO(bug-bash)` comments.

---

## Phase 8: User Story 6 — Findings Summary Report (Priority: P1)

**Goal**: Produce a comprehensive summary table listing every finding from all audit phases. Each entry includes file path, line number(s), bug category, description, and resolution status.

**Independent Test**: Every entry in the summary has a corresponding Fix commit or `TODO(bug-bash)` comment in the codebase. Every Fix commit and `TODO(bug-bash)` comment appears in the summary. Category counts match actual findings.

- [ ] T078 [US6] Compile all security findings (Phase 3) into the summary table with file path, line numbers, category (🔴 Security), description, and status (✅ Fixed / ⚠️ Flagged)
- [ ] T079 [P] [US6] Compile all runtime error findings (Phase 4) into the summary table with file path, line numbers, category (🟠 Runtime), description, and status
- [ ] T080 [P] [US6] Compile all logic bug findings (Phase 5) into the summary table with file path, line numbers, category (🟡 Logic), description, and status
- [ ] T081 [P] [US6] Compile all test quality findings (Phase 6) into the summary table with file path, line numbers, category (🔵 Test Quality), description, and status
- [ ] T082 [P] [US6] Compile all code quality findings (Phase 7) into the summary table with file path, line numbers, category (⚪ Code Quality), description, and status
- [ ] T083 [US6] Merge all category tables into a single findings summary report in `specs/016-codebase-bug-bash/summary-report.md` with counts per category, fixed/flagged totals, and overall test/lint status
- [ ] T084 [US6] Cross-reference summary report against actual codebase — verify every ✅ Fixed entry has a corresponding commit and regression test, and every ⚠️ Flagged entry has a `TODO(bug-bash)` comment at the documented location
- [ ] T085 [US6] Verify zero-finding categories are explicitly listed in the summary report with a "0 findings" note

**Checkpoint**: Summary report complete and cross-referenced — every finding is documented and traceable.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all audit phases. Ensure complete consistency between fixes, flags, tests, and the summary report.

- [ ] T086 Run complete backend verification: `cd backend && pytest -v && ruff check src tests && ruff format --check src tests`
- [ ] T087 Run complete frontend verification: `cd frontend && npm test && npm run lint && npm run type-check`
- [ ] T088 Verify all `TODO(bug-bash)` comments in the codebase are present in the summary report via `grep -rn "TODO(bug-bash)" backend/ frontend/ .github/`
- [ ] T089 Verify all regression test functions added during the bug bash are listed in the summary report
- [ ] T090 Final review of summary report for completeness: confirm every fix commit has a matching entry, category counts are accurate, and overall status reflects current test/lint state

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
- Then audit infrastructure files
- Fix confirmed bugs immediately with regression tests
- Flag ambiguous issues with `TODO(bug-bash)` comments
- Run verification tests after completing each story phase

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T006, T007, T008, T009 can all run in parallel (independent tool scans)

**Within Phase 3 (US1: Security)**:
- T017, T018, T019, T020 can run in parallel (different backend files)
- T022, T023 can run in parallel (different frontend areas)
- T024, T025 can run in parallel (different infrastructure files)

**Within Phase 4 (US2: Runtime)**:
- T031, T032, T033, T034 can run in parallel (different backend areas)
- T037, T038, T039 can run in parallel (different frontend areas)

**Within Phase 5 (US3: Logic)**:
- T043, T044, T045, T046, T047 can run in parallel (different file groups)
- T049, T050, T051, T052 can run in parallel (different frontend areas)

**Within Phase 6 (US4: Test Quality)**:
- T056, T057 can run in parallel (different test areas)
- T060, T061 can run in parallel (different frontend test areas)

**Within Phase 7 (US5: Code Quality)**:
- T066, T067, T068, T069 can run in parallel (different backend files)
- T071, T072, T073 can run in parallel (different frontend areas)
- T074, T075 can run in parallel (different infrastructure files)

**Within Phase 8 (US6: Summary)**:
- T079, T080, T081, T082 can run in parallel (independent category compilations)

**Cross-Story Parallelism** (with separate developers):
- US1 (Security) + US5 (Code Quality) can proceed simultaneously
- US2 (Runtime) + US3 (Logic) can proceed simultaneously after US1
- US4 (Test Quality) must wait for US1–US3

---

## Parallel Example: User Story 1 (Security Audit)

```bash
# Sequential: Backend critical files first
Task T012: "Audit auth.py for OAuth and session security"
Task T013: "Audit dependencies.py for authorization"
Task T014: "Audit config.py for secret management"
Task T015: "Audit database.py for SQL injection"
Task T016: "Audit service.py for token security"

# Parallel: Remaining backend files (different files, no dependencies)
Task T017: "Audit chat.py for input handling"       # [P]
Task T018: "Audit remaining API files"               # [P]
Task T019: "Audit ai_agent.py for prompt injection"  # [P]
Task T020: "Audit signal_chat.py for input validation" # [P]

# Parallel: Frontend files (different files)
Task T021: "Audit api.ts for credential handling"
Task T022: "Audit components for XSS"               # [P]
Task T023: "Audit hooks for data leaks"              # [P]

# Parallel: Infrastructure files (different files)
Task T024: "Audit GitHub Actions workflows"          # [P]
Task T025: "Audit Docker configuration"              # [P]
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
4. Commit each fix individually with the standard commit message format

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story (bug category) for traceability
- Each user story (bug category) should be independently completable and testable
- Tests are MANDATORY per FR-003: every fix must include ≥1 regression test
- Use commit format: `fix(<category>): <description>` per `contracts/audit-standards.md`
- Use flag format: `# TODO(bug-bash): <Category> — <Description>` per `contracts/audit-standards.md`
- Commit after each fix — one bug per commit, no bundled changes
- Run verification tests after completing each user story phase
- Stop at any checkpoint to validate phase independently
- Pre-existing failures documented in Phase 1 are EXCLUDED from audit findings
