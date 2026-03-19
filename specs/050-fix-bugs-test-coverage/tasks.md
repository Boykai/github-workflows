# Tasks: Find/Fix Bugs & Increase Test Coverage

**Input**: Design documents from `/specs/050-fix-bugs-test-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests ARE the primary deliverable of this feature — explicitly requested in the spec. All phases include test-writing tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/` (Python/FastAPI), `solune/frontend/` (React/TypeScript)
- All paths are relative to the monorepo root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing tooling works, establish baseline measurements, and prepare the environment for bug fixes and coverage expansion.

- [X] T001 Verify backend virtual environment and dev dependencies are installed in solune/backend/.venv/
- [ ] T002 [P] Verify frontend dependencies are installed in solune/frontend/ via `npm install`
- [X] T003 [P] Run baseline backend test suite and record current coverage percentage via `cd solune/backend && .venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing`
- [ ] T004 [P] Run baseline frontend test suite and record current coverage percentage via `cd solune/frontend && npm run test:coverage`
- [ ] T005 [P] Run baseline E2E test suite and record current spec count via `cd solune/frontend && npm run test:e2e`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Static analysis sweep and flaky test detection — surfaces all latent defects before any fixes or new tests are written.

**⚠️ CRITICAL**: No bug-fix or coverage-expansion work should begin until this phase is complete. These tasks produce the defect backlog that drives all subsequent phases.

- [X] T006 [P] Run backend lint sweep via `cd solune/backend && .venv/bin/ruff check src/` and capture violation report
- [X] T007 [P] Run backend type-check sweep via `cd solune/backend && .venv/bin/pyright src/` and capture error report
- [ ] T008 [P] Run frontend lint sweep via `cd solune/frontend && npx eslint . --max-warnings=0` and capture violation report
- [ ] T009 [P] Run frontend type-check sweep via `cd solune/frontend && npx tsc --noEmit` and capture error report
- [X] T010 [P] Run backend test suite with JUnit output via `cd solune/backend && .venv/bin/python -m pytest tests/ -q --tb=short --junitxml=results.xml`
- [ ] T011 [P] Run frontend test suite with verbose reporter via `cd solune/frontend && npm run test -- --reporter=verbose`
- [ ] T012 Run flaky test detection across 5+ runs via `cd solune/backend && python scripts/detect_flaky.py --runs=5` (depends on T010)
- [ ] T013 Triage all findings from T006–T012: categorize each as fix-now, fix-later, or false-positive and document in a triage report

**Checkpoint**: All static analysis and test execution reports generated. Defect backlog established. Phase 3 can now begin.

---

## Phase 3: User Story 1 — Fix Known Bugs Blocking Test Infrastructure (Priority: P1) 🎯 MVP

**Goal**: Resolve all 4 known bugs (BUG-001 through BUG-004) that block or degrade test infrastructure, producing trustworthy, deterministic test results.

**Independent Test**: Run the complete backend test suite and verify: zero AsyncMock warnings, zero flaky failures, non-zero mutation kill rates, and valid pipeline state transitions.

### BUG-001: Fix Mutmut Trampoline Name-Resolution (Critical)

- [X] T014 [US1] Investigate current `get_mutant_name()` behavior and `orig.__module__` prefix mismatch in solune/backend/scripts/run_mutmut_shard.py
- [X] T015 [US1] Patch trampoline template or normalize PYTHONPATH in solune/backend/scripts/run_mutmut_shard.py so `src.` prefix is consistently handled
- [X] T016 [P] [US1] Verify mutmut version pinning (≥3.2.0) in solune/backend/pyproject.toml aligns with trampoline fix
- [X] T017 [US1] Verify fix by running `cd solune/backend && python scripts/run_mutmut_shard.py --shard=auth-and-projects` and confirming kill rate >0%

### BUG-002: Fix Cache Leakage Between Tests

- [X] T018 [US1] Audit all cache entry points (LRU caches, module-level dicts, class singletons) in solune/backend/src/services/cache.py
- [X] T019 [US1] Verify `_clear_test_caches` autouse fixture covers all cache entry points in solune/backend/tests/conftest.py
- [X] T020 [US1] Add any missing cache-clearing calls to the autouse fixture in solune/backend/tests/conftest.py
- [X] T021 [US1] Verify fix by running `cd solune/backend && .venv/bin/python -m pytest tests/unit/ tests/integration/ -q --tb=short` with no stale state

