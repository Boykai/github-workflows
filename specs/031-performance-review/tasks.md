# Tasks: Performance Review

**Input**: Design documents from `/specs/031-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — spec.md requires regression test extension (FR-015) for cache behavior, WebSocket change detection, fallback polling, and board refresh logic.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Note that US1 (Baseline Measurement) blocks all optimization stories, and US7 (Verification) depends on all optimization stories completing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` (per plan.md project structure)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Define baseline measurement protocol and document the before/after checklist before any optimization code is written.

- [x] T001 Document the repeatable baseline measurement protocol in specs/031-performance-review/quickstart.md with step-by-step instructions for idle API call count, per-refresh API call count, component render count, drag frame rate, and network activity on fallback polling (FR-001)
- [x] T002 [P] Define the before/after metrics checklist table in specs/031-performance-review/quickstart.md mapping each metric to its target value (SC-001 through SC-011) and existing test file that guards it

---

## Phase 2: Foundational (Spec 022 Audit & Blocking Prerequisites)

**Purpose**: Verify current backend state against Spec 022 acceptance criteria. Identify gaps that must be addressed before optimization work begins. This phase BLOCKS all user story work.

**⚠️ CRITICAL**: No optimization work can begin until this audit confirms the current state.

- [x] T003 Audit WebSocket change detection in backend/src/api/projects.py — confirm SHA256 hash comparison is present and refresh messages are only sent when data changes (FR-002)
- [x] T004 [P] Audit board cache TTL alignment in backend/src/api/board.py — confirm cache key `board_data:{project_id}` uses TTL=300s matching the frontend 5-minute auto-refresh interval (FR-002)
- [x] T005 [P] Audit sub-issue cache invalidation in backend/src/api/board.py — confirm manual refresh (`refresh=true`) clears sub-issue cache entries for the project (FR-002)
- [x] T006 [P] Audit polling loop in backend/src/services/copilot_polling/polling_loop.py — confirm adaptive backoff and rate-limit pre-checks are active (FR-002)
- [x] T007 Document audit findings and remaining gaps in specs/031-performance-review/research.md, noting which Spec 022 items are complete vs. which need remediation

**Checkpoint**: Spec 022 audit is complete. All gaps are documented and ready to be addressed in subsequent phases.

---

## Phase 3: User Story 1 — Baseline Measurement Before Any Optimization (Priority: P1) 🎯 MVP

**Goal**: Capture current backend and frontend performance baselines using the measurement protocol defined in Phase 1, before any code changes are applied.

**Independent Test**: Execute the measurement protocol on a representative board (50–200 cards) and record idle API call count, board endpoint cost, render time, rerender counts, and refresh frequency.

### Implementation for User Story 1

- [x] T008 [US1] Execute backend idle API call measurement — monitor backend logs for 5 minutes on an idle board, record outbound GitHub API call count per specs/031-performance-review/quickstart.md Measurement 1 (FR-001)
- [x] T009 [P] [US1] Execute backend per-refresh API call measurement — trigger a single board refresh with warm sub-issue cache, record API call count per specs/031-performance-review/quickstart.md Measurement 2 (FR-001)
- [x] T010 [P] [US1] Execute frontend component render count measurement — use React DevTools Profiler to count renders on a single-card status change per specs/031-performance-review/quickstart.md Measurement 3 (FR-001)
- [x] T011 [P] [US1] Execute frontend drag frame rate measurement — use Chrome DevTools Performance tab during chat popup drag per specs/031-performance-review/quickstart.md Measurement 4 (FR-001)
- [x] T012 [P] [US1] Execute frontend network activity measurement — verify fallback polling behavior and board data request count per specs/031-performance-review/quickstart.md Measurement 5 (FR-001)
- [x] T013 [US1] Record all baseline values in the before/after checklist table in specs/031-performance-review/quickstart.md and map existing tests to optimization areas they guard (FR-001, FR-016)

**Checkpoint**: All baseline metrics are captured and documented. Optimization work can now begin with data to prove improvements.

---

## Phase 4: User Story 2 — Idle Board Viewing Without Excessive API Calls (Priority: P1)

**Goal**: Ensure an idle board with no data changes makes no more than 2 GitHub API calls over a 5-minute window (excluding initial load).

