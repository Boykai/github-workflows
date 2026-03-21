# Tasks: Performance Review

**Input**: Design documents from `/specs/001-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/refresh-policy.md, quickstart.md

**Tests**: Tests ARE required for this feature (FR-019 through FR-021, User Story 6). Regression tests guard against reintroduction of performance problems.

**Organization**: Tasks are grouped by user story. User Story 5 (Baselines) is foundational and blocks all other stories. Backend stories (US1) and frontend stories (US4) can proceed in parallel once baselines are captured.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- **Backend tests**: `solune/backend/tests/unit/`
- **Frontend tests**: Co-located with source files (e.g., `useRealTimeSync.test.tsx`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing test infrastructure passes and development environment is ready before any optimization work begins.

- [ ] T001 Confirm existing backend targeted tests pass by running `python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -x -q --timeout=30` in solune/backend
- [ ] T002 [P] Confirm existing frontend targeted tests pass by running `npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx` in solune/frontend
- [ ] T003 [P] Run backend linting (`ruff check src/`) and type checking (`python -m pyright src/`) in solune/backend
- [ ] T004 [P] Run frontend linting (`npx eslint .`), type checking (`npx tsc --noEmit`), and build (`npx vite build`) in solune/frontend

---

## Phase 2: Foundational — User Story 5: Performance Baselines Are Captured Before Changes (Priority: P1)

**Goal**: Capture current backend and frontend performance baselines before any optimization code changes are made. These baselines serve as the "before" measurement that all improvements are validated against.

**Independent Test**: Produce a baseline report documenting idle API request count, board endpoint response time, board render time, and component re-render counts. All existing tests must pass.

**⚠️ CRITICAL**: No optimization work (Phases 3–7) can begin until this phase is complete.

### Baseline Capture

- [ ] T005 [US5] Create baseline measurement document at specs/001-performance-review/baseline.md with sections for backend metrics (idle API count, board endpoint cost, WebSocket refresh frequency) and frontend metrics (render time, re-render counts, network activity)
- [ ] T006 [US5] Audit WebSocket change detection by confirming `compute_data_hash()` comparison logic in `send_tasks()` within solune/backend/src/api/projects.py
- [ ] T007 [P] [US5] Audit board cache TTL alignment by confirming 300-second TTL in solune/backend/src/api/board.py matches `AUTO_REFRESH_INTERVAL_MS` (5 minutes) in solune/frontend/src/hooks/useBoardRefresh.ts
- [ ] T008 [P] [US5] Audit sub-issue cache invalidation on manual refresh by confirming `refresh=True` clears sub-issue caches via `cache.delete(get_sub_issues_cache_key(...))` in solune/backend/src/api/board.py
- [ ] T009 [P] [US5] Audit sub-issue cache preservation on auto-refresh by confirming `refresh=False` does NOT clear sub-issue caches in solune/backend/src/api/board.py
- [ ] T010 [P] [US5] Audit stale-revalidation counter behavior (10-cycle forced fetch with hash comparison) in solune/backend/src/api/projects.py `send_tasks()` loop
- [ ] T011 [P] [US5] Audit frontend refresh path decoupling by confirming `useRealTimeSync` only invalidates `['projects', projectId, 'tasks']` and never `['board', 'data', projectId]` in solune/frontend/src/hooks/useRealTimeSync.ts
- [ ] T012 [P] [US5] Audit fallback polling invalidation scope by confirming the 30-second fallback only invalidates the tasks query in solune/frontend/src/hooks/useRealTimeSync.ts
- [ ] T013 [US5] Document all audit findings and any identified gaps as implementation targets in specs/001-performance-review/baseline.md

**Checkpoint**: Baselines documented; all existing tests passing; backend and frontend state confirmed. Optimization work can now begin.

---

## Phase 3: User Story 1 — Board Stays Quiet When Idle (Priority: P1) 🎯 MVP

**Goal**: Reduce unnecessary GitHub API calls during idle board viewing. When board data is unchanged, the system should not issue repeated refresh cycles that consume API quota.

**Independent Test**: Open a board, leave it idle for 10 minutes, and count the outbound requests to GitHub. Compare the count against the Phase 2 baseline to confirm a reduction of at least 50% (SC-001).

### Tests for User Story 1

- [ ] T014 [US1] Add test for hash-based WebSocket refresh suppression verifying that `send_tasks()` does NOT send a `refresh` message when `compute_data_hash()` returns the same hash as the stored `CacheEntry.data_hash` in solune/backend/tests/unit/test_cache.py
- [ ] T015 [P] [US1] Add test for `refresh_ttl()` verifying it extends cache expiration without replacing the data entry or hash when data is unchanged in solune/backend/tests/unit/test_cache.py
- [ ] T016 [P] [US1] Add test verifying fallback polling loop does NOT call the board data endpoint and operates independently via `get_project_items()` in solune/backend/tests/unit/test_copilot_polling.py
- [ ] T017 [P] [US1] Add test verifying sub-issue filtering (`is_sub_issue()` filter) removes child issues before pipeline processing in solune/backend/tests/unit/test_copilot_polling.py
- [ ] T018 [P] [US1] Add test verifying sub-issue cache is preserved when board endpoint is called with `refresh=False` (auto-refresh path) in solune/backend/tests/unit/test_api_board.py

### Implementation for User Story 1

- [ ] T019 [US1] Verify and fix (if needed) WebSocket `send_tasks()` hash comparison logic suppresses refresh messages for unchanged data in solune/backend/src/api/projects.py
- [ ] T020 [US1] Verify and fix (if needed) `refresh_ttl()` correctly extends cache TTL without data replacement in solune/backend/src/services/cache.py
- [ ] T021 [P] [US1] Verify and fix (if needed) polling loop rate-limit gating at three thresholds (pause=50, skip_expensive=100, slow=200) in solune/backend/src/services/copilot_polling/polling_loop.py
- [ ] T022 [P] [US1] Verify and fix (if needed) sub-issue filtering in polling loop removes child issues before processing in solune/backend/src/services/copilot_polling/polling_loop.py
- [ ] T023 [US1] Re-measure backend idle API activity after verification/fixes and compare against Phase 2 baseline targeting ≥50% reduction (SC-001)

**Checkpoint**: Backend idle API calls confirmed reduced. WebSocket suppression, cache TTL extension, and polling isolation verified with test coverage.

---

## Phase 4: User Story 4 — Real-Time Updates Are Fast and Lightweight (Priority: P2)

**Goal**: Ensure WebSocket task-level updates remain decoupled from the expensive board data query. Lightweight task updates should never trigger a full board reload.

**Independent Test**: Have two users view the same board. One user changes a task status. Confirm the other user sees the update within 5 seconds without a full board reload appearing in the network log.

**Note**: This phase can proceed in parallel with Phase 3 (different files: frontend hooks vs. backend services).

### Tests for User Story 4

- [ ] T024 [US4] Add test verifying WebSocket `task_update` messages invalidate only `['projects', pid, 'tasks']` and NOT `['board', 'data', pid]` in solune/frontend/src/hooks/useRealTimeSync.test.tsx
- [ ] T025 [P] [US4] Add test verifying WebSocket `task_created` and `status_changed` messages follow the same tasks-only invalidation policy in solune/frontend/src/hooks/useRealTimeSync.test.tsx
- [ ] T026 [P] [US4] Add test verifying fallback polling (30-second interval) only invalidates the tasks query, not the board data query, in solune/frontend/src/hooks/useRealTimeSync.test.tsx
- [ ] T027 [P] [US4] Add test verifying `initial_data` debounce (2-second window) prevents cascade invalidations on WebSocket reconnect in solune/frontend/src/hooks/useRealTimeSync.test.tsx
- [ ] T028 [P] [US4] Add test verifying transition from WebSocket connected → polling fallback → reconnected does not multiply refresh requests in solune/frontend/src/hooks/useRealTimeSync.test.tsx

### Implementation for User Story 4

- [ ] T029 [US4] Verify and fix (if needed) `useRealTimeSync` WebSocket message handler only invalidates `['projects', projectId, 'tasks']` for all task-level message types in solune/frontend/src/hooks/useRealTimeSync.ts
- [ ] T030 [US4] Verify and fix (if needed) fallback polling path follows the same invalidation policy as WebSocket (tasks query only) in solune/frontend/src/hooks/useRealTimeSync.ts
- [ ] T031 [US4] Verify and fix (if needed) `initial_data` debounce prevents cascade invalidations on reconnect in solune/frontend/src/hooks/useRealTimeSync.ts
- [ ] T032 [US4] Verify and fix (if needed) `onRefreshTriggered` callback correctly resets board auto-refresh timer when WebSocket activity proves connectivity in solune/frontend/src/hooks/useRealTimeSync.ts

**Checkpoint**: WebSocket task updates confirmed decoupled from board data query. Fallback polling follows same policy. Reconnection debounce prevents cascade.

---

## Phase 5: User Story 3 — Manual Refresh Bypasses Caches (Priority: P2)

**Goal**: When a user clicks manual refresh, the system bypasses all caches and fetches fresh data from GitHub, including sub-issue data. This is the user's escape hatch for stale data.

**Independent Test**: Modify a card's status directly in GitHub, then click manual refresh on the board. Confirm the updated status appears without waiting for an auto-refresh cycle.

### Tests for User Story 3

- [ ] T033 [US3] Add test verifying `useBoardRefresh.refresh()` cancels in-flight auto-refresh queries and pending debounced reloads in solune/frontend/src/hooks/useBoardRefresh.test.tsx
- [ ] T034 [P] [US3] Add test verifying manual refresh result is written directly to query cache via `setQueryData` in solune/frontend/src/hooks/useBoardRefresh.test.tsx
- [ ] T035 [P] [US3] Add test verifying manual refresh during concurrent auto-refresh: manual result takes priority and auto-refresh result is discarded in solune/frontend/src/hooks/useBoardRefresh.test.tsx
- [ ] T036 [P] [US3] Add test verifying board endpoint with `refresh=true` bypasses board data cache AND proactively clears all sub-issue caches in solune/backend/tests/unit/test_api_board.py

### Implementation for User Story 3

- [ ] T037 [US3] Verify and fix (if needed) `useBoardRefresh.refresh()` cancels in-flight queries via `cancelQueries` and bypasses debounce in solune/frontend/src/hooks/useBoardRefresh.ts
- [ ] T038 [US3] Verify and fix (if needed) manual refresh writes result directly to query cache via `setQueryData` in solune/frontend/src/hooks/useBoardRefresh.ts
- [ ] T039 [US3] Verify and fix (if needed) board endpoint `refresh=true` path iterates all board items and deletes their sub-issue cache entries in solune/backend/src/api/board.py
- [ ] T040 [US3] Verify and fix (if needed) auto-refresh timer is reset after manual refresh completes in solune/frontend/src/hooks/useBoardRefresh.ts

**Checkpoint**: Manual refresh confirmed to bypass all caches, cancel competing refreshes, and deliver fresh data with priority over auto-refresh.

---

## Phase 6: User Story 2 — Board Loads and Responds Quickly (Priority: P1)

**Goal**: Reduce rendering costs in board and chat surfaces. Confirm memoization effectiveness, stabilize props, and throttle hot event listeners for low-risk render improvements.

**Independent Test**: Load a board with 50+ cards across 5+ columns. Measure initial render time and interaction latency. Compare against the Phase 2 baseline to confirm measurable improvement (SC-002: ≥20% render improvement target).

### Implementation for User Story 2

- [ ] T041 [US2] Profile `BoardColumn` `React.memo()` effectiveness — verify that when a single card updates, only the affected column re-renders, not all columns in solune/frontend/src/components/board/BoardColumn.tsx
- [ ] T042 [P] [US2] Profile `IssueCard` `React.memo()` effectiveness — verify that when one card updates via WebSocket, only that card re-renders (SC-003) in solune/frontend/src/components/board/IssueCard.tsx
- [ ] T043 [US2] Stabilize `BoardColumn` props with `useCallback`/`useMemo` where profiling shows callback recreation causes unnecessary re-renders in solune/frontend/src/components/board/BoardColumn.tsx
- [ ] T044 [P] [US2] Stabilize `IssueCard` callback props with `useCallback` where profiling shows unnecessary re-renders in solune/frontend/src/components/board/IssueCard.tsx
- [ ] T045 [US2] Verify `ProjectsPage` `useMemo` blocks cover all expensive derived computations (heroStats, rateLimitState, syncStatusLabel, syncStatusToneClass, assignedPipelineName) in solune/frontend/src/pages/ProjectsPage.tsx
- [ ] T046 [P] [US2] Verify `useBoardControls` transformation output (filter/sort/group) is memoized to prevent redundant recalculation in solune/frontend/src/hooks/ (locate useBoardControls or equivalent hook)
- [ ] T047 [US2] Verify `ChatPopup` `requestAnimationFrame` gating is effective for drag resize handlers — confirm no excessive callback frequency during drag in solune/frontend/src/components/chat/ChatPopup.tsx
- [ ] T048 [P] [US2] Verify `AddAgentPopover` uses Radix UI automatic positioning without custom hot listeners — confirm no manual position calculation on every frame in solune/frontend/src/components/agents/AddAgentPopover.tsx
- [ ] T049 [US2] Add `requestAnimationFrame` or `throttle()` gating to any board drag event listeners firing excessively (if profiling identifies a gap) in solune/frontend/src/components/board/ directory
- [ ] T050 [US2] Re-measure frontend render profile after fixes and compare against Phase 2 baseline (SC-002 target: ≥20% improvement, SC-009 target: ≥30% callback reduction)

**Checkpoint**: Board and chat rendering confirmed optimized. Component re-renders isolated to affected cards. Event listeners throttled where needed.

---

## Phase 7: User Story 6 — Regression Tests Guard Against Performance Regressions (Priority: P3)

**Goal**: Extend test coverage around all changed behaviors. The test suite should catch regressions if future changes accidentally reintroduce the performance problems fixed in earlier phases.

**Independent Test**: Run all targeted test suites and confirm all tests pass. Verify that new tests cover change-detection suppression, refresh path decoupling, and event listener throttling.

### Backend Regression Tests

- [ ] T051 [US6] Extend solune/backend/tests/unit/test_cache.py with test for `refresh_ttl()` preserving data hash when data content is unchanged
- [ ] T052 [P] [US6] Extend solune/backend/tests/unit/test_api_board.py with test for sub-issue cache preservation during auto-refresh (`refresh=False`)
- [ ] T053 [P] [US6] Extend solune/backend/tests/unit/test_copilot_polling.py with test for sub-issue filtering correctness (child issues removed before pipeline)
- [ ] T054 [US6] Run full backend test suite (`python -m pytest tests/unit/ -x -q --timeout=30`) and confirm all 3365+ tests pass in solune/backend

### Frontend Regression Tests

- [ ] T055 [US6] Extend solune/frontend/src/hooks/useRealTimeSync.test.tsx with test verifying board data query is NOT invalidated on any WebSocket task message type
- [ ] T056 [P] [US6] Extend solune/frontend/src/hooks/useBoardRefresh.test.tsx with test for manual refresh cancelling concurrent auto-refresh and taking priority
- [ ] T057 [US6] Run full frontend test suite (`npx vitest run`) and confirm all 1219+ tests pass in solune/frontend
- [ ] T058 [US6] Run frontend build check (`npx vite build`) to confirm no build regressions in solune/frontend

**Checkpoint**: All existing and new tests pass. Regression coverage confirmed for cache behavior, refresh decoupling, and polling isolation.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, measurement comparison, and documentation of results across all user stories.

- [ ] T059 Re-measure backend idle API activity over 10-minute window and compare against Phase 2 baseline (SC-001 target: ≥50% reduction)
- [ ] T060 [P] Re-measure frontend board render profile for 50+ card board and compare against Phase 2 baseline (SC-002 target: ≥20% improvement)
- [ ] T061 Manual end-to-end verification: confirm WebSocket updates refresh task data quickly, fallback polling remains safe, manual refresh bypasses caches, and board interactions remain responsive (SC-004, SC-005, SC-008)
- [ ] T062 Document before/after measurement results with specific numbers in specs/001-performance-review/baseline.md
- [ ] T063 [P] Run backend linting (`ruff check src/`) and type checking (`python -m pyright src/`) for final validation in solune/backend
- [ ] T064 [P] Run frontend linting (`npx eslint .`) and type checking (`npx tsc --noEmit`) for final validation in solune/frontend
- [ ] T065 Evaluate whether Phase 4 second-wave work (virtualization, service decomposition) is needed based on measurement results and document recommendation in specs/001-performance-review/baseline.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational / US5 Baselines (Phase 2)**: Depends on Setup — BLOCKS all optimization phases
- **US1 Backend API Fixes (Phase 3)**: Depends on Phase 2 baselines
- **US4 Frontend Refresh Paths (Phase 4)**: Depends on Phase 2 baselines — **can run in parallel with Phase 3**
- **US3 Manual Refresh (Phase 5)**: Depends on Phase 3 (backend cache) and Phase 4 (frontend refresh)
- **US2 Render Optimization (Phase 6)**: Depends on Phase 4 (refresh paths must be correct before optimizing renders)
- **US6 Regression Tests (Phase 7)**: Depends on all optimization phases (3–6)
- **Polish (Phase 8)**: Depends on all phases being complete

### User Story Dependencies

- **US5 (P1) — Baselines**: Foundational; blocks all other stories. No dependencies on other stories.
- **US1 (P1) — Idle API Reduction**: Depends on US5 baselines. Backend-only; independent of frontend stories.
- **US4 (P2) — Real-Time Updates**: Depends on US5 baselines. Frontend-only; can run in parallel with US1.
- **US3 (P2) — Manual Refresh**: Depends on US1 (backend cache contract) and US4 (frontend refresh paths).
- **US2 (P1) — Render Optimization**: Depends on US4 (refresh paths confirmed correct before render work).
- **US6 (P3) — Regression Tests**: Depends on all other stories being complete.

### Within Each User Story

- Tests written FIRST, verified to fail before implementation (where applicable)
- Audit/verification before implementation fixes
- Core fixes before integration
- Measurement after fixes to validate improvement
- Story checkpoint before moving to next

### Parallel Opportunities

- **Phase 1**: T001, T002, T003, T004 can all run in parallel (independent validation)
- **Phase 2**: T006 is sequential (audit entry point), but T007–T012 can all run in parallel (independent audits across different files)
- **Phase 3 + Phase 4**: Entire phases can run in parallel (backend vs. frontend, different file sets)
- **Phase 3**: T014–T018 tests can run in parallel; T021, T022 fixes can run in parallel (different files)
- **Phase 4**: T024–T028 tests can run in parallel (same file but different test blocks)
- **Phase 5**: T033–T036 tests can run in parallel (frontend + backend test files)
- **Phase 6**: T041+T042, T043+T044, T045+T046, T047+T048 are paired parallel tasks across related components
- **Phase 7**: Backend tests (T051–T053) and frontend tests (T055–T056) can run in parallel
- **Phase 8**: T059+T060, T063+T064 are paired parallel measurement/validation tasks

---

## Parallel Example: Phase 3 + Phase 4 (Maximum Parallelism)

```text
# These two phases can run simultaneously with different developers:

