# Tasks: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Input**: Design documents from `/specs/052-fix-bugs-test-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are the PRIMARY DELIVERABLE of this feature — all test tasks are explicitly required by the specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories are sequential (US1 blocks US2/US3, US2/US3 block US4, US4 blocks US5).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `apps/solune/backend/` (Python/FastAPI), `apps/solune/frontend/` (React/TypeScript)
- Backend tests: `apps/solune/backend/tests/`
- Frontend tests: colocated `__tests__/` directories under `apps/solune/frontend/src/`

---

## Phase 1: Setup (Verification)

**Purpose**: Verify prerequisites and ensure existing toolchain is functional

- [X] T001 Verify all prerequisite tools and existing tests pass per specs/052-fix-bugs-test-coverage/quickstart.md

---

## Phase 2: Foundational (No Blocking Prerequisites)

**Purpose**: No foundational infrastructure needed — the project, tools, and test infrastructure already exist. User Story 1 (Static Analysis) serves as the blocking prerequisite for all subsequent stories.

**⚠️ CRITICAL**: User Story 1 (Phase 3) MUST complete before any coverage expansion work (Phases 4–5) can begin.

**Checkpoint**: Proceed directly to Phase 3

---

## Phase 3: User Story 1 — Complete Static Analysis Sweep (Priority: P1) 🎯 MVP

**Goal**: Resolve all lint, type-check, and security violations across the entire monorepo. Quarantine all flaky tests with documented root causes. Eliminate all deprecation warnings.

**Independent Test**: Run the full static analysis tool chain and flaky test detection script. All tools exit cleanly with zero violations, zero flaky tests remain active, and zero AsyncMock warnings are emitted.

**Quality Gates**: GA-01 through GA-07

### Frontend Static Analysis (parallel)

- [X] T002 [P] [US1] Run frontend lint sweep (`npx eslint . --fix`) and fix all remaining violations in apps/solune/frontend/src/
- [X] T003 [P] [US1] Run frontend type-check (`npx tsc --noEmit`) in strict mode and fix all errors in apps/solune/frontend/src/

### Backend Static Analysis (parallel)

- [X] T004 [P] [US1] Run backend lint (`ruff check src/ --fix`) and fix all remaining violations in apps/solune/backend/src/
- [X] T005 [P] [US1] Run backend type-check (`pyright`) and fix all errors in apps/solune/backend/src/
- [X] T006 [P] [US1] Run backend security scan (`bandit -r src/ -s B104,B608`) and fix all issues in apps/solune/backend/src/

### Flaky Test Detection (depends on static analysis)

- [X] T007 [US1] Run backend flaky test detection (`python scripts/detect_flaky.py`, 5 runs) in apps/solune/backend/
- [X] T008 [US1] Run frontend flaky test detection (`vitest run` ×5, diff results) in apps/solune/frontend/

### Quarantine & Cleanup (depends on flaky detection)

- [X] T009 [US1] Quarantine confirmed flaky tests with skip markers and file GitHub issues in apps/solune/backend/tests/ and apps/solune/frontend/src/
- [X] T010 [US1] Resolve all test warnings including AsyncMock deprecation in apps/solune/backend/tests/

**Checkpoint**: All static analysis tools exit with zero violations. Zero flaky tests in active suite. Zero AsyncMock warnings.

**Verification**:
```bash
cd apps/solune/frontend && npx eslint . && npx tsc --noEmit
cd apps/solune/backend && ruff check src/ && pyright && bandit -r src/ -s B104,B608
cd apps/solune/backend && python scripts/detect_flaky.py
cd apps/solune/backend && pytest 2>&1 | grep -c "AsyncMock"  # Expected: 0
```

---

## Phase 4: User Story 2 — Raise Backend Line Coverage to 80% (Priority: P2)

**Goal**: Increase backend line coverage from 75% to 80% by adding integration tests for high-risk API routes, unit tests for orphan modules, edge-case tests for high-risk services, and property-based tests for complex state logic.

**Independent Test**: Run `pytest --cov=src --cov-fail-under=80` — the coverage gate must pass.

**Quality Gate**: GB-01

