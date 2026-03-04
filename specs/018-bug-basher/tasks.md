# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/018-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED — FR-004 mandates at least one new regression test per bug fix.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each story maps to one of the five bug categories (Security, Runtime, Logic, Test Quality, Code Quality) reviewed in priority order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend tests: `backend/tests/unit/`
- Frontend tests: colocated `*.test.tsx` / `*.test.ts` files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development environment and establish baseline test/lint status before any changes

- [X] T001 Install backend dev dependencies with `pip install -e ".[dev]"` in backend/
- [X] T002 Install frontend dependencies with `npm install` in frontend/
- [X] T003 [P] Run baseline backend tests file-by-file with `timeout 30 python -m pytest tests/unit/test_*.py -q` in backend/ to establish green status
- [X] T004 [P] Run baseline frontend tests with `npx vitest run` in frontend/ to establish green status
- [X] T005 [P] Run baseline backend linting with `ruff check src tests && ruff format --check src tests` in backend/
- [X] T006 [P] Run baseline frontend linting with `npx eslint .` and `npx tsc --noEmit` in frontend/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Catalog existing patterns and create tracking artifacts that ALL review phases depend on

**⚠️ CRITICAL**: No review work can begin until this phase is complete

- [X] T007 Catalog error handling patterns (safe_error_response, handle_service_error) from backend/src/logging_utils.py as reference for all fix phases
- [X] T008 Catalog established test mock patterns (vi.spyOn + mockRestore) from frontend/src/components/common/ErrorBoundary.test.tsx and frontend/src/components/ThemeProvider.test.tsx as reference for test quality phase
- [X] T009 Create bug tracking summary table document following data-model.md schema for use across all phases

**Checkpoint**: Foundation ready — review phases can now proceed in priority order

---

## Phase 3: User Story 1 — Fix Security Vulnerabilities (Priority: P1) 🎯 MVP

**Goal**: Audit every file for security vulnerabilities (auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation) and fix confirmed issues with regression tests

**Independent Test**: Run full test suite after each security fix; verify vulnerability is closed by regression test, no existing tests regress

### Audit for User Story 1

- [X] T010 [US1] Audit all except blocks for raw exception text (str(e)) leaking into API responses in backend/src/api/auth.py, backend/src/api/board.py, backend/src/api/chat.py, backend/src/api/cleanup.py, backend/src/api/health.py, backend/src/api/mcp.py, backend/src/api/projects.py, backend/src/api/settings.py, backend/src/api/signal.py, backend/src/api/tasks.py, backend/src/api/webhooks.py, backend/src/api/workflow.py, backend/src/api/agents.py, backend/src/api/chores.py
- [X] T011 [P] [US1] Audit authentication and authorization checks on all route handlers in backend/src/api/*.py
- [X] T012 [P] [US1] Audit input validation via Pydantic models on all endpoints in backend/src/api/*.py
- [X] T013 [P] [US1] Audit for SQL injection risks in query construction in backend/src/services/database.py, backend/src/services/session_store.py, backend/src/services/settings_store.py, backend/src/services/mcp_store.py, backend/src/services/cache.py
- [X] T014 [P] [US1] Audit for hardcoded secrets, tokens, and insecure defaults in backend/src/config.py
- [X] T015 [P] [US1] Audit for hardcoded secrets and improper input sanitization in backend/src/services/agent_creator.py, backend/src/services/signal_chat.py, backend/src/services/github_auth.py, backend/src/services/encryption.py
- [X] T016 [P] [US1] Audit for XSS vulnerabilities (dangerouslySetInnerHTML, unsanitized user input rendering) in frontend/src/components/**/*.tsx
- [X] T017 [P] [US1] Audit for exposed secrets or real tokens in .env.example and docker-compose.yml
- [X] T018 [P] [US1] Audit for command injection in subprocess or shell calls in backend/src/services/**/*.py and scripts/

### Fix and Test for User Story 1

- [X] T019 [US1] Fix all confirmed str(e) leaks — replace with static error messages and server-side logging using patterns from backend/src/logging_utils.py
- [X] T020 [US1] Fix all confirmed missing auth checks, input validation gaps, and insecure defaults in backend/src/api/*.py and backend/src/config.py
- [X] T021 [P] [US1] Fix all confirmed SQL injection risks in backend/src/services/*.py
- [X] T022 [P] [US1] Fix all confirmed XSS vulnerabilities in frontend/src/components/**/*.tsx
- [X] T023 [P] [US1] Fix all confirmed secrets exposure in .env.example, docker-compose.yml, and backend/src/config.py
- [X] T024 [US1] Add regression tests for each backend security fix in backend/tests/unit/ (one test per fix minimum per FR-004)
- [X] T025 [P] [US1] Add regression tests for each frontend security fix in colocated frontend/src/**/*.test.tsx files
- [X] T026 [US1] Run full backend test suite file-by-file and `ruff check src tests` to validate all security fixes in backend/
- [X] T027 [P] [US1] Run full frontend test suite with `npx vitest run` and `npx eslint .` to validate all security fixes in frontend/

