# Tasks: Performance Review

**Input**: Design documents from `/specs/001-performance-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly required by FR-015 and FR-016. Test tasks extend existing test files — no new test framework.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app monorepo**: `solune/backend/src/`, `solune/frontend/src/`
- **Backend tests**: `solune/backend/tests/unit/`
- **Frontend tests**: colocated in `solune/frontend/src/hooks/`, `solune/frontend/src/components/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, environment verification, and baseline documentation structure

- [x] T001 Create baseline report template at specs/001-performance-review/baselines/baseline-report.md with sections for each metric from data-model.md E-004 (idle API calls, board cache cost, WebSocket idle events, render times, rerender counts, event fire rates, network request counts)
- [x] T002 [P] Verify backend dev environment: run `cd solune/backend && pip install -e ".[dev]" && pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --timeout=30` and record pass/fail counts
- [x] T003 [P] Verify frontend dev environment: run `cd solune/frontend && npm install && npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx` and record pass/fail counts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Audit current implementation state (FR-003) to confirm which optimizations are already landed and identify remaining gaps. This phase MUST complete before any optimization work begins.

**⚠️ CRITICAL**: No user story work (Phases 4–8) can begin until this phase is complete

- [x] T004 Audit backend cache implementation state by inspecting solune/backend/src/services/cache.py — verify InMemoryCache TTL defaults (expect 300s), CacheEntry.data_hash field, cached_fetch() hash comparison, and stale fallback behavior. Document findings in baseline report per R-001
- [x] T005 [P] Audit WebSocket change detection by inspecting solune/backend/src/api/projects.py — verify hash comparison suppresses unchanged `refresh` messages, confirm stale revalidation counter exists, and identify any gaps per R-002
- [x] T006 [P] Audit polling loop behavior by inspecting solune/backend/src/services/copilot_polling/polling_loop.py — verify rate-limit thresholds (pause at 50, slow at 200, skip expensive at 100), backoff behavior, and whether polling can trigger board cache invalidation per R-003
- [x] T007 [P] Audit frontend query invalidation by inspecting solune/frontend/src/hooks/useRealTimeSync.ts — verify WebSocket message handlers invalidate only `['projects', projectId, 'tasks']`, identify whether polling fallback path uses broader invalidation per R-002 gap
- [x] T008 [P] Audit frontend refresh policy by inspecting solune/frontend/src/hooks/useBoardRefresh.ts and solune/frontend/src/hooks/useProjectBoard.ts — verify auto-refresh suppression when WebSocket connected, adaptive polling interaction, debounce window (2s), and staleTime settings per R-004 and R-007
- [x] T009 [P] Audit frontend rendering by inspecting solune/frontend/src/components/board/IssueCard.tsx, solune/frontend/src/components/board/BoardColumn.tsx, solune/frontend/src/pages/ProjectsPage.tsx, solune/frontend/src/components/chat/ChatPopup.tsx, and solune/frontend/src/components/board/AddAgentPopover.tsx — identify missing memoization, unthrottled event listeners, and repeated derived-data computation per R-005
- [x] T010 Document audit findings as implementation-state gap analysis in specs/001-performance-review/baselines/baseline-report.md — mark each item from FR-003 as fully landed, partially landed, or missing. This determines the scope of work for Phases 4–7

**Checkpoint**: Implementation state fully documented. Gap analysis determines which tasks in subsequent phases are needed vs. already completed.

---

## Phase 3: User Story 1 — Establish Performance Baselines (Priority: P1) 🎯 MVP

**Goal**: Capture and document backend and frontend performance baselines before any optimization code changes, providing the before-and-after foundation for all subsequent stories (FR-001, FR-002).

**Independent Test**: Run the measurement procedure against the unmodified codebase and produce a baseline report that includes all metrics from E-004 (data-model.md). No code changes are needed — this is a measurement-only phase.

### Implementation for User Story 1

