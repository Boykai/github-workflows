# Tasks: Code Quality & Technical Debt — Cache Wrapper Extraction, Error Handling Consolidation & Dead Code Sweep

**Input**: Design documents from `/specs/001-code-quality-tech-debt/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅, contracts/ ✅

**Tests**: Tests are included only where the specification explicitly mandates them — FR-005 (regression test for `branch_preserved` path) and FR-004 (unit test for `error_cls` type relaxation). No blanket TDD approach.

**Organization**: Tasks are grouped by user story and ordered by the plan's execution phases (A → B → C → D) to respect technical dependencies. Priority labels are included in each phase header.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions (relative to repo root)

## Path Conventions

- **Project root**: `solune/backend/`
- **Source**: `solune/backend/src/`
- **Tests**: `solune/backend/tests/`

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Establish green baseline before any refactoring

- [ ] T001 Verify existing test suite passes with `cd solune/backend && python -m pytest tests/ -x`
- [ ] T002 Verify ruff check passes with `cd solune/backend && ruff check src/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure required — this is a pure refactoring of existing code

**⚠️ NOTE**: All required infrastructure (`cached_fetch()` in cache.py, `handle_service_error()` in logging_utils.py, `InMemoryCache`, `AppException` hierarchy) already exists. No foundational tasks are needed before user story work begins.

**Checkpoint**: Baseline green — user story implementation can begin. Phases 3 and 4 can proceed in parallel (Plan Phase A).

---

## Phase 3: User Story 2 — Cycle Cache Pattern Consolidation (Priority: P1) 🎯 Quick Win

**Goal**: Add `_cycle_cached()` instance method to `GitHubProjectsService` and refactor all 7 call sites to eliminate the repeated cache-get → hit-count-check → fetch → cache-set boilerplate (~5 LOC net reduction).

**Independent Test**: Call any cycle-cached method (e.g., fetching linked PRs), verify cache-miss triggers upstream fetch, cache-hit returns stored data and increments hit count, and all existing tests pass unchanged.

**Plan Phase**: A (parallel — can run alongside Phase 4 and Phase 5)

### Implementation for User Story 2

- [ ] T003 [US2] Add `_cycle_cached(self, cache_key: str, fetch_fn: Callable[[], Awaitable[T]]) -> T` instance method to `GitHubProjectsService` in `solune/backend/src/services/github_projects/service.py` — implement cache check, hit-count increment on hit, fetch-and-store on miss
- [ ] T004 [P] [US2] Refactor 3 cycle cache call sites in `solune/backend/src/services/github_projects/pull_requests.py` (~lines 295, 375, 450) to use `self._cycle_cached(cache_key, fetch_fn)`
- [ ] T005 [P] [US2] Refactor 1 cycle cache call site in `solune/backend/src/services/github_projects/projects.py` (~line 354) to use `self._cycle_cached(cache_key, fetch_fn)`
- [ ] T006 [P] [US2] Refactor 2 cycle cache call sites in `solune/backend/src/services/github_projects/copilot.py` (~lines 230, 280) to use `self._cycle_cached(cache_key, fetch_fn)`
- [ ] T007 [P] [US2] Refactor 1 cycle cache call site in `solune/backend/src/services/github_projects/issues.py` (~line 437) to use `self._cycle_cached(cache_key, fetch_fn)`
- [ ] T008 [US2] Run verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/`

**Checkpoint**: All 7 cycle cache call sites consolidated into `_cycle_cached()`. Existing tests pass unchanged.

---

## Phase 4: User Story 5 — Intentional Deviation Documentation (Priority: P3)

**Goal**: Add inline comments to two `resolve_repository()` call sites in `workflow.py` that intentionally deviate from the canonical 5-step fallback, so future engineers understand the deliberate deviation and don't mistakenly "fix" them (~+5 LOC).

**Independent Test**: Code review — comments are present, accurate, and explain the rationale for each deviation.

**Plan Phase**: A (parallel — can run alongside Phase 3 and Phase 5)

### Implementation for User Story 5

- [ ] T009 [P] [US5] Add inline comment at `solune/backend/src/api/workflow.py` (~line 543) documenting why `get_config` uses a custom `session.github_username` fallback instead of the canonical `resolve_repository()` 5-step fallback — explain the ~90% consolidation state
- [ ] T010 [P] [US5] Add inline comment at `solune/backend/src/api/workflow.py` (~line 615) documenting why `discover_agents` uses intentional partial-resolution with query param override instead of the canonical `resolve_repository()` 5-step fallback
- [ ] T011 [US5] Run verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/`