### Integration Tests (parallel — follow pattern from tests/integration/test_health_endpoint.py, R1)

- [X] T011 [P] [US2] Add integration tests for auth callback route in apps/solune/backend/tests/integration/test_auth_callback.py
- [X] T012 [P] [US2] Add integration tests for webhook dispatch route in apps/solune/backend/tests/integration/test_webhook_dispatch.py
- [X] T013 [P] [US2] Add integration tests for pipeline launch route in apps/solune/backend/tests/integration/test_pipeline_launch.py
- [X] T014 [P] [US2] Add integration tests for chat confirm route in apps/solune/backend/tests/integration/test_chat_confirm.py

### Unit Tests for Orphan Modules (parallel)
- [X] T015 [P] [US2] Add unit tests for dependency injection module in apps/solune/backend/tests/unit/test_dependencies.py
- [X] T016 [P] [US2] Add unit tests for request ID middleware in apps/solune/backend/tests/unit/test_request_id_middleware.py

### Edge-Case Tests for High-Risk Services (parallel)

- [X] T017 [P] [US2] Add edge-case tests for recovery logic (crash mid-recovery, empty state, concurrent attempts) in apps/solune/backend/tests/unit/test_recovery_edge_cases.py
- [X] T018 [P] [US2] Add edge-case tests for state validation boundaries (boundary transitions, invalid state combinations) in apps/solune/backend/tests/unit/test_state_validation_edge_cases.py
- [X] T019 [P] [US2] Add edge-case tests for signal bridge error propagation (timeout, message loss) in apps/solune/backend/tests/unit/test_signal_bridge_edge_cases.py
- [X] T020 [P] [US2] Add edge-case tests for guard service and signal delivery (permission boundaries, retry/failure paths) in apps/solune/backend/tests/unit/test_guard_signal_edge_cases.py

### Property-Based Tests (parallel — follow pattern from R4)

- [X] T021 [P] [US2] Extend property-based tests for pipeline state machine with ≥100 examples in apps/solune/backend/tests/property/test_pipeline_state_machine.py
- [X] T022 [P] [US2] Add property-based tests for markdown parser roundtrips in apps/solune/backend/tests/property/test_markdown_parser_roundtrips.py

### Verification Gates (sequential)

- [X] T023 [US2] Verify mutation shard config includes api-and-middleware targets in apps/solune/backend/scripts/run_mutmut_shard.py
- [ ] T024 [US2] Verify backend line coverage ≥ 80% via `pytest --cov=src --cov-report=term-missing --cov-fail-under=80` in apps/solune/backend/

**Checkpoint**: Backend line coverage ≥ 80%. All new tests pass. Mutation shard config verified.

