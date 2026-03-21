# Tasks: Performance Review

**Input**: Design documents from `/specs/056-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included because the specification explicitly requests verification and regression coverage (User Story 5, FR-014). Tests follow implementation in each user story phase since the spec's verification phase (US5) depends on optimization work being complete.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture baselines and confirm current state before any behavioral changes. This phase blocks all optimization work because success criteria depend on measured starting points.

- [ ] T001 Run existing backend tests to capture "before" regression baseline via `python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -x -q` in `solune/backend/`
- [ ] T002 [P] Run existing frontend tests to capture "before" regression baseline via `npm test -- --run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx` in `solune/frontend/`
- [ ] T003 [P] Run backend lint and type checks via `ruff check src/` and `pyright src/` in `solune/backend/`
- [ ] T004 [P] Run frontend lint, type-check, and build via `npm run lint && npm run type-check && npm run build` in `solune/frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Audit current backend state against Spec 022 and document optimization targets. MUST complete before any code changes begin.

**⚠️ CRITICAL**: No optimization work can begin until this phase confirms what is already implemented vs. what remains.

- [ ] T005 Audit WebSocket change detection in `solune/backend/src/api/projects.py` — confirm `compute_data_hash()` suppresses unchanged refresh messages and document any gaps against Spec 022
- [ ] T006 [P] Audit board cache TTL alignment in `solune/backend/src/api/board.py` — confirm 300s TTL on `board_data:{project_id}` and sub-issue cache invalidation on manual refresh (lines ~390–399)
- [ ] T007 [P] Audit sub-issue cache behavior in `solune/backend/src/services/github_projects/service.py` — confirm sub-issue caches are reused on non-manual board refreshes and document any missing reuse paths
- [ ] T008 [P] Audit polling loop cache behavior in `solune/backend/src/services/copilot_polling/polling_loop.py` — confirm `get_project_items()` is cache-first and does not trigger full board data refreshes
- [ ] T009 [P] Audit frontend refresh invalidation scope in `solune/frontend/src/hooks/useRealTimeSync.ts` — confirm WebSocket and polling fallback invalidate tasks query only, not board data query
- [ ] T010 [P] Audit frontend auto-refresh interaction with WebSocket in `solune/frontend/src/hooks/useBoardRefresh.ts` — confirm whether 5-minute auto-refresh fires redundantly when WebSocket connection is healthy

**Checkpoint**: Audit complete — optimization targets are confirmed and documented. Code changes can now begin.

---

## Phase 3: User Story 2 — Reduce Idle Backend API Consumption (Priority: P1) 🎯 MVP

**Goal**: Eliminate redundant upstream API calls during idle board viewing — idle boards should produce ≥50% fewer API calls compared to baseline (SC-001).

**Independent Test**: Open a board, leave it idle for a measured interval, count API calls. Compare against baseline. Verify no repeated unchanged refreshes are sent.

### Implementation for User Story 2

- [ ] T011 [US2] Remove redundant `list_user_projects()` call from the WebSocket refresh cycle in `solune/backend/src/api/projects.py` — validate project access once on connection, not every 30-second cycle (R2 finding)
- [ ] T012 [US2] Ensure non-manual board refresh reuses sub-issue cache in `solune/backend/src/api/board.py` — only clear sub-issue caches when `refresh=True` parameter is set (FR-005)
- [ ] T013 [P] [US2] Verify `get_project_items()` in `solune/backend/src/services/github_projects/service.py` serves from cache within TTL window and does not make upstream calls for unchanged data (FR-003, FR-004)
- [ ] T014 [P] [US2] Verify polling loop in `solune/backend/src/services/copilot_polling/polling_loop.py` does not trigger expensive board data refreshes when data is unchanged (FR-006)
- [ ] T015 [US2] Add or extend test coverage in `solune/backend/tests/unit/test_api_board.py` to verify sub-issue cache reuse on non-manual refresh and cache clearing on manual refresh
- [ ] T016 [P] [US2] Add or extend test coverage in `solune/backend/tests/unit/test_cache.py` to verify `refresh_ttl()` extends expiry without replacing value when data hash is unchanged