**Checkpoint**: Both deviation sites documented. No functional changes.

---

## Phase 5: User Story 4 — Dead Code Removal and Spec 039 (Priority: P2)

**Goal**: Remove the unreachable `branch_in_delete` inner block in `cleanup_service.py`, add a regression test for the `branch_preserved` code path, author Spec 039 with a complete dead code inventory from static analysis, and execute a time-boxed sweep (~9 LOC reduction from block removal + inventory-driven sweep).

**Independent Test**: Run `ruff check --select F401,F811 src/` and `vulture src/` before and after the sweep — verify inventory matches spec. Regression test confirms `branch_preserved` code path works correctly.

**Plan Phase**: A (dead code block removal, parallel with Phases 3–4) + D (Spec 039 authoring, after Phases 6–7 complete)

**⚠️ EXECUTION SPLIT**: Tasks T012–T016 can proceed in Plan Phase A (parallel with US2 and US5). Tasks T017–T020 should wait until Plan Phases B and C are complete to avoid noisy diffs during the largest refactoring phases.

### Implementation for User Story 4

#### Part 1: Dead Code Block Removal (Plan Phase A — parallel)

- [ ] T012 [US4] Verify mutual exclusivity of `preserved_branch_names` and `branches_to_delete` by inspecting the `_classify_branches()` categorization logic in `solune/backend/src/services/cleanup_service.py` — confirm the `if/else` at ~lines 758–767 places each branch in exactly one list
- [ ] T013 [US4] Remove unreachable `branch_in_delete` inner block (lines 641–649) in `solune/backend/src/services/cleanup_service.py` — remove the nested check and its body, preserving the outer `branch_preserved` logic
- [ ] T014 [US4] Add regression test exercising the `branch_preserved` code path in `solune/backend/tests/unit/test_cleanup_service.py` — test that a branch categorized as preserved is correctly handled and does NOT appear in `branches_to_delete`
- [ ] T015 [US4] Run verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/`

#### Part 2: Spec 039 Authoring & Dead Code Sweep (Plan Phase D — after Phases 6–7)

- [ ] T016 [US4] Run `ruff check --select F401,F811 solune/backend/src/` and capture full output as dead code inventory input
- [ ] T017 [US4] Run `vulture solune/backend/src/` (install if not available via `pip install vulture`) and capture full output as dead code inventory input
- [ ] T018 [US4] Create `specs/039-dead-code-cleanup/` directory and author `spec.md` documenting all dead code items — include the `cleanup_service.py` L641–649 block, all `ruff` findings, all `vulture` findings, and a disposition for each item (remove, defer, or retain with justification)
- [ ] T019 [US4] Execute time-boxed dead code sweep: remove only items with "remove" disposition from Spec 039, skip deferred or retained items
- [ ] T020 [US4] Run verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/ && ruff check --select F401,F811 src/`

**Checkpoint**: Dead code block removed, regression test passes, Spec 039 authored with complete inventory, sweep executed. `ruff check --select F401,F811 src/` returns zero new findings.

---

## Phase 6: User Story 1 — Global Cache Pattern Consolidation (Priority: P1) 🎯 MVP

**Goal**: Refactor up to 10 call sites to use the existing `cached_fetch()` helper in `cache.py`, targeting ~80 LOC reduction. Board.py dual-key cache sites should remain inline if the generic wrapper is ill-fitting (80% coverage target).