**Verification**:
```bash
cd apps/solune/backend && pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

---

## Phase 5: User Story 3 — Raise Frontend Coverage to 55/50/45 (Priority: P3)

**Goal**: Increase frontend statement, branch, and function coverage to 55%, 50%, and 45% respectively by adding component tests, hook tests, utility tests, and service layer tests.

**Independent Test**: Run `vitest run --coverage` — all threshold gates must pass.

**Quality Gate**: GC-01

### Board Component Tests (parallel — follow pattern from BoardColumn.test.tsx, R2)

- [ ] T025 [P] [US3] Add component tests for ProjectBoard with DndContext wrapper in apps/solune/frontend/src/components/board/__tests__/ProjectBoard.test.tsx
- [ ] T026 [P] [US3] Add component tests for BoardToolbar in apps/solune/frontend/src/components/board/__tests__/BoardToolbar.test.tsx
- [ ] T027 [P] [US3] Add component tests for CleanUpConfirmModal in apps/solune/frontend/src/components/board/__tests__/CleanUpConfirmModal.test.tsx
- [ ] T028 [P] [US3] Add component tests for AgentColumnCell in apps/solune/frontend/src/components/board/__tests__/AgentColumnCell.test.tsx
- [ ] T029 [P] [US3] Add component tests for BoardDragOverlay in apps/solune/frontend/src/components/board/__tests__/BoardDragOverlay.test.tsx

### Hook Tests with 5 Branch Paths (parallel — follow pattern from useBoardControls.test.tsx, R3)

- [ ] T030 [P] [US3] Add hook tests for useBoardDragDrop (success, error, loading, empty, edge-case) in apps/solune/frontend/src/hooks/__tests__/useBoardDragDrop.test.ts
- [ ] T031 [P] [US3] Add hook tests for useConfirmation (success, error, loading, empty, edge-case) in apps/solune/frontend/src/hooks/__tests__/useConfirmation.test.ts
- [ ] T032 [P] [US3] Add hook tests for useUnsavedPipelineGuard (success, error, loading, empty, edge-case) in apps/solune/frontend/src/hooks/__tests__/useUnsavedPipelineGuard.test.ts

### Utility Tests (parallel)

- [ ] T033 [P] [US3] Add tests for lazyWithRetry utility (retry with sessionStorage flag) in apps/solune/frontend/src/lib/__tests__/lazyWithRetry.test.ts
- [ ] T034 [P] [US3] Add tests for commands directory in apps/solune/frontend/src/lib/__tests__/commands.test.ts
- [ ] T035 [P] [US3] Add tests for formatAgentName utility in apps/solune/frontend/src/lib/__tests__/formatAgentName.test.ts
- [ ] T036 [P] [US3] Add tests for generateId utility in apps/solune/frontend/src/lib/__tests__/generateId.test.ts

### Service Layer Tests (parallel)

- [ ] T037 [P] [US3] Add service layer tests for error handling, retry logic, and response parsing in apps/solune/frontend/src/services/__tests__/api-errors.test.ts

### Branch Coverage Expansion (depends on hook tests T030–T032)

- [ ] T038 [US3] Add branch coverage tests for hooks (error/loading/empty states) in hook test files under apps/solune/frontend/src/hooks/__tests__/

### Verification Gate

- [ ] T039 [US3] Verify frontend coverage ≥ 55/50/45/55 via `npx vitest run --coverage` in apps/solune/frontend/

**Checkpoint**: Frontend statement ≥ 55%, branch ≥ 50%, function ≥ 45%, line ≥ 55%. All new tests pass.

**Verification**:
```bash
cd apps/solune/frontend && npx vitest run --coverage
```

---

## Phase 6: User Story 4 — Verify Mutation Kill Rates (Priority: P4)

**Goal**: Execute mutation testing across all backend shards and frontend suite. Triage surviving mutants and write targeted assertions for killable survivors. Achieve >60% kill rate per shard.

**Independent Test**: Run all mutation shards and verify >60% kill rate. All killable survivors have targeted assertions.

**Quality Gates**: GD-01, GD-02

### Backend Mutation Shards (parallel — see R6)

- [ ] T040 [P] [US4] Execute backend mutation shard auth-and-projects via `python scripts/run_mutmut_shard.py --shard auth-and-projects` in apps/solune/backend/
- [ ] T041 [P] [US4] Execute backend mutation shard orchestration via `python scripts/run_mutmut_shard.py --shard orchestration` in apps/solune/backend/
- [ ] T042 [P] [US4] Execute backend mutation shard app-and-data via `python scripts/run_mutmut_shard.py --shard app-and-data` in apps/solune/backend/
- [ ] T043 [P] [US4] Execute backend mutation shard agents-and-integrations via `python scripts/run_mutmut_shard.py --shard agents-and-integrations` in apps/solune/backend/
- [ ] T044 [P] [US4] Execute backend mutation shard api-and-middleware via `python scripts/run_mutmut_shard.py --shard api-and-middleware` in apps/solune/backend/

### Frontend Mutation Suite (parallel with backend shards)

- [ ] T045 [P] [US4] Execute frontend mutation testing via `npx stryker run` in apps/solune/frontend/

### Triage & Resolution (sequential)

- [ ] T046 [US4] Review and classify all surviving mutants as killable/equivalent/non-killable with documented justification in apps/solune/docs/mutation-triage.md
- [ ] T047 [US4] Write targeted assertions to kill surviving mutants in relevant test files across apps/solune/

**Checkpoint**: Kill rate >60% per shard. All killable survivors addressed. Triage documented.

**Verification**:
```bash
cd apps/solune/backend && mutmut results
cd apps/solune/frontend && npx stryker run
```

---

## Phase 7: User Story 5 — Enforce Thresholds and Harden CI (Priority: P5)

**Goal**: Ratchet coverage thresholds upward in configuration files. Verify pre-commit hooks complete quickly. Document emergency override process. Generate final reports.

**Independent Test**: Push a commit that lowers coverage — CI must reject it. Run pre-commit hooks in <30 seconds.

**Quality Gates**: GE-01 through GE-04

### Threshold Ratcheting & Verification (parallel — see R7)

- [ ] T048 [P] [US5] Ratchet backend coverage threshold to `fail_under = 80` in apps/solune/backend/pyproject.toml
- [ ] T049 [P] [US5] Ratchet frontend coverage thresholds to 55/50/45/55 in apps/solune/frontend/vitest.config.ts
- [ ] T050 [P] [US5] Run final flaky test detection (5 runs each suite) in apps/solune/backend/ and apps/solune/frontend/
- [ ] T051 [P] [US5] Verify zero AsyncMock deprecation warnings via `pytest 2>&1 | grep -c "AsyncMock"` in apps/solune/backend/
- [ ] T052 [P] [US5] Verify pre-commit hooks complete in <30 seconds via `time scripts/pre-commit` in apps/solune/

### Documentation & Reporting (sequential — see R8)

- [ ] T053 [US5] Document emergency hotfix override process with `SKIP_COVERAGE=1` and audit trail in apps/solune/docs/emergency-override.md
- [ ] T054 [US5] Generate final coverage HTML reports and mutation reports in apps/solune/backend/ and apps/solune/frontend/

**Checkpoint**: Thresholds enforced in CI. Pre-commit <30s. Override documented. Reports generated.

**Verification**:
```bash
grep "fail_under" apps/solune/backend/pyproject.toml        # Expected: fail_under = 80
grep -A4 "thresholds" apps/solune/frontend/vitest.config.ts  # Expected: 55/50/45/55
cd apps/solune && time scripts/pre-commit                    # Expected: < 30 seconds
```

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation updates

- [ ] T055 [P] Run full verification sequence from specs/052-fix-bugs-test-coverage/contracts/verification-commands.md
- [ ] T056 Update project documentation with final coverage metrics in apps/solune/docs/testing.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)     → No dependencies
Phase 2 (Found.)    → Skipped (no foundational tasks needed)
Phase 3 (US1: P1)   → Depends on Phase 1
Phase 4 (US2: P2)   → Depends on Phase 3 (static analysis must be clean)
Phase 5 (US3: P3)   → Depends on Phase 3 (static analysis must be clean)
Phase 6 (US4: P4)   → Depends on Phase 4 AND Phase 5 (coverage expansion complete)
Phase 7 (US5: P5)   → Depends on Phase 6 (mutation verification complete)
Phase 8 (Polish)    → Depends on Phase 7 (all stories complete)
```

