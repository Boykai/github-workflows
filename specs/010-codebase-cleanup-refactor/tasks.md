# Tasks: Codebase Cleanup — Remove Dead Code, Backwards Compatibility & Stale Tests

**Input**: Design documents from `/specs/010-codebase-cleanup-refactor/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: No new test tasks — the spec requires existing tests to continue passing (FR-009) but does not mandate new tests. Test Optionality (Constitution IV) applies.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Delivery order: US1 → US2 → US3 → US4 → US5 (per quickstart.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/`
- **Frontend tests**: `frontend/src/` (Vitest co-located)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline state — verify all tests pass and tooling works before any code changes

- [ ] T001 Run full backend test suite (`cd backend && pytest -v`) and record baseline pass count
- [ ] T002 [P] Run full frontend test suite (`cd frontend && npm test`) and record baseline pass count
- [ ] T003 [P] Run backend linting baseline (`cd backend && ruff check src/ tests/`) and record zero-violation state
- [ ] T004 [P] Run frontend linting and type-check baseline (`cd frontend && npm run lint && npm run type-check`) and record zero-violation state

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking foundational infrastructure needed — this is a pure refactor on an existing codebase. All tools, frameworks, and project structure are already in place.

**⚠️ NOTE**: Phase 1 baseline verification MUST pass before proceeding. If existing tests fail, those failures must be documented as pre-existing before cleanup begins.

**Checkpoint**: Baseline established — user story implementation can now begin in priority order

---

## Phase 3: User Story 1 — Remove Backwards Compatibility Shims and Legacy Code (Priority: P1) 🎯 MVP

**Goal**: Remove all backwards compatibility layers, legacy shims, and deprecated code paths so the codebase only contains code supporting current functionality.

**Independent Test**: Search codebase for known backwards compatibility patterns (plaintext fallback, `custom_agent` field, legacy shims) and confirm zero remain. All existing tests pass after removal.

### Implementation for User Story 1

- [ ] T005 [US1] Evaluate plaintext token fallback in `backend/src/services/encryption.py` — audit database for `gho_` prefix tokens; if zero exist, remove the plaintext fallback branch from the `decrypt()` method (per research.md R1)
- [ ] T006 [US1] Remove `custom_agent` field deprecation references across backend if fully migrated to `agent_mappings` — search `backend/src/` for `custom_agent` and remove stale references (per research.md R1)
- [ ] T007 [P] [US1] Update "legacy" comments in `backend/src/services/copilot_polling/pipeline.py` to "fallback" terminology — these paths handle active non-pipeline issue cases and are not backwards compatibility shims (per research.md R1, data-model.md)
- [ ] T008 [US1] Verify no remaining backwards compatibility patterns by running: `grep -rn "legacy\|backward\|compat\|deprecated" backend/src/ --include="*.py" | grep -v "test_\|\.pyc\|__pycache__"` and reviewing each match (per quickstart.md Story 1 verification)
- [ ] T009 [US1] Run full backend test suite (`cd backend && pytest -v`) to confirm zero regressions after backwards compatibility removal
- [ ] T010 [P] [US1] Run backend linting (`cd backend && ruff check src/ tests/`) to confirm zero new violations

**Checkpoint**: All backwards compatibility shims removed. Codebase contains only current functionality code. All tests pass.

---

## Phase 4: User Story 2 — Eliminate Dead Code Across the Entire Codebase (Priority: P1)

**Goal**: Remove all dead code — unused types, silent exception suppression, unused imports, unused variables/functions, and unreachable branches — so every line serves a purpose.

**Independent Test**: Run static analysis (Ruff F401 for backend, ESLint for frontend, grep for unused types) with zero violations. Application builds, starts, and all tests pass after removal.

### Implementation for User Story 2

#### Backend — Silent Exception Handlers (replace `pass` with `logger.debug()`)