**Independent Test**: Invoke any cached endpoint (e.g., fetch board data), verify cache miss triggers upstream fetch and stores result with correct TTL, subsequent call within TTL returns cached value. Stale fallback tested by simulating upstream failure after prior success.

**Plan Phase**: B (sequential — requires Plan Phase A stability from Phases 3–5)

**⚠️ PREREQUISITE**: Phases 3, 4, and 5 Part 1 must be complete (Plan Phase A stability).

### Implementation for User Story 1

- [ ] T021 [US1] Audit all 10 global cache call sites across `board.py`, `projects.py`, `utils.py`, `issues.py`, `service.py` — classify each as refactorable (single-key pattern) or must-stay-inline (dual-key/custom variant per board.py) using the call-site mapping from data-model.md
- [ ] T022 [P] [US1] Refactor 4 cache call sites in `solune/backend/src/api/projects.py` (~lines 128, 150, 170, 190) to use `await cached_fetch(cache_key, fetch_fn, ttl_seconds=...)` — these form a single stale-fallback group and should be consolidated into one `cached_fetch()` call
- [ ] T023 [P] [US1] Refactor 1 cache call site in `solune/backend/src/utils.py` (~line 238, `resolve_repository`) to use `await cached_fetch(cache_key, fetch_fn, ttl_seconds=...)`
- [ ] T024 [P] [US1] Refactor 1 cache call site in `solune/backend/src/services/github_projects/issues.py` (~line 751, `sub_issues`) to use `await cached_fetch(cache_key, fetch_fn, ttl_seconds=600)`
- [ ] T025 [P] [US1] Refactor 1 cache call site in `solune/backend/src/services/github_projects/service.py` (~line 108) to use `await cached_fetch(cache_key, fetch_fn, ttl_seconds=...)`
- [ ] T026 [US1] Evaluate and refactor refactorable cache call sites in `solune/backend/src/api/board.py` (~lines 221, 293, 432) — skip dual-key variants with stale-fallback + rate-limit classification that don't fit `cached_fetch()` cleanly; document which sites remain inline and why
- [ ] T027 [US1] Run verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/`

**Checkpoint**: Up to 10 cache call sites consolidated. ~80 LOC reduction achieved. Board.py dual-key sites documented if kept inline. All existing tests pass unchanged.

---

## Phase 7: User Story 3 — Error Handling Consolidation (Priority: P2)

**Goal**: Extend `handle_service_error()` with relaxed `error_cls` typing, migrate 8 catch-log-raise patterns across 3 files, preserve `ValueError` at `ai_agent.py` API boundaries, and document the ValueError deviation (~15–20 LOC reduction).

**Independent Test**: Trigger an error in each of the 8 call sites, verify exception type, message, and logged context are identical before and after migration. Verify API-layer test assertions for hardcoded exception type checks pass unchanged.

**Plan Phase**: C (sequential — requires Plan Phase A stability from Phases 3–5)

**⚠️ PREREQUISITE**: Phases 3, 4, and 5 Part 1 must be complete (Plan Phase A stability).

### Implementation for User Story 3

- [ ] T028 [US3] Extend `handle_service_error()` in `solune/backend/src/logging_utils.py` — relax `error_cls` type annotation from `type[AppException] | None` to `type[Exception] | None` and add type-aware construction: use `error_cls(message=...)` for `AppException` subclasses, `error_cls(...)` (positional) for other exception types like `ValueError`
- [ ] T029 [US3] Add test case in `solune/backend/tests/unit/test_logging_utils.py` covering `handle_service_error()` with `error_cls=ValueError` — verify `ValueError` is raised with positional message, not keyword `message=`
- [ ] T030 [US3] Audit API-layer test assertions across `solune/backend/tests/` for hardcoded exception type checks (e.g., `GitHubAPIError`, `ValueError`) — document which tests verify exception types so post-migration regression can be confirmed
- [ ] T031 [P] [US3] Migrate 3 catch-log-raise patterns in `solune/backend/src/api/board.py` (L293, L432, L532) to `handle_service_error(e, "operation", error_cls=GitHubAPIError)` — preserve identical `GitHubAPIError` with same message format
- [ ] T032 [P] [US3] Migrate 4 catch-log-raise patterns in `solune/backend/src/services/ai_agent.py` (L193, L262, L595, L769) to `handle_service_error(e, "operation", error_cls=ValueError)` — preserve string-based error classification (`"401"`, `"404"`, `"Access denied"`) as pre-check conditionals before calling the helper; document string-based classification as tech debt with inline comment
- [ ] T033 [US3] Add inline comment in `solune/backend/src/services/ai_agent.py` at each migrated site documenting the deliberate `ValueError` deviation from the `AppException` subclass convention — explain that changing to `AppException` would silently alter API error-response shape (FR-010)
- [ ] T034 [US3] Migrate 1 bare-raise pattern in `solune/backend/src/services/agents/service.py` (~L1176) to `handle_service_error(exc, "agent chat completion")` — preserve re-raise behavior (no `error_cls`, original exception propagates)
- [ ] T035 [US3] Run verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/` — confirm all API-layer exception type assertions pass unchanged