**Checkpoint**: All security vulnerabilities fixed and validated. User Story 1 independently testable.

---

## Phase 4: User Story 2 — Fix Runtime Errors (Priority: P2)

**Goal**: Audit every file for runtime errors (unhandled exceptions, race conditions, null references, missing imports, type errors, resource leaks) and fix confirmed issues with regression tests

**Independent Test**: Run full test suite after each runtime fix; verify the error condition no longer causes crashes, resources are properly released

### Audit for User Story 2

- [X] T028 [US2] Audit for assert statements in production code paths in backend/src/services/copilot_polling/pipeline.py, backend/src/api/chat.py, and all other files in backend/src/**/*.py
- [X] T029 [P] [US2] Audit for unhandled exceptions in async functions in backend/src/services/**/*.py and backend/src/api/*.py
- [X] T030 [P] [US2] Audit for resource leaks (file handles, DB connections not using context managers) in backend/src/services/database.py, backend/src/services/cleanup_service.py, backend/src/services/session_store.py
- [X] T031 [P] [US2] Audit for missing imports and type errors detectable by pyright in backend/src/**/*.py
- [X] T032 [P] [US2] Verify and fix handle_service_error() return type annotation to NoReturn in backend/src/logging_utils.py
- [X] T033 [P] [US2] Audit for unhandled promise rejections and null/undefined access in frontend/src/hooks/*.ts and frontend/src/services/api.ts
- [X] T034 [P] [US2] Audit for uncaught exceptions in event handlers and missing error boundaries in frontend/src/components/**/*.tsx

### Fix and Test for User Story 2

- [X] T035 [US2] Replace all assert statements in production code with proper if-checks and error handling (raise/return/log) in backend/src/**/*.py
- [X] T036 [US2] Fix all confirmed unhandled exceptions and add proper error handling in backend/src/services/**/*.py and backend/src/api/*.py
- [X] T037 [P] [US2] Fix all confirmed resource leaks with context managers (with/async with) in backend/src/services/*.py
- [X] T038 [P] [US2] Fix all confirmed null/undefined access and unhandled rejections in frontend/src/**/*.ts and frontend/src/**/*.tsx
- [X] T039 [US2] Add regression tests for each backend runtime fix in backend/tests/unit/ (one test per fix minimum per FR-004)
- [X] T040 [P] [US2] Add regression tests for each frontend runtime fix in colocated frontend/src/**/*.test.tsx files
- [X] T041 [US2] Run full backend test suite file-by-file and `ruff check src tests` to validate all runtime fixes in backend/
- [X] T042 [P] [US2] Run full frontend test suite with `npx vitest run` and `npx tsc --noEmit` to validate all runtime fixes in frontend/

**Checkpoint**: All runtime errors fixed and validated. User Stories 1 AND 2 independently testable.

---

## Phase 5: User Story 3 — Fix Logic Bugs (Priority: P3)

**Goal**: Audit every file for logic bugs (incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, incorrect return values) and fix confirmed issues with regression tests

**Independent Test**: Run full test suite after each logic fix; verify correct output for previously buggy input, boundary conditions tested

### Audit for User Story 3

- [X] T043 [US3] Audit state transitions and control flow in backend/src/services/workflow_orchestrator/*.py, backend/src/services/copilot_polling/*.py, backend/src/services/agent_creator.py
- [X] T044 [P] [US3] Audit return values and off-by-one errors in backend/src/services/**/*.py and backend/src/utils.py
- [X] T045 [P] [US3] Audit dependency arrays in useEffect/useMemo/useCallback hooks in frontend/src/hooks/useChat.ts, frontend/src/hooks/useAuth.ts, frontend/src/hooks/useProjectBoard.ts, frontend/src/hooks/useWorkflow.ts, frontend/src/hooks/useRealTimeSync.ts, frontend/src/hooks/useBoardRefresh.ts, frontend/src/hooks/useCommands.ts, frontend/src/hooks/useSettingsForm.ts
- [X] T046 [P] [US3] Audit utility function behavior and edge cases in frontend/src/lib/utils.ts and frontend/src/lib/commands/**/*.ts

### Fix and Test for User Story 3