- [ ] T011 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/api/settings.py` (per data-model.md, line ~148)
- [ ] T012 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/api/workflow.py` (ImportError handler, per data-model.md, line ~82)
- [ ] T013 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/services/copilot_polling/agent_output.py` (per data-model.md, line ~312)
- [ ] T014 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/services/copilot_polling/pipeline.py` (per data-model.md, line ~280)
- [ ] T015 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/services/signal_chat.py` (per data-model.md, line ~240)
- [ ] T016 [P] [US2] Replace silent exception handlers with `logger.debug()` in `backend/src/services/ai_agent.py` (json.JSONDecodeError handlers at lines ~550, ~585)
- [ ] T017 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/services/model_fetcher.py` (ValueError/TypeError handler at line ~330)
- [ ] T018 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/services/workflow_orchestrator/config.py` (per data-model.md, line ~232)
- [ ] T019 [P] [US2] Replace silent exception handler with `logger.debug()` in `backend/src/api/chat.py` (RuntimeError handler at line ~286)

#### Frontend — Unused Type Exports

- [ ] T020 [P] [US2] Remove unused `IssueLabel` type export from `frontend/src/types/index.ts` (verify zero imports with `grep -r "IssueLabel" frontend/src/`)
- [ ] T021 [P] [US2] Remove unused `PipelineStateInfo` type export from `frontend/src/types/index.ts` (verify zero imports with `grep -r "PipelineStateInfo" frontend/src/`)
- [ ] T022 [P] [US2] Remove unused `AgentNotification` type export from `frontend/src/types/index.ts` (verify zero imports with `grep -r "AgentNotification" frontend/src/`)
- [ ] T023 [P] [US2] Remove unused `SignalConnectionStatus` type export from `frontend/src/types/index.ts` (verify zero imports with `grep -r "SignalConnectionStatus" frontend/src/`)
- [ ] T024 [P] [US2] Remove unused `SignalNotificationMode` type export from `frontend/src/types/index.ts` (verify zero imports with `grep -r "SignalNotificationMode" frontend/src/`)
- [ ] T025 [P] [US2] Remove unused `SignalLinkStatus` type export from `frontend/src/types/index.ts` (verify zero imports with `grep -r "SignalLinkStatus" frontend/src/`)

#### Cross-Stack — Unused Imports, Variables, and Unreachable Branches

- [ ] T026 [US2] Run `ruff check src/ --select F401` in `backend/` and remove all unused imports flagged across `backend/src/`
- [ ] T027 [P] [US2] Run `ruff check src/ --select F841` in `backend/` and remove all unused variables flagged across `backend/src/`
- [ ] T028 [P] [US2] Audit `backend/src/constants.py` for stale constants no longer referenced by any module — remove unused entries
- [ ] T029 [US2] Run frontend build (`cd frontend && npm run build`) and resolve any dead code warnings; run `npm run type-check` to confirm zero type errors after type export removal

#### Verification

- [ ] T030 [US2] Verify silent exception handlers replaced: `grep -rn "except.*:$" backend/src/ --include="*.py" -A1 | grep "pass$"` should return zero matches (per quickstart.md Story 2 verification)
- [ ] T031 [US2] Run full backend test suite (`cd backend && pytest -v`) to confirm zero regressions
- [ ] T032 [P] [US2] Run full frontend test suite (`cd frontend && npm test`) to confirm zero regressions

**Checkpoint**: All dead code eliminated. Every line of code serves a purpose. Static analysis passes clean. All tests pass.

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic Following DRY Principles (Priority: P2)

**Goal**: Consolidate duplicated code patterns into shared, reusable abstractions so bug fixes and behavior changes only happen in one place.

**Independent Test**: Identify known duplicated patterns and confirm each exists in exactly one location. All callers reference the shared implementation. All tests pass.

### Implementation for User Story 3

#### Backend — Cache Pattern Consolidation

- [ ] T033 [US3] Create `cached_response()` async utility function in `backend/src/services/cache.py` following the pattern in research.md R4: accept `cache_key`, `refresh`, `fetch_fn`, `logger`, and `description` parameters
- [ ] T034 [US3] Refactor cache patterns in `backend/src/api/board.py` to use the new `cached_response()` utility from `backend/src/services/cache.py`
- [ ] T035 [P] [US3] Refactor cache patterns in `backend/src/api/projects.py` to use the new `cached_response()` utility from `backend/src/services/cache.py`
- [ ] T036 [P] [US3] Refactor cache patterns in `backend/src/api/chat.py` to use the new `cached_response()` utility from `backend/src/services/cache.py`

#### Frontend — Hook Deduplication

- [ ] T037 [US3] Extract `hasAgentOrderChanged()` helper function in `frontend/src/hooks/useAgentConfig.ts` to consolidate the duplicated agent order comparison logic (lines ~108-120 vs ~122-133, per research.md R5)
- [ ] T038 [US3] Refactor dirty-checking logic in `frontend/src/hooks/useAgentConfig.ts` to use the extracted `hasAgentOrderChanged()` helper

#### Verification

- [ ] T039 [US3] Verify cache pattern consolidation: `grep -rn "cache.get\|cache.set" backend/src/api/ --include="*.py"` should show reduced direct cache calls (per quickstart.md Story 3 verification)
- [ ] T040 [US3] Run full backend test suite (`cd backend && pytest -v`) to confirm zero regressions after cache consolidation
- [ ] T041 [P] [US3] Run full frontend test suite (`cd frontend && npm test`) to confirm zero regressions after hook deduplication

**Checkpoint**: All identified duplication consolidated. Each pattern exists in exactly one shared location. All tests pass.

---

## Phase 6: User Story 4 — Remove Stale, Redundant, and Obsolete Tests (Priority: P2)

**Goal**: Remove all tests that no longer reflect current behavior, test non-existent functionality, or duplicate coverage, so the test suite is trustworthy and efficient.

**Independent Test**: Every remaining test validates real, current application behavior. Full test suite passes consistently with no failures, no unexpected skips, and no flaky behavior.

### Implementation for User Story 4

- [ ] T042 [US4] If plaintext fallback was removed in T005, remove `test_legacy_plaintext_fallback_on_decrypt` test from `backend/tests/unit/test_token_encryption.py` with documented rationale (per research.md R6)
- [ ] T043 [US4] Audit all backend tests (`backend/tests/`) for tests referencing removed code, deprecated behavior, or `custom_agent` field — remove stale tests with documented rationale per research.md R6 criteria
- [ ] T044 [P] [US4] Audit all frontend tests for tests referencing removed types (`IssueLabel`, `PipelineStateInfo`, `AgentNotification`, `SignalConnectionStatus`, `SignalNotificationMode`, `SignalLinkStatus`) or removed code — remove stale tests with documented rationale
- [ ] T045 [US4] Scan for perpetually skipped or disabled tests: `grep -rn "skip\|xfail\|@pytest.mark.skip\|xit\|xdescribe\|test.skip\|test.todo" backend/tests/ frontend/src/` — review each and either fix/re-enable or remove with documented rationale
- [ ] T046 [US4] Run full backend test suite (`cd backend && pytest -v`) to confirm all remaining tests pass cleanly
- [ ] T047 [P] [US4] Run full frontend test suite (`cd frontend && npm test`) to confirm all remaining tests pass cleanly

**Checkpoint**: Test suite is clean — every test validates current behavior. Zero stale tests remain. All tests pass.

---

## Phase 7: User Story 5 — Apply Current Best Practices and Enforce Code Quality Standards (Priority: P3)

**Goal**: Ensure the codebase follows current language and framework best practices — idiomatic, consistent, and easier to understand and extend.

**Independent Test**: Linting and formatting checks pass with zero violations. No deprecated patterns remain. All comments accurately reflect the current codebase.

### Implementation for User Story 5

- [ ] T048 [P] [US5] Audit and update stale inline comments in `backend/src/` that reference removed code, old patterns, or outdated behavior — update or remove each (FR-012)
- [ ] T049 [P] [US5] Audit and update stale inline comments in `frontend/src/` that reference removed code, old patterns, or outdated behavior — update or remove each (FR-012)
- [ ] T050 [US5] Run backend linting and formatting checks: `cd backend && ruff check src/ tests/ && ruff format --check src/ tests/` — fix any violations found (FR-011)
- [ ] T051 [P] [US5] Run frontend linting and type-check: `cd frontend && npm run lint && npm run type-check` — fix any violations found (FR-011)
- [ ] T052 [US5] Run full backend test suite (`cd backend && pytest -v`) to confirm zero regressions after best practice changes
- [ ] T053 [P] [US5] Run full frontend test suite (`cd frontend && npm test`) to confirm zero regressions after best practice changes

**Checkpoint**: Codebase follows current best practices. All linting, formatting, and type checks pass clean. All comments are accurate.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories and documentation cleanup

- [ ] T054 [P] Measure LOC reduction: compare `wc -l` across `backend/src/` and `frontend/src/` before and after cleanup to confirm measurable reduction (SC-008)
- [ ] T055 Run quickstart.md full verification checklist (all commands from quickstart.md Verification Commands section) to confirm end-to-end regression-free state
- [ ] T056 [P] Update `specs/010-codebase-cleanup-refactor/` documentation if any implementation decisions deviated from the plan
- [ ] T057 Final full test run: `cd backend && pytest -v` and `cd frontend && npm test` — all tests must pass with zero failures (SC-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup baseline passing — DOCUMENTS pre-existing issues
- **US1 (Phase 3)**: Depends on baseline verification — removes backwards compatibility code first to simplify subsequent stories
- **US2 (Phase 4)**: Depends on US1 completion — dead code is cleaner to identify after backwards compatibility removal
- **US3 (Phase 5)**: Depends on US2 completion — duplication patterns are more visible after dead code is removed
- **US4 (Phase 6)**: Depends on US1 and US2 — stale tests correspond to removed code from those stories
- **US5 (Phase 7)**: Depends on US1–US4 — best practice polish happens on the final cleaned codebase
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 baseline — No dependencies on other stories
- **User Story 2 (P1)**: Best done after US1 — backwards compat removal may expose additional dead code
- **User Story 3 (P2)**: Best done after US2 — deduplication is clearest on the leanest codebase
- **User Story 4 (P2)**: Depends on US1 and US2 — stale tests track removed code (e.g., `test_legacy_plaintext_fallback_on_decrypt`)
- **User Story 5 (P3)**: Best done last — polishing code that will be further modified wastes effort

### Within Each User Story

- Backend changes before frontend changes (backend APIs must be stable)
- Code removal/modification before verification commands
- All verification passes before moving to next story

### Parallel Opportunities

- **Phase 1**: T001, T002, T003, T004 — all baseline checks are independent
- **Phase 3 (US1)**: T007 (comment updates) can run parallel to T005/T006 (code removal)
- **Phase 4 (US2)**: All T011–T019 (silent exception handlers) can run in parallel; all T020–T025 (type exports) can run in parallel
- **Phase 5 (US3)**: T035 and T036 can run parallel after T033/T034 establish the pattern
- **Phase 6 (US4)**: T043 and T044 (backend/frontend audits) can run in parallel
- **Phase 7 (US5)**: T048/T049 (comment audits) can run parallel; T050/T051 (lint checks) can run parallel

---

## Parallel Example: User Story 2

```bash
# Launch all silent exception handler replacements together (different files):
Task T011: "Replace silent exception handler in backend/src/api/settings.py"
Task T012: "Replace silent exception handler in backend/src/api/workflow.py"
Task T013: "Replace silent exception handler in backend/src/services/copilot_polling/agent_output.py"
Task T014: "Replace silent exception handler in backend/src/services/copilot_polling/pipeline.py"
Task T015: "Replace silent exception handler in backend/src/services/signal_chat.py"
Task T016: "Replace silent exception handlers in backend/src/services/ai_agent.py"
Task T017: "Replace silent exception handler in backend/src/services/model_fetcher.py"
Task T018: "Replace silent exception handler in backend/src/services/workflow_orchestrator/config.py"
Task T019: "Replace silent exception handler in backend/src/api/chat.py"