### BUG-003: Fix AsyncMock Warnings in Integration Tests

- [X] T022 [US1] Identify all `AsyncMock(spec=...)` patterns in solune/backend/tests/integration/conftest.py
- [X] T023 [US1] Replace each `AsyncMock(spec=SomeService)` with a plain async stub class implementing the same interface in solune/backend/tests/integration/conftest.py
- [X] T024 [US1] Verify fix by running `cd solune/backend && .venv/bin/python -m pytest tests/ -q 2>&1 | grep -i "asyncmock"` and confirming zero matches

### BUG-004: Fix Pipeline "Stuck in In Progress"

- [X] T025 [US1] Review state transition logic in solune/backend/src/services/copilot_polling/state_validation.py for overly strict backward-transition rejection
- [X] T026 [US1] Fix state validation to accept valid forward transitions (Queued → In Progress → Completed) in solune/backend/src/services/copilot_polling/state_validation.py
- [X] T027 [P] [US1] Review pipeline service for transition ordering issues in solune/backend/src/services/copilot_polling/pipeline.py
- [X] T028 [US1] Add explicit test cases for all valid and invalid transition sequences in solune/backend/tests/unit/test_copilot_polling/
- [X] T029 [US1] Verify fix by running `cd solune/backend && .venv/bin/python -m pytest tests/unit/test_copilot_polling/ -q --tb=short`

### US1 Integration Verification

- [X] T030 [US1] Run full backend test suite and confirm zero warnings, zero flaky failures: `cd solune/backend && .venv/bin/python -m pytest tests/ -q --tb=short`

**Checkpoint**: All 4 known bugs fixed. Test infrastructure is trustworthy. Coverage expansion (Phases 4–5) can now begin.

---

## Phase 4: User Story 2 — Discover and Triage Existing Defects via Static Analysis (Priority: P2)

**Goal**: Produce a complete, triaged defect backlog from static analysis and test execution across both codebases, including quarantining and documenting flaky tests.

**Independent Test**: Verify that lint, type-check, and test suites produce clean reports, and flaky test detection across 10 runs reports zero flaky tests.

> **Note**: Most discovery work was performed in Phase 2 (Foundational). This phase focuses on acting on findings: fixing critical violations and quarantining flaky tests.

- [ ] T031 [US2] Fix all "fix-now" lint violations identified in T006 triage across solune/backend/src/
- [ ] T032 [P] [US2] Fix all "fix-now" type errors identified in T007 triage across solune/backend/src/
- [ ] T033 [P] [US2] Fix all "fix-now" lint violations identified in T008 triage across solune/frontend/src/
- [ ] T034 [P] [US2] Fix all "fix-now" type errors identified in T009 triage across solune/frontend/src/
- [ ] T035 [US2] Quarantine genuinely flaky tests with `@pytest.mark.skip(reason="flaky: <root_cause>")` and document root causes (async timing, shared state) in solune/backend/tests/
- [ ] T035b [US2] Define quarantine-removal process: document criteria for re-enabling quarantined tests (root cause fixed, 10 consecutive green runs) and add a CI reminder/periodic check so quarantines do not become permanent
- [ ] T036 [US2] Run extended flaky test detection via `cd solune/backend && python scripts/detect_flaky.py --runs=10` and confirm zero flaky tests remain

**Checkpoint**: All critical static analysis findings resolved. Flaky tests quarantined with documented root causes. Codebase is clean for coverage expansion.

---

## Phase 5: User Story 3 — Expand Backend Test Coverage (Priority: P3)

**Goal**: Increase backend test coverage from 75% to at least 80% (stretch: 85%+) by targeting high-risk, critical-path modules with integration tests, unit tests, property-based tests, and mutation testing expansion.

**Independent Test**: Run `cd solune/backend && .venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80` and confirm pass.

### API Route Integration Tests (Step 8)

- [ ] T037 [P] [US3] Create integration test for auth flow API routes using `httpx.AsyncClient` + `ASGITransport` pattern in solune/backend/tests/integration/test_api_auth.py
- [ ] T038 [P] [US3] Create integration test for webhook dispatch API routes in solune/backend/tests/integration/test_api_webhooks.py
- [ ] T039 [P] [US3] Create integration test for pipeline CRUD API routes in solune/backend/tests/integration/test_api_pipelines.py
- [ ] T040 [P] [US3] Create integration test for chat message API routes in solune/backend/tests/integration/test_api_chat.py