- [x] T011 [US1] Capture backend idle API call count: open a board, leave idle for 5 minutes, count outbound GitHub API calls using backend logging. Record value in specs/001-performance-review/baselines/baseline-report.md under metric `idle_api_calls_5min`
- [x] T012 [P] [US1] Capture board endpoint warm-cache and cold-cache request cost: issue board requests with empty cache and warm cache, count GitHub API calls for each. Record in specs/001-performance-review/baselines/baseline-report.md under metrics `board_cold_cache_api_calls` and `board_warm_cache_api_calls`
- [x] T013 [P] [US1] Capture WebSocket idle refresh event count: monitor WebSocket subscription with no upstream data changes for 5 minutes, count `refresh` messages sent. Record in specs/001-performance-review/baselines/baseline-report.md under metric `ws_idle_refresh_count_5min`
- [x] T014 [US1] Capture frontend initial board render baseline: load a representative board (5+ columns, 20+ cards), record initial render time (ms) and component mount count. Record in specs/001-performance-review/baselines/baseline-report.md under metrics `board_initial_render_ms` and `component_mount_count`
- [x] T015 [P] [US1] Capture frontend single-card-update rerender count: trigger one card status change via WebSocket, count components that rerender and network requests triggered. Record in specs/001-performance-review/baselines/baseline-report.md under metrics `single_card_rerender_count` and `ws_task_update_network_requests`
- [x] T016 [P] [US1] Capture drag interaction event fire rate: perform a card drag operation, measure event listener fire frequency (events/second). Record in specs/001-performance-review/baselines/baseline-report.md under metric `drag_event_fires_per_sec`
- [x] T017 [US1] Capture existing test suite timing baseline: run full backend targeted tests (`pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py`) and frontend targeted tests (`vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx`), record pass counts and execution times. Record in specs/001-performance-review/baselines/baseline-report.md
- [x] T018 [US1] Finalize baseline report at specs/001-performance-review/baselines/baseline-report.md — ensure all 10 metrics from E-004 Baseline Metrics Catalog are captured, conditions documented, and board size recorded. This is the reference document for SC-001 through SC-008 verification in Phase 8

**Checkpoint**: At this point, User Story 1 should be fully complete — all baselines documented. No code has been changed yet. All subsequent optimization work is measured against these baselines.

---

## Phase 4: User Story 2 — Reduce Backend API Consumption During Idle Board Viewing (Priority: P1)

**Goal**: Eliminate unnecessary board-data refresh calls to GitHub when data is unchanged, ensure sub-issue cache reuse during non-manual refreshes, and prevent polling fallback from triggering expensive board refreshes (FR-004, FR-005, FR-006, FR-007).

**Independent Test**: Open a board, leave idle for 5 minutes, and confirm the outbound GitHub API call count is at or below the 50% reduction target (SC-001). Automated tests validate cache behavior, change detection, and polling guard conditions.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T019 [P] [US2] Add test in solune/backend/tests/unit/test_cache.py verifying that `cached_fetch()` with unchanged data hash refreshes TTL without replacing value and without triggering an upstream API call (covers FR-004, cache-contract.md Refresh TTL row)
- [x] T020 [P] [US2] Add test in solune/backend/tests/unit/test_api_board.py verifying that a board endpoint request within TTL window returns cached data with zero upstream GitHub API calls (covers FR-007, SC-002, cache-contract.md Serve warm row)
- [x] T021 [P] [US2] Add test in solune/backend/tests/unit/test_api_board.py verifying that automatic (non-manual) board refresh reuses cached sub-issue data and does not fetch sub-issues from GitHub API (covers FR-005, cache-contract.md Sub-Issue Cache Reuse row)
- [x] T022 [P] [US2] Add test in solune/backend/tests/unit/test_copilot_polling.py verifying that a polling cycle that detects no data changes does not trigger board cache invalidation (covers FR-006, R-003 remaining concern)
- [x] T023 [P] [US2] Add test in solune/backend/tests/unit/test_api_board.py verifying that the WebSocket subscription suppresses `refresh` messages when data hash is unchanged (covers FR-004, cache-contract.md WebSocket Change Detection step 4a)

### Implementation for User Story 2

