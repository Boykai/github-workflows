# Tasks: Performance Review

**Input**: Design documents from `/specs/027-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Regression tests are required per FR-012. New unit tests are added only for areas directly modified by optimization changes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend tests: `backend/tests/unit/`
- Frontend tests: `frontend/src/hooks/` (co-located test files)

---

## Phase 1: Setup (Spec 022 Audit)

**Purpose**: Confirm current backend implementation state against Spec 022 before making changes. Prevents redoing completed work and identifies remaining gaps.

- [ ] T001 Audit Spec 022 implementation state by reviewing backend/src/api/projects.py (WebSocket hash-based change detection), backend/src/api/board.py (board cache TTL and sub-issue clear on manual refresh), backend/src/services/cache.py (TTL configuration), and backend/src/services/copilot_polling/polling_loop.py (adaptive backoff and rate-limit pre-checks). Document confirmed items and remaining gaps.
- [ ] T002 [P] Review frontend refresh paths by inspecting frontend/src/hooks/useRealTimeSync.ts (WebSocket and fallback polling invalidation targets), frontend/src/hooks/useBoardRefresh.ts (auto-refresh timer and manual refresh flow), and frontend/src/hooks/useProjectBoard.ts (board query configuration). Identify where task-only updates currently invalidate board data.

---

## Phase 2: Foundational (Baseline Capture)

**Purpose**: Capture pre-optimization performance baselines. All optimization work is blocked until baselines are recorded so improvements can be proven, not assumed.

**⚠️ CRITICAL**: No optimization code changes can begin until this phase is complete

- [ ] T003 Capture backend baseline measurements: idle API call count over 5 minutes, per-refresh API call count with and without warm sub-issue cache. Follow measurement protocol in specs/027-performance-review/quickstart.md. Record results in the Post-Optimization Comparison Template.
- [ ] T004 [P] Capture frontend baseline measurements: component render count for a single-card status change on a 100-card board, chat drag frame rate, and fallback polling network activity. Follow measurement protocol in specs/027-performance-review/quickstart.md. Record results in the Post-Optimization Comparison Template.

**Checkpoint**: Baselines recorded — optimization implementation can now begin

---

## Phase 3: User Story 1 — Idle Board Viewing Without Excessive API Calls (Priority: P1) 🎯 MVP

**Goal**: Ensure an idle board with no active changes generates no more than 2 GitHub API calls over a 5-minute window (excluding initial load). WebSocket change detection suppresses no-change refresh messages; fallback polling does not trigger expensive board refreshes.

**Independent Test**: Open a board with no pending changes. Monitor backend logs for 5 minutes. Count outbound GitHub API calls — must be ≤2.

### Implementation for User Story 1

- [ ] T005 [US1] Verify and tighten WebSocket subscription refresh logic to confirm no refresh message is sent when task data hash is unchanged in backend/src/api/projects.py. Ensure `last_sent_hash` comparison gates all outbound refresh messages.
- [ ] T006 [P] [US1] Guard polling loop against triggering board data refreshes when polled data is unchanged from previous cycle in backend/src/services/copilot_polling/polling_loop.py. Ensure adaptive backoff is respected and idle cycles do not trigger downstream board endpoint calls.
- [ ] T007 [P] [US1] Add regression tests for idle WebSocket and polling behavior: verify no-change hash suppresses refresh, verify adaptive backoff under idle conditions, verify rate-limit pre-checks prevent unnecessary API calls in backend/tests/unit/test_copilot_polling.py

**Checkpoint**: Idle board API consumption meets ≤2 calls/5 min target

---

## Phase 4: User Story 2 — Fast and Coherent Board Refresh on Real-Time Updates (Priority: P1)

**Goal**: Lightweight task updates (WebSocket and polling) refresh only the tasks query without triggering the expensive board data query. Manual refresh bypasses all caches with highest priority. Reconnection does not cascade invalidations.

**Independent Test**: Make a single task change on one client. On a second client, verify the update appears within 30 seconds, the board data endpoint is NOT called (only tasks query), and no cascade of invalidations occurs.

### Implementation for User Story 2

- [ ] T008 [US2] Decouple WebSocket task update messages from board data query invalidation in frontend/src/hooks/useRealTimeSync.ts. On receiving a `refresh` type message, invalidate only `['projects', projectId, 'tasks']` — do NOT invalidate `['board', 'data', projectId]`.
- [ ] T009 [US2] Add reconnection debounce guard in frontend/src/hooks/useRealTimeSync.ts. On WebSocket reconnection (`initial_data` message), debounce invalidation to at most once per reconnection cycle (2-second window) targeting only the tasks query.
- [ ] T010 [US2] Ensure fallback polling path only invalidates tasks query `['projects', projectId, 'tasks']` and does NOT invalidate board data in frontend/src/hooks/useRealTimeSync.ts. Verify auto-refresh timer reset is called on polling updates.
- [ ] T011 [US2] Implement manual refresh priority in frontend/src/hooks/useBoardRefresh.ts: call `queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] })` before initiating manual fetch with `refresh=true`. Ensure auto-refresh timer resets after manual refresh completes.
- [ ] T012 [US2] Ensure auto-refresh timer resets on any data update source (WebSocket, polling, manual) to maintain 5-minute window from last update in frontend/src/hooks/useBoardRefresh.ts per refresh-contract.md.
- [ ] T013 [P] [US2] Extend WebSocket and polling invalidation tests in frontend/src/hooks/useRealTimeSync.test.tsx: verify task-only invalidation on refresh messages, verify no board data invalidation, verify reconnection debounce limits invalidation to once per cycle.
- [ ] T014 [P] [US2] Extend manual refresh and timer tests in frontend/src/hooks/useBoardRefresh.test.tsx: verify cancelQueries is called before manual fetch, verify timer resets on all update sources, verify manual refresh takes priority over in-progress auto-refresh.

**Checkpoint**: Task updates are decoupled from board query; manual refresh has priority; reconnection is guarded

---

## Phase 5: User Story 4 — Sub-Issue Cache Reduces Redundant Fetches (Priority: P2)

**Goal**: Automatic (non-manual) board refreshes serve sub-issue data from cache, reducing sub-issue API calls by ≥80%. Manual refresh clears sub-issue caches and fetches fresh data.

**Independent Test**: Load a board with sub-issues. Wait for cache to warm. Trigger an automatic refresh (non-manual) and verify zero sub-issue API calls in backend logs. Trigger a manual refresh and verify sub-issue cache is cleared and fresh data is fetched.

### Implementation for User Story 4

- [ ] T015 [US4] Add cache-check gate before per-issue sub-issue REST calls in the board data fetch path in backend/src/services/github_projects/service.py. For each issue: check `cache.get("sub_issues:{issue_node_id}")` — on HIT, use cached data; on MISS, fetch from GitHub and `cache.set()` with 600s TTL.
- [ ] T016 [P] [US4] Verify sub-issue cache TTL is configured at 600 seconds (2x board data TTL) in backend/src/services/cache.py. Confirm the TTL constant is used consistently across all sub-issue cache operations.
- [ ] T017 [US4] Verify manual refresh path in backend/src/api/board.py clears all sub-issue cache entries for the project before fetching fresh data. Confirm the `refresh=true` query parameter triggers cache bypass and sub-issue cache invalidation.
- [ ] T018 [P] [US4] Add sub-issue cache hit/miss regression tests in backend/tests/unit/test_cache.py: verify warm cache returns data without API calls, verify expired TTL triggers fresh fetch, verify cache.set stores data with correct TTL.
- [ ] T019 [P] [US4] Add board refresh with warm sub-issue cache tests in backend/tests/unit/test_api_board.py: verify automatic refresh uses cached sub-issues (zero sub-issue API calls), verify manual refresh clears sub-issue cache and fetches fresh data.

**Checkpoint**: Sub-issue cache hit rate ≥80% on automatic refresh; manual refresh bypasses cache

---

## Phase 6: User Story 3 — Responsive Board Interactions on Medium-to-Large Boards (Priority: P2)

**Goal**: A single-card status change on a 100-card board causes ≤3 component re-renders (card + column + board container). Drag interactions maintain ≥30 fps. Inline sorting and derived state are memoized.

**Independent Test**: Profile a 100-card board in React DevTools. Change a single card status and verify only 3 components re-render. Drag a card between columns and verify ≥30 fps in Chrome Performance tab.

### Implementation for User Story 3

- [ ] T020 [P] [US3] Wrap BoardColumn component export with React.memo() using default shallow comparison in frontend/src/components/board/BoardColumn.tsx. No custom comparator needed — TanStack Query returns new references only when data changes.
- [ ] T021 [P] [US3] Wrap IssueCard component export with React.memo() using default shallow comparison in frontend/src/components/board/IssueCard.tsx. Ensure card props are stable across parent re-renders.
- [ ] T022 [US3] Wrap inline sorting, progress calculation, and rate-limit state derivation in useMemo with appropriate dependency arrays in frontend/src/pages/ProjectsPage.tsx. Stabilize `sortedBoardData`, `progress`, and `rateLimitInfo` across re-renders.
- [ ] T023 [US3] Stabilize event handler props with useCallback in frontend/src/pages/ProjectsPage.tsx: wrap `handleCardClick`, `handleProjectSwitch`, and other callback props passed to board components. Include appropriate dependency arrays.
- [ ] T024 [US3] Review board query invalidation strategy in frontend/src/hooks/useProjectBoard.ts to confirm staleTime and invalidation behavior limit unnecessary refetches that would trigger full board re-renders.

**Checkpoint**: Single-card change re-renders ≤3 components; board interactions remain smooth

---

## Phase 7: User Story 5 — Chat and Popover Interactions Without Performance Degradation (Priority: P3)

**Goal**: Chat popup drag maintains ≥30 fps with throttled position updates. Popover repositioning does not trigger excessive re-renders of unrelated components.

**Independent Test**: Profile chat drag in Chrome Performance tab — verify ≥30 fps. Open an agent popover and resize/scroll viewport — verify no excessive re-renders in React DevTools.

### Implementation for User Story 5

- [ ] T025 [P] [US5] Add requestAnimationFrame gating to the drag mousemove handler in frontend/src/components/chat/ChatPopup.tsx. Only process position updates once per animation frame during active drag — prevents per-pixel event handler execution.
- [ ] T026 [P] [US5] Memoize updatePosition callback with useCallback in frontend/src/components/agents/AddAgentPopover.tsx. Stabilize the callback reference so scroll/resize listeners are not removed and re-added on every render.

**Checkpoint**: Drag and popover interactions are throttled and responsive

---

## Phase 8: Verification & Polish

**Purpose**: Run full test suites, capture post-optimization measurements, confirm zero regressions, and document results.

- [ ] T027 [P] Run backend verification suite: `ruff check src/`, `pyright src/`, and `pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v` followed by full `pytest --tb=short` per specs/027-performance-review/quickstart.md
- [ ] T028 [P] Run frontend verification suite: `npx eslint src/`, `npx tsc --noEmit`, `npx vitest run`, and `npm run build` per specs/027-performance-review/quickstart.md
- [ ] T029 Run post-optimization measurements using the same protocol as Phase 2 baseline. Complete the before/after comparison table in specs/027-performance-review/quickstart.md with improvement percentages for each metric.
- [ ] T030 Validate zero test regressions: confirm all pre-existing backend and frontend tests pass after optimization changes. Document any test modifications and their justification.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all optimization work
- **US1 (Phase 3)**: Depends on Foundational — backend-only, can start first
- **US2 (Phase 4)**: Depends on Foundational — frontend-only, can run in parallel with US1
- **US4 (Phase 5)**: Depends on Foundational — backend-only, can run in parallel with US2
- **US3 (Phase 6)**: Depends on Foundational — frontend-only, can run in parallel with US4
- **US5 (Phase 7)**: Depends on Foundational — frontend-only, can run in parallel with US3
- **Verification (Phase 8)**: Depends on ALL user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Backend-only. No dependencies on other stories. Can start immediately after Foundational.
- **US2 (P1)**: Frontend-only. No dependencies on other stories. Can run in parallel with US1.
- **US4 (P2)**: Backend-only. Independent of US1 but may build on same cache infrastructure. Can run in parallel with US2.
- **US3 (P2)**: Frontend-only. Benefits from US2 refresh-path changes being in place (fewer invalidations = fewer re-renders) but is independently testable.
- **US5 (P3)**: Frontend-only. Fully independent of all other stories.
- **US6 (P1)**: Covered by Phase 1 (Setup) + Phase 2 (Foundational) + Phase 8 (Verification). Not a separate implementation phase.

### Within Each User Story

- Backend changes before frontend changes (where applicable)
- Implementation tasks before test extension tasks
- Core changes before integration/verification
- Commit after each task or logical group

### Parallel Opportunities

- Phase 1: T001 ‖ T002 (backend audit ‖ frontend audit)
- Phase 2: T003 ‖ T004 (backend baseline ‖ frontend baseline)
- Phase 3 (US1): T006 ‖ T007 (polling guard ‖ regression tests)
- Phase 4 (US2): T013 ‖ T014 (WebSocket tests ‖ refresh tests)
- Phase 5 (US4): T016 ‖ T018 ‖ T019 (TTL verify ‖ cache tests ‖ board tests)
- Phase 6 (US3): T020 ‖ T021 (BoardColumn memo ‖ IssueCard memo)
- Phase 7 (US5): T025 ‖ T026 (ChatPopup throttle ‖ AddAgentPopover memo)
- Phase 8: T027 ‖ T028 (backend verify ‖ frontend verify)
- **Cross-story**: US1 (backend) ‖ US2 (frontend) — different codebases, zero overlap
- **Cross-story**: US4 (backend) ‖ US3 (frontend) — different codebases, zero overlap
- **Cross-story**: US3 ‖ US5 — different frontend files, no dependencies

---

## Parallel Example: User Story 1 (Backend)

```bash
# After T005 (WebSocket verification), launch in parallel:
Task: "Guard polling loop against board data refreshes in backend/src/services/copilot_polling/polling_loop.py"    # T006
Task: "Add idle WebSocket and polling regression tests in backend/tests/unit/test_copilot_polling.py"              # T007
```

## Parallel Example: User Story 3 (Frontend)

```bash
# Launch board component memoization in parallel (different files):
Task: "Wrap BoardColumn with React.memo in frontend/src/components/board/BoardColumn.tsx"    # T020
Task: "Wrap IssueCard with React.memo in frontend/src/components/board/IssueCard.tsx"        # T021