### High-Risk Service Module Tests (Step 9)

- [ ] T041 [P] [US3] Add unit tests for recovery logic in solune/backend/tests/unit/test_copilot_polling_recovery.py covering solune/backend/src/services/copilot_polling/recovery.py
- [X] T042 [P] [US3] Add unit tests for state validation edge cases in solune/backend/tests/unit/test_state_validation_edges.py covering solune/backend/src/services/copilot_polling/state_validation.py
- [X] T043 [P] [US3] Add unit tests for workflow transitions logic in solune/backend/tests/unit/test_workflow_transitions.py covering solune/backend/src/services/workflow_orchestrator/transitions.py
- [ ] T044 [P] [US3] Add unit tests for signal bridge in solune/backend/tests/unit/test_signal_bridge.py covering solune/backend/src/services/signal_bridge.py
- [ ] T045 [P] [US3] Add unit tests for signal delivery in solune/backend/tests/unit/test_signal_delivery.py covering solune/backend/src/services/signal_delivery.py
- [ ] T046 [P] [US3] Add unit tests for guard enforcement in solune/backend/tests/unit/test_guard_service.py covering solune/backend/src/services/guard_service.py
- [ ] T047 [P] [US3] Add Hypothesis property-based tests for state machine invariants in solune/backend/tests/property/test_state_machine_properties.py
- [ ] T048 [P] [US3] Add Hypothesis property-based tests for parser invariants in solune/backend/tests/property/test_parser_properties.py

### Mutation Testing Expansion (Step 10)

- [X] T049 [US3] Expand mutation testing targets by adding `src/api/`, `src/middleware/`, `src/utils.py` to SHARDS dict in solune/backend/scripts/run_mutmut_shard.py
- [ ] T050 [US3] Run expanded mutation testing via `cd solune/backend && python scripts/run_mutmut_shard.py` across all shards and identify surviving mutants
- [ ] T051 [US3] Kill surviving mutants with targeted assertions in corresponding test files under solune/backend/tests/

### Characterization Tests for DRY Candidates (Step 11)

- [X] T052 [P] [US3] Add characterization tests for 8 repo-resolution paths in solune/backend/tests/unit/test_regression_bugfixes.py to pin current behavior
- [X] T053 [P] [US3] Add characterization tests for 5 error-response patterns in solune/backend/tests/unit/test_regression_bugfixes.py to pin current behavior

### US3 Coverage Verification

- [ ] T054 [US3] Run backend coverage check and confirm ≥80%: `cd solune/backend && .venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80`

**Checkpoint**: Backend coverage ≥80%. Mutation kill rate >60% per shard. All high-risk modules covered. Characterization tests protect DRY candidates.

---

## Phase 6: User Story 4 — Expand Frontend Test Coverage (Priority: P4)

**Goal**: Increase frontend statement coverage from 51% to at least 55% (stretch: 65%+), branch coverage from 44% to 50%+, and expand the E2E suite from 10 to 14+ specs.

**Independent Test**: Run `cd solune/frontend && npm run test:coverage` and `cd solune/frontend && npm run test:e2e` and confirm all thresholds pass.

### Cover App.tsx (Step 12)

- [X] T055 [US4] Create comprehensive tests for App.tsx including route rendering, auth guards, and error boundaries using `MemoryRouter` in solune/frontend/src/__tests__/App.test.tsx

### Cover Board Components (Step 13)

- [ ] T056 [P] [US4] Add interaction tests for column drag-drop behavior in solune/frontend/src/components/board/ test files
- [ ] T057 [P] [US4] Add interaction tests for card rendering in solune/frontend/src/components/board/ test files
- [ ] T058 [P] [US4] Add interaction tests for project switching in solune/frontend/src/components/board/ test files

### Increase Branch Coverage in Hooks (Step 14)

- [ ] T059 [P] [US4] Add tests for error state branches in hook test files under solune/frontend/src/hooks/
- [ ] T060 [P] [US4] Add tests for loading state branches in hook test files under solune/frontend/src/hooks/
- [ ] T061 [P] [US4] Add tests for empty data branches in hook test files under solune/frontend/src/hooks/
- [ ] T062 [P] [US4] Add tests for API failure branches in hook test files under solune/frontend/src/hooks/