# Launch all unused type export removals together (same file but independent edits):
Task T020: "Remove IssueLabel from frontend/src/types/index.ts"
Task T021: "Remove PipelineStateInfo from frontend/src/types/index.ts"
Task T022: "Remove AgentNotification from frontend/src/types/index.ts"
Task T023: "Remove SignalConnectionStatus from frontend/src/types/index.ts"
Task T024: "Remove SignalNotificationMode from frontend/src/types/index.ts"
Task T025: "Remove SignalLinkStatus from frontend/src/types/index.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (establish baseline)
2. Complete Phase 3: User Story 1 — Remove backwards compatibility code
3. **STOP and VALIDATE**: All tests pass, no backwards compat patterns remain
4. This is the minimum viable cleanup — removes the most dangerous technical debt

### Incremental Delivery

1. Phase 1: Setup → Baseline established
2. US1 → Backwards compat removed → Tests pass → Commit (MVP!)
3. US2 → Dead code eliminated → Tests pass → Commit
4. US3 → Duplication consolidated → Tests pass → Commit
5. US4 → Stale tests removed → Tests pass → Commit
6. US5 → Best practices applied → Tests pass → Commit
7. Phase 8: Polish → Final validation → Commit
8. Each story adds cleanliness without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team establishes Phase 1 baseline together
2. After baseline established:
   - Developer A: User Story 1 (backwards compat) then User Story 2 (dead code) — sequential dependency
   - Developer B: User Story 3 (DRY) can start after US2 completes
   - Developer C: User Story 4 (stale tests) can start after US1+US2 complete
3. User Story 5 (best practices) is done last by any developer on the final codebase

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable: all tests must pass at each merge point (SC-010)
- No new test frameworks introduced (Constitution IV: Test Optionality)
- Research.md R7 explicitly decided NOT to consolidate API error handling — do not create error handling abstractions
- Pipeline.py "legacy" paths are retained as active fallback logic — only comments are updated (R1)
- Silent exception handlers preserve suppression behavior but add observability via logging (R2)
- Frontend hook factory was rejected (R5) — only extract `hasAgentOrderChanged()` helper, not a generic `useApiResource()`
