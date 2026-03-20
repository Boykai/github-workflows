# Tasks: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Input**: Design documents from `/specs/051-fix-bugs-test-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Predecessor**: `050-fix-bugs-test-coverage` (42% complete — all 4 critical bugs fixed, infrastructure established)

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

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Verify existing tooling works, establish baseline measurements, and prepare the environment for the Phase 2 work.

- [ ] T001 [P] [Setup] Verify backend virtual environment and dev dependencies are installed in `solune/backend/.venv/` via `cd solune/backend && .venv/bin/python -m pytest --version`
- [ ] T002 [P] [Setup] Verify frontend dependencies are installed in `solune/frontend/` via `cd solune/frontend && npm ls --depth=0`
- [ ] T003 [P] [Setup] Run baseline backend test suite and record current coverage percentage via `cd solune/backend && .venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing`

---

## Phase A: Static Analysis Completion (User Story 1 — P1)

**Purpose**: Finish the static analysis sweep started in spec 050 (~50% complete). Resolve all remaining lint errors, type-check failures, and test warnings. Detect and quarantine flaky tests.

**⚠️ CRITICAL**: No coverage-expansion work (Phases B or C) should begin until this phase is complete. Clean analysis ensures new tests are written against correct, type-safe code.

### Frontend Static Analysis

- [ ] T004 [P] [US1] Run frontend lint sweep via `cd solune/frontend && npx eslint . --max-warnings=0` and triage all violations as fix-now, fix-later, or false-positive
- [ ] T005 [US1] Fix all frontend lint violations triaged as fix-now in `solune/frontend/src/`
- [ ] T006 [P] [US1] Run frontend type-check via `cd solune/frontend && npx tsc --noEmit` and fix all type errors
- [ ] T007 [P] [US1] Catalog and resolve all frontend test warnings via `cd solune/frontend && npx vitest run --reporter=verbose 2>&1 | grep -i warn`

### Backend Static Analysis

- [ ] T008 [P] [US1] Run backend lint sweep via `cd solune/backend && .venv/bin/ruff check src/` and fix all violations
- [ ] T009 [P] [US1] Run backend type-check via `cd solune/backend && .venv/bin/pyright src/` and fix all type errors
- [ ] T010 [P] [US1] Run backend security scan via `cd solune/backend && .venv/bin/bandit -r src/ -c pyproject.toml` and fix all issues

### Flaky Test Detection

- [ ] T011 [US1] Run backend flaky test detection via `cd solune/backend && python scripts/detect_flaky.py --runs=5` and document results
- [ ] T012 [US1] Run frontend flaky test detection by executing `cd solune/frontend && npm run test` 5 consecutive times and comparing results
- [ ] T013 [US1] Quarantine any confirmed flaky tests with root cause category, tracking reference, and re-enablement condition

### Backend Lint/Type Fix

- [ ] T014 [US1] Fix any remaining backend lint violations (ruff), type errors (pyright), and security issues (bandit) found in T008–T010

### Verification

- [ ] T015 [US1] Verify zero frontend lint violations: `cd solune/frontend && npx eslint . --max-warnings=0` exits 0
- [ ] T016 [US1] Verify zero frontend type errors: `cd solune/frontend && npx tsc --noEmit` exits 0
- [ ] T017 [US1] Verify zero backend lint violations: `cd solune/backend && .venv/bin/ruff check src/` exits 0
- [ ] T018 [US1] Verify zero backend type errors: `cd solune/backend && .venv/bin/pyright src/` exits 0
- [ ] T019 [US1] Verify zero backend security issues: `cd solune/backend && .venv/bin/bandit -r src/ -c pyproject.toml` exits 0
- [ ] T020 [US1] Verify zero flaky tests detected across both test suites
- [ ] T021 [US1] Verify all frontend test warnings are resolved or documented

**⚠️ GATE**: All T015–T021 must pass before proceeding to Phase B. Run all verification commands and confirm exit code 0 for each.

---

## Phase B: Backend Coverage Expansion (User Story 2 — P2)

**Purpose**: Raise backend line coverage from 75% to at least 80% by adding integration tests for untested API routes, unit tests for orphan files, service edge-case tests, and property-based tests.

### API Route Integration Tests

- [ ] T022 [P] [US2] Add integration tests for auth callback route covering valid input, invalid input, and authorization checks in `solune/backend/tests/integration/test_auth_callback.py` using `httpx.AsyncClient` + `ASGITransport` pattern
- [ ] T023 [P] [US2] Add integration tests for webhook dispatch route covering valid input, invalid input, and authorization checks in `solune/backend/tests/integration/test_webhook_dispatch.py` using `httpx.AsyncClient` + `ASGITransport` pattern
- [ ] T024 [P] [US2] Add integration tests for pipeline launch route covering valid input, invalid input, and authorization checks in `solune/backend/tests/integration/test_pipeline_launch.py` using `httpx.AsyncClient` + `ASGITransport` pattern
- [ ] T025 [P] [US2] Add integration tests for chat confirm route covering valid input, invalid input, and authorization checks in `solune/backend/tests/integration/test_chat_confirm.py` using `httpx.AsyncClient` + `ASGITransport` pattern