- [X] T047 [US3] Fix all confirmed state transition and control flow bugs in backend/src/services/**/*.py
- [X] T048 [P] [US3] Fix all confirmed off-by-one errors and incorrect return values in backend/src/**/*.py
- [X] T049 [P] [US3] Fix all confirmed incorrect dependency arrays and state update logic in frontend/src/hooks/*.ts
- [X] T050 [P] [US3] Fix all confirmed logic bugs in frontend/src/lib/**/*.ts
- [X] T051 [US3] Add regression tests for each backend logic fix in backend/tests/unit/ (one test per fix minimum per FR-004)
- [X] T052 [P] [US3] Add regression tests for each frontend logic fix in colocated frontend/src/**/*.test.ts files
- [X] T053 [US3] Run full backend test suite file-by-file and `ruff check src tests` to validate all logic fixes in backend/
- [X] T054 [P] [US3] Run full frontend test suite with `npx vitest run` to validate all logic fixes in frontend/

**Checkpoint**: All logic bugs fixed and validated. User Stories 1, 2, AND 3 independently testable.

---

## Phase 6: User Story 6 — Flag Ambiguous Issues for Human Review (Priority: P3)

**Goal**: Review all changes from prior phases for ambiguous cases; add structured `# TODO(bug-bash):` / `// TODO(bug-bash):` comments for issues requiring human judgment; verify no source code changes were made at flagged locations beyond the comment

**Independent Test**: Verify all TODO comments follow required format (marker + description + options + rationale), and no code was changed at flagged locations

### Implementation for User Story 6

- [X] T055 [US6] Review all findings from US1–US3 and identify ambiguous or trade-off situations in backend/src/**/*.py and frontend/src/**/*.{ts,tsx}
- [X] T056 [US6] Add `# TODO(bug-bash):` comments with description, options, and rationale at each ambiguous location in backend/src/**/*.py (format per data-model.md)
- [X] T057 [P] [US6] Add `// TODO(bug-bash):` comments with description, options, and rationale at each ambiguous location in frontend/src/**/*.{ts,tsx} (format per data-model.md)
- [X] T058 [US6] Verify all TODO(bug-bash) comments follow the required format: marker, description, options, rationale — grep all TODO(bug-bash) across the codebase
- [X] T059 [US6] Verify no source code changes were made at flagged-only locations (only the comment was added)

**Checkpoint**: All ambiguous issues properly flagged. No incorrect fixes applied to trade-off situations.

---

## Phase 7: User Story 4 — Address Test Gaps and Test Quality (Priority: P4)

**Goal**: Audit the test suite for quality issues (untested code paths, tests passing for wrong reason, mock leaks, assertions that never fail, missing edge case coverage) and fix confirmed issues

**Independent Test**: Verify new/corrected tests fail when corresponding production code is intentionally broken; verify mock objects confined to test scope

### Audit for User Story 4

- [X] T060 [US4] Audit for assertions that never fail (e.g., `assert True`, always-true conditions) in backend/tests/unit/*.py
- [X] T061 [P] [US4] Audit for MagicMock objects leaking into production code paths (e.g., mock objects used as database file paths) in backend/tests/unit/*.py
- [X] T062 [P] [US4] Audit for missing vi.spyOn + mockRestore() pairs in afterEach blocks in frontend/src/**/*.test.tsx
- [X] T063 [P] [US4] Audit for always-true assertions (e.g., `expect(true).toBe(true)`) in frontend/src/**/*.test.tsx
- [X] T064 [P] [US4] Identify critical code paths with no test coverage in backend/src/api/*.py and backend/src/services/**/*.py

### Fix and Test for User Story 4

- [X] T065 [US4] Fix confirmed always-true assertions to be specific and meaningful in backend/tests/unit/*.py
- [X] T066 [P] [US4] Fix confirmed mock leaks — scope MagicMock objects properly and add cleanup in backend/tests/unit/*.py
- [X] T067 [P] [US4] Fix confirmed missing mockRestore() — add proper vi.spyOn cleanup in afterEach in frontend/src/**/*.test.tsx
- [X] T068 [P] [US4] Fix confirmed always-true assertions to be specific in frontend/src/**/*.test.tsx
- [X] T069 [US4] Add tests for untested critical code paths identified in T064 in backend/tests/unit/
- [X] T070 [P] [US4] Add tests for untested critical code paths in frontend/src/**/*.test.tsx
- [X] T071 [US4] Validate: run full backend test suite file-by-file to confirm test quality fixes in backend/
- [X] T072 [P] [US4] Validate: run full frontend test suite with `npx vitest run` to confirm test quality fixes in frontend/