### Expand E2E Suite (Step 15)

- [X] T063 [P] [US4] Create E2E spec for agent creation flow in solune/frontend/e2e/agent-creation.spec.ts
- [X] T064 [P] [US4] Create E2E spec for pipeline monitoring flow in solune/frontend/e2e/pipeline-monitoring.spec.ts
- [X] T065 [P] [US4] Create E2E spec for MCP tool configuration flow in solune/frontend/e2e/mcp-tool-config.spec.ts
- [X] T066 [P] [US4] Create E2E spec for error recovery flow in solune/frontend/e2e/error-recovery.spec.ts

### Run Stryker and Kill Survivors (Step 16)

- [ ] T067 [US4] Run Stryker mutation testing via `cd solune/frontend && npm run test:mutate` and review HTML report (depends on T055–T062)
- [ ] T068 [US4] Add targeted assertions to kill surviving mutants in hooks and lib modules under solune/frontend/src/hooks/ and solune/frontend/src/lib/ test files

### US4 Coverage Verification

- [ ] T069 [US4] Run frontend coverage check and confirm thresholds pass: `cd solune/frontend && npm run test:coverage`
- [ ] T070 [US4] Run E2E suite and confirm ≥14 passing specs: `cd solune/frontend && npm run test:e2e`

**Checkpoint**: Frontend statement coverage ≥55%, branch coverage ≥50%, function coverage ≥45%. E2E suite has ≥14 specs. Mutation survivors killed.

---

## Phase 7: User Story 5 — Harden CI Gates and Prevent Regression (Priority: P5)

**Goal**: Lock in quality improvements by ratcheting coverage thresholds, verifying pre-commit hooks, and adding chaos/concurrency tests so that quality cannot silently degrade.

**Independent Test**: Attempt to merge code that lowers coverage below thresholds and verify it is rejected.

### Ratchet Coverage Thresholds (Step 17)

- [X] T071 [P] [US5] Ratchet backend coverage threshold from `fail_under = 75` to `fail_under = 80` in solune/backend/pyproject.toml `[tool.coverage.report]` section
- [X] T072 [P] [US5] Ratchet frontend coverage thresholds from 50/44/41/50 to 55/50/45/55 (statements/branches/functions/lines) in solune/frontend/vitest.config.ts

### Verify Pre-commit Hooks (Step 18)

- [X] T073 [US5] Verify pre-commit hook runs `ruff format` + `ruff check` + `pyright` on changed backend files in solune/scripts/pre-commit
- [X] T074 [P] [US5] Verify pre-commit hook runs `eslint` + `tsc --noEmit` on changed frontend files in solune/scripts/pre-commit
- [ ] T075 [US5] Test pre-commit hooks by introducing a deliberate lint violation, attempting to commit, and confirming the hook blocks it
- [ ] T075b [US5] Measure pre-commit hook execution time on a typical changeset (≤5 files) and verify it completes in under 30 seconds per SC-009; if exceeded, profile and optimize the slowest hook stage

### Document Emergency Hotfix Override (Step 18b)

- [ ] T075c [US5] Document emergency hotfix override process for temporarily bypassing coverage gates (e.g., `--no-verify` with required post-merge coverage restoration) in solune/docs/ or the project README

### Expand Chaos/Concurrency Tests (Step 19)

- [X] T076 [P] [US5] Add chaos test for concurrent pipeline state updates in solune/backend/tests/chaos/test_concurrent_state_updates.py
- [X] T077 [P] [US5] Add chaos test for DB connection pool exhaustion in solune/backend/tests/chaos/test_connection_pool_exhaustion.py
- [X] T078 [P] [US5] Add concurrency test for WebSocket reconnection under load in solune/backend/tests/concurrency/test_websocket_reconnection.py

### US5 Hardening Verification

- [ ] T079 [US5] Verify ratcheted thresholds by running `cd solune/backend && .venv/bin/python -m pytest tests/ --cov=src --cov-fail-under=80`
- [ ] T080 [US5] Verify ratcheted thresholds by running `cd solune/frontend && npm run test:coverage`
- [ ] T081 [US5] Run chaos tests via `cd solune/backend && .venv/bin/python -m pytest tests/chaos/ -q --tb=short`
- [ ] T082 [US5] Run concurrency tests via `cd solune/backend && .venv/bin/python -m pytest tests/concurrency/ -q --tb=short`

