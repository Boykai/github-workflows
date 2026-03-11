# Tasks: Performance Review

**Input**: Design documents from `/specs/034-performance-review/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/backend-cache.md`, `contracts/board-endpoints.md`, `contracts/refresh-policy.md`

**Tests**: Required. This feature explicitly mandates regression coverage and manual verification in FR-013 and FR-014.

**Organization**: Tasks are grouped by user story so each increment remains independently implementable and testable while preserving the first-pass, low-risk optimization scope.

## Path Conventions

- Backend source: `backend/src/`
- Backend tests: `backend/tests/`
- Frontend source: `frontend/src/`
- Frontend tests: `frontend/src/**/*.test.tsx`
- Feature docs: `specs/034-performance-review/`

## Summary Table

| Scope | Priority | Task Count | Verification Criteria |
|-------|----------|------------|-----------------------------|
| Setup | — | 3 | Measurement helpers and command workflow are ready across backend, frontend, and feature docs |
| Foundational | — | 4 | Shared instrumentation and query-key scaffolding are in place for all later stories |
| User Story 1 - Baseline Performance Measurement | P1 | 5 | Capture backend and frontend baseline metrics and document them reproducibly |
| User Story 2 - Reduced Backend API Consumption During Idle Board Viewing | P1 | 9 | Idle board viewing shows fewer GitHub API calls with no redundant unchanged refreshes |
| User Story 3 - Coherent Frontend Refresh Policy | P2 | 6 | WebSocket, polling, auto-refresh, and manual refresh follow the documented task-only/full-board policy |
| User Story 4 - Responsive Board Rendering on Interaction | P2 | 7 | Drag, scroll, and popover interactions avoid whole-board rerenders and repeated derived computations |
| User Story 5 - Verification and Regression Coverage | P3 | 5 | Backend/frontend regression suites and manual profile verification confirm the improvements |
| Polish & Cross-Cutting | — | 5 | Contracts, quickstart guidance, and deferred second-wave follow-up notes are aligned |
| **Total** | — | **44** | **25 tasks marked `[P]`; recommended MVP cut = US1 baseline lock + US2 backend idle API reduction** |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the measurement workflow and reusable test helpers that every story depends on.

- [ ] T001 Update measurement workflow, representative board assumptions, and command checklist in `specs/034-performance-review/quickstart.md`
- [ ] T002 [P] Add backend performance assertion helpers for API-call and cache-hit comparisons in `backend/tests/helpers/assertions.py`
- [ ] T003 [P] Add frontend render-count and query-client test helpers in `frontend/src/test/test-utils.tsx`

**Checkpoint**: Backend/frontend measurement scaffolding exists and the feature quickstart reflects the real repo commands.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared audit and instrumentation that blocks all user-story implementation until complete.

**⚠️ CRITICAL**: No user story work should start until this phase is complete.

- [ ] T004 Record Spec 022 audit checkpoints and first-pass scope boundaries in `specs/034-performance-review/research.md`
- [ ] T005 [P] Add board endpoint and cache measurement logging hooks in `backend/src/api/board.py`
- [ ] T006 [P] Add websocket idle-cycle and refresh-cycle measurement logging hooks in `backend/src/api/projects.py`
- [ ] T007 [P] Centralize board and task query-key helpers for selective invalidation in `frontend/src/hooks/useProjectBoard.ts`

**Checkpoint**: Audit notes, backend instrumentation, and frontend query-key scaffolding are ready for story work.

---

## Phase 3: User Story 1 - Baseline Performance Measurement (Priority: P1) 🎯

**Goal**: Establish reproducible backend and frontend baselines before optimization changes are judged complete.

**Independent Test**: Open a representative board, capture idle API activity, board endpoint cost, WebSocket/polling behavior, and frontend render hot spots, then verify the resulting measurements are documented in the feature artifacts.

### Tests for User Story 1