**Independent Test**: Open a board with no pending changes, monitor network activity for 5 minutes, confirm ≤2 outbound GitHub API calls.

### Implementation for User Story 2

- [x] T014 [US2] Verify WebSocket subscription in backend/src/api/projects.py only sends refresh messages when `current_hash != last_hash` — if gap found, add guard to skip send when hashes match (FR-003)
- [x] T015 [US2] Verify fallback polling in frontend/src/hooks/useRealTimeSync.ts only invalidates tasks query key `['projects', projectId, 'tasks']` and does NOT invalidate board data query key `['board', 'data', projectId]` — fix if board data is currently invalidated (FR-004, FR-005)
- [x] T016 [US2] Verify polling loop in backend/src/services/copilot_polling/polling_loop.py does not trigger expensive board data refreshes unintentionally — confirm rate-limit-aware adaptive backoff prevents unnecessary cycles (FR-004)
- [x] T017 [US2] Add reconnection guard in frontend/src/hooks/useRealTimeSync.ts to debounce WebSocket reconnection invalidations — at most one task query invalidation per 2-second reconnection window (FR-012)

**Checkpoint**: Idle board viewing produces minimal API activity. WebSocket, polling, and reconnection paths do not trigger unnecessary refreshes.

---

## Phase 5: User Story 3 — Coherent and Lightweight Board Refresh on Real-Time Updates (Priority: P1)

**Goal**: Decouple lightweight task updates from the expensive full board data query. Ensure all four refresh paths follow a single coherent policy per specs/031-performance-review/contracts/refresh-contract.md.

**Independent Test**: Make a single task change on one client; on the second client, verify only the tasks query is invalidated (not board data) for WebSocket and polling paths, and that manual refresh correctly bypasses all caches.

### Implementation for User Story 3

- [x] T018 [US3] Verify WebSocket update handler in frontend/src/hooks/useRealTimeSync.ts invalidates ONLY `['projects', projectId, 'tasks']` on "refresh" messages — do NOT invalidate `['board', 'data', projectId]` (FR-005)
- [x] T019 [US3] Verify WebSocket initial_data handler in frontend/src/hooks/useRealTimeSync.ts invalidates ONLY tasks query on connection/reconnection and does NOT cascade to board data (FR-005, FR-012)
- [x] T020 [US3] Verify auto-refresh timer in frontend/src/hooks/useBoardRefresh.ts invalidates `['board', 'data', projectId]` on 5-minute interval and resets timer on any data update from any source (FR-014)
- [x] T021 [US3] Implement manual refresh priority in frontend/src/hooks/useBoardRefresh.ts — call `queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] })` before triggering manual fetch with `refresh=true` (FR-006, FR-013)
- [x] T022 [US3] Verify auto-refresh timer resets on polling updates in frontend/src/hooks/useRealTimeSync.ts — call `useBoardRefresh.resetTimer()` after polling invalidation to maintain 5-minute window from last data update regardless of source (FR-014)
- [x] T023 [US3] Verify board query in frontend/src/hooks/useProjectBoard.ts does NOT use `refetchInterval` — board refetch should be controlled exclusively by useBoardRefresh auto-refresh timer and manual refresh (FR-014)

**Checkpoint**: All four refresh paths (WebSocket, polling, auto-refresh, manual) follow the documented coherent policy. Lightweight task updates do not trigger expensive board data re-fetches.

---

## Phase 6: User Story 4 — Sub-Issue Cache Reduces Redundant Fetches (Priority: P2)

**Goal**: Ensure sub-issue data is served from cache on automatic board refreshes, reducing sub-issue API calls by ≥80%.

**Independent Test**: Load a board with sub-issues, trigger an automatic refresh, confirm zero sub-issue API calls are made (all served from warm cache).

### Implementation for User Story 4