### Orphan File Unit Tests

- [ ] T026 [P] [US2] Add unit tests for dependency injection module in `solune/backend/tests/unit/test_dependencies.py` targeting ≥90% line coverage of `solune/backend/src/dependencies.py`
- [ ] T027 [P] [US2] Add unit tests for request ID middleware in `solune/backend/tests/unit/test_request_id_middleware.py` targeting ≥90% line coverage of `solune/backend/src/middleware/request_id.py`

### Service Edge-Case Tests

- [ ] T028 [P] [US2] Add edge-case tests for recovery logic covering retry scenarios, max-retry exhaustion, and partial recovery in `solune/backend/tests/unit/test_recovery_edge_cases.py`
- [ ] T029 [P] [US2] Add edge-case tests for state validation covering boundary state values, invalid transitions, and concurrent state updates in `solune/backend/tests/unit/test_state_validation_edge_cases.py`
- [ ] T030 [P] [US2] Add edge-case tests for signal bridge covering error propagation paths, timeout handling, and connection failures in `solune/backend/tests/unit/test_signal_bridge_edge_cases.py`

### Property-Based Tests

- [ ] T031 [P] [US2] Add property-based tests for pipeline state machine transition invariants using Hypothesis with ≥100 generated inputs in `solune/backend/tests/property/test_pipeline_state_machine.py`
- [ ] T032 [P] [US2] Add property-based tests for markdown parser roundtrip consistency using Hypothesis with ≥100 generated inputs in `solune/backend/tests/property/test_markdown_parser.py`

### Mutation Expansion

- [ ] T033 [US2] Expand mutation testing targets in `solune/backend/scripts/run_mutmut_shard.py` to include `src/api/`, `src/middleware/`, and `src/utils.py` distributed across existing 4 shards by module affinity

### Coverage Gate

- [ ] T034 [US2] Verify backend line coverage ≥ 80% via `cd solune/backend && .venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80`

---

## Phase C: Frontend Coverage Expansion (User Story 3 — P3)

**Purpose**: Raise frontend statement coverage from 51% to ≥55%, branch coverage from 44% to ≥50%, and function coverage from ~41% to ≥45% by testing the largest untested component and hook files.

### Board Component Tests

- [ ] T035 [P] [US3] Add tests for ProjectBoard component covering rendering, user interactions, and conditional branches in `solune/frontend/src/components/board/__tests__/ProjectBoard.test.tsx` using `@testing-library/react` and `DndContext` wrapper
- [ ] T036 [P] [US3] Add tests for BoardToolbar component covering rendering, user interactions, and conditional branches in `solune/frontend/src/components/board/__tests__/BoardToolbar.test.tsx`
- [ ] T037 [P] [US3] Add tests for CleanUpConfirmModal component covering rendering, user interactions, and conditional branches in `solune/frontend/src/components/board/__tests__/CleanUpConfirmModal.test.tsx`
- [ ] T038 [P] [US3] Add tests for AgentColumnCell component covering rendering, user interactions, and conditional branches in `solune/frontend/src/components/board/__tests__/AgentColumnCell.test.tsx`
- [ ] T039 [P] [US3] Add tests for BoardDragOverlay component covering rendering and conditional branches in `solune/frontend/src/components/board/__tests__/BoardDragOverlay.test.tsx`

### Hook Tests

- [ ] T040 [P] [US3] Add tests for useBoardDragDrop hook covering success path, error state, loading state, empty data, and API failure in `solune/frontend/src/hooks/__tests__/useBoardDragDrop.test.ts` using `renderHook` with `DndContext` and `QueryClientProvider` wrappers
- [ ] T041 [P] [US3] Add tests for useConfirmation hook covering success path, error state, loading state, empty data, and API failure in `solune/frontend/src/hooks/__tests__/useConfirmation.test.ts` using `renderHook`
- [ ] T042 [P] [US3] Add tests for useUnsavedPipelineGuard hook covering success path, error state, loading state, empty data, and API failure in `solune/frontend/src/hooks/__tests__/useUnsavedPipelineGuard.test.ts` using `renderHook` with `RouterProvider` wrapper

### Utility Library Tests

- [ ] T043 [P] [US3] Add tests for lazyWithRetry utility targeting ≥90% line coverage in `solune/frontend/src/lib/__tests__/lazyWithRetry.test.ts`
- [ ] T044 [P] [US3] Add tests for commands directory targeting ≥90% line coverage in `solune/frontend/src/lib/__tests__/commands.test.ts`
- [ ] T045 [P] [US3] Add tests for formatAgentName utility targeting ≥90% line coverage in `solune/frontend/src/lib/__tests__/formatAgentName.test.ts`
- [ ] T046 [P] [US3] Add tests for generateId utility targeting ≥90% line coverage in `solune/frontend/src/lib/__tests__/generateId.test.ts`

### Branch Coverage Enhancement