- [ ] T008 [P] [US1] Extend backend baseline coverage for idle board endpoint activity in `backend/tests/unit/test_api_board.py`
- [ ] T009 [P] [US1] Extend frontend baseline profiling coverage for representative board renders in `frontend/src/pages/ProjectsPage.test.tsx`

### Implementation for User Story 1

- [ ] T010 [US1] Document backend baseline measurements and observation steps in `specs/034-performance-review/quickstart.md`
- [ ] T011 [US1] Document frontend baseline measurements and Spec 022 audit findings in `specs/034-performance-review/research.md`
- [ ] T012 [US1] Capture baseline metric tables and pre-optimization thresholds in `specs/034-performance-review/contracts/board-endpoints.md`

**Checkpoint**: Pre-change baselines are locked, reproducible, and ready to compare against later story outcomes.

---

## Phase 4: User Story 2 - Reduced Backend API Consumption During Idle Board Viewing (Priority: P1)

**Goal**: Eliminate redundant backend GitHub API work during idle board viewing while preserving manual refresh and stale fallback behavior.

**Independent Test**: Leave a board idle with WebSocket connected and with fallback polling active, then verify that unchanged cycles do not trigger repeated expensive refreshes and that warm sub-issue caches measurably reduce GitHub API calls.

### Tests for User Story 2