# Then sequentially (same file):
Task: "Wrap sorting/progress in useMemo in frontend/src/pages/ProjectsPage.tsx"              # T022
Task: "Stabilize handlers with useCallback in frontend/src/pages/ProjectsPage.tsx"           # T023
```

## Parallel Example: Cross-Story (Backend ‖ Frontend)

```bash
# Backend and frontend stories can proceed in parallel:
# Developer A (Backend):
Task: US1 — "Verify WebSocket change detection in backend/src/api/projects.py"               # T005
Task: US4 — "Add cache gate in backend/src/services/github_projects/service.py"              # T015

# Developer B (Frontend):
Task: US2 — "Decouple task updates from board query in frontend/src/hooks/useRealTimeSync.ts" # T008
Task: US3 — "Wrap BoardColumn with React.memo in frontend/src/components/board/BoardColumn.tsx" # T020
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (Spec 022 audit)
2. Complete Phase 2: Foundational (baseline capture)
3. Complete Phase 3: US1 — Idle board API reduction (backend)
4. Complete Phase 4: US2 — Refresh path decoupling (frontend)
5. **STOP and VALIDATE**: Measure idle API calls and refresh behavior against baselines
6. If targets met: deploy; if not: proceed to Phase 5+

### Incremental Delivery

1. Setup + Foundational → Baselines captured, Spec 022 audit complete
2. US1 + US2 → Backend API churn fixed + Frontend refresh decoupled → Measure (MVP!)
3. US4 → Sub-issue cache optimized → Measure per-refresh cost reduction
4. US3 → Board render optimized → Measure rerender count and frame rate
5. US5 → Chat/popover throttled → Measure drag frame rate
6. Verification → Full test suite pass + before/after comparison documented

### Parallel Team Strategy

With two developers (Backend + Frontend):

1. Team reviews Setup together (Phase 1)
2. Baselines captured together (Phase 2)
3. Once Foundational is done:
   - **Backend developer**: US1 (idle board) → US4 (sub-issue cache)
   - **Frontend developer**: US2 (refresh path) → US3 (render optimization) → US5 (chat/popover)
4. Verification together (Phase 8)

---

## Notes

- [P] tasks = different files, no dependencies — safe to execute in parallel
- [Story] label maps each task to its specific user story for traceability
- US6 (Baseline Measurement) is woven into Setup, Foundational, and Verification phases rather than being a standalone implementation phase
- Existing Spec 022 implementation is substantially complete — tasks focus on remaining gaps, not reimplementation
- All optimization improvements must be validated with before/after measurements using the protocol in quickstart.md
- Board virtualization, major service decomposition, and new dependencies are explicitly out of scope (deferred to potential Phase 4 per plan.md)
- Commit after each task or logical group; stop at any checkpoint to validate independently