- [x] T024 [US2] Verify and tighten WebSocket change detection in solune/backend/src/api/projects.py — ensure hash comparison correctly suppresses unchanged `refresh` messages per cache-contract.md steps 1–5 and stale revalidation counter resets on actual change
- [x] T025 [US2] Verify and tighten sub-issue cache reuse in solune/backend/src/services/github_projects/service.py — ensure `get_sub_issues()` or equivalent checks cache before fetching, and that non-manual refresh paths skip sub-issue API calls per cache-contract.md Sub-Issue Cache rules
- [x] T026 [US2] Verify and tighten board endpoint cache behavior in solune/backend/src/api/board.py — ensure warm-cache requests return without upstream API calls, manual refresh (`refresh=true`) correctly deletes cache entries, and status updates invalidate board cache per cache-contract.md Board Data Cache table
- [x] T027 [US2] Verify and tighten polling fallback behavior in solune/backend/src/services/copilot_polling/polling_loop.py — ensure polling steps that detect no changes do not trigger board cache invalidation, and rate-limit-aware step skipping is correctly applied per cache-contract.md Rate-Limit-Aware Behavior table
- [x] T028 [US2] Run targeted backend tests: `cd solune/backend && pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --timeout=30` — all tests including new ones from T019–T023 must pass

**Checkpoint**: At this point, User Story 2 should be fully functional. Backend idle API consumption is reduced. Run the idle board measurement from T011 and compare against baseline to verify SC-001 target (≥50% reduction).

---

## Phase 5: User Story 3 — Decouple Frontend Refresh Paths (Priority: P2)

**Goal**: Update real-time and fallback refresh paths so lightweight task updates stay decoupled from the expensive board data query. Enforce a single coherent refresh policy across all refresh sources per refresh-policy.md (FR-008, FR-009, FR-010, FR-011).

**Independent Test**: Trigger a lightweight task update via WebSocket and confirm via network inspection that only the Task Query is invalidated, not the Board Query. Verify manual refresh still bypasses all caches.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T029 [P] [US3] Add test in solune/frontend/src/hooks/useRealTimeSync.test.tsx verifying that polling fallback uses selective invalidation (Task Query only) for task-level changes, not full Board Query invalidation (covers FR-009, refresh-policy.md Polling Fallback row 2, R-002 gap)
- [x] T030 [P] [US3] Add test in solune/frontend/src/hooks/useRealTimeSync.test.tsx verifying that WebSocket `task_update` messages invalidate only `['projects', projectId, 'tasks']` and never `['board', 'data', projectId]` (covers FR-008, refresh-policy.md WebSocket Messages table)
- [x] T031 [P] [US3] Add test in solune/frontend/src/hooks/useBoardRefresh.test.tsx verifying that manual refresh bypasses all caches with `refresh=true` and is not debounced (covers FR-010, refresh-policy.md Manual Refresh table)
- [x] T032 [P] [US3] Add test in solune/frontend/src/hooks/useBoardRefresh.test.tsx verifying that auto-refresh timer is suppressed when WebSocket is connected (covers FR-011, refresh-policy.md Auto-Refresh Timer table row 1)

### Implementation for User Story 3

- [x] T033 [US3] Fix polling fallback selective invalidation in solune/frontend/src/hooks/useRealTimeSync.ts — ensure polling fallback invalidates only Task Query (`['projects', projectId, 'tasks']`) for task-level changes, matching WebSocket handler behavior per refresh-policy.md section 2 and R-002 identified gap
- [x] T034 [US3] Verify WebSocket message handlers in solune/frontend/src/hooks/useRealTimeSync.ts — confirm all message types (`initial_data`, `refresh`, `task_update`, `task_created`, `status_changed`, `auto_merge_completed`) use selective invalidation per refresh-policy.md section 1 table
- [x] T035 [US3] Verify and enforce adaptive polling deferral in solune/frontend/src/hooks/useProjectBoard.ts — ensure `refetchInterval` is extended or paused when WebSocket is connected per refresh-policy.md section 5 and R-007 recommendation
- [x] T036 [US3] Verify refresh policy coherence across solune/frontend/src/hooks/useRealTimeSync.ts, solune/frontend/src/hooks/useBoardRefresh.ts, and solune/frontend/src/hooks/useProjectBoard.ts — ensure precedence rules from refresh-policy.md are enforced: manual refresh always wins, debounce deduplicates non-manual triggers, WebSocket suppresses auto-refresh and adaptive polling
- [x] T037 [US3] Run targeted frontend tests: `cd solune/frontend && npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx` — all tests including new ones from T029–T032 must pass

**Checkpoint**: At this point, User Story 3 should be fully functional. Lightweight task updates no longer trigger full board reloads. Run the network inspection from T015 and compare against baseline to verify SC-003.

