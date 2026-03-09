# Tasks: Performance Review

**Input**: Design documents from `/specs/032-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — spec.md explicitly requires test coverage (FR-015, FR-016) and the plan constitution confirms test optionality is exercised.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories US1 and US4 (backend and frontend respectively) can proceed in parallel after baselines are captured.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`
- **Frontend tests**: `frontend/src/hooks/*.test.tsx`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Validate environment, confirm current implementation state, and prepare for baseline measurement.

- [x] T001 Validate development environment: install backend dependencies (`pip install -e ".[dev]"` in `backend/`) and frontend dependencies (`npm install` in `frontend/`), run existing test suites to confirm green baseline
- [x] T002 Audit Spec 022 implementation state in `backend/src/api/projects.py`: verify whether server-side hash-based change detection for WebSocket subscriptions is implemented or missing
- [x] T003 [P] Audit fallback polling invalidation scope in `frontend/src/hooks/useRealTimeSync.ts`: document whether polling currently invalidates board data query or tasks query only

---

## Phase 2: Foundational — Performance Baselines (Blocking Prerequisites)

**Purpose**: Capture quantitative before-state for all performance metrics. This phase BLOCKS all optimization work because success criteria depend on these baselines.

**⚠️ CRITICAL**: No optimization task (Phase 3+) can begin until this phase is complete.

### Baseline Capture for User Story 3

- [x] T004 [US3] Define measurement protocol covering all baseline metrics (idle API call count, board endpoint cost cold/warm, WS refresh frequency, polling refresh frequency, board render time, interaction response time, rerender count per update) per data-model.md PerformanceBaseline entity
- [x] T005 [P] [US3] Capture backend idle API call count baseline: count outgoing GitHub API calls with a board open and no user interaction over a 5-minute window using `backend/src/api/board.py` and `backend/src/api/projects.py` request logging
- [x] T006 [P] [US3] Capture backend cold-cache vs warm-cache board refresh call counts: measure external API calls for a full board refresh with empty cache vs warm sub-issue cache in `backend/src/services/github_projects/service.py`
- [x] T007 [P] [US3] Capture frontend render profiling baseline: measure rerender counts per single task update and board initial load time using React Profiler on `frontend/src/pages/ProjectsPage.tsx` and board components
- [x] T008 [P] [US3] Capture frontend network activity baseline: document fallback polling request frequency, WebSocket message frequency, and query invalidation patterns in `frontend/src/hooks/useRealTimeSync.ts` and `frontend/src/hooks/useBoardRefresh.ts`
- [x] T009 [US3] Document all baseline results in a measurement log for before/after comparison per FR-001 and FR-002

**Checkpoint**: Baselines documented — optimization work can now begin. US1/US5 (backend) and US4/US2/US6 (frontend) can proceed in parallel.

---

## Phase 3: User Story 1 — Idle Board Viewing Without Unnecessary API Activity (Priority: P1) 🎯 MVP

**Goal**: Reduce idle API consumption by at least 50% through server-side WebSocket change detection and fallback polling scope fixes.

**Independent Test**: Open a board, leave it idle for 5 minutes, count outgoing API calls. Compare against Phase 2 baseline — must be ≤50% of baseline (SC-001).

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Add backend test for WebSocket hash-based change detection: verify that when task data is unchanged, no WebSocket message is sent to the client in `backend/tests/unit/test_api_board.py`
- [x] T011 [P] [US1] Add backend test for WebSocket hash update on data change: verify that when task data changes, a message is sent and the stored hash is updated in `backend/tests/unit/test_api_board.py`
- [x] T012 [P] [US1] Add frontend test for fallback polling invalidation scope: verify that polling fallback only invalidates the tasks query and does NOT invalidate the board data query in `frontend/src/hooks/useRealTimeSync.test.tsx`

### Implementation for User Story 1

- [x] T013 [US1] Implement server-side hash-based change detection for WebSocket subscriptions in `backend/src/api/projects.py`: hash current task data before sending, compare with stored hash per subscription, skip message if unchanged per cache-contract.md Contract 3
- [x] T014 [US1] Add hash storage and cleanup lifecycle for WebSocket subscriptions in `backend/src/api/projects.py`: initialize hash as null on new connection, clean up on disconnection
- [x] T015 [US1] Fix fallback polling to only invalidate tasks query (not board data query) in `frontend/src/hooks/useRealTimeSync.ts` per refresh-contract.md Contract 1
- [x] T016 [US1] Verify idle board produces zero WebSocket messages after initial data delivery when data is unchanged, and fallback polling does not trigger expensive board refreshes

