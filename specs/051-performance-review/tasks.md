# Tasks: Performance Review

**Input**: Design documents from `/specs/051-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly requested (FR-017, FR-018, FR-019) for backend cache behavior, change detection, fallback polling safety, frontend real-time sync, board refresh hooks, and query invalidation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- Backend tests: `solune/backend/tests/unit/`
- Frontend tests: colocated with source (e.g., `solune/frontend/src/hooks/*.test.tsx`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the measurement infrastructure and verify the current implementation state before any optimization code changes.

- [x] T001 Create the baseline capture checklist document in `specs/051-performance-review/checklists/baseline.md` using the metric definitions from `contracts/baseline-metrics.md`
- [x] T002 [P] Review and document current implementation state against Spec 022 targets using `solune/specs/022-api-rate-limit-protection/spec.md` as the reference

---

## Phase 2: Foundational — Performance Baselines (Blocking Prerequisites)

**Purpose**: Capture all pre-optimization performance baselines. This phase MUST complete before ANY optimization code changes begin.

**⚠️ CRITICAL**: No optimization work (Phases 3–7) can begin until baselines are recorded.

**Maps to**: User Story 6 (P1) — Performance Baselines Are Captured Before Changes

- [ ] T003 [US6] Capture backend idle API call rate (BM-1) by running the backend with debug logging and counting external API calls over a 5-minute idle board session per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T004 [P] [US6] Capture board endpoint request cost (BM-2) cold and warm by profiling `GET /api/v1/board/projects/{project_id}` with and without `refresh=true` per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T005 [P] [US6] Capture polling cycle cost (BM-3) by disabling WebSocket and measuring external API calls during 5 consecutive SSE polling cycles per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T006 [P] [US6] Capture frontend board time-to-interactive (FM-1) with warm caches using Performance API or React Profiler per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T007 [P] [US6] Capture frontend render cycle count (FM-2) during board load using React Profiler per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T008 [P] [US6] Capture frontend interaction frame rate (FM-3) for drag, popover, and scroll on a 50+ card board using DevTools Performance panel per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T009 [P] [US6] Capture frontend network request count (FM-4) during board page load using DevTools Network panel per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T010 [P] [US6] Capture real-time update latency (FM-5) by timing task status change propagation between two browser sessions per `specs/051-performance-review/contracts/baseline-metrics.md`
- [ ] T011 [US6] Record all baseline values in `specs/051-performance-review/checklists/baseline.md` and confirm every metric has a numeric value before proceeding

**Checkpoint**: All baseline metrics recorded. Optimization work can now begin. Each post-optimization metric will be compared against these values.

---

## Phase 3: User Story 1 — Idle Board Does Not Waste Resources (Priority: P1) 🎯 MVP

**Goal**: Ensure an idle board produces no more than 2 external API calls per minute on average, by fixing the WebSocket subscription refresh logic, stale-revalidation counter, and duplicate repository resolution.

**Independent Test**: Open a board, leave it idle for 5 minutes, count external service calls. Count must be ≤2/minute average with no repeated unchanged refreshes.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US1] Add test for WebSocket handler cache-hit short-circuit (no external API call when cache is warm and data unchanged) in `solune/backend/tests/unit/test_api_board.py`
- [x] T013 [P] [US1] Add test for stale-revalidation counter resetting on verified-unchanged data (same hash) rather than on forced fetch in `solune/backend/tests/unit/test_api_board.py`
- [x] T014 [P] [US1] Add test verifying `workflow.py` uses shared `resolve_repository()` from `utils.py` instead of duplicate resolution logic in `solune/backend/tests/unit/test_api_board.py`

### Implementation for User Story 1

- [x] T015 [US1] Fix WebSocket subscription handler to short-circuit on cache hit — skip `get_project_tasks()` external call when cached data has not expired in `solune/backend/src/api/projects.py`
- [x] T016 [US1] Fix stale-revalidation counter to reset on verified-unchanged data (same hash comparison) rather than on forced fetches in `solune/backend/src/api/projects.py`
- [x] T017 [US1] Consolidate duplicate repository-resolution logic in `solune/backend/src/api/workflow.py` to use shared `resolve_repository()` from `solune/backend/src/utils.py`
- [ ] T018 [US1] Verify idle board behavior end-to-end per `specs/051-performance-review/quickstart.md`: open board, wait 5 minutes, confirm ≤2 external API calls/minute average with no repeated unchanged refreshes

**Checkpoint**: Idle board API consumption is within target. SC-001 (≤2 calls/min, ≥50% reduction) should be achievable.

---

## Phase 4: User Story 2 — Board Loads and Refreshes Quickly (Priority: P1)

**Goal**: Board load with warm caches is at least 30% faster by reusing cached sub-issue data during non-manual refreshes and ensuring manual refresh properly bypasses all caches.

**Independent Test**: Navigate to a board with cached sub-issue data and measure time-to-interactive. Trigger manual refresh and confirm caches are bypassed.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T019 [P] [US2] Add test verifying sub-issue cache is checked before making external API calls during non-manual board refresh in `solune/backend/tests/unit/test_api_board.py`
- [x] T020 [P] [US2] Add test verifying sub-issue cache entries are cleared on manual refresh (`refresh=True`) in `solune/backend/tests/unit/test_api_board.py`
- [x] T021 [P] [US2] Add test verifying warm sub-issue cache reduces external sub-issue fetch count by ≥40% in `solune/backend/tests/unit/test_api_board.py`

### Implementation for User Story 2

- [x] T022 [US2] Add sub-issue cache check before external API calls in the board data fetch path in `solune/backend/src/services/github_projects/service.py`
- [x] T023 [US2] Verify manual refresh clears all sub-issue cache entries for board items before fetching fresh data in `solune/backend/src/api/board.py`
- [x] T024 [US2] Verify cache TTL alignment — board data cache uses 300-second TTL consistent with frontend auto-refresh interval in `solune/backend/src/services/cache.py`
- [ ] T025 [US2] Measure board load TTI with warm caches post-optimization and compare against FM-1 baseline in `specs/051-performance-review/checklists/baseline.md`

**Checkpoint**: Board loads with warm caches are measurably faster. SC-002 (30% TTI improvement) and SC-003 (40% fewer sub-issue fetches) should be achievable.

---

## Phase 5: User Story 3 — Real-Time Updates Arrive Without Disruption (Priority: P2)

**Goal**: WebSocket task updates refresh only task data — not the full board query — preserving scroll position and open UI elements.

**Independent Test**: Two users view the same board. One changes a task status. The other sees the update within 3 seconds without the board visually resetting.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T026 [P] [US3] Add test verifying `task_update`, `task_created`, and `status_changed` WebSocket messages invalidate only the tasks query (not board data query) in `solune/frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T027 [P] [US3] Add test verifying `initial_data` and `refresh` WebSocket messages invalidate the tasks query correctly in `solune/frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T028 [P] [US3] Add test verifying board data query (`['board', 'data', projectId]`) is NOT invalidated on task-level WebSocket messages in `solune/frontend/src/hooks/useRealTimeSync.test.tsx`

### Implementation for User Story 3

- [x] T029 [US3] Scope WebSocket task-level message handlers (`task_update`, `task_created`, `status_changed`) to invalidate only the tasks query — remove any board data query invalidation in `solune/frontend/src/hooks/useRealTimeSync.ts`
- [x] T030 [US3] Ensure board data freshness is managed exclusively by `useBoardRefresh` (auto-refresh timer and manual refresh) in `solune/frontend/src/hooks/useBoardRefresh.ts`
- [x] T031 [US3] Verify that `useProjectBoard` query configuration does not use `refetchInterval` or other auto-polling that could bypass the refresh policy in `solune/frontend/src/hooks/useProjectBoard.ts`
- [ ] T032 [US3] Verify scroll position and open popover preservation during real-time task updates end-to-end per `specs/051-performance-review/quickstart.md`

**Checkpoint**: Real-time task updates arrive within 3 seconds without full board re-render. SC-004 (≤3s update latency, no full board refresh) should be met.

---

## Phase 6: User Story 4 — Board Interactions Feel Responsive (Priority: P2)

**Goal**: Board interactions (drag, popover, scroll) maintain ≥30 FPS on boards with 50+ cards by memoizing heavy components, stabilizing derived data, and throttling hot event listeners.

**Independent Test**: On a 50+ card board, drag a card between columns and open a popover. Measure frame rate. No dropped frames or visible lag.

### Implementation for User Story 4

- [x] T033 [P] [US4] Wrap `BoardColumn` component with `React.memo` and add stable key props in `solune/frontend/src/components/board/BoardColumn.tsx`
- [x] T034 [P] [US4] Wrap `IssueCard` component with `React.memo` and add stable key props in `solune/frontend/src/components/board/IssueCard.tsx`
- [x] T035 [P] [US4] Add `useMemo` for derived data (sorting, filtering, aggregation) in `solune/frontend/src/pages/ProjectsPage.tsx`
- [x] T036 [US4] Add `useCallback` for event handlers passed as props to memoized `BoardColumn` and `IssueCard` children in `solune/frontend/src/pages/ProjectsPage.tsx`
- [x] T037 [P] [US4] Throttle resize/drag event handler with `requestAnimationFrame` gating in `solune/frontend/src/components/chat/ChatPopup.tsx`
- [x] T038 [P] [US4] Review and throttle positioning listener update frequency in `solune/frontend/src/components/agents/AddAgentPopover.tsx` if custom listeners exist
- [ ] T039 [US4] Measure interaction frame rates post-optimization (drag, popover, scroll) and compare against FM-3 baseline in `specs/051-performance-review/checklists/baseline.md`

**Checkpoint**: Board interactions maintain ≥30 FPS. SC-006 (≥30 FPS on 50+ card board) should be met.

---

## Phase 7: User Story 5 — Fallback Polling Remains Safe (Priority: P3)

**Goal**: When WebSocket is unavailable, fallback polling does not trigger expensive full board refreshes, does not create polling storms, and respects rate-limit budgets.

**Independent Test**: Disable real-time channel, observe polling for 5 minutes. Verify consistent intervals, lightweight calls, no repeated expensive refreshes.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T040 [P] [US5] Add test verifying fallback polling compares polled data against cached data before invalidating queries in `solune/frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T041 [P] [US5] Add test verifying fallback polling does NOT invalidate board data query when no changes are detected in `solune/frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T042 [P] [US5] Add test verifying fallback polling intervals remain consistent and do not escalate in `solune/frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T043 [P] [US5] Add backend test verifying polling cycle produces ≤1 lightweight external call when data is unchanged in `solune/backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 5

- [x] T044 [US5] Add client-side change detection to fallback polling — compare polled data hash against cached version before invalidating queries in `solune/frontend/src/hooks/useRealTimeSync.ts`
- [x] T045 [US5] Ensure fallback polling only invalidates the tasks query (not board data query) when actual changes are detected, matching the WebSocket handler policy in `solune/frontend/src/hooks/useRealTimeSync.ts`
- [x] T046 [US5] Verify backend SSE polling endpoint serves stale data on fetch failures without triggering cascading refreshes in `solune/backend/src/api/projects.py`
- [ ] T047 [US5] Verify fallback polling end-to-end per `specs/051-performance-review/quickstart.md`: disable WebSocket, observe 5 minutes of polling, confirm consistent intervals and no expensive full board refreshes

**Checkpoint**: Fallback polling is safe and lightweight. SC-005 (≤1 call/interval, no expensive refresh unless changes detected) should be met.

---

## Phase 8: Verification & Regression Coverage

**Purpose**: Extend automated test coverage for all changed behavior and validate improvements against baselines.

### Backend Regression Tests

- [x] T048 [P] Extend cache TTL and stale fallback tests to cover 300-second TTL alignment and hash-based change detection in `solune/backend/tests/unit/test_cache.py`
- [x] T049 [P] Extend board endpoint tests to cover sub-issue cache reuse on non-manual refresh and cache clearing on manual refresh in `solune/backend/tests/unit/test_api_board.py`
- [x] T050 [P] Extend polling behavior tests to cover rate-limit-aware scheduling, adaptive backoff, and idle-safe polling cycles in `solune/backend/tests/unit/test_copilot_polling.py`

### Frontend Regression Tests

- [x] T051 [P] Extend real-time sync tests to cover the full refresh policy contract (WebSocket message types → query invalidation scope) per `specs/051-performance-review/contracts/refresh-policy.md` in `solune/frontend/src/hooks/useRealTimeSync.test.tsx`
- [x] T052 [P] Extend board refresh tests to cover auto-refresh timer behavior, page visibility pause/resume, manual refresh cache bypass, and debounce deduplication per `specs/051-performance-review/contracts/refresh-policy.md` in `solune/frontend/src/hooks/useBoardRefresh.test.tsx`

### Automated Verification

- [x] T053 Run backend lint (`ruff check src/`), type check (`pyright src/`), and targeted tests (`pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v`) from `solune/backend/`
- [x] T054 [P] Run frontend lint (`npx eslint src/`), type check (`npx tsc --noEmit`), targeted tests (`npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx`), and build check (`npm run build`) from `solune/frontend/`

**Checkpoint**: All automated checks pass. Regression coverage is in place for all changed behavior.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, baseline comparison, and documentation.

- [ ] T055 Re-capture all baseline metrics post-optimization and record post-optimization values in `specs/051-performance-review/checklists/baseline.md`
- [ ] T056 Compare post-optimization metrics against pre-optimization baselines and document improvements for each success criterion (SC-001 through SC-008) in `specs/051-performance-review/checklists/baseline.md`
- [ ] T057 Run the manual end-to-end verification per `specs/051-performance-review/quickstart.md` — verify WebSocket updates, fallback polling safety, manual refresh cache bypass, and board interaction responsiveness
- [ ] T058 Document any metrics that did not meet targets and assess whether Phase 4 (optional second-wave) work is needed per `specs/051-performance-review/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational / Baselines (Phase 2)**: Depends on Setup — BLOCKS all optimization work (Phases 3–7)
- **US1: Idle Board (Phase 3)**: Depends on Phase 2 baselines — backend-only, can start immediately after baselines
- **US2: Board Load Speed (Phase 4)**: Depends on Phase 2 baselines — backend-only, can run in parallel with Phase 3
- **US3: Real-Time Updates (Phase 5)**: Depends on Phase 2 baselines — frontend-only, can run in parallel with Phases 3–4
- **US4: Board Interactions (Phase 6)**: Depends on Phase 2 baselines — frontend-only, can run in parallel with Phases 3–5
- **US5: Fallback Polling (Phase 7)**: Depends on Phase 2 baselines — frontend + backend, can run in parallel with Phases 3–6 but benefits from US3 refresh-policy changes
- **Verification (Phase 8)**: Depends on Phases 3–7 completion
- **Polish (Phase 9)**: Depends on Phase 8 completion

### User Story Dependencies

- **US6 / Baselines (Phase 2)**: No dependencies on other stories — MUST complete first
- **US1 (Phase 3)**: Backend-only changes — independent of all other stories
- **US2 (Phase 4)**: Backend-only changes — independent of US1, but may share `service.py` edits (coordinate)
- **US3 (Phase 5)**: Frontend changes to `useRealTimeSync.ts` — establishes the refresh policy that US5 extends
- **US4 (Phase 6)**: Frontend render changes — fully independent of US1–US3 (different files)
- **US5 (Phase 7)**: Frontend + backend changes — extends the refresh policy from US3 for the polling fallback path

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend changes before frontend changes (where both exist)
- Core implementation before integration/verification
- Story complete before moving to next priority

### Parallel Opportunities

- All baseline capture tasks (T003–T010) marked [P] can run in parallel once T001–T002 are done
- US1 (backend) and US3 (frontend) can proceed in parallel after Phase 2
- US2 (backend) and US4 (frontend) can proceed in parallel after Phase 2
- Within US4, all `React.memo` and `useMemo` tasks (T033–T035, T037–T038) can run in parallel (different files)
- All Phase 8 regression test tasks (T048–T052) can run in parallel (different files)
- Backend (T053) and frontend (T054) verification can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Test WebSocket cache-hit short-circuit in solune/backend/tests/unit/test_api_board.py"
Task: "Test stale-revalidation counter reset in solune/backend/tests/unit/test_api_board.py"
Task: "Test workflow.py shared resolve_repository in solune/backend/tests/unit/test_api_board.py"
```

## Parallel Example: User Story 4

```bash
# Launch all memoization tasks together (different files):
Task: "React.memo BoardColumn in solune/frontend/src/components/board/BoardColumn.tsx"
Task: "React.memo IssueCard in solune/frontend/src/components/board/IssueCard.tsx"
Task: "useMemo derived data in solune/frontend/src/pages/ProjectsPage.tsx"
Task: "rAF throttle in solune/frontend/src/components/chat/ChatPopup.tsx"
Task: "Throttle listeners in solune/frontend/src/components/agents/AddAgentPopover.tsx"
```

## Parallel Example: Cross-Story Parallelism

```bash
# After Phase 2 baselines are captured, these can proceed simultaneously:
# Developer A (Backend): US1 — Idle Board fixes (projects.py, workflow.py, utils.py)
# Developer B (Backend): US2 — Board Load fixes (service.py, board.py, cache.py)
# Developer C (Frontend): US3 — Real-Time Updates (useRealTimeSync.ts, useBoardRefresh.ts)
# Developer D (Frontend): US4 — Render Optimization (BoardColumn.tsx, IssueCard.tsx, ProjectsPage.tsx)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Capture Baselines (US6) — CRITICAL, blocks all optimization
3. Complete Phase 3: US1 — Idle Board (highest-leverage fix, reduces API waste)
4. **STOP and VALIDATE**: Measure idle API calls, confirm ≤2/min
5. Deploy/demo if ready — this alone proves the optimization approach works

### Incremental Delivery

1. Complete Setup + Baselines → Measurement infrastructure ready
2. Add US1 (Idle Board) → Test independently → Measure SC-001 (MVP!)
3. Add US2 (Board Load Speed) → Test independently → Measure SC-002, SC-003
4. Add US3 (Real-Time Updates) → Test independently → Measure SC-004
5. Add US4 (Board Interactions) → Test independently → Measure SC-006
6. Add US5 (Fallback Polling) → Test independently → Measure SC-005
7. Run Verification (Phase 8) → All tests pass, SC-007 met
8. Run Polish (Phase 9) → All metrics compared, SC-008 manual check done
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Baselines together (Phases 1–2)
2. Once baselines are captured:
   - Developer A (Backend): US1 — Idle Board (projects.py, workflow.py)
   - Developer B (Backend): US2 — Board Load Speed (service.py, board.py)
   - Developer C (Frontend): US3 — Real-Time Updates (useRealTimeSync.ts)
   - Developer D (Frontend): US4 — Board Interactions (BoardColumn.tsx, IssueCard.tsx, ProjectsPage.tsx)
3. After US3 completes: US5 — Fallback Polling (extends US3 refresh policy)
4. All stories converge at Phase 8 for verification

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Baseline measurement (Phase 2) MUST complete before any optimization code is changed
- Tests are included per FR-017 (backend), FR-018 (frontend), FR-019 (manual E2E)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Phase 4 (optional second-wave) from plan.md is explicitly out of scope unless Phase 9 metrics justify it