# Developer A — Phase 3 (US1 Backend):
Task T014: "Test hash-based WebSocket suppression in test_cache.py"
Task T015: "Test refresh_ttl() behavior in test_cache.py"
Task T016: "Test polling isolation in test_copilot_polling.py"
Task T019: "Verify send_tasks() hash comparison in projects.py"
Task T020: "Verify refresh_ttl() in cache.py"

# Developer B — Phase 4 (US4 Frontend):
Task T024: "Test WebSocket invalidation scope in useRealTimeSync.test.tsx"
Task T026: "Test fallback polling scope in useRealTimeSync.test.tsx"
Task T029: "Verify useRealTimeSync invalidation in useRealTimeSync.ts"
Task T030: "Verify fallback polling policy in useRealTimeSync.ts"
```

---

## Parallel Example: Phase 6 Render Optimization

```text
# Profile and fix pairs can run in parallel (different component files):

# Pair 1 — Column components:
Task T041: "Profile BoardColumn memo effectiveness in BoardColumn.tsx"
Task T043: "Stabilize BoardColumn props in BoardColumn.tsx"

# Pair 2 — Card components (parallel with Pair 1):
Task T042: "Profile IssueCard memo effectiveness in IssueCard.tsx"
Task T044: "Stabilize IssueCard callback props in IssueCard.tsx"