---

## Phase 6: User Story 4 — Optimize Frontend Board Rendering (Priority: P2)

**Goal**: Reduce rendering costs in board and chat surfaces through low-risk optimizations: memoize heavy components, stabilize props, memoize derived data, and throttle hot event listeners (FR-012, FR-013, FR-014). No new dependencies or virtualization.

**Independent Test**: Profile the board during common interactions (drag, scroll, popover open) and confirm that rerender counts and event-listener fire rates are reduced compared to baseline (SC-004).

### Implementation for User Story 4

- [x] T038 [P] [US4] Wrap IssueCard component with React.memo in solune/frontend/src/components/board/IssueCard.tsx — add shallow prop comparison to skip rerenders when card data is unchanged (covers FR-012, R-005 recommendation)
- [x] T039 [P] [US4] Wrap BoardColumn component with React.memo in solune/frontend/src/components/board/BoardColumn.tsx — add shallow prop comparison to skip rerenders when column data and card list are unchanged (covers FR-012, R-005 recommendation)
- [x] T040 [US4] Memoize board-level derived data (sorting, grouping, aggregation) with useMemo in solune/frontend/src/pages/ProjectsPage.tsx — ensure derived data recomputes only when underlying board data reference changes (covers FR-014, R-005 recommendation)
- [x] T041 [US4] Stabilize callback props passed to IssueCard and BoardColumn using useCallback in parent components (solune/frontend/src/pages/ProjectsPage.tsx and/or solune/frontend/src/components/board/BoardColumn.tsx) — prevent React.memo bypass from unstable function references (covers FR-012, R-005 recommendation)
- [x] T042 [P] [US4] Throttle drag event listeners in solune/frontend/src/components/chat/ChatPopup.tsx — use requestAnimationFrame or 16ms throttle for drag position updates to limit fire rate to ~60fps (covers FR-013, R-005 recommendation)
- [x] T043 [P] [US4] Throttle popover positioning listeners in solune/frontend/src/components/board/AddAgentPopover.tsx — debounce or throttle position recalculation to prevent excessive layout recalculations (covers FR-013, R-005 recommendation)
- [x] T044 [US4] Run frontend lint and type-check: `cd solune/frontend && npm run lint && npm run type-check` — verify all rendering optimizations pass ESLint and TypeScript checks
- [x] T045 [US4] Run full frontend test suite: `cd solune/frontend && npm run test` — verify rendering optimizations do not break existing component behavior

**Checkpoint**: At this point, User Story 4 should be fully functional. Board interactions are visually smoother. Run the profiling from T014–T016 and compare against baseline to verify SC-004.

---

## Phase 7: User Story 5 — Verification and Regression Coverage (Priority: P3)

**Goal**: Confirm all optimizations from US2–US4 are proven by automated tests and at least one manual verification pass, and that regression coverage prevents future degradation (FR-015, FR-016).

**Independent Test**: Run the full automated test suite (backend and frontend) and one manual network/profile pass, comparing all results to baselines from US1.

### Tests for User Story 5

- [x] T046 [P] [US5] Verify all backend tests pass: `cd solune/backend && pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --timeout=30` — confirm all existing and new tests from T019–T023 pass with optimizations applied (covers FR-015, SC-005)
- [x] T047 [P] [US5] Verify all frontend tests pass: `cd solune/frontend && npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx` — confirm all existing and new tests from T029–T032 pass with optimizations applied (covers FR-015, SC-005)

### Implementation for User Story 5