**Checkpoint**: Idle API consumption should be measurably reduced. Re-measure idle call count and compare against T005 baseline.

---

## Phase 4: User Story 4 — Coherent Refresh Policy Across Update Channels (Priority: P2)

**Goal**: Establish a single coherent refresh policy so WebSocket, fallback polling, auto-refresh, and manual refresh do not duplicate or conflict with each other.

**Independent Test**: Simulate each refresh trigger (WebSocket message, poll tick, auto-refresh timer, manual refresh button) in isolation and combination. Confirm only the expected data operations occur per refresh-contract.md Contract 1 decision matrix.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T017 [P] [US4] Add test for refresh channel isolation: verify WebSocket messages do not trigger board data query invalidation in `frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T018 [P] [US4] Add test for refresh deduplication: verify that 3+ simultaneous refresh triggers within 1 second result in at most 1 board data refresh in `frontend/src/hooks/useBoardRefresh.test.tsx`
- [x] T019 [P] [US4] Add test for manual refresh cache bypass: verify manual refresh calls API with `refresh=true` and invalidates both board data and tasks queries in `frontend/src/hooks/useBoardRefresh.test.tsx`

### Implementation for User Story 4

- [x] T020 [US4] Ensure all WebSocket message types (`task_update`, `task_created`, `status_changed`, `refresh`, `initial_data`) only invalidate tasks query in `frontend/src/hooks/useRealTimeSync.ts` per refresh-contract.md Contract 3 message-type-to-action mapping
- [x] T021 [US4] Verify auto-refresh in `frontend/src/hooks/useBoardRefresh.ts` uses `invalidateQueries` with stale-while-revalidate (no `refresh=true` bypass) per refresh-contract.md Contract 1
- [x] T022 [US4] Confirm manual refresh is the only path that calls API with `refresh=true` and invalidates both board data and tasks queries in `frontend/src/hooks/useBoardRefresh.ts`
- [x] T023 [US4] Verify fallback polling suppression when WebSocket is connected: poll tick should be a no-op when WS is active in `frontend/src/hooks/useRealTimeSync.ts` per refresh-contract.md Contract 2 timing contract

**Checkpoint**: All four refresh channels operate under a single coherent policy. Simulate combined triggers and confirm no refresh storms.

---

## Phase 5: User Story 2 — Responsive Board Interactions (Priority: P2)

**Goal**: Ensure board interactions (scroll, drag, card click) respond within 100ms on 50+ card boards, and single task updates do not cause full board rerenders.

**Independent Test**: Profile board interactions on a representative board (5+ columns, 50+ cards). Confirm interaction response times <100ms and single-card updates only rerender the affected card and parent column (SC-003, SC-004).

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T024 [P] [US2] Add test verifying that callback props passed to BoardColumn are stable references (do not change identity between renders) in `frontend/src/pages/ProjectsPage.tsx` test file or inline test
- [x] T025 [P] [US2] Add test verifying that a single card data change does not trigger rerender of unrelated BoardColumn components in `frontend/src/components/board/BoardColumn.tsx` test file or inline test

### Implementation for User Story 2

- [x] T026 [US2] Stabilize callback props passed to memoized BoardColumn components: wrap `getGroups` and other function props in `useCallback` with correct dependency arrays in `frontend/src/pages/ProjectsPage.tsx`
- [x] T027 [P] [US2] Stabilize callback props passed to memoized IssueCard components: ensure `onClick`, `onStatusChange`, and `availableAgents` props are stable references in `frontend/src/components/board/BoardColumn.tsx`
- [x] T028 [US2] Verify that a single task update arriving via WebSocket rerenders only the affected IssueCard in `frontend/src/components/board/IssueCard.tsx` and its parent BoardColumn in `frontend/src/components/board/BoardColumn.tsx` — not other columns or cards

**Checkpoint**: Board interactions are responsive. Profile confirms <100ms interaction response and minimal rerender scope per SC-003 and SC-004.

---

## Phase 6: User Story 5 — Backend Cache Effectiveness for Board Data (Priority: P3)

**Goal**: Ensure warm sub-issue caches reduce external API calls by at least 50% compared to cold-cache board refresh (SC-002).

**Independent Test**: Warm the cache with an initial board load, then trigger a subsequent board refresh (without `refresh=true`) and count external API calls. Compare against cold-cache count from T006 baseline.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T029 [P] [US5] Add test verifying that automatic board refresh reuses cached sub-issue data (no sub-issue API calls when cache is warm) in `backend/tests/unit/test_api_board.py`
- [x] T030 [P] [US5] Add test verifying that manual refresh (`refresh=true`) clears sub-issue caches before fetching in `backend/tests/unit/test_api_board.py`
- [x] T031 [P] [US5] Add test for sub-issue cache key format (`sub_issues:{owner}/{repo}#{issue_number}`) and TTL (600s) in `backend/tests/unit/test_cache.py`