**Checkpoint**: Coverage thresholds ratcheted and enforced. Pre-commit hooks verified. Chaos and concurrency tests pass. Quality improvements are locked in.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup that spans all user stories.

- [ ] T083 Run full backend verification suite: `cd solune/backend && .venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80`
- [ ] T084 [P] Run full frontend verification suite: `cd solune/frontend && npm run test:coverage`
- [ ] T085 [P] Run extended flaky detection (10 runs) and confirm zero flaky tests: `cd solune/backend && python scripts/detect_flaky.py --runs=10`
- [ ] T086 Run backend tests and confirm zero AsyncMock warnings: `cd solune/backend && .venv/bin/python -m pytest tests/ -q 2>&1 | grep -i asyncmock`
- [ ] T087 [P] Run all E2E specs and confirm pass: `cd solune/frontend && npm run test:e2e`
- [ ] T088 Run backend mutation testing across all shards and confirm >60% kill rate: `cd solune/backend && python scripts/run_mutmut_shard.py`
- [ ] T089 [P] Run frontend mutation testing and confirm thresholds met: `cd solune/frontend && npm run test:mutate`
- [ ] T090 Run quickstart.md verification — execute all commands from specs/050-fix-bugs-test-coverage/quickstart.md and confirm they pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 / Bug Fixes (Phase 3)**: Depends on Foundational phase (Phase 2) completion — BLOCKS coverage expansion
- **User Story 2 / Static Analysis Actions (Phase 4)**: Depends on Foundational phase (Phase 2); can run in parallel with Phase 3
- **User Story 3 / Backend Coverage (Phase 5)**: Depends on Phase 3 (Bug Fixes) completion — test infrastructure must be trustworthy
- **User Story 4 / Frontend Coverage (Phase 6)**: Depends on Phase 3 (Bug Fixes) completion — can run in parallel with Phase 5
- **User Story 5 / CI Hardening (Phase 7)**: Depends on Phases 5 and 6 (coverage must meet thresholds before ratcheting)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — **BLOCKS User Stories 3, 4, 5** (fix before expand principle)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Independent of US1; discovery can overlap with bug fixes
- **User Story 3 (P3)**: Requires US1 complete — backend test infrastructure must be trustworthy before expanding coverage
- **User Story 4 (P4)**: Requires US1 complete — can run in parallel with US3 (different codebase: frontend vs backend)
- **User Story 5 (P5)**: Requires US3 and US4 complete — thresholds can only be ratcheted after coverage meets targets

### Within Each User Story

- Bug fixes (US1): Each bug fix is independent and can be parallelized
- Static analysis (US2): Fix-now items can be parallelized across codebases
- Backend coverage (US3): API route tests, service tests, property tests, and characterization tests can be parallelized; mutation testing depends on test expansion
- Frontend coverage (US4): Component tests, hook tests, and E2E specs can be parallelized; Stryker depends on coverage expansion
- CI hardening (US5): Threshold ratcheting, pre-commit verification, and chaos tests can be parallelized

### Parallel Opportunities

- All Setup tasks (T001–T005) marked [P] can run in parallel
- All Foundational lint/type-check tasks (T006–T011) marked [P] can run in parallel
- Within US1: BUG-001 (T014–T017), BUG-002 (T018–T021), BUG-003 (T022–T024), BUG-004 (T025–T029) can be worked in parallel
- Within US3: API route tests (T037–T040), service tests (T041–T048), and characterization tests (T052–T053) can all be parallelized
- Within US4: Board tests (T056–T058), hook tests (T059–T062), and E2E specs (T063–T066) can all be parallelized
- US3 (backend coverage) and US4 (frontend coverage) can run in parallel on separate tracks

---

## Parallel Example: User Story 3 (Backend Coverage)

```bash
# Launch all API route integration tests together:
Task: T037 "Integration test for auth flow in tests/integration/test_api_auth.py"
Task: T038 "Integration test for webhook dispatch in tests/integration/test_api_webhooks.py"
Task: T039 "Integration test for pipeline CRUD in tests/integration/test_api_pipelines.py"
Task: T040 "Integration test for chat messages in tests/integration/test_api_chat.py"

# Launch all high-risk service module tests together:
Task: T041 "Unit tests for recovery.py"
Task: T042 "Unit tests for state_validation.py edges"
Task: T043 "Unit tests for transitions.py"
Task: T044 "Unit tests for signal_bridge.py"
Task: T045 "Unit tests for signal_delivery.py"
Task: T046 "Unit tests for guard_service.py"

# Launch all property-based tests together:
Task: T047 "Property tests for state machine invariants"
Task: T048 "Property tests for parser invariants"
```