### User Story Dependencies

- **US1 (P1)**: Can start immediately after Setup — **BLOCKS all other stories**
- **US2 (P2)**: Can start after US1 — Independent of US3
- **US3 (P3)**: Can start after US1 — Independent of US2 — **US2 and US3 can run in parallel**
- **US4 (P4)**: Depends on BOTH US2 and US3 — Cannot start until coverage expansion is complete
- **US5 (P5)**: Depends on US4 — Final enforcement step

### Within Each User Story

- Static analysis fixes before test authoring
- Integration/component tests in parallel (different files)
- Property-based tests in parallel with unit/edge-case tests
- Verification gates run last (sequential)
- Story complete before progressing to dependent stories

### Parallel Opportunities

**Within US1** (Phase 3):
- T002+T003 (frontend lint+types) run simultaneously
- T004+T005+T006 (backend lint+types+security) run simultaneously
- T007 and T008 (flaky detection) can run in parallel after their respective analysis steps

**Within US2** (Phase 4):
- T011–T022 (all test authoring) can run in parallel — all target different test files

**Within US3** (Phase 5):
- T025–T037 (all test authoring) can run in parallel — all target different test files

**Within US4** (Phase 6):
- T040–T045 (all mutation shards + Stryker) can run in parallel

**Within US5** (Phase 7):
- T048–T052 (threshold updates + verifications) can run in parallel