### Implementation for User Story 5

- [x] T032 [US5] Verify automatic refresh path in `backend/src/services/github_projects/service.py` checks sub-issue cache before making REST calls and serves cached data when TTL is valid per cache-contract.md Contract 2
- [x] T033 [US5] Verify manual refresh path in `backend/src/api/board.py` clears sub-issue caches for affected issues before fetching per cache-contract.md Contract 2 invariant 5
- [x] T034 [P] [US5] Add debug-level logging for sub-issue cache hit/miss events in `backend/src/services/github_projects/service.py` for observability per cache-contract.md error behavior
- [x] T035 [US5] Measure warm-cache board refresh API call count and confirm ≥50% reduction vs cold-cache baseline from T006

**Checkpoint**: Warm-cache board refresh uses at least 50% fewer external API calls. Cache hit/miss logging confirms effectiveness.

---

## Phase 7: User Story 6 — Low-Risk Frontend Render Optimization (Priority: P3)

**Goal**: Reduce unnecessary computational work during rendering through memoization, stable references, and event listener throttling — without introducing new dependencies or architectural changes.

**Independent Test**: Profile render counts and component update frequency during typical board interactions. Compare against T007 baseline and confirm reduced rerender counts and throttled listener execution.

### Implementation for User Story 6

- [x] T036 [P] [US6] Memoize `getGroups` function (or equivalent grouping logic) in `frontend/src/pages/ProjectsPage.tsx` using `useCallback` with correct dependency array to prevent new closure creation per render
- [x] T037 [P] [US6] Throttle scroll and resize event listeners in `frontend/src/components/agents/AddAgentPopover.tsx` using `requestAnimationFrame` gating to prevent per-pixel `updatePosition` execution per refresh-contract.md Contract 4 invariant 3
- [x] T038 [US6] Verify derived state computations (`blockingIssueNumbers`, `assignedPipeline`, `assignedStageMap`) in `frontend/src/pages/ProjectsPage.tsx` have correct `useMemo` dependency arrays and do not recompute when input data is unchanged per FR-012
- [x] T039 [US6] Profile board interactions on `frontend/src/pages/ProjectsPage.tsx` and board components after render optimizations and confirm reduced rerender counts vs T007 baseline

**Checkpoint**: Frontend render work is measurably reduced. Profiling confirms fewer rerenders and throttled listeners per SC-003.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verification, regression coverage, and post-optimization baseline comparison across all user stories.

### Regression Test Extensions