- [ ] T013 [P] [US2] Extend warm-cache and forced-refresh coverage in `backend/tests/unit/test_api_board.py`
- [ ] T014 [P] [US2] Extend websocket zero-change cycle coverage in `backend/tests/unit/test_api_projects.py`
- [ ] T015 [P] [US2] Extend idle polling no-full-refresh coverage in `backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 2

- [ ] T016 [US2] Clear board and related sub-issue cache keys on manual refresh in `backend/src/api/board.py`
- [ ] T017 [US2] Reuse warm sub-issue cache entries before refetching GitHub data in `backend/src/services/github_projects/service.py`
- [ ] T018 [US2] Skip unchanged websocket refresh cycles before expensive board fetches in `backend/src/api/projects.py`
- [ ] T019 [US2] Gate fallback polling escalation behind lightweight change detection in `backend/src/services/copilot_polling/polling_loop.py`
- [ ] T020 [P] [US2] Replace duplicate repository resolution calls with the canonical helper in `backend/src/api/workflow.py`
- [ ] T021 [P] [US2] Memoize repeated repository resolution results for refresh flows in `backend/src/utils.py`

**Checkpoint**: Backend idle viewing is measurably cheaper, manual refresh still bypasses cache, and polling no longer escalates into unnecessary full refreshes.

---

## Phase 5: User Story 3 - Coherent Frontend Refresh Policy (Priority: P2)

**Goal**: Keep lightweight task updates fast and scoped while reserving full-board reloads for explicit manual refresh.

**Independent Test**: Trigger WebSocket and polling task updates to confirm only task queries refresh, then trigger manual refresh to confirm a forced full-board reload still occurs.

### Tests for User Story 3

- [ ] T022 [P] [US3] Extend task-only invalidation coverage for websocket and polling events in `frontend/src/hooks/useRealTimeSync.test.tsx`
- [ ] T023 [P] [US3] Extend auto-refresh and manual-refresh policy coverage in `frontend/src/hooks/useBoardRefresh.test.tsx`
- [ ] T024 [P] [US3] Extend board and task query-key contract coverage in `frontend/src/hooks/useProjectBoard.test.tsx`

### Implementation for User Story 3

- [ ] T025 [US3] Narrow fallback polling invalidation to task-only query keys in `frontend/src/hooks/useRealTimeSync.ts`
- [ ] T026 [US3] Align auto-refresh and manual-refresh paths to the shared refresh policy in `frontend/src/hooks/useBoardRefresh.ts`
- [ ] T027 [US3] Export stable board and task query-key helpers for refresh callers in `frontend/src/hooks/useProjectBoard.ts`

**Checkpoint**: Refresh events are coherent across WebSocket, polling, auto-refresh, and manual refresh, with no accidental full-board invalidation.

---

## Phase 6: User Story 4 - Responsive Board Rendering on Interaction (Priority: P2)

**Goal**: Reduce unnecessary rerenders and repeated derived-state work so board interactions stay responsive on larger boards.

**Independent Test**: Profile drag, scroll, and popover interactions on a representative board and verify only the affected columns/cards rerender while unchanged derived values remain memoized.

### Tests for User Story 4

- [ ] T028 [P] [US4] Extend derived-state and rerender-scope coverage in `frontend/src/pages/ProjectsPage.test.tsx`
- [ ] T029 [P] [US4] Extend sibling-column rerender guards in `frontend/src/components/board/BoardColumn.test.tsx`
- [ ] T030 [P] [US4] Extend unchanged-card rerender guards in `frontend/src/components/board/IssueCard.test.tsx`

### Implementation for User Story 4

- [ ] T031 [US4] Memoize pipeline grid style and other stable board-derived values in `frontend/src/pages/ProjectsPage.tsx`
- [ ] T032 [US4] Stabilize modal and popover listener callbacks to reduce hot re-registration in `frontend/src/pages/ProjectsPage.tsx`
- [ ] T033 [US4] Preserve memoized drag-update boundaries for columns in `frontend/src/components/board/BoardColumn.tsx`
- [ ] T034 [US4] Preserve memoized single-card update boundaries in `frontend/src/components/board/IssueCard.tsx`

**Checkpoint**: Board interactions remain responsive without introducing second-wave architectural work such as virtualization.

---

## Phase 7: User Story 5 - Verification and Regression Coverage (Priority: P3)

**Goal**: Lock in the performance improvements with automated regression coverage and one manual verification pass.

**Independent Test**: Run the backend and frontend regression suites, then perform a manual network/profile pass and confirm the observed behavior matches the automated expectations and success criteria.

### Tests for User Story 5

- [ ] T035 [P] [US5] Extend backend cache regression coverage for warm-versus-cold sub-issue behavior in `backend/tests/unit/test_cache.py`
- [ ] T036 [P] [US5] Extend frontend end-to-end refresh regression coverage in `frontend/src/hooks/useBoardRefresh.test.tsx`

### Implementation for User Story 5

- [ ] T037 [US5] Record backend regression-suite commands and manual verification steps in `specs/034-performance-review/quickstart.md`
- [ ] T038 [US5] Record frontend regression-suite results and manual profile pass notes in `specs/034-performance-review/quickstart.md`
- [ ] T039 [US5] Reconcile measured results against SC-001 through SC-009 in `specs/034-performance-review/research.md`

**Checkpoint**: Regression coverage and manual verification demonstrate the optimized behavior is real and maintainable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Align final contracts and documentation, and capture only deferred follow-up planning for work that remains out of scope in this first pass.

- [ ] T040 [P] Align verified cache reuse and forced-refresh behavior notes in `specs/034-performance-review/contracts/backend-cache.md`
- [ ] T041 [P] Align verified endpoint and rerender measurement notes in `specs/034-performance-review/contracts/board-endpoints.md`
- [ ] T042 [P] Align verified unified refresh policy notes in `specs/034-performance-review/contracts/refresh-policy.md`
- [ ] T043 [P] Document deferred second-wave follow-up items only (no implementation) in `specs/034-performance-review/research.md`
- [ ] T044 [P] Refresh final implementation checklist, command matrix, and validation notes in `specs/034-performance-review/quickstart.md`

**Checkpoint**: Feature docs and contracts accurately describe the shipped first-pass work and clearly separate deferred follow-up ideas.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks every user story.
- **User Story 1 (Phase 3)**: Depends on Foundational because measurement helpers and instrumentation must already exist.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because backend optimization targets must be judged against captured baselines.
- **User Story 3 (Phase 5)**: Depends on User Story 1 and Foundational because frontend refresh changes must preserve measured baseline behavior and use the shared query-key scaffolding.
- **User Story 4 (Phase 6)**: Depends on User Story 1 and User Story 3 because render optimization should be profiled against the baseline after refresh-policy churn is stabilized.
- **User Story 5 (Phase 7)**: Depends on User Stories 2, 3, and 4 because regression coverage and verification are only meaningful after the optimizations land.
- **Polish (Phase 8)**: Depends on all completed user stories.

### User Story Dependency Graph

```text
Setup -> Foundational -> US1
                         ├──> US2
                         └──> US3 -> US4