- [ ] T047 [US3] Add branch coverage tests for hooks targeting error paths, loading states, empty data, and API failure scenarios to raise overall hook branch coverage to ≥50%

### Untested File Verification

- [ ] T048 [US3] Verify the number of frontend files with 0% statement coverage is no more than 7 (reduced from ~23 baseline) via `cd solune/frontend && npm run test:coverage 2>&1 | grep "0.00"`
- [ ] T049 [US3] Run `npx vitest run --coverage --reporter=verbose` and count files with 0% statement coverage, confirming ≤ 7 remain

### Coverage Gate

- [ ] T050 [US3] Verify frontend coverage ≥ 55% statements, 50% branches, 45% functions via `cd solune/frontend && npm run test:coverage`

---

## Phase D: Mutation Verification (User Story 4 — P4)

**Purpose**: Verify mutation kill rates across all backend shards and the frontend, with kill rates exceeding defined thresholds.

- [ ] T051 [P] [US4] Execute backend mutation shard `auth-and-projects` via `cd solune/backend && python scripts/run_mutmut_shard.py --shard=auth-and-projects` and verify kill rate ≥ 60%
- [ ] T052 [P] [US4] Execute backend mutation shard `orchestration` via `cd solune/backend && python scripts/run_mutmut_shard.py --shard=orchestration` and verify kill rate ≥ 60%
- [ ] T053 [P] [US4] Execute backend mutation shard `app-and-data` via `cd solune/backend && python scripts/run_mutmut_shard.py --shard=app-and-data` and verify kill rate ≥ 60%
- [ ] T054 [P] [US4] Execute backend mutation shard `agents-and-integrations` via `cd solune/backend && python scripts/run_mutmut_shard.py --shard=agents-and-integrations` and verify kill rate ≥ 60%
- [ ] T055 [P] [US4] Execute frontend mutation testing via `cd solune/frontend && npx stryker run` and verify mutation score meets thresholds (80% high, 60% low)
- [ ] T056 [US4] Review all surviving mutants from T051–T055, write targeted assertions to kill survivor mutants or document as equivalent/non-killable with justification

---

## Phase E: Final Verification and CI Enforcement (User Story 5 — P5)

**Purpose**: Final end-to-end verification pass confirming all targets are met, CI gates enforce the new thresholds, and the development workflow remains fast.

### CI Enforcement

- [ ] T057 [US5] Update backend coverage threshold in `solune/backend/pyproject.toml` to `fail_under = 80` (ratchet from 75)
- [ ] T058 [US5] Update frontend coverage thresholds in `solune/frontend/vitest.config.ts` to `statements: 55, branches: 50, functions: 45, lines: 55` (ratchet from 50/44/41/50)

### Final Verification

- [ ] T059 [P] [US5] Run final flaky test detection for backend via `cd solune/backend && python scripts/detect_flaky.py --runs=5` and verify zero flaky tests
- [ ] T060 [P] [US5] Run final flaky test detection for frontend (5 consecutive runs) and verify zero flaky tests
- [ ] T061 [P] [US5] Verify zero AsyncMock deprecation warnings via `cd solune/backend && .venv/bin/python -m pytest tests/ -q 2>&1 | grep -qi asyncmock` returns no matches
- [ ] T062 [P] [US5] Verify pre-commit hooks complete in under 30 seconds via `cd solune && time scripts/pre-commit`

### Documentation

- [ ] T063 [US5] Document emergency hotfix override process for CI bypass scenarios, including mandatory post-merge coverage restoration requirements

### Final Reports

- [ ] T064 [US5] Run full backend test suite with coverage enforcement at 80% threshold and generate final coverage report
- [ ] T065 [US5] Run full frontend test suite with coverage thresholds at 55/50/45 and generate final coverage report
- [ ] T066 [US5] Run all mutation testing (4 backend shards + frontend Stryker) and generate final mutation reports
- [ ] T067 [US5] Mark all tasks in this spec's task tracker complete and archive final coverage and mutation reports

---

## Summary

| Phase | User Story | Tasks | Parallel |
|-------|-----------|-------|----------|
| Phase 0: Setup | Setup | T001–T003 | 3 |
| Phase A: Static Analysis | US1 | T004–T021 | 10 |
| Phase B: Backend Coverage | US2 | T022–T034 | 11 |
| Phase C: Frontend Coverage | US3 | T035–T050 | 13 |
| Phase D: Mutation Verification | US4 | T051–T056 | 5 |
| Phase E: Final Verification | US5 | T057–T067 | 5 |
| **Total** | | **T001–T067 (67 tasks)** | **47 parallelizable** |

### Story Distribution

- **US1 (Static Analysis)**: 18 tasks (T004–T021)
- **US2 (Backend Coverage)**: 13 tasks (T022–T034)
- **US3 (Frontend Coverage)**: 16 tasks (T035–T050)
- **US4 (Mutation)**: 6 tasks (T051–T056)
- **US5 (Final Verification)**: 11 tasks (T057–T067)
- **Setup**: 3 tasks (T001–T003)