**Cross-Story Parallelism**:
- US2 (Phase 4) and US3 (Phase 5) can run **simultaneously** after US1 completes

---

## Parallel Example: User Story 2

```bash
# Launch all integration tests in parallel (different files):
T011: "Add integration tests for auth callback in tests/integration/test_auth_callback.py"
T012: "Add integration tests for webhook dispatch in tests/integration/test_webhook_dispatch.py"
T013: "Add integration tests for pipeline launch in tests/integration/test_pipeline_launch.py"
T014: "Add integration tests for chat confirm in tests/integration/test_chat_confirm.py"

# Launch all unit/edge-case tests in parallel (different files):
T015: "Add unit tests for dependency injection in tests/unit/test_dependencies.py"
T016: "Add unit tests for request ID middleware in tests/unit/test_request_id_middleware.py"
T017: "Add edge-case tests for recovery in tests/unit/test_recovery_edge_cases.py"
T018: "Add edge-case tests for state validation in tests/unit/test_state_validation_edge_cases.py"
T019: "Add edge-case tests for signal bridge in tests/unit/test_signal_bridge_edge_cases.py"
T020: "Add edge-case tests for guard service in tests/unit/test_guard_signal_edge_cases.py"

# Launch all property-based tests in parallel (different files):
T021: "Extend property-based tests for pipeline state machine in tests/property/test_pipeline_state_machine.py"
T022: "Add property-based tests for markdown parser in tests/property/test_markdown_parser_roundtrips.py"

# Then verify (sequential):
T023: "Verify mutation shard config"
T024: "Verify backend coverage ≥ 80%"
```

---

## Parallel Example: User Story 3

```bash
# Launch all component tests in parallel (different files):
T025: "ProjectBoard.test.tsx"
T026: "BoardToolbar.test.tsx"
T027: "CleanUpConfirmModal.test.tsx"
T028: "AgentColumnCell.test.tsx"
T029: "BoardDragOverlay.test.tsx"

# Launch all hook tests in parallel (different files):
T030: "useBoardDragDrop.test.ts"
T031: "useConfirmation.test.ts"
T032: "useUnsavedPipelineGuard.test.ts"

# Launch all utility + service tests in parallel (different files):
T033: "lazyWithRetry.test.ts"
T034: "commands.test.ts"
T035: "formatAgentName.test.ts"
T036: "generateId.test.ts"
T037: "api-errors.test.ts"

# Then expand + verify (sequential):
T038: "Add branch coverage for hooks"
T039: "Verify frontend coverage ≥ 55/50/45/55"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 3: User Story 1 — Static Analysis Sweep (T002–T010)
3. **STOP and VALIDATE**: All linters, type-checkers, and security scanner exit clean. Zero flaky tests. Zero warnings.
4. This is the MVP — a clean, warning-free codebase ready for coverage expansion.

### Incremental Delivery

1. US1 → Clean baseline (MVP)
2. US2 + US3 (in parallel) → Coverage gates met
3. US4 → Mutation quality verified
4. US5 → CI enforcement locked in
5. Each story adds verifiable quality improvements without breaking previous stories

### Parallel Team Strategy

With two developers after US1 completes:
- **Developer A**: User Story 2 (backend coverage)
- **Developer B**: User Story 3 (frontend coverage)
- Both complete → merge → proceed to US4 together

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story from spec.md for traceability
- Tests are the PRIMARY deliverable — each task creates or verifies test coverage
- Characterization tests only — document current behavior, no DRY refactoring
- Thresholds ratchet upward only — never decrease
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate the story independently
- Reference quickstart.md for code patterns (integration tests, hook tests, component tests, property-based tests)
- Reference research.md for decisions: R1 (httpx pattern), R2 (DndContext wrapping), R3 (renderHook branches), R4 (Hypothesis RuleBasedStateMachine), R5 (5-run flaky detection), R6 (api-and-middleware shard exists), R7 (ratchet last), R8 (SKIP_COVERAGE=1 override)