- [x] T024 [US4] Verify sub-issue fetch path in backend/src/services/github_projects/service.py checks `cache.get("sub_issues:{owner}/{repo}#{issue_number}")` before making REST calls — if cache hit and TTL valid, return cached data without API call (FR-007)
- [x] T025 [US4] If cache miss in the sub-issue fetch path, verify `cache.set()` is called with TTL=600s after fetching fresh sub-issue data in backend/src/services/github_projects/service.py (FR-007, FR-008)
- [x] T026 [US4] Verify manual refresh path in backend/src/api/board.py clears all sub-issue cache entries for the project before fetching fresh data — confirm `cache.delete("sub_issues:{owner}/{repo}#{issue_number}")` is called per issue (FR-006, FR-008)
- [x] T027 [US4] Verify partial cache behavior — when some sub-issues are cached and others are not, only missing sub-issues should be fetched from GitHub in backend/src/services/github_projects/service.py (FR-007)

**Checkpoint**: Sub-issue cache is properly warmed on first load and reused on automatic refreshes. Manual refresh correctly invalidates and refetches. Partial cache misses only trigger targeted fetches.

---

## Phase 7: User Story 5 — Responsive Board Interactions on Medium-to-Large Boards (Priority: P2)

**Goal**: Ensure only affected cards and their containing columns re-render on single-card changes. Stabilize derived-state computation in page components.

**Independent Test**: Profile a 100-card board during a single-card status change; confirm ≤3 component re-renders (card + column + container) and smooth drag interaction at ≥30 fps.

### Implementation for User Story 5

- [x] T028 [P] [US5] Verify `BoardColumn` in frontend/src/components/board/BoardColumn.tsx uses `React.memo()` — if not present, wrap the export with `memo()` for shallow prop comparison (FR-009)
- [x] T029 [P] [US5] Verify `IssueCard` in frontend/src/components/board/IssueCard.tsx uses `React.memo()` — if not present, wrap the export with `memo()` for shallow prop comparison (FR-009)
- [x] T030 [US5] Stabilize callback props in frontend/src/pages/ProjectsPage.tsx — wrap `handleCardClick`, `handleProjectSwitch`, and other card/column callback handlers in `useCallback` with appropriate dependency arrays to prevent memo bypass from unstable references (FR-009)
- [x] T031 [US5] Memoize derived state in frontend/src/pages/ProjectsPage.tsx — wrap inline sorting (`O(n log n)` per render), progress calculation, and rate-limit state derivation in `useMemo` with correct dependency arrays (FR-010)
- [x] T032 [US5] Verify board query data flow in frontend/src/hooks/useProjectBoard.ts returns stable references when data has not changed — TanStack Query should provide referential stability via `structuralSharing` by default (FR-009)

**Checkpoint**: Board component memoization is effective. Callback props are stable. Derived state is computed only when inputs change. Single-card updates cause ≤3 re-renders.

---

## Phase 8: User Story 6 — Chat and Popover Interactions Without Performance Degradation (Priority: P3)

**Goal**: Throttle hot event listeners in chat drag and popover positioning to maintain ≥30 fps during continuous interaction.

**Independent Test**: Profile chat popup drag and popover open/resize; confirm ≥30 fps and throttled event handler invocations.

### Implementation for User Story 6

- [x] T033 [P] [US6] Add `requestAnimationFrame` gating to the `mousemove` handler in frontend/src/components/chat/ChatPopup.tsx — only process position updates once per animation frame during resize drag to prevent per-pixel handler execution (FR-011)
- [x] T034 [P] [US6] Wrap `updatePosition` callback in frontend/src/components/agents/AddAgentPopover.tsx with `useCallback` and appropriate dependencies to prevent re-registration of scroll/resize listeners on every render (FR-011)

**Checkpoint**: Chat drag and popover positioning are throttled. Event handler frequency is bounded by animation frames, not mouse movement pixels.

---

## Phase 9: User Story 7 — Verification and Regression Coverage (Priority: P2)

**Goal**: Extend automated test coverage for all optimization areas and validate improvements with before/after measurement comparison.

**Independent Test**: Run full backend and frontend test suites. Compare post-optimization metrics against Phase 3 baselines.

### Tests for User Story 7