**Checkpoint**: Backend idle API consumption is reduced. Tests pass. Sub-issue caches are reused on non-manual refreshes. WebSocket subscription no longer makes redundant project-access calls per cycle.

---

## Phase 4: User Story 3 — Coherent Frontend Refresh Policy (Priority: P2)

**Goal**: Decouple lightweight task updates from full board data query re-execution. All refresh sources follow a single coherent policy per `contracts/refresh-policy.md` (FR-008, FR-010).

**Independent Test**: Trigger a lightweight task update (status change) while monitoring network activity. Confirm only the tasks query is refetched, not the full board data query (SC-004). Verify polling fallback follows the same lightweight policy.

### Implementation for User Story 3

- [ ] T017 [US3] Suppress auto-refresh timer in `solune/frontend/src/hooks/useBoardRefresh.ts` when WebSocket connection is healthy and actively delivering updates; resume timer on WebSocket disconnect (R5 finding, contracts/refresh-policy.md §3)
- [ ] T018 [US3] Confirm and harden polling fallback in `solune/frontend/src/hooks/useRealTimeSync.ts` to invalidate tasks query only — ensure no code path invalidates board data during polling fallback (FR-006, SC-003)
- [ ] T019 [US3] Ensure WebSocket reconnection storms are coalesced in `solune/frontend/src/hooks/useRealTimeSync.ts` — debounce `initial_data` invalidations within a 2-second window (contracts/refresh-policy.md §1, edge case)
- [ ] T020 [US3] Add or extend test in `solune/frontend/src/hooks/useBoardRefresh.test.tsx` to verify auto-refresh timer is suppressed when WebSocket connection is healthy and resumes on disconnect
- [ ] T021 [P] [US3] Add or extend test in `solune/frontend/src/hooks/useRealTimeSync.test.tsx` to verify polling fallback never invalidates board data query and that reconnection debounce coalesces rapid reconnections

**Checkpoint**: All refresh sources follow a single coherent policy. WebSocket and polling update tasks only. Manual refresh triggers full board reload. Auto-refresh is suppressed when WebSocket is active.

---

## Phase 5: User Story 4 — Responsive Board Interactions (Priority: P2)

**Goal**: Reduce unnecessary component rerenders and excessive event processing during board interactions (browsing, dragging, popovers). Measurable reduction in rerender counts compared to baseline (SC-005).

**Independent Test**: Interact with a board of representative size (5+ columns, 50+ tasks). Profile render counts and event listener fire rates. Compare against baseline to verify improvement.

### Implementation for User Story 4

- [ ] T022 [P] [US4] Stabilize `onCardClick` callback prop in the parent component that renders `BoardColumn` (likely `solune/frontend/src/pages/ProjectsPage.tsx` or board container) using `useCallback` so `React.memo` on `BoardColumn` is effective (R6 finding)
- [ ] T023 [P] [US4] Memoize inline label parsing and body truncation in `solune/frontend/src/components/board/IssueCard.tsx` using `useMemo` — prevent recomputation on every render when source data is unchanged (FR-013, R6 finding)
- [ ] T024 [P] [US4] Memoize `filteredAgents` array and `assignedSlugs` computation in `solune/frontend/src/components/agents/AddAgentPopover.tsx` using `useMemo` (R6 finding)
- [ ] T025 [US4] Memoize sync status labels and stabilize `RateLimitContext` value in `solune/frontend/src/pages/ProjectsPage.tsx` using `useMemo` to prevent consumer rerenders when values are unchanged (FR-013, R6 finding)
- [ ] T026 [US4] Stabilize `onResizeStart` callback in `solune/frontend/src/components/chat/ChatPopup.tsx` using `useCallback` with correct dependencies — prevent recreation on every resize (R6 finding)
- [ ] T027 [US4] Stabilize `onClick` and `availableAgents` props passed to `IssueCard` in the parent component to ensure `React.memo` on `IssueCard` prevents unnecessary rerenders (R6 finding)

**Checkpoint**: Board interactions are smoother. Components wrapped in `React.memo` effectively skip rerenders when props are stable. Derived data is not recomputed unnecessarily.

---