US2 ------------------------------┐
US3 ------------------------------┼--> US5 -> Polish
US4 ------------------------------┘
```

### Within Each User Story

- Write the listed tests first and confirm they fail before changing implementation files.
- Complete shared helpers before endpoint or hook changes that depend on them.
- Finish the implementation tasks before updating measurement/verification documentation.
- Keep optional second-wave ideas documented only; do not implement them as part of this task set.

### Parallel Opportunities

- **25 tasks** are explicitly marked `[P]` and can be split across teammates; validate this count whenever task markers change.
- Setup parallelism: backend helper work (`T002`) and frontend helper work (`T003`) can run together after `T001` is scoped.
- Foundational parallelism: `T005`, `T006`, and `T007` touch different files and can proceed simultaneously after `T004`.
- Story parallelism: once US1 is complete, backend work (US2) and frontend refresh work (US3) can proceed in parallel; US4 should follow once US3 stabilizes.
- Polish parallelism: `T040`-`T044` are documentation-alignment tasks across separate files and can be finished concurrently.

---

## Parallel Execution Examples

### User Story 1

```text
Run in parallel: T008, T009
Then complete in parallel: T010, T011
Finish with: T012
```

### User Story 2

```text
Run in parallel: T013, T014, T015
Run in parallel after tests are red: T020, T021
Then complete sequential backend flow: T016 -> T017 -> T018 -> T019
```

### User Story 3

```text
Run in parallel: T022, T023, T024
Then complete implementation flow: T027 -> T025 -> T026
```

### User Story 4

```text
Run in parallel: T028, T029, T030
Then complete page-level work: T031 -> T032
Finish component boundaries in parallel: T033, T034
```

### User Story 5

```text
Run in parallel: T035, T036
Then document verification in order: T037 -> T038 -> T039
```

---

## Implementation Strategy

### MVP First

1. Complete **Phase 1: Setup**.
2. Complete **Phase 2: Foundational**.
3. Complete **Phase 3: User Story 1** to lock the baseline and audit state.
4. Complete **Phase 4: User Story 2** for the first measurable production win.
5. **STOP and VALIDATE**: Compare idle API consumption and warm-cache refresh behavior against the captured baseline before expanding scope.

### Incremental Delivery

1. Ship measurement scaffolding and documented baseline capture (US1).
2. Ship backend idle API reduction and cache reuse improvements (US2).
3. Ship coherent frontend refresh policy without broad invalidation (US3).
4. Ship rendering optimizations limited to memoization and listener stabilization (US4).
5. Lock in coverage and manual verification evidence (US5).
6. Update contracts and deferred follow-up notes without adding second-wave implementation work (Polish).

### Parallel Team Strategy

1. One developer owns backend instrumentation and helpers (`T002`, `T005`, `T006`).
2. One developer owns frontend test harness and query-key scaffolding (`T003`, `T007`).
3. After US1, backend optimization work (US2) and frontend refresh work (US3) can proceed in parallel.
4. Once US3 settles, a frontend-focused developer can finish rendering optimization (US4) while another developer prepares regression verification (US5).

---

## Notes

- Every task above follows the required checklist format: `- [ ] T### [P?] [US?] Description with exact file path`.
- `[P]` means the task is parallelizable because it targets a separate file or an isolated documentation stream.
- User story labels map directly to the five user stories in `spec.md`.
- The task list intentionally stays inside first-pass, low-risk performance work; virtualization, ETag-based conditional requests, and major service decomposition remain deferred follow-up planning only.