- [x] T035 [P] [US7] Extend backend cache regression tests in backend/tests/unit/test_cache.py — add tests for sub-issue cache TTL behavior, warm-cache reuse on automatic refresh, and cache bypass on manual refresh (FR-015)
- [x] T036 [P] [US7] Extend backend board endpoint tests in backend/tests/unit/test_api_board.py — add tests for board cache TTL alignment (300s), manual refresh cache bypass, and sub-issue cache clearing on manual refresh (FR-015)
- [x] T037 [P] [US7] Extend backend polling tests in backend/tests/unit/test_copilot_polling.py — add tests for polling loop not triggering board data refreshes and adaptive backoff behavior under rate-limit pressure (FR-015)
- [x] T038 [P] [US7] Extend frontend real-time sync tests in frontend/src/hooks/useRealTimeSync.test.tsx — add tests for task-only query invalidation on WebSocket updates, board query NOT invalidated on polling fallback, and reconnection debounce guard (FR-015)
- [x] T039 [P] [US7] Extend frontend board refresh tests in frontend/src/hooks/useBoardRefresh.test.tsx — add tests for manual refresh canceling in-flight auto-refresh, timer reset on all data sources, and 5-minute auto-refresh interval (FR-015)

### Verification for User Story 7

- [x] T040 [US7] Run full backend test suite: `cd backend && python -m pytest tests/unit/ -x -q` — confirm all tests pass including new regression tests (FR-015)
- [x] T041 [US7] Run full frontend test suite: `cd frontend && npx vitest run` — confirm all tests pass including new regression tests (FR-015)
- [x] T042 [US7] Run backend linter and type checker: `cd backend && ruff check src/ && pyright src/` — confirm no new issues (FR-015)
- [x] T043 [US7] Run frontend linter, type checker, and build: `cd frontend && npx eslint src/ && npx tsc --noEmit && npm run build` — confirm no new issues (FR-015)
- [x] T044 [US7] Re-execute all baseline measurements from Phase 3 using the same protocol and record "after" values in the before/after checklist table in specs/031-performance-review/quickstart.md (FR-016)
- [x] T045 [US7] Perform manual end-to-end verification per specs/031-performance-review/quickstart.md — confirm WebSocket updates refresh task data, fallback polling is safe, manual refresh bypasses caches, and board interactions are responsive (FR-016)

**Checkpoint**: All automated tests pass. Before/after measurements confirm improvements meet success criteria (SC-001 through SC-011). Manual verification confirms real-world behavior matches expectations.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and documentation updates that span multiple user stories.

- [x] T046 [P] Update specs/031-performance-review/quickstart.md with finalized before/after comparison results and pass/fail status for each metric
- [x] T047 [P] Review all modified files for leftover debug logging, commented-out code, or temporary instrumentation — clean up
- [x] T048 Run quickstart.md end-to-end validation to confirm all verification steps still pass after cleanup

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational / Spec 022 Audit (Phase 2)**: Depends on Setup completion — BLOCKS all optimization work
- **Baseline Measurement (Phase 3 / US1)**: Depends on Phase 2 audit — BLOCKS all code changes
- **Backend API Fixes (Phase 4 / US2)**: Depends on Phase 3 baselines
- **Refresh Path Fixes (Phase 5 / US3)**: Depends on Phase 3 baselines — can run in parallel with Phase 4
- **Sub-Issue Cache (Phase 6 / US4)**: Depends on Phase 3 baselines — can run in parallel with Phases 4–5
- **Board Render Optimization (Phase 7 / US5)**: Depends on Phase 3 baselines — can run in parallel with Phases 4–6
- **Chat/Popover Throttling (Phase 8 / US6)**: Depends on Phase 3 baselines — can run in parallel with Phases 4–7
- **Verification (Phase 9 / US7)**: Depends on ALL optimization phases (4–8) completing
- **Polish (Phase 10)**: Depends on Verification completing

### User Story Dependencies

- **US1 (P1)**: BLOCKS all other stories — baseline must exist before any optimization
- **US2 (P1)**: Backend focus — independent of US3–US6 after baselines captured
- **US3 (P1)**: Frontend refresh focus — independent of US2, US4–US6 after baselines captured
- **US4 (P2)**: Backend cache focus — can proceed in parallel with US2, US3, US5, US6
- **US5 (P2)**: Frontend render focus — independent of US2–US4, US6
- **US6 (P3)**: Frontend event listener focus — independent of US2–US5
- **US7 (P2)**: Depends on ALL of US2–US6 completing — verification phase

### Within Each User Story

