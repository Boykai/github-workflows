# Tasks: Performance Review

**Input**: Design documents from `/specs/001-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/refresh-contract.md, quickstart.md

**Tests**: Tests are REQUIRED — the specification explicitly mandates regression test extension (FR-012, FR-013, SC-010).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories map to the phased implementation plan from the parent issue.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- **Backend tests**: `solune/backend/tests/unit/`
- **Frontend tests**: `solune/frontend/src/hooks/` (co-located test files)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment setup, verify all existing tests pass, and confirm tooling works before any measurement or optimization work begins.

- [ ] T001 Verify backend dev dependencies install cleanly with `cd solune/backend && pip install -e ".[dev]"`
- [ ] T002 [P] Verify frontend dependencies install cleanly with `cd solune/frontend && npm install`
- [ ] T003 Run existing backend test suite for performance-related files with `pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --timeout=60` in `solune/backend/`
- [ ] T004 [P] Run existing frontend test suite for refresh-related hooks with `npm run test -- --run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx` in `solune/frontend/`
- [ ] T005 [P] Run backend linting and type checks with `ruff check src tests && pyright src` in `solune/backend/`
- [ ] T006 [P] Run frontend linting, type checks, and build with `npm run lint && npm run type-check && npm run build` in `solune/frontend/`

**Checkpoint**: All existing tests pass, tooling works, and the codebase is in a known-good state before measurement begins.

---

## Phase 2: User Story 1 — Baseline Performance Measurement (Priority: P1) 🎯 MVP

**Goal**: Capture documented backend and frontend performance baselines so every subsequent optimization can be validated against real numbers. This phase BLOCKS all optimization work.

**Independent Test**: Run the baseline capture procedure on an open board. Record idle API call counts, board endpoint response times, WebSocket/polling refresh frequency, and frontend render profile data. Produces a measurement checklist that gates all subsequent work.

### Implementation for User Story 1

- [ ] T007 [US1] Audit WebSocket subscription loop for hash-based change detection status in `solune/backend/src/api/projects.py` — document whether `compute_data_hash()` is wired into the send-tasks flow and record current behavior (sends on every cycle vs. hash-gated)
- [ ] T008 [P] [US1] Audit board endpoint cache behavior in `solune/backend/src/api/board.py` — confirm 300s TTL is active, sub-issue cache is cleared on manual refresh (`refresh=True`), and cached data is served within TTL window
- [ ] T009 [P] [US1] Audit polling loop rate-limit budget behavior in `solune/backend/src/services/copilot_polling/polling_loop.py` — confirm `_check_rate_limit_budget()` and `_pause_if_rate_limited()` are active and record current threshold values
- [ ] T010 [P] [US1] Audit sub-issue caching in `solune/backend/src/services/github_projects/service.py` — confirm `get_sub_issues()` checks cache first with 600s TTL and only makes REST API calls on cache miss
- [ ] T011 [P] [US1] Audit frontend refresh-path separation in `solune/frontend/src/hooks/useRealTimeSync.ts` — confirm WebSocket messages and fallback polling invalidate only `['projects', projectId, 'tasks']` and do not touch `['board', 'data', projectId]`
- [ ] T012 [P] [US1] Audit auto-refresh suppression in `solune/frontend/src/hooks/useBoardRefresh.ts` — confirm auto-refresh timer is paused when `isWebSocketConnected=true` and resumes on disconnect
- [ ] T013 [P] [US1] Audit board query invalidation strategy in `solune/frontend/src/hooks/useProjectBoard.ts` — confirm query keys, stale times, and refetch triggers align with the refresh contract in `specs/001-performance-review/contracts/refresh-contract.md`
- [ ] T014 [P] [US1] Audit frontend component memoization in `solune/frontend/src/components/board/BoardColumn.tsx` and `solune/frontend/src/components/board/IssueCard.tsx` — confirm `React.memo()` wrapping and `useMemo` usage, identify any unstable callback references passed as props
- [ ] T015 [P] [US1] Audit page-level derived data in `solune/frontend/src/pages/ProjectsPage.tsx` — confirm `heroStats`, `rateLimitState`, `syncStatusLabel` are memoized via `useMemo`, identify any inline sorting/aggregation computed on every render
- [ ] T016 [P] [US1] Audit event listener patterns in `solune/frontend/src/components/chat/ChatPopup.tsx` — confirm resize/mousemove handlers are RAF-gated or throttled, identify any unthrottled hot listeners
- [ ] T017 [US1] Create baseline measurement document recording all audit findings at `specs/001-performance-review/checklists/baseline-measurements.md` — include current state of each audited behavior, gaps found, and before-values for SC-001 through SC-010

**Checkpoint**: Baseline measurements are documented. All gaps between current behavior and target behavior are identified. Optimization work can now begin with clear before/after comparison points.

---

## Phase 3: User Story 2 — Reduced Backend API Consumption During Idle Board Viewing (Priority: P1)

**Goal**: Eliminate unnecessary outbound GitHub API calls during idle board viewing by wiring hash-based change detection into the WebSocket subscription loop, verifying sub-issue cache reuse, and confirming polling guard rails.

**Independent Test**: Open a board, leave it idle for 5 minutes, and confirm that zero repeated unchanged refresh calls are emitted. The WebSocket subscription loop skips sending refresh messages when the data hash is unchanged.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US2] Add test for WebSocket hash-based change detection suppression in `solune/backend/tests/unit/test_api_board.py` — test that when `compute_data_hash()` returns the same hash as the last-sent message, no `refresh` message is sent to the client
- [ ] T019 [P] [US2] Add test for board endpoint cache hit within TTL in `solune/backend/tests/unit/test_api_board.py` — test that calling the board endpoint within 300s TTL without `refresh=True` returns cached data without an outbound GitHub API call
- [ ] T020 [P] [US2] Add test for sub-issue cache reuse on non-manual refresh in `solune/backend/tests/unit/test_api_board.py` — test that warm sub-issue cache entries are reused and no additional GitHub API calls are made for sub-issues
- [ ] T021 [P] [US2] Add test for fallback polling not triggering full board refetch in `solune/backend/tests/unit/test_copilot_polling.py` — test that polling interval fires do not invoke the board data endpoint

### Implementation for User Story 2

- [ ] T022 [US2] Wire `compute_data_hash()` into the WebSocket subscription send-tasks flow in `solune/backend/src/api/projects.py` — store last-sent hash per subscription, compare current hash against last-sent hash, skip sending `refresh` message when hashes match (FR-003, SC-001, SC-007)
- [ ] T023 [US2] Verify stale-revalidation counter correctly forces a fresh fetch after 10 unchanged cycles in `solune/backend/src/api/projects.py` — confirm the counter resets after a force-refresh and does not suppress legitimate data changes
- [ ] T024 [P] [US2] Verify board endpoint returns cached data within TTL without outbound API calls in `solune/backend/src/api/board.py` — confirm `cached_fetch()` is used correctly with the `board_data:{project_id}` cache key and 300s TTL (FR-004, SC-002)
- [ ] T025 [P] [US2] Verify sub-issue cache entries are preserved on non-manual board requests and cleared only on manual refresh in `solune/backend/src/api/board.py` — confirm the `refresh=True` path deletes sub-issue cache entries while the default path reuses them (FR-005, FR-006)
- [ ] T026 [P] [US2] Verify rate limit exhaustion returns stale cached data gracefully in `solune/backend/src/services/cache.py` — confirm `cached_fetch()` stale fallback activates on rate limit detection (429/403) and includes rate limit info in response (FR-014)

**Checkpoint**: Backend idle API consumption is eliminated. WebSocket subscription loop suppresses unchanged refresh messages. Cached board data is served within TTL. Sub-issue caches are reused. Rate limit exhaustion is handled gracefully.

---

## Phase 4: User Story 3 — Clean Refresh-Path Separation (Priority: P2)

**Goal**: Enforce clean separation between lightweight task updates (tasks query only) and expensive board data queries. WebSocket and polling messages invalidate only the tasks query; board data refreshes only via its own timer or manual user action.

**Independent Test**: Trigger a WebSocket task update message and verify only the tasks query is invalidated (not board data). Then trigger a manual refresh and confirm the full board query fires with cache bypass.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T027 [P] [US3] Add test for WebSocket `task_update` invalidating only tasks query in `solune/frontend/src/hooks/useRealTimeSync.test.tsx` — test that receiving a `task_update` message calls `invalidateQueries` with `['projects', projectId, 'tasks']` and does NOT call it with `['board', 'data', projectId]`
- [ ] T028 [P] [US3] Add test for fallback polling invalidating only tasks query in `solune/frontend/src/hooks/useRealTimeSync.test.tsx` — test that when WebSocket is unavailable and polling fires, only `['projects', projectId, 'tasks']` is invalidated
- [ ] T029 [P] [US3] Add test for auto-refresh suppression when WebSocket is connected in `solune/frontend/src/hooks/useBoardRefresh.test.tsx` — test that the auto-refresh timer does not fire when `isWebSocketConnected=true`
- [ ] T030 [P] [US3] Add test for manual refresh triggering full board data refetch with cache bypass in `solune/frontend/src/hooks/useBoardRefresh.test.tsx` — test that manual refresh calls the backend with `refresh=true` and the board data query is refetched

### Implementation for User Story 3

- [ ] T031 [US3] Verify and enforce tasks-only invalidation for all WebSocket message types in `solune/frontend/src/hooks/useRealTimeSync.ts` — confirm `task_update`, `task_created`, `status_changed`, `refresh`, and `initial_data` messages all invalidate only `['projects', projectId, 'tasks']` per the refresh contract (FR-007, FR-008)
- [ ] T032 [US3] Verify and enforce tasks-only invalidation for fallback polling in `solune/frontend/src/hooks/useRealTimeSync.ts` — confirm polling fallback path invalidates only `['projects', projectId, 'tasks']` and does not touch board data query (FR-007, SC-008)
- [ ] T033 [US3] Verify auto-refresh timer coordination with WebSocket status in `solune/frontend/src/hooks/useBoardRefresh.ts` — confirm timer is paused when WS connected, resumes on disconnect, and resets on WS-triggered refresh (FR-009)
- [ ] T034 [US3] Verify manual refresh bypasses all caches and triggers full board data reload in `solune/frontend/src/hooks/useBoardRefresh.ts` — confirm `requestBoardReload()` sends `refresh=true` to backend, cancels pending debounced reloads, and the board data query refetches with fresh data (FR-006, SC-009)
- [ ] T035 [US3] Verify board data query stale time and auto-refresh interval alignment in `solune/frontend/src/hooks/useProjectBoard.ts` — confirm board data query uses `STALE_TIME_SHORT` matching the 5-minute auto-refresh schedule, and query key `['board', 'data', projectId]` is stable

**Checkpoint**: Refresh-path separation is enforced end-to-end. Lightweight task updates never trigger expensive board data reloads. Manual refresh still performs full cache bypass. Auto-refresh coordinates correctly with WebSocket status.

---

## Phase 5: User Story 4 — Improved Frontend Board Rendering Performance (Priority: P2)

**Goal**: Reduce unnecessary re-renders and eliminate render-time performance bottlenecks in board and chat surfaces through derived-data memoization, callback stabilization, prop stabilization, and event listener throttling.

**Independent Test**: Profile board interactions (drag, scroll, hover) on a 50+ card board using browser DevTools. Confirm unnecessary re-renders are eliminated, derived computations are not repeated when data is unchanged, and hot event listeners are throttled.

### Implementation for User Story 4

- [ ] T036 [US4] Stabilize callback references passed to memoized `BoardColumn` children in `solune/frontend/src/pages/ProjectsPage.tsx` — wrap callbacks (e.g., `getGroups`, card click handlers, drag handlers) in `useCallback` with stable dependency arrays so `React.memo` on `BoardColumn` can skip re-renders when data is unchanged (FR-010, SC-005)
- [ ] T037 [P] [US4] Verify `useBoardControls` transform output referential stability in the hook used by `solune/frontend/src/pages/ProjectsPage.tsx` — confirm that `transformedData` from `useBoardControls` returns the same object reference when the underlying board data has not changed, preventing unnecessary downstream re-renders
- [ ] T038 [P] [US4] Verify `getGroups` callback reference stability in `solune/frontend/src/components/board/BoardColumn.tsx` — confirm the callback passed as a prop is stable across renders and does not break `React.memo` on child components
- [ ] T039 [P] [US4] Verify `React.memo` effectiveness on `IssueCard` in `solune/frontend/src/components/board/IssueCard.tsx` — confirm `useMemo` for labels, pipeline/agent parsing, and body snippet are correctly dependency-arrayed and that all props passed to `IssueCard` are referentially stable
- [ ] T040 [P] [US4] Verify page-level `useMemo` correctness for `heroStats`, `rateLimitState`, and `syncStatusLabel` in `solune/frontend/src/pages/ProjectsPage.tsx` — confirm dependency arrays are minimal and correct, and that these memoized values do not recompute when unrelated state changes (FR-010, SC-005)
- [ ] T041 [P] [US4] Verify RAF-gated mousemove handler in `solune/frontend/src/components/chat/ChatPopup.tsx` — confirm resize/drag positioning listener uses `requestAnimationFrame` gating and does not fire continuously when idle (FR-011)
- [ ] T042 [P] [US4] Verify event listener patterns in `solune/frontend/src/components/agents/AddAgentModal.tsx` — confirm no hot positioning listeners exist (research found modal-based, not popover) and no throttling changes are needed

**Checkpoint**: Board rendering is optimized with stable callback references, proper memoization, and throttled event listeners. Board interactions (scroll, drag, hover) on 50+ card boards maintain >30 FPS with no perceptible jank.

---

## Phase 6: User Story 5 — Regression Test Coverage for Performance-Sensitive Paths (Priority: P3)

**Goal**: Extend existing test suites to cover the specific behaviors modified by optimization work, ensuring gains are preserved over time and regressions are caught before they reach production.

**Independent Test**: Run the extended test suites and confirm all new test cases pass, covering idle refresh suppression, cache hit/miss behavior, refresh-path separation, and render optimization guards.

### Implementation for User Story 5

- [ ] T043 [P] [US5] Extend cache TTL behavior tests in `solune/backend/tests/unit/test_cache.py` — add test cases for: cache hit returns data without API call within TTL, stale fallback activates on rate limit, hash comparison refreshes TTL without re-storing data (FR-004, FR-014, SC-002)
- [ ] T044 [P] [US5] Extend WebSocket change detection tests in `solune/backend/tests/unit/test_api_board.py` — add test cases for: hash unchanged → no refresh message sent, hash changed → refresh message sent, stale counter reaches limit → force refresh, counter resets after force refresh (FR-003, SC-001)
- [ ] T045 [P] [US5] Extend polling behavior tests in `solune/backend/tests/unit/test_copilot_polling.py` — add test cases for: polling does not trigger board data refetch, rate limit budget pauses polling at threshold, expensive operations skipped at skip threshold (SC-008)
- [ ] T046 [P] [US5] Extend real-time sync tests in `solune/frontend/src/hooks/useRealTimeSync.test.tsx` — add test cases for: each WebSocket message type (`task_update`, `task_created`, `status_changed`, `refresh`, `initial_data`) invalidates only tasks query, reconnection debounce prevents query storm (FR-007, FR-008, SC-003)
- [ ] T047 [P] [US5] Extend board refresh tests in `solune/frontend/src/hooks/useBoardRefresh.test.tsx` — add test cases for: auto-refresh paused when WS connected, auto-refresh resumes on WS disconnect, tab visibility pauses/resumes timer, manual refresh cancels debounced reloads (FR-009, SC-009)
- [ ] T048 [US5] Run full backend test suite to confirm zero regressions with `pytest tests/ -v --timeout=60` in `solune/backend/` (SC-006)
- [ ] T049 [US5] Run full frontend test suite to confirm zero regressions with `npm run test` in `solune/frontend/` (SC-006)
- [ ] T050 [US5] Run backend linting and type checks to confirm no new violations with `ruff check src tests && pyright src` in `solune/backend/`
- [ ] T051 [US5] Run frontend linting, type checks, and build to confirm no new violations with `npm run lint && npm run type-check && npm run build` in `solune/frontend/`

**Checkpoint**: All new regression tests pass. Full test suites confirm zero regressions. Linting and type checks pass. Performance-sensitive code paths are covered by automated tests that will catch future regressions.

---

## Phase 7: User Story 6 — Optional Second-Wave Optimization Plan (Priority: P3)

**Goal**: If first-pass optimizations do not meet performance targets (SC-001 through SC-010), produce a documented follow-on plan identifying structural changes for a second wave.

**Independent Test**: Review the follow-on plan document (if produced) and confirm it identifies specific structural changes, estimated effort, and the measurement thresholds that triggered its creation.

### Implementation for User Story 6

- [ ] T052 [US6] Re-measure backend idle API activity against baseline from T017 and compare against SC-001 (zero unnecessary idle calls) and SC-007 (≥50% reduction) targets
- [ ] T053 [P] [US6] Re-measure frontend render performance against baseline from T017 and compare against SC-004 (>30 FPS on 50+ cards) and SC-005 (≥30% re-render reduction) targets
- [ ] T054 [US6] If targets are NOT met: create follow-on plan at `specs/001-performance-review/second-wave-plan.md` documenting recommended structural changes — include board virtualization (if SC-004 fails), deeper service consolidation in GitHub projects service (if SC-007 fails), bounded cache policies, and request budget instrumentation (FR-015)
- [ ] T055 [US6] If targets ARE met: document success in baseline measurements file at `specs/001-performance-review/checklists/baseline-measurements.md` with after-values for all success criteria

**Checkpoint**: Performance targets are evaluated against measured baselines. Either targets are met and documented, or a follow-on plan is produced with specific next steps.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup that spans multiple user stories.

- [ ] T056 Run full manual end-to-end verification per `specs/001-performance-review/quickstart.md` Phase 3 checklist — WebSocket updates refresh task data quickly, fallback polling remains safe, manual refresh bypasses caches, board interactions remain responsive
- [ ] T057 [P] Verify refresh contract compliance by walking through each row of the query invalidation matrix in `specs/001-performance-review/contracts/refresh-contract.md` — confirm actual behavior matches documented contract for all 8 refresh sources
- [ ] T058 [P] Update baseline measurements document at `specs/001-performance-review/checklists/baseline-measurements.md` with final after-values for all success criteria (SC-001 through SC-010)
- [ ] T059 Run quickstart.md validation — execute all steps in `specs/001-performance-review/quickstart.md` to confirm the documented setup, implementation, and verification procedures are accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 Baseline (Phase 2)**: Depends on Setup completion — **BLOCKS all optimization work** (no code changes until baselines are captured)
- **US2 Backend API (Phase 3)**: Depends on US1 Baseline completion
- **US3 Refresh Path (Phase 4)**: Depends on US1 Baseline completion — can proceed in parallel with US2
- **US4 Frontend Render (Phase 5)**: Depends on US1 Baseline completion — can proceed in parallel with US2 and US3
- **US5 Regression Tests (Phase 6)**: Depends on US2, US3, and US4 completion (tests cover behaviors modified in those stories)
- **US6 Second-Wave Plan (Phase 7)**: Depends on US2, US3, US4, and US5 completion (requires re-measurement after all optimizations)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Baseline — blocks everything; no dependencies on other stories
- **US2 (P1)**: Backend API — depends on US1 baseline; independent of US3/US4
- **US3 (P2)**: Refresh Path — depends on US1 baseline; can run in parallel with US2
- **US4 (P2)**: Frontend Render — depends on US1 baseline; can run in parallel with US2 and US3
- **US5 (P3)**: Regression Tests — depends on US2, US3, US4 (tests cover modified behaviors)
- **US6 (P3)**: Second-Wave Plan — depends on US2, US3, US4, US5 (requires final measurement)

### Within Each User Story

- Tests (where included) MUST be written and FAIL before implementation
- Audit/verification tasks before code changes
- Backend changes before frontend changes (where cross-cutting)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002, T004, T005, T006 can all run in parallel with T001/T003
- **Phase 2 (US1)**: T008–T016 can all run in parallel after T007
- **Phase 3 (US2)**: T018–T021 (tests) can all run in parallel; T024–T026 can run in parallel
- **Phase 4 (US3)**: T027–T030 (tests) can all run in parallel
- **Phase 5 (US4)**: T037–T042 can all run in parallel
- **Phase 6 (US5)**: T043–T047 can all run in parallel
- **US2, US3, US4 can start in parallel** once US1 baseline is complete (different files, different domains)

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: "Add test for WebSocket hash-based change detection suppression in solune/backend/tests/unit/test_api_board.py"
Task: "Add test for board endpoint cache hit within TTL in solune/backend/tests/unit/test_api_board.py"
Task: "Add test for sub-issue cache reuse on non-manual refresh in solune/backend/tests/unit/test_api_board.py"
Task: "Add test for fallback polling not triggering full board refetch in solune/backend/tests/unit/test_copilot_polling.py"

# Launch parallel verification tasks after hash detection is wired:
Task: "Verify board endpoint returns cached data within TTL in solune/backend/src/api/board.py"
Task: "Verify sub-issue cache entries are preserved on non-manual board requests in solune/backend/src/api/board.py"
Task: "Verify rate limit exhaustion returns stale cached data gracefully in solune/backend/src/services/cache.py"
```