## Parallel Example: User Story 4 (Frontend Coverage)

```bash
# Launch all E2E specs together:
Task: T063 "E2E spec for agent creation"
Task: T064 "E2E spec for pipeline monitoring"
Task: T065 "E2E spec for MCP tool config"
Task: T066 "E2E spec for error recovery"

# Launch all hook branch tests together:
Task: T059 "Error state branches in hooks"
Task: T060 "Loading state branches in hooks"
Task: T061 "Empty data branches in hooks"
Task: T062 "API failure branches in hooks"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — Bug Fixes)

1. Complete Phase 1: Setup — verify environment
2. Complete Phase 2: Foundational — run static analysis and flaky detection
3. Complete Phase 3: User Story 1 — fix all 4 known bugs
4. **STOP and VALIDATE**: Run full backend test suite — zero warnings, zero flaky, kill rate >0%
5. Deploy/demo if ready — test infrastructure is trustworthy

### Incremental Delivery

1. Complete Setup + Foundational → Environment verified, defect backlog established
2. Fix Known Bugs (US1) → Test infrastructure trustworthy → **MVP!**
3. Triage Static Analysis (US2) → Clean codebase → Ready for expansion
4. Expand Backend Coverage (US3) → 80%+ coverage → Risk-first protection
5. Expand Frontend Coverage (US4) → 55%+ statements → User-facing protection
6. Harden CI Gates (US5) → Thresholds ratcheted → Quality locked in
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Split into bug-fix tracks:
   - Developer A: BUG-001 + BUG-002
   - Developer B: BUG-003 + BUG-004
3. After bugs fixed:
   - Developer A: User Story 3 (Backend Coverage)
   - Developer B: User Story 4 (Frontend Coverage)
   - Developer C: User Story 2 (Static Analysis Actions)
4. After coverage met: User Story 5 (CI Hardening) — any developer

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Fix before expand**: Phase 3 (bug fixes) MUST complete before Phases 5–6 (coverage expansion)
- **Risk-first coverage**: Target high-complexity, critical-path code; not easy-to-cover files
- **Mutation testing expansion**: Gradual — services → API → middleware
- **AsyncMock replacement**: Use plain async stub classes per repo best practice
- **Threshold ratcheting**: Raise only after consistently meeting in CI
- **Scope exclusion**: No DRY refactoring — add characterization tests first, refactor separately
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

## Task Summary

| Phase | Description | Task Range | Count |
|-------|-------------|------------|-------|
| Phase 1 | Setup | T001–T005 | 5 |
| Phase 2 | Foundational | T006–T013 | 8 |
| Phase 3 | US1: Fix Known Bugs (P1) | T014–T030 | 17 |
| Phase 4 | US2: Static Analysis Actions (P2) | T031–T036 | 6 |
| Phase 5 | US3: Backend Coverage (P3) | T037–T054 | 18 |
| Phase 6 | US4: Frontend Coverage (P4) | T055–T070 | 16 |
| Phase 7 | US5: CI Hardening (P5) | T071–T082 | 12 |
| Phase 8 | Polish | T083–T090 | 8 |
| **Total** | | **T001–T090** | **90** |

| User Story | Tasks | Parallel Opportunities |
|------------|-------|----------------------|
| US1: Fix Known Bugs | 17 | 4 independent bug-fix tracks |
| US2: Static Analysis | 6 | 4 parallel fix tracks (BE lint, BE types, FE lint, FE types) |
| US3: Backend Coverage | 18 | API routes (4), services (6), property (2), characterization (2) |
| US4: Frontend Coverage | 16 | Board (3), hooks (4), E2E (4) |
| US5: CI Hardening | 12 | Thresholds (2), hooks (2), chaos/concurrency (3) |

**Suggested MVP scope**: User Story 1 (Phase 3) — fix all 4 known bugs. This unblocks all downstream coverage expansion and produces immediate, measurable improvement (non-zero mutation kill rates, clean test output).