- Verify existing behavior before modifying (audit-then-fix pattern)
- Backend changes before frontend changes within the same concern
- Implementation before test extension for that concern
- Story complete and independently testable before moving to next priority

### Parallel Opportunities

- **Phase 2**: T003–T006 (Spec 022 audit tasks) are all [P] — audit different files in parallel
- **Phase 3**: T009–T012 (baseline measurements) are all [P] — measure different metrics in parallel
- **Phases 4–8**: US2–US6 can all proceed in parallel once US1 baselines are captured
  - US2 (backend API) and US3 (frontend refresh) target different codebases
  - US4 (backend cache) targets different files than US2
  - US5 (frontend render) targets different components than US3
  - US6 (frontend events) targets different components than US3/US5
- **Phase 9**: T035–T039 (test extension tasks) are all [P] — different test files

---

## Parallel Example: User Story 2 + User Story 3

```bash
# After US1 baselines are captured, launch backend and frontend work together:

# Developer A (backend): US2 — Idle API reduction
Task: T014 "Verify WebSocket change detection in backend/src/api/projects.py"
Task: T015 "Verify fallback polling in frontend/src/hooks/useRealTimeSync.ts"
Task: T016 "Verify polling loop in backend/src/services/copilot_polling/polling_loop.py"

# Developer B (frontend): US3 — Refresh path coherence
Task: T018 "Verify WebSocket update handler in frontend/src/hooks/useRealTimeSync.ts"
Task: T020 "Verify auto-refresh timer in frontend/src/hooks/useBoardRefresh.ts"
Task: T021 "Implement manual refresh priority in frontend/src/hooks/useBoardRefresh.ts"
```

## Parallel Example: User Story 5 + User Story 6

```bash
# Frontend render work and event throttling can proceed simultaneously:

# Developer A: US5 — Board render optimization
Task: T028 "Verify BoardColumn memo in frontend/src/components/board/BoardColumn.tsx"
Task: T029 "Verify IssueCard memo in frontend/src/components/board/IssueCard.tsx"

# Developer B: US6 — Event listener throttling
Task: T033 "Add rAF gating to ChatPopup in frontend/src/components/chat/ChatPopup.tsx"
Task: T034 "Wrap updatePosition in AddAgentPopover in frontend/src/components/agents/AddAgentPopover.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Complete Phase 1: Setup (measurement protocol)
2. Complete Phase 2: Spec 022 Audit (foundational)
3. Complete Phase 3: US1 Baseline Measurement
4. Complete Phase 4: US2 Idle API Reduction (highest-value backend fix)
5. **STOP and VALIDATE**: Re-run idle API measurement. If ≤2 calls/5 min → MVP target met.
6. Proceed to US3–US7 for full pass

### Incremental Delivery

1. Setup + Audit + Baselines → Measurement infrastructure ready
2. US2 (Idle API) → Backend API churn fixed → Validate with backend metrics
3. US3 (Refresh Paths) → Frontend refresh coherence → Validate with network inspection
4. US4 (Sub-Issue Cache) → Cache hit rate ≥80% → Validate with backend logs
5. US5 (Board Render) → ≤3 rerenders per card change → Validate with React Profiler
6. US6 (Chat/Popover) → ≥30 fps during drag → Validate with Performance tab
7. US7 (Verification) → Full before/after comparison → All SC pass
8. Each story adds measurable, proven value without breaking previous stories

### Parallel Team Strategy

With multiple developers after US1 baselines:

1. Team completes Setup + Audit + Baselines together (Phases 1–3)
2. Once baselines are captured:
   - Developer A (backend): US2 (Idle API) + US4 (Sub-Issue Cache)
   - Developer B (frontend): US3 (Refresh Paths) + US5 (Board Render) + US6 (Event Throttling)
3. Both developers: US7 (Verification) — backend dev runs backend tests, frontend dev runs frontend tests
4. Joint: Phase 10 cleanup and final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable (except US7 which validates all)
- All optimizations use standard patterns: React.memo/useMemo/useCallback (frontend), existing cache service (backend)
- No new dependencies introduced — constraint from spec (out of scope)
- Verify before modifying: each task starts with "verify" to confirm current state before applying changes
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: adding new abstractions, virtualization, or major service decomposition (deferred to Phase 4 optional work per spec)