## Parallel Example: User Story 4

```bash
# Launch all frontend audit tasks together:
Task: "Verify useBoardControls transform output referential stability"
Task: "Verify getGroups callback reference stability in BoardColumn.tsx"
Task: "Verify React.memo effectiveness on IssueCard in IssueCard.tsx"
Task: "Verify page-level useMemo correctness in ProjectsPage.tsx"
Task: "Verify RAF-gated mousemove handler in ChatPopup.tsx"
Task: "Verify event listener patterns in AddAgentModal.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Complete Phase 1: Setup (verify tooling)
2. Complete Phase 2: US1 Baseline (capture before-state) — **CRITICAL GATE**
3. Complete Phase 3: US2 Backend API (highest-value backend fix)
4. **STOP and VALIDATE**: Re-measure idle API calls against baseline. If SC-001 and SC-007 are met, the highest-value backend optimization is confirmed.

### Incremental Delivery

1. Setup + US1 Baseline → Measurement baseline established
2. Add US2 Backend API → Test independently → Validate idle API reduction (MVP!)
3. Add US3 Refresh Path → Test independently → Validate refresh separation
4. Add US4 Frontend Render → Test independently → Validate render performance
5. Add US5 Regression Tests → Full test coverage confirmed
6. Add US6 Second-Wave Plan → Final measurement and documentation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + US1 Baseline together
2. Once Baseline is done:
   - Developer A: US2 (Backend API) — `solune/backend/src/api/projects.py`, `board.py`
   - Developer B: US3 (Refresh Path) — `solune/frontend/src/hooks/useRealTimeSync.ts`, `useBoardRefresh.ts`
   - Developer C: US4 (Frontend Render) — `solune/frontend/src/pages/ProjectsPage.tsx`, `BoardColumn.tsx`, `IssueCard.tsx`
3. Once US2–US4 complete: US5 Regression Tests (can be split across backend/frontend)
4. Final: US6 measurement and documentation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are REQUIRED for this feature (FR-012, FR-013, SC-010)
- Verify tests fail before implementing (TDD approach for US2 and US3 test tasks)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new dependencies allowed in first pass (plan constraint)
- No board virtualization unless baselines prove need (plan constraint)
- Preserve existing 300s board cache TTL and 30s WebSocket check interval (plan constraint)
