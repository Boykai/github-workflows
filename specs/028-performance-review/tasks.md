# Tasks: Performance Review — Balanced First Pass

**Input**: Design documents from `/specs/028-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Regression tests are required per FR-015. New unit tests are added only for areas directly modified by optimization changes (spec §IV Test Optionality).

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

**Purpose**: Confirm current backend and frontend implementation state against Spec 022 acceptance criteria before making any changes. Prevents redoing completed work and identifies remaining gaps (FR-002).

- [ ] T001 Audit Spec 022 backend implementation by reviewing backend/src/api/projects.py (WebSocket SHA256 hash-based change detection on 30-second cycle), backend/src/api/board.py (board cache TTL=300s, sub-issue cache clear on manual refresh), backend/src/services/cache.py (TTL constants, BoundedDict), backend/src/services/copilot_polling/polling_loop.py (adaptive backoff 60→120→240→300s cap, rate-limit pre-checks, sub-issue filtering), and backend/src/services/github_projects/service.py (sub-issue cache TTL=600s, per-issue cache lookup). Document confirmed items and remaining gaps per research.md findings.
- [ ] T002 [P] Audit frontend refresh paths by reviewing frontend/src/hooks/useRealTimeSync.ts (WebSocket task-only invalidation targeting `['projects', projectId, 'tasks']`, reconnection 2-second debounce, exponential backoff 1s→30s cap, fallback polling scope), frontend/src/hooks/useBoardRefresh.ts (5-minute auto-refresh timer, manual refresh flow, timer reset on any update source), and frontend/src/hooks/useProjectBoard.ts (board query staleTime, invalidation configuration). Verify current behavior matches refresh-contract.md and identify any divergences.

---

## Phase 2: Foundational (Baseline Capture)

**Purpose**: Capture pre-optimization performance baselines using the measurement protocol defined in specs/028-performance-review/quickstart.md. All optimization work is blocked until baselines are recorded so improvements can be proven, not assumed (FR-001, SC-008).

**⚠️ CRITICAL**: No optimization code changes can begin until this phase is complete

- [ ] T003 Capture backend baseline measurements following specs/028-performance-review/quickstart.md: idle API call count over 5 minutes (Measurement 1), per-refresh API call count with warm and cold sub-issue cache (Measurement 2). Record results in the Post-Optimization Comparison Template in quickstart.md.
- [ ] T004 [P] Capture frontend baseline measurements following specs/028-performance-review/quickstart.md: component render count for a single-card status change on a 100-card board (Measurement 3), chat popup drag frame rate (Measurement 4), and fallback polling network activity for board data requests (Measurement 5). Record results in the Post-Optimization Comparison Template in quickstart.md.

**Checkpoint**: Baselines recorded — optimization implementation can now begin

---

## Phase 3: User Story 2 — Idle Board Viewing Without Excessive API Calls (Priority: P1) 🎯 MVP

**Goal**: Ensure an idle board with no active changes generates ≤2 GitHub API calls over a 5-minute window (excluding initial load). WebSocket change detection suppresses no-change refresh messages. Fallback polling does not trigger expensive board refreshes (FR-003, FR-004, SC-001, SC-009).

**Independent Test**: Open a board with no pending changes. Monitor backend logs for 5 minutes. Count outbound GitHub API calls — must be ≤2.

### Implementation for User Story 2

- [ ] T005 [US2] Verify and tighten WebSocket subscription refresh logic in backend/src/api/projects.py to confirm no refresh message is sent when the SHA256 hash of task data is unchanged. Ensure `last_sent_hash` comparison gates all outbound refresh messages on each 30-second cycle. Address any remaining gap identified in Phase 1 audit.
- [ ] T006 [P] [US2] Verify polling loop in backend/src/services/copilot_polling/polling_loop.py does not trigger downstream board endpoint calls when polled data is unchanged. Confirm adaptive backoff (60→120→240→300s cap) is respected during idle cycles, rate-limit pre-checks (RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD, RATE_LIMIT_SLOW_THRESHOLD) prevent unnecessary API calls, and sub-issues are filtered out upfront.
- [ ] T007 [P] [US2] Add regression tests for idle WebSocket and polling behavior in backend/tests/unit/test_copilot_polling.py: verify no-change hash comparison suppresses refresh messages, verify adaptive backoff increases interval under idle conditions, verify rate-limit pre-checks gate expensive operations.

**Checkpoint**: Idle board API consumption meets ≤2 calls/5 min target

---

## Phase 4: User Story 3 — Coherent Refresh Policy Across All Update Paths (Priority: P1)

**Goal**: Lightweight task updates (WebSocket, polling) refresh only the tasks query without triggering the expensive board data query. Manual refresh bypasses all caches with highest priority. Reconnection triggers a single full refresh without cascade. All refresh sources follow the contract defined in contracts/refresh-contract.md (FR-005, FR-006, FR-007, FR-013, FR-014, SC-002, SC-010).

**Independent Test**: Make a single task change on one client. On a second client, verify the update appears within 30 seconds, the board data endpoint is NOT called (only tasks query), and no cascade of invalidations occurs. Trigger manual refresh and verify board data endpoint is called with `?refresh=true`.

### Implementation for User Story 3

- [ ] T008 [US3] Verify and enforce WebSocket task update decoupling in frontend/src/hooks/useRealTimeSync.ts: on receiving a `refresh` type message, confirm only `['projects', projectId, 'tasks']` is invalidated and `['board', 'data', projectId]` is NOT invalidated. Fix if any board data invalidation path exists.
- [ ] T009 [US3] Verify reconnection debounce guard in frontend/src/hooks/useRealTimeSync.ts: on WebSocket reconnection (`initial_data` message), confirm debounce limits invalidation to at most once per 2-second reconnection cycle and targets only the tasks query. Fix if reconnection cascades board invalidation.
- [ ] T010 [US3] Verify fallback polling path in frontend/src/hooks/useRealTimeSync.ts only invalidates `['projects', projectId, 'tasks']` and does NOT invalidate board data. Confirm auto-refresh timer reset is called on polling updates (same as WebSocket updates) per refresh-contract.md.
- [ ] T011 [US3] Implement or verify manual refresh priority in frontend/src/hooks/useBoardRefresh.ts: call `queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] })` before initiating manual fetch with `refresh=true`. Ensure auto-refresh timer resets after manual refresh completes per refresh-contract.md §5.
- [ ] T012 [US3] Verify auto-refresh timer resets on any data update source (WebSocket, polling, manual) to maintain a consistent 5-minute window from the last update in frontend/src/hooks/useBoardRefresh.ts. Confirm timer pauses when tab is hidden and resumes with freshness check per data-model.md §6.
- [ ] T013 [P] [US3] Extend WebSocket and polling invalidation tests in frontend/src/hooks/useRealTimeSync.test.tsx: verify task-only invalidation on `refresh` messages, verify no board data invalidation, verify reconnection debounce limits invalidation to once per 2-second cycle, verify fallback polling targets only tasks query.
- [ ] T014 [P] [US3] Extend manual refresh and timer tests in frontend/src/hooks/useBoardRefresh.test.tsx: verify `cancelQueries` is called before manual fetch, verify timer resets on all update sources (WebSocket, polling, manual), verify manual refresh takes priority over in-progress auto-refresh.

**Checkpoint**: Task updates are decoupled from board query; manual refresh has priority; reconnection is guarded; refresh policy is coherent across all sources

---

## Phase 5: User Story 4 — Responsive Board Interactions on Medium-to-Large Boards (Priority: P2)

**Goal**: A single-card status change on a 100-card board causes ≤3 component re-renders (card + column + board container). Drag interactions maintain ≥30 fps. Derived state is memoized. Function props passed to memoized children are stable (FR-010, FR-011, SC-004, SC-005).

**Independent Test**: Profile a 100-card board in React DevTools Profiler. Change a single card status and verify only 3 components re-render. Drag a card between columns and verify ≥30 fps in Chrome Performance tab.

### Implementation for User Story 4

- [ ] T015 [P] [US4] Verify BoardColumn is already wrapped in React.memo() in frontend/src/components/board/BoardColumn.tsx (confirmed in research.md §4). No additional wrapping needed — focus shifts to stabilizing parent-supplied function props in T018.
- [ ] T016 [P] [US4] Verify IssueCard is already wrapped in React.memo() in frontend/src/components/board/IssueCard.tsx (confirmed in research.md §4). No additional wrapping needed — focus shifts to stabilizing parent-supplied function props in T018.
- [ ] T017 [US4] Verify `blockingIssueNumbers` and `assignedStageMap` are already memoized with useMemo in frontend/src/pages/ProjectsPage.tsx (confirmed in research.md §5). Confirm `getGroups` is also memoized. Identify any remaining inline derivations that warrant memoization — per research, `totalItems`, `projectsRateLimitError`, `boardRateLimitError`, and `pipelineGridStyle` are trivial and do NOT warrant useMemo.
- [ ] T018 [US4] Stabilize event handler props with useCallback in frontend/src/pages/ProjectsPage.tsx: wrap `handleCardClick`, `handleCloseModal`, `handleProjectSwitch`, and any other callback props passed to BoardColumn or IssueCard components. Include appropriate dependency arrays. This makes the existing React.memo() on child components effective by ensuring referential equality of function props across renders.
- [ ] T019 [US4] Review board query invalidation strategy in frontend/src/hooks/useProjectBoard.ts to confirm staleTime and invalidation behavior limit unnecessary refetches that would trigger full board re-renders. Verify query configuration aligns with cache-contract.md.

**Checkpoint**: Single-card change re-renders ≤3 components; board interactions remain smooth; derived state is memoized

---

## Phase 6: User Story 5 — Chat and Popover Interactions Without Performance Degradation (Priority: P3)

**Goal**: Chat popup drag maintains ≥30 fps with throttled position updates. Agent popover repositioning does not trigger excessive re-renders of unrelated components during scroll/resize (FR-012, SC-006).

**Independent Test**: Profile chat drag in Chrome Performance tab — verify ≥30 fps. Open an agent popover and resize/scroll viewport — verify no excessive re-renders in React DevTools.

### Implementation for User Story 5

- [ ] T020 [P] [US5] Verify ChatPopup drag listener already uses requestAnimationFrame (RAF) gating in frontend/src/components/chat/ChatPopup.tsx (confirmed in research.md §6 — `rafId` stored, position updates limited to once per animation frame). No further throttling changes needed.
- [ ] T021 [P] [US5] Add requestAnimationFrame gating or debounce to scroll/resize position listeners in frontend/src/components/agents/AddAgentPopover.tsx. Wrap `updatePosition` in useCallback with appropriate dependencies and gate scroll/resize event handlers through RAF to prevent 100+ invocations per second during rapid scrolling per research.md §6.

**Checkpoint**: Drag and popover interactions are throttled and responsive

---

## Phase 7: User Story 6 — Verification and Regression Coverage (Priority: P2)

**Goal**: Extend or adjust unit/integration coverage around modified areas. Run full test suites. Capture post-optimization measurements. Confirm zero regressions and validate improvements against baselines (FR-015, FR-016, SC-007, SC-008).

**Independent Test**: Run full backend and frontend test suites — all must pass. Perform manual network/profile pass to confirm target improvements.

### Implementation for User Story 6

- [ ] T022 [P] [US6] Extend cache TTL regression tests in backend/tests/unit/test_cache.py: verify board data cache TTL=300s, verify sub-issue cache TTL=600s, verify stale fallback serves expired data on upstream errors, verify cache.set stores data with correct TTL.
- [ ] T023 [P] [US6] Extend board cache regression tests in backend/tests/unit/test_api_board.py: verify automatic refresh uses cached board data when TTL is valid (zero API calls), verify automatic refresh uses cached sub-issues (zero sub-issue API calls), verify manual refresh with `refresh=true` clears sub-issue cache and fetches fresh data.
- [ ] T024 [P] [US6] Verify existing polling regression tests in backend/tests/unit/test_copilot_polling.py cover: polling-triggered refresh guard, adaptive backoff behavior, and rate-limit-aware skip logic. Extend coverage if gaps remain.

**Checkpoint**: All tests pass; post-optimization measurements validate improvements against baselines

---

## Phase 8: Polish & Verification

**Purpose**: Run full verification suites, capture post-optimization measurements, confirm zero regressions, and document before/after results.

- [ ] T025 [P] Run backend verification suite per specs/028-performance-review/quickstart.md: `cd backend && ruff check src/`, `pyright src/`, `python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --tb=short`
- [ ] T026 [P] Run frontend verification suite per specs/028-performance-review/quickstart.md: `cd frontend && npx eslint src/`, `npx tsc --noEmit`, `npx vitest run`, `npm run build`
- [ ] T027 Run post-optimization measurements using the same baseline protocol from Phase 2 (specs/028-performance-review/quickstart.md). Complete the Post-Optimization Comparison Template with before/after values and improvement percentages for each metric.
- [ ] T028 Perform manual end-to-end verification per specs/028-performance-review/quickstart.md §End-to-End Verification: confirm WebSocket updates refresh task data quickly, fallback polling remains safe, manual refresh bypasses caches, and board interactions remain responsive. Document pass/fail for each check.
- [ ] T029 Validate zero test regressions: confirm all pre-existing backend and frontend tests pass after optimization changes. Document any test modifications and their justification.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all optimization work
- **US2 (Phase 3)**: Depends on Foundational — backend-only, can start first
- **US3 (Phase 4)**: Depends on Foundational — frontend-only, can run in parallel with US2
- **US4 (Phase 5)**: Depends on Foundational — frontend-only, can run in parallel with US2/US3
- **US5 (Phase 6)**: Depends on Foundational — frontend-only, can run in parallel with US4
- **US6 (Phase 7)**: Depends on US2 + US3 implementation completion (tests cover modified areas)
- **Polish (Phase 8)**: Depends on ALL user story phases being complete

### User Story Dependencies

- **US1 (P1) — Baseline Measurement**: Covered by Phase 1 (Setup) + Phase 2 (Foundational) — not a separate implementation phase since it is a measurement/audit activity
- **US2 (P1) — Idle API Reduction**: Backend-only. No dependencies on other stories. Can start immediately after Foundational.
- **US3 (P1) — Refresh Policy**: Frontend-only. No dependencies on other stories. Can run in parallel with US2.
- **US4 (P2) — Board Render**: Frontend-only. Benefits from US3 refresh-path changes being in place (fewer invalidations = fewer re-renders) but is independently testable.
- **US5 (P3) — Chat/Popover**: Frontend-only. Fully independent of all other stories.
- **US6 (P2) — Verification**: Depends on US2–US5 implementation being complete. Extends test coverage for modified areas.

### Within Each User Story

- Verification tasks (confirm existing state) before modification tasks
- Implementation tasks before test extension tasks
- Core changes before integration/verification
- Commit after each task or logical group

### Parallel Opportunities

- Phase 1: T001 ‖ T002 (backend audit ‖ frontend audit)
- Phase 2: T003 ‖ T004 (backend baseline ‖ frontend baseline)
- Phase 3 (US2): T006 ‖ T007 (polling guard ‖ regression tests)
- Phase 4 (US3): T013 ‖ T014 (WebSocket tests ‖ refresh tests)
- Phase 5 (US4): T015 ‖ T016 (BoardColumn verify ‖ IssueCard verify)
- Phase 6 (US5): T020 ‖ T021 (ChatPopup verify ‖ AddAgentPopover throttle)
- Phase 7 (US6): T022 ‖ T023 ‖ T024 (cache tests ‖ board tests ‖ polling tests)
- Phase 8: T025 ‖ T026 (backend verify ‖ frontend verify)
- **Cross-story**: US2 (backend) ‖ US3 (frontend) — different codebases, zero overlap
- **Cross-story**: US4 (frontend) ‖ US5 (frontend) — different files, no dependencies

---

## Parallel Example: User Story 2 (Backend)

```bash
# After T005 (WebSocket verification), launch in parallel:
Task: "Verify polling loop idle behavior in backend/src/services/copilot_polling/polling_loop.py"  # T006
Task: "Add idle WebSocket and polling regression tests in backend/tests/unit/test_copilot_polling.py"  # T007
```

## Parallel Example: User Story 4 (Frontend)

```bash
# Launch board component verification in parallel (different files):
Task: "Verify BoardColumn React.memo in frontend/src/components/board/BoardColumn.tsx"  # T015
Task: "Verify IssueCard React.memo in frontend/src/components/board/IssueCard.tsx"      # T016