**Checkpoint**: All 8 catch-log-raise patterns migrated. `ValueError` preserved at `ai_agent.py` boundaries. ~15–20 LOC reduction achieved. All existing tests pass unchanged.

---

## Phase 8: User Story 6 — Singleton Removal Deferral Documentation (Priority: P3)

**Goal**: Document that module-level singleton removal is explicitly deferred to a follow-up PR, with pre-defined scope for that PR (audit 17+ consumers, introduce `get_github_service()` accessor, update test mocks).

**Independent Test**: Confirm no changes are made to singleton patterns in this PR. Verify deferral documentation exists with follow-up scope.

**Plan Phase**: E (deferred — NOT part of this PR, documentation only)

### Implementation for User Story 6

- [ ] T036 [P] [US6] Add deferral documentation comment at the module-level singleton in `solune/backend/src/services/github_projects/service.py` (~line 459) — note that removal is deferred to a follow-up PR per FR-008, list required scope: audit 17+ consumers (background tasks, signal bridge, orchestrator), introduce `get_github_service()` accessor, update all test mocks
- [ ] T037 [P] [US6] Add deferral documentation comment at the module-level singleton in `solune/backend/src/services/github_projects/agents.py` (~line 363) — note that removal is deferred to a follow-up PR per FR-008, with same scope requirements as T036
- [ ] T038 [US6] Run verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/`

**Checkpoint**: Singleton deferral documented. No functional changes to singletons. Follow-up PR scope pre-defined.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, quality checks, and cross-cutting verification

- [ ] T039 Run full verification gate: `cd solune/backend && python -m pytest tests/ -x && ruff check src/ && ruff check --select F401,F811 src/`
- [ ] T040 Verify zero behavioral changes at API boundaries — spot-check that cache TTLs, stale-fallback semantics, exception types, and response shapes are identical pre/post refactoring
- [ ] T041 Run optional quality checks: `cd solune/backend && pyright src/` (type checking) and `bandit -r src/` (security scanning)
- [ ] T042 Verify Spec 039 inventory matches actual dead code removal — confirm all "remove" items were removed and all "defer"/"retain" items are untouched
- [ ] T043 Confirm singleton patterns at `service.py:459` and `agents.py:363` are untouched (FR-008 deferral compliance)

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup (baseline verification)
  └── No dependencies — start immediately

Phase 2: Foundational (N/A)
  └── Skip — no new infrastructure needed

┌─────────────────────────────────────────────────────────────┐
│  PLAN PHASE A — Parallel, Low Risk                          │
│                                                             │
│  Phase 3: US2 (Cycle Cache)    ──┐                          │
│  Phase 4: US5 (Deviation Docs) ──├── No interdependencies   │
│  Phase 5 Part 1: US4 (Dead Code)─┘   Can run in parallel    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼ (requires Phase A stability)
┌─────────────────────────────────────────────────────────────┐
│  PLAN PHASE B — Sequential, Largest Change                  │
│                                                             │
│  Phase 6: US1 (Global Cache — ~80 LOC, 10 call sites)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼ (requires Phase A stability)
┌─────────────────────────────────────────────────────────────┐
│  PLAN PHASE C — Sequential, Error Handling                  │
│                                                             │
│  Phase 7: US3 (Error Handling — 8 sites, 3 files)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼ (requires Phases B+C completion)
┌─────────────────────────────────────────────────────────────┐
│  PLAN PHASE D — Spec Authoring & Sweep                      │
│                                                             │
│  Phase 5 Part 2: US4 (Spec 039 + Dead Code Sweep)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
Phase 8: US6 (Singleton Deferral — documentation only)
Phase 9: Polish & Cross-Cutting Concerns
```

