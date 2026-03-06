# Tasks: Bug Bash — Full Codebase Review & Fix

**Input**: Design documents from `/specs/025-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY for this feature — FR-013 requires at least one regression test per bug fix, and SC-002 requires a 1:1 fix-to-test ratio.

**Organization**: Tasks are grouped by bug category (mapped to user stories US1–US5) in priority order from spec.md, enabling independent implementation and testing of each category.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=Security, US2=Runtime, US3=Logic, US4=TestQuality, US5=CodeQuality)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`, `frontend/src/`, `frontend/e2e/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a passing baseline for both backend and frontend before any changes

- [ ] T001 Install backend dependencies and record baseline lint/type-check/test pass counts in backend/
- [ ] T002 Install frontend dependencies and record baseline lint/type-check/test pass counts in frontend/
- [ ] T003 [P] Run grep-based pattern scans for all five bug categories across the full codebase and compile prioritized audit target list

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Execute pattern-based scans to identify candidate bugs in each category — MUST complete before file-level audit begins

**⚠️ CRITICAL**: No file-level audit work can begin until this phase is complete

- [ ] T004 Scan backend/src/ for security anti-patterns: hardcoded secrets, eval/exec, raw SQL, missing auth Depends(), wildcard CORS, pickle/yaml unsafe loads, secrets in logs
- [ ] T005 [P] Scan frontend/src/ for security anti-patterns: dangerouslySetInnerHTML, localStorage token storage, unvalidated URL params, missing rel="noopener noreferrer" on external links
- [ ] T006 [P] Scan backend/src/ for runtime error anti-patterns: bare except, missing await on coroutines, file/DB handles without context managers, dict[] on user data, asyncio.create_task without error handling
- [ ] T007 [P] Scan backend/tests/ for test quality anti-patterns: MagicMock used as path/URL/config, assert mock_obj (always truthy), assert True, test functions with no assertions, pytest.raises(Exception) too broad
- [ ] T008 [P] Scan full codebase for code quality anti-patterns: dead code, bare except pass, duplicated logic blocks, hardcoded timeouts/URLs/retry counts

**Checkpoint**: All scan results compiled — file-level audit can now begin per category priority

---

## Phase 3: User Story 1 — Security Vulnerability Remediation (Priority: P1) 🎯 MVP

**Goal**: Identify and fix all security vulnerabilities: auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation

**Independent Test**: Run full test suite including new regression tests for each security fix. Verify zero secrets in source code, all inputs validated, auth enforced on all protected endpoints, security defaults follow best practices.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Audit and fix backend/src/config.py for hardcoded secrets, insecure defaults, missing environment variable validation
- [ ] T010 [P] [US1] Audit and fix backend/src/api/auth.py for OAuth flow vulnerabilities, token handling, input validation on redirect URI
- [ ] T011 [P] [US1] Audit and fix backend/src/services/github_auth.py for authentication bypasses, token leakage, improper credential handling
- [ ] T012 [P] [US1] Audit and fix backend/src/services/encryption.py for cryptographic issues, key management, insecure algorithms
- [ ] T013 [P] [US1] Audit and fix backend/src/api/webhooks.py for missing webhook signature verification, payload validation
- [ ] T014 [P] [US1] Audit and fix backend/src/middleware/request_id.py and backend/src/middleware/error_handler.py for information leakage in error responses
- [ ] T015 [P] [US1] Audit and fix backend/src/prompts/system.py and backend/src/prompts/templates.py for prompt injection risks
- [ ] T016 [P] [US1] Audit and fix remaining backend/src/api/ endpoints (agents.py, board.py, chat.py, chores.py, cleanup.py, health.py, mcp.py, metadata.py, projects.py, settings.py, signal.py, tasks.py, workflow.py) for missing auth checks, input validation
- [ ] T017 [P] [US1] Audit and fix backend/src/logging_utils.py for sensitive data exposure in log output
- [ ] T018 [P] [US1] Audit and fix frontend/src/services/api.ts for auth header injection, credential exposure, error response leaks
- [ ] T019 [P] [US1] Audit and fix frontend/src/hooks/useAuth.ts and frontend/src/components/auth/ for token storage security, XSS vectors
- [ ] T020 [P] [US1] Audit and fix remaining frontend/src/components/ for dangerouslySetInnerHTML usage, unvalidated URL handling, missing rel attributes on external links
- [ ] T021 [P] [US1] Add regression tests for all backend security fixes in backend/tests/unit/ and backend/tests/integration/
- [ ] T022 [P] [US1] Add regression tests for all frontend security fixes in frontend/src/**/*.test.tsx colocated test files
- [ ] T023 [US1] Validate US1: run backend ruff check + ruff format --check + pyright + pytest (batched) in backend/
- [ ] T024 [US1] Validate US1: run frontend eslint + tsc --noEmit + vitest in frontend/

**Checkpoint**: All security vulnerabilities fixed or flagged. Run full test suite — User Story 1 is independently testable.

---

## Phase 4: User Story 2 — Runtime Error Remediation (Priority: P2)

**Goal**: Identify and fix all runtime errors: unhandled exceptions, race conditions, null/None references, missing imports, type errors, resource leaks

**Independent Test**: Run full test suite and verify all new regression tests pass. Confirm unhandled exceptions are caught gracefully, resource handles use context managers, null references are guarded.

### Implementation for User Story 2

- [ ] T025 [US2] Audit and fix backend/src/services/database.py for connection leaks, missing context managers, unclosed cursors
- [ ] T026 [P] [US2] Audit and fix backend/src/services/signal_bridge.py for WebSocket connection leaks, unhandled disconnection errors
- [ ] T027 [P] [US2] Audit and fix backend/src/services/signal_delivery.py for retry logic failures, unhandled HTTP errors, resource leaks
- [ ] T028 [P] [US2] Audit and fix backend/src/services/copilot_polling/ (all 8 files) for async errors, race conditions, missing awaits, fire-and-forget tasks without error handling
- [ ] T029 [P] [US2] Audit and fix backend/src/services/github_projects/ (service.py and related) for null refs on API responses, unhandled GitHub API errors
- [ ] T030 [P] [US2] Audit and fix backend/src/dependencies.py for initialization safety, missing null checks on service singletons
- [ ] T031 [P] [US2] Audit and fix backend/src/main.py for startup/shutdown safety, unclosed resources on shutdown
- [ ] T032 [P] [US2] Audit and fix remaining backend/src/services/ (ai_agent.py, cache.py, cleanup_service.py, completion_providers.py, metadata_service.py, model_fetcher.py, mcp_store.py, session_store.py, settings_store.py, signal_chat.py, websocket.py, github_commit_workflow.py) for unhandled exceptions, missing imports, type errors
- [ ] T033 [P] [US2] Audit and fix backend/src/utils.py for BoundedDict/BoundedSet edge cases, thread safety
- [ ] T034 [P] [US2] Audit and fix frontend/src/hooks/ for unhandled promise rejections, missing error boundaries, stale closure bugs
- [ ] T035 [P] [US2] Audit and fix frontend/src/components/ for unhandled null/undefined references, missing loading/error states
- [ ] T036 [P] [US2] Add regression tests for all backend runtime error fixes in backend/tests/unit/ and backend/tests/integration/
- [ ] T037 [P] [US2] Add regression tests for all frontend runtime error fixes in frontend/src/**/*.test.tsx colocated test files
- [ ] T038 [US2] Validate US2: run backend ruff check + ruff format --check + pyright + pytest (batched) in backend/
- [ ] T039 [US2] Validate US2: run frontend eslint + tsc --noEmit + vitest in frontend/

**Checkpoint**: All runtime errors fixed or flagged. Run full test suite — User Story 2 is independently testable.

---

## Phase 5: User Story 3 — Logic Bug Remediation (Priority: P3)

**Goal**: Identify and fix all logic bugs: incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, incorrect return values

**Independent Test**: Run full test suite and verify each logic bug fix includes at least one regression test that would have caught the original bug.

### Implementation for User Story 3

- [ ] T040 [US3] Audit and fix backend/src/services/workflow_orchestrator/ for state transition errors, invalid guard conditions, missing transitions
- [ ] T041 [P] [US3] Audit and fix backend/src/services/chores/ for scheduling logic errors, timing edge cases, missed triggers
- [ ] T042 [P] [US3] Audit and fix backend/src/services/cache.py for cache invalidation logic, TTL calculation errors, stale data
- [ ] T043 [P] [US3] Audit and fix backend/src/api/ for incorrect response codes, off-by-one in pagination, wrong HTTP methods
- [ ] T044 [P] [US3] Audit and fix backend/src/models/ for validation logic errors, missing constraints, incorrect type coercion
- [ ] T045 [P] [US3] Audit and fix backend/src/services/agents/ for agent lifecycle logic, incorrect state management
- [ ] T046 [P] [US3] Audit and fix frontend/src/hooks/useProjectBoard.ts for board state management bugs, incorrect drag-drop ordering
- [ ] T047 [P] [US3] Audit and fix frontend/src/components/board/ for drag-and-drop logic errors, incorrect item positioning
- [ ] T048 [P] [US3] Audit and fix remaining frontend/src/components/ and frontend/src/hooks/ for control flow errors, incorrect return values, state inconsistencies
- [ ] T049 [P] [US3] Audit and fix frontend/src/lib/ and frontend/src/utils/ for utility function edge cases, incorrect calculations
- [ ] T050 [P] [US3] Add regression tests for all backend logic bug fixes in backend/tests/unit/
- [ ] T051 [P] [US3] Add regression tests for all frontend logic bug fixes in frontend/src/**/*.test.tsx colocated test files
- [ ] T052 [US3] Validate US3: run backend ruff check + ruff format --check + pyright + pytest (batched) in backend/
- [ ] T053 [US3] Validate US3: run frontend eslint + tsc --noEmit + vitest in frontend/

**Checkpoint**: All logic bugs fixed or flagged. Run full test suite — User Story 3 is independently testable.

---

## Phase 6: User Story 4 — Test Gap & Test Quality Remediation (Priority: P4)

**Goal**: Identify and fix all test gaps and test quality issues: untested code paths, mock leaks, meaningless assertions, missing edge case coverage

**Independent Test**: Run full test suite and verify new tests cover previously untested paths, mock objects are properly scoped, and all assertions are meaningful.

### Implementation for User Story 4

- [ ] T054 [US4] Audit and fix backend/tests/conftest.py for mock leaks across test boundaries, incorrect fixture scoping, shared mutable state
- [ ] T055 [P] [US4] Audit and fix backend/tests/unit/test_copilot_polling.py for MagicMock leaks into production paths, meaningless assertions, tests passing for wrong reasons
- [ ] T056 [P] [US4] Audit and fix backend/tests/unit/test_github_projects.py for MagicMock leaks into production paths, meaningless assertions, tests passing for wrong reasons
- [ ] T057 [P] [US4] Scan and fix all backend/tests/unit/ files for MagicMock objects used as file paths, database URLs, or config values that reach production code
- [ ] T058 [P] [US4] Scan and fix all backend/tests/unit/ files for meaningless assertions: assert mock_obj (always truthy), assert True, assert result is not None on MagicMock
- [ ] T059 [P] [US4] Identify and add tests for untested critical backend code paths: error handlers, auth checks, data validation, edge cases in backend/tests/unit/
- [ ] T060 [P] [US4] Audit and fix backend/tests/helpers/ for factory/mock correctness, ensure helpers produce realistic test data
- [ ] T061 [P] [US4] Audit and fix frontend test files (src/**/*.test.tsx, src/**/*.test.ts) for mock quality, missing assertions, untested error states
- [ ] T062 [P] [US4] Audit and fix frontend/e2e/ tests for flaky selectors, missing assertions, race conditions
- [ ] T063 [US4] Validate US4: run full backend test suite (batched) — all tests pass with meaningful assertions in backend/
- [ ] T064 [US4] Validate US4: run full frontend test suite — all tests pass in frontend/

**Checkpoint**: All test quality issues fixed. Mock leaks eliminated, meaningless assertions replaced, critical paths tested.

---

## Phase 7: User Story 5 — Code Quality Issue Remediation (Priority: P5)

**Goal**: Identify and fix all code quality issues: dead code, unreachable branches, duplicated logic, hardcoded values, silent failures

**Independent Test**: Run full test suite and verify removed dead code breaks nothing, silent failures now log/surface errors, hardcoded values are configurable.

### Implementation for User Story 5

- [ ] T065 [US5] Scan and remove dead code in backend/src/ — verify zero references via grep/ruff before removal, flag dynamic dispatch cases as TODO(bug-bash)
- [ ] T066 [P] [US5] Fix silent exception handlers in backend/src/ — replace bare except:pass and except Exception:pass with logging or re-raise
- [ ] T067 [P] [US5] Extract frequently used hardcoded values (timeouts, retry counts, URL patterns) to backend/src/config.py or backend/src/constants.py with sensible defaults
- [ ] T068 [P] [US5] Identify and consolidate duplicated logic (10+ lines) across backend/src/ into shared utilities in backend/src/utils.py
- [ ] T069 [P] [US5] Scan and remove dead code in frontend/src/ — verify zero references via grep/eslint before removal
- [ ] T070 [P] [US5] Fix silent error handlers in frontend/src/ — add logging, user-facing error messages, or re-throw
- [ ] T071 [P] [US5] Extract frequently used hardcoded values in frontend/src/ to configuration constants
- [ ] T072 [P] [US5] Add regression tests for code quality fixes that change behavior (silent failures now surfacing) in backend/tests/unit/
- [ ] T073 [P] [US5] Add regression tests for code quality fixes that change behavior in frontend/src/**/*.test.tsx colocated test files
- [ ] T074 [US5] Validate US5: run backend ruff check + ruff format --check + pyright + pytest (batched) in backend/
- [ ] T075 [US5] Validate US5: run frontend eslint + tsc --noEmit + vitest + npm run build in frontend/

**Checkpoint**: All code quality issues fixed or flagged. Codebase is clean, maintainable, free of dead code and silent failures.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, summary compilation, and cross-story verification

- [ ] T076 Compile final summary table per output contract format in specs/025-bug-basher/contracts/output-contracts.md — all findings listed with #, File, Line(s), Category, Description, Status
- [ ] T077 Verify every TODO(bug-bash) comment in source has a corresponding ⚠️ Flagged (TODO) entry in summary table
- [ ] T078 Verify every ✅ Fixed entry in summary table has at least one regression test (1:1 ratio per SC-002)
- [ ] T079 Run final full backend validation: ruff check + ruff format --check + pyright + pytest full suite (batched) in backend/
- [ ] T080 Run final full frontend validation: eslint + tsc --noEmit + vitest + npm run build in frontend/
- [ ] T081 Cross-check: compare test pass counts against Phase 1 baseline — verify zero previously passing tests broken (SC-003)
- [ ] T082 Verify commit messages follow commit message contract format: fix(<category>): <description> with What/Why/How/Affects/Tests
- [ ] T083 Final review: ensure no architecture changes, no public API changes, no new dependencies, each fix minimal and focused (FR-024, FR-025, FR-026)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all file-level audit work
- **User Stories (Phases 3–7)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order (P1 → P2 → P3 → P4 → P5)
  - Or in parallel if staffed (security audit independent of runtime audit, etc.)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 — Security (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 — Runtime (P2)**: Can start after Foundational (Phase 2) — Independent of US1 (different bug category)
- **User Story 3 — Logic (P3)**: Can start after Foundational (Phase 2) — Independent of US1/US2 (different bug category)
- **User Story 4 — Test Quality (P4)**: Can start after Foundational (Phase 2) — Benefits from US1–US3 being done first (tests may reference fixed code), but independently testable
- **User Story 5 — Code Quality (P5)**: Can start after Foundational (Phase 2) — Benefits from US1–US3 being done first (dead code analysis more accurate after fixes), but independently testable

### Within Each User Story

- Pattern scan results from Phase 2 inform which files to audit first
- High-priority files (listed in plan.md) audited before remaining files
- Fix bugs inline with minimal changes
- Add regression test(s) for each fix in the corresponding test file
- Flag ambiguous issues with `# TODO(bug-bash):` comment
- Validate by running lint + type check + relevant test files
- Full suite validation at end of each story phase

