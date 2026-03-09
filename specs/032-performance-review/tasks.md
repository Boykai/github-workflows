# Tasks: Performance Review

**Input**: Design documents from `/specs/032-performance-review/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/internal-contracts.md ✅, quickstart.md ✅

**Tests**: Spec explicitly requires regression test coverage (FR-014, User Story 7). Existing test suites serve as regression guardrails; extension is limited to areas directly affected by optimization changes.

**Organization**: Tasks are grouped by user story (US1–US7) to enable independent implementation and testing. User stories map to spec.md priorities (P1–P3). Tests are included per spec requirement.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/` (Python/FastAPI), `frontend/src/` (TypeScript/React)
- **Backend tests**: `backend/tests/unit/`
- **Frontend tests**: colocated with source (`frontend/src/hooks/*.test.tsx`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development environment, confirm build/test baselines are green before any optimization work begins. No code changes in this phase.

- [ ] T001 Install backend dependencies and verify backend test baseline (`cd backend && python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v`)
- [ ] T002 [P] Install frontend dependencies and verify frontend build baseline (`cd frontend && npm install && npm run build`)
- [ ] T003 [P] Verify frontend lint, type-check, and test baseline (`cd frontend && npm run lint && npm run type-check && npm test`)
- [ ] T004 Document any pre-existing lint warnings, type errors, or test failures as baseline (do not fix — out of scope unless directly related to this feature)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify existing Spec 022 implementations are fully landed and establish the measurement protocol. These verifications MUST be complete before any optimization code changes begin.

**⚠️ CRITICAL**: No optimization work (user story phases) can begin until this phase confirms the current state.

- [ ] T005 Verify WebSocket hash-based change detection is implemented in `backend/src/api/projects.py` — confirm SHA-256 hash comparison in the WebSocket subscription handler (Lines ~375–388), confirm `last_sent_hash` is compared each 30-second cycle, and refresh messages are only sent when hash differs
- [ ] T006 [P] Verify board data cache TTL of 300 seconds is set in `backend/src/api/board.py` (Line ~359) — confirm cache key format `board_data:{project_id}` and TTL alignment with frontend 5-minute auto-refresh
- [ ] T007 [P] Verify sub-issue caching with 600s TTL is implemented in `backend/src/services/github_projects/service.py` (Lines ~4329–4382) — confirm `get_sub_issues()` checks `InMemoryCache` first with key `sub_issues:{owner}/{repo}#{issue_number}`
- [ ] T008 [P] Verify manual refresh (`refresh=true`) bypasses board cache and clears sub-issue caches in `backend/src/api/board.py` (Lines ~301–322)
- [ ] T009 [P] Verify frontend query invalidation decoupling in `frontend/src/hooks/useRealTimeSync.ts` (Lines ~64, 71, 83) — confirm WebSocket message handler only invalidates `['projects', projectId, 'tasks']` and does NOT invalidate board data query
- [ ] T010 [P] Verify reconnection debounce (2-second window) in `frontend/src/hooks/useRealTimeSync.ts` (Lines ~13–14, 59–63) — confirm `lastInvalidationRef` timestamp comparison prevents cascading invalidation on reconnect
- [ ] T011 [P] Verify refresh deduplication via `isRefreshingRef` in `frontend/src/hooks/useBoardRefresh.ts` (Lines ~67, 78, 105–106) — confirm concurrent refresh calls are deduplicated with manual refresh taking priority
- [ ] T012 [P] Verify rate-limit-aware adaptive polling in `backend/src/services/copilot_polling/polling_loop.py` (Lines ~384–438) — confirm consecutive idle detection, interval doubling, 8x max multiplier, and rate-limit thresholds at 50/200/100
- [ ] T013 Define repeatable measurement protocol for baseline capture: idle API call count over 5-minute window, board endpoint response time, sub-issue fetch count per board refresh, board initial render time, single-card rerender count, drag interaction fps, event handler invocation frequency — use tools documented in `specs/032-performance-review/quickstart.md` (backend logs, React DevTools Profiler, browser Network/Performance tabs)

**Checkpoint**: Spec 022 state confirmed, measurement protocol defined. Optimization work can now begin.

---

## Phase 3: User Story 1 — Baseline Performance Measurement (Priority: P1) 🎯 MVP

**Goal**: Capture current performance baselines across backend and frontend so improvements can be proven with data and regressions detected immediately.

**Independent Test**: Execute the measurement protocol defined in T013. Record all metrics. Confirm results are documented and reproducible by running the protocol twice and comparing values.

### Implementation for User Story 1

- [ ] T014 [US1] Capture backend baseline: start the application, open a project board, wait 5 minutes idle, count outbound API calls in backend logs — record `idle_api_call_count` metric
- [ ] T015 [P] [US1] Capture backend baseline: measure board endpoint response time and sub-issue fetch count per board refresh — record `board_endpoint_response_time_ms` and `sub_issue_fetch_count` metrics
- [ ] T016 [P] [US1] Capture frontend baseline: open React DevTools Profiler, load a board with 50+ cards, record initial render time — record `board_initial_render_time_ms` metric
- [ ] T017 [P] [US1] Capture frontend baseline: trigger a single-card update on a loaded board, count component re-renders — record `single_card_rerender_count` metric
- [ ] T018 [P] [US1] Capture frontend baseline: profile chat popup drag and popover scroll/resize — record `drag_fps` and `event_handler_invocations_per_sec` metrics
- [ ] T019 [US1] Document all baseline measurements in a before/after comparison table for use in Phase verification (store alongside quickstart.md or in measurement notes)

**Checkpoint**: All baseline metrics recorded. Before/after comparison framework established. Optimization phases can now proceed with measurable targets.

---

## Phase 4: User Story 2 — Idle Board Viewing Without Excessive API Calls (Priority: P1)

**Goal**: Ensure an idle board (no active changes) makes no more than 2 outbound API calls in a 5-minute window (excluding initial load). Change detection must suppress redundant refreshes.

**Independent Test**: Open a board with no pending changes, wait 5 minutes, count outbound API calls. Verify count ≤ 2. Verify fallback polling (when WebSocket is down) also does not trigger expensive board refreshes when data is unchanged.

### Tests for User Story 2

- [ ] T020 [P] [US2] Add test in `backend/tests/unit/test_api_board.py` verifying that board endpoint returns cached data when called within TTL window without `refresh=true`
- [ ] T021 [P] [US2] Add test in `frontend/src/hooks/useRealTimeSync.test.tsx` verifying that fallback polling invalidation does NOT trigger board data query invalidation — only tasks query key is invalidated

### Implementation for User Story 2

- [ ] T022 [US2] Review and fix (if needed) fallback polling in `frontend/src/hooks/useRealTimeSync.ts` (Lines ~100–112) — ensure the 30-second `setInterval` fallback only invalidates `['projects', projectId, 'tasks']` and does not cascade to board data queries
- [ ] T023 [P] [US2] Review and fix (if needed) WebSocket subscription cycle in `backend/src/api/projects.py` — ensure no unnecessary API calls are made when `last_sent_hash` matches current data hash (no-change cycles should be lightweight, no outbound GitHub API calls)
- [ ] T024 [P] [US2] Review and fix (if needed) polling loop in `backend/src/services/copilot_polling/polling_loop.py` — ensure adaptive backoff properly reduces polling frequency during idle periods and does not trigger expensive board refreshes
- [ ] T025 [US2] Validate idle API activity: start application, open board, wait 5 minutes idle, count API calls — confirm ≤ 2 calls (SC-001: ≥50% reduction from baseline)

**Checkpoint**: Idle board viewing confirmed safe. No redundant API calls during idle. Fallback polling does not trigger expensive refreshes.

---

## Phase 5: User Story 3 — Fast and Coherent Board Refresh on Real-Time Updates (Priority: P1)

**Goal**: Lightweight task updates (field changes via real-time channels or polling) stay decoupled from the expensive full board data query. Only manual refresh triggers a full board data re-fetch.

**Independent Test**: Make a single task change on one client, observe update latency and network activity on a second client. Verify lightweight update completes in < 1 second without full board data re-fetch. Verify manual refresh still performs full board fetch with cache bypass.

### Tests for User Story 3

- [ ] T026 [P] [US3] Add test in `frontend/src/hooks/useRealTimeSync.test.tsx` verifying that WebSocket `task_update` message invalidates tasks query only — board data query key is never passed to `invalidateQueries`
- [ ] T027 [P] [US3] Add test in `frontend/src/hooks/useBoardRefresh.test.tsx` verifying that manual refresh calls board API with `refresh=true` parameter and resets auto-refresh timer

### Implementation for User Story 3

- [ ] T028 [US3] Review and fix (if needed) WebSocket message handlers in `frontend/src/hooks/useRealTimeSync.ts` — ensure `refresh`, `task_update`, `task_created`, `status_changed` messages only invalidate `['projects', projectId, 'tasks']` and `['blocking-queue', projectId]`, never board data query
- [ ] T029 [P] [US3] Review and fix (if needed) auto-refresh in `frontend/src/hooks/useBoardRefresh.ts` — ensure auto-refresh uses `invalidateQueries` (allows backend cache hit) while manual refresh uses direct fetch with `refresh=true` + `setQueryData`
- [ ] T030 [US3] Review and fix (if needed) refresh policy coherence — verify all four refresh sources (WebSocket, fallback polling, auto-refresh, manual refresh) follow the Refresh Policy Matrix defined in `specs/032-performance-review/data-model.md` (FR-015)
- [ ] T031 [US3] Validate refresh behavior: trigger a single-card update via WebSocket, confirm update appears in < 1 second (SC-002), confirm no full board data re-fetch in network tab

**Checkpoint**: Real-time updates are fast and lightweight. Manual refresh still performs full cache bypass. Refresh policy is coherent across all sources.

---

## Phase 6: User Story 4 — Sub-Issue Cache Reduces Redundant Fetches (Priority: P2)

**Goal**: Sub-issue data is reused from cache across automatic board refreshes. Manual refresh invalidates sub-issue caches. Partially cached sub-issues result in only uncached entries being fetched.

**Independent Test**: Load a board with sub-issues, observe initial sub-issue API call count, trigger an automatic refresh, confirm zero additional sub-issue API calls from cache. Trigger manual refresh, confirm all sub-issue data is re-fetched.

### Tests for User Story 4

- [ ] T032 [P] [US4] Add test in `backend/tests/unit/test_cache.py` verifying that sub-issue cache entries with key `sub_issues:{owner}/{repo}#{issue_number}` are served from cache within 600s TTL window
- [ ] T033 [P] [US4] Add test in `backend/tests/unit/test_api_board.py` verifying that manual refresh (`refresh=true`) clears all sub-issue cache entries for the board's items

### Implementation for User Story 4

- [ ] T034 [US4] Review and fix (if needed) `get_sub_issues()` in `backend/src/services/github_projects/service.py` — confirm cache lookup uses correct key format, TTL is 600s, cache miss fetches from API and stores result, partial cache scenario fetches only missing entries
- [ ] T035 [P] [US4] Review and fix (if needed) sub-issue cache invalidation in `backend/src/api/board.py` — confirm manual refresh iterates all board items and deletes per-issue sub-issue cache entries
- [ ] T036 [US4] Validate sub-issue caching: load board with sub-issues, count sub-issue API calls on initial load, trigger auto-refresh, confirm zero sub-issue API calls — confirm ≥80% reduction (SC-003)

**Checkpoint**: Sub-issue caching confirmed effective. Manual refresh bypasses cache. Partial cache scenario handled correctly.

---

## Phase 7: User Story 5 — Responsive Board Interactions on Medium-to-Large Boards (Priority: P2)

**Goal**: Reduce unnecessary re-renders and derived-data recomputation on boards with 50–200 cards. Single-card updates cause ≤ 3 component re-renders. Board initial render time is not degraded.

**Independent Test**: Profile a board with 100+ cards. Trigger a single-card status change and count re-renders (target: ≤ 3). Measure board initial render time (target: within 10% of baseline). Drag a card and confirm ≥ 30 fps.

### Implementation for User Story 5

- [ ] T037 [US5] Wrap derived-data computations (column stats, sorted/filtered lists, aggregated counts) in `useMemo` with appropriate dependency arrays in `frontend/src/pages/ProjectsPage.tsx` — prevent recomputation on unrelated state changes (FR-010)
- [ ] T038 [P] [US5] Stabilize callbacks passed to `BoardColumn` and `IssueCard` via `useCallback` in `frontend/src/pages/ProjectsPage.tsx` — ensure `React.memo` on child components is effective by preventing new function references on every render
- [ ] T039 [P] [US5] Verify `React.memo` on `BoardColumn` in `frontend/src/components/board/BoardColumn.tsx` (Line ~20) is effective — confirm props are stable (no inline objects/functions) and single-card updates only re-render the affected column
- [ ] T040 [P] [US5] Verify `React.memo` on `IssueCard` in `frontend/src/components/board/IssueCard.tsx` (Line ~108) is effective — confirm props are stable and single-card updates only re-render the affected card
- [ ] T041 [US5] Verify `staleTime` configuration on board data query in `frontend/src/hooks/useProjectBoard.ts` — confirm `staleTime` is set appropriately (60s for board data, 15 min for project list) to prevent unnecessary background refetches
- [ ] T042 [US5] Run `npm run type-check && npm run lint && npm test` in `frontend/` to verify render optimization changes compile and pass all checks
- [ ] T043 [US5] Validate render optimization: profile board with 100+ cards, trigger single-card update, count re-renders — confirm ≤ 3 (SC-005). Measure initial render time — confirm within 10% of baseline (SC-004)

**Checkpoint**: Board rendering is optimized. Derived data is memoized. Callbacks are stable. Single-card updates cause minimal re-renders. No render time regression.

---

## Phase 8: User Story 6 — Chat and Popover Interactions Without Performance Degradation (Priority: P3)

**Goal**: Throttle event listeners on AddAgentPopover positioning to prevent excessive layout recalculation. ChatPopup already uses RAF gating (no changes needed per research R5).

**Independent Test**: Open an agent popover, rapidly scroll/resize the viewport, confirm smooth repositioning without jank. Profile event handler invocations — confirm they fire at most once per animation frame. Verify chat popup drag maintains ≥ 30 fps.

### Implementation for User Story 6

- [ ] T044 [US6] Add `requestAnimationFrame` gating to `updatePosition()` in `frontend/src/components/agents/AddAgentPopover.tsx` (Lines ~72–83) — wrap `scroll` and `resize` event handlers with RAF guard (same pattern as `ChatPopup.tsx` Lines ~97–113) to prevent `getBoundingClientRect()` calls more than once per frame
- [ ] T045 [US6] Add RAF cleanup in `AddAgentPopover.tsx` — cancel pending `requestAnimationFrame` on unmount or `isOpen` change via `cancelAnimationFrame` in the effect cleanup function
- [ ] T046 [US6] Verify ChatPopup drag performance in `frontend/src/components/chat/ChatPopup.tsx` — confirm existing RAF gating is correct (`if (rafId) return` pattern on `onMouseMove`, RAF cancelled on `onMouseUp`), no changes needed (research R5 confirmation)
- [ ] T047 [US6] Run `npm run type-check && npm run lint && npm test` in `frontend/` to verify event listener changes compile and pass all checks
- [ ] T048 [US6] Validate event listener optimization: profile AddAgentPopover scroll/resize — confirm `updatePosition()` fires at most once per frame. Profile chat popup drag — confirm ≥ 30 fps (SC-006)

**Checkpoint**: Event listeners are throttled. Popover repositioning is smooth. Chat drag maintains target fps. No jank during interactions.

---

## Phase 9: User Story 7 — Regression-Safe Optimization with Test Coverage (Priority: P2)

**Goal**: Ensure all optimization changes are covered by regression tests. All existing tests pass. New tests cover changed behavior. Before/after measurements confirm improvements.

**Independent Test**: Run full backend and frontend test suites. All tests pass. New tests for changed behavior exist and are green. Before/after measurement comparison shows target improvements.

### Tests for User Story 7

- [ ] T049 [P] [US7] Add test in `backend/tests/unit/test_cache.py` verifying cache TTL expiration behavior — confirm entries are evicted after TTL and subsequent requests fetch fresh data
- [ ] T050 [P] [US7] Add test in `frontend/src/hooks/useRealTimeSync.test.tsx` verifying reconnection debounce — confirm that rapid WebSocket reconnections within 2-second window do not produce cascading task query invalidations
- [ ] T051 [P] [US7] Add test in `frontend/src/hooks/useBoardRefresh.test.tsx` verifying page visibility interaction — confirm auto-refresh timer pauses when tab is hidden and resumes (with staleness check) when tab becomes visible

### Implementation for User Story 7

- [ ] T052 [US7] Run full backend test suite (`cd backend && python -m pytest tests/ -v`) — confirm all existing and new tests pass (SC-007)
- [ ] T053 [P] [US7] Run full frontend test suite (`cd frontend && npm test`) — confirm all existing and new tests pass (SC-007)
- [ ] T054 [US7] Run backend linting and type-checking (`cd backend && ruff check src/ && pyright src/`) — confirm no new issues introduced
- [ ] T055 [P] [US7] Run frontend linting and type-checking (`cd frontend && npm run lint && npm run type-check`) — confirm no new issues introduced
- [ ] T056 [US7] Recapture all baseline metrics using the same measurement protocol from T013–T019 — document post-optimization values in before/after comparison table (SC-008)
- [ ] T057 [US7] Validate all success criteria against before/after measurements: SC-001 (≥50% idle API reduction), SC-002 (< 1s single-card update), SC-003 (≥80% sub-issue API reduction), SC-004 (render time within 10% of baseline), SC-005 (≤3 re-renders per card update), SC-006 (≥30 fps drag), SC-007 (no existing tests broken — validated by T052/T053), SC-008 (before/after measurements documented — validated by T056), SC-009 (polling no full-board refresh on unchanged data), SC-010 (manual refresh bypasses all caches)

**Checkpoint**: All tests green. All success criteria validated with measurements. Regression safety confirmed.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup across all user stories

- [ ] T058 Perform manual end-to-end verification: WebSocket updates refresh task data quickly, fallback polling is safe, manual refresh bypasses caches, board interactions are responsive, chat popup drag is smooth
- [ ] T059 [P] Review all modified files for consistency — ensure no dead code, no debug logging left behind, no TODO comments without tracking issues
- [ ] T060 [P] Verify repository resolution deduplication in `backend/src/api/workflow.py` — confirm it uses shared `utils.resolve_repository` and does not duplicate resolution logic (FR-010 cross-cutting concern)
- [ ] T061 Run `specs/032-performance-review/quickstart.md` verification steps end-to-end to confirm all phases pass
- [ ] T062 Document any remaining items for the optional second-wave work (Phase 4 from the issue): board virtualization, deeper service decomposition, bounded cache policies, stronger instrumentation — if first-pass measurements show they are needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all optimization work
- **User Story 1 — Baselines (Phase 3)**: Depends on Foundational — BLOCKS all optimization code changes
- **User Stories 2, 3 (Phases 4, 5)**: Depend on Baselines (Phase 3) — can run in parallel with each other
- **User Story 4 (Phase 6)**: Depends on Baselines (Phase 3) — can run in parallel with Phases 4 and 5
- **User Story 5 (Phase 7)**: Depends on Baselines (Phase 3) — can run in parallel with Phases 4, 5, and 6
- **User Story 6 (Phase 8)**: Depends on Baselines (Phase 3) — can run in parallel with Phases 4–7
- **User Story 7 — Regression (Phase 9)**: Depends on ALL optimization phases (4–8) being complete
- **Polish (Phase 10)**: Depends on Phase 9

### User Story Dependencies

- **US1 (Baselines)**: Depends on Foundational (Phase 2) — BLOCKS all other stories
- **US2 (Idle API)**: Depends on US1 baselines — can run in parallel with US3, US4, US5, US6
- **US3 (Refresh Path)**: Depends on US1 baselines — can run in parallel with US2, US4, US5, US6
- **US4 (Sub-Issue Cache)**: Depends on US1 baselines — can run in parallel with US2, US3, US5, US6
- **US5 (Render Optimization)**: Depends on US1 baselines — can run in parallel with US2, US3, US4, US6
- **US6 (Event Listeners)**: Depends on US1 baselines — can run in parallel with US2, US3, US4, US5
- **US7 (Regression Coverage)**: Depends on US2, US3, US4, US5, US6 all being complete

### Within Each User Story

- Tests (where included) SHOULD be written first to define expected behavior
- Verification and review tasks before code changes (confirm current state)
- Code changes after review
- Validation measurement after code changes
- Story complete before contributing to Phase 9 verification

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational verification tasks marked [P] can run in parallel (within Phase 2)
- Once Baselines (Phase 3) are complete, US2–US6 can start in parallel (if team capacity allows)
- Backend stories (US2, US4) can proceed independently from frontend stories (US3, US5, US6)
- All test tasks marked [P] within a story can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2 (Idle API)

```bash
# Launch tests for US2 in parallel:
Task T020: "Add board cache test in backend/tests/unit/test_api_board.py"
Task T021: "Add fallback polling test in frontend/src/hooks/useRealTimeSync.test.tsx"

# Launch implementation reviews in parallel:
Task T023: "Review WebSocket subscription in backend/src/api/projects.py"
Task T024: "Review polling loop in backend/src/services/copilot_polling/polling_loop.py"
```

## Parallel Example: User Story 5 (Render Optimization)

```bash
# Launch parallel implementation:
Task T038: "Stabilize callbacks with useCallback in frontend/src/pages/ProjectsPage.tsx"
Task T039: "Verify React.memo on BoardColumn in frontend/src/components/board/BoardColumn.tsx"
Task T040: "Verify React.memo on IssueCard in frontend/src/components/board/IssueCard.tsx"
```

## Parallel Example: Cross-Story Backend + Frontend

```bash
# Backend stories (one developer):
Phase 4 (US2): Idle API fixes — backend/src/api/projects.py, polling_loop.py
Phase 6 (US4): Sub-issue cache — backend/src/services/github_projects/service.py, board.py

# Frontend stories (another developer):
Phase 5 (US3): Refresh path — frontend/src/hooks/useRealTimeSync.ts, useBoardRefresh.ts
Phase 7 (US5): Render optimization — frontend/src/pages/ProjectsPage.tsx, BoardColumn.tsx, IssueCard.tsx
Phase 8 (US6): Event listeners — frontend/src/components/agents/AddAgentPopover.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (verify Spec 022 state)
3. Complete Phase 3: User Story 1 (capture baselines)
4. **STOP and VALIDATE**: Baselines documented and reproducible
5. Baselines enable data-driven decisions for remaining stories

### Incremental Delivery

1. Complete Setup + Foundational + Baselines → Measurement framework ready
2. Add User Story 2 (Idle API) → Validate idle API reduction ≥ 50% → Backend safe
3. Add User Story 3 (Refresh Path) → Validate coherent refresh policy → Real-time safe
4. Add User Story 4 (Sub-Issue Cache) → Validate ≥ 80% sub-issue call reduction → Cache effective
5. Add User Story 5 (Render Optimization) → Validate ≤ 3 re-renders per card update → UI responsive
6. Add User Story 6 (Event Listeners) → Validate ≥ 30 fps drag → Interactions smooth
7. Add User Story 7 (Regression) → Full test pass + before/after measurements → Ship-ready
8. Each story adds measurable value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Baselines together (Phases 1–3)
2. Once baselines are captured:
   - **Backend developer**: US2 (Idle API) → US4 (Sub-Issue Cache)
   - **Frontend developer**: US3 (Refresh Path) → US5 (Render Optimization) → US6 (Event Listeners)
3. Both developers converge for US7 (Regression Coverage) and Phase 10 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Baseline measurement (US1) is mandatory before any optimization code changes
- All optimization changes are targeted edits to existing files — no new modules or dependencies
- Verify tests fail/pass appropriately before and after changes
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- If first-pass measurements show targets are not met, prepare second-wave plan (T062) per Phase 4 of the issue
- Deferred from first pass: board virtualization, service decomposition, new dependencies, architectural rewrites