**Checkpoint**: Test suite quality improved. All test fixes validated. Mock leaks eliminated.

---

## Phase 8: User Story 5 — Resolve Code Quality Issues (Priority: P5)

**Goal**: Audit the codebase for code quality issues (dead code, unreachable branches, duplicated logic, hardcoded values, missing error messages, silent failures) and fix confirmed issues or flag ambiguous ones

**Independent Test**: Verify removed dead code doesn't break tests; verify deduplicated logic passes all related tests; verify error messages appear in failure scenarios

### Audit for User Story 5

- [X] T073 [US5] Audit for dead code and unreachable branches in backend/src/**/*.py
- [X] T074 [P] [US5] Audit for duplicated logic that should be shared in backend/src/api/*.py and backend/src/services/**/*.py
- [X] T075 [P] [US5] Audit for hardcoded values that should be configurable in backend/src/**/*.py
- [X] T076 [P] [US5] Audit for silent `except: pass` blocks and missing error messages in backend/src/**/*.py
- [X] T077 [P] [US5] Audit for unused imports, dead code, and console.log statements in frontend/src/**/*.{ts,tsx}

### Fix and Test for User Story 5

- [X] T078 [US5] Remove confirmed dead code and unreachable branches in backend/src/**/*.py
- [X] T079 [P] [US5] Fix confirmed duplicated logic by reusing existing utility functions in backend/src/**/*.py
- [X] T080 [P] [US5] Extract confirmed hardcoded values to configuration in backend/src/config.py
- [X] T081 [P] [US5] Fix confirmed silent exception blocks — add appropriate error logging in backend/src/**/*.py
- [X] T082 [P] [US5] Remove confirmed unused imports, dead code, and console.log in frontend/src/**/*.{ts,tsx}
- [X] T083 [US5] Add regression tests for code quality fixes in backend/tests/unit/ (one test per fix minimum per FR-004)
- [X] T084 [P] [US5] Add regression tests for code quality fixes in frontend/src/**/*.test.tsx
- [X] T085 [US5] Validate: run full backend test suite + `ruff check src tests` + `ruff format --check src tests` for code quality phase
- [X] T086 [P] [US5] Validate: run full frontend test suite + `npx eslint .` + `npx tsc --noEmit` for code quality phase

**Checkpoint**: All code quality issues resolved. Full codebase clean.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary generation, and documentation

- [X] T087 Generate final summary table with all findings (file, lines, category, description, status) following data-model.md schema in specs/018-bug-basher/
- [X] T088 Verify every ✅ Fixed entry in summary has a corresponding regression test in backend/tests/unit/ or frontend/src/**/*.test.tsx
- [X] T089 Verify every ⚠️ Flagged entry in summary has a corresponding TODO(bug-bash) comment in source code
- [X] T090 Run complete backend test suite (all ~47 test files) for final validation in backend/
- [X] T091 [P] Run complete frontend test suite with `npx vitest run` for final validation in frontend/
- [X] T092 [P] Run all linting: `ruff check src tests && ruff format --check src tests` in backend/, `npx eslint .` and `npx tsc --noEmit` in frontend/
- [X] T093 Verify all commit messages follow `fix(<category>): <subject>` format per data-model.md
- [X] T094 Run quickstart.md validation scenarios to confirm review process was followed correctly
- [X] T095 Verify zero regressions: compare test count before and after (backend ~1284 tests, frontend ~334 tests — count should only increase)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all review phases
- **US1 Security (Phase 3)**: Depends on Foundational — MUST be first review phase (highest priority)
- **US2 Runtime (Phase 4)**: Depends on Foundational — can start after US1 or in parallel if no file conflicts
- **US3 Logic (Phase 5)**: Depends on Foundational — can start after US2 or in parallel if no file conflicts
- **US6 Flagging (Phase 6)**: Depends on US1–US3 completion — reviews findings from prior phases
- **US4 Test Quality (Phase 7)**: Depends on Foundational — can start after US3 or in parallel if no file conflicts
- **US5 Code Quality (Phase 8)**: Depends on Foundational — can start after US4 or in parallel if no file conflicts
- **Polish (Phase 9)**: Depends on ALL review phases being complete

### User Story Dependencies

- **US1 (P1) Security**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2) Runtime**: Can start after Foundational (Phase 2) — Independent of US1 (different bug category, may overlap files)
- **US3 (P3) Logic**: Can start after Foundational (Phase 2) — Independent of US1/US2
- **US6 (P3) Flagging**: Depends on US1–US3 — reviews findings from those phases for ambiguous cases
- **US4 (P4) Test Quality**: Can start after Foundational (Phase 2) — Independent of other stories
- **US5 (P5) Code Quality**: Can start after Foundational (Phase 2) — Independent of other stories

