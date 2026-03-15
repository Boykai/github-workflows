# Tasks: Performance Review

**Input**: Design documents from `/specs/001-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED per FR-014 and SC-008. Test extension tasks are included in the relevant user story phases and in the dedicated verification phase (US6).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- Backend tests: `solune/backend/tests/unit/`
- Frontend tests: co-located with source (e.g., `solune/frontend/src/hooks/*.test.tsx`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create measurement infrastructure and audit checklists before any code changes. No source code modifications in this phase.

- [ ] T001 Create performance measurement checklist document in specs/001-performance-review/checklists/measurement-checklist.md defining metrics, measurement methods, target values (SC-001 through SC-006), and regression thresholds
- [ ] T002 [P] Compile Spec 022 acceptance criteria audit checklist in specs/001-performance-review/checklists/spec-022-audit.md listing each criterion (change detection, cache TTL alignment, sub-issue invalidation, rate-limit-aware polling, inflight coalescing, stale fallback) with pass/fail columns

---

## Phase 2: Foundational — Baselines and Spec 022 Audit (Blocking Prerequisites)

**Purpose**: Capture current performance baselines and confirm Spec 022 implementation status. MUST complete before ANY optimization work begins (FR-001, FR-002).

**⚠️ CRITICAL**: No optimization code changes (Phases 3–7) can begin until this phase is complete. Baselines define success criteria and regression guardrails.

### User Story 1 — Establish Performance Baselines (Priority: P1)

**Goal**: Record backend and frontend performance baselines on a representative board (50–100 tasks across 4–8 columns) so improvements are provable and regressions detectable.

**Independent Test**: All baseline values documented in measurement checklist with current value, target improvement, and regression threshold for each metric.

- [ ] T003 [US1] Record backend idle baseline: start backend, open a board, monitor structlog output for outbound GitHub API calls over a 5-minute idle window, and document call count in specs/001-performance-review/checklists/measurement-checklist.md
- [ ] T004 [P] [US1] Record backend cache-hit baseline: perform a board refresh with cold cache (count outbound calls), then with warm cache (count outbound calls), and document both in specs/001-performance-review/checklists/measurement-checklist.md
- [ ] T005 [P] [US1] Record frontend load baseline: profile board load with React DevTools Profiler on a 50+ task board, record time-to-interactive, render count, and network request count in specs/001-performance-review/checklists/measurement-checklist.md
- [ ] T006 [P] [US1] Record frontend interaction baseline: profile drag-card, click-card, and open-task-detail interactions with React DevTools Profiler, record rerender counts and interaction latencies in specs/001-performance-review/checklists/measurement-checklist.md
- [ ] T007 [P] [US1] Record real-time sync idle baseline: observe WebSocket/polling network activity on an idle board for 5 minutes, document query invalidation count and data transfer events in specs/001-performance-review/checklists/measurement-checklist.md
- [ ] T008 [US1] Finalize measurement checklist: ensure every metric (SC-001 through SC-006) has a documented current value, target value, and regression threshold in specs/001-performance-review/checklists/measurement-checklist.md

### User Story 2 — Confirm Current State Against Spec 022 (Priority: P1)

**Goal**: Audit every Spec 022 acceptance criterion against the live codebase and classify each as fully implemented, partially implemented, or not started, so optimization targets only remaining gaps.

**Independent Test**: Audit checklist completed with status for each criterion; only partially or not-started items feed into optimization scope.

- [ ] T009 [P] [US2] Audit board cache TTL alignment: verify 300-second TTL in solune/backend/src/api/board.py and confirm stale-data serving during cache window; record in specs/001-performance-review/checklists/spec-022-audit.md
- [ ] T010 [P] [US2] Audit sub-issue cache invalidation on manual refresh: verify cache clearing when refresh=True in solune/backend/src/api/board.py against test_manual_refresh_clears_sub_issue_caches in solune/backend/tests/unit/test_api_board.py; record in audit checklist
- [ ] T011 [P] [US2] Audit WebSocket change detection: verify data_hash comparison in 30-second periodic check in solune/backend/src/api/projects.py and confirm unchanged data suppresses client pushes; record in audit checklist
- [ ] T012 [P] [US2] Audit rate-limit-aware polling: verify pause thresholds, expensive-step skipping, and adaptive idle backoff (up to 300s) in solune/backend/src/services/copilot_polling/polling_loop.py; record in audit checklist
- [ ] T013 [P] [US2] Audit inflight request coalescing: verify concurrent GraphQL request deduplication in solune/backend/src/services/github_projects/service.py; record in audit checklist
- [ ] T014 [P] [US2] Audit stale fallback on error: verify cached_fetch() and board endpoint serve expired cache on GitHub API errors in solune/backend/src/services/cache.py and solune/backend/src/api/board.py; record in audit checklist
- [ ] T015 [US2] Summarize Spec 022 audit results in specs/001-performance-review/checklists/spec-022-audit.md with final status per criterion and list of remaining gaps to address

**Checkpoint**: Baselines captured and Spec 022 status confirmed — optimization work can now begin. Only items marked partially/not-started in the audit feed into optimization phases.

---

## Phase 3: User Story 3 — Reduce Idle Backend Service Call Volume (Priority: P1) 🎯 MVP

**Goal**: Eliminate unnecessary outbound GitHub API calls when a board is idle by ensuring WebSocket periodic checks reuse warm cache, sub-issue caches are reused on non-manual refreshes, and duplicate repository resolution is consolidated. Target: ≥ 50% idle call reduction (SC-001), ≥ 30% fewer calls with warm sub-issue cache (SC-002).

**Independent Test**: Open a board, leave idle for 5 minutes, and confirm outbound call count meets SC-001 target. Perform cold-cache then warm-cache board refresh and confirm SC-002 target.

### Tests for User Story 3

- [ ] T016 [P] [US3] Add test asserting warm board cache prevents outbound API calls during WebSocket periodic check in solune/backend/tests/unit/test_api_board.py
- [ ] T017 [P] [US3] Add test asserting sub-issue cache reuse reduces outbound call count on non-manual board refresh in solune/backend/tests/unit/test_api_board.py
- [ ] T018 [P] [US3] Add test asserting unchanged data hash suppresses client push in WebSocket subscription in solune/backend/tests/unit/test_api_board.py

### Implementation for User Story 3

- [ ] T019 [US3] Optimize WebSocket subscription periodic check to reuse warm board cache instead of force_refresh on 30-second interval in solune/backend/src/api/projects.py (FR-003, FR-004)
- [ ] T020 [US3] Verify and fix sub-issue cache reuse on non-manual refresh path (refresh=false) in solune/backend/src/api/board.py (FR-005)
- [ ] T021 [P] [US3] Consolidate duplicate resolve_repository() calls in solune/backend/src/api/workflow.py to reuse shared utility from solune/backend/src/utils.py (R-001 gap 4)
- [ ] T022 [US3] Verify that background polling in solune/backend/src/services/copilot_polling/polling_loop.py does not trigger unnecessary board-level refreshes when no relevant changes are detected (FR-007)
- [ ] T023 [US3] Run backend linter and type checks: cd solune/backend && python -m ruff check src/ && python -m pyright src/
- [ ] T024 [US3] Run targeted backend tests: cd solune/backend && python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v

**Checkpoint**: Backend idle call volume meets SC-001 and SC-002 targets. All existing backend tests still pass (SC-007).

---

## Phase 4: User Story 4 — Decouple Lightweight Updates from Full Board Refreshes (Priority: P2)

**Goal**: Ensure real-time task updates appear quickly without triggering full board data reloads, fallback polling remains scoped to tasks-only invalidation, and all refresh sources follow a single coherent policy. Target: single-task update < 2s (SC-003), zero unnecessary full refreshes during polling (SC-004).

**Independent Test**: Move a card to a different status column via real-time update; confirm only the tasks query updates (not board data). Activate fallback polling; confirm no board data invalidation occurs. Trigger auto-refresh, manual refresh, and polling simultaneously; confirm deduplication.

### Tests for User Story 4

- [ ] T025 [P] [US4] Add test asserting fallback polling invalidates only tasks query key, never board data query key in solune/frontend/src/hooks/useRealTimeSync.test.tsx (FR-006)
- [ ] T026 [P] [US4] Add test asserting WebSocket-to-polling transition produces at most one tasks query invalidation within 30 seconds in solune/frontend/src/hooks/useRealTimeSync.test.tsx (FR-010)
- [ ] T027 [P] [US4] Add test asserting simultaneous auto-refresh + polling triggers are deduplicated in solune/frontend/src/hooks/useBoardRefresh.test.tsx (FR-010)

### Implementation for User Story 4

- [ ] T028 [US4] Verify and fix fallback polling scope: ensure polling only invalidates tasks query and never board data in solune/frontend/src/hooks/useRealTimeSync.ts (FR-006, FR-008)
- [ ] T029 [US4] Verify refresh policy coherence: audit interactions between WebSocket updates, fallback polling, auto-refresh timer, and manual refresh in solune/frontend/src/hooks/useBoardRefresh.ts and solune/frontend/src/hooks/useRealTimeSync.ts (FR-010)
- [ ] T030 [US4] Verify useProjectBoard query ownership and invalidation strategy align with refresh policy in solune/frontend/src/hooks/useProjectBoard.ts
- [ ] T031 [US4] Run frontend linter and type checks: cd solune/frontend && npm run lint && npm run type-check
- [ ] T032 [US4] Run targeted frontend tests: cd solune/frontend && npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx

**Checkpoint**: Lightweight updates are decoupled from full board refreshes. SC-003 and SC-004 met. Existing frontend tests pass (SC-007).

---

## Phase 5: User Story 5 — Improve Board Rendering Responsiveness (Priority: P2)

**Goal**: Reduce unnecessary rerenders and rationalize event listeners so board interactions feel smooth on 50+ task boards. Target: measurable interaction latency improvement (SC-005), rerenders scoped to affected card + container only (SC-006).

**Independent Test**: Profile board interactions before and after changes on a 50+ task board. Confirm rerender count per interaction is reduced and limited to affected components. Confirm drag-card, click-card, and popover interactions do not trigger unrelated component rerenders.

### Implementation for User Story 5

- [ ] T033 [US5] Audit and stabilize all useMemo dependencies for derived computations (grid template, hero stats, pipeline lookup, stage map, total-items aggregation) in solune/frontend/src/pages/ProjectsPage.tsx (FR-012)
- [ ] T034 [P] [US5] Verify memo() effectiveness for BoardColumn: ensure props passed to memoized component are stable references (not recreated per render) in solune/frontend/src/components/board/BoardColumn.tsx (FR-011)
- [ ] T035 [P] [US5] Verify memo() effectiveness for IssueCard: ensure props passed to memoized component are stable references (not recreated per render) in solune/frontend/src/components/board/IssueCard.tsx (FR-011)
- [ ] T036 [P] [US5] Verify RAF throttling and listener cleanup for drag-to-resize in solune/frontend/src/components/chat/ChatPopup.tsx (FR-013)
- [ ] T037 [P] [US5] Verify RAF throttling and listener cleanup for popover positioning in solune/frontend/src/components/agents/AddAgentPopover.tsx (FR-013)
- [ ] T038 [US5] Fix any unstable props, missing memoization, or unthrottled listeners identified in T033–T037 across solune/frontend/src/pages/ProjectsPage.tsx, solune/frontend/src/components/board/BoardColumn.tsx, solune/frontend/src/components/board/IssueCard.tsx, solune/frontend/src/components/chat/ChatPopup.tsx, and solune/frontend/src/components/agents/AddAgentPopover.tsx
- [ ] T039 [US5] Run frontend linter, type checks, and build: cd solune/frontend && npm run lint && npm run type-check && npm run build
- [ ] T040 [US5] Run full frontend test suite: cd solune/frontend && npx vitest run

**Checkpoint**: Board interactions show measurable improvement on 50+ task boards (SC-005). Rerenders scoped to affected components (SC-006). All frontend tests pass.

---

## Phase 6: User Story 6 — Verify Improvements and Prevent Regressions (Priority: P3)

**Goal**: Extend automated test coverage for performance-critical paths and perform manual verification pass to confirm real-world improvements match targets. Deliver SC-008 regression coverage.

**Independent Test**: Run full backend and frontend test suites — all pass. Manual profiling pass shows improvements against baselines from Phase 2.

### Tests for User Story 6

- [ ] T041 [P] [US6] Extend cache behavior tests: add assertion that warm cache prevents redundant outbound calls and TTLs align with expected values in solune/backend/tests/unit/test_cache.py (SC-008)
- [ ] T042 [P] [US6] Extend board endpoint tests: add assertion that sub-issue cache reuse on non-manual refresh reduces call count in solune/backend/tests/unit/test_api_board.py (SC-008)
- [ ] T043 [P] [US6] Extend polling tests: add idle-board minimal-activity scenario asserting no unnecessary board-level refreshes in solune/backend/tests/unit/test_copilot_polling.py (SC-008)
- [ ] T044 [P] [US6] Extend real-time sync tests: add assertions for polling-to-WebSocket transition safety and scoped invalidation in solune/frontend/src/hooks/useRealTimeSync.test.tsx (SC-008)
- [ ] T045 [P] [US6] Extend board refresh tests: add assertions for timer reset on external triggers and deduplication across simultaneous sources in solune/frontend/src/hooks/useBoardRefresh.test.tsx (SC-008)

### Verification for User Story 6

- [ ] T046 [US6] Run full backend test suite: cd solune/backend && python -m pytest tests/ -v
- [ ] T047 [P] [US6] Run full frontend test suite: cd solune/frontend && npx vitest run
- [ ] T048 [US6] Perform manual backend network profiling pass: monitor idle board outbound calls via solune/backend/ structlog output for 5 minutes and compare against Phase 2 baseline (SC-001)
- [ ] T049 [P] [US6] Perform manual frontend rendering profiling pass: profile board interactions in solune/frontend/ with React DevTools Profiler and compare rerender counts and latencies against Phase 2 baseline (SC-005, SC-006)
- [ ] T050 [US6] Document post-optimization measurements and before/after comparison in specs/001-performance-review/checklists/measurement-checklist.md

**Checkpoint**: All tests pass (SC-007). Regression coverage delivered (SC-008). Manual verification confirms real-world improvements.

---

## Phase 7: User Story 7 — Scope Boundary and Follow-On Plan (Priority: P3)

**Goal**: Confirm no out-of-scope changes were introduced and produce follow-on documentation if targets were not fully met. Deliver SC-009, SC-010.

**Independent Test**: Review delivered changes — no new external dependencies, no virtualization, no major service decomposition. If targets not met, follow-on plan exists with data-driven recommendations.

- [ ] T051 [US7] Verify no new external dependencies were introduced: check solune/backend/pyproject.toml and solune/frontend/package.json against pre-optimization versions (SC-009, FR-015)
- [ ] T052 [US7] If SC-001 through SC-006 targets are not fully met, create follow-on plan in specs/001-performance-review/follow-on-plan.md with specific recommendations and supporting measurement data (SC-010, FR-016)
- [ ] T053 [P] [US7] Document instrumentation recommendations for future regression visibility (refresh cost tracking, cache hit rates, refresh-source attribution) in specs/001-performance-review/follow-on-plan.md

**Checkpoint**: Scope boundaries respected. Follow-on plan documented if needed.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all phases, documentation updates, and sign-off.

- [ ] T054 Run full backend linter and type checks: cd solune/backend && python -m ruff check src/ && python -m pyright src/
- [ ] T055 [P] Run full frontend linter, type checks, and build: cd solune/frontend && npm run lint && npm run type-check && npm run build
- [ ] T056 Run full backend test suite for final regression check: cd solune/backend && python -m pytest tests/ -v
- [ ] T057 [P] Run full frontend test suite for final regression check: cd solune/frontend && npx vitest run
- [ ] T058 Final measurement checklist sign-off: confirm all SC-001 through SC-010 criteria are documented as met or addressed in specs/001-performance-review/checklists/measurement-checklist.md
- [ ] T059 Run quickstart.md validation: execute verification checklist from specs/001-performance-review/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all optimization phases**
- **US3 (Phase 3)**: Depends on Phase 2 (baselines and Spec 022 audit)
- **US4 (Phase 4)**: Depends on Phase 2; can run in **parallel** with Phase 3 (different codebase areas: backend vs. frontend)
- **US5 (Phase 5)**: Depends on Phase 4 (refresh-path fixes should land before render optimization to isolate causes)
- **US6 (Phase 6)**: Depends on Phases 3, 4, and 5 (all optimization work must complete before verification)
- **US7 (Phase 7)**: Depends on Phase 6 (scope review requires verification results)
- **Polish (Phase 8)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Can start immediately — produces baselines that gate all optimization
- **US2 (P1)**: Can start after T001 (measurement checklist exists) — can run in **parallel** with US1 frontend baselines
- **US3 (P1)**: Depends on US1 + US2 completion — backend optimization, independent of frontend stories
- **US4 (P2)**: Depends on US1 + US2 completion — frontend optimization, can run in **parallel** with US3
- **US5 (P2)**: Depends on US4 completion — render optimization builds on refresh-path fixes
- **US6 (P3)**: Depends on US3, US4, US5 — verification covers all optimization phases
- **US7 (P3)**: Depends on US6 — scope boundary review uses verification results

### Within Each User Story

- Tests FIRST (when present) — ensure they exist before implementation
- Audit/verify existing behavior before modifying
- Core implementation changes before integration fixes
- Linter/type checks after implementation
- Targeted test runs to validate changes

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different files)
- **Phase 2**: T003–T007 (US1 baselines) and T009–T014 (US2 audits) can run in parallel after T001/T002
- **Phase 2 internal**: All [P]-marked US1 baselines (T004, T005, T006, T007) can run in parallel; all [P]-marked US2 audits (T009–T014) can run in parallel
- **Phase 3 + Phase 4**: Can run in parallel (backend vs. frontend, different files)
- **Phase 3 internal**: T016, T017, T018 (tests) can run in parallel; T021 can run in parallel with T019/T020
- **Phase 4 internal**: T025, T026, T027 (tests) can run in parallel
- **Phase 5 internal**: T034, T035, T036, T037 can run in parallel (different component files)
- **Phase 6 internal**: T041–T045 (test extensions) can run in parallel; T046/T047 can run in parallel; T048/T049 can run in parallel
- **Phase 8**: T054/T055 can run in parallel; T056/T057 can run in parallel

---

## Parallel Example: User Story 3 (Backend Optimization)

```bash
# Launch all tests for US3 together:
Task: T016 "Add warm cache test in solune/backend/tests/unit/test_api_board.py"
Task: T017 "Add sub-issue cache reuse test in solune/backend/tests/unit/test_api_board.py"
Task: T018 "Add data hash suppression test in solune/backend/tests/unit/test_api_board.py"

# Then launch independent implementation tasks:
Task: T019 "Optimize WebSocket periodic check in solune/backend/src/api/projects.py"
Task: T021 "Consolidate resolve_repository() in solune/backend/src/api/workflow.py"  # [P] - different file
```

## Parallel Example: Phase 3 + Phase 4 (Backend + Frontend in Parallel)

```bash
# Developer A (Backend — US3):
Task: T019 "Optimize WebSocket periodic check in projects.py"
Task: T020 "Verify sub-issue cache reuse in board.py"
Task: T021 "Consolidate resolve_repository() in workflow.py"

# Developer B (Frontend — US4, simultaneously):
Task: T028 "Verify fallback polling scope in useRealTimeSync.ts"
Task: T029 "Verify refresh policy coherence in useBoardRefresh.ts"
Task: T030 "Verify useProjectBoard query ownership"
```

---

## Implementation Strategy

### MVP First (User Story 3 Only)

1. Complete Phase 1: Setup (measurement checklist + audit checklist)
2. Complete Phase 2: Foundational (baselines + Spec 022 audit) — **CRITICAL GATE**
3. Complete Phase 3: User Story 3 — backend idle call reduction
4. **STOP and VALIDATE**: Compare idle call count against baseline; confirm SC-001 and SC-002 targets
5. Deploy/demo if backend savings are sufficient for first milestone

### Incremental Delivery

1. Complete Setup + Foundational → Baselines and audit ready
2. Add US3 (backend optimization) → Test independently → ≥ 50% idle reduction (MVP!)
3. Add US4 (refresh decoupling) → Test independently → < 2s task updates, zero unnecessary polling refreshes
4. Add US5 (render optimization) → Test independently → Measurable interaction improvement
5. Add US6 (verification) → Full regression pass → All targets validated
6. Add US7 (scope boundary) → Follow-on plan if needed
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (baselines require system access)
2. Once Foundational is done:
   - Developer A: User Story 3 (backend — Python)
   - Developer B: User Story 4 (frontend — TypeScript)
3. After US3 + US4:
   - Developer A: User Story 6 backend tests (T041–T043, T046, T048)
   - Developer B: User Story 5 (render optimization) → US6 frontend tests (T044–T045, T047, T049)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Baselines (Phase 2) are a hard gate — no optimization code changes before baselines
- Research findings (R-001 through R-006) identified existing implementations; tasks target remaining gaps only
- Many components (BoardColumn, IssueCard, ChatPopup, AddAgentPopover) already have memo()/RAF — tasks verify effectiveness and fix only where needed
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