# Then sequentially (same file):
Task: "Verify memoized derivations in frontend/src/pages/ProjectsPage.tsx"              # T017
Task: "Stabilize handlers with useCallback in frontend/src/pages/ProjectsPage.tsx"      # T018
```

## Parallel Example: Cross-Story (Backend ‖ Frontend)

```bash
# Backend and frontend stories can proceed in parallel:
# Developer A (Backend):
Task: US2 — "Verify WebSocket change detection in backend/src/api/projects.py"                     # T005
Task: US6 — "Extend cache regression tests in backend/tests/unit/test_cache.py"                    # T022

# Developer B (Frontend):
Task: US3 — "Verify task update decoupling in frontend/src/hooks/useRealTimeSync.ts"               # T008
Task: US4 — "Stabilize handlers with useCallback in frontend/src/pages/ProjectsPage.tsx"           # T018
```

---

## Implementation Strategy

### MVP First (User Stories 2 + 3 Only)

1. Complete Phase 1: Setup (Spec 022 audit)
2. Complete Phase 2: Foundational (baseline capture)
3. Complete Phase 3: US2 — Idle board API reduction (backend)
4. Complete Phase 4: US3 — Refresh path decoupling (frontend)
5. **STOP and VALIDATE**: Measure idle API calls and refresh behavior against baselines
6. If targets met: deploy; if not: proceed to Phase 5+

### Incremental Delivery

1. Setup + Foundational → Baselines captured, Spec 022 audit complete
2. US2 + US3 → Backend API churn fixed + Frontend refresh decoupled → Measure (MVP!)
3. US4 → Board render optimized → Measure rerender count and frame rate
4. US5 → Chat/popover throttled → Measure drag frame rate
5. US6 → Regression tests extended → Full test suite pass
6. Verification → before/after comparison documented

### Parallel Team Strategy

With two developers (Backend + Frontend):

1. Team reviews Setup together (Phase 1)
2. Baselines captured together (Phase 2)
3. Once Foundational is done:
   - **Backend developer**: US2 (idle board) → US6 backend tests (cache, board, polling)
   - **Frontend developer**: US3 (refresh path) → US4 (render optimization) → US5 (chat/popover) → US6 frontend tests
4. Verification together (Phase 8)

---

## Notes

- [P] tasks = different files, no dependencies — safe to execute in parallel
- [Story] label maps each task to its specific user story for traceability
- US1 (Baseline Measurement) is woven into Setup (Phase 1) and Foundational (Phase 2) rather than being a standalone implementation phase — it is a measurement activity, not a code change
- Existing Spec 022 implementation is substantially complete per research.md — tasks focus on verifying, tightening remaining gaps, and documenting contracts rather than reimplementation
- All optimization improvements must be validated with before/after measurements using the protocol in quickstart.md
- Board virtualization, major service decomposition, and new dependencies are explicitly out of scope for the first pass (deferred to potential second-wave work per plan.md)
- ChatPopup drag listener already uses RAF — T020 is a verification task, not a code change (research.md §6)
- BoardColumn and IssueCard are already wrapped in React.memo() — T015/T016 are verification tasks; the real work is stabilizing function props in T018 (research.md §4)
- Commit after each task or logical group; stop at any checkpoint to validate independently