## Phase 6: User Story 5 — Verification and Regression Coverage (Priority: P3)

**Goal**: Prove that optimizations achieved their targets with before/after measurement comparisons and extended automated test coverage (FR-014, FR-015).

**Independent Test**: Run full automated test suite (backend + frontend), repeat baseline measurements, and perform manual verification. All existing tests pass with additional coverage for changed behaviors.

### Implementation for User Story 5

- [ ] T028 [US5] Run full backend test suite via `python -m pytest tests/unit/ -x -q` in `solune/backend/` — verify all existing tests pass after optimizations (SC-006)
- [ ] T029 [P] [US5] Run full frontend test suite via `npm test` in `solune/frontend/` — verify all existing tests pass after optimizations (SC-006)
- [ ] T030 [P] [US5] Run backend lint and type checks via `ruff check src/` and `pyright src/` in `solune/backend/` — no regressions
- [ ] T031 [P] [US5] Run frontend lint, type-check, and build via `npm run lint && npm run type-check && npm run build` in `solune/frontend/` — no regressions
- [ ] T032 [US5] Perform manual end-to-end verification: confirm WebSocket updates arrive promptly, polling fallback remains safe, manual refresh bypasses caches, board interactions remain responsive (SC-007, SC-008)
- [ ] T033 [US5] Repeat baseline measurements and document before/after comparison for idle API calls (SC-001), sub-issue cache effectiveness (SC-002), polling behavior (SC-003), refresh decoupling (SC-004), and rerender reduction (SC-005)

**Checkpoint**: All automated tests pass. Before/after measurements demonstrate measurable improvement. Manual verification confirms no regressions.

---

## Phase 7: User Story 6 — Second-Wave Planning Guidance (Priority: P3)

**Goal**: If first-pass optimizations do not meet targets, provide a documented follow-on plan for deeper structural changes. This phase is satisfied by documentation — no code changes unless metrics justify them.

**Independent Test**: Review the documented plan after first-pass measurements. If targets are met, the plan exists as a reference. If not, it provides actionable next steps.

### Implementation for User Story 6

- [ ] T034 [US6] Document second-wave recommendations based on first-pass results in `specs/056-performance-review/` — include board virtualization guidance if large boards still lag (SC-005 miss), service consolidation guidance if API churn persists (SC-001 miss), and instrumentation recommendations for ongoing performance monitoring
- [ ] T035 [P] [US6] Document recommended lightweight instrumentation additions (board refresh cost logging, sub-issue cache hit rate tracking, refresh-source attribution) for proactive regression detection in future iterations

**Checkpoint**: Second-wave plan exists as a documented reference. If first-pass targets are met, no further action needed. If not, the plan provides data-driven next steps.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation across all user stories.

- [ ] T036 [P] Run `solune/backend/tests/unit/test_copilot_polling.py` to verify polling optimization changes have not regressed any existing polling behavior
- [ ] T037 [P] Verify no new runtime dependencies were introduced in `solune/backend/pyproject.toml` or `solune/frontend/package.json` (constraint from plan.md)
- [ ] T038 Run quickstart.md manual verification checklist to confirm all success criteria are met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — capture baselines immediately
- **Foundational (Phase 2)**: Depends on Phase 1 baseline capture — BLOCKS all optimization work
- **US2 Backend API (Phase 3)**: Depends on Phase 2 audit — first optimization target (MVP)
- **US3 Frontend Refresh (Phase 4)**: Depends on Phase 2 audit — can run in parallel with Phase 3
- **US4 Board Render (Phase 5)**: Depends on Phase 2 audit — can run in parallel with Phases 3 and 4
- **US5 Verification (Phase 6)**: Depends on Phases 3, 4, and 5 — all optimizations must be complete
- **US6 Planning (Phase 7)**: Depends on Phase 6 measurement results — documentation only
- **Polish (Phase 8)**: Depends on all optimization phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Baseline capture — embedded in Setup and Foundational phases (Phases 1–2)
- **User Story 2 (P1)**: Backend API reduction — can start after Phase 2 audit. No dependency on other stories
- **User Story 3 (P2)**: Frontend refresh policy — can start after Phase 2 audit. Independent of US2 but benefits from knowing backend behavior
- **User Story 4 (P2)**: Board render optimization — can start after Phase 2 audit. Fully independent of US2 and US3
- **User Story 5 (P3)**: Verification — depends on US2, US3, US4 being complete
- **User Story 6 (P3)**: Second-wave planning — depends on US5 measurement results