### Parallel Opportunities

- All Phase 2 scan tasks (T004–T008) can run in parallel
- Within US1: All file audit tasks (T010–T020) can run in parallel (different files)
- Within US2: All file audit tasks (T026–T035) can run in parallel
- Within US3: All file audit tasks (T041–T049) can run in parallel
- Within US4: All scan/fix tasks (T055–T062) can run in parallel
- Within US5: All scan/fix tasks (T066–T071) can run in parallel
- Cross-story: US1–US5 can run in parallel if team capacity allows (different bug categories, different files)

---

## Parallel Example: User Story 1 (Security)

```bash
# Launch all backend security audit tasks together:
Task T010: "Audit and fix backend/src/api/auth.py for OAuth flow vulnerabilities"
Task T011: "Audit and fix backend/src/services/github_auth.py for auth issues"
Task T012: "Audit and fix backend/src/services/encryption.py for crypto issues"
Task T013: "Audit and fix backend/src/api/webhooks.py for signature verification"
Task T014: "Audit and fix backend/src/middleware/ for information leakage"
Task T015: "Audit and fix backend/src/prompts/ for injection risks"

# Launch all frontend security audit tasks together:
Task T018: "Audit and fix frontend/src/services/api.ts for auth header injection"
Task T019: "Audit and fix frontend/src/hooks/useAuth.ts for token storage security"
Task T020: "Audit and fix frontend/src/components/ for XSS vectors"
```