# Pair 3 — Page-level (parallel with Pairs 1-2):
Task T045: "Verify ProjectsPage useMemo coverage in ProjectsPage.tsx"
Task T046: "Verify useBoardControls memoization"
```

---

## Implementation Strategy

### MVP First (User Story 5 + User Story 1)

1. Complete Phase 1: Setup — confirm existing tests pass
2. Complete Phase 2: US5 Baselines — capture measurements, audit existing state
3. Complete Phase 3: US1 Backend API Reduction — verify/fix idle API consumption
4. **STOP and VALIDATE**: Re-measure idle API activity against baseline (SC-001: ≥50% reduction)
5. If SC-001 is met, the highest-value optimization is delivered

### Incremental Delivery

1. **Setup + Baselines (Phase 1-2)** → Foundation ready, measurements captured
2. **US1 Backend Fixes (Phase 3)** → Idle API reduction verified → Highest-cost issue resolved (MVP!)
3. **US4 Frontend Refresh (Phase 4)** → Real-time updates confirmed decoupled → Collaboration quality confirmed
4. **US3 Manual Refresh (Phase 5)** → Cache bypass contract verified → User trust in refresh established
5. **US2 Render Optimization (Phase 6)** → Board responsiveness improved → User-facing quality gain
6. **US6 Regression Tests (Phase 7)** → Full regression coverage → Long-term protection
7. **Polish (Phase 8)** → Final measurements, documentation, go/no-go for second wave

Each increment adds measurable value without breaking previous stories.

### Parallel Team Strategy

With two developers:

1. Team completes Setup + Baselines together (Phases 1-2)
2. Once baselines are captured:
   - **Developer A (Backend)**: US1 → US3 backend tasks → US6 backend tests
   - **Developer B (Frontend)**: US4 → US3 frontend tasks → US2 → US6 frontend tests
3. Both converge for Phase 8: Polish and final validation

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Research confirmed all core mechanisms (hash-based change detection, cache TTLs, refresh decoupling, component memoization) are already implemented — work is primarily verification, test coverage extension, and targeted fixes for any gaps
- No new dependencies are introduced (constraint from spec)
- No virtualization or service decomposition in this pass (deferred to Phase 4 optional second-wave unless metrics justify it)
- Baseline measurement is mandatory before code changes so improvements can be proven, not assumed
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