### Within Each User Story

- Audit/confirmation before code changes
- Implementation changes before test additions
- Tests validate the implementation
- Checkpoint validates the story independently

### Parallel Opportunities

- **Phase 1**: T001, T002, T003, T004 are all independent baseline/lint tasks — run in parallel
- **Phase 2**: T005 is the primary audit; T006–T010 can all run in parallel after T005
- **Phase 3 (US2)**: T013 and T014 can run in parallel (different files); T015 and T016 can run in parallel
- **Phase 4 (US3)**: T020 and T021 can run in parallel (different test files)
- **Phase 5 (US4)**: T022, T023, T024 can all run in parallel (different component files)
- **Phase 6 (US5)**: T028–T031 are independent verification tasks — run in parallel
- **Phase 7 (US6)**: T034 and T035 can run in parallel (different documentation sections)
- **Cross-phase**: US2 (Phase 3), US3 (Phase 4), and US4 (Phase 5) can proceed in parallel once Phase 2 completes

---

## Parallel Example: User Story 2 (Backend API Reduction)

```bash
# Sequential dependency chain:
T011 → T012 → T015  (board.py changes then tests)

# Parallel tasks (different files, no dependencies):
T013 (service.py verification) ‖ T014 (polling_loop.py verification) ‖ T016 (test_cache.py)
```

## Parallel Example: User Story 4 (Board Render Optimization)

```bash
# All parallel (different component files, no dependencies):
T022 (BoardColumn parent) ‖ T023 (IssueCard.tsx) ‖ T024 (AddAgentPopover.tsx)

# Sequential (depends on T022/T023 results):
T025 (ProjectsPage.tsx) → T026 (ChatPopup.tsx) → T027 (IssueCard parent)
```

## Parallel Example: Cross-Phase

```bash
# After Phase 2 completes, all three user story phases can start in parallel:
Phase 3 (US2 Backend) ‖ Phase 4 (US3 Frontend Refresh) ‖ Phase 5 (US4 Board Render)

# Phase 6 (US5 Verification) waits for all three to complete
```

---

## Implementation Strategy

### MVP First (User Story 2 Only)

1. Complete Phase 1: Setup — capture baselines
2. Complete Phase 2: Foundational — audit current state
3. Complete Phase 3: User Story 2 — backend API reduction
4. **STOP and VALIDATE**: Measure idle API calls against baseline (SC-001: ≥50% reduction)
5. If target met → proceed to US3/US4. If not → reassess approach before more work

### Incremental Delivery

1. Setup + Foundational → Baselines captured, audit complete
2. Add User Story 2 (Backend API) → Measure → Validate SC-001, SC-002, SC-003 (MVP!)
3. Add User Story 3 (Frontend Refresh) → Measure → Validate SC-004
4. Add User Story 4 (Board Render) → Profile → Validate SC-005
5. Add User Story 5 (Verification) → Full before/after comparison → Validate SC-006, SC-007, SC-008
6. Add User Story 6 (Planning) → Document second-wave if needed
7. Each story adds measurable value without breaking previous optimizations

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational audit is done:
   - Developer A: User Story 2 (Backend API) — `solune/backend/`
   - Developer B: User Story 3 (Frontend Refresh) — `solune/frontend/src/hooks/`
   - Developer C: User Story 4 (Board Render) — `solune/frontend/src/components/` + `src/pages/`
3. Stories complete and validate independently
4. Developer D (or any): User Story 5 verification after A, B, C complete

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- User Story 1 (Baselines) is embedded in Phases 1–2 rather than a separate implementation phase, since baseline capture is a prerequisite activity, not an optimization
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new runtime dependencies allowed in first pass (plan.md constraint)
- Avoid: board virtualization, service decomposition, new dependencies unless baseline metrics prove them necessary