- [x] T048 [US5] Run full backend CI validation: `cd solune/backend && ruff check src tests && ruff format --check src tests && pyright src && pytest --cov=src --cov-report=term-missing --ignore=tests/property --ignore=tests/fuzz --ignore=tests/chaos --ignore=tests/concurrency` — confirm no regressions across the entire backend (covers SC-005)
- [x] T049 [US5] Run full frontend CI validation: `cd solune/frontend && npm run lint && npm run type-check && npm run test && npm run build` — confirm no regressions across the entire frontend (covers SC-005)
- [x] T050 [US5] Perform manual end-to-end verification pass — confirm WebSocket updates refresh task data promptly, fallback polling does not cause unnecessary refreshes, manual refresh bypasses caches correctly, and board interactions remain responsive. Document results in specs/001-performance-review/baselines/baseline-report.md post-optimization section (covers FR-016, SC-007)
- [x] T051 [US5] Capture post-optimization backend metrics: repeat T011–T013 measurements (idle API calls, cache cost, WebSocket idle events) and record in specs/001-performance-review/baselines/baseline-report.md post-optimization section. Compare against baselines: SC-001 target is ≥50% fewer idle API calls, SC-002 target is zero warm-cache API calls
- [x] T052 [US5] Capture post-optimization frontend metrics: repeat T014–T016 measurements (render time, rerender count, event fire rate) and record in specs/001-performance-review/baselines/baseline-report.md post-optimization section. Compare against baselines: SC-003 target is no full board reload on single task update, SC-004 target is measurable rerender reduction
- [x] T053 [US5] Write verification summary in specs/001-performance-review/baselines/baseline-report.md — record pass/fail for each success criterion SC-001 through SC-008, note whether targets were met, and flag any criteria requiring second-wave work

**Checkpoint**: At this point, all optimizations are proven by automated tests and manual verification. Baselines and post-optimization metrics are documented side-by-side.

---

## Phase 8: User Story 6 — Optional Second-Wave Planning (Priority: P4)

**Goal**: If first-pass optimizations do not meet performance targets, document a follow-on plan identifying structural changes to pursue. This phase is conditional — skip entirely if all SC targets are met in Phase 7.

**Independent Test**: Review the follow-on plan for completeness: must identify specific structural changes with expected impact and effort estimates.

### Implementation for User Story 6

- [x] T054 [US6] Review SC-001 through SC-008 results from T053 — determine whether any targets were NOT met
- [x] T055 [US6] If backend idle API targets (SC-001) not met: document recommended deeper consolidation in GitHub project fetching/polling pipeline in specs/001-performance-review/baselines/second-wave-plan.md with estimated effort
- [x] T056 [US6] If frontend large-board lag persists (SC-004 not met): document recommended board virtualization approach (react-window or react-virtuoso) in specs/001-performance-review/baselines/second-wave-plan.md with estimated effort
- [x] T057 [US6] If repeated performance work is anticipated: document recommended lightweight instrumentation (board refresh cost logging, sub-issue cache hit rate, refresh-source attribution) in specs/001-performance-review/baselines/second-wave-plan.md

**Checkpoint**: Second-wave plan is documented (or skipped if all targets met). Team has a clear path forward.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation across all stories

- [x] T058 [P] Run full backend CI validation suite: `cd solune/backend && pip-audit . --skip-editable --ignore-vuln CVE-2026-4539 && ruff check src tests && ruff format --check src tests && bandit -r src/ -ll -ii --skip B104,B608 && pyright src && pytest --cov=src --cov-report=term-missing --ignore=tests/property --ignore=tests/fuzz --ignore=tests/chaos --ignore=tests/concurrency`
- [x] T059 [P] Run full frontend CI validation suite: `cd solune/frontend && npm audit --audit-level=high && npm run lint && npm run type-check && npm run test && npm run build`
- [x] T060 Code cleanup — remove any temporary logging, debug statements, or commented-out code introduced during optimization work across all modified files
- [x] T061 Run quickstart.md validation — execute all commands from specs/001-performance-review/quickstart.md and confirm they succeed
- [x] T062 Verify no new external dependencies introduced (FR-017, SC-008) — check solune/backend/pyproject.toml and solune/frontend/package.json for any additions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 / Baselines (Phase 3)**: Depends on Foundational phase audit completion — BLOCKS all optimization work
- **User Story 2 / Backend API (Phase 4)**: Depends on User Story 1 baselines being captured
- **User Story 3 / Frontend Refresh (Phase 5)**: Depends on User Story 1 baselines being captured; can proceed IN PARALLEL with Phase 4
- **User Story 4 / Frontend Rendering (Phase 6)**: Depends on User Story 1 baselines; can proceed IN PARALLEL with Phases 4 and 5
- **User Story 5 / Verification (Phase 7)**: Depends on completion of Phases 4, 5, AND 6
- **User Story 6 / Second-Wave (Phase 8)**: Depends on Phase 7 verification results — CONDITIONAL (skip if all targets met)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. **BLOCKS all optimization stories.**
- **User Story 2 (P1)**: Can start after US1 baselines — Backend-only changes, independent of frontend stories
- **User Story 3 (P2)**: Can start after US1 baselines — Frontend-only changes, independent of backend story (US2). **Can run IN PARALLEL with US2.**
- **User Story 4 (P2)**: Can start after US1 baselines — Frontend rendering changes, independent of refresh-path changes (US3). **Can run IN PARALLEL with US2 and US3** (different files)
- **User Story 5 (P3)**: Depends on US2, US3, and US4 completion — Verification cannot proceed until all optimizations are applied
- **User Story 6 (P4)**: Depends on US5 results — Conditional work, only needed if targets are not met