- [x] T040 [P] Extend backend cache tests for sub-issue cache key generation and warm-cache reuse patterns in `backend/tests/unit/test_cache.py`
- [x] T041 [P] Extend frontend real-time sync tests for fallback polling scope and WebSocket message-type-to-action mapping in `frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T042 [P] Extend frontend board refresh tests for auto-refresh stale-while-revalidate behavior and refresh channel isolation in `frontend/src/hooks/useBoardRefresh.test.tsx`

### Post-Optimization Verification (US3 completion)

- [x] T043 [US3] Re-capture all baseline metrics using the same measurement protocol from T004 and compare against before-state documented in T009 per FR-014
- [x] T044 [US3] Validate that every baseline metric shows measurable improvement and no metric has regressed beyond acceptable tolerance per SC-008
- [x] T045 Run full backend test suite (`pytest` in `backend/`) and confirm all existing tests pass per FR-015
- [x] T046 [P] Run full frontend test suite (`npm test` in `frontend/`) and confirm all existing tests pass per FR-015
- [x] T047 [P] Run backend linting (`ruff check src/ tests/`) and type checking (`pyright src/`) in `backend/`
- [x] T048 [P] Run frontend linting (`npm run lint`), type checking (`npm run type-check`), and production build (`npm run build`) in `frontend/`
- [x] T049 Perform manual end-to-end verification per FR-016: confirm WebSocket updates refresh task data promptly, fallback polling remains safe, manual refresh bypasses caches, and board interactions remain responsive
- [x] T050 Run quickstart.md validation steps to confirm all commands and verification procedures work as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational / Baselines (Phase 2)**: Depends on Setup — BLOCKS all optimization phases
- **US1 (Phase 3) + US4 (Phase 4)**: Both depend on Foundational; can proceed in PARALLEL (backend vs frontend)
- **US2 (Phase 5)**: Depends on US4 completion (refresh-path fixes are prerequisite for responsiveness)
- **US5 (Phase 6) + US6 (Phase 7)**: Both depend on Foundational; can proceed in PARALLEL (backend vs frontend). US6 can start after Phase 2 but benefits from US4 completion (not strictly blocked)
- **Polish (Phase 8)**: Depends on all optimization phases being complete

### User Story Dependencies

- **US3 (P1)**: Foundational — blocks all other stories. Completes in Phase 2 (baselines) + Phase 8 (verification)
- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories (backend-only)
- **US4 (P2)**: Can start after Phase 2 — no dependencies on other stories (frontend-only). Can run in PARALLEL with US1
- **US2 (P2)**: Depends on US4 — refresh-path coherence is prerequisite for responsive interactions
- **US5 (P3)**: Can start after Phase 2 — independent backend work. Can run in PARALLEL with US4/US6
- **US6 (P3)**: Can start after Phase 2 — independent frontend work. Benefits from US4 but not strictly blocked

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend changes before frontend changes (when both exist in a story)
- Core implementation before integration verification
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different codebases)
- **Phase 2**: T005, T006, T007, T008 can all run in parallel (independent measurements)
- **Phase 3 + Phase 4**: Entire phases can run in parallel (backend US1 vs frontend US4)
- **Phase 6 + Phase 7**: Entire phases can run in parallel (backend US5 vs frontend US6)
- **Phase 8**: T040, T041, T042 can run in parallel; T045/T046/T047/T048 can run in parallel

---

## Parallel Example: US1 (Backend) + US4 (Frontend)

```bash
# After Phase 2 baselines are complete, launch backend and frontend work simultaneously:

# Backend (US1 — Idle Board Viewing):
Task: "Add backend test for WebSocket hash change detection in backend/tests/unit/test_api_board.py"
Task: "Implement server-side hash change detection in backend/src/api/projects.py"

# Frontend (US4 — Coherent Refresh Policy):
Task: "Add test for refresh channel isolation in frontend/src/hooks/useRealTimeSync.test.tsx"
Task: "Ensure all WebSocket message types only invalidate tasks query in frontend/src/hooks/useRealTimeSync.ts"
```

## Parallel Example: US5 (Backend) + US6 (Frontend)

```bash
# After US1/US4 are complete (or after Phase 2 if running in parallel):

# Backend (US5 — Cache Effectiveness):
Task: "Add test for warm-cache board refresh call reduction in backend/tests/unit/test_api_board.py"
Task: "Verify automatic refresh path checks sub-issue cache in backend/src/services/github_projects/service.py"

# Frontend (US6 — Render Optimization):
Task: "Memoize getGroups function in frontend/src/pages/ProjectsPage.tsx"
Task: "Throttle scroll/resize listeners in frontend/src/components/agents/AddAgentPopover.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 + Baselines)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational / Baselines (US3 before-state)
3. Complete Phase 3: User Story 1 — Idle Board Viewing
4. **STOP and VALIDATE**: Measure idle API call reduction against baseline
5. This alone delivers the highest-value improvement (P1 priority)

### Incremental Delivery

1. Phase 1 + Phase 2 → Baselines documented, environment validated
2. Phase 3 (US1) → Backend idle API reduction → Measure improvement (MVP!)
3. Phase 4 (US4) → Frontend refresh coherence → Verify no refresh storms
4. Phase 5 (US2) → Board responsiveness → Profile interactions
5. Phase 6 (US5) → Backend cache effectiveness → Measure warm-cache reduction
6. Phase 7 (US6) → Frontend render optimization → Profile rerenders
7. Phase 8 → Full verification, regression testing, before/after comparison

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + Phase 2 together (baselines)
2. Once baselines are documented:
   - **Backend developer**: US1 (Phase 3) → US5 (Phase 6)
   - **Frontend developer**: US4 (Phase 4) → US2 (Phase 5) → US6 (Phase 7)
3. Team reconvenes for Phase 8 (verification and regression coverage)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are written FIRST and verified to FAIL before implementation (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Deferred from first pass: board virtualization, service decomposition, new dependencies, architectural rewrites
- If Phase 8 measurements show large boards still lag, prepare follow-on plan per Phase 4 of the parent issue