### User Story Dependencies

- **US2 (P1)**: Can start immediately after baseline — no dependencies on other stories
- **US5 (P3)**: Can start immediately after baseline — no dependencies on other stories
- **US4 Part 1 (P2)**: Can start immediately after baseline — dead code block removal is independent
- **US1 (P1)**: Requires Phase A completion — largest change, needs stable baseline after US2/US5/US4-Part1
- **US3 (P2)**: Requires Phase A completion — touches overlapping files with US1, needs stable baseline
- **US4 Part 2 (P2)**: Requires Phases B+C completion — Spec 039 should capture final state after all refactoring
- **US6 (P3)**: No functional dependencies — documentation only, but logically last

### Within Each User Story

- Foundational method/helper creation before call-site refactoring
- Call-site refactoring across parallel files (marked [P])
- Verification gate after all call sites are refactored
- Tests only where spec mandates (FR-005 regression test, FR-004 error_cls test)

### Parallel Opportunities

**Plan Phase A** (Phases 3, 4, 5 Part 1 — all parallel):
- T004–T007 can run in parallel (different files in `github_projects/`)
- T009–T010 can run in parallel (same file, different locations)
- T012–T014 can proceed independently from T003–T007 and T009–T010

**Plan Phase B** (Phase 6):
- T022–T025 can run in parallel (different files: `projects.py`, `utils.py`, `issues.py`, `service.py`)

**Plan Phase C** (Phase 7):
- T031–T032 can run in parallel (different files: `board.py`, `ai_agent.py`)

**Cross-phase parallelism**:
- Phases 3, 4, and 5 Part 1 can be staffed to three developers simultaneously
- Phases 6 and 7 can potentially overlap if they don't touch the same files (US1 touches `board.py` and `issues.py`, US3 touches `board.py` — so board.py is a conflict point; sequence US1 board.py work before US3 board.py work)

---

## Parallel Example: User Story 2

```bash
# After T003 (helper method) is complete, launch all call-site refactors in parallel:
Task T004: "Refactor 3 cycle cache sites in pull_requests.py"
Task T005: "Refactor 1 cycle cache site in projects.py"
Task T006: "Refactor 2 cycle cache sites in copilot.py"
Task T007: "Refactor 1 cycle cache site in issues.py"
```

## Parallel Example: User Story 1

```bash
# After T021 (audit) is complete, launch all single-key refactors in parallel:
Task T022: "Refactor 4 cache sites in api/projects.py"
Task T023: "Refactor 1 cache site in utils.py"
Task T024: "Refactor 1 cache site in github_projects/issues.py"
Task T025: "Refactor 1 cache site in github_projects/service.py"
```

---

## Implementation Strategy

### MVP First (Plan Phase A — Quick Wins)

1. Complete Phase 1: Setup (baseline green)
2. Complete Phase 3: US2 — Cycle Cache (~5 LOC reduction, 7 call sites → 1 helper)
3. **STOP and VALIDATE**: Run verification gate, confirm all tests pass
4. This delivers the smallest, safest consolidation first