### Recommended Sequential Order

For a single developer, the recommended execution order follows priority:
1. Setup → Foundational → US1 (Security) → US2 (Runtime) → US3 (Logic) → US6 (Flagging) → US4 (Test Quality) → US5 (Code Quality) → Polish

> **Note**: US6 (Flagging) MUST wait for US1–US3 to complete, as it reviews findings from those phases. US4 and US5 could theoretically start earlier (after Foundational), but are ordered later by priority. In the parallel team strategy, US4/US5 can be moved earlier if US6 is handled as a final pass.

### Within Each User Story

- Audit tasks FIRST — identify all issues before fixing
- Fix tasks SECOND — apply minimal, focused fixes
- Test tasks THIRD — add regression tests per FR-004
- Validate tasks LAST — confirm full test suite and linting pass

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003–T006)
- Once Foundational phase completes, US1–US5 audit tasks can theoretically start in parallel (different bug categories)
- Within each story: audit tasks marked [P] can run in parallel (different file groups)
- Within each story: fix tasks marked [P] can run in parallel (different files)
- Backend and frontend work within the same story can run in parallel

---

## Parallel Example: User Story 1 (Security)

```bash
# Launch all audit tasks for US1 in parallel (different file groups):
Task T011: "Audit auth checks in backend/src/api/*.py"
Task T012: "Audit input validation in backend/src/api/*.py"
Task T013: "Audit SQL injection in backend/src/services/*.py"
Task T014: "Audit secrets in backend/src/config.py"
Task T015: "Audit secrets in backend/src/services/*.py"
Task T016: "Audit XSS in frontend/src/components/**/*.tsx"
Task T017: "Audit secrets in .env.example"
Task T018: "Audit command injection in backend/src/services/**/*.py"

# Launch backend and frontend fixes in parallel:
Task T019-T021: "Fix backend security issues"
Task T022: "Fix frontend security issues"

# Launch backend and frontend test additions in parallel:
Task T024: "Add backend regression tests"
Task T025: "Add frontend regression tests"

# Launch backend and frontend validation in parallel:
Task T026: "Validate backend"
Task T027: "Validate frontend"
```

---

## Implementation Strategy

### MVP First (User Story 1 — Security Only)

1. Complete Phase 1: Setup (verify environment, baseline tests)
2. Complete Phase 2: Foundational (catalog patterns, create tracking)
3. Complete Phase 3: User Story 1 — Security Vulnerabilities
4. **STOP and VALIDATE**: Run full test suite, confirm all security fixes validated
5. Deploy/demo if ready — security is the highest-value increment

### Incremental Delivery

1. Complete Setup + Foundational → Environment ready, patterns cataloged
2. Add US1 (Security) → Test independently → Highest-risk bugs eliminated (MVP!)
3. Add US2 (Runtime) → Test independently → Crashes and resource leaks fixed
4. Add US3 (Logic) → Test independently → Silent incorrect behavior fixed
5. Add US6 (Flagging) → Validate → Ambiguous issues documented for humans
6. Add US4 (Test Quality) → Test independently → Test suite reliability improved
7. Add US5 (Code Quality) → Test independently → Maintenance burden reduced
8. Polish → Final summary table, full validation, commit message review

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Security) — backend focus
   - Developer B: US1 (Security) — frontend focus
3. After US1:
   - Developer A: US2 (Runtime) — backend
   - Developer B: US3 (Logic) — frontend hooks/components
4. After US2/US3:
   - Developer A: US4 (Test Quality) — backend tests
   - Developer B: US5 (Code Quality) — frontend cleanup
5. Together: US6 (Flagging review) + Polish

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story corresponds to one bug category (US1→Security, US2→Runtime, US3→Logic, US4→Test Quality, US5→Code Quality, US6→Flagging)
- US6 (Flagging) is cross-cutting but given its own phase after US1–US3 to validate ambiguous findings
- Tests are REQUIRED per FR-004: at least one regression test per bug fix
- Commit after each task or logical group following `fix(<category>): <subject>` format
- Stop at any checkpoint to validate story independently
- Constraints: no new dependencies (FR-013), no API surface changes (FR-012), no architecture changes, preserve code style (FR-014), each fix minimal and focused (FR-015)
- Backend tests must run file-by-file with `timeout 30` to avoid hanging (per research.md R4)
- Avoid: vague tasks, same file conflicts in [P] tasks, cross-story dependencies that break independence