### Within Each User Story

- Tests (FR-015, FR-016) MUST be written and FAIL before implementation
- Audit/verify before modifying — understand current state first
- Core implementation before integration
- Run targeted tests after implementation
- Story complete before verification phase

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational audit tasks marked [P] can run in parallel (T005–T009)
- Within US1: baseline measurements T012/T013, T015/T016 can run in parallel
- Within US2: all test tasks T019–T023 can run in parallel
- Within US3: all test tasks T029–T032 can run in parallel
- Within US4: component memoization T038/T039 can run in parallel; listener throttling T042/T043 can run in parallel
- **Cross-story parallelism**: US2 (backend) + US3 (frontend refresh) + US4 (frontend rendering) can all proceed in parallel after US1 baselines, touching different files
- Within US5: backend verification T046 and frontend verification T047 can run in parallel

---

## Parallel Example: User Story 2 (Backend API)

```bash
# Launch all test tasks for US2 together (different test files):
Task T019: "Add cached_fetch unchanged hash test in tests/unit/test_cache.py"
Task T020: "Add warm-cache zero API calls test in tests/unit/test_api_board.py"
Task T021: "Add sub-issue cache reuse test in tests/unit/test_api_board.py"
Task T022: "Add polling no-invalidation test in tests/unit/test_copilot_polling.py"
Task T023: "Add WS suppression test in tests/unit/test_api_board.py"

# After tests written, implementation tasks T024–T027 can partially overlap
# (different source files: projects.py, service.py, board.py, polling_loop.py)
```

## Parallel Example: Cross-Story Parallelism (Phases 4–6)

```bash
# These three stories touch completely different file sets and can run in parallel:

# Developer A: US2 (Backend) — solune/backend/src/api/, solune/backend/src/services/
Task T024-T028: Backend API consumption fixes

# Developer B: US3 (Frontend Refresh) — solune/frontend/src/hooks/
Task T033-T037: Frontend refresh path fixes

# Developer C: US4 (Frontend Rendering) — solune/frontend/src/components/, solune/frontend/src/pages/
Task T038-T045: Frontend render optimizations
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — audit blocks all stories)
3. Complete Phase 3: User Story 1 — Baselines
4. **STOP and VALIDATE**: Baseline report is complete with all 10 metrics
5. This baseline report is the MVP deliverable — all subsequent optimization is measured against it

### Incremental Delivery

1. Complete Setup + Foundational + US1 → Baselines captured (MVP!)
2. Add US2 (Backend API) → Run targeted backend tests → Measure idle API improvement
3. Add US3 (Frontend Refresh) → Run targeted frontend tests → Verify decoupled refresh paths
4. Add US4 (Frontend Rendering) → Profile board interactions → Verify smoother UI
5. Add US5 (Verification) → Full test suite + manual pass → Prove all improvements
6. Each story adds measurable value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + US1 together (sequential — measurement is the gating deliverable)
2. Once US1 baselines are captured:
   - Developer A: User Story 2 (backend API — Python files only)
   - Developer B: User Story 3 (frontend refresh — hook files only)
   - Developer C: User Story 4 (frontend rendering — component/page files only)
3. All three stories complete independently, touching non-overlapping files
4. Team reconvenes for US5 (verification) once all three stories are done

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are REQUIRED per FR-015 and FR-016 — write them before implementation
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new external dependencies allowed (FR-017, SC-008)
- Board virtualization and major service decomposition are explicitly out of scope (FR-017) unless US5 verification proves they are necessary
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