### Incremental Delivery

1. **Plan Phase A** → US2 + US5 + US4-Part1 complete → Foundation stable ✅
2. **Plan Phase B** → US1 complete → Largest LOC reduction (~80 lines) ✅
3. **Plan Phase C** → US3 complete → Error handling uniform ✅
4. **Plan Phase D** → US4-Part2 complete → Spec 039 authored, dead code swept ✅
5. **Documentation** → US6 complete → Singleton deferral documented ✅
6. Each phase adds value without breaking previous phases

### Parallel Team Strategy

With multiple developers:

1. Team verifies baseline together (Phase 1)
2. Once baseline is green:
   - Developer A: US2 (Cycle Cache — Phase 3)
   - Developer B: US5 (Deviation Docs — Phase 4)
   - Developer C: US4 Part 1 (Dead Code Block — Phase 5 Part 1)
3. After Phase A complete:
   - Developer A: US1 (Global Cache — Phase 6)
   - Developer B: US3 (Error Handling — Phase 7) — coordinate board.py timing with Dev A
4. After Phases B+C complete:
   - Developer C: US4 Part 2 (Spec 039 — Phase 5 Part 2)
5. Final: US6 docs + Polish (Phase 8 + 9)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 43 |
| **US1 tasks** (Global Cache) | 7 (T021–T027) |
| **US2 tasks** (Cycle Cache) | 6 (T003–T008) |
| **US3 tasks** (Error Handling) | 8 (T028–T035) |
| **US4 tasks** (Dead Code + Spec 039) | 9 (T012–T020) |
| **US5 tasks** (Deviation Docs) | 3 (T009–T011) |
| **US6 tasks** (Singleton Deferral) | 3 (T036–T038) |
| **Setup tasks** | 2 (T001–T002) |
| **Polish tasks** | 5 (T039–T043) |
| **Parallel opportunities** | 14 tasks marked [P] across 4 phases |
| **Est. total LOC reduction** | ~109 lines (~80 cache + ~5 cycle + ~15–20 error + ~9 dead code) |
| **Suggested MVP scope** | US2 (Phase 3) — smallest, safest, parallel-ready |
| **Deferred to follow-up PR** | Singleton removal (US6/FR-008) — 17+ consumers, highest blast radius |

### Format Validation

✅ ALL 43 tasks follow the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ Setup phase tasks (T001–T002): No story label ✓
✅ User story phase tasks (T003–T038): Story label present where required ✓
✅ Polish phase tasks (T039–T043): No story label ✓
✅ All [P] markers indicate tasks on different files with no dependencies on incomplete tasks ✓
✅ All tasks include exact file paths or verification commands ✓

### Independent Test Criteria Per Story

| Story | Independent Test |
|-------|-----------------|
| US1 | Invoke cached endpoint → verify cache miss/hit/stale behavior → all existing tests pass |
| US2 | Call cycle-cached method → verify cache miss/hit + hit-count → all existing tests pass |
| US3 | Trigger error at each of 8 sites → verify exception type/message/context identical → API tests pass |
| US4 | Run `ruff --select F401,F811` + `vulture` → zero findings after sweep → regression test passes |
| US5 | Code review confirms comments present and accurate at workflow.py ~L543 and ~L615 |
| US6 | Confirm singletons untouched + deferral docs present |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Verification gate after every phase: `python -m pytest tests/ -x && ruff check src/`
- board.py dual-key cache sites may remain inline — 80% coverage target, not 100% (Principle V: Simplicity)
- ai_agent.py ValueError is a deliberate deviation from AppException — must be documented, not "fixed"
- Singleton removal (FR-008) is BLOCKED — do NOT modify `service.py:459` or `agents.py:363` singletons
- Spec 039 directory does not yet exist — creation is task T018
- `cached_fetch()` already exists in `cache.py` L187–277 — no new helper needed, only call-site refactoring