## Parallel Example: User Story 4 (Test Quality)

```bash
# Launch all test quality scan tasks together:
Task T055: "Audit test_copilot_polling.py for MagicMock leaks"
Task T056: "Audit test_github_projects.py for MagicMock leaks"
Task T057: "Scan all tests for MagicMock used as file paths/URLs/config"
Task T058: "Scan all tests for meaningless assertions"
Task T059: "Identify untested critical code paths"
```

---

## Implementation Strategy

### MVP First (User Story 1 — Security Only)

1. Complete Phase 1: Setup — establish baseline
2. Complete Phase 2: Foundational — run all pattern scans
3. Complete Phase 3: User Story 1 (Security) — audit, fix, test, validate
4. **STOP and VALIDATE**: Security audit is independently complete and testable
5. Deploy/review if ready — highest-risk bugs are addressed

### Incremental Delivery

1. Complete Setup + Foundational → Scan results ready
2. Add User Story 1 (Security) → Test independently → Review (MVP!)
3. Add User Story 2 (Runtime) → Test independently → Review
4. Add User Story 3 (Logic) → Test independently → Review
5. Add User Story 4 (Test Quality) → Test independently → Review
6. Add User Story 5 (Code Quality) → Test independently → Review
7. Each story adds value without breaking previous fixes

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Security) — highest priority
   - Developer B: User Story 2 (Runtime) — independent category
   - Developer C: User Story 3 (Logic) — independent category
3. After US1–US3 complete:
   - Developer A: User Story 4 (Test Quality) — benefits from seeing fixed code
   - Developer B: User Story 5 (Code Quality) — benefits from seeing fixed code
4. Final team review: Polish phase together

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story (US1=Security, US2=Runtime, US3=Logic, US4=TestQuality, US5=CodeQuality)
- Each user story is independently completable and testable
- Regression tests are MANDATORY (FR-013, SC-002) — every fix needs at least one test
- Ambiguous issues get `# TODO(bug-bash):` comments, not direct fixes (FR-022)
- Run tests in batches to avoid timeout (research.md finding #6)
- Frontend E2E tests deferred to CI pipeline (research.md finding #7)
- Commit per category: `fix(security):`, `fix(runtime):`, `fix(logic):`, `fix(test):`, `fix(quality):`
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts, scope creep beyond minimal focused fixes
